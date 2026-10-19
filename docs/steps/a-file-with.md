# a file "game.txt" with:

```gherkin
Given a file "todo.txt" with:
  """
  buy milk
  call Ada
  """
```

## What it does

Writes a file with this name and these lines (each ending in a newline) into the program's
folder before the program starts. The lines go between two lines of three quotes under the
step; their common indentation is removed. The scenario runs in a copy of your folder, so
your own files are never touched. An ALL_CAPS constant of the program may stand for the
name, as in [`a file "photos/beach.jpg"`](a-file.md).

## Why you need it

The several-line form of [`a file "game.txt" containing "round 3"`](a-file-containing.md):
a to-do list, a board, a puzzle, a table of scores. The scenario shows the file as it is,
line by line, and the checks that follow are about how the program reads it.

## Example

```gherkin
Feature: To do

  Scenario: the list in the file is shown
    Given a file "todo.txt" with:
      """
      buy milk
      call Ada
      """
    When I start the program
    Then "2 things to do:" is printed
    And "2. call Ada" is printed
```

```python
import os
todos = open("todo.txt").read().splitlines() if os.path.exists("todo.txt") else []
print(f"{len(todos)} things to do:")
for i, todo in enumerate(todos, 1):
    print(f"{i}. {todo}")
new = input("Add one (or enter to quit): ")
if new:
    todos.append(new)
    with open("todo.txt", "w") as f:
        f.write("\n".join(todos) + "\n")
    print("Saved.")
```

## When it fails

The step itself cannot fail with a quoted name; with a constant the program lacks,
`main.py has no SAVE_FILE_NAME (...)`. A program that cannot read the file crashes, and the
next check reports the traceback.

## See also

[`a file "game.txt" containing "round 3"`](a-file-containing.md) ·
[`there is no file "game.txt"`](there-is-no-file.md) ·
[`the file "game.txt" contains:`](the-file-contains-lines.md) ·
[`a saved game:`](a-saved-game.md)
