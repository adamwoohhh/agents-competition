import importlib
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock


class ConstantsTest(unittest.TestCase):
    def dino_game(self):
        return importlib.import_module("dino_game")

    def test_frame_and_llm_window_constants_are_consistent(self):
        dino_game = self.dino_game()

        self.assertEqual(dino_game.FRAME_MS, 1000 // dino_game.FPS)
        self.assertEqual(dino_game.LLM_ACTION_WINDOW_FRAMES, 600)
        self.assertEqual(
            dino_game.LLM_ACTION_WINDOW_FRAMES,
            dino_game.FPS * dino_game.LLM_ACTION_WINDOW_SECONDS,
        )

    def test_llm_feame_window_env_overrides_action_window_frames(self):
        constants = importlib.import_module("dino_game.constants")

        with mock.patch.dict(os.environ, {"LLM_FEAME_WINDOW": "120"}):
            constants = importlib.reload(constants)
            self.assertEqual(constants.LLM_ACTION_WINDOW_FRAMES, 120)
            self.assertEqual(constants.LLM_ACTION_WINDOW_SECONDS, 4)

        importlib.reload(constants)

    def test_llm_feame_window_env_invalid_values_fall_back_to_default(self):
        constants = importlib.import_module("dino_game.constants")

        for value in ("", "abc", "0", "-1"):
            with mock.patch.dict(os.environ, {"LLM_FEAME_WINDOW": value}):
                constants = importlib.reload(constants)
                self.assertEqual(constants.LLM_ACTION_WINDOW_FRAMES, 600)

        importlib.reload(constants)

    def test_config_llm_window_frames_overrides_default_window_frames(self):
        constants = importlib.import_module("dino_game.constants")

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = pathlib.Path(temp_dir) / ".config" / "ai-dino-in-terminal"
            config_dir.mkdir(parents=True)
            (config_dir / "config.json").write_text(
                json.dumps({"llm_window_frames": 240}),
                encoding="utf-8",
            )

            with mock.patch.dict(os.environ, {"HOME": temp_dir}, clear=True):
                constants = importlib.reload(constants)
                self.assertEqual(constants.LLM_ACTION_WINDOW_FRAMES, 240)
                self.assertEqual(constants.LLM_ACTION_WINDOW_SECONDS, 8)

        importlib.reload(constants)

    def test_llm_feame_window_env_overrides_config_window_frames(self):
        constants = importlib.import_module("dino_game.constants")

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = pathlib.Path(temp_dir) / ".config" / "ai-dino-in-terminal"
            config_dir.mkdir(parents=True)
            (config_dir / "config.json").write_text(
                json.dumps({"llm_window_frames": 240}),
                encoding="utf-8",
            )

            with mock.patch.dict(
                    os.environ,
                    {"HOME": temp_dir, "LLM_FEAME_WINDOW": "120"},
                    clear=True):
                constants = importlib.reload(constants)
                self.assertEqual(constants.LLM_ACTION_WINDOW_FRAMES, 120)

        importlib.reload(constants)
