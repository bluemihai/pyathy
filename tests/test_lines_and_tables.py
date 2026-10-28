"""`main.py has X = …`, `the line with … also has …`, `the "…" row has … under "…"`: run with `.venv/bin/pytest tests`."""

import textwrap

import pytest

from pyathy.program import Program, ProgramError
from pyathy.steps import has_constant, has_setting, line_also_has, row_has

BOX = """
SHOW = False
print("Totals")
name = input("Name: ")
if SHOW:
    print("┌──────┬───────┐")
    print("│ Name │ Score │")
    print("├──────┼───────┤")
    print("│ Ann  │    12 │")
    print("│ Bob  │       │")
    print("│ Cem  │    -- │")
    print("└──────┴───────┘")
print(f"Total for {name}: 42")
"""

PIPES = """
print("| Name | Score |")
print("|------|-------|")
print("| Ann  | 3     |")
print("| Bob  |       |")
"""


def program_for(tmp_path, source):
    app = tmp_path / "main.py"
    app.write_text(textwrap.dedent(source))
    return Program(str(app))


def run(tmp_path, source, *steps):
    program = program_for(tmp_path, source)
    for step in steps:
        step(program)
    program.settle()
    return program


def test_constant_is_set_in_the_copy_only(tmp_path):
    program = program_for(tmp_path, BOX)
    has_constant(program, "main.py", "SHOW", "True")
    program.type("Ann")
    row_has(program, "Ann", "12", "Score")
    assert "SHOW = False" in (tmp_path / "main.py").read_text()
    program.close()


def test_constant_keeps_a_comment_and_takes_the_last_assignment(tmp_path):
    program = program_for(
        tmp_path, "SHOW = 1\nSHOW = False  # the switch\nprint(SHOW)\n"
    )
    has_constant(program, "main.py", "SHOW", "'yes'")
    has_constant(program, "main.py", "SHOW", "[1, 2]")
    assert (
        program.files[-1][1] == "SHOW = 1\nSHOW = [1, 2]  # the switch\nprint(SHOW)\n"
    )
    program.close()


def test_constant_missing(tmp_path):
    program = program_for(tmp_path, "def f():\n    SHOW = True\n")
    with pytest.raises(ProgramError, match="main.py has no SHOW"):
        has_constant(program, "main.py", "SHOW", "True")
    with pytest.raises(ProgramError, match="there is no other.py"):
        has_constant(program, "other.py", "SHOW", "True")
    with pytest.raises(ProgramError, match="not a Python value"):
        has_constant(program, "main.py", "SHOW", "True (")
    program.close()


def test_constant_after_the_start(tmp_path):
    program = run(tmp_path, BOX, lambda p: p.type("Ann"))
    with pytest.raises(ProgramError, match="must come before"):
        has_constant(program, "main.py", "SHOW", "True")
    program.close()


def test_setting_present(tmp_path):
    program = program_for(tmp_path, BOX)
    has_setting(program, "main.py", "SHOW")
    program.type("Ann")
    has_setting(program, "main.py", "SHOW")  # after the start too
    program.close()


def test_setting_annotated(tmp_path):
    program = program_for(tmp_path, "SHOW: bool = False\nprint(SHOW)\n")
    has_setting(program, "main.py", "SHOW")
    program.close()


def test_setting_missing(tmp_path):
    program = program_for(tmp_path, "print('hi')\n")
    with pytest.raises(ProgramError, match=r"main.py has no SHOW = … at the top \(outside any function\): put SHOW = … at the top of main.py"):
        has_setting(program, "main.py", "SHOW")
    with pytest.raises(ProgramError, match="there is no other.py"):
        has_setting(program, "other.py", "SHOW")
    program.close()


def test_setting_only_inside_a_function(tmp_path):
    program = program_for(tmp_path, "def f():\n    SHOW = True\n")
    with pytest.raises(ProgramError, match="main.py has no SHOW"):
        has_setting(program, "main.py", "SHOW")
    program.close()


def test_setting_sees_a_staged_copy(tmp_path):
    program = program_for(tmp_path, "print('hi')\n")
    program.write_file("main.py", "SHOW = 1\nprint('hi')\n")
    has_setting(program, "main.py", "SHOW")
    program.close()


def test_setting_step_does_not_collide():
    from pyathy import steps

    def hits(line):
        return [fn.__name__ for _, _, parser, fn in steps.REGISTERED if parser.is_matching(line)]

    assert hits("main.py has a SHOW setting") == ["has_setting"]
    assert hits("main.py has an ITEM setting") == ["has_setting"]
    assert hits("main.py has SHOW = True") == ["has_constant"]


def test_line_also_has(tmp_path):
    program = run(tmp_path, BOX, lambda p: p.type("Ann"))
    line_also_has(program, "total for", "42")
    with pytest.raises(ProgramError, match='last line with "Total" to also have "43"'):
        line_also_has(program, "Total", "43")
    with pytest.raises(ProgramError, match="no line printed has it"):
        line_also_has(program, "Grand total", "42")
    program.close()


def test_line_also_has_skips_typed_answers(tmp_path):
    program = run(tmp_path, BOX, lambda p: p.type("Zed"))
    with pytest.raises(ProgramError, match="no line printed has it"):
        line_also_has(program, "Name: Zed", "Zed")
    program.close()


def test_box_table(tmp_path):
    program = run(
        tmp_path,
        BOX,
        lambda p: has_constant(p, "main.py", "SHOW", "True"),
        lambda p: p.type("Ann"),
    )
    row_has(program, "Ann", "12", "Score")
    row_has(program, "bob", "", "score")
    row_has(program, "Cem", "--", "Score")
    with pytest.raises(ProgramError, match='to have "12" under "Score", but it has ""'):
        row_has(program, "Bob", "12", "Score")
    with pytest.raises(ProgramError, match="there is none"):
        row_has(program, "Dee", "", "Score")
    with pytest.raises(ProgramError, match='a column "Points"'):
        row_has(program, "Ann", "12", "Points")
    program.close()


def test_pipe_table(tmp_path):
    program = run(tmp_path, PIPES)
    row_has(program, "Ann", "3", "Score")
    row_has(program, "Bob", "", "Score")
    program.close()


def test_last_table_counts(tmp_path):
    program = run(tmp_path, PIPES + PIPES.replace("3", "7"))
    row_has(program, "Ann", "7", "Score")
    program.close()
