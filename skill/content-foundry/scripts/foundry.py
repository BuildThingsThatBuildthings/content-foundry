#!/usr/bin/env python3
"""Content Foundry universal runtime.

The host skill translates natural-language requests into this deterministic
interface. Run `foundry.py --help` for the portable CLI.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from runtime import FoundryError, prepare_run  # noqa: E402
from runtime.adapters import registry_snapshot  # noqa: E402
from runtime.core import (  # noqa: E402
    approve_run,
    execute_engine,
    plan_engine,
    plan_run,
    resume_status,
    verify_engine_project,
)


def csv_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def command_prepare(args: argparse.Namespace) -> int:
    try:
        paths = prepare_run(
            inputs=args.input,
            goal=args.goal,
            channels=csv_values(args.channels),
            budget=args.budget,
            run_dir=Path(args.run_dir).expanduser(),
            context=args.context,
            domain=args.domain,
            pack=args.pack,
        )
    except FoundryError as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1
    print(f"PREPARED {Path(args.run_dir).expanduser().resolve()}")
    for name, path in paths.items():
        print(f"  {name}: {path}")
    print("  next: Stage 2 — UNIFY")
    return 0


def command_plan(args: argparse.Namespace) -> int:
    try:
        paths = plan_run(Path(args.run_dir).expanduser())
    except FoundryError as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1
    print(f"PLANNED {Path(args.run_dir).expanduser().resolve()}")
    for name, path in paths.items():
        print(f"  {name}: {path}")
    print("  STOP: resolve research gaps and approve BRIEF.md before generation")
    return 0


def command_adapters(args: argparse.Namespace) -> int:
    snapshot = registry_snapshot()
    if args.json:
        print(json.dumps(snapshot, indent=2))
        return 0
    for item in snapshot["adapters"]:
        status = "ready" if item["probe"]["available"] else "setup required"
        print(f"{item['name']}: {status}")
        print(f"  capabilities: {', '.join(item['capabilities'])}")
        print(f"  fallback: {item['fallback']}")
    return 0


def command_approve(args: argparse.Namespace) -> int:
    try:
        receipt = approve_run(
            Path(args.run_dir).expanduser(),
            args.direction,
            private_preview=args.private_preview,
        )
    except FoundryError as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1
    print(f"APPROVED {receipt}")
    print("  next: Stage 6 — GENERATE")
    return 0


def command_resume(args: argparse.Namespace) -> int:
    try:
        status = resume_status(Path(args.run_dir).expanduser())
    except FoundryError as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(f"RUN {status['run_dir']}")
        print(f"  next stage: {status['next_stage'] or 'complete'}")
        print(f"  portable state: {'yes' if status['portable'] else 'no'}")
        if status["artifact_issues"]:
            print(f"  missing artifacts: {len(status['artifact_issues'])}")
    return 0


def command_engine_plan(args: argparse.Namespace) -> int:
    try:
        path = plan_engine(Path(args.run_dir).expanduser(), args.engine)
    except FoundryError as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1
    print(f"ENGINE PLAN {path}")
    return 0


def command_engine_execute(args: argparse.Namespace) -> int:
    try:
        path = execute_engine(Path(args.run_dir).expanduser(), args.engine)
    except FoundryError as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1
    print(f"ENGINE VERIFIED {path}")
    return 0


def command_engine_check(args: argparse.Namespace) -> int:
    try:
        path = verify_engine_project(
            Path(args.run_dir).expanduser(),
            args.engine,
            strict=args.strict,
            snapshots=args.snapshots,
        )
    except FoundryError as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1
    print(f"ENGINE CHECK PASSED {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Content Foundry universal production runtime"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser(
        "prepare",
        help="create job.json, inventory mixed inputs, and initialize resumable run state",
    )
    prepare.add_argument(
        "--input",
        action="append",
        required=True,
        help="repeatable path, URL, repository, or text:<raw request>",
    )
    prepare.add_argument("--context", help="portable brand/workspace context folder")
    prepare.add_argument("--goal", required=True)
    prepare.add_argument("--channels", default="ig,fb,li")
    prepare.add_argument("--budget", type=float, default=0.0)
    prepare.add_argument("--domain", default="general")
    prepare.add_argument("--pack", default="general-social")
    prepare.add_argument("--run-dir", required=True)
    prepare.set_defaults(handler=command_prepare)

    plan = subparsers.add_parser(
        "plan",
        help="unify intake and draft claims, creative system, route, and approval brief",
    )
    plan.add_argument("--run-dir", required=True)
    plan.set_defaults(handler=command_plan)

    adapters = subparsers.add_parser(
        "adapters",
        help="show engine capabilities, dependency state, and fallbacks",
    )
    adapters.add_argument("--json", action="store_true")
    adapters.set_defaults(handler=command_adapters)

    approve = subparsers.add_parser(
        "approve",
        help="verify the research/rights/brief gate and issue a hashed approval receipt",
    )
    approve.add_argument("--run-dir", required=True)
    approve.add_argument("--direction", required=True)
    approve.add_argument(
        "--private-preview",
        action="store_true",
        help="allow unknown rights for a private review run; deployment remains blocked",
    )
    approve.set_defaults(handler=command_approve)

    resume = subparsers.add_parser(
        "resume",
        help="inspect portable run state and identify the first unfinished stage",
    )
    resume.add_argument("--run-dir", required=True)
    resume.add_argument("--json", action="store_true")
    resume.set_defaults(handler=command_resume)

    engine_plan = subparsers.add_parser(
        "engine-plan",
        help="write a costed engine plan under the approved route",
    )
    engine_plan.add_argument("--run-dir", required=True)
    engine_plan.add_argument("--engine", required=True)
    engine_plan.set_defaults(handler=command_engine_plan)

    engine_execute = subparsers.add_parser(
        "engine-execute",
        help="execute an approved engine plan and write a central ledger receipt",
    )
    engine_execute.add_argument("--run-dir", required=True)
    engine_execute.add_argument("--engine", required=True)
    engine_execute.set_defaults(handler=command_engine_execute)

    engine_check = subparsers.add_parser(
        "engine-check",
        help="run the HyperFrames browser gate and attach its evidence to the receipt",
    )
    engine_check.add_argument("--run-dir", required=True)
    engine_check.add_argument("--engine", required=True)
    engine_check.add_argument("--strict", action="store_true")
    engine_check.add_argument("--snapshots", action="store_true")
    engine_check.set_defaults(handler=command_engine_check)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
