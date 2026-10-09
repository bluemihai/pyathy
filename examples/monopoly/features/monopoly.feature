Feature: Mini Monopoly
  The board: Start, Old Road ($60), Mill Lane ($60), Tax Office, Station ($200),
  Park Street ($100), Free Parking, Harbour ($120). Everyone starts with $1500.
  "Ann rolls 3+4 and answers y" is a built-in turn step: enter, the dice, and y to the buy
  question. "Ann and Bob play 1 round", "Ann has $1460" and "Ann owns Harbour" come from
  monopoly_steps.py, next to this file.

  Scenario: buying a street
    Given Ann and Bob play 1 round
    When Ann rolls 1+1 and answers y
    And Bob rolls 3+4 and answers n
    Then "Ann buys Mill Lane." is printed
    And Ann has $1440
    And Ann owns Mill Lane
    And Bob has $1500
    And Bob owns nothing

  Scenario: landing on someone else's street costs rent
    Given Ann and Bob play 1 round
    When Ann rolls 1+1 and answers y
    And Bob rolls 1+1
    Then "Bob pays $6 rent to Ann." is printed
    And Bob has $1494
    And Ann has $1446

  Scenario: passing Start pays $200
    Given Ann and Bob play 2 rounds
    When Ann rolls 3+4 and answers n
    And Bob rolls 2+2 and answers n
    And Ann rolls 1+1 and answers n
    Then "Ann passes Start and collects $200." is printed
    And Ann has $1700

  Scenario: the Tax Office takes $100
    Given Ann and Bob play 1 round
    When Ann rolls 1+2
    Then "Ann pays $100 tax." is printed
    And Ann has $1400

  Scenario: the same turn with built-in steps only
    When I input 2, Ann, Bob, 1
    And I input enter
    And I roll 2 and 3
    Then "Ann rolls 2+3 and lands on Park Street." is printed
    And the program asks "Buy Park Street for $100? (y/n)"

  Scenario: the richest player wins
    Given Ann and Bob play 1 round
    When Ann rolls 2+2 and answers y
    And Bob rolls 1+2
    Then the output shows:
      """
      Game over!
      Bob wins with $1400!
      """
    And the program ends

  Scenario: equal money is a tie
    Given Ann, Bob and Cy play 1 round
    When Ann rolls 3+3
    And Bob rolls 3+3
    And Cy rolls 3+3
    Then "It's a tie between Ann, Bob and Cy!" is printed

  Scenario: a wrong number of players is asked again
    When I input 1, 5, 3
    Then "Please type a number from 2 to 4." is printed 2 times
    And the program asks "Name of player 1:"
