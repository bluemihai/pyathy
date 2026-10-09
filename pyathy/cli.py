"""pyathy's command line: run the features, init, steps, -h; and the Report (pyathy's own
output instead of pytest's). The help and step texts live in help.py.
"""

import difflib
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
from importlib.metadata import PackageNotFoundError, distribution

import pytest
from pytest_bdd.exceptions import GherkinParseError
from pytest_bdd.feature import get_feature
from pytest_bdd.parser import render_string
from pytest_bdd.scenario import scenario_wrapper_template_registry

from . import __version__
from .help import BOLD, DIM, GREEN, PLACEHOLDER, RED, Styler, help_text, own_steps, steps_text, suggest
from .lastrun import LastRun, NextFailure, key
from .program import ProgramError, plain, student_python

HELLO_FEATURE = '''Feature: Hello World

  Scenario: the program greets the world
    When I start the program
    Then "Hello World" is printed
    And the program ends
'''

HELLO_MAIN = 'print("Hello World")\n'

RUNNER = '''from pytest_bdd import scenarios


scenarios({paths})
'''


MAX_TRANSCRIPT = 200  # lines of one scenario's run shown (its first 150, its last 50); the rest is counted
PIPED_WIDTH = 120     # columns a -q reason line is cut to when the output is not a terminal

# The shapes of a reason's lines, coloured by meaning (the text itself is never changed):
# `expected X, but Y` splits where the observed part starts; a block of `    | ` lines follows a
# header that announces the expected lines (green) or the lines the program printed (red in a diff)
OBSERVED = re.compile(r"(, but |; but | but |; files written: |; it wrote)")
EXPECTED_BLOCK = re.compile(r"^expected .*(?:these lines|these rows|to contain).*:$")
PRINTED_BLOCK = re.compile(r"^(?:the last \d+ lines|the only line) printed:$")
BLOCK = "    | "


def origin():
    """Where this pyathy runs from, so two copies are never confused: the pyathy/ folder a
    student unzipped (`python pyathy`), the repo an editable install points at, or the
    installed package."""
    package = pathlib.Path(__file__).resolve().parent
    folder = package.parent
    if (folder / "__main__.py").is_file() and (folder / "lib").is_dir():
        return str(folder)
    try:
        url = json.loads(distribution("pyathy").read_text("direct_url.json") or "{}")
        if url.get("dir_info", {}).get("editable") and url.get("url", "").startswith("file://"):
            return f"editable: {url['url'].removeprefix('file://')}"
    except (PackageNotFoundError, ValueError):
        pass
    return f"installed: {package}"


def version_line():
    return f"pyathy {__version__} ({origin()})"


def title_line(styler):
    """The dim last line of the report, `steps` and -h: which pyathy answered, from where."""
    return styler.style(2, f"pyathy {__version__} · {origin()}")


