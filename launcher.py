#!/usr/bin/env python3
"""Start the EXIF Location Patcher dev server and open it in the browser.

Usage: python launcher.py [port]   (default port: 8000)

Runs ``manage.py runserver`` with the project's .venv interpreter when it
exists, so the launcher works no matter which Python starts it.
"""

import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

OBJ_PROJECT_DIR = Path(__file__).resolve().parent
OBJ_VENV_PYTHON = OBJ_PROJECT_DIR / ".venv" / "bin" / "python"
INT_DEFAULT_PORT = 8000


def open_browser_when_ready(str_url: str, flt_timeout_s: float = 15.0) -> None:
    """Open the URL in the default browser once the server answers."""
    flt_deadline = time.monotonic() + flt_timeout_s
    while time.monotonic() < flt_deadline:
        try:
            urllib.request.urlopen(str_url, timeout=1)
            webbrowser.open(str_url)
            return
        except OSError:
            time.sleep(0.5)


def main() -> int:
    int_port = int(sys.argv[1]) if len(sys.argv) > 1 else INT_DEFAULT_PORT
    str_python = str(OBJ_VENV_PYTHON) if OBJ_VENV_PYTHON.exists() else sys.executable
    str_url = f"http://127.0.0.1:{int_port}/"

    threading.Thread(target=open_browser_when_ready, args=(str_url,), daemon=True).start()
    print(f"EXIF Location Patcher running at {str_url}  (Ctrl+C to stop)")
    try:
        return subprocess.call(
            [str_python, "manage.py", "runserver", f"127.0.0.1:{int_port}"],
            cwd=OBJ_PROJECT_DIR,
        )
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
