"""Engine adapter interface and capability registry."""

from __future__ import annotations

import abc
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .core import FoundryError, sha256_file, utc_now


SKILL_DIR = Path(__file__).resolve().parents[1]


class EngineAdapter(abc.ABC):
    """Deep module seam for every production engine."""

    name: str
    capabilities: tuple[str, ...]
    fallback: str

    @abc.abstractmethod
    def probe(self) -> dict[str, Any]:
        """Return availability and actionable dependency detail."""

    @abc.abstractmethod
    def plan(
        self, job: dict[str, Any], creative_system: dict[str, Any]
    ) -> dict[str, Any]:
        """Return cost, outputs, limitations, and required approvals."""

    @abc.abstractmethod
    def execute(self, plan: dict[str, Any], run_dir: Path) -> dict[str, Any]:
        """Execute only an approved plan and return raw results."""

    def verify(self, result: dict[str, Any]) -> dict[str, Any]:
        artifacts = [Path(item) for item in result.get("artifacts", [])]
        missing = [str(item) for item in artifacts if not item.exists()]
        empty = [str(item) for item in artifacts if item.exists() and item.stat().st_size == 0]
        return {
            "ok": not missing and not empty,
            "missing": missing,
            "empty": empty,
            "checked_at": utc_now(),
        }

    def artifacts(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        records = []
        run_dir = Path(result["run_dir"]).resolve() if result.get("run_dir") else None
        for item in result.get("artifacts", []):
            path = Path(item)
            if path.exists() and path.is_file():
                stored_path = str(path.resolve())
                if run_dir:
                    try:
                        stored_path = str(path.resolve().relative_to(run_dir))
                    except ValueError:
                        pass
                records.append(
                    {
                        "path": stored_path,
                        "size_bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
        return records

    def receipt(self, result: dict[str, Any]) -> dict[str, Any]:
        verification = self.verify(result)
        return {
            "schema_version": "1.0",
            "engine": self.name,
            "created_at": utc_now(),
            "status": "verified" if verification["ok"] else "failed",
            "provider": result.get("provider", self.name),
            "model_or_version": result.get("model_or_version"),
            "cost": result.get("cost", {"currency": "USD", "amount": 0.0}),
            "artifacts": self.artifacts(result),
            "verification": verification,
            "command": result.get("command"),
            "warnings": result.get("warnings", []),
        }


class LocalProjectAdapter(EngineAdapter):
    """Build a deterministic local project through a pinned Node builder."""

    def __init__(
        self,
        *,
        name: str,
        capabilities: tuple[str, ...],
        fallback: str,
        builder: Path,
        dependency_files: tuple[Path, ...],
        artifact_names: tuple[str, ...],
        model_or_version: str,
    ):
        self.name = name
        self.capabilities = capabilities
        self.fallback = fallback
        self.builder = builder
        self.dependency_files = dependency_files
        self.artifact_names = artifact_names
        self.model_or_version = model_or_version

    def probe(self) -> dict[str, Any]:
        missing_commands = [name for name in ("node",) if not shutil.which(name)]
        required = (self.builder, *self.dependency_files)
        missing_paths = [str(path) for path in required if not path.exists()]
        return {
            "available": not missing_commands and not missing_paths,
            "mode": "local",
            "missing_commands": missing_commands,
            "missing_paths": missing_paths,
            "detail": (
                "ready"
                if not missing_commands and not missing_paths
                else "run setup to install pinned local engine dependencies"
            ),
        }

    def plan(
        self, job: dict[str, Any], creative_system: dict[str, Any]
    ) -> dict[str, Any]:
        deliverable = next(
            (
                item
                for item in job.get("deliverables", [])
                if item.get("duration_seconds")
            ),
            {},
        )
        return {
            "schema_version": "1.0",
            "engine": self.name,
            "capabilities": list(self.capabilities),
            "objective": job["objective"],
            "selected_direction": creative_system.get("selected_direction"),
            "output": f"working/{self.name}",
            "artifacts": [
                f"working/{self.name}/{name}" for name in self.artifact_names
            ],
            "duration_seconds": float(deliverable.get("duration_seconds", 12)),
            "estimated_cost": {"currency": "USD", "amount": 0.0},
            "limitations": [] if self.probe()["available"] else [self.fallback],
            "requires_approval": True,
            "provider": "local",
            "model_or_version": self.model_or_version,
        }

    def execute(self, plan: dict[str, Any], run_dir: Path) -> dict[str, Any]:
        if not plan.get("approved"):
            raise FoundryError(f"{self.name} plan is not approved")
        probe = self.probe()
        if not probe["available"]:
            raise FoundryError(
                f"{self.name} is unavailable: "
                + ", ".join(probe["missing_commands"] + probe["missing_paths"])
            )
        output = run_dir / plan["output"]
        output.mkdir(parents=True, exist_ok=True)
        command = [
            shutil.which("node") or "node",
            str(self.builder),
            "--run-dir",
            str(run_dir),
            "--output",
            str(output),
        ]
        process = subprocess.run(
            command,
            cwd=run_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if process.returncode:
            raise FoundryError(
                f"{self.name} failed ({process.returncode}): "
                f"{(process.stderr or process.stdout).strip()}"
            )
        return {
            "run_dir": str(run_dir),
            "provider": "local",
            "model_or_version": self.model_or_version,
            "command": ["node", self.builder.name, "--run-dir", ".", "--output", plan["output"]],
            "artifacts": [run_dir / item for item in plan["artifacts"]],
            "cost": {"currency": "USD", "amount": 0.0},
            "warnings": [],
            "stdout": process.stdout,
        }


class CapabilityAdapter(EngineAdapter):
    def __init__(
        self,
        name: str,
        capabilities: tuple[str, ...],
        fallback: str,
        commands: tuple[str, ...] = (),
        paths: tuple[Path, ...] = (),
        mode: str = "local",
    ):
        self.name = name
        self.capabilities = capabilities
        self.fallback = fallback
        self.commands = commands
        self.paths = paths
        self.mode = mode

    def probe(self) -> dict[str, Any]:
        missing_commands = [item for item in self.commands if not shutil.which(item)]
        missing_paths = [str(item) for item in self.paths if not item.exists()]
        available = not missing_commands and not missing_paths
        return {
            "available": available,
            "mode": self.mode,
            "missing_commands": missing_commands,
            "missing_paths": missing_paths,
            "detail": "ready" if available else "dependency setup required",
        }

    def plan(
        self, job: dict[str, Any], creative_system: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "engine": self.name,
            "capabilities": list(self.capabilities),
            "objective": job["objective"],
            "creative_directions": [
                item["id"] for item in creative_system.get("directions", [])
            ],
            "estimated_cost": {"currency": "USD", "amount": None},
            "limitations": [] if self.probe()["available"] else [self.fallback],
            "requires_approval": True,
        }

    def execute(self, plan: dict[str, Any], run_dir: Path) -> dict[str, Any]:
        command = plan.get("command")
        if not command:
            raise FoundryError(
                f"{self.name} execution requires an adapter-produced command plan"
            )
        if not plan.get("approved"):
            raise FoundryError(f"{self.name} plan is not approved")
        result = subprocess.run(
            command,
            cwd=run_dir,
            capture_output=True,
            text=True,
            timeout=plan.get("timeout_seconds", 900),
        )
        if result.returncode:
            raise FoundryError(
                f"{self.name} failed ({result.returncode}): "
                f"{(result.stderr or result.stdout).strip()}"
            )
        return {
            "provider": self.name,
            "command": command,
            "artifacts": plan.get("artifacts", []),
            "warnings": [],
            "stdout": result.stdout,
        }


class ProviderAdapter(CapabilityAdapter):
    """Optional provider adapter with explicit secret and fallback reporting."""

    def __init__(
        self,
        *args: Any,
        secret_names: tuple[str, ...],
        provider: str,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.secret_names = secret_names
        self.provider = provider

    def probe(self) -> dict[str, Any]:
        base = super().probe()
        configured = [name for name in self.secret_names if os.environ.get(name)]
        base["provider"] = self.provider
        base["secret_names"] = list(self.secret_names)
        base["configured_secret_names"] = configured
        if self.secret_names and not configured:
            base["available"] = False
            base["detail"] = "provider credential not configured"
        return base

def registry() -> dict[str, EngineAdapter]:
    pillow_available = importlib.util.find_spec("PIL") is not None
    engines_dir = SKILL_DIR / "engines"
    adapters: list[EngineAdapter] = [
        CapabilityAdapter(
            "stills",
            ("image-composite", "brand-truth", "channel-export"),
            "Use the source asset without a generated base and preserve the brief.",
            paths=(SKILL_DIR / "scripts" / "composite.py",),
        ),
        CapabilityAdapter(
            "remotion",
            ("motion-design", "captions", "data", "compliance"),
            "Export still/carousel variants from the same creative system.",
            commands=("node", "npm", "ffmpeg"),
            paths=(SKILL_DIR / "engines" / "remotion" / "src" / "Root.tsx",),
        ),
        LocalProjectAdapter(
            name="hyperframes",
            capabilities=(
                "cinematic-assembly",
                "html-video",
                "transitions",
                "finishing",
            ),
            fallback="Use Remotion plus FFmpeg and the same timeline manifest.",
            builder=engines_dir / "hyperframes" / "build_composition.mjs",
            dependency_files=(
                SKILL_DIR / "assets" / "fonts" / "SourceSans3.ttf",
            ),
            artifact_names=(
                "index.html",
                "hyperframes.json",
                "BRIEF.md",
                "vendor/SourceSans3.ttf",
            ),
            model_or_version="hyperframes-project/1; css-animation-runtime",
        ),
        LocalProjectAdapter(
            name="world3d",
            capabilities=("threejs-world", "camera-paths", "spatial-transitions"),
            fallback="Use 2.5D parallax scenes rendered through Remotion.",
            builder=engines_dir / "world3d" / "build_world.mjs",
            dependency_files=(
                engines_dir
                / "node_modules"
                / "three"
                / "build"
                / "three.module.min.js",
            ),
            artifact_names=(
                "index.html",
                "world.json",
                "vendor/three.module.min.js",
                "vendor/three.core.min.js",
                "vendor/SourceSans3.ttf",
            ),
            model_or_version="three/0.181.2; world-builder/1",
        ),
        CapabilityAdapter(
            "audio",
            ("voice", "music", "sfx", "word-timing", "loudness"),
            "Use disclosed silent output and preserve timing placeholders.",
            commands=("ffmpeg", "ffprobe"),
        ),
        ProviderAdapter(
            "stills-openai",
            ("image-generation", "image-editing", "provider-receipt"),
            "Use Gemini, a user-supplied source image, or deterministic composition.",
            commands=("python",),
            mode="optional-provider",
            secret_names=("OPENAI_API_KEY",),
            provider="OpenAI",
        ),
        ProviderAdapter(
            "stills-gemini",
            ("image-generation", "image-editing", "provider-receipt"),
            "Use OpenAI, a user-supplied source image, or deterministic composition.",
            commands=("python",),
            mode="optional-provider",
            secret_names=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
            provider="Google Gemini",
        ),
        ProviderAdapter(
            "voice-openai",
            ("tts", "voice", "provider-receipt"),
            "Use an approved recording, HeyGen, or local Kokoro.",
            commands=("python", "ffmpeg"),
            mode="optional-provider",
            secret_names=("OPENAI_API_KEY",),
            provider="OpenAI",
        ),
        ProviderAdapter(
            "voice-heygen",
            ("tts", "avatar-voice", "provider-receipt"),
            "Use an approved recording, OpenAI, or local Kokoro.",
            commands=("ffmpeg",),
            mode="optional-provider",
            secret_names=("HEYGEN_API_KEY",),
            provider="HeyGen",
        ),
        CapabilityAdapter(
            "voice-kokoro",
            ("local-tts", "word-timing"),
            "Use an approved recording or a configured hosted voice provider.",
            commands=("kokoro", "ffmpeg"),
            mode="optional-local",
        ),
        CapabilityAdapter(
            "browser-research",
            ("fetch", "capture", "citation", "interface-evidence"),
            "Preserve URLs as unresolved sources and block uncited claims.",
            mode="host",
        ),
        CapabilityAdapter(
            "deploy",
            ("unlisted-review", "interactive-hosting", "deployment-receipt"),
            "Serve the exported package locally.",
            commands=("npx",),
            mode="optional",
        ),
        ProviderAdapter(
            "deploy-netlify",
            ("unlisted-review", "interactive-hosting", "deployment-receipt"),
            "Export a local review package without deployment.",
            commands=("npx",),
            mode="optional-provider",
            secret_names=("NETLIFY_AUTH_TOKEN",),
            provider="Netlify",
        ),
        ProviderAdapter(
            "deploy-vercel",
            ("unlisted-review", "interactive-hosting", "deployment-receipt"),
            "Export a local review package without deployment.",
            commands=("npx",),
            mode="optional-provider",
            secret_names=("VERCEL_TOKEN",),
            provider="Vercel",
        ),
        ProviderAdapter(
            "postbridge",
            ("queue-read", "draft-schedule", "status-readback"),
            "Export a schedule manifest without creating external posts.",
            commands=("npx",),
            mode="optional-provider",
            secret_names=("POST_BRIDGE_API_KEY", "POSTBRIDGE_API_KEY"),
            provider="PostBridge",
        ),
    ]
    result = {item.name: item for item in adapters}
    if not pillow_available:
        result["stills"].fallback = "Install Pillow; no branded raster output is permitted."
    return result


def registry_snapshot() -> dict[str, Any]:
    items = []
    for name, adapter in registry().items():
        items.append(
            {
                "name": name,
                "capabilities": list(adapter.capabilities),
                "fallback": adapter.fallback,
                "probe": adapter.probe(),
            }
        )
    return {"schema_version": "1.0", "adapters": items}


def write_registry_snapshot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry_snapshot(), indent=2) + "\n")
