# Your own steps

Every `*_steps.py` next to the `.feature` files is loaded, so a game can read like the
game: `Ann has $1460`, `Ann owns Harbour`, `Ann and Bob play 2 rounds`. A few lines of
Python per step; the built-in steps keep working next to them.

## Writing one

A step is a pattern in [Cucumber style](https://github.com/cucumber/cucumber-expressions):
`{name}` matches anything, `{name:w}` one word, `{n:d}` a whole number, and each field
becomes a parameter of the function. Several patterns can share one function
(`@step("{names} play {rounds:d} rounds", "{names} play {rounds:d} round")`); a field a
pattern leaves out gets the function's default. Every step works after `Given`, `When`,
`Then`, `And` or `But`, like the built-ins.

The first parameter is always `program`, the running program:

- `program.type("2", "Ann", "Bob")` types answers, one per question;
- `program.roll(6)` makes the next die show 6;
- `program.settle()` runs the program as far as it can and returns everything printed so far
  (checks read this);
- `fail(program, message)` fails the step with the message, where the program is (waiting
  for input, ended, or crashed) and its last lines under it.

`examples/monopoly/features/monopoly_steps.py` adds `Ann has $1460` and `Ann owns Harbour`:

```python
import re

from pyathy.steps import fail, step


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
```

`python pyathy steps` lists your steps under the built-ins, as written; `python pyathy check`
matches feature lines against them too.
