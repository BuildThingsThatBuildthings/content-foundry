---
name: content-foundry
description: >
  End-to-end universal creative production skill for Claude and OpenAI/Codex. Use it when a user
  provides any mix of images, video, audio, documents, URLs, repositories, brand folders,
  transcripts, data, or only a free-form request and wants researched, strategically distinct,
  brand-correct stills, videos, HyperFrames compositions, Three.js worlds, audio, web assets,
  exports, deployments, or scheduled drafts. Also triggers on "/content-foundry", "produce this
  campaign", "turn these references into video", "build a launch asset system", listing/event/
  educational/data-story work, and Content Foundry setup, doctor, resume, QC, or packaging.
---

# Content Foundry

Content Foundry is one portable production system with two thin host surfaces: Claude and
OpenAI/Codex. It accepts imperfect inputs, researches the assignment, develops a real creative
system, routes by capability, executes through audited adapters, blocks weak or unsafe work, and
exports or schedules only with explicit approval.

## Invocations

```text
/content-foundry produce
  --context <portable-brand-or-workspace-folder>
  --input <repeatable-file-folder-url-repository-or-text>
  --goal "<outcome>"
  --channels <channels>
  --budget <ceiling>
```

Shortcuts `event`, `listing`, `product-launch`, `education`, `data-story`, and `general-social`
compile into the same job contract. Existing `agents/{slug}` folders remain valid contexts.

Deterministic CLI:

```bash
python scripts/foundry.py prepare --input <source> --goal "<outcome>" --run-dir <run>
python scripts/foundry.py plan --run-dir <run>
python scripts/foundry.py approve --run-dir <run> --direction <direction-id>
python scripts/foundry.py engine-plan --run-dir <run> --engine <engine>
python scripts/foundry.py engine-execute --run-dir <run> --engine <engine>
python scripts/foundry.py resume --run-dir <run>
```

The host interprets, researches, describes media, and manages approvals. The shared runtime owns
schemas, manifests, state, engine receipts, and resumability.

## Non-negotiable laws

1. **Portable context is the tenancy boundary.** Read brand, person, company, product, event, and
   client truth only from the selected context and cited inputs. Never transfer identity or facts
   from memory or another run.
2. **Composite exact truth.** Logos, exact colors, disclosures, sponsor marks, numbers, citations,
   and CTA details are placed deterministically from files and ledgers. A model may create the
   visual world; it may not redraw or remember protected brand truth.
3. **Brief before spend.** Stage 4 writes `BRIEF.md`, `creative-system.json`, `claims-ledger.json`,
   and `route-plan.json`, then stops. Generation requires a current hashed `approval.json`.
4. **Preview before final render; approval before external write.** A passed check is not preview
   approval. Deployment, scheduling, publishing, and provider spend obey `job.json`.
5. **Every engine uses the adapter contract.** `probe`, `plan`, `execute`, `verify`, `artifacts`,
   and `receipt` are mandatory. No asset may bypass `run.json`.
6. **Fail soft, never silently.** Unsupported files are preserved and reported. Missing optional
   engines activate declared fallbacks. Failed factual, rights, brand, visual, accessibility, or
   technical gates block export.
7. **Directions must be structurally different.** A palette swap is not a concept. Layout, scene
   construction, pacing, camera behavior, hierarchy, and metaphor must differ.
8. **Public core, optional private extensions.** Never require private paths, repositories, skills,
   identities, or credentials. Optional adapters must disclose their capability difference.

## Universal input contract

Stage 1 accepts local files/folders, repositories, URLs, inline text, and portable context folders.
Each input becomes an `asset-manifest.json` record with:

- stable ID, type, MIME, hash, size, dimensions/duration where available;
- source, access time, provenance, staging location, and intended role;
- rights basis and review status;
- extraction, description, or transcript status;
- duplicate relationships and preservation status.

The standard-library inventory runs before any optional provider. See
`references/universal-inputs.md`.

## Tool and engine composition plan

Always include the routed tools and their exact role in `BRIEF.md`:

| Capability | Composition role |
|---|---|
| Claude/OpenAI host | Interpret intent, perform host research/media understanding, and conduct approval conversations against the same portable contracts. |
| Native brand context | Build or import a portable foundation. Brand Brain-compatible folders may be imported, but private Brand Brain is never required. |
| Browser/research | Read live pages, capture interfaces, verify claims, and record URLs plus access dates in the claims ledger. |
| Media resolver | Resolve official logos, headshots, fonts, footage, audio, licensing, and provenance before generation. |
| OpenAI/Gemini still adapters | Generate or edit source imagery without logos, exact type, disclosures, or factual overlays. Use either provider or the deterministic fallback. |
| HyperFrames | Build cinematic HTML timelines, scene transitions, multi-engine assembly, preview, finishing, and master renders. It is a real local project adapter. |
| Remotion | Render deterministic typography, captions, data, UI demonstrations, presenter plates, CTAs, and compliance overlays. |
| Bundled Three.js world builder | Build pinned local 3D scenes, spatial camera paths, depth transitions, and `hf-seek`-driven worlds without a private repository. |
| Pretext | Compute deterministic safe-zone-aware typography and line breaks. |
| Pillow composite | Place exact logos, colors, facts, citations, sponsor marks, disclosures, and export-safe treatments. |
| Audio adapters | Use approved recordings or configured OpenAI, HeyGen, or local Kokoro voices; store timings and rights. |
| FFmpeg/ffprobe | Conform, stitch, normalize loudness, mux captions, encode variants, create thumbnails, and perform technical QC. |
| Netlify/Vercel | Optionally deploy unlisted review pages or approved interactive assets with readback receipts. |
| PostBridge | Inspect queues, upload media, create scheduled drafts, and reconcile returned post IDs. Never treat a local schedule manifest as a scheduled post. |
| GitHub | Distribute source, test clean installs, publish semantic releases, checksums, changelogs, and rights-clean fixtures. |
| RyVibes-derived QC | Apply vendored rights-safe slop, hierarchy, specificity, distinctness, hook, and watch-through gates. |

