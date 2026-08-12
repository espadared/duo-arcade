"""Heads-up Texas Hold'em against the clock, with a dealer running the table.

Both players start with the same pile of chips. The blinds climb every few
hands, so the stacks get shallower and shallower in relative terms until
somebody is all in before the flop and simply has to show. Win all the chips
to win the match.

The dealer is scenery - it deals, narrates and never plays a hand.
"""

import random
import time
from collections import Counter
from itertools import combinations

KEY = "poker"
NAME = "Poker"
EMOJI = "♠️"
TAGLINE = "Heads-up Texas Hold'em. Rising blinds until somebody has to show."
RULES = ("You each start with 1,000 chips. Every hand you get two cards face down "
         "and share five in the middle, betting after each one is revealed — fold, "
         "check, call or raise. Best five-card hand takes the pot. The blinds go up "
         "every few hands, so sitting back gets expensive and eventually somebody is "
         "all in before the flop. Win all the chips to win the match.")
LEVEL = "Hard"
MINUTES = "20 min"

START_STACK = 1000
HANDS_PER_LEVEL = 4
BLIND_LEVELS = [(10, 20), (20, 40), (40, 80), (75, 150),
                (150, 300), (300, 600), (600, 1200), (1000, 2000)]

SHOWDOWN_SECONDS = 7.0  # long enough to read both hands and the board
FOLD_SECONDS = 5.0      # counts down 5, 4, 3, 2, 1

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["♠", "♥", "♦", "♣"]
VALUE = {rank: index + 2 for index, rank in enumerate(RANKS)}

HAND_NAMES = ["High card", "Pair", "Two pair", "Three of a kind", "Straight",
              "Flush", "Full house", "Four of a kind", "Straight flush"]


# --- working out who won ---------------------------------------------------

def _score_five(cards):
    """Rank exactly five cards. Bigger tuple wins, and ties compare equal."""
    values = sorted((VALUE[c["r"]] for c in cards), reverse=True)
    counts = Counter(values)
    # by how many of a rank first, then by the rank itself
    grouped = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))
    flush = len({c["s"] for c in cards}) == 1

    straight_high = None
    distinct = sorted(set(values), reverse=True)
    if len(distinct) == 5:
        if distinct[0] - distinct[4] == 4:
            straight_high = distinct[0]
        elif distinct == [14, 5, 4, 3, 2]:
            straight_high = 5  # the wheel: A-2-3-4-5, ace plays low

    singles = sorted((rank for rank, n in grouped if n == 1), reverse=True)
    pairs = sorted((rank for rank, n in grouped if n == 2), reverse=True)

    if flush and straight_high:
        return (8, straight_high)
    if grouped[0][1] == 4:
        return (7, grouped[0][0], singles[0])
    if grouped[0][1] == 3 and grouped[1][1] >= 2:
        return (6, grouped[0][0], grouped[1][0])
    if flush:
        return (5, *values)
    if straight_high:
        return (4, straight_high)
    if grouped[0][1] == 3:
        return (3, grouped[0][0], *singles)
    if len(pairs) >= 2:
        return (2, pairs[0], pairs[1], singles[0])
    if pairs:
        return (1, pairs[0], *singles)
    return (0, *values)


def best_hand(cards):
    """Best five-card score available from seven cards."""
    return max(_score_five(list(five)) for five in combinations(cards, 5))


def hand_name(score):
    return HAND_NAMES[score[0]]


FULL_DECK = [{"r": rank, "s": suit} for rank in RANKS for suit in SUITS]
EQUITY_SAMPLES = 900  # about a point of error, and only paid once per street


def equity(hole, board):
    """Chance these two cards end up winning, and the chance of a tie.

    Worked out from *only* what this player can already see - their own two
    cards and the shared board. The opponent's real hand is deliberately left
    in the pool of unknown cards, because a number calculated against their
    actual holding would itself give away what they have.

    With every card out the maths is exact; before that it is estimated by
    dealing out random finishes, so treat it as a guide rather than gospel.
    """
    seen = {(c["r"], c["s"]) for c in hole + board}
    rest = [c for c in FULL_DECK if (c["r"], c["s"]) not in seen]
    still_to_come = 5 - len(board)
    wins = ties = total = 0

    if still_to_come == 0:
        mine = best_hand(hole + board)
        for pair in combinations(rest, 2):
            theirs = best_hand(list(pair) + board)
            total += 1
            wins += mine > theirs
            ties += mine == theirs
    else:
        for _ in range(EQUITY_SAMPLES):
            drawn = random.sample(rest, 2 + still_to_come)
            finished = board + drawn[2:]
            mine = best_hand(hole + finished)
            theirs = best_hand(drawn[:2] + finished)
            total += 1
            wins += mine > theirs
            ties += mine == theirs

    return wins / total, ties / total


# --- setting up ------------------------------------------------------------

def _fresh_deck():
    deck = [{"r": rank, "s": suit} for rank in RANKS for suit in SUITS]
    random.shuffle(deck)
    return deck


