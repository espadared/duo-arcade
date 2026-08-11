"""Crosswires - the classic blocking game Bridg-It (also known as Gale).

Two lattices of posts sit interleaved. Every wire one player could draw crosses
exactly one wire the other could draw, so claiming a gap always does two jobs at
once: it extends your own route and severs one of theirs.

Everything lives on a single (2N+1) x (2N+1) grid of coordinates:

    (even row, odd  col)  a post belonging to player 0
    (odd  row, even col)  a post belonging to player 1
    (odd  row, odd  col)  a gap: player 0's vertical wire OR player 1's horizontal
    (even row, even col)  a gap: player 0's horizontal wire OR player 1's vertical

Player 0 is trying to join the top row to the bottom; player 1, left to right.
"""

from collections import deque

KEY = "crosswires"
NAME = "Crosswires"
EMOJI = "🔌"
TAGLINE = "Wire your way across the board — every wire you lay cuts one of theirs."
RULES = ("Take turns joining two of your own posts that sit side by side. One of "
         "you is wiring top to bottom, the other left to right. The two grids "
         "overlap, so every gap can hold only one wire — taking it for yourself "
         "is also the only way to block them. Somebody always gets through.")
LEVEL = "Medium"
MINUTES = "10 min"

N = 5
SPAN = 2 * N  # coordinates run 0..SPAN on both axes


def _wires_for(player):
    """Map of gap coordinate -> the two posts that wire would join."""
    wires = {}
    if player == 0:
        for row in range(0, SPAN + 1, 2):                     # horizontal wires
            for col in range(2, SPAN - 1, 2):
                wires[(row, col)] = ((row, col - 1), (row, col + 1))
        for row in range(1, SPAN, 2):                         # vertical wires
            for col in range(1, SPAN, 2):
                wires[(row, col)] = ((row - 1, col), (row + 1, col))
    else:
        for row in range(1, SPAN, 2):                         # horizontal wires
            for col in range(1, SPAN, 2):
                wires[(row, col)] = ((row, col - 1), (row, col + 1))
        for row in range(2, SPAN - 1, 2):                     # vertical wires
            for col in range(0, SPAN + 1, 2):
                wires[(row, col)] = ((row - 1, col), (row + 1, col))
    return wires


WIRES = (_wires_for(0), _wires_for(1))


def new_state(starter):
    return {"n": N, "span": SPAN,
            "grid": [[None] * (SPAN + 1) for _ in range(SPAN + 1)],
            "turn": starter, "over": False, "winner": None,
            "last": None, "counts": [0, 0]}


def _connected(grid, player):
    """Has this player joined their two home edges yet?"""
    links = {}
    for (row, col), (a, b) in WIRES[player].items():
        if grid[row][col] == player:
            links.setdefault(a, []).append(b)
            links.setdefault(b, []).append(a)
    if player == 0:
        starts = [p for p in links if p[0] == 0]
        arrived = lambda p: p[0] == SPAN
    else:
        starts = [p for p in links if p[1] == 0]
        arrived = lambda p: p[1] == SPAN

    seen = set(starts)
    queue = deque(starts)
    while queue:
        post = queue.popleft()
        if arrived(post):
            return True
        for nxt in links.get(post, []):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return False


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    row, col = mv.get("r"), mv.get("c")
    if (row, col) not in WIRES[player]:
        return "You can't lay a wire there."
    if state["grid"][row][col] is not None:
        return "That gap is already wired."

    state["grid"][row][col] = player
    state["last"] = [row, col]
    state["counts"][player] += 1

    if _connected(state["grid"], player):
        state.update(over=True, winner=player, turn=None)
        return None
    if not any(state["grid"][r][c] is None for r, c in WIRES[1 - player]):
        state["over"] = True  # nowhere left for them to play
        state["winner"] = player if _connected(state["grid"], player) else None
        state["turn"] = None
        return None
    state["turn"] = 1 - player
    return None


def view(state, player):
    out = dict(state)
    # the gaps this player could still take, so their side can be highlighted
    out["yours"] = sorted([r, c] for r, c in WIRES[player] if state["grid"][r][c] is None) \
        if state["turn"] == player and not state["over"] else []
    return out
