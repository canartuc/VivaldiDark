"""8-Bit Cosmos: a dithered green nebula, a banded ringed planet (the ring passes behind and in front),
a starfield and a tiny satellite, in the canartuc.com terminal palette."""
import math
import random

from PIL import Image, ImageDraw

from tools.pixel import BAYER, PH, PW, edge_shade, upscale

C = {"bg": (8, 12, 9), "green": (0, 255, 65), "green2": (0, 190, 50), "green3": (0, 110, 32), "green4": (0, 60, 20),
     "cyan": (0, 170, 255), "cyan2": (0, 100, 160), "mint": (214, 232, 214), "sage": (107, 138, 107),
     "grey": (123, 132, 149), "text": (194, 199, 208)}
NEBULA = [(0, 36, 20), (0, 62, 38), (0, 88, 64)]

PLANET = (418, 150, 32)  # centre x, centre y, radius on the 480x270 grid
RING = (56, 10)          # ring half-width, half-height
HERO_BOX = ((PLANET[0] - PLANET[2]) * 8.0, (PLANET[1] - PLANET[2]) * 8.0, (PLANET[0] + PLANET[2]) * 8.0 + 8, (PLANET[1] + PLANET[2]) * 8.0 + 8)


def build_small() -> Image.Image:
    rng = random.Random(3)
    img = Image.new("RGB", (PW, PH), C["bg"])
    d = ImageDraw.Draw(img)
    for _ in range(420):
        d.point((rng.randrange(PW), rng.randrange(PH)), fill=rng.choice([C["sage"], C["grey"], C["mint"], C["green3"]]))
    px = img.load()
    for y in range(PH):  # nebula: three dithered densities, a soft cloud drifting toward the planet
        for x in range(PW):
            v = (math.exp(-((x - 300) ** 2 / 14000 + (y - 120) ** 2 / 3200))
                 + 0.7 * math.exp(-((x - 200) ** 2 / 9000 + (y - 175) ** 2 / 2200)))
            if v * 18 > BAYER[y % 4][x % 4] + 3:
                px[x, y] = NEBULA[int(min(2.99, v * 3.2))]
    edge_shade(img)
    # hero on top of the shading: ring (back half), planet, ring (front half), satellite
    d = ImageDraw.Draw(img)
    cx, cy, r = PLANET
    rw, rh = RING
    d.arc((cx - rw, cy - rh, cx + rw, cy + rh), 180, 360, fill=C["cyan2"])
    px = img.load()
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= r * r:
                light = (-dx - dy) / (2 * r) + 0.5
                base = C["green2"] if (y // 6) % 2 else C["green3"]
                px[x, y] = base if light * 16 > BAYER[y % 4][x % 4] else C["green4"]
    d = ImageDraw.Draw(img)
    d.arc((cx - rw, cy - rh, cx + rw, cy + rh), 0, 180, fill=C["cyan"])
    d.arc((cx - rw + 7, cy - rh + 3, cx + rw - 7, cy + rh - 3), 0, 180, fill=C["cyan2"])
    sx, sy = 352, 92
    d.rectangle((sx, sy, sx + 4, sy + 3), fill=C["text"])
    d.rectangle((sx - 6, sy + 1, sx - 2, sy + 2), fill=C["cyan"])
    d.rectangle((sx + 6, sy + 1, sx + 10, sy + 2), fill=C["cyan"])
    return img


def build_image() -> Image.Image:
    return upscale(build_small())
