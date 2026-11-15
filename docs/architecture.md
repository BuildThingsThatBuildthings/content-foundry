# Content Foundry architecture

## One canonical skill, two hosts

`skill/content-foundry/` is the source of truth. Claude and OpenAI/Codex launchers stay thin and
operate the same Python runtime, schemas, packs, references, engines, fixtures, and quality gates.
`scripts/install_skill.py` installs the canonical tree to either host and records its content hash.

## Layering

1. **Universal core:** ingest, unify, research, brief, creative system, route, generate, composite,
   QC, export, deploy/schedule.
2. **Domain packs:** general social, events/classes, real estate, product launch, education, data
   story.
3. **Engine adapters:** still/provider generation, deterministic composite, Remotion, HyperFrames,
   Three.js, audio, browser research, deployment, scheduling.
4. **Host adapters:** Claude and OpenAI/Codex interpretation, media understanding, research, and
   approval conversation.

Portable context folders represent a person, company, product, event, property, or client.
`agents/{slug}` remains backward compatible.

## Contracts

- `job.json` describes outcome, conversion action, audience, sources, context, pack, deliverables,
  channels, research, claims, art direction, providers, budget, approvals, and distribution.
- `asset-manifest.json` stores hash, type, provenance, rights, dimensions/duration, extraction,
  transcript, role, duplicates, and unsupported preservation.
- `creative-system.json` stores strategy, art direction, scene/camera/motion/audio/CTA systems, and
  at least three structurally distinct directions.
- `run.json` stores ten stages, per-engine substeps, attempts, failures, receipts, costs,
  deployments, and scheduling readback.
- Every adapter implements `probe`, `plan`, `execute`, `verify`, `artifacts`, and `receipt`.

All paths inside stage state and receipts are run-relative so the run can move between machines.

## Approval and mutation boundary

Stage 4 produces the complete brief and route before generation. Approval hashes all governing
artifacts. Engine plan/execution/check refuses stale approval. A passed automated check still
requires visual/watch-through review and final-preview approval before rendering. Deployment and
scheduled drafts are separate explicit mutations with external readback.

## Deterministic and generative boundary

Generative engines may create visual worlds, imagery, narration, and exploratory footage.
Deterministic engines place exact logos, brand values, type, claims, citations, disclosures,
sponsor marks, captions, safe zones, and CTAs. Provider calls cannot bypass the ledger.

HyperFrames and Three.js are real project adapters. HyperFrames generates an offline seekable
composition and can attach browser-check evidence. The Three.js builder vendors pinned MIT modules
and renders only from `hf-seek`; no wall clock, render-time network, or private repository.

## Quality gate

Export blocks on applicable factual, rights, brand, compliance, hierarchy, slop, distinctness,
hook, accessibility, safe-zone, contrast, duration, codec, loudness, missing-media, hash, and human
review failures. Each root cause gets at most two retries before a plain-language stop.

## Open-source boundary

The public package contains no private paths, brands, people, keys, or repository assumptions.
Private engines may plug into the same adapter interface, but declared open fallbacks remain
functional. Public evaluation fixtures are fictional and rights-clean.
