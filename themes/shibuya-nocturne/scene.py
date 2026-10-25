"""Shibuya Nocturne: a rainy neon street canyon at night.

Tall neon-clad towers frame both edges so every bar sits over detail; a giant-screen tower and the moon
stand in the right third, clear of the Start Page and of a vertical tab bar on the left; the centre is a quiet hazy skyline; the wet
street mirrors it all.
"""
import random

from tools.palette import P
from tools.svg import COMMON, H, W, bar_zones, f, finish, lin, poly, rad, rain, stars, svg

GROUND = H * 0.84
TAB_BAND = 330  # art px kept free of neon so the tab bar stays dark (0..~90 window px at 1920)

# The hero: a corner tower wrapped in a giant glowing screen, in the left third, beside the moon.
SCREEN_BLDG = (3130.0, 560.0, 440.0)  # x, top, width — right third, clear of a left vertical tab bar
SCREEN = (3160.0, 650.0, 380.0, 640.0)  # x, y, w, h
HERO_BOX = (SCREEN_BLDG[0] - 10, SCREEN_BLDG[1] - 60, SCREEN_BLDG[0] + SCREEN_BLDG[2] + 10, SCREEN[1] + SCREEN[3] + 40)
MOON = (2880.0, 560.0)

NEON = ["magenta2", "magenta", "cyan", "blue1", "red", "orange", "blue", "teal"]


