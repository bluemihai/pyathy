"""pyathy's command line: run the features, init, steps, -h; and the Report (pyathy's own
output instead of pytest's). The help and step texts live in help.py.
"""

import os
import pathlib
import sys
import tempfile

import pytest
from pytest_bdd.exceptions import GherkinParseError
from pytest_bdd.feature import get_feature
from pytest_bdd.parser import render_string
from pytest_bdd.scenario import scenario_wrapper_template_registry

from .help import Styler, colour_ok, help_text, own_steps, steps_text
from .lastrun import LastRun, NextFailure, key
from .program import ProgramError, student_python

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


class Report:
    """pyathy's own output instead of pytest's. By default each scenario's run as a terminal
    would show it (prompts, typed answers, boards), then its ✔/✘ line with the reason under a
    ✘; after all scenarios a summary of the ✔/✘ lines and the TOTAL line graders read.
    quiet: only the ✔/✘ lines and TOTAL."""

    def __init__(self, broken=0, quiet=False, lastrun=None, next_failure=None):
        self.errors = {}
        self.feature = None
        self.passed = 0
        self.total = broken  # each unreadable feature file counts as one failed scenario
        self.quiet = quiet
        self.colour = colour_ok()
        self.programs = {}
        self.results = []    # (feature, line) per scenario, for the summary
        self.lastrun = lastrun            # the .pyathy/last-run.json memory, rewritten at the end
        self.next_failure = next_failure  # the NextFailure plugin under --next-failure, else None
        self.keys, self.collected, self.count = {}, [], 0
        self.ran, self.failed = set(), set()
        self.command = command()

    def style(self, code, text):
        return f"\x1b[{code}m{text}\x1b[0m" if self.colour else text

    def transcript(self, program):
        """The program's run as a terminal showed it, under a gutter; typed answers in bold."""
        if program is None or program.state == "new":
            return [self.style(2, "  │ ") + self.style(2, "(the program did not start)")]
        lines = []
        for text, typed in [*program.runs, (program.output, program.typed)]:
            if lines:  # an earlier run, then the run after "the program is started again"
                lines.append(self.style(2, "[the program is started again]"))
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

    def pytest_collectreport(self, report):
        if report.failed:
            last = report.longreprtext.strip().splitlines()[-1:] or ["?"]
            print(f"✘ could not load the features: {last[0].removeprefix('E   ')}")

    def pytest_bdd_step_func_lookup_error(self, request, feature, scenario, step, exception):
        self.errors[request.node.nodeid] = (f"line {step.line_number}: pyathy has no step that matches\n"
                                            f"    {step.keyword} {step.name}")

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
            print("\n".join(f"      {line}" for line in error.splitlines()))
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
                    print(f"Feature: {feature}")
                print(line)
        stopped = session is not None and bool(session.shouldfail or session.shouldstop)
        not_run = self.count - len(self.ran - {None})
        suffix = f" (stopped at the first failure; {plural(not_run, 'scenario')} not run)" if stopped else ""
        print(f"\nTOTAL  {self.passed} of {self.total}{suffix}")
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
    good, broken = [], 0
    for path in files:
        if (problem := gherkin_problem(path)) is None:
            good.append(os.path.abspath(path))
        else:
            broken += 1
            print(f"✘ {os.path.relpath(path)} is not valid Gherkin\n{problem}")
    if not files:
        print(f"pyathy: no .feature files in {', '.join(targets)}")
        return 2
    try:
        if "solution" in options:  # the features here, against the teacher's program next door
            os.environ["PYATHY_APP"] = os.path.abspath(os.path.join(solution_folder(options["solution"]), "main.py"))
        os.environ.setdefault("PYATHY_APP", os.path.abspath("main.py"))
        folder = os.path.dirname(os.path.abspath(os.environ["PYATHY_APP"]))
        python, how = student_python(folder)
    except ProgramError as e:
        print(f"pyathy: {e}")
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
        print(help_text(Styler()))
        sys.exit(0)
    if args[:1] == ["steps"]:
        print(steps_text(Styler(), own_steps()))
        sys.exit(0)
    sys.exit(run(args))


if __name__ == "__main__":
    main()
