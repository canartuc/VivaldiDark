"""VivaldiDark toolbar icons: lint, manifest and build (from tools/icon_glyphs.py).

    uv run python -m tools.icons      # writes icons/*.svg, icons/manifest.json, icons/preview.png
"""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ICONS = REPO / "icons"
NS = "{http://www.w3.org/2000/svg}"
ROOT_ATTRS = {"viewBox": "0 0 28 28", "fill": "none", "stroke": "currentColor", "stroke-width": "1.6",
              "stroke-linecap": "round", "stroke-linejoin": "round"}
SHAPES = {"path", "circle", "rect", "line", "polyline", "ellipse", "g"}
GEOMETRY = {"d", "cx", "cy", "r", "rx", "ry", "x", "y", "width", "height", "x1", "y1", "x2", "y2", "points"}
BANNED = {"id", "class", "style", "filter", "mask", "clip-path", "href"}


PIXEL_ROOT = {"viewBox": "0 0 28 28", "fill": "currentColor"}


def lint(svg_text: str, profile: str = "outline") -> list[str]:
    if profile == "pixel":
        return _lint_pixel(svg_text)
    problems = []
    for tag in ("style", "script", "use"):
        if f"<{tag}" in svg_text:
            problems.append(f"<{tag}> is not allowed")
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as e:
        return problems + [f"not valid XML: {e}"]
    for k, v in ROOT_ATTRS.items():
        if root.get(k) != v:
            problems.append(f'root {k}="{root.get(k)}", expected "{v}"' + (" (currentColor)" if k == "stroke" else ""))
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if el is not root and tag not in SHAPES:
            problems.append(f"<{tag}> is not allowed")
        for k, v in el.attrib.items():
            if k in BANNED or k.endswith("href"):
                problems.append(f"attribute {k} is not allowed (no id/filter/mask/style)")
            if el is not root and k in ("stroke", "fill") and v not in ("currentColor", "none"):
                problems.append(f"{tag} {k}={v}: colours must be currentColor or none")
            if el is not root and k == "stroke-width":
                problems.append(f"{tag} overrides stroke-width")
            if k in GEOMETRY:
                nums = re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", v)
                if k == "d":
                    nums = _path_coords(v)
                for n in nums:
                    if abs(float(n) * 2 - round(float(n) * 2)) > 1e-9:
                        problems.append(f"{tag} {k}: {n} is not a multiple of 0.5")
                        break
    return problems


def _lint_pixel(svg_text: str) -> list[str]:
    """Pixel family: only <rect>s on a 2-unit grid, filled currentColor, no strokes."""
    problems = []
    for tag in ("style", "script", "use"):
        if f"<{tag}" in svg_text:
            problems.append(f"<{tag}> is not allowed")
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as e:
        return problems + [f"not valid XML: {e}"]
    for k, v in PIXEL_ROOT.items():
        if root.get(k) != v:
            problems.append(f'root {k}="{root.get(k)}", expected "{v}"' + (" (currentColor)" if k == "fill" else ""))
    for el in root.iter():
        if el is root:
            continue
        tag = el.tag.replace(NS, "")
        if tag != "rect":
            problems.append(f"<{tag}> is not allowed in pixel icons (rects only, no path)")
        for k, v in el.attrib.items():
            if k.startswith("stroke"):
                problems.append(f"{tag} {k}: pixel icons have no stroke")
            if k == "fill" and v != "currentColor":
                problems.append(f"{tag} fill={v}: must be currentColor")
            if k in ("x", "y", "width", "height") and int(float(v)) % 2:
                problems.append(f"{tag} {k}={v} is not a multiple of 2")
    return problems


def _path_coords(d: str) -> list[str]:
    """Numbers in a path, minus the arc flags (which are 0/1 anyway)."""
    return re.findall(r"-?\d*\.?\d+", d)


def family_dir(family: str = "outline") -> Path:
    return ICONS / "pixel" if family == "pixel" else ICONS


def load_manifest(family: str = "outline") -> dict[str, str]:
    return json.loads((family_dir(family) / "manifest.json").read_text())


def pixel_svg(bitmap: list[str]) -> str:
    """One rect per horizontal run of '#' cells; each cell is 2x2 units of the 28x28 viewBox."""
    rects = []
    for y, row in enumerate(bitmap):
        x = 0
        while x < len(row):
            if row[x] == "#":
                start = x
                while x < len(row) and row[x] == "#":
                    x += 1
                rects.append(f'<rect x="{start * 2}" y="{y * 2}" width="{(x - start) * 2}" height="2"/>')
            else:
                x += 1
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" fill="currentColor">{"".join(rects)}</svg>\n'


def svg_for(elements: list[str]) -> str:
    attrs = " ".join(f'{k}="{v}"' for k, v in ROOT_ATTRS.items())
    return f'<svg xmlns="http://www.w3.org/2000/svg" {attrs}>{"".join(elements)}</svg>\n'


def build(family: str = "outline") -> dict[str, str]:
    from tools.icon_glyphs import BUTTONS
    out = family_dir(family)
    out.mkdir(exist_ok=True)
    if family == "pixel":
        from tools.pixel_glyphs import GLYPHS as PIXEL
        for stem, bitmap in PIXEL.items():
            (out / f"{stem}.svg").write_text(pixel_svg(bitmap))
    else:
        from tools.icon_glyphs import GLYPHS
        for stem, elements in GLYPHS.items():
            (out / f"{stem}.svg").write_text(svg_for(elements))
    manifest = {button: f"{stem}.svg" for button, stem in BUTTONS.items()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def preview(family: str = "outline") -> Path:
    """Every icon at 1x and 2x on a dark background, at rest (dim) and hover (#ffffff)."""
    from tools.render import render_svg
    path = family_dir(family) / "preview.png"
    if family == "pixel":
        from tools.pixel_glyphs import GLYPHS as PIXEL
        GLYPHS = {k: [pixel_svg(v).split(">", 1)[1].rsplit("</svg>", 1)[0]] for k, v in PIXEL.items()}
        root, rest, bg = {"fill": "currentColor"}, "#6b8a6b", "#0b100c"
    else:
        from tools.icon_glyphs import GLYPHS
        root, rest, bg = {k: v for k, v in ROOT_ATTRS.items() if k != "viewBox"}, "#828bb8", "#1a1b26"
    stems = sorted(GLYPHS)
    cols = 10
    cell = 28 * 2 + 28 + 40
    rows = (len(stems) + cols - 1) // cols
    w, h = cols * cell * 2, rows * 70
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{bg}"/>']
    for i, stem in enumerate(stems):
        x0, y0 = (i % cols) * cell * 2, (i // cols) * 70 + 6
        inner = "".join(GLYPHS[stem])
        g = " ".join(f'{k}="{v}"' for k, v in root.items())
        for j, (colour, scale) in enumerate(((rest, 1), (rest, 2), ("#ffffff", 2))):
            x = x0 + (0, 34, 34 + 60)[j]
            parts.append(f'<g transform="translate({x},{y0}) scale({scale})" color="{colour}" {g}>{inner}</g>')
        parts.append(f'<text x="{x0 + 160}" y="{y0 + 34}" fill="#565f89" font-size="11" font-family="Menlo">{stem}</text>')
    parts.append("</svg>")
    src = REPO / "build" / f"icons-preview-{family}.svg"
    src.parent.mkdir(exist_ok=True)
    src.write_text("".join(parts))
    render_svg(src, path, w, h)
    return path


if __name__ == "__main__":
    import sys
    fam = sys.argv[1] if len(sys.argv) > 1 else "outline"
    print(len(build(fam)), "buttons")
    print(preview(fam))
