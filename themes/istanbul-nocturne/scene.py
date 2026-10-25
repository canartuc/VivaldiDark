"""Istanbul Nocturne: the Bosphorus at night from the Asian shore, in Bosphorus turquoise.

Maiden's Tower stands on its islet in the right third with the suspension bridge behind it (unlit: only
moonlight on its cables). A full moon, gulls and a city ferry; two street cats keep watch from the
waterfront railing beside a tulip glass of tea.
"""
import math
import random

from tools.svg import COMMON, H, W, bar_zones, f, finish, lin, rad, stars, svg

C = {  # Bosphorus turquoise
    "sky": ["#04101a", "#08202e", "#0d3442", "#145160", "#1f7a80"],
    "moon": "#eef0e2", "halo": "#5fd0c8", "amber": "#f4b85a", "tea": "#c2412f",
    "tower": "#03101a", "far": "#0a2a38", "bridge": "#174150", "cable": "#285e6c",
    "shore": "#020a10", "water": ("#0d3a48", "#02080e"), "dark_window": "#0a1c26",
}

RIVER = H * 0.72
MOON = (2760.0, 560.0, 95.0)
TOWER = (3150.0, RIVER - 26, 1.7)  # islet centre x, islet top, scale
QUAY = H * 0.84
_tx = TOWER[0] + 80 * TOWER[2]
HERO_BOX = (_tx - 80 * TOWER[2], TOWER[1] - 640 * TOWER[2], _tx + 80 * TOWER[2], TOWER[1] + 30 * TOWER[2])


