"""The private owner dashboard - what people played, and where they dropped off.

Reached at /owner?key=<OWNER_KEY>. Without an OWNER_KEY set, the page is off
entirely when running on a host, and uses the key "localtest" on your own
computer.

Events are kept in memory so the page works with no setup at all, and are also
written to Supabase when SUPABASE_URL and SUPABASE_KEY are set, which is what
makes the history survive the server going to sleep.

Only what players type is recorded - the name they chose, the game, and the
result. No IP addresses, no device details, nothing that identifies a person
beyond the name they picked themselves.
"""

import html
import json
import os
import secrets
import threading
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
TABLE = "arcade_events"

# On a host the dashboard stays switched off until a real OWNER_KEY is set;
# "localtest" only ever works on your own machine.
OWNER_KEY = os.environ.get("OWNER_KEY", "" if os.environ.get("RENDER") else "localtest")

SG_TIME = ZoneInfo("Asia/Singapore")
EVENT_CAP = 3000

EVENTS = []  # newest first
_LOCK = threading.Lock()


def key_is_valid(supplied):
    return bool(OWNER_KEY) and secrets.compare_digest(str(supplied or ""), OWNER_KEY)


# --- recording -------------------------------------------------------------

def record(kind, **fields):
    """Note something that happened. Never raises - analytics must not break play."""
    event = {"kind": kind, "created_at": datetime.now(timezone.utc).isoformat()}
    event.update({k: v for k, v in fields.items() if v is not None})
    with _LOCK:
        EVENTS.insert(0, event)
        del EVENTS[EVENT_CAP:]
    if SUPABASE_URL and SUPABASE_KEY:
        threading.Thread(target=_push, args=(event,), daemon=True).start()


