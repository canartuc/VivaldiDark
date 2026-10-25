"""Silk Nocturne: ribbons of silk in Tokyo Night blues, violets and cyans sweeping corner to corner.

Each ribbon is hundreds of fine strands between two edges whose width follows |cos(twist)|; the
light follows the same phase, which reads as light on twisting silk. The brightest twist sits in
the lower right, clear of the Start Page; the top band stays dark for the tab bar.
"""
import math
import random

from tools.palette import P
from tools.svg import COMMON, H, W, bar_zones, f, finish, lin, poly, rad, stars, svg

HERO_BOX = (3120.0, 1180.0, 3620.0, 1780.0)
TAB_BAND = 330


def _twist(u: float, freq: float, phase: float) -> float:
    """Twist phase with an irregular rhythm, so pinch points are not evenly spaced."""
    return math.cos(u * math.pi * freq + phase + 0.9 * math.sin(u * math.pi * 1.7 + phase * 0.6))


def ribbon(y0, slope, amps, phase, width, freq, tphase, grad, op, strands=150):
    n = 260
    xs = [-400 + (W + 800) * i / n for i in range(n + 1)]
    centre, half, light = [], [], []
    for x in xs:
        u = x / W
        y = y0 + slope * (u - 0.5) * H
        for k, a in enumerate(amps):
            y += a * math.sin(u * math.pi * (k + 1.2) + phase * (k + 1))
        tw = _twist(u, freq, tphase)
        centre.append((x, y))
        half.append(width / 2 * (0.10 + 0.90 * math.sqrt(tw * tw + 0.012)))  # soft pinch, no corner
        light.append(0.5 + 0.5 * tw)
    out = [f'<path d="{poly(centre)}" stroke="url(#{grad})" stroke-width="{f(width * 2.2)}" fill="none" '
           f'opacity="{op * 0.20:.2f}" filter="url(#b120)"/>',
           f'<path d="{poly(centre)}" stroke="url(#{grad})" stroke-width="{f(width * 1.3)}" fill="none" '
           f'opacity="{op * 0.22:.2f}" filter="url(#b40)"/>',
           '<g filter="url(#b4)">']
    for s in range(strands):
        v = -1 + 2 * s / (strands - 1)
        pts = [(x, y + v * h) for (x, y), h in zip(centre, half)]
        edge = (1 - abs(v) ** 2) ** 1.5  # feathered: strands fade out well before the edge
        a = op * edge * (0.25 + 0.75 * (0.5 + 0.5 * math.cos(v * 2.2 + 0.6)))
        out.append(f'<path d="{poly(pts)}" stroke="url(#{grad})" stroke-width="2.2" fill="none" opacity="{a:.3f}"/>')
    # continuous specular sheen: one stroke along the upper third, its opacity following the light
    sheen = [(x, y - h * 0.35) for (x, y), h in zip(centre, half)]
    for i in range(0, len(sheen) - 1, 2):
        lv = (light[i] - 0.55) / 0.45
        if lv > 0:
            seg = poly(sheen[i:i + 3])
            out.append(f'<path d="{seg}" stroke="{P["fg"]}" stroke-width="14" opacity="{0.30 * lv:.2f}" fill="none" filter="url(#b14)"/>')
    out.append("</g>")
    return "\n".join(out)


def build() -> str:
    rng = random.Random(3)
    defs = COMMON + [
        lin("base", [(0, "#10111b", 1), (0.25, "#0e0f18", 1), (0.5, "#0c0d15", 1), (0.75, "#0a0b12", 1), (1, "#090a0f", 1)], x2="1", y2="1"),
        lin("topdark", [(0, "#07080c", 0.75), (1, "#07080c", 0)]),
        rad("bl1", [(0, P["blue0"], 0.50), (1, P["blue0"], 0)]),
        rad("bl2", [(0, P["purple"], 0.35), (1, P["purple"], 0)]),
        rad("bl3", [(0, P["blue1"], 0.18), (1, P["blue1"], 0)]),
        lin("gA", [(0, P["blue1"], 1), (0.3, P["blue"], 1), (0.62, P["magenta"], 1), (1, P["magenta2"], 1)], x2="1", y2="0"),
        lin("gB", [(0, P["purple"], 1), (0.45, P["blue"], 1), (1, P["cyan"], 1)], x2="1", y2="0"),
        lin("gC", [(0, P["blue7"], 1), (0.5, P["blue0"], 1), (1, P["purple"], 1)], x2="1", y2="0"),
    ]
    b = [f'<rect width="{W}" height="{H}" fill="url(#base)"/>']
    b.append(f'<ellipse cx="{f(W * 0.10)}" cy="{f(H * 0.30)}" rx="1600" ry="950" fill="url(#bl1)"/>')
    b.append(f'<ellipse cx="{f(W * 0.92)}" cy="{f(H * 0.88)}" rx="1600" ry="950" fill="url(#bl2)"/>')
    b.append(f'<ellipse cx="{f(W * 0.80)}" cy="{f(H * 0.30)}" rx="1300" ry="650" fill="url(#bl3)"/>')
    b.append(stars(rng, 240, H, [P["fg"], P["cyan"]], rmax=1.6, amax=0.32))
    b.append(ribbon(H * 0.86, -0.70, [140, 60, 20], 0.5, 520, 2.2, 0.4, "gC", 0.50, strands=90))
    b.append(ribbon(H * 0.62, -0.80, [150, 70, 30], 1.2, 360, 3.0, 1.3, "gA", 0.9))
    b.append(ribbon(H * 0.73, -0.58, [120, 90, 25], 2.1, 220, 3.6, 2.6, "gB", 0.75))
    for _ in range(34):
        r = rng.uniform(6, 44)
        b.append(f'<circle cx="{f(rng.uniform(0, W))}" cy="{f(rng.uniform(TAB_BAND, H))}" r="{f(r)}" '
                 f'fill="{rng.choice([P["cyan"], P["blue"], P["magenta"], P["fg"]])}" opacity="{rng.uniform(.04, .13):.2f}" filter="url(#b4)"/>')
    b.append(f'<rect width="{W}" height="{TAB_BAND * 1.6}" fill="url(#topdark)"/>')
    zd, zb = bar_zones()
    defs.append(zd)
    b.append(zb)
    b.append(finish())
    return svg("\n".join(defs), "\n".join(b))
