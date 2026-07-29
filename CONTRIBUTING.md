# Contributing

## Setup
1. `python skill/content-foundry/scripts/doctor.py` — fix anything marked `!!`.
2. `pip install -r skill/content-foundry/requirements.txt`
3. Video work: `cd skill/content-foundry/engines/remotion && npm install`

## Ground rules (from SKILL.md — the non-negotiable laws)
- **Composite, don't request.** Brand truth (logos, hexes, license, disclosure) is placed by
  script, never requested from a generative model.
- **The lint must be able to fail.** Any change to `composite.py` must keep `brand_lint.py`
  able to fail: run the negative tests below and confirm they still fail correctly.
- **Compliance is placement, not wording.** Never add code or prompts that draft legal text.
- **Draft-first.** Nothing may auto-publish.

## Smoke tests (run before any PR)
```bash
cd <repo root>
python skill/content-foundry/scripts/inventory.py tests/fixtures/drop-messy --quiet
python skill/content-foundry/scripts/composite.py \
  --base tests/fixtures/drop-messy/photo.jpg \
  --agent tests/fixtures/agent-testbrand --channel ig --treatment panel \
  --headline "CI Smoke" --out /tmp/cf-ci.jpg
python skill/content-foundry/scripts/brand_lint.py /tmp/cf-ci.jpg \
  --agent tests/fixtures/agent-testbrand          # must PASS
# negative: wrong hex must FAIL (exit 1)
sed 's/#1b4d3e/#7c3aed/' tests/fixtures/agent-testbrand/brand-context-visual.md > /tmp/wrong-visual.md
```
CI runs the same checks on ubuntu + macos; keep them green.

## Style
- Python: stdlib + Pillow only in `scripts/` (no new hard dependencies without discussion).
- Docs: keep SKILL.md under 500 lines; engine details live in `references/`.
