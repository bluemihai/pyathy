# "Error" is printed 3 times

```gherkin
Then "Error" is printed 3 times
Then "That square is taken." is printed 1 time
Then exactly "Error" is printed 2 times
```

## What it does

Counts how many times the text appears in everything printed so far, and checks that the
count is exactly this number. Case, spaces at the end of lines and colour codes are
ignored, as in [`"Hello" is printed`](is-printed.md); `exactly` keeps the case. The
program runs first, until it asks for something not yet scripted or ends. Overlapping
matches are not counted twice.

## Why you need it

Some things must happen a certain number of times, no more and no fewer: a question asked
again after two wrong answers (and not after the right one), a board printed once per turn,
a message that should appear once but comes out twice because of a loop that runs one time
too many. `is printed` alone would pass all of those; the count catches them.

## Example

```gherkin
Feature: Quiz

  Scenario: one right, one wrong
    When I input 4, 7
    Then "Correct!" is printed 1 time
    And "Wrong." is printed 1 time
    And "?" is printed 2 times
```

The program is the quiz on the [`"Hello" is printed`](is-printed.md) page: two questions,
each ending in `?`, one answered right and one wrong.

## When it fails

`expected "Wrong." to be printed 1 times, but it was printed 2 times`, then where the
program is and its last lines. A count of 0 means the text is missing altogether; a count
too high often means the text is also part of another line (a prompt that repeats it, a
summary).

## See also

[`"Hello" is printed`](is-printed.md) ·
[`"Game over" is not printed`](is-not-printed.md) ·
[`"orange" is refused with a message`](is-refused-with-a-message.md)
