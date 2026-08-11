"""Rock Paper Scissors - best of five, both choosing at the same time."""

import time

KEY = "rps"
NAME = "Rock Paper Scissors"
EMOJI = "✊"
TAGLINE = "Best of five. Both of you choose at the same time."
RULES = ("Both players choose in secret, then the throws are revealed together. "
         "Rock beats scissors, scissors beats paper, paper beats rock. "
         "First to win three rounds takes it.")
LEVEL = "Easy"
MINUTES = "2 min"

THROWS = ["rock", "paper", "scissors"]
BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
BEST_OF = 5
NEEDED = BEST_OF // 2 + 1
REVEAL_SECONDS = 2.6


def new_state(starter):
    return {"turn": None, "over": False, "winner": None, "round": 1,
            "picks": [None, None], "wins": [0, 0], "history": [],
            "reveal": None, "revealUntil": 0}


def move(state, player, mv):
    if state["over"]:
        return "The match is already finished."
    if state["reveal"]:
        return "Wait for the round to finish."
    if state["picks"][player] is not None:
        return "You've locked in already — waiting for your opponent."
    pick = mv.get("pick")
    if pick not in THROWS:
        return "Choose rock, paper or scissors."

    state["picks"][player] = pick
    if all(p is not None for p in state["picks"]):
        _resolve(state)
    return None


def _resolve(state):
    a, b = state["picks"]
    if a == b:
        result = None
    elif BEATS[a] == b:
        result = 0
    else:
        result = 1
    if result is not None:
        state["wins"][result] += 1
    state["reveal"] = {"picks": [a, b], "result": result}
    state["revealUntil"] = time.time() + REVEAL_SECONDS
    state["history"].append({"picks": [a, b], "result": result})


def tick(state, now):
    """After the reveal has been on screen for a moment, start the next round."""
    if state["over"] or not state["reveal"] or now < state["revealUntil"]:
        return False
    state["reveal"] = None
    state["picks"] = [None, None]
    if max(state["wins"]) >= NEEDED:
        state["over"] = True
        state["winner"] = state["wins"].index(max(state["wins"]))
    elif len(state["history"]) >= BEST_OF:
        state["over"] = True
        if state["wins"][0] != state["wins"][1]:
            state["winner"] = state["wins"].index(max(state["wins"]))
    else:
        state["round"] += 1
    return True


def view(state, player):
    out = {k: state[k] for k in ("over", "winner", "round", "wins", "reveal", "turn")}
    out["bestOf"] = BEST_OF
    out["needed"] = NEEDED
    out["yourPick"] = state["picks"][player]
    # you can see *that* they've chosen, never *what* they chose
    out["theyPicked"] = state["picks"][1 - player] is not None
    out["history"] = state["history"]
    if state["reveal"]:
        out["revealIn"] = max(0, state["revealUntil"] - time.time())
    return out
