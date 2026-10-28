"""The built-in steps (PRD section 4). Each works after Given, When, Then, And or But.

Matching ignores case and trailing spaces, unless the step says "exactly", and always ignores
the colour codes a program prints (program.settle(), .text and .turn_output() are plain).
"""

import ast
import importlib.util
import os
import pathlib
import re
import shlex
import sys

import pytest
from pytest_bdd import given, parsers, then, when

from .program import Program, ProgramError, constant, plain, save_file


REGISTERED = []  # (pattern, file, parser, function) of every step, for `pyathy steps` and turn tables


def dice(text):
    """'6' -> [6];  '4+6' -> [4, 6];  '4 and 6' -> [4, 6]."""
    return [int(f) for f in re.findall(r"\d+", text)]


dice.pattern = r"\d+(?:\s*(?:\+|and|,)\s*\d+)*"
TYPES = {"Dice": dice}


def step(*patterns):
    """Register one step, written as a Cucumber-style pattern: `"{name} rolls {n:d}"` ({n:d} a
    whole number, {name:w} one word, {text} anything). Several patterns share one function;
    a field a pattern leaves out gets the function's default."""
    return _register([(p, parsers.cfparse(p, extra_types=TYPES)) for p in patterns], sys._getframe(1).f_code.co_filename)


def _re(*patterns):
    """A built-in whose pattern is a regular expression (an optional part, an alternative)."""
    return _register([(p, parsers.re(p)) for p in patterns], sys._getframe(1).f_code.co_filename)


def _register(parsed, file):
    def register(fn):
        for pattern, parser in parsed:
            REGISTERED.append((pattern, file, parser, fn))
            given(parser, stacklevel=2)(when(parser, stacklevel=2)(then(parser, stacklevel=2)(fn)))
        return fn

    return register


EMPTY = re.compile(r"enter|nothing|(?:with )?(?:an? )?empty (?:string|line)", re.IGNORECASE)


def values(text):
    """'-3' -> ['-3'];  '"Ada Lovelace"' -> ['Ada Lovelace'];  '1, 2, 3' -> ['1', '2', '3'].
    An unquoted `enter`, `nothing` or `an empty string` (whole, or one item of the list) is the
    empty line, in any case; quoted, `"enter"` is the word."""
    found = re.findall(r'\s*"([^"]*)"\s*|([^,]+)', text.strip())
    return [quoted if quoted or not bare else value(bare.strip()) for quoted, bare in found]


def value(bare):
    return "" if EMPTY.fullmatch(bare) else bare


def norm(text):
    return "\n".join(line.rstrip() for line in text.splitlines()).lower()


# ---- the program -------------------------------------------------------------

@pytest.fixture
def program(request):
    app = os.environ.get("PYATHY_APP", os.path.join(os.getcwd(), "main.py"))
    p = Program(app)
    request.node.pyathy_program = p  # the report prints its transcript after the scenario
    yield p
    p.close()


@_re(r"the program (?P<name>[\w./-]+\.py)")
def the_program(program, name):
    program.app = os.path.join(os.path.dirname(program.app), name)


@step("I start the program")
def start(program):
    program.settle()


@_re(r"I run the program(?: with (?P<args>.+))?")
def run_with(program, args):
    """`I run the program with photos/ --all`: starts it like `python main.py photos/ --all`.
    Quote an argument with spaces in it: `with "my file.txt"`."""
    if program.state != "new":
        raise ProgramError('"I run the program with ..." must come before any step that starts the'
                           " program (an input, a roll, a check): it has already started")
    try:
        program.args = shlex.split(args or "")
    except ValueError as e:
        raise ProgramError(f"could not read the arguments {args!r}: {e}") from None
    program.settle()


