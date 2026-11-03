# Run `hybrid-live-validation`

Live Gemini validation, failure-driven backend repair and LLM_ONLY replacement readiness of
`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` (backend only; `frontend/**` untouched). Reports:
- **Live Gemini evaluation & cutover decision (C25):** [`LIVE_GEMINI_EVALUATION_REPORT.md`](LIVE_GEMINI_EVALUATION_REPORT.md)
- **Prior preflight-blocked offline baseline (C24, preserved byte-for-byte):** [`HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md`](HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md)

- **Live Gemini (`gemini-2.5-flash`, `OWNER_ATTESTED`, `70 / 70` HTTP requests):**
  - `owner-paid-attestation.json` - Owner's verbatim paid-service statement (`"tôi dùng tiền mà ko free"`, `OWNER_ATTESTED` / `EXPLICIT_OWNER_PAID_ATTESTATION`, `cloud_billing_verified: false`, `project_id: null`).
  - `live-pilots-79bbc053/` - Run 1 (`3` HTTP 400 on tuple `prefixItems`, halted cleanly by `INFRASTRUCTURE_STREAK`; fixed in `48372208`).
  - `live-pilots-48372208/` - Run 2 (`3` HTTP 400 on Gemini constrained-decoding FSM state limit; fixed in `8853c4b0` via 4,333-byte flat wire schema).
  - `live-pilots-8853c4b0/` - **Run 3 primary live measurement** on candidate `44568bc9` (`8853c4b0`, `5c0175289995b921…`): **`64 / 64` HTTP 200 `STOP`**, `0` retries (`K-1` `16/16`, `S-2` `36/36` = `35` HTTP + `1` domain gate, `R-1` `14/18` = `13` HTTP + `1` `R1-F01` halted pre-call at `70/70` `GLOBAL_REQUEST_CAP`; `4` unmeasured `R1-F02..R1-G02`); USD `0.340464` reported (`0.318308` cache-discounted, `0.495793` campaign upper bound <= `4.00`); **`0 / 65` mathematically wrong answers served (`19 / 19` `SERVED` match exact symbolic oracle 100%)**; `LIVE_GEMINI_MEASURED = YES`, `LIVE_GEMINI_QUALITY_VALIDATED = NO`, `HYBRID_CUTOVER_BLOCKED`.
  - `../hybrid-live-gemini-execution/candidate_divergence.json` + `frozen-evaluation-candidate.json` - post-Run-3 candidate `428515dc` (product `f60ae29e`, `118` files, `e758e25af26707c2…`), correcting `candidate_divergence.json` below without mutating any frozen receipt.
- *(Historical C24 preflight record)* `live-preflight.json` + `c21-delegated-execution-receipt.json` - initial C24 preflight before Owner attestation (`PAID_PROJECT_NOT_VERIFIED`, 0 HTTP requests at `79bbc053`).
- `candidate_divergence.json` - C24 divergence layer correcting `../pedagogical-simulation-integration/candidate_divergence.json`; candidate
  product `57457fc4`, 118 files, `6202a6a6…` (`frozen-evaluation-candidate.json`; first freeze `d5c4098b` at `55db50c3` / `f4ed426a…` superseded after review round 1). Now corrected by `../hybrid-live-gemini-execution/candidate_divergence.json`. The `fba8b7a7` candidate and every
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