class Report:
    """pyathy's own output instead of pytest's. By default each scenario's run as a terminal
    would show it (prompts, typed answers, boards), then its ✔/✘ line with the reason under a
    ✘; after all scenarios a summary of the ✔/✘ lines and the TOTAL line graders read.
    quiet: only the ✔/✘ lines (a ✘ with its reason's first line) and TOTAL."""

    def __init__(self, broken=0, quiet=False, lastrun=None, next_failure=None):
        self.errors = {}
        self.feature = None
        self.passed = 0
        self.total = broken  # each unreadable feature file counts as one failed scenario
        self.quiet = quiet
        self.styler = Styler()
        self.colour = self.styler.colour
        self.width = shutil.get_terminal_size().columns if sys.stdout.isatty() else PIPED_WIDTH
        self.programs = {}
        self.results = []    # (feature, line) per scenario, for the summary
        self.lastrun = lastrun            # the .pyathy/last-run.json memory, rewritten at the end
        self.next_failure = next_failure  # the NextFailure plugin under --next-failure, else None
        self.keys, self.collected, self.count = {}, [], 0
        self.ran, self.failed = set(), set()
        self.command = command()

    def style(self, code, text):
        return self.styler.style(code, text)

    def paint(self, text, base=None, tokens=True):
        return self.styler.paint(text, base, tokens)

    def transcript(self, program):
        """The program's run as a terminal showed it, under a gutter; typed answers in bold.
        With colour off (piped, NO_COLOR) the program's own colour codes go too: plain text."""
        if program is None or program.state == "new":
            return [self.style(2, "  │ ") + self.style(2, "(the program did not start)")]
        lines = []
        for text, typed in [*program.runs, (program.output, program.typed)]:
            if lines:  # an earlier run, then the run after "the program is started again"
                lines.append(self.style(2, "[the program is started again]"))
            if not self.colour:
                text = plain(text)
            pieces, at = [], 0
            for start, end in typed if self.colour else []:
                pieces += [text[at:start], self.style(1, text[start:end])]
                at = end
            lines += ("".join(pieces) + text[at:]).splitlines() or [self.style(2, "(the program printed nothing)")]
        more = len(lines) - MAX_TRANSCRIPT
        if more > 0:  # the start and the end (where a failure usually is), the middle counted
            head = MAX_TRANSCRIPT * 3 // 4
            lines = lines[:head] + [self.style(2, f"… ({more} more lines)")] + lines[head + more:]
        gutter = self.style(2, "  │ ")
        return [gutter + line for line in lines]

    def reason(self, error):
        """Why a scenario failed, indented under its ✘ line: the whole message, or under -q
        its first non-empty line cut to the terminal's width (the rest is a run without -q).
        On a terminal the lines are coloured by what they say (reason_lines)."""
        if not self.quiet:
            return "\n".join(f"      {line}" for line in self.reason_lines(error.splitlines()))
        filled = [line for line in error.splitlines() if line.strip()]
        first = filled[0] if filled else "?"
        if first.rstrip().endswith(":") and len(filled) > 1:  # "expected these lines, in a row:" + the first one
            first = f"{first.rstrip()} {filled[1].strip()}"
        if len(first) + 6 > self.width:
            first = first[:max(self.width - 7, 1)] + "…"
        return "      " + self.reason_line(first)

    def reason_lines(self, lines):
        """The lines of a reason, coloured by meaning. The block of lines the scenario expected
        (`expected these lines, in a row:` + `    | ` lines) is shown as a diff against the block
        the program printed (`the last N lines printed:`) when the message has both: `+ ` expected
        lines green, `- ` printed lines red, lines in both dim. A file's expected lines have no
        printed twin in the message, so they stay green on their own."""
        printed = None
        for i, line in enumerate(lines):
            if PRINTED_BLOCK.match(line):
                printed = [text[len(BLOCK):] for text in lines[i + 1:] if text.startswith(BLOCK)]
        out, i = [], 0
        while i < len(lines):
            line = lines[i]
            out.append(self.reason_line(line))
            i += 1
            if EXPECTED_BLOCK.match(line):
                want = []
                while i < len(lines) and lines[i].startswith(BLOCK):
                    want.append(lines[i][len(BLOCK):])
                    i += 1
                if printed and "the file" not in line:
                    out += self.diff(want, printed)
                else:
                    out += [self.paint(BLOCK + text, GREEN) for text in want]
        return out

    def reason_line(self, line):
        """One line of a reason: what was expected green and what was observed red (`expected X,
        but Y`; `closest line printed: …`), quoted strings and file names cyan, a `note:` and where
        the program stopped dim, the turns played dim but the last one (where it failed)."""
        if line.startswith("expected "):
            m = OBSERVED.search(line)
            if m:
                return self.paint(line[:m.start()], GREEN) + self.paint(line[m.start():], RED)
            return self.paint(line, GREEN)
        if line.startswith("did you mean: "):  # the suggested step in the placeholder colour
            return "did you mean: " + self.style(PLACEHOLDER, line[len("did you mean: "):])
        if line == "run pyathy steps for the list":
            return "run " + self.style(PLACEHOLDER, "pyathy steps") + " for the list"
        if line.startswith("closest line printed:"):
            return self.paint(line, RED, tokens=False)
        if line.startswith(("note:", "the program is waiting for ", "the program has ended")):
            return self.paint(line, DIM)
        if line.startswith("turns: "):
            head, sep, last = line.rpartition(" · ")
            if not sep:
                head, sep, last = "turns:", " ", line[len("turns: "):]
            return self.paint(head + sep, DIM) + self.paint(last)
        return self.paint(line)

    def diff(self, want, have):
        """`want` (the expected lines) against the window of `have` (the printed lines) that
        matches it best, the usual way round: `- ` what was printed, `+ ` what was expected.
        Lines are compared as the steps compare them (trailing spaces and case ignored)."""
        def norm(text):
            return text.rstrip().lower()
        best, score = have, -1.0
        for size in range(len(want), len(want) + 3):
            for start in range(max(len(have) - size + 1, 1)):
                window = have[start:start + size]
                ratio = difflib.SequenceMatcher(None, "\n".join(map(norm, window)),
                                                "\n".join(map(norm, want))).ratio()
                if ratio > score:
                    best, score = window, ratio
        out = []
        matcher = difflib.SequenceMatcher(None, [norm(t) for t in best], [norm(t) for t in want])
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                out += [self.paint(f"      {text}", DIM, tokens=False) for text in best[i1:i2]]
                continue
            out += [self.paint(f"    - {text}", RED, tokens=False) for text in best[i1:i2]]
            out += [self.paint(f"    + {text}", GREEN, tokens=False) for text in want[j1:j2]]
        return out

    def pytest_collectreport(self, report):
        if report.failed:
            last = report.longreprtext.strip().splitlines()[-1:] or ["?"]
            print(f"✘ could not load the features: {last[0].removeprefix('E   ')}")

    def pytest_bdd_step_func_lookup_error(self, request, feature, scenario, step, exception):
        from . import steps
        own = [pattern for pattern, file, _, _ in steps.REGISTERED if file != steps.__file__]
        closest = suggest(step.name, own)
        hint = f"did you mean: {closest}" if closest else "run pyathy steps for the list"
        self.errors[request.node.nodeid] = (f"line {step.line_number}: pyathy has no step that matches\n"
                                            f"    {step.keyword} {step.name}\n{hint}")

    def pytest_runtest_makereport(self, item, call):
        if hasattr(item, "pyathy_program"):
            self.programs[item.nodeid] = item.pyathy_program
        if call.excinfo is not None and item.nodeid not in self.errors:
            self.errors[item.nodeid] = str(call.excinfo.value)

    def pytest_runtest_logfinish(self, nodeid, location):
        feature = self.features.get(nodeid)
        name = self.names.get(nodeid, nodeid)
        if feature is not None and feature != self.feature:
            self.feature = feature
            print(f"\n{self.style(1, f'Feature: {feature}')}")
        if not self.quiet:
            print(f"\n  Scenario: {name}")
            print("\n".join(self.transcript(self.programs.get(nodeid))))
        self.programs.pop(nodeid, None)
        self.total += 1
        self.ran.add(self.keys.get(nodeid))
        error = self.errors.get(nodeid)
        if error is None:
            self.passed += 1
            line = f"  {self.style(32, '✔')} {name}"
        else:
            self.failed.add(self.keys.get(nodeid))
            line = f"  {self.style(31, '✘')} {name}"
        self.results.append((feature, line))
        print(line)
        if error is not None:
            print(self.reason(error))
        order = self.next_failure.order if self.next_failure else []
        if order and nodeid == order[-1] and error is None and self.count > len(order):
            n = len(order)
            verb = "passes" if n == 1 else "pass"
            note = f"{plural(n, 'scenario')} that failed last time {verb} now; running everything else."
            print(f"\n{self.style(1, note)}")

    def pytest_collection_finish(self, session):
        self.names, self.features = {}, {}
        self.count = len(session.items)
        for item in session.items:
            scenario = scenario_wrapper_template_registry.get(item.obj)
            name = scenario.name if scenario else item.name
            example = getattr(getattr(item, "callspec", None), "params", {}).get("_pytest_bdd_example")
            if example:  # a Scenario Outline row: its values, not the <placeholders>
                name = render_string(name, example)
            self.names[item.nodeid] = name
            self.keys[item.nodeid] = key(item)
            self.collected.append(self.keys[item.nodeid])
            if scenario is not None:
                self.features[item.nodeid] = scenario.feature.name

    def pytest_sessionfinish(self, session):
        if not self.quiet and self.results:
            print(f"\n{self.style(1, 'Summary')}")
            shown = None
            for feature, line in self.results:
                if feature is not None and feature != shown:
                    shown = feature
                    print(self.style(BOLD, f"Feature: {feature}"))
                print(line)
        stopped = session is not None and bool(session.shouldfail or session.shouldstop)
        not_run = self.count - len(self.ran - {None})
        suffix = f" (stopped at the first failure; {plural(not_run, 'scenario')} not run)" if stopped else ""
        print(f"\nTOTAL  {self.passed} of {self.total}{suffix}")
        if self.quiet and self.passed < self.total:
            print(self.style(2, f"run {self.command} without -q for the full output of each ✘"))
        if stopped and self.next_failure:
            order = self.next_failure.order
            left = len(order) - len([n for n in order if n in self.names and self.keys[n] in self.ran])
            rest = not_run - left
            again = f"Fix it and run {self.command} --next-failure again:"
            if left:
                then = f", then the other {rest}" if rest else ""
                print(f"{again} {left} more scenario{'' if left == 1 else 's'} that failed last time{then}.")
            else:
                then = f", so the other {rest} run next" if rest else ""
                print(f"{again} it was the last one that failed last time{then}.")
        if self.lastrun is not None:
            self.lastrun.update([k for k in self.collected if k is not None], self.ran, self.failed,
                                prune=self.next_failure is not None)
        print(title_line(self.styler))  # last, after TOTAL and any hint under it


