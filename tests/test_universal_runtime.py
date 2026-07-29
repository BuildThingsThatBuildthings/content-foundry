import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skill" / "content-foundry" / "scripts" / "foundry.py"


class UniversalRuntimeTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(CLI), *map(str, args)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def prepare_approved_run(self, temp, *, pack="event-campaign"):
        source = temp / "source.md"
        source.write_text("# Verified source\nA practical workshop with a clear outcome.")
        run_dir = temp / "run"
        prepared = self.run_cli(
            "prepare",
            "--input",
            source,
            "--goal",
            "Fill a practical AI workshop",
            "--pack",
            pack,
            "--domain",
            "event",
            "--run-dir",
            run_dir,
        )
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.assertEqual(self.run_cli("plan", "--run-dir", run_dir).returncode, 0)

        job = json.loads((run_dir / "job.json").read_text())
        job["conversion_action"] = "Register"
        job["audience"]["description"] = "Working professionals"
        job["deliverables"] = [{"type": "hero-video", "duration_seconds": 12}]
        (run_dir / "job.json").write_text(json.dumps(job, indent=2))
        manifest = json.loads((run_dir / "asset-manifest.json").read_text())
        for asset in manifest["assets"]:
            asset["rights"]["status"] = "owned"
        (run_dir / "asset-manifest.json").write_text(json.dumps(manifest, indent=2))
        ledger = json.loads((run_dir / "claims-ledger.json").read_text())
        ledger["blocking_gaps"] = []
        for source_record in ledger["sources"]:
            source_record["verification_status"] = "verified"
        (run_dir / "claims-ledger.json").write_text(json.dumps(ledger, indent=2))
        approved = self.run_cli(
            "approve",
            "--run-dir",
            run_dir,
            "--direction",
            "cinematic-world",
        )
        self.assertEqual(approved.returncode, 0, approved.stderr)
        return run_dir

    def test_prepare_accepts_mixed_inputs_and_writes_resumable_state(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            inputs = temp / "inputs"
            inputs.mkdir()
            (inputs / "notes.txt").write_text("A rough launch note.")
            (inputs / "metrics.csv").write_text("week,leads\n1,14\n")
            (inputs / "component.tsx").write_text(
                "export function Component(){ return <main>Proof</main>; }\n"
            )
            (inputs / "mystery.xyz").write_text("preserve me")
            repo = temp / "product-repo"
            repo.mkdir()
            (repo / "README.md").write_text("# Example product")
            (repo / ".git").mkdir()
            run_dir = temp / "run"

            result = self.run_cli(
                "prepare",
                "--input",
                inputs,
                "--input",
                repo,
                "--input",
                "https://example.com/product",
                "--input",
                "text:Turn this into a launch campaign",
                "--goal",
                "Launch the product",
                "--channels",
                "ig,li",
                "--budget",
                "42.50",
                "--run-dir",
                run_dir,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            job = json.loads((run_dir / "job.json").read_text())
            state = json.loads((run_dir / "run.json").read_text())
            manifest = json.loads((run_dir / "asset-manifest.json").read_text())

            self.assertEqual(job["objective"], "Launch the product")
            self.assertEqual(job["channels"], ["ig", "li"])
            self.assertEqual(job["budget"]["ceiling"], 42.5)
            self.assertEqual(len(job["inputs"]), 4)
            self.assertEqual(state["stages"]["ingest"]["status"], "done")
            self.assertEqual(state["stages"]["unify"]["status"], "pending")
            self.assertEqual(len(state["stages"]), 10)

            kinds = {item["provenance"]["kind"] for item in manifest["assets"]}
            self.assertTrue({"local_file", "repository", "url", "text"}.issubset(kinds))
            self.assertTrue(all("rights" in item for item in manifest["assets"]))
            unsupported = {item["path"] for item in manifest["unsupported"]}
            self.assertIn("mystery.xyz", unsupported)
            code = next(item for item in manifest["assets"] if item["path"] == "component.tsx")
            self.assertEqual(code["category"], "code")
            self.assertEqual(code["unify_handler"], "inspect_source")
            self.assertIn("extraction", code)
            self.assertIn("transcript", code)

    def test_empty_or_entirely_unusable_input_is_preserved_and_blocks_cleanly(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            inputs = temp / "inputs"
            inputs.mkdir()
            (inputs / "empty.txt").write_text("")
            (inputs / "unknown.bin").write_bytes(b"unsupported")
            run_dir = temp / "run"
            result = self.run_cli(
                "prepare",
                "--input",
                inputs,
                "--goal",
                "Create something",
                "--run-dir",
                run_dir,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no usable inputs", result.stderr.lower())
            manifest = json.loads((run_dir / "asset-manifest.json").read_text())
            state = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(len(manifest["unsupported"]), 2)
            self.assertTrue(all(item["preserved"] for item in manifest["unsupported"]))
            self.assertEqual(state["status"], "blocked")
            self.assertEqual(state["stages"]["ingest"]["status"], "blocked")

    def test_plan_creates_distinct_creative_system_and_stops_for_approval(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            source = temp / "brief.txt"
            source.write_text("A practical class for operators who want better AI workflows.")
            run_dir = temp / "run"
            prepared = self.run_cli(
                "prepare",
                "--input",
                source,
                "--goal",
                "Fill a local AI workshop",
                "--channels",
                "ig,fb,li",
                "--domain",
                "event",
                "--pack",
                "event-campaign",
                "--run-dir",
                run_dir,
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr)

            planned = self.run_cli("plan", "--run-dir", run_dir)
            self.assertEqual(planned.returncode, 0, planned.stderr)

            creative = json.loads((run_dir / "creative-system.json").read_text())
            route = json.loads((run_dir / "route-plan.json").read_text())
            state = json.loads((run_dir / "run.json").read_text())

            required = {
                "strategic_hook",
                "emotional_promise",
                "narrative_arc",
                "reference_decomposition",
                "visual_world",
                "layout_families",
                "scene_archetypes",
                "type_system",
                "depth",
                "lighting",
                "camera_grammar",
                "motion_cadence",
                "transition_motif",
                "caption_behavior",
                "audio_signature",
                "cta_system",
                "anti_reference",
                "directions",
            }
            self.assertTrue(required.issubset(creative))
            signatures = {
                (
                    direction["layout_family"],
                    direction["camera_behavior"],
                    direction["pacing"],
                    direction["metaphor"],
                )
                for direction in creative["directions"]
            }
            self.assertEqual(len(signatures), 3)
            self.assertIn("hyperframes", route["engines"])
            self.assertIn("world3d", route["engines"])
            brief = (run_dir / "BRIEF.md").read_text()
            self.assertIn("## Complete tool composition", brief)
            self.assertIn("| **hyperframes** |", brief)
            self.assertIn("| **world3d** |", brief)
            self.assertEqual(state["stages"]["brief"]["status"], "awaiting_approval")
            self.assertEqual(state["stages"]["route"]["status"], "pending")
            self.assertFalse((run_dir / "working").exists())

    def test_adapter_registry_exposes_real_capabilities_and_fallbacks(self):
        result = self.run_cli("adapters", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        names = {item["name"] for item in payload["adapters"]}
        self.assertTrue(
            {
                "stills",
                "remotion",
                "hyperframes",
                "world3d",
                "audio",
                "browser-research",
                "deploy",
                "postbridge",
            }.issubset(names)
        )
        for item in payload["adapters"]:
            self.assertIn("available", item["probe"])
            self.assertIn("capabilities", item)
            self.assertIn("fallback", item)

    def test_approval_is_hashed_blocks_gaps_and_survives_moving_the_run(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            source = temp / "source.md"
            source.write_text("# Verified source")
            run_dir = temp / "run"
            self.assertEqual(
                self.run_cli(
                    "prepare",
                    "--input",
                    source,
                    "--goal",
                    "Create a credible campaign",
                    "--pack",
                    "general-social",
                    "--run-dir",
                    run_dir,
                ).returncode,
                0,
            )
            self.assertEqual(self.run_cli("plan", "--run-dir", run_dir).returncode, 0)

            blocked = self.run_cli(
                "approve",
                "--run-dir",
                run_dir,
                "--direction",
                "cinematic-world",
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("conversion action", blocked.stderr.lower())
            self.assertFalse((run_dir / "working").exists())

            job = json.loads((run_dir / "job.json").read_text())
            job["conversion_action"] = "Register"
            job["audience"]["description"] = "Operations leaders"
            job["deliverables"] = [{"type": "hero-video", "duration_seconds": 30}]
            (run_dir / "job.json").write_text(json.dumps(job, indent=2))
            manifest = json.loads((run_dir / "asset-manifest.json").read_text())
            for asset in manifest["assets"]:
                asset["rights"]["status"] = "owned"
            (run_dir / "asset-manifest.json").write_text(json.dumps(manifest, indent=2))
            ledger = json.loads((run_dir / "claims-ledger.json").read_text())
            ledger["blocking_gaps"] = []
            for source_record in ledger["sources"]:
                source_record["verification_status"] = "verified"
            (run_dir / "claims-ledger.json").write_text(json.dumps(ledger, indent=2))

            approved = self.run_cli(
                "approve",
                "--run-dir",
                run_dir,
                "--direction",
                "cinematic-world",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr)
            receipt = json.loads((run_dir / "approval.json").read_text())
            self.assertEqual(receipt["direction"], "cinematic-world")
            self.assertEqual(
                set(receipt["hashes"]),
                {"job", "manifest", "brief", "creative", "claims", "route"},
            )
            state = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(state["stages"]["route"]["status"], "done")
            self.assertEqual(state["current_stage"], "generate")
            self.assertTrue((run_dir / "working").is_dir())

            moved = temp / "moved-run"
            import shutil

            shutil.copytree(run_dir, moved)
            status = self.run_cli("resume", "--run-dir", moved, "--json")
            self.assertEqual(status.returncode, 0, status.stderr)
            payload = json.loads(status.stdout)
            self.assertEqual(payload["next_stage"], "generate")
            moved_state = json.loads((moved / "run.json").read_text())
            self.assertEqual(moved_state["job"], "job.json")
            self.assertTrue(
                all(
                    not Path(path).is_absolute()
                    for stage in moved_state["stages"].values()
                    for path in stage["artifacts"]
                )
            )

    def test_local_cinematic_engines_execute_through_the_run_ledger(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            run_dir = self.prepare_approved_run(temp)

            for engine in ("world3d", "hyperframes"):
                planned = self.run_cli(
                    "engine-plan",
                    "--run-dir",
                    run_dir,
                    "--engine",
                    engine,
                )
                self.assertEqual(planned.returncode, 0, planned.stderr)
                executed = self.run_cli(
                    "engine-execute",
                    "--run-dir",
                    run_dir,
                    "--engine",
                    engine,
                )
                self.assertEqual(executed.returncode, 0, executed.stderr)
                receipt = json.loads(
                    (run_dir / "receipts" / f"{engine}.json").read_text()
                )
                self.assertEqual(receipt["status"], "verified")
                self.assertEqual(receipt["cost"]["amount"], 0.0)
                self.assertTrue(receipt["artifacts"])
                self.assertTrue(
                    all(item["sha256"] for item in receipt["artifacts"])
                )

            world_html = (run_dir / "working" / "world3d" / "index.html").read_text()
            self.assertIn('data-composition-id="world3d"', world_html)
            self.assertIn('data-duration="12"', world_html)
            self.assertIn("hf-seek", world_html)
            self.assertIn("./vendor/three.module.min.js", world_html)
            self.assertNotIn("requestAnimationFrame", world_html)
            self.assertNotIn("Math.random", world_html)

            hyper_html = (
                run_dir / "working" / "hyperframes" / "index.html"
            ).read_text()
            self.assertIn('data-composition-id="content-foundry-master"', hyper_html)
            self.assertIn('data-duration="12"', hyper_html)
            self.assertIn('class="clip"', hyper_html)
            self.assertIn("@keyframes hook-beat", hyper_html)
            self.assertIn("animation:", hyper_html)
            self.assertNotIn("gsap", hyper_html.lower())
            self.assertNotIn("https://", hyper_html)

            stale = run_dir / "working" / "hyperframes" / "snapshots" / "stale.png"
            stale.parent.mkdir()
            stale.write_bytes(b"stale")
            rerun = self.run_cli(
                "engine-execute",
                "--run-dir",
                run_dir,
                "--engine",
                "hyperframes",
            )
            self.assertEqual(rerun.returncode, 0, rerun.stderr)
            self.assertFalse(stale.exists())

            for engine, builder in (
                (
                    "hyperframes",
                    ROOT
                    / "skill"
                    / "content-foundry"
                    / "engines"
                    / "hyperframes"
                    / "build_composition.mjs",
                ),
                (
                    "world3d",
                    ROOT
                    / "skill"
                    / "content-foundry"
                    / "engines"
                    / "world3d"
                    / "build_world.mjs",
                ),
            ):
                unsafe = subprocess.run(
                    [
                        "node",
                        str(builder),
                        "--run-dir",
                        str(run_dir),
                        "--output",
                        str(temp / f"outside-{engine}"),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(unsafe.returncode, 0)
                self.assertIn("child directory", unsafe.stderr)

            world_manifest = json.loads(
                (run_dir / "working" / "world3d" / "world.json").read_text()
            )
            self.assertTrue(world_manifest["scene"]["materials"])

            state = json.loads((run_dir / "run.json").read_text())
            receipt_paths = set(state["stages"]["generate"]["receipts"])
            self.assertEqual(
                receipt_paths,
                {"receipts/world3d.json", "receipts/hyperframes.json"},
            )
            self.assertEqual(
                {item["engine"] for item in state["costs"]["items"]},
                {"world3d", "hyperframes"},
            )

    def test_canonical_skill_packages_for_claude_and_openai(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            installer = ROOT / "scripts" / "install_skill.py"
            for host, expected in (
                ("claude", temp / ".claude" / "skills" / "content-foundry"),
                ("openai", temp / ".agents" / "skills" / "content-foundry"),
            ):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(installer),
                        "--host",
                        host,
                        "--root",
                        str(temp),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((expected / "SKILL.md").is_file())
                self.assertTrue((expected / "scripts" / "foundry.py").is_file())
                self.assertTrue((expected / "agents" / "openai.yaml").is_file())

            claude = temp / ".claude" / "skills" / "content-foundry"
            openai = temp / ".agents" / "skills" / "content-foundry"
            self.assertEqual(
                (claude / "CANONICAL-SHA256").read_text(),
                (openai / "CANONICAL-SHA256").read_text(),
            )

    def test_public_schemas_and_domain_packs_cover_the_universal_contract(self):
        skill = ROOT / "skill" / "content-foundry"
        for name in (
            "job.schema.json",
            "asset-manifest.schema.json",
            "creative-system.schema.json",
            "run.schema.json",
            "engine-receipt.schema.json",
        ):
            schema = json.loads((skill / "schemas" / name).read_text())
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["additionalProperties"], False)

        pack_names = {
            json.loads(path.read_text())["name"]
            for path in (skill / "packs").glob("*.json")
        }
        self.assertTrue(
            {
                "real-estate",
                "event-campaign",
                "product-launch",
                "education",
                "data-story",
                "general-social",
            }.issubset(pack_names)
        )

        forbidden = ("/Users/ryan", "ai_acceleration_v3", "/contentfoundry/")
        for path in skill.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                try:
                    body = path.read_text()
                except UnicodeDecodeError:
                    continue
                for marker in forbidden:
                    self.assertNotIn(marker, body, f"{marker} leaked into {path}")


if __name__ == "__main__":
    unittest.main()
