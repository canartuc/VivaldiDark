"""Pixel Valley: a 16-bit title screen in mono-phosphor greens — layered mountains, a pine forest,
fireflies, and a crescent moon reflected in a still lake."""
import math
import random

from PIL import Image, ImageDraw

from tools.pixel import PH, PW, dither_gradient, edge_shade, upscale

# Mono phosphor ramp, darkest to brightest
R = [(5, 10, 6), (11, 36, 18), (19, 80, 42), (31, 138, 62), (51, 255, 102), (184, 255, 204)]
SKY_TOP, SKY_LOW = (4, 9, 5), (9, 26, 13)
MOUNTAINS = [(14, 48, 25), (10, 34, 18), (7, 22, 12)]
FOREST, LAKE_TOP, LAKE_LOW = (4, 12, 7), (8, 26, 14), (3, 8, 5)

MOON = (412, 82, 20)  # centre x, centre y, radius on the 480x270 grid (below the top bar zone)
LAKE = 205
HERO_BOX = ((MOON[0] - MOON[2]) * 8.0, (MOON[1] - MOON[2]) * 8.0, (MOON[0] + MOON[2]) * 8.0 + 8, (LAKE + 18) * 8.0)


def build_small() -> Image.Image:
    rng = random.Random(2)
    img = Image.new("RGB", (PW, PH), SKY_TOP)
    dither_gradient(img, (0, 0, PW, 170), SKY_TOP, SKY_LOW)
    d = ImageDraw.Draw(img)
    for _ in range(220):
        d.point((rng.randrange(PW), rng.randrange(140)), fill=rng.choice([R[3], R[2], R[5]]))
    for i, (base, amp, col) in enumerate(((150, 40, MOUNTAINS[0]), (170, 34, MOUNTAINS[1]), (190, 26, MOUNTAINS[2]))):
        ph = rng.uniform(0, 6)
        for x in range(PW):
            y = int(base - amp * (0.5 + 0.35 * math.sin(x / (40 + i * 13) + ph) + 0.15 * math.sin(x / 9 + ph * 2)))
            d.line((x, y, x, LAKE), fill=col)
            if i == 0 and rng.random() < 0.025:
                d.point((x, y), fill=R[3])  # moonlit ridge glints
    for x in range(0, PW, 5):  # pine forest silhouettes
        h = rng.randint(10, 22)
        for k in range(h):
            w = max(0, (k * 3) // h + (k % 3 == 0))
            d.line((x + 2 - w, LAKE - h + k, x + 2 + w, LAKE - h + k), fill=FOREST)
    dither_gradient(img, (0, LAKE, PW, PH), LAKE_TOP, LAKE_LOW)
    d = ImageDraw.Draw(img)
    for _ in range(26):  # fireflies over the forest
        d.point((rng.randrange(PW), rng.randrange(172, LAKE)), fill=R[4])
    edge_shade(img)
    # hero on top of the shading: crescent moon and its broken reflection
    d = ImageDraw.Draw(img)
    cx, cy, r = MOON
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and (x - cx - 9) ** 2 + (y - cy + 4) ** 2 > (r - 1) ** 2:
                d.point((x, y), fill=R[5] if (x - cx) < -r * 0.45 else R[4])
    for k in range(6):  # stops above the bottom bar zone (row 230)
        y = LAKE + 3 + k * 4
        w = 12 - k * 2
        d.line((cx - 4 - w, y, cx - 4 + w, y), fill=R[5] if k < 2 else R[4] if k < 4 else R[3])
    return img


def build_image() -> Image.Image:
    return upscale(build_small())
