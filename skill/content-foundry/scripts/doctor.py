#!/usr/bin/env python3
"""Portable dependency and capability doctor for Content Foundry."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]


def command_probe(command: str, args: list[str], minimum: int | None = None) -> dict:
    executable = shutil.which(command)
    if not executable:
        return {"available": False, "detail": "not found"}
    try:
        result = subprocess.run(
            [executable, *args], capture_output=True, text=True, timeout=15
        )
    except Exception as error:
        return {"available": False, "detail": f"probe failed: {error}"}
    first = (result.stdout or result.stderr).strip().splitlines()
    detail = first[0] if first else f"exit {result.returncode}"
    available = result.returncode == 0
    if minimum is not None:
        match = re.search(r"v?(\d+)", detail)
        if not match or int(match.group(1)) < minimum:
            available = False
            detail += f" (requires >= {minimum})"
    return {"available": available, "detail": detail}


def file_probe(path: Path) -> dict:
    return {
        "available": path.exists(),
        "detail": "ready" if path.exists() else f"missing {path.relative_to(SKILL)}",
    }


def build_report() -> dict:
    checks = {
        "python": {
            "tier": "required",
            "available": sys.version_info >= (3, 10),
            "detail": platform.python_version(),
        },
        "pillow": {
            "tier": "required",
            "available": importlib.util.find_spec("PIL") is not None,
            "detail": "installed" if importlib.util.find_spec("PIL") else "pip install Pillow",
        },
        "fonts": {
            "tier": "required",
            **file_probe(SKILL / "assets" / "fonts" / "PlayfairDisplay.ttf"),
        },
        "schemas": {
            "tier": "required",
            "available": len(list((SKILL / "schemas").glob("*.schema.json"))) >= 5,
            "detail": f"{len(list((SKILL / 'schemas').glob('*.schema.json')))} schemas",
        },
        "openai_host_metadata": {
            "tier": "required",
            **file_probe(SKILL / "agents" / "openai.yaml"),
        },
        "node22": {"tier": "cinematic", **command_probe("node", ["--version"], 22)},
        "npm": {"tier": "cinematic", **command_probe("npm", ["--version"])},
        "ffmpeg": {"tier": "media", **command_probe("ffmpeg", ["-version"])},
        "ffprobe": {"tier": "media", **command_probe("ffprobe", ["-version"])},
        "hyperframes_builder": {
            "tier": "cinematic",
            **file_probe(SKILL / "engines" / "hyperframes" / "build_composition.mjs"),
        },
        "world3d_builder": {
            "tier": "cinematic",
            **file_probe(SKILL / "engines" / "world3d" / "build_world.mjs"),
        },
        "cinematic_dependencies": {
            "tier": "cinematic",
            **file_probe(SKILL / "engines" / "node_modules" / "three" / "build" / "three.module.min.js"),
        },
        "remotion_dependencies": {
            "tier": "cinematic",
            "available": (SKILL / "engines" / "remotion" / "node_modules").exists(),
            "detail": (
                "ready"
                if (SKILL / "engines" / "remotion" / "node_modules").exists()
                else "run npm ci in engines/remotion"
            ),
        },
        "openai_provider": {
            "tier": "optional-provider",
            "available": bool(os.environ.get("OPENAI_API_KEY")),
            "detail": "configured" if os.environ.get("OPENAI_API_KEY") else "not configured",
        },
        "gemini_provider": {
            "tier": "optional-provider",
            "available": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
            "detail": (
                "configured"
                if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
                else "not configured"
            ),
        },
        "postbridge_provider": {
            "tier": "optional-provider",
            "available": bool(
                os.environ.get("POST_BRIDGE_API_KEY")
                or os.environ.get("POSTBRIDGE_API_KEY")
            ),
            "detail": (
                "configured"
                if os.environ.get("POST_BRIDGE_API_KEY")
                or os.environ.get("POSTBRIDGE_API_KEY")
                else "not configured"
            ),
        },
    }
    required_ready = all(
        item["available"] for item in checks.values() if item["tier"] == "required"
    )
    levels = {
        "core": required_ready,
        "cinematic_project": required_ready
        and checks["node22"]["available"]
        and checks["cinematic_dependencies"]["available"],
        "remotion_render": required_ready
        and checks["node22"]["available"]
        and checks["remotion_dependencies"]["available"]
        and checks["ffmpeg"]["available"],
        "media_render": checks["ffmpeg"]["available"] and checks["ffprobe"]["available"],
        "provider_generation": checks["openai_provider"]["available"]
        or checks["gemini_provider"]["available"],
        "scheduling": checks["postbridge_provider"]["available"],
    }
    return {
        "schema_version": "1.0",
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "ok": required_ready,
        "capability_levels": levels,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("Content Foundry doctor")
        print("=" * 62)
        for name, item in report["checks"].items():
            marker = "OK" if item["available"] else "--"
            print(f"{marker} [{item['tier']}] {name}: {item['detail']}")
        print("=" * 62)
        enabled = [
            name for name, available in report["capability_levels"].items() if available
        ]
        print("Ready capability levels: " + ", ".join(enabled))
        if not report["ok"]:
            print("Required core checks failed.")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
