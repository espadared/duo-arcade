"""Battleship - hide your fleet, then hunt theirs."""

import random

KEY = "battleship"
NAME = "Battleship"
EMOJI = "🚢"
TAGLINE = "Hide your fleet, then hunt theirs one square at a time."
RULES = ("First, place your five ships on your own grid. Then take turns firing at "
         "squares on your opponent's grid. A hit earns you another shot straight "
         "away; a miss hands over the turn. Sink all five of their ships to win.")
LEVEL = "Medium"
MINUTES = "12 min"

SIZE = 10
FLEET = [("Carrier", 5), ("Battleship", 4), ("Cruiser", 3), ("Submarine", 3), ("Destroyer", 2)]


def new_state(starter):
    return {"size": SIZE, "phase": "place", "turn": None, "over": False, "winner": None,
            "fleets": [[], []], "ready": [False, False],
            "attacks": [[None] * (SIZE * SIZE), [None] * (SIZE * SIZE)],
            "last": [None, None], "sunkNote": None,
            "spec": [{"name": n, "len": ln} for n, ln in FLEET],
            "starter": starter}


def _cells_for(row, col, length, direction):
    if direction == "h":
        if col + length > SIZE:
            return None
        return [row * SIZE + col + i for i in range(length)]
    if direction == "v":
        if row + length > SIZE:
            return None
        return [(row + i) * SIZE + col for i in range(length)]
    return None


def _build_fleet(placements):
    """Turn [[row, col, direction], ...] into a validated fleet, or None."""
    if not isinstance(placements, list) or len(placements) != len(FLEET):
        return None
    used = set()
    fleet = []
    for (name, length), spot in zip(FLEET, placements):
        if not isinstance(spot, list) or len(spot) != 3:
            return None
        row, col, direction = spot
        if not isinstance(row, int) or not isinstance(col, int):
            return None
        if not (0 <= row < SIZE and 0 <= col < SIZE):
            return None
        cells = _cells_for(row, col, length, direction)
        if cells is None or used & set(cells):
            return None
        used.update(cells)
        fleet.append({"name": name, "len": length, "cells": cells, "hit": [False] * length})
    return fleet


def _random_fleet():
    while True:
        placements = []
        used = set()
        for _name, length in FLEET:
            for _attempt in range(200):
                direction = random.choice("hv")
                row = random.randrange(SIZE)
                col = random.randrange(SIZE)
                cells = _cells_for(row, col, length, direction)
                if cells and not used & set(cells):
                    used.update(cells)
                    placements.append([row, col, direction])
                    break
            else:
                break  # this layout got stuck - start over
        if len(placements) == len(FLEET):
            return placements


def _all_sunk(fleet):
    return all(all(ship["hit"]) for ship in fleet)


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    action = mv.get("action")

    if state["phase"] == "place":
        if state["ready"][player]:
            return "Your fleet is already set — waiting for your opponent."
        placements = _random_fleet() if action == "random" else mv.get("ships")
        fleet = _build_fleet(placements)
        if fleet is None:
            return "That layout doesn't work — ships must fit on the grid without overlapping."
        state["fleets"][player] = fleet
        state["ready"][player] = True
        if all(state["ready"]):
            state["phase"] = "fire"
            state["turn"] = state["starter"]
        return None

    if action != "fire":
        return "Pick a square to fire at."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    cell = mv.get("cell")
    if not isinstance(cell, int) or not 0 <= cell < SIZE * SIZE:
        return "That square doesn't exist."
    if state["attacks"][player][cell] is not None:
        return "You've already fired at that square."

    enemy = state["fleets"][1 - player]
    struck = None
    for ship in enemy:
        if cell in ship["cells"]:
            ship["hit"][ship["cells"].index(cell)] = True
            struck = ship
            break

    state["attacks"][player][cell] = "hit" if struck else "miss"
    state["last"][player] = cell

    if struck is None:
        state["sunkNote"] = None
        state["turn"] = 1 - player  # a miss hands over the turn
        return None

    state["sunkNote"] = {"player": player, "ship": struck["name"]} if all(struck["hit"]) else None
    if _all_sunk(enemy):
        state.update(over=True, winner=player, turn=None)
    return None


def view(state, player):
    mine = state["fleets"][player]
    theirs = state["fleets"][1 - player]

    your_ships = [{"name": s["name"], "cells": s["cells"], "hit": s["hit"],
                   "sunk": all(s["hit"])} for s in mine]
    # you only get to see their ships once they're sunk (or the game is over)
    their_ships = [
        {"name": s["name"], "len": s["len"], "sunk": all(s["hit"]),
         "cells": s["cells"] if (all(s["hit"]) or state["over"]) else None}
        for s in theirs
    ]

    return {"size": SIZE, "phase": state["phase"], "turn": state["turn"],
            "over": state["over"], "winner": state["winner"],
            "spec": state["spec"],
            "yourShips": your_ships, "theirShips": their_ships,
            "shotsAtThem": state["attacks"][player],
            "shotsAtYou": state["attacks"][1 - player],
            "youReady": state["ready"][player], "theyReady": state["ready"][1 - player],
            "lastTheirs": state["last"][1 - player], "sunkNote": state["sunkNote"]}
