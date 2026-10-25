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


@pytest.mark.vivaldi
def test_private_check_catches_a_renamed_weather_widget():
    import time
    from tools.verify import _activate
    from tools.vivaldi import Vivaldi
    with Vivaldi() as v:
        _activate(v, "Start Page", "startpage")
        time.sleep(2)
        preview.hide_private(v)
        preview.assert_private(v)  # the real Weather widget is handled
        # a weather widget Vivaldi might ship later: new class name, non-English labels
        v.run_ui("""(() => { const w = document.createElement('div'); w.className = 'dashboard-widget Dashboard-ForecastCard';
          w.textContent = 'Hava durumu 12°'; document.querySelector('.Dashboard-Widgets').appendChild(w); return true; })()""")
        with pytest.raises(preview.PrivacyError):
            preview.assert_private(v)
        preview.hide_private(v)
        preview.assert_private(v)
