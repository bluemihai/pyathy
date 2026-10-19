# nothing moves

```gherkin
Then nothing moves
```

## What it does

Checks that no line printed this turn reports a move: no line with exactly two numbers and
`to` or an arrow (`->`, `→`, `=>`) between them. "This turn" is everything printed since
the last roll; before any roll, the whole output. It is the opposite of
[`a pawn moves from 0 to 3`](moves-from-to.md).

## Why you need it

The rules that stop a pawn are as important as the ones that move it: a six is needed to
leave the start, a pawn cannot land on its own colour, an exact roll is needed to finish.
Each of those is a scenario where the roll happens and nothing moves, and this step is how
the scenario says so.

## Example

```gherkin
Feature: Race

  Scenario: without a six the pawn stays at the start
    Given I input Ann, Bob
    When Ann rolls 2
    Then nothing moves
```

The program is the race on the [`red rolls 6`](rolls.md) page: on a 2 from the start it
prints `Ann rolls 2: a six is needed to leave the start`, a line with one number, and no
move line.

## When it fails

`expected nothing to move this turn, but a line says 0 to 2`, followed by the last lines
printed. Either the program moved when it should not have, or a line of this turn that is
not a move reads like one (`round 1 to 3`, say): any two numbers with `to` between them
count.

## See also

[`a pawn moves from 0 to 3`](moves-from-to.md) ·
[`red rolls 6`](rolls.md)
