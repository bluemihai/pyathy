# there is no saved game

```gherkin
Given there is no saved game
```

## What it does

Leaves the program's save file out of the copy of your folder the scenario runs in, so the
program starts without it, whatever playing left in your folder. The save file is found in
the program's code, as for [`a saved game:`](a-saved-game.md). A program that saves nothing
yet has nothing to leave out, and the step does nothing.

## Why you need it

A scenario about a new game must start without one, every time, even after you played the
program yourself and it saved. Without this step "the first start counts from zero" would
pass or fail depending on what you did last.

## Example

```gherkin
Feature: Counter

  Scenario: a fresh start counts from zero
    Given there is no saved game
    When I start the program
    Then "Count: 0" is printed
```

The program is the counter on the
[`a file "game.txt" containing "round 3"`](a-file-containing.md) page.

## When it fails

The step itself cannot fail. Placed after the program started, it removes the file from the
copy at that moment, too late for a program that read it at its start.

## See also

[`a saved game:`](a-saved-game.md) ·
[`there is no file "game.txt"`](there-is-no-file.md) ·
[`no saved game is left`](no-saved-game-is-left.md)
