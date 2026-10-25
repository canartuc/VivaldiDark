"""Neon Fuji: Mount Fuji under a sliced synthwave moon, a starfield and a neon grid to the horizon.

The moon and Fuji stand in the right third, clear of the Start Page; the open sky on the left
carries the stars; the grid's vanishing point sits under Fuji.
"""
import math
import random

from tools.palette import P
from tools.svg import COMMON, H, W, bar_zones, f, finish, lin, poly, rad, stars, svg

HZ = H * 0.70  # horizon
MX, MY, MR = 3360.0, 880.0, 280.0  # moon
PEAK, HALF_BASE, RIM = H * 0.47, 700.0, 60.0  # Fuji
HERO_BOX = (MX - MR, MY - MR, MX + MR, MY + MR)
TAB_BAND = 330


def build() -> str:
    rng = random.Random(5)
    hz, mx, my, mr = HZ, MX, MY, MR
    defs = COMMON + [
        lin("sky", [(0, "#08090e", 1), (0.15, "#0b0c14", 1), (0.3, "#0f101b", 1), (0.42, "#141426", 1), (0.55, "#1a1731", 1), (0.68, "#231b3b", 1), (0.8, "#2e1f46", 1), (0.9, "#3a204b", 1), (1, "#46204d", 1)]),
        lin("moon", [(0, P["cyan"], 1), (0.2, "#8fb6fb", 1), (0.42, P["magenta"], 1), (0.62, "#d98ae6", 1), (0.85, P["magenta2"], 1)]),
        rad("moonhalo", [(0, P["magenta"], 0.40), (0.3, P["purple"], 0.16), (1, P["purple"], 0)]),
        lin("mtn", [(0, "#252a45", 1), (0.2, "#1d2035", 1), (0.45, "#151726", 1), (0.75, "#0f1019", 1), (1, "#0b0c13", 1)]),
        lin("mtnshade", [(0, "#000", 0), (0.5, "#000", 0), (1, "#000", 0.45)], x2="1", y2="0"),
        lin("snow", [(0, "#e3e8ff", 1), (0.3, "#d2daff", 0.97), (0.6, P["fg"], 0.9), (1, P["blue"], 0.55)]),
        lin("floor", [(0, "#22163a", 1), (0.2, "#120f1f", 1), (1, "#07080c", 1)]),
        lin("gridfade", [(0, "#fff", 0.0), (0.06, "#fff", 1), (0.6, "#fff", 0.5), (1, "#fff", 0.25)]),
        lin("hzline", [(0, P["magenta2"], 0.15), (0.85, P["magenta2"], 1), (1, P["magenta2"], 0.6)], x2="1", y2="0"),
        lin("shoot", [(0, P["fg"], 0), (1, P["fg"], 0.9)], x2="1", y2="0"),
        lin("mist", [(0, "#4a3a70", 0), (0.5, "#4a3a70", 0.5), (1, "#4a3a70", 0)]),
        lin("ridgeFar", [(0, "#2e2952", 0.85), (0.6, "#251f42", 0.55), (1, "#3b2a5c", 0.25)]),
        lin("ridgeMid", [(0, "#211d3a", 1), (0.7, "#1a1730", 0.9), (1, "#2a1f45", 0.6)]),
        rad("refl", [(0, P["magenta"], 0.40), (1, P["magenta"], 0)]),
        '<mask id="gridmask"><rect x="0" y="0" width="100%" height="100%" fill="url(#gridfade)"/></mask>',
    ]
    cuts, yy, gap = [], my + mr * 0.10, 5
    while yy < my + mr:
        cuts.append(f'<rect x="{f(mx - mr - 5)}" y="{f(yy)}" width="{f(2 * mr + 10)}" height="{f(gap)}" fill="#000"/>')
        yy += 30
        gap += 4
    defs.append(f'<mask id="moonmask"><rect width="{W}" height="{H}" fill="#fff"/><g filter="url(#b4)">{"".join(cuts)}</g></mask>')

    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    # stars stay faint in the tab-bar band; sparkles keep away from the moon
    b.append(stars(rng, 900, hz * 0.95, [P["fg"], P["fg_dark"], P["cyan"], P["magenta"]], amax=0.75, sparkle=12,
                   x_avoid=(mx - mr * 1.6, W)))
    b.append(f'<rect width="{W}" height="{TAB_BAND}" fill="#08090e" opacity=".35"/>')
    for sx, sy, L in [(W * 0.30, H * 0.22, 460), (W * 0.62, H * 0.18, 300)]:
        b.append(f'<g transform="translate({f(sx)},{f(sy)}) rotate(160)"><rect x="0" y="-1.5" width="{L}" height="3" fill="url(#shoot)" opacity=".7"/></g>')
    b.append(f'<circle cx="{f(mx)}" cy="{f(my)}" r="{f(mr * 3.2)}" fill="url(#moonhalo)"/>')
    b.append(f'<circle cx="{f(mx)}" cy="{f(my)}" r="{f(mr + 6)}" fill="url(#moon)" opacity=".35" filter="url(#b14)"/>')
    b.append(f'<circle cx="{f(mx)}" cy="{f(my)}" r="{f(mr)}" fill="url(#moon)" mask="url(#moonmask)" filter="url(#b2)"/>')
    # distant ranges across the whole width (they carry the left edge and the side panel)
    b.append(ridge(rng, hz, H * 0.11, "url(#ridgeFar)", 1, 7, blur="b8"))
    b.append(ridge(rng, hz, H * 0.07, "url(#ridgeMid)", 1, 11, blur="b2"))
    b.append(f'<rect x="0" y="{f(hz - H * 0.09)}" width="{W}" height="{f(H * 0.11)}" fill="url(#mist)" opacity=".7"/>')
    # Fuji: concave flanks, a short crater rim
    left, right = [], []
    for i in range(80):
        t = i / 79
        dx = RIM + (HALF_BASE - RIM) * t
        y = hz - (hz - PEAK) * (1 - t) ** 2.1 + 4 * math.sin(t * 9) * t
        left.append((mx - dx, y))
        right.append((mx + dx, y))
    crater = [(mx - RIM * 0.5, PEAK + 6), (mx - RIM * 0.1, PEAK + 2), (mx + RIM * 0.3, PEAK + 8), (mx + RIM * 0.7, PEAK + 3)]
    ridge_line = list(reversed(left)) + crater + right
    outline = poly(ridge_line) + " Z"
    b.append(f'<path d="{outline}" fill="url(#mtn)"/>')
    b.append(f'<path d="{outline}" fill="url(#mtnshade)"/>')
    b.append(f'<path d="{snowcap(rng, left, right, crater)}" fill="url(#snow)" opacity=".92" filter="url(#b2)"/>')
    b.append(f'<path d="{poly(ridge_line)}" fill="none" stroke="{P["magenta"]}" stroke-width="5" opacity=".35" filter="url(#b4)"/>')
    b.append(f'<path d="{poly(ridge_line)}" fill="none" stroke="{P["magenta"]}" stroke-width="16" opacity=".18" filter="url(#b8)"/>')
    b.append(ridge(rng, hz + 2, H * 0.04, "#100d1b", 1, 15, blur="b2"))
    b.append(f'<g filter="url(#b2)">{city_strip(rng, hz)}</g>')
    b.append(f'<rect x="0" y="{f(hz - 3)}" width="{W}" height="6" fill="url(#hzline)" opacity=".75" filter="url(#b4)"/>')
    b.append(f'<rect x="0" y="{f(hz - 30)}" width="{W}" height="60" fill="url(#hzline)" opacity=".45" filter="url(#b24)"/>')
    # floor: perspective grid converging under Fuji + the moon's broken reflection
    b.append(f'<rect x="0" y="{f(hz)}" width="{W}" height="{f(H - hz)}" fill="url(#floor)"/>')
    b.append(f'<ellipse cx="{f(mx)}" cy="{f(hz + 110)}" rx="{f(mr * 1.5)}" ry="130" fill="url(#refl)" filter="url(#b40)"/>')
    for i in range(9):
        y = hz + 22 + i * 20 + i * i * 3
        w = mr * (1.15 - i * 0.09) * rng.uniform(0.7, 1)
        b.append(f'<rect x="{f(mx - w / 2)}" y="{f(y)}" width="{f(w)}" height="{f(4 + i * 0.6)}" rx="3" fill="{P["magenta"]}" opacity="{0.42 - 0.035 * i:.2f}" filter="url(#b4)"/>')
    vx = W / 2  # centred vanishing point; outer lines fade so the fan has no edge and no dense band
    verts = []
    for i in range(-170, 171):
        fade = max(0.0, 1 - abs(i) / 170) ** 1.6
        if fade < 0.02:
            continue
        verts.append(f'<path d="M{f(vx + i * 12)},{f(hz)} L{f(vx + i * 230)},{f(H + 40)}" opacity="{fade:.2f}"/>')
    horiz, k = [], 1
    while True:
        y = hz + 5 * k ** 1.95
        if y > H + 10:
            break
        horiz.append(f"M0,{f(y)} L{W},{f(y)}")
        k += 1
    hd = "".join(horiz)
    vd = "".join(verts)
    b.append(f'<g mask="url(#gridmask)" fill="none" filter="url(#b2)">'
             f'<path d="{hd}" stroke="{P["blue"]}" stroke-width="9" opacity=".12" filter="url(#b4)"/>'
             f'<path d="{hd}" stroke="{P["magenta"]}" stroke-width="2" opacity=".5"/>'
             f'<g stroke="{P["magenta"]}" stroke-width="2" opacity=".5">{vd}</g></g>')
    zd, zb = bar_zones()
    defs.append(zd)
    b.append(zb)
    b.append(finish())
    return svg("\n".join(defs), "\n".join(b))


