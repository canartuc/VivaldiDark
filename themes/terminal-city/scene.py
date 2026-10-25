"""Terminal City: a pixel skyline at night with Matrix-style code rain, a pixel moon and a floating
terminal window (abstract prompt lines and a static cursor block), in the canartuc.com terminal palette."""
import random

from PIL import Image, ImageDraw

from tools.pixel import PH, PW, dither_gradient, edge_shade, upscale

C = {"bg": (8, 12, 9), "bg2": (12, 22, 15), "panel": (26, 31, 43), "green": (0, 255, 65), "green2": (0, 190, 50),
     "green3": (0, 110, 32), "green4": (0, 60, 20), "cyan": (0, 170, 255), "mint": (214, 232, 214),
     "sage": (107, 138, 107), "text": (194, 199, 208)}

MOON = (404, 66, 24)  # x, y, size on the 480x270 grid (below the top bar zone)
PANEL = (384, 120, 454, 170)
HERO_BOX = (PANEL[0] * 8.0, MOON[1] * 8.0, PANEL[2] * 8.0 + 8, PANEL[3] * 8.0 + 8)


def build_small() -> Image.Image:
    rng = random.Random(1)
    img = Image.new("RGB", (PW, PH), C["bg"])
    dither_gradient(img, (0, 0, PW, 205), C["bg"], C["bg2"])
    d = ImageDraw.Draw(img)
    for _ in range(140):
        d.point((rng.randrange(PW), rng.randrange(150)), fill=rng.choice([C["sage"], C["green3"], C["mint"]]))
    mx, my, ms = MOON
    # code rain: columns of 2x3 glyph blocks, bright head, fading tail (abstract, never real characters)
    for x in range(4, PW, 9):
        if rng.random() < 0.55:
            y0, n = rng.randrange(-40, 120), rng.randrange(6, 18)
            for k in range(n):
                col = C["mint"] if k == n - 1 else (C["green"] if k > n - 4 else C["green3"] if k > n - 9 else C["green4"])
                gy = y0 + k * 5
                in_panel = PANEL[0] - 3 <= x <= PANEL[2] + 3 and PANEL[1] - 3 <= gy <= PANEL[3] + 3
                in_moon = mx - 4 <= x <= mx + ms + 4 and my - 4 <= gy <= my + ms + 4
                if 0 <= gy < 230 and rng.random() < 0.85 and not (in_panel or in_moon):
                    d.rectangle((x, gy, x + 1, gy + 2), fill=col)
    # skyline: two layers, lit windows in green and cyan
    for layer, (lo, hi, col, lit) in enumerate(((150, 200, (14, 26, 18), 0.10), (175, 232, (9, 16, 11), 0.22))):
        x = -5
        while x < PW:
            bw, top = rng.randint(14, 34), rng.randint(lo, hi) - layer * 10
            d.rectangle((x, top, x + bw, PH), fill=col)
            if rng.random() < 0.3:
                d.rectangle((x + bw // 2, top - rng.randint(4, 12), x + bw // 2, top), fill=col)
            for wy in range(top + 3, PH - 4, 4):
                for wx in range(x + 2, x + bw - 2, 3):
                    if rng.random() < lit:
                        d.point((wx, wy), fill=rng.choice([C["green"], C["green2"], C["cyan"]]))
            x += bw + rng.randint(0, 2)
    edge_shade(img)
    # hero elements go on top of the shading: they sit below the bar zones, so the tab text is unaffected
    d = ImageDraw.Draw(img)
    d.ellipse((mx, my, mx + ms, my + ms), fill=C["mint"])
    for cx, cy in ((mx + 8, my + 8), (mx + 15, my + 14), (mx + 7, my + 15), (mx + 16, my + 7)):
        d.point((cx, cy), fill=C["sage"])
    # the terminal window: title bar dots, abstract prompt lines, static cursor
    x0, y0, x1, y1 = PANEL
    d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), fill=(10, 30, 16))  # soft glow ring
    d.rectangle((x0, y0, x1, y1), fill=C["panel"], outline=C["green2"])
    for i, col in enumerate((C["green"], C["cyan"], C["sage"])):
        d.point((x0 + 4 + i * 3, y0 + 3), fill=col)
    for i, (w, col) in enumerate(((22, C["green"]), (40, C["text"]), (30, C["text"]), (16, C["green"]))):
        d.rectangle((x0 + 5, y0 + 9 + i * 9, x0 + 5 + w, y0 + 10 + i * 9), fill=col)
    d.rectangle((x0 + 24, y0 + 36, x0 + 27, y0 + 41), fill=C["green"])  # cursor block
    return img


def build_image() -> Image.Image:
    return upscale(build_small())
