"""Vivaldi 8.2 theme settings: the keys an export contains and the values every VivaldiDark theme shares."""

EXPORT_KEYS = frozenset("""
accentFromPage accentOnWindow accentSaturationLimit alpha backgroundImage backgroundPosition blur buttons
colorAccentBg colorBg colorFg colorHighlightBg colorPosition colorWindowBg contrast dimBlurred engineVersion
id name preferSystemAccent radius simpleScrollbar transparencyTabBar transparencyTabs url version
""".split())

SHARED = {
    "accentFromPage": False,
    "accentOnWindow": False,
    "accentSaturationLimit": 1,
    "backgroundImage": "background.webp",
    "backgroundPosition": "stretch",  # rendered as CSS `cover`
    "colorAccentBg": "#16161e",  # dark accent -> Vivaldi computes white active-tab text
    "colorBg": "#1a1b26",
    "colorFg": "#828bb8",  # dim text for inactive tabs and UI (5.2:1 on colorBg)
    "colorPosition": "unified",
    "colorWindowBg": "#16161e",
    "contrast": 7,  # editor "Color Contrast" (-10..20): Vivaldi lifts derived text (URL, faded) to >= 4.5:1
    "dimBlurred": False,
    "engineVersion": 1,
    "preferSystemAccent": False,
    "simpleScrollbar": True,
    "transparencyTabBar": True,
    "transparencyTabs": True,
    "url": "",
    "version": 1,
}

# Below 0.5 Vivaldi switches to `unified-ui-transparent`, which paints every tab title white.
MIN_ALPHA = 0.5
MIN_IMAGE = (1920, 1080)
MAX_ZIP_BYTES = 8 * 1024 * 1024
