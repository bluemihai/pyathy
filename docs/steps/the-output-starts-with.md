# the output starts with "Welcome"

```gherkin
Then the output starts with "Welcome"
```

## What it does

Lets the program run until it asks for something not yet scripted, or ends, then checks
that everything printed so far begins with this text: the very first characters, not just
the first line. Case, spaces at the end of lines and colour codes are ignored. After
[`the program is started again`](the-program-is-started-again.md) it reads the new run
from its start.

## Why you need it

A welcome line, a title, a banner: the one thing that has to come before anything else.
[`"Welcome" is printed`](is-printed.md) would pass if it came after the first question;
this step holds the program to printing it first.

## Example

```gherkin
Feature: Quiz

  Scenario: the welcome comes first
    When I start the program
    Then the output starts with "Welcome to the quiz!"
```

The program is the quiz on the [`"Hello" is printed`](is-printed.md) page.

## When it fails

`expected the output to start with "Welcome to the quiz!"`, then where the program is and
its last lines. A blank line or a cleared screen printed first is enough to fail it; so is
a prompt printed before the welcome.

## See also

[`"Hello" is printed`](is-printed.md) ·
[`the output shows:`](the-output-shows.md) ·
[`I start the program`](start-the-program.md)
