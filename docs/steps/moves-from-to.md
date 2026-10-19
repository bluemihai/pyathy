# a pawn moves from 0 to 3

```gherkin
Then a pawn moves from 0 to 3
Then red moves from 0 to 3
```

## What it does

Checks that a line printed this turn reports a move from 0 to 3: a line with exactly two
numbers in it, 0 then 3, and `to` or an arrow (`->`, `→`, `=>`) between them, like
`Pawn moving from 0 to 3.` or `red: 0 -> 3`. "This turn" is everything printed since the last
roll (`I roll 6` or `red rolls 6`); before any roll, it is the whole output. The two wordings
are the same check: the name in `red moves from 0 to 3` is for the reader, it is not matched
against the line.

## Why you need it

Where a pawn ends up is the heart of a board game, and it depends on the roll, the square
it was on, and the rules in between (a six to leave the start, a ladder, a bump). Dictating
the roll with a turn step and checking the move with this one tests exactly that rule.
Reading only this turn's output keeps an earlier `0 to 3` from satisfying a later check.

## Example

```gherkin
Feature: Race

  Scenario: a pawn on the board moves by the roll
    Given I input Ann, Bob
    When Ann rolls 6
    Then Ann moves from 0 to 6
    When Bob rolls 6
    And Ann rolls 3
    Then a pawn moves from 6 to 9
```

The program is the race on the [`red rolls 6`](rolls.md) page. Its move line is
`Pawn moves from 6 to 9`, on its own: a line that also held the roll, like
`Ann rolls 3: pawn moves from 6 to 9`, has three numbers and would not count.

## When it fails

`expected a line of this turn to say red moves from 0 to 3: the two squares in that order,
like 'Pawn moving from 0 to 3.'`, followed by the last lines printed. Check that the line has
no third number (the roll, a turn counter), that the squares are in `from to` order, and
that the check comes right after the roll it belongs to: after `Bob rolls 6`, Ann's move is
no longer "this turn".

## See also

[`nothing moves`](nothing-moves.md) ·
[`red rolls 6`](rolls.md) ·
[`I roll 6`](i-roll.md)