@_re(r"(?P<name>[\w./-]+\.py) has (?P<constant>[A-Za-z_]\w*) = (?P<text>.+)")
def has_constant(program, name, constant, text):
    """`main.py has DEBUG = True`: before the program starts, the scenario's copy of main.py
    gets this value in its top-level `DEBUG = …` (the file in your folder stays as it is)."""
    if program.state != "new":
        raise ProgramError(f'"{name} has {constant} = …" must come before any step that starts the'
                           " program (an input, a roll, a check): it has already started")
    try:
        ast.parse(text, mode="eval")
    except SyntaxError:
        raise ProgramError(f"{text} is not a Python value, so {constant} cannot be set to it") from None
    program.write_file(name, with_value(source_of(program, name), name, constant, text))


@_re(r"(?P<name>[\w./-]+\.py) has an? (?P<constant>[A-Za-z_]\w*) setting")
def has_setting(program, name, constant):
    """`main.py has a DEBUG setting`: main.py has a top-level `DEBUG = …` (outside any function).
    Only reads the file (or the copy an earlier step wrote), so it may come before or after the start."""
    top_level_value(source_of(program, name), name, constant)


def source_of(program, name):
    """The text the copy will get for this file: what a step already put there, else the file."""
    staged = [text for staged_name, text in program.files if staged_name == name]
    if staged:
        return staged[-1]
    path = os.path.join(os.path.dirname(program.app), name)
    if not os.path.isfile(path):
        raise ProgramError(f"there is no {name} in {os.path.dirname(program.app)}")
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def top_level_value(source, name, constant, why=""):
    """The value node of the last top-level `constant = …` (plain or annotated) in `source`;
    a ProgramError naming the fix when there is none. `why` follows the "at the top" part."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ProgramError(f"{name} has a syntax error on line {e.lineno}, so {constant} could not be found: {e.msg}") from None
    node = None
    for statement in tree.body:
        targets = (statement.targets if isinstance(statement, ast.Assign)
                   else [statement.target] if isinstance(statement, ast.AnnAssign) else [])
        if any(isinstance(t, ast.Name) and t.id == constant for t in targets) and statement.value is not None:
            node = statement.value
    if node is None:
        raise ProgramError(f"{name} has no {constant} = … at the top (outside any function){why}:"
                           f" put {constant} = … at the top of {name}")
    return node


def with_value(source, name, constant, text):
    """`source` with the value of its last top-level `constant = …` replaced by `text`."""
    node = top_level_value(source, name, constant, ", so the scenario cannot set it")
    lines = source.splitlines(keepends=True)
    # ast columns count UTF-8 bytes
    head = lines[node.lineno - 1].encode()[:node.col_offset].decode()
    tail = lines[node.end_lineno - 1].encode()[node.end_col_offset:].decode()
    return "".join(lines[:node.lineno - 1] + [head + text + tail] + lines[node.end_lineno:])


@_re(r"the program may take (?P<seconds>\d+(?:\.\d+)?) seconds?")
def may_take(program, seconds):
    """A slow program: wait up to this long for it to print or ask something (default 10)."""
    program.timeout = float(seconds)
    program.run_limit = max(program.run_limit, float(seconds))


# ---- typing --------------------------------------------------------------------

@_re(r"I (?:input|answer|type|enter) (?P<text>.+)")
def type_(program, text):
    typed = values(text)
    program.players += [t for t in typed if t.isalpha() and not known(program, t)]
    program.type(*typed)


# ---- randomness ----------------------------------------------------------------

@_re(r"I roll (?P<faces>-?\d+(?:\s*(?:,|\+|and)\s*-?\d+)*)")
def roll(program, faces):
    program.roll(*(int(f) for f in re.findall(r"-?\d+", faces)))


@_re(r'the random (?:choice|pick|number) is (?P<text>.+)')
def choose(program, text):
    for v in values(text):
        program.choose(int(v) if re.fullmatch(r"-?\d+", v) else v)


# ---- turns ----------------------------------------------------------------------

def known(program, name):
    return any(p.lower() == name.lower() for p in program.players)


def announced(line, players):
    """The player a line announces, or None: it names exactly one of them and has no digits
    ("Player red:", "***** Timothy's turn *****"). Boards and player lists carry numbers."""
    if re.search(r"\d", line):
        return None
    named = [p for p in players if re.search(rf"\b{re.escape(p)}\b", line, re.IGNORECASE)]
    return named[0] if len(named) == 1 else None


def announcements(program, since=0):
    """[(line, player)] of every turn announcement in the output from `since` on."""
    found = []
    for line in plain(program.output[since:]).splitlines():
        player = announced(line, program.players)
        if player:
            found.append((line.strip(), player))
    return found


def check_turn(program, name):
    """It is this player's turn: the last announcement names them."""
    last = announcements(program)[-1:]
    if not last:
        fail(program, f"expected it to be {name}'s turn, but no line announced anyone's turn (one naming the"
                      f" player and no other, without digits, like 'Player {name}:')")
    if last[0][1].lower() != name.lower():
        fail(program, f"expected it to be {name}'s turn; the last announcement was {last[0][0]!r}")


