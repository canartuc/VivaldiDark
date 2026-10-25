import json
import re
from pathlib import Path

import pytest

from tools import package
from tools.svg import H, W
from tools.verify import crop_check

REPO = Path(__file__).resolve().parent.parent
THEMES = ["shibuya-nocturne", "neon-fuji", "silk-nocturne", "paris-nocturne", "istanbul-nocturne", "terminal-city", "pixel-valley", "8-bit-cosmos"]
BUSY = json.loads((REPO / "tools" / "startpage_busy.json").read_text())


@pytest.mark.parametrize("slug", THEMES)
def test_scene_builds(slug):
    scene = package.load_scene(REPO / "themes" / slug)
    if hasattr(scene, "build_image"):  # raster (pixel-art) scene
        a, b = scene.build_image(), scene.build_image()
        assert a.size == (W, H)
        assert a.tobytes() == b.tobytes(), "scene output must be deterministic"
    else:
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


ZONES = {"top": (0, 0, 3840, 420), "left": (0, 0, 950, 2160), "bottom": (0, 1840, 3840, 2160)}


@pytest.mark.parametrize("slug", THEMES)
def test_bar_zones_are_dark(slug, tmp_path):
    from PIL import Image
    from tools import contrast
    from tools.render import render_svg
    scene = package.load_scene(REPO / "themes" / slug)
    if hasattr(scene, "build_image"):
        img = scene.build_image().convert("RGB").reduce(2)
    else:
        svg = tmp_path / "art.svg"
        svg.write_text(scene.build())
        render_svg(svg, tmp_path / "art.png")
        img = Image.open(tmp_path / "art.png").convert("RGB").reduce(2)  # ignore single sub-pixel sparkles
    for name, (x0, y0, x1, y1) in ZONES.items():
        region = img.crop((x0 // 2, y0 // 2, x1 // 2, y1 // 2))
        worst = max(set(region.get_flattened_data()), key=contrast.luminance)
        cfg = package.load_config(REPO / "themes" / slug)
        limit = contrast.zone_limit(cfg.fg, cfg.bg, cfg.alpha)  # keeps this theme's tab text >= 4.5:1
        assert contrast.luminance(worst) <= limit, f"{name} zone has {worst} (limit {limit:.3f})"
