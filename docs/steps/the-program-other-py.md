# the program other.py

```gherkin
Given the program solver.py
```

## What it does

Picks the file the scenario runs: `solver.py` (any `.py` file next to `main.py`, a path like
`tools/solver.py` works too) instead of `main.py`. It starts nothing itself; the next step
that touches the program starts that file. It must come before that step, so it is a `Given`.

## Why you need it

A folder sometimes holds more than one program: the game and a separate solver, the program
and a small tool that converts its files. Each gets its own feature file, and the feature for
the second program opens every scenario with this step. `pyathy check` warns when the file
does not exist.

## Example

```gherkin
Feature: The solver

  Scenario: the tenth Fibonacci number
    Given the program solver.py
    When I input 10
    Then "Fibonacci 10 is 55" is printed
```

```python
# solver.py, next to main.py
n = int(input("Which Fibonacci number? "))
a, b = 0, 1
for _ in range(n):
    a, b = b, a + b
print(f"Fibonacci {n} is {a}")
```

## When it fails

- `there is no solver.py in <folder>`: the file is not next to `main.py`, or its name is
  misspelt.
- Placed after a step that started the program, it changes nothing: the run of `main.py`
  goes on. Put it first.

## See also

[`I start the program`](start-the-program.md) ·
[`I run the program with puzzle.txt --hard`](start-the-program.md)
