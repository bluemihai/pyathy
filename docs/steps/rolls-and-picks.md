# red rolls 3 and picks 2

```gherkin
When red rolls 3 and picks 2
When Ann rolls 4+6 and answers y
```

## What it does

[`red rolls 3`](rolls.md), then the answer: after the roll the program must ask something
(an `input()` of this same turn, before any new turn is announced), and the step types 2 at
it. `picks` and `answers` are the same step. Then the program runs on until it asks for
something else, or ends.

## Why you need it

Many turns are a roll followed by one question: which pawn to move, whether to buy the
street you landed on, whether to roll again. Writing the roll and the answer as one step
keeps a scenario one line per turn, and adds a check: the program has to ask after the
roll. A program that moves without asking, or that goes straight to the next player, fails
here.

## Example

```gherkin
Feature: Two pawns each

  Scenario: Ann moves the same pawn twice
    Given I input Ann, Bob
    When Ann rolls 5 and picks A
    And Bob rolls 2 and answers b
    And Ann rolls 3 and picks A
    Then a pawn moves from 5 to 8
```

```python
import random
players = [input("Player 1: "), input("Player 2: ")]
pawns = {p: {"A": 0, "B": 0} for p in players}
for turn in range(4):
    p = players[turn % 2]
    print(f"Player {p}:")
    input("Press enter to roll")
    roll = random.randint(1, 6)
    print(f"{p} rolls {roll}")
    pawn = input("Move pawn A or B? ").upper()
    print(f"Pawn {pawn} moves from {pawns[p][pawn]} to {pawns[p][pawn] + roll}")
    pawns[p][pawn] += roll
```

## When it fails

- The turn checks of [`red rolls 6`](rolls.md), when it is not red's turn.
- `red rolled and should have been asked something (to answer '2'), but the program asked
  nothing`: the program ended, or is waiting for a die, not for input.
- `red rolled and should have been asked something (to answer '2'), but the program went on
  to green's turn`: the question came too late, or not at all.

## See also

[`red rolls 6`](rolls.md) ·
[`I input 4`](i-input.md) ·
[`these turns are played 3 times:`](these-turns-are-played.md)
