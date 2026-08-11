"""Two Player Arcade - a shared room where two people play many games.

Run with:  python3 server.py

One player picks a game and creates a room (a 4-letter code plus a share
link). Their friend opens the link and they play. When the game ends they
can rematch or pick a different game - the room stays the same, so the
link only ever has to be shared once.

No external packages needed - Python's standard library only.
"""

import json
import mimetypes
import os
import random
import secrets
import socket
import threading
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import owner
from games import GAMES, CATALOG

# Hosting services (like Render) tell us the port via the environment;
# at home we default to 8400.
PORT = int(os.environ.get("PORT", 8400))
DIR = Path(__file__).parent
STATIC = DIR / "static"

# Rooms are forgotten after a day of silence so old games don't pile up.
ROOM_TTL_SECONDS = 24 * 60 * 60

# No 0/O or 1/I/L - too easy to mix up when reading a code aloud.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

# How long a waiting browser is parked before we answer it anyway.
LONG_POLL_SECONDS = 25

LOCK = threading.Condition()
ROOMS = {}  # room code -> room dict


# --- room helpers ---------------------------------------------------------

def new_room_code():
    while True:
        code = "".join(random.choices(CODE_ALPHABET, k=4))
        if code not in ROOMS:
            return code


def bump(room):
    """Mark the room as changed and wake up any waiting browsers."""
    room["version"] += 1
    room["touched"] = time.time()
    LOCK.notify_all()


def prune_rooms():
    cutoff = time.time() - ROOM_TTL_SECONDS
    for code in [c for c, r in ROOMS.items() if r["touched"] < cutoff]:
        del ROOMS[code]


def start_game(room, key):
    """Begin a fresh round of `key` in this room."""
    room["game"] = key
    room["gs"] = GAMES[key].new_state(room["starter"])
    room["phase"] = "playing"
    room["rematch"] = [False, False]
    room["round"] = room.get("round", 0) + 1
    room["began"] = time.time()
    room["moves"] = 0
    room["scores"].setdefault(key, [0, 0])
    owner.record("game_started", room=room["code"], game=key, players=list(room["players"]))


def close_out(room, reason):
    """Note a game that stopped without being played to the end."""
    if room.get("phase") != "playing" or not room.get("gs") or room["gs"].get("over"):
        return
    owner.record("game_ended", room=room["code"], game=room["game"],
                 players=list(room["players"]), reason=reason,
                 seconds=int(time.time() - room.get("began", time.time())),
                 moves=room.get("moves", 0))


def settle(room):
    """Record the result once, the moment a game finishes."""
    gs = room.get("gs")
    if not gs or not gs.get("over") or gs.get("scored"):
        return
    gs["scored"] = True
    winner = gs.get("winner")
    owner.record("game_ended", room=room["code"], game=room["game"],
                 players=list(room["players"]), reason="finished", winner=winner,
                 seconds=int(time.time() - room.get("began", time.time())),
                 moves=room.get("moves", 0))
    if winner in (0, 1):
        room["scores"][room["game"]][winner] += 1
        room["wins"][winner] += 1
    else:
        room["draws"] += 1
    # loser starts the next round (and on a draw, the other player does)
    room["starter"] = 1 - winner if winner in (0, 1) else 1 - room["starter"]


def view_for(room, player):
    """Everything one player's browser needs to draw the screen."""
    key = room.get("game")
    payload = {
        "v": room["version"],
        "code": room["code"],
        "phase": room["phase"],
        "names": list(room["players"]),
        "you": player,
        "game": key,
        "round": room.get("round", 0),
        "rematch": list(room["rematch"]),
        "wins": list(room["wins"]),
        "draws": room["draws"],
        "scores": room["scores"].get(key, [0, 0]) if key else [0, 0],
    }
    if room["phase"] == "playing" and key and player is not None:
        payload["state"] = GAMES[key].view(room["gs"], player)
    return payload


# --- background janitor ---------------------------------------------------

def janitor():
    """Some games have timers (cards flipping back, results revealing).
    This wakes them up and clears out stale rooms."""
    while True:
        time.sleep(0.2)
        now = time.time()
        with LOCK:
            for room in list(ROOMS.values()):
                mod = GAMES.get(room.get("game") or "")
                gs = room.get("gs")
                if mod and gs and hasattr(mod, "tick") and mod.tick(gs, now):
                    settle(room)
                    bump(room)
            if int(now) % 300 == 0:
                prune_rooms()