def snowcap(rng, left, right, crater) -> str:
    """One shape: the cap follows the flanks, its hem waves gently and dips into a few narrow gullies."""
    sl = [p for i, p in enumerate(left) if i / 79 <= 0.27]
    sr = [p for i, p in enumerate(right) if i / 79 <= 0.27]
    (xl, yl), (xr, yr) = sl[-1], sr[-1]
    phase = rng.uniform(0, 6)
    gullies = [(rng.uniform(0.08, 0.92), rng.choice([25, 40, 60, 90, 120, 150]), rng.uniform(0.005, 0.010)) for _ in range(10)]
    n = 360
    hem = []
    for i in range(1, n):
        u = i / n
        x = xr - (xr - xl) * u
        taper = math.sin(u * math.pi) ** 0.5  # 0 where the hem meets the flanks: no step
        y = yr + (yl - yr) * u + (26 + 14 * math.sin(u * math.pi * 3.2 + phase) + 8 * math.sin(u * math.pi * 7.3 + phase * 2)) * taper
        for gu, depth, width in gullies:
            y += depth * (1 - abs(gu - 0.5) * 1.2) * math.exp(-((u - gu) / width) ** 2)
        hem.append((x, y))
    return poly(list(reversed(sl)) + crater + sr + hem + [(xl, yl)]) + " Z"


