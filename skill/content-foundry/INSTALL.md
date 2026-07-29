# Install Content Foundry

Content Foundry is one skill that runs in Claude or OpenAI/Codex.

## Automatic install from a checkout

```bash
python scripts/install_skill.py --host claude
python scripts/install_skill.py --host openai
```

Claude installs at `~/.claude/skills/content-foundry`. OpenAI/Codex installs at
`~/.agents/skills/content-foundry` (or the corresponding workspace `.agents/skills` root).
Both copies include `CANONICAL-SHA256`; matching values prove they came from the same source.

## Dependencies

Core:

```bash
python skill/content-foundry/scripts/setup.py --tier core
```

Cinematic project builders, Remotion, and local media:

```bash
python skill/content-foundry/scripts/setup.py --tier cinematic
```

HyperFrames needs Node 22+. FFmpeg/ffprobe are needed for final media. Provider credentials are
optional and must be configured through the host’s secure secret flow.

Verify the install:

```bash
python skill/content-foundry/scripts/doctor.py --json
python skill/content-foundry/scripts/self_test.py
```

## Migrate an existing real-estate agent folder

```bash
python skill/content-foundry/scripts/migrate_context.py \
  ./agents/example \
  ./contexts/example
```

The migration copies files, hashes them, writes `context.json`, and requires review of identity,
rights, logos, colors, fonts, claims, and compliance before public production.

## First successful run

```bash
python skill/content-foundry/scripts/foundry.py prepare \
  --input "text:A fictional product that helps teams verify creative work." \
  --goal "Create a product-launch campaign" \
  --pack product-launch \
  --run-dir ./runs/first-run

python skill/content-foundry/scripts/foundry.py plan --run-dir ./runs/first-run
```

The run stops at its research/brief approval gate by design. Review `BRIEF.md`,
`claims-ledger.json`, `creative-system.json`, and `route-plan.json` before any generation spend.