def take_turn(program, name, dice):
    """Enter (if the program is waiting for it), then the dice show these faces, after checking
    that it is this player's turn."""
    program.settle()
    if not known(program, name):
        program.players.append(name)
    if program.state != "waiting":
        fail(program, f"expected {name} to roll, but it cannot:")
    check_turn(program, name)
    program.turn(*dice)


def asked_after_roll(program):
    """The program is waiting for an answer to a question of this turn (no turn announced since the roll)."""
    program.settle()
    return program.state == "waiting" and program.request[0] == "input" and not announcements(program, program.turn_start)


def answer_after_roll(program, name, answer):
    if not asked_after_roll(program):
        since = announcements(program, program.turn_start)
        went = f"went on to {since[-1][1]}'s turn" if since else "asked nothing"
        fail(program, f"{name} rolled and should have been asked something (to answer {answer!r}), but the program {went}")
    program.type(*values(answer))


@step("the players are {names}")
def players(program, names):
    """`the players are red and green`: the names a turn announcement may use (otherwise:
    the names the scenario typed or rolled for)."""
    program.players += [n for n in re.split(r", | and |,", names) if n.strip() and not known(program, n.strip())]


@step("{name:w} rolls {dice:Dice}")
def turn(program, name, dice):
    take_turn(program, name, dice)


@step("{name:w} rolls {dice:Dice} and picks {answer}", "{name:w} rolls {dice:Dice} and answers {answer}")
def turn_and_answer(program, name, dice, answer):
    take_turn(program, name, dice)
    answer_after_roll(program, name, answer)


@step("these turns are played {n:d} times:", "these turns are played {n:d} time:")
def turns(program, n, datatable):
    """A table with one step per row (`| red rolls 5 |`), run in order, this many times."""
    for _ in range(n):
        for row in datatable:
            run_step(program, row[0].strip())


def run_step(program, text):
    """Run one step by its text, as a table row: the last registered step that matches it
    (a features folder's own steps come after the built-ins, so theirs win)."""
    for pattern, _, parser, fn in reversed(REGISTERED):
        if parser.is_matching(text):
            return fn(program, **parser.parse_arguments(text))
    raise ProgramError(f"no step matches the table row {text!r}")


@step("{name:w}'s turn is announced", "it is {name:w}'s turn")
def turn_announced(program, name):
    program.settle()
    if not known(program, name):
        program.players.append(name)
    if not any(p.lower() == name.lower() for _, p in announcements(program)):
        fail(program, f"expected a line announcing {name}'s turn: one naming {name} (and no other player),"
                      f" without digits, like 'Player {name}:'")


MOVE = re.compile(r"->|→|=>|\bto\b")


