# the saved game holds:

```gherkin
Then the saved game holds:
  """
  4
  """
```

## What it does

Lets the program run as far as it can, then reads the program's save file from the copy of
your folder and checks that these lines appear in it in a row. The lines go between two
lines of three quotes under the step; case and spaces at the end of lines are ignored. The
save file is found in the program's code, as for [`a saved game:`](a-saved-game.md). It is
[`the file "game.txt" contains:`](the-file-contains-lines.md) with the name taken from the
program.

## Why you need it

A saved game is a promise to the next run. Dictating one, playing a move and checking the
file afterwards tests the saving half of that promise on its own, without starting the
program again; the loading half is [`a saved game:`](a-saved-game.md) followed by a check
of what the program shows.

## Example

```gherkin
Feature: Counter

  Scenario: the file holds the new count
    Given a saved game:
      """
      3
      """
    When I input ""
    Then the saved game holds:
      """
      4
      """
```

The program is the counter on the
[`a file "game.txt" containing "round 3"`](a-file-containing.md) page.

## When it fails

- `expected a file "count.txt", but the program did not write one`: no save file in the
  copy.
- `expected the file "count.txt" to contain these lines, in a row:` with the lines.
- `pyathy can't tell which file your program saves to: ...`: see
  [`a saved game:`](a-saved-game.md).

## See also

[`a saved game:`](a-saved-game.md) ·
[`a saved game is written`](a-saved-game-is-written.md) ·
[`the file "game.txt" contains:`](the-file-contains-lines.md)
