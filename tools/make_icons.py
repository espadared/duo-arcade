"""Draw the Duo Arcade app icon at every size the stores ask for.

Writes PNGs with nothing but Python's standard library - no image packages to
install. The mark is two overlapping counters, pink and blue, on the same dark
background the site uses: the two players, side by side.

Run with:  python3 tools/make_icons.py
"""

import math
import struct
import zlib
from pathlib import Path

OUT = Path(__file__).parent.parent / "static" / "icons"

BACKDROP_TOP = (26, 20, 58)      # deep violet, matching the site's header glow
BACKDROP_BOTTOM = (11, 13, 23)   # the page background
PINK = (255, 107, 138)
BLUE = (76, 201, 255)
SUPERSAMPLE = 4                  # draw big, shrink down: cheap anti-aliasing


def _disc(x, y, cx, cy, radius):
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2


def _rounded(x, y, size, radius):
    """Inside the rounded square used for the icon's own corners?"""
    for cx, cy in ((radius, radius), (size - radius, radius),
                   (radius, size - radius), (size - radius, size - radius)):
        if (x < radius or x > size - radius) and (y < radius or y > size - radius):
            if abs(x - cx) <= radius and abs(y - cy) <= radius:
                return _disc(x, y, cx, cy, radius)
    return True


def _blend(base, layer, alpha):
    return tuple(round(b + (l - b) * alpha) for b, l in zip(base, layer))


def draw(size, rounded=True):
    """One icon, as a list of rows of (r, g, b, a)."""
    big = size * SUPERSAMPLE
    radius = big * 0.22
    # the two counters, overlapping slightly in the middle
    r_disc = big * 0.235
    left = (big * 0.385, big * 0.5)
    right = (big * 0.615, big * 0.5)

    rows = []
    for y in range(big):
        row = []
        slide = y / max(1, big - 1)
        backdrop = tuple(round(t + (b - t) * slide)
                         for t, b in zip(BACKDROP_TOP, BACKDROP_BOTTOM))
        for x in range(big):
            if rounded and not _rounded(x, y, big, radius):
                row.append((0, 0, 0, 0))
                continue
            pixel = backdrop
            # blue sits behind, pink in front, so they read as two players
            if _disc(x, y, right[0], right[1], r_disc):
                shade = 0.75 + 0.25 * (1 - (y / big))
                pixel = _blend(pixel, tuple(round(c * shade) for c in BLUE), 1.0)
            if _disc(x, y, left[0], left[1], r_disc):
                shade = 0.75 + 0.25 * (1 - (y / big))
                pixel = _blend(pixel, tuple(round(c * shade) for c in PINK), 1.0)
            row.append(pixel + (255,))
        rows.append(row)

    # shrink back down, averaging each block - this is what smooths the edges
    out = []
    for y in range(size):
        row = []
        for x in range(size):
            r = g = b = a = 0
            for dy in range(SUPERSAMPLE):
                for dx in range(SUPERSAMPLE):
                    pr, pg, pb, pa = rows[y * SUPERSAMPLE + dy][x * SUPERSAMPLE + dx]
                    r += pr * pa; g += pg * pa; b += pb * pa; a += pa
            if a:
                row.append((round(r / a), round(g / a), round(b / a),
                            round(a / (SUPERSAMPLE ** 2))))
            else:
                row.append((0, 0, 0, 0))
        out.append(row)
    return out


def write_png(path, pixels):
    height, width = len(pixels), len(pixels[0])
    raw = b"".join(
        b"\x00" + b"".join(struct.pack("BBBB", *px) for px in row) for row in pixels)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    path.write_bytes(png)


# name -> (pixels, square corners or rounded)
WANTED = {
    "icon-192.png": (192, True),
    "icon-512.png": (512, True),
    "icon-maskable-512.png": (512, False),   # Android crops this to its own shape
    "apple-touch-icon.png": (180, False),    # iOS rounds it itself
    "icon-1024.png": (1024, False),          # what the App Store listing needs
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (size, rounded) in WANTED.items():
        write_png(OUT / name, draw(size, rounded))
        print(f"  wrote {name} ({size}x{size})")
    print(f"icons are in {OUT}")