def build() -> str:
    rng = random.Random(21)
    ground = GROUND
    defs = COMMON + [
        lin("sky", [(0, "#08090e", 1), (0.35, "#0e0f18", 1), (0.6, "#191b2b", 1), (0.74, "#2a2442", 1), (0.84, "#382347", 1), (1, "#0b0c13", 1)]),
        rad("gM", [(0, P["magenta2"], 0.32), (1, P["magenta2"], 0)]),
        rad("gB", [(0, P["blue"], 0.28), (1, P["blue"], 0)]),
        rad("gC", [(0, P["cyan"], 0.20), (1, P["cyan"], 0)]),
        rad("gO", [(0, P["orange"], 0.24), (1, P["orange"], 0)]),
        rad("moonglow", [(0, P["fg"], 0.30), (0.2, P["blue"], 0.10), (1, P["blue"], 0)]),
        lin("haze", [(0, "#30355a", 0), (0.55, "#30355a", 0.55), (1, "#30355a", 0)]),
        lin("street", [(0, "#0d0e16", 1), (1, "#050609", 1)]),
        lin("rimL", [(0, P["magenta"], 0), (1, P["magenta"], 0.35)], x2="1", y2="0"),
        lin("rimR", [(0, P["cyan"], 0.30), (1, P["cyan"], 0)], x2="1", y2="0"),
        lin("rimUp", [(0, "#fff", 0), (1, "#fff", 1)]),
        '<mask id="rimfade" maskContentUnits="objectBoundingBox"><rect width="1" height="1" fill="url(#rimUp)"/></mask>',
        lin("fadeDown", [(0, "#fff", 0.9), (1, "#fff", 0)]),
        f'<mask id="reflmask"><rect x="0" y="{f(ground)}" width="{W}" height="{f(H - ground)}" fill="url(#fadeDown)"/></mask>',
    ]
    sky, far, mid, near, signs, streaks = [], [], [], [], [], []

    sky.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    sky.append(stars(rng, 200, H * 0.42, [P["fg"], P["fg_dark"], P["cyan"]], amax=0.45))
    mx, my = MOON
    sky.append(f'<circle cx="{f(mx)}" cy="{f(my)}" r="520" fill="url(#moonglow)"/>')
    sky.append(f'<circle cx="{f(mx)}" cy="{f(my)}" r="62" fill="{P["fg"]}" opacity=".95"/>')
    sky.append(f'<circle cx="{f(mx + 22)}" cy="{f(my - 11)}" r="58" fill="#0e0f18" opacity=".6" filter="url(#b4)"/>')
    for _ in range(16):
        cx, cy = rng.uniform(-200, W + 200), rng.uniform(H * 0.08, H * 0.45)
        sky.append(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rng.uniform(500, 1500))}" ry="{f(rng.uniform(16, 46))}" '
                   f'fill="{rng.choice([P["storm"], P["bg_hl"], P["blue7"]])}" opacity="{rng.uniform(.18, .45):.2f}" filter="url(#b40)"/>')
    for x, g, rx, ry in [(0.5, "gM", 1500, 420), (0.32, "gB", 900, 360), (0.7, "gC", 900, 300), (0.16, "gO", 700, 300)]:
        sky.append(f'<ellipse cx="{f(W * x)}" cy="{f(H * 0.72)}" rx="{rx}" ry="{ry}" fill="url(#{g})"/>')

    # far skyline: hazy, tiny window specks
    x = -40
    while x < W + 40:
        bw, top = rng.uniform(40, 150), H * rng.uniform(0.56, 0.68)
        far.append(f'<rect x="{f(x)}" y="{f(top)}" width="{f(bw)}" height="{f(ground - top)}" fill="#262a44"/>')
        for _ in range(int(bw * (ground - top) / 1800)):
            far.append(f'<rect x="{f(rng.uniform(x + 3, x + bw - 5))}" y="{f(rng.uniform(top + 6, ground - 8))}" width="3" height="4" '
                       f'fill="{rng.choice([P["cyan"], P["fg"], P["yellow"]])}" opacity="{rng.uniform(.2, .5):.2f}"/>')
        x += bw + rng.uniform(0, 10)
    far.append(f'<rect x="0" y="{f(H * 0.5)}" width="{W}" height="{f(H * 0.38)}" fill="url(#haze)" opacity=".7"/>')

    # mid layer
    x = -40
    while x < W + 40:
        bw = rng.uniform(90, 230)
        top = H * rng.uniform(0.52, 0.65)
        mid.append(building(rng, x, top, bw, ground, "#171928", 0.7, 0.16))
        if rng.random() < 0.15 and top > H * 0.55 and abs(x + bw / 2 - (SCREEN_BLDG[0] + SCREEN_BLDG[2] / 2)) > 450:
            mid.append(neon_blade(rng, x + bw * rng.uniform(0.2, 0.7), top + rng.uniform(30, 100), 0.7))
        x += bw + rng.uniform(-4, 10)
    mid.append(f'<rect x="0" y="{f(H * 0.6)}" width="{W}" height="{f(H * 0.3)}" fill="url(#haze)" opacity=".35"/>')

    # near flanks: a narrow left flank (the tower needs the room) and a wide right flank
    for side, x0, x1 in (("L", -80, W * 0.27), ("R", SCREEN_BLDG[0] + SCREEN_BLDG[2] + 20, W + 80)):
        x = x0
        placed = []  # sign rects on this flank, so neon never overlaps neon
        while x < x1:
            bw = min(rng.uniform(220, 400), x1 - x)
            if bw < 120:
                break
            edge = 1 - min(1, abs((x + bw / 2) - (0 if side == "L" else W)) / (W * 0.3))
            top = H * (0.24 - 0.30 * edge) + rng.uniform(-40, 40)
            near.append(building(rng, x, top, bw, ground, "#0c0d15", 1.25, 0.20))
            # soft street glow on the corner facing the canyon: blurred, fading upward, no hard edge
            gx = x + bw - 70 if side == "L" else x
            near.append(f'<rect x="{f(gx)}" y="{f(ground - (ground - top) * 0.7)}" width="70" height="{f((ground - top) * 0.7)}" '
                        f'fill="url(#rim{side})" mask="url(#rimfade)" filter="url(#b24)" opacity=".55"/>')
            for _ in range(rng.randint(1, 2)):
                nx = x + bw * rng.uniform(0.15, 0.75)
                ny, nh = max(top, TAB_BAND) + rng.uniform(40, 600), rng.uniform(180, 420) * 1.35
                if _free(placed, (nx - 30, ny - 30, 100, nh + 60)):
                    signs.append(neon_blade(rng, nx, ny, 1.35, nh))
                    streaks.append((nx - 10, 60, signs[-1].split('fill="', 1)[1].split('"', 1)[0]))
            if rng.random() < 0.55:
                bx, by, bww = x + bw * 0.12, max(top, TAB_BAND) + rng.uniform(260, 800), bw * 0.76
                if _free(placed, (bx - 30, by - 30, bww + 60, bww * 0.6 + 60)):
                    signs.append(billboard(rng, bx, by, bww))
            x += bw + rng.uniform(4, 30)

    near.append(screen_tower(rng, ground, streaks))
    scene = "\n".join(far + mid + near + signs)
    street = [
        f'<rect x="0" y="{f(ground)}" width="{W}" height="{f(H - ground)}" fill="url(#street)"/>',
        f'<g mask="url(#reflmask)" opacity=".5"><g transform="translate(0,{f(2 * ground)}) scale(1,-1)" filter="url(#b8)">{"".join(far + mid)}</g></g>',
        f'<rect x="0" y="{f(ground - 3)}" width="{W}" height="8" fill="{P["magenta"]}" opacity=".18" filter="url(#b4)"/>',
    ]
    for sx, sw, sc in streaks:
        street.append(f'<rect x="{f(sx)}" y="{f(ground + 4)}" width="{f(sw)}" height="{f((H - ground) * rng.uniform(.55, .95))}" '
                      f'fill="{sc}" opacity=".30" filter="url(#b14)" mask="url(#reflmask)"/>')
    for _ in range(70):
        sx = rng.uniform(0, W)
        c = rng.choice([P["yellow"], P["red"], P["cyan"], P["fg"], P["magenta2"]])
        street.append(f'<ellipse cx="{f(sx)}" cy="{f(ground + rng.uniform(30, 300))}" rx="{f(rng.uniform(8, 40))}" ry="{f(rng.uniform(2, 5))}" '
                      f'fill="{c}" opacity="{rng.uniform(.12, .4):.2f}" filter="url(#b4)"/>')
    body = "\n".join(sky) + scene + "\n".join(street)
    zd, zb = bar_zones()
    defs.append(zd)
    body += rain(rng, 2000, P["fg_dark"]) + zb + finish()
    return svg("\n".join(defs), body)


