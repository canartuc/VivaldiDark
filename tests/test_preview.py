from pathlib import Path

import pytest
from PIL import Image

from tools import preview

REPO = Path(__file__).resolve().parent.parent


@pytest.mark.vivaldi
def test_preview_hides_weather_widget(tmp_path):
    out = preview.make_preview(REPO / "themes" / "silk-nocturne", tmp_path / "preview.jpg")
    assert Image.open(out).size == (1920, 1080)


def test_preview_refuses_when_weather_visible():
    class FakeVivaldi:
        def run_ui(self, js):
            return True  # the widget still renders
    with pytest.raises(preview.PrivacyError):
        preview.assert_private(FakeVivaldi())
