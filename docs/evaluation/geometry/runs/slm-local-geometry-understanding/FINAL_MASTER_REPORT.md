# FINAL_MASTER_REPORT.md — AXO HYBRID /5: Specialized Sub-1B Local SLM for Vietnamese Geometry Understanding

**Run ID:** `slm-local-geometry-understanding`  
**Branch:** `feat/local-first-geometry-understanding` (`range_base_commit`: `69526ca6c2dc20124f49b3b707b394164d183f84`)  
**Product Commit:** `a182b54600752e57f3be408aad6a673bd9a0d41f` (`a182b5460`)  
**Frozen Candidate:** `96791162faa46df330beee9aef2f17f82e03c868` (`96791162f`, `122` measured files, `tree_hash = 771fe868279c814f9a913ab5120b8dba35c086b6f8e523112c95b4b837e2f542`, `cay_lam_viec_sach = true`)  
**Cache & Locked Gemini Surfaces:** `CACHE_VERSION = "145"` (`145:route-d`), `semantic_environment_hash = 6233c43c395c9b49...`, all `4` locked Gemini schema/surface hashes (`function_calling`, `fact_extraction_flat`, `fact_extraction_v3`, `typed_fact_next`) preserved **100% unchanged**  
**Offline Constraint:** `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`, `0` edits under `frontend/**`, `Planner /26`, `Registry /33`, `Exact Kernel /24`, `Source Gate`, `sealed H-1`, `locked W2/W3`, or frozen `v145` artifacts  
**Preregistered Replacement Verdict:** **`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`** (`HYBRID_ROUTE_MODE = "live"` remains production default; `HYBRID_ROUTE_MODE = "local-slm"` retained as opt-in local/offline fallback)

---

## 1. Executive Summary & Scientific Verdict

This campaign implemented, sandbox-isolated, empirically benchmarked, and rendered an evidence-based replacement decision on a sub-1B local CPU Small Language Model (**`Qwen3-0.6B-Q4_K_M`** primary + **`Qwen2.5-0.5B-Instruct-Q4_K_M`** comparator via bundled MIT `llama.cpp b12470`) operating behind Axo's deterministic Source Grounding, `TypedFactNext /2`, `Planner /26`, `Registry /33`, `Exact Kernel /24`, and `Adapter /4`.

Against the preregistered gates in [`preregistered_replacement_criteria.json`](preregistered_replacement_criteria.json), the empirical verdict is **`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`**:

1. **Zero Safety Harm Proven Across All Suites:** `0` new false `Mode A` leaks (`0/6` `DEV_CALIBRATION_16` neg, `0/18` `S2` neg, `0/12` holdout neg, `0/11` autonomous neg, `0/10` RM72 neg, `0/13` PROBES39 neg, `0` leaks on `REAL27`; `COMP112` has `2` identical to deterministic Config A where `slm_invoked = false`), `0` `Scene3D` continuity errors, `0` regressions on `v145` baselines, and `5/5` fault-injection recovery checks (`missing_model_fail_closed`, `crash_auto_recovery`, `timeout_kill_and_recovery`, `bounded_queue_busy`, `prompt_injection_rejected`) PASS.
2. **Genuine Net Coverage Gain Over Deterministic `v145`:** Approach B (`minimal_ops` + `slm-grounding-validator/1`) improved `DEV_CALIBRATION_16` partial-parser solves from `0/10` (`deterministic_v145`) and `0/10` (`direct_wire`) to **`2/10`** (`cal_p01_pyramid_vol = a³√3/6`, `cal_p02_dist_split = 2a√57/19`), and raised `SLM_INDEPENDENT_HOLDOUT_40` (`0` overlap across `9` corpora) positive exact solves from `9/28` (`32.14%`) to **`10/28`** (`35.71%`, `+1` net gain on `slm_h28_split_dist_3a_4a = 12a√273/91`), while `Qwen2.5-0.5B` stayed flat at `9/28` (`+0`, with JSON loop truncations).
3. **Why Gemini 2.5 Flash Is NOT Replaced Today:** Zero-shot sub-1B CPU inference achieves `35.71%` holdout accuracy (below `>= 85%` `READY_TO_REPLACE_GEMINI_DEFAULT` and `>= 65%` `READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS`), runs at `p95 = 8025.00–8480.07 ms` warm bench / `11693.69 ms` holdout CPU latency (above `<= 5000 ms` default gate), and lacks derived section & multi-solid relation parity. Therefore `HYBRID_ROUTE_MODE = "live"` stays default and `HYBRID_ROUTE_MODE = "local-slm"` stays opt-in experimental.

