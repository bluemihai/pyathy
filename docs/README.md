# The built-in steps, one page each

Every step works after `Given`, `When`, `Then`, `And` or `But`. Each page shows the step as
written in a feature, what it checks or sets, when it is needed, a small scenario that runs,
and the message it fails with. `python pyathy steps` prints the same list in the terminal.

Guides: [running pyathy and the report](running.md), [`pyathy check`](check.md),
[turn-based games](turns.md), [starting from a saved state](saved-games.md),
[your own steps](own-steps.md).

## Starting the program

- [`I start the program` / `I run the program with puzzle.txt --hard`](steps/start-the-program.md): run `main.py` until it asks something or ends, with these command-line arguments if any
- [`the program other.py`](steps/the-program-other-py.md): run `other.py` instead of `main.py`
- [`the program may take 30 seconds`](steps/the-program-may-take.md): wait longer for a slow program (default 10)

## Typing

- [`I input 4` / `I input 4, left, no` / `I input enter`](steps/i-input.md): type answers, one per question; `enter` alone presses enter

## Dice and random

- [`I roll 6` / `I roll 3 and 4`](steps/i-roll.md): the next dice show these faces
- [`the random choice is red`](steps/the-random-choice-is.md): the next random pick returns this value

## Turns

- [`red rolls 6` / `Ann rolls 4+6`](steps/rolls.md): enter if needed, then the dice, after checking it is red's turn
- [`red rolls 3 and picks 2` / `… and answers 2`](steps/rolls-and-picks.md): the same, then types 2 at the question that follows
- [`these turns are played 3 times:` + a table](steps/these-turns-are-played.md): one step per row, run in order, that many times
- [`the players are red and green`](steps/the-players-are.md): the names a turn announcement may use
- [`red's turn is announced` / `it is red's turn`](steps/turn-is-announced.md): a line names red and no other player, without digits
- [`a pawn moves from 0 to 3` / `red moves from 0 to 3`](steps/moves-from-to.md): a line of this turn has these two numbers, `to` or an arrow between them
- [`nothing moves`](steps/nothing-moves.md): no such line this turn

## Output

- [`"Hello" is printed`](steps/is-printed.md): somewhere in the output
- [`"Error" is printed 3 times`](steps/is-printed-n-times.md): exactly that many times
- [`"Game over" is not printed`](steps/is-not-printed.md): nowhere in the output
- [`the output starts with "Welcome"`](steps/the-output-starts-with.md): the very first output
- [`the output shows:` + lines between `"""`](steps/the-output-shows.md): these lines, in a row
- [`the program asks "Your name?"`](steps/the-program-asks.md): it is now waiting for input after that question
- [`"orange" is refused with a message`](steps/is-refused-with-a-message.md): after typing it, a message was printed and the same question asked again

## Ending

- [`the program ends`](steps/the-program-ends.md): it finished on its own, without crashing
- [`the program is still running`](steps/the-program-is-still-running.md): it is waiting for input or a roll

## Files

- [`a file "photos/beach.jpg"`](steps/a-file.md): an empty file in the folder before the program starts
- [`a file "game.txt" containing "round 3"`](steps/a-file-containing.md): this one-line file in the folder before the program starts
- [`a file "game.txt" with:` + lines between `"""`](steps/a-file-with.md): the same, several lines
- [`there is no file "game.txt"`](steps/there-is-no-file.md): the program starts without it, whatever is in your folder
- [`a file "game.txt" is written`](steps/a-file-is-written.md): the program made a file, or changed one
- [`no file is written`](steps/no-file-is-written.md): the program made or changed no file
- [`the file "game.txt" contains "round 4"`](steps/the-file-contains.md): anywhere in the file
- [`the file "game.txt" contains:` + lines between `"""`](steps/the-file-contains-lines.md): these lines, in a row

## Saved games

- [`a saved game:` + lines between `"""`](steps/a-saved-game.md): these lines are in the program's save file before it starts
- [`there is no saved game`](steps/there-is-no-saved-game.md): the program starts without its save file
- [`a saved game is written`](steps/a-saved-game-is-written.md): the program made its save file, or changed it
- [`the saved game holds:` + lines between `"""`](steps/the-saved-game-holds.md): these lines, in a row, in the save file
- [`no saved game is left`](steps/no-saved-game-is-left.md): the save file was removed, or emptied
- [`the program is started again`](steps/the-program-is-started-again.md): stop it and start it over in the same folder, files kept
