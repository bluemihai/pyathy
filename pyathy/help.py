"""`pyathy -h` and `pyathy steps`: the help and the step list, colour-coded on a terminal.

Text here is marked up with {braces} around the parts a student replaces (`I input {4}`);
a Styler turns them into a colour on a terminal and drops them when piped (colour_ok()).
"""

import os
import pathlib
import re
import sys

INTRO = "pyathy: test your Python program with scenarios written in plain English."

USAGE = [
    ("pyathy", "run every features/*.feature against main.py here"),
    ("pyathy {features/x.feature}", "run only that file (or folder)"),
    ("pyathy init", "create features/hello.feature to start from"),
    ("pyathy steps", "list every step you can use"),
    ("-q, --quiet", "only one line per scenario and the total"),
    ("-h", "this help"),
]

EXAMPLE = """\
A feature file (features/tictactoe.feature):

  Feature: Tic Tac Toe

    Scenario: X wins with the top row
      When I input 1, 4, 2, 5, 3
      Then "Player X wins!" is printed
      And the program ends"""

OUTRO = "Run `pyathy steps` for every step you can use."

# (step as written, what it does); a newline in the explanation starts a second line
STEPS = {
    "Starting": [
        ("I start the program", "run main.py until it asks something or ends"),
        ("the program {files.py}", "run files.py instead of main.py"),
        ("I run the program with {photos/ --all}",
         'start it with these command-line arguments\n(quote one with spaces: "my file.txt")'),
        ("the program may take {30} seconds", "wait this long for a slow program (default 10)"),
    ],
    "Typing": [
        ("I input {4}", "type 4 when the program asks"),
        ("I input {1, 4, 2}", "several answers, one per question"),
        ("I answer with an empty string", "just press enter"),
    ],
    "Dice": [
        ("I roll {6}", "the next die shows 6"),
        ("I roll {4} and {6}", "two dice"),
        ("the random choice is {red}", "the next random pick returns this value"),
    ],
    "Checking": [
        ('{"Hello World"} is printed', "anywhere in the output (case ignored)"),
        ('{"ERROR"} is printed {3} times', ""),
        ('{"Congratulations"} is not printed', ""),
        ('the output starts with {"Welcome"}', ""),
        ("the output shows:", "these lines in a row (put them\nbetween two lines of three quotes)"),
        ('the program asks {"Player X, choose a square (1-9):"}', ""),
        ("the program ends", ""),
        ("the program is still running", ""),
        ('the file {"scores.txt"} contains {"Ann 3"}', "a file the program wrote"),
    ],
}

STEPS_INTRO = "Steps you can use (after Given, When, Then or And):"
STEPS_OUTRO = """\
Each scenario runs your program from the start, in a copy of this folder.
A folder with a Poetry pyproject.toml runs on its Poetry environment (run
poetry install first); else a .venv in the folder; else pyathy's own Python."""

BOLD, DIM, PLACEHOLDER = "1", "2", "36"
GHERKIN = re.compile(r"^(\s*)(Feature:|Scenario:|Given|When|Then|And|But)( .*)$")


