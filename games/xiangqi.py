"""Xiangqi (Chinese Chess) - the full game, with proper check and checkmate."""

KEY = "xiangqi"
NAME = "Chinese Chess"
EMOJI = "🀄"
TAGLINE = "Xiangqi in full — cannons, elephants, the river and the palace."
RULES = ("Trap the enemy General to win. Chariots move like rooks; cannons move like "
         "chariots but must jump exactly one piece to capture; horses are blocked by "
         "the square beside them; elephants move two diagonally and cannot cross the "
         "river; advisors and the General stay inside the palace; soldiers move "
         "forward, and sideways too once they've crossed the river. The two Generals "
         "may never face each other down an open file.")
LEVEL = "Hard"
MINUTES = "25 min"

W, H = 9, 10
QUIET_LIMIT = 120  # half-moves with no capture -> a draw

ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
# each horse move with the square that blocks it ("the horse's leg")
HORSE = ((-2, -1, -1, 0), (-2, 1, -1, 0), (2, -1, 1, 0), (2, 1, 1, 0),
         (-1, -2, 0, -1), (1, -2, 0, -1), (-1, 2, 0, 1), (1, 2, 0, 1))

BACK_RANK = ["R", "H", "E", "A", "K", "A", "E", "H", "R"]


def new_state(starter):
    """`starter` plays Red and moves first, so colours swap between rematches."""
    board = [None] * (W * H)
    bottom, top = starter, 1 - starter
    for col, kind in enumerate(BACK_RANK):
        board[9 * W + col] = {"p": kind, "o": bottom}
        board[0 * W + col] = {"p": kind, "o": top}
    for col in (1, 7):
        board[7 * W + col] = {"p": "C", "o": bottom}
        board[2 * W + col] = {"p": "C", "o": top}
    for col in (0, 2, 4, 6, 8):
        board[6 * W + col] = {"p": "P", "o": bottom}
        board[3 * W + col] = {"p": "P", "o": top}

    state = {"w": W, "h": H, "board": board, "bottom": bottom, "red": bottom,
             "turn": starter, "over": False, "winner": None, "last": None,
             "quiet": 0, "check": False, "captured": [[], []], "legal": {}}
    state["legal"] = {str(k): v for k, v in legal_moves(board, starter, bottom).items()}
    return state


# --- geometry -------------------------------------------------------------

def _own_half(owner, bottom, row):
    return row >= 5 if owner == bottom else row <= 4


def _in_palace(owner, bottom, row, col):
    if not 3 <= col <= 5:
        return False
    return 7 <= row <= 9 if owner == bottom else 0 <= row <= 2


