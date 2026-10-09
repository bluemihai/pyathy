Feature: edge cases (every scenario here is EXPECTED TO FAIL, each with a clear message)

  Scenario: a crash is reported with the student's traceback
    When I input Ann
    Then "Hi Ann" is printed
    And the program ends

  Scenario: an endless loop times out
    Given the program forever.py
    When I start the program
    Then "never" is printed

  Scenario: an input nobody asked for
    When I input Ann, Bob
    Then "Hi Ann" is printed

  Scenario: a roll nobody used
    Given the program dice.py
    When I roll 3
    And I roll 5
    Then "rolled 3" is printed

  Scenario: a roll outside the die
    Given the program dice.py
    When I roll 0
    Then "rolled 0" is printed
