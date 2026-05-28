import unittest
from unittest import mock

from dino_game import sessions
from dino_game.cli import CliArgs


class SessionsTest(unittest.TestCase):
    def test_replay_list_command_uses_replay_list_session_without_renderer(self):
        stdscr = object()
        cli_args = CliArgs(command="replay", replay_action="list")

        with mock.patch("dino_game.sessions.Renderer") as renderer_class:
            session = sessions.session_for_cli_args(stdscr, cli_args)

        self.assertIsInstance(session, sessions.ReplayListSession)
        renderer_class.assert_not_called()

    def test_manual_session_next_action_uses_manual_input_helper(self):
        renderer = mock.Mock()
        session = sessions.ManualSession(
            stdscr=mock.Mock(),
            renderer=renderer,
            cli_args=CliArgs(command="play", mode="manual"),
        )

        action = session._next_action(ord(" "))

        self.assertEqual(action, "jump")
        self.assertEqual(session.event_frame, 1)
        self.assertTrue(session.game.jumping)

    def test_game_over_does_not_auto_save_replay_until_s_is_pressed(self):
        renderer = mock.Mock()
        session = sessions.ManualSession(
            stdscr=mock.Mock(),
            renderer=renderer,
            cli_args=CliArgs(command="play", mode="manual"),
        )
        session.recorder = mock.Mock()

        def end_game():
            session.game.game_over = True
            return []

        session.game.update = end_game
        with (
            mock.patch("dino_game.sessions.finish_recording") as finish_recording,
            mock.patch("dino_game.sessions.save_high_score", return_value=0),
        ):
            session._update_game("none")

            finish_recording.assert_not_called()
            session.recorder.save.assert_not_called()

            session._handle_game_over(ord("s"))

            finish_recording.assert_called_once_with(session.recorder)
            renderer.draw.assert_called_with(
                session.game,
                session.agent_name,
                cached_frames_view=None,
                game_over_save_status="saved",
            )

    def test_session_loads_and_persists_mode_high_score(self):
        renderer = mock.Mock()
        with (
            mock.patch("dino_game.sessions.load_high_score", return_value=41),
            mock.patch("dino_game.sessions.save_high_score", return_value=50) as save_high_score,
        ):
            session = sessions.ManualSession(
                stdscr=mock.Mock(),
                renderer=renderer,
                cli_args=CliArgs(command="play", mode="manual"),
            )

            self.assertEqual(session.game.high_score, 41)
            session.game.score = 50
            session.game.update = lambda: setattr(session.game, "game_over", True) or []
            session._update_game("none")

        save_high_score.assert_called_once_with("manual", 50)
        self.assertEqual(session.game.high_score, 50)
