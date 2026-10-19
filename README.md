# pyathy

Test a Python command-line program with scenarios written in plain English.

You write `.feature` files (Gherkin: `Scenario`, `When`, `Then`) that type answers into
the program, fix its dice rolls, and check what it prints. pyathy runs each scenario against
a fresh start of `main.py` and shows each run, then one `✔`/`✘` line per scenario plus a total.
It is built on [pytest-bdd](https://github.com/pytest-dev/pytest-bdd) and needs Python 3.11+.

It was built for the Saxion ADSD python course, so that the acceptance tests of an assignment
can be read, and written, by people new to programming: the steps are the words a person
would use at the keyboard, and no code is needed. It tests any Python command-line program,
anywhere, the same way.

## Install and use

Three ways to get the command. They run the same features the same way.

**No install: the `pyathy/` folder next to `main.py`.** This is what a student package holds
(built from this repo by `scripts/build-folder.sh` into `dist/pyathy/`, pytest-bdd inside):

```
my-game/
  main.py
  features/
    game.feature
  pyathy/
```

```
python pyathy
```

**Poetry**, with that same `pyathy/` folder in the project:

```
poetry add ./pyathy
poetry run pyathy
```

**pip**, in a venv: `pip install ./pyathy` for the folder, or from a clone of this repo:

```
python -m venv .venv
.venv/bin/pip install .          # Windows: .venv\Scripts\pip install .
cd examples/tictactoe
../../.venv/bin/pyathy           # Windows: ..\..\.venv\Scripts\pyathy
```

That runs the tic-tac-toe example's features against its `main.py`.

From the folder that holds `main.py` and `features/` (write `python pyathy …` for the folder,
`poetry run pyathy …` under Poetry):

```
pyathy                      run every features/*.feature against main.py
pyathy features/x.feature   run only that file (or folder)
pyathy check                find mistakes in the feature files, without running main.py
pyathy init                 create features/hello.feature (and a main.py) to start from
pyathy steps                every step you can use (plus your own, from features/*_steps.py)
pyathy -h                   usage and an example feature
```

Options, each with a short and a long form:

```
-q,  --quiet              only one line per scenario (a ✘ gets one reason line) and the total
-ff, --fail-fast          stop at the first scenario that fails
-nf, --next-failure       run the scenarios that failed last time, in order, stopping at the first that still fails
-s,  --solution [FOLDER]  run the features here against ./_solution/main.py, or ./FOLDER/main.py (-s obj2 means _solution-obj2)
-h,  --help               this help
-v,  --version            pyathy's version and where it runs from
```

The report shows each scenario's run as a terminal would have (what was printed, what was
typed), then its `✔`/`✘` line with the reason under a `✘`, a summary per feature, and the last
line `TOTAL  n of m`; `-q` keeps only the `✔`/`✘` lines and the total. Every report ends with
`pyathy <version> · <where it runs from>`, the same as `-v`, so two copies on one machine are
never confused. `-nf` reads the failures remembered in `.pyathy/last-run.json`; `-s` is for
the teacher's folder, where the reference program sits in `_solution/`. The report's colours,
the long-run cut and the details of `-nf` and `-s`: [docs/running.md](docs/running.md).

`pyathy check` reads the feature files without running the program and lists, per file,
what would stop a scenario before it starts: a line no step matches (with the closest step,
`did you mean: I input Ada`), a file that is not valid Gherkin, a scenario or step indented
differently from the others, and a file step pyathy cannot find in the program. It exits with
1 when it found something; `--json` prints the same for an editor (the pyathy VS Code
extension uses it). Details and sample output: [docs/check.md](docs/check.md).

## A first feature

```gherkin
Feature: Tic Tac Toe

  Scenario: X wins with the top row
    When I input 1, 4, 2, 5, 3
    Then "Player X wins!" is printed
    And the program asks "Play again? (y/n)"
```

A `Scenario` is one run of the program, from a fresh start. `When` lines act (type answers,
roll dice) and `Then` lines check what the program did; `And` continues the line before it.

## Built-in steps, or your own