def colour_ok():
    """ANSI styles only on a terminal that shows them (and never with NO_COLOR set).
    FORCE_COLOR turns them on when piped (to capture or page the coloured output)."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if not sys.stdout.isatty():
        return False
    return os.name != "nt" or bool(os.environ.get("WT_SESSION") or os.environ.get("TERM"))


class Styler:
    """Bold headers, placeholders in colour, explanations dim; plain text when colour is off."""

    def __init__(self, colour=None):
        self.colour = colour_ok() if colour is None else colour

    def style(self, code, text):
        return f"\x1b[{code}m{text}\x1b[0m" if self.colour and text else text

    def marked(self, text):
        """`I input {4}` -> the 4 in the placeholder colour, braces gone."""
        return re.sub(r"\{([^{}]*)\}", lambda m: self.style(PLACEHOLDER, m.group(1)), text)

    def entry(self, step, explanation, column):
        """`  <step>  <explanation>` with the explanation dim at `column`, or on the next
        line(s) when the step reaches that far."""
        width = len(re.sub(r"[{}]", "", step)) + 2
        lines = explanation.splitlines()
        first = "  " + self.marked(step)
        if not lines:
            return [first]
        if width + 2 > column:
            out = [first]
        else:
            out = [first + " " * (column - width) + self.style(DIM, lines.pop(0))]
        return out + [" " * column + self.style(DIM, line) for line in lines]

    def gherkin(self, text):
        """Feature/Scenario/When/Then/And in bold."""
        return "\n".join(f"{m.group(1)}{self.style(BOLD, m.group(2))}{m.group(3)}" if (m := GHERKIN.match(line))
                         else line for line in text.splitlines())


def help_text(styler):
    out = [INTRO, "", styler.style(BOLD, "usage:")]
    for command, explanation in USAGE:
        out += styler.entry(command, explanation, 31)
    return "\n".join(out + ["", styler.gherkin(EXAMPLE), "", OUTRO])


def steps_text(styler, own):
    """The built-in step list, then the steps of each *steps.py in `own`."""
    out = [STEPS_INTRO]
    for section, entries in STEPS.items():
        out += ["", styler.style(BOLD, section)]
        for step, explanation in entries:
            out += styler.entry(step, explanation, 35)
    for path, patterns in own:
        out += ["", styler.style(BOLD, "Your own steps") + styler.style(DIM, f"  ({path})")]
        for pattern in patterns:
            out += styler.entry(readable(pattern), "", 35)
    return "\n".join(out + ["", STEPS_OUTRO])


# ---- a features folder's own steps ---------------------------------------------

def own_steps(folder="features"):
    """[(relative path, [pattern, ...])] for every *steps.py under the features folder here."""
    from . import steps

    root = pathlib.Path(folder)
    if not root.is_dir():
        return []
    found = []
    for path in sorted(root.rglob("*steps.py")):
        before = len(steps.REGISTERED)
        try:
            steps.load_own_steps(path)
        except Exception as e:  # noqa: BLE001 - a broken steps file is reported, not fatal
            found.append((str(path), [f"(could not load it: {type(e).__name__}: {e})"]))
            continue
        found.append((str(path), [pattern for pattern, _ in steps.REGISTERED[before:]]))
    return found


def readable(pattern):
    r"""A step's regex as a student reads it: `(?P<name>\w+) has \$(?P<cash>\d+)` -> `<name> has $<cash>`
    (the <names> marked as placeholders). An optional part in [brackets], a bare character class as `…`;
    the rest is kept as written."""
    pattern = pattern.removeprefix("^")
    if pattern.endswith("$") and not pattern.endswith(r"\$"):
        pattern = pattern[:-1]
    out, i = [], 0

    def quantified(piece, at):
        """Append `piece`, reading a quantifier after position `at`; returns the next index."""
        if at < len(pattern) and pattern[at] == "?":
            out.append(f"[{piece}]")
            return at + 1
        out.append(piece)
        return at + 1 if at < len(pattern) and pattern[at] in "+*" else at

    while i < len(pattern):
        c = pattern[i]
        if c == "\\" and i + 1 < len(pattern):
            nxt = pattern[i + 1]
            i = quantified("…" if nxt in "wdsWDS" else "" if nxt in "bB" else nxt, i + 2)
        elif c == "(":
            end = _close(pattern, i)
            inner = pattern[i + 1:end]
            if m := re.match(r"\?P<(\w+)>", inner):
                text = f"{{<{m.group(1)}>}}"
            else:
                text = readable(inner.removeprefix("?:"))
                if "|" in text and not (end + 1 < len(pattern) and pattern[end + 1] == "?"):
                    text = f"({text})"
            i = quantified(text, end + 1)
        elif c == "[":
            end = pattern.index("]", i + 2 if pattern[i + 1] == "]" else i + 1)
            i = quantified("…", end + 1)
        elif c == ".":
            i = quantified("…", i + 1)
        else:
            i = quantified(c, i + 1)
    return "".join(out)


def _close(pattern, start):
    """Index of the ')' matching the '(' at `start`."""
    depth, i = 0, start
    while i < len(pattern):
        if pattern[i] == "\\":
            i += 2
            continue
        if pattern[i] == "(":
            depth += 1
        elif pattern[i] == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(pattern) - 1