---

## 2. Implemented Product Components & Contracts

- **Runtime (`local-slm-runtime/1`):** [`backend/app/ai/local_slm_runtime.py`](../../../../../backend/app/ai/local_slm_runtime.py) & [`backend/scripts/provision_local_slm.py`](../../../../../backend/scripts/provision_local_slm.py)  
  - Bundles pinned MIT `llama-b12470-bin-win-cpu-x64.zip` (`25,272,394` B, `sha256:fc833716...`) and Apache-2.0 GGUF artifacts (`Qwen3-0.6B-Q4_K_M.gguf` `396,705,472` B; `qwen2.5-0.5b-instruct-q4_k_m.gguf` `491,400,032` B) outside the Git repository (`%LOCALAPPDATA%\axo-slm`).
  - Resolves Qwen3 `<think>` vs strict JSON grammar conflicts via `--reasoning off`, preserves test offline guards via stdlib `http.client` on `127.0.0.1`, avoids Windows `WinError 10013` port exclusion via `[31000..47999]` fallback, measures 64-bit Win32 process RSS via `psapi.GetProcessMemoryInfo`, enforces bounded concurrency (`LOCAL_SLM_BUSY`), and auto-restarts on crash/timeout (`LOCAL_SLM_TIMEOUT`).
- **Extractor & Grounding Gate (`local-slm-extractor/1`, `slm-grounding-validator/1`, `slm-grounding-envelope/1`):** [`backend/app/ai/local_slm_extractor.py`](../../../../../backend/app/ai/local_slm_extractor.py)  
  - Implements calibration comparator Approach A (`direct_wire`) and winner Approach B (`minimal_ops`), with pre-inference prompt-injection blocking (`PROMPT_INJECTION_REJECTED`), verbatim clause indexing (`split_into_Sentences`), closed lexical cues, negation/question guards, proximity & symbolic `parse_quantity_expr` checks, singular `"cạnh bên"`/`"mặt bên"` ambiguity checks (`AMBIGUOUS_REFERENCE`), and Local Parser conflict guards (`PARSER_SLM_CONFLICT`).
- **Router & API Integration:** [`backend/app/ai/adaptive_input_router.py`](../../../../../backend/app/ai/adaptive_input_router.py) (`LOCAL_SLM_FALLBACK`, `route_text_input_local_slm`), [`backend/app/ai/hybrid_offline.py`](../../../../../backend/app/ai/hybrid_offline.py) (`LocalSlmHybridRun`, `HYBRID_V5_LOCAL_SLM` isolated cache key, `502`/`503`/`504` infra mapping), [`backend/app/main.py`](../../../../../backend/app/main.py) (`HYBRID_ROUTE_MODE=local-slm` opt-in; `"live"` default & `CACHE_VERSION="145"` untouched).
- **Automated Tests:** [`backend/tests/geometry/test_local_slm_understanding.py`](../../../../../backend/tests/geometry/test_local_slm_understanding.py) (`5 passed` in targeted CPU API + fault-recovery verification).

---

## 3. Empirical Results Across Calibration, Baseline Suites, Disjoint Holdout & Resources

### A. Strategy Calibration (`DEV_CALIBRATION_16`, `Qwen3-0.6B-Q4_K_M`, [`dev_calibration_16.json`](dev_calibration_16.json))

| Mode / Strategy | Positives Solved | Negatives Refused | False Mode A Leaks | Continuity Errors | Total `p50` / `p95` (ms) | SLM `p50` / `p95` (ms) |
|---|---|---|---|---|---|---|
| `deterministic_v145` | `0 / 10` | `6 / 6` | `0` | `0` | `8.35` / `51.95` | `N/A` (`0` calls) |
| `direct_wire` (Approach A) | `0 / 10` | `6 / 6` | `0` | `0` | `13962.67` / `17047.14` | — |
| `minimal_ops` (Approach B — Winner) | **`2 / 10`** | **`6 / 6`** | **`0`** | **`0`** | `8381.93` / `14746.84` | `8364.31` / `14730.26` |

