"""WCAG 2.x contrast helpers."""
import re
from pathlib import Path

from PIL import Image

RGB = tuple[int, int, int]


def parse(color: str) -> RGB:
    color = color.strip()
    if color.startswith("#"):
        return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    nums = re.findall(r"[\d.]+", color)
    return tuple(int(float(n)) for n in nums[:3])


def luminance(rgb: RGB) -> float:
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg: str | RGB, bg: str | RGB) -> float:
    a = luminance(parse(fg) if isinstance(fg, str) else fg)
    b = luminance(parse(bg) if isinstance(bg, str) else bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def worst_bg(png: Path, rect, scale: float, fg: str, text_png: Path | None = None) -> RGB:
    """The background pixel inside `rect` (CSS px) that gives `fg` the lowest contrast.

    With `text_png` (the same frame with the text drawn), only pixels the glyphs actually cover count.
    """
    x, y, w, h = (round(v * scale) for v in rect)
    box = (x, y, x + max(w, 1), y + max(h, 1))
    region = Image.open(png).convert("RGB").crop(box)
    pixels = list(region.get_flattened_data())
    if text_png is not None:
        shown = list(Image.open(text_png).convert("RGB").crop(box).get_flattened_data())
        under = [b for b, t in zip(pixels, shown) if sum(abs(i - j) for i, j in zip(b, t)) > 24]
        pixels = under or pixels
    fg_rgb = parse(fg)
    return min(set(pixels), key=lambda px: ratio(fg_rgb, px))
