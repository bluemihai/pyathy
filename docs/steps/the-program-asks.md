# the program asks "Your name?"

```gherkin
Then the program asks "Your name?"
Then the program asks "Your move"
```

## What it does

Lets the program run until it asks for something not yet scripted, or ends, then checks
two things: the program is now waiting at an `input()` (or a read from `sys.stdin`), and
this text is in the last part of what it printed (the question itself, or the lines just
before it). The text may be a part of the question. Case, spaces at the end of lines and
colour codes are ignored.

## Why you need it

It says where the program stands: after a taken square it must ask for a square again;
after a win it must ask "Play again?"; at the start it must ask the first question, not
print the whole game. It is also the check that the program has not ended or crashed
when it should be waiting for the player, since only a waiting program passes.

## Example

```gherkin
Feature: Quiz

  Scenario: the second question follows the first answer
    When I input 4
    Then the program asks "3*3?"
```

The program is the quiz on the [`"Hello" is printed`](is-printed.md) page.

## When it fails

`expected the program to ask "3*3?"`, then where the program is and its last lines.
`the program has ended` or `the program crashed:` means it is not waiting at all;
`the program is waiting for a die roll (random.randint(1, 6))` means it wants a roll, not
an answer; with `the program is waiting for input (...)`, the question is another one, or
worded differently, as the last lines show.

## See also

[`I input 4`](i-input.md) ·
[`"orange" is refused with a message`](is-refused-with-a-message.md) ·
[`the program is still running`](the-program-is-still-running.md) ·
[`"Hello" is printed`](is-printed.md)