def moves(text):
    """Every move a text reports: a line with exactly two numbers, 'to' or an arrow between them."""
    found = []
    for line in text.splitlines():
        numbers = list(re.finditer(r"\b\d+\b", line))
        if len(numbers) == 2 and MOVE.search(line, numbers[0].end(), numbers[1].start()):
            found.append((int(numbers[0].group()), int(numbers[1].group())))
    return found


@step("a pawn moves from {a:d} to {b:d}", "{name:w} moves from {a:d} to {b:d}")
def moved(program, a, b, name="a pawn"):
    program.settle()
    if (a, b) not in moves(program.turn_output()):
        fail(program, f"expected a line of this turn to say {name} moves from {a} to {b}: the two squares in"
                      f" that order, like 'Pawn moving from {a} to {b}.'")


@step("nothing moves")
def nothing_moved(program):
    program.settle()
    found = moves(program.turn_output())
    if found:
        fail(program, f"expected nothing to move this turn, but a line says {found[0][0]} to {found[0][1]}")


# ---- checking ------------------------------------------------------------------

def fail(program, message):
    waiting = program.waiting_for()
    where = (f"the program is waiting for {waiting}" if waiting
             else f"the program crashed:\n{program.crash}" if program.crash
             else "the program has ended")
    raise ProgramError(f"{message}\n{where}\n{program.tail()}")


@_re(r'(?P<exact>exactly )?"(?P<text>[^"]*)" is printed(?: (?P<n>\d+) times?)?')
def printed(program, exact, text, n):
    out = program.settle()
    haystack, needle = (out, text) if exact else (norm(out), norm(text))
    count = haystack.count(needle)
    if n is None and count == 0:
        fail(program, f'expected "{text}" to be printed, but it was not')
    if n is not None and count != int(n):
        fail(program, f'expected "{text}" to be printed {n} times, but it was printed {count} times')


@_re(r'"(?P<text>[^"]*)" is not printed')
def not_printed(program, text):
    if norm(text) in norm(program.settle()):
        fail(program, f'expected "{text}" NOT to be printed, but it was')


@_re(r'the output starts with "(?P<text>[^"]*)"')
def starts_with(program, text):
    if not norm(program.settle()).startswith(norm(text)):
        fail(program, f'expected the output to start with "{text}"')


@_re(r"the output shows:?")
def shows(program, docstring):
    want = [line.rstrip().lower() for line in docstring.splitlines()]
    have = [line.rstrip().lower() for line in program.settle().splitlines()]
    for i in range(len(have) - len(want) + 1):
        if have[i:i + len(want)] == want:
            return
    shown = "\n".join(f"    | {line}" for line in docstring.splitlines())
    fail(program, f"expected these lines, in a row:\n{shown}")


def printed_lines(program):
    """Every line the program printed in this run, without the answers typed into it."""
    program.settle()
    out, pieces, at = program.output, [], 0
    for start, end in program.typed:
        pieces.append(out[at:start])
        at = end
    pieces.append(out[at:])
    return plain("".join(pieces)).splitlines()


@_re(r'the line with "(?P<text>[^"]+)" also has "(?P<also>[^"]*)"')
def line_also_has(program, text, also):
    """The last line printed with the first text in it also has the second (case ignored)."""
    found = [line for line in printed_lines(program) if text.lower() in line.lower()]
    if not found:
        fail(program, f'expected a line with "{text}", but no line printed has it')
    if also.lower() not in found[-1].lower():
        fail(program, f'expected the last line with "{text}" to also have "{also}", but it is:\n'
                      f"    | {found[-1].rstrip()}")


BORDER = re.compile(r"[\s\-=+:─━│┃|┌┐└┘├┤┬┴┼╭╮╯╰╔╗╚╝╠╣╦╩╬═║]+")
RULE = re.compile(r"[-=─━═]")  # a border line has one of these; a row of empty cells has not