def maidens_tower(cx: float, base: float, s: float, fill: str, window: str, rim: str) -> str:
    """Rocky islet and breakwater, a two-storey stone hall with arched windows and a small domed annex, then the
    tower: square base, octagonal shaft, balcony, lantern, pointed lead cupola, spire and flag."""
    S = lambda v: f(v * s)
    o = []
    rocks = [(-330, 30), (-318, 10), (-290, 2), (-250, -4), (230, -4), (280, 0), (318, 8), (340, 30)]
    o.append(f'<path d="M{f(cx - 340 * s)},{f(base + 40 * s)} ' + " ".join(f"L{f(cx + x * s)},{f(base + y * s)}" for x, y in rocks)
             + f' L{f(cx + 360 * s)},{f(base + 40 * s)} Z" fill="{fill}"/>')
    o.append(f'<rect x="{f(cx - 420 * s)}" y="{f(base + 18 * s)}" width="{S(140)}" height="{S(14)}" fill="{fill}"/>')
    hx0, hx1, hy = cx - 230 * s, cx + 170 * s, base - 150 * s
    o.append(f'<rect x="{f(hx0)}" y="{f(hy)}" width="{f(hx1 - hx0)}" height="{S(150)}" fill="{fill}"/>')
    o.append(f'<rect x="{f(hx0 - 6 * s)}" y="{f(hy - 10 * s)}" width="{f(hx1 - hx0 + 12 * s)}" height="{S(12)}" fill="{fill}"/>')
    o.append(f'<rect x="{f(cx - 300 * s)}" y="{f(base - 95 * s)}" width="{S(90)}" height="{S(95)}" fill="{fill}"/>')
    o.append(f'<path d="M{f(cx - 292 * s)},{f(base - 95 * s)} A{S(37)},{S(34)} 0 0 1 {f(cx - 218 * s)},{f(base - 95 * s)} Z" fill="{fill}"/>')
    o.append(f'<rect x="{f(cx - 256 * s)}" y="{f(base - 150 * s)}" width="{S(3)}" height="{S(24)}" fill="{fill}"/>')
    for k in range(6):
        for row, wy in enumerate((base - 125 * s, base - 62 * s)):
            wx, lit = hx0 + (28 + k * 62) * s, (k + row) % 3 == 0
            o.append(f'<path d="M{f(wx)},{f(wy + 34 * s)} L{f(wx)},{f(wy + 9 * s)} A{S(9)},{S(9)} 0 0 1 {f(wx + 18 * s)},{f(wy + 9 * s)} '
                     f'L{f(wx + 18 * s)},{f(wy + 34 * s)} Z" fill="{window if lit else C["dark_window"]}" opacity="{.75 if lit else .9}"/>')
    tx = cx + 80 * s
    sq_w, sq_top = 120 * s, hy - 40 * s
    o.append(f'<rect x="{f(tx - sq_w / 2)}" y="{f(sq_top)}" width="{f(sq_w)}" height="{f(base - sq_top)}" fill="{fill}"/>')
    oct_w, oct_top = 96 * s, sq_top - 150 * s
    o.append(f'<rect x="{f(tx - oct_w / 2)}" y="{f(oct_top)}" width="{f(oct_w)}" height="{f(sq_top - oct_top + 2)}" fill="{fill}"/>')
    for dx in (-oct_w * 0.25, oct_w * 0.25):  # octagon facet edges
        o.append(f'<rect x="{f(tx + dx - 1)}" y="{f(oct_top)}" width="2" height="{f(sq_top - oct_top)}" fill="{rim}" opacity=".18"/>')
    o.append(f'<rect x="{f(tx - 9 * s)}" y="{f(sq_top - 100 * s)}" width="{S(18)}" height="{S(36)}" fill="{window}" opacity=".75"/>')
    by = oct_top - 6 * s
    o.append(f'<rect x="{f(tx - 78 * s)}" y="{f(by)}" width="{S(156)}" height="{S(12)}" fill="{fill}"/>')
    o.append("".join(f'<rect x="{f(tx + (-74 + k * 16) * s)}" y="{f(by - 22 * s)}" width="{S(3)}" height="{S(22)}" fill="{fill}"/>' for k in range(10)))
    o.append(f'<rect x="{f(tx - 78 * s)}" y="{f(by - 24 * s)}" width="{S(156)}" height="{S(4)}" fill="{fill}"/>')
    lw, ltop = 64 * s, by - 86 * s
    o.append(f'<rect x="{f(tx - lw / 2)}" y="{f(ltop)}" width="{f(lw)}" height="{f(by - ltop)}" fill="{fill}"/>')
    for dx in (-18, 4):
        o.append(f'<rect x="{f(tx + dx * s)}" y="{f(ltop + 16 * s)}" width="{S(12)}" height="{S(40)}" fill="{window}" opacity=".8"/>')
    o.append(f'<rect x="{f(tx - lw / 2 - 6 * s)}" y="{f(ltop - 8 * s)}" width="{f(lw + 12 * s)}" height="{S(10)}" fill="{fill}"/>')
    ch = 120 * s
    o.append(f'<path d="M{f(tx - lw / 2 - 2 * s)},{f(ltop - 8 * s)} C{f(tx - lw / 2 + 4 * s)},{f(ltop - 70 * s)} {f(tx - 6 * s)},{f(ltop - ch + 20 * s)} {f(tx)},{f(ltop - ch)} '
             f'C{f(tx + 6 * s)},{f(ltop - ch + 20 * s)} {f(tx + lw / 2 - 4 * s)},{f(ltop - 70 * s)} {f(tx + lw / 2 + 2 * s)},{f(ltop - 8 * s)} Z" fill="{fill}"/>')
    o.append(f'<rect x="{f(tx - 2)}" y="{f(ltop - ch - 60 * s)}" width="4" height="{S(62)}" fill="{fill}"/>')
    o.append(f'<path d="M{f(tx + 2)},{f(ltop - ch - 58 * s)} L{f(tx + 40 * s)},{f(ltop - ch - 50 * s)} L{f(tx + 2)},{f(ltop - ch - 40 * s)} Z" fill="{fill}"/>')
    o.append(f'<rect x="{f(tx - oct_w / 2)}" y="{f(oct_top)}" width="3" height="{f(sq_top - oct_top)}" fill="{rim}" opacity=".35" filter="url(#b2)"/>')
    return "".join(o)


