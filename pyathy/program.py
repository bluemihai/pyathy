"""The student's program, run under _boot.py and fed from queues the steps fill.

Every step pushes what it scripts (an input, a die face, a random value) and then the
program runs as far as it can: until it asks for something nothing scripted yet, or ends.
So "I input 4" then "I roll 6" and "I roll 6" then "I input 4" both work: inputs and
rolls are consumed in their own order, whichever the program asks for first.
"""

import functools
import hashlib
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import deque
from multiprocessing.connection import Listener

BOOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_boot.py")
STEP_TIMEOUT = 10.0     # seconds a step may go without the program printing or asking anything
RUN_LIMIT = 60.0        # seconds a step may keep the program running (printing) without it asking
MAX_OUTPUT = 50_000_000  # characters: a memory guard only; endless printing is caught by RUN_LIMIT
OLDEST_PYTHON = (3, 9)  # the oldest Python _boot.py is known to run under (tested on 3.9 and 3.10)


class ProgramError(AssertionError):
    pass


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

    (a) a Poetry project (pyproject.toml with [tool.poetry]) and poetry on PATH: its environment;
    (b) a .venv in the folder; (c) the Python pyathy itself runs on."""
    pyproject = os.path.join(folder, "pyproject.toml")
    poetry = shutil.which("poetry")
    if os.path.isfile(pyproject) and poetry and "[tool.poetry" in open(pyproject, encoding="utf-8", errors="replace").read():
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
        self.snapshot = None      # {relative path: digest} of the copy's files at the first start
        self.runs = []            # (output, typed) of each earlier run, after "started again"
        # A features folder's own steps may answer requests themselves (a whole Monopoly
        # turn, say): called with each request first; it returns a reply, or None for the queues.
        self.answerer = None

    # Everything printed (and echoed) so far. Kept as a list of pieces so a program that
    # prints megabytes in small writes costs linear time, joined only when a step reads it.
    @property
    def output(self):
        if len(self._parts) > 1:
            self._parts = ["".join(self._parts)]
        return self._parts[0] if self._parts else ""

    @output.setter
    def output(self, text):
        self._parts, self._size = [text], len(text)

    def _print(self, text):
        self._parts.append(text)
        self._size += len(text)

    # ---- what steps call ---------------------------------------------------

    def type(self, *texts):
        self.inputs.extend(texts)
        self.advance()

    def roll(self, *faces):
        self.dice.extend(faces)
        self.advance()

    def choose(self, value):
        self.values.append(value)
        self.advance()

    def settle(self):
        self.advance()
        return self.output

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
        self.output, self.typed = "", []
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
        if is_die:
            if not self.dice:
                return None
            face = self.dice.popleft()
            if isinstance(menu, range) and face not in menu:
                raise ProgramError(f"rolled {face}, but the program's die ({description}) "
                                   f"goes from {menu.start} to {menu.stop - 1}")
            return ("value", face)
        if self.values:
            return ("value", self.values.popleft())
        return ("first",)

    # ---- for messages --------------------------------------------------------

    def waiting_for(self):
        if self.request is None:
            return None
        if self.request[0] == "input":
            return f"input ({self.request[1].strip() or 'no prompt'})"
        return f"a die roll ({self.request[1]})" if self.request[2] else self.request[1]

    def tail(self, n=15):
        lines = self.output.splitlines()[-n:]
        if not lines:
            return "the program printed nothing"
        shown = "\n".join(f"    | {line}" for line in lines)
        what = "the only line" if len(lines) == 1 else f"the last {len(lines)} lines"
        return f"{what} printed:\n{shown}"
