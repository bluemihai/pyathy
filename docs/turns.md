# Turn-based games

A turn-based game reads as a game: `red rolls 6` presses enter if the program is waiting
for it and makes the die show 6, after checking that the last turn announcement names red
(a line naming red and no other player, without digits, like `Player red:`). The checks
`a pawn moves from 0 to 3` and `nothing moves` read what was printed since that roll.

```gherkin
  Scenario: a six puts a pawn on the board
    Given I input 2, red, green
    When red rolls 6
    And green rolls 2
    And red rolls 3
    Then red moves from 0 to 3
    When green rolls 5
    Then nothing moves
```

The steps, one page each: [`red rolls 6`](steps/rolls.md),
[`red rolls 3 and picks 2`](steps/rolls-and-picks.md),
[`these turns are played 3 times:`](steps/these-turns-are-played.md),
[`the players are red and green`](steps/the-players-are.md),
[`red's turn is announced`](steps/turn-is-announced.md),
[`a pawn moves from 0 to 3`](steps/moves-from-to.md), [`nothing moves`](steps/nothing-moves.md).
