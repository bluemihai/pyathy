"""Monopoly's own steps. pyathy loads every *steps.py next to the .feature files, so these
work like the built-in ones:

    Given Ann and Bob play 2 rounds
    When Ann rolls 3+4 and buys
    And Bob rolls 1+1 and doesn't buy
    Then Ann has $1380
    And Ann owns Harbour

A roll step presses enter for that player and makes the two dice show those faces
(the built-in `I roll 3 and 4` does the same for the dice). The checks read the last
"  Ann: $1380, owns Harbour" line the game printed.
"""

import re

from pyathy.steps import fail, step


@step(r"(?P<names>\w+(?:, \w+)* and \w+) play (?P<rounds>\d+) rounds?")
def players(program, names, rounds):
    names = re.split(r", | and ", names)
    program.type(str(len(names)), *names, rounds)


@step(r"(?P<name>\w+) rolls (?P<first>\d)\+(?P<second>\d)(?: and (?P<choice>buys|doesn't buy))?")
def rolls(program, name, first, second, choice):
    program.settle()
    lines = program.output.rstrip().splitlines()
    if not lines or not lines[-1].startswith(f"{name}, press enter"):
        fail(program, f"expected it to be {name}'s turn to roll")
    program.type("")
    program.roll(int(first), int(second))
    if choice:
        program.type("y" if choice == "buys" else "n")


def last_status(program, name):
    found = re.findall(rf"^\s*{re.escape(name)}: \$(-?\d+), owns (.*)$", program.settle(), re.M)
    if not found:
        fail(program, f"expected a line like '{name}: $1500, owns nothing'")
    cash, streets = found[-1]
    return int(cash), [s.strip() for s in streets.split(",")]


@step(r"(?P<name>\w+) has \$(?P<cash>-?\d+)")
def has(program, name, cash):
    have, _ = last_status(program, name)
    if have != int(cash):
        fail(program, f"expected {name} to have ${cash}, but {name} has ${have}")


@step(r"(?P<name>\w+) owns (?P<street>.+)")
def owns(program, name, street):
    _, streets = last_status(program, name)
    if street not in streets:
        fail(program, f"expected {name} to own {street}, but {name} owns {', '.join(streets)}")
