# Game Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist completed game records and render a curses dashboard with score and token totals by mode across fixed time windows.

**Architecture:** Extend `dino_game/scores.py` with JSONL history and aggregation helpers, route `dino dashboard` through `dino_game/cli.py` and `dino_game/sessions.py`, and add dashboard drawing to `dino_game/rendering.py`. Game sessions append records once at game over while preserving existing high score behavior.

**Tech Stack:** Python 3.11 standard library, curses, unittest.

---

### Task 1: Score History Helpers

**Files:**
- Modify: `dino_game/scores.py`
- Test: `tests/test_scores.py`

- [ ] Write failing tests for appending game records, ignoring invalid rows, compact token formatting, and aggregating fixed windows by mode.
- [ ] Run `python3 -m unittest tests.test_scores -v` and confirm the new tests fail because helpers are missing.
- [ ] Implement `game_records_file_path`, `append_game_record`, `load_game_records`, `format_compact_tokens`, and `aggregate_game_records`.
- [ ] Re-run `python3 -m unittest tests.test_scores -v` and confirm the tests pass.

### Task 2: CLI And Session Routing

**Files:**
- Modify: `dino_game/cli.py`
- Modify: `dino_game/sessions.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_sessions.py`

- [ ] Write failing tests that `dashboard` appears in help, parses as a command, routes to `DashboardSession`, and does not build normal play sessions.
- [ ] Run `python3 -m unittest tests.test_cli tests.test_sessions -v` and confirm failures are for missing dashboard support.
- [ ] Add `dashboard` command metadata and route it through curses to `DashboardSession`.
- [ ] Re-run `python3 -m unittest tests.test_cli tests.test_sessions -v` and confirm the tests pass.

### Task 3: Record Completed Games

**Files:**
- Modify: `dino_game/sessions.py`
- Test: `tests/test_sessions.py`

- [ ] Write failing tests that non-replay game over appends one record with mode, score, and LLM total tokens when available.
- [ ] Run `python3 -m unittest tests.test_sessions -v` and confirm the record tests fail.
- [ ] Call the score-history append helper exactly once when `_update_game` detects game over.
- [ ] Re-run `python3 -m unittest tests.test_sessions -v` and confirm the tests pass.

### Task 4: Dashboard Rendering

**Files:**
- Modify: `dino_game/rendering.py`
- Test: `tests/test_rendering.py`

- [ ] Write failing tests that `draw_dashboard` renders `DINO`, a running dino sprite, window labels, mode rows, compact token totals, and an empty state.
- [ ] Run `python3 -m unittest tests.test_rendering -v` and confirm the tests fail because rendering is missing.
- [ ] Implement `Renderer.draw_dashboard`.
- [ ] Re-run `python3 -m unittest tests.test_rendering -v` and confirm the tests pass.

### Task 5: Exports And Docs

**Files:**
- Modify: `dino_game/__init__.py`
- Modify: `README.md`
- Test: full suite

- [ ] Export any new public helpers needed by tests.
- [ ] Add `dino dashboard` to README command examples and mode table.
- [ ] Run `python3 -m unittest discover -v`.
