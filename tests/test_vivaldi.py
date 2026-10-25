"""Integration tests: drive a throwaway Vivaldi profile over CDP."""
import json
import shutil
from pathlib import Path

import pytest

from tools import package
from tools.vivaldi import Vivaldi

pytestmark = pytest.mark.vivaldi

DIM = "rgb(130, 139, 184)"  # #828bb8
BRIGHT = "rgb(255, 255, 255)"
URLS = ["https://example.com/", "https://example.org/", "https://example.net/"]

SCENE = '''
HERO_BOX = (1000.0, 500.0, 1400.0, 900.0)

def build():
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160">'
            '<defs><linearGradient id="g" x2="1" y2="1"><stop offset="0" stop-color="#0c0e14"/>'
            '<stop offset="1" stop-color="#1f2335"/></linearGradient></defs>'
            '<rect width="3840" height="2160" fill="url(#g)"/></svg>')
'''


def fixture_theme(tmp_path: Path, alpha: float = 0.5, check: bool = True) -> Path:
    """Build a dark gradient test theme; check=False bypasses validation (for pinning Vivaldi behaviour)."""
    theme = tmp_path / "themes" / f"fixture-{str(alpha).replace('.', '')}"
    theme.mkdir(parents=True)
    (theme / "scene.py").write_text(SCENE)
    (theme / "theme.json").write_text(json.dumps(dict(
        slug=theme.name, name=f"Fixture {alpha}", id=f"00000000-0000-4000-8000-{int(alpha * 100):012d}",
        highlight="#7aa2f7", radius=8, alpha=alpha, blur=4, webp_quality=90)))
    icons = tmp_path / "icons"
    icons.mkdir(exist_ok=True)
    if check:
        return package.build_theme(theme, icons)
    original = package.validate
    package.validate = lambda *a: []
    try:
        return package.build_theme(theme, icons)
    finally:
        package.validate = original


@pytest.fixture(scope="module")
def browser():
    with Vivaldi() as v:
        v.open_tabs(URLS)
        yield v


def test_install_sets_unified_and_colors(browser, tmp_path):
    browser.install_theme(fixture_theme(tmp_path, 0.5))
    m = browser.measure()
    assert "unified-ui" in m["classes"]
    assert "unified-ui-transparent" not in m["classes"]
    inactive = [t["color"] for t in m["tabs"] if not t["active"]]
    active = [t["color"] for t in m["tabs"] if t["active"]]
    assert len(inactive) >= 3 and set(inactive) == {DIM}
    assert active == [BRIGHT]


def test_alpha_below_half_turns_tabs_white(browser, tmp_path):
    browser.install_theme(fixture_theme(tmp_path, 0.45, check=False))
    m = browser.measure()
    assert "unified-ui-transparent" in m["classes"]
    assert {t["color"] for t in m["tabs"]} == {BRIGHT}


def test_reimport_replaces(browser, tmp_path):
    zp = fixture_theme(tmp_path, 0.55)
    tid = browser.install_theme(zp)
    browser.install_theme(zp)
    users = browser.pref("vivaldi.themes.user")
    assert [t["id"] for t in users].count(tid) == 1
    assert browser.pref("vivaldi.themes.preview") == []


def test_replaceable_buttons_nonempty(browser):
    ids = browser.replaceable_buttons()
    assert {"Back", "Reload", "PanelBookmarks"} <= set(ids)
    assert len(ids) == len(set(ids))


def test_export_keys_match_schema(browser, tmp_path):
    browser.install_theme(fixture_theme(tmp_path, 0.6))
    exported = browser.export_current_settings()
    from tools.settings_schema import EXPORT_KEYS
    assert set(exported) == EXPORT_KEYS


def test_startpage_busy_rect_is_central(browser):
    browser.ui.send("Emulation.setDeviceMetricsOverride", {"width": 1920, "height": 1080, "deviceScaleFactor": 2, "mobile": False})
    try:
        browser.run_ui("new Promise(r => chrome.tabs.query({}, ts => chrome.tabs.update(ts.find(t => (t.url || '').includes('startpage')).id, {active: true}, r)))")
        x, y, w, h = browser.startpage_busy_rect()
    finally:
        browser.ui.send("Emulation.clearDeviceMetricsOverride")
    assert 300 < w < 1600 and 200 < h < 1000
    assert abs((x + w / 2) - 1920 / 2) < 120  # centred in the window, give or take the side panel
    assert 40 < y < 400
