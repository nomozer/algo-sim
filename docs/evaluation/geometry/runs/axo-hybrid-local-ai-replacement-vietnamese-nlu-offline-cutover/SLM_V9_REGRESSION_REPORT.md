# AXO HYBRID /9 — Phase P9 Full Regression, Security & Construction Freeze Integrity Report

> **Runner:** [`run_slm_v9_regressions.py`](../../../../../backend/scripts/run_slm_v9_regressions.py) (`SLM_V9_REGRESSION_RESULTS.json`)  
> **Configuration Audited:** Product Commit `f285fcec1` (`Config E = Qwen3-0.6B-AxoV9-Q4_K_M` + `slm-verified-normalizer/3` + `local-slm-extractor/4` `closure_mode="v9"` + `local-slm-runtime/4`, `HYBRID_V9_LOCAL_SLM`, `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`)

---

## 1. Core Safety Invariants

| Invariant | Verified Result |
| --- | --- |
| External AI / Gemini Calls (`external_ai_calls`) | **`0`** |
| Baseline Positive Regressions vs. `Config A` (`det v145`) | **`0`** (`[]`) |
| New Mode A Answer Leaks Above `Config A` | **`0`** |
| `Scene3D` Continuity Errors (`Config E`) | **`0`** |
| Internal Token / Traceback Leaks (`<think>`, `compact_clause`) | **`0`** |
| `AXO CONSTRUCTION /2` Package Freeze Integrity (`CANDIDATE_V2_FREEZE_SHA256`) | **`MATCH` (`26c9b505fc7796ed9ff6a5c9578701978e92b9c1d6726a8208916a9ea3dca60c`, `14` `.py` files, `0` diffs)** |

---

## 2. Existing 11 Baseline Geometry Suites (`Config A` vs. `Config E`)

| Suite | Positives (`Config A -> Config E`) | Negatives Safe (`Config A -> Config E`) | Wrong-Served | Regression? |
| --- | --- | --- | --- | --- |
| `REAL27_TEXT` (`27`) | `21/27 -> 21/27` | `—` | **`0`** | No |
| `REAL27_IMAGES` (`27`) | `21/27 -> 21/27` | `—` | `0` | No |
| `NC_NL` (`21`) | `21/21 -> 21/21` | `—` | `0` | No |
| `NC_GOLD` (`21`) | `21/21` | `—` | `0` | No |
| `AUTONOMOUS_NEGATIVES` (`11`) | `—` | `11/11` | `0` | No |
| `RM72` (`72`) | `61/62` | `10/10` | `0` | No |
| `DEV37` (`37`) | `30/30 -> 30/30` | `7/7 -> 7/7` | `0` | No |
| `PROBES39` (`39`) | `23/26 -> 23/26` | `13/13 -> 13/13` | `0` | No |
| `S2_36` (`36`) | `16/18 -> 16/18` | `18/18 -> 18/18` | `0` | No |
| `COMP112` (`112`, dual strict / historical) | `66/66 -> 66/66` | `44/46 -> 44/46` (`112/112` reconciled historical, `slm_invoked=False`) | **`0` new leaks** | No |
| `frozen_unseen_vmmu20` (`19`, separate) | `0/19` unverified served (`GROUND_TRUTH_UNVERIFIED`) | — | — | No |

---

## 3. Historical SLM Suites (`HISTORICAL_REGRESSION_COMPARISON_NOT_NEW_BLIND_HOLDOUT`, `axo-math-evaluator/2`)

> **Disclosure:** These corpora were used during `/5`–`/8` calibration or post-audit analysis and are reported strictly as historical comparisons against `/8` (`AxoV7 + v7/v2`), never as unseen `/9` holdouts.

| Historical Suite | `/8` `AxoV7` Positives | `/9` `AxoV9 + v9/v3` Positives | Fast / SLM Split | Negatives Safe | Wrong-Served | Delta (`AxoV7 -> AxoV9`) |
| --- | --- | --- | --- | --- | --- | --- |
| `DEV_CALIBRATION_16` (`10+/6-`) | `9 / 10` | `8 / 10` | `6` fast + `2` SLM | `6 / 6` | **`0`** | `-1` (fail-closed refusal shift, `0` wrong-served) |
| `HOLDOUT_40` (`28+/12-`) | `24 / 28` | **`25 / 28`** | `23` fast + `2` SLM | `12 / 12` | **`0`** | **`+1`** |
| `SLM_NEW_HOLDOUT_48` (`32+/16-`) | `32 / 32` | `31 / 32` | `26` fast + `5` SLM | `16 / 16` | **`0`** | `-1` (fail-closed refusal shift, `0` wrong-served) |
| `SLM_V7_HOLDOUT_112` (`80+/32-`) | `74 / 80` | `70 / 80` | `48` fast + `22` SLM | `32 / 32` | **`0`** | `-4` (`/7`-template specificity trade-off, `0` wrong-served) |
| `C60_BLIND_NLU` (`42+/18-`) | `13 / 42` (`30.95%`) | **`32 / 42` (`76.19%`)** | `23` fast + `9` SLM | `18 / 18` | **`0`** | **`+19` (`+45.24 pp`)** |
| `EXTERNAL17_REAL_TRANSCRIPTIONS` (`12+/5-`) | `12 / 12` | `12 / 12` (`100%`) | `12` fast | `5 / 5` | **`0`** | `0` (parity maintained) |
| `PERMISSIBLE_UNSEEN_77` Combined | `25 / 54` (`46.30%`) | **`44 / 54` (`81.48%`)** | `35` fast + `9` SLM | `23 / 23` | **`0`** | **`+19` (`+35.19 pp`)** |
| **Total Across All 5 Historical Corpora** | **`164 / 224`** | **`178 / 224`** | — | **`89 / 89` (`100%`)** | **`0`** | **Net `+14` solved positives, `0` wrong-served** |

---

## 4. Security & Runtime Fault Checks (`16 / 16 PASS`)

All 16 security and fault-recovery checks passed on `AxoV9-Q4_K_M` (`v9`/`v3`) and preserved `AxoV7` rollback checksums:
`malformed_output`, `model_crash`, `model_timeout`, `missing_model`, `incorrect_checksum` (`MODEL_CHECKSUM_MISMATCH` on all 3 GGUFs + HTTP `503 MISSING_API_KEY` on unkeyed `live`), `port_binding_failure`, `bounded_queue_overflow`, `prompt_injection`, `conflicting_premises`, `unsupported_relation`, `negation`, `conditional_clauses`, `ambiguous_references`, `invalid_quantities`, `concurrent_inference`, and `process_recovery_after_repeated_requests`.

---

## 5. Pytest Suites (`14` Targeted Modules + Full Clean-Tree Backend)

- **Targeted `14` Modules on Clean Frozen Commit (`107fd290d`):** **`280 passed, 1 warning in 145.13s` (`0 failed`, exit code `0`)** via `run_slm_v9_regressions.py --refresh-pytest-only`, including all SLM `/5`–`/9` suites, `test_slm_v9_language_closure_and_security.py`, `test_local_only_product_and_network_isolation.py`, `test_api.py`, `test_s2_student_language_pilot_runner.py`, `test_evaluation_candidate.py`, and `AXO CONSTRUCTION /1`–`/2` suites.
- **Full Clean-Tree Backend Pytest (`pytest -c backend/pytest.ini backend/tests -q` on `107fd290d`):** **`15,099 passed, 7 skipped, 3 deselected, 12 xfailed, 0 failed` (`1` warning) in `931.68s` (`0:15:31`, exit code `0`)**.
