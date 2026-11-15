"""Universal job preparation and resumable run state.

This module is the external seam shared by the Claude and OpenAI/Codex host
packages. It intentionally uses the Python standard library so a clean install
can inventory inputs before optional creative dependencies are installed.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
STAGES = (
    "ingest",
    "unify",
    "research",
    "brief",
    "route",
    "generate",
    "composite",
    "qc",
    "export",
    "deploy_schedule",
)
URL_RE = re.compile(r"^https?://", re.IGNORECASE)
SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", ".gitkeep"}
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "__MACOSX"}
SUPPORTED_EXTENSIONS = {
    ".aac": ("audio", "transcribe"),
    ".avi": ("video", "transcribe"),
    ".csv": ("data", "extract"),
    ".css": ("code", "inspect_source"),
    ".docx": ("document", "extract"),
    ".flac": ("audio", "transcribe"),
    ".gif": ("image", "describe"),
    ".heic": ("image", "describe"),
    ".html": ("document", "extract"),
    ".jpeg": ("image", "describe"),
    ".jpg": ("image", "describe"),
    ".json": ("data", "extract"),
    ".js": ("code", "inspect_source"),
    ".jsx": ("code", "inspect_source"),
    ".m4a": ("audio", "transcribe"),
    ".m4v": ("video", "transcribe"),
    ".md": ("text", "read_or_fetch"),
    ".mov": ("video", "transcribe"),
    ".mp3": ("audio", "transcribe"),
    ".mp4": ("video", "transcribe"),
    ".numbers": ("data", "extract"),
    ".pdf": ("document", "extract"),
    ".py": ("code", "inspect_source"),
    ".png": ("image", "describe"),
    ".pptx": ("document", "extract"),
    ".rtf": ("text", "read_or_fetch"),
    ".scss": ("code", "inspect_source"),
    ".sh": ("code", "inspect_source"),
    ".svg": ("image", "describe"),
    ".tif": ("image", "describe"),
    ".tiff": ("image", "describe"),
    ".tsv": ("data", "extract"),
    ".ts": ("code", "inspect_source"),
    ".tsx": ("code", "inspect_source"),
    ".txt": ("text", "read_or_fetch"),
    ".wav": ("audio", "transcribe"),
    ".webm": ("video", "transcribe"),
    ".webp": ("image", "describe"),
    ".xlsx": ("data", "extract"),
    ".xml": ("data", "extract"),
    ".yaml": ("data", "extract"),
    ".yml": ("data", "extract"),
}
ASSET_POLICY_ROOT = Path(__file__).resolve().parents[1] / "assets"
BLOCKED_AUDIO_POLICY = ASSET_POLICY_ROOT / "audio-denylist.json"


class FoundryError(RuntimeError):
    """A user-correctable pipeline failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def blocked_audio_fingerprints() -> dict[str, dict[str, str]]:
    """Return globally rejected audio hashes from the portable skill policy."""
    if not BLOCKED_AUDIO_POLICY.exists():
        return {}
    try:
        payload = json.loads(BLOCKED_AUDIO_POLICY.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise FoundryError(f"invalid blocked-audio policy: {BLOCKED_AUDIO_POLICY}: {exc}") from exc
    blocked = payload.get("blocked_sha256", {})
    if not isinstance(blocked, dict):
        raise FoundryError(f"invalid blocked-audio policy: blocked_sha256 must be an object")
    return blocked


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower().strip()).strip("-")


def _copy_to_cache(source: Path, cache_root: Path, rel: Path) -> Path:
    target = cache_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or sha256_file(target) != sha256_file(source):
        shutil.copy2(source, target)
    return target


def _rights(kind: str) -> dict[str, str]:
    basis = "user_supplied" if kind in {"local_file", "repository", "text"} else "unverified_url"
    return {"status": "unknown", "basis": basis, "review": "required_before_publication"}


def _image_dimensions(path: Path, extension: str) -> dict[str, int] | None:
    if extension not in {
        ".gif",
        ".heic",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
        ".webp",
    }:
        return None
    try:
        from PIL import Image

        with Image.open(path) as image:
            return {"width": int(image.width), "height": int(image.height)}
    except Exception:
        return None


