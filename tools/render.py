"""Render an SVG to PNG with Playwright's cached chrome-headless-shell."""
import os
import subprocess
import tempfile
from pathlib import Path

PLAYWRIGHT_CACHE = Path.home() / "Library/Caches/ms-playwright"


def find_headless() -> Path:
    env = os.environ.get("VIVALDIDARK_HEADLESS")
    if env and Path(env).is_file():
        return Path(env)
    found = sorted(
        PLAYWRIGHT_CACHE.glob("chromium_headless_shell-*/chrome-headless-shell-mac-*/chrome-headless-shell"),
        key=lambda p: int(p.parts[-3].rsplit("-", 1)[1]))  # newest build number last
    if not found:
        raise FileNotFoundError(
            "chrome-headless-shell not found; run `npx playwright install chromium-headless-shell` "
            "or set VIVALDIDARK_HEADLESS")
    return found[-1]


def render_svg(svg_path: Path, png_path: Path, width: int = 3840, height: int = 2160) -> None:
    binary = find_headless()
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(
            '<!doctype html><html><body style="margin:0;background:#000">'
            f'<img src="{Path(svg_path).resolve().as_uri()}" '
            f'style="display:block;width:{width}px;height:{height}px"></body></html>')
        subprocess.run(
            [str(binary), "--headless", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1", "--allow-file-access-from-files",
             f"--window-size={width},{height}", "--virtual-time-budget=20000",
             f"--screenshot={Path(png_path).resolve()}", page.as_uri()],
            check=True, capture_output=True, timeout=300)
