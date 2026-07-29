# Content Foundry

**An MIT-licensed universal creative-production skill for Claude and OpenAI/Codex.**

Give it mixed files, folders, URLs, repositories, brand context, transcripts, data—or only a
free-form request. Content Foundry inventories and researches the assignment, creates a
source-grounded brief and structurally distinct creative system, routes work through still,
Remotion, HyperFrames, Three.js, audio, browser, composite, deployment, and scheduling adapters,
then blocks weak, unsafe, or unverifiable output before export.

The existing real-estate workflow remains the first domain pack. It is not the product boundary.

## What is implemented

- One canonical skill tree installs to Claude or `.agents/skills` for OpenAI/Codex.
- Portable `job.json`, `asset-manifest.json`, `creative-system.json`, `run.json`, and engine
  receipt schemas.
- Mixed-input inventory with hashes, provenance, rights status, duplicate detection, preservation
  of unsupported files, and clean blocking for empty/unusable intake.
- Six domain packs: general social, events/classes, real estate/Fair Housing, product launches,
  education, and data stories.
- A hashed Stage-4 approval gate; approved-file drift blocks engine work.
- A first-class HyperFrames project builder and browser-check integration.
- A bundled, pinned Three.js world builder driven by `hf-seek`, with no private repository.
- Existing deterministic Pillow/Pretext, Remotion, FFmpeg, scroll-tour, brand-lint, and slop-QC
  foundations.
- Provider-neutral probes and explicit fallbacks for OpenAI, Gemini, HeyGen, Kokoro, Netlify,
  Vercel, and PostBridge.
- Resume after moving a run to another machine.
- Offline self-test, ten-case cross-domain evaluation suite, cross-host conformance, Windows CI,
  release archives, and checksums.

## Install

Clone the repository, then install the same canonical source for either host:

```bash
python scripts/install_skill.py --host claude
python scripts/install_skill.py --host openai
```

Install core dependencies and verify:

```bash
python skill/content-foundry/scripts/setup.py --tier core
python skill/content-foundry/scripts/doctor.py --json
python skill/content-foundry/scripts/self_test.py
```

For local cinematic projects and Remotion:

```bash
python skill/content-foundry/scripts/setup.py --tier cinematic
```

Node 22+ is required for HyperFrames. Hosted generation, deployment, and scheduling are optional
capability upgrades; configure credentials through the host’s secure secret flow.

## First run

```bash
python skill/content-foundry/scripts/foundry.py prepare \
  --input ./references \
  --input https://example.com/product \
  --goal "Launch this product" \
  --channels ig,li,web \
  --budget 50 \
  --pack product-launch \
  --run-dir ./runs/launch

python skill/content-foundry/scripts/foundry.py plan --run-dir ./runs/launch
```

Planning writes the brief, claims ledger, creative system, tool/route plan, and stops. Fill the
audience, conversion action, deliverables, rights, evidence gaps, and cost; select a direction;
then approve:

```bash
python skill/content-foundry/scripts/foundry.py approve \
  --run-dir ./runs/launch \
  --direction cinematic-world
```

Build and verify first-class cinematic projects through the central ledger:

```bash
python skill/content-foundry/scripts/foundry.py engine-plan \
  --run-dir ./runs/launch --engine hyperframes
python skill/content-foundry/scripts/foundry.py engine-execute \
  --run-dir ./runs/launch --engine hyperframes
python skill/content-foundry/scripts/foundry.py engine-check \
  --run-dir ./runs/launch --engine hyperframes --snapshots

python skill/content-foundry/scripts/foundry.py engine-plan \
  --run-dir ./runs/launch --engine world3d
python skill/content-foundry/scripts/foundry.py engine-execute \
  --run-dir ./runs/launch --engine world3d
python skill/content-foundry/scripts/foundry.py engine-check \
  --run-dir ./runs/launch --engine world3d --snapshots
```

Final render, deployment, and scheduling remain approval-gated. A check is not a preview approval;
an export manifest is not a scheduled post.

## Architecture

```text
arbitrary inputs
  -> ingest -> unify -> research -> brief/creative approval
  -> capability route
  -> generate -> deterministic composite
  -> factual + rights + brand + visual + accessibility + technical QC
  -> channel exports
  -> optional deploy / scheduled drafts with readback
```

The host handles interpretation, media understanding, live research, and approvals. The shared
runtime owns schemas, manifests, portable state, engine execution, receipts, costs, and blocking
gates. See [architecture](docs/architecture.md) and the canonical
[skill instructions](skill/content-foundry/SKILL.md).

## Evaluation

```bash
python -m unittest discover -s tests -v
python scripts/evaluate.py
```

The rights-clean suite covers an event, listing, software launch, transcript recut, CSV data story,
incomplete brand, unusable intake, offline provider fallback, Claude/OpenAI conformance, and a
fresh-install/moved-run resume.

## Real-estate pack

The original listing workflow is preserved: exact logos/colors/license/disclosures are
deterministically composited and pixel-checked; required legal language is supplied by the
brokerage, never invented; Fair Housing constraints describe the property rather than the buyer.
This is assistive tooling, not legal advice.

## Release and license

The repository is MIT licensed. Optional engines/services retain their own licenses and terms; see
[dependency inventory](DEPENDENCIES.md), [LICENSE](LICENSE), and [NOTICE](NOTICE).

Tagged releases create separate Claude/OpenAI archives from the same canonical source plus
`SHA256SUMS`.
