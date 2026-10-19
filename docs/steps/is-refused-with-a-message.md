# "orange" is refused with a message

```gherkin
Then "orange" is refused with a message
```

## What it does

Looks back at the place where the scenario typed `orange` (with [`I input`](i-input.md))
and checks what came after it: a message was printed, and then the same question was asked
again. The question is the line the answer was typed on (`Pick red or green: `), or the
line above it when the answer was typed on an empty line. The message is any other
non-empty line between the answer and the repeated question. When `orange` was typed more
than once, one refusal is enough.

## Why you need it

Input checking is a rule of its own: a wrong answer is not an error and not a silent
retry; the program says what was wrong and asks again. Checking that with
[`is printed`](is-printed.md) and [`the program asks`](the-program-asks.md) takes two steps
and still does not tie the message to the answer that caused it. This step does, in one
line, in the words of the rule.

## Example

```gherkin
Feature: Pick a colour

  Scenario: a wrong colour is asked again
    When I input orange, green
    Then "orange" is refused with a message
    And "Green it is." is printed
```

```python
while True:
    colour = input("Pick red or green: ")
    if colour in ("red", "green"):
        break
    print("That is not one of the two.")
print(f"{colour.capitalize()} it is.")
```

## When it fails

- `'orange' was never typed`: no input step typed exactly that text.
- `after 'orange' was typed, the same question should be asked again ('Pick red or
  green:')`: the program took the answer, or asked something else, or ended.
- `after 'orange' was typed, a message should be printed before the question is asked
  again`: the question came back with nothing said in between.

Each ends with where the program is and its last lines.

## See also

[`I input 4`](i-input.md) ·
[`the program asks "Your name?"`](the-program-asks.md) ·
[`"Error" is printed 3 times`](is-printed-n-times.md)
