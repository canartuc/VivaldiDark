import json
from pathlib import Path

import pytest

from tools import icons

REPO = Path(__file__).resolve().parent.parent
GOOD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M16.5 8.5 11 14l5.5 5.5"/></svg>')


def test_manifest_covers_all_buttons():
    buttons = json.loads((REPO / "tools" / "vivaldi_buttons.json").read_text())
    wanted = {b for b in buttons if not b.startswith("COMMAND_")}
    assert wanted <= set(icons.load_manifest())


def test_manifest_files_exist():
    for button, name in icons.load_manifest().items():
        assert (REPO / "icons" / name).is_file(), button


def test_every_icon_lints_clean():
    names = set(icons.load_manifest().values())
    problems = {n: icons.lint((REPO / "icons" / n).read_text()) for n in names}
    assert {n: p for n, p in problems.items() if p} == {}


def test_lint_accepts_good():
    assert icons.lint(GOOD) == []


@pytest.mark.parametrize("bad, fragment", [
    (GOOD.replace("<path", "<style>p{}</style><path"), "style"),
    (GOOD.replace("<path", '<path id="a"'), "id"),
    (GOOD.replace("<path", '<path filter="url(#f)"'), "filter"),
    (GOOD.replace("<path", '<use href="#a"/><path'), "use"),
    (GOOD.replace("0 0 28 28", "0 0 24 24"), "viewBox"),
    (GOOD.replace('stroke="currentColor"', 'stroke="#ffffff"'), "currentColor"),
    (GOOD.replace("M16.5 8.5", "M16.3 8.5"), "0.5"),
    (GOOD.replace('stroke-width="1.6"', 'stroke-width="2"'), "stroke-width"),
])
def test_lint_rejects(bad, fragment):
    assert any(fragment in p for p in icons.lint(bad))


PIXEL_GOOD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 28" fill="currentColor">'
              '<rect x="10" y="12" width="8" height="2"/><rect x="12" y="10" width="2" height="2"/></svg>')


def test_pixel_manifest_matches_outline():
    assert set(icons.load_manifest("pixel")) == set(icons.load_manifest("outline"))


def test_every_pixel_icon_lints_clean():
    names = set(icons.load_manifest("pixel").values())
    problems = {n: icons.lint((REPO / "icons" / "pixel" / n).read_text(), "pixel") for n in names}
    assert {n: p for n, p in problems.items() if p} == {}


def test_pixel_lint_accepts_good():
    assert icons.lint(PIXEL_GOOD, "pixel") == []


@pytest.mark.parametrize("bad, fragment", [
    (PIXEL_GOOD.replace('<rect x="10"', '<rect stroke="currentColor" x="10"'), "stroke"),
    (PIXEL_GOOD.replace('x="10"', 'x="11"'), "multiple of 2"),
    (PIXEL_GOOD.replace("<rect x=\"12\" y=\"10\" width=\"2\" height=\"2\"/>", '<path d="M2 2h2"/>'), "path"),
    (PIXEL_GOOD.replace('fill="currentColor"', 'fill="#00ff41"'), "currentColor"),
])
def test_pixel_lint_rejects(bad, fragment):
    assert any(fragment in p for p in icons.lint(bad, "pixel"))


def test_build_theme_picks_pixel_family(tmp_path):
    import zipfile
    from tools import package
    theme = tmp_path / "themes" / "px"
    theme.mkdir(parents=True)
    (theme / "scene.py").write_text('HERO_BOX = (0.0, 0.0, 10.0, 10.0)\n'
                                    'def build():\n    return \'<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160">'
                                    '<rect width="3840" height="2160" fill="#080c09"/></svg>\'\n')
    (theme / "theme.json").write_text(json.dumps(dict(slug="px", name="Px Fixture", id="00000000-0000-4000-8000-000000000001",
                                                      highlight="#00ff41", radius=4, alpha=0.5, blur=4, webp_quality=90, icons="pixel")))
    zp = package.build_theme(theme, REPO / "icons")
    with zipfile.ZipFile(zp) as z:
        back = z.read(json.loads(z.read("settings.json"))["buttons"]["Back"]).decode()
    assert 'fill="currentColor"' in back and "<rect" in back and "stroke" not in back
