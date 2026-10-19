# red rolls 6

```gherkin
When red rolls 6
When Ann rolls 4+6
When Ann rolls 4 and 6
```

## What it does

One turn of a dice game, in one step. First pyathy checks that it is red's turn: the last
line that announces a turn names red and no other player, and has no digits in it
(`Player red:`, `***** red's turn *****`). Then, if the program is waiting at an `input()`
(a "press enter to roll" prompt), it presses enter; then the next die shows 6 (or the two
dice 4 and 6), and the program runs on until it asks for something else, or ends. The name
is added to the players pyathy knows, so a later announcement check can tell it from the
others.

## Why you need it

A turn-based game reads better as a game than as keystrokes: `red rolls 6` says what
happens, where `I input enter` plus `I roll 6` only says how. The turn check is the point:
the step fails when the program skipped a player, let one go twice, or forgot to say whose
turn it is, which `I roll 6` alone would never notice.

## Example

```gherkin
Feature: Race

  Scenario: a six leaves the start, a three does not
    Given I input Ann, Bob
    When Ann rolls 6
    Then Ann moves from 0 to 6
    When Bob rolls 3
    Then "Bob rolls 3: a six is needed to leave the start" is printed
```

```python
import random
players = [input("Player 1: "), input("Player 2: ")]
pos = {p: 0 for p in players}
turn = 0
while max(pos.values()) < 20:
    p = players[turn % 2]
    print(f"Player {p}:")
    input("Press enter to roll")
    roll = random.randint(1, 6)
    if pos[p] == 0 and roll != 6:
        print(f"{p} rolls {roll}: a six is needed to leave the start")
    else:
        print(f"{p} rolls {roll}")
        print(f"Pawn moves from {pos[p]} to {pos[p] + roll}")
        pos[p] += roll
    turn += 1
```

## When it fails

- `expected it to be red's turn, but no line announced anyone's turn (one naming the player
  and no other, without digits, like 'Player red:')`: no such line, or every candidate line
  also holds a number (a score, a position).
- `expected it to be red's turn; the last announcement was 'Player green:'`: the turn went
  to someone else.
- `expected red to roll, but it cannot:` then `the program has ended` or `the program
  crashed:`: there is no turn to take.

## See also

[`red rolls 3 and picks 2`](rolls-and-picks.md) ·
[`these turns are played 3 times:`](these-turns-are-played.md) ·
[`the players are red and green`](the-players-are.md) ·
[`red's turn is announced`](turn-is-announced.md) ·
[`a pawn moves from 0 to 3`](moves-from-to.md) · [`I roll 6`](i-roll.md)