def _supabase(path, data=None):
    request = urllib.request.Request(
        SUPABASE_URL + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": "Bearer " + SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
    return json.loads(body) if body else None


def _push(event):
    try:
        _supabase(f"/rest/v1/{TABLE}", event)
    except Exception:
        pass  # the in-memory copy still has it


def _load():
    """Every event we can see, plus where it came from."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            rows = _supabase(f"/rest/v1/{TABLE}?select=*&order=created_at.desc&limit=3000")
            return rows or [], "permanent"
        except Exception:
            with _LOCK:
                return list(EVENTS), "memory-fallback"
    with _LOCK:
        return list(EVENTS), "memory-only"


# --- presentation ----------------------------------------------------------

def _esc(value):
    return html.escape(str(value))


def _when(iso):
    try:
        moment = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(SG_TIME).strftime("%-d %b, %-I:%M%p").lower()
    except Exception:
        return str(iso)


def _ago(iso):
    try:
        moment = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        seconds = (datetime.now(timezone.utc) - moment).total_seconds()
    except Exception:
        return ""
    for limit, size, label in ((60, 1, "s"), (3600, 60, "m"), (86400, 3600, "h")):
        if seconds < limit:
            return f"{int(seconds // size)}{label} ago"
    return f"{int(seconds // 86400)}d ago"


def _clock(seconds):
    if seconds is None:
        return "—"
    seconds = int(seconds)
    return f"{seconds // 60}m {seconds % 60}s" if seconds >= 60 else f"{seconds}s"


def _pct(part, whole):
    return 0 if not whole else round(100 * part / whole)


def _bar(label, value, total, colour, note=""):
    return (
        f'<div class="bar"><div class="bar-top"><span>{_esc(label)}</span>'
        f'<span class="bar-val">{value}{_esc(note)}</span></div>'
        f'<div class="track"><div class="fill" style="width:{_pct(value, total)}%;'
        f'background:{colour}"></div></div></div>')


def build_page(live_rooms, catalog):
    events, source = _load()
    names = {game["key"]: game["name"] for game in catalog}
    emoji = {game["key"]: game["emoji"] for game in catalog}

    created = [e for e in events if e.get("kind") == "room_created"]
    joined = [e for e in events if e.get("kind") == "partner_joined"]
    started = [e for e in events if e.get("kind") == "game_started"]
    ended = [e for e in events if e.get("kind") == "game_ended"]
    finished = [e for e in ended if e.get("reason") == "finished"]

    # per game: how often chosen, how often played to the end
    per_game = defaultdict(lambda: {"started": 0, "finished": 0, "quit": 0, "seconds": []})
    for event in started:
        per_game[event.get("game", "?")]["started"] += 1
    for event in ended:
        row = per_game[event.get("game", "?")]
        if event.get("reason") == "finished":
            row["finished"] += 1
            if event.get("seconds") is not None:  # a 0-second game still counts
                row["seconds"].append(event["seconds"])
        else:
            row["quit"] += 1

    # who has been playing
    people = defaultdict(lambda: {"games": 0, "last": ""})
    for event in events:
        for person in event.get("players") or ([event["host"]] if event.get("host") else []):
            entry = people[person]
            if event.get("kind") == "game_ended":
                entry["games"] += 1
            if not entry["last"]:
                entry["last"] = event.get("created_at", "")

    out = [f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Duo Arcade — Owner</title>
<link rel="stylesheet" href="/static/style.css">
<style>
.wrap {{ max-width: 820px; }}
h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
h2 {{ font-size: 1rem; margin: 28px 0 10px; color: var(--muted);
     text-transform: uppercase; letter-spacing: .08em; }}
.tiles {{ display: grid; gap: 10px; grid-template-columns: repeat(2, 1fr); }}
@media (min-width: 560px) {{ .tiles {{ grid-template-columns: repeat(4, 1fr); }} }}
.tile {{ background: var(--panel); border: 1px solid var(--line);
        border-radius: 14px; padding: 14px; }}
.tile .n {{ font-size: 1.8rem; font-weight: 700; line-height: 1.1; }}
.tile .l {{ font-size: .76rem; color: var(--muted); }}
.bar {{ margin-bottom: 10px; }}
.bar-top {{ display: flex; justify-content: space-between; font-size: .86rem;
           margin-bottom: 4px; }}
.bar-val {{ color: var(--muted); }}
.track {{ height: 8px; background: rgba(255,255,255,.07); border-radius: 999px;
         overflow: hidden; }}
.fill {{ height: 100%; border-radius: 999px; min-width: 2px; }}
table {{ width: 100%; border-collapse: collapse; font-size: .86rem; }}
th {{ text-align: left; color: var(--muted); font-weight: 500; padding: 6px 8px;
     border-bottom: 1px solid var(--line); font-size: .76rem;
     text-transform: uppercase; letter-spacing: .05em; }}
td {{ padding: 8px; border-bottom: 1px solid var(--line); vertical-align: middle; }}
td.num, th.num {{ text-align: right; }}
.feed div {{ padding: 8px 10px; border-bottom: 1px solid var(--line);
            font-size: .86rem; display: flex; justify-content: space-between; gap: 10px; }}
.feed .t {{ color: var(--muted); font-size: .78rem; white-space: nowrap; }}
.note {{ background: var(--panel); border: 1px solid var(--line); border-left: 3px solid var(--warn);
        border-radius: 10px; padding: 12px 14px; font-size: .84rem; color: var(--muted); }}
.empty {{ color: var(--muted); font-size: .88rem; padding: 10px 0; }}
</style></head><body><div class="wrap">
<h1>Duo Arcade — owner dashboard 🔑</h1>
<p class="muted small">Private. Times are Singapore time.</p>"""]

    if source == "memory-only":
        out.append('<div class="note" style="margin-top:14px">⚠️ <b>Nothing is being saved permanently yet.</b> '
                   'This page is showing only what has happened since the server last woke up — on the free plan '
                   'that resets whenever the site sits idle for about 15 minutes. Set up a database to keep '
                   'the history (see the README).</div>')
    elif source == "memory-fallback":
        out.append('<div class="note" style="margin-top:14px">⚠️ Could not reach the database just now — '
                   'showing recent activity from memory instead.</div>')

    # --- headline numbers
    out.append('<h2>At a glance</h2><div class="tiles">')
    for number, label in ((len(created), "rooms created"),
                          (len(joined), "friends joined"),
                          (len(started), "games played"),
                          (len(finished), "played to the end")):
        out.append(f'<div class="tile"><div class="n">{number}</div><div class="l">{label}</div></div>')
    out.append("</div>")

    # --- the funnel: this is the number worth acting on
    out.append("<h2>Where people drop off</h2>")
    if not created:
        out.append('<p class="empty">No rooms created yet.</p>')
    else:
        out.append(_bar("Created a room", len(created), len(created), "var(--accent)"))
        out.append(_bar("Friend actually joined", len(joined), len(created), "var(--mint)",
                        f" ({_pct(len(joined), len(created))}%)"))
        out.append(_bar("Finished a game", len(finished), len(created), "var(--accent-2)",
                        f" ({_pct(len(finished), len(created))}%)"))
        lonely = len(created) - len(joined)
        if lonely > 0:
            out.append(f'<p class="empty">{lonely} room{"s" if lonely != 1 else ""} never got a second '
                       f'player — that is the biggest thing to improve if the number stays high.</p>')

    # --- live
    out.append(f"<h2>Live right now ({len(live_rooms)})</h2>")
    if not live_rooms:
        out.append('<p class="empty">Nobody is playing at the moment.</p>')
    else:
        out.append('<table><tr><th>Room</th><th>Players</th><th>Game</th><th>Doing</th></tr>')
        for room in live_rooms:
            players = " &amp; ".join(_esc(p) for p in room["players"]) or "—"
            state = {"waiting": "waiting for a friend", "picking": "choosing a game",
                     "playing": "playing"}.get(room["phase"], room["phase"])
            out.append(f'<tr><td><b>{_esc(room["code"])}</b></td><td>{players}</td>'
                       f'<td>{_esc(names.get(room["game"], room["game"] or "—"))}</td>'
                       f'<td class="muted">{_esc(state)}</td></tr>')
        out.append("</table>")

    # --- games
    out.append("<h2>Which games they choose</h2>")
    if not per_game:
        out.append('<p class="empty">No games played yet.</p>')
    else:
        ranked = sorted(per_game.items(), key=lambda kv: -kv[1]["started"])
        out.append('<table><tr><th>Game</th><th class="num">Played</th><th class="num">Finished</th>'
                   '<th class="num">Quit</th><th class="num">Typical length</th></tr>')
        for key, row in ranked:
            times = row["seconds"]
            typical = _clock(sorted(times)[len(times) // 2]) if times else _clock(None)
            out.append(
                f'<tr><td>{emoji.get(key, "🎮")} {_esc(names.get(key, key))}</td>'
                f'<td class="num">{row["started"]}</td>'
                f'<td class="num">{row["finished"]}</td>'
                f'<td class="num">{row["quit"] or ""}</td>'
                f'<td class="num muted">{typical}</td></tr>')
        out.append("</table>")
        never = [k for k in names if k not in per_game]
        if never:
            out.append('<p class="empty">Never picked once: '
                       + ", ".join(_esc(names[k]) for k in never) + ".</p>")

    # --- people
    out.append(f"<h2>Who has been playing ({len(people)})</h2>")
    if not people:
        out.append('<p class="empty">No players yet.</p>')
    else:
        ranked = sorted(people.items(), key=lambda kv: (-kv[1]["games"], kv[0]))[:40]
        out.append('<table><tr><th>Name</th><th class="num">Games</th><th class="num">Last seen</th></tr>')
        for person, row in ranked:
            out.append(f'<tr><td>{_esc(person)}</td><td class="num">{row["games"]}</td>'
                       f'<td class="num muted">{_esc(_ago(row["last"]))}</td></tr>')
        out.append("</table>")

    # --- feed
    out.append("<h2>Recent activity</h2>")
    if not events:
        out.append('<p class="empty">Nothing yet. Share the link and check back!</p>')
    else:
        out.append('<div class="feed">')
        for event in events[:60]:
            out.append(f'<div><span>{_story(event, names)}</span>'
                       f'<span class="t">{_esc(_when(event.get("created_at")))}</span></div>')
        out.append("</div>")

    out.append("</div></body></html>")
    return "".join(out)


def _story(event, names):
    """One line of plain English for the activity feed."""
    kind = event.get("kind")
    game = _esc(names.get(event.get("game"), event.get("game") or "a game"))
    players = " &amp; ".join(_esc(p) for p in (event.get("players") or []))
    room = _esc(event.get("room", ""))

    if kind == "room_created":
        return f'<b>{_esc(event.get("host", "someone"))}</b> opened room {room} for {game}'
    if kind == "partner_joined":
        return f'{players} paired up in room {room}'
    if kind == "game_started":
        return f'{players or "two players"} started {game}'
    if kind == "game_ended":
        reason = event.get("reason")
        who = event.get("players") or []
        winner = event.get("winner")
        if reason == "finished":
            if winner is None or winner >= len(who):
                result = f"{game} ended in a draw"
            else:
                result = f'<b>{_esc(who[winner])}</b> won {game}'
            return f'{result} · {_clock(event.get("seconds"))}, {event.get("moves", 0)} moves'
        wording = "switched away from" if reason == "switched" else "abandoned"
        return f'{players or "someone"} {wording} {game} after {_clock(event.get("seconds"))}'
    return _esc(kind)
