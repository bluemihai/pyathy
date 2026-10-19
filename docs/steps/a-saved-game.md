# a saved game:

```gherkin
Given a saved game:
  """
  3
  """
```

## What it does

Writes these lines into the program's save file before the program starts, in the copy of
your folder the scenario runs in. The scenario never names the file: pyathy reads the
program's code (it does not run it) and takes the file a `SAVE_FILE_NAME = "count.txt"`
constant at the top of `main.py` names, or else the one file the program opens for writing
(`open("count.txt", "w")`). A program that writes several files needs the constant.

## Why you need it

A program that saves its state can be tested from any point: dictate the saved game, start
the program, and check what it shows or does next. No need to play the first twenty moves
in every scenario, and when the program renames its save file, nothing in the scenarios
changes. It is [`a file "game.txt" with:`](a-file-with.md) with the file name taken from the
program.

## Example

```gherkin
Feature: Counter

  Scenario: it continues from the saved count
    Given a saved game:
      """
      3
      """
    When I start the program
    Then "Count: 3" is printed
```

The program is the counter on the
[`a file "game.txt" containing "round 3"`](a-file-containing.md) page: it reads `count.txt`
at the start and writes it after every count, so `count.txt` is its save file.

## When it fails

`pyathy can't tell which file your program saves to: put SAVE_FILE_NAME = "…" at the top
of main.py`: the program opens no file for writing, or more than one, or builds the name in
a way pyathy cannot read from the code. `pyathy check` reports the same before any
scenario runs.

## See also

[`there is no saved game`](there-is-no-saved-game.md) ·
[`the saved game holds:`](the-saved-game-holds.md) ·
[`a saved game is written`](a-saved-game-is-written.md) ·
[`the program is started again`](the-program-is-started-again.md) ·
[`a file "game.txt" with:`](a-file-with.md)
