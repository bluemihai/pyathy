# "Hello" is printed

```gherkin
Then "Hello" is printed
Then exactly "Hello" is printed
```

## What it does

Lets the program run until it asks for something not yet scripted, or ends, then checks that
the text appears somewhere in everything printed so far, prompts included. Case is ignored,
so are spaces at the end of lines and any colour codes the program prints; `exactly "Hello"`
keeps the case. The text may be part of a line: `"wins!"` matches `Player X wins!`. With a
count (`is printed 3 times`) it checks the number of times, see
[`"Error" is printed 3 times`](is-printed-n-times.md).

## Why you need it

It is the basic check: after the scenario typed its answers and rolled its dice, did the
program say the thing? The winner, the error message, the score, the goodbye. Most
scenarios end in one or more of these.

## Example

```gherkin
Feature: Quiz

  Scenario: a right answer
    When I input 4
    Then "Correct!" is printed

  Scenario: the full score
    When I input 4, 9
    Then "Score: 2 of 2" is printed
    And exactly "Score: 2 of 2" is printed
```

```python
print("Welcome to the quiz!")
score = 0
for question, answer in [("2+2?", "4"), ("3*3?", "9")]:
    if input(question + " ") == answer:
        score += 1
        print("Correct!")
    else:
        print("Wrong.")
print(f"Score: {score} of 2")
```

## When it fails

`expected "Correct!" to be printed, but it was not`, then where the program is (`the
program is waiting for input (3*3?)`, `the program has ended`, or `the program crashed:` with
the traceback) and its last lines. When the text is there but with other spacing or
punctuation, the last lines show it; a crash means the program never got that far.

## See also

[`"Error" is printed 3 times`](is-printed-n-times.md) ·
[`"Game over" is not printed`](is-not-printed.md) ·
[`the output shows:`](the-output-shows.md) ·
[`the output starts with "Welcome"`](the-output-starts-with.md) ·
[`the program asks "Your name?"`](the-program-asks.md)