def _pseudo(board, idx, bottom):
    """Where this piece could go if we ignore whether it exposes the General."""
    piece = board[idx]
    owner, kind = piece["o"], piece["p"]
    row, col = divmod(idx, W)
    out = []

    def add(r, c):
        if 0 <= r < H and 0 <= c < W:
            target = board[r * W + c]
            if target is None or target["o"] != owner:
                out.append(r * W + c)

    if kind == "R":
        for dr, dc in ORTHOGONAL:
            r, c = row + dr, col + dc
            while 0 <= r < H and 0 <= c < W:
                target = board[r * W + c]
                if target is None:
                    out.append(r * W + c)
                else:
                    if target["o"] != owner:
                        out.append(r * W + c)
                    break
                r, c = r + dr, c + dc

    elif kind == "C":
        for dr, dc in ORTHOGONAL:
            r, c = row + dr, col + dc
            jumped = False
            while 0 <= r < H and 0 <= c < W:
                target = board[r * W + c]
                if not jumped:
                    if target is None:
                        out.append(r * W + c)   # moves like a chariot when not capturing
                    else:
                        jumped = True           # this is the screen to fire over
                elif target is not None:
                    if target["o"] != owner:
                        out.append(r * W + c)
                    break
                r, c = r + dr, c + dc

    elif kind == "H":
        for dr, dc, br, bc in HORSE:
            r, c = row + br, col + bc
            if 0 <= r < H and 0 <= c < W and board[r * W + c] is None:
                add(row + dr, col + dc)

    elif kind == "E":
        for dr, dc in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
            r, c = row + dr, col + dc
            if not (0 <= r < H and 0 <= c < W):
                continue
            if not _own_half(owner, bottom, r):
                continue  # elephants never cross the river
            if board[(row + dr // 2) * W + (col + dc // 2)] is not None:
                continue  # the elephant's eye is blocked
            add(r, c)

    elif kind == "A":
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            if _in_palace(owner, bottom, row + dr, col + dc):
                add(row + dr, col + dc)

    elif kind == "K":
        for dr, dc in ORTHOGONAL:
            if _in_palace(owner, bottom, row + dr, col + dc):
                add(row + dr, col + dc)

    elif kind == "P":
        forward = -1 if owner == bottom else 1
        add(row + forward, col)
        if not _own_half(owner, bottom, row):  # crossed the river
            add(row, col - 1)
            add(row, col + 1)

    return out


# --- check and legality ---------------------------------------------------

def _general(board, owner):
    for i, piece in enumerate(board):
        if piece and piece["p"] == "K" and piece["o"] == owner:
            return i
    return None


def _generals_face(board):
    a, b = _general(board, 0), _general(board, 1)
    if a is None or b is None or a % W != b % W:
        return False
    col = a % W
    low, high = sorted((a // W, b // W))
    return all(board[r * W + col] is None for r in range(low + 1, high))


def in_check(board, owner, bottom):
    king = _general(board, owner)
    if king is None:
        return True
    if _generals_face(board):
        return True
    for i, piece in enumerate(board):
        if piece and piece["o"] != owner and king in _pseudo(board, i, bottom):
            return True
    return False


def legal_moves(board, owner, bottom):
    """Pseudo-moves minus anything that would leave your own General exposed."""
    out = {}
    for i, piece in enumerate(board):
        if not piece or piece["o"] != owner:
            continue
        safe = []
        for target in _pseudo(board, i, bottom):
            captured = board[target]
            board[target], board[i] = piece, None
            if not in_check(board, owner, bottom):
                safe.append(target)
            board[i], board[target] = piece, captured
        if safe:
            out[i] = safe
    return out


# --- playing --------------------------------------------------------------

def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    src, dst = mv.get("from"), mv.get("to")
    if not isinstance(src, int) or not isinstance(dst, int):
        return "That isn't a move."
    allowed = state["legal"].get(str(src))
    if not allowed:
        return "That piece has no move right now."
    if dst not in allowed:
        return "That piece can't go there."

    board = state["board"]
    taken = board[dst]
    board[dst] = board[src]
    board[src] = None
    state["last"] = [src, dst]
    if taken:
        state["captured"][player].append(taken["p"])
        state["quiet"] = 0
    else:
        state["quiet"] += 1

    opponent = 1 - player
    bottom = state["bottom"]
    moves = legal_moves(board, opponent, bottom)
    state["legal"] = {str(k): v for k, v in moves.items()}
    state["check"] = in_check(board, opponent, bottom)
    state["turn"] = opponent

    if not moves:
        # in Xiangqi, having no legal move loses - stalemate included
        state.update(over=True, winner=player, turn=None)
    elif state["quiet"] >= QUIET_LIMIT:
        state.update(over=True, winner=None, turn=None)
    return None


def view(state, player):
    return {"w": W, "h": H, "board": state["board"], "red": state["red"],
            "bottom": state["bottom"], "flip": player != state["bottom"],
            "turn": state["turn"], "over": state["over"], "winner": state["winner"],
            "last": state["last"], "check": state["check"],
            "captured": state["captured"],
            "moves": state["legal"] if state["turn"] == player and not state["over"] else {}}
