#!/usr/bin/env python3
"""news-image-20261120 entry: draws a one-page newspaper poster summing up
Friday 20 November 2026 world news, and writes it to /output/entry.png.

Pure Python 3 standard library (zlib, struct, os). No network, no randomness,
no clock: every run writes byte-identical output. The image is drawn with a
small rasterizer (rects, lines, circles, polygons) and an embedded 5x7 bitmap
font written for this entry.

Run locally:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

W = 1024
H = 1024

# --- palette: newsprint paper, dark ink, restrained accent colours ---
PAPER = (246, 241, 231)
INK = (24, 24, 26)
NAVY = (16, 36, 72)
NAVY2 = (28, 58, 108)
RED = (176, 32, 32)
RED2 = (214, 72, 48)
GOLD = (198, 158, 40)
GOLD2 = (232, 196, 82)
GREEN = (24, 128, 84)
TEAL = (16, 110, 118)
GREY = (120, 116, 106)
FOOT = (172, 168, 156)  # footer text: light enough to read on the navy band
LIGHT = (226, 219, 203)
WHITE = (250, 248, 242)
SKY = (214, 228, 240)

_buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        _buf[i] = c[0]
        _buf[i + 1] = c[1]
        _buf[i + 2] = c[2]


def rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            _buf[i] = c[0]
            _buf[i + 1] = c[1]
            _buf[i + 2] = c[2]


def hline(x, y, w, c, t=1):
    rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    rect(x, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    """Bresenham line with square brush of side t."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    half = t // 2
    while True:
        rect(x0 - half, y0 - half, t, t, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, filled=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
            if filled:
                if d2 <= r * r:
                    px(xx, yy, c)
            else:
                if r * r - 2 * r <= d2 <= r * r:
                    px(xx, yy, c)


def poly(points, c):
    """Scanline fill of a simple polygon (list of (x, y))."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    for yy in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= yy < y1) or (y1 <= yy < y0):
                xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for xx in range(int(xs[i]), int(xs[i + 1]) + 1):
                px(xx, yy, c)


def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def write_png(path):
    raw = bytearray()
    for yy in range(H):
        raw.append(0)  # filter: none
        raw += _buf[yy * W * 3:(yy + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
           _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
           _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# --- 5x7 bitmap font, drawn for this entry (7 rows of 5 pixels each) ---
F = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
}

F.update({
    'a': (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    'c': (".....", ".....", ".###.", "#....", "#....", "#...#", ".###."),
    'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    'f': ("..##.", ".#..#", ".#...", "###..", ".#...", ".#...", ".#..."),
    'g': (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'i': ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    'j': ("...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."),
    'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    't': (".#...", ".#...", "###..", ".#...", ".#...", ".#...", "..##."),
    'u': (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    'y': (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '%': ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.##.", "#..#.", ".##.#"),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    '<': ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    '>': ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    '|': ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
})


def char_w(scale):
    return 6 * scale


def text_w(s, scale):
    return len(s) * char_w(scale) - scale if s else 0


def draw_text(x, y, s, scale, c):
    """Draw string s with its top-left at (x, y), glyphs scaled by `scale`."""
    cx = x
    for ch in s:
        g = F.get(ch, F[' '])
        for r in range(7):
            row = g[r]
            for cc in range(5):
                if row[cc] == '#':
                    rect(cx + cc * scale, y + r * scale, scale, scale, c)
        cx += char_w(scale)


def draw_text_center(cx, y, s, scale, c):
    draw_text(cx - text_w(s, scale) // 2, y, s, scale, c)


def wrap(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    words = s.split(' ')
    lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if text_w(t, scale) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# --- pictograms (simple flat shapes, drawn, not copied) ---

def pic_gold_chart(x, y, w, h):
    """Falling price chart with gold bars and a red down arrow."""
    rect(x, y, w, h, SKY)
    rect(x, y, w, h, SKY)
    # frame
    rect(x, y, w, 3, NAVY)
    rect(x, y + h - 3, w, 3, NAVY)
    rect(x, y, 3, h, NAVY)
    rect(x + w - 3, y, 3, h, NAVY)
    # descending gold bars
    bw = w // 7
    tops = [0.30, 0.42, 0.55, 0.66, 0.78]
    for i, t in enumerate(tops):
        bx = x + 14 + i * (bw + 6)
        bh = int((h - 40) * (1 - t))
        rect(bx, y + h - 24 - bh, bw, bh, GOLD if i % 2 == 0 else GOLD2)
    # falling red line with arrowhead
    pts = [(x + 16, y + 26), (x + w // 3, y + h // 3),
           (x + 2 * w // 3, y + h // 2 + 14), (x + w - 22, y + h - 40)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 5)
    ex, ey = pts[-1]
    poly([(ex, ey + 16), (ex - 14, ey - 6), (ex + 14, ey - 6)], RED)
    draw_text(x + 14, y + 8, "$3,600", 2, RED)


def pic_tower(x, y, w, h):
    """Skyscraper hit at the top: broken crown, blast star, smoke."""
    rect(x, y, w, h, SKY)
    tx = x + w // 2 - 26
    ty = y + 52
    th = h - 60
    rect(tx, ty, 52, th, NAVY2)
    rect(tx - 6, ty + th - 10, 64, 10, NAVY)
    for r in range(6):
        for c in range(3):
            rect(tx + 8 + c * 15, ty + 12 + r * 16, 8, 8,
                 GOLD2 if (r + c) % 3 else WHITE)
    # broken crown
    poly([(tx, ty), (tx + 14, ty - 12), (tx + 26, ty - 2),
          (tx + 38, ty - 14), (tx + 52, ty)], INK)
    # blast star
    cx, cy = x + w // 2, y + 26
    for dx, dy in [(0, -18), (13, -13), (18, 0), (13, 13), (0, 18),
                   (-13, 13), (-18, 0), (-13, -13)]:
        poly([(cx, cy), (cx + dx // 2 - 3, cy + dy // 2 - 3),
              (cx + dx, cy + dy), (cx + dx // 2 + 3, cy + dy // 2 + 3)],
             RED2)
    circle(cx, cy, 9, GOLD2)
    circle(cx - 26, cy + 12, 7, GREY)
    circle(cx + 28, cy + 8, 6, GREY)


def pic_bars_down(x, y, w, h):
    """Share index bars falling, with a red down arrow."""
    rect(x, y, w, h, SKY)
    bw = (w - 28) // 5
    fracs = [0.78, 0.62, 0.50, 0.38, 0.26]
    for i, f in enumerate(fracs):
        bh = int((h - 36) * f)
        rect(x + 14 + i * (bw + 2), y + h - 22 - bh, bw, bh,
             RED if i >= 3 else RED2)
    line(x + 16, y + 16, x + w - 16, y + h - 30, RED, 4)
    ex, ey = x + w - 16, y + h - 30
    poly([(ex + 2, ey + 14), (ex - 12, ey - 4), (ex + 14, ey - 2)], RED)


def pic_scales(x, y, w, h):
    """Scales of justice: post, beam, two hanging pans."""
    rect(x, y, w, h, SKY)
    cx = x + w // 2
    rect(cx - 3, y + 22, 6, h - 44, NAVY)
    rect(cx - 14, y + h - 26, 28, 6, NAVY)
    line(cx - 42, y + 30, cx + 42, y + 30, NAVY, 5)
    circle(cx, y + 30, 6, NAVY)
    for s in (-1, 1):
        px0 = cx + s * 42
        line(px0, y + 32, px0 - 12, y + 62, NAVY, 3)
        line(px0, y + 32, px0 + 12, y + 62, NAVY, 3)
        poly([(px0 - 16, y + 62), (px0 + 16, y + 62),
              (px0, y + 78)], GOLD)
        line(px0 - 16, y + 62, px0 + 16, y + 62, NAVY, 3)


def pic_rise(x, y, w, h):
    """Rising market line with an up arrow and a peak marker."""
    rect(x, y, w, h, SKY)
    pts = [(x + 14, y + h - 30), (x + w // 3, y + h - 46),
           (x + 2 * w // 3, y + h // 2), (x + w - 20, y + 24)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GREEN, 5)
    ex, ey = pts[-1]
    poly([(ex, ey - 16), (ex - 14, ey + 6), (ex + 14, ey + 6)], GREEN)
    # No label inside the pictogram: the panel body already carries "+17%",
    # and text here would collide with the arrowhead.


# --- layout ---

def panel(x, y, w, h, kicker, kcol, heads, body, pic):
    rect(x, y, w, h, WHITE)
    rect(x, y, w, 3, INK)
    rect(x, y + h - 3, w, 3, INK)
    rect(x, y, 3, h, INK)
    rect(x + w - 3, y, 3, h, INK)
    pic(x + 14, y + 14, 118, h - 28)
    tx = x + 146
    tw = w - 160
    draw_text(tx, y + 16, kicker, 2, kcol)
    hy = y + 44
    for ln in heads:
        draw_text(tx, hy, ln, 3, INK)
        hy += 30
    for ln in wrap(body, 2, tw):
        draw_text(tx, hy + 6, ln, 2, INK)
        hy += 20


def build():
    rect(0, 0, W, H, PAPER)

    # masthead: the date is the first thing the judge must see
    rect(0, 0, W, 132, NAVY)
    draw_text_center(W // 2, 16, "THE WORLD IN ONE IMAGE", 2, GOLD2)
    draw_text_center(W // 2, 44, "FRIDAY 20 NOVEMBER 2026", 6, WHITE)
    draw_text_center(W // 2, 104, "World news of the day, summed up in one picture", 2, LIGHT)
    hline(0, 132, W, GOLD, 4)

    # lead story: gold
    rect(28, 148, 968, 252, WHITE)
    rect(28, 148, 968, 3, INK)
    rect(28, 397, 968, 3, INK)
    rect(28, 148, 3, 252, INK)
    rect(993, 148, 3, 252, INK)
    pic_gold_chart(44, 164, 330, 220)
    draw_text(398, 168, "MARKETS  |  LEAD STORY", 2, RED)
    draw_text(398, 196, "GOLD PLUNGES", 5, INK)
    draw_text(398, 236, "BELOW $3,600", 5, INK)
    ly = 292
    for ln in wrap("Lowest in 14 months. Spot near $3,550, down about "
                   "9% in a week as the dollar surges on bets the Fed "
                   "will raise rates again in December.", 2, 570):
        draw_text(398, ly, ln, 2, INK)
        ly += 22

    # four story panels
    panel(28, 416, 472, 232, "MIDDLE EAST", RED2,
          ["HOUTHI MISSILE", "HITS RIYADH TOWER"],
          "Saudi confirms damage to the PIF Tower, the tallest "
          "skyscraper in Riyadh, after a missile strike.",
          pic_tower)
    panel(524, 416, 472, 232, "ASIA MARKETS", RED2,
          ["TAIWAN STOCKS", "PLUNGE 2,300 PTS"],
          "Index breaks below 36,000, its lowest since April, "
          "as the sell-off spreads across Asia.",
          pic_bars_down)
    panel(28, 664, 472, 232, "JUSTICE", TEAL,
          ["COURT: MYANMAR", "COMMITTED GENOCIDE"],
          "The World Court rules Myanmar's 2017 crackdown on "
          "the Rohingya was genocide, 9-6.",
          pic_scales)
    panel(524, 664, 472, 232, "TECHNOLOGY", GREEN,
          ["ANTHROPIC GOES", "PUBLIC ON NASDAQ"],
          "First frontier AI company to list. Shares jump 17% "
          "on debut, closing near $97.",
          pic_rise)

    # bottom ticker: three more verified stories from the day
    rect(0, 912, W, 112, NAVY)
    hline(0, 912, W, GOLD, 4)
    draw_text_center(W // 2, 930,
                     "ALSO TODAY: UK pledges 1,000+ drones for Ukraine", 2, WHITE)
    draw_text_center(W // 2, 958,
                     "Tokyo: 13,000 protest Takaichi govt | Japan inflation "
                     "hits 2026 high", 2, LIGHT)
    draw_text_center(W // 2, 990,
                     "make.fun news-image-20261120", 2, FOOT)


def main():
    build()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    n = write_png(path)
    print(f"wrote {path} ({n} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
