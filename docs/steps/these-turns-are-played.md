# these turns are played 3 times:

```gherkin
When these turns are played 3 times:
  | red rolls 5   |
  | green rolls 2 |
When these turns are played 1 time:
  | Ann rolls 1+1 and answers n |
```

## What it does

Runs the steps in the table, one per row, in order, that many times. A row is any step
written as it would be on its own line (a built-in, or one of the folder's own steps from a
`*_steps.py`; when both match, the folder's own wins). The table is Gherkin's data table:
each row between `|` bars, indented under the step.

## Why you need it

A game often has to be played some way in before the interesting part: passing Start needs
a lap, a win needs enough turns to reach the end. Writing every turn out makes a scenario
long and hides what it is about. This step plays a round of turns a given number of times,
and every turn in it is still checked like a step on its own line, so a program that gets
the turn order wrong on lap three is caught.

## Example

```gherkin
Feature: Race

  Scenario: two rounds of sixes
    Given I input Ann, Bob
    When these turns are played 2 times:
      | Ann rolls 6 |
      | Bob rolls 6 |
    Then "Pawn moves from 6 to 12" is printed 2 times
    And it is Ann's turn
```

The program is the race on the [`red rolls 6`](rolls.md) page: each player's first six
moves a pawn from 0 to 6, the second from 6 to 12.

## When it fails

- `no step matches the table row 'red rols 5'`: a typo in a row; `pyathy steps` lists what
  can be written there.
- Any failure of the row's own step, with that step's message, the first time it fails;
  the report shows how far the program got.

## See also

[`red rolls 6`](rolls.md) ·
[`red rolls 3 and picks 2`](rolls-and-picks.md) ·
[`red's turn is announced`](turn-is-announced.md)
