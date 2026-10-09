Feature: Mini Sudoku
  A 4x4 puzzle: every row, column and 2x2 box holds 1 to 4 once.
  A move is "row column number". The board is checked with "the output shows".

  Scenario: the puzzle is shown at the start
    When I start the program
    Then the output shows:
      """
      +-----+-----+
      | 1 3 | . 4 |
      | . 4 | 1 . |
      +-----+-----+
      | . 1 | 4 . |
      | 4 . | . 1 |
      +-----+-----+
      """
    And the program asks "Your move (row column number), or q to quit:"

  Scenario: a good move fills the square
    When I input 1 3 2
    Then the output shows:
      """
      | 1 3 | 2 4 |
      | . 4 | 1 . |
      """

  Scenario Outline: the move <move> is refused
    When I input <move>
    Then "<message>" is printed
    And the program asks "Your move"

    Examples:
      | move  | message                            |
      | 1 3 4 | 4 is already in row 1.             |
      | 4 2 3 | 3 is already in column 2.          |
      | 2 1 3 | 3 is already in that box.          |
      | 1 1 2 | That square is part of the puzzle. |
      | 1 5 2 | Every number goes from 1 to 4.     |
      | 1 2   | Type three numbers, like: 1 2 3    |

  Scenario: filling every square solves the puzzle
    When I input 1 3 2, 2 1 2, 2 4 3, 3 1 3, 3 4 2, 4 2 2, 4 3 3
    Then the output shows:
      """
      +-----+-----+
      | 1 3 | 2 4 |
      | 2 4 | 1 3 |
      +-----+-----+
      | 3 1 | 4 2 |
      | 4 2 | 3 1 |
      +-----+-----+
      Solved!
      """
    And the program ends

  Scenario: another puzzle file, given on the command line
    When I run the program with almost.txt
    And I input 4 3 2
    Then "Solved!" is printed
    And the program ends

  Scenario: q quits
    When I input q
    Then "Bye!" is printed
    And "Solved!" is not printed
    And the program ends
