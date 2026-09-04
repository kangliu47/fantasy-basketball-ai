"""Persist private discovery JSON locally, without request credentials."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from .config import ESPNConfig
from .response import ESPNView, JsonObject, redact_credentials


def save_snapshot(payload: JsonObject, view: ESPNView, config: ESPNConfig, root: Path) -> Path:
    """Write a complete timestamped file with owner-only access, then publish it."""
    view = ESPNView(view)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    path = (
        root / f"{config.league_id}_{config.season}_{view.value}_{timestamp}_{uuid4().hex[:8]}.json"
    )
    content = json.dumps(
        redact_credentials(payload, config), indent=2, ensure_ascii=False, allow_nan=False
    )
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=root, suffix=".tmp", delete=False
        ) as file:
            temporary = Path(file.name)
            file.write(content + "\n")
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
        return path
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
