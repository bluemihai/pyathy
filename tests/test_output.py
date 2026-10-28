"""-o show|hide|slow and --delay: run with `.venv/bin/pytest tests`."""

import pytest

from pyathy import cli
from pyathy.cli import Report, parse


class Terminal:
    @staticmethod
    def isatty():
        return True


class Pipe:
    @staticmethod
    def isatty():
        return False


@pytest.mark.parametrize(
    "args, options",
    [
        (["-o", "hide"], {"output": "hide"}),
        (["--output=slow"], {"output": "slow"}),
        (["-o=show", "features"], {"output": "show"}),
        (["--delay", "0.05"], {"delay": "0.05"}),
        (["-o", "slow", "--delay=0"], {"output": "slow", "delay": "0"}),
    ],
)
def test_parse_reads_the_value_after_the_flag(args, options):
    targets, got, flags = parse(args)
    assert got == options
    assert flags == []


def test_slow_on_a_terminal_pauses_after_each_line(monkeypatch, capsys):
    monkeypatch.setattr(cli.sys, "stdout", Terminal())
    pauses = []
    report = Report(output="slow", delay=0.05, sleep=pauses.append)
    monkeypatch.undo()
    report.show(["a", "b", "c"])
    assert pauses == [0.05, 0.05, 0.05]
    assert capsys.readouterr().out == "a\nb\nc\n"


def test_slow_when_piped_prints_at_once(monkeypatch, capsys):
    monkeypatch.setattr(cli.sys, "stdout", Pipe())
    pauses = []
    report = Report(output="slow", delay=0.05, sleep=pauses.append)
    monkeypatch.undo()
    report.show(["a", "b"])
    assert pauses == []
    assert capsys.readouterr().out == "a\nb\n"


@pytest.mark.parametrize("output", ["show", "hide"])
def test_only_slow_pauses(monkeypatch, output):
    monkeypatch.setattr(cli.sys, "stdout", Terminal())
    pauses = []
    report = Report(output=output, sleep=pauses.append)
    monkeypatch.undo()
    report.show(["a"])
    assert pauses == []


@pytest.mark.parametrize(
    "args, message",
    [
        (["-o", "loud"], "pyathy: -o takes show, hide, slow, not loud"),
        (
            ["--delay", "soon"],
            "pyathy: --delay takes a number of seconds, like 0.1, not soon",
        ),
        (["--delay=-1"], "pyathy: --delay takes a number of seconds, like 0.1, not -1"),
    ],
)
def test_a_wrong_value_is_refused(args, message, capsys):
    assert cli.run(args) == 2
    assert capsys.readouterr().out.strip() == message
