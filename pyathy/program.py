"""The student's program, run under _boot.py and fed from queues the steps fill.

Every step pushes what it scripts (an input, a die face, a random value) and then the
program runs as far as it can: until it asks for something nothing scripted yet, or ends.
So "I input 4" then "I roll 6" and "I roll 6" then "I input 4" both work: inputs and
rolls are consumed in their own order, whichever the program asks for first.
"""

import ast
import functools
import hashlib
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from collections import deque
from multiprocessing.connection import Listener

BOOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_boot.py")
STEP_TIMEOUT = 10.0     # seconds a step may go without the program printing or asking anything
RUN_LIMIT = 60.0        # seconds a step may keep the program running (printing) without it asking
MAX_OUTPUT = 50_000_000  # characters: a memory guard only; endless printing is caught by RUN_LIMIT
OLDEST_PYTHON = (3, 9)  # the oldest Python _boot.py is known to run under (tested on 3.9 and 3.10)


class ProgramError(AssertionError):
    pass


# Terminal escape sequences a program colours its output with: CSI (\x1b[31m, cursor moves),
# OSC (\x1b]0;title\x07) and the two-character escapes. Every check reads the output without
# them (plain), so "\x1b[31mPlayer red:\x1b[0m" is "Player red:"; the transcript keeps them.
ESCAPES = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?|\x1b[@-Z\\-_]")


def plain(text):
    """`text` without terminal escape sequences (colours, bold, cursor moves)."""
    return ESCAPES.sub("", text) if "\x1b" in text else text


# The folder pyathy runs from, never copied along with the student's: the student folder
# `python pyathy` runs from (pyathy/__main__.py + pyathy/pyathy/), whatever it is named.
_PACKAGE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_PACKAGE)
OWN_FOLDER = os.path.realpath(_PARENT if os.path.isfile(os.path.join(_PARENT, "__main__.py")) else _PACKAGE)
_SKIP_NAMES = shutil.ignore_patterns("__pycache__", ".git", ".venv", "features", "node_modules", "pyathy")


def skip(folder, names):
    """copytree's ignore: the usual clutter, a folder named pyathy, and pyathy's own folder."""
    skipped = set(_SKIP_NAMES(folder, names))
    for name in names:
        if name not in skipped and os.path.realpath(os.path.join(folder, name)) == OWN_FOLDER:
            skipped.add(name)
    return skipped


def _digests(folder):
    """{relative path: digest of its contents} for every file under `folder` (the clutter
    copytree skips, __pycache__ and .pyathy, left out), to tell which files a run wrote."""
    found = {}
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv", "node_modules", ".pyathy")]
        for name in files:
            path = os.path.join(root, name)
            try:
                with open(path, "rb") as f:
                    found[os.path.relpath(path, folder).replace(os.sep, "/")] = hashlib.blake2b(f.read()).digest()
            except OSError:
                pass
    return found


@functools.cache
def student_python(folder):
    """The Python the student runs their program with, as (path, how); how is None for pyathy's own.

    (a) a Poetry project (pyproject.toml with [tool.poetry]) that has dependencies, and poetry
    on PATH: its environment; (b) a .venv in the folder; (c) the Python pyathy itself runs on.
    A Poetry project without dependencies needs no environment of its own, so it runs on (b) or (c)."""
    pyproject = os.path.join(folder, "pyproject.toml")
    poetry = shutil.which("poetry")
    if os.path.isfile(pyproject) and poetry and _needs_poetry(pyproject):
        env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "POETRY_ACTIVE")}
        done = subprocess.run([poetry, "env", "info", "--executable"], cwd=folder, env=env,
                              capture_output=True, text=True)
        path = done.stdout.strip().splitlines()[-1:] if done.returncode == 0 else []
        if not path or path[0] == "NA" or not os.path.isfile(path[0]):
            raise ProgramError(f"{folder} is a Poetry project, but its environment does not exist yet.\n"
                               f"Run this in that folder first, then pyathy again:\n    poetry install")
        found = path[0], "the Poetry environment"
    else:
        for venv in (os.path.join(folder, ".venv", "bin", "python"),
                     os.path.join(folder, ".venv", "Scripts", "python.exe")):
            if os.path.isfile(venv):
                found = venv, "the folder's .venv"
                break
        else:
            return sys.executable, None
    path, how = found
    version = subprocess.run([path, "-c", "import sys; print(*sys.version_info[:2])"],
                             capture_output=True, text=True).stdout.split()
    if len(version) != 2:
        raise ProgramError(f"could not run {path} ({how})")
    if tuple(map(int, version)) < OLDEST_PYTHON:
        raise ProgramError(f"{how} has Python {'.'.join(version)} ({path}); pyathy needs Python "
                           f"{'.'.join(map(str, OLDEST_PYTHON))} or newer to run your program")
    return path, f"{how}, Python {'.'.join(version)}"


