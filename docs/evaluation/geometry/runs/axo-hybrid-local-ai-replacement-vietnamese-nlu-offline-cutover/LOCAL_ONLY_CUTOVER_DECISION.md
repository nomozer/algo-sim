# AXO HYBRID /9 — Phase P10 Local-Only Cutover & Release Readiness Decision (`Gate G10`)

> **Campaign:** `AXO HYBRID /9 — Local AI Replacement, Vietnamese NLU Generalization & Offline Production Cutover`  
> **Run ID:** `axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover`  
> **Product Commit:** `f285fcec1afc097084e3fab154f583f01620cab7` (`measured_system = a7a6bc4157d02018d5a67e5ee408469f22795385f920444eafc39d4772fa8330`, `123` files, `CACHE_VERSION = "145"`)  
> **Default Production Route State Preserved:** `HYBRID_ROUTE_MODE = "live"` (until explicit owner cutover)

---

## 1. Executive Verdict Summary (Goal A vs. Goal B Separated)

Per §26 and §37 (`Gate G10`), technical readiness on verified backend infrastructure is separated cleanly from owner-gated production default cutover, blocked ownership surfaces, and unmeasured hardware/external domains:

| Axis | Verdict / Status | Precise Technical Meaning & Evidence Basis |
|---|---|---|
| **Goal A (`LOCAL_ONLY_OPERATIONAL`) — Opt-In Route (`HYBRID_ROUTE_MODE=local-only-scoped`, `offline-lab`)** | **`LOCAL_ONLY_SCOPED_RELEASE_READY` (Backend Opt-In Technical Readiness)** | Genuine keyless execution via `/api/analyze`, `/api/input/prepare` (text, `.docx`, clean PDF), `/api/health` without `GEMINI_API_KEY`; `0` wrong-served across all tested corpora; `0` external AI calls; `0` silent cloud fallbacks; mixed warm uncached host `p95 = 4,109.98 ms <= 5,000 ms`; peak WS `973.28 MiB`; atomic model activation/rollback (`--rollback v7`) verified. |
| **Goal A — Default Cutover (`live` -> `local-only-scoped`) & Full-Stack Keyless UI (`Gate G10`)** | **`BLOCKED_OWNERSHIP`** | Flipping default `HYBRID_ROUTE_MODE` off `"live"`, wiring `frontend/src/` keyless `/api/health` readiness UX, and optional Source Gate conversational lead-ins in `registry.py` require owner sign-off and cross-worktree integration (`axo-geometry-library`). All three verified `git apply --check` patches live in [`handoff/`](./handoff/). |
| **Goal B (`GEMINI_CAPABILITY_REPLACEMENT`) — Full Equivalent General Cutover (`local-only-general`)** | **`NOT_EQUIVALENT_FULL_REPLACEMENT` / `BLOCKED_OWNERSHIP` + `NOT_MEASURED`** | Text-only 0.6B SLM covers scoped Vietnamese polyhedral geometry (`32/42 = 76.19%` `C60`, `94/105 = 89.52%` `SLM_V9_UNSEEN_150`, `12/12` `EXTERNAL17`) rather than arbitrary open-domain multimodal problems: cloud vision OCR is explicitly blocked (`503 LOCAL_ONLY_CLOUD_VISION_DISABLED`), `9/42` `C60` items exceed upstream `TypedFactNext /2` / `Bridge /2` / `Registry` scope, `local-only-general` fails closed (`503 LOCAL_ONLY_GENERAL_NOT_APPROVED` unless `AXO_ALLOW_GENERAL_LOCAL_CUTOVER=1`), and `GEMINI_PARITY`, `EXTERNAL_INDEPENDENCE`, `PHYSICAL_TARGET_HARDWARE`, `INDEPENDENT_H1_VALIDATION`, and `REAL_STUDENT_USABILITY` remain `NOT_MEASURED`. |

---

## 2. Level 1 / Level 2 / Level 3 Compliance Audit (§26)

