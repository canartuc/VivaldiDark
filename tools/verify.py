"""Verification matrix: install a theme in a throwaway Vivaldi and check every state.

    uv run python -m tools.verify themes/<slug> [--quick]
"""
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from tools import contrast, macos, package
from tools.svg import H as ART_H, W as ART_W
from tools.vivaldi import Vivaldi

REPO = Path(__file__).resolve().parent.parent
SIZES = [(1280, 800), (1440, 900), (1920, 1080), (2560, 1440), (3440, 1440)]
LAYOUTS = ["tabs-top", "tabs-left"]
STATES = ["startpage", "dark-site", "light-site", "many-tabs", "hover", "unfocused", "settings",
          "bookmarks-panel", "address-dropdown", "find", "downloads-panel"]
QUICK = dict(sizes=[(1920, 1080)], layouts=["tabs-top"], states=["startpage", "many-tabs"])
SCALE = 2  # every screenshot is taken at device scale 2
DIM = "rgb(135, 144, 189)"  # #828bb8 as Vivaldi renders it at Color Contrast 7
BRIGHT = "rgb(255, 255, 255)"
TEXT_FLOOR, UI_FLOOR, BLURRED_FLOOR = 4.5, 3.0, 3.0
# Selected text in a focused address field: Chromium paints the selection from the highlight colour
# at ~50% and keeps the dim text colour (owner-accepted platform limitation). Guard against regressions.
SELECTION_FLOOR = 1.6
# Unchecked checkbox/radio: Vivaldi draws a soft filled shape a theme cannot restyle (its own Dark
# theme scores 1.47:1). Owner-accepted documented floor; checked controls keep the 3:1 rule.
UNCHECKED_FLOOR = 2.2

DARK_PAGE = ("data:text/html,<title>Dark site</title><body style='margin:0;background:%230d1117;color:%23c9d1d9;"
             "font:16px system-ui;padding:40px'><h1>Dark site</h1><p>Body text on a dark page.</p>")
LIGHT_PAGE = ("data:text/html,<title>Light site</title><body style='margin:0;background:%23fff;color:%23111;"
              "font:16px system-ui;padding:40px'><h1>Light site</h1><p>Body text on a light page.</p>")


@dataclass
class Report:
    slug: str
    failures: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.__dict__, indent=1))


# --- geometry (offline) ---------------------------------------------------------------------
def busy_rect_at(busy, size):
    """busy = (dx from window centre, top, width, height) in CSS px -> absolute rect at `size`."""
    dx, top, w, h = busy
    return (size[0] / 2 + dx, top, w, h)


def _overlaps(a, b) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def crop_check(hero_box, busy, sizes=SIZES) -> list[str]:
    """`cover` maps the art onto each window size; the hero must stay visible and clear of the Start Page."""
    failures = []
    hx0, hy0, hx1, hy1 = hero_box
    for w, h in sizes:
        scale = max(w / ART_W, h / ART_H)
        ix0, iy0 = (ART_W - w / scale) / 2, (ART_H - h / scale) / 2
        if hx0 < ix0 or hy0 < iy0 or hx1 > ART_W - ix0 or hy1 > ART_H - iy0:
            failures.append(f"{w}x{h}: hero {hero_box} is cropped by cover")
            continue
        hero_win = ((hx0 - ix0) * scale, (hy0 - iy0) * scale, (hx1 - hx0) * scale, (hy1 - hy0) * scale)
        if _overlaps(hero_win, busy_rect_at(busy, (w, h))):
            failures.append(f"{w}x{h}: hero sits behind the Start Page widgets")
    return failures


# --- pixel analysis -------------------------------------------------------------------------
def _colors(img: Image.Image, box, min_share: float) -> list[tuple]:
    region = img.crop(box)
    counts = Counter(region.get_flattened_data())
    total = sum(counts.values())
    return [c for c, n in counts.most_common() if n / total >= min_share]


