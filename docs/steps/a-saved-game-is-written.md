# a saved game is written

```gherkin
Then a saved game is written
```

## What it does

Lets the program run as far as it can, then checks that the program's save file is new
since the program first started, or has other contents than it had then. The save file is
found in the program's code, as for [`a saved game:`](a-saved-game.md). It is
[`a file "game.txt" is written`](a-file-is-written.md) with the name taken from the program.

## Why you need it

Saving is the rule under test: after a move, after a count, after "save and quit", the
game is on disk. This step says that it was written; what it holds is checked with
[`the saved game holds:`](the-saved-game-holds.md), and that it loads with
[`the program is started again`](the-program-is-started-again.md).

## Example

```gherkin
Feature: Counter

  Scenario: counting once saves
    When I input ""
    Then "Count: 1" is printed
    And a saved game is written
```

The program is the counter on the
[`a file "game.txt" containing "round 3"`](a-file-containing.md) page; `""` is an empty
answer, which counts.

## When it fails

- `expected the program to write a file "count.txt", but it did not; it wrote no file`
  (or `...; it wrote: scores.txt`).
- `expected the program to write the file "count.txt", but it is as it was`: the file was
  there and the program did not change it.
- `pyathy can't tell which file your program saves to: ...`: see
  [`a saved game:`](a-saved-game.md).

## See also

[`the saved game holds:`](the-saved-game-holds.md) ·
[`no saved game is left`](no-saved-game-is-left.md) ·
[`a file "game.txt" is written`](a-file-is-written.md)
