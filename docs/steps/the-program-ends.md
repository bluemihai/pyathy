# the program ends

```gherkin
Then the program ends
```

## What it does

Lets the program run as far as it can, then checks that it has ended on its own: it ran off
the end of `main.py`, or called `sys.exit()`, or `quit()`. The exit code is not checked. A
crash is not an ending: a program that stops with an exception fails this step.

## Why you need it

Stopping is part of the game: after the last question, after "q", after "Play again? n",
the program must be finished, not waiting for one more answer. This step is also how a
scenario says "and it did not crash": a scenario that only checks the output would pass
when the program printed the right thing and then threw an exception.

## Example

```gherkin
Feature: Quiz

  Scenario: after two answers the quiz is over
    When I input 4, 9
    Then "Score: 2 of 2" is printed
    And the program ends
```

The program is the quiz on the [`"Hello" is printed`](is-printed.md) page: two questions,
then the score, then the end.

## When it fails

- `expected the program to end`, then `the program is waiting for input (...)` and its
  last lines: it asked one more question than the scenario expected.
- `expected the program to end, but it crashed`, then the traceback, through the
  program's own files.

## See also

[`the program is still running`](the-program-is-still-running.md) ·
[`the program is started again`](the-program-is-started-again.md) ·
[`"Hello" is printed`](is-printed.md)