# --- HTTP -----------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def write_body(self, body):
        """Browsers close long-polling connections all the time; that's not an error."""
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.write_body(body)

    def send_file(self, path, status=200):
        try:
            body = path.read_bytes()
        except OSError:
            self.send_json({"error": "not found"}, 404)
            return
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",):
            ctype += "; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.write_body(body)

    # -- reading requests --

    def body_json(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None

    def authed_room(self, body):
        """Find the room and check this browser really is that player."""
        code = str(body.get("room", "")).strip().upper()
        room = ROOMS.get(code)
        if room is None:
            return None, None
        player = body.get("player")
        token = body.get("token")
        if player in (0, 1) and player < len(room["tokens"]) and secrets.compare_digest(
            str(token or ""), room["tokens"][player]
        ):
            return room, player
        return room, None

    # -- routes --

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/games":
            self.send_json({"games": CATALOG})
        elif path == "/owner":
            self.handle_owner(parse_qs(parsed.query).get("key", [""])[0])
        elif path == "/api/state":
            self.handle_state(parse_qs(parsed.query))
        elif path in ("/", "/index.html"):
            self.send_file(STATIC / "index.html")
        elif path.startswith("/static/"):
            target = (STATIC / path[len("/static/"):]).resolve()
            if STATIC.resolve() in target.parents and target.is_file():
                self.send_file(target)
            else:
                self.send_json({"error": "not found"}, 404)
        else:
            # unknown address - just show the arcade
            self.send_file(STATIC / "index.html")

    def do_POST(self):
        body = self.body_json()
        if body is None:
            self.send_json({"error": "Bad request."}, 400)
            return
        routes = {
            "/api/create": self.handle_create,
            "/api/join": self.handle_join,
            "/api/resume": self.handle_resume,
            "/api/peek": self.handle_peek,
            "/api/move": self.handle_move,
            "/api/pick": self.handle_pick,
            "/api/rematch": self.handle_rematch,
            "/api/menu": self.handle_menu,
            "/api/leave": self.handle_leave,
        }
        handler = routes.get(urlparse(self.path).path)
        if handler is None:
            self.send_json({"error": "not found"}, 404)
            return
        with LOCK:
            handler(body)

    # -- long polling --

    def handle_owner(self, key):
        if not owner.key_is_valid(key):
            # say as little as possible to anyone poking around
            self.send_html("<h1>Not found</h1>", 404)
            return
        with LOCK:
            live = [{"code": r["code"], "players": list(r["players"]),
                     "phase": r["phase"], "game": r.get("game")}
                    for r in ROOMS.values()]
        self.send_html(owner.build_page(live, CATALOG))

    def send_html(self, text, status=200):
        body = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Robots-Tag", "noindex, nofollow")
        self.end_headers()
        self.write_body(body)

    def handle_state(self, query):
        code = query.get("room", [""])[0].strip().upper()
        try:
            since = int(query.get("v", ["0"])[0])
        except ValueError:
            since = 0
        player = None
        try:
            candidate = int(query.get("player", [""])[0])
            player = candidate if candidate in (0, 1) else None
        except (ValueError, IndexError):
            player = None

        with LOCK:
            room = ROOMS.get(code)
            if room is None:
                self.send_json({"error": "room-not-found"}, 404)
                return
            deadline = time.time() + LONG_POLL_SECONDS
            while room["version"] <= since and time.time() < deadline:
                LOCK.wait(timeout=1.0)
                if ROOMS.get(code) is not room:  # room closed while waiting
                    self.send_json({"error": "room-closed"}, 404)
                    return
            room["touched"] = time.time()
            self.send_json(view_for(room, player))

    # -- room lifecycle --

    def handle_create(self, body):
        name = str(body.get("name", "")).strip()[:16]
        key = str(body.get("game", ""))
        if not name:
            self.send_json({"error": "Please enter your name."}, 400)
            return
        if key not in GAMES:
            self.send_json({"error": "Please choose a game."}, 400)
            return
        prune_rooms()
        code = new_room_code()
        token = secrets.token_hex(8)
        ROOMS[code] = {
            "code": code,
            "players": [name],
            "tokens": [token],
            "game": key,
            "gs": None,
            "phase": "waiting",
            "rematch": [False, False],
            "scores": {},
            "wins": [0, 0],
            "draws": 0,
            "round": 0,
            "starter": 0,
            "version": 1,
            "created": time.time(),
            "touched": time.time(),
        }
        owner.record("room_created", room=code, game=key, host=name)
        self.send_json({"room": code, "player": 0, "token": token, "name": name, "game": key})

    def handle_join(self, body):
        name = str(body.get("name", "")).strip()[:16]
        code = str(body.get("room", "")).strip().upper()
        room = ROOMS.get(code)
        if not name:
            self.send_json({"error": "Please enter your name."}, 400)
            return
        if room is None:
            self.send_json({"error": "No room with that code - double-check it with your friend."}, 404)
            return
        if len(room["players"]) >= 2:
            self.send_json({"error": "This room already has two players."}, 409)
            return
        token = secrets.token_hex(8)
        room["players"].append(name)
        room["tokens"].append(token)
        owner.record("partner_joined", room=code, game=room["game"], players=list(room["players"]))
        start_game(room, room["game"])
        bump(room)
        self.send_json({"room": code, "player": 1, "token": token, "name": name, "game": room["game"]})

    def handle_resume(self, body):
        """Come back after a refresh or a dropped connection."""
        room, player = self.authed_room(body)
        if room is None or player is None:
            self.send_json({"error": "gone"}, 404)
            return
        self.send_json({
            "room": room["code"], "player": player,
            "name": room["players"][player], "game": room["game"],
        })

    def handle_peek(self, body):
        """Used by the join screen to show which game is waiting."""
        room = ROOMS.get(str(body.get("room", "")).strip().upper())
        if room is None:
            self.send_json({"error": "No room with that code."}, 404)
            return
        self.send_json({
            "room": room["code"], "game": room["game"],
            "host": room["players"][0], "full": len(room["players"]) >= 2,
        })

    def handle_leave(self, body):
        room, player = self.authed_room(body)
        if room is not None and player is not None:
            close_out(room, "left")
            del ROOMS[room["code"]]
            LOCK.notify_all()
        self.send_json({"ok": True})

    # -- in-game --

    def handle_move(self, body):
        room, player = self.authed_room(body)
        if room is None or player is None:
            self.send_json({"error": "gone"}, 404)
            return
        if room["phase"] != "playing":
            self.send_json({"error": "No game in progress."}, 400)
            return
        mod = GAMES[room["game"]]
        error = mod.move(room["gs"], player, body.get("move") or {})
        if error:
            self.send_json({"error": error, **view_for(room, player)}, 200)
            return
        room["moves"] = room.get("moves", 0) + 1
        settle(room)
        bump(room)
        self.send_json(view_for(room, player))

    def handle_pick(self, body):
        """Either player can choose the next game from the menu."""
        room, player = self.authed_room(body)
        if room is None or player is None:
            self.send_json({"error": "gone"}, 404)
            return
        key = str(body.get("game", ""))
        if key not in GAMES:
            self.send_json({"error": "Unknown game."}, 400)
            return
        if len(room["players"]) < 2:
            room["game"] = key  # still waiting - just change what we'll play
        else:
            close_out(room, "switched")
            start_game(room, key)
        bump(room)
        self.send_json(view_for(room, player))

    def handle_rematch(self, body):
        """Both players have to agree before the board resets."""
        room, player = self.authed_room(body)
        if room is None or player is None:
            self.send_json({"error": "gone"}, 404)
            return
        room["rematch"][player] = True
        if all(room["rematch"]):
            start_game(room, room["game"])
        bump(room)
        self.send_json(view_for(room, player))

    def handle_menu(self, body):
        room, player = self.authed_room(body)
        if room is None or player is None:
            self.send_json({"error": "gone"}, 404)
            return
        close_out(room, "switched")
        room["phase"] = "picking"
        room["rematch"] = [False, False]
        bump(room)
        self.send_json(view_for(room, player))

    def handle_one_request(self):
        try:
            BaseHTTPRequestHandler.handle_one_request(self)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def log_message(self, format, *args):
        pass  # keep the terminal quiet


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "localhost"


if __name__ == "__main__":
    threading.Thread(target=janitor, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    saving, detail = owner.storage_check()
    print(f"Two Player Arcade is running with {len(CATALOG)} games!")
    print(f"  History: {'saved to database' if saving else 'MEMORY ONLY'} — {detail}")
    print(f"  On this computer:  http://localhost:{PORT}")
    print(f"  On another device (same WiFi):  http://{get_lan_ip()}:{PORT}")
    server.serve_forever()