def _needs_poetry(pyproject):
    """Whether this pyproject.toml is a Poetry project with dependencies to install (a
    `[tool.poetry]` table, and a dependency under [project] or [tool.poetry] besides python)."""
    with open(pyproject, "rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError:
            f.seek(0)
            return b"[tool.poetry" in f.read()
    poetry = data.get("tool", {}).get("poetry")
    if poetry is None:
        return False
    listed = list(data.get("project", {}).get("dependencies", []))
    listed += [d for d in poetry.get("dependencies", {}) if d != "python"]
    for group in poetry.get("group", {}).values():
        listed += list(group.get("dependencies", {}))
    return bool(listed)


def constant(app, name):
    """The file a scenario names by an ALL_CAPS constant (`a file SAVE_FILE_NAME with:`): the
    string a module-level `NAME = "…"` assigns in the program file, else in another module of
    the program, else the one file the program opens for writing. Read with ast (the program is
    not run), so renaming the file in the program never touches the scenario."""
    found, written = _lookup(app, name)
    if found is not None:
        return found
    short = os.path.basename(app)
    hint = (f"; it writes several files ({', '.join(written)}), so the scenario cannot tell which one"
            if written else "; no file opened for writing was found either")
    raise ProgramError(f'{short} has no {name} (the scenario needs it: put {name} = "…" at the top of {short}{hint})')


SAVE_FILE = "SAVE_FILE_NAME"  # the optional override of the file a program saves to


def save_file(app):
    """The file the program saves its game to, for the saved-game steps: what a SAVE_FILE_NAME
    constant names, else the one file the program opens for writing."""
    found, _ = _lookup(app, SAVE_FILE)
    if found is None:
        raise ProgramError(f"pyathy can't tell which file your program saves to: put {SAVE_FILE} = \"…\""
                           f" at the top of {os.path.basename(app)}")
    return found


def _lookup(app, name):
    """(the file name, None) when the program says it, else (None, the files it opens for writing)."""
    short = os.path.basename(app)
    if not os.path.exists(app):
        raise ProgramError(f"there is no {short} in {os.path.dirname(app)}")
    source, tree = _parse(app, name)
    found = _assignment(tree, name)
    if found is not None:
        text = _literal(found.value)
        if text is None:
            line = ast.get_source_segment(source, found) or f"{name} = …"
            raise ProgramError(f"{short} line {found.lineno}: {name} is not a plain string, so the scenario cannot"
                               f' read the file name from it (it needs {name} = "…"):\n    {line}')
        return text, None
    others = _modules(os.path.dirname(app), skip=short)
    for _, other in others:
        node = _assignment(other, name)
        if node is not None and _literal(node.value) is not None:
            return _literal(node.value), None
    trees = [tree] + [other for _, other in others]
    written = sorted({w for module in trees for w in _written(module, trees)})
    if len(written) == 1:
        return written[0], None
    return None, written


def _parse(path, name):
    with open(path, encoding="utf-8", errors="replace") as f:
        source = f.read()
    try:
        return source, ast.parse(source, filename=os.path.basename(path))
    except SyntaxError as e:
        raise ProgramError(f"{os.path.basename(path)} has a syntax error on line {e.lineno}, so {name} could not"
                           f" be read: {e.msg}") from None


def _modules(folder, skip):
    """(path, tree) of the other top-level .py files of the program; one that does not parse is left out."""
    found = []
    for entry in sorted(os.listdir(folder)):
        if entry.endswith(".py") and entry != skip and not entry.startswith("."):
            try:
                found.append((entry, _parse(os.path.join(folder, entry), "")[1]))
            except ProgramError:
                pass
    return found


def _assignment(tree, name):
    """The last top-level `name = …` in the module, or None."""
    found = None
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == name for t in targets) and getattr(node, "value", None) is not None:
            found = node
    return found


