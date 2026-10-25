"""Integration tests for the verification runner (launch Vivaldi)."""
import json
from pathlib import Path

import pytest

from tests.test_vivaldi import SCENE
from tools import verify
from tools.vivaldi import Vivaldi

pytestmark = pytest.mark.vivaldi

WHITE_SCENE = SCENE.replace("#0c0e14", "#f4f4f6").replace("#1f2335", "#ffffff")


def make_theme(tmp_path: Path, name: str, scene: str = SCENE, highlight: str = "#7aa2f7", **colours) -> Path:
    theme = tmp_path / "themes" / name.lower().replace(" ", "-")
    theme.mkdir(parents=True)
    (theme / "scene.py").write_text(scene)
    (theme / "theme.json").write_text(json.dumps(dict(
        slug=theme.name, name=name, id="11111111-2222-4333-8444-%012d" % (abs(hash(name)) % 10**12),
        highlight=highlight, radius=8, alpha=0.5, blur=4, webp_quality=90, **colours)))
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


def test_lost_focus_becomes_pending_not_crash(tmp_path, monkeypatch):
    from tools import macos

    def refuse(*a, **k):
        raise macos.NotFrontmost("user is typing elsewhere")
    monkeypatch.setattr(macos, "key", refuse)
    report = verify.verify_theme(make_theme(tmp_path, "Focus Fixture"), quick=True, out=tmp_path / "out", states=["find"])
    assert any("find" in p for p in report.pending)
    assert (tmp_path / "out" / "report.json").exists()


def test_typed_url_does_not_leak_into_next_state(tmp_path):
    with Vivaldi() as v:
        verify.prepare_tabs(v)
        verify.emulate(v, (1920, 1080))
        for state in ("address-dropdown", "find"):  # the real matrix order
            verify.state_setup(v, state)
            verify.state_teardown(v, state)
        verify.state_setup(v, "downloads-panel")
        typed = v.run_ui("(document.querySelector('.UrlBar-UrlField') || {}).value || ''")
        verify.state_teardown(v, "downloads-panel")
    assert "exa" not in typed


def test_selected_address_text_uses_selection_floor(tmp_path):
    from tools import package
    zp = package.build_theme(make_theme(tmp_path, "Selection Fixture"), tmp_path / "icons")
    with Vivaldi() as v:
        v.install_theme(zp)
        verify.prepare_tabs(v)
        verify.emulate(v, (1920, 1080))
        opts = verify.state_setup(v, "address-dropdown")
        shot = v.screenshot(tmp_path / "dd.png")
        fails = verify.check_frame(v, "dd", shot, opts.get("floor", 4.5), url_floor=opts.get("url_floor"))
        verify.state_teardown(v, "address-dropdown")
    assert opts.get("url_floor") == verify.SELECTION_FLOOR
    assert not [f for f in fails if "address" in f], fails


def test_controls_audit_reads_the_visible_settings_tab(tmp_path):
    with Vivaldi() as v:
        verify.prepare_tabs(v)  # already contains a Settings tab, like the full run
        verify.emulate(v, (1920, 1080))
        results = verify.audit_controls(v, sections=["general"], shots=tmp_path / "shots")
    unlabeled = [r for r in results if r["kind"] != "text" and not r["label"]]
    assert results and unlabeled == []


def test_native_menu_retries_once_after_unprovable_capture(tmp_path, monkeypatch):
    from tools import macos, package
    calls = {"n": 0}

    def flaky(v, selector, path):
        calls["n"] += 1
        if calls["n"] % 2 == 1:
            raise macos.UnsafeCapture("screen changed during capture")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"png")
        return path
    monkeypatch.setattr(macos, "native_menu", flaky)
    monkeypatch.setattr(verify, "NATIVE_MENUS", {"tab": ".tab-position .tab:not(.active)"})
    zp = package.build_theme(make_theme(tmp_path, "Retry Fixture"), tmp_path / "icons")
    captured, pending = verify.native_menus(zp, tmp_path / "native")
    assert len(captured) == 1 and pending == []


def test_controls_audit_skips_hidden_and_exempts_disabled(tmp_path):
    with Vivaldi() as v:
        verify.emulate(v, (1920, 1080))
        results = verify.audit_controls(v, sections=["tabs"], shots=tmp_path / "shots")
    controls = [r for r in results if r["kind"] != "text"]
    flat = [r["label"] for r in controls if not r.get("disabled") and r["ident"] < 1.05]
    assert flat == [], f"measured under something that covers them: {flat}"
    disabled = [r for r in controls if r.get("disabled")]
    assert disabled and all(r["ok"] for r in disabled)


def test_quick_verify_sage_fixture(tmp_path):
    dark = SCENE.replace("#0c0e14", "#050806").replace("#1f2335", "#0b100c")
    theme = make_theme(tmp_path, "Sage Fixture", dark, highlight="#00ff41", bg="#0b100c", fg="#6b8a6b",
                       accent="#060906", window="#060906", contrast=7)
    report = verify.verify_theme(theme, quick=True, out=tmp_path / "out")
    assert report.failures == [], report.failures


def test_same_colour_tolerates_rounding_jitter():
    assert verify.same_colour("rgb(113, 142, 113)", "rgb(112, 143, 111)")
    assert not verify.same_colour("rgb(255, 255, 255)", "rgb(112, 143, 111)")
    assert not verify.same_colour("rgb(116, 143, 111)", "rgb(112, 143, 111)")
