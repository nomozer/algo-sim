# AXO HYBRID /16 — Semantic Grounding Integrity, SLM Capability Recovery & Final Text-Scope Validation (`FINAL_MASTER_REPORT`)

**Date:** 2026-11-21 · **Run ID:** `semantic-grounding-slm-recovery` · **Branch:** `feat/semantic-grounding-slm-recovery` (base `/15`: `c4ae9dd1f`)

> **Text-only local validation verdict (Candidate 157, `CACHE_VERSION = 157`):** **`COMPOSITE_LIVE_TEXT_ACCEPTED = true`**, **`FULL_PRODUCT_GATE_PASS = true`**, **`LOCAL_TEXT_MODEL1_VERIFIED = true`**, **`LOCAL_VISION_REPLACEMENT_VERIFIED = false`** (OCR/Vision postponed by owner), **`FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED = false`**, **`MAIN_MERGE_READY = false`**, **`MAIN_MERGE_COMPLETED = false`**, **`REMOTE_PUSH_COMPLETED = false`**, **`AUTHORITATIVE_DETACHED_COMPLIANCE = NOT_VERIFIED`**, **`EXTERNAL_INDEPENDENCE = NOT_MEASURED`**. Default runtime route stays **`HYBRID_ROUTE_MODE = "live"`** (`ALLOW_LIVE_AI = 0` applied only inside evaluation harness).

---

## 1. Candidate Identity & Architectural Integrity

| Field | Value |
|---|---|
| Product commit (`CACHE_VERSION 157`) | `4c1b94b61cdd8b1747059829a9d487b1749e1383` (`4c1b94b61`) |
| Evaluation candidate freeze commit | `39c95599e9ddc2efc7cc3455ae2505384af63e21` |
| Detached `Full T3` HEAD | `d27b78de5` |
| Detached `Holdout-6` + `SLM-Independent-3` HEAD | `b28783e31` (`0` product changes vs `4c1b94b61`) |
| Measured system tree SHA-256 (`127` files) | `3152f3829fbe4744baa298b0ee147648cd1cb666103baabcb1497cb9ffb525d5` |
| Cache & route policy | `CACHE_VERSION = "157"` · `ROUTE_D_CACHE_POLICY = "157:route-d"` |
| Semantic environment hash | `f9df4bf0c8bd458a278d2692567fa3e096340ae37ff5493730dff4067c0f5e19` |
| Component versions | `local-geometry-parser/3` · `local-slm-extractor/6` · `slm-grounding-validator/6` · `axo-live-acceptance-harness/1` |
| Local SLM (`system_prompt_modified = false`) | `qwen3-0.6b-axo-v9-q4_k_m` (`Qwen3-0.6B-AxoV9-Q4_K_M`, GGUF SHA-256 `73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35`) + `llama.cpp b12470` |
| Default `HYBRID_ROUTE_MODE` | `"live"` preserved in product code |

**Worktree disclosure:** All evaluations executed on clean trees at detached HEADs (`d27b78de5` for `Full T3`, `b28783e31` for `Holdout-6` & `SLM-Independent-3`) inside the shared development worktree (not a freshly branched isolated authoritative worktree); therefore **`AUTHORITATIVE_DETACHED_COMPLIANCE = NOT_VERIFIED`**. All frozen `/5`–`/15` runs, `docs/evaluation/geometry/harness/live-acceptance/**`, and `backend/experimental/construction_planner/**` have `0` byte diff vs `c4ae9dd1f`.

---

## 2. `/15` Baseline Preservation & Verdict Reconciliation

- Frozen `/15` artifacts in [`grounded-geometry-language-recovery/`](../grounded-geometry-language-recovery/report.md) are **unmodified** (`0` diff vs `c4ae9dd1f`).
- Registered `/15` baseline preserved untouched: **`REGISTERED_SLM_SCORE_V15 = "5/38 (0.1316)"`**, **`SLM_GATE_V15 = "FAIL"`**.
- [`VERDICT_RECONCILIATION_V15.json`](VERDICT_RECONCILIATION_V15.json) (`sha256: 06b19f33406ea27aadc8e330883d5c7b2eeb222e8e86ac6e638ce12d8923a0ab`) audits why `/15`'s narrative report recorded `LIVE_SIMULATION_ACCEPTED = true` while its [`run.json`](../grounded-geometry-language-recovery/run.json) emitted `false` (caused by `summarize_c154.py`) without altering `/15` files.

