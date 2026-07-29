#!/usr/bin/env python3
"""Cross-platform Remotion render wrapper."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
ENGINE = SKILL / "engines" / "remotion"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("props", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("composition", nargs="?", default="Walkthrough")
    parser.add_argument("extra", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.props.exists():
        parser.error(f"props file not found: {args.props}")
    if not shutil.which("npx"):
        parser.error("npx not found; install Node.js")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "npx",
        "remotion",
        "render",
        "src/index.ts",
        args.composition,
        str(args.output.resolve()),
        f"--props={args.props.resolve()}",
        *args.extra,
    ]
    return subprocess.run(command, cwd=ENGINE).returncode


if __name__ == "__main__":
    raise SystemExit(main())
