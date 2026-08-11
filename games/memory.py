"""Memory Match - flip cards two at a time and remember where the pairs are."""

import random
import time

KEY = "memory"
NAME = "Memory Match"
EMOJI = "🧠"
TAGLINE = "Flip two cards. Find the pairs. Trust your memory."
RULES = ("On your turn, flip over two cards. If they match you keep the pair and go "
         "again. If they don't, they flip back and it's your opponent's turn. "
         "Whoever collects the most pairs wins.")
LEVEL = "Easy"
MINUTES = "5 min"

COLS = 6
ROWS = 4
PAIRS = COLS * ROWS // 2
HIDE_SECONDS = 1.4

SYMBOLS = ["🍕", "🌵", "🐙", "🎈", "🍩", "🚀", "🦊", "🌈", "🎸", "🍋",
           "🐳", "⚡", "🍄", "🎲", "🦋", "🌻"]


def new_state(starter):
    picked = random.sample(SYMBOLS, PAIRS)
    cards = picked * 2
    random.shuffle(cards)
    return {"cols": COLS, "rows": ROWS, "cards": cards,
            "matched": [None] * len(cards), "up": [],
            "turn": starter, "scores": [0, 0], "over": False,
            "winner": None, "hideAt": 0}


def move(state, player, mv):
    if state["over"]:
        return "The game is already finished."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    if state["hideAt"]:
        return "Take a look at those two first…"
    cell = mv.get("cell")
    if not isinstance(cell, int) or not 0 <= cell < len(state["cards"]):
        return "That card doesn't exist."
    if state["matched"][cell] is not None:
        return "That pair has already been won."
    if cell in state["up"]:
        return "That card is already face up."

    state["up"].append(cell)
    if len(state["up"]) < 2:
        return None

    first, second = state["up"]
    if state["cards"][first] == state["cards"][second]:
        state["matched"][first] = player
        state["matched"][second] = player
        state["scores"][player] += 1
        state["up"] = []
        if all(m is not None for m in state["matched"]):
            state["over"] = True
            if state["scores"][0] != state["scores"][1]:
                state["winner"] = state["scores"].index(max(state["scores"]))
    else:
        state["hideAt"] = time.time() + HIDE_SECONDS  # leave them up for a moment
    return None


def tick(state, now):
    if not state["hideAt"] or now < state["hideAt"]:
        return False
    state["up"] = []
    state["hideAt"] = 0
    state["turn"] = 1 - state["turn"]
    return True


def view(state, player):
    visible = [
        state["cards"][i] if (state["matched"][i] is not None or i in state["up"]) else None
        for i in range(len(state["cards"]))
    ]
    return {"cols": COLS, "rows": ROWS, "faces": visible, "matched": state["matched"],
            "up": list(state["up"]), "turn": state["turn"], "scores": state["scores"],
            "over": state["over"], "winner": state["winner"],
            "waiting": bool(state["hideAt"])}