def _file_record(
    source: Path,
    rel: Path,
    cache_root: Path,
    input_index: int,
    provenance_kind: str = "local_file",
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    stat = source.stat()
    extension = source.suffix.lower()
    digest = sha256_file(source)
    category_and_handler = SUPPORTED_EXTENSIONS.get(extension)
    is_blocked_audio = bool(
        category_and_handler
        and category_and_handler[0] == "audio"
        and digest in blocked_audio_fingerprints()
    )
    staged = None if is_blocked_audio else _copy_to_cache(
        source, cache_root / f"input-{input_index:02d}", rel
    )
    base = {
        "id": f"asset-{digest[:16]}",
        "path": rel.as_posix(),
        "source": str(source.resolve()),
        "staged_path": str(staged.resolve()) if staged else None,
        "extension": extension or "(none)",
        "size_bytes": stat.st_size,
        "sha256": digest,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "mime_type": mimetypes.guess_type(source.name)[0] or "application/octet-stream",
        "provenance": {
            "kind": provenance_kind,
            "input_index": input_index,
            "captured_at": utc_now(),
        },
        "rights": _rights(provenance_kind),
        "intended_role": "unclassified",
        "dimensions": _image_dimensions(source, extension),
        "duration_seconds": None,
        "extraction": {
            "status": "pending",
            "method": None,
            "artifact": None,
        },
        "transcript": {
            "status": "not_applicable",
            "method": None,
            "artifact": None,
        },
    }
    if stat.st_size == 0:
        return None, {
            **base,
            "reason": "empty file",
            "preserved": True,
        }
    if extension not in SUPPORTED_EXTENSIONS:
        unsupported = {
            **base,
            "reason": "unrecognized extension",
            "preserved": True,
        }
        return None, unsupported
    if is_blocked_audio:
        policy = blocked_audio_fingerprints()[digest]
        return None, {
            **base,
            "reason": "blocked audio fingerprint",
            "policy": policy,
            "preserved": False,
            "status": "blocked",
        }
    category, handler = SUPPORTED_EXTENSIONS[extension]
    transcript_status = "pending" if handler == "transcribe" else "not_applicable"
    return {
        **base,
        "category": category,
        "unify_handler": handler,
        "status": "inventoried",
        "transcript": {
            "status": transcript_status,
            "method": None,
            "artifact": None,
        },
    }, None


def _scan_directory(
    directory: Path,
    cache_root: Path,
    input_index: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    assets: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    is_repository = (directory / ".git").exists()
    if is_repository:
        repo_marker = {
            "id": f"repository-{sha256_text(str(directory.resolve()))[:16]}",
            "path": directory.name,
            "source": str(directory.resolve()),
            "staged_path": None,
            "category": "repository",
            "unify_handler": "inspect_repository",
            "status": "inventoried",
            "provenance": {
                "kind": "repository",
                "input_index": input_index,
                "captured_at": utc_now(),
            },
            "rights": _rights("repository"),
            "intended_role": "source_context",
            "dimensions": None,
            "duration_seconds": None,
            "extraction": {
                "status": "pending",
                "method": None,
                "artifact": None,
            },
            "transcript": {
                "status": "not_applicable",
                "method": None,
                "artifact": None,
            },
        }
        assets.append(repo_marker)
    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(
            item
            for item in dirs
            if item not in SKIP_DIRS and not item.startswith(".")
        )
        for name in sorted(files):
            if name in SKIP_NAMES or name.startswith("._"):
                continue
            source = Path(root) / name
            rel = source.relative_to(directory)
            record, rejected = _file_record(
                source,
                rel,
                cache_root,
                input_index,
                "repository" if is_repository else "local_file",
            )
            if record:
                assets.append(record)
            if rejected:
                unsupported.append(rejected)
    return assets, unsupported


def inventory_inputs(
    inputs: Iterable[str],
    run_dir: Path,
) -> dict[str, Any]:
    inputs = list(inputs)
    assets: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    cache_root = run_dir / "inputs"
    cache_root.mkdir(parents=True, exist_ok=True)

    for index, raw in enumerate(inputs, start=1):
        if raw.startswith("text:"):
            value = raw.removeprefix("text:")
            staged = cache_root / f"input-{index:02d}" / "input.txt"
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(value)
            assets.append(
                {
                    "id": f"text-{sha256_text(value)[:16]}",
                    "path": "input.txt",
                    "source": "inline",
                    "staged_path": str(staged.resolve()),
                    "category": "text",
                    "unify_handler": "read_or_fetch",
                    "size_bytes": len(value.encode("utf-8")),
                    "sha256": sha256_text(value),
                    "status": "inventoried",
                    "provenance": {
                        "kind": "text",
                        "input_index": index,
                        "captured_at": utc_now(),
                    },
                    "rights": _rights("text"),
                    "intended_role": "request_context",
                    "dimensions": None,
                    "duration_seconds": None,
                    "extraction": {
                        "status": "ready",
                        "method": "inline_text",
                        "artifact": str(staged.resolve()),
                    },
                    "transcript": {
                        "status": "not_applicable",
                        "method": None,
                        "artifact": None,
                    },
                }
            )
            continue
        if URL_RE.match(raw):
            staged = cache_root / f"input-{index:02d}" / "url.txt"
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(raw)
            assets.append(
                {
                    "id": f"url-{sha256_text(raw)[:16]}",
                    "path": raw,
                    "source": raw,
                    "staged_path": str(staged.resolve()),
                    "category": "url",
                    "unify_handler": "fetch",
                    "size_bytes": len(raw.encode("utf-8")),
                    "sha256": sha256_text(raw),
                    "status": "inventoried",
                    "provenance": {
                        "kind": "url",
                        "input_index": index,
                        "captured_at": utc_now(),
                    },
                    "rights": _rights("url"),
                    "intended_role": "research_source",
                    "dimensions": None,
                    "duration_seconds": None,
                    "extraction": {
                        "status": "pending",
                        "method": None,
                        "artifact": None,
                    },
                    "transcript": {
                        "status": "not_applicable",
                        "method": None,
                        "artifact": None,
                    },
                }
            )
            continue

        source = Path(raw).expanduser()
        if not source.exists():
            raise FoundryError(f"input does not exist and is not a URL or text input: {raw}")
        if source.is_dir():
            found, rejected = _scan_directory(source, cache_root, index)
            assets.extend(found)
            unsupported.extend(rejected)
        else:
            record, rejected = _file_record(
                source,
                Path(source.name),
                cache_root,
                index,
            )
            if record:
                assets.append(record)
            if rejected:
                unsupported.append(rejected)

    by_hash: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        digest = asset.get("sha256")
        if digest:
            by_hash.setdefault(digest, []).append(asset)
    duplicates = []
    for digest, records in by_hash.items():
        if len(records) <= 1:
            continue
        primary = records[0]["id"]
        duplicates.append({"sha256": digest, "asset_ids": [r["id"] for r in records]})
        for duplicate in records[1:]:
            duplicate["duplicate_of"] = primary

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "assets": assets,
        "unsupported": unsupported,
        "duplicates": duplicates,
        "summary": {
            "inputs": len(inputs),
            "assets": len(assets),
            "unsupported": len(unsupported),
            "duplicates": sum(len(item["asset_ids"]) - 1 for item in duplicates),
            "by_category": {
                category: sum(1 for asset in assets if asset["category"] == category)
                for category in sorted({asset["category"] for asset in assets})
            },
        },
    }


def build_job(
    inputs: list[str],
    goal: str,
    channels: list[str],
    budget: float,
    context: str | None = None,
    domain: str = "general",
    pack: str = "general-social",
) -> dict[str, Any]:
    if not goal.strip():
        raise FoundryError("goal cannot be blank")
    if budget < 0:
        raise FoundryError("budget ceiling cannot be negative")
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "objective": goal.strip(),
        "conversion_action": None,
        "audience": {"description": None, "segments": []},
        "inputs": [{"value": value} for value in inputs],
        "context": {"path": context, "kind": "portable_folder" if context else "none"},
        "domain": domain,
        "pack": pack,
        "deliverables": [],
        "channels": channels,
        "research": {"depth": "auto", "citations_required": True},
        "claims_policy": {
            "mode": "source_grounded",
            "uncited_numbers": "block",
            "invented_proof": "block",
        },
        "art_direction": {"required": True, "concept_count": 3},
        "providers": {"preferences": [], "allow_fallback": True},
        "budget": {"currency": "USD", "ceiling": float(budget), "spent": 0.0},
        "approvals": {
            "brief_before_spend": True,
            "preview_before_render": True,
            "publish_requires_explicit_approval": True,
        },
        "distribution": {
            "deploy": "optional",
            "schedule": "draft_first",
            "minimum_review_hours": 36,
        },
    }


