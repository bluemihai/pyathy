# the program is still running

```gherkin
Then the program is still running
```

## What it does

Lets the program run as far as it can, then checks that it is waiting for something: an
answer, or a die roll. The opposite of [`the program ends`](the-program-ends.md). It does
not say what the program is waiting for; [`the program asks "..."`](the-program-asks.md)
checks that.

## Why you need it

Some rules are about going on: a game that is not over after a draw-free move, a menu that
comes back after an action, a loop that must not stop on an unexpected answer. This step
says the program is still there without tying the scenario to the exact words of its next
question.

## Example

```gherkin
Feature: Quiz

  Scenario: after one answer the quiz goes on
    When I input 4
    Then the program is still running
```

The program is the quiz on the [`"Hello" is printed`](is-printed.md) page: after the
first answer it is waiting at the second question.

## When it fails

`expected the program to still be running`, then `the program has ended` or `the program
crashed:` with the traceback, and the last lines printed.

## See also

[`the program ends`](the-program-ends.md) ·
[`the program asks "Your name?"`](the-program-asks.md) ·
[`the program may take 30 seconds`](the-program-may-take.md)
