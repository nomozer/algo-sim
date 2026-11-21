# AXO HYBRID /8 — Gemini Parity Protocol & Non-Parity Historical Diagnostics (`GEMINI_PARITY_PROTOCOL.md`)

> **Status (`GEMINI_PARITY`):** **`NOT_MEASURED`** (`ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`). Per `/8` rules, **no live cloud calls** were executed and `GEMINI_PARITY_EVALUATION.json` is **omitted** rather than fabricated.  
> **Scope of This Document:** (1) Pre-registered protocol for a future authorized head-to-head live Gemini 2.5 Flash vs `Qwen3-0.6B-AxoV7` comparison; (2) Offline local replay diagnostics (`0` cloud calls) on historical `{K-1, R-1, S-2}` and `C60` corpora with explicit compatibility disclosures explaining why they do **not** constitute valid Gemini parity evidence.

---

## 1. Why Head-to-Head Gemini Parity Is `NOT_MEASURED`

1. **Zero Cloud Authorization / Credential Boundary:** `ALLOW_LIVE_AI` is enforced at `"0"` and `GEMINI_API_KEY` is unset throughout AXO HYBRID /8 (`external_ai_calls = 0`).
2. **Incompatible Historical Artifacts:** Historical Gemini runs in the repository (`K-1`, `R-1`, `S-2`, `C60`) ran on earlier `CACHE_VERSION` (`125`–`132`) / schema / prompt versions, and `K-1`/`R-1`/`S-2` also test contract scopes (`derived cross-sections`, `pilot-specific student templates` marked `PENDING_OWNER_DECISION`) that differ from `/7`'s `slm-compact-clause/1` single-solid boundary.

---

## 2. Pre-Registered Live Parity Protocol (For Future Authorized Execution)

When owner authorization, API key, and paid budget approval are explicitly granted, a dedicated parity wave MUST satisfy all six controls:

1. **Budget Cap & Hard Stop Rules:**
   - Register max live request cap (e.g. `<= 250` requests across benchmark + adversarial controls) and max estimated USD ceiling before sending the first request.
   - Stop immediately on HTTP `401/403`, sustained `429/5xx`, malformed JSON rate `> 10%`, or first verified `WRONG_SERVED` (`Mode A` leak) caused by extraction bypass.
2. **Paired Shared Benchmark Architecture (`5` Strata, `n >= 150`):**
   - `Stratum 1`: Clean textbook single-solid metric/angle problems (`40` items).
   - `Stratum 2`: Conversational / reordered natural Vietnamese student phrasings (`40` items).
   - `Stratum 3`: Derived cross-sections (`sec`), intersection lines (`inter`), spheres, and reflection/multi-solid problems (`30` items — explicitly testing Gemini's broader surface vs SLM's capability boundary).
   - `Stratum 4`: Underspecified / contradictory / ambiguous problems (`25` items — measuring over-refusal vs false-serve risk).
   - `Stratum 5`: OOS / non-Euclidean / 2D / off-topic controls (`15` items).
3. **Identical Downstream Verification Stack & Grader:** Both arms (`HYBRID_ROUTE_MODE = "live"` Gemini 2.5 Flash vs `HYBRID_ROUTE_MODE = "local-slm"` `Qwen3-0.6B-AxoV7`) must feed the exact same `Source Gate` (`registry.kiem_nguon`), `Planner /26`, `Exact Kernel /24`, `Adapter /4`, and be graded identically with **`axo-math-evaluator/2`** ([`slm_math_evaluator_v2.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/slm_math_evaluator_v2.py)).
4. **Metrics Recorded Side-by-Side:** Exact `SERVED` correctness (Wilson 95% CI), paired McNemar `p` & Cohen's `h`, `WRONG_SERVED` count (strictly `0`), safe refusal rate on Stratum 4+5, `p50/p95` latency (cold vs warm), cost per solved problem (`USD`), and fallback/failure taxonomy (`INFRASTRUCTURE_FAILURE` vs `CAPABILITY_GAP` vs `MODEL_SEMANTIC_ERROR`).
5. **Routing Threshold Requirement for Replacement Review:** Local SLM may only be considered for parity-based default replacement if paired accuracy gap is non-inferior within pre-registered margin on **all** supported strata (`Stratum 1–3`) OR router escalation explicitly handles `Stratum 3` while preserving `<= 5s` UX latency and `0` Mode-A leaks.

---

## 3. Offline Non-Parity Historical Diagnostics (`0` Cloud Calls, `VERIFIED` Trace Only)

As an offline engineering diagnostic (recorded in [`PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json) under `offline_k1_r1_s2_historical_gemini_diagnostic` with `external_ai_calls = 0`), we compared historical archived Gemini 2.5 Flash telemetry on `{K-1, R-1, S-2}` and `C60` against offline local `Config D (AxoV7)` traces:

