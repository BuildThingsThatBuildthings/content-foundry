#!/usr/bin/env python3
"""Create reproducible Claude/OpenAI skill archives and SHA-256 checksums."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skill" / "content-foundry"
EXCLUDED = {"node_modules", "__pycache__", "runs", "output", ".git"}


def source_files() -> list[Path]:
    return [
        path
        for path in sorted(SOURCE.rglob("*"))
        if path.is_file() and not any(part in EXCLUDED for part in path.relative_to(SOURCE).parts)
    ]


def create_archive(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in source_files():
            rel = source.relative_to(SOURCE)
            info = zipfile.ZipInfo(f"content-foundry/{rel.as_posix()}")
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    archives = []
    for host in ("claude", "openai"):
        path = args.out / f"content-foundry-{args.version}-{host}.zip"
        create_archive(path)
        archives.append(path)
    lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in archives
    ]
    checksum = args.out / "SHA256SUMS"
    checksum.write_text("\n".join(lines) + "\n")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
