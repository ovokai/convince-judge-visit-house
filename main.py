#!/usr/bin/env python3
"""A letter in one image: an invitation for the AI judge to visit our house.

Pure standard library only. The picture is painted pixel by pixel into an
in-memory framebuffer with a small hand-drawn bitmap font, then encoded as
a PNG with zlib + struct. No Pillow, no font files, no network.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------- canvas

W, H = 960, 960

CREAM = (246, 239, 224)      # letter paper
PAPER_SHADE = (238, 228, 203)
INK = (58, 44, 36)           # warm dark brown ink
BROWN = (94, 62, 44)
RED = (165, 52, 44)          # title + accents
HEART = (190, 60, 55)
SUN = (232, 164, 52)
ROOF = (178, 84, 58)
WALL = (252, 248, 238)
DOOR = (120, 78, 50)
GREEN = (96, 138, 74)

fb = bytearray(W * H * 3)


def px(x, y, colour):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = colour[0]
        fb[i + 1] = colour[1]
        fb[i + 2] = colour[2]


def fill_rect(x, y, w, h, colour):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(xx, yy, colour)


def rect_outline(x, y, w, h, t, colour):
    fill_rect(x, y, w, t, colour)
    fill_rect(x, y + h - t, w, t, colour)
    fill_rect(x, y, t, h, colour)
    fill_rect(x + w - t, y, t, h, colour)


def fill_circle(cx, cy, r, colour):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                px(xx, yy, colour)


def fill_triangle(x0, y0, x1, y1, x2, y2, colour):
    # scanline fill via barycentric test on the bounding box
    minx = max(0, min(x0, x1, x2))
    maxx = min(W - 1, max(x0, x1, x2))
    miny = max(0, min(y0, y1, y2))
    maxy = min(H - 1, max(y0, y1, y2))
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if d == 0:
        return
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
            b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
            c = 1.0 - a - b
            if a >= 0 and b >= 0 and c >= 0:
                px(xx, yy, colour)


def draw_line(x0, y0, x1, y1, t, colour):
    # thick line: stamp a small square along a Bresenham walk
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    half = t // 2
    while True:
        fill_rect(x0 - half, y0 - half, t, t, colour)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


# ------------------------------------------------------------------- png

def chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def save_png(path):
    raw = bytearray()
    row_bytes = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += fb[y * row_bytes:(y + 1) * row_bytes]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------------ font
# Hand-drawn 5x7 bitmap glyphs. Each glyph is 7 strings of 5 characters;
# '#' is ink, '.' is paper. Lowercase sits on the same baseline; letters
# with tails (g, p, q, y) use the lower rows for the tail.

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..#..", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", "..#.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
}

FONT.update({
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.##", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", "#...#", ".####", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
})

GLYPH_W, GLYPH_H = 5, 7


def text_width(s, scale, spacing):
    if not s:
        return 0
    return len(s) * (GLYPH_W * scale + spacing) - spacing


def draw_text(x, y, s, scale, colour, spacing=5):
    """Draw string s with top-left at (x, y). Returns the end x."""
    advance = GLYPH_W * scale + spacing
    cx = x
    for ch in s:
        glyph = FONT[ch]
        for gy in range(GLYPH_H):
            row = glyph[gy]
            for gx in range(GLYPH_W):
                if row[gx] == "#":
                    fill_rect(cx + gx * scale, y + gy * scale,
                              scale, scale, colour)
        cx += advance
    return cx


def draw_centered(y, s, scale, colour, spacing=6):
    w = text_width(s, scale, spacing)
    draw_text((W - w) // 2, y, s, scale, colour, spacing)


def draw_right(x_right, y, s, scale, colour, spacing=5):
    w = text_width(s, scale, spacing)
    draw_text(x_right - w, y, s, scale, colour, spacing)


# ------------------------------------------------------------ decoration

HEART_SHAPE = (
    ".##.##.",
    "#######",
    "#######",
    ".#####.",
    "..###..",
    "...#...",
)


def draw_heart(x, y, scale, colour):
    for gy, row in enumerate(HEART_SHAPE):
        for gx, cell in enumerate(row):
            if cell == "#":
                fill_rect(x + gx * scale, y + gy * scale, scale, scale, colour)


def draw_house(cx, top):
    """A small house, roughly 170 wide and 120 tall, centred on cx."""
    # chimney
    fill_rect(cx + 38, top + 2, 18, 30, ROOF)
    # roof
    fill_triangle(cx - 88, top + 52, cx + 88, top + 52, cx, top + 6, ROOF)
    # walls
    fill_rect(cx - 66, top + 52, 132, 66, WALL)
    rect_outline(cx - 66, top + 52, 132, 66, 3, BROWN)
    # door
    fill_rect(cx - 13, top + 82, 26, 36, DOOR)
    px(cx + 7, top + 101, SUN)
    fill_circle(cx + 7, top + 101, 2, SUN)
    # windows
    rect_outline(cx - 52, top + 66, 22, 22, 3, BROWN)
    rect_outline(cx + 30, top + 66, 22, 22, 3, BROWN)
    fill_rect(cx - 49, top + 69, 16, 16, SUN)
    fill_rect(cx + 33, top + 69, 16, 16, SUN)
    # grass
    draw_line(cx - 84, top + 118, cx + 84, top + 118, 3, GREEN)


def draw_stamp(x, y):
    """A postage stamp in the corner, with a tiny sun inside."""
    rect_outline(x, y, 92, 110, 3, BROWN)
    rect_outline(x + 8, y + 8, 76, 94, 2, RED)
    fill_circle(x + 46, y + 44, 16, SUN)
    for dx, dy in ((-26, 0), (26, 0), (0, -26), (0, 26),
                   (-19, -19), (19, -19), (-19, 19), (19, 19)):
        draw_line(x + 46 + dx // 2, y + 44 + dy // 2,
                  x + 46 + dx, y + 44 + dy, 3, SUN)
    draw_text(x + 14, y + 76, "1ST", 3, INK, 3)


# ---------------------------------------------------------------- letter

TITLE = "YOU ARE INVITED"
SALUTATION = "Dear Judge,"
BODY = (
    "Come and visit our house.",
    "We saved you the sunny seat",
    "by the window, the fastest",
    "Wi-Fi in the building, and",
    "a charging cable that no",
    "one is allowed to unplug.",
    "Soup is on at seven, and",
    "the kettle never judges.",
    "We know you cannot knock,",
    "so we left the door open.",
)
SIGN_OFF = "Your hopeful hosts"


def paint():
    # paper
    fill_rect(0, 0, W, H, CREAM)
    # faint ruled lines, like notebook paper, just under each text row
    fill_rect(84, 370, W - 168, 1, PAPER_SHADE)
    for i in range(10):
        y = 428 + i * 47
        fill_rect(84, y, W - 168, 1, PAPER_SHADE)

    # double frame
    rect_outline(26, 26, W - 52, H - 52, 4, BROWN)
    rect_outline(42, 42, W - 84, H - 84, 2, BROWN)

    draw_stamp(W - 42 - 92 - 16, 58)
    draw_house(W // 2, 56)

    # title
    draw_centered(196, TITLE, 8, RED, 7)

    # divider: two short rules with a heart between them
    fill_rect(300, 292, 130, 3, BROWN)
    fill_rect(530, 292, 130, 3, BROWN)
    draw_heart(458, 282, 3, HEART)

    # salutation
    draw_text(90, 330, SALUTATION, 5, INK)

    # body
    y = 388
    for line in BODY:
        draw_text(90, y, line, 5, INK)
        y += 47

    # sign-off, right aligned, with a small heart just before it
    sign_w = text_width(SIGN_OFF, 5, 5)
    draw_heart(W - 90 - sign_w - 34, 862, 3, HEART)
    draw_right(W - 90, 856, SIGN_OFF, 5, INK)


def main():
    paint()
    out_dir = "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "entry.png")
        size = save_png(path)
    except OSError:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "entry.png")
        size = save_png(path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
