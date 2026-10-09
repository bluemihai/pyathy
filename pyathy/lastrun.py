"""The scenarios that failed last time, remembered in .pyathy/last-run.json in the student's
folder (pyathy's own file; pytest's cache stays off), and --next-failure, which runs them first.

A scenario is identified across runs by its feature file (relative to the folder pyathy runs
in), its name as written in the file, and its Scenario Outline row, if any.
"""

import json
import os

import pytest
from pytest_bdd.scenario import scenario_wrapper_template_registry

FILE = os.path.join(".pyathy", "last-run.json")


def key(item):
    """A pytest item's scenario identity as a JSON string (sortable, hashable); None for an
    item that is not a pytest-bdd scenario."""
    scenario = scenario_wrapper_template_registry.get(getattr(item, "obj", None))
    if scenario is None:
        return None
    path = scenario.feature.filename
    try:
        path = os.path.relpath(path)
    except ValueError:  # another drive on Windows
        pass
    example = getattr(getattr(item, "callspec", None), "params", {}).get("_pytest_bdd_example")
    return json.dumps({"feature": path.replace(os.sep, "/"), "scenario": scenario.name,
                       "example": dict(example) if example else None}, sort_keys=True)


class LastRun:
    """Reads .pyathy/last-run.json and rewrites it after a run: a scenario that ran is in the
    list iff it failed; one that was collected but did not run (stopped early) keeps its place;
    one that was not even looked at (another feature file was run) is kept too."""

    def __init__(self):
        self.failed = self.read()  # keys, in file order

    def read(self):
        try:
            with open(FILE, encoding="utf-8") as f:
                return [json.dumps(k, sort_keys=True) for k in json.load(f)["failed"]]
        except (OSError, ValueError, KeyError, TypeError):
            return []

    def update(self, collected, ran, failed, prune=False):
        """collected: the keys in run order; ran, failed: sets of keys. prune: drop the remembered
        scenarios that were not collected (they no longer exist)."""
        before = set(self.failed)
        now = [k for k in collected if (k in failed if k in ran else k in before)]
        if not prune:
            seen = set(collected)
            now += [k for k in self.failed if k not in seen]
        self.failed = now
        if now or os.path.exists(FILE):  # a clean folder stays clean until something fails
            self.write()

    def write(self):
        os.makedirs(os.path.dirname(FILE), exist_ok=True)
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({"failed": [json.loads(k) for k in self.failed]}, f, indent=1)
            f.write("\n")


class NextFailure:
    """--next-failure: the remembered scenarios run first, in their remembered (file) order,
    and the first that still fails stops the run; when all of them pass, the rest runs too."""

    def __init__(self, remembered):
        self.remembered = remembered  # keys
        self.order = []               # nodeids of the remembered scenarios that exist, in run order
        self.missing = 0

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        by_key = {}
        for item in items:
            if (k := key(item)) is not None:
                by_key.setdefault(k, []).append(item)
        first = [item for k in self.remembered for item in by_key.get(k, [])]
        self.missing = sum(1 for k in self.remembered if k not in by_key)
        chosen = set(map(id, first))
        items[:] = first + [item for item in items if id(item) not in chosen]
        self.order = [item.nodeid for item in first]

    def pytest_runtest_makereport(self, item, call):
        if call.excinfo is not None and item.nodeid in self.order:
            item.session.shouldfail = "stopped at the first failure"