def plural(n, noun):
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def command():
    """How this run was started, for a hint: `python pyathy` (the folder next to main.py) or `pyathy`."""
    started = sys.argv[0]
    return "python pyathy" if os.path.isdir(started) or started.endswith("__main__.py") else "pyathy"


def init():
    os.makedirs("features", exist_ok=True)
    made = []
    for path, text in (("features/hello.feature", HELLO_FEATURE), ("main.py", HELLO_MAIN)):
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(text)
            made.append(path)
    for path in made:
        print(f"created {path}")
    print("now run:  pyathy")
    return 0


# pyathy's own flags, short and long (-x: pytest's spelling of -ff, kept as an unlisted alias)
FLAGS = {"-q": "quiet", "--quiet": "quiet",
         "-ff": "fail_fast", "--fail-fast": "fail_fast", "-x": "fail_fast",
         "-nf": "next_failure", "--next-failure": "next_failure",
         "-s": "solution", "--solution": "solution"}
SOLUTION = "_solution"


def has_features(path):
    """A .feature file, or a folder with one in it: a target, never -s's folder."""
    if os.path.isfile(path):
        return path.endswith(".feature")
    return os.path.isdir(path) and any(pathlib.Path(path).rglob("*.feature"))


def parse(args):
    """(targets, options, flags for pytest). options: pyathy's own flags by their long name;
    "solution" holds the folder name -s was given (`-s NAME`, `-s=NAME`, or the default)."""
    targets, options, flags = [], {}, []
    i = 0
    while i < len(args):
        arg, i = args[i], i + 1
        name, _, value = arg.partition("=")
        if FLAGS.get(name) == "solution":
            if not value and i < len(args) and not args[i].startswith("-") and not has_features(args[i]):
                value, i = args[i], i + 1
            options["solution"] = value or SOLUTION
        elif arg in FLAGS:
            options[FLAGS[arg]] = True
        elif arg.startswith("-"):
            flags.append(arg)
        else:
            targets.append(arg)
    return targets, options, flags


