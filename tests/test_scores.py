import pathlib
import tempfile
import unittest

import dino_game


class ScoresTest(unittest.TestCase):
    def test_load_high_score_returns_zero_when_file_is_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "scores.json"

            self.assertEqual(dino_game.load_high_score("manual", path), 0)

    def test_save_high_score_keeps_highest_score_per_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "scores.json"

            self.assertEqual(dino_game.save_high_score("manual", 12, path), 12)
            self.assertEqual(dino_game.save_high_score("manual", 8, path), 12)
            self.assertEqual(dino_game.save_high_score("agent", 5, path), 5)

            self.assertEqual(dino_game.load_high_score("manual", path), 12)
            self.assertEqual(dino_game.load_high_score("agent", path), 5)

