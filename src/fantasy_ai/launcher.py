"""Start or reuse the local workspace without requiring a terminal."""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import httpx

APP_URL = "http://127.0.0.1:8765"


def workspace_running() -> bool:
    try:
        with httpx.Client(trust_env=False, timeout=1) as client:
            response = client.get(f"{APP_URL}/api/health")
        data = response.json()
        return (
            response.status_code == 200
            and isinstance(data, dict)
            and data.get("app") == "fantasy-basketball-ai"
        )
    except (httpx.HTTPError, ValueError):
        return False


def start_workspace(root: Path) -> bool:
    if workspace_running():
        return True
    if not (root / "frontend/dist/fantasy-workspace/browser/index.html").exists():
        return False
    local = root / ".local"
    local.mkdir(exist_ok=True, mode=0o700)
    log_path = local / "server.log"
    with log_path.open("ab") as log:
        log_path.chmod(0o600)
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "fantasy_ai.bootstrap:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
                "--no-access-log",
            ],
            cwd=root,
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    for _ in range(80):
        if workspace_running():
            return True
        if process.poll() is not None:
            return False
        time.sleep(0.25)
    process.terminate()
    return False


def main() -> int:
    root = Path.cwd()
    try:
        ready = start_workspace(root)
    except OSError:
        ready = False
    if ready:
        webbrowser.open(APP_URL)
        return 0
    local = root / ".local"
    local.mkdir(exist_ok=True, mode=0o700)
    error_page = local / "startup-help.html"
    error_page.write_text(
        '<!doctype html><meta charset="utf-8"><title>Fantasy Basketball</title>'
        "<style>body{font:18px system-ui;max-width:600px;margin:12vh auto;"
        "padding:24px;color:#163b39}"
        "a{color:#11746b}</style><h1>The workspace could not start</h1>"
        "<p>The local app may need a rebuild, or another program may be using its port.</p>"
        "<p>Return to the project in Codex and ask to restart the workspace. "
        "Your league data and saved connection are unchanged.</p>"
    )
    webbrowser.open(error_page.as_uri())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
