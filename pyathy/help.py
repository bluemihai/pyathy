"""`pyathy -h` and `pyathy steps`: the help and the step list, colour-coded on a terminal.

Text here is marked up with {braces} around the parts a student replaces (`I input {4}`);
a Styler turns them into a colour on a terminal and drops them when piped (colour_ok()).
"""

import difflib
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
]

# (short, long forms; what it does), each printed man-style: the flag, its explanation under it
OPTIONS = [
    ("-q, --quiet", "only one line per scenario (a ✘ gets one reason line) and the total"),
    ("-ff, --fail-fast", "stop at the first scenario that fails"),
    ("-nf, --next-failure", "run the scenarios that failed last time, in order, stopping at the first that still fails"),
    ("-s, --solution [{FOLDER}]", "run the features here against ./_solution/main.py, or ./FOLDER/main.py "
                                  "(-s obj2 means _solution-obj2)"),
    ("-h, --help", "this help"),
    ("-v, --version", "pyathy's version and where it runs from"),
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
    "Turns": [
        ("{red} rolls {6}", "`I input enter` (if the program is waiting for it) then `I roll 6`,\n"
                            "after checking it is red's turn: the last line announcing a turn\n"
                            "names red and no other player, without digits, like 'Player red:'"),
        ("{Ann} rolls {4}+{6}", "two dice (or: Ann rolls 4 and 6)"),
        ("{red} rolls {3} and picks {2}", "the same, then types 2 at the question that follows\n(or: and answers 2)"),
        ("these turns are played {3} times:", "a table with one step per row (| red rolls 5 |),\nrun in order, this many times"),
        ("the players are {red} and {green}", "the names a turn announcement may use\n(otherwise: the names typed or rolled for so far)"),
        ("{red}'s turn is announced", "a line names red and no other player, without digits\n(or: it is red's turn)"),
        ("a pawn moves from {0} to {3}", "a line of this turn (since the last roll) has these two\n"
                                         "numbers, 'to' or an arrow between them (or: red moves from 0 to 3)"),
        ("nothing moves", "no such line this turn"),
    ],
    "Checking": [
        ('{"Hello World"} is printed', "anywhere in the output (case ignored)"),
        ('{"ERROR"} is printed {3} times', ""),
        ('{"Congratulations"} is not printed', ""),
        ('the output starts with {"Welcome"}', ""),
        ("the output shows:", "these lines in a row (put them\nbetween two lines of three quotes)"),
        ('the program asks {"Player X, choose a square (1-9):"}', ""),
        ('{"orange"} is refused with a message', "after typing it, a message was printed and\nthe same question was asked again"),
        ("the program ends", ""),
        ("the program is still running", ""),
    ],
    "Files": [
        ('a file {"game.txt"} containing {"round 3"}', "put this one-line file in the folder\nbefore the program starts"),
        ('a file {"game.txt"} with:', "the same, several lines (between\ntwo lines of three quotes)"),
        ('there is no file {"game.txt"}', "the program starts without it, whatever is in\nyour folder (a saved game from playing, say)"),
        ('a file {"game.txt"} is written', "the program made it, or changed it"),
        ("no file is written", ""),
        ('the file {"game.txt"} contains {"round 4"}', "anywhere in the file (case ignored)"),
        ('the file {"game.txt"} contains:', "these lines in a row"),
        ("a saved game:", "these lines are in your program's save file before it starts\n"
                          "(between two lines of three quotes)"),
        ("there is no saved game", "the program starts without its save file"),
        ("a saved game is written", "the program made its save file, or changed it"),
        ("the saved game holds:", "these lines in a row in the save file"),
        ("no saved game is left", "the save file was removed, or emptied"),
        ("the program is started again", "stop it and start it over in the same folder,\nso the files it wrote are still there"),
    ],
}

STEPS_INTRO = "Steps you can use (after Given, When, Then or And):"
STEPS_OUTRO = """\
Colours in your program's output are ignored when matching, and shown in the report.
Each scenario runs your program from the start, in a copy of this folder.
A folder with a Poetry pyproject.toml that lists dependencies runs on its Poetry
environment (run poetry install first); else a .venv in the folder; else pyathy's
own Python (a Poetry project without dependencies runs there too)."""

BOLD, DIM, PLACEHOLDER, GREEN, RED = "1", "2", "36", "32", "31"
GHERKIN = re.compile(r"^(\s*)(Feature:|Scenario:|Given|When|Then|And|But)( .*)$")
# What a reason line quotes from the student's world, shown in the placeholder colour: a "quoted"
# or 'quoted' string (an apostrophe inside a word is not a quote), a file name, an ALL_CAPS constant
TOKEN = re.compile(r'"[^"]*"|(?<!\w)\'[^\']*\'(?!\w)|\b[\w.-]+\.(?:py|txt|sav|json|csv|feature|md)\b'
                   r'|\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b')


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

    def own(self, pattern):
        """A step pattern as its author wrote it: `{name} rolls {n:d}` -> `{name} rolls {n}`,
        each {field} in the placeholder colour, braces kept."""
        return re.sub(r"\{(\w*)(?::[^{}]*)?\}", lambda m: self.style(PLACEHOLDER, f"{{{m.group(1)}}}"), pattern)

    def paint(self, text, base=None, tokens=True):
        """`text` in the `base` colour (none: the default), with its quoted strings, file names
        and ALL_CAPS constants in the placeholder colour inside it (tokens=False: not)."""
        if not self.colour or not text:
            return text
        back, close = (f"\x1b[{base}m", "\x1b[0m") if base else ("", "")
        if tokens:  # a token closes the base colour and reopens it after itself
            text = TOKEN.sub(lambda m: f"{close}\x1b[{PLACEHOLDER}m{m.group(0)}\x1b[0m{back}", text)
        if not base:
            return text
        if text.endswith(back):  # a token at the end: its own reset already closed the line
            return back + text[:-len(back)]
        return f"{back}{text}{close}"

    def stanza(self, step, explanation):
        """`  <step>` on its own line, its explanation dim on the next, indented further
        (man-page style); an explanation written over two lines is joined into one."""
        out = ["  " + self.marked(step)]
        if explanation:
            out.append("      " + self.style(DIM, " ".join(explanation.splitlines())))
        return out

    def gherkin(self, text):
        """Feature/Scenario/When/Then/And in bold."""
        return "\n".join(f"{m.group(1)}{self.style(BOLD, m.group(2))}{m.group(3)}" if (m := GHERKIN.match(line))
                         else line for line in text.splitlines())


