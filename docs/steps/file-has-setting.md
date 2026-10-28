# main.py has a DEBUG setting

```gherkin
Then main.py has a DEBUG setting
Given settings.py has a MAX_PLAYERS setting
```

## What it does

Checks that `main.py` has `DEBUG = …` at the top of the file, outside any function, with any
value (`DEBUG: bool = False` counts too). It only reads the file and sets nothing, so it may
come before or after the program starts. When an earlier step changed the file (for example
[`main.py has DEBUG = True`](file-has-constant.md)), it checks that changed copy.

## Why you need it

Some assignments ask for a switch at the top of the program (`DEBUG`, `HARD_MODE`) without
saying what it must be set to. This step checks the switch is there, whatever its value.

## Example

```gherkin
Feature: Hard mode

  Scenario: the program has a hard mode switch
    Then main.py has a HARD_MODE setting
```

```python
HARD_MODE = False

def main():
    tries = 3 if HARD_MODE else 10
    print(f"You have {tries} tries")

main()
```

## When it fails

`main.py has no HARD_MODE = … at the top (outside any function): put HARD_MODE = … at the top
of main.py`: the name is missing, or only set inside a function. `there is no main.py`: the
file name is wrong.

## See also

[`main.py has DEBUG = True`](file-has-constant.md) ·
[`the program other.py`](the-program-other-py.md)
