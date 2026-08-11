"""Reversi (Othello) - trap your opponent's discs and flip them to your colour."""

KEY = "reversi"
NAME = "Reversi"
EMOJI = "⚪"
TAGLINE = "Sandwich their discs and flip the whole board your colour."
RULES = ("Place a disc so that one or more of your opponent's discs sit in a straight "
         "line between it and another of your discs — every trapped disc flips to your "
         "colour. You must flip at least one disc; if you can't move, your turn is "
         "skipped. Most discs at the end wins.")
LEVEL = "Medium"
MINUTES = "12 min"

SIZE = 8
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def new_state(starter):
    board = [[None] * SIZE for _ in range(SIZE)]
    board[3][3] = board[4][4] = 1
    board[3][4] = board[4][3] = 0
    return {"size": SIZE, "board": board, "turn": 0, "over": False, "winner": None,
            "scores": [2, 2], "last": None, "skipped": None}
    # Reversi always opens with dark, so `starter` is deliberately ignored.


def _flips(board, row, col, player):
    """Every disc that would flip if `player` played here (empty list = illegal)."""
    if board[row][col] is not None:
        return []
    won = []
    for dr, dc in DIRECTIONS:
        r, c, run = row + dr, col + dc, []
        while 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == 1 - player:
            run.append((r, c))
            r, c = r + dr, c + dc
        if run and 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == player:
            won.extend(run)
    return won


def _legal_moves(board, player):
    return {r * SIZE + c: _flips(board, r, c, player)
            for r in range(SIZE) for c in range(SIZE)
            if _flips(board, r, c, player)}


def _count(board):
    flat = [cell for row in board for cell in row]
    return [flat.count(0), flat.count(1)]


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    cell = mv.get("cell")
    if not isinstance(cell, int) or not 0 <= cell < SIZE * SIZE:
        return "That square doesn't exist."

    board = state["board"]
    row, col = divmod(cell, SIZE)
    won = _flips(board, row, col, player)
    if not won:
        return "You have to flip at least one of their discs."

    board[row][col] = player
    for r, c in won:
        board[r][c] = player
    state["last"] = cell
    state["scores"] = _count(board)

    # the other player goes next - unless they have nowhere to play
    if _legal_moves(board, 1 - player):
        state["turn"] = 1 - player
        state["skipped"] = None
    elif _legal_moves(board, player):
        state["skipped"] = 1 - player  # they have to pass
    else:
        state["over"] = True
        if state["scores"][0] != state["scores"][1]:
            state["winner"] = state["scores"].index(max(state["scores"]))
    return None


def view(state, player):
    out = dict(state)
    out["valid"] = sorted(_legal_moves(state["board"], player)) if not state["over"] else []
    return out
