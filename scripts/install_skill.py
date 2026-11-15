#!/usr/bin/env python3
"""Install the canonical Content Foundry source tree for either supported host."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "skill" / "content-foundry"
IGNORED_DIRS = {"node_modules", "__pycache__", "runs", "output", ".git"}
IGNORED_FILES = {".DS_Store", "CANONICAL-SHA256"}


def canonical_hash(source: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source)
        if any(part in IGNORED_DIRS for part in rel.parts) or path.name in IGNORED_FILES:
            continue
        digest.update(rel.as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def ignore(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in IGNORED_DIRS or name in IGNORED_FILES
    }


def install(host: str, root: Path) -> Path:
    if host == "claude":
        destination = root / ".claude" / "skills" / "content-foundry"
    elif host == "openai":
        destination = root / ".agents" / "skills" / "content-foundry"
    else:
        raise ValueError(f"unsupported host: {host}")
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, destination, ignore=ignore)
    (destination / "CANONICAL-SHA256").write_text(canonical_hash(SOURCE) + "\n")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, choices=("claude", "openai"))
    parser.add_argument("--root", type=Path, default=Path.home())
    args = parser.parse_args()
    destination = install(args.host, args.root.expanduser().resolve())
    print(f"Installed Content Foundry for {args.host}: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
