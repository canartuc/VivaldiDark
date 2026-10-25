from pathlib import Path

import pytest
from PIL import Image

from tools import contrast
from tools.verify import busy_rect_at, crop_check


def test_ratio_known_values():
    assert contrast.ratio("#828bb8", (26, 27, 38)) == pytest.approx(5.16, abs=0.02)
    assert contrast.ratio("#787c99", (26, 27, 38)) == pytest.approx(4.18, abs=0.02)
    assert contrast.ratio("rgb(255, 255, 255)", (0, 0, 0)) == pytest.approx(21.0)


def test_parse_color_forms():
    assert contrast.parse("#7aa2f7") == (122, 162, 247)
    assert contrast.parse("rgb(130, 139, 184)") == (130, 139, 184)
    assert contrast.parse("rgba(130, 139, 184, 0.5)") == (130, 139, 184)
    assert contrast.parse("rgb(255 255 255)") == (255, 255, 255)


def test_worst_bg_picks_lowest_contrast_pixel(tmp_path: Path):
    img = Image.new("RGB", (100, 50), (10, 10, 10))
    img.putpixel((60, 20), (90, 90, 90))  # the lightest pixel: worst for light text
    png = tmp_path / "s.png"
    img.save(png)
    # rect is in CSS px; screenshot is at scale 2, so CSS (25..35, 5..15) covers pixel (60, 20)
    assert contrast.worst_bg(png, [25, 5, 10, 10], 2, "#ffffff") == (90, 90, 90)
    # for dark text the worst background is the darkest one
    assert contrast.worst_bg(png, [25, 5, 10, 10], 2, "#000000") == (10, 10, 10)


HERO_CENTRE = (1700.0, 900.0, 2140.0, 1300.0)


def test_crop_check_passes_centred_hero():
    busy = (600, 100, 200, 150)  # small box right of the hero
    assert crop_check(HERO_CENTRE, busy, [(1920, 1080), (3440, 1440), (1280, 800)]) == []


def test_crop_check_flags_hero_out_of_crop():
    edge_hero = (1700.0, 20.0, 2140.0, 300.0)  # near the top: 21:9 cover trims top and bottom
    fails = crop_check(edge_hero, (0, 0, 0, 0), [(3440, 1440)])
    assert fails and "3440x1440" in fails[0]


def test_crop_check_flags_hero_behind_busy_rect():
    busy = (-400, 200, 800, 700)  # centred 800x700 block from y=200
    fails = crop_check(HERO_CENTRE, busy, [(1920, 1080)])
    assert fails and "Start Page" in fails[0]


def test_busy_rect_is_centre_anchored():
    # busy rect is measured as (dx from centre, top, width, height) in CSS px
    assert busy_rect_at((-400, 200, 800, 700), (1920, 1080)) == (560, 200, 800, 700)
    assert busy_rect_at((-400, 200, 800, 700), (2560, 1440)) == (880, 200, 800, 700)


def _control_png(tmp_path, fill, mark, bg=(26, 27, 38)) -> Path:
    """A 16x16 CSS-px control drawn at scale 2 on a 40x40 CSS-px background."""
    img = Image.new("RGB", (80, 80), bg)
    for x in range(24, 56):
        for y in range(24, 56):
            img.putpixel((x, y), fill)
    for x in range(32, 48):  # a thick 'mark' bar in the middle
        for y in range(36, 44):
            img.putpixel((x, y), mark)
    png = tmp_path / "c.png"
    img.save(png)
    return png


def test_analyze_control_passes_clear_checked_box(tmp_path):
    from tools.verify import analyze_control
    r = analyze_control(_control_png(tmp_path, (122, 162, 247), (0, 0, 0)), [12, 12, 16, 16], 2, checked=True)
    assert r["ok"] and r["ident"] >= 3 and r["mark"] >= 3


def test_analyze_control_fails_invisible_mark(tmp_path):
    from tools.verify import analyze_control
    r = analyze_control(_control_png(tmp_path, (122, 162, 247), (110, 150, 235)), [12, 12, 16, 16], 2, checked=True)
    assert not r["ok"]


def test_analyze_control_fails_unchecked_box_lost_in_background(tmp_path):
    from tools.verify import analyze_control
    r = analyze_control(_control_png(tmp_path, (30, 31, 44), (30, 31, 44)), [12, 12, 16, 16], 2, checked=False)
    assert not r["ok"] and r["ident"] < 3


def test_worst_bg_only_samples_under_text_pixels(tmp_path: Path):
    bg = Image.new("RGB", (100, 50), (10, 10, 10))
    bg.putpixel((90, 5), (240, 240, 240))  # a bright badge inside the rect but away from the glyphs
    bg.putpixel((40, 20), (60, 60, 60))  # what sits under the glyph
    with_text = bg.copy()
    with_text.putpixel((40, 20), (200, 200, 200))  # the glyph pixel
    hidden, shown = tmp_path / "hidden.png", tmp_path / "shown.png"
    bg.save(hidden)
    with_text.save(shown)
    got = contrast.worst_bg(hidden, [0, 0, 50, 25], 2, "#ffffff", text_png=shown)
    assert got == (60, 60, 60)
