"""Bridges - the connection game Hex, on a 9x9 rhombus.

One player joins the top edge to the bottom, the other joins left to right.
Because the two goals cross, exactly one player can ever succeed - there are
no draws in this game.
"""

from collections import deque

KEY = "bridges"
NAME = "Bridges"
EMOJI = "🌉"
TAGLINE = "Build an unbroken chain across the board before they cut you off."
RULES = ("Take turns claiming any empty cell. One of you is trying to join the "
         "top edge to the bottom edge, the other the left edge to the right — "
         "and cells touch on six sides, so chains can weave. Every blocking move "
         "you make also builds your own chain, which is the whole trick. "
         "Somebody always connects: Bridges cannot end in a draw.")
LEVEL = "Hard"
MINUTES = "12 min"

SIZE = 9
# a hex touches six neighbours in this rhombus layout
NEIGHBOURS = ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, 1), (1, -1))


def new_state(starter):
    return {"size": SIZE, "board": [None] * (SIZE * SIZE), "turn": starter,
            "over": False, "winner": None, "last": None, "path": None}


def _winning_path(board, player):
    """The chain joining `player`'s two home edges, if they have one yet.

    Player 0 runs top to bottom; player 1 runs left to right.
    """
    if player == 0:
        starts = [c for c in range(SIZE) if board[c] == 0]
        arrived = lambda idx: idx // SIZE == SIZE - 1
    else:
        starts = [r * SIZE for r in range(SIZE) if board[r * SIZE] == 1]
        arrived = lambda idx: idx % SIZE == SIZE - 1

    came_from = {s: None for s in starts}
    queue = deque(starts)
    while queue:
        idx = queue.popleft()
        if arrived(idx):
            path = [idx]
            while came_from[path[-1]] is not None:
                path.append(came_from[path[-1]])
            return path[::-1]
        row, col = divmod(idx, SIZE)
        for dr, dc in NEIGHBOURS:
            r, c = row + dr, col + dc
            if 0 <= r < SIZE and 0 <= c < SIZE:
                nxt = r * SIZE + c
                if nxt not in came_from and board[nxt] == player:
                    came_from[nxt] = idx
                    queue.append(nxt)
    return None


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    cell = mv.get("cell")
    if not isinstance(cell, int) or not 0 <= cell < SIZE * SIZE:
        return "That cell doesn't exist."
    if state["board"][cell] is not None:
        return "That cell is already taken."

    state["board"][cell] = player
    state["last"] = cell
    path = _winning_path(state["board"], player)
    if path:
        state.update(over=True, winner=player, path=path, turn=None)
        return None
    if all(c is not None for c in state["board"]):
        state["over"] = True  # can't happen in Hex, but never hang on a full board
        return None
    state["turn"] = 1 - player
    return None


def view(state, player):
    return state
