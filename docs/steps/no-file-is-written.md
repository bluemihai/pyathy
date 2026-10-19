# no file is written

```gherkin
Then no file is written
```

## What it does

Lets the program run as far as it can, then checks that no file in the copy of your folder
is new since the program first started, and none has other contents than it had then. The
opposite of [`a file "game.txt" is written`](a-file-is-written.md), for every file at once.

## Why you need it

Not saving is a rule too: quitting without a change leaves the list alone, a refused move
is not saved, looking at the high scores does not rewrite them. A program that writes on
every run, or writes a file it should not, is caught here.

## Example

```gherkin
Feature: To do

  Scenario: quitting at once saves nothing
    When I input enter
    Then no file is written
```

The program is the to-do list on the [`a file "game.txt" with:`](a-file-with.md) page:
an empty answer to "Add one" ends it without writing.

## When it fails

`expected the program to write no file; it wrote: todo.txt`, then where the program is and
its last lines. The list names every file that is new or changed, so a log or a cache the
program writes as a side effect shows up here too.

## See also

[`a file "game.txt" is written`](a-file-is-written.md) ·
[`there is no file "game.txt"`](there-is-no-file.md) ·
[`no saved game is left`](no-saved-game-is-left.md)