def building(rng, x, top, bw, ground, col, sc, lit):
    out = [f'<rect x="{f(x)}" y="{f(top)}" width="{f(bw)}" height="{f(ground - top + 2)}" fill="{col}"/>']
    if rng.random() < 0.3 and top > 0:
        sw, sh = bw * rng.uniform(0.4, 0.7), rng.uniform(20, 80) * sc
        out.append(f'<rect x="{f(x + (bw - sw) / 2)}" y="{f(top - sh)}" width="{f(sw)}" height="{f(sh + 1)}" fill="{col}"/>')
        if rng.random() < 0.6:
            ax, ah = x + bw / 2, rng.uniform(40, 120) * sc
            out.append(f'<line x1="{f(ax)}" y1="{f(top - sh)}" x2="{f(ax)}" y2="{f(top - sh - ah)}" stroke="{col}" stroke-width="{f(3 * sc)}"/>'
                       f'<circle cx="{f(ax)}" cy="{f(top - sh - ah)}" r="{f(3.2 * sc)}" fill="{P["red"]}"/>'
                       f'<circle cx="{f(ax)}" cy="{f(top - sh - ah)}" r="{f(14 * sc)}" fill="{P["red"]}" opacity=".35" filter="url(#b4)"/>')
    # windows lit in floor bands, one colour family per building
    ww, wh, gx, gy = 8 * sc, 11 * sc, 17 * sc, 24 * sc
    cols = max(1, int((bw - 16 * sc) // gx))
    x0 = x + (bw - cols * gx) / 2 + (gx - ww) / 2
    fam = rng.choice([[P["yellow"], P["orange"]], [P["cyan"], P["fg"]], [P["fg"], P["yellow"]], [P["magenta"], P["blue"]]])
    y = max(top, TAB_BAND * 0.6) + 30 * sc  # no lit windows behind the tab bar
    win = []
    while y < ground - 30:
        p = lit * rng.choice([0, 0.3, 1, 1.6, 2.6])
        for c in range(cols):
            if rng.random() < p:
                win.append(f'<rect x="{f(x0 + c * gx)}" y="{f(y)}" width="{f(ww)}" height="{f(wh)}" fill="{rng.choice(fam)}" '
                           f'opacity="{rng.uniform(.35, .8):.2f}"/>')
        y += gy
    out.append(f'<g>{"".join(win)}</g>')
    return "".join(out)


def _free(placed: list, rect) -> bool:
    """Reserve `rect` unless it overlaps one already placed."""
    x, y, w, h = rect
    if any(x < px + pw and px < x + w and y < py + ph and py < y + h for px, py, pw, ph in placed):
        return False
    placed.append(rect)
    return True


def neon_blade(rng, x, y, sc, h=None):
    c = P[rng.choice(NEON)]
    w, h = 30 * sc, h or rng.uniform(180, 420) * sc
    n = int(h // (34 * sc))
    glyphs = []
    for i in range(n):  # abstract glyph strokes, deliberately not real characters
        gy = y + 14 * sc + i * (h - 28 * sc) / n
        gh = (h - 28 * sc) / n * 0.7
        k = rng.random()
        if k < 0.33:
            glyphs.append(f'<rect x="{f(x + w * 0.25)}" y="{f(gy)}" width="{f(w * 0.5)}" height="{f(gh * 0.25)}"/>'
                          f'<rect x="{f(x + w * 0.45)}" y="{f(gy)}" width="{f(w * 0.12)}" height="{f(gh)}"/>')
        elif k < 0.66:
            glyphs.append(f'<rect x="{f(x + w * 0.22)}" y="{f(gy)}" width="{f(w * 0.56)}" height="{f(gh)}" fill="none" stroke="{c}" stroke-width="{f(2.4 * sc)}"/>')
        else:
            glyphs.append(f'<rect x="{f(x + w * 0.25)}" y="{f(gy + gh * 0.4)}" width="{f(w * 0.5)}" height="{f(gh * 0.22)}"/>'
                          f'<rect x="{f(x + w * 0.25)}" y="{f(gy)}" width="{f(w * 0.12)}" height="{f(gh)}"/>')
    return (
        f'<rect x="{f(x - w * 0.8)}" y="{f(y - w * 0.6)}" width="{f(w * 2.6)}" height="{f(h + w * 1.2)}" fill="{c}" opacity=".26" filter="url(#b24)"/>'
        f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(4 * sc)}" fill="#0a0b11" stroke="{c}" stroke-width="{f(3 * sc)}"/>'
        f'<g fill="{c}" opacity=".9">{"".join(glyphs)}</g>'
    )


def billboard(rng, x, y, w):
    c1, c2 = rng.sample([P["blue"], P["magenta"], P["cyan"], P["purple"], P["blue0"], P["magenta2"]], 2)
    h = w * rng.uniform(0.35, 0.6)
    gid = f"bb{rng.randint(0, 10 ** 9)}"
    bars = "".join(
        f'<rect x="{f(x + w * 0.1)}" y="{f(y + h * (0.25 + 0.16 * i))}" width="{f(w * rng.uniform(0.3, 0.75))}" height="{f(h * 0.06)}" rx="3" fill="{P["fg"]}" opacity="{rng.uniform(.25, .55):.2f}"/>'
        for i in range(3)
    )
    return (
        f'<defs>{lin(gid, [(0, c1, .9), (1, c2, .75)], x2="1", y2="1")}</defs>'
        f'<rect x="{f(x - 30)}" y="{f(y - 30)}" width="{f(w + 60)}" height="{f(h + 60)}" fill="{c1}" opacity=".22" filter="url(#b40)"/>'
        f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="6" fill="url(#{gid})" opacity=".5"/>'
        f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="6" fill="none" stroke="{c1}" stroke-width="3" opacity=".9"/>'
        + bars
    )


def screen_tower(rng, ground, streaks) -> str:
    """A dark corner tower wrapped in a giant screen showing an abstract Tokyo Night light show."""
    bx, btop, bw = SCREEN_BLDG
    sx, sy, sw, sh = SCREEN
    out = [
        f'<defs>{lin("scr", [(0, "#101a3a", 1), (0.4, P["blue0"], 1), (0.75, P["purple"], 1), (1, P["magenta2"], 1)], x2="1", y2="1")}'
        f'{rad("scrblob", [(0, P["cyan"], 0.9), (1, P["cyan"], 0)])}'
        f'{rad("scrblob2", [(0, P["magenta2"], 0.8), (1, P["magenta2"], 0)])}'
        f'<clipPath id="scrclip"><rect x="{f(sx)}" y="{f(sy)}" width="{f(sw)}" height="{f(sh)}" rx="6"/></clipPath></defs>',
        # light spill into the rainy air and onto the neighbours
        f'<rect x="{f(sx - 160)}" y="{f(sy - 120)}" width="{f(sw + 320)}" height="{f(sh + 240)}" fill="{P["blue"]}" opacity=".30" filter="url(#b120)"/>',
        f'<rect x="{f(sx - 60)}" y="{f(sy - 40)}" width="{f(sw + 120)}" height="{f(sh + 80)}" fill="{P["magenta"]}" opacity=".18" filter="url(#b70)"/>',
        # the building, with a rooftop frame and aviation light
        f'<rect x="{f(bx)}" y="{f(btop)}" width="{f(bw)}" height="{f(ground - btop + 2)}" fill="#0b0c14"/>',
        f'<rect x="{f(bx + 30)}" y="{f(btop - 46)}" width="{f(bw - 60)}" height="48" fill="#0b0c14"/>',
        f'<line x1="{f(bx + bw * 0.7)}" y1="{f(btop - 46)}" x2="{f(bx + bw * 0.7)}" y2="{f(btop - 150)}" stroke="#0b0c14" stroke-width="5"/>',
        f'<circle cx="{f(bx + bw * 0.7)}" cy="{f(btop - 150)}" r="5" fill="{P["red"]}"/>',
        f'<circle cx="{f(bx + bw * 0.7)}" cy="{f(btop - 150)}" r="20" fill="{P["red"]}" opacity=".4" filter="url(#b8)"/>',
        # the screen: gradient, drifting light blobs, a horizon of bars, fine scanlines
        f'<g clip-path="url(#scrclip)">',
        f'<rect x="{f(sx)}" y="{f(sy)}" width="{f(sw)}" height="{f(sh)}" fill="url(#scr)"/>',
    ]
    for _ in range(7):
        r = rng.uniform(60, 170)
        out.append(f'<circle cx="{f(rng.uniform(sx, sx + sw))}" cy="{f(rng.uniform(sy, sy + sh))}" r="{f(r)}" '
                   f'fill="url(#{rng.choice(["scrblob", "scrblob2"])})" opacity="{rng.uniform(.30, .60):.2f}"/>')
    for k in range(3):  # sweeping light ribbons across the screen
        y0 = sy + sh * (0.15 + 0.22 * k)
        out.append(f'<path d="M{f(sx - 20)},{f(y0 + 80)} C{f(sx + sw * 0.3)},{f(y0 - 60)} {f(sx + sw * 0.7)},{f(y0 + 140)} {f(sx + sw + 20)},{f(y0)}" '
                   f'stroke="{[P["cyan"], P["fg"], P["magenta"]][k]}" stroke-width="{[10, 4, 7][k]}" fill="none" opacity=".75"/>')
    for i in range(14):  # an abstract equaliser of light bars along the lower third
        h = rng.uniform(30, 190)
        out.append(f'<rect x="{f(sx + 18 + i * (sw - 36) / 14)}" y="{f(sy + sh - 40 - h)}" width="{f((sw - 36) / 14 - 6)}" '
                   f'height="{f(h)}" rx="3" fill="{P["cyan"]}" opacity="{rng.uniform(.35, .7):.2f}"/>')
    out.append(''.join(f'<rect x="{f(sx)}" y="{f(sy + k * 6)}" width="{f(sw)}" height="2" fill="#000" opacity=".16"/>'
                       for k in range(int(sh // 6))))
    out.append('</g>')
    out.append(f'<rect x="{f(sx)}" y="{f(sy)}" width="{f(sw)}" height="{f(sh)}" rx="6" fill="none" stroke="{P["fg"]}" stroke-width="3" opacity=".55"/>')
    # quiet lit windows under the screen
    for y in range(int(sy + sh + 50), int(ground - 40), 30):
        for k in range(10):
            if rng.random() < 0.25:
                out.append(f'<rect x="{f(bx + 26 + k * (bw - 52) / 10)}" y="{y}" width="12" height="15" fill="{P["cyan"]}" opacity="{rng.uniform(.3, .6):.2f}"/>')
    streaks.append((sx + 40, sw - 80, P["blue"]))
    return "".join(out)
