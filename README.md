# pyathy

Test a Python command-line program with scenarios written in plain English.

You write `.feature` files (Gherkin: `Scenario`, `When`, `Then`) that type answers into
your program, fix its dice rolls, and check what it prints. pyathy runs each scenario
against a fresh start of your `main.py` and shows each run, then one line per scenario plus a total.
It is built on [pytest-bdd](https://github.com/pytest-dev/pytest-bdd) and needs Python 3.11+.

## Run it

Put the `pyathy` folder next to your program, so the folder looks like this:

```
my-game/
  main.py
  features/
    game.feature
  pyathy/
```

Then, from `my-game/`:

```
python pyathy        # run every features/*.feature against main.py
python pyathy steps  # every step you can use (plus your own, from features/*_steps.py)
python pyathy -h     # usage and an example feature
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

`--next-failure` (as in rspec) reads the failures pyathy remembered in `.pyathy/last-run.json`
(rewritten after every run; safe to gitignore); when all of them pass it runs everything else.
`--solution` is for the teacher's folder, where the reference program sits in `_solution/` next
to the student's `main.py`: the features are checked against the reference, and the report's
first line names it (`Program: _solution/main.py`).

By default each scenario's run is shown as a terminal would have shown it: what the
program printed (boards, trees, prompts) and what was typed (bold, on a terminal with
colour), under a `│` gutter, then its `✔`/`✘` line with the reason under a `✘`. On a terminal
the reason is coloured by meaning: what was expected green, what the program did red, quoted
text and file names cyan, notes dim, and `the output shows:` lines as a `+`/`-` diff against
what was printed (never when piped, or with `NO_COLOR` set). A run
longer than 200 lines shows its first 150 and last 50. After the last scenario comes a
summary of every `✔`/`✘` line per feature, and the last line is `TOTAL  n of m`. With
`-q` (or `--quiet`) only the `✔`/`✘` lines and the TOTAL line are printed, each `✘` with the
first line of its reason (cut to the terminal's width), then a hint to run without `-q` for
the full output. Every report opens with a dim `pyathy 0.2.0 · <where it runs from>` line, the
same origin `-v` (`--version`) prints, so two copies of pyathy on one machine are never confused:
the unzipped `pyathy/` folder, `editable: <repo>` for a `pip install -e` / `uv tool install -e`,
or `installed: <site-packages>/pyathy`.

The `pyathy` folder is built from this repo with `scripts/build-folder.sh` (it lands in
`dist/pyathy/`, with pytest-bdd inside, so nothing needs installing). You can also install
pyathy as a command with `pip install .` and run `pyathy` instead of `python pyathy`.

## A feature

```gherkin
Feature: Tic Tac Toe

  Scenario: X wins with the top row
    When I input 1, 4, 2, 5, 3
    Then "Player X wins!" is printed
    And the program asks "Play again? (y/n)"

  Scenario: a taken square is asked again
    When I input 5, 5
    Then "That square is taken." is printed
```

## Built-in steps

Each works after `Given`, `When`, `Then`, `And` or `But`. Text checks ignore case and
trailing spaces. `python pyathy steps` prints this list (colour-coded on a terminal:
the parts you replace in cyan).

| Step | What it does |
|---|---|
| `I start the program` | run `main.py` until it asks something or ends |
| `the program other.py` | run `other.py` instead of `main.py` |
| `I run the program with puzzle.txt --hard` | start it with these command-line arguments |
| `the program may take 30 seconds` | wait longer for a slow program (default 10) |
| `I input 4` / `I input 4, left, no` | type answers, one per question |
| `I input enter` | just press enter |
| `I roll 6` / `I roll 3 and 4` | the next dice show these faces |
| `the random choice is red` | the next random pick returns this value |
| `"Hello" is printed` | somewhere in the output |
| `"Error" is printed 3 times` | exactly that many times |
| `"Game over" is not printed` | nowhere in the output |
| `the output starts with "Welcome"` | the very first output |
| `the output shows:` + lines between `"""` | these lines, in a row |
| `the program asks "Your name?"` | it is now waiting for input after that question |
| `the program ends` / `the program is still running` | |
| `a file "game.txt" containing "round 3"` | put this one-line file in the folder before the program starts |
| `a file "game.txt" with:` + lines between `"""` | the same, several lines |
| `a file "game.txt" is written` / `no file is written` | the program made a file, or changed one |
| `the file "game.txt" contains "round 4"` | anywhere in the file |
| `the file "game.txt" contains:` + lines between `"""` | these lines, in a row |
| `a file SAVE_FILE_NAME with:` | in every file step, an unquoted ALL_CAPS name is read from your program: `SAVE_FILE_NAME = "game.txt"` at its top |
| `the program is started again` | stop it and start it over in the same folder, so the files it wrote are still there |

## Start from a saved state

A program that saves its state to a text file is easy to test from any point: dictate the
file, start the program, play a move, and check the file (or what is printed). Each scenario
runs in a copy of your folder, so the dictated file and whatever the program writes never
touch your own files. For a save-then-load check in one scenario, `the program is started
again` restarts it in that same copy, with its save file still there; the steps after it
read the new run, and the report shows both runs.

```gherkin
Feature: Counter

  Scenario: it continues from the saved count and saves the new one
    Given a file "count.txt" with:
      """
      3
      """
    When I start the program
    Then "Count: 3" is printed
    When I input enter, q
    Then the file "count.txt" contains:
      """
      4
      """

  Scenario: save, start again, it continued
    When I input enter, enter, q
    Then a file "count.txt" is written
    When the program is started again
    Then "Count: 2" is printed
```

Name the file by a constant of your program instead, and the scenario survives a rename: with
`SAVE_FILE_NAME = "count.txt"` at the top of `main.py`, write the name unquoted in any file step.
pyathy reads the constant from your program (it does not run it), so changing it to
`"state.txt"` later changes the scenario too.

```gherkin
  Scenario: it continues from the saved count (the file named by the program)
    Given a file SAVE_FILE_NAME with:
      """
      3
      """
    When I start the program
    Then "Count: 3" is printed
    When I input enter, q
    Then the file SAVE_FILE_NAME contains:
      """
      4
      """
```

## Your own steps

Every `*_steps.py` next to your `.feature` files is loaded, so a game can read like the
game. `examples/monopoly/features/monopoly_steps.py` adds `Ann rolls 3+4 and buys` and
`Ann has $1460`:

```python
from pyathy.steps import fail, step

@step(r"(?P<name>\w+) has \$(?P<cash>\d+)")
def has(program, name, cash):
    ...
```

## Examples

`examples/tictactoe` (built-in steps only), `examples/sudoku` (boards checked with
`the output shows:`, a puzzle file as argument) and `examples/monopoly` (dice and its own
steps). `examples/edge` fails on purpose, to show the messages. Run them all with
`scripts/try-examples.sh`.

## License

MIT, see `LICENSE`.