### B. Full Regression & Disjoint Holdout Comparison (`0` External AI Calls, [`SLM_BASELINE_COMPARISON.json`](SLM_BASELINE_COMPARISON.json))

| Suite | Config A (`Deterministic v145`) | Config B (`Local Parser + Qwen3-0.6B minimal_ops`) | SLM Invoked | Delta / Notes |
|---|---|---|---|---|
| `REAL27_TEXT` (`27`) | `21 / 27` served (`0` wrong) | `21 / 27` served (`0` wrong) | `4` (`r256, r461, r475, r491`) | `0` wrong; 4 invoked refusals stayed fail-closed |
| `REAL27_IMAGES` (`27`, post-OCR artifact) | `21 / 27` served | `21 / 27` served | `4` | Reuses verified `v145` post-OCR text parity |
| `NC_GOLD` (`21`) & `NC_NL` (`21`) | `21 / 21` & `21 / 21` | `21 / 21` & `21 / 21` | `0` | Parser fast-path handles all cleanly (`0` SLM calls) |
| `AUTONOMOUS_NEGATIVES` (`11`) | `11 / 11` refused (`0` false) | `11 / 11` refused (`0` false) | — | `0` leaks |
| `RM72` (`62` pos + `10` neg) | `61 / 62` pos + `10 / 10` neg | `61 / 62` pos + `10 / 10` neg | — | `MG9` stays `IR_MEMORY_BUDGET_EXCEEDED` |
| `DEV37` (`30` pos + `7` neg) | `30 / 30` pos + `7 / 7` neg | `30 / 30` pos + `7 / 7` neg | `4` | `delta = 0`, `0` false serves |
| `COMP112` (`66` pos + `46` neg) | `66 / 66` pos + `44 / 46` neg | `66 / 66` pos + `44 / 46` neg | `19` | `2` identical `slm_invoked=false` (`dp_reflection`, `dp_projection_unnamed_image`) |
| `PROBES39` (`26` pos + `13` neg) | `23 / 26` pos + `13 / 13` neg | `23 / 26` pos + `13 / 13` neg | `10` | `delta = 0`, `0` leaks |
| `S2_36` (`18` pos + `18` neg) | `17 / 18` served (`16 / 18` ok) + `18 / 18` neg | `17 / 18` served (`16 / 18` ok) + `18 / 18` neg | `1` (`S2-F-S07`) | Typo `"hình chop"` refused `UNGROUNDED_VALUE` |
| **`SLM_INDEPENDENT_HOLDOUT_40`** (`28` pos + `12` neg) | `9 / 28` pos (`32.14%`) + `12 / 12` neg | **`10 / 28` pos (`35.71%`) + `12 / 12` neg** | `25` | **`+1` gain** (`slm_h28_split_dist_3a_4a = 12a√273/91`), `0` leaks, `0` corpus overlaps |

### C. Model-to-Model Extraction & Resource Benchmarks ([`SLM_EXTRACTION_EVALUATION.json`](SLM_EXTRACTION_EVALUATION.json) & [`SLM_RESOURCE_BENCHMARK.json`](SLM_RESOURCE_BENCHMARK.json))

- **`Qwen3-0.6B-Q4_K_M` (`minimal_ops`):** `HOLDOUT_40` **`10 / 28` (`35.71%`)**, `12 / 12` neg refused (`0` false positives), `DEV_CALIBRATION_16` **`2 / 10`**, `S2_INCOMPLETE` `0 / 1`, holdout SLM `p50 = 10603.26 ms` / `p95 = 11693.69 ms`, **`0` JSON truncations**; warm resource bench (`threads=6`): load `834.98 ms`, cold `8913.13 ms`, warm `p50 = 6683.53 ms`, `p95 = 8025.00 ms`, `38.08 tok/s`, peak combined RSS **`1040.57 MiB`** (`924.43 MiB` server RSS, `< 2048 MiB`), `0` warm runtime failures (`threads=4`: warm `p50 = 8065.27 ms`, `p95 = 8480.07 ms`, `32.18 tok/s`, peak combined RSS `1039.62 MiB`).
- **`Qwen2.5-0.5B-Instruct-Q4_K_M` (`minimal_ops`):** `HOLDOUT_40` **`9 / 28` (`32.14%`)**, `12 / 12` neg refused, `DEV_CALIBRATION_16` **`0 / 10`**, holdout SLM `p50 = 7662.48 ms` / `p95 = 11410.15 ms`, **`2 / 40` holdout + `4 / 16` cal + `1 / 5` warm bench (`cal_p05`) `LOCAL_SLM_RESPONSE_INVALID` JSON truncation loops**; warm resource bench (`threads=4`): load `731.51 ms`, cold `7926.47 ms`, warm `p50 = 5440.94 ms`, `p95 = 5730.06 ms`, `44.06 tok/s`, peak combined RSS `674.81 MiB` (`558.77 MiB` server RSS).

