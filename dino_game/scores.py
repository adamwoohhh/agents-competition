"""Persistent high scores by game mode."""

from __future__ import annotations

import json
import os

from .constants import CONFIG_DIR_NAME

SCORES_FILE_NAME = "scores.json"


def scores_file_path(home: str | None = None) -> str:
    home_dir = home if home is not None else os.path.expanduser("~")
    return os.path.join(home_dir, ".config", CONFIG_DIR_NAME, SCORES_FILE_NAME)


def load_scores(path: str | os.PathLike | None = None) -> dict[str, int]:
    scores_path = os.fspath(path or scores_file_path())
    try:
        with open(scores_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    scores: dict[str, int] = {}
    for mode, score in data.items():
        try:
            scores[str(mode)] = max(0, int(score))
        except (TypeError, ValueError):
            continue
    return scores


def load_high_score(mode: str, path: str | os.PathLike | None = None) -> int:
    return load_scores(path).get(mode, 0)


def save_high_score(
        mode: str,
        score: int,
        path: str | os.PathLike | None = None) -> int:
    scores_path = os.fspath(path or scores_file_path())
    scores = load_scores(scores_path)
    high_score = max(scores.get(mode, 0), int(score))
    scores[mode] = high_score
    directory = os.path.dirname(scores_path)
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(scores_path, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=2, sort_keys=True)
            f.write("\n")
    except OSError:
        return high_score
    return high_score
