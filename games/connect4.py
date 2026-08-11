"""Connect Four - drop discs down a 7x6 grid and line up four."""

KEY = "connect4"
NAME = "Connect Four"
EMOJI = "🔴"
TAGLINE = "Drop your discs and line up four before they do."
RULES = ("Tap a column to drop your disc — it falls to the lowest free slot. "
         "Get four in a row in any direction to win.")
LEVEL = "Easy"
MINUTES = "5 min"

COLS = 7
ROWS = 6


def new_state(starter):
    return {"grid": [[None] * COLS for _ in range(ROWS)], "turn": starter,
            "over": False, "winner": None, "line": None, "last": None}


def _line_through(grid, row, col, player):
    """The four-in-a-row that passes through this disc, if there is one."""
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        cells = [(row, col)]
        for step in (1, -1):
            r, c = row + dr * step, col + dc * step
            while 0 <= r < ROWS and 0 <= c < COLS and grid[r][c] == player:
                cells.append((r, c))
                r, c = r + dr * step, c + dc * step
        if len(cells) >= 4:
            cells.sort()
            return [list(cell) for cell in cells]
    return None


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    col = mv.get("col")
    if not isinstance(col, int) or not 0 <= col < COLS:
        return "That column doesn't exist."

    grid = state["grid"]
    for row in range(ROWS - 1, -1, -1):
        if grid[row][col] is None:
            break
    else:
        return "That column is full — try another one."

    grid[row][col] = player
    state["last"] = [row, col]
    line = _line_through(grid, row, col, player)
    if line:
        state.update(over=True, winner=player, line=line)
        return None
    if all(cell is not None for cell in grid[0]):
        state["over"] = True  # draw
        return None
    state["turn"] = 1 - player
    return None


def view(state, player):
    return state