---

## 4. Strictly Separated Blind Set, Pending C21 Metadata Refresh & Honest Limitations

- **`frozen_unseen_vmmu20_separate` (`19` items):** Strictly excluded from verified accuracy denominators (`GROUND_TRUTH_UNVERIFIED`, `independent_ground_truth_validation = NOT_MEASURED`, `served_unverified_count = 0`).
- **C21 Pending Approval Template Metadata Refresh ([`pending_template_refresh.json`](pending_template_refresh.json)):** Because `backend/app/` grew from `120` to `122` measured files (`8a88dbfe9ddc… -> 771fe868279c…`), the three pending owner templates (`k1`, `s2`, `r1`) under `hybrid-master-backend-replacement/` had their `measured_system` / `measured_system_tree_hash` metadata synced (prior snapshots archived in `logs/prior-*-owner-approval.template.json`), strictly preserving `owner_decision = "PENDING_OWNER_DECISION"` and `paid_project_confirmed = false`. Targeted verification (`test_s2_student_language_pilot_runner.py`): **`106 passed` (`0 failed`)**.
- **Unmeasured / Deferred Boundaries:** `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` · `PHYSICAL_LOW_END = NOT_MEASURED` (host had `15.78 GiB` RAM) · `REAL_STUDENT_USABILITY = NOT_MEASURED` · `FRONTEND_INTEGRATION = BLOCKED_OWNERSHIP`.

---

## 5. Companion Run Deliverables & Authoritative Verification Status

- [`SLM_ARCHITECTURE.md`](SLM_ARCHITECTURE.md) — Pipeline integration, `direct_wire` vs `minimal_ops`, and 6-layer deterministic grounding checks.
- [`SLM_RUNTIME_IMPLEMENTATION.md`](SLM_RUNTIME_IMPLEMENTATION.md) — Pinned binary/GGUF manifests, runtime fixes (`--reasoning off`, `WinError 10013`, 64-bit Win32 RSS), thread scaling, and `5/5` fault recovery.
- [`SLM_FAILURE_ANALYSIS.md`](SLM_FAILURE_ANALYSIS.md) — Zero-leak proof and 3-layer failure breakdown across the `18` holdout misses.
- [`SLM_REPLACEMENT_DECISION.md`](SLM_REPLACEMENT_DECISION.md) — Preregistered gate matrix (`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`), LoRA/QLoRA roadmap, and Dynamic Geometry Construction Planning architecture beyond fixed patterns.
- [`SLM_MODEL_MANIFEST.json`](SLM_MODEL_MANIFEST.json), [`SLM_BASELINE_COMPARISON.json`](SLM_BASELINE_COMPARISON.json), [`SLM_EXTRACTION_EVALUATION.json`](SLM_EXTRACTION_EVALUATION.json), [`SLM_RESOURCE_BENCHMARK.json`](SLM_RESOURCE_BENCHMARK.json), [`dev_calibration_16.json`](dev_calibration_16.json), [`preregistered_replacement_criteria.json`](preregistered_replacement_criteria.json), [`independent_slm_holdout_manifest.json`](independent_slm_holdout_manifest.json), [`pending_template_refresh.json`](pending_template_refresh.json), [`run.json`](run.json).

**Pre-Clean-Tree Full Pytest Baseline + Targeted Runner:** Prior full suite before final docs (`14,900 passed, 7 skipped, 3 deselected, 12 xfailed`, with only `test_docs_information_architecture` failing before `FINAL_MASTER_REPORT.md` existed) and C21 runner check (`106 passed`). **Clean-tree authoritative full `pytest` verification receipt on Commit 1 follows in the final verification revision below.**
