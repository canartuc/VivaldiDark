"""Real OS input/capture for native UI (needs Screen Recording + Accessibility for the terminal)."""
import subprocess

import pytest
from PIL import Image, ImageChops

from tools import macos

pytestmark = pytest.mark.vivaldi


def test_refuses_to_type_into_another_app():
    other = subprocess.Popen(["sleep", "30"])  # a pid that can never be frontmost
    try:
        with pytest.raises(macos.NotFrontmost):
            macos.key(other.pid, "f", ["command"])
    finally:
        other.kill()


class _NotFront:
    """Stands in for a Vivaldi whose window is not in front (a non-GUI process)."""
    def __init__(self, pid):
        self.proc = type("P", (), {"pid": pid})()

    def run_ui(self, js):
        return [0, 0, 300, 200]


def test_capture_refuses_when_target_not_frontmost(tmp_path):
    other = subprocess.Popen(["sleep", "30"])
    try:
        with pytest.raises(macos.NotFrontmost):
            macos.capture_window(_NotFront(other.pid), tmp_path / "x.png")
        assert not (tmp_path / "x.png").exists()
    finally:
        other.kill()


def test_capture_window_shows_only_the_throwaway_vivaldi(tmp_path):
    from tools.vivaldi import Vivaldi
    with Vivaldi() as v:
        png = macos.capture_window(v, tmp_path / "w.png")
        assert macos.frontmost_pid() == v.proc.pid
    assert Image.open(png).size[0] >= 300


@pytest.mark.skipif(not macos.can_type(), reason="keystrokes not permitted for this terminal session yet")
def test_real_cmd_f_opens_find_bar(tmp_path):
    from tools import verify
    from tools.vivaldi import Vivaldi
    with Vivaldi() as v:
        verify.prepare_tabs(v)
        verify._activate(v, "Light site")
        macos.key(v.proc.pid, "f", ["command"])
        v._wait_js("[...document.querySelectorAll('.find-in-page-wrapper')].some(e => e.getBoundingClientRect().height > 10)", 5)


def test_native_tab_menu_is_captured(tmp_path):
    from tools import verify
    from tools.vivaldi import Vivaldi
    with Vivaldi() as v:
        verify.prepare_tabs(v)
        shot = macos.native_menu(v, ".tab-position .tab:not(.active)", tmp_path / "menu.png")
    assert shot.exists()


def _img(tmp_path, name, colour, box=None, box_colour=(255, 0, 0)):
    im = Image.new("RGB", (200, 100), colour)
    if box:
        for x in range(box[0], box[2]):
            for y in range(box[1], box[3]):
                im.putpixel((x, y), box_colour)
    p = tmp_path / name
    im.save(p)
    return p


def test_match_ratio_identical_and_overlaid(tmp_path):
    ref = _img(tmp_path, "ref.png", (20, 20, 30))
    assert macos.match_ratio(_img(tmp_path, "same.png", (20, 20, 30)), ref) == 1.0
    covered = _img(tmp_path, "cov.png", (20, 20, 30), (0, 0, 100, 100))  # half covered by "another window"
    assert macos.match_ratio(covered, ref) == pytest.approx(0.5, abs=0.01)


def test_change_is_local_only_near_point(tmp_path):
    before = _img(tmp_path, "b.png", (20, 20, 30))
    menu = _img(tmp_path, "m.png", (20, 20, 30), (60, 20, 120, 90))
    assert macos.change_is_local(before, menu, point=(62, 22), max_share=0.5)
    elsewhere = _img(tmp_path, "e.png", (20, 20, 30), (150, 80, 200, 100))
    assert not macos.change_is_local(before, elsewhere, point=(10, 10), max_share=0.5)


def test_native_menu_capture_is_proven(tmp_path):
    from tools import verify
    from tools.vivaldi import Vivaldi
    with Vivaldi() as v:
        verify.prepare_tabs(v)
        shot = macos.native_menu(v, ".tab-position .tab:not(.active)", tmp_path / "menu.png")
    assert shot.exists()


def test_capture_window_creates_missing_folders(tmp_path):
    from tools.vivaldi import Vivaldi
    with Vivaldi() as v:
        png = macos.capture_window(v, tmp_path / "new" / "nested" / "w.png")
    assert png.exists()


def _scene(tmp_path, name, boxes):
    im = Image.new("RGB", (1280, 768), (20, 20, 30))
    for (x0, y0, x1, y1) in boxes:
        for x in range(x0, x1):
            for y in range(y0, y1):
                im.putpixel((x, y), (200, 200, 220))
    p = tmp_path / name
    im.save(p)
    return p


def test_menu_proof_tolerates_caret_and_clock_ticks(tmp_path):
    before = _scene(tmp_path, "b.png", [])
    # menu at the click + a 2px caret blink + a clock digit change far away
    after = _scene(tmp_path, "a.png", [(300, 100, 700, 600), (900, 40, 902, 60), (1200, 740, 1230, 760)])
    assert macos.menu_proof(before, after, point=(310, 110))


def test_menu_proof_rejects_a_notification_banner(tmp_path):
    before = _scene(tmp_path, "b.png", [])
    after = _scene(tmp_path, "a.png", [(300, 100, 700, 600), (880, 20, 1270, 160)])  # a banner-sized block
    assert not macos.menu_proof(before, after, point=(310, 110))


def test_menu_proof_rejects_no_menu(tmp_path):
    before = _scene(tmp_path, "b.png", [])
    after = _scene(tmp_path, "a.png", [(900, 40, 902, 60)])
    assert not macos.menu_proof(before, after, point=(310, 110))