def cells(line):
    """The cells of a table row (split on │ or |; the bars at both ends left off), else None."""
    line = line.strip()
    if "│" not in line and "|" not in line:
        return None
    parts = [cell.strip() for cell in re.split(r"[│|]", line)]
    if line[0] in "│|":
        parts = parts[1:]
    if line[-1] in "│|":
        parts = parts[:-1]
    return parts


def tables(lines):
    """Every table printed: [rows], each row its cells. A table is lines in a row with │ or |
    in them; border lines (├──┼──┤, +---+) are skipped."""
    found, rows = [], []
    for line in lines + [""]:
        if BORDER.fullmatch(line.strip()) and RULE.search(line):
            continue
        row = cells(line)
        if row is None:
            if rows:
                found.append(rows)
            rows = []
        else:
            rows.append(row)
    return found


def cell_under(program, row_text, column):
    """(the row's cells, the cell under `column`) in the last printed table with a header cell
    `column`: the row is the first one under the header with a cell that is `row_text`, else
    one with a cell that has it in it (case ignored)."""
    for table in reversed(tables(printed_lines(program))):
        heads = [i for i, row in enumerate(table) if column.lower() in (c.lower() for c in row)]
        if heads:
            break
    else:
        fail(program, f'expected a table with a column "{column}" (cells split by │ or |), but none was printed')
    header = table[heads[-1]]
    at = [c.lower() for c in header].index(column.lower())
    below = table[heads[-1] + 1:]
    want = row_text.lower()
    rows = ([row for row in below if want in (c.lower() for c in row)]
            or [row for row in below if any(want in c.lower() for c in row)])
    if not rows:
        fail(program, f'expected a row with "{row_text}" in the table with the column "{column}", but there is none')
    return rows[0], rows[0][at] if at < len(rows[0]) else ""


@_re(r'the "(?P<row>[^"]+)" row has (?:"(?P<want>[^"]*)"|nothing) under "(?P<column>[^"]+)"')
def row_has(program, row, want, column):
    """In the last table printed with a `column` header cell, the cell of the `row` row under it
    is `want` (case ignored), or empty ("nothing")."""
    found, have = cell_under(program, row, column)
    want = want or ""
    if have.lower() != want.lower():
        what = f'"{want}"' if want else "nothing"
        fail(program, f'expected the "{row}" row to have {what} under "{column}", but it has "{have}":\n'
                      f"    | {' | '.join(found)}")


@_re(r'the program asks "(?P<text>[^"]*)"')
def asks(program, text):
    program.settle()
    if program.request is None or program.request[0] != "input":
        fail(program, f'expected the program to ask "{text}"')
    tail = norm(program.text)[-(len(text) + 200):]
    if norm(text) not in tail:
        fail(program, f'expected the program to ask "{text}"')


@step('"{text}" is refused with a message', '"" is refused with a message')
def refused(program, text=""):
    """After typing it (`""`: pressing enter), a message was printed and the same question was
    asked again. The message is a line printed between the answer and the repeated question that
    is not part of what the program prints every time it asks that question, such as its menu."""
    program.settle()
    out = program.output  # raw: `typed` indexes into it; what is read from it is made plain
    typed = program.typed
    tries = [k for k, (start, end) in enumerate(typed) if out[start:end] == text]
    if not tries:
        fail(program, f"{text!r} was never typed")
    # what the program printed before each answer, and after the last one
    blocks = [plain(out[a:b]) for a, b in zip([0] + [end for _, end in typed],
                                               [start for start, _ in typed] + [len(out)])]
    for k in tries:
        question = plain(question_before(out, typed[k][0]))
        after = blocks[k + 1]
        asked_again = bool(question) and question in after
        if not asked_again:
            continue
        # the lines that come before this question every time it is asked up to now (a menu)
        leads = [lead_in(block, question) for block in blocks[:k + 2] if question in block]
        same = 0
        while all(len(lead) > same for lead in leads) and len({lead[-1 - same] for lead in leads}) == 1:
            same += 1
        message = leads[-1][:len(leads[-1]) - same]
        if any(line != question for line in message):
            return
    if not asked_again:
        fail(program, f"after {text!r} was typed, the same question should be asked again ({question!r})")
    fail(program, f"after {text!r} was typed, a message should be printed before the question is asked again")


