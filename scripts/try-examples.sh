#!/bin/sh
# Runs pyathy in each example folder (its main.py against its features/).
# Usage: scripts/try-examples.sh [example...]   (default: tictactoe sudoku monopoly)
# examples/edge is left out: every scenario there is meant to fail, to show the messages.
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PYATHY="$HERE/.venv/bin/pyathy"
[ -x "$PYATHY" ] || PYATHY=pyathy
status=0
for example in ${@:-tictactoe sudoku monopoly}; do
  echo "=== $example"
  (cd "$HERE/examples/$example" && "$PYATHY") || status=1
done
exit $status
