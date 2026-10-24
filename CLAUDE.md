# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

VivaldiDark is a collection of dark Vivaldi browser themes inspired by Tokyo Night (Enkia, MIT). Each theme is a zip of `settings.json`, one background image and the shared toolbar icons. The repo is public: never commit `docs/superpowers/`, `.superpowers/` or `.playwright-mcp/` (all git-ignored).

## Commands

- `uv sync`: set up the environment (Python ≥3.12, Pillow, websockets, pytest)
- `uv run pytest`: run all tests. Add `-m "not vivaldi"` to skip tests that launch Vivaldi.
- `uv run pytest tests/test_x.py::test_name`: run a single test
