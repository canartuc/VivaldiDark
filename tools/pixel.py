"""Pixel-art helpers: a 480x270 canvas, Bayer dithering, dithered bar zones, x8 upscale with scanlines."""
from PIL import Image

PW, PH, SCALE = 480, 270, 8
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
SHADE = (6, 9, 7)
# Bar zones on the pixel grid (wave-1 zones / 8): full strength inside, dithered fade beyond.
TOP_FULL, TOP_END = 53, 100
LEFT_FULL, LEFT_END = 119, 290
BOTTOM_FULL, BOTTOM_START = 230, 200


def dither_gradient(img: Image.Image, box, top, bottom, vertical: bool = True) -> None:
    """Ordered (Bayer) dithering between two colours: the classic 8/16-bit gradient."""
    x0, y0, x1, y1 = box
    px = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            t = (y - y0) / max(1, y1 - y0 - 1) if vertical else (x - x0) / max(1, x1 - x0 - 1)
            px[x, y] = bottom if t * 16 > BAYER[y % 4][x % 4] + 0.5 else top


def _zone(x: int, y: int) -> float:
    """1.0 where a bar can sit, smoothly falling to 0 beyond it."""
    def fall(d, full, end):
        if d < full:
            return 1.0
        t = min(1.0, (d - full) / (end - full))
        return 1 - t * t * (3 - 2 * t)
    top = fall(y, TOP_FULL, TOP_END)
    left = fall(x, LEFT_FULL, LEFT_END)
    bottom = 1.0 if y >= BOTTOM_FULL else max(0.0, (y - BOTTOM_START) / (BOTTOM_FULL - BOTTOM_START)) ** 2
    return max(top, left, bottom)


LEVELS = 8  # shade quantisation for the dithered fade


def edge_shade(img: Image.Image, strength: float = 0.9) -> None:
    """Sink the art into shadow under the bars. Beyond them the shade fades out in LEVELS steps, each
    pixel dithered (Bayer) between the two nearest steps, so the fade is smooth and shows no edge."""
    px = img.load()
    for y in range(PH):
        for x in range(PW):
            z = _zone(x, y)
            if z <= 0:
                continue
            if z < 1.0:
                q = z * LEVELS
                lo = int(q)
                z = (lo + (1 if (q - lo) * 16 > BAYER[y % 4][x % 4] + 0.5 else 0)) / LEVELS
            a = strength * z
            r, g, b = px[x, y]
            px[x, y] = (round(r * (1 - a) + SHADE[0] * a), round(g * (1 - a) + SHADE[1] * a), round(b * (1 - a) + SHADE[2] * a))


def upscale(img: Image.Image) -> Image.Image:
    """x8 nearest-neighbour to 3840x2160, then a faint CRT scanline on the last row of every pixel."""
    big = img.convert("RGB").resize((PW * SCALE, PH * SCALE), Image.NEAREST)
    px = big.load()
    for y in range(SCALE - 1, PH * SCALE, SCALE):
        for x in range(PW * SCALE):
            r, g, b = px[x, y]
            px[x, y] = (int(r * 0.78), int(g * 0.78), int(b * 0.78))
    return big
