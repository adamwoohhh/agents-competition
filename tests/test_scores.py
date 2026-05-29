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

    def test_append_and_load_game_records_ignore_invalid_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "game_records.jsonl"

            dino_game.append_game_record("manual", 12, total_tokens=0, path=path, created_at=100.0)
            dino_game.append_game_record("llm", 34, total_tokens=1500, path=path, created_at=200.0)
            with open(path, "a", encoding="utf-8") as f:
                f.write("not json\n")
                f.write('{"mode": "agent", "score": "bad", "created_at": 300}\n')

            self.assertEqual(dino_game.load_game_records(path), [
                {
                    "created_at": 100.0,
                    "mode": "manual",
                    "score": 12,
                    "total_tokens": 0,
                },
                {
                    "created_at": 200.0,
                    "mode": "llm",
                    "score": 34,
                    "total_tokens": 1500,
                },
            ])

    def test_format_compact_tokens_uses_k_m_b_units(self):
        self.assertEqual(dino_game.format_compact_tokens(0), "0")
        self.assertEqual(dino_game.format_compact_tokens(950), "950")
        self.assertEqual(dino_game.format_compact_tokens(1200), "1.2K")
        self.assertEqual(dino_game.format_compact_tokens(2_500_000), "2.5M")
        self.assertEqual(dino_game.format_compact_tokens(3_200_000_000), "3.2B")

    def test_aggregate_game_records_groups_by_window_and_mode(self):
        now = 86_400.0 * 120 + 3600.0
        records = [
            {"created_at": now - 2 * 86_400.0, "mode": "manual", "score": 10, "total_tokens": 0},
            {"created_at": now - 6 * 86_400.0, "mode": "llm", "score": 20, "total_tokens": 1500},
            {"created_at": now - 20 * 86_400.0, "mode": "manual", "score": 30, "total_tokens": 0},
            {"created_at": now - 80 * 86_400.0, "mode": "llm", "score": 40, "total_tokens": 2_000_000},
            {"created_at": now - 120 * 86_400.0, "mode": "agent", "score": 50, "total_tokens": 0},
        ]
        summary = dino_game.aggregate_game_records(records, now=now)

        all_time = summary[-1]
        self.assertEqual(all_time["label"], "All time")
        self.assertEqual(all_time["modes"]["manual"]["score"], 40)
        self.assertEqual(all_time["modes"]["llm"]["total_tokens"], 2_001_500)
        self.assertEqual(all_time["modes"]["agent"]["score"], 50)

        last_90 = next(item for item in summary if item["label"] == "Last 90 days")
        self.assertNotIn("agent", last_90["modes"])
        self.assertEqual(last_90["modes"]["llm"]["score"], 60)

        last_30 = next(item for item in summary if item["label"] == "Last 30 days")
        self.assertEqual(last_30["modes"]["manual"]["score"], 40)
        self.assertEqual(last_30["modes"]["llm"]["score"], 20)
