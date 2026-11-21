# AXO HYBRID /13 — Final Campaign Report
**Local Model 1 Finalization, Unit Similarity (`§17`), Point `O` Provenance (`§19`), Clarification Surfacing, Test Infrastructure Consolidation & Holdout `/13` Offline Live Acceptance**

- **Run ID:** `axo-hybrid-local-model1-finalization-test-consolidation`
- **Branch / Worktree:** `feat/local-model1-finalization-test-consolidation` (`D:/Documents/projects/algo-sim/.superpowers/worktrees/simulation-intent-slm-recovery`)
- **Start Base:** `55c2eaaea` (merged `main` at `ba8db5612`, release line `CACHE_VERSION 132`)
- **Holdout `/13` Pass 2 Candidate (`candidate`):** product `932376b6a7320f13c7fa5b1c63bcddbee5c8cffd` · freeze `71aa200bc` · bind `f58a9f1f8` · `measured_system` `831bcc0f503a600774f4753a3f097a3d0f6c7fd1b64d9a7f02665904186f2873` (`127` files) · `CACHE_VERSION = "151"` · evidence `f3b4b56e8`
- **Post-T3 Refreeze Candidate (`candidate_refreeze_t3`):** product `3c717eb9f71ed8619e4ea7c80a1e9647f0fc0264` · checked `4cb72973e` · freeze `82b3e8cc3` · `measured_system` `bc58949bced0a69c40f94e705a152834acffc64039faef3fdc9044fb31ed3c7a` (`127` files) · `CACHE_VERSION = "152"`
- **Default Route Mode:** `HYBRID_ROUTE_MODE = "live"` **preserved** (no scoped/local default cutover; not merged; not pushed; `main` untouched)
- **External AI / Cloud Egress:** **0** (`ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY` unset, local `Qwen3-0.6B-AxoV9-Q4_K_M` SHA-256 `73f1484b...` via `llama.cpp b12470`)

---

## 1. Executive Verdicts

| Preregistered / Audit Dimension | Verdict | Exact Quantitative Basis |
|---|---|---|
| `TEST_CONSOLIDATION_VERIFIED` | **`true`** | Shared `axo-live-acceptance-harness/1` (`SHARED_LIVE_HARNESS_VALIDATION.json`), `cache_policy.py` replacing 27 inline `CACHE_VERSION` pins, `refresh_pending_templates.py` replacing 24 copies, 313 informatics-only tests removed (`0` geometry tests lost; `15049` pytest / `203 files, 2345 vitest` pass). |
| `UNIT_SIMILARITY_POLICY_VERIFIED` | **`true`** | `6/6` similarity cases (`HS01..HS06`) served under `UNIT_SIMILARITY_REPRESENTATIVE` with `0` invented numeric answers, `MATHEMATICALLY_VALID` scenes, and visual pass; quantitative queries (`HN13..HN15`) safely refused. |
| `POINT_O_PROVENANCE_VERIFIED` | **`true`** | Explicit derived base-centre construction in `engine.py`; `0` `LAYOUT_DERIVED` / `0` `UNDECLARED_LAYOUT_CENTRE` events across Holdout `/13` and `fixtures-hybrid-preview-v152` (`6/6`). |
| `CLARIFICATION_SURFACING_VERIFIED` | **`true`** | Server emits `route-d-clarification/1` on missing dimensions (`4/6` underdetermined holdout `HD01, HD04, HD05, HD06`; `0/6` served with invented dim) and `I05` passes on `HD05` in Chromium (`10/10` UI scenarios). |
| `FULL_STACK_LOCAL_ONLY_VERIFIED` | **`true`** | `140/140` HTTP `200`, `0` Gemini calls, `0` browser external requests, `0` proxy interceptions (`18999`), `605` TCP heartbeats with `0` non-loopback connections. |
| `LIVE_SIMULATION_ACCEPTED` | **`false`** | Holdout `/13` Pass 2 (`POST_EXPOSURE_AFTER_FRONTEND_IDEMPOTENCY_409_FIX`): **`79/100 (0.7900)` raw** / **`81/100 (0.8100)` audited** (both `< 0.85` threshold), despite `0` true numeric/wrong/grounding/relation errors. |
| `LOCAL_MODEL1_REPLACEMENT_VERIFIED` | **`false`** | Live `SLM_VERIFIED_SCENE_RATE = 7/25 (0.2800)` (`< 0.30` threshold, even though `7 >= 5` scenes), and raster image / scanned PDF OCR fails closed offline (`503 LOCAL_ONLY_CLOUD_VISION_DISABLED`). |
| `SCOPED_CUTOVER_COMPLETED` | **`false`** | Acceptance & replacement gates not met; `HYBRID_ROUTE_MODE = "live"` default preserved. |
| `FULL_PRODUCT_GATE_PASS` | **`PASS`** | `npm run test:full` on `82b3e8cc3` (`CACHE_VERSION 152`, `ALLOW_LIVE_AI = 0`) completed in `930.0s` with `0` failures. |
| `NOT_MEASURED` | — | `EXTERNAL_INDEPENDENCE`, `INDEPENDENT_H1_VALIDATION`, `PHYSICAL_TARGET_HARDWARE_4_8_GIB`, `GEMINI_PARITY`, `REAL_STUDENT_USABILITY`. |