def ridge(rng, base, amp, color, op, waves, blur=None):
    pts = []
    phase = rng.uniform(0, 6)
    for i in range(0, 321):
        u = i / 320
        y = base - amp * (0.55 + 0.30 * math.sin(u * waves + phase) + 0.15 * math.sin(u * waves * 3.7 + phase * 2))
        pts.append((W * u, y))
    flt = f' filter="url(#{blur})"' if blur else ""
    return f'<path d="M0,{f(base)} L{poly(pts)[1:]} L{W},{f(base)} Z" fill="{color}" opacity="{op}"{flt}/>'


def city_strip(rng, hz):
    out, x = [], 0
    while x < W:
        bw = rng.uniform(10, 46)
        bh = rng.uniform(6, 50) * (1.7 if rng.random() < 0.07 else 1)
        out.append(f'<rect x="{f(x)}" y="{f(hz - bh)}" width="{f(bw)}" height="{f(bh)}" fill="#0c0a16"/>')
        for _ in range(rng.randint(0, 2)):
            out.append(f'<rect x="{f(x + rng.uniform(2, bw - 4))}" y="{f(hz - rng.uniform(3, bh))}" width="2.5" height="2.5" '
                       f'fill="{rng.choice([P["yellow"], P["cyan"], P["magenta"], P["fg"]])}" opacity=".85"/>')
        x += bw
    return "".join(out)