---

## 3. Two-Layer Semantic Rewrite Safety & Language Gap Recovery

### 3.1 Semantic Rewrite Safety Audit (`SEMANTIC_REWRITE_SAFETY_AUDIT.json`)
- Schema `axo-semantic-rewrite-safety-audit/1` (`sha256: be8d2b97a2a4c73d718bc665ad311e2f8344ed694ce968794c445df47ace2b4`), **`SEMANTIC_REWRITE_SAFETY_VERIFIED = true`**.
- Audited **`94`** parser/rewrite rules across 2 layers: **`5 SAFE_EQUIVALENT`**, **`89 GUARDED_EQUIVALENT`**, **`0 RESTRICTED/REMOVED`**, covered by `110` verification tests including `13` paired metamorphic equivalence/non-equivalence tests.
- Hardened Layer 2 `Source Gate` checks in `backend/app/simulation/geometry_functions/registry.py`:
  1. Removed `|đừng|chớ` from `_KHONG_KHANG_DINH` so imperative negated instructions refuse rather than silently stripping negation.
  2. Scoped `liệu` in `_HOI_QUAN_HE` (`liệu(?![^,;:?]*\?)`) so relation interrogatives preserve clause boundaries.
  3. Checked `doc_khang_dinh_loai_hinh` `ambiguous_base` -> `AMBIGUOUS_REFERENCE` prior to `SOURCE_OBJECT_MISMATCH` in `_kiem_mat_chung`.
  4. Moved `"trong không gian,"` lead strip from `_GIAN_DAN` into `_kiem_vung_tien_de` so Source Gate spans keep literal premise grounding.
- Verified across 9 targeted pytest files (`554 passed, 0 failed` in `178.70s`) with `0` `app.ai` imports in `engine.py` or `registry.py`.

### 3.2 AxoV9 Root-Cause Ablation (`SLM_ROOT_CAUSE_ABLATION.json`) & Gap Recovery (`LANGUAGE_GAP_RECOVERY.json`)
- Evaluated 5 ablation arms (`9` positive diagnostic cases `A01, A02, A03, A05, B18, E02, G08, M05, M06` + `4` negatives `N01, N02, N03, N10`) (`sha256: 9f15330eafbd5ae5c486db58912266d4d8566db306aa4d188a0c8f524199af3e`):

| Arm | Positive Served | Positive Lowered | Negative Safe |
|---|---:|---:|---:|
| `A_baseline` | 0 | 1 | 4 |
| `B_clause_split` | 1 | 7 | 4 |
| `C_sim_goal_carrier` | 1 | 2 | 4 |
| `D_prompt_synonym` | 0 | 1 | 4 |
| `E_combined` | 1 | 7 | 4 |

- **Decision:** **`RETAIN_AXOV9_NO_FINETUNE_NEEDED`** — multi-clause splitting and simulation/language-gap normalization recover 7/9 lowerings without weight updates or system prompt edits.
- [`LANGUAGE_GAP_RECOVERY.json`](LANGUAGE_GAP_RECOVERY.json) (`sha256: 7032d919892b55ee5690e68c30469d411858df4814c3936b31a4868831960838`) closes diagnostic gaps on `B18, E02, G08, M06, Family A..M05` (`9/9` positive + `4/4` negative across router and isolated `AxoV9`) while keeping registered denominators fixed.

---

## 4. Disclosed Prior Candidate / Holdout Failures (Zero Score Transfer)

