# a file "photos/beach.jpg"

```gherkin
Given a file "photos/beach.jpg"
Given a file SAVE_FILE_NAME
```

## What it does

Puts an empty file with this name in the program's folder before the program starts, making
its folders too (`photos/` here). The scenario runs in a copy of your folder, so the file is
created in the copy and your own folder is never touched. Instead of a quoted name, an
ALL_CAPS constant of the program (`SAVE_FILE_NAME`) names the file the program assigns to
that constant, read from the code; renaming the file in the program then needs no change in
the scenario.

## Why you need it

A program that lists, counts or opens files needs some to be there, and what matters is
usually the name, not the contents: a photo browser, a file picker, a check that "the
file already exists". The scenario says which files exist, so it does not depend on what
happens to be in your folder.

## Example

```gherkin
Feature: Photos

  Scenario: two photos in the folder
    Given a file "photos/beach.jpg"
    And a file "photos/dunes.jpg"
    When I start the program
    Then "2 photos:" is printed
    And "dunes.jpg" is printed
```

```python
import os
photos = sorted(os.listdir("photos")) if os.path.isdir("photos") else []
print(f"{len(photos)} photos:")
for photo in photos:
    print(" ", photo)
```

## When it fails

The step itself cannot fail with a quoted name. With a constant:
`main.py has no SAVE_FILE_NAME (the scenario needs it: put SAVE_FILE_NAME = "…" at the
top of main.py; ...)`. Placed after the program started, the file is written into the
copy at that moment, too late for a program that read the folder at its start.

## See also

[`a file "game.txt" containing "round 3"`](a-file-containing.md) ·
[`a file "game.txt" with:`](a-file-with.md) ·
[`there is no file "game.txt"`](there-is-no-file.md) ·
[`a file "game.txt" is written`](a-file-is-written.md)
