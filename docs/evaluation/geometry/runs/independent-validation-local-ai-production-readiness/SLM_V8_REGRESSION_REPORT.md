# AXO HYBRID /8 — Regression, Security & Verification Report (`SLM_V8_REGRESSION_REPORT.md`)

> **Verdict (`Gate D8` & `Gate D9`):** **`PASS`**  
> **Code Under Test:** Frozen `/7` Product Candidate (`6310113f2202bc3a4919406b26fad08cb09b38c9` / `measured_system = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `123` files, `0` edits to `backend/app/**` or `frontend/**`) + `/8` Evaluation/Test Commit **`6ca84e5367f7dd2e21f58978ef8d4c196c7959cb`** (`6ca84e536`)  
> **Environment:** `ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`, `axo-math-evaluator/2`, `local-slm-runtime/3`, `HYBRID_V7_LOCAL_SLM`, `HYBRID_ROUTE_MODE = "live"` default preserved  
> **Machine Receipt:** [`SLM_V8_REGRESSION_RESULTS.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/SLM_V8_REGRESSION_RESULTS.json)

---

## 1. Zero-Regression Verification Across Baseline & Frozen Product Suites (`VERIFIED`)

Comparing `Config A` (`det_v145`) vs `Config D` (`/7 + Qwen3-0.6B-AxoV7-Q4_K_M`) via [`run_slm_v8_regressions.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/run_slm_v8_regressions.py):

- **Baseline regressions (`Config D` < `Config A` on any expected positive):** **`0`**
- **New `Mode A` leaks above `Config A`:** **`0`**
- **`Scene3D` continuity errors (`Config A` / `Config D`):** **`0`** / **`0`**
- **Internal token leaks (`<think>`, `</think>`, `compact_clause`, trace markers) on student/refusal surfaces:** **`0`**

| Suite | Positives (`Config A` / `Config D`) | Negatives (`Config A` / `Config D`) | Wrong-Served | Separation / Dual-Report Notes |
|---|---:|---:|---:|---|
| `NC_NL` (`21`) | `21/21` / `21/21` | `0/0` / `0/0` | `0` | Exact parity (`0` regressions) |
| `NC_GOLD` (`21`) | — / `21/21` | — | `0` | Verified |
| `AUTONOMOUS_NEGATIVES` (`11`) | — | — / `11/11` | `0` | `100%` refused |
| `RM72` (`72`) | — / `61/62` | — / `10/10` | `0` | `MG9` fail-closed at `IR_MEMORY_BUDGET_EXCEEDED` |
| `DEV37` (`37`) | `30/30` / `30/30` | `7/7` / `7/7` | `0` | Exact parity |
| `PROBES39` (`39`) | `23/26` / `23/26` | `13/13` / `13/13` | `0` | Exact parity |
| `S2_36` (`36`) | `16/18` / `16/18` | `18/18` / `18/18` | `0` | Exact parity |
| `COMP112` (`112`) | `66/66` / `66/66` | `44/46` / `44/46` | `0` new | Historical `dp_reflection` & `dp_projection_unnamed_image` identical to `Config A` (`slm_invoked = False`; `112/112` reconciled, `0` new Mode A leaks) |
| `REAL27_TEXT` (`27`) | `21/27` / `21/27` | — | `0` | `0` wrong-served |
| `REAL27_IMAGES` (`27`) | `21/27` / `21/27` | — | `0` | `0` regressions |
| `frozen_unseen_vmmu20` (`19`, separate) | `0` unverified serves (`Config D`) | — | `0` | Strictly `GROUND_TRUTH_UNVERIFIED` / excluded from accuracy |

---

## 2. Live `Config D` Re-Verification Under `axo-math-evaluator/2` (`VERIFIED`)

| Historical / Calibration / Holdout Suite | Positives Passed | Negatives Safe | Wrong Served | Continuity Errors | Internal Token Leaks |
|---|---:|---:|---:|---:|---:|
| `DEV_CALIBRATION_16` (`10+ / 6-`) | `9/10` | `6/6` | `0` | `0` | `0` |
| `HOLDOUT_40` (`28+ / 12-`) | `24/28` | `12/12` | `0` | `0` | `0` |
| `SLM_NEW_HOLDOUT_48` (`32+ / 16-`) | `32/32` (`100%`) | `16/16` | `0` | `0` | `0` |
| **`SLM_V7_HOLDOUT_112`** (`80+ / 32-`) | **`74/80` (`92.50%`)** | **`32/32` (`100%`)** | **`0`** | **`0`** | **`0`** |

*(Confirms byte-for-byte reproducibility of `/7` live `Config D` under `axo-math-evaluator/2`, closing `/7`'s raw `69/80` `cos²=` formatting artifact without mutating `/7` receipts.)*

---

## 3. All `16/16` Security & Runtime Fault-Injection Checks (`/8 §16`, `PASS`)

All 16 mandatory security and fault-recovery checks passed across both `Qwen3-0.6B-Q4_K_M` and `Qwen3-0.6B-AxoV7-Q4_K_M`:

| # | Security / Runtime Fault Case | Status | Verification Summary |
|---|---|---|---|
| 1 | `malformed_output` | **PASS** | Mocked HTTP loopback returning `<think>secret</think>{bad_json` and non-object `[1, 2, 3]` cleanly raises `LocalSlmRuntimeError("LOCAL_SLM_RESPONSE_INVALID")`, returns `REFUSED` with `0` `<think>` leaks *(Note: `validate_and_lower_compact_clause` itself assumes a `dict` at `local_slm_extractor.py:3026`, which `local_slm_runtime.py:1057` always guarantees before returning; non-blocking owner hardening note to add an `isinstance(..., dict)` guard in a future product slice)* |
| 2 | `model_crash` | **PASS** | Killed `llama-server` PID -> fail-closed error, automatic healthy restart on next request |
| 3 | `model_timeout` | **PASS** | Socket/timeout simulation -> `LOCAL_SLM_TIMEOUT` (`504`), automatic clean recovery |
| 4 | `missing_model` | **PASS** | Non-existent model file -> fail-closed `MODEL_FILE_MISSING`, zero cloud fallback |
| 5 | `incorrect_checksum` | **PASS** | Bad SHA-256 -> `MODEL_CHECKSUM_MISMATCH`, zero cloud fallback |
| 6 | `port_binding_failure` | **PASS** | Blocked ephemeral port (`62974`) -> `LocalSlmRuntimeError`, clean recovery once port freed |
| 7 | `bounded_queue_overflow` | **PASS** | Queue limit enforced (`BUSY` rejection on overflow), `0` zombie sockets |
| 8 | `prompt_injection` | **PASS** | EN & VI instruction-override attempts blocked (`0` grounded premises accepted) |
| 9 | `conflicting_premises` | **PASS** | Contradictory geometric claims rejected by validator / Source Gate |
| 10 | `unsupported_relation` | **PASS** | Curved/sphere problem (`mặt cầu nội tiếp`) refused safely |
| 11 | `negation` | **PASS** | Negated perpendicular clauses never inverted into positive premises |
| 12 | `conditional_clauses` | **PASS** | Conditional `"Nếu ... thì ..."` clauses never promoted as facts |
| 13 | `ambiguous_references` | **PASS** | Ambiguous quantifiers / unqualified refs refused safely |
| 14 | `invalid_quantities` | **PASS** | Negative length (`-2a`) rejected fail-closed (`NON_POSITIVE_LENGTH` / refused) |
| 15 | `concurrent_inference` | **PASS** | Parallel requests serialized cleanly with `SERVED` & `0` continuity errors |
| 16 | `process_recovery_after_repeated_requests` | **PASS** | `5/5` consecutive requests after fault cycles `SERVED`, `0` continuity errors, `0` leaks |

---

## 4. Pytest Verification (`91/91` Targeted + `15,026` Full Clean-Tree Backend, `PASS`)

1. **Targeted SLM & `/8` Test Suite (`7` modules via `run_slm_v8_regressions.py`):**
   - `test_local_slm_understanding.py`, `test_slm_compact_extraction.py`, `test_slm_language_closure.py`, `test_slm_finetuned_runtime.py`, `test_slm_math_evaluator_v2.py` (`56`), `test_source_gate_handoff_boundaries.py` (`8`), `test_scoped_local_routing_policy.py` (`4`)
   - Result: **`91 passed, 1 warning in 44.03s`** (`exit_code = 0`).
2. **Full Clean-Tree Backend Test Suite (Executed on Commit `6ca84e5367f7dd2e21f58978ef8d4c196c7959cb`):**
   - Command: `pytest -c backend/pytest.ini backend/tests -q` (`ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`)
   - Result: **`15,026 passed, 7 skipped, 3 deselected, 12 xfailed, 1 warning in 702.93s`** (**`0 failed`**, `exit_code = 0`, up cleanly from `/7`'s `14,944` with `+82` new `/8` unit & contract tests).
   - Frozen candidate identity verified on `6ca84e536`: **`MATCH` (`123` files, `113a6a7cf6bbc15a...`)**.