Read only the references for the selected engines. HyperFrames and Three.js require
`references/engine-hyperframes.md` and `references/engine-3d.md`.

## Ten-stage production pipeline

### 1 — Ingest

Create `job.json`, `asset-manifest.json`, and `run.json`. Preserve unsupported inputs. Stop only
when a required source is missing or unusable; do not crash on mixed folders.

### 2 — Unify

Extract documents/data, inspect repositories, transcribe media, describe images, capture pages,
and normalize context in `unified-context.md`. Mark unresolved host actions explicitly.

### 3 — Research

Fill evidence gaps, decompose references, verify live facts, and maintain `claims-ledger.json`.
Every number, testimonial, event detail, product assertion, and market fact needs a source.

### 4 — Brief and creative system — stop for approval

Write:

- objective, audience, promise, conversion action, deliverables, formats, channels, cost ceiling;
- claims/rights status and open blockers;
- exact tool list with composition role and fallbacks;
- at least three structurally different concepts in `creative-system.json`;
- route and per-engine cost/limitation plans.

Do not create `working/` before approval. Approval hashes job, manifest, brief, creative system,
claims ledger, and route; later drift invalidates it.

### 5 — Route

Load the selected domain pack from `packs/` and choose engines by capabilities, dependency probes,
budget, rights, and deliverable needs. Fallbacks must state what capability is lost.

### 6 — Generate

Execute approved engine plans. Generate base imagery, worlds, footage, audio, diagrams, and
interface captures without exact brand truth. Each call records provider/model/version, cost,
hashes, warnings, and status.

### 7 — Composite

Apply exact logos, fonts, colors, copy, facts, disclosures, sponsor marks, citations, captions,
safe zones, and CTA details deterministically. Use Pretext/Pillow/Remotion rather than image-model
text for required copy.

### 8 — Blocking QC

Run all applicable gates:

- factual and citation;
- rights and provenance;
- brand and compliance;
- visual hierarchy, specificity, distinctness, slop, and hook;
- accessibility, safe zones, captions, and contrast;
- technical dimensions, duration, codec, loudness, missing media, and hashes;
- human watch-through or visual inspection.

Write receipts and retry causes. Maximum two generation retries per root cause; then stop with the
smallest recovery action. See `references/qc-gate.md`.

### 9 — Export

Create channel-native deliverables, thumbnails, captions, source packages, `export-manifest.json`,
and cost report. Filename and channel rules come from `references/channel-specs.md`.

### 10 — Deploy or schedule

Only after explicit approval. Deploy approved interactive work or create PostBridge scheduled
drafts. Store returned URLs/post IDs and immediately read them back. Reconcile expected account,
asset, caption, time, and queue state. “Prepared” and “uploaded” are not “scheduled.”

## Creative-system contract

Every `creative-system.json` contains strategic hook, emotional promise, narrative arc, reference
decomposition, visual world/metaphor, layout families, scene archetypes, type scale/behavior,
depth, materials, lighting, color/texture, camera grammar, motion cadence, transition motif,
captions, audio signature, CTA system, and anti-reference/slop risks.

Reusable archetypes include cinematic world reveal, asymmetric editorial, presenter/proof split,
kinetic workflow, 3D control room, product/interface demo, data story, and conversion endcard.
See `references/creative-system.md`.

## Domain packs

- `general-social` — general branded social content;
- `event-campaign` — classes, events, presenters, logistics, sponsors, registration;
- `real-estate` — listings, local market work, brokerage rules, Fair Housing;
- `product-launch` — repository, interface, proof, demo, conversion;
- `education` — lesson promise, learning arc, exercises, instructor proof;
- `data-story` — PDF/CSV evidence, methods, comparisons, charts, accessibility.

Packs may add constraints; they may not weaken universal evidence, rights, approval, or QC gates.

## Setup, doctor, self-test, and migration

```bash
python scripts/doctor.py --json
python scripts/self_test.py
python scripts/foundry.py adapters --json
```

Provider credentials are optional capability upgrades. Use the host's secure credential setup;
never print, write, or request secret values in chat. A clean core install must still produce
deterministic still, Remotion/FFmpeg, HyperFrames-project, and Three.js-project fallbacks when their
documented local dependencies are installed.

## Reference map

- `references/universal-inputs.md`
- `references/creative-system.md`
- `references/adapter-contract.md`
- `references/engine-stills.md`
- `references/engine-remotion.md`
- `references/engine-hyperframes.md`
- `references/engine-3d.md`
- `references/engine-scroll-tour.md`
- `references/qc-gate.md`
- `references/channel-specs.md`
- `references/postbridge-automation.md`
- `references/context-kit-import.md`
