"""Terminal City: a pixel skyline at night with Matrix-style code rain and a pixel moon,
in the canartuc.com terminal palette."""
import random

from PIL import Image, ImageDraw

from tools.pixel import PH, PW, dither_gradient, edge_shade, upscale

C = {"bg": (8, 12, 9), "bg2": (12, 22, 15), "green": (0, 255, 65), "green2": (0, 190, 50),
     "green3": (0, 110, 32), "green4": (0, 60, 20), "cyan": (0, 170, 255), "mint": (214, 232, 214),
     "sage": (107, 138, 107), "text": (194, 199, 208)}

MOON = (404, 66, 24)  # x, y, size on the 480x270 grid (below the top bar zone)
HERO_BOX = (MOON[0] * 8.0, MOON[1] * 8.0, (MOON[0] + MOON[2]) * 8.0 + 8, (MOON[1] + MOON[2]) * 8.0 + 8)


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
                in_moon = mx - 4 <= x <= mx + ms + 4 and my - 4 <= gy <= my + ms + 4
                if 0 <= gy < 230 and rng.random() < 0.85 and not in_moon:
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
    # the moon goes on top of the shading: it sits below the bar zones, so the tab text is unaffected
    d = ImageDraw.Draw(img)
    d.ellipse((mx, my, mx + ms, my + ms), fill=C["mint"])
    for cx, cy in ((mx + 8, my + 8), (mx + 15, my + 14), (mx + 7, my + 15), (mx + 16, my + 7)):
        d.point((cx, cy), fill=C["sage"])
    return img


def build_image() -> Image.Image:
    return upscale(build_small())