| Historical Corpus | Cases / Exp. Served | Archived Gemini 2.5 Flash (Historical Commit/Schema) | Offline Local `Config D` (`/7 + AxoV7`, Current `v145`) | Why NOT Parity Evidence |
|---|---:|---|---|---|
| **`K-1`** (`derived sections`) | `16` (`10` exp.) | `10/16` served, `10` E2E correct, median `10,950.1 ms`, `$0.097564` | `10/16` served, median `69.2 ms` (`REFUSED`: `1 PLANE_NOT_UNIQUE`, `1 INCONSISTENT_FACTS`, `2 DEGENERATE_POINTS`, `2 AMBIGUOUS_FACT`) | `K-1` tests derived cross-sections outside `slm-compact-clause/1` AND `PENDING_OWNER_DECISION`; current `v145` deterministic parser + kernel advances differ from K-1's archived commit |
| **`R-1`** (`ratios/projections`) | `18` (`13` exp.) | `11/18` served (`10` E2E correct), median `7,035.2 ms`, `$0.084548` | `15/18` served, median `48.6 ms` (`REFUSED`: `2 AMBIGUOUS_FACT`, `1 SOURCE_OBJECT_MISMATCH`) | `R-1` uses pilot-specific contract assumptions & post-archived planner upgrades in `v145`; cannot isolate Gemini vs SLM extraction delta |
| **`S-2`** (`student phrasing pilot`) | `36` (`18` exp.) | `16/36` served (`26` E2E expected incl. safe refusals), median `7,691.1 ms`, `$0.167801` | `17/36` served, median `24.9 ms` (`REFUSED`: `7 AMBIGUOUS_FACT`, `6 INCONSISTENT_FACTS`, `6 OUT_OF_SCOPE`) | `S-2` includes mixed pilot expectations and templates (`PENDING_OWNER_DECISION`); deterministic rule upgrades in `/7` account for fast-path local serves |
| **`C60_BLIND_NLU`** (`locked 44` Gemini vs `42+` current) | `60` | Historical V1 (`CACHE 125`, `TypedFact` branch B): **`2/44` served** (`27/45` goal+entity, median `5.55–7.0 s`, `$0.299` across `76` calls; `Gold = 8/44` locked, `10/60` overall) | Current `Config D` (`v145`): **`13/42` (`30.95%`)** served (`12/42` deterministic `Config A`), **`0` wrong-served**, `13/13` neg refused | Archived Gemini ran on `CACHE_VERSION=125` `TypedFact[]` (before `TypedFactNext /2`, Planner `/26`, and Source Gate upgrades), not current Route D `live` |

### Conclusion on Gemini Role
- **What IS verified:** Without live Gemini, `HYBRID_ROUTE_MODE = "local-slm"` (`Config D`) serves `100%` of `EXTERNAL17` (`12/12`) and `92.50%` of in-distribution `SLM_V7_HOLDOUT_112` at zero marginal API cost and millisecond-to-few-second local CPU latency with `0` Mode-A leaks — **while dropping to `30.95%` on unseen conversational `C60_BLIND_NLU`**.
- **What is `NOT_MEASURED`:** Whether current `HYBRID_ROUTE_MODE = "live"` (Gemini 2.5 Flash on `TypedFactNext /2` + `Planner /26` + `v145` Source Gate) outperforms `Config D` by a large margin on unconstrained `C60_BLIND_NLU`, complex sections (`K-1`), and unseen natural problems. Therefore **`GEMINI_PARITY = NOT_MEASURED`** and **Gemini 2.5 Flash MUST remain production default**.
