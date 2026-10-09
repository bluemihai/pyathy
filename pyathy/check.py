"""`pyathy check`: read the feature files without running the program, and list what would
stop a scenario before it starts: a line no step matches (with the closest step), a file that
is not valid Gherkin, indentation that differs from the rest of the file, and a file step whose
file pyathy cannot find in the program.
"""

import json
import os
import pathlib
import re
from collections import Counter

from pytest_bdd.exceptions import GherkinParseError
from pytest_bdd.feature import get_feature
from pytest_bdd.parser import render_string

from . import __version__
from .help import STEPS, Styler, suggest
from .program import ProgramError, constant, save_file

STEP_LINE = re.compile(r"^(\s*)(Given|When|Then|And|But|\*)(\s+)(.*?)\s*$")
BLOCK_LINE = re.compile(r"^(\s*)(Scenario Outline|Scenario Template|Scenario|Example|Background|Rule):")
SAVED_GAME = re.compile(r"(?:a saved game:?|there is no saved game|the saved game holds:?|"
                        r"a saved game is written|no saved game is left)", re.IGNORECASE)
CONSTANT = re.compile(r'^(?:a file|there is no file|the file) ([A-Z][A-Z0-9_]*)\b')
OTHER_PROGRAM = re.compile(r"^the program ([\w./-]+\.py)$")
GHERKIN_HINT = "note: each line of a scenario starts with Given, When, Then, And or But (or # for a comment)"


class Problem:
    """One thing found at one line of one file: `message` is what the report prints under it;
    `start`/`end` (0-based columns) mark the step text and `suggestion` replaces it, for an editor."""

    def __init__(self, path, line, message, kind, start=0, end=0, suggestion=None):
        self.path, self.line, self.message, self.kind = path, line, message, kind
        self.start, self.end, self.suggestion = start, end, suggestion

    def as_dict(self):
        return {"file": self.path, "line": self.line, "start": self.start, "end": self.end,
                "kind": self.kind, "message": self.message, "suggestion": self.suggestion}


def feature_files(targets):
    """The .feature files the targets name (a file, or every one in a folder), and the targets
    that are neither."""
    files, missing = [], []
    for target in targets:
        if os.path.isdir(target):
            files += sorted(str(p) for p in pathlib.Path(target).rglob("*.feature"))
        elif os.path.isfile(target):
            files.append(target)
        else:
            missing.append(target)
    return files, missing


def own_patterns(folder):
    """The step patterns of every *steps.py next to the feature files of `folder`, loaded once."""
    from . import steps

    loaded = {file for _, file, _, _ in steps.REGISTERED}
    for path in sorted(pathlib.Path(folder).glob("*steps.py")):
        if str(path) not in loaded:
            steps.load_own_steps(path)
    return [pattern for pattern, file, _, _ in steps.REGISTERED if file != steps.__file__]


def matches(text):
    from . import steps

    return any(parser.is_matching(text) for _, _, parser, _ in steps.REGISTERED)


def check_file(path, app):
    """The problems of one feature file, in line order."""
    rel = os.path.relpath(path)
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    problems = indentation(rel, lines)
    try:
        feature = get_feature(os.path.dirname(os.path.abspath(path)), os.path.basename(path))
    except GherkinParseError as e:
        raw = lines[e.line - 1] if 0 < e.line <= len(lines) else ""
        hint = "" if STEP_LINE.match(raw) or BLOCK_LINE.match(raw) else f"\n{GHERKIN_HINT}"
        problems.append(Problem(rel, e.line, f"not valid Gherkin: {e.message}\n    {raw.strip()}{hint}", "gherkin",
                                len(raw) - len(raw.lstrip()), len(raw)))
        return sorted(problems, key=lambda p: p.line)
    except Exception as e:  # noqa: BLE001 - anything else the parser trips on
        problems.append(Problem(rel, 1, f"not valid Gherkin: {e}", "gherkin"))
        return problems
    try:
        own = own_patterns(os.path.dirname(os.path.abspath(path)))
    except Exception as e:  # noqa: BLE001 - a broken steps file is reported, not fatal
        problems.append(Problem(rel, 1, f"could not load the steps next to it: {type(e).__name__}: {e}", "steps"))
        own = []
    seen = set()
    for scenario in feature.scenarios.values():
        contexts = [c for examples in scenario.examples for c in examples.as_contexts()] or [{}]
        for step in scenario.steps:
            if step.line_number in seen:
                continue
            for context in contexts:
                text = render_string(step.name, context) if context else step.name
                problem = step_problem(rel, lines, step, text, own, app)
                if problem is not None:
                    seen.add(step.line_number)
                    problems.append(problem)
                    break
    return sorted(problems, key=lambda p: p.line)