def analyze_control(png: Path, rect, scale: float, checked: bool) -> dict:
    """WCAG 1.4.11 for a checkbox/radio/slider: the control must stand out from what surrounds it
    (ident >= 3), and a checked control's mark must stand out from its fill (mark >= 3)."""
    img = Image.open(png).convert("RGB")
    x, y, w, h = (round(v * scale) for v in rect)
    pad = round(3 * scale)
    ring = Counter()
    for box in ((x - pad, y - pad, x + w + pad, y), (x - pad, y + h, x + w + pad, y + h + pad),
                (x - pad, y, x, y + h), (x + w, y, x + w + pad, y + h)):
        ring.update(img.crop(box).get_flattened_data())
    bg = ring.most_common(1)[0][0]
    inner = _colors(img, (x, y, x + w, y + h), 0.03)
    ident = max(contrast.ratio(c, bg) for c in inner)
    result = {"bg": bg, "ident": round(ident, 2)}
    ok = ident >= (UI_FLOOR if checked else UNCHECKED_FLOOR)
    if checked:
        fill = inner[0]
        mark = max(contrast.ratio(c, fill) for c in inner)
        result["mark"] = round(mark, 2)
        ok = ok and mark >= UI_FLOOR
    result["ok"] = ok
    return result


# --- live helpers ---------------------------------------------------------------------------
def _key(v: Vivaldi, key: str, code: str, vk: int, modifiers: int = 0) -> None:
    """Non-character keys (and shortcuts) must be rawKeyDown for Chromium to act on them."""
    for t in ("rawKeyDown", "keyUp"):
        v.ui.send("Input.dispatchKeyEvent", {"type": t, "key": key, "code": code,
                                             "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk, "modifiers": modifiers})


def _click(v: Vivaldi, x: float, y: float, button: str = "left") -> None:
    for t in ("mousePressed", "mouseReleased"):
        v.ui.send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": button, "clickCount": 1})


def _centre(v: Vivaldi, selector: str):
    return v.run_ui(f"""(() => {{ const e = document.querySelector({json.dumps(selector)});
      if (!e) return null; const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }})()""")


def emulate(v: Vivaldi, size) -> None:
    v.ui.send("Emulation.setDeviceMetricsOverride",
              {"width": size[0], "height": size[1], "deviceScaleFactor": SCALE, "mobile": False})
    time.sleep(0.8)


def _hidden_text_shot(v: Vivaldi, path: Path) -> Path:
    """Screenshot with tab titles and address text transparent, to sample what sits behind them."""
    v.run_ui("""(() => { const s = document.createElement('style'); s.id = 'vd-hide';
      s.textContent = '.tab .title, .UrlBar-UrlField, .UrlFragment-Wrapper, .UrlFragment-Wrapper * { color: transparent !important; -webkit-text-fill-color: transparent !important; caret-color: transparent !important; }';
      document.head.append(s); })()""")
    time.sleep(0.2)
    v.screenshot(path)
    v.run_ui("document.getElementById('vd-hide').remove()")
    return path


def check_frame(v: Vivaldi, label: str, shot: Path, floor: float = TEXT_FLOOR, hovered: int | None = None,
                blurred: bool = False, url_floor: float | None = None) -> list[str]:
    failures = []
    m = v.measure()
    if "unified-ui" not in m["classes"] or "unified-ui-transparent" in m["classes"]:
        failures.append(f"{label}: browser is not in opaque unified mode ({m['classes']})")
    hidden = _hidden_text_shot(v, shot.with_name(shot.stem + ".bg.png"))
    for i, tab in enumerate(m["tabs"]):
        if tab["rect"][2] < 4:
            continue  # pinned tabs have no title
        expected = BRIGHT if tab["active"] else DIM
        if blurred:
            # Vivaldi dims everything further when the window loses focus; inactive titles must still not be bright
            if not tab["active"] and contrast.parse(tab["color"]) == contrast.parse(BRIGHT):
                failures.append(f"{label}: inactive tab {i} title is white in an unfocused window")
        elif i != hovered and tab["color"] != expected:
            failures.append(f"{label}: tab {i} title is {tab['color']}, expected {expected}")
        bg = contrast.worst_bg(hidden, tab["rect"], SCALE, tab["color"], text_png=shot)
        r = contrast.ratio(tab["color"], bg)
        if r < floor:
            failures.append(f"{label}: tab {i} title contrast {r:.2f} < {floor} on {bg}")
    # The visible URL is drawn by .UrlFragment-Wrapper spans (each with its own colour) over the input.
    frags = v.run_ui("""(() => {
      const spans = [...document.querySelectorAll('.UrlFragment-Wrapper span')].filter(s => s.textContent.trim());
      const els = spans.length ? spans : [document.querySelector('.UrlBar-UrlField')].filter(Boolean);
      return els.map(e => { const rg = document.createRange(); rg.selectNodeContents(e);
        const r = (e.tagName === 'INPUT' ? e : rg).getBoundingClientRect();
        return {rect: [r.x, r.y, r.width, r.height], color: getComputedStyle(e).color, text: e.textContent || e.value}; });
    })()""")
    for frag in frags or []:
        if frag["rect"][2] < 2:
            continue
        bg = contrast.worst_bg(hidden, frag["rect"], SCALE, frag["color"], text_png=shot)
        r = contrast.ratio(frag["color"], bg)
        need = url_floor if url_floor is not None else floor
        if r < need:
            failures.append(f"{label}: address text '{frag['text'][:30]}' contrast {r:.2f} < {need} on {bg}")
    return failures


# --- states ---------------------------------------------------------------------------------
def _activate(v: Vivaldi, *matches: str) -> None:
    """Activate the first tab whose title or URL contains any of `matches` (case-insensitive)."""
    match = matches[0]
    ok = v.run_ui(f"""new Promise(r => chrome.tabs.query({{}}, ts => {{ const ms = {json.dumps([m.lower() for m in matches])};
      const hit = t => ms.some(m => (t.title || '').toLowerCase().includes(m) || decodeURIComponent(t.url || t.pendingUrl || '').toLowerCase().includes(m));
      const t = ts.find(hit);
      t ? chrome.tabs.update(t.id, {{active: true}}, () => r(true)) : r(false); }}))""")
    if not ok:
        raise RuntimeError(f"no tab matches {match!r}")
    time.sleep(0.6)


def _close_dropdown(v: Vivaldi) -> None:
    for _ in range(10):
        if v.run_ui("!document.querySelector('.OmniDropdown')"):
            return
        _key(v, "Escape", "Escape", 27)
        v.run_ui("document.activeElement && document.activeElement.blur && document.activeElement.blur(), true")
        time.sleep(0.3)
    raise RuntimeError("address dropdown would not close")


def _reset(v: Vivaldi) -> None:
    _key(v, "Escape", "Escape", 27)
    v.run_ui("document.getElementById('browser').classList.remove('isblurred')")
    v.ui.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 5, "y": 400})
    _activate(v, "Start Page", "startpage")
    _close_dropdown(v)


