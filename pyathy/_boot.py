"""Runs INSIDE the child process: starts the student's game with its input and randomness scripted.

You never run or import this file yourself: harness/scripted_game.py starts it as

    python _game_boot.py <main.py> [args...]

with the environment variables SCRIPTED_GAME_ADDRESS, SCRIPTED_GAME_KEY and
SCRIPTED_GAME_SIDES set. Before the student's code loads it:

- connects to the test over multiprocessing.connection (a Unix socket on Linux/macOS,
  a named pipe on Windows; no TCP port, no firewall prompt);
- replaces input() and sys.stdin (readline, read, readlines, iteration) with a call that
  asks the test what to type and BLOCKS until the test answers;
- replaces the random calls a game draws with (randint, randrange, choice, choices,
  random, uniform, sample, shuffle), on the random module AND on every random.Random /
  SystemRandom instance, plus secrets.randbelow / secrets.choice. Each call asks the test
  what it returns: a face for a die (exactly SIDES consecutive integers: randint(1, 6),
  randrange(6)), or an exact value for anything else (choice(string.ascii_letters) -> "q");
- makes time.sleep return at once, telling the test how long it was asked to wait;
- replaces sys.stdout / sys.stderr with a writer that sends every write to the test as
  it happens, so buffering never reorders anything, and os.system("clear") (which
  writes to the real terminal, not to sys.stdout) cannot get mixed in;
- then runs the game like `python main.py` would: __name__ == "__main__", sys.argv set,
  the game folder first on sys.path.

When the test is done it answers a waiting call with "stop", and this process ends with
os._exit(0) from inside that call, so no try/except in the student's code can catch it.

Stdlib only, Python 3.9+ (tested on 3.9, 3.10 and 3.14).
"""

import builtins
import os
import random
import runpy
import sys
import threading
import traceback
from multiprocessing.connection import Client

APP = os.path.abspath(sys.argv[1])
FOLDER = os.path.dirname(APP)
SIDES = int(os.environ.get("SCRIPTED_GAME_SIDES", "6"))
HERE = os.path.dirname(os.path.abspath(__file__))

conn = Client(os.environ["SCRIPTED_GAME_ADDRESS"], authkey=bytes.fromhex(os.environ["SCRIPTED_GAME_KEY"]))
send_lock = threading.Lock()     # one message at a time on the wire
request_lock = threading.Lock()  # one question (input or die) waiting for its answer at a time


def send(message):
    """The test hung up (it is done with this game): end here, so nothing can catch it."""
    with send_lock:
        try:
            conn.send(message)
        except OSError:
            os._exit(0)


def ask(message):
    """Send a request and block until the test answers. "stop" ends the process right here."""
    with request_lock:
        try:
            send(message)
            reply = conn.recv()
        except (EOFError, OSError):
            os._exit(0)
        if reply[0] == "stop":
            os._exit(0)
        return reply


# ---- output -----------------------------------------------------------------

class Writer:
    """sys.stdout / sys.stderr: every write goes to the test at once."""

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, name):
        self.name = name

    def write(self, text):
        text = str(text)
        if text:
            send(("out", text))
        return len(text)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def flush(self):
        pass

    def isatty(self):
        return False

    def fileno(self):
        raise OSError("scripted output has no file descriptor")

    def readable(self):
        return False

    def writable(self):
        return True


# ---- input ------------------------------------------------------------------

def typed(prompt, how):
    reply = ask(("input", prompt, how))
    return reply[1]


def fake_input(prompt=""):
    return typed(str(prompt), "input()")


class Stdin:
    """sys.stdin: every line read is one question to the test."""

    encoding = "utf-8"
    errors = "replace"

    def readline(self, size=-1):
        return typed("", "sys.stdin.readline()") + "\n"

    def read(self, size=-1):
        return typed("", "sys.stdin.read()") + "\n"

    def readlines(self, hint=-1):
        return [self.readline()]

    def __iter__(self):
        return self

    def __next__(self):
        return self.readline()

    def isatty(self):
        return False

    def readable(self):
        return True

    def fileno(self):
        raise OSError("scripted input has no file descriptor")

    def close(self):
        pass


# ---- randomness ---------------------------------------------------------------
#
# Every random call asks the test: ("random", description, is_die, menu, kind).
#   menu: the options as a range, or as a list of their repr()s (None when there are too many)
#   kind: "pick" (one of the options), "float", "shuffle" or "sample"
# The test answers ("face", n): the n-th smallest option of a die; ("value", v): exactly v;
# ("index", i): options[i], in the program's own order;
# or ("first",): the first option (a suite that lets unscripted randomness through).

def is_die(options):
    """Exactly SIDES consecutive integers, in any order."""
    if len(options) != SIDES:
        return False
    options = list(options)
    if not all(type(o) is int for o in options):
        return False
    low = min(options)
    return sorted(options) == list(range(low, low + SIDES))


def menu(options):
    if isinstance(options, range):
        return options
    return [repr(o) for o in options] if len(options) <= 500 else None