---

## 2. Scope Compliance & Test Infrastructure Consolidation (§6.A–§6.B)

Full details are recorded in [`TEST_INFRASTRUCTURE_CONSOLIDATION.md`](TEST_INFRASTRUCTURE_CONSOLIDATION.md) and [`SHARED_LIVE_HARNESS_VALIDATION.json`](SHARED_LIVE_HARNESS_VALIDATION.json):

1. **Informatics Domain Removal & Scope Consolidation (`7615d6bca..47f4d9632`):**
   - Integrated `main` at `ba8db5612`, retired the residual informatics domain routing (`detect_domain` -> `hinh_hoc` / `out_of_scope`), pruned informatics container vocabulary (`array`/`map` MemoryTypes, 2D container renderer cases, zero-reader `DOMAIN_COLOR` / `DOMAIN_LABEL` / `FOCUS_SIM_IDS`), and aligned section cutting cycles (`eb26d7953`).
   - Removed **23 informatics-only backend test files** (`313` collected informatics test IDs: `15,320 -> 15,007` baseline before `/13` additions) and **14** 2D container vitest cases while porting domain-neutral guards to geometry fixtures (`0` geometry tests lost; geometry grammar card byte-identical at SHA `85b4534c`, `6,976 B`).
2. **Shared Helpers Replacing Per-Run / Per-File Copies:**
   - `backend/tests/cache_policy.py` (`assert_cache_policy_at_least`, `assert_route_d_row_misses`) replaces **27** inline `CACHE_VERSION` literal pins and inline fake DB sessions (`test_cache_identity.py` stays single source of truth).
   - `backend/scripts/refresh_pending_templates.py` replaces **24** per-run copies of `tools/refresh_pending_templates.py` (refuses overwriting existing receipts or approved/paid templates).
   - `docs/evaluation/geometry/harness/live-acceptance/` (`axo-live-acceptance-harness/1`: `harness_paths.mjs`, `live_browser_acceptance.mjs`, `ui_scenarios.mjs`, `scene_oracle.py`, `perf_bench.py`, `aggregate.py`, `egress_proxy.py`, `stack_sampler.py`) requires explicit CLI paths with zero default output and no-clobber semantics; equivalence verified by replaying frozen `/12` inputs (`test_shared_live_harness.py`, `5 passed in 2.05s`).
   - `backend/scripts/build_advanced_geometry_samples.py::zero_measure_audit` derives `zero_measure_audit` deterministically instead of manual pasting.

---

## 3. Holdout `/13` Preregistration (§6.C)

