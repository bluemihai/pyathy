# no saved game is left

```gherkin
Then no saved game is left
```

## What it does

Lets the program run as far as it can, then checks that the program's save file is gone
from the copy of your folder, or is there but empty (nothing but whitespace), so the next
start is a new game. The save file is found in the program's code, as for
[`a saved game:`](a-saved-game.md).

## Why you need it

Ending a game cleanly means the next start does not pick it up again: after a win, after
"new game", after "delete my save". Whether the program removes the file or empties it,
this step accepts both; what it refuses is a save file that still holds a game.

## Example

```gherkin
Feature: Counter

  Scenario: a new game removes the save
    Given a saved game:
      """
      3
      """
    When I input n
    Then "Count: 0" is printed
    And no saved game is left
```

The program is the counter on the
[`a file "game.txt" containing "round 3"`](a-file-containing.md) page: `n` resets the count
and removes `count.txt`.

## When it fails

`expected the save file "count.txt" to be removed (or emptied), but it still holds a game`,
then where the program is and its last lines. Or `pyathy can't tell which file your program
saves to: ...`, see [`a saved game:`](a-saved-game.md).

## See also

[`there is no saved game`](there-is-no-saved-game.md) ·
[`a saved game is written`](a-saved-game-is-written.md) ·
[`no file is written`](no-file-is-written.md)
