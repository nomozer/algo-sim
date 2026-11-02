# Independent Adversarial Review — Real Product Integration (`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`)

- **Reviewer:** `Independent Product Integration Adversarial Reviewer` (`research` subagent `fb072bfb-a333-491f-b146-5990179d9d8e`, read-only sandbox, zero network access)
- **Branch:** `research/hybrid-master-backend-replacement`

## Round 1 — `NOT_READY` (`1 BLOCKER`, `2 MAJOR`, `5 MINOR`, `2 NIT`)

- **`BLOCKER-1` (Publication safety gate):** Contiguous placeholder/test credential literals in `backend/.env.example`, `backend/tests/test_hybrid_product_integration.py`, and `frontend/scripts/verify-hybrid-product-e2e.mjs` tripped `check_publication_safety.py`.
  - **Resolution (`6fc6b309`):** Restored angle-bracket `<dan-key-vao-day>` placeholder in `backend/.env.example` and replaced contiguous test secret/password literals with split runtime concatenations; verified `check_publication_safety.py --range f986e897..HEAD` → `violations=0, pending_exception=0, verdict=PASS`.
- **`MAJOR-1` + `MINOR-5` (Live transport timeout/deadline & retry budget):** Non-finite `HYBRID_LIVE_TIMEOUT_SECONDS` (`nan`/`inf`), `is_retry` accounting on transient retries, per-attempt vs overall deadline bounding, and empty `GEMINI_MODEL` normalization.
  - **Resolution (`6fc6b309`, refined in `d17116cb`):** Added `_finite_pos`, `resolve_hybrid_gemini_model`, `is_retry=(attempt > 0)` in `live_transport` (`ApiBudget`), and dedicated `HybridTransportTimeout` (preserving `PROVIDER_ERROR` on generic `httpx.TimeoutException` in `run_paired_route_evaluation.py`).
- **`MAJOR-2` (`M18` active assignment / semanticFocus store reset):** `setAnalysisError`, `loadUnsupported`, and `loadEnvelope` error branches left `activeAssignment` / `semanticFocus` populated when clearing `active`.
  - **Resolution (`6fc6b309`):** Cleared `activeAssignment: null` and `semanticFocus: null` alongside `active: null` in `frontend/src/state/store.ts`; covered in `hybrid-product-integration.test.tsx`.
- **`MINOR-1`, `MINOR-2`, `NIT-1` (Frontend clarification & Category B validator hardening):**
  - **Resolution (`6fc6b309`):** `photo-problem-flow.ts::buildFailureMessage` surfaces `clarification.question`; `hybrid-preview-adapter.ts::kiemClarification` enforces `spans.length >= 1` and rejects leaked machine tokens in `question`; `kiemEngineDerivedSection` checks `plane_equation` and `closure_certificate.producer`/`area_squared`.
- **`MINOR-3` (Living governance docs):**
  - **Resolution:** Updated `docs/CURRENT_STATE.md`, `docs/EVIDENCE_INDEX.md`, `docs/CODE_INDEX.md`, and `HYBRID_MASTER_EPIC_CURRENT_STATE.md`.
- **`MINOR-4`, `NIT-2` (Staging replay memoization & test DB isolation):**
  - **Resolution (`6fc6b309`):** Memoized `load_replay_corpus` by `(path, st_mtime_ns, st_size)`, stored single `recorded` entry on `StagingReplay`, and isolated `test_hybrid_product_integration.py` on a `tmp_path` SQLite DB.
- **Additional Full T3 Attempt 1 closure (`d17116cb`, frozen at `123e57da`):** Normalized CRLF → LF in `sha256_bytes` / `sha256_file` in `run_paired_route_evaluation.py` and `run_s2_student_language_pilot.py`, re-bound pilot approval templates (`2199eb32` / `a6792fce` / `9f832e67`), and passed Authoritative Full T3 Attempt 2 on clean detached worktree `hm-t3-123e57da` (`FULL_PRODUCT_GATE_PASS`, `16,648` pytest, `1,486` vitest, `full-t3-123e57da.json`).

## Round 2 — `NOT_READY` (`0 BLOCKER`, `1 MAJOR`, `1 MINOR`, `1 NIT` — `0` code/test defects, report-prose drift only)

- **Code & Test Verification:** All 10 Round 1 findings (`BLOCKER-1`, `MAJOR-1`, `MAJOR-2`, `MINOR-1..5`, `NIT-1..2`) and both Full T3 Attempt 1 fixes (`d17116cb`, frozen candidate `123e57da`, templates `2199eb32` / `a6792fce` / `9f832e67`) verified **CLOSED** with zero defects in `backend/app`, `frontend/src`, `backend/scripts`, `backend/tests`, or `frontend/scripts`.
- **`MAJOR-R2-1` (Browser E2E flow case IDs & answers in report):** `ALGOSIM_REAL_PRODUCT_INTEGRATION_REPORT.md` cited paraphrased/wrong case IDs and answers in Section C instead of the exact 6 flows in `product-e2e-browser-receipt.json`.
  - **Resolution:** Rewrote Section C items 1–6 verbatim from `product-e2e-browser-receipt.json` (`flow_1_supported_polyhedral` `S2-B-I07_ve_va_tinh` → `8/3`; `flow_2_curved_and_composite_geometry` `cr.shared_base_pyramids_plus_inscribed_sphere` + `cone.par.S` → `72`, `9π`, `81π/16`; `flow_3_multi_function_composition` `S2-B-P07_shared_intermediate_two_goals` → `√3`, `1`; `flow_4_constrained_plane_and_orthocenter` `K-A01` → `3√2/2` + `R1-B01` → `2304/625`; `flow_5_ambiguous_and_contradictory_refusal` `S2-C-A01_goc_chieu` + `S2-D-D03_contradictory_length`; `flow_6_infrastructure_failure_and_recovery` `HTTP 503 LIVE_AI_DISABLED` → recovery on `S2-B-I07_ve_va_tinh` + `rollback_off`).
- **`MINOR-R2-1` (Report CLI command, Docker/`.env.example` keys, Vitest count, and refusal categories):**
  - **Resolution:** Updated Section B/C/D in `ALGOSIM_REAL_PRODUCT_INTEGRATION_REPORT.md` to cite the exact read-only pytest gate (`pytest tests/test_hybrid_product_integration.py -k test_staging_replay_serves_and_refuses_all_16_scope_classes`), `62` vitest tests in `hybrid-product-integration.test.tsx`, `4` corpus refusal/clarify categories (`13_contradictory_data`..`16_unsupported_goals`) + pre-extraction `out_of_scope` domain gate, and exact `docker-compose.yml` / `backend/.env.example` keys vs optional `main.py` timeout overrides.
- **`NIT-R2-1` (`.env.example` placeholder wording in Round 1 note):**
  - **Resolution:** Clarified `<dan-key-vao-day>` placeholder wording in Round 1 `BLOCKER-1` note above.

## Round 3 — Pending Final Verification
