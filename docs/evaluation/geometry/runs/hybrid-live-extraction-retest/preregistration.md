# C26 live retest — pre-registration (written and committed BEFORE any C26 request)

Run `hybrid-live-extraction-retest` · Master Epic `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · backend only.

## 1. Identity (frozen before the canary)

| | value |
|---|---|
| product commit | `d331e75b` (repairs + instruction) |
| candidate | `EVALUATION_CANDIDATE.json` frozen at runner commit `7c66a466`; `measured_system` `276fc548196e13ea…` (118 files) |
| runner / scorer / paired harness | `d1dc51d7…` / `8c330bd4…` / `4af1dc76…` |
| model | `gemini-2.5-flash` only, no fallback |
| corpora | K-1 (16), S-2 (36), R-1 (18) — unchanged bytes (`corpus_sha256` in the templates) |
| paid tier | `owner-paid-attestation.json` reused unchanged: `OWNER_ATTESTED` / `EXPLICIT_OWNER_PAID_ATTESTATION`, `project_id = null` — **not** `CLOUD_BILLING_VERIFIED` |

## 2. Authorization and caps

New Owner authorization **C26**: `<= 80` HTTP requests and `<= USD 1.00` ledger upper bound, retries included, K-1/S-2/R-1
only (no H-1, no paired LLM_ONLY). It does not reset C21 (70/70, frozen). One ledger chain: canary ledger
`canary/c26-global-budget-ledger.json` is carried into the full run (`carried_from`), so the two runs share the 80 / 1.00 cap.

## 3. Canary (10 cases, counted in the full retest, never re-sent)

| failure family seen in Run 3 | cases |
|---|---|
| named vs described points | `K-C02`, `S2-B-P07_shared_intermediate_two_goals` |
| section simulation goals | `K-A01`, `R1-B02` |
| source quote grounding | `S2-A-I08_trailing_ve`, `R1-A01`, `S2-F-S08_altitude_wording` |
| clarification / missing operand | `K-E01`, `S2-C-C04_angle_plane_missing`, `R1-E02` |

**Canary stop rule (any one ⇒ stop, fix, re-test offline, re-freeze; a changed candidate starts a NEW full run, never
pooled):** any HTTP status other than 200; any served answer ≠ oracle or uncertified; any served expected-refusal; ≥ 2
schema/wire decode failures (`INVALID_*`, `DANGLING_DEPENDENCY`) of the same shape. Otherwise the full run continues on the
same candidate. Improvement is **not** a canary condition.

## 4. Metrics (fixed now; scored identically for Run 3 and C26)

1. **Safety (hard):** mathematically wrong served = served with `answers != expected_answers` or certificate not verified;
   served on an expected non-served case. Any > 0 ⇒ `SEVERE_REGRESSION`, label below forced to `HYBRID_CUTOVER_BLOCKED`.
2. **False refusal** on expected-`SERVED` cases. Primary comparison on the **39 positives Run 3 measured** (baseline
   20/39); the 4 never-measured R-1 cases are reported separately.
3. Correct refusal / clarification on expected non-served cases (status-only and reason-verified, the runner's rule).
4. Two separate correctness tracks: **mathematical answer correctness** (oracle + certificate) and **strict contract
   correctness** (the unchanged scorer's goals/operands/signature). A served exact answer with a contract mismatch is
   counted in track 2, never as a wrong answer.
5. Extraction accuracy, goal completeness, named/described-point and constraint checks, Source Gate failure codes,
   planner composition labels — the unchanged runner/scorer fields.
6. Tokens (prompt / output / thinking / cached / total; absent usage = `UNKNOWN` / `ABSENT`, never 0), provider HTTP
   latency vs deterministic backend latency, USD (runner-reported and ledger upper bound).

## 5. Labels (assigned only by these rules)

- `LIVE_REGRESSION_MEASURED` = all 70 cases measured live on ONE candidate (canary rows included) with no
  `NOT_RECOVERABLE` row; otherwise `PARTIAL` with the unmeasured scope listed.
- `LIVE_GEMINI_QUALITY_VALIDATED` = **NO by construction**: K-1/S-2/R-1 were used to find and fix these failures
  (development-contaminated, VII.3); only an independent corpus (H-1) can validate quality.
- `HYBRID_CUTOVER_READY` = **NO by construction** in this campaign: H-1 (D-04), paired live Hybrid vs LLM_ONLY (D-11) and
  the Owner's cutover decision (D-13) are outside it. Result: `HYBRID_CUTOVER_BLOCKED`.
- "False refusal reduced" is claimed only if the 39-positive count is strictly below 20 **and** safety is 0/0.

## 6. Offline evidence before the canary (0 provider calls; not a live result)

Captured-wire replay of the 64 Run 3 extractions at `d331e75b` (`captured-wire-replay-d331e75b.jsonl`): false refusal
**1/39** (only `S2-F-S07_typo_tone`, the known S-1 diacritic case), 38 served, 0 wrong answers, 0 served negatives.
This is the same contaminated data the repairs were built from — it shows the repairs act as intended, nothing more.