def _new_run_state(job_path: Path, manifest_path: Path) -> dict[str, Any]:
    stages = {
        name: {
            "status": "done" if name == "ingest" else "pending",
            "started_at": utc_now() if name == "ingest" else None,
            "completed_at": utc_now() if name == "ingest" else None,
            "attempts": 1 if name == "ingest" else 0,
            "artifacts": [manifest_path.name] if name == "ingest" else [],
            "receipts": [],
            "failure": None,
        }
        for name in STAGES
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "job": job_path.name,
        "status": "active",
        "current_stage": "unify",
        "stages": stages,
        "costs": {"currency": "USD", "total": 0.0, "items": []},
        "deployments": [],
        "scheduling": [],
    }


def prepare_run(
    *,
    inputs: list[str],
    goal: str,
    channels: list[str],
    budget: float,
    run_dir: Path,
    context: str | None = None,
    domain: str = "general",
    pack: str = "general-social",
) -> dict[str, Path]:
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    job = build_job(inputs, goal, channels, budget, context, domain, pack)
    job_path = run_dir / "job.json"
    manifest_path = run_dir / "asset-manifest.json"
    run_path = run_dir / "run.json"
    job_path.write_text(json.dumps(job, indent=2) + "\n")
    manifest = inventory_inputs(inputs, run_dir)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    state = _new_run_state(job_path, manifest_path)
    if not manifest["assets"]:
        state["status"] = "blocked"
        state["current_stage"] = "ingest"
        state["stages"]["ingest"]["status"] = "blocked"
        state["stages"]["ingest"]["completed_at"] = None
        state["stages"]["ingest"]["failure"] = {
            "code": "NO_USABLE_INPUTS",
            "message": (
                "No usable inputs were found; preserved unsupported entries "
                "in the manifest."
            ),
        }
    run_path.write_text(json.dumps(state, indent=2) + "\n")
    if not manifest["assets"]:
        raise FoundryError(
            "no usable inputs found; asset-manifest.json preserves everything inspected"
        )
    return {"job": job_path, "manifest": manifest_path, "run": run_path}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def _load_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    job_path = run_dir / "job.json"
    manifest_path = run_dir / "asset-manifest.json"
    run_path = run_dir / "run.json"
    missing = [
        str(path)
        for path in (job_path, manifest_path, run_path)
        if not path.exists()
    ]
    if missing:
        raise FoundryError(f"run is not prepared; missing: {', '.join(missing)}")
    return (
        json.loads(job_path.read_text()),
        json.loads(manifest_path.read_text()),
        json.loads(run_path.read_text()),
    )