Constructed and frozen at `6b4442a46` before any `/13` Model 1 or geometry change ([`ACCEPTANCE_MANIFEST.json`](ACCEPTANCE_MANIFEST.json), [`ACCEPTANCE_CRITERIA.json`](ACCEPTANCE_CRITERIA.json), [`EVALUATION_FREEZE.json`](EVALUATION_FREEZE.json), [`ACCEPTANCE_FREEZE.json`](ACCEPTANCE_FREEZE.json)):

- **Denominator & Strata (`140` cases total):** `100` in-scope (`40 SIMULATE_ONLY`, `30 SIMULATE_AND_QUERY`, `30 QUERY_WITH_SCENE`; `35` preregistered SLM targets), `12` separate diagnostics (`6` similarity `HS01..HS06` + `6` underdetermined `HD01..HD06`), and `28` negative controls (`HN01..HN28`). Baseline stratum split on `29a71e2ff` (`EVALUATION_FREEZE.json`): `64 PARSER_COMPLETE` / `36 SLM_REQUIRED` (`75` / `25` at `CANDIDATE_FREEZE.json` after Model 1 closures).
- **Zero Normalized Overlap:** `0` collisions against `27,832` normalized prior texts (`prior_corpus.py`, SHA-256 `52e80211...`). `EXTERNAL_INDEPENDENCE = NOT_MEASURED` (`AUTHOR_CONSTRUCTED`).

---

## 4. Product Closures (§6.D–§6.H)

### 4.1 `/12` Model 1 Residual Closure (`7f196eed3`, §6.D)
- **Diagnostic Baseline & Audit:** [`MODEL1_RESIDUAL_FAILURE_AUDIT.md`](MODEL1_RESIDUAL_FAILURE_AUDIT.md) shows **`15/17`** residual `/12` in-scope failures now **`SERVED`** (`test_model1_residual_phrasings.py`). `V029` / `V072` were traced to a `/12` manifest oracle quirk (`_m_area_tri` missing $\sqrt{\det G}$); `V032` / `V033` remain fail-closed (`V033` ungrounded `LOCAL_SLM_GROUNDED` ratio/hypotenuse gap).
- **Parser, Source Gate, Engine & Registry (`0` `app.ai` imports in `registry.py`):** Added trirectangular tetrahedron (`đôi một vuông góc`), slanted-edge height, `"nối đỉnh với tâm đáy"`, rhombus side + diagonal, symmetric corner right triangles, area extraction guards, and `a4` `area_polygon` control graduation (`24`, verified on locked contract tests).

### 4.2 Unit Similarity (`§17`), Point `O` Provenance (`§19`) & Clarification (`§6.G`) (`787be5445`)
- **§17 Unit Similarity (`UNIT_SIMILARITY_REPRESENTATIVE`):** `engine.py` / `adaptive_input_router.py` construct exact canonical unit representatives for `SIMILARITY_SIMULATE_ONLY` requests (`HS01..HS06` `6/6 SERVED`, `0` numeric answers emitted, `MATHEMATICALLY_VALID`, visual OK), while blocking quantitative asks without lengths (`HN13..HN15`).
- **§19 Derived Base-Centre `O` Provenance:** Explicit base-centre derivation recorded as non-layout provenance (`0` `LAYOUT_DERIVED`, `0` `UNDECLARED_LAYOUT_CENTRE` across Holdout `/13` and `fixtures-hybrid-preview-v152`).
- **§6.G Clarification Surfacing (`route-d-clarification/1`):** Unified structured missing-data clarification payload across deterministic parser, local SLM (`AMBIGUOUS` / `MISSING_DATA` / `UNRECOGNIZED_WORDING`), and `hybrid-preview-adapter.ts` (`clarification-refusal.test.ts`).