def _assigned(tree, name):
    """The value of the last `name = …` anywhere in the module (a constant at the top, or a
    variable inside the function that opens the file), or None."""
    found = None
    for node in ast.walk(tree):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == name for t in targets) and getattr(node, "value", None) is not None:
            found = node.value
    return found


def _written(tree, trees=()):
    """The file names a module opens for writing: `open("save.txt", "w")`, the name a literal or
    a name assigned one in that module, the mode a literal starting with w or a. A name that is
    a parameter of the function around the open (`def save(filename): open(filename, "w")`) is
    followed to the calls of that function in the program's modules (`save(SAVE_FILE)`)."""
    found = []
    functions = {child: node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 for child in ast.walk(node)}  # each node -> the innermost function around it (walk is outer-first)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open" and node.args):
            continue
        mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
        if not (isinstance(mode, ast.Constant) and isinstance(mode.value, str) and mode.value[:1] in ("w", "a")):
            continue
        target = node.args[0]
        if isinstance(target, ast.Name):
            value = _assigned(tree, target.id)
            if value is None and node in functions:
                found += _passed(functions[node], target.id, trees or [tree])
                continue
            target = value
        if (text := _literal(target)) is not None:
            found.append(text)
    return found


def _passed(function, name, trees):
    """The file names the program's calls of `function` pass for its parameter `name`."""
    params = [a.arg for a in function.args.posonlyargs + function.args.args]
    if name not in params:
        return []
    at = params.index(name) - (1 if params[0] in ("self", "cls") else 0)
    found = []
    for module in trees:
        for call in ast.walk(module):
            if not (isinstance(call, ast.Call) and function.name == getattr(call.func, "id", getattr(call.func, "attr", None))):
                continue
            arg = call.args[at] if 0 <= at < len(call.args) else next((k.value for k in call.keywords if k.arg == name), None)
            if isinstance(arg, ast.Name):
                arg = _assigned(module, arg.id)
            if (text := _literal(arg)) is not None:
                found.append(text)
    return found


