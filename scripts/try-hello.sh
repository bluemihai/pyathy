#!/bin/sh
# Smoke test: pyathy init, pyathy check and pyathy in a brand-new folder.
set -e
PYATHY="$(cd "$(dirname "$0")/.." && pwd)/.venv/bin/pyathy"
DIR="$(mktemp -d -t pyathy-hello)"
cd "$DIR"
"$PYATHY" init
"$PYATHY" check
"$PYATHY"
