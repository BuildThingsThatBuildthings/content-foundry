"""Domain-pack loading and routing defaults."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import FoundryError


PACK_DIR = Path(__file__).resolve().parents[1] / "packs"


def load_pack(name: str) -> dict[str, Any]:
    path = PACK_DIR / f"{name}.json"
    if not path.exists():
        available = ", ".join(sorted(item.stem for item in PACK_DIR.glob("*.json")))
        raise FoundryError(f"unknown pack '{name}'. Available: {available}")
    return json.loads(path.read_text())


def list_packs() -> list[dict[str, Any]]:
    return [load_pack(path.stem) for path in sorted(PACK_DIR.glob("*.json"))]
