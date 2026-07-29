#!/usr/bin/env python3
"""Migrate an existing agents/{slug} folder into a portable context folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    destination = args.destination.expanduser().resolve()
    if not source.is_dir():
        parser.error(f"source context is not a directory: {source}")
    if destination.exists() and any(destination.iterdir()):
        parser.error(f"destination must be absent or empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(source)
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        files.append(
            {
                "path": rel.as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    context = {
        "schema_version": "1.0",
        "kind": "portable-brand-workspace-context",
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "source_convention": "agents/{slug}",
        "files": files,
        "review_required": [
            "Confirm identity, rights, logos, colors, fonts, claims, and compliance before production."
        ],
    }
    (destination / "context.json").write_text(json.dumps(context, indent=2) + "\n")
    print(f"Migrated {len(files)} files to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
