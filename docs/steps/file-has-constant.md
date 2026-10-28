# main.py has DEBUG = True

```gherkin
Given main.py has DEBUG = True
Given settings.py has MAX_PLAYERS = 6
```

## What it does

Before the program starts, it changes one line of the program's code: the value of the
top-level `DEBUG = …` in `main.py` becomes the Python value after the `=` (`True`, `6`,
`"easy"`, `[1, 2]`). Only the scenario's copy of the folder changes; the file in your folder
stays as it is. The name must be assigned at the top of the file, outside any function; when
it is assigned more than once there, the last one changes.

It must come before any step that starts the program (an input, a roll, a check).

## Why you need it

Some programs have a switch at the top (`DEBUG`, `HARD_MODE`, `FANCY_OUTPUT`) that changes
what they do. With this step one scenario can test the program with the switch on and
another with it off, whatever the switch is set to in your folder.

## Example

```gherkin
Feature: Greeting

  Scenario: a loud greeting
    Given main.py has LOUD = True
    When I input Ada
    Then "HELLO ADA" is printed

  Scenario: a quiet greeting
    Given main.py has LOUD = False
    When I input Ada
    Then "Hello Ada" is printed
```

```python
LOUD = False

name = input("Your name? ")
greeting = f"Hello {name}"
print(greeting.upper() if LOUD else greeting)
```

## When it fails

`main.py has no LOUD = … at the top (outside any function)`: the name is missing, or only
set inside a function. `there is no main.py`: the file name is wrong. `True ( is not a Python
value`: the value after `=` is not valid Python. `must come before any step that starts the
program`: move the step up, before the first input or check.

## See also

[`main.py has a DEBUG setting`](file-has-setting.md) ·
[`the program other.py`](the-program-other-py.md) ·
[`a file "game.txt" with:`](a-file-with.md)
