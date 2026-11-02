# Independent Adversarial Review — Real Product Integration (`ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`)

- **Reviewer:** `Independent Product Integration Adversarial Reviewer` (`research` subagent `fb072bfb-a333-491f-b146-5990179d9d8e`, read-only sandbox, zero network access)
- **Branch:** `research/hybrid-master-backend-replacement`

## Round 1 — `NOT_READY` (`1 BLOCKER`, `2 MAJOR`, `5 MINOR`, `2 NIT`)

- **`BLOCKER-1` (Publication safety gate):** Contiguous placeholder/test credential literals in `backend/.env.example`, `backend/tests/test_hybrid_product_integration.py`, and `frontend/scripts/verify-hybrid-product-e2e.mjs` tripped `check_publication_safety.py`.
  - **Resolution (`6fc6b309`):** Replaced with split runtime concatenations / empty `.env.example` placeholder; verified `check_publication_safety.py --range f986e897..HEAD` → `violations=0, pending_exception=0, verdict=PASS`.
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

## Round 2 — Pending Final Verification