def lead_in(block, question):
    """The non-empty lines printed before the last time `question` is asked in `block` (text
    printed on the question's own line, before it, counts as a line)."""
    return [line.strip() for line in block[:block.rfind(question)].splitlines() if line.strip()]


def question_before(out, at):
    """The prompt before an answer typed at `at`: the line it was typed on, else the line above."""
    line_start = out.rfind("\n", 0, at) + 1
    question = out[line_start:at].strip()
    if not question and line_start > 0:
        question = out[out.rfind("\n", 0, line_start - 1) + 1:line_start - 1].strip()
    return question


@step("the program ends")
def ends(program):
    program.settle()
    if program.state == "crashed":
        fail(program, "expected the program to end, but it crashed")
    if program.state != "exited":
        fail(program, "expected the program to end")


@step("the program is still running")
def running(program):
    program.settle()
    if program.state != "waiting":
        fail(program, "expected the program to still be running")


# ---- after every scenario ------------------------------------------------------

def unused(program, when="the program never used"):
    """A roll or input the scenario scripted but the program never used is a failure."""
    program.settle()
    left = []
    if program.dice:
        left.append(f"rolls {', '.join(map(str, program.dice))}")
    if program.inputs:
        left.append(f"inputs {', '.join(repr(i) for i in program.inputs)}")
    if left:
        fail(program, f"{when} the scripted {' and '.join(left)}")


def pytest_bdd_after_scenario(request, feature, scenario):
    program = request.getfixturevalue("program")
    if program.state != "new":
        unused(program)


# ---- files ---------------------------------------------------------------------

NAME = r'(?P<name>"[^"]+"|[A-Z][A-Z0-9_]*)'  # "game.txt", or a constant of the program: SAVE_FILE_NAME


def file_name(program, name):
    """The file a Files step names: a quoted literal, or an ALL_CAPS constant read from the
    program (`SAVE_FILE_NAME = "game.txt"` at the top of main.py or another module, else the
    one file the program writes), so the scenario follows the program when the file is renamed."""
    if name.startswith('"'):
        return name[1:-1]
    return constant(program.app, name)


@_re(rf'a file {NAME} containing "(?P<text>[^"]*)"')
def file_with_line(program, name, text):
    """A one-line file in the program's folder before it starts (written into the copy)."""
    program.write_file(file_name(program, name), text + "\n")


@_re(rf'a file {NAME}')
def empty_file(program, name):
    """An empty file in the program's folder before it starts, its folders made too."""
    program.write_file(file_name(program, name), "")


@_re(rf'a file {NAME} with:?')
def file_with(program, name, docstring):
    """The same with several lines, between two lines of three quotes."""
    program.write_file(file_name(program, name), docstring + "\n")


@step("there is no file {name}")
def no_file(program, name):
    """The program starts without this file, whatever is in the folder (a saved game from
    playing, say). A constant the program does not have yet names no file: nothing to leave out."""
    try:
        program.remove_file(file_name(program, name))
    except ProgramError:
        if name.startswith('"'):
            raise


def file_text(program, name):
    program.settle()
    path = os.path.join(program.workdir or "", name)
    if not os.path.isfile(path):
        fail(program, f'expected a file "{name}", but the program did not write one')
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


@_re(rf'a file {NAME} is written')
def file_written(program, name):
    name = file_name(program, name)
    program.settle()
    if name not in program.changed_files():
        if os.path.isfile(os.path.join(program.workdir or "", name)):
            fail(program, f'expected the program to write the file "{name}", but it is as it was')
        fail(program, f'expected the program to write a file "{name}", but it did not'
             f"{_wrote(program)}")