def _open_panel(v: Vivaldi, name: str) -> None:
    pt = _centre(v, f"button[data-name={name}]")
    if pt:
        _click(v, *pt)
        time.sleep(0.8)


def _close_panel(v: Vivaldi, name: str) -> None:
    if v.run_ui("!!document.querySelector('#panels-container.switcher, #panels-container:not(.icons)') && "
                "!!document.querySelector('.panel-group .panel')"):
        _open_panel(v, name)


def state_setup(v: Vivaldi, state: str) -> dict:
    """Bring the browser into `state`; returns check options."""
    if state == "startpage":
        _activate(v, "Start Page", "startpage")
    elif state == "dark-site":
        _activate(v, "Dark site")
    elif state == "light-site":
        _activate(v, "Light site")
    elif state == "many-tabs":
        _activate(v, "Dark site")
    elif state == "hover":
        rect = v.run_ui("(() => { const t = [...document.querySelectorAll('.tab-position .tab')].find(t => !t.classList.contains('active') && t.querySelector('.title') && t.querySelector('.title').getBoundingClientRect().width > 20); const r = t.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
        v.ui.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": rect[0], "y": rect[1]})
        time.sleep(0.5)
        idx = v.run_ui("[...document.querySelectorAll('.tab-position .tab')].findIndex(t => t.matches(':hover'))")
        return {"hovered": idx}
    elif state == "unfocused":
        v.run_ui("document.getElementById('browser').classList.add('isblurred')")
        time.sleep(0.4)
        return {"floor": BLURRED_FLOOR, "blurred": True}
    elif state == "settings":
        _activate(v, "Settings")
    elif state == "bookmarks-panel":
        _open_panel(v, "PanelBookmarks")
    elif state == "downloads-panel":
        _open_panel(v, "PanelDownloads")
    elif state == "address-dropdown":
        pt = _centre(v, ".UrlBar-UrlField")
        _click(v, *pt)
        v.ui.send("Input.insertText", {"text": "exa"})
        time.sleep(1.0)
        return {"url_floor": SELECTION_FLOOR}
    elif state == "find":
        _activate(v, "Light site")
        macos.key(v.proc.pid, "f", ["command"])  # Vivaldi's shortcuts only react to real keystrokes
        v._wait_js("[...document.querySelectorAll('.find-in-page-wrapper')].some(e => e.getBoundingClientRect().height > 10)", 5)
    return {}


def _clear_typed_url(v: Vivaldi) -> None:
    """Vivaldi keeps half-typed address text per tab; erase what the address-dropdown state typed."""
    pt = _centre(v, ".UrlBar-UrlField")
    if pt:
        _click(v, *pt)
        v.run_ui("document.querySelector('.UrlBar-UrlField').select(), true")
        _key(v, "Backspace", "Backspace", 8)
        time.sleep(0.2)


def state_teardown(v: Vivaldi, state: str) -> None:
    if state == "address-dropdown":
        _clear_typed_url(v)
    if state == "find":
        macos.key(v.proc.pid, "escape")
        time.sleep(0.4)
    if state == "bookmarks-panel":
        _open_panel(v, "PanelBookmarks")
    elif state == "downloads-panel":
        _open_panel(v, "PanelDownloads")
    _reset(v)


def prepare_tabs(v: Vivaldi) -> None:
    pages = [DARK_PAGE, LIGHT_PAGE, "vivaldi://settings/appearance/"] + [
        DARK_PAGE.replace("Dark%20site", f"Tab%20{i}").replace(">Dark site<", f">Tab {i}<") for i in range(1, 11)]
    v.open_tabs(pages)
    v.run_ui("""new Promise(r => chrome.tabs.query({}, ts => {
      const pin = ts.filter(t => (t.url || t.pendingUrl || '').includes('Tab%201')).slice(0, 2);
      let n = pin.length; if (!n) r(); pin.forEach(t => chrome.tabs.update(t.id, {pinned: true}, () => --n || r())); }))""")
    time.sleep(1.5)


def set_layout(v: Vivaldi, layout: str) -> None:
    v.set_pref("vivaldi.tabs.bar.position", "left" if layout == "tabs-left" else "top")
    time.sleep(1.0)


# --- audits ---------------------------------------------------------------------------------
# Several Settings tabs can exist; only the visible one is drawn, so every query is scoped to it.
SETTINGS_ROOT = "[...document.querySelectorAll('.vivaldi-settings')].find(e => e.checkVisibility())"

CONTROLS_JS = """(() => {
  const root = """ + SETTINGS_ROOT + """;
  // visible = fully inside the Settings scroll area (not under the status bar or the sticky header)
  const area = root.querySelector('.settings-content').getBoundingClientRect();
  const vis = r => r.width > 0 && r.height > 0 && r.y >= area.y && r.bottom <= area.bottom && r.x >= area.x && r.right <= area.right;
  const out = [];
  root.querySelectorAll('input[type=checkbox], input[type=radio], input[type=range]').forEach(e => {
    const r = e.getBoundingClientRect(); if (!vis(r)) return;
    out.push({kind: e.type === 'range' ? 'slider' : e.type, checked: !!e.checked, disabled: e.matches(':disabled'), rect: [r.x, r.y, r.width, r.height],
              label: (e.closest('label') || e.parentElement).innerText.trim().slice(0, 60)});
  });
  root.querySelectorAll('label > span, .setting-group h2, .setting-group h3, .setting-single > p, .selectbox, input[type=text], input[type=number], input[type=search]').forEach(e => {
    const r = e.getBoundingClientRect(); if (!vis(r) || !e.innerText && e.tagName !== 'INPUT') return;
    let p = e, bg = 'rgba(0, 0, 0, 0)';
    while (p && (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent')) { bg = getComputedStyle(p).backgroundColor; p = p.parentElement; }
    out.push({kind: 'text', checked: false, rect: [r.x, r.y, r.width, r.height], color: getComputedStyle(e).color, bgColor: bg,
              label: (e.innerText || e.value || '').trim().slice(0, 60)});
  });
  return out;
})()"""


def _scroller(v: Vivaldi) -> None:
    v.run_ui(f"window.__vdScroll = ({SETTINGS_ROOT}).querySelector('.settings-content'), true")


def section_selector(section: str) -> str:
    return f'.vivaldi-settings .tree-item[data-id="{section}"] .tree-row'


def _section_centre(v: Vivaldi, section: str):
    return v.run_ui(f"""(() => {{ const e = ({SETTINGS_ROOT}).querySelector({json.dumps(section_selector(section).replace('.vivaldi-settings ', ''))});
      if (!e) return null; const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }})()""")


def audit_controls(v: Vivaldi, sections: list[str] | None = None, shots: Path | None = None) -> list[dict]:
    """Every checkbox, radio, slider and text label in each Settings section, scrolled through fully."""
    shots = Path(shots or REPO / "build" / "verify" / "controls")
    shots.mkdir(parents=True, exist_ok=True)
    v.open_tabs(["vivaldi://settings/general/"])
    _activate(v, "Settings")
    v._wait_js(f"!!(({SETTINGS_ROOT}) || {{querySelector: () => null}}).querySelector('.tree-item')", 15)
    sections = sections or v.run_ui(f"[...({SETTINGS_ROOT}).querySelectorAll('.tree-item[aria-level=\"1\"]')].map(e => e.dataset.id).filter(id => id !== 'all')")
    results, seen = [], set()
    for sec in sections:
        pt = _section_centre(v, sec)
        _click(v, *pt)
        time.sleep(1.2)
        _scroller(v)
        page = 0
        while True:
            shot = v.screenshot(shots / f"{sec}-{page:02d}.png")
            for c in v.run_ui(CONTROLS_JS):
                top = v.run_ui("window.__vdScroll ? window.__vdScroll.scrollTop : 0")
                key = (sec, c["kind"], c["label"], round(c["rect"][1] + top))
                if key in seen:
                    continue
                seen.add(key)
                if c["kind"] == "text":
                    r = contrast.ratio(c["color"], c["bgColor"])
                    res = {"ident": round(r, 2), "ok": r >= TEXT_FLOOR}
                elif c.get("disabled"):
                    # deliberately dimmed by Vivaldi to say "unavailable"; WCAG exempts disabled controls
                    res = {**analyze_control(shot, c["rect"], SCALE, c["checked"]), "ok": True}
                else:
                    res = analyze_control(shot, c["rect"], SCALE, c["checked"])
                results.append({**c, **res, "section": sec, "shot": shot.name})
            more = v.run_ui("""(() => { const s = window.__vdScroll; if (!s) return false;
              const before = s.scrollTop; s.scrollTop += s.clientHeight * 0.85; return s.scrollTop > before; })()""")
            if not more:
                break
            time.sleep(0.4)
            page += 1
    return results


MENU_ITEMS_JS = """(sel => {
  const m = document.querySelector(sel); if (!m) return [];
  const items = [...m.querySelectorAll('button, [role=menuitem], [role=option], li, .item, .OmniDropdown-Item, a')]
    .filter(e => { const r = e.getBoundingClientRect(); return r.width > 10 && r.height > 8 && e.innerText.trim(); });
  return items.map(e => { let p = e, bg = 'rgba(0, 0, 0, 0)';
    while (p && (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent')) { bg = getComputedStyle(p).backgroundColor; p = p.parentElement; }
    const r = e.getBoundingClientRect();
    return {text: e.innerText.trim().split('\\n')[0].slice(0, 50), color: getComputedStyle(e).color, bg, rect: [r.x, r.y, r.width, r.height],
            disabled: e.disabled || e.getAttribute('aria-disabled') === 'true'}; });
})"""

MENUS = {  # name -> (open action, menu root selector)
    "workspaces": ("button[data-name=WorkspaceButton]", ".ToolbarButtonPopup-DefaultStyles"),
    "address-dropdown": (".UrlBar-UrlField", ".OmniDropdown"),
}


def audit_menus(v: Vivaldi, shots: Path | None = None) -> list[dict]:
    """Popup menus Vivaldi draws itself: every item at rest, plus the first item hovered."""
    shots = Path(shots or REPO / "build" / "verify" / "menus")
    shots.mkdir(parents=True, exist_ok=True)
    out = []
    for name, (opener, root) in MENUS.items():
        pt = _centre(v, opener)
        if not pt:
            out.append({"menu": name, "items": [], "error": f"opener {opener} not found"})
            continue
        _click(v, *pt)
        if name == "address-dropdown":
            v.ui.send("Input.insertText", {"text": "vivaldi"})
        time.sleep(1.0)
        shot = v.screenshot(shots / f"{name}.png")
        items = []
        for it in v.run_ui(f"({MENU_ITEMS_JS})({json.dumps(root)})"):
            r = contrast.ratio(it["color"], it["bg"])
            items.append({**it, "ratio": round(r, 2), "ok": it["disabled"] or r >= TEXT_FLOOR})
        if items:
            x, y, w, h = items[0]["rect"]
            v.ui.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x + w / 2, "y": y + h / 2})
            time.sleep(0.4)
            v.screenshot(shots / f"{name}-hover.png")
            hov = v.run_ui(f"({MENU_ITEMS_JS})({json.dumps(root)})")[0]
            r = contrast.ratio(hov["color"], hov["bg"])
            items.append({**hov, "text": hov["text"] + " (hover)", "ratio": round(r, 2), "ok": r >= TEXT_FLOOR})
        out.append({"menu": name, "items": items, "shot": shot.name})
        _key(v, "Escape", "Escape", 27)
        _key(v, "Escape", "Escape", 27)
        time.sleep(0.4)
    return out


