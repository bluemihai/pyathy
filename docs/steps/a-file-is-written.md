# a file "game.txt" is written

```gherkin
Then a file "todo.txt" is written
Then a file SAVE_FILE_NAME is written
```

## What it does

Lets the program run as far as it can, then checks that this file is new since the program
first started, or has other contents than it had then. pyathy takes a fingerprint of every
file in the copy of your folder at the first start and compares against it, so a file that
was there and is unchanged does not count as written. An ALL_CAPS constant of the program
may stand for the name, as in [`a file "photos/beach.jpg"`](a-file.md).

## Why you need it

Saving is a rule like any other: after adding an item the list is on disk, after a move the
game is saved. This step checks that the program wrote, without saying what; for the
contents, follow it with [`the file "game.txt" contains "..."`](the-file-contains.md).

## Example

```gherkin
Feature: To do

  Scenario: adding one saves the list
    When I input buy milk
    Then "Saved." is printed
    And a file "todo.txt" is written
```

The program is the to-do list on the [`a file "game.txt" with:`](a-file-with.md) page.

## When it fails

- `expected the program to write a file "todo.txt", but it did not; it wrote no file`,
  or `...; it wrote: scores.txt`: nothing was written, or something else was, perhaps under
  another name.
- `expected the program to write the file "todo.txt", but it is as it was`: the file
  exists (it was in your folder, or a `Given` put it there), and the program did not change
  it.

Each ends with where the program is and its last lines.

## See also

[`no file is written`](no-file-is-written.md) ·
[`the file "game.txt" contains "round 4"`](the-file-contains.md) ·
[`a saved game is written`](a-saved-game-is-written.md)