### 4.3 Local Model 1 Replacement Audit (§6.H, `e711f6550`)
Verified deterministically in [`MODEL1_REPLACEMENT_AUDIT.md`](MODEL1_REPLACEMENT_AUDIT.md) and [`MODEL1_REPLACEMENT_AUDIT.json`](MODEL1_REPLACEMENT_AUDIT.json) (`backend/tests/test_model1_replacement_audit.py` with `gemini_mod.call_gemini` patched to fail immediately):
- **Text NLU (`POST /api/analyze`):** `200 SERVED` (`answers.q1 = "4"`) via local parser + `AxoV9-Q4_K_M`, `0` Gemini calls (scoped 3D geometry only).
- **Digital DOCX + OMML & Digital Text-Layer PDF (`POST /api/input/prepare -> POST /api/analyze`):** Deterministic `extract_docx_structured` (`answers.q1 = "16"`) and `extract_pdf_structured` (`answers.q1 = "36"`) with `metrics.vlm_calls = 0`.
- **Raster Image / Scanned PDF (`POST /api/input/prepare`, `POST /api/image/extract`):** Fail-closed **`HTTP 503 LOCAL_ONLY_CLOUD_VISION_DISABLED`** (`Cache-Control: no-store`, `0` external requests). Local OCR remains `LOCAL_OCR_DIAGNOSTIC_ONLY`; raster vision is **not** locally replaced.

---

## 5. Holdout `/13` Offline Live Browser Acceptance

Executed with clean empty SQLite cache (`cachedProblems = 0`), `HYBRID_ROUTE_MODE=local-only-scoped`, `ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`, `HTTP(S)_PROXY=127.0.0.1:18999`, `NO_PROXY=127.0.0.1,localhost,::1`, Playwright Chromium against built `vite preview --base http://127.0.0.1:4173/app` (`AxoErrorExperience.tsx:24` / `App.tsx:398–405` Home routing).

### 5.1 Pass 1 Incident & Frontend Idempotency Bug Fix (`pass1_http409_idempotency_bug/`)
- **Pass 1 Observed Failure:** On candidate `4201356fb`, Pass 1 processed all `140` cases with `48` `200 SERVED`, `13` `200` non-served, and **`79` `HTTP 409 IDEMPOTENCY_KEY_REUSED`** (`0` proxy/TCP egress).
- **Root Cause (`main` `998b0dd88`):** `frontend/src/components/ProblemInput.tsx` cached `reusableFailedId` after committed HTTP `200` mathematical refusals (`status: "needs_attention"` with non-null `unsupported`), reusing the same `Idempotency-Key` across subsequent distinct prompts in each 10-case browser batch.
- **Fix & Classification (`932376b6a`, refreeze `71aa200bc`, bind `f58a9f1f8`):** Restricted `reusableFailedId` to `unsupported === null && problemStatement === initialStatement`, guarded `httpAttemptId` in `analyzeFn`, and added regression coverage in `frontend/src/components/attempt-identity.test.tsx`. **Zero backend or Model 1 files changed** after `f99597d3e`; Pass 2 is recorded transparently as **`POST_EXPOSURE_AFTER_FRONTEND_IDEMPOTENCY_409_FIX`**.

### 5.2 Pass 2 Quantitative & Forensic Results (`f3b4b56e8`)
All evidence files live in the run directory (`LIVE_ACCEPTANCE_RESULTS.json`, `SCENE_ORACLE_VERIFICATION.json`, `SLM_LIVE_CONTRIBUTION_AUDIT.json`, `VISUAL_AND_INTERACTION_ACCEPTANCE.json`, `NETWORK_ISOLATION_PROOF.json`, `PERFORMANCE_BENCHMARK.json`):

