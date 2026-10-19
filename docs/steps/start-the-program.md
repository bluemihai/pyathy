# I start the program / I run the program with puzzle.txt --hard

```gherkin
When I start the program
When I run the program
When I run the program with puzzle.txt --hard
When I run the program with "my puzzle.txt"
```

## What it does

Starts `main.py` in a fresh copy of your folder and lets it run until it asks for something
(an `input()`, or a die roll no step has scripted yet) or ends. `I start the program` and
`I run the program` are the same step in two wordings. `I run the program with …` also puts
the words after `with` into `sys.argv`, split like a shell does, so `puzzle.txt --hard` gives
`sys.argv == ["main.py", "puzzle.txt", "--hard"]`; an argument with spaces in it goes between
quotes.

## Why you need it

Every other step starts the program on its own when it has not started yet: `I input 4`
starts it and types 4, `"Welcome" is printed` starts it and reads the output. So the plain
form is only needed when the first thing a scenario does is look: at the welcome line, at the
first board, at the first question. The `with …` form is the one way to give the program
command-line arguments, and it must be the first step that touches the program, because
the arguments go on the command line that starts it.

## Example

```gherkin
Feature: Starting

  Scenario: the welcome line
    When I start the program
    Then "Welcome!" is printed
    And the program asks "Press enter to start:"

  Scenario: a puzzle file and a flag on the command line
    When I run the program with puzzle.txt --hard
    Then "Loading puzzle.txt" is printed
    And "Hard mode: no hints." is printed
```

```python
import sys
puzzle = sys.argv[1] if len(sys.argv) > 1 else "easy.txt"
print(f"Welcome! Loading {puzzle}")
if "--hard" in sys.argv:
    print("Hard mode: no hints.")
input("Press enter to start: ")
```

## When it fails

- `there is no main.py in <folder>`: pyathy runs from the folder that holds `main.py` (and
  `features/`); run it from there, or name another file with
  [`the program other.py`](the-program-other-py.md).
- `"I run the program with ..." must come before any step that starts the program (an input,
  a roll, a check): it has already started`: move the step up.
- `the program did not start`: the program printed nothing, asked nothing and did not end
  within 10 seconds of starting (an import that hangs, say).

## See also

[`the program other.py`](the-program-other-py.md) ·
[`the program may take 30 seconds`](the-program-may-take.md) ·
[`I input 4`](i-input.md) ·
[`the program is started again`](the-program-is-started-again.md)
