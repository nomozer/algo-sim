# Run `hybrid-live-validation`

Live Gemini validation, failure-driven backend repair and LLM_ONLY replacement readiness of
`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (backend only; `frontend/**` untouched). Report:
[`HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md`](HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md).

- **Live Gemini: not run.** The one grounded preflight (`live-preflight.json`) stopped at `PAID_PROJECT_NOT_VERIFIED`
  before any request: 0 HTTP requests, USD 0.00. No `LIVE_GEMINI_EVALUATION_REPORT.md` exists because nothing was
  measured live.
- `candidate_divergence.json` - corrects `../pedagogical-simulation-integration/candidate_divergence.json`; candidate
  product `57457fc4`, 118 files, `6202a6a6…` (`frozen-evaluation-candidate.json`; first freeze `d5c4098b` at `55db50c3` / `f4ed426a…` superseded after review round 1). The `fba8b7a7` candidate and every
  earlier receipt stay byte-for-byte.
- `gold-replay-regression.json` + `wave3-gold-replay.json` - Wave 3 (144) / locked development (96) / reviewer probes
  (203) replayed on gold TypedFactNext payloads at the candidate (offline, 0 provider calls).
- `planner-composition-c18-probe.json` + `measurement-probe.json` - C18 composition probe and the S.ABCD measurement probe
  re-run at the candidate (the C11 matrix tool aborts on its own pre-C16 expectation, also at `adf4a113`).
- `legacy-dependency-inventory.json` (`tools/legacy_dependency_inventory.py`) - static import inventory of the LLM_ONLY
  and Hybrid closures.
- `full-t3-79bbc053.json` - Full T3 at the frozen candidate on a clean detached worktree (attempt 1 at `d5c4098b` failed on
  one divergence-layer key; recorded in the same receipt).
- `independent-review.md` - fresh-context adversarial review rounds.
