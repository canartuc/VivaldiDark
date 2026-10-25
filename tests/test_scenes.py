import json
import re
from pathlib import Path

import pytest

from tools import package
from tools.svg import H, W
from tools.verify import crop_check

REPO = Path(__file__).resolve().parent.parent
THEMES = ["shibuya-nocturne", "neon-fuji", "silk-nocturne"]
BUSY = json.loads((REPO / "tools" / "startpage_busy.json").read_text())


@pytest.mark.parametrize("slug", THEMES)
def test_scene_builds(slug):
    scene = package.load_scene(REPO / "themes" / slug)
    a, b = scene.build(), scene.build()
    assert a == b, "scene output must be deterministic"
    assert f'width="{W}" height="{H}"' in a
    x0, y0, x1, y1 = scene.HERO_BOX
    assert 0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H


@pytest.mark.parametrize("slug", THEMES)
def test_hero_clear_of_start_page_at_every_size(slug):
    scene = package.load_scene(REPO / "themes" / slug)
    assert crop_check(scene.HERO_BOX, BUSY) == []


@pytest.mark.parametrize("slug", THEMES)
def test_theme_config(slug):
    cfg = package.load_config(REPO / "themes" / slug)
    assert cfg.slug == slug
    assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", cfg.id)
    assert 0.5 <= cfg.alpha <= 0.6 and 4 <= cfg.blur <= 6
    assert "·" not in cfg.name and "vivaldi" not in cfg.name.lower()
