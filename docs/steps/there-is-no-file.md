# there is no file "game.txt"

```gherkin
Given there is no file "todo.txt"
Given there is no file SAVE_FILE_NAME
```

## What it does

Leaves this file out of the copy of your folder the scenario runs in, so the program starts
without it, whatever is in your own folder. An ALL_CAPS constant of the program may stand
for the name; a constant the program does not have yet names no file, and the step does
nothing.

## Why you need it

Playing the program yourself leaves files behind: a saved game, a to-do list, a high score.
A scenario about the first start ("with nothing to do yet") would then pass or fail
depending on what you did last, which is no test at all. This step makes the first start
the same every time.

## Example

```gherkin
Feature: To do

  Scenario: the first start has nothing to do
    Given there is no file "todo.txt"
    When I start the program
    Then "0 things to do:" is printed
```

The program is the to-do list on the [`a file "game.txt" with:`](a-file-with.md) page.

## When it fails

The step itself cannot fail. Placed after the program started, it removes the file from the
copy at that moment, too late for a program that read it at its start.

## See also

[`a file "game.txt" with:`](a-file-with.md) ·
[`there is no saved game`](there-is-no-saved-game.md) ·
[`no file is written`](no-file-is-written.md)
