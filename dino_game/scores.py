"""Persistent high scores by game mode."""

from __future__ import annotations

import json
import os
import time

from .constants import CONFIG_DIR_NAME

SCORES_FILE_NAME = "scores.json"
GAME_RECORDS_FILE_NAME = "game_records.jsonl"

SECONDS_PER_DAY = 86_400


def scores_file_path(home: str | None = None) -> str:
    home_dir = home if home is not None else os.path.expanduser("~")
    return os.path.join(home_dir, ".config", CONFIG_DIR_NAME, SCORES_FILE_NAME)


def game_records_file_path(home: str | None = None) -> str:
    home_dir = home if home is not None else os.path.expanduser("~")
    return os.path.join(home_dir, ".config", CONFIG_DIR_NAME, GAME_RECORDS_FILE_NAME)


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


def append_game_record(
        mode: str,
        score: int,
        total_tokens: int | None = None,
        path: str | os.PathLike | None = None,
        created_at: float | None = None) -> bool:
    records_path = os.fspath(path or game_records_file_path())
    record = {
        "created_at": float(time.time() if created_at is None else created_at),
        "mode": str(mode),
        "score": max(0, int(score)),
        "total_tokens": max(0, int(total_tokens or 0)),
    }
    directory = os.path.dirname(records_path)
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(records_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")
    except OSError:
        return False
    return True


def load_game_records(path: str | os.PathLike | None = None) -> list[dict]:
    records_path = os.fspath(path or game_records_file_path())
    try:
        with open(records_path, "r", encoding="utf-8") as f:
            lines = list(f)
    except OSError:
        return []

    records = []
    for line in lines:
        try:
            raw = json.loads(line)
            record = {
                "created_at": float(raw["created_at"]),
                "mode": str(raw["mode"]),
                "score": max(0, int(raw["score"])),
                "total_tokens": max(0, int(raw.get("total_tokens", 0) or 0)),
            }
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            continue
        records.append(record)
    return records


def format_compact_tokens(tokens: int | float | None) -> str:
    value = max(0, int(tokens or 0))
    for suffix, unit in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if value >= unit:
            compact = value / unit
            text = f"{compact:.1f}".rstrip("0").rstrip(".")
            return f"{text}{suffix}"
    return str(value)


def _today_start(now: float) -> float:
    local = time.localtime(now)
    return time.mktime((
        local.tm_year,
        local.tm_mon,
        local.tm_mday,
        0,
        0,
        0,
        local.tm_wday,
        local.tm_yday,
        local.tm_isdst,
    ))


def _dashboard_mode(mode: str) -> str | None:
    if mode == "competitive":
        return "manual"
    if mode in ("manual", "llm"):
        return mode
    return None


def aggregate_game_records(records: list[dict], now: float | None = None) -> list[dict]:
    current_time = time.time() if now is None else float(now)
    windows = [
        ("Today", _today_start(current_time)),
        ("Last 7 days", current_time - 7 * SECONDS_PER_DAY),
        ("Last 30 days", current_time - 30 * SECONDS_PER_DAY),
        ("Last 90 days", current_time - 90 * SECONDS_PER_DAY),
        ("All time", None),
    ]
    summary = []
    for label, start in windows:
        modes: dict[str, dict[str, int]] = {}
        for record in records:
            created_at = float(record["created_at"])
            if start is not None and created_at < start:
                continue
            mode = _dashboard_mode(str(record["mode"]))
            if mode is None:
                continue
            bucket = modes.setdefault(mode, {"score": 0, "total_tokens": 0})
            bucket["score"] += int(record["score"])
            bucket["total_tokens"] += int(record.get("total_tokens", 0) or 0)
        summary.append({"label": label, "modes": modes})
    return summary