### Level 1 — `LOCAL_ONLY_EXPERIMENTAL`
- **Status:** **MET**
- Local-only execution (`offline-lab`, `local-only-scoped`, `local-shadow`, gated `local-only-general`) runs cleanly with `external_ai_calls = 0`, `gemini_invocations = 0`, `silent_cloud_fallbacks = 0`. Source Gate, Exact Kernel `/24`, fault recovery (`16/16`), capability matrix (`SLM_V9_CAPABILITY_MATRIX.json`), and regressions pass without error.

### Level 2 — `LOCAL_ONLY_SCOPED_RELEASE_READY`
- **Status:** **TECHNICAL CRITERIA MET ON BACKEND OPT-IN ROUTE (`RELEASE DEFAULT CUTOVER = BLOCKED_OWNERSHIP`)**
  - **Keyless Operation:** Verified via `/api/health` (`hasKey=False`, `localOnlyMode=True`, `localSlmReady=True`, `aiAvailable=True`), `/api/analyze` (`SERVED`), and `/api/input/prepare` (`.docx` `vlm_calls=0`).
  - **Scoped Coverage & Safety:** `SLM_V9_UNSEEN_150` single-shot `94/105` positives (`89.52%`, Wilson 95% CI `[0.8221, 0.9405]`: `54` fast-path + `40` SLM), `45/45` negatives safe-refused (`100.00%`, CI `[0.9213, 1.0000]`), `0/150` wrong-served; `C60_BLIND_NLU` `32/42` (`76.19%`, `32/33 = 96.97%` of `Arm B Gold Canon` solvable ceiling, `0` wrong-served); `EXTERNAL17` `12/12` + `5/5`, `0` wrong-served. Notice `0` observed wrong-served on tested suites demonstrates strong fail-closed gating within tested distributions, not zero mathematical probability on arbitrary real-world student phrasing.
  - **Fail-Closed Unsupported Handling:** Spheres/cones/cylinders/Oxyz/calculus/2D, missing/contradictory premises, conditional clauses, typos, prompt injections, and unverified photos (`503 LOCAL_ONLY_CLOUD_VISION_DISABLED`) all refuse transparently.
  - **Rollback & Provisioning:** `provision_local_slm.py --rollback v7` (`AxoV7` SHA-256 `36e784d1…`) and `--rollback orig` (`Qwen3-0.6B-Q4_K_M` SHA-256 `ac2d9771…`) alongside Git rollback cleanly restore prior baselines.
  - **Honest Owner & Measurement Disclosures Still Open for Default Scoped Launch:**
    - Owner must review and apply [`handoff/default_cutover_local_only_scoped.patch`](./handoff/default_cutover_local_only_scoped.patch) and [`handoff/frontend_local_ai_status_and_keyless_ux.patch`](./handoff/frontend_local_ai_status_and_keyless_ux.patch).
    - Target 4–8 GiB student hardware timing/co-residency with full browser/Chromium remains `PHYSICAL_TARGET_HARDWARE = NOT_MEASURED` (`15.78 GiB` Windows dev host measured `973.28 MiB` backend+SLM working set, `637.5 MiB` private commit; simulated `2`-thread `n=24` ablation ran `p50=7,196.61 ms` / `p95=10,196.66 ms`).

### Level 3 — `LOCAL_ONLY_GENERAL_RELEASE_READY`
- **Status:** **NOT MET (`BLOCKED_DATA_ACCESS` + `BLOCKED_HARDWARE` + `BLOCKED_OWNERSHIP`)**
  - Although author-constructed `SLM_V9_UNSEEN_150` reached `89.52%` positives (`[0.8221, 0.9405]`) and mixed warm uncached host `p95 = 4,109.98 ms <= 5,000 ms`, pure SLM-only uncached `n=100` `p95 = 5,411.75 ms` exceeds `5,000 ms`, `C60_BLIND_NLU` sits at `76.19%` (`32/42`, capped at `33/42 = 78.57%` upstream `TypedFactNext /2` Gold ceiling), `EXTERNAL_INDEPENDENCE = NOT_MEASURED` (`sealed_H1` & `locked_W2_W3` unopened; no live external student corpus), `GEMINI_PARITY = NOT_MEASURED`, `PHYSICAL_TARGET_HARDWARE = NOT_MEASURED`, `REAL_STUDENT_USABILITY = NOT_MEASURED`, and `SOURCE_GATE_OWNER_HANDOFF = BLOCKED_OWNERSHIP`.