def new_state(starter):
    state = {
        "stacks": [START_STACK, START_STACK],
        "button": starter,          # the button posts the small blind heads-up
        "hand": 0, "level": 0,
        "over": False, "winner": None, "turn": None,
        "startStack": START_STACK,
    }
    _start_hand(state)
    return state


def _blinds(state):
    level = min(state["level"], len(BLIND_LEVELS) - 1)
    return BLIND_LEVELS[level]


def _post(state, player, amount):
    """Move chips from a stack into the pot for this street."""
    amount = min(amount, state["stacks"][player])
    state["stacks"][player] -= amount
    state["bets"][player] += amount
    if state["stacks"][player] == 0:
        state["allIn"][player] = True
    return amount


def _start_hand(state):
    state["hand"] += 1
    state["level"] = (state["hand"] - 1) // HANDS_PER_LEVEL
    small, big = _blinds(state)

    deck = _fresh_deck()
    state["deck"] = deck
    state["holes"] = [[deck.pop(), deck.pop()], [deck.pop(), deck.pop()]]
    state["board"] = []
    state["street"] = "preflop"
    state["pot"] = 0
    state["bets"] = [0, 0]
    state["folded"] = [False, False]
    state["allIn"] = [False, False]
    state["acted"] = []
    state["result"] = None
    state["pending"] = 0
    state["log"] = []

    button = state["button"]
    _post(state, button, small)            # heads-up: the button is the small blind
    _post(state, 1 - button, big)
    state["lastRaise"] = big
    state["turn"] = button                 # and acts first before the flop
    state["says"] = f"Blinds {small}/{big}. Good luck."
    _refresh_odds(state)
    _skip_if_cannot_act(state)


def _refresh_odds(state):
    """Recalculate both players' chances. Only ever called when a card lands,
    so the cost is paid once a street rather than on every screen refresh."""
    state["odds"] = [equity(state["holes"][p], state["board"]) for p in (0, 1)]


def _skip_if_cannot_act(state):
    """Posting a blind can put someone all in; then there is nothing to decide."""
    if not _anyone_to_act(state):
        _end_street(state)
    elif not _must_act(state, state["turn"]):
        state["turn"] = 1 - state["turn"]


# --- the betting round -----------------------------------------------------

def _must_act(state, player):
    if state["folded"][player] or state["allIn"][player]:
        return False
    if player not in state["acted"]:
        return True
    return state["bets"][player] < max(state["bets"])


def _anyone_to_act(state):
    return any(_must_act(state, p) for p in (0, 1))


def _live(state):
    return [p for p in (0, 1) if not state["folded"][p]]


def to_call(state, player):
    return min(max(state["bets"]) - state["bets"][player], state["stacks"][player])


def min_raise_to(state, player):
    """Smallest total bet a raise may go to, capped by what they actually have."""
    target = max(state["bets"]) + state["lastRaise"]
    ceiling = state["stacks"][player] + state["bets"][player]
    return min(target, ceiling)


def move(state, player, mv):
    if state["over"]:
        return "The match is already finished."
    if state["result"]:
        return "Wait for the next hand to be dealt."
    if state["turn"] != player:
        return "Hold on — it's not your turn."

    action = mv.get("action")
    owed = to_call(state, player)
    name = "You"

    if action == "fold":
        state["folded"][player] = True
        state["acted"].append(player)
        _note(state, f"{{p{player}}} folds")
        _finish_hand(state, winner=1 - player, reason="fold")
        return None

    if action == "check":
        if owed > 0:
            return f"You can't check — there's {owed} to call."
        state["acted"].append(player)
        _note(state, f"{{p{player}}} checks")

    elif action == "call":
        if owed <= 0:
            return "There's nothing to call — check instead."
        paid = _post(state, player, owed)
        state["acted"].append(player)
        _note(state, f"{{p{player}}} calls {paid}")

    elif action == "raise":
        target = mv.get("to")
        if not isinstance(target, int):
            return "How much do you want to raise to?"
        ceiling = state["stacks"][player] + state["bets"][player]
        if target > ceiling:
            return "You don't have that many chips."
        if target <= max(state["bets"]):
            return "A raise has to be more than the current bet."
        if target < min_raise_to(state, player) and target < ceiling:
            return f"The smallest raise is to {min_raise_to(state, player)}."
        increase = target - max(state["bets"])
        _post(state, player, target - state["bets"][player])
        if increase >= state["lastRaise"]:
            state["lastRaise"] = increase
        # a raise puts the decision back on the opponent
        state["acted"] = [player]
        verb = "goes all in for" if state["allIn"][player] else "raises to"
        _note(state, f"{{p{player}}} {verb} {target}")

    else:
        return "Choose fold, check, call or raise."

    if _anyone_to_act(state):
        other = 1 - player
        state["turn"] = other if _must_act(state, other) else player
    else:
        _end_street(state)
    return None


def _note(state, text):
    state["log"].append(text)
    del state["log"][:-6]
    state["says"] = text


# --- moving between streets ------------------------------------------------

def _collect(state):
    """Sweep this street's bets into the pot, handing back anything uncalled."""
    high, low = max(state["bets"]), min(state["bets"])
    if high > low:
        # heads-up has no side pots: the extra simply comes back
        payer = state["bets"].index(high)
        state["stacks"][payer] += high - low
        state["bets"][payer] = low
        if state["stacks"][payer] > 0:
            state["allIn"][payer] = False
    state["pot"] += sum(state["bets"])
    state["bets"] = [0, 0]