@step("no file is written")
def no_file_written(program):
    program.settle()
    if program.changed_files():
        fail(program, f"expected the program to write no file{_wrote(program)}")


def _wrote(program):
    written = program.changed_files()
    return f"; it wrote: {', '.join(written)}" if written else "; it wrote no file"


@_re(rf'the file {NAME} contains "(?P<text>[^"]*)"')
def file_contains(program, name, text):
    name = file_name(program, name)
    if norm(text) not in norm(file_text(program, name)):
        fail(program, f'expected the file "{name}" to contain "{text}"')


@_re(rf'the file {NAME} contains:?')
def file_shows(program, name, docstring):
    """These lines in a row, like `the output shows:`."""
    lines_in_a_row(program, file_name(program, name), docstring)


def lines_in_a_row(program, name, docstring):
    want = [line.rstrip().lower() for line in docstring.splitlines()]
    have = [line.rstrip().lower() for line in file_text(program, name).splitlines()]
    for i in range(len(have) - len(want) + 1):
        if have[i:i + len(want)] == want:
            return
    shown = "\n".join(f"    | {line}" for line in docstring.splitlines())
    fail(program, f'expected the file "{name}" to contain these lines, in a row:\n{shown}')


# ---- a saved game: the file the program saves to, found in the program -------------

def saved_file(program):
    """The name of the file the program saves its game to: what a SAVE_FILE_NAME constant
    names, else the one file the program opens for writing (read from the code, not run)."""
    return save_file(program.app)


@_re(r"a saved game:?")
def saved_game(program, docstring):
    """These lines are in the program's save file before it starts."""
    program.write_file(saved_file(program), docstring + "\n")


@step("there is no saved game")
def no_saved_game(program):
    """The program starts without its save file, whatever playing left in the folder. A program
    that saves nothing yet has nothing to leave out."""
    try:
        program.remove_file(saved_file(program))
    except ProgramError:
        pass


@_re(r"the saved game holds:?")
def saved_game_holds(program, docstring):
    """The save file has these lines in a row, like `the file "game.txt" contains:`."""
    lines_in_a_row(program, saved_file(program), docstring)


@step("a saved game is written")
def saved_game_written(program):
    file_written(program, '"' + saved_file(program) + '"')


@step("no saved game is left")
def no_saved_game_left(program):
    """The save file was removed, or emptied (so the next start is a new game)."""
    name = saved_file(program)
    program.settle()
    path = os.path.join(program.workdir or "", name)
    if os.path.isfile(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            if f.read().strip():
                fail(program, f'expected the save file "{name}" to be removed (or emptied), but it still holds a game')


@step("the program is started again")
def started_again(program):
    """Stop the program and start it again in the same folder, with the files it wrote still
    there. The steps after this one read the new run; the report shows both."""
    if program.state != "new":
        unused(program, 'before "the program is started again", the program never used')
    program.restart()


# ---- a features folder's own steps ---------------------------------------------

def load_own_steps(path):
    """Import one *steps.py (without writing a __pycache__ into their folder); returns the module."""
    name = f"pyathy_own_steps_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    writes, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = writes
    return module


def pytest_collection_modifyitems(session, config, items):
    """A features folder may ship its own steps: every *steps.py next to a .feature file is
    loaded, so its steps (written with `from pyathy.steps import step`) work like built-ins."""
    from pytest_bdd.scenario import scenario_wrapper_template_registry

    folders = set()
    for item in items:
        scenario = scenario_wrapper_template_registry.get(getattr(item, "obj", None))
        if scenario is not None:
            folders.add(pathlib.Path(scenario.feature.filename).parent)
    for path in sorted(p for folder in folders for p in folder.glob("*steps.py")):
        name = f"pyathy_own_steps_{abs(hash(str(path)))}"
        if config.pluginmanager.has_plugin(name):
            continue
        config.pluginmanager.register(load_own_steps(path), name)