def _complete_stage(
    state: dict[str, Any],
    name: str,
    artifacts: list[Path],
    status: str = "done",
    run_dir: Path | None = None,
) -> None:
    stage = state["stages"][name]
    stage["status"] = status
    stage["started_at"] = stage.get("started_at") or utc_now()
    stage["completed_at"] = utc_now() if status == "done" else None
    stage["attempts"] = int(stage.get("attempts") or 0) + 1
    portable = []
    for path in artifacts:
        resolved = path.resolve()
        if run_dir:
            try:
                portable.append(str(resolved.relative_to(run_dir.resolve())))
                continue
            except ValueError:
                pass
        portable.append(str(resolved))
    stage["artifacts"] = portable
    stage["failure"] = None


def _unify_manifest(manifest: dict[str, Any]) -> str:
    lines = [
        "# Unified Context",
        "",
        "This file is deterministic intake context. Host-resolved descriptions,",
        "transcripts, page captures, and citations must be added before approval.",
        "",
    ]
    for asset in manifest.get("assets", []):
        lines.extend(
            [
                f"## {asset['id']}",
                "",
                f"- Category: `{asset['category']}`",
                f"- Source: `{asset['source']}`",
                f"- Provenance: `{asset['provenance']['kind']}`",
                f"- Rights: `{asset['rights']['status']}`",
                f"- Intended role: `{asset.get('intended_role', 'unclassified')}`",
            ]
        )
        staged = asset.get("staged_path")
        if (
            staged
            and asset["category"] in {"text", "data", "document", "code"}
            and Path(staged).suffix.lower()
            in {
                ".txt",
                ".md",
                ".csv",
                ".tsv",
                ".json",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".py",
                ".css",
                ".scss",
                ".sh",
            }
        ):
            body = Path(staged).read_text(encoding="utf-8", errors="replace")[:6000]
            lines.extend(["", "```text", body, "```"])
        if asset["unify_handler"] in {
            "describe",
            "transcribe",
            "fetch",
            "inspect_repository",
            "inspect_source",
        }:
            lines.extend(
                [
                    "",
                    f"<!-- HOST_ACTION: {asset['unify_handler']} this asset; "
                    "record evidence and any claims before approval. -->",
                ]
            )
        lines.append("")
    if manifest.get("unsupported"):
        lines.extend(["## Preserved unsupported inputs", ""])
        for item in manifest["unsupported"]:
            lines.append(f"- `{item['path']}` — {item['reason']}")
        lines.append("")
    return "\n".join(lines)


