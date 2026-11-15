# Universal inputs

Use `scripts/foundry.py prepare` for the first pass. It accepts repeatable local files, folders,
repositories, URLs, and `text:<value>` inputs. It stages local evidence in the run, hashes every
supported file, preserves unsupported files, marks duplicates, and records provenance and rights.

Host actions after deterministic inventory:

- images: record dimensions and an evidence-grounded description;
- video/audio: record duration, codec, transcript, speaker confidence, and rights;
- PDF/office: extract text and page/slide/sheet references;
- CSV/JSON: record schema, row counts, data-quality warnings, and sensitive fields;
- URLs: capture title, canonical URL, access date, screenshot where useful, and claims used;
- repositories: inventory product surfaces, build instructions, UI captures, and license;
- corrupt/encrypted: preserve, mark blocked, and name the smallest recovery action.

Never silently omit an input. Never infer ownership from possession.
