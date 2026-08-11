"""Word Ladders - a race from one word to another, one letter at a time.

Both players get the same pair of words and climb their own ladder. The word
list is `words4.txt` (four-letter words from Webster's Second, public domain).
"""

import random
from collections import deque
from pathlib import Path

KEY = "wordladder"
NAME = "Word Ladders"
EMOJI = "🔤"
TAGLINE = "Turn one word into another, changing a single letter at a time."
RULES = ("You both get the same starting word and the same target. Change one "
         "letter at a time — every step has to be a real word — and race your "
         "opponent to the target. You can undo a step if you paint yourself into "
         "a corner.")
LEVEL = "Medium"
MINUTES = "8 min"

LENGTH = 4
ALPHABET = "abcdefghijklmnopqrstuvwxyz"

WORDS = frozenset((Path(__file__).parent / "words4.txt").read_text().split())

# Puzzles start and end on familiar words, but any word in the list is a legal
# rung — so nobody is stuck hunting for obscure vocabulary.
_FAMILIAR = """
able acid acre aged aide airy ajar akin ally aloe also alto amid apex aqua arch
area arid army atom aunt aura auto avid away axis baby back bail bait bake bald
bale ball balm band bane bang bank bare bark barn base bash bask bass bath bead
beak beam bean bear beat beef been beer beet bell belt bend bent best bike bile
bill bind bird bite blot blow blue blur boar boat body boil bold bolt bomb bond
bone book boom boot bore born boss both bout bowl brag bran brew brim brow buck
bulb bulk bull bump bunk burn bury bush bust busy buzz cage cake calf call calm
came camp cane cape card care cart case cash cask cast cave cell cent chap char
chat chef chew chin chip chop cite city clad clam clan clap claw clay clip clog
club clue coal coat code coil coin cold colt comb come cone cook cool cope copy
cord core cork corn cost coup cove crab cram crew crib crop crow cube cuff cult
curb cure curl cusp cyst dame damp dark darn dart dash data date dawn dead deaf
deal dean dear debt deck deed deem deep deer dent deny desk dial dice diet dime
dine dire dirt dish disk dive dock dole doll dome done doom door dose dote dove
down doze drab drag draw drew drip drop drum dual duck duel dull duly dumb dune
dusk dust duty each earl earn ease east easy echo edge edit envy epic even ever
evil exam exit face fact fade fail fair fake fall fame farm fast fate fawn fear
feat feed feel fell felt fern feud file fill film find fine fire firm fish fist
five flag flap flat flaw flea fled flee flew flip floe flow foam foil fold folk
fond font food fool foot ford fore fork form fort foul four fowl free fret frog
from fuel full fume fund fury fuse fuss gain gait gale game gang gape garb gash
gasp gate gave gaze gear gene gift gild gill gilt girl give glad glee glen glow
glue glum gnat goal goat gold golf gone good gown grab gram gray grew grid grim
grin grip grit grow gulf gull gulp gust hail hair hale half hall halt hand hang
hard hare harm harp hash hate haul have hawk haze head heal heap hear heat heed
heel heir held hell helm help hemp herb herd hero hide high hike hill hilt hint
hire hive hoax hold hole holy home hone hood hoof hook hoop hope horn hose host
hour howl huge hulk hull hunt hurl hurt hush husk hymn icon idea idle idol inch
iron isle itch item jade jail jazz jest join joke jolt jump junk jury just keen
keep kelp kept kick kiln kilt kind king kiss kite knee knit knob knot know lace
lack lady laid lair lake lamb lame lamp land lane lark lash last late lava lawn
lazy lead leaf leak lean leap left lend lens lent less lest life lift like limb
lime limp line link lint lion list live load loaf loan lobe lock lode loft lone
long look loom loop loot lord lore lose loss lost loud love luck lull lump lung
lure lurk lush lute made maid mail main make male mall malt mane many mare mark
mash mask mass mast mate maze mead meal mean meat meek meet meld melt memo mend
menu mere mesh mess mice mild mile milk mill mind mine mint mire miss mist mite
moan moat mock mode mold mole monk mood moon moor more moss most moth move much
mule mull mush must mute myth nail name nape navy near neat neck need nest news
next nice nick nine node none noon norm nose note noun nude numb oath obey odor
oily omen once only onto open oral oval oven over pace pack pact page paid pail
pain pair pale palm pane pang pant park part pass past path pave pawn peak peal
pear peat peck peel peer pelt perk pest pick pier pike pile pill pine pink pint
pipe pity plan play plea plot plow plug plum plus poem poet poke pole poll pond
pony pool poor pope pork port pose post pour pray prey prim prod prop prow pull
pulp pump punk pure push quit quiz race rack raft rage raid rail rain rake ramp
rang rank rant rare rash rate rave read real ream reap rear reed reef reel rein
rely rend rent rest rice rich ride rift rile rime rind ring riot ripe rise risk
rite road roam roar robe rock rode role roll roof rook room root rope rose rosy
rout rude ruin rule rung runt rush rust sack safe sage said sail sake sale salt
same sand sane sang sank save scan scar seal seam sear seat sect seed seek seem
seen self sell send sent shed ship shoe shop shot show shun shut sick side sift
sigh sign silk sill silt sing sink site size skin skip skit slab slam slap slat
sled slew slid slim slip slit slot slow slug slum snap snow snug soak soap soar
sock soda sofa soft soil sold sole solo some song soon soot sore sort soul soup
sour sown span spar spin spit spot spun spur stab stag star stay stem step stew
stir stop stow stub stun such suit sung sunk sure surf swan swap swat sway swim
swum tack tail take tale talk tall tame tank tape task taut teal team tear tell
tend tent term test text than that thaw thee them then they thin this thou thud
thug tide tidy tied tier tile till tilt time tint tiny tire toad toil told toll
tomb tone took tool torn tort toss tour town trap tray tree trim trio trip trot
true tuba tube tuck tuft tune turf turn tusk twig twin type ugly unit upon urge
used vain vale vane vase vast veal veer veil vein vent verb very vest veto vice
view vine void volt vote wade wage wail wait wake walk wall wand wane want ward
ware warm warn warp wart wary wash wasp wave wavy waxy weak wear weed week weep
weld well welt went wept were west what when whim whip whir whom wick wide wife
wild will wilt wind wine wing wink wipe wire wise wish wisp with woke wolf wood
wool word wore work worm worn wrap wren yard yarn yawn year yell yelp yoke your
yule zeal zero zest zinc zone zoom
"""
FAMILIAR = sorted({w for w in _FAMILIAR.split() if w in WORDS})
_FAMILIAR_SET = frozenset(FAMILIAR)

