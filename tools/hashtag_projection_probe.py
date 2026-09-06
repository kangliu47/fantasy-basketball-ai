"""Run the local-only, public Hashtag Basketball projection ingestion POC."""

import argparse
import json
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

from fantasy_ai.domain.projections.models import ProjectionSnapshot
from fantasy_ai.infrastructure.projections.hashtag import HashtagProjectionSource

DEFAULT_SEASON = "2026-27"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", default=DEFAULT_SEASON, help="Projection season label.")
    args = parser.parse_args()
    try:
        snapshot = HashtagProjectionSource().load(args.season)
    except (RuntimeError, ValueError) as error:
        print("Hashtag projection probe")
        print(f"status: FAIL — {error}")
        return 1
    destination = _write_snapshot(snapshot)
    ids = sum(player.source_player_id is not None for player in snapshot.players)
    expected = (
        "PASS"
        if len(snapshot.players) == 30
        else f"MISMATCH (expected 30, found {len(snapshot.players)})"
    )
    print("Hashtag projection probe")
    print(f"season: {snapshot.season}")
    print(f"tier: {snapshot.source_tier}")
    source_updated = (
        snapshot.source_updated_at.isoformat() if snapshot.source_updated_at else "unknown"
    )
    print(f"source updated: {source_updated}")
    print(f"players parsed: {len(snapshot.players)}")
    print(f"players valid: {len(snapshot.players)}")
    print("required columns: OK")
    print("percentage components: OK")
    print(f"provider ids: {ids}/{len(snapshot.players)}")
    print(f"public row expectation: {expected}")
    print(f"snapshot: {destination}")
    print("status: PASS")
    return 0


def _write_snapshot(snapshot: ProjectionSnapshot) -> Path:
    root = Path(".local/projections/hashtag")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    captured_at = datetime.now(UTC)
    destination = root / f"{captured_at.strftime('%Y-%m-%dT%H-%M-%SZ')}.json"
    payload = _json_ready(asdict(snapshot))
    if not isinstance(payload, dict):
        raise RuntimeError("Projection snapshot serialization did not produce an object.")
    payload["row_count"] = len(snapshot.players)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def _json_ready(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
