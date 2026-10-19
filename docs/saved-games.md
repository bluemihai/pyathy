# Start from a saved state

A program that saves its state to a text file is easy to test from any point: dictate the
saved game, start the program, play a move, and check the saved game (or what is printed).
Each scenario runs in a copy of the folder, so the dictated file and whatever the program
writes never touch your own files. For a save-then-load check in one scenario, `the program
is started again` restarts it in that same copy, with its saved game still there; the steps
after it read the new run, and the report shows both runs.

```gherkin
Feature: Counter

  Scenario: it continues from the saved count and saves the new one
    Given a saved game:
      """
      3
      """
    When I start the program
    Then "Count: 3" is printed
    When I input "", q
    Then the saved game holds:
      """
      4
      """

  Scenario: save, start again, it continued
    Given there is no saved game
    When I input "", ""
    And I input q
    Then a saved game is written
    When the program is started again
    Then "Count: 2" is printed
```

The program is the counter on the
[`a file "game.txt" containing "round 3"`](steps/a-file-containing.md) page; each `""` is an
empty answer (just enter), which counts.

The scenario never names the file: pyathy finds it in the program (it reads the code, it does
not run it), as the one file the program opens for writing. A program that writes several
files says which one is the save file with `SAVE_FILE_NAME = "count.txt"` at the top of `main.py`.

The steps, one page each: [`a saved game:`](steps/a-saved-game.md),
[`there is no saved game`](steps/there-is-no-saved-game.md),
[`a saved game is written`](steps/a-saved-game-is-written.md),
[`the saved game holds:`](steps/the-saved-game-holds.md),
[`no saved game is left`](steps/no-saved-game-is-left.md),
[`the program is started again`](steps/the-program-is-started-again.md).
