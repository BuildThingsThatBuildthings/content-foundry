# HyperFrames adapter

Content Foundry's HyperFrames adapter is executable. `engine-plan` creates a zero-local-cost plan;
`engine-execute` runs `engines/hyperframes/build_composition.mjs`, vendors a local font, creates a
valid root composition, and records hashes in `receipts/hyperframes.json`.

The generated project must:

- have one standalone root with `data-composition-id`, static `data-duration`, dimensions, and
  direct-child timed clips;
- use finite deterministic CSS/WAAPI animation that HyperFrames can seek;
- use local render-critical dependencies and media;
- avoid wall clocks, uncontrolled randomness, infinite loops, and network fetches at render;
- keep clip visibility under HyperFrames control and animate children/wrappers.

Production loop:

1. build the composition through the adapter and ledger;
2. run `npx hyperframes check` from the generated project;
3. inspect snapshots and mounted sub-compositions;
4. open the Studio preview and obtain final-preview approval;
5. only then render high quality;
6. verify file size, duration, codecs, frames, audio, captions, and receipt.

Without HyperFrames CLI, preserve the generated HTML project and route final MP4 through
Remotion/FFmpeg. State that Studio validation/finishing is unavailable.
