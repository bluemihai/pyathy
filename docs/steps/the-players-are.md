# the players are red and green

```gherkin
Given the players are red and green
Given the players are Ann, Bob and Cy
```

## What it does

Tells pyathy the names a turn announcement may use. The turn steps ([`red rolls 6`](rolls.md),
[`red's turn is announced`](turn-is-announced.md)) look for a line naming one of the
players and no other; to do that, they need the full list. Without this step the list is
built as the scenario goes: every word typed with `I input`, and every name rolled for.
This step sets it up front, before the program starts.

## Why you need it

Some programs name the players themselves: the colours of a board game, `X` and `O`, the
computer. Nothing in the scenario types those names, so pyathy would not know them, and a
line like `green's turn` would not count as an announcement. With the names declared, the
turn checks work on such a program as they do on one where the names are typed.

## Example

```gherkin
Feature: Fixed colours

  Scenario: the program names the players itself
    Given the players are red and green
    When red rolls 4
    And green rolls 2
    Then green moves from 0 to 2
    And it is red's turn
```

```python
import random
pos = {"red": 0, "green": 0}
for turn in range(4):
    p = ["red", "green"][turn % 2]
    print(f"{p}'s turn")
    input("Press enter to roll")
    roll = random.randint(1, 6)
    print(f"pawn moves from {pos[p]} to {pos[p] + roll}")
    pos[p] += roll
```

## When it fails

The step itself cannot fail. A name missing from the list is invisible to the turn checks:
a line like `red takes green's pawn` then counts as announcing red's turn (it names one
known player and no digits), and the next `green rolls 2` fails with `expected it to be
green's turn; the last announcement was 'red takes green's pawn'`.

## See also

[`red rolls 6`](rolls.md) ·
[`red's turn is announced`](turn-is-announced.md) ·
[`I input 4`](i-input.md)
