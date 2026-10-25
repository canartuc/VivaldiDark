"""Gallery previews: the verified Start Page at 1920x1080, with personal data hidden.

Previews are public. Vivaldi's Weather widget shows the town it geolocates from the IP address, so it is hidden
(visibility only, the layout stays as verified) and the capture is refused if it still renders. Besides its class,
any Start Page widget showing a temperature (a number and a degree sign) counts as weather, whatever its class or
language.
"""
import sys
import time
from pathlib import Path

from PIL import Image

from tools import package
from tools.verify import _activate, emulate, prepare_tabs, set_layout
from tools.vivaldi import Vivaldi

REPO = Path(__file__).resolve().parent.parent
SIZE = (1920, 1080)
PRIVATE = [".Dashboard-WeatherWidget"]
TEMPERATURE = r"\d\s*°"
# Start Page widgets that show a temperature, under any class name
_WEATHERLIKE = f"[...document.querySelectorAll('.Dashboard .dashboard-widget')].filter(w => /{TEMPERATURE}/.test(w.textContent))"


class PrivacyError(RuntimeError):
    pass


def hide_private(v: Vivaldi) -> None:
    css = ",".join(PRIVATE) + "{visibility:hidden !important}"
    v.run_ui(f"""(() => {{ const s = document.createElement('style'); s.textContent = {css!r};
      document.head.appendChild(s); {_WEATHERLIKE}.forEach(w => w.style.setProperty('visibility', 'hidden', 'important'));
      return true; }})()""")
    time.sleep(0.3)


def assert_private(v: Vivaldi) -> None:
    # also by the widget's own labels, in case Vivaldi renames the class
    shown = v.run_ui(f"""(() => {{ const vis = e => e.checkVisibility({{visibilityProperty: true}});
      return [...document.querySelectorAll({",".join(PRIVATE)!r})].some(vis) || {_WEATHERLIKE}.some(vis)
        || [...document.querySelectorAll('.Dashboard *')].some(e => e.children.length === 0
             && /Feels like|Forecast from/.test(e.textContent) && vis(e)); }})()""")
    if shown:
        raise PrivacyError("a private widget is still visible; preview not saved")


def make_preview(theme_dir: Path, out: Path | None = None) -> Path:
    theme_dir = Path(theme_dir)
    out = Path(out or theme_dir / "preview.jpg")
    zip_path = package.build_theme(theme_dir, REPO / "icons")
    with Vivaldi() as v:
        v.install_theme(zip_path)
        prepare_tabs(v)
        set_layout(v, "tabs-top")
        emulate(v, SIZE)
        _activate(v, "Start Page", "startpage")
        time.sleep(2)  # let the Start Page widgets render before hiding them
        hide_private(v)
        assert_private(v)
        png = v.screenshot(out.with_suffix(".png"))
    Image.open(png).convert("RGB").resize(SIZE, Image.LANCZOS).save(out, quality=88, optimize=True)
    png.unlink()
    return out


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(make_preview(Path(d)))
