# I input 4

```gherkin
When I input 4
When I input 4, left, no
When I input "Lovelace, Ada", blue
When I input enter
When I answer 4
When I type 4
```

## What it does

Types these answers, one per question, and lets the program run until it asks for something
not yet scripted, or ends. Answers are separated by commas; an answer that holds a comma, or
starts or ends with a space, goes between double quotes. `I input enter` on its own (also
`nothing`, `an empty string`) presses enter with nothing typed; in a list, write the empty
answer as `""`, since `enter` in a list is typed as the word. `I answer`, `I type` and
`I enter` are the same step. Each answer feeds one `input()` call or one line read from
`sys.stdin`. The program keeps the answers it has not used yet, so `I input 4` then
`I input 5` is the same as `I input 4, 5`.

## Why you need it

It is the keyboard. A menu choice, a name, a move, a yes or no: every question the program
asks gets its answer from this step, and the output that follows is what the other steps
check. Answers and dice rolls are kept apart: `I input 4` then `I roll 6` works whether the
program asks for the number or rolls the die first.

## Example

```gherkin
Feature: Greeting

  Scenario: two answers, one per question
    When I input Ada, blue
    Then "Hi Ada, blue it is." is printed

  Scenario: an answer with a comma is quoted
    When I input "Lovelace, Ada", blue
    Then "Hi Lovelace, Ada, blue it is." is printed

  Scenario: just enter
    When I input enter
    And I input red
    Then "Hi , red it is." is printed
```

```python
name = input("Your name? ")
colour = input("Favourite colour? ")
print(f"Hi {name}, {colour} it is.")
```

## When it fails

- `the program never used the scripted inputs 'Bob'`, at the end of the scenario: the
  scenario typed more than the program asked for. Often the program ended, or asked fewer
  questions than expected; the lines above it show where it stopped.
- A check after it failing with `the program is waiting for input (Your name?)`: the
  program asked one more question than the scenario answered.

## See also

[`the program asks "Your name?"`](the-program-asks.md) ·
[`"orange" is refused with a message`](is-refused-with-a-message.md) ·
[`I roll 6`](i-roll.md) ·
[`red rolls 6`](rolls.md)
