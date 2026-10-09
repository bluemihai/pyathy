"""Dev tool: run a program with scripted inputs and rolls, print everything it printed.

    .venv/bin/python scripts/peek.py <main.py> "2, red, green" "roll 6" "" "roll 3"

Each argument is either "roll N[, N]" or inputs as a step would take them ("" = enter).
"""

import sys

from pyathy.program import Program, ProgramError
from pyathy.steps import values

p = Program(sys.argv[1])
try:
    for arg in sys.argv[2:]:
        if arg.startswith("roll "):
            p.roll(*(int(x) for x in arg[5:].replace(",", " ").split()))
        else:
            p.type(*(values(arg) if arg else [""]))
    p.settle()
except ProgramError as e:
    print(f"!! {e}")
print(p.output)
print(f"-- state={p.state} waiting_for={p.waiting_for()} dice_left={list(p.dice)} inputs_left={list(p.inputs)}")
p.close()