def step_problem(rel, lines, step, text, own, app):
    """None when `text` (a step's line, its outline values filled in) matches a step and names a
    file the program has; else what is wrong with it."""
    raw = lines[step.line_number - 1] if step.line_number <= len(lines) else ""
    m = STEP_LINE.match(raw)
    start = m.end(3) if m else 0
    end = m.end(4) if m else len(raw)
    if not matches(text):
        closest = suggest(step.name, own)
        hint = f"did you mean: {closest}" if closest else "run pyathy steps for the list"
        return Problem(rel, step.line_number, f"pyathy has no step that matches\n    {step.keyword} {step.name}\n{hint}",
                       "step", start, end, closest)
    if not os.path.isfile(app):  # no program yet: nothing to look the files up in
        return None
    try:
        if SAVED_GAME.fullmatch(text.strip()):
            save_file(app)
        elif cm := CONSTANT.match(text):
            constant(app, cm.group(1))
        elif om := OTHER_PROGRAM.match(text):
            other = os.path.join(os.path.dirname(app), om.group(1))
            if not os.path.isfile(other):
                raise ProgramError(f"there is no {om.group(1)} in this folder")
    except ProgramError as e:
        return Problem(rel, step.line_number, f"pyathy cannot find the file this step needs\n"
                       f"    {step.keyword} {step.name}\n{e}", "file", start, end)
    return None


def indentation(rel, lines):
    """A tab in the indentation, or a scenario or step indented differently from most of its
    kind in the file (lines inside \"\"\" blocks, tables and comments are left alone)."""
    problems, kinds, inside = [], {"scenario": [], "step": []}, False
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith(('"""', "```")):
            inside = not inside
            continue
        if inside or not stripped or stripped.startswith(("#", "|")):
            continue
        lead = line[:len(line) - len(line.lstrip())]
        if "\t" in lead:
            problems.append(Problem(rel, number, "indented with a tab: use spaces", "indent", 0, len(lead)))
            continue
        if BLOCK_LINE.match(line):
            kinds["scenario"].append((number, len(lead)))
        elif STEP_LINE.match(line):
            kinds["step"].append((number, len(lead)))
    if "Rule:" in "\n".join(lines):  # scenarios under a Rule sit deeper on purpose
        return problems
    names = {"scenario": "scenarios", "step": "steps"}
    for kind, found in kinds.items():
        if not found:
            continue
        usual = Counter(indent for _, indent in found).most_common(1)[0][0]
        for number, indent in found:
            if indent != usual:
                problems.append(Problem(rel, number, f"indented {plural(indent, 'space')}, the other "
                                        f"{names[kind]} {usual}", "indent", 0, indent, " " * usual))
    return problems


def plural(n, noun):
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def step_list(own):
    """The steps an editor offers while typing: the built-ins as `pyathy steps` writes them
    ({4} a value to replace), then the folder's own patterns."""
    out = [{"step": step, "doc": " ".join(doc.splitlines()), "own": False}
           for entries in STEPS.values() for step, doc in entries]
    return out + [{"step": pattern, "doc": "", "own": True} for pattern in own]


def run(args):
    """`pyathy check [--json] [targets]`: 0 when nothing is found, 1 when something is, 2 when a
    target does not exist or has no feature files."""
    from .cli import Report, title_line

    as_json = "--json" in args
    targets = [a for a in args if a != "--json"] or ["features"]
    files, missing = feature_files(targets)
    app = os.path.abspath(os.environ.get("PYATHY_APP", "main.py"))
    if missing or not files:
        problem = (f"no such file or folder: {missing[0]}" if missing
                   else f"no .feature files in {', '.join(targets)}")
        if as_json:
            print(json.dumps({"version": __version__, "error": problem, "problems": [], "steps": step_list([])}))
        else:
            print(f"pyathy: {problem}")
        return 2
    results = [(path, check_file(path, app)) for path in files]
    if as_json:
        own = sorted({p for path in files for p in own_patterns(os.path.dirname(os.path.abspath(path)))})
        print(json.dumps({"version": __version__,
                          "problems": [p.as_dict() for _, found in results for p in found],
                          "steps": step_list(own)}, ensure_ascii=False))
        return 1 if any(found for _, found in results) else 0
    report = Report()
    styler = Styler()
    count = 0
    for path, found in results:
        mark = styler.style(31, "✘") if found else styler.style(32, "✔")
        print(f"{mark} {os.path.relpath(path)}")
        for i, problem in enumerate(found):
            count += 1
            print(("\n" if i else "") + report.reason(f"line {problem.line}: {problem.message}"))
    bad = sum(1 for _, found in results if found)
    summary = (f"{plural(count, 'problem')} in {bad} of {plural(len(files), 'file')}" if count
               else f"no problems in {plural(len(files), 'file')}")
    print(f"\n{styler.style(1, summary)}")
    print(title_line(styler))
    return 1 if count else 0
