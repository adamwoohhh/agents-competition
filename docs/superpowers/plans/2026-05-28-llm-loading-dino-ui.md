# LLM Loading Dino UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a front-facing blinking dino UI for LLM loading frames while preserving collision behavior.

**Architecture:** Keep the game as a single-module curses app. Add dedicated loading-only sprite constants and a small sprite-selection helper in `dino_game.py`; use it from `TerminalRenderer.draw()` when `loading_text` is active. Tests lock sprite footprint and verify collision code is untouched by loading UI state.

**Tech Stack:** Python, curses, unittest.

---

### Task 1: Loading Dino Sprites

**Files:**
- Modify: `dino_game.py`
- Modify: `tests/test_packaging.py`

- [ ] **Step 1: Write failing tests**

Add tests near the existing gameplay/rendering tests in `tests/test_packaging.py`:

```python
class LoadingDinoSpriteTest(unittest.TestCase):
    def test_loading_dino_sprites_keep_existing_footprint(self):
        dino_game = importlib.import_module("dino_game")

        for sprite in (
            dino_game.DINO_LOADING_STAND,
            dino_game.DINO_LOADING_JUMP,
            dino_game.DINO_LOADING_DUCK,
        ):
            self.assertEqual(len(sprite), 6)
            self.assertLessEqual(max(len(line) for line in sprite), 10)

        self.assertEqual(dino_game.DINO_LOADING_DUCK[:2], ["          ", "          "])

    def test_loading_dino_sprites_only_cut_out_eyes(self):
        dino_game = importlib.import_module("dino_game")

        self.assertIn("██  ██", dino_game.DINO_LOADING_STAND)
        self.assertIn("██ ███", dino_game.DINO_LOADING_JUMP)
        self.assertIn("  ██ ████", dino_game.DINO_LOADING_DUCK)
        for sprite in (
            dino_game.DINO_LOADING_STAND,
            dino_game.DINO_LOADING_JUMP,
            dino_game.DINO_LOADING_DUCK,
        ):
            joined = "\n".join(sprite)
            self.assertNotIn("▾", joined)
            self.assertNotIn("▴", joined)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_packaging.LoadingDinoSpriteTest -v`

Expected: FAIL or ERROR because `DINO_LOADING_STAND`, `DINO_LOADING_JUMP`, and `DINO_LOADING_DUCK` do not exist.

- [ ] **Step 3: Implement minimal sprites and selection**

In `dino_game.py`, add loading sprite constants next to existing `DINO_*` constants:

```python
DINO_LOADING_STAND = [
    r"   ▄████▄ ",
    r"   ██  ██ ",
    r"   ██████ ",
    r"   ▀████▀ ",
    r"    ██    ",
    r"   █  █   ",
]

DINO_LOADING_JUMP = [
    r"   ▄████▄ ",
    r"   ██ ███ ",
    r"   ██████ ",
    r"   ▀████▀ ",
    r"   ▄██▄   ",
    r"  ▀    ▀  ",
]

DINO_LOADING_DUCK = [
    r"          ",
    r"          ",
    r"   ▄████▄ ",
    r"  ██ ████ ",
    r"  ███████ ",
    r"   ▀████▀ ",
]
```

Add helper:

```python
def dino_art_for_state(game: DinoGame, loading: bool = False) -> list[str]:
    if loading:
        if game.ducking:
            return DINO_LOADING_DUCK
        if game.jumping:
            return DINO_LOADING_JUMP
        return DINO_LOADING_STAND
    if game.ducking:
        return DINO_DUCK
    if game.jumping:
        return DINO_JUMP
    if (game.frame // RUN_ANIM_FRAME_INTERVAL) % 2 == 0:
        return DINO_RUN_1
    return DINO_RUN_2
```

Use this helper in `TerminalRenderer.draw()` for normal rendering:

```python
art = dino_art_for_state(game, loading=bool(loading_text and not (pause_state and pause_state.status != "running")))
```

Keep `draw_competition_lane()` on the normal sprites unless competition loading is added later.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_packaging.LoadingDinoSpriteTest -v`

Expected: PASS.

- [ ] **Step 5: Run broader verification**

Run: `python3 -m unittest tests.test_packaging -v`

Expected: all tests pass.

Run: `python3 -m py_compile dino_game.py`

Expected: exit code 0.
