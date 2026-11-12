#!/usr/bin/env python3
"""Start the EXIF Location Patcher dev server and open it in the browser.

Usage: uv run launcher.py [port]   (default port: 8000)

Runs Django in the current Python environment, so it works the same on
Linux, macOS and Windows, and as the installed ``exif-location-patcher``
command.
"""

import os
import sys
import threading
import time
import urllib.request
import webbrowser

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


def main() -> None:
    """Parse the optional port argument and run the dev server."""
    int_port = int(sys.argv[1]) if len(sys.argv) > 1 else INT_DEFAULT_PORT
    str_url = f"http://127.0.0.1:{int_port}/"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "epl_config.settings")

    # Django's auto-reloader re-runs this script in a child process (with
    # RUN_MAIN=true); only the first run should announce and open the browser.
    if os.environ.get("RUN_MAIN") != "true":
        print(f"EXIF Location Patcher running at {str_url}  (Ctrl+C to stop)")
        threading.Thread(target=open_browser_when_ready, args=(str_url,), daemon=True).start()

    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "runserver", f"127.0.0.1:{int_port}"])


if __name__ == "__main__":
    main()