The built-in steps are the keyboard and the screen: type an answer, make the die show a
face, check what was printed, check a file. They need no code, so a feature can be read and
written by someone who has never seen a test; `examples/tictactoe` uses nothing else.
Your own steps speak the program's own language instead (`Ann has $1440`, `Ann owns
Harbour`): a few lines of Python each, in a `features/*_steps.py`, worth writing once a feature
file starts repeating the same five built-in lines to say one thing.

Each built-in works after `Given`, `When`, `Then`, `And` or `But`. Text checks ignore case and
trailing spaces. Colours in the program's output (`\033[31m`-style codes) are ignored when
matching, and shown in the report. `python pyathy steps` prints this list (colour-coded on
a terminal: the parts you replace in cyan).

Each step has its own page under [`docs/`](docs/README.md), with what it checks, when it is
needed, a scenario that runs and the message it fails with. Two guides: [turn-based
games](docs/turns.md) (`red rolls 6`, `red moves from 0 to 3`) and [starting from a saved
state](docs/saved-games.md) (`a saved game:`, `the program is started again`).

| Step | What it does |
|---|---|
| [`I start the program`](docs/steps/start-the-program.md) / [`I run the program with puzzle.txt --hard`](docs/steps/start-the-program.md) | run `main.py` until it asks something or ends; `with …` starts it with these command-line arguments |
| [`the program other.py`](docs/steps/the-program-other-py.md) | run `other.py` instead of `main.py` |
| [`the program may take 30 seconds`](docs/steps/the-program-may-take.md) | wait longer for a slow program (default 10) |
| [`I input 4`](docs/steps/i-input.md) / [`I input 4, left, no`](docs/steps/i-input.md) | type answers, one per question |
| [`I input enter`](docs/steps/i-input.md) / [`I input enter, q`](docs/steps/i-input.md) | press enter, on its own or as one answer of the list (quote `"enter"` to type the word) |
| [`I roll 6`](docs/steps/i-roll.md) / [`I roll 3 and 4`](docs/steps/i-roll.md) | the next dice show these faces |
| [`the random choice is red`](docs/steps/the-random-choice-is.md) | the next random pick returns this value |
| [`red rolls 6`](docs/steps/rolls.md) / [`Ann rolls 4+6`](docs/steps/rolls.md) | `I input enter` (if the program is waiting for it) then `I roll 6`, after checking it is red's turn: the last line announcing a turn names red and no other player, without digits (`Player red:`) |
| [`red rolls 3 and picks 2`](docs/steps/rolls-and-picks.md) / [`… and answers 2`](docs/steps/rolls-and-picks.md) | the same, then types 2 at the question that follows |
| [`these turns are played 3 times:`](docs/steps/these-turns-are-played.md) + a table | one step per row (`\| red rolls 5 \|`), run in order, that many times |
| [`the players are red and green`](docs/steps/the-players-are.md) | the names a turn announcement may use (otherwise: the names typed or rolled for so far) |
| [`red's turn is announced`](docs/steps/turn-is-announced.md) / [`it is red's turn`](docs/steps/turn-is-announced.md) | a line names red and no other player, without digits |
| [`a pawn moves from 0 to 3`](docs/steps/moves-from-to.md) / [`red moves from 0 to 3`](docs/steps/moves-from-to.md) | a line of this turn (since the last roll) has these two numbers, `to` or an arrow between them |
| [`nothing moves`](docs/steps/nothing-moves.md) | no such line this turn |
| [`"Hello" is printed`](docs/steps/is-printed.md) | somewhere in the output |
| [`"Error" is printed 3 times`](docs/steps/is-printed-n-times.md) | exactly that many times |
| [`"Game over" is not printed`](docs/steps/is-not-printed.md) | nowhere in the output |
| [`the output starts with "Welcome"`](docs/steps/the-output-starts-with.md) | the very first output |
| [`the output shows:`](docs/steps/the-output-shows.md) + lines between `"""` | these lines, in a row |
| [`the program asks "Your name?"`](docs/steps/the-program-asks.md) | it is now waiting for input after that question |
| [`"orange" is refused with a message`](docs/steps/is-refused-with-a-message.md) | after typing it, a message was printed and the same question was asked again |
| [`the program ends`](docs/steps/the-program-ends.md) / [`the program is still running`](docs/steps/the-program-is-still-running.md) | |
| [`a file "photos/beach.jpg"`](docs/steps/a-file.md) | an empty file in the folder before the program starts (its folders made too) |
| [`a file "game.txt" containing "round 3"`](docs/steps/a-file-containing.md) | put this one-line file in the folder before the program starts |
| [`a file "game.txt" with:`](docs/steps/a-file-with.md) + lines between `"""` | the same, several lines |
| [`there is no file "game.txt"`](docs/steps/there-is-no-file.md) | the program starts without it, whatever is in your folder (a saved game from playing, say) |
| [`a file "game.txt" is written`](docs/steps/a-file-is-written.md) / [`no file is written`](docs/steps/no-file-is-written.md) | the program made a file, or changed one |
| [`the file "game.txt" contains "round 4"`](docs/steps/the-file-contains.md) | anywhere in the file |
| [`the file "game.txt" contains:`](docs/steps/the-file-contains-lines.md) + lines between `"""` | these lines, in a row |
| [`a saved game:`](docs/steps/a-saved-game.md) + lines between `"""` | these lines are in the program's save file before it starts |
| [`there is no saved game`](docs/steps/there-is-no-saved-game.md) | the program starts without its save file |
| [`a saved game is written`](docs/steps/a-saved-game-is-written.md) | the program made its save file, or changed it |
| [`the saved game holds:`](docs/steps/the-saved-game-holds.md) + lines between `"""` | these lines, in a row, in the save file |
| [`no saved game is left`](docs/steps/no-saved-game-is-left.md) | the save file was removed, or emptied |
| [`the program is started again`](docs/steps/the-program-is-started-again.md) | stop it and start it over in the same folder, so the files it wrote are still there |

## Your own steps

Every `*_steps.py` next to the `.feature` files is loaded. A step is a pattern in
[Cucumber style](https://github.com/cucumber/cucumber-expressions): `{name}` matches anything,
`{name:w}` one word, `{n:d}` a whole number, and each field becomes a parameter of the function.
`program.settle()` returns everything printed so far; `fail(program, message)` fails the step
with the program's last lines under the message.
`examples/monopoly/features/monopoly_steps.py` adds `Ann has $1460` and `Ann owns Harbour`:

```python
from pyathy.steps import fail, step

@step("{name:w} has ${cash:d}")
def has(program, name, cash):
    ...
```

`python pyathy steps` lists them under the built-ins, as written. The whole of it, with the
step above in full: [docs/own-steps.md](docs/own-steps.md).

## Examples

`examples/tictactoe` (built-in steps only), `examples/sudoku` (boards checked with
`the output shows:`, a puzzle file as argument) and `examples/monopoly` (dice and its own
steps). `examples/edge` fails on purpose, to show the messages. Run them all with
`scripts/try-examples.sh`.

## License

MIT, see `LICENSE`.
