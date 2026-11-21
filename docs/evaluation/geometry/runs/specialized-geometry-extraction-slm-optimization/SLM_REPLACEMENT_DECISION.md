# SLM_REPLACEMENT_DECISION.md — Preregistered Empirical Replacement Verdict (AXO HYBRID /6)

> **Campaign:** `specialized-geometry-extraction-slm-optimization` (AXO HYBRID /6)  
> **Preregistered Gate Specification:** [`../slm-local-geometry-understanding/preregistered_replacement_criteria.json`](../slm-local-geometry-understanding/preregistered_replacement_criteria.json) (`slm-preregistered-replacement-criteria/1`, thresholds UNCHANGED)  
> **Primary Verdict:** **`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`**  
> **Production Default Status:** Keep **`HYBRID_ROUTE_MODE = "live"`** (Gemini 2.5 Flash) as production default. Retain **`HYBRID_ROUTE_MODE = "local-slm"`** strictly as an **opt-in experimental local/offline route**, upgraded in-place to `/6 compact_clause` (`slm-compact-clause/1` + `slm-verified-normalizer/1` + `local-slm-runtime/2`). **DO NOT auto-replace Gemini.**

---

## 1. Gate-by-Gate Evaluation Against Unmodified Preregistered Criteria

| Criterion (`slm-preregistered-replacement-criteria/1`) | `READY_TO_REPLACE_GEMINI_DEFAULT` | `READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS` | `PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL` | Observed `/6` Measurement | Gate Status |
|---|---|---|---|---|---|
| False-positive `Mode A` leaks | `<= 0` | `<= 0` | `<= 0` | **`0`** across `DEV_CALIBRATION_16` (`0/6`), `HOLDOUT_40` (`0/12`), blind `SLM_NEW_HOLDOUT_48` (`0/16`), `REAL27`, `NC`, `AUTONOMOUS_NEGATIVES`, `RM72`, `DEV37`, `PROBES39`, `S2_36`, `COMP112` (`2` historical items had `slm_invoked=false`, identical to Det `v145`) | **PASS** |
| `Scene3D` continuity errors | `<= 0` | `<= 0` | `<= 0` | **`0`** across all suites and holdouts | **PASS** |
| Deterministic `v145` regressions | `0` | `0` | `0` | **`0`** (`regression_count = 0` across 11 regression suites) | **PASS** |
| External AI / network calls | `0` | `0` | `0` | **`0`** (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`) | **PASS** |
| Holdout disjointness overlaps | `0` | `0` | `0` | **`0`** exact & **`0`** structural skeleton overlaps vs `328` unlocked corpus rows (`max_jaccard = 0.68`) | **PASS** |
| Fault-injection & adversarial checks | All pass | All pass | All pass | **`14 / 14 PASS`** (`SLM_REGRESSION_REPORT.md`) + `24 / 24` grounding reliability checks PASS (`SLM_GROUNDING_RELIABILITY.json`) | **PASS** |
| Combined RSS vs 4–6 GiB RAM budget | `<= 2048 MiB` | `<= 2048 MiB` | `<= 2048 MiB` | **`1049.30 MiB`** peak warm bench (`p50 = 1042.93 MiB`, `n=30, 6T`), **`1170.95 MiB`** peak holdout (`p50 = 1170.61 MiB`, `n=28`); server load `p50 = 997.90 ms <= 5000 ms`; **`PHYSICAL_LOW_END = NOT_MEASURED`** (15.78 GiB host) | **PASS (Host RSS; low-end physical NOT_MEASURED)** |
| Blind holdout negative refusal rate | `1.0` | `1.0` | `1.0` | **`1.0` (`16 / 16`)** on `SLM_NEW_HOLDOUT_48` (`12/12` on `HOLDOUT_40`, `6/6` on `DEV16`) | **PASS** |
| Warm inference CPU `p95` | `<= 5000 ms` | `<= 12000 ms` | `<= 20000 ms` | **`5392.59 ms`** (`threads=6`, `p50=3204.27 ms`) · **`5116.95 ms`** (`SLM_NEW_HOLDOUT_48` `p50=3837.81 ms`) · `threads=8` achieves `4452.59 ms` (`p50=2993.00 ms`) | **FAILS Default (`<= 5000ms` at 6T); PASSES Primary (`<= 12s`) & Experimental** |
| **Blind single-shot holdout positive exact rate (`SLM_NEW_HOLDOUT_48`)** | **`>= 0.85` (`>=28/32`)** | **`>= 0.65` (`>=21/32`)** | **`> Config A` (`>13/32`)** | **`0.5938` (`19 / 32`)**, 95% Wilson CI `[0.4226, 0.7448]` (up `+6` / `+18.75 pp` vs `Config A 13/32` & `/5 13/32`, McNemar `p = 0.03125`; SLM rescue `6/19 = 31.58%` vs `0/19`) *(Diagnostic `HOLDOUT_40`: `18/28`, `DEV16`: `8/10`)* | **FAILS Default (`0.85`) & Primary (`0.65` by 2 cases); PASSES `> Config A`** |
| Derived section & relation parity vs Gemini 2.5 Flash | `Required` | `Optional` | `Optional` | **No parity:** `compact_clause` omits derived sections, constrained multi-solid cuts, and no live Gemini A/B comparator ran (`external_ai_calls = 0`) | **FAILS Parity** |

---

## 2. Scientific Verdict Rationale & Honest Progress vs `/5`

1. **Substantial Real Progress Over AXO HYBRID /5 (Hypotheses Confirmed):**
   - Shifting deterministic string copying, entity/quantity identification, and surface canonicalization out of `Qwen3-0.6B` into `slm-verified-normalizer/1` + per-problem GBNF (`slm-compact-clause/1`) **doubled blind SLM rescue rate from `0/19 (0%)` (`/5`) to `6/19 (31.58%)` (`/6`)** (`19/32 = 59.38%` vs `13/32 = 40.62%`, McNemar `p = 0.03125`), lifted `DEV_CALIBRATION_16` from `2/10` to **`8/10`** (`p = 0.03125`), and lifted diagnostic `HOLDOUT_40` from `10/28` to **`18/28`** (`p = 0.007812`) with **`0` validator rejections** and **`0` false serves**.
   - CPU latency dropped **by more than half** (`p50` `6683.53 -> 3204.27 ms` warm bench `-52.1%`; `8494.29 -> 3837.81 ms` blind holdout `-54.8%`; paired `9012.71 -> 3429.11 ms` `-62.0%`), and repeat requests hit `LocalSlmExtractionCache` in **`p50 = 39.64 ms / p95 = 53.92 ms`**.
2. **Why `PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL` Remains Mandatory:**
   - **Below Local-Primary (`0.65`) and Default-Replacement (`0.85`) Accuracy Gates:** Under strict pre-registered thresholds and untouched blind single-shot scoring (`19/32 = 59.38%`), `/6` misses `READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS` (`>= 21/32 = 65.6%`) by `2` cases and misses `READY_TO_REPLACE_GEMINI_DEFAULT` (`>= 28/32`) by `9` cases.
   - **6-Thread Warm `p95` Just Above `5000 ms`:** Default `threads=6` warm uncached `p95` (`5392.59 ms`) and blind holdout `p95` (`5116.95 ms`) exceed the `5000 ms` default threshold (only `threads=8` measured `p95 = 4452.59 ms` on a 12-logical-core development host).
   - **Scope & Hardware Unmeasured Boundaries Preserved:** Derive sections, multi-solid relations, and direct Gemini parity remain unimplemented/unmeasured (`external_ai_calls = 0`), **`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`**, **`REAL_STUDENT_USABILITY = NOT_MEASURED`**, **`PHYSICAL_LOW_END = NOT_MEASURED`** (all RSS measurements `1040–1171 MiB` come from a 15.78 GiB development host), and `frozen_unseen_vmmu20` remains strictly separated (`GROUND_TRUTH_UNVERIFIED`, `0` unverified serves).
3. **Deployment Decision:**
   - Keep **`HYBRID_ROUTE_MODE = "live"`** (Gemini 2.5 Flash) as production default (`CACHE_VERSION = "145"`, `4` locked Gemini extraction surfaces 100% unchanged).
   - Keep **`HYBRID_ROUTE_MODE = "local-slm"`** as a dramatically faster (`3.2–3.8 s` p50 uncached, `39.6 ms` cached), safer (`0` leaks), and strictly higher-coverage (`+6/32` blind holdout, `+9/28` diagnostic holdout) opt-in offline mode.
   - Execute the **Case C (surface/Source-Gate closure) + Case B (disjoint compact QLoRA on `Qwen3-0.6B`)** roadmap specified in [`SLM_FINE_TUNING_DECISION.md`](SLM_FINE_TUNING_DECISION.md) before any future re-evaluation against the `>= 85%` Gemini replacement bar.
