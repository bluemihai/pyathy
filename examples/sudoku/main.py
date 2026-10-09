"""Mini Sudoku: a 4x4 puzzle with 2x2 boxes.

Fill the empty squares (shown as dots) so that every row, every column and every box
holds the numbers 1 to 4 exactly once. A move is three numbers: row, column, number.

    python main.py              plays puzzle.txt
    python main.py other.txt    plays another puzzle file
"""

import sys

SIZE = 4
BOX = 2


def load(filename):
    """Read a puzzle: one line per row, numbers or dots separated by spaces."""
    grid = []
    with open(filename) as file:
        for line in file:
            if line.strip():
                grid.append([0 if cell == "." else int(cell) for cell in line.split()])
    return grid


def show(grid):
    border = "+-----+-----+"
    print(border)
    for row in range(SIZE):
        cells = [str(n) if n else "." for n in grid[row]]
        print(f"| {cells[0]} {cells[1]} | {cells[2]} {cells[3]} |")
        if row % BOX == BOX - 1:
            print(border)


def problem(grid, row, col, number):
    """Return why `number` cannot go at (row, col), or None when it can."""
    if number in grid[row]:
        return f"{number} is already in row {row + 1}."
    if number in [grid[r][col] for r in range(SIZE)]:
        return f"{number} is already in column {col + 1}."
    top, left = row - row % BOX, col - col % BOX
    for r in range(top, top + BOX):
        for c in range(left, left + BOX):
            if grid[r][c] == number:
                return f"{number} is already in that box."
    return None


def read_move():
    """Ask for a move. Returns (row, col, number) counted from 0, or None to quit."""
    while True:
        answer = input("Your move (row column number), or q to quit: ").strip().lower()
        if answer == "q":
            return None
        parts = answer.split()
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            print("Type three numbers, like: 1 2 3")
        elif not all(1 <= int(part) <= SIZE for part in parts):
            print(f"Every number goes from 1 to {SIZE}.")
        else:
            row, col, number = (int(part) for part in parts)
            return row - 1, col - 1, number


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "puzzle.txt"
    grid = load(filename)
    given = [[n != 0 for n in row] for row in grid]
    print("Mini Sudoku")
    show(grid)
    while any(0 in row for row in grid):
        move = read_move()
        if move is None:
            print("Bye!")
            return
        row, col, number = move
        if given[row][col]:
            print("That square is part of the puzzle.")
            continue
        grid[row][col] = 0  # a square the player filled before may be changed
        why = problem(grid, row, col, number)
        if why:
            print(why)
        else:
            grid[row][col] = number
            show(grid)
    print("Solved!")


main()
