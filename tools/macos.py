"""Real macOS input and screen capture, for UI Vivaldi draws natively (menus, shortcuts).

Needs Screen Recording + Accessibility for the terminal app. Every keystroke is guarded: the target
process must be frontmost, otherwise nothing is typed (keys would land in whatever app has focus).
"""
import base64
import io
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageChops

KEY_CODES = {"escape": 53, "return": 36, "down": 125, "up": 126}


class NotFrontmost(RuntimeError):
    pass


class UnsafeCapture(RuntimeError):
    """A screen capture could not be proven to show only the throwaway Vivaldi; it was deleted unseen."""


def match_ratio(capture_png: Path, reference_png: Path, tol: int = 14) -> float:
    """Share of pixels that match the reference (resized to the same size) within `tol` per channel."""
    ref = Image.open(reference_png).convert("RGB")
    cap = Image.open(capture_png).convert("RGB").resize(ref.size)
    diff = ImageChops.difference(cap, ref).convert("L").point(lambda d: 255 if d > tol else 0)
    changed = sum(1 for px in diff.get_flattened_data() if px)
    return 1 - changed / (ref.size[0] * ref.size[1])


def change_boxes(before_png: Path, after_png: Path, tol: int = 14, cell: int = 64) -> list:
    """Coarse grid cells (x0, y0, x1, y1) that changed — coordinates only, never pixels."""
    a = Image.open(before_png).convert("RGB")
    b = Image.open(after_png).convert("RGB").resize(a.size)
    mask = ImageChops.difference(a, b).convert("L").point(lambda d: 255 if d > tol else 0)
    cells = []
    for y in range(0, a.size[1], cell):
        for x in range(0, a.size[0], cell):
            if mask.crop((x, y, x + cell, y + cell)).getbbox():
                cells.append((x, y))
    if not cells:
        return []
    xs, ys = [c[0] for c in cells], [c[1] for c in cells]
    return [(min(xs), min(ys), max(xs) + cell, max(ys) + cell), f"{len(cells)} cells"]


def menu_proof(before_png: Path, after_png: Path, point, cell: int = 64, max_other_cells: int = 2,
               tol: int = 14) -> bool:
    """The changes between two captures are a menu and nothing that could be another window.

    Changed pixels are grouped into connected blocks of `cell`-sized grid squares. The block holding
    `point` is the menu and must exist; every other block must be tiny (a blinking caret, a clock
    digit). Another app's window or a notification is a large block and fails the proof.
    """
    a = Image.open(before_png).convert("RGB")
    b = Image.open(after_png).convert("RGB").resize(a.size)
    mask = ImageChops.difference(a, b).convert("L").point(lambda d: 255 if d > tol else 0)
    cols, rows = (a.size[0] + cell - 1) // cell, (a.size[1] + cell - 1) // cell
    changed = {(cx, cy) for cy in range(rows) for cx in range(cols)
               if mask.crop((cx * cell, cy * cell, (cx + 1) * cell, (cy + 1) * cell)).getbbox()}
    blocks, seen = [], set()
    for start in changed:
        if start in seen:
            continue
        stack, block = [start], set()
        seen.add(start)
        while stack:
            cx, cy = stack.pop()
            block.add((cx, cy))
            for nx in (cx - 1, cx, cx + 1):
                for ny in (cy - 1, cy, cy + 1):
                    if (nx, ny) in changed and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
        blocks.append(block)
    home = (int(point[0]) // cell, int(point[1]) // cell)
    menu = next((blk for blk in blocks if any(abs(cx - home[0]) <= 1 and abs(cy - home[1]) <= 1 for cx, cy in blk)), None)
    if menu is None:
        return False
    return all(len(blk) <= max_other_cells for blk in blocks if blk is not menu)


def change_is_local(before_png: Path, after_png: Path, point, max_share: float, tol: int = 14) -> bool:
    """True when everything that changed sits in one box that starts at `point` (the menu) and is small."""
    a = Image.open(before_png).convert("RGB")
    b = Image.open(after_png).convert("RGB").resize(a.size)
    mask = ImageChops.difference(a, b).convert("L").point(lambda d: 255 if d > tol else 0)
    box = mask.getbbox()
    if box is None:
        return False
    x0, y0, x1, y1 = box
    px, py = point
    near = x0 - 40 <= px <= x1 + 40 and y0 - 40 <= py <= y1 + 40
    return near and (x1 - x0) * (y1 - y0) <= max_share * a.size[0] * a.size[1]


def _osa(script: str) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"osascript failed: {r.stderr.strip()}")
    return r.stdout.strip()


def frontmost_pid() -> int:
    return int(_osa('tell application "System Events" to get unix id of first process whose frontmost is true'))


def activate(pid: int, timeout: float = 3) -> None:
    try:
        _osa(f'tell application "System Events" to set frontmost of (first process whose unix id is {pid}) to true')
    except RuntimeError:
        pass  # not a GUI process; the check below fails safely
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if frontmost_pid() == pid:
            return
        time.sleep(0.1)
    raise NotFrontmost(f"process {pid} is not frontmost; refusing to send keys")


