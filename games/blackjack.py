"""Blackjack, head to head - no dealer, just the two of you, best of five."""

import random
import time

KEY = "blackjack"
NAME = "Blackjack"
EMOJI = "🃏"
TAGLINE = "Get closer to 21 than they do. No dealer — just the two of you."
RULES = ("Each round you're both dealt two cards, one of them face down to your "
         "opponent. Hit to take another card or stand to stop. Go over 21 and you "
         "bust and lose the round. Closest to 21 wins the round — best of five wins "
         "the match.")
LEVEL = "Easy"
MINUTES = "6 min"

BEST_OF = 5
NEEDED = BEST_OF // 2 + 1
REVEAL_SECONDS = 4.0

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["♠", "♥", "♦", "♣"]


def _fresh_deck():
    deck = [{"r": r, "s": s} for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def total(cards):
    """Best total that isn't a bust, treating aces as 11 where it helps."""
    value, aces = 0, 0
    for card in cards:
        if card["r"] == "A":
            value += 11
            aces += 1
        elif card["r"] in ("J", "Q", "K", "10"):
            value += 10
        else:
            value += int(card["r"])
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


def _is_blackjack(cards):
    return len(cards) == 2 and total(cards) == 21


def _deal(state):
    deck = _fresh_deck()
    state["deck"] = deck
    state["hands"] = [[deck.pop(), deck.pop()], [deck.pop(), deck.pop()]]
    state["done"] = [False, False]
    state["result"] = None
    # take turns going first, so neither player always acts with more information
    first = (state["firstActor"] + 1) % 2 if state["round"] > 1 else state["firstActor"]
    state["firstActor"] = first
    state["turn"] = first
    # a dealt blackjack stands on its own
    for player in (0, 1):
        if _is_blackjack(state["hands"][player]):
            state["done"][player] = True
    if all(state["done"]):
        _finish_round(state)
    elif state["done"][state["turn"]]:
        state["turn"] = 1 - state["turn"]


def new_state(starter):
    state = {"turn": starter, "over": False, "winner": None, "round": 1,
             "wins": [0, 0], "hands": [[], []], "done": [False, False],
             "deck": [], "result": None, "revealUntil": 0, "firstActor": starter,
             "bestOf": BEST_OF}
    _deal(state)
    return state


def _finish_round(state):
    hands = state["hands"]
    totals = [total(hands[0]), total(hands[1])]
    busts = [totals[0] > 21, totals[1] > 21]

    if busts[0] and busts[1]:
        winner, reason = None, "You both went bust!"
    elif busts[0]:
        winner, reason = 1, f"{{p0}} went bust on {totals[0]}."
    elif busts[1]:
        winner, reason = 0, f"{{p1}} went bust on {totals[1]}."
    elif _is_blackjack(hands[0]) and not _is_blackjack(hands[1]):
        winner, reason = 0, "Blackjack!"
    elif _is_blackjack(hands[1]) and not _is_blackjack(hands[0]):
        winner, reason = 1, "Blackjack!"
    elif totals[0] == totals[1]:
        winner, reason = None, f"Both on {totals[0]} — nobody wins this one."
    else:
        winner = 0 if totals[0] > totals[1] else 1
        reason = f"{max(totals)} beats {min(totals)}."

    if winner is not None:
        state["wins"][winner] += 1
    state["result"] = {"totals": totals, "winner": winner, "reason": reason,
                       "hands": [list(hands[0]), list(hands[1])]}
    state["revealUntil"] = time.time() + REVEAL_SECONDS
    state["turn"] = None


def move(state, player, mv):
    if state["over"]:
        return "The match is already finished."
    if state["result"]:
        return "Wait for the next round to be dealt."
    if state["turn"] != player:
        return "Hold on — it's not your turn."
    action = mv.get("action")
    if action not in ("hit", "stand"):
        return "Choose hit or stand."

    if action == "hit":
        state["hands"][player].append(state["deck"].pop())
        if total(state["hands"][player]) > 21:
            state["done"] = [True, True]  # a bust settles the round straight away
            _finish_round(state)
            return None
        if total(state["hands"][player]) == 21:
            state["done"][player] = True  # 21 needs no more cards
    else:
        state["done"][player] = True

    if all(state["done"]):
        _finish_round(state)
    elif state["done"][state["turn"]]:
        state["turn"] = 1 - state["turn"]
    return None


def tick(state, now):
    if state["over"] or not state["result"] or now < state["revealUntil"]:
        return False
    if max(state["wins"]) >= NEEDED or state["round"] >= BEST_OF:
        state["over"] = True
        if state["wins"][0] != state["wins"][1]:
            state["winner"] = state["wins"].index(max(state["wins"]))
        state["turn"] = None
        return True
    state["round"] += 1
    _deal(state)
    return True


def view(state, player):
    showdown = state["result"] is not None
    mine = state["hands"][player]
    theirs = state["hands"][1 - player]
    if showdown:
        their_cards = theirs
        their_total = total(theirs)
    else:
        # their first card stays face down until the round is settled
        their_cards = [{"hidden": True}] + theirs[1:]
        their_total = total(theirs[1:])

    result = state["result"]
    if result:
        # the reason text carries {p0}/{p1} markers; the client swaps in real names
        result = dict(result)
        result["youWon"] = result["winner"] == player
        result["mine"] = result["totals"][player]
        result["theirs"] = result["totals"][1 - player]

    return {"turn": state["turn"], "over": state["over"], "winner": state["winner"],
            "round": state["round"], "bestOf": BEST_OF, "needed": NEEDED,
            "wins": state["wins"], "yourCards": mine, "yourTotal": total(mine),
            "theirCards": their_cards, "theirTotal": their_total,
            "yourDone": state["done"][player], "theirDone": state["done"][1 - player],
            "result": result, "showdown": showdown}