def _literal(node):
    """A file name the program spells out: a string literal, literals joined with +, the last
    part of an os.path.join(…, "name") or of a pathlib `… / "name"` (the program runs in its own
    folder, so that part is the file next to main.py); else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal(node.left), _literal(node.right)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _literal(node.right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "join" and node.args:
        return _literal(node.args[-1])
    return None


class Program:
    def __init__(self, app):
        self.app = os.path.abspath(app)
        self.args = []            # command-line arguments, after the program's name
        self.timeout = STEP_TIMEOUT
        self.run_limit = RUN_LIMIT
        self.inputs = deque()
        self.dice = deque()
        self.values = deque()
        self._parts, self._size = [], 0
        self.typed = []           # (start, end) of each typed answer in output, for the transcript
        self.state = "new"        # new | waiting | exited | crashed
        self.request = None       # the question the program is blocked on
        self.exit_code = None
        self.crash = None
        self.conn = None
        self.proc = None
        self.workdir = None
        self.files = []           # (name, text) to write into the copy before the first start
        self.removed = []         # names to leave out of the copy ("there is no file …")
        self.snapshot = None      # {relative path: digest} of the copy's files at the first start
        self.runs = []            # (output, typed) of each earlier run, after "started again"
        self.players = []         # the names a turn announcement may use (typed, declared or rolled)
        self.turn_start = None    # where in output the last roll was made: "this turn" starts there
        # A features folder's own steps may answer a request themselves (a board file's name,
        # say): called with each request first; it returns a reply, or None for the queues.
        self.answerer = None

    # Everything printed (and echoed) so far, as the terminal got it (colour codes and all:
    # the transcript shows them, and `typed` indexes into it). Kept as a list of pieces so a
    # program that prints megabytes in small writes costs linear time, joined only when read.
    @property
    def output(self):
        if len(self._parts) > 1:
            self._parts = ["".join(self._parts)]
        return self._parts[0] if self._parts else ""

    @output.setter
    def output(self, text):
        self._parts, self._size = [text], len(text)

    # The same without colours: what every check reads.
    @property
    def text(self):
        return plain(self.output)

    def _print(self, text):
        self._parts.append(text)
        self._size += len(text)

    # ---- what steps call ---------------------------------------------------

    def type(self, *texts):
        self.inputs.extend(texts)
        self.advance()

    def roll(self, *faces):
        self.turn_start = self._size
        self.dice.extend(faces)
        self.advance()

    def turn(self, *faces):
        """One turn: enter (if the program is waiting for it), then the dice show these faces."""
        self.turn_start = self._size
        self.dice.extend(faces)
        if self.request is not None and self.request[0] == "input":
            self.inputs.append("")
        self.advance()

    def choose(self, value):
        """The next random pick (not a die) returns this value."""
        self.values.append(("value", value))
        self.advance()

    def choose_option(self, number):
        """The next random pick (not a die) returns the n-th of the options, counted from 1."""
        self.values.append(("index", number - 1))
        self.advance()

    def turn_output(self):
        """What the program printed since the last roll (everything, before any roll), plain."""
        return plain(self.output[self.turn_start or 0:])

    def settle(self):
        """Run the program as far as it can; returns the plain output (checks read this)."""
        self.advance()
        return self.text

    def write_file(self, name, text):
        """A file the scenario puts in the program's folder: written into the copy now, or
        staged for the first start when there is no copy yet."""
        if self.workdir is None:
            self.files.append((name, text))
            return
        path = os.path.join(self.workdir, name)
        os.makedirs(os.path.dirname(path) or self.workdir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def remove_file(self, name):
        """A file the program starts without, whatever is in the folder: left out of the copy."""
        if self.workdir is None:
            self.removed.append(name)
            return
        path = os.path.join(self.workdir, name)
        if os.path.isfile(path):
            os.chmod(path, 0o644)
            os.remove(path)

    def changed_files(self):
        """The files the program wrote: new since the first start, or with other contents."""
        if self.snapshot is None:
            return []
        now = _digests(self.workdir)
        return sorted(name for name, digest in now.items() if self.snapshot.get(name) != digest)

    def stop(self):
        """End the current run (the process), keeping the copy of the folder."""
        if self.conn is not None:
            try:
                if self.request is not None:
                    self.conn.send(("stop",))
                self.conn.close()
            except OSError:
                pass
        if self.proc is not None and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait()
        self.conn = self.proc = None

    def close(self):
        self.stop()
        if self.workdir:
            shutil.rmtree(self.workdir, ignore_errors=True)

    def restart(self):
        """Stop the program and start it again in the same copy of the folder, with the files
        it wrote still there (a saved game loads). Its earlier run moves to `runs`; output,
        typed and state are the new run's."""
        if self.state == "new":
            raise ProgramError('"the program is started again" needs a run before it:'
                               ' start the program first (an input, a roll, a check)')
        self.stop()
        self.runs.append((self.output, self.typed))
        self.output, self.typed, self.turn_start = "", [], None
        self.state, self.request, self.exit_code, self.crash = "new", None, None, None
        self.advance()

    # ---- the run loop ------------------------------------------------------

    def start(self):
        if not os.path.exists(self.app):
            raise ProgramError(f"there is no {os.path.basename(self.app)} in {os.path.dirname(self.app)}")
        if self.workdir is None:
            # A fresh copy of the folder per scenario: a save file from one scenario never
            # leaks into the next, and nothing is ever written into the student's folder.
            self.workdir = tempfile.mkdtemp(prefix="pyathy-work-")
            shutil.copytree(os.path.dirname(self.app), self.workdir, dirs_exist_ok=True, ignore=skip,
                            ignore_dangling_symlinks=True)
            for name in self.removed:
                self.remove_file(name)
            for name, text in self.files:
                self.write_file(name, text)
            self.snapshot = _digests(self.workdir)
        app = os.path.join(self.workdir, os.path.basename(self.app))
        key = secrets.token_bytes(16)
        if sys.platform == "win32":
            address = rf"\\.\pipe\pyathy-{secrets.token_hex(8)}"
        else:
            address = os.path.join(tempfile.mkdtemp(prefix="pyathy-"), "s")
        listener = Listener(address, authkey=key)
        env = dict(os.environ, SCRIPTED_GAME_ADDRESS=address, SCRIPTED_GAME_KEY=key.hex(), SCRIPTED_GAME_SIDES="6")
        python, _ = student_python(os.path.dirname(self.app))
        self.proc = subprocess.Popen([python, BOOT, app, *self.args], env=env, cwd=self.workdir)
        accepted = {}
        t = threading.Thread(target=lambda: accepted.setdefault("c", listener.accept()), daemon=True)
        t.start()
        t.join(max(self.timeout, STEP_TIMEOUT))
        listener.close()
        if "c" not in accepted:
            self.proc.kill()
            raise ProgramError("the program did not start")
        self.conn = accepted["c"]
        self.state = "waiting"

    def advance(self):
        if self.state == "new":
            self.start()
        began = time.monotonic()
        while self.state == "waiting":
            if self.request is not None:
                reply = (self.answerer and self.answerer(self.request)) or self._answer(self.request)
                if reply is None:
                    return  # blocked on something no step scripted yet
                self.request = None
                self.conn.send(reply)
            if not self.conn.poll(self.timeout):
                self.state = "hung"
                raise ProgramError(
                    f"the program printed nothing and asked nothing for {self.timeout:g} seconds"
                    f" (an endless loop? if it is just slow, add the step"
                    f" 'Given the program may take 30 seconds')\n{self.tail()}")
            if time.monotonic() - began > self.run_limit:
                self.state = "hung"
                raise ProgramError(
                    f"the program kept running for {self.run_limit:g} seconds without asking for anything"
                    f" (an endless loop? if it is just slow, add the step"
                    f" 'Given the program may take {2 * self.run_limit:g} seconds')\n{self.tail()}")
            try:
                message = self.conn.recv()
            except EOFError:
                self.state = "exited"
                self.exit_code = self.proc.wait()
                return
            kind = message[0]
            if kind == "out":
                self._print(message[1])
                if self._size > MAX_OUTPUT:
                    self.state = "hung"
                    raise ProgramError(f"the program printed over {MAX_OUTPUT // 1_000_000} million characters"
                                       f" (an endless loop?)\n{self.tail()}")
            elif kind in ("input", "random"):
                if kind == "input" and message[1]:
                    self._print(message[1])  # input("prompt") prints its prompt
                self.request = message
            elif kind == "exit":
                self.state, self.exit_code = "exited", message[1]
            elif kind == "crash":
                self.state, self.crash = "crashed", message[1]
            # "sleep": ignored, time.sleep returns at once

    def _answer(self, request):
        if request[0] == "input":
            if not self.inputs:
                return None
            text = self.inputs.popleft()
            self.typed.append((self._size, self._size + len(text)))
            self._print(text + "\n")  # echo, as a terminal shows it
            return ("text", text)
        _, description, is_die, menu, kind = request
        if is_die and self.dice:
            face = self.dice.popleft()
            if isinstance(menu, range) and face not in menu:
                raise ProgramError(f"rolled {face}, but the program's die ({description}) "
                                   f"goes from {menu.start} to {menu.stop - 1}")
            return ("value", face)
        if self.values:  # a scripted pick answers any random call, even a six-option one
            return self.values.popleft()
        return None if is_die else ("first",)

    # ---- for messages --------------------------------------------------------

    def waiting_for(self):
        if self.request is None:
            return None
        if self.request[0] == "input":
            return f"input ({self.request[1].strip() or 'no prompt'})"
        return f"a die roll ({self.request[1]})" if self.request[2] else self.request[1]

    def tail(self, n=15):
        lines = self.text.splitlines()[-n:]
        if not lines:
            return "the program printed nothing"
        shown = "\n".join(f"    | {line}" for line in lines)
        what = "the only line" if len(lines) == 1 else f"the last {len(lines)} lines"
        return f"{what} printed:\n{shown}"
