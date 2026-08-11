# Duo Arcade 🎮

A website for two people. One person picks a game and gets a room code plus a
share link; their friend opens the link and they play, each on their own phone.
When a game finishes they can rematch or pick a different game — **the room stays
the same, so the link only ever has to be shared once**.

## The games (11 so far)

| Game | Difficulty | Roughly |
| --- | --- | --- |
| Tic-Tac-Toe | Easy | 1 min |
| Connect Four | Easy | 5 min |
| Rock Paper Scissors (best of 5) | Easy | 2 min |
| Memory Match | Easy | 5 min |
| Dots & Boxes | Medium | 8 min |
| Gomoku (five in a row) | Medium | 10 min |
| Reversi | Medium | 12 min |
| Blackjack (head to head, best of 5) | Easy | 6 min |
| Battleship | Medium | 12 min |
| Checkers | Hard | 15 min |
| Chinese Chess (Xiangqi) | Hard | 25 min |

Chinese Chess is the full game — cannons that jump to capture, blocked horses,
elephants that can't cross the river, the flying-general rule, and real
checkmate detection.

## Running it on your own computer

```bash
python3 server.py
```

Then open http://localhost:8400. To play across two phones on the same WiFi,
use the second address the server prints when it starts.

There is nothing to install — it uses only Python's standard library.

## Putting it online

The repo is ready for [Render](https://render.com) via `render.yaml`:
create a new **Web Service**, point it at this repo, and it will pick up the
build and start commands automatically. The free plan is enough.

Rooms live in the server's memory and are forgotten after a day of silence, so
there is no database to set up.

## How it fits together

```
server.py          the room engine: codes, invites, turns, rematches
games/             one file per game - the actual rules, server-side
static/index.html  the page
static/app.js      the shell: lobby, invites, scoreboard, polling
static/games/      one file per game - how it's drawn and tapped
```

The server holds the only real copy of every game, so nobody can cheat by
editing the page, and each player is only ever sent what they're allowed to see
(your opponent's Battleship fleet and their face-down Blackjack card never leave
the server). Browsers stay on a long-poll connection, so moves show up on the
other phone straight away rather than a second later.

## Adding a twelfth game

1. Write `games/yourgame.py` with `new_state`, `move`, `view` (and `tick` if it
   needs a timer). The header comment in `games/__init__.py` spells out the
   contract.
2. Import it in `games/__init__.py` and add it to `MODULES`.
3. Write `static/games/yourgame.js` registering a `render(root, state, ctx)`.
4. Add the `<script>` tag to `static/index.html`.

Nothing else needs touching — the card, the lobby, rematches and the scoreboard
all come for free.