def bridge(x0: float, x1: float, t0: float, t1: float, deck: float, th: float, fill: str, cable: str, rim: str) -> str:
    """Suspension bridge, unlit: portal towers, a main cable to both shore anchorages, inclined (zig-zag)
    hangers and a thin, gently arched deck."""
    o, rise = [], 18
    def dy(x):
        return deck - rise * (1 - ((x - (t0 + t1) / 2) / ((t1 - t0) / 2)) ** 2) if t0 <= x <= t1 else deck
    pts = [(x, dy(x)) for x in range(int(x0), int(x1) + 1, 20)]
    top = " L".join(f"{f(x)},{f(y)}" for x, y in pts)
    o.append(f'<path d="M{top} L' + " L".join(f"{f(x)},{f(y + 16)}" for x, y in reversed(pts)) + f' Z" fill="{fill}"/>')
    o.append(f'<path d="M{top}" stroke="{rim}" stroke-width="2" opacity=".35" fill="none"/>')
    ctop, sag = deck - th, deck - 40
    def cable_y(x):
        if x < t0:
            return deck + (ctop - deck) * (x - x0) / (t0 - x0)
        if x > t1:
            return ctop + (deck - ctop) * (x - t1) / (x1 - t1)
        return sag + (ctop - sag) * ((x - (t0 + t1) / 2) / ((t1 - t0) / 2)) ** 2
    o.append(f'<path d="M' + " L".join(f"{f(x)},{f(cable_y(x))}" for x in range(int(x0), int(x1) + 1, 10))
             + f'" stroke="{cable}" stroke-width="5" fill="none"/>')
    hangers = []
    for i, x in enumerate(range(int(x0) + 20, int(x1) - 20, 44)):
        if abs(x - t0) >= 30 and abs(x - t1) >= 30:
            xb = x + (22 if i % 2 else -22)
            hangers.append(f"M{f(x)},{f(cable_y(x))} L{f(xb)},{f(dy(xb))}")
    o.append(f'<path d="{"".join(hangers)}" stroke="{cable}" stroke-width="1.6" opacity=".55" fill="none"/>')
    for tx in (t0, t1):
        lw, gap = 16, 38
        for side in (-1, 1):
            xa = tx + side * gap
            o.append(f'<path d="M{f(xa - lw / 2)},{f(deck + 60)} L{f(xa - lw / 2 - side * 4)},{f(ctop - 8)} '
                     f'L{f(xa + lw / 2 - side * 4)},{f(ctop - 8)} L{f(xa + lw / 2)},{f(deck + 60)} Z" fill="{fill}"/>')
        for k in (0.0, 0.42, 0.78):
            o.append(f'<rect x="{f(tx - gap - 6)}" y="{f(ctop - 8 + (deck - ctop) * k)}" width="{f(2 * gap + 12)}" height="12" fill="{fill}"/>')
        o.append(f'<rect x="{f(tx - gap + 2)}" y="{f(ctop - 8)}" width="3" height="{f(th + 60)}" fill="{rim}" opacity=".25"/>')
    return "".join(o)


def ferry(x: float, water: float, fill: str, window: str) -> str:
    return (f'<path d="M{f(x)},{f(water - 10)} L{f(x + 600)},{f(water - 10)} L{f(x + 560)},{f(water + 30)} L{f(x + 40)},{f(water + 30)} Z" fill="{fill}"/>'
            f'<rect x="{f(x + 80)}" y="{f(water - 80)}" width="440" height="72" fill="{fill}"/>'
            f'<rect x="{f(x + 150)}" y="{f(water - 130)}" width="300" height="52" fill="{fill}"/>'
            f'<rect x="{f(x + 320)}" y="{f(water - 210)}" width="46" height="82" fill="{fill}"/>'
            + "".join(f'<rect x="{f(x + 100 + i * 34)}" y="{f(water - 62)}" width="16" height="22" fill="{window}" opacity=".75"/>' for i in range(12)))


def cat(x: float, y: float, s: float, fill: str, eye: str, rim: str, pose: str = "sit", flip: bool = False) -> str:
    """A street cat in silhouette with a faint moonlit outline; its amber eyes catch the light."""
    t = f' transform="translate({f(x)},{f(y)}) scale({f(-s if flip else s)},{f(s)})"'
    if pose == "sit":
        body = ('<path d="M-38,0 C-46,-40 -36,-92 -6,-104 C18,-112 34,-92 36,-60 C40,-30 42,-8 34,0 Z"/>'
                '<circle cx="4" cy="-120" r="27"/><path d="M-20,-134 L-16,-166 L-2,-142 Z M10,-142 L24,-166 L28,-134 Z"/>'
                '<path d="M30,-4 C70,-2 86,-20 74,-44 C70,-52 62,-48 66,-40 C74,-24 60,-14 30,-14 Z"/>')
        eyes = (-8, -122), (14, -122)
    else:  # loaf
        body = ('<path d="M-60,0 C-62,-34 -30,-52 10,-50 C46,-48 62,-30 60,0 Z"/>'
                '<circle cx="48" cy="-50" r="24"/><path d="M32,-62 L34,-92 L48,-70 Z M54,-70 L68,-92 L70,-60 Z"/>'
                '<path d="M-58,-6 C-86,-6 -96,8 -76,14 C-62,18 -40,10 -40,4 Z"/>')
        eyes = (40, -52), (58, -52)
    e = "".join(f'<circle cx="{ex}" cy="{ey}" r="3.6" fill="{eye}"/><circle cx="{ex}" cy="{ey}" r="9" fill="{eye}" opacity=".25"/>'
                for ex, ey in eyes)
    return (f'<g{t} fill="none" stroke="{rim}" stroke-width="5" opacity=".45" filter="url(#b2)">{body}</g>'
            f'<g{t} fill="{fill}">{body}{e}</g>')


