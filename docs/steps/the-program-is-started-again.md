# the program is started again

```gherkin
When the program is started again
```

## What it does

Stops the running program and starts it over in the same copy of your folder, so the files
it wrote are still there and a saved game loads. The steps after it read the new run only:
[`"Count: 2" is printed`](is-printed.md) looks at what the second run printed, and
[`the output starts with`](the-output-starts-with.md) at its first line. The file checks
still compare against the folder as it was at the first start, so what the first run wrote
counts as written. The report shows both runs. Before stopping, the answers and rolls the
first run never used are reported as a failure, like at the end of a scenario.

## Why you need it

A save-then-load check in one scenario: play, see that the game was saved, start again, see
that it continued. Without this step the two halves live in two scenarios, the second
dictating a saved game by hand, and nothing ties what the first wrote to what the second
reads. With it, the second run reads what the first actually wrote.

## Example

```gherkin
Feature: Counter

  Scenario: save, start again, it continued
    Given there is no saved game
    When I input "", ""
    And I input q
    Then a saved game is written
    When the program is started again
    Then "Count: 2" is printed
```

The program is the counter on the
[`a file "game.txt" containing "round 3"`](a-file-containing.md) page; each `""` is an empty
answer, which counts.

## When it fails

- `"the program is started again" needs a run before it: start the program first (an
  input, a roll, a check)`: it is the first step that touches the program.
- `before "the program is started again", the program never used the scripted inputs
  'q'`: the first run ended, or stopped asking, before using everything the scenario typed.
- `there is no main.py in ...` or `the program did not start`: as for
  [`I start the program`](start-the-program.md).

## See also

[`a saved game is written`](a-saved-game-is-written.md) ·
[`a saved game:`](a-saved-game.md) ·
[`I start the program`](start-the-program.md) ·
[`the program ends`](the-program-ends.md)
