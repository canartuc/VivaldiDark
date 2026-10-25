"""Integration tests for the verification runner (launch Vivaldi)."""
import json
from pathlib import Path

import pytest

from tests.test_vivaldi import SCENE
from tools import verify
from tools.vivaldi import Vivaldi

pytestmark = pytest.mark.vivaldi

WHITE_SCENE = SCENE.replace("#0c0e14", "#f4f4f6").replace("#1f2335", "#ffffff")


def make_theme(tmp_path: Path, name: str, scene: str = SCENE, highlight: str = "#7aa2f7") -> Path:
    theme = tmp_path / "themes" / name.lower().replace(" ", "-")
    theme.mkdir(parents=True)
    (theme / "scene.py").write_text(scene)
    (theme / "theme.json").write_text(json.dumps(dict(
        slug=theme.name, name=name, id="11111111-2222-4333-8444-%012d" % (abs(hash(name)) % 10**12),
        highlight=highlight, radius=8, alpha=0.5, blur=4, webp_quality=90)))
    return theme


def test_verify_quick_passes_fixture(tmp_path):
    report = verify.verify_theme(make_theme(tmp_path, "Dark Fixture"), quick=True, out=tmp_path / "out")
    assert report.failures == [], report.failures
    assert (tmp_path / "out" / "tabs-top" / "1920x1080" / "startpage.png").exists()


def test_verify_flags_bright_bars(tmp_path):
    report = verify.verify_theme(make_theme(tmp_path, "White Fixture", WHITE_SCENE), quick=True, out=tmp_path / "out")
    assert any("contrast" in f for f in report.failures)


def test_controls_audit_reports_every_control(tmp_path):
    from tools import package
    zp = package.build_theme(make_theme(tmp_path, "Controls Fixture"), tmp_path / "icons")
    with Vivaldi() as v:
        v.install_theme(zp)
        results = verify.audit_controls(v, sections=["tabs"], shots=tmp_path / "shots")
    kinds = {r["kind"] for r in results}
    assert {"checkbox", "radio"} <= kinds
    assert sum(r["kind"] == "checkbox" for r in results) >= 30  # the Tabs section has 38
    assert all({"kind", "checked", "ident", "ok", "section"} <= set(r) for r in results)


def test_menu_audit_lists_items(tmp_path):
    from tools import package
    zp = package.build_theme(make_theme(tmp_path, "Menu Fixture"), tmp_path / "icons")
    with Vivaldi() as v:
        v.install_theme(zp)
        menus = verify.audit_menus(v, shots=tmp_path / "shots")
    workspaces = next(m for m in menus if m["menu"] == "workspaces")
    assert len(workspaces["items"]) >= 1
    assert all({"text", "color", "bg", "ratio", "ok"} <= set(i) for i in workspaces["items"])


def test_states_do_not_leak(tmp_path):
    from tools import package
    zp = package.build_theme(make_theme(tmp_path, "Leak Fixture"), tmp_path / "icons")
    with Vivaldi() as v:
        v.install_theme(zp)
        verify.prepare_tabs(v)
        verify.emulate(v, (1920, 1080))
        verify.state_setup(v, "address-dropdown")
        assert v.run_ui("!!document.querySelector('.OmniDropdown')")
        verify.state_teardown(v, "address-dropdown")
        assert v.run_ui("!document.querySelector('.OmniDropdown')")


def test_settings_address_measures_clean(tmp_path):
    from tools import package
    zp = package.build_theme(make_theme(tmp_path, "Settings Fixture"), tmp_path / "icons")
    with Vivaldi() as v:
        v.install_theme(zp)
        verify.prepare_tabs(v)
        verify.emulate(v, (1920, 1080))
        verify.state_setup(v, "settings")
        shot = v.screenshot(tmp_path / "settings.png")
        fails = verify.check_frame(v, "settings", shot)
    assert not [f for f in fails if "address" in f], fails


def test_unfocused_accepts_vivaldis_own_dimming(tmp_path):
    from tools import package
    zp = package.build_theme(make_theme(tmp_path, "Blur Fixture"), tmp_path / "icons")
    with Vivaldi() as v:
        v.install_theme(zp)
        verify.prepare_tabs(v)
        verify.emulate(v, (1920, 1080))
        opts = verify.state_setup(v, "unfocused")
        shot = v.screenshot(tmp_path / "unfocused.png")
        fails = verify.check_frame(v, "unfocused", shot, opts.get("floor", 4.5), blurred=opts.get("blurred", False))
        verify.state_teardown(v, "unfocused")
    assert fails == [], fails


@pytest.mark.parametrize("state, title", [("dark-site", "Dark site"), ("light-site", "Light site"), ("settings", "Settings")])
def test_states_activate_the_right_tab(tmp_path, state, title):
    with Vivaldi() as v:
        verify.prepare_tabs(v)
        verify.state_setup(v, state)
        active = v.run_ui("new Promise(r => chrome.tabs.query({active: true, currentWindow: true}, t => r(t[0].title)))")
    assert title.lower() in active.lower()


def test_find_state_opens_find_bar(tmp_path):
    with Vivaldi() as v:
        verify.prepare_tabs(v)
        verify.state_setup(v, "find")
        visible = v.run_ui("[...document.querySelectorAll('.find-in-page-wrapper')].some(e => e.getBoundingClientRect().height > 10)")
        verify.state_teardown(v, "find")
        hidden = v.run_ui("![...document.querySelectorAll('.find-in-page-wrapper')].some(e => e.getBoundingClientRect().height > 10)")
    assert visible and hidden