def _claims_ledger(manifest: dict[str, Any]) -> dict[str, Any]:
    sources = []
    for asset in manifest.get("assets", []):
        sources.append(
            {
                "source_id": asset["id"],
                "location": asset["source"],
                "kind": asset["provenance"]["kind"],
                "rights_status": asset["rights"]["status"],
                "accessed_at": asset["provenance"]["captured_at"],
                "verification_status": (
                    "pending"
                    if asset["unify_handler"]
                    in {
                        "describe",
                        "transcribe",
                        "fetch",
                        "inspect_repository",
                        "inspect_source",
                    }
                    else "local_source"
                ),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "policy": {
            "uncited_numbers": "block",
            "invented_proof": "block",
            "stale_facts": "block",
        },
        "sources": sources,
        "claims": [],
        "blocking_gaps": [
            {
                "code": "HOST_RESEARCH_REQUIRED",
                "message": "Resolve pending source actions and record claims before approval.",
            }
        ]
        if any(item["verification_status"] == "pending" for item in sources)
        else [],
    }


def _brief_markdown(
    job: dict[str, Any],
    manifest: dict[str, Any],
    creative: dict[str, Any],
    route: dict[str, Any],
) -> str:
    sources = "\n".join(
        f"- `{item['id']}` — {item['source']}"
        for item in manifest.get("assets", [])
    )
    directions = "\n".join(
        f"- **{item['name']}** — {item['scene_construction']}; "
        f"{item['camera_behavior']}; {item['metaphor']}."
        for item in creative["directions"]
    )
    engines = ", ".join(route["engines"])
    tool_rows = []
    for name in route["engines"]:
        plan = route.get("plans", {}).get(name, {})
        capabilities = ", ".join(plan.get("capabilities", [])) or "adapter-defined"
        limitation = "; ".join(plan.get("limitations", [])) or "none at planning time"
        estimate = plan.get("estimated_cost", {})
        amount = estimate.get("amount")
        cost = (
            f"{estimate.get('currency', 'USD')} {float(amount):.2f}"
            if amount is not None
            else "provider quote required"
        )
        fallback = route.get("fallbacks", {}).get(name, "no silent fallback")
        tool_rows.append(
            f"| **{name}** | {capabilities} | {fallback} | {cost} | {limitation} |"
        )
    supporting_tools = (
        (
            "Claude/OpenAI host adapters",
            "Interpret the request, perform host-native research, and maintain approval conversations around the same run ledger.",
            "Either host can operate the canonical skill.",
            "USD 0.00 plus host plan",
            "Host parity is checked by manifest conformance.",
        ),
        (
            "native brand-context module",
            "Loads portable identity, palette, voice, typography, marks, claims rules, and anti-reference truth; can import Brand Brain-compatible context.",
            "Create an incomplete context report and block brand-sensitive export.",
            "USD 0.00",
            "Never requires a private Brand Brain installation.",
        ),
        (
            "RyVibes-derived QC",
            "Blocks generic slop, weak hooks, poor hierarchy, low specificity, and directions that differ only by palette.",
            "Human visual review remains mandatory.",
            "USD 0.00",
            "Rights-safe rules only; no private dependency.",
        ),
        (
            "media resolver",
            "Selects official logos, headshots, fonts, music, SFX, voice, grades, licenses, and provenance before generation.",
            "Preserve unresolved media slots and block publication.",
            "source dependent",
            "No guessed or scraped media may ship.",
        ),
        (
            "OpenAI/Gemini image adapters",
            "Generate or edit source-grounded base imagery when the route requires it; each call returns provider, model, cost, and hash receipts.",
            "Use the alternate provider, supplied media, or deterministic composition.",
            "provider quote required",
            "Credential and rights approval required before spend.",
        ),
        (
            "Pretext",
            "Computes deterministic safe-zone-aware line breaks and measured typography inside deterministic compositions.",
            "Use the same font metrics through the local compositor.",
            "USD 0.00",
            "Typography must still pass visual QC.",
        ),
        (
            "Pillow compositor",
            "Applies exact logos, colors, sponsor marks, facts, disclosures, and export-safe raster treatments.",
            "No raster export if Pillow is unavailable.",
            "USD 0.00",
            "Generated imagery never redraws official marks.",
        ),
        (
            "FFmpeg/FFprobe",
            "Conforms, stitches, loudness-normalizes, captions, encodes, adapts channels, extracts thumbnails, and runs technical QC.",
            "Export source projects with an explicit render blocker.",
            "USD 0.00",
            "Required for final media renders.",
        ),
        (
            "Netlify/Vercel adapters",
            "Deploy approved unlisted review pages and interactive worlds and record deployment receipts.",
            "Export a local review package.",
            "provider plan dependent",
            "Deployment is a separate approval-gated state.",
        ),
        (
            "GitHub",
            "Distributes the MIT source, semantic releases, host packages, checksums, changelog, and fixture conformance checks.",
            "Local reproducible release archives.",
            "provider plan dependent",
            "Private campaign media is excluded from the public repository.",
        ),
    )
    for name, role, fallback, cost, limitation in supporting_tools:
        tool_rows.append(
            f"| **{name}** | {role} | {fallback} | {cost} | {limitation} |"
        )
    tools = "\n".join(tool_rows)
    return f"""# Content Foundry Brief

**Status:** DRAFT — APPROVAL REQUIRED BEFORE GENERATION  
**Objective:** {job['objective']}  
**Domain pack:** {job['pack']}  
**Channels:** {', '.join(job.get('channels', [])) or 'not specified'}  
**Budget ceiling:** {job['budget']['currency']} {job['budget']['ceiling']:.2f}

## Conversion intent

One audience, one promise, and one conversion action. The host must fill audience and
conversion action from cited source evidence before approval.

## Strategic hook

{creative['strategic_hook']}

## Emotional promise

{creative['emotional_promise']}

## Structurally distinct directions

{directions}

## Proposed route

{engines}

Fallbacks are explicit in `route-plan.json`. A fallback may preserve the message but must
record the capability difference; it may not masquerade as the requested engine.

## Complete tool composition

| Tool or adapter | How it is used in the composition | Fallback | Planned cost | Current limitation |
|---|---|---|---|---|
{tools}

Supporting tools may not bypass the run ledger even when invoked by an engine adapter.

## Sources

{sources}

## Approval gate

Before approval: resolve host actions in `unified-context.md`, populate the claims ledger,
confirm rights, select a creative direction, state deliverables, and record estimated cost.
No Stage 6 working directory exists until this gate passes.
"""


def plan_run(run_dir: Path) -> dict[str, Path]:
    from .adapters import registry, write_registry_snapshot
    from .creative import draft_creative_system
    from .packs import load_pack

    run_dir = run_dir.resolve()
    job, manifest, state = _load_run(run_dir)
    pack = load_pack(job["pack"])
    creative = draft_creative_system(job, pack)
    adapters = registry()
    engines = pack["engines"]
    route = {
        "schema_version": SCHEMA_VERSION,
        "status": "proposed",
        "pack": pack["name"],
        "engines": engines,
        "fallbacks": pack.get("fallbacks", {}),
        "plans": {
            name: adapters[name].plan(job, creative)
            for name in engines
            if name in adapters
        },
        "missing_adapters": [name for name in engines if name not in adapters],
        "approval_required": True,
    }
    unified_path = run_dir / "unified-context.md"
    claims_path = run_dir / "claims-ledger.json"
    creative_path = run_dir / "creative-system.json"
    route_path = run_dir / "route-plan.json"
    brief_path = run_dir / "BRIEF.md"
    adapters_path = run_dir / "adapter-status.json"
    unified_path.write_text(_unify_manifest(manifest))
    _write_json(claims_path, _claims_ledger(manifest))
    _write_json(creative_path, creative)
    _write_json(route_path, route)
    brief_path.write_text(_brief_markdown(job, manifest, creative, route))
    write_registry_snapshot(adapters_path)

    _complete_stage(state, "unify", [unified_path], run_dir=run_dir)
    _complete_stage(
        state, "research", [claims_path], status="needs_host", run_dir=run_dir
    )
    _complete_stage(
        state,
        "brief",
        [brief_path, creative_path, route_path, adapters_path],
        status="awaiting_approval",
        run_dir=run_dir,
    )
    state["current_stage"] = "research"
    state["updated_at"] = utc_now()
    _write_json(run_dir / "run.json", state)
    return {
        "unified": unified_path,
        "claims": claims_path,
        "creative": creative_path,
        "route": route_path,
        "brief": brief_path,
        "adapters": adapters_path,
    }


def _hashes(run_dir: Path, names: dict[str, str]) -> dict[str, str]:
    return {
        key: sha256_file(run_dir / filename)
        for key, filename in names.items()
    }


def approve_run(run_dir: Path, direction: str, private_preview: bool = False) -> Path:
    run_dir = run_dir.resolve()
    job, manifest, state = _load_run(run_dir)
    claims_path = run_dir / "claims-ledger.json"
    creative_path = run_dir / "creative-system.json"
    route_path = run_dir / "route-plan.json"
    brief_path = run_dir / "BRIEF.md"
    missing = [
        str(path.name)
        for path in (claims_path, creative_path, route_path, brief_path)
        if not path.exists()
    ]
    if missing:
        raise FoundryError(f"plan the run before approval; missing: {', '.join(missing)}")

    claims = json.loads(claims_path.read_text())
    creative = json.loads(creative_path.read_text())
    route = json.loads(route_path.read_text())
    problems = []
    if not job.get("conversion_action"):
        problems.append("conversion action is missing")
    if not job.get("audience", {}).get("description"):
        problems.append("audience description is missing")
    if not job.get("deliverables"):
        problems.append("deliverables are missing")
    if claims.get("blocking_gaps"):
        problems.append("claims ledger has blocking gaps")
    pending_sources = [
        item["source_id"]
        for item in claims.get("sources", [])
        if item.get("verification_status") not in {"verified", "local_source"}
    ]
    if pending_sources:
        problems.append(f"source verification is pending: {', '.join(pending_sources)}")
    uncleared = [
        item["id"]
        for item in manifest.get("assets", [])
        if item.get("rights", {}).get("status")
        not in {"owned", "licensed", "cleared", "public_domain", "internal"}
    ]
    if uncleared and not private_preview:
        problems.append(
            "rights are not cleared for public production: " + ", ".join(uncleared)
        )
    direction_ids = {item["id"] for item in creative.get("directions", [])}
    if direction not in direction_ids:
        problems.append(
            f"unknown creative direction '{direction}'; choose one of "
            + ", ".join(sorted(direction_ids))
        )
    if route.get("missing_adapters"):
        problems.append(
            "route contains missing adapters: " + ", ".join(route["missing_adapters"])
        )
    if problems:
        raise FoundryError("approval blocked: " + "; ".join(problems))

    creative["status"] = "approved"
    creative["selected_direction"] = direction
    route["status"] = "approved"
    route["selected_direction"] = direction
    route["approved_at"] = utc_now()
    _write_json(creative_path, creative)
    _write_json(route_path, route)

    receipt_path = run_dir / "approval.json"
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "approved_at": utc_now(),
        "direction": direction,
        "private_preview": private_preview,
        "hashes": _hashes(
            run_dir,
            {
                "job": "job.json",
                "manifest": "asset-manifest.json",
                "brief": "BRIEF.md",
                "creative": "creative-system.json",
                "claims": "claims-ledger.json",
                "route": "route-plan.json",
            },
        ),
        "conditions": {
            "brief_before_spend": True,
            "preview_before_render": True,
            "publish_requires_explicit_approval": True,
        },
    }
    _write_json(receipt_path, receipt)
    _complete_stage(state, "research", [claims_path], run_dir=run_dir)
    _complete_stage(
        state,
        "brief",
        [brief_path, creative_path, receipt_path],
        run_dir=run_dir,
    )
    _complete_stage(state, "route", [route_path], run_dir=run_dir)
    state["current_stage"] = "generate"
    state["updated_at"] = utc_now()
    _write_json(run_dir / "run.json", state)
    (run_dir / "working").mkdir(exist_ok=True)
    return receipt_path