NATIVE_MENUS = {  # name -> element to right-click
    "tab": ".tab-position .tab:not(.active)",
    "page": ".webpageview.active",
    "address": ".UrlBar-UrlField",
    "panel-button": "button[data-name=PanelBookmarks]",
}


def native_menus(zip_path: Path, shots: Path) -> tuple[list[Path], list[str]]:
    """Capture each native macOS menu over the theme, one fresh Vivaldi per attempt (quitting closes it).

    An unprovable capture (the screen changed meanwhile) is deleted unseen and retried once.
    """
    captured, pending = [], []
    for name, selector in NATIVE_MENUS.items():
        error = None
        for _ in range(2):
            with Vivaldi() as v:
                v.install_theme(zip_path)
                prepare_tabs(v)
                if name == "page":
                    _activate(v, "Light site")
                else:
                    _activate(v, "Start Page", "startpage")
                try:
                    captured.append(macos.native_menu(v, selector, Path(shots) / f"native-{name}.png"))
                    error = None
                    break
                except (macos.UnsafeCapture, macos.NotFrontmost) as e:
                    error = e
        if error:
            pending.append(f"native menu {name}: {error}")
    return captured, pending


# --- runner ---------------------------------------------------------------------------------
def verify_theme(theme_dir: Path, quick: bool = False, out: Path | None = None,
                 states: list[str] | None = None) -> Report:
    theme_dir = Path(theme_dir)
    cfg = package.load_config(theme_dir)
    out = Path(out or REPO / "build" / "verify" / cfg.slug)
    zip_path = package.build_theme(theme_dir, REPO / "icons")
    report = Report(cfg.slug)
    plan = dict(QUICK if quick else dict(sizes=SIZES, layouts=LAYOUTS, states=STATES))
    if states:
        plan["states"] = states
    with Vivaldi() as v:
        v.install_theme(zip_path)
        prepare_tabs(v)
        for layout in plan["layouts"]:
            set_layout(v, layout)
            for size in plan["sizes"]:
                emulate(v, size)
                for state in plan["states"]:
                    shot = out / layout / f"{size[0]}x{size[1]}" / f"{state}.png"
                    try:
                        opts = state_setup(v, state)
                    except macos.NotFrontmost as e:  # the user took focus; never type blind
                        report.pending.append(f"{layout} {size[0]}x{size[1]} {state}: {e}")
                        _reset(v)
                        continue
                    v.screenshot(shot)
                    fails = check_frame(v, f"{layout} {size[0]}x{size[1]} {state}", shot,
                                        opts.get("floor", TEXT_FLOOR), opts.get("hovered"), opts.get("blurred", False),
                                        opts.get("url_floor"))
                    report.failures += fails
                    report.checks.append({"layout": layout, "size": size, "state": state, "failures": fails})
                    try:
                        state_teardown(v, state)
                    except macos.NotFrontmost as e:
                        report.pending.append(f"{layout} {size[0]}x{size[1]} {state} teardown: {e}")
                        _reset(v)
        out.mkdir(parents=True, exist_ok=True)
        report.save(out / "report.json")  # keep the matrix results whatever happens next
        if not quick:
            set_layout(v, "tabs-top")
            emulate(v, (1920, 1080))
            for c in audit_controls(v, shots=out / "controls"):
                if not c["ok"]:
                    report.failures.append(f"controls {c['section']}: {c['kind']} '{c['label']}' contrast {c['ident']}"
                                           + (f" / mark {c.get('mark')}" if c["kind"] != "text" else ""))
            for m in audit_menus(v, shots=out / "menus"):
                if m.get("error"):
                    report.failures.append(f"menu {m['menu']}: {m['error']}")
                for it in m["items"]:
                    if not it["ok"]:
                        report.failures.append(f"menu {m['menu']}: '{it['text']}' contrast {it['ratio']}")
    if not quick:
        _, pending = native_menus(zip_path, out / "native")
        report.pending += pending
    if not quick:
        scene = package.load_scene(theme_dir)
        report.failures += crop_check(scene.HERO_BOX, json.loads((REPO / "tools" / "startpage_busy.json").read_text()))
    out.mkdir(parents=True, exist_ok=True)
    report.save(out / "report.json")
    return report


if __name__ == "__main__":
    rep = verify_theme(Path(sys.argv[1]), quick="--quick" in sys.argv)
    print("\n".join(rep.failures) or "OK", *(f"PENDING: {p}" for p in rep.pending), sep="\n")
    sys.exit(1 if rep.failures else 0)
