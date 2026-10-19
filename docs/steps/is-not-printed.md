# "Game over" is not printed

```gherkin
Then "Game over" is not printed
```

## What it does

Lets the program run until it asks for something not yet scripted, or ends, then checks
that the text appears nowhere in everything printed so far. Case, spaces at the end of
lines and colour codes are ignored, as in [`"Hello" is printed`](is-printed.md).

## Why you need it

Half of a rule is what must not happen: no winner on a draw, no "Doubles!" on a 2 and a
5, no error message on a valid move, no second question after the right answer. The check
reads what the program has printed up to this point, so a scenario that wants "it is never
printed" ends the game first (or checks that [`the program ends`](the-program-ends.md)).

## Example

```gherkin
Feature: Quiz

  Scenario: two right answers
    When I input 4, 9
    Then "Wrong." is not printed
```

The program is the quiz on the [`"Hello" is printed`](is-printed.md) page.

## When it fails

`expected "Wrong." NOT to be printed, but it was`, then where the program is and its last
lines, which show the line it appeared in. A short text also matches inside a longer one:
`"win"` is found in `window`; pick a text that only the unwanted line has.

## See also

[`"Hello" is printed`](is-printed.md) ·
[`"Error" is printed 3 times`](is-printed-n-times.md) ·
[`nothing moves`](nothing-moves.md)
