#!/usr/bin/env python3
"""Install portable Content Foundry dependency tiers without editing source."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+ " + " ".join(command))
    result = subprocess.run(command, cwd=cwd)
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tier",
        choices=("core", "cinematic", "all"),
        default="core",
    )
    args = parser.parse_args()
    run([sys.executable, "-m", "pip", "install", "-r", str(SKILL / "requirements.txt")])
    if args.tier in {"cinematic", "all"}:
        if not shutil.which("npm"):
            parser.error("cinematic setup requires Node.js 22+ and npm")
        run(["npm", "ci"], SKILL / "engines")
        run(["npm", "ci"], SKILL / "engines" / "remotion")
    run([sys.executable, str(SKILL / "scripts" / "doctor.py")])
    run([sys.executable, str(SKILL / "scripts" / "self_test.py")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
