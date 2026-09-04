"""Generate a double-click local Mac app bundle after building the frontend."""

import plistlib
from pathlib import Path


def create_launcher(root: Path) -> Path:
    bundle = root / "Fantasy Basketball.app"
    executable = bundle / "Contents/MacOS/FantasyBasketball"
    executable.parent.mkdir(parents=True, exist_ok=True)
    (bundle / "Contents/Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleName": "Fantasy Basketball",
                "CFBundleDisplayName": "Fantasy Basketball",
                "CFBundleIdentifier": "local.fantasy-basketball-ai.workspace",
                "CFBundleExecutable": "FantasyBasketball",
                "CFBundlePackageType": "APPL",
                "CFBundleVersion": "1",
                "CFBundleShortVersionString": "0.2.0",
                "LSUIElement": True,
            }
        )
    )
    executable.write_text(
        "#!/bin/sh\nset -eu\n"
        'PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"\n'
        'cd "$PROJECT_ROOT"\n'
        'exec "$PROJECT_ROOT/.venv/bin/python" -m fantasy_ai.launcher\n'
    )
    executable.chmod(0o755)
    return bundle


if __name__ == "__main__":
    print(create_launcher(Path.cwd()))
