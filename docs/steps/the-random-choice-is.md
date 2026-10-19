# the random choice is red

```gherkin
Given the random choice is red
Given the random pick is red, blue
Given the random number is 42
```

## What it does

Fixes what the next random pick returns, when that pick is not a die: `random.choice`,
`random.randint` over a range that is not six long, `random.random()`, and so on. A number is
given as a number (`42`, `0.25`), anything else as the text of the option, matched against
the program's own options so the program gets its own object back. Several values, separated
by commas, serve the next several picks. `choice`, `pick` and `number` are the same step.
A pick that no step fixed returns the first option (a `random.random()` returns 0.0), so a
program with randomness in it runs without this step; the step is for the case where the
scenario needs a particular outcome.

## Why you need it

A secret colour, a shuffled deck, a computer opponent's move: anything the program draws at
random would make the outcome of a scenario change from run to run. This step pins the draw
to the value the scenario is about, so "a right guess is congratulated" can be written once
and checked every time.

## Example

```gherkin
Feature: Guess the colour

  Scenario: a right guess
    Given the random choice is green
    When I input green
    Then "Right!" is printed

  Scenario: a wrong guess
    Given the random choice is blue
    When I input green
    Then "No, it was blue." is printed
```

```python
import random
secret = random.choice(["red", "green", "blue"])
guess = input("Guess the colour: ")
print("Right!" if guess == secret else f"No, it was {secret}.")
```

## When it fails

The step itself does not fail; a value that is not among the program's options is handed to
the program as it is, and the check after it shows what the program did with it. A value
that is never used is simply left over.

## See also

[`I roll 6`](i-roll.md) ·
[`I input 4`](i-input.md)
