"""Play every game with random legal moves and make sure nothing explodes.

Run with:  python3 test_games.py
Every line should start with OK - a STUCK line means a game can reach a
position where nobody has a legal move and it never finishes.
"""
import random, sys, time, json
from games import GAMES

def candidates(key, state, p):
    """A pile of plausible moves; we just try them until one is accepted."""
    if key == "tictactoe":
        return [{"cell": i} for i in range(9)]
    if key == "connect4":
        return [{"col": i} for i in range(7)]
    if key == "gomoku":
        return [{"cell": random.randrange(225)} for _ in range(40)]
    if key == "reversi":
        return [{"cell": i} for i in range(64)]
    if key == "memory":
        return [{"cell": i} for i in range(24)]
    if key == "dots":
        return [{"t": t, "r": r, "c": c} for t in "hv" for r in range(6) for c in range(6)]
    if key == "rps":
        return [{"pick": random.choice(["rock", "paper", "scissors"])}]
    if key == "blackjack":
        return [{"action": random.choice(["hit", "stand"])}]
    if key == "battleship":
        if state["phase"] == "place":
            return [{"action": "random"}]
        return [{"action": "fire", "cell": i} for i in random.sample(range(100), 100)]
    if key == "bridges":
        return [{"cell": i} for i in random.sample(range(81), 81)]
    if key == "crosswires":
        gaps = list(GAMES[key].WIRES[p])
        random.shuffle(gaps)
        return [{"r": r, "c": c} for r, c in gaps]
    if key == "wordladder":
        # walk the real shortest route - this also proves every puzzle is solvable
        mod = GAMES[key]
        route = mod.shortest_path(state["ladders"][p][-1], state["target"])
        assert route, "a word ladder puzzle was generated with no solution"
        return [{"word": route[1]}] if len(route) > 1 else []
    if key in ("checkers", "xiangqi"):
        mod = GAMES[key]
        if key == "xiangqi":
            moves = state["legal"]
            return [{"from": int(f), "to": t} for f, ts in moves.items() for t in ts]
        moves = mod.legal_moves(state, p)
        return [{"from": f, "to": m["to"]} for f, ms in moves.items() for m in ms]
    return []

random.seed(7)
for key, mod in GAMES.items():
    for trial in range(6):
        state = mod.new_state(trial % 2)
        steps = 0
        t0 = time.time()
        while not state["over"] and steps < 4000:
            steps += 1
            if hasattr(mod, "tick"):
                mod.tick(state, time.time() + 999)
                if state["over"]:
                    break
            turn = state.get("turn")
            actors = [0, 1] if turn is None else [turn]
            moved = False
            for p in actors:
                opts = candidates(key, state, p)
                random.shuffle(opts)
                for mv in opts:
                    if mod.move(state, p, mv) is None:
                        moved = True
                        break
                if moved and turn is not None:
                    break
            if not moved:
                print(f"  !! {key}: stuck after {steps} moves, turn={turn}")
                break
            for p in (0, 1):
                json.dumps(mod.view(state, p))  # must be JSON-safe
        flag = "OK " if state["over"] else "STUCK"
        print(f"{flag} {key:11s} trial{trial} steps={steps:4d} winner={state.get('winner')} "
              f"{time.time()-t0:.2f}s")
