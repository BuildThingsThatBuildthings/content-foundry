# Changelog

## v1.4.0 — 2026-07-29
- **Prospect-research setup mode** (`setup --from-research`): research-drafted agent
  foundations with per-file source provenance — the outreach spec-sample flow.
- **Demo guard**: demo/fixture personas refuse listing content (`--allow-demo` to override);
  palette-distinctness check in brand lint.
- **Design-language layer**: `brand-context-design.md` tokens (layout family, display type,
  motion energy, accent treatment) drive structurally different output per brand across
  stills, videos, and the tour.
- **Kinetic word-synced captions** at reading speed: narration renders on screen word-by-word
  from TTS word timestamps; groups linger until the next phrase speaks.
- **Persistent fact pins**: key facts spring into an on-screen rail when spoken and stay;
  persistent address chip.
- **Agent headshot support**: declared in the visual file; used in video intro/endcards and
  the outreach page automatically.
- **i2v parallax flights**: scenes and tours consume image-to-video camera moves generated
  from the real photos (`--flights-dir`), with the ffmpeg path as fallback.
- **Outreach page engine** (`engines/outreach/build_page.py`) + canonical outreach workflow
  with blocking quality gates (`references/engine-outreach.md`).

## v1.3.0 — 2026-07-28 (initial open-source release)
- Stills pipeline: ingest → unify → research → brief → composite → brand lint → export
  (deterministic brand + compliance layer; WCAG-AA worst-case contrast guarantees for
  headline and compliance block; aspect-aware layouts).
- Multi-agent tenancy via Context Kit folders (one folder per agent).
- Video products (Remotion): narrated Digital Walkthrough, Digital Sales Brief, Teaser —
  brand-token driven, VO-timed scenes, bundled OFL typography.
- Interactive Scroll Tour (scroll-world engine, MIT): scroll-scrubbed room flights from real
  photos with doorway-portal transitions and staggered info reveals.
- Post Bridge draft-first scheduling module (optional).
- Cross-platform font bundling (Playfair Display, Source Sans 3 — OFL), dependency doctor,
  BYO TTS/music/image-generation contracts.