def over(options):
    """'52 letters', "['Ann', 'Bob']", '30 items'."""
    if isinstance(options, str) or all(isinstance(o, str) and len(o) == 1 for o in options):
        letters = all(str(o).isalpha() for o in options)
        return f"{len(options)} {'letters' if letters else 'characters'}"
    if len(options) <= 6:
        return repr(list(options))
    return f"{len(options)} items"


def describe(name, args, options=None):
    if name in ("choice", "choices", "shuffle", "sample") and options is not None:
        return f"random.{name} over {over(options)}"
    return f"random.{name}({', '.join(repr(a) for a in args)})"


def matching(options, value):
    """The option equal to `value` (so a scripted 3 returns the student's own object), else value."""
    if not isinstance(options, range):
        for option in options:
            if option == value:
                return option
    return value


def draw(name, args, options):
    """One random pick from `options`, as the test scripts it."""
    if not isinstance(options, range):
        options = list(options)
    if not options:
        raise IndexError("cannot choose from an empty sequence")
    reply = ask(("random", describe(name, args, options), is_die(options), menu(options), "pick"))
    if reply[0] == "face":
        return sorted(options)[reply[1] - 1]
    if reply[0] == "index":  # the n-th option in the program's own order (0-based)
        return options[reply[1]]
    if reply[0] == "value":
        return matching(options, reply[1])
    return options[0]


def p_randint(self, a, b):
    return draw("randint", (a, b), range(a, b + 1))


def p_randrange(self, start, stop=None, step=1):
    args = (start,) if stop is None else (start, stop) if step == 1 else (start, stop, step)
    choices = range(start) if stop is None else range(start, stop, step)
    if not choices:
        raise ValueError(f"empty range for randrange{args}")
    return draw("randrange", args, choices)


def p_choice(self, seq):
    return draw("choice", (seq,), seq)


def p_choices(self, population, weights=None, *, cum_weights=None, k=1):
    population = list(population)
    return [draw("choices", (population,), population) for _ in range(k)]


def p_random(self):
    reply = ask(("random", "random.random()", False, None, "float"))
    return float(reply[1]) if reply[0] == "value" else 0.0


def p_uniform(self, a, b):
    reply = ask(("random", describe("uniform", (a, b)), False, None, "float"))
    return float(reply[1]) if reply[0] == "value" else a


def p_sample(self, population, k, *, counts=None):
    population = list(population)
    reply = ask(("random", describe("sample", (population, k), population), False, menu(population), "sample"))
    if reply[0] == "value":
        return [matching(population, v) for v in reply[1]]
    return population[:k]


def p_shuffle(self, x):
    reply = ask(("random", describe("shuffle", (x,), x), False, menu(x), "shuffle"))
    if reply[0] == "value":
        x[:] = [matching(list(x), v) for v in reply[1]]


PATCHES = {
    "randint": p_randint, "randrange": p_randrange, "choice": p_choice, "choices": p_choices,
    "random": p_random, "uniform": p_uniform, "sample": p_sample, "shuffle": p_shuffle,
}


def patch_random():
    for cls in (random.Random, random.SystemRandom):
        for name, fn in PATCHES.items():
            setattr(cls, name, fn)
    for name in PATCHES:  # the module functions are bound methods of one hidden instance
        setattr(random, name, getattr(random._inst, name))
    import secrets

    secrets.randbelow = lambda n: draw("randbelow", (n,), range(n))
    secrets.choice = lambda seq: draw("choice", (seq,), seq)


def patch_sleep():
    """time.sleep returns at once (a countdown can't eat the step timeout); the test sees how long."""
    import time

    time.sleep = lambda seconds: send(("sleep", seconds))


# ---- run the game -----------------------------------------------------------

def student_traceback(error):
    """The traceback through the student's own files only, paths relative to the game folder."""
    lines = ["Traceback (most recent call last):\n"]
    for frame in traceback.extract_tb(error.__traceback__):
        path = os.path.abspath(frame.filename)
        if not frame.filename.startswith("<") and path.startswith(FOLDER + os.sep):
            rel = os.path.relpath(path, FOLDER)
            lines.append(f'  File "{rel}", line {frame.lineno}, in {frame.name}\n')
            if frame.line:
                lines.append(f"    {frame.line.strip()}\n")
    lines += traceback.format_exception_only(type(error), error)
    return "".join(lines)


def main():
    patch_random()
    patch_sleep()
    builtins.input = fake_input
    sys.stdin = sys.__stdin__ = Stdin()
    sys.stdout = Writer("stdout")
    sys.stderr = Writer("stderr")
    sys.argv = [APP, *sys.argv[2:]]
    sys.path[:] = [FOLDER] + [p for p in sys.path if os.path.abspath(p or ".") not in (HERE, FOLDER)]
    os.chdir(FOLDER)
    code = 0
    try:
        runpy.run_path(APP, run_name="__main__")
    except SystemExit as stop:
        if stop.code is None:
            code = 0
        elif isinstance(stop.code, int):
            code = stop.code
        else:
            sys.stderr.write(f"{stop.code}\n")
            code = 1
    except BaseException as error:  # noqa: BLE001 - report every crash to the test
        send(("crash", student_traceback(error)))
        os._exit(1)
    send(("exit", code))
    os._exit(0)


main()
