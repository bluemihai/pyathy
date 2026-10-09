"""Tic Tac Toe for two players at one keyboard.

The squares are numbered like the keys of a phone:

     1 | 2 | 3
    ---+---+---
     4 | 5 | 6
    ---+---+---
     7 | 8 | 9

X goes first. Three in a row (across, down or diagonal) wins.
"""

LINES = [
    (1, 2, 3), (4, 5, 6), (7, 8, 9),  # across
    (1, 4, 7), (2, 5, 8), (3, 6, 9),  # down
    (1, 5, 9), (3, 5, 7),             # diagonals
]


def show(board):
    """Print the board. An empty square shows its number, so players know what to type."""
    rows = []
    for first in (1, 4, 7):
        cells = [board[n] or str(n) for n in (first, first + 1, first + 2)]
        rows.append(" " + " | ".join(cells))
    print("\n---+---+---\n".join(rows))


def winner(board):
    """Return "X" or "O" when that player has three in a row, otherwise None."""
    for a, b, c in LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def ask_square(board, player):
    """Keep asking until the player types the number of an empty square."""
    while True:
        answer = input(f"Player {player}, choose a square (1-9): ").strip()
        if not answer.isdigit() or not 1 <= int(answer) <= 9:
            print("Please type a number from 1 to 9.")
        elif board[int(answer)]:
            print("That square is taken.")
        else:
            return int(answer)


def play():
    board = {n: "" for n in range(1, 10)}
    player = "X"
    for turn in range(9):
        show(board)
        board[ask_square(board, player)] = player
        if winner(board):
            show(board)
            print(f"Player {player} wins!")
            return
        player = "O" if player == "X" else "X"
    show(board)
    print("It's a draw!")


def main():
    print("Welcome to Tic Tac Toe!")
    while True:
        play()
        again = input("Play again? (y/n) ").strip().lower()
        if again != "y":
            print("Thanks for playing!")
            break


main()
