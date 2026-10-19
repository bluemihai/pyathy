# the file "game.txt" contains "round 4"

```gherkin
Then the file "todo.txt" contains "buy milk"
Then the file SAVE_FILE_NAME contains "round 4"
```

## What it does

Lets the program run as far as it can, then reads this file from the copy of your folder
the scenario runs in and checks that the text appears somewhere in it. Case and spaces at
the end of lines are ignored. The file may be one the program wrote, or one a `Given` put
there. An ALL_CAPS constant of the program may stand for the name, as in
[`a file "photos/beach.jpg"`](a-file.md).

## Why you need it

What the program printed is only half of what it did; what it saved is the other half, and
the next run depends on it. This step checks the file the way
[`"Hello" is printed`](is-printed.md) checks the screen: by one piece of text. For several
lines in a row, use [`the file "game.txt" contains:`](the-file-contains-lines.md).

## Example

```gherkin
Feature: To do

  Scenario: the new item is in the file
    When I input buy milk
    Then the file "todo.txt" contains "buy milk"
```

The program is the to-do list on the [`a file "game.txt" with:`](a-file-with.md) page.

## When it fails

- `expected a file "todo.txt", but the program did not write one`: there is no such file in
  the copy.
- `expected the file "todo.txt" to contain "buy milk"`: the file is there without the text.

Each ends with where the program is and its last lines. The file itself is not shown;
[`the file "game.txt" contains:`](the-file-contains-lines.md) shows the lines it expected.

## See also

[`the file "game.txt" contains:`](the-file-contains-lines.md) ·
[`a file "game.txt" is written`](a-file-is-written.md) ·
[`the saved game holds:`](the-saved-game-holds.md)
