# Running pyathy and reading the report

From the folder that holds `main.py` and `features/` (write `python pyathy …` when pyathy is
the folder next to `main.py`, `poetry run pyathy …` under Poetry):

```
pyathy                      run every features/*.feature against main.py
pyathy features/x.feature   run only that file (or folder)
pyathy check                find mistakes in the feature files, without running main.py
pyathy init                 create features/hello.feature (and a main.py) to start from
pyathy steps                every step you can use (plus your own, from features/*_steps.py)
pyathy -h                   usage and an example feature
```

Options, each with a short and a long form:

```
-q,  --quiet              only one line per scenario (a ✘ gets one reason line) and the total
-ff, --fail-fast          stop at the first scenario that fails
-nf, --next-failure       run the scenarios that failed last time, in order, stopping at the first that still fails
-s,  --solution [FOLDER]  run the features here against ./_solution/main.py, or ./FOLDER/main.py (-s obj2 means _solution-obj2)
-h,  --help               this help
-v,  --version            pyathy's version and where it runs from
```

`--next-failure` (as in rspec) reads the failures pyathy remembered in `.pyathy/last-run.json`
(rewritten after every run; safe to gitignore); when all of them pass it runs everything else.
A runner that must not write into the program's folder (a teacher's acceptance-test install)
sets `PYATHY_LASTRUN` to the folder whose `.pyathy/last-run.json` pyathy reads and rewrites instead.
`--solution` is for the teacher's folder, where the reference program sits in `_solution/` next
to the program under test: the features are checked against the reference, and the report's
first line names it (`Program: _solution/main.py`).

## The report

By default each scenario's run is shown as a terminal would have shown it: what the
program printed (boards, trees, prompts) and what was typed (bold, on a terminal with
colour), under a `│` gutter, then its `✔`/`✘` line with the reason under a `✘`. On a terminal
the reason is coloured by meaning: what was expected green, what the program did red, quoted
text and file names cyan, notes dim, and `the output shows:` lines as a `+`/`-` diff against
what was printed (never when piped, or with `NO_COLOR` set). A run
longer than 200 lines shows its first 150 and last 50. After the last scenario comes a
summary of every `✔`/`✘` line per feature, and the last line is `TOTAL  n of m`. With
`-q` (or `--quiet`) only the `✔`/`✘` lines and the TOTAL line are printed, each `✘` with the
first line of its reason (cut to the terminal's width), then a hint to run without `-q` for
the full output.

## Which pyathy is running

Every report (and `pyathy steps`, `pyathy -h`) ends with a dim
`pyathy 0.1.7 · <where it runs from>` line, under TOTAL and its hint, the same origin `-v`
(`--version`) prints, so two copies of pyathy on one machine are never confused:
the unzipped `pyathy/` folder, `editable: <repo>` for a `pip install -e` / `uv tool install -e`,
or `installed: <site-packages>/pyathy`.