def _assert_approval_current(run_dir: Path) -> dict[str, Any]:
    approval_path = run_dir / "approval.json"
    if not approval_path.exists():
        raise FoundryError("engine work requires an approved brief")
    approval = json.loads(approval_path.read_text())
    current = _hashes(
        run_dir,
        {
            "job": "job.json",
            "manifest": "asset-manifest.json",
            "brief": "BRIEF.md",
            "creative": "creative-system.json",
            "claims": "claims-ledger.json",
            "route": "route-plan.json",
        },
    )
    drift = [
        name
        for name, digest in approval.get("hashes", {}).items()
        if current.get(name) != digest
    ]
    if drift:
        raise FoundryError(
            "approval is stale because approved files changed: " + ", ".join(drift)
        )
    return approval


def plan_engine(run_dir: Path, engine: str) -> Path:
    from .adapters import registry

    run_dir = run_dir.resolve()
    job, _, state = _load_run(run_dir)
    approval = _assert_approval_current(run_dir)
    creative = json.loads((run_dir / "creative-system.json").read_text())
    adapters = registry()
    if engine not in adapters:
        raise FoundryError(f"unknown engine: {engine}")
    route = json.loads((run_dir / "route-plan.json").read_text())
    if engine not in route.get("engines", []):
        raise FoundryError(f"engine '{engine}' is outside the approved route")
    adapter = adapters[engine]
    plan = adapter.plan(job, creative)
    plan.update(
        {
            "approved": True,
            "approval_hash": sha256_file(run_dir / "approval.json"),
            "direction": approval["direction"],
            "created_at": utc_now(),
        }
    )
    path = run_dir / "engine-plans" / f"{engine}.json"
    _write_json(path, plan)
    stage = state["stages"]["generate"]
    stage.setdefault("engines", {})[engine] = {
        "status": "planned",
        "plan": str(path.relative_to(run_dir)),
        "attempts": 0,
        "receipt": None,
        "failure": None,
    }
    stage["status"] = "in_progress"
    stage["started_at"] = stage.get("started_at") or utc_now()
    state["updated_at"] = utc_now()
    _write_json(run_dir / "run.json", state)
    return path


