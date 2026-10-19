# I roll 6

```gherkin
When I roll 6
When I roll 3 and 4
When I roll 3, 4
```

## What it does

Fixes what the next die shows: the next time the program rolls a die, it gets 6. With two
or more numbers, the next rolls get them in that order. A die is any random call over
exactly six consecutive whole numbers: `random.randint(1, 6)`, `random.randrange(6)`,
`random.choice([1, 2, 3, 4, 5, 6])`. Then the program runs on until it asks for something
not yet scripted, or ends. Rolls and typed answers are kept apart, each used in its own
order, so it does not matter which the program asks for first.

## Why you need it

A game with dice cannot be tested by playing it: every run is different. This step makes
the dice do what the scenario says, so "doubles let you roll again" or "a six leaves the
start" can be checked once and will pass every time. The program is not changed; its
`random` calls are answered from the scenario while it runs.

## Example

```gherkin
Feature: Two dice

  Scenario: doubles
    When I roll 4 and 4
    Then "You rolled 4 and 4" is printed
    And "Doubles! Roll again." is printed

  Scenario: no doubles
    When I roll 2 and 5
    Then "Doubles!" is not printed
```

```python
import random
a, b = random.randint(1, 6), random.randint(1, 6)
print(f"You rolled {a} and {b}")
if a == b:
    print("Doubles! Roll again.")
```

## When it fails

- `rolled 0, but the program's die (random.randint(1, 6)) goes from 1 to 6`: the face is
  not on that die.
- `the program never used the scripted rolls 5`, at the end of the scenario: more rolls
  were scripted than the program made.
- A check failing with `the program is waiting for a die roll (random.randint(1, 6))`: the
  program rolled once more than the scenario scripted. Every die roll needs a step; a random
  pick that is not a die runs on without one.

## See also

[`red rolls 6`](rolls.md) ·
[`the random choice is red`](the-random-choice-is.md) ·
[`I input 4`](i-input.md)
