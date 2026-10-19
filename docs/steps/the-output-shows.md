# the output shows:

```gherkin
Then the output shows:
  """
  X . .
  . X .
  . . .
  """
```

## What it does

Lets the program run until it asks for something not yet scripted, or ends, then checks
that these lines appear in the output in a row, one after the other, with nothing between
them. The lines go between two lines of three quotes under the step; their common
indentation is removed, so the `"""` lines set the left edge. Case, spaces at the end of
lines and colour codes are ignored. When it fails, the report shows a `+`/`-` diff against
what was printed.

## Why you need it

A board, a table, a tree, a receipt: anything that is a shape rather than a sentence. One
[`"X . ." is printed`](is-printed.md) per line would pass with the rows in the wrong order,
or with other lines between them; this step checks the whole block as it is.

## Example

```gherkin
Feature: Board

  Scenario: two crosses on the diagonal
    When I input 1 1, 2 2
    Then the output shows:
      """
      X . .
      . X .
      . . .
      """
```

```python
board = [["." for _ in range(3)] for _ in range(3)]
while True:
    for row in board:
        print(" ".join(row))
    move = input("Square (row col), or q: ")
    if move == "q":
        break
    r, c = (int(n) - 1 for n in move.split())
    board[r][c] = "X"
print("Bye!")
```

## When it fails

`expected these lines, in a row:` with the lines, then where the program is and its last
lines, as a diff. Usual causes: a line between the expected ones (a blank line the program
prints between rows), a space more or fewer inside a line (`X .  .`), or the block as a
whole never printed because the program stopped earlier.

## See also

[`"Hello" is printed`](is-printed.md) ·
[`the output starts with "Welcome"`](the-output-starts-with.md) ·
[`the file "game.txt" contains:`](the-file-contains-lines.md)
