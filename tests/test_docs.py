import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
THEMES = {  # slug: (name, Tokyo Night palette?)
    "shibuya-nocturne": ("Shibuya Nocturne", True),
    "neon-fuji": ("Neon Fuji", True),
    "silk-nocturne": ("Silk Nocturne", True),
    "paris-nocturne": ("Paris Nocturne", False),
    "terminal-city": ("Terminal City", False),
    "pixel-valley": ("Pixel Valley", False),
    "8-bit-cosmos": ("8-Bit Cosmos", False),
}
# The values these themes use from the themes.vivaldi.net upload form's fixed lists
CATEGORIES = {"Abstract", "Art", "Dark", "Games", "Minimalist", "Nature", "Space", "Technology"}
COLOURS = {"Black", "Blue", "Green", "Pink", "Purple"}
CREDIT = "Tokyo Night by Enkia (MIT)"


def _field(text: str, name: str) -> list[str]:
    m = re.search(rf"^- \*\*{name}:\*\* (.+)$", text, re.M)
    assert m, f"missing field {name}"
    return [v.strip() for v in m.group(1).split("·")]


@pytest.mark.parametrize("slug", THEMES)
def test_gallery_files(slug):
    name, tokyo = THEMES[slug]
    text = (REPO / "themes" / slug / "GALLERY.md").read_text()
    assert _field(text, "Theme name") == [name]
    cats, cols = _field(text, "Categories"), _field(text, "Colors")
    assert 1 <= len(cats) <= 3 and set(cats) <= CATEGORIES
    assert 1 <= len(cols) <= 2 and set(cols) <= COLOURS
    assert (CREDIT in text) == tokyo
    assert f"themes/{slug}/" in text and (REPO / "themes" / slug / "preview.jpg").exists()


def test_no_tower_trademark_anywhere():
    word = "eif" + "fel"  # spelled apart so this file passes its own check
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
    for f in files:
        assert word not in f.lower(), f
        path = REPO / f
        if path.is_file():
            assert word.encode() not in path.read_bytes().lower(), f
