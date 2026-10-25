"""SVG building blocks shared by every theme scene (3840x2160 canvas)."""
from tools.palette import P

W, H = 3840, 2160


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def poly(pts):
    return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)


def svg(defs, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">\n<defs>\n{defs}\n</defs>\n{body}\n</svg>\n'
    )


def stops(st):
    return "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in st)


def lin(id_, st, x2="0", y2="1", x1="0", y1="0", units=""):
    u = f' gradientUnits="{units}"' if units else ""
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{u}>{stops(st)}</linearGradient>'


def rad(id_, st, cx=".5", cy=".5", r=".5"):
    return f'<radialGradient id="{id_}" cx="{cx}" cy="{cy}" r="{r}">{stops(st)}</radialGradient>'


def blur(id_, sd):
    return (
        f'<filter id="{id_}" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur stdDeviation="{sd}"/></filter>'
    )


# Film grain kills gradient banding and is most of the "premium" feel on big flat skies.
GRAIN = (
    '<filter id="grain" x="0" y="0" width="100%" height="100%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7" stitchTiles="stitch"/>'
    '<feColorMatrix type="matrix" values="0 0 0 0 0.75  0 0 0 0 0.79  0 0 0 0 0.96  0 0 0 0.10 0"/>'
    "</filter>"
)
VIGNETTE = rad("vig", [(0, "#000", 0), (0.65, "#000", 0), (1, "#05060a", 0.45)], r=".75")
COMMON = [blur(f"b{n}", n) for n in (2, 4, 8, 14, 24, 40, 70, 120)] + [GRAIN, VIGNETTE]


def finish():
    return (
        f'<rect width="{W}" height="{H}" fill="url(#vig)"/>'
        f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.5"/>'
    )


def stars(rng, n, y_max, colors, rmin=0.8, rmax=2.4, amin=0.12, amax=0.8, sparkle=0, x_avoid=None):
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, y_max)
        r = rng.uniform(rmin, rmax) * (1 if rng.random() > 0.06 else 1.6)
        a = rng.uniform(amin, amax) * (1 - y / y_max) ** 0.5
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{rng.choice(colors)}" opacity="{a:.2f}"/>')
    for _ in range(sparkle):
        x, y = rng.uniform(0, W), rng.uniform(y_max * 0.05, y_max * 0.75)
        if x_avoid and x_avoid[0] < x < x_avoid[1]:
            continue
        L = rng.uniform(16, 34)
        c = rng.choice(colors)
        out.append(
            f'<circle cx="{f(x)}" cy="{f(y)}" r="22" fill="{c}" opacity=".22" filter="url(#b8)"/>'
            f'<g opacity="{rng.uniform(.55,.9):.2f}" stroke="{c}" stroke-width="1.6" stroke-linecap="round">'
            f'<line x1="{f(x-L)}" y1="{f(y)}" x2="{f(x+L)}" y2="{f(y)}"/>'
            f'<line x1="{f(x)}" y1="{f(y-L)}" x2="{f(x)}" y2="{f(y+L)}"/></g>'
            f'<circle cx="{f(x)}" cy="{f(y)}" r="2.6" fill="{P["fg"]}"/>'
        )
    return "\n".join(out)


def rain(rng, n, color, amin=0.05, amax=0.2):
    r = []
    for _ in range(n):
        x, y = rng.uniform(-200, W + 200), rng.uniform(-120, H)
        L = rng.uniform(26, 120)
        r.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x-L*0.16)}" y2="{f(y+L)}" '
                 f'stroke-opacity="{rng.uniform(amin,amax):.2f}" stroke-width="{rng.choice([1,1,1.4,2])}"/>')
    return f'<g stroke="{color}" stroke-linecap="round">{"".join(r)}</g>'


SHADE = "#06070b"


def _eased(start: float, end: float, strength: float, rising: bool) -> list:
    """Gradient stops with a smootherstep ramp between `start` and `end` (fractions): no visible edge."""
    out = []
    for i in range(17):
        t = i / 16
        s = t * t * t * (t * (6 * t - 15) + 10)
        a = strength * (s if rising else 1 - s)
        out.append((round(start + (end - start) * t, 4), SHADE, round(a, 3)))
    return out


def bar_zones(strength: float = 0.9) -> tuple[str, str]:
    """(defs, body) that sink the art into shadow where Vivaldi's bars sit.

    Full strength only right under the bars (top 0..300 px, left 0..700 px, bottom 1950..2160 px),
    then a long, gentle falloff (to 800 / 2300 / 1300 px) so the scene reads as light falling
    from the right rather than as a frame. Measured against tab text in tests/test_scenes.py.
    """
    top = lin("bzTop", [(0, SHADE, strength)] + _eased(300 / 800, 1, strength, rising=False),
              x1="0", y1="0", x2="0", y2="800", units="userSpaceOnUse")
    left = lin("bzLeft", [(0, SHADE, strength)] + _eased(700 / 2300, 1, strength, rising=False),
               x1="0", y1="0", x2="2300", y2="0", units="userSpaceOnUse")
    bottom = lin("bzBottom", _eased(0, 650 / 860, strength, rising=True) + [(1, SHADE, strength)],
                 x1="0", y1="1300", x2="0", y2="2160", units="userSpaceOnUse")
    body = (f'<rect width="{W}" height="800" fill="url(#bzTop)"/>'
            f'<rect width="2300" height="{H}" fill="url(#bzLeft)"/>'
            f'<rect y="1300" width="{W}" height="860" fill="url(#bzBottom)"/>')
    return top + left + bottom, body
