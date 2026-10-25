"""Paris Nocturne: the Seine at moonrise, in the Nuit de Paris palette.

The iron tower stands in the right third, UNLIT (its structure is public domain; its lighting is
protected): a dark silhouette with only moonlight catching one edge. A full moon rises just to its
right; Haussmann façades with a few warm windows line the river; a lamp-lit stone bridge crosses it.
"""
import random

from tools.svg import COMMON, H, W, bar_zones, f, finish, lin, poly, rad, stars, svg

C = {  # Nuit de Paris
    "sky": ["#05070f", "#0a1024", "#121b3a", "#1d2a55", "#2a2f5a"],
    "moon": "#ece6d8", "halo": "#6f8fd8", "bleu": "#318ce7", "lumiere": "#e8b04a",
    "build": "#0e1428", "tower": "#070a14", "water": ("#141c38", "#05070f"), "cloud": "#1a2346",
}

RIVER = H * 0.76
TOWER_X, TOWER_H = 3250.0, 1200.0
TOWER_BASE = RIVER - 20
MOON = (3470.0, 700.0, 140.0)

# Half-width of the tower as a fraction of its half base width, by height fraction from the TOP.
# Base 125 m; 1st platform at 57 m (~70 m wide) over the great arch; 2nd at 115 m (~40 m); top at 276 m.
PROFILE = [(0.0, 0.025), (0.164, 0.085), (0.35, 0.13), (0.652, 0.31), (0.75, 0.41), (0.827, 0.57), (0.92, 0.76), (1.0, 1.0)]
T_P1, T_P2, T_TOP = 0.827, 0.652, 0.164
HW = TOWER_H * 0.19
_top = TOWER_BASE - TOWER_H
HERO_BOX = (TOWER_X - HW * 0.57 - 40, _top - TOWER_H * 0.06 - 20, MOON[0] + MOON[2] + 10, _top + TOWER_H * T_P1 + 20)


def half_frac(t: float) -> float:
    """Monotone cubic (PCHIP-style) through PROFILE: a smooth concave flare with no kinks."""
    xs, ys = [p[0] for p in PROFILE], [p[1] for p in PROFILE]
    d = [(ys[k + 1] - ys[k]) / (xs[k + 1] - xs[k]) for k in range(len(xs) - 1)]

    def slope(k):
        if k == 0:
            return d[0]
        if k == len(xs) - 1:
            return d[-1]
        return 0 if d[k - 1] * d[k] <= 0 else 2 / (1 / d[k - 1] + 1 / d[k])
    for i in range(len(xs) - 1):
        if xs[i] <= t <= xs[i + 1]:
            h, u = xs[i + 1] - xs[i], (t - xs[i]) / (xs[i + 1] - xs[i])
            h00, h10, h01, h11 = 2*u**3 - 3*u**2 + 1, u**3 - 2*u**2 + u, -2*u**3 + 3*u**2, u**3 - u**2
            return h00 * ys[i] + h10 * h * slope(i) + h01 * ys[i + 1] + h11 * h * slope(i + 1)
    return ys[-1]


def tower(cx: float, base: float, height: float, fill: str, rim: str, lattice: str) -> str:
    """Unlit lattice tower: flared legs, great arch, open frame, three platforms, slim antenna."""
    hw = height * 0.19
    half = lambda t: hw * half_frac(t)
    y_of = lambda t: base - height + height * t
    n = 160
    left = [(cx - half(i / n), y_of(i / n)) for i in range(n + 1)]
    right = [(cx + half(i / n), y_of(i / n)) for i in range(n + 1)]
    outer = poly(left) + " L" + " L".join(f"{f(x)},{f(y)}" for x, y in reversed(right)) + " Z"
    arch_l = [(cx - half(1.0) + hw * 0.36, base)]
    for i in range(1, 21):
        t = 1.0 - (1.0 - T_P1 - 0.03) * i / 20
        arch_l.append((cx - half(t) + hw * 0.36 * (1 - (1 - t) * 2.5), y_of(t)))
    arch_r = [(2 * cx - x, y) for x, y in arch_l]
    arch = (poly(arch_l) + f" Q{f(cx)},{f(y_of(T_P1 + 0.03) - height * 0.035)} {f(arch_r[-1][0])},{f(arch_r[-1][1])} L"
            + " L".join(f"{f(x)},{f(y)}" for x, y in reversed(arch_r)) + " Z")
    frame_l = [(cx - half(t) * 0.55, y_of(t)) for t in [T_P1 - 0.025 - k * (T_P1 - T_P2 - 0.05) / 12 for k in range(13)]]
    frame = poly(frame_l) + " L" + " L".join(f"{f(2 * cx - x)},{f(y)}" for x, y in reversed(frame_l)) + " Z"
    out = [f'<path d="{outer} {arch} {frame}" fill="{fill}" fill-rule="evenodd"/>']
    for t, th, extra in ((T_P1, height * 0.024, 0.13), (T_P2, height * 0.018, 0.10), (T_TOP, height * 0.012, 0.06)):
        w = half(t) * 2 + hw * extra
        out.append(f'<rect x="{f(cx - w / 2)}" y="{f(y_of(t) - th / 2)}" width="{f(w)}" height="{f(th)}" fill="{fill}"/>')
        out.append(f'<rect x="{f(cx - w / 2)}" y="{f(y_of(t) - th / 2)}" width="{f(w)}" height="2" fill="{rim}" opacity=".25"/>')
    ah = height * 0.06
    out.append(f'<rect x="{f(cx - height * 0.0035)}" y="{f(base - height - ah)}" width="{f(height * 0.007)}" height="{f(ah)}" fill="{fill}"/>')
    lines = []
    for i in range(12, 150, 2):
        t0, t1 = i / 160, (i + 2) / 160
        lines.append(f"M{f(cx - half(t0))},{f(y_of(t0))} L{f(cx - half(t1) * 0.55)},{f(y_of(t1))}"
                     f"M{f(cx + half(t0))},{f(y_of(t0))} L{f(cx + half(t1) * 0.55)},{f(y_of(t1))}")
    out.append(f'<path d="{"".join(lines)}" stroke="{lattice}" stroke-width="1.6" opacity=".22" fill="none"/>')
    # moonlight catching the moon-side edge: ambient light, never the tower's own illumination
    out.append(f'<path d="{poly(right)}" stroke="{rim}" stroke-width="3" opacity=".42" fill="none" filter="url(#b2)"/>')
    return "".join(out)


