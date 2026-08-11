"""Tic-Tac-Toe - three in a row on a 3x3 grid."""

KEY = "tictactoe"
NAME = "Tic-Tac-Toe"
EMOJI = "⭕"
TAGLINE = "Three in a row. The one everybody knows."
RULES = "Take turns claiming a square. First to line up three — across, down or diagonally — wins."
LEVEL = "Easy"
MINUTES = "1 min"

LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8),
         (0, 3, 6), (1, 4, 7), (2, 5, 8),
         (0, 4, 8), (2, 4, 6)]


def new_state(starter):
    return {"board": [None] * 9, "turn": starter, "over": False,
            "winner": None, "line": None}


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    cell = mv.get("cell")
    if not isinstance(cell, int) or not 0 <= cell < 9:
        return "That square doesn't exist."
    if state["board"][cell] is not None:
        return "That square is already taken."

    state["board"][cell] = player
    for line in LINES:
        if all(state["board"][i] == player for i in line):
            state.update(over=True, winner=player, line=list(line))
            return None
    if all(c is not None for c in state["board"]):
        state["over"] = True  # draw
        return None
    state["turn"] = 1 - player
    return None


def view(state, player):
    return state
