#!/usr/bin/env python3
"""Run the rights-clean cross-domain Content Foundry contract suite."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "content-foundry"
CLI = SKILL / "scripts" / "foundry.py"
CASES = ROOT / "evaluation" / "fixtures" / "cases.json"
INSTALLER = ROOT / "scripts" / "install_skill.py"


def invoke(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        timeout=90,
    )


def make_source(case: dict, root: Path) -> Path:
    kind = case["kind"]
    if kind == "repository":
        source = root / "repository"
        source.mkdir()
        (source / ".git").mkdir()
        (source / "README.md").write_text(
            "# Fictional product\nA rights-clean test interface for workflow planning."
        )
        return source
    if kind == "csv":
        source = root / "data.csv"
        source.write_text("week,completed\n1,12\n2,17\n3,21\n")
        return source
    if kind == "transcript":
        source = root / "transcript.txt"
        source.write_text(
            "HOST: Today we learn a fictional three-step workflow.\n"
            "HOST: First capture, then verify, then export.\n"
        )
        return source
    if kind == "context":
        source = root / "context"
        source.mkdir()
        (source / "_MANIFEST.md").write_text(
            "# Incomplete fictional brand\n<!-- Missing colors and logo by design. -->"
        )
        return source
    if kind == "unusable":
        source = root / "unusable"
        source.mkdir()
        (source / "empty.txt").write_text("")
        (source / "unsupported.bin").write_bytes(b"rights-clean unsupported fixture")
        return source
    source = root / "source.md"
    source.write_text(
        "# Rights-clean fictional source\n"
        "The assignment uses invented people, organizations, facts, and outcomes."
    )
    return source


def run_case(case: dict, root: Path) -> dict:
    case_root = root / case["id"]
    case_root.mkdir()
    source = make_source(case, case_root)
    run_dir = case_root / "run"
    prepared = invoke(
        "prepare",
        "--input",
        str(source),
        "--goal",
        case["goal"],
        "--pack",
        case["pack"],
        "--domain",
        case["domain"],
        "--run-dir",
        str(run_dir),
    )
    if case.get("expected") == "blocked":
        manifest = json.loads((run_dir / "asset-manifest.json").read_text())
        state = json.loads((run_dir / "run.json").read_text())
        ok = (
            prepared.returncode != 0
            and state["status"] == "blocked"
            and bool(manifest["unsupported"])
        )
        return {"id": case["id"], "ok": ok, "expected": "blocked"}
    if prepared.returncode:
        return {"id": case["id"], "ok": False, "error": prepared.stderr}
    planned = invoke("plan", "--run-dir", str(run_dir))
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
    ok = planned.returncode == 0 and all((run_dir / name).exists() for name in required)
    detail: dict[str, object] = {"id": case["id"], "ok": ok}

    if case.get("expected") == "provider-fallback":
        clean_env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "OPENAI_API_KEY",
                "GEMINI_API_KEY",
                "GOOGLE_API_KEY",
                "HEYGEN_API_KEY",
            }
        }
        adapters = invoke("adapters", "--json", env=clean_env)
        payload = json.loads(adapters.stdout)
        providers = [
            item
            for item in payload["adapters"]
            if item["name"] in {"stills-openai", "stills-gemini"}
        ]
        ok = ok and all(
            not item["probe"]["available"] and item["fallback"] for item in providers
        )
        detail["ok"] = ok
    elif case.get("expected") == "portable-resume":
        moved = case_root / "moved"
        shutil.copytree(run_dir, moved)
        resumed = invoke("resume", "--run-dir", str(moved), "--json")
        payload = json.loads(resumed.stdout)
        ok = ok and payload["portable"] and payload["next_stage"] == "research"
        detail["ok"] = ok
    elif case.get("expected") == "host-conformance":
        host_root = case_root / "hosts"
        for host in ("claude", "openai"):
            installed = subprocess.run(
                [
                    sys.executable,
                    str(INSTALLER),
                    "--host",
                    host,
                    "--root",
                    str(host_root),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            ok = ok and installed.returncode == 0
        claude_hash = (
            host_root / ".claude" / "skills" / "content-foundry" / "CANONICAL-SHA256"
        ).read_text()
        openai_hash = (
            host_root / ".agents" / "skills" / "content-foundry" / "CANONICAL-SHA256"
        ).read_text()
        detail["ok"] = ok and claude_hash == openai_hash
    return detail


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cases = json.loads(CASES.read_text())["cases"]
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        results = [run_case(case, root) for case in cases]
    report = {
        "schema_version": "1.0",
        "ok": all(item["ok"] for item in results),
        "passed": sum(bool(item["ok"]) for item in results),
        "total": len(results),
        "cases": results,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