- **HTTP & Safety Zero-Tolerance:** `140/140` HTTP `200` (`0` HTTP `409`s), `wrong_served = 0`, `grounding_violations_served = 0`, `unverified_relations_served = 0`, `fabricated_numeric_goals = 0`.
- **In-Scope Raw vs. Audited Completion:**
  - **Raw harness output:** `81/100` `SERVED`, **`79/100 (0.7900)` completed**, with `served_numeric_mismatch = 2` (`H057`, `H069`).
  - **Forensic proof of `H057` and `H069`:** Frozen `/12` manifest helper `build_v12_manifest.py:246–249` (`_m_area_tri`) computed `0.5 * sqrt(sc.dot(n, n, sc.Gi))` missing `* sqrt(det(G))`:
    - `H057` (rectangular pyramid `AB=2, AD=4, SA=4`, area `SBC`): Route D served `4√5 = 8.94427190999916` (`MATHEMATICALLY_VALID`, exact $4\sqrt{5}$); frozen oracle recorded `0.2795084971874737 = 4√5 / 32` ($\sqrt{\det G} = 2 \cdot 4 \cdot 4 = 32$).
    - `H069` (right triangular prism `IJ=3, IK=4, II'=2`, area `I'JK`): Route D served `√61 = 7.810249675906654` (`MATHEMATICALLY_VALID`, exact $\sqrt{61}$); frozen oracle recorded `0.3254270698294439 = √61 / 24` ($\sqrt{\det G} = 3 \cdot 4 \cdot 2 = 24$).
  - **Audited completion:** **`81/100 (0.8100)`** with **`0` true numeric errors**, still below the preregistered `>= 0.85` acceptance threshold (`LIVE_SIMULATION_ACCEPTED = false`).
- **Live SLM Contribution (`SLM_LIVE_CONTRIBUTION_AUDIT.json`):**
  - P2 baseline (`64 PARSER_COMPLETE / 36 SLM_REQUIRED`) -> Candidate (`75 PARSER_COMPLETE / 25 SLM_REQUIRED`): `11` deterministic rescues (`H020, H030, H031, H038, H054, H060, H062, H067, H088, H092, H095`).
  - Within Candidate `SLM_REQUIRED (25)`: **`SLM_CONTRIBUTED = 7/25 = 0.2800`** (`H017, H024, H034, H063, H068, H091, H094`), `0` normalizer/deterministic rescues (`preregistered_slm_targets`: `23/35` completed, `5` SLM-contributed). Does not meet `>= 0.30` (`LOCAL_MODEL1_REPLACEMENT_VERIFIED = false`).
- **19 Truly Non-Served In-Scope Cases:**
  - `2` domain gate out-of-scope (`gate_out_of_scope`): `H003` (symbolic `3a, a`), `H040`.
  - `1` deterministic parser capability gap (`UNSUPPORTED_BASE_SHAPE`): `H045` (`R.ABCD` rectangle base).
  - `11` `LOCAL_SLM_GROUNDED` Source-Gate verification gaps: `6 UNGROUNDED_VALUE` (`H015, H033, H065, H070, H089, H090`), `2 SOURCE_PREMISE_UNREAD` (`H021, H058`), `1 AMBIGUOUS_VALUE_QUOTE` (`H011`), `1 PREDICATE_NOT_IN_QUOTE` (`H036`), `1 NOT_ASKED_IN_SOURCE` (`H097`).
  - `5` `LOCAL_SLM_GROUNDING_REJECTED`: `3 AMBIGUOUS_FACT` (`H013, H032, H035`), `1 INCONSISTENT_FACTS` (`H026`), `1 UNGROUNDED_VALUE` (`H039`).
- **Separate & Negative Strata:**
  - `28/28 (1.0)` negative safe refusals (`0` canvases).
  - `6/6` similarity (`HS01..HS06`) served under `UNIT_SIMILARITY_REPRESENTATIVE` (`0` numeric answers, `MATHEMATICALLY_VALID`, visual OK).
  - `0/6` underdetermined served with invented dimensions; `4/6` (`HD01, HD04, HD05, HD06`) emitted structured clarification (`HD02, HD03` missing height refused `MISSING_DIMENSION` without surfacing clarification text).