### 4.1 Candidate 156 (`c3e944d7f`, `CACHE_VERSION 156`) on `Holdout-4` & `Full T3`
- Disclosed in [`CANDIDATE_156_LIVE_TEXT_ACCEPTANCE_RESULTS.json`](holdout-4/CANDIDATE_156_LIVE_TEXT_ACCEPTANCE_RESULTS.json), [`CANDIDATE_156_SLM_CAPABILITY_AUDIT.json`](holdout-4/CANDIDATE_156_SLM_CAPABILITY_AUDIT.json), and [`CANDIDATE_156_FULL_T3_RECEIPT.json`](holdout-4/CANDIDATE_156_FULL_T3_RECEIPT.json):
  - `Holdout-4` live acceptance (`64/72`, `22/30` SLM fallback, `SLM-Ind-1 25/30`, `26/26` neg safe) failed UI scenario **`I05`** (`ui_scenarios = 9/10`; `NEG01` showed generic `"Đề bài chưa được hỗ trợ"` instead of conditional clarification).
  - `Full T3` on `ee013b8fc` **FAILED (`FULL_PRODUCT_GATE_FAIL`, exit `1`)** with **`15,157 passed, 4 failed`** in backend pytest (`1055.17s`): `test_question_mark_clause_mutant_is_killed`, `test_each_grammar_extension_is_load_bearing[no_space_lead]`, `test_blocker_r2_1_multi_solid_unlabelled_base_shape_binds_local_prose_solid_and_reapexed_tetrahedron`, and `test_a_negated_derived_pyramid_request_is_refused[nhưng đừng dựng]`. No Candidate 156 score was carried forward.

### 4.2 Candidate 157 on `Holdout-5` (`build_holdout.py` Oracle Bug)
- Disclosed in [`CANDIDATE_157_HOLDOUT5_ORACLE_BUG_RECEIPT.json`](holdout-5/CANDIDATE_157_HOLDOUT5_ORACLE_BUG_RECEIPT.json) (`sha256: ebb917ce7a28a05081712f4b82b3cd417bf56e071f99be0f7ff1510943dbcd6a`):
  - `Holdout-5` observed `63/72 (0.875)`, `24/30 (0.80)` SLM fallback, `10/10` UI scenarios, `26/26` neg safe, `SLM-Ind-2 24/30 (0.80)` (`gate_pass = true`), with `P04, P05, S07` marked `MATHEMATICALLY_INVALID` solely because `holdout-5/build_holdout.py` called `tet()` (`L[0]`) instead of `tri_pyr_rect()` (`L[1]`). Direct check confirmed all 5 true relations and exact volumes held on Candidate 157's served scenes. Per §17, `holdout-5` was **not altered** and was retired untouched as exposed diagnostic evidence.

---

## 5. Authoritative Verification on Candidate 157

### 5.1 Full Product Gate (`Full T3`, `FULL_T3_RECEIPT.json`)
- Executed `cd frontend && npm run test:full` on clean detached HEAD `d27b78de5` (`ALLOW_LIVE_AI = 0`, `duration = 1411.3 s`, exit **`0`**, log SHA-256 `4ec0202412e38c95f1fc7b7f5fb7f88646a926d4ee1ffb1cc989232a107cfbbe`):
  - **`backend_pytest`**: **`15,162 passed, 0 failed`**, `8 skipped`, `9 deselected`, `12 xfailed`, `1 warning` (`1276.04 s` pytest / `1280.6 s` wrapper).
  - **`frontend_vitest`**: **`203 passed (203)` files**, **`2,345 passed (2,345)` tests**, `0 failed` (`119.14 s` vitest / `121.5 s` wrapper).
  - **`typecheck_build`**: **PASS** (`vite 5.11 s` / `8.0 s` wrapper).
  - **`demo_replay`**: **`5/5`** + reduced chain **`1/1`** (`0.7 s`).
  - **`demo_crash_surface`**: **`6/6`** (`0` unexpected 500s, `0.4 s`).
  - **Verdict:** **`FULL_PRODUCT_GATE_PASS`**.

