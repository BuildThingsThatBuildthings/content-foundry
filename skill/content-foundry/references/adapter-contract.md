# Engine adapter contract

Every engine implements:

- `probe()` — dependencies, credentials, capability level, and actionable fallback;
- `plan()` — outputs, cost estimate, limitations, approvals, and expected artifacts;
- `execute()` — approved work only;
- `verify()` — technical and visual evidence;
- `artifacts()` — paths, sizes, hashes, formats, and metadata;
- `receipt()` — provider, model/version, cost, warnings, status, and evidence.

Rules:

- Plans and receipts are portable JSON under the run directory.
- Execution requires a current `approval.json`; any approved-file drift blocks.
- Every attempt, failure, retry cause, cost, artifact, and receipt updates `run.json`.
- Provider adapters may be unavailable. Their fallback stays explicit and never impersonates the
  missing capability.
- Deployment and scheduling receipts require readback from the external system.