# how far apart the two ends of a puzzle should be
MIN_PAR, MAX_PAR = 4, 6


def neighbours(word, pool=WORDS):
    """Every word in `pool` that is one letter away from this one."""
    out = []
    for i in range(LENGTH):
        for letter in ALPHABET:
            if letter != word[i]:
                candidate = word[:i] + letter + word[i + 1:]
                if candidate in pool:
                    out.append(candidate)
    return out


def shortest_path(start, target, pool=WORDS):
    """The fewest rungs from start to target, or None if there's no route."""
    if start == target:
        return [start]
    came_from = {start: None}
    queue = deque([start])
    while queue:
        word = queue.popleft()
        for nxt in neighbours(word, pool):
            if nxt in came_from:
                continue
            came_from[nxt] = word
            if nxt == target:
                path = [nxt]
                while came_from[path[-1]] is not None:
                    path.append(came_from[path[-1]])
                return path[::-1]
            queue.append(nxt)
    return None


def _familiar_at_distance(start):
    """Familiar words MIN_PAR..MAX_PAR steps from `start` using familiar rungs only.

    Searching the *familiar* subgraph — not the whole dictionary — is what makes
    puzzles fair: it guarantees a route exists made entirely of everyday words.
    Players may still use any word in the full list if they know one.
    """
    seen = {start}
    frontier = [start]
    found = []
    for step in range(1, MAX_PAR + 1):
        nxt = []
        for word in frontier:
            for candidate in neighbours(word, _FAMILIAR_SET):
                if candidate in seen:
                    continue
                seen.add(candidate)
                nxt.append(candidate)
                if step >= MIN_PAR:
                    found.append((candidate, step))
        frontier = nxt
        if not frontier:
            break
    return found


def _make_puzzle():
    for _attempt in range(80):
        start = random.choice(FAMILIAR)
        options = _familiar_at_distance(start)
        if options:
            target, par = random.choice(options)
            return start, target, par
    raise RuntimeError("no solvable word ladder could be built")  # never seen


def new_state(starter):
    start, target, par = _make_puzzle()
    return {"turn": None, "over": False, "winner": None,
            "start": start, "target": target, "par": par,
            "ladders": [[start], [start]], "length": LENGTH}
    # `starter` is deliberately ignored - both players race at the same time.


def move(state, player, mv):
    if state["over"]:
        return "The race is already finished."
    ladder = state["ladders"][player]

    if mv.get("action") == "undo":
        if len(ladder) <= 1:
            return "You're still on the starting word."
        ladder.pop()
        return None

    word = str(mv.get("word", "")).strip().lower()
    if len(word) != LENGTH or not word.isalpha():
        return f"Every rung is a {LENGTH}-letter word."
    if word not in WORDS:
        return f"'{word}' isn't in the word list."
    if word in ladder:
        return "That word is already on your ladder."
    current = ladder[-1]
    changed = sum(1 for a, b in zip(current, word) if a != b)
    if changed != 1:
        return f"Change exactly one letter of '{current}'."

    ladder.append(word)
    if word == state["target"]:
        state.update(over=True, winner=player)
    return None


def view(state, player):
    return {"turn": None, "over": state["over"], "winner": state["winner"],
            "start": state["start"], "target": state["target"], "par": state["par"],
            "length": LENGTH,
            "yourLadder": list(state["ladders"][player]),
            "yourRungs": len(state["ladders"][player]) - 1,
            "theirRungs": len(state["ladders"][1 - player]) - 1,
            # their route stays secret until the race is over
            "theirLadder": list(state["ladders"][1 - player]) if state["over"] else None}
