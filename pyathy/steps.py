"""The built-in steps (PRD section 4). Each works after Given, When, Then, And or But.

Matching ignores case and trailing spaces, unless the step says "exactly".
"""

import os
import re
import shlex

import pytest
from pytest_bdd import given, parsers, then, when

from .program import Program, ProgramError


def step(pattern):
    """Register one step under all three keywords."""
    parser = parsers.re(pattern)

    def register(fn):
        return given(parser, stacklevel=2)(when(parser, stacklevel=2)(then(parser, stacklevel=2)(fn)))

    return register


def values(text):
    """'-3' -> ['-3'];  '"Ada Lovelace"' -> ['Ada Lovelace'];  '1, 2, 3' -> ['1', '2', '3']."""
    text = text.strip()
    if re.fullmatch(r"(?:an? )?empty string|with (?:an? )?empty string|enter|nothing", text):
        return [""]
    found = re.findall(r'"([^"]*)"|([^,]+)', text)
    return [quoted if quoted or not bare else bare.strip() for quoted, bare in found]


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


@step(r"the program (?P<name>[\w./-]+\.py)")
def the_program(program, name):
    program.app = os.path.join(os.path.dirname(program.app), name)


@step(r"I start the program")
def start(program):
    program.settle()


@step(r"I run the program(?: with (?P<args>.+))?")
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


@step(r"the program may take (?P<seconds>\d+(?:\.\d+)?) seconds?")
def may_take(program, seconds):
    """A slow program: wait up to this long for it to print or ask something (default 10)."""
    program.timeout = float(seconds)
    program.run_limit = max(program.run_limit, float(seconds))


# ---- typing --------------------------------------------------------------------

@step(r"I (?:input|answer|type|enter) (?P<text>.+)")
def type_(program, text):
    program.type(*values(text))


# ---- randomness ----------------------------------------------------------------

@step(r"I roll (?P<faces>-?\d+(?:\s*(?:,|\+|and)\s*-?\d+)*)")
def roll(program, faces):
    program.roll(*(int(f) for f in re.findall(r"-?\d+", faces)))


@step(r'the random (?:choice|pick|number) is (?P<text>.+)')
def choose(program, text):
    for v in values(text):
        program.choose(int(v) if re.fullmatch(r"-?\d+", v) else v)


# ---- checking ------------------------------------------------------------------

def fail(program, message):
    waiting = program.waiting_for()
    where = (f"the program is waiting for {waiting}" if waiting
             else f"the program crashed:\n{program.crash}" if program.crash
             else "the program has ended")
    raise ProgramError(f"{message}\n{where}\n{program.tail()}")


@step(r'(?P<exact>exactly )?"(?P<text>[^"]*)" is printed(?: (?P<n>\d+) times?)?')
def printed(program, exact, text, n):
    out = program.settle()
    haystack, needle = (out, text) if exact else (norm(out), norm(text))
    count = haystack.count(needle)
    if n is None and count == 0:
        fail(program, f'expected "{text}" to be printed, but it was not')
    if n is not None and count != int(n):
        fail(program, f'expected "{text}" to be printed {n} times, but it was printed {count} times')


@step(r'"(?P<text>[^"]*)" is not printed')
def not_printed(program, text):
    if norm(text) in norm(program.settle()):
        fail(program, f'expected "{text}" NOT to be printed, but it was')


@step(r'the output starts with "(?P<text>[^"]*)"')
def starts_with(program, text):
    if not norm(program.settle()).startswith(norm(text)):
        fail(program, f'expected the output to start with "{text}"')


@step(r"the output shows:?")
def shows(program, docstring):
    want = [line.rstrip().lower() for line in docstring.splitlines()]
    have = [line.rstrip().lower() for line in program.settle().splitlines()]
    for i in range(len(have) - len(want) + 1):
        if have[i:i + len(want)] == want:
            return
    shown = "\n".join(f"    | {line}" for line in docstring.splitlines())
    fail(program, f"expected these lines, in a row:\n{shown}")


@step(r'the program asks "(?P<text>[^"]*)"')
def asks(program, text):
    program.settle()
    if program.request is None or program.request[0] != "input":
        fail(program, f'expected the program to ask "{text}"')
    tail = norm(program.output)[-(len(text) + 200):]
    if norm(text) not in tail:
        fail(program, f'expected the program to ask "{text}"')


@step(r"the program ends")
def ends(program):
    program.settle()
    if program.state == "crashed":
        fail(program, "expected the program to end, but it crashed")
    if program.state != "exited":
        fail(program, "expected the program to end")


@step(r"the program is still running")
def running(program):
    program.settle()
    if program.state != "waiting":
        fail(program, "expected the program to still be running")


# ---- after every scenario ------------------------------------------------------

def pytest_bdd_after_scenario(request, feature, scenario):
    """A roll or input the scenario scripted but the program never used is a failure."""
    program = request.getfixturevalue("program")
    if program.state == "new":
        return
    program.settle()
    left = []
    if program.dice:
        left.append(f"rolls {', '.join(map(str, program.dice))}")
    if program.inputs:
        left.append(f"inputs {', '.join(repr(i) for i in program.inputs)}")
    if left:
        fail(program, f"the program never used the scripted {' and '.join(left)}")


@step(r'the file "(?P<name>[^"]+)" contains "(?P<text>[^"]*)"')
def file_contains(program, name, text):
    program.settle()
    path = os.path.join(program.workdir or "", name)
    if not os.path.exists(path):
        fail(program, f'expected a file "{name}", but the program did not write one')
    with open(path, encoding="utf-8", errors="replace") as f:
        if norm(text) not in norm(f.read()):
            fail(program, f'expected the file "{name}" to contain "{text}"')


# ---- a features folder's own steps ---------------------------------------------

def pytest_collection_modifyitems(session, config, items):
    """A features folder may ship its own steps: every *steps.py next to a .feature file is
    loaded, so its steps (written with `from pyathy.steps import step`) work like built-ins."""
    import importlib.util
    import pathlib

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
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        import sys
        writes, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # no __pycache__ in their folder
        try:
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = writes
        config.pluginmanager.register(module, name)
