from pathlib import Path

import pytest
from PIL import Image

from tools import render


def test_render_solid_svg(tmp_path: Path):
    svg = tmp_path / "solid.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
        '<rect width="400" height="200" fill="#7aa2f7"/></svg>'
    )
    png = tmp_path / "solid.png"
    render.render_svg(svg, png, width=400, height=200)
    img = Image.open(png).convert("RGB")
    assert img.size == (400, 200)
    assert img.getpixel((200, 100)) == (122, 162, 247)


def test_render_missing_binary_raises(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("VIVALDIDARK_HEADLESS", "/nope")
    monkeypatch.setattr(render, "PLAYWRIGHT_CACHE", tmp_path / "empty")
    with pytest.raises(FileNotFoundError):
        render.find_headless()