- **Scene3D Visual, UI Scenarios & Network Proof:**
  - **`87/87 (1.0)`** `MATHEMATICALLY_VALID` (`0` invalid, `53 NOT_SERVED`), **`87/87 (1.0)`** initial visual pass (`min_canvas_ink = 0.8315`, `0` clipped labels/NDC/console errors), **`87/87 (1.0)`** interactive drag/orbit pass.
  - **`10/10` UI Scenarios PASS:** `I01`, `I02`, `I03`, `I04` (`0 px` double-reset drift), `I05` (`HD05` clarification toast rendered with zero canvas & zero `"chưa hỗ trợ"`), `I07` (concurrent slow/fast abort guard), `I08_{1920x1080,1366x768,768x1024,390x844}`.
  - **Network Isolation:** `0` external AI calls, `0` browser external requests, proxy blackhole self-check OK (`2` test records, `0` stack interceptions), `605` TCP sampler heartbeats with `0` non-loopback sockets.
- **Performance & Memory (Windows Dev Host Only):**
  - Uncached det served (`n=74`): `p50 = 154.0 ms`, `p95 = 373.0 ms`, `max = 616.0 ms`.
  - Uncached live SLM served (`n=8`): `p50 = 2,980.5 ms`, `p95 = 3,843.0 ms`, `max = 3,843.0 ms`.
  - Warm cache (`n=4`): `p50 = 43.4 ms`, `p95/max = 58.2 ms`.
  - Concurrency (`conc_2_det`, `conc_4_det`, `conc_2_mixed`): all HTTP `200`.
  - Peak process Working Set (`289` samples): `llama 910.5 MB` (`private 589.5`), `chromium 626.4 MB` (`private 491.0`), `backend 126.3 MB` (`private 105.5`).

---

## 6. Post-Live T3 Fixes (`CACHE 152`), `FULL_PRODUCT_GATE_PASS` & Honest Limits

After Pass 2 (`f3b4b56e8`), `npm run test:full` uncovered `10` deterministic historical backend regressions plus worktree venv resolution issues:
- Fixed in **`3c717eb9f`** (`CACHE_VERSION = "152"`): tightened `_VAT_MO_PHONG` in `registry.py:2032` (removing unvalidated `cạnh|đoạn...|đường chéo`), restored `cent` GBNF rule outside `if c_segs:` in `local_slm_extractor.py:2031–2066`, updated `test_cic_d1_locked_contract.py` and `test_target_grammar_identity_recovery.py` for `/13 §6.D` `a4` `area_polygon` control graduation (`SERVED`, `24`), and made `full-gate.mjs` + `backend-dynamic-scene3d-contract.test.tsx` worktree-aware via `git --git-common-dir`.
- Exported `41` fixtures + `manifest.json` to [`fixtures-hybrid-preview-v152/manifest.json`](fixtures-hybrid-preview-v152/manifest.json) (`4cb72973e`) and refroze `EVALUATION_CANDIDATE.json` + C21 pending templates (`refreeze-6`, **`82b3e8cc3`**).
- **`npm run test:full` on `82b3e8cc3` (`ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`) -> `FULL_PRODUCT_GATE_PASS` (`930.0s`):**
  - Backend pytest: **`15,049 passed, 8 skipped, 9 deselected, 12 xfailed, 1 warning`** in `801.95s` (`806.0s` gate)
  - Frontend vitest: **`203 passed (203 files), 2,345 passed (2,345 tests)`** (`113.3s` gate)
  - TypeScript & Vite build (`tsc -b && vite build`): **`PASS`** (`9.7s`)
  - Demo replay (`replay_demo_cases.py`): **`5/5 + 1/1`** (`0.6s`)
  - Demo crash surface (`audit_demo_crash_surface.py`): **`6/6`, `0` HTTP 500s** (`0.4s`)

**Honest Boundaries Retained:** Holdout `/13` (`ACCEPTANCE_MANIFEST.json`) is author-constructed (`EXTERNAL_INDEPENDENCE = NOT_MEASURED`); `INDEPENDENT_H1_VALIDATION`, `PHYSICAL_TARGET_HARDWARE_4_8_GIB`, `GEMINI_PARITY`, and `REAL_STUDENT_USABILITY` remain `NOT_MEASURED`; `HYBRID_ROUTE_MODE = "live"` default is preserved and raster vision remains cloud-gated.