def build() -> str:
    c, rng = C, random.Random(5)
    river, sky = RIVER, c["sky"]
    defs = COMMON + [
        lin("sky", [(i / (len(sky) - 1), col, 1) for i, col in enumerate(sky)]),
        rad("halo", [(0, c["moon"], 0.32), (0.3, c["halo"], 0.12), (1, c["halo"], 0)]),
        lin("water", [(0, c["water"][0], 1), (1, c["water"][1], 1)]),
        lin("fadeDown", [(0, "#fff", 0.8), (1, "#fff", 0)]),
        f'<mask id="rm"><rect x="0" y="{f(river)}" width="{W}" height="{f(H - river)}" fill="url(#fadeDown)"/></mask>',
    ]
    zd, zb = bar_zones()
    defs.append(zd)
    mx, my, mr = MOON
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>', stars(rng, 320, H * 0.55, [c["moon"], c["halo"]], amax=0.5),
         f'<circle cx="{f(mx)}" cy="{f(my)}" r="{f(mr * 4.8)}" fill="url(#halo)"/>',
         f'<circle cx="{f(mx)}" cy="{f(my)}" r="{f(mr)}" fill="{c["moon"]}" opacity=".95"/>']
    # the Asian shore: low hills and a scatter of lit windows along the water
    hills = " ".join(f"L{x},{f(river - 90 - 70 * math.sin(x / 520) - 30 * math.sin(x / 170))}" for x in range(0, W + 80, 80))
    b.append(f'<path d="M0,{f(river)} {hills} L{W},{f(river)} Z" fill="{c["far"]}"/>')
    x = -40.0
    while x < W + 40:
        bw, h = rng.uniform(60, 150), rng.uniform(20, 60)
        b.append(f'<rect x="{f(x)}" y="{f(river - h)}" width="{f(bw)}" height="{f(h)}" fill="{c["far"]}"/>')
        if rng.random() < 0.35:
            b.append(f'<rect x="{f(x + bw / 2)}" y="{f(river - h + 12)}" width="9" height="14" fill="{c["amber"]}" opacity="{rng.uniform(.35, .8):.2f}"/>')
        x += bw + rng.uniform(-4, 4)
    scene = (bridge(1500, 4100, 1950, 3620, river - 80, 360, c["bridge"], c["cable"], c["halo"])
             + maidens_tower(*TOWER, c["tower"], c["amber"], c["halo"])
             + ferry(1150, river + 20, c["tower"], c["amber"]))
    b.append(scene)
    for _ in range(9):  # gulls
        gx, gy = rng.uniform(1700, 3700), rng.uniform(800, 1250)
        b.append(f'<path d="M{f(gx - 16)},{f(gy)} Q{f(gx - 8)},{f(gy - 9)} {f(gx)},{f(gy)} Q{f(gx + 8)},{f(gy - 9)} {f(gx + 16)},{f(gy)}" '
                 f'stroke="{c["moon"]}" stroke-width="2.5" fill="none" opacity=".45"/>')
    b.append(f'<rect x="0" y="{f(river)}" width="{W}" height="{f(H - river)}" fill="url(#water)"/>')
    b.append(f'<g mask="url(#rm)" opacity=".42"><g transform="translate(0,{f(2 * river)}) scale(1,-1)" filter="url(#b8)">{scene}</g></g>')
    b.append(f'<rect x="{f(mx - 50)}" y="{f(river + 10)}" width="100" height="{f(H - river)}" fill="{c["moon"]}" opacity=".16" filter="url(#b24)"/>')
    # the waterfront: railing, two cats, a tulip glass of tea on the ledge
    q = QUAY
    b.append(f'<rect x="0" y="{f(q)}" width="{W}" height="{f(H - q)}" fill="{c["shore"]}"/>')
    b.append(f'<rect x="0" y="{f(q)}" width="{W}" height="4" fill="{c["halo"]}" opacity=".22"/>')
    b.append(f'<rect x="0" y="{f(q - 120)}" width="{W}" height="6" fill="{c["shore"]}"/>')
    b += [f'<rect x="{px}" y="{f(q - 120)}" width="8" height="120" fill="{c["shore"]}"/>' for px in range(40, W, 160)]
    b += [cat(3420, q, 1.55, c["shore"], c["amber"], "#9fb8d8"), cat(3020, q, 1.3, c["shore"], c["amber"], "#9fb8d8", "loaf", True)]
    gx = 3720
    b.append(f'<path d="M{gx - 18},{f(q - 70)} C{gx - 26},{f(q - 40)} {gx - 8},{f(q - 30)} {gx - 12},{f(q - 6)} L{gx + 12},{f(q - 6)} '
             f'C{gx + 8},{f(q - 30)} {gx + 26},{f(q - 40)} {gx + 18},{f(q - 70)} Z" fill="{c["tea"]}" opacity=".85"/>'
             f'<rect x="{gx - 30}" y="{f(q - 6)}" width="60" height="6" fill="#d9d2c0" opacity=".5"/>')
    b += [zb, finish()]
    return svg("\n".join(defs), "\n".join(b))
