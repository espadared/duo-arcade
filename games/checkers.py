"""Checkers (English draughts) - jump their pieces and crown your kings."""

KEY = "checkers"
NAME = "Checkers"
EMOJI = "🔵"
TAGLINE = "Jump their pieces, crown your kings, take the board."
RULES = ("Pieces move diagonally forward one square. Jump over a neighbouring enemy "
         "piece to capture it — and if you can capture, you must. Chain jumps count "
         "as one turn. Reach the far side and your piece is crowned a king, which can "
         "move backwards too. Take all their pieces, or leave them with no move, to win.")
LEVEL = "Hard"
MINUTES = "15 min"

SIZE = 8
QUIET_LIMIT = 50  # moves by both players with no capture -> a draw


def new_state(starter):
    board = [None] * (SIZE * SIZE)
    for row in range(SIZE):
        for col in range(SIZE):
            if (row + col) % 2 == 0:
                continue  # only the dark squares are used
            if row < 3:
                board[row * SIZE + col] = {"o": 1, "k": False}
            elif row > 4:
                board[row * SIZE + col] = {"o": 0, "k": False}
    return {"size": SIZE, "board": board, "turn": starter, "over": False,
            "winner": None, "chain": None, "last": None, "quiet": 0,
            "counts": [12, 12]}


def _directions(piece):
    if piece["k"]:
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    forward = -1 if piece["o"] == 0 else 1  # player 0 sits at the bottom
    return [(forward, -1), (forward, 1)]


def _on_board(row, col):
    return 0 <= row < SIZE and 0 <= col < SIZE


def _captures_from(board, idx):
    piece = board[idx]
    row, col = divmod(idx, SIZE)
    out = []
    for dr, dc in _directions(piece):
        mid_r, mid_c = row + dr, col + dc
        end_r, end_c = row + 2 * dr, col + 2 * dc
        if not _on_board(end_r, end_c):
            continue
        mid = board[mid_r * SIZE + mid_c]
        if mid and mid["o"] != piece["o"] and board[end_r * SIZE + end_c] is None:
            out.append({"to": end_r * SIZE + end_c, "cap": mid_r * SIZE + mid_c})
    return out


def _steps_from(board, idx):
    piece = board[idx]
    row, col = divmod(idx, SIZE)
    out = []
    for dr, dc in _directions(piece):
        r, c = row + dr, col + dc
        if _on_board(r, c) and board[r * SIZE + c] is None:
            out.append({"to": r * SIZE + c, "cap": None})
    return out


def legal_moves(state, player):
    """Every move `player` may make right now, as {from: [move, ...]}."""
    board = state["board"]
    if state["chain"] is not None:
        jumps = _captures_from(board, state["chain"])
        return {state["chain"]: jumps} if jumps else {}

    owned = [i for i, p in enumerate(board) if p and p["o"] == player]
    captures = {i: _captures_from(board, i) for i in owned}
    captures = {i: m for i, m in captures.items() if m}
    if captures:
        return captures  # capturing is compulsory
    steps = {i: _steps_from(board, i) for i in owned}
    return {i: m for i, m in steps.items() if m}


def _crown_row(player):
    return 0 if player == 0 else SIZE - 1


def _end_turn(state, player):
    state["chain"] = None
    state["turn"] = 1 - player
    if not legal_moves(state, 1 - player):
        state.update(over=True, winner=player, turn=None)
    elif state["quiet"] >= QUIET_LIMIT:
        state.update(over=True, winner=None, turn=None)  # nobody is getting anywhere


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    src, dst = mv.get("from"), mv.get("to")
    if not isinstance(src, int) or not isinstance(dst, int):
        return "That isn't a move."

    options = legal_moves(state, player)
    board = state["board"]
    if src not in options or not (board[src] and board[src]["o"] == player):
        if any(m["cap"] for moves in options.values() for m in moves):
            return "You have a capture available — you have to take it."
        return "That piece can't move."
    chosen = next((m for m in options[src] if m["to"] == dst), None)
    if chosen is None:
        return "That piece can't go there."

    piece = board[src]
    board[src] = None
    board[dst] = piece
    state["last"] = [src, dst]

    if chosen["cap"] is not None:
        board[chosen["cap"]] = None
        state["counts"][1 - player] -= 1
        state["quiet"] = 0
    else:
        state["quiet"] += 1

    crowned = False
    if not piece["k"] and dst // SIZE == _crown_row(player):
        piece["k"] = True
        crowned = True  # being crowned ends your move

    if state["counts"][1 - player] == 0:
        state.update(over=True, winner=player, turn=None, chain=None)
        return None

    # a jump that can continue must continue
    if chosen["cap"] is not None and not crowned and _captures_from(board, dst):
        state["chain"] = dst
        return None

    _end_turn(state, player)
    return None


def view(state, player):
    out = dict(state)
    out["moves"] = {str(k): v for k, v in legal_moves(state, player).items()} \
        if state["turn"] == player and not state["over"] else {}
    out["flip"] = player == 1  # player 0 sits at the bottom of the board
    return out