def haussmann_row(rng, x0, x1, base, hmin, hmax, fill, window, win_op=0.5):
    out, x = [], x0
    while x < x1:
        bw, h = rng.uniform(140, 260), rng.uniform(hmin, hmax)
        top, roof = base - h, rng.uniform(40, 80)
        out.append(f'<path d="M{f(x)},{f(base)} L{f(x)},{f(top)} L{f(x + 18)},{f(top - roof)} L{f(x + bw - 18)},{f(top - roof)} '
                   f'L{f(x + bw)},{f(top)} L{f(x + bw)},{f(base)} Z" fill="{fill}"/>')
        for _ in range(rng.randint(1, 3)):
            out.append(f'<rect x="{f(x + rng.uniform(30, bw - 40))}" y="{f(top - roof - 34)}" width="{f(rng.uniform(16, 28))}" height="36" fill="{fill}"/>')
        for wy in range(int(top + 30), int(base - 30), 46):
            for wx in range(int(x + 20), int(x + bw - 30), 40):
                if rng.random() < 0.12:
                    out.append(f'<rect x="{wx}" y="{wy}" width="14" height="22" fill="{window}" opacity="{rng.uniform(.3, win_op):.2f}"/>')
        x += bw + rng.uniform(0, 6)
    return "".join(out)


def build() -> str:
    c, rng = C, random.Random(1)
    river = RIVER
    sky = c["sky"]
    defs = COMMON + [
        lin("sky", [(i / (len(sky) - 1), col, 1) for i, col in enumerate(sky)]),
        rad("halo", [(0, c["moon"], 0.35), (0.3, c["halo"], 0.14), (1, c["halo"], 0)]),
        lin("water", [(0, c["water"][0], 1), (1, c["water"][1], 1)]),
        lin("fadeDown", [(0, "#fff", 0.8), (1, "#fff", 0)]),
        f'<mask id="rm"><rect x="0" y="{f(river)}" width="{W}" height="{f(H - river)}" fill="url(#fadeDown)"/></mask>',
    ]
    zd, zb = bar_zones()
    defs.append(zd)
    mx, my, mr = MOON
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>', stars(rng, 380, H * 0.6, [c["moon"], c["halo"]], amax=0.45)]
    for _ in range(10):  # clouds sit behind the moon, so its disc stays clean
        b.append(f'<ellipse cx="{f(rng.uniform(0, W))}" cy="{f(rng.uniform(300, 1100))}" rx="{f(rng.uniform(500, 1300))}" ry="{f(rng.uniform(20, 50))}" '
                 f'fill="{c["cloud"]}" opacity="{rng.uniform(.35, .65):.2f}" filter="url(#b40)"/>')
    b += [f'<circle cx="{mx}" cy="{my}" r="{mr * 5}" fill="url(#halo)"/>', f'<circle cx="{mx}" cy="{my}" r="{mr}" fill="{c["moon"]}" opacity=".96"/>']
    scene = [haussmann_row(rng, -50, W + 50, river, 260, 420, c["build"], c["lumiere"]),
             tower(TOWER_X, TOWER_BASE, TOWER_H, c["tower"], c["moon"], c["bleu"])]
    bx0, bx1, by = 600, 2500, river + 40
    arches = "".join(f'<path d="M{f(bx0 + i * 380)},{f(by + 90)} Q{f(bx0 + i * 380 + 190)},{f(by - 30)} {f(bx0 + (i + 1) * 380)},{f(by + 90)}" '
                     f'stroke="{c["tower"]}" stroke-width="40" fill="none"/>' for i in range(5))
    lamps = "".join(f'<circle cx="{f(bx0 + i * 95)}" cy="{f(by - 30)}" r="5" fill="{c["lumiere"]}"/>'
                    f'<circle cx="{f(bx0 + i * 95)}" cy="{f(by - 30)}" r="22" fill="{c["lumiere"]}" opacity=".25" filter="url(#b8)"/>' for i in range(21))
    b += scene
    b.append(f'<rect x="0" y="{f(river)}" width="{W}" height="{f(H - river)}" fill="url(#water)"/>')
    b.append(f'<g mask="url(#rm)" opacity=".45"><g transform="translate(0,{f(2 * river)}) scale(1,-1)" filter="url(#b8)">{"".join(scene)}</g></g>')
    b.append(f'<rect x="{f(mx - 55)}" y="{f(river + 10)}" width="110" height="{f(H - river)}" fill="{c["moon"]}" opacity=".18" filter="url(#b24)"/>')
    b += [f'<rect x="{bx0 - 40}" y="{f(by - 20)}" width="{bx1 - bx0 + 80}" height="22" fill="{c["tower"]}"/>', arches, lamps, zb, finish()]
    return svg("\n".join(defs), "\n".join(b))