def key(pid: int, key_name: str, modifiers: list[str] | None = None) -> None:
    activate(pid)
    using = f" using {{{', '.join(m + ' down' for m in modifiers)}}}" if modifiers else ""
    action = f"key code {KEY_CODES[key_name]}" if key_name in KEY_CODES else f'keystroke "{key_name}"'
    if frontmost_pid() != pid:  # re-check immediately before typing
        raise NotFrontmost(f"process {pid} lost focus; refusing to send keys")
    _osa(f'tell application "System Events" to {action}{using}')


def capture(path: Path, rect: tuple[int, int, int, int]) -> Path:
    x, y, w, h = rect
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["screencapture", "-x", "-o", f"-R{x},{y},{w},{h}", str(path)], check=True)
    return Path(path)


def window_rect(v) -> tuple[int, int, int, int]:
    w = v.run_ui("new Promise(r => chrome.windows.get(vivaldiWindowId, w => r([w.left, w.top, w.width, w.height])))")
    return tuple(int(n) for n in w)


def can_type() -> bool:
    """True when this process may send keystrokes (Accessibility granted and active)."""
    try:
        return _osa('tell application "System Events" to get UI elements enabled') == "true"
    except RuntimeError:
        return False


def place_on_main_display(v) -> None:
    """Move the throwaway window fully onto the main display (origin 0,0) and prove it is there."""
    v.run_ui("new Promise(r => chrome.windows.update(vivaldiWindowId, {state: 'normal', left: 40, top: 60, width: 1400, height: 900}, () => r(true)))")
    time.sleep(0.8)
    ok = v.run_ui("""(() => screen.availLeft === 0 && screen.availTop >= 0 && screenX >= 0 && screenY >= 0
      && screenX + outerWidth <= screen.width && screenY + outerHeight <= screen.height)()""")
    if not ok:
        raise UnsafeCapture("throwaway Vivaldi is not fully on the main display; refusing to capture")


def _reference(v, path: Path) -> Path:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = v.ui.send("Page.captureScreenshot", {"format": "png"})["data"]
    Image.open(io.BytesIO(base64.b64decode(data))).save(path)
    return path


def capture_window(v, path: Path, margin: int = 0) -> Path:
    """Capture the throwaway Vivaldi's window area — only when proven safe.

    The window is put on the main display and brought to front; the capture must then match the
    browser's own internal screenshot (>= 98%), proving nothing else (the user's apps) is in it.
    Otherwise the file is deleted unseen and UnsafeCapture is raised.
    """
    place_on_main_display(v)
    activate(v.proc.pid)
    x, y, w, h = window_rect(v)
    if frontmost_pid() != v.proc.pid:
        raise NotFrontmost("throwaway Vivaldi lost focus; refusing to capture the screen")
    ref = _reference(v, Path(path).with_suffix(".ref.png"))
    shot = capture(path, (x - margin, y - margin, w + 2 * margin, h + 2 * margin))
    ratio = match_ratio(shot, ref)
    ref.unlink()
    if ratio < 0.98:
        shot.unlink()
        raise UnsafeCapture(f"capture matched the browser's own screenshot only {ratio:.1%}; deleted unseen")
    return shot


def native_menu(v, selector: str, path: Path) -> Path:
    """Right-click `selector` so Vivaldi opens its native menu, and capture it — proven safe.

    A proven baseline is captured first; after the menu opens, every changed pixel must sit in one
    compact box at the click point (the menu). The menu stays open: callers use a fresh Vivaldi per
    menu and quit it afterwards, which closes the menu without keystrokes.
    """
    path = Path(path)
    # An open native menu takes focus and Vivaldi then dims its UI (`isblurred`) — at an unpredictable
    # moment. Hold the class off while capturing so the only difference from the baseline is the menu.
    v.run_ui("""(() => { const b = document.getElementById('browser');
      window.__vdKeepFocus = new MutationObserver(() => b.classList.contains('isblurred') && b.classList.remove('isblurred'));
      window.__vdKeepFocus.observe(b, {attributes: true, attributeFilter: ['class']}); return true; })()""")
    before = capture_window(v, path.with_suffix(".before.png"))
    pt = v.run_ui(f"""(() => {{ const e = document.querySelector({selector!r}); if (!e) return null;
      const r = e.getBoundingClientRect(); return [r.x + Math.min(30, r.width / 2), r.y + r.height / 2]; }})()""")
    if pt is None:
        before.unlink()
        raise RuntimeError(f"nothing matches {selector}")
    for t in ("mousePressed", "mouseReleased"):
        v.ui.send("Input.dispatchMouseEvent", {"type": t, "x": pt[0], "y": pt[1], "button": "right", "clickCount": 1})
    time.sleep(1.0)
    if frontmost_pid() != v.proc.pid:
        before.unlink()
        raise NotFrontmost("throwaway Vivaldi lost focus; refusing to capture the screen")
    x, y, w, h = window_rect(v)
    shot = capture(path, (x, y, w, h))
    scale = Image.open(shot).size[0] / w
    local = menu_proof(before, shot, (pt[0] * scale, pt[1] * scale))
    if not local:
        boxes = change_boxes(before, shot)
        before.unlink()
        shot.unlink()
        raise UnsafeCapture(f"changes outside the menu area (click {[round(c * scale) for c in pt]}, changed regions {boxes}); "
                            "capture deleted unseen")
    before.unlink()
    v.run_ui("window.__vdKeepFocus && window.__vdKeepFocus.disconnect(), true")
    return shot