### 5.2 Unexposed `Holdout-6` + `SLM-Independent-3` (`b28783e31`, `0` product changes)
- [`holdout-6/`](holdout-6/ACCEPTANCE_MANIFEST.json) constructed with automated `_cross_check_prose()` segment-length and perpendicularity assertions; verified **`0` containment matches** and **`0` cross-set overlaps** against **`29,423`** normalized prior strings (including `/5`–`/15`, `Holdout-4/5`, and local training corpus). **`EXTERNAL_INDEPENDENCE = NOT_MEASURED`** (author-generated prose, not third-party unseen external exam acquisition).
- [`ACCEPTANCE_MANIFEST.json`](holdout-6/ACCEPTANCE_MANIFEST.json) (`sha256: f5423a44d64e34984bc3580e4c34c9d1f8529b6fd070d6d705fda2726235a0f2`): `72` positive in-scope (`41` `PARSER_COMPLETE` + `31` `SLM_REQUIRED`, `12/12` preregistered targets) + `26` negative = `98` total.
- [`SLM_INDEPENDENT_MANIFEST.json`](holdout-6/SLM_INDEPENDENT_MANIFEST.json) (`sha256: eca2456dfab2f245d3b54506d3686b9d7834bd0e21e0bda1ba62fdbb7e393f5d`): `30` positive + `10` negative = `40` total.
- Cold run (`route_mode = local-only-scoped`, `ALLOW_LIVE_AI = 0`, `CACHE_VERSION = 157`, `db_cached = 0`, `identity_mismatches = []`):

| Metric (`§16`) | Score | Threshold / Policy | Outcome |
|---|---:|---|---|
| **`END_TO_END_SYSTEM_SCORE`** (`Holdout-6`) | **`64/72 (0.8889)`** | `>= 0.85` & `>= 62` (`64/64` served valid & browser-verified) | **PASS** |
| **`CANDIDATE_FALLBACK_SCORE`** (`Holdout-6`) | **`23/31 (0.7419)`** | `>= 0.50`, min sample `8`, min live scenes `5` (`11/12` preregistered `L01..L05, L07..L12` via `LOCAL_SLM_GROUNDED`) | **PASS** |
| **`INDEPENDENT_SLM_SCORE`** (`SLM-Independent-3`) | **`21/30 (0.7000)`** | `allow_parser_reconcile = false`, `>= 0.60` & `>= 18`; `ext_corr = 0.7333`, `ground_corr = 0.7333`, `neg_safe = 10/10`, `0` false/invalid | **PASS** |
| **`LEGACY_BASELINE_STRATUM_SCORE`** | **`23/31 (0.7419)`** | `completed_deterministically_on_candidate = 0` | **Recorded** |

- **Safety, UI & Offline Network (`Holdout-6`, [`LIVE_TEXT_ACCEPTANCE_RESULTS.json`](LIVE_TEXT_ACCEPTANCE_RESULTS.json)):**
  - Positive oracle audit (`scene_oracle.py`): `MATHEMATICALLY_VALID = 64`, `MATHEMATICALLY_INVALID = 0`, `VALIDATION_ERROR = 0`, `NOT_SERVED = 34` (`8` positive fail-closed + `26` negatives).
  - Negative safety: **`26/26` safely refused**, `wrong_served = 0`, `grounding_violations_served = 0`, `unverified_relations_served = 0`, `fabricated_numeric_goals = 0`, `served_numeric_mismatch = 0`, `attachment_provenance_not_present = 0`.
  - Real Chromium Playwright scenarios: **`10/10` passed** (`I01, I02, I03, I04, I05 [NEG01 conditional toast], I07, I08_1920x1080, I08_1366x768, I08_768x1024, I08_390x844`; `0` console errors; `0` external browser requests).
  - Network monitor: `external_ai_calls_reported = 0`, `browser_external_requests = 0`, `proxy_intercepted = 0`, `tcp_heartbeats = 586`, `tcp_non_loopback_records = 0` (`physical_internet_disconnect = NOT_MEASURED`).

---

## 6. Residual Failures & Host Performance

### 6.1 Fail-Closed Residuals
- **`Holdout-6` 8 unserved positive cases** (all cleanly refused fail-closed, `0` wrong scenes): `C05` (`UNGROUNDED_VALUE`), `C07` (`SOURCE_OBJECT_MISMATCH`), `C10` (`AMBIGUOUS_FACT`), `R06` (`SOURCE_OBJECT_MISMATCH`), `P08` (`QUESTION_CONTEXT_UNSUPPORTED`), `S02` (`AMBIGUOUS_FACT`), `Q01b` (`OUT_OF_SCOPE`), `L06` (`AMBIGUOUS_FACT`).
- **`SLM-Independent-3` (`SLM_CAPABILITY_AUDIT.json`) 9 unserved positive cases** (`0` false assertions/invalid relations): `I01, I02, I06, I07, I10, I12, I13, I14, I27`.

