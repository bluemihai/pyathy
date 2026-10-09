Feature: Tic Tac Toe
  Two players take turns typing the number of a square. X goes first.
  Every step here is a built-in pyathy step: no steps file needed.

  Scenario: the empty board shows the numbers to type
    When I start the program
    Then "Welcome to Tic Tac Toe!" is printed
    And the output shows:
      """
       1 | 2 | 3
      ---+---+---
       4 | 5 | 6
      ---+---+---
       7 | 8 | 9
      """
    And the program asks "Player X, choose a square (1-9):"

  Scenario: X wins with the top row
    When I input 1, 4, 2, 5, 3
    Then the output shows:
      """
       X | X | X
      ---+---+---
       O | O | 6
      ---+---+---
       7 | 8 | 9
      """
    And "Player X wins!" is printed
    And "Player O wins!" is not printed
    And the program asks "Play again? (y/n)"

  Scenario: O wins with a diagonal
    When I input 2, 3, 4, 5, 9, 7
    Then "Player O wins!" is printed

  Scenario: a full board without three in a row is a draw
    When I input 1, 2, 3, 5, 4, 6, 8, 7, 9
    Then "It's a draw!" is printed
    And "wins!" is not printed

  Scenario: a taken square or a wrong number is asked again
    When I input 5, 5, 0, ten, 1
    Then "That square is taken." is printed 1 time
    And "Please type a number from 1 to 9." is printed 2 times
    And the program asks "Player X, choose a square (1-9):"

  Scenario: playing again starts a fresh board
    When I input 1, 4, 2, 5, 3, y
    Then "Player X, choose a square (1-9):" is printed 4 times
    When I input 7, 1, 8, 2, 9, n
    Then "Player X wins!" is printed 2 times
    And "Thanks for playing!" is printed
    And the program ends
