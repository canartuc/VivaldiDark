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
