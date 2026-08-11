"""The game library.

Every game is one file with the same four things:

    new_state(starter)  -> a fresh game, with `starter` making the first move
    move(state, player, mv) -> None if the move was allowed, else a message
    view(state, player) -> what that player is allowed to see
    tick(state, now)    -> optional; for games with timers. True = something changed

Every state dict carries: turn (0, 1 or None), over (True/False),
winner (0, 1, or None for a draw), and note (a line of text for the players).

To add a new game: write the file, import it below, add it to MODULES,
and drop a matching renderer in static/games/.
"""

from . import (
    bridges,
    connect4,
    crosswires,
    dots,
    gomoku,
    memory,
    poker,
    reversi,
    rps,
    tictactoe,
    wordladder,
    xiangqi,
)

# The order here is the order they appear on the website.
MODULES = [
    tictactoe,
    connect4,
    rps,
    memory,
    wordladder,
    dots,
    crosswires,
    gomoku,
    reversi,
    bridges,
    poker,
    xiangqi,
]

GAMES = {m.KEY: m for m in MODULES}

CATALOG = [
    {
        "key": m.KEY,
        "name": m.NAME,
        "emoji": m.EMOJI,
        "tagline": m.TAGLINE,
        "rules": m.RULES,
        "level": m.LEVEL,
        "minutes": m.MINUTES,
    }
    for m in MODULES
]