def _end_street(state):
    _collect(state)

    if len(_live(state)) == 1:
        _finish_hand(state, winner=_live(state)[0], reason="fold")
        return

    order = ["preflop", "flop", "turn", "river"]
    if state["street"] == "river":
        _showdown(state)
        return

    # if nobody can bet any more, run the rest of the board out and show
    if all(state["allIn"][p] or state["stacks"][p] == 0 for p in _live(state)) or \
            sum(1 for p in _live(state) if not state["allIn"][p]) < 2:
        # nobody can bet again, so run the board out without recalculating
        # odds for streets that will never be shown on their own
        while state["street"] != "river":
            _deal_next(state, order)
        _showdown(state)
        return

    _deal_next(state, order)
    _refresh_odds(state)
    state["acted"] = []
    state["lastRaise"] = _blinds(state)[1]
    first = 1 - state["button"]        # out of position acts first after the flop
    state["turn"] = first if _must_act(state, first) else 1 - first


def _deal_next(state, order):
    step = order[order.index(state["street"]) + 1]
    state["street"] = step
    state["deck"].pop()                # burn one, as at a real table
    count = 3 if step == "flop" else 1
    for _ in range(count):
        state["board"].append(state["deck"].pop())
    state["says"] = {"flop": "Here comes the flop.",
                     "turn": "The turn.",
                     "river": "And the river."}[step]


# --- ending a hand ---------------------------------------------------------

def _showdown(state):
    scores = [best_hand(state["holes"][p] + state["board"]) for p in (0, 1)]
    if scores[0] > scores[1]:
        winner = 0
    elif scores[1] > scores[0]:
        winner = 1
    else:
        winner = None
    _finish_hand(state, winner=winner, reason="showdown", scores=scores)


def _finish_hand(state, winner, reason, scores=None):
    _collect(state)
    pot = state["pot"]

    if winner is None:                       # split pot
        half = pot // 2
        state["stacks"][0] += half
        state["stacks"][1] += pot - half
        state["says"] = "Split pot — dead even."
    else:
        state["stacks"][winner] += pot
        if reason == "fold":
            state["says"] = f"{{p{winner}}} takes {pot} — no showdown."
        else:
            state["says"] = f"{{p{winner}}} wins {pot} with {hand_name(scores[winner]).lower()}."

    state["result"] = {
        "winner": winner,
        "reason": reason,
        "pot": pot,
        "names": [hand_name(s) for s in scores] if scores else None,
        "showCards": reason == "showdown",
    }
    state["pot"] = 0
    state["turn"] = None
    state["pending"] = time.time() + (SHOWDOWN_SECONDS if reason == "showdown" else FOLD_SECONDS)


def tick(state, now):
    if state["over"] or not state["result"] or now < state["pending"]:
        return False
    if min(state["stacks"]) <= 0:
        state["over"] = True
        state["winner"] = state["stacks"].index(max(state["stacks"]))
        state["turn"] = None
        state["result"] = None
        state["says"] = "That's the match."
        return True
    state["button"] = 1 - state["button"]
    _start_hand(state)
    return True


# --- what each player is allowed to see ------------------------------------

def view(state, player):
    showdown = bool(state["result"] and state["result"]["showCards"])
    finished = state["over"]
    reveal = showdown or finished

    small, big = _blinds(state)
    yours = state["turn"] == player and not state["result"] and not finished

    win, tie = state.get("odds", [(0, 0), (0, 0)])[player]
    # what they're actually holding right now, once there's enough to name
    made = (hand_name(best_hand(state["holes"][player] + state["board"]))
            if len(state["board"]) >= 3 else None)

    return {
        "winChance": round(win * 100),
        "tieChance": round(tie * 100),
        "exactOdds": len(state["board"]) == 5,
        "madeHand": made,
        "nextIn": max(0, round(state["pending"] - time.time(), 1)) if state["result"] else 0,
        "turn": state["turn"], "over": finished, "winner": state["winner"],
        "you": player,
        "stacks": state["stacks"], "pot": state["pot"], "bets": state["bets"],
        "board": state["board"], "street": state["street"],
        "yourCards": state["holes"][player],
        "theirCards": state["holes"][1 - player] if reveal else None,
        "folded": state["folded"], "allIn": state["allIn"],
        "button": state["button"],
        "hand": state["hand"], "blinds": [small, big],
        "nextLevelIn": HANDS_PER_LEVEL - ((state["hand"] - 1) % HANDS_PER_LEVEL),
        "says": state["says"], "log": state["log"],
        "result": state["result"],
        "startStack": START_STACK,
        # everything the buttons need
        "yourTurn": yours,
        "toCall": to_call(state, player) if yours else 0,
        "minRaiseTo": min_raise_to(state, player) if yours else 0,
        "maxRaiseTo": state["stacks"][player] + state["bets"][player],
        "canCheck": yours and to_call(state, player) == 0,
    }
