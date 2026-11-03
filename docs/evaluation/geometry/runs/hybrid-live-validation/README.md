# Run `hybrid-live-validation`

Live Gemini validation, failure-driven backend repair and LLM_ONLY replacement readiness of
`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (backend only; `frontend/**` untouched). Report:
[`HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md`](HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md).

- **Live Gemini: not run.** The one grounded preflight (`live-preflight.json`) stopped at `PAID_PROJECT_NOT_VERIFIED`
  before any request: 0 HTTP requests, USD 0.00. No `LIVE_GEMINI_EVALUATION_REPORT.md` exists because nothing was
  measured live.
- `candidate_divergence.json` - corrects `../pedagogical-simulation-integration/candidate_divergence.json`; candidate
  product `55db50c3`, 118 files, `f4ed426a…` (`frozen-evaluation-candidate.json`). The `fba8b7a7` candidate and every
  earlier receipt stay byte-for-byte.
- `gold-replay-regression.json` + `wave3-gold-replay.json` - Wave 3 (144) / locked development (96) / reviewer probes
  (203) replayed on gold TypedFactNext payloads at the candidate (offline, 0 provider calls).
- `planner-composition-*.json` - C11/C18 composition probes re-run at the candidate.
- `legacy-dependency-inventory.json` (`tools/legacy_dependency_inventory.py`) - static import inventory of the LLM_ONLY
  and Hybrid closures.
- `full-t3-*.json` - Full T3 at the frozen candidate on a clean detached worktree.
