import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from tools import package
from tools.settings_schema import EXPORT_KEYS

UUID = "0b9d6f43-6f0e-4c39-9b1e-2f3a4c5d6e7f"


def make_cfg(**over) -> package.ThemeConfig:
    base = dict(slug="test-theme", name="Test Theme", id=UUID, highlight="#7aa2f7",
                radius=8, alpha=0.5, blur=4, webp_quality=90)
    base.update(over)
    return package.ThemeConfig(**base)


def write_image(path: Path, size=(1920, 1080)) -> Path:
    Image.new("RGB", size, (26, 27, 38)).save(path, "WEBP")
    return path


def write_zip(path: Path, payload_bytes: int = 10) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
        z.writestr("blob.bin", b"\0" * payload_bytes)
    return path


@pytest.fixture
def good(tmp_path):
    settings = package.build_settings(make_cfg(), {})
    return settings, write_image(tmp_path / "bg.webp"), write_zip(tmp_path / "t.zip")


def test_build_settings_shared_values():
    s = package.build_settings(make_cfg(), {"Back": "back.svg"})
    assert set(s) == EXPORT_KEYS
    assert s["colorFg"] == "#828bb8"
    assert s["colorPosition"] == "unified"
    assert s["colorHighlightBg"] == "#7aa2f7"
    assert s["buttons"] == {"Back": "back.svg"}
    assert s["backgroundImage"] == "background.webp"


def test_validate_accepts_good(good):
    assert package.validate(*good) == []


def test_validate_rejects_alpha_below_half(good):
    settings, img, zp = good
    settings["alpha"] = 0.49
    assert any("alpha" in p for p in package.validate(settings, img, zp))


def test_validate_rejects_unknown_key(good):
    settings, img, zp = good
    settings["colourFg"] = "#fff"
    assert any("colourFg" in p for p in package.validate(settings, img, zp))


def test_validate_rejects_small_image(good, tmp_path):
    settings, _, zp = good
    small = write_image(tmp_path / "small.webp", (1280, 720))
    assert any("1920" in p for p in package.validate(settings, small, zp))


def test_validate_rejects_big_zip(good, tmp_path):
    settings, img, _ = good
    big = write_zip(tmp_path / "big.zip", 8 * 1024 * 1024 + 1)
    assert any("8 MB" in p for p in package.validate(settings, img, big))


SCENE = '''
HERO_BOX = (1000.0, 500.0, 1400.0, 900.0)

def build():
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160">'
            '<defs><linearGradient id="g" x2="0" y2="1"><stop offset="0" stop-color="#0c0e14"/>'
            '<stop offset="1" stop-color="#1a1b26"/></linearGradient></defs>'
            '<rect width="3840" height="2160" fill="url(#g)"/></svg>')
'''

ICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M16.5 8.5 11 14l5.5 5.5"/></svg>')


def test_build_theme_end_to_end(tmp_path):
    theme = tmp_path / "themes" / "test-theme"
    theme.mkdir(parents=True)
    (theme / "scene.py").write_text(SCENE)
    cfg = make_cfg()
    (theme / "theme.json").write_text(json.dumps(cfg.__dict__))
    icons = tmp_path / "icons"
    icons.mkdir()
    (icons / "back.svg").write_text(ICON)
    (icons / "reload.svg").write_text(ICON)
    (icons / "manifest.json").write_text(json.dumps({"Back": "back.svg", "Reload": "reload.svg"}))

    zp = package.build_theme(theme, icons)

    assert zp == theme / "Test-Theme.zip"
    with zipfile.ZipFile(zp) as z:
        assert sorted(z.namelist()) == ["back.svg", "background.webp", "reload.svg", "settings.json"]
        settings = json.loads(z.read("settings.json"))
    assert settings["buttons"] == {"Back": "back.svg", "Reload": "reload.svg"}
    assert settings["id"] == UUID
    assert Image.open(theme / "background.webp").size == (3840, 2160)


@pytest.mark.parametrize("name", ["vivaldinight · Neon Fuji", "VivaldiDark Neon Fuji", "X · Neon Fuji"])
def test_validate_rejects_prefixed_names(good, name):
    settings, img, zp = good
    settings["name"] = name
    assert any("name" in p for p in package.validate(settings, img, zp))
