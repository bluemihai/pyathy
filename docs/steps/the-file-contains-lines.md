# the file "game.txt" contains:

```gherkin
Then the file "todo.txt" contains:
  """
  call Ada
  buy milk
  """
```

## What it does

Lets the program run as far as it can, then reads this file from the copy of your folder
the scenario runs in and checks that these lines appear in it in a row, one after the
other. The lines go between two lines of three quotes under the step; their common
indentation is removed. Case and spaces at the end of lines are ignored. An ALL_CAPS
constant of the program may stand for the name, as in
[`a file "photos/beach.jpg"`](a-file.md).

## Why you need it

The several-line form of [`the file "game.txt" contains "round 4"`](the-file-contains.md),
for a file with a shape: the order of a list, a board, a table. It holds the program to
writing the lines in that order with nothing in between, which a check per line would not.

## Example

```gherkin
Feature: To do

  Scenario: the new item goes under the old ones
    Given a file "todo.txt" containing "call Ada"
    When I input buy milk
    Then the file "todo.txt" contains:
      """
      call Ada
      buy milk
      """
```

The program is the to-do list on the [`a file "game.txt" with:`](a-file-with.md) page.

## When it fails

- `expected a file "todo.txt", but the program did not write one`: there is no such file in
  the copy.
- `expected the file "todo.txt" to contain these lines, in a row:` with the lines: they are
  not there, not in that order, or with something between them.

Each ends with where the program is and its last lines.

## See also

[`the file "game.txt" contains "round 4"`](the-file-contains.md) ·
[`the output shows:`](the-output-shows.md) ·
[`the saved game holds:`](the-saved-game-holds.md)
