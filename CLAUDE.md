# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

VivaldiDark is a collection of dark Vivaldi browser themes. Each theme is a zip of `settings.json`, one background image and one toolbar icon family (`icons/` outline or `icons/pixel/`, chosen by `theme.json`). A theme's `scene.py` draws its art: `build()` returns SVG, and pixel scenes use `build_image()` (480×270 upscaled 8×, lossless WebP). Three themes use Tokyo Night colours (Enkia, MIT); the pixel themes use the canartuc.com palette.

Previews (`themes/<slug>/preview.jpg`) are public: they must not show the owner's location or other personal data (hide the Start Page Weather widget). Never name the Paris tower ("E…l" is checked by `tests/test_docs.py`) and never draw its lights. The repo is public: never commit `docs/superpowers/`, `.superpowers/` or `.playwright-mcp/` (all git-ignored).

## Commands

- `uv sync`: set up the environment (Python ≥3.12, Pillow, websockets, pytest)
- `uv run pytest`: run all tests. Add `-m "not vivaldi"` to skip tests that launch Vivaldi.
- `uv run pytest tests/test_x.py::test_name`: run a single test