def execute_engine(run_dir: Path, engine: str) -> Path:
    from .adapters import registry

    run_dir = run_dir.resolve()
    _, _, state = _load_run(run_dir)
    _assert_approval_current(run_dir)
    plan_path = run_dir / "engine-plans" / f"{engine}.json"
    if not plan_path.exists():
        raise FoundryError(f"plan engine '{engine}' before execution")
    plan = json.loads(plan_path.read_text())
    if plan.get("approval_hash") != sha256_file(run_dir / "approval.json"):
        raise FoundryError(f"{engine} plan was created under a different approval")
    adapters = registry()
    if engine not in adapters:
        raise FoundryError(f"unknown engine: {engine}")
    adapter = adapters[engine]
    stage = state["stages"]["generate"]
    engine_state = stage.setdefault("engines", {}).setdefault(engine, {})
    engine_state["status"] = "running"
    engine_state["attempts"] = int(engine_state.get("attempts") or 0) + 1
    engine_state["failure"] = None
    state["updated_at"] = utc_now()
    _write_json(run_dir / "run.json", state)
    try:
        result = adapter.execute(plan, run_dir)
        receipt = adapter.receipt(result)
        if receipt["status"] != "verified":
            raise FoundryError(
                f"{engine} verification failed: {receipt['verification']}"
            )
    except Exception as error:
        state = json.loads((run_dir / "run.json").read_text())
        engine_state = state["stages"]["generate"]["engines"][engine]
        engine_state["status"] = "failed"
        engine_state["failure"] = str(error)
        state["updated_at"] = utc_now()
        _write_json(run_dir / "run.json", state)
        if isinstance(error, FoundryError):
            raise
        raise FoundryError(f"{engine} failed: {error}") from error

    receipt_path = run_dir / "receipts" / f"{engine}.json"
    _write_json(receipt_path, receipt)
    state = json.loads((run_dir / "run.json").read_text())
    stage = state["stages"]["generate"]
    engine_state = stage["engines"][engine]
    engine_state["status"] = "verified"
    engine_state["receipt"] = str(receipt_path.relative_to(run_dir))
    stage["receipts"] = sorted(
        {
            *stage.get("receipts", []),
            str(receipt_path.relative_to(run_dir)),
        }
    )
    stage["artifacts"] = sorted(
        {
            *stage.get("artifacts", []),
            *(item["path"] for item in receipt["artifacts"]),
        }
    )
    cost_item = {
        "engine": engine,
        "currency": receipt["cost"]["currency"],
        "amount": float(receipt["cost"]["amount"]),
        "receipt": str(receipt_path.relative_to(run_dir)),
    }
    state["costs"]["items"] = [
        item for item in state["costs"]["items"] if item["engine"] != engine
    ] + [cost_item]
    state["costs"]["total"] = sum(
        float(item["amount"]) for item in state["costs"]["items"]
    )
    state["updated_at"] = utc_now()
    _write_json(run_dir / "run.json", state)
    return receipt_path


