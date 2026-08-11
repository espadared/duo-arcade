"""Gomoku - five in a row on a 15x15 board."""

KEY = "gomoku"
NAME = "Gomoku"
EMOJI = "⚫"
TAGLINE = "Five in a row. Like Tic-Tac-Toe, but it never ends the same way twice."
RULES = ("Take turns placing a stone on any empty point. The first player to get "
         "five of their stones in an unbroken line — across, down or diagonally — wins.")
LEVEL = "Medium"
MINUTES = "10 min"

SIZE = 15
NEED = 5


def new_state(starter):
    return {"size": SIZE, "board": [None] * (SIZE * SIZE), "turn": starter,
            "over": False, "winner": None, "line": None, "last": None}


def _line_through(board, row, col, player):
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        cells = [(row, col)]
        for step in (1, -1):
            r, c = row + dr * step, col + dc * step
            while 0 <= r < SIZE and 0 <= c < SIZE and board[r * SIZE + c] == player:
                cells.append((r, c))
                r, c = r + dr * step, c + dc * step
        if len(cells) >= NEED:
            cells.sort()
            return [r * SIZE + c for r, c in cells]
    return None


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    cell = mv.get("cell")
    if not isinstance(cell, int) or not 0 <= cell < SIZE * SIZE:
        return "That point doesn't exist."
    if state["board"][cell] is not None:
        return "There's already a stone there."

    state["board"][cell] = player
    state["last"] = cell
    line = _line_through(state["board"], cell // SIZE, cell % SIZE, player)
    if line:
        state.update(over=True, winner=player, line=line)
        return None
    if all(c is not None for c in state["board"]):
        state["over"] = True  # a full board with no five in a row
        return None
    state["turn"] = 1 - player
    return None


def view(state, player):
    return state
