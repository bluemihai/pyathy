# the program may take 30 seconds

```gherkin
Given the program may take 30 seconds
Given the program may take 2.5 seconds
```

## What it does

Raises the silence limit for the rest of the scenario: pyathy waits up to this many
seconds, instead of 10, for the program to print something, ask something or end. It also
raises the running limit (60 seconds, see below) to this number when it is larger. It does
not slow anything down: a program that answers in a second still passes in a second.

## Why you need it

An endless loop and a slow program look the same from outside: nothing happens. pyathy
tells them apart with two clocks. The first is for silence: when the program has printed
nothing and asked nothing for 10 seconds, the step fails. The second is for running: when
the program has kept going for 60 seconds without ever asking for input (printing all the
while, say), the step fails too. A program that genuinely needs longer, such as a solver that
searches for 12 seconds before printing its answer, trips the first clock, and this step is
how a scenario says that is fine. It does not hide a real endless loop: a loop that stays
silent fails after 30 seconds instead of 10. `time.sleep()` returns at once under pyathy,
so a countdown or a pause for effect never needs this step; only real work does.

## Example

```gherkin
Feature: A slow search

  Scenario: the search takes a while
    Given the program may take 30 seconds
    When I start the program
    Then "Found 7 solutions" is printed
```

```python
import time
print("Searching...")
count, deadline = 0, time.monotonic() + 12
while time.monotonic() < deadline:
    count += 1
print("Found 7 solutions")
```

Without the step, that scenario fails after 10 seconds; with it, it passes after 12.

## When it fails

The step itself cannot fail; the limits it raises can. Without it, or with a number that is
still too small:

- `the program printed nothing and asked nothing for 10 seconds (an endless loop? if it is
  just slow, add the step 'Given the program may take 30 seconds')`
- `the program kept running for 60 seconds without asking for anything (an endless loop? if
  it is just slow, add the step 'Given the program may take 120 seconds')`

Both end with the last lines the program printed, which usually show where it was.

## See also

[`I start the program`](start-the-program.md) ·
[`the program is still running`](the-program-is-still-running.md) ·
[`the program ends`](the-program-ends.md)
