"""A very small Monopoly: 8 squares, two dice, a fixed number of rounds.

Land on a street nobody owns and you may buy it. Land on someone else's street and you
pay them rent. Pass (or land on) Start and you collect $200. The Tax Office takes $100.
After the last round the richest player wins.
"""

import random

START_MONEY = 1500
START_BONUS = 200
TAX = 100

# Every square: (name, price, rent). A price of 0 means it cannot be bought.
BOARD = [
    ("Start", 0, 0),
    ("Old Road", 60, 6),
    ("Mill Lane", 60, 6),
    ("Tax Office", 0, 0),
    ("Station", 200, 25),
    ("Park Street", 100, 10),
    ("Free Parking", 0, 0),
    ("Harbour", 120, 12),
]


def ask_number(question, low, high):
    while True:
        answer = input(question).strip()
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        print(f"Please type a number from {low} to {high}.")


def show_players(players):
    for player in players:
        streets = ", ".join(player["streets"]) or "nothing"
        print(f"  {player['name']}: ${player['cash']}, owns {streets}")


def take_turn(player, owners):
    name = player["name"]
    input(f"{name}, press enter to roll the dice. ")
    first, second = random.randint(1, 6), random.randint(1, 6)
    position = player["position"] + first + second
    if position >= len(BOARD):
        position -= len(BOARD)
        player["cash"] += START_BONUS
        print(f"{name} passes Start and collects ${START_BONUS}.")
    player["position"] = position
    square, price, rent = BOARD[position]
    print(f"{name} rolls {first}+{second} and lands on {square}.")

    if square == "Tax Office":
        player["cash"] -= TAX
        print(f"{name} pays ${TAX} tax.")
    elif price > 0:
        owner = owners.get(square)
        if owner is None:
            if player["cash"] < price:
                print(f"{name} cannot afford {square}.")
            elif input(f"Buy {square} for ${price}? (y/n) ").strip().lower() == "y":
                player["cash"] -= price
                player["streets"].append(square)
                owners[square] = player
                print(f"{name} buys {square}.")
        elif owner is not player:
            player["cash"] -= rent
            owner["cash"] += rent
            print(f"{name} pays ${rent} rent to {owner['name']}.")


def main():
    print("Welcome to Mini Monopoly!")
    count = ask_number("How many players (2-4)? ", 2, 4)
    players = []
    for number in range(1, count + 1):
        name = input(f"Name of player {number}: ").strip()
        players.append({"name": name, "cash": START_MONEY, "position": 0, "streets": []})
    rounds = ask_number("How many rounds (1-20)? ", 1, 20)

    owners = {}
    for round_number in range(1, rounds + 1):
        print(f"--- Round {round_number} ---")
        for player in players:
            take_turn(player, owners)
            show_players(players)

    print("Game over!")
    richest = max(player["cash"] for player in players)
    winners = [player["name"] for player in players if player["cash"] == richest]
    if len(winners) == 1:
        print(f"{winners[0]} wins with ${richest}!")
    else:
        print(f"It's a tie between {', '.join(winners[:-1])} and {winners[-1]}!")


main()
