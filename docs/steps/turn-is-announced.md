# red's turn is announced / it is red's turn

```gherkin
Then red's turn is announced
Then it is red's turn
```

## What it does

Checks that a line of the output so far announces red's turn: a line that names red, names
no other player, and has no digits in it (`Player red:`, `It is red's turn!`). The two
wordings are the same step. Any such line counts, not only the last one, so after several
turns it says red had a turn at some point; for "whose turn is it now", put it right after
the turn before, as in the example. The name is added to the players pyathy knows.

## Why you need it

The first thing a turn-based game has to get right is saying whose turn it is, and this
is the check for it, on its own: before any dice, does the program announce the first
player? After a turn, does it hand over to the next? The same check runs inside
[`red rolls 6`](rolls.md) before every roll; this step is for the places where no roll
follows, such as the start of the game or the turn after the last roll of the scenario.

## Example

```gherkin
Feature: Race

  Scenario: turns alternate
    Given I input Ann, Bob
    Then Ann's turn is announced
    When Ann rolls 6
    Then it is Bob's turn
```

The program is the race on the [`red rolls 6`](rolls.md) page: it prints `Player Ann:`
before each of Ann's turns.

## When it fails

`expected a line announcing red's turn: one naming red (and no other player), without
digits, like 'Player red:'`, followed by the last lines printed. Common causes: the line
also holds a number (`Player red (score 3):`), it names two players (`red to play, green
waits`), or the name is spelt differently in the program.

## See also

[`red rolls 6`](rolls.md) ·
[`the players are red and green`](the-players-are.md) ·
[`a pawn moves from 0 to 3`](moves-from-to.md)
