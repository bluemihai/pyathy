#!/bin/sh
# Builds dist/pyathy/ (and dist/pyathy.zip of it): a folder students unzip next to
# their main.py and run with `python pyathy`. No install, pure Python, any OS.
#   dist/pyathy/__main__.py   bootstrap (source: packaging/__main__.py)
#   dist/pyathy/README.txt    what this is (source: packaging/README.txt)
#   dist/pyathy/pyathy/       pyathy's own code
#   dist/pyathy/lib/          pytest-bdd, pytest and their dependencies
# Rebuild after every change.
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/dist/pyathy"
rm -rf "$OUT" "$HERE/dist/pyathy.zip"
mkdir -p "$OUT"

uv pip install --quiet --target "$OUT/lib" --python 3.14 --python-version 3.11 --no-compile "$HERE"

# pyathy's own code goes on top, not among the libraries
rm -rf "$OUT/lib/pyathy" "$OUT/lib"/pyathy-*.dist-info
mkdir "$OUT/pyathy"
cp "$HERE"/pyathy/*.py "$OUT/pyathy/"
cp "$HERE/packaging/__main__.py" "$HERE/packaging/README.txt" "$OUT/"

# trim: console scripts, markupsafe's
# compiled speedups (it falls back to pure Python), install bookkeeping, caches
rm -rf "$OUT/lib/bin"
rm -f "$OUT/lib/markupsafe"/_speedups.*

# trim modules nothing imports (traced with sys.modules at exit: passing, failing, crashing,
# hanging, undefined-step, bad-Gherkin, outline, no-main.py, PY_COLORS=1 and -h runs, on 3.12-3.14).
# keep(dir, names...): delete every .py in dir (and its subpackages) except the names given.
keep() {
  dir="$1"; shift
  for f in "$dir"/*.py; do
    case " $* " in *" $(basename "$f" .py) "*) ;; *) rm -f "$f" ;; esac
  done
}
# pygments: pytest 9 imports it unconditionally but only highlights tracebacks on a colour
# terminal, which pyathy's own report never uses. Keep exactly that highlighter (python and
# diff lexers, terminal formatter, default style) and the registries; drop the other 300 files.
L="$OUT/lib/pygments"
keep "$L" __init__ console filter formatter lexer modeline plugin regexopt style token unistring util
keep "$L/lexers" __init__ _mapping diff python
keep "$L/formatters" __init__ _mapping terminal
keep "$L/styles" __init__ _mapping default
# mako (pytest-bdd's templates): its extensions are optional plugins. Without pygmentplugin,
# mako.exceptions falls back to plain HTML escaping instead of importing 25 more lexers.
rm -rf "$OUT/lib/mako/testing" "$OUT/lib/mako/cmd.py"
keep "$OUT/lib/mako/ext" __init__
# packaging: pytest uses version, and requirements for the required_plugins ini option;
# the license, metadata and lock-file modules are never reached from those.
rm -rf "$OUT/lib/packaging/licenses"
for m in metadata pylock dependency_groups direct_url errors _structures; do
  rm -f "$OUT/lib/packaging/$m.py"
done
find "$OUT" -name __pycache__ -type d -prune -exec rm -rf {} +
find "$OUT/lib" -name '*.pyi' -delete
find "$OUT/lib" -path '*.dist-info/*' \( -name RECORD -o -name INSTALLER -o -name REQUESTED -o -name WHEEL -o -name direct_url.json \) -delete

# every dependency must be pure Python, so one folder works on Windows, macOS and Linux
if find "$OUT" \( -name '*.so' -o -name '*.pyd' -o -name '*.dylib' -o -name '*.dll' \) | grep .; then
  echo "compiled files above: not pure Python" >&2
  exit 1
fi

(cd "$HERE/dist" && zip -qrX pyathy.zip pyathy)
echo "$(find "$OUT" -type f | wc -l | tr -d ' ') files, $(du -sh "$OUT" | cut -f1) in dist/pyathy/"
ls -la "$HERE/dist/pyathy.zip"