def help_text(styler):
    out = [INTRO, "", styler.style(BOLD, "usage:")]
    for command, explanation in USAGE:
        out += styler.stanza(command, explanation)
    out += ["", styler.style(BOLD, "options:")]
    for flag, explanation in OPTIONS:
        out += styler.stanza(flag, explanation)
    return "\n".join(out + ["", styler.gherkin(EXAMPLE), "", OUTRO])


def steps_text(styler, own):
    """The built-in step list, then the steps of each *steps.py in `own`: like a man page,
    each step on its own line and its explanation (dim) indented under it."""
    out = [STEPS_INTRO]
    for section, entries in STEPS.items():
        out += ["", styler.style(BOLD, section)]
        for step, explanation in entries:
            out += styler.stanza(step, explanation)
    for path, patterns in own:
        out += ["", styler.style(BOLD, "Your own steps") + styler.style(DIM, f"  ({path})")]
        for pattern in patterns:
            out += ["  " + styler.own(pattern)]
    return "\n".join(out + ["", STEPS_OUTRO])


# ---- did you mean: the closest step to a line no step matches --------------------

# The "(or: …)" forms of the steps above, so a line written the other way is suggested that way
ALSO = ["{Ann} rolls {4} and {6}", "{red} rolls {3} and answers {2}", "it is {red}'s turn",
        "{red} moves from {0} to {3}", "I answer {4}", "I type {4}", "I enter {4}"]
SUGGEST_RATIO = 0.75  # how alike the line and the suggestion must be (difflib ratio, 0..1)
WORD = re.compile(r'\S*\{[^{}]*\}\S*|"[^"]*"\S*|\S+')


def _fits(part, value, own):
    """Whether the line's `value` can stand in for a template word with placeholders: a number
    where the example is a number (`{6}`, own `{n:d}`), a "quoted" string where it is quoted, a
    .py file for `{files.py}`, one word for a name (`{red}`, own `{name:w}`), else anything."""
    def hole(m):
        inner = m.group(1)
        if own:
            kind = inner.partition(":")[2]
            return {"d": r"-?\d+", "w": r"\w+", "Dice": dice_pattern}.get(kind, r".+")
        if re.fullmatch(r"-?\d+", inner):
            return r"-?\d+"
        if inner.startswith('"'):
            return r'"[^"]*"'
        if inner.endswith(".py"):
            return r"\S+\.py"
        if re.fullmatch(r"\w+", inner):
            return r"\w+"
        return r".+"
    pattern = "".join(hole(m) if m.group(1) is not None else re.escape(m.group(2))
                      for m in re.finditer(r"\{([^{}]*)\}|([^{}]+)", part))
    return re.fullmatch(pattern, value, re.IGNORECASE) is not None


dice_pattern = r"\d+(?:\s*(?:\+|and|,)\s*\d+)*"


def _render(template, words, own=False):
    """`template` (`{red} rolls {6}`) with the line's own `words` where its placeholders line
    up (difflib on the words): ['red', 'rolled', '6'] -> 'red rolls 6'. A placeholder the
    line has no value for keeps its example value; an own step's `{name:w}` stays `{name}`."""
    parts = WORD.findall(template)
    keys = ["\0" if "{" in part else part.lower() for part in parts]
    out = []
    matcher = difflib.SequenceMatcher(None, keys, [w.lower() for w in words], autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        mine, theirs = parts[i1:i2], words[j1:j2]
        holes = [p for p in mine if "{" in p]
        if tag == "replace" and len(mine) == len(theirs):  # word for word: their values, our words
            out += [t if "{" in p and _fits(p, t, own) else p for p, t in zip(mine, theirs)]
        elif tag == "replace" and mine == holes and len(holes) == 1 and _fits(mine[0], " ".join(theirs), own):
            out.append(" ".join(theirs))  # one value of several words
        else:
            out += mine
    if own:
        return " ".join(re.sub(r"\{(\w*)(?::[^{}]*)?\}", r"{\1}", part) for part in out)
    return " ".join(re.sub(r"\{([^{}]*)\}", r"\1", part) for part in out)


def suggest(text, own=()):
    """The closest step to `text` (a feature line no step matches) as it would be written with
    the line's own values, or None when nothing is alike enough (SUGGEST_RATIO). Candidates: the
    built-ins (STEPS and ALSO) and the folder's own step patterns."""
    templates = [(s, False) for entries in STEPS.values() for s, _ in entries]
    templates += [(s, False) for s in ALSO] + [(s, True) for s in own]
    words = WORD.findall(text.strip())
    best, score = None, 0.0
    for template, mine in templates:
        rendered = _render(template, words, mine)
        ratio = difflib.SequenceMatcher(None, rendered.lower(), text.strip().lower()).ratio()
        if ratio > score:
            best, score = rendered, ratio
    return best if score >= SUGGEST_RATIO else None


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
        found.append((str(path), [entry[0] for entry in steps.REGISTERED[before:]]))
    return found
