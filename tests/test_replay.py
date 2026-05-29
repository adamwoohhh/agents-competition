import importlib
import json
import os
import pathlib
import tempfile
import tomllib
import unittest
from unittest import mock


class ReplayTest(unittest.TestCase):
    def replay_jump_distance(self, path, playfield_width):
        dino_game = importlib.import_module("dino_game")
        player = dino_game.ReplayPlayer.from_file(
            path,
            playback_playfield_width=playfield_width,
        )
        game = dino_game.DinoGame(
            rng=dino_game.random.Random(player.seed),
            obstacle_spawn_x=playfield_width,
        )

        for frame in range(1, player.max_frame + 1):
            action = player.action_for_frame(frame)
            dino_game.apply_game_action(game, action)
            game.update(replay_obstacles=player.obstacles_for_frame(frame))
            if action == "jump":
                state = game.get_state(max_obstacle_count=1)
                self.assertTrue(state["obstacles"])
                return state["obstacles"][0]["distance"]

        self.fail("Replay did not jump")

    def test_replay_recorder_writes_actions_and_obstacles_without_none_actions(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            recorder = dino_game.ReplayRecorder(path, seed=123, mode="agent")
            recorder.record_action(1, "none")
            recorder.record_obstacle(
                2,
                dino_game.Obstacle(
                    "cactus_group",
                    82,
                    plants=("short", "tall"),
                ),
            )
            recorder.record_action(2, "jump")
            recorder.save()

            data = dino_game.load_replay_file(path)
            self.assertEqual(data["seed"], 123)
            self.assertEqual(data["mode"], "agent")
            self.assertEqual(data["version"], 3)
            self.assertEqual(data["screen"]["playfield_width"], 82)
            self.assertEqual(data["frames"], 2)
            self.assertEqual(data["actions"], [
                {"frame": 2, "action": {"value": "jump"}},
            ])
            self.assertEqual(data["obstacles"], [
                {
                    "frame": 2,
                    "action": {
                        "kind": "cactus_group",
                        "height": 0,
                        "plants": ["short", "tall"],
                    },
                },
            ])

    def test_replay_recorder_writes_competition_metadata(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            recorder = dino_game.ReplayRecorder(
                path,
                seed=123,
                mode="manual",
                competitive=True,
                source_replay="replays/source.json",
            )

            recorder.record_action(1, "jump")
            recorder.save()

            data = dino_game.load_replay_file(path)
            self.assertTrue(data["competitive"])
            self.assertEqual(data["source_replay"], "replays/source.json")

    def test_replay_recorder_writes_llm_usage_snapshot(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            recorder = dino_game.ReplayRecorder(path, seed=123, mode="llm")
            recorder.set_llm_usage({
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": 7470,
                "events": [{
                    "frame": 0,
                    "start_frame": 1,
                    "window_frames": 600,
                    "provider": "codex",
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "total_tokens": 7470,
                }],
            })

            recorder.save()

            data = dino_game.load_replay_file(path)
            self.assertEqual(data["llm_usage"]["total_tokens"], 7470)
            self.assertEqual(data["llm_usage"]["events"][0]["provider"], "codex")

    def test_replay_player_returns_recorded_mode_actions_and_obstacles_by_frame(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            path.write_text(
                '{"version": 3, "seed": 99, "mode": "llm", "frames": 3, '
                '"actions": [{"frame": 1, "action": {"value": "jump"}}], '
                '"obstacles": [{"frame": 2, "action": {"kind": "bird", '
                '"x": 82, "height": 4}}]}'
            )

            player = dino_game.ReplayPlayer.from_file(path)
            self.assertEqual(player.seed, 99)
            self.assertEqual(player.mode, "llm")
            self.assertEqual(player.action_for_frame(1), "jump")
            self.assertEqual(player.action_for_frame(2), "none")
            self.assertEqual(player.action_for_frame(3), "none")
            self.assertEqual(player.obstacles_for_frame(2), [{
                "kind": "bird",
                "x": 82,
                "height": 4,
            }])
            self.assertTrue(player.has_frame(3))
            self.assertFalse(player.has_frame(4))

    def test_replay_player_delays_actions_when_played_on_wider_spawn_position(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            path.write_text(
                '{"version": 3, "seed": 99, "mode": "manual", "frames": 80, '
                '"screen": {"playfield_width": 82}, '
                '"actions": [{"frame": 40, "action": {"value": "jump"}}], '
                '"obstacles": [{"frame": 10, "action": {"kind": "bird", '
                '"height": 4}}]}'
            )

            player = dino_game.ReplayPlayer.from_file(
                path,
                playback_playfield_width=160,
            )

            self.assertEqual(player.action_for_frame(40), "none")
            self.assertIn("jump", [player.action_for_frame(frame) for frame in range(80, 86)])
            self.assertGreaterEqual(player.max_frame, 80)

    def test_replay_jump_distance_matches_across_playfield_widths(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            path.write_text(
                '{"version": 3, "seed": 99, "mode": "manual", "frames": 80, '
                '"screen": {"playfield_width": 82}, '
                '"actions": [{"frame": 40, "action": {"value": "jump"}}], '
                '"obstacles": [{"frame": 10, "action": {"kind": "bird", '
                '"height": 4}}]}'
            )

            recorded_distance = self.replay_jump_distance(path, 82)

            for playfield_width in (90, 120, 160):
                with self.subTest(playfield_width=playfield_width):
                    replayed_distance = self.replay_jump_distance(
                        path,
                        playfield_width,
                    )
                    self.assertAlmostEqual(
                        replayed_distance,
                        recorded_distance,
                        delta=dino_game.MAX_SPEED,
                    )

    def test_replay_end_frame_expands_for_wider_playfield(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            path.write_text(
                '{"version": 3, "seed": 99, "mode": "manual", "frames": 525, '
                '"screen": {"playfield_width": 107}, '
                '"actions": [], '
                '"obstacles": [{"frame": 478, "action": {"kind": "cactus_group", '
                '"height": 0, "plants": ["tall"]}}]}'
            )

            player = dino_game.ReplayPlayer.from_file(
                path,
                playback_playfield_width=160,
            )
            game = dino_game.DinoGame(
                rng=dino_game.random.Random(player.seed),
                obstacle_spawn_x=160,
            )

            for frame in range(1, player.max_frame + 1):
                dino_game.apply_game_action(game, player.action_for_frame(frame))
                game.update(replay_obstacles=player.obstacles_for_frame(frame))
                if game.game_over:
                    break

            self.assertGreater(player.max_frame, 525)
            self.assertTrue(game.game_over)

    def test_wide_replay_retimes_jumps_against_nearest_recorded_obstacle_on_small_playfield(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            path.write_text(
                '{"version": 3, "seed": 1780031604433970000, '
                '"mode": "manual", "frames": 261, '
                '"screen": {"playfield_width": 215}, '
                '"actions": ['
                '{"frame": 18, "action": {"value": "jump"}},'
                '{"frame": 42, "action": {"value": "jump"}},'
                '{"frame": 66, "action": {"value": "jump"}},'
                '{"frame": 151, "action": {"value": "jump"}},'
                '{"frame": 175, "action": {"value": "jump"}},'
                '{"frame": 220, "action": {"value": "jump"}}], '
                '"obstacles": ['
                '{"frame": 40, "action": {"kind": "cactus_group", '
                '"height": 0, "plants": ["short", "tall"]}},'
                '{"frame": 70, "action": {"kind": "cactus_group", '
                '"height": 0, "plants": ["short"]}},'
                '{"frame": 116, "action": {"kind": "cactus_group", '
                '"height": 0, "plants": ["tall", "short"]}},'
                '{"frame": 152, "action": {"kind": "cactus_group", '
                '"height": 0, "plants": ["short", "short"]}},'
                '{"frame": 201, "action": {"kind": "bird", "height": 8}},'
                '{"frame": 245, "action": {"kind": "cactus_group", '
                '"height": 0, "plants": ["tall"]}}]}'
            )

            player = dino_game.ReplayPlayer.from_file(
                path,
                playback_playfield_width=82,
            )
            game = dino_game.DinoGame(
                rng=dino_game.random.Random(player.seed),
                obstacle_spawn_x=82,
            )
            game_over_frame = None
            for frame in range(1, player.max_frame + 1):
                dino_game.apply_game_action(game, player.action_for_frame(frame))
                game.update(replay_obstacles=player.obstacles_for_frame(frame))
                if game.game_over:
                    game_over_frame = frame
                    break

            self.assertGreater(game_over_frame, 150)
            self.assertTrue(game.game_over)

    def test_replay_player_uses_legacy_spawn_position_when_screen_metadata_is_missing(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            path.write_text(
                '{"version": 3, "seed": 99, "mode": "manual", "frames": 80, '
                '"actions": [{"frame": 40, "action": {"value": "jump"}}], '
                '"obstacles": [{"frame": 10, "action": {"kind": "bird", '
                '"x": 82, "height": 4}}]}'
            )

            player = dino_game.ReplayPlayer.from_file(
                path,
                playback_playfield_width=160,
            )

            self.assertIn("jump", [player.action_for_frame(frame) for frame in range(80, 86)])

    def test_replay_player_converts_legacy_events_to_actions_and_obstacles(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            path.write_text(
                '{"version": 2, "seed": 99, "mode": "llm", "events": ['
                '{"frame": 1, "action": {"type": "input", "value": "jump"}},'
                '{"frame": 2, "action": {"type": "obstacle", "kind": "bird", '
                '"x": 82, "height": 4}},'
                '{"frame": 2, "action": {"type": "input", "value": "none"}}'
                ']}'
            )

            player = dino_game.ReplayPlayer.from_file(path)

            self.assertEqual(player.action_for_frame(1), "jump")
            self.assertEqual(player.action_for_frame(2), "none")
            self.assertEqual(player.obstacles_for_frame(2), [{
                "kind": "bird",
                "x": 82,
                "height": 4,
            }])

    def test_replay_player_converts_legacy_actions_to_frame_events(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            path.write_text(
                '{"version": 1, "seed": 99, "actions": ["jump", "none"]}'
            )

            player = dino_game.ReplayPlayer.from_file(path)

            self.assertEqual(player.action_for_frame(1), "jump")
            self.assertEqual(player.action_for_frame(2), "none")
            self.assertEqual(player.next_action(), "jump")
            self.assertIsNone(player.next_action())

    def test_obstacle_data_round_trips_to_obstacle(self):
        dino_game = importlib.import_module("dino_game")
        obstacle = dino_game.Obstacle(
            "cactus_group",
            82,
            plants=("short", "tall"),
        )

        data = dino_game.obstacle_to_action_data(obstacle)
        restored = dino_game.obstacle_from_action_data(data)

        self.assertEqual(restored.kind, "cactus_group")
        self.assertEqual(restored.x, 82)
        self.assertEqual(restored.height, 0)
        self.assertEqual(restored.plants, ("short", "tall"))

    def test_obstacle_data_restores_at_current_spawn_position(self):
        dino_game = importlib.import_module("dino_game")
        obstacle = dino_game.obstacle_from_action_data(
            {
                "kind": "bird",
                "x": 82,
                "height": 4,
            },
            spawn_x=160,
        )

        self.assertEqual(obstacle.x, 160)
        self.assertEqual(obstacle.height, 4)

    def test_game_update_uses_replay_obstacles_instead_of_random_spawn(self):
        dino_game = importlib.import_module("dino_game")
        game = dino_game.DinoGame(obstacle_spawn_x=160)
        game.spawn_timer = 0

        spawned = game.update(replay_obstacles=[{
            "kind": "bird",
            "x": 82,
            "height": 4,
        }])

        self.assertEqual(len(spawned), 1)
        self.assertEqual(game.obstacles[0].kind, "bird")
        self.assertEqual(game.obstacles[0].x, 160)
        self.assertEqual(game.obstacles[0].height, 4)

    def test_default_replay_path_uses_replay_directory_and_mode(self):
        dino_game = importlib.import_module("dino_game")

        path = dino_game.default_replay_path("manual", seed=123456, directory="runs")

        self.assertTrue(path.startswith("runs" + os.sep))
        self.assertIn("-manual-", pathlib.Path(path).name)
        self.assertTrue(path.endswith(".json"))

    def test_default_replay_path_uses_config_replay_directory(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir, \
                mock.patch("dino_game.constants.os.path.expanduser", return_value=tmpdir):
            path = pathlib.Path(dino_game.default_replay_path("manual", seed=123456))

        self.assertEqual(
            path.parent,
            pathlib.Path(tmpdir) / ".config" / "ai-dino-in-terminal" / "replays",
        )
        self.assertIn("-manual-", path.name)
        self.assertTrue(path.name.endswith(".json"))

    def test_explicit_record_path_adds_run_suffix_after_first_game(self):
        dino_game = importlib.import_module("dino_game")

        self.assertEqual(
            dino_game.record_path_for_run("run.json", "manual", 123, 1),
            "run.json",
        )
        self.assertEqual(
            dino_game.record_path_for_run("run.json", "manual", 123, 2),
            "run-2.json",
        )

    def test_finish_recording_saves_once_at_game_over(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "run.json"
            recorder = dino_game.ReplayRecorder(path, seed=123, mode="manual")

            dino_game.finish_recording(recorder)
            dino_game.finish_recording(recorder)

            data = dino_game.load_replay_file(path)
            self.assertEqual(data["seed"], 123)

    def test_start_recording_run_creates_new_default_file_per_game(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            _, first = dino_game.start_recording_run(
                "manual",
                None,
                1,
                directory=tmpdir,
                seed=111,
            )
            _, second = dino_game.start_recording_run(
                "manual",
                None,
                2,
                directory=tmpdir,
                seed=222,
            )

            self.assertNotEqual(first.path, second.path)
            self.assertIn("-manual-", pathlib.Path(first.path).name)
            self.assertIn("-manual-", pathlib.Path(second.path).name)

    def test_list_replay_files_returns_json_files_newest_first(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            old_path = pathlib.Path(tmpdir) / "old.json"
            new_path = pathlib.Path(tmpdir) / "new.json"
            ignored_path = pathlib.Path(tmpdir) / "notes.txt"
            old_path.write_text("{}")
            new_path.write_text("{}")
            ignored_path.write_text("ignore")
            os.utime(old_path, (10, 10))
            os.utime(new_path, (20, 20))

            self.assertEqual(
                dino_game.list_replay_files(tmpdir),
                [str(new_path), str(old_path)],
            )

    def test_clear_replay_files_removes_only_replay_json_files(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            replay_path = pathlib.Path(tmpdir) / "run.json"
            notes_path = pathlib.Path(tmpdir) / "notes.txt"
            replay_path.write_text("{}")
            notes_path.write_text("keep")

            removed = dino_game.clear_replay_files(tmpdir)

            self.assertEqual(removed, 1)
            self.assertFalse(replay_path.exists())
            self.assertTrue(notes_path.exists())

    def test_replay_metadata_reports_mode_frames_creation_and_competition_source(self):
        dino_game = importlib.import_module("dino_game")

        with tempfile.TemporaryDirectory() as tmpdir:
            replay_path = pathlib.Path(tmpdir) / "competition.json"
            replay_path.write_text(
                '{"version": 3, "seed": 99, "mode": "competitive", "frames": 12, '
                '"competitive": true, "source_replay": "replays/source.json", '
                '"actions": [], "obstacles": []}'
            )

            metadata = dino_game.replay_metadata(replay_path)
            lines = dino_game.render_replay_metadata(metadata)

            self.assertEqual(metadata["mode"], "competitive")
            self.assertEqual(metadata["frames"], 12)
            self.assertEqual(metadata["competitive"], True)
            self.assertEqual(metadata["source_replay"], "replays/source.json")
            self.assertIn("模式: competitive", lines)
            self.assertIn("帧数: 12", lines)
            self.assertIn("是否竞技模式: 是", lines)
            self.assertIn("竞技模式源记录: replays/source.json", lines)
            self.assertIn("创建时间:", lines)

    def test_move_replay_selection_wraps_with_arrow_keys(self):
        dino_game = importlib.import_module("dino_game")

        self.assertEqual(dino_game.move_replay_selection(0, dino_game.curses.KEY_DOWN, 3), 1)
        self.assertEqual(dino_game.move_replay_selection(0, dino_game.curses.KEY_UP, 3), 2)
        self.assertEqual(dino_game.move_replay_selection(2, dino_game.curses.KEY_DOWN, 3), 0)

    def test_browse_replay_files_opens_metadata_then_returns_on_q(self):
        dino_game = importlib.import_module("dino_game")

        class FakeScreen:
            def __init__(self):
                self.keys = [10, ord("q")]
                self.nodelay_calls = []

            def keypad(self, value):
                pass

            def nodelay(self, value):
                self.nodelay_calls.append(value)

            def erase(self):
                pass

            def getmaxyx(self):
                return (24, 100)

            def addstr(self, *args):
                pass

            def refresh(self):
                pass

            def getch(self):
                return self.keys.pop(0)

        with tempfile.TemporaryDirectory() as tmpdir:
            replay_path = pathlib.Path(tmpdir) / "run.json"
            replay_path.write_text(
                '{"version": 3, "seed": 1, "mode": "manual", '
                '"frames": 0, "actions": [], "obstacles": []}'
            )
            screen = FakeScreen()
            with (
                mock.patch.object(dino_game.curses, "curs_set"),
                mock.patch("dino_game.replay.show_replay_metadata") as show_metadata,
            ):
                dino_game.browse_replay_files(screen, [str(replay_path)])

        self.assertEqual(screen.nodelay_calls, [False])
        show_metadata.assert_called_once_with(screen, str(replay_path))

    def test_browse_replay_files_empty_list_returns_on_enter(self):
        dino_game = importlib.import_module("dino_game")

        class FakeScreen:
            def __init__(self):
                self.keys = [10]

            def keypad(self, value):
                pass

            def nodelay(self, value):
                pass

            def erase(self):
                pass

            def getmaxyx(self):
                return (24, 100)

            def addstr(self, *args):
                pass

            def refresh(self):
                pass

            def getch(self):
                return self.keys.pop(0)

        with mock.patch.object(dino_game.curses, "curs_set"):
            dino_game.browse_replay_files(FakeScreen(), [])

    def test_game_mode_from_args_tracks_manual_agent_and_llm(self):
        dino_game = importlib.import_module("dino_game")

        self.assertEqual(dino_game.game_mode_from_args([]), "manual")
        self.assertEqual(dino_game.game_mode_from_args(["play"]), "manual")
        self.assertEqual(dino_game.game_mode_from_args(["play", "--auto"]), "agent")
        self.assertEqual(dino_game.game_mode_from_args(["play", "--llm"]), "llm")
        self.assertEqual(dino_game.game_mode_from_args(["compete"]), "competitive")

    def test_competition_source_path_accepts_positional_arg_only(self):
        dino_game = importlib.import_module("dino_game")

        self.assertEqual(
            dino_game.competition_source_path(["compete", "run.json"]),
            "run.json",
        )
        self.assertIsNone(dino_game.competition_source_path(["compete"]))
        self.assertIsNone(dino_game.competition_source_path(["--compete", "run.json"]))

    def test_replay_seed_and_actions_are_deterministic(self):
        dino_game = importlib.import_module("dino_game")
        actions = ["none"] * 20 + ["jump"] + ["none"] * 40

        first = dino_game.run_replay_simulation(seed=42, actions=actions)
        second = dino_game.run_replay_simulation(seed=42, actions=actions)

        self.assertEqual(first, second)
