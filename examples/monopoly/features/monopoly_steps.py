"""Monopoly's own steps. pyathy loads every *steps.py next to the .feature files, so these
work like the built-in ones:

    Given Ann and Bob play 2 rounds
    Then Ann has $1380
    And Ann owns Harbour

The checks read the last "  Ann: $1380, owns Harbour" line the game printed.
"""

import re

from pyathy.steps import fail, step


@step("{names} play {rounds:d} rounds", "{names} play {rounds:d} round")
def players(program, names, rounds):
    """`Ann and Bob play 2 rounds`: types the number of players, their names and the rounds."""
    names = re.split(r", | and ", names)
    program.players += names
    program.type(str(len(names)), *names, str(rounds))


def last_status(program, name):
    found = re.findall(rf"^\s*{re.escape(name)}: \$(-?\d+), owns (.*)$", program.settle(), re.M)
    if not found:
        fail(program, f"expected a line like '{name}: $1500, owns nothing'")
    cash, streets = found[-1]
    return int(cash), [s.strip() for s in streets.split(",")]


@step("{name:w} has ${cash:d}")
def has(program, name, cash):
    """The last status line shows this much cash."""
    have, _ = last_status(program, name)
    if have != cash:
        fail(program, f"expected {name} to have ${cash}, but {name} has ${have}")


@step("{name:w} owns {street}")
def owns(program, name, street):
    """The last status line lists this street (or "nothing")."""
    _, streets = last_status(program, name)
    if street not in streets:
        fail(program, f"expected {name} to own {street}, but {name} owns {', '.join(streets)}")
