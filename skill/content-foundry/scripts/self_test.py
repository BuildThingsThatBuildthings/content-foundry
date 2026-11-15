#!/usr/bin/env python3
"""Run an offline, rights-clean Content Foundry smoke test."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
CLI = SKILL / "scripts" / "foundry.py"


def run(*args: str) -> None:
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        text=True,
        capture_output=True,
        timeout=60,
    )
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def main() -> int:
    try:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.md"
            source.write_text(
                "# Rights-clean fixture\nA fictional workshop helps operators improve a workflow."
            )
            run_dir = root / "run"
            run(
                "prepare",
                "--input",
                str(source),
                "--goal",
                "Create a fictional workshop campaign",
                "--pack",
                "event-campaign",
                "--run-dir",
                str(run_dir),
            )
            run("plan", "--run-dir", str(run_dir))
            run("resume", "--run-dir", str(run_dir), "--json")
            required = {
                "job.json",
                "asset-manifest.json",
                "run.json",
                "unified-context.md",
                "claims-ledger.json",
                "creative-system.json",
                "route-plan.json",
                "BRIEF.md",
            }
            missing = [name for name in required if not (run_dir / name).exists()]
            if missing:
                raise RuntimeError("missing smoke artifacts: " + ", ".join(sorted(missing)))
            creative = json.loads((run_dir / "creative-system.json").read_text())
            if len(creative.get("directions", [])) < 3:
                raise RuntimeError("creative system did not create three directions")
    except Exception as error:
        print(f"SELF-TEST FAILED: {error}", file=sys.stderr)
        return 1
    print("SELF-TEST PASSED: offline intake, planning, approval stop, and resume are ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
