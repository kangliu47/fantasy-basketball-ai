"""Command-line entry point for the read-only connectivity spike."""

import argparse
import logging
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from fantasy_ai.providers.espn.client import LOGGER, ESPNClient
from fantasy_ai.providers.espn.config import ConfigurationError, ESPNConfig
from fantasy_ai.providers.espn.errors import ESPNError
from fantasy_ai.providers.espn.response import ESPNView
from fantasy_ai.providers.espn.snapshots import save_snapshot


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Save read-only ESPN league snapshots locally.")
    parser.add_argument(
        "--view",
        action="append",
        choices=[view.value for view in ESPNView],
        help="View to fetch; repeat to select several. Default: all three views.",
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/espn"))
    args = parser.parse_args(argv)
    views = list(dict.fromkeys(ESPNView(value) for value in (args.view or list(ESPNView))))

    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("%(asctime)sZ %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S")
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    old_level, old_propagate = LOGGER.level, LOGGER.propagate
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False
    try:
        config = ESPNConfig.from_env(args.env_file)
        with ESPNClient(config) as client:
            for view in views:
                payload = client.get_view(view)
                path = save_snapshot(payload, view, config, args.output_dir)
                print(f"Saved {view.value}: {path}")
        return 0
    except ConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    except ESPNError as error:
        print(f"ESPN error: {error}", file=sys.stderr)
        return 1
    except OSError:
        print(
            "Local file error: check the environment file and output directory permissions.",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        print("Probe interrupted.", file=sys.stderr)
        return 130
    finally:
        LOGGER.removeHandler(handler)
        handler.close()
        LOGGER.setLevel(old_level)
        LOGGER.propagate = old_propagate


if __name__ == "__main__":
    raise SystemExit(main())
