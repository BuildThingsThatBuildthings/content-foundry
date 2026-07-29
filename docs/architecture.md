# Content Foundry — Architecture

## Design philosophy

Three constraints drive every decision:

1. **It's a skill, not an app.** No server, no database, no UI. The entire product is a folder;
   Claude Code is the runtime. Distribution is a copy; support burden stays near zero.
2. **Foundation once, content forever.** An agent's brand is captured one time into a Context Kit
   folder. Every run reads that folder. One folder per agent is the tenancy boundary — a
   brokerage with 40 agents has 40 folders, and nothing outside the selected folder can
   influence a run.
3. **Deterministic where possible, generative where necessary.** File inventory, brand
   compositing, brand linting, export sizing, and naming are scripts. Creative decisions are the
   model's job. **Never let the model do what a script can verify.**

Constraint 3 is load-bearing: asking a generative model to "include the logo and use `#676147`"
is exactly the failure this product prevents. So it is never asked.

## The agent folder (tenancy unit)

```
agents/{slug}/
├── _MANIFEST.md                  # load order; Tier 1 overrides Tier 2
├── about-me.md                   # Tier 1 — identity
├── brand-voice.md                # Tier 1 — voice rules, banned words, examples
├── working-style.md              # Tier 1 — collaboration defaults
├── brand-context-visual.md       # Tier 2 — hexes, logo paths, fonts, photo style
├── brand-context-compliance.md   # Tier 2 — license, disclosure, Fair Housing, bans
└── assets/logo-*.png
```

`scripts/brandkit.py` is the single reader — `composite.py` and `brand_lint.py` both consume it,
so the linter always validates the same truth the compositor used. Blank-template detection stops
a half-configured agent from producing assets.

## The pipeline

| Stage | What | Deterministic? |
|---|---|---|
| 1 INGEST | `inventory.py`: walk the drop, hash, dims, duplicates, unsupported-but-not-fatal | ✅ |
| 2 UNIFY | transcribe / extract / fetch / describe → one canonical context doc | model-assisted |
| 3 RESEARCH | scoped web search; every stat needs a citation | model |
| 4 BRIEF ✋ | creative brief written to disk **before** any generation spend; user reviews | model |
| 5 ROUTE | brief → engine (stills / walkthrough / sales-brief / teaser / scroll tour) | table |
| 6 GENERATE | base imagery only — no logo, no text, no disclosure in generated pixels | model/BYO |
| 7 COMPOSITE ⚙ | `composite.py`: logo bytes, exact hexes, headline type, compliance block at channel-spec coordinates; WCAG-AA worst-case contrast with scrim → panel → backing-strip escalation | ✅ |
| 8 QC GATE | `brand_lint.py` (pixels + manifest) AND model QC vs slop taxonomy; max 2 retries, then plain-language surface | ✅ + model |
| 9 EXPORT | channel sizing, naming convention, manifest | ✅ |
| 10 PUBLISH | Post Bridge drafts only; explicit `auto_publish: true` required to ever change that | ✅ |

### Why the lint is trustworthy

`brand_lint.py` does not trust the compositor's claims. It re-reads the brand folder, then
verifies pixels: logo sampled against its source bytes, exact hexes probed on solid elements,
compliance strings matched verbatim, worst-case (not average) contrast measured behind text, safe
zones enforced. CI runs negative tests — a wrong hex and a stripped disclosure **must** fail —
so the gate can never silently rot into a formality.

### Contrast is measured worst-case

Averages hide local failure. Text contrast is sampled at the ~p85 worst pixel of the exact box
the text occupies; if a gradient scrim can't clear 4.5:1, the compositor escalates to a solid
brand panel, and the compliance block gets its own backing strip. "Almost legible" legal text is
a failure by definition.

## Video engines

- **Remotion** (`engines/remotion/`): three comps — narrated Walkthrough, SalesBrief, Teaser —
  driven entirely by a props file from `video_props.py` (brand tokens via brandkit; measured VO
  durations drive scene timing; photos carry real aspect ratios so landscape images are fitted
  into editorial bands, never blind-cropped). Bundled OFL display font loaded via FontFace for
  identical renders on every OS. [Pretext](https://www.pretext.cool/) computes deterministic
  headline line breaks.
- **Scroll Tour** (`engines/scroll-tour/`): the vendored
  [scroll-world](https://github.com/oso95/scroll-world) scrub engine (MIT) plus
  `build_tour.py` — ffmpeg camera flights generated from the listing's real photos (2×
  supersampled zoompan; zero AI generation), doorway-portal connectors that dive into each
  room's declared focal point with frame-identical seams, staggered scroll-driven info reveals,
  brand theming, compliance footer.

## Degradation rules

Missing optional dependency → fall back, never fail: no Remotion → stills from the same brief +
install offer; no narration → music-only → silent (each warned in the props); no Post Bridge →
exports remain on disk. The one thing that never degrades: compliance placement. An unfilled
disclosure blocks production output entirely.
