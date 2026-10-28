# the line with "Total" also has "42"

```gherkin
Then the line with "Total" also has "42"
```

## What it does

Lets the program run until it asks for something not yet scripted, or ends, then finds the
last line it printed with the first text in it and checks that the same line also has the
second text. Case is ignored, and so are colour codes. The answers typed into the program are
not part of a line.

## Why you need it

`"42" is printed` passes when 42 is printed anywhere, even in another line. This step ties the
two together: the total is 42, not some other number on the screen.

## Example

```gherkin
Feature: Shopping list

  Scenario: the total of two items
    When I input 30, 12, done
    Then the line with "Total" also has "42"
```

```python
total = 0
while (price := input("Price (or done): ")) != "done":
    total += int(price)
print(f"Total: {total}")
```

## When it fails

`expected a line with "Total", but no line printed has it`, or `expected the last line with
"Total" to also have "42", but it is:` with that line under it. When the line is printed more
than once, only the last one counts.

## See also

[`"Hello" is printed`](is-printed.md) ·
[`the "Bob" row has "7" under "Score"`](the-row-has-under.md)