### 6.2 Windows Dev Host Latency & Memory (No Cross-Hardware Claims)
- Uncached live deterministic served (`n = 41`): min `115.0 ms`, **`p50 = 185.0 ms`**, `p95 = 384.0 ms`, max `791.0 ms`.
- Uncached live SLM-contributed served (`n = 23`): min `2146.0 ms`, **`p50 = 5414.0 ms`**, `p95 = 12607.0 ms`, max `27226.0 ms`.
- Refused valid (`n = 8`): `p50 = 5163.0 ms` (`p95 = 11280.0 ms`); refused negative (`n = 26`): `p50 = 1389.0 ms` (`p95 = 3407.0 ms`).
- Warm cache hit (`n = 4`): **`p50 = 63.8 ms`** (`p95 = 72.9 ms`).
- Concurrency (`all_200 = true`): `conc_2_deterministic` (`109.3 ms`), `conc_4_deterministic` (`240.6 ms`), `conc_2_mixed_slm_and_det` (`121.6 ms`).
- Stack peak RSS (`277` samples): `llama` (`max_pid 1`, **`905.4 MB`** WS / `590.1 MB` private), `chromium` (`max_pid 16`, **`2366.1 MB`** WS / `1326.8 MB` private), `backend` (`max_pid 2`, **`124.6 MB`** WS / `104.2 MB` private).

---

## 7. Mandatory Final Verdict Table (§24)

| Flag / Verdict | Value | Evidence |
|---|---|---|
| `REGISTERED_SLM_SCORE_V15` | `"5/38 (0.1316)"` (`SLM_GATE_V15 = "FAIL"`) | Preserved unmodified (`/15` baseline) |
| `SEMANTIC_REWRITE_SAFETY_VERIFIED` | `true` | [`SEMANTIC_REWRITE_SAFETY_AUDIT.json`](SEMANTIC_REWRITE_SAFETY_AUDIT.json) |
| `SOURCE_GROUNDING_VERIFIED` | `true` | `0` grounding violations served on `Holdout-6` + `SLM-Independent-3` |
| `SYSTEM_TEXT_COMPLETION_THRESHOLD_MET` | `true` | `64/72 (0.8889 >= 0.85)` |
| `SLM_FALLBACK_GATE_MET` | `true` | `23/31 (0.7419 >= 0.50)`, `n_routed = 31 >= 8`, `n_served = 23 >= 5` |
| `SLM_INDEPENDENT_CAPABILITY_GATE_MET` | `true` | [`SLM_CAPABILITY_AUDIT.json`](SLM_CAPABILITY_AUDIT.json) (`21/30 = 0.7000`, `10/10` neg safe) |
| `COMPOSITE_LIVE_TEXT_ACCEPTED` | `true` | [`LIVE_TEXT_ACCEPTANCE_RESULTS.json`](LIVE_TEXT_ACCEPTANCE_RESULTS.json) |
| `LOCAL_TEXT_MODEL1_VERIFIED` | `true` | Composite text acceptance + SLM independent gate + Full T3 PASS |
| `LOCAL_VISION_REPLACEMENT_VERIFIED` | `false` | Text-only campaign; OCR/Vision deferred by owner |
| `FULL_GEMINI_ROLE_REPLACEMENT_VERIFIED` | `false` | Vision/image Gemini replacement not verified; default mode remains `"live"` |
| `FULL_PRODUCT_GATE_PASS` | `true` | [`FULL_T3_RECEIPT.json`](FULL_T3_RECEIPT.json) (`15,162` pytest, `2,345` vitest) |
| `MAIN_MERGE_READY` | `false` | Detached worktree non-compliance + OCR/Vision deferred + explicit owner approval required |
| `MAIN_MERGE_COMPLETED` | `false` | Not merged into `main` |
| `REMOTE_PUSH_COMPLETED` | `false` | Not pushed to any remote |
| `AUTHORITATIVE_DETACHED_COMPLIANCE` | `"NOT_VERIFIED"` | Shared worktree switched to detached HEADs (`d27b78de5`, `b28783e31`) |
| `EXTERNAL_INDEPENDENCE` | `"NOT_MEASURED"` | Zero prior string collisions (`29,423` strings), author-authored synthetic holdout |
