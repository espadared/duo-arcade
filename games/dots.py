"""Dots and Boxes - draw lines between dots and claim the squares."""

KEY = "dots"
NAME = "Dots & Boxes"
EMOJI = "🔲"
TAGLINE = "Draw a line, close a box, claim it. Then go again."
RULES = ("Take turns drawing one line between two neighbouring dots. If your line "
         "closes a box, you claim it and take another turn straight away. "
         "The most boxes when the grid is full wins.")
LEVEL = "Medium"
MINUTES = "8 min"

SIZE = 5  # boxes across and down


def new_state(starter):
    return {"size": SIZE,
            "h": [[None] * SIZE for _ in range(SIZE + 1)],       # horizontal lines
            "v": [[None] * (SIZE + 1) for _ in range(SIZE)],     # vertical lines
            "boxes": [[None] * SIZE for _ in range(SIZE)],
            "turn": starter, "scores": [0, 0], "over": False,
            "winner": None, "last": None, "claimed": []}


def _box_done(state, r, c):
    return (state["h"][r][c] is not None and state["h"][r + 1][c] is not None
            and state["v"][r][c] is not None and state["v"][r][c + 1] is not None)


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    kind, r, c = mv.get("t"), mv.get("r"), mv.get("c")
    if kind not in ("h", "v") or not isinstance(r, int) or not isinstance(c, int):
        return "That isn't a line."
    grid = state[kind]
    if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
        return "That line doesn't exist."
    if grid[r][c] is not None:
        return "That line has already been drawn."

    grid[r][c] = player
    state["last"] = {"t": kind, "r": r, "c": c}

    # which boxes could this line possibly have closed?
    if kind == "h":
        candidates = [(r - 1, c), (r, c)]
    else:
        candidates = [(r, c - 1), (r, c)]

    claimed = []
    for br, bc in candidates:
        if 0 <= br < SIZE and 0 <= bc < SIZE and state["boxes"][br][bc] is None and _box_done(state, br, bc):
            state["boxes"][br][bc] = player
            state["scores"][player] += 1
            claimed.append([br, bc])
    state["claimed"] = claimed

    if sum(state["scores"]) == SIZE * SIZE:
        state["over"] = True
        if state["scores"][0] != state["scores"][1]:
            state["winner"] = state["scores"].index(max(state["scores"]))
    elif not claimed:
        state["turn"] = 1 - player  # closing a box earns you another go
    return None


def view(state, player):
    return state
