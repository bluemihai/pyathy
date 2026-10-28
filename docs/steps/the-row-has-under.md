# the "Bob" row has "7" under "Score"

```gherkin
Then the "Bob" row has "7" under "Score"
Then the "Bob" row has nothing under "Score"
```

## What it does

Lets the program run until it asks for something not yet scripted, or ends, then reads the
last table it printed that has a header cell `Score`. Cells are split on `│` or `|`; border
lines like `├────┼────┤` or `|----|----|` are skipped. The row is the first one under the
header with a cell that is `Bob`, else the first with a cell that has `Bob` in it. The step
checks the cell of that row in the `Score` column: it is `7` (case and spaces around it
ignored), or with `nothing`, it is empty.

A table lined up with spaces only, without `│` or `|`, is not read: use
[`the line with "Bob" also has "7"`](the-line-with-also-has.md) for it.

## Why you need it

In a table, a number printed somewhere is not enough: it must be in the right row and the
right column. An empty cell is impossible to check with `is printed` at all.

## Example

```gherkin
Feature: Scores

  Scenario: Ann scored, Bob did not
    When I input Ann, 12, Bob, skip
    Then the "Ann" row has "12" under "Score"
    And the "Bob" row has nothing under "Score"
```

```python
scores = {}
for _ in range(2):
    name = input("Name: ")
    score = input("Score (or skip): ")
    scores[name] = "" if score == "skip" else score
print("│ Name │ Score │")
for name, score in scores.items():
    print(f"│ {name:<4} │ {score:>5} │")
```

## When it fails

`expected a table with a column "Score"`: no table was printed with that header cell (check
the spelling, or whether the table uses `│` or `|`). `expected a row with "Bob"`: the table has
no such row. `expected the "Bob" row to have "7" under "Score", but it has "5"`, with the row's
cells under it.

## See also

[`the line with "Total" also has "42"`](the-line-with-also-has.md) ·
[`the output shows:`](the-output-shows.md)
