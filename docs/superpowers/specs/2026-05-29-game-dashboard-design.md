# Game Dashboard Design

## Goal

Record every completed non-replay game with score, mode, and token usage when available, then show a curses dashboard for today, the last 7 days, last 30 days, last 90 days, and all time.

## Storage

Keep the existing high score file unchanged. Add `game_records.jsonl` under the existing config directory, with one JSON object per completed game:

- `created_at`: Unix timestamp in seconds.
- `mode`: normalized game mode such as `manual`, `agent`, `llm`, or `competitive`.
- `score`: completed game score.
- `total_tokens`: LLM token total, or `0` when unavailable.

Malformed rows and invalid values are ignored while loading dashboard data.

## Aggregation

Dashboard aggregation groups records by time window and mode. The fixed windows are:

- Today, starting at local midnight.
- Last 7 days.
- Last 30 days.
- Last 90 days.
- All time.

Each group reports cumulative score and cumulative token usage. Token usage is formatted with compact `K`, `M`, and `B` units.

## CLI And UI

Add `dino dashboard`. It enters curses through the existing wrapper and creates a dedicated dashboard session. The screen renders an animated banner with a running dino sprite and `DINO` text, then a table of the aggregated data. `Q` exits.

## Testing

Tests cover record append/load behavior, time-window aggregation, compact token formatting, CLI parsing/help, session routing, and dashboard rendering of the banner plus data rows.
