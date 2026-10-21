"""`"x" is refused with a message`: run with `.venv/bin/pytest tests`."""

import textwrap

import pytest

from pyathy.program import Program, ProgramError
from pyathy.steps import refused

MENU = """
def menu():
    print("1. Display contacts")
    print("2. Add contact")
    print("0. Exit application")

print("Black book")
menu()
while True:
    option = input("choose an option: ")
    if option == "0":
        break
    if option == "1":
        print("No contacts")
    elif option == "2":
        print("Added")
    else:
        {wrong}
    menu()
"""

ASK = """
while True:
    age = input("Your age: ")
    if age.isdigit():
        break
    {wrong}
print("Thanks")
"""


def run(tmp_path, source, *answers):
    app = tmp_path / "main.py"
    app.write_text(textwrap.dedent(source))
    program = Program(str(app))
    program.type(*answers)
    program.settle()
    return program


def menu_program(tmp_path, wrong, *answers):
    return run(tmp_path, MENU.replace("{wrong}", wrong), *answers, "0")


def test_reprinted_menu_alone_is_not_a_message(tmp_path):
    program = menu_program(tmp_path, "pass", "5")
    with pytest.raises(ProgramError, match="a message should be printed"):
        refused(program, "5")
    program.close()


def test_message_then_menu_is_refused(tmp_path):
    program = menu_program(tmp_path, 'print("Invalid option!")', "5")
    refused(program, "5")
    program.close()


def test_the_same_message_for_a_second_wrong_answer(tmp_path):
    program = menu_program(tmp_path, 'print("Invalid option!")', "5", "7")
    refused(program, "7")
    program.close()


def test_the_same_message_after_a_right_answer_in_between(tmp_path):
    program = menu_program(tmp_path, 'print("Invalid option!")', "5", "1", "7")
    refused(program, "7")
    program.close()


def test_message_on_the_question_line(tmp_path):
    source = MENU.replace("{wrong}", 'print("Invalid option! ", end="")').replace("    menu()\n", "")
    program = run(tmp_path, source, "5", "0")
    refused(program, "5")
    program.close()


def test_message_then_question_without_a_menu(tmp_path):
    program = run(tmp_path, ASK.replace("{wrong}", 'print("Not a number")'), "abc", "42")
    refused(program, "abc")
    program.close()


def test_question_again_without_a_message(tmp_path):
    program = run(tmp_path, ASK.replace("{wrong}", "pass"), "abc", "42")
    with pytest.raises(ProgramError, match="a message should be printed"):
        refused(program, "abc")
    program.close()


def test_empty_answer_refused(tmp_path):
    program = run(tmp_path, ASK.replace("{wrong}", 'print("Please type a number")'), "", "42")
    refused(program, "")
    program.close()


def test_empty_answer_accepted_silently(tmp_path):
    source = 'name = input("Your name: ")\nprint("Bye")\n'
    program = run(tmp_path, source, "")
    with pytest.raises(ProgramError, match="the same question should be asked again"):
        refused(program, "")
    program.close()


def test_empty_answer_has_its_own_step():
    from pyathy import steps

    assert any(p.is_matching('"" is refused with a message') for _, _, p, fn in steps.REGISTERED if fn is refused)
