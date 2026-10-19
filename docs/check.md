# `pyathy check`: find mistakes in the feature files

`python pyathy check` reads the feature files without running the program and lists, per
file, what would stop a scenario before it starts:

1. a line no step matches, with the closest step written with your values
   (`did you mean: I input Ada`), else a pointer to `pyathy steps`;
2. a file that is not valid Gherkin (a line in a scenario that starts with no keyword);
3. a scenario or step indented differently from the others in its file, or with a tab;
4. a file step pyathy cannot find in the program: a saved-game step when it can't tell which
   file the program saves to, `a file SAVE_FILE_NAME …` when main.py has no such constant,
   `the program other.py` when there is no other.py.

It ends with `n problems in m of k files` (or `no problems in k files`) and exits with 1 when
it found something. `python pyathy check features/game.feature` checks one file.
`--json` prints the same as JSON (each problem's line, columns, message and suggested text,
plus the step list) for an editor; the pyathy VS Code extension uses it for its squiggles.

```
✘ features/greeter.feature
      line 4: pyathy has no step that matches
          When I imput Ada
      did you mean: I input Ada

      line 6: indented 6 spaces, the other steps 4

2 problems in 1 of 1 file
```