def solution_folder(name):
    """The folder -s names: ./NAME, or ./_solution-NAME for a bare suffix (`-s obj2`)."""
    looked = [name] if name.startswith(SOLUTION) else [name, f"{SOLUTION}-{name}"]
    for folder in looked:
        if os.path.isdir(folder):
            return folder
    where = " or ".join(f"./{f}" for f in looked)
    raise ProgramError(f"no {looked[-1]} folder here (looked for {where})")


def run(args):
    targets, options, flags = parse(args)
    targets = targets or ["features"]
    quiet, fail_fast = options.get("quiet", False), options.get("fail_fast", False)
    next_failure = options.get("next_failure", False)
    flags += ["-x"] if fail_fast else []
    files = []
    for t in targets:
        if os.path.isdir(t):
            files += sorted(str(p) for p in pathlib.Path(t).rglob("*.feature"))
        elif os.path.isfile(t):
            files.append(t)
        else:
            print(f"pyathy: no such file or folder: {t}")
            return 2
    if not files:
        print(f"pyathy: no .feature files in {', '.join(targets)}")
        return 2
    good, broken = [], 0
    for path in files:
        if (problem := gherkin_problem(path)) is None:
            good.append(os.path.abspath(path))
        else:
            broken += 1
            print(f"✘ {os.path.relpath(path)} is not valid Gherkin\n{problem}")
    try:
        if "solution" in options:  # the features here, against the teacher's program next door
            os.environ["PYATHY_APP"] = os.path.abspath(os.path.join(solution_folder(options["solution"]), "main.py"))
        os.environ.setdefault("PYATHY_APP", os.path.abspath("main.py"))
        folder = os.path.dirname(os.path.abspath(os.environ["PYATHY_APP"]))
        python, how = student_python(folder)
    except ProgramError as e:
        print(f"pyathy: {e}")
        print(title_line(Styler()))
        return 2
    if folder != os.getcwd():
        print(f"Program: {os.path.relpath(os.environ['PYATHY_APP'])}")
    if how:
        print(f"Python: {python} ({how})")
    lastrun = LastRun(folder)  # the failures are remembered next to the program that failed
    plugins = []
    if next_failure:
        if lastrun.failed:
            n = len(lastrun.failed)
            print(f"{command()} --next-failure: {n} scenario{'' if n == 1 else 's'} failed last time; "
                  f"running {'it' if n == 1 else 'them'} first, stopping at the first that still fails.")
            plugins.append(NextFailure(lastrun.failed))
        else:
            print(f"{command()} --next-failure: no scenario failed last time; running everything.")
    report = Report(broken, quiet, lastrun, plugins[0] if plugins else None)
    if not good:
        report.pytest_sessionfinish(None)
        return 1
    with tempfile.TemporaryDirectory(prefix="pyathy-run-") as tmp:
        runner = os.path.join(tmp, "test_features.py")
        with open(runner, "w") as f:
            f.write(RUNNER.format(paths=", ".join(repr(p) for p in good)))
        code = pytest.main([runner, "--rootdir", tmp, "-p", "no:cacheprovider", "-p", "pyathy.steps",
                            "-p", "no:terminal", *flags], plugins=[*plugins, report])
    return code or (1 if broken else 0)


def gherkin_problem(path):
    """None when the file parses, else a short beginner-readable reason."""
    try:
        get_feature(os.path.dirname(os.path.abspath(path)), os.path.basename(path))
    except GherkinParseError as e:
        return f"    line {e.line}: {e.line_content.strip()}\n    {e.message}"
    except Exception as e:  # anything else the parser trips on
        return f"    {e}"
    return None


def main():
    args = sys.argv[1:]
    if args[:1] == ["init"]:
        sys.exit(init())
    if args[:1] in (["-h"], ["--help"]):
        styler = Styler()
        print(help_text(styler) + "\n" + title_line(styler))
        sys.exit(0)
    if args[:1] in (["-v"], ["--version"]):
        print(version_line())
        sys.exit(0)
    if args[:1] == ["steps"]:
        styler = Styler()
        print(steps_text(styler, own_steps()) + "\n" + title_line(styler))
        sys.exit(0)
    sys.exit(run(args))


if __name__ == "__main__":
    main()