def verify_engine_project(
    run_dir: Path,
    engine: str,
    *,
    strict: bool = False,
    snapshots: bool = False,
) -> Path:
    """Run the HyperFrames browser gate for HTML/Three projects and ledger it."""

    run_dir = run_dir.resolve()
    _, _, state = _load_run(run_dir)
    _assert_approval_current(run_dir)
    if engine not in {"hyperframes", "world3d"}:
        raise FoundryError(
            f"engine-check currently supports hyperframes and world3d, not {engine}"
        )
    receipt_path = run_dir / "receipts" / f"{engine}.json"
    if not receipt_path.exists():
        raise FoundryError(f"execute {engine} before running its browser check")
    project_dir = run_dir / "working" / engine
    if not shutil.which("npx"):
        raise FoundryError("HyperFrames check requires Node 22+ and npx")
    command = ["npx", "hyperframes", "check", "--json"]
    if strict:
        command.append("--strict")
    if snapshots:
        command.append("--snapshots")
    process = subprocess.run(
        command,
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=180,
    )
    raw = process.stdout.strip()
    start = raw.find("{")
    if start < 0:
        raise FoundryError(
            f"{engine} check returned no JSON: "
            f"{(process.stderr or process.stdout).strip()}"
        )
    try:
        payload = json.loads(raw[start:])
    except json.JSONDecodeError as error:
        raise FoundryError(f"{engine} check returned invalid JSON: {error}") from error
    check_path = run_dir / "checks" / f"{engine}.json"
    _write_json(check_path, payload)

    receipt = json.loads(receipt_path.read_text())
    receipt["verification"]["hyperframes_check"] = {
        "ok": bool(payload.get("ok")),
        "strict": strict,
        "lint_errors": payload.get("lint", {}).get("errorCount"),
        "runtime_errors": payload.get("runtime", {}).get("errorCount"),
        "layout_errors": payload.get("layout", {}).get("errorCount"),
        "contrast_errors": payload.get("contrast", {}).get("errorCount"),
        "evidence": str(check_path.relative_to(run_dir)),
        "snapshots": payload.get("snapshots", {}).get("files", []),
    }
    receipt["status"] = "verified" if payload.get("ok") else "failed"
    _write_json(receipt_path, receipt)

    engine_state = state["stages"]["generate"].setdefault("engines", {}).setdefault(
        engine, {}
    )
    engine_state["status"] = "checked" if payload.get("ok") else "failed"
    engine_state["check"] = str(check_path.relative_to(run_dir))
    engine_state["failure"] = (
        None if payload.get("ok") else "HyperFrames browser gate failed"
    )
    state["updated_at"] = utc_now()
    _write_json(run_dir / "run.json", state)
    if not payload.get("ok") or process.returncode:
        raise FoundryError(
            f"{engine} browser check failed; inspect {check_path.relative_to(run_dir)}"
        )
    return check_path


def resume_status(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    _, _, state = _load_run(run_dir)
    next_stage = None
    for name in STAGES:
        if state["stages"][name]["status"] != "done":
            next_stage = name
            break
    artifact_issues = []
    for name, stage in state["stages"].items():
        for item in stage.get("artifacts", []):
            path = Path(item)
            resolved = path if path.is_absolute() else run_dir / path
            if not resolved.exists():
                artifact_issues.append({"stage": name, "artifact": item})
    return {
        "schema_version": SCHEMA_VERSION,
        "run_dir": str(run_dir),
        "status": state["status"],
        "next_stage": next_stage,
        "artifact_issues": artifact_issues,
        "portable": not any(
            Path(item).is_absolute()
            for stage in state["stages"].values()
            for item in stage.get("artifacts", [])
        ),
    }