---

## 3. Gate `G0`–`G10` Disposition Table

| Gate | Requirement | Final Status | Supporting Artifact(s) |
|---|---|---|---|
| **G0** | Baseline Identity & Ownership Audit | **PASS** | `BASELINE_AND_OWNERSHIP_AUDIT.md`, `EVALUATION_CANDIDATE.json`, `cache_identity.lock.json` |
| **G1** | C60 Root-Cause & Gold Intervention | **PASS** | `C60_CASE_LEVEL_ROOT_CAUSE.json`, `C60_GOLD_INTERVENTION_RESULTS.json`, `SLM_V9_BOTTLENECK_REPORT.md` |
| **G2** | Deterministic Vietnamese Closure | **PASS** | `DETERMINISTIC_VIETNAMESE_CLOSURE.md`, `C60_POST_P2_V9_RESULTS.json`, `test_slm_v9_language_closure_and_security.py` |
| **G3** | Targeted SLM Improvement (`AxoV9-Q4_K_M`) | **PASS** | `SLM_V9_TRAINING_DECISION.md`, `SLM_V9_TRAINING_RUN.json`, `SLM_V9_MODEL_MANIFEST.json`, `SLM_V9_QUANTIZATION_EVALUATION.json`, `C60_POST_P3_V9_RESULTS.json` |
| **G4** | Performance, Caching & Fault Recovery | **PASS (Host Mixed `p95 <= 5s`) / `PHYSICAL_TARGET_HARDWARE = NOT_MEASURED`** | `SLM_V9_ABLATION.json`, `SLM_V9_RUNTIME_PERFORMANCE.json`, `SLM_V9_SYSTEM_RESOURCE_REPORT.md` |
| **G5** | Unseen Single-Shot Evaluation (`SLM_V9_UNSEEN_150`) | **PASS (With `EXTERNAL_INDEPENDENCE = NOT_MEASURED` Disclosure)** | `SLM_V9_UNSEEN_MANIFEST.json`, `SLM_V9_UNSEEN_EVALUATION.json`, `SLM_V9_CAPABILITY_MATRIX.json` |
| **G6** | Gemini Dependency Inventory & Coverage | **PASS** | `GEMINI_DEPENDENCY_INVENTORY.json`, `GEMINI_REPLACEMENT_COVERAGE_REPORT.md`, `LOCAL_REPLACEMENT_COVERAGE_REPORT.md` |
| **G7** | Real Local-Only Product Route & UX | **BACKEND OPT-IN PASS / DEFAULT CUTOVER & FRONTEND `BLOCKED_OWNERSHIP`** | `LOCAL_ONLY_ROUTING_DESIGN.md`, `LOCAL_ONLY_PRODUCT_INTEGRATION_REPORT.md`, `LOCAL_MODEL_PROVISIONING_REPORT.md`, `LOCAL_AI_USER_EXPERIENCE_REPORT.md`, `OWNER_HANDOFF.md` |
| **G8** | Offline Security & Network Isolation | **PASS (`0` External AI Calls)** | `OFFLINE_NETWORK_ISOLATION_REPORT.md`, `verify_offline_network_isolation_v9.py`, `test_local_only_product_and_network_isolation.py` |
| **G9** | Full Regression & Construction Freeze Integrity | **PASS** | `SLM_V9_REGRESSION_RESULTS.json`, `SLM_V9_REGRESSION_REPORT.md` |
| **G10** | Release & Default Cutover Decision | **`LOCAL_ONLY_SCOPED_RELEASE_READY` (Backend Opt-In) / `BLOCKED_OWNERSHIP` (Default Switch & UI)** | `LOCAL_ONLY_CUTOVER_DECISION.md`, `FINAL_MASTER_REPORT.md` |
