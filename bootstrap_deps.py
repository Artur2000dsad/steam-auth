# -*- coding: utf-8 -*-
"""Install Flask bypassing system SOCKS proxy (Clash/V2Ray etc.)."""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.request

for key in list(os.environ):
    if "proxy" in key.lower():
        os.environ.pop(key, None)

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

urllib.request.getproxies = lambda: {}  # type: ignore[method-assign]


def main() -> int:
    packages = [
        "Flask==3.0.3",
        "Werkzeug==3.0.6",
        "Jinja2==3.1.6",
        "MarkupSafe==3.0.2",
        "itsdangerous==2.2.0",
        "click==8.1.8",
        "blinker==1.9.0",
    ]
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-cache-dir",
        "-i",
        "https://pypi.org/simple",
        *packages,
    ]
    print("[bootstrap] Installing:", " ".join(packages))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print("[bootstrap] pip failed, exit", result.returncode)
        return result.returncode

    import flask  # noqa: F401

    print("[bootstrap] Flask OK:", flask.__version__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
