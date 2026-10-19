# a file "game.txt" containing "round 3"

```gherkin
Given a file "count.txt" containing "3"
Given a file SAVE_FILE_NAME containing "round 3"
```

## What it does

Writes a one-line file with this name and this text (plus a newline) into the program's
folder before the program starts. The scenario runs in a copy of your folder, so your own
files are never touched; the copy's file is replaced if one was there. An ALL_CAPS constant
of the program may stand for the name, as in [`a file "photos/beach.jpg"`](a-file.md).

## Why you need it

A program that reads a setting, a high score or a count from a file has to be tested from
a known file: this step dictates it, in the scenario, so the check that follows
("it continues from 3") is about the program's reading, not about what a previous run left
behind. For a file of several lines, use [`a file "game.txt" with:`](a-file-with.md).

## Example

```gherkin
Feature: Counter

  Scenario: it continues from the count in the file
    Given a file "count.txt" containing "3"
    When I start the program
    Then "Count: 3" is printed
```

```python
import os
count = int(open("count.txt").read()) if os.path.exists("count.txt") else 0
print(f"Count: {count}")
while True:
    key = input("Enter to count, n for a new game, q to quit: ")
    if key == "q":
        break
    if key == "n":
        count = 0
        if os.path.exists("count.txt"):
            os.remove("count.txt")
    else:
        count += 1
        with open("count.txt", "w") as f:
            f.write(f"{count}\n")
    print(f"Count: {count}")
```

## When it fails

The step itself cannot fail with a quoted name; with a constant the program lacks,
`main.py has no SAVE_FILE_NAME (...)`. A program that cannot read the file crashes, and the
next check reports the traceback.

## See also

[`a file "game.txt" with:`](a-file-with.md) ·
[`a file "photos/beach.jpg"`](a-file.md) ·
[`a saved game:`](a-saved-game.md) ·
[`the file "game.txt" contains "round 4"`](the-file-contains.md)
