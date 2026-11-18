# AXO Step Editor — Integration & Regression Closure Report

- **Campaign:** `AXO STEP EDITOR — INTEGRATION & REGRESSION CLOSURE`
- **Date:** `2026-11-19`
- **Branch:** `feat/axo-geometry-library-verification`
- **Primary Development Worktree:** `D:/Documents/projects/axo-geometry-library`
- **Clean Verification Worktree:** `D:/Documents/projects/algo-sim/.superpowers/worktrees/step-editor-clean-candidate`
- **Protected Root Checkout:** `D:/Documents/projects/algo-sim` (`axo-ui-consistency` — untouched)
- **Model Status:** `MODEL_NOT_TRAINED` (deterministic closed grammar + Exact Kernel `Fraction`/`Radical`; zero LLM calls during step editing)
- **Final Verdict:** **`BLOCKED`** (`ENVIRONMENT_BLOCKED` on live PostgreSQL container execution + `OWNERSHIP_BLOCKED` / `PRE_EXISTING` incomplete parallel frontend & attachment WIP on `HEAD`)

---

## 1. Repository snapshot

- **Base `HEAD` before this closure wave:** `bae665e79d69b6b47fae34187b0ea1b02d722e50` (`92` commits ahead of `main = bb046fa22aceff47abe22aa783aa64fc65caee13`, `0` behind).
- **Local commits produced on `feat/axo-geometry-library-verification` (not merged, not pushed):**
  1. **Product Commit `P` (`37b7460ddd6f01dc07e5999dd09e29abe3ac2486`):** `10` owned files fixing geometry kernel boundary, real repo Alembic wiring + `9c4d8e2b7a10`, Step Editor concurrency/retry/version-clock, regression tests, and `docs/CODE_INDEX.md` lines 13–14.
  2. **Candidate Seal Commit `C` (`3eabbf674bfca82d19ca00b2894d2576dd87a5e5`):** `4` evaluation seal/template files generated from clean worktree `step-editor-clean-candidate` at `P`.
  3. **Evidence & Closure Commit `D`:** closure run evidence artifacts under `docs/evaluation/geometry/runs/step-editor-integration-closure/`.
- **Clean vs Dirty Tree Audit:**
  - `step-editor-clean-candidate` was verified completely clean (`git status --porcelain` = empty) prior to freezing Candidate Seal and after attaching gitignored `frontend/node_modules` junction.
  - `axo-geometry-library` preserves all `77` pre-existing `OWNERSHIP_BLOCKED` uncommitted files/hunks from parallel Classroom/Attachment/Workspace WIP untouched.

---

## 2. Baseline

Verified pre-intervention state saved at [`results/pre-intervention-baseline.json`](results/pre-intervention-baseline.json):

| Backlog Item | Observed Baseline Command / State | Status |
|---|---|---|
| Geometry `15` failures (`test_KHONG_co_mat_cong...` + `13` seal + `1` `CODE_INDEX`) | `pytest tests/geometry/test_curriculum_coverage.py -k KHONG_co_mat_cong -v` failed `AssertionError: sphere`; `freeze_evaluation_candidate.py --verify` exited `1` | `REPRODUCED` |
| Semantic Candidate `1` failure | `pytest tests/semantic_program/test_evaluation_candidate.py -q` -> `1 failed, 25 passed` (`tree_hash` frozen `b1a8d439...` / 106 files != `e7723a3c...` / 109 files) | `REPRODUCED` |
| Candidate Seal uniformity | `k1/r1/s2-owner-approval.template.json` stored dict `measured_system` instead of 64-char hex string matching `EVALUATION_CANDIDATE.json` | `REPRODUCED` |
| PostgreSQL integration & Alembic | `step_edit_models.ensure_step_edit_tables()` is intentional no-op on PostgreSQL; `backend/alembic/env.py` lacked `step_edit_models`; committed Alembic head `e437149641fa` lacked `step_edit_*` migration; `com.docker.service` `Stopped` | `REPRODUCED` |
| Alembic Classroom dependency | Untracked `f8a2c41d9e05` sets `down_revision = "e437149641fa"` in parallel Classroom WIP | `REPRODUCED` |
| `4` Classroom stale paths in `CODE_INDEX.md` | All `4` (`LiveClassDock.tsx`, `LiveClassStrip.tsx`, `MonitorView.tsx`, `classroom-sync.ts`) verified present in committed `HEAD`; only deleted in uncommitted `OWNERSHIP_BLOCKED` WIP | `NOT_REPRODUCED_ON_CLEAN_HEAD` |
| Step Editor concurrency & version clock | `_LATEST_CLIENT_SEQ` incremented pre-commit (`503` poisoned retry into `409`); missing `expected_committed_version` OCC / `FOR UPDATE`; `construction-step-edits.ts` returned raw `version_number` instead of `effectiveVer` after failed `422`s | `REPRODUCED` |

---

## 3. Root cause analysis

1. **Geometry Boundary (`kernel.py` -> `curved.py`):** Commit `ef9c20160` added `ERR_KHONG_NGOAI_TIEP` and `circumscribed_sphere` directly inside `backend/app/simulation/geometry/kernel.py`, violating the polyhedral `Fraction` boundary (`test_curriculum_coverage.py:151` asserts `"sphere"` is absent from `dir(kernel)`). Moved both symbols cleanly into `curved.py` and re-exported them via `geometry/__init__.py`.
2. **Alembic Without Classroom Coupling:** Committed `HEAD` ends at `e437149641fa`, while Classroom removal (`f8a2c41d9e05`) is uncommitted WIP. Created committed migration `9c4d8e2b7a10_add_step_edit_tables.py` (`down_revision = "e437149641fa"`) importing `step_edit_models` in `backend/alembic/env.py`, plus rebase instructions for Classroom WIP in [`patches/classroom-wip-rebase-onto-step-editor.patch`](patches/classroom-wip-rebase-onto-step-editor.patch).
3. **Router Retry Poisoning, Row Locking, & Optimistic Concurrency:**
   - Moved `_LATEST_CLIENT_SEQ` updates in `step_edit_router.py` strictly *after* `db.commit()` (both `200` and `422` paths) and persisted `_latest_client_seq` in `StepEditSessionRecord.dependency_graph_json` so an interrupted `db.commit()` (`OperationalError` -> `503`) never blocks retry of the same `client_seq` / `client_request_id`.
   - Added `expected_committed_version` check returning HTTP `409 STALE_REVISION_CONFLICT` with authoritative `committed_version`, and enabled `SELECT ... FOR UPDATE` (`.with_for_update()`) on non-SQLite engines (PostgreSQL).
4. **Frontend Version Clock Drift (`construction-step-edits.ts`):** When failed `422` attempts advance backend `revision_count` (`version_number`), `submitConstructionStepEdit` now normalizes returned `version_number` to `effectiveVer` (`committed_version`) while preserving `revision_version_number`, and supports sending `expected_committed_version`.
5. **Candidate Drift & Template Dict Format:** Froze updated `EVALUATION_CANDIDATE.json` cleanly via `freeze_evaluation_candidate.py` on clean `37b7460dd` (`111` files, `c1323d0a7bd9fda0...`) and synced `k1/r1/s2-owner-approval.template.json` to the 64-char hex string format expected by `run_s2_student_language_pilot.py` & `test_evaluation_candidate.py`.
6. **Pre-existing Clean-HEAD Frontend / Attachment Incomplete Commits (`OWNERSHIP_BLOCKED`):** `git show bae665e79` proved `ProblemInput.tsx`, `WorkspaceTabBar.tsx`, and `docs/CODE_INDEX.md:7` already referenced uncommitted `ScreenCaptureDialog.tsx`, `store.ts` fields, and `attachment-resize.node-test.mjs` prior to this campaign. Left untouched per ownership rules.

---

## 4. PostgreSQL & Alembic

- **Real Repo Alembic Chain (`FIXED_AND_VERIFIED` on SQLite isolated harness):**
  - Updated [`backend/alembic/env.py`](../../../../alembic/env.py) to register `step_edit_models`.
  - Added [`backend/alembic/versions/9c4d8e2b7a10_add_step_edit_tables.py`](../../../../alembic/versions/9c4d8e2b7a10_add_step_edit_tables.py) (`revision = "9c4d8e2b7a10"`, `down_revision = "e437149641fa"`).
  - Clean worktree `pytest tests/test_migration_drift.py -v`: **`2 passed in 5.07s`** (`test_model_and_migration_head_have_no_drift`, `test_repeated_upgrade_at_head_is_noop`).
  - `test_real_repo_alembic_env_and_9c4d8e2b7a10_upgrade_downgrade_zero_drift`: verified `upgrade head`, `downgrade e437149641fa`, `upgrade head`, and zero `step_edit_*` schema drift.
- **PostgreSQL 16 Live Execution (`ENVIRONMENT_BLOCKED` / `BLOCKED_ENVIRONMENT`):**
  - Attempted `docker desktop status`, `docker desktop start` (`✓ Starting Docker Desktop`), `docker info`, `Get-Service com.docker.service`, and `wsl -l -v`.
  - Observed exact blocker: `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`, `com.docker.service` `Stopped`, WSL `docker-desktop` `Stopped`, and no local PostgreSQL binary installed.
  - Running `pytest tests/test_postgres_integration.py tests/test_postgres_axo_history_migration.py tests/geometry/test_step_editor_integration_closure.py -m postgres -v` resulted in **`4 skipped, 8 deselected in 2.95s`**. No SQLite mock was substituted as PostgreSQL pass.
- **Persistence & Restart Verification (SQLite Fallback Host DB):**
  - Verified full commit -> `422` rollback retention -> `:8000` process termination & restart (`PID 12604 -> 8688`) -> fresh-context `GET /api/simulation/sessions/{id}/state` HTTP `200` recovery (`found: true`, `committed_version: 1`, `M = ["0", "0", "9/2"]`).

---

## 5. Geometry & Semantic

- **Curriculum Boundary (`tests/geometry/test_curriculum_coverage.py` + `test_axo_11_advanced_samples.py`):** **`23 passed in 1.11s`** (`test_KHONG_co_mat_cong_va_KHONG_co_phep_chieu_song_song` green after moving `circumscribed_sphere` & `ERR_KHONG_NGOAI_TIEP` to `curved.py`).
- **Generalized Semantic Equivalence vs Hypothesis Mutation & Helper Retirement:** `test_generalized_semantic_equivalence_families_vs_hypothesis_mutation_and_retired_helper` verified:
  - Ratio wording families (`SM/SA = 1/2`, `AM/AS = 1/2`) classify as `EQUIVALENT_GEOMETRY` (`before_after_diff.changed === False`, `M` coordinates invariant).
  - Hypothesis mutation (`SM/SA = 1/3`) classifies as `GEOMETRY_MUTATED` and recomputes downstream objects.
  - Circumsphere invariant on unmodified sample 11 enforces `DOWNSTREAM_CIRCUMSCRIBED_SPHERE_BROKEN` when invalidating equidistance.
  - Retiring exclusive inline helper `M_AB` removes it from surviving objects with zero dangling `depends`.
- **Full Semantic Program & Demo Replay:** `tests/semantic_program`: **`1192 passed, 1 skipped in 68.86s`**; `replay_demo_cases.py`: **`5/5` (`REDUCED_CHAIN_CASES 1/1`)**; `audit_demo_crash_surface.py`: **`6/6` (`0` unhandled `500`)**.

---

## 6. Ownership & Candidate integrity

- **Strict Ownership Preservation:** Zero changes made to `D:/Documents/projects/algo-sim` or any of the `77` `OWNERSHIP_BLOCKED` files (`SimulationWorkspace.tsx`, `backend/app/main.py`, `backend/app/accounts/*`, `classroom_models.py`, `f8a2c41d9e05_remove_classroom_and_live_session_tables.py`, `test_postgres_axo_history_migration.py`, `docs/EVIDENCE_INDEX.md`, `frontend/package*.json`, etc.).
- **Documentation & `CODE_INDEX` Audit:**
  - Updated lines 13–14 of `docs/CODE_INDEX.md` for Step Editor (`curved.py`, `alembic/env.py`, `9c4d8e2b7a10`, `STALE_REVISION_CONFLICT`, `expectedCommittedVersion`, normalized `version_number`).
  - On clean worktree `step-editor-clean-candidate`: all `4` Classroom paths (`LiveClassDock.tsx`, `LiveClassStrip.tsx`, `MonitorView.tsx`, `classroom-sync.ts`) resolved cleanly (`0` stale Classroom paths). The single remaining failure in `audit_docs_information_architecture.py` (`CODE_INDEX stale paths: 1`) is `docs/CODE_INDEX.md:7 -> frontend/scripts/attachment-resize.node-test.mjs` (`OWNERSHIP_BLOCKED` / `PRE_EXISTING` untracked Attachment WIP).
- **Candidate Seal Integrity (`3eabbf674`):**
  - Generated exclusively via `python scripts/freeze_evaluation_candidate.py` in clean `step-editor-clean-candidate`.
  - Product commit pinned: `37b7460ddd6f01dc07e5999dd09e29abe3ac2486` (`111` files, `tree_hash = c1323d0a7bd9fda0e13114bfc4a03fe36124bb8d733ef472cf5430f967378b38`, `SEALED = DA_NIEM_PHONG`).
  - `freeze_evaluation_candidate.py --verify` exits **`0`**; `pytest tests/semantic_program/test_evaluation_candidate.py -q` passes **`26/26`**.
  - Owner approval templates `{k1,r1,s2}-owner-approval.template.json` synced to `tree_hash` with `owner_decision = "PENDING_OWNER_DECISION"` and `paid_project_confirmed = false`.

---

## 7. End-to-end acceptance

All live E2E scenarios passed cleanly against `http://localhost:3001` (`PID 11008`) + `http://127.0.0.1:8000` (`PID 12604 -> 8688`), recorded in [`results/closure-e2e-verification.json`](results/closure-e2e-verification.json):

| Problem / Scenario | Outcome | Key Observed Evidence |
|---|---|---|
| **P1: Hình chóp `S.ABCD` & mặt cầu ngoại tiếp** (`chop-mat-cau-ngoai-tiep`) | `PASS` | Hover height delta `0px`, opacity `0 -> 1`, hotkey isolated (`Space`/`ArrowLeft`), `422 MISSING_DEPENDENCY` preserves draft & sphere (`closure-1920-invalid-422.png`), subsequent valid edit returns `committed_version=1` despite raw `version_number=2` (`closure-1920-p1-valid-edit.png`) |
| **P2: Hình chóp `S.ABCD` & thiết diện** (`chop-thiet-dien-ba-diem`) | `PASS` | Early step edit `SM/SA = 1/4` -> `M=["0","0","9/2"]`, `recomputedCount=6` (`mp_MNP`, `E`, `F`, `thiet_dien`, `S_td`, `V_chop`), survives `F5` reload (`closure-1920-p2-cascade-f5.png`) |
| **P3: Lăng trụ & thiết diện** (`lang-tru-tam-giac-thiet-dien`) | `PASS` | Renders `CC′` (zero `_prime`), commits `CP = 1/3 CC′` with HTTP `200` (`closure-1920-p3-prism.png`) |
| **P4: Đoạn vuông góc chung** (`khoang-cach-hai-duong-cheo-nhau`) | `PASS` | Step navigation syncs `#pa-short-title`, invalid ratio `BP/BD = 1/5` returns `422 DOWNSTREAM_ORTHOGONALITY_BROKEN` preserving draft & valid scene (`closure-1920-p4-common-perp.png`) |
| **Scenario 4: Real `:8000` Restart Recovery** | `PASS` | Killed `PID 12604`, restarted `PID 8688` on same DB; fresh context (`localStorage` seeded with token only) received `GET /state` `200` (`found=true`, `committedVersion=1`, `M=["0","0","9/2"]`) and rendered `SM/SA = 1/4` (`closure-1920-post-restart.png`) |
| **Scenario 5: Multi-Problem Switching** | `PASS` | Switching between P1, P2, P3 retains each session override with zero cross-problem leakage |
| **Scenario 6 + 7 Viewports + Touch (`390x844`)** | `PASS` | `1920x1080`, `1440x900`, `1366x768`, `1024x768`, `768x1024`, `390x844`, `320x568` all `overflowX = 0`, `canvasVisible = true`, zero clipping/occlusion (`closure-vp-*.png`); touch tap opens editor (`editorOpenedViaTap = true`) |
| **REA MCP CDP (`:9338`)** | `PASS` | `list_browser_targets` `ev_ac7a48fd...`, `capture_web_screenshot` `ev_d6aa74d3...` (`sha256: 7c6be261...`, `images/closure-rea-mcp-screenshot.png`) |

---

## 8. Quality gates

| Gate & Command | Worktree | Total | Passed | Failed | Skipped / Desel / XFail | Exit | Classification |
|---|---|---|---|---|---|---|---|
| `pytest tests/geometry/test_step_editor_integration_closure.py ... (6 suites)` | `axo-geometry-library` | 84 | 82 | 0 | 2 desel (`postgres`) | 0 | `FIXED_AND_VERIFIED` |
| `pytest tests/test_migration_drift.py -v` | `clean-candidate` | 2 | 2 | 0 | 0 | 0 | `FIXED_AND_VERIFIED` |
| `pytest tests/geometry -m "not postgres" -q` | `clean-candidate` | 12011 | 11994 | 2 | 6 skip, 2 desel, 9 xfail | 1 | `OWNERSHIP_BLOCKED` (`CODE_INDEX:7` Attachment) + `-m` override ran `external_evidence` |
| `pytest tests/geometry/test_evidence_identity_reconciliation.py -v` | `clean-candidate` | 7 | 6 | 0 | 1 desel (`external_evidence`) | 0 | `FIXED_AND_VERIFIED` (confirms `pytest.ini` default deselection) |
| `pytest tests/semantic_program -q` | `clean-candidate` | 1193 | 1192 | 0 | 1 skip | 0 | `FIXED_AND_VERIFIED` |
| `pytest tests/semantic_program/test_evaluation_candidate.py -q` | `clean-candidate` | 26 | 26 | 0 | 0 | 0 | `FIXED_AND_VERIFIED` |
| `pytest tests --ignore=tests/geometry --ignore=tests/semantic_program -q` | `clean-candidate` | 867 | 865 | 0 | 2 desel | 0 | `FIXED_AND_VERIFIED` |
| `pytest ... -m postgres -v` | `clean-candidate` | 12 | 0 | 0 | 4 skip, 8 desel | 0 | `ENVIRONMENT_BLOCKED` (Docker Linux pipe down) |
| `python scripts/replay_demo_cases.py` | `clean-candidate` | 5 (+1) | 5 (+1) | 0 | 0 | 0 | `FIXED_AND_VERIFIED` |
| `python scripts/audit_demo_crash_surface.py` | `clean-candidate` | 6 | 6 | 0 | 0 | 0 | `FIXED_AND_VERIFIED` |
| `python scripts/audit_docs_information_architecture.py` | `clean-candidate` | 1 suite | — | 1 | 0 | 1 | `OWNERSHIP_BLOCKED` (`CODE_INDEX:7 -> attachment-resize.node-test.mjs` untracked WIP) |
| `python scripts/freeze_evaluation_candidate.py --verify` | `clean-candidate` | seal | 1 | 0 | 0 | 0 | `FIXED_AND_VERIFIED` |
| `npx vitest run src/components/construction-step-editor.test.tsx` | `axo-geometry-library` | 22 | 22 | 0 | 0 | 0 | `FIXED_AND_VERIFIED` |
| `npx vitest run` | `clean-candidate` | 2050 | 2038 | 9 | 3 skip | 1 | `OWNERSHIP_BLOCKED / PRE_EXISTING` (incomplete `ProblemInput`/`WorkspaceTabBar` commits missing `ScreenCaptureDialog`/`store` WIP) |
| `npx tsc -b` & `npx vite build` | `clean-candidate` | — | — | failed | — | 1 | `OWNERSHIP_BLOCKED / PRE_EXISTING` (missing uncommitted `ScreenCaptureDialog.tsx` & `store.ts` WIP) |
| `npx vitest run` (standalone) | `axo-geometry-library` | 2272 | 2272 | 0 | 0 | 0 | `FIXED_AND_VERIFIED` (`192/192` files in `119.61s`) |
| `npx tsc --noEmit` | `axo-geometry-library` | — | pass | 0 | — | 0 | `FIXED_AND_VERIFIED` |
| `npx vite build --outDir .../scratch/vite-dist` | `axo-geometry-library` | 129 mod | pass | 0 | — | 0 | `FIXED_AND_VERIFIED` (`11.02s`) |

---

## 9. Host verification

Live services currently running for Owner inspection (with explicit DB caveat — PostgreSQL unavailable due to `ENVIRONMENT_BLOCKED`):

| Service | URL | Port | PID | Backing Directory & DB | Live HTTP Status |
|---|---|---|---|---|---|
| Axo Backend API (`uvicorn`) | `http://127.0.0.1:8000` | `8000` | `8688` | `D:/Documents/projects/axo-geometry-library/backend`, `DATABASE_URL=sqlite:///D:/Documents/projects/algo-sim/.superpowers/step-editor-host-live.db` | `GET /api/health` -> `200` (`{"ok":true,...,"db":"sqlite"}`) |
| Axo Frontend (`vite`) | `http://localhost:3001/app` | `3001` | `11008` | `D:/Documents/projects/axo-geometry-library/frontend` | `GET /app` -> `200` |

---

## 10. Git changes

- **Commit `P` (`37b7460ddd6f01dc07e5999dd09e29abe3ac2486`) — Owned code, migration, tests, `CODE_INDEX`:**
  - `backend/app/simulation/geometry/curved.py`
  - `backend/app/simulation/geometry/__init__.py`
  - `backend/app/simulation/geometry/kernel.py`
  - `backend/alembic/env.py`
  - `backend/alembic/versions/9c4d8e2b7a10_add_step_edit_tables.py`
  - `backend/app/simulation/step_edit_router.py`
  - `backend/tests/geometry/test_step_editor_integration_closure.py`
  - `frontend/src/state/construction-step-edits.ts`
  - `frontend/src/components/construction-step-editor.test.tsx`
  - `docs/CODE_INDEX.md` (lines 13–14 only)
- **Commit `C` (`3eabbf674bfca82d19ca00b2894d2576dd87a5e5`) — Candidate Seal & Templates:**
  - `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`
  - `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/k1-owner-approval.template.json`
  - `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/r1-owner-approval.template.json`
  - `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/s2-owner-approval.template.json`
- **Closure Evidence Commit `D` (`docs/evaluation/geometry/runs/step-editor-integration-closure/` only):** `run.json`, `report.md`, `AXO-STEP-EDITOR-INTEGRATION-CLOSURE-REPORT.md`, `results/*.json`, `images/*.png`, `patches/classroom-wip-rebase-onto-step-editor.patch`.
- **Untouched:** All `77` `OWNERSHIP_BLOCKED` files in `D:/Documents/projects/axo-geometry-library`, `D:/Documents/projects/algo-sim`, `main` branch (no merge, no push). Zero secrets stored.

---

## 11. Remaining risks

1. **Unverified Live PostgreSQL Runtime (`ENVIRONMENT_BLOCKED`, High):** Alembic `9c4d8e2b7a10`, `.with_for_update()` row locking, and full PostgreSQL E2E test `test_postgres_real_step_editor_end_to_end_persistence_restart_and_rollback` could not execute against a live PostgreSQL 16 engine because Docker Desktop Linux Engine (`npipe:////./pipe/dockerDesktopLinuxEngine`) failed to start here.
2. **Pre-existing Uncommitted Frontend / Attachment WIP on `HEAD` (`OWNERSHIP_BLOCKED`, High for Clean Checkout Merge):** Committed `ProblemInput.tsx`, `WorkspaceTabBar.tsx`, and `CODE_INDEX.md:7` depend on uncommitted `ScreenCaptureDialog.tsx`, `store.ts`, and `attachment-resize.node-test.mjs` WIP from parallel tracks, breaking clean-checkout `vite build`, `tsc -b`, and `audit_docs_information_architecture.py` (`1` stale path).
3. **Parallel Classroom Alembic Rebase Pending:** `f8a2c41d9e05_remove_classroom_and_live_session_tables.py` (untracked WIP) shares `down_revision = "e437149641fa"` and must apply `patches/classroom-wip-rebase-onto-step-editor.patch` when landing.
4. **Single-Worker Process Constraint:** Step Editor in-memory session lock / sequence caches enforce single-worker Uvicorn (`503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY`).
5. **`MODEL_NOT_TRAINED`:** Step editing relies strictly on the deterministic closed parser and Exact Kernel without a trained local neural model.

---

## 12. Final verdict

**Verdict: `BLOCKED`**

All Step Editor product defects, geometry kernel boundary violations, Alembic migration wiring (`9c4d8e2b7a10`), concurrency/retry/version-clock bugs, candidate seal drift (`3eabbf674`), and live Step Editor E2E behaviors are **`FIXED_AND_VERIFIED`**. However, release/merge readiness remains **`BLOCKED`** under §XI because:
1. Live PostgreSQL verification (`§XI #1`) could not execute (`ENVIRONMENT_BLOCKED`: Docker Desktop Linux Engine pipe unavailable locally).
2. A clean checkout of committed `HEAD` cannot currently pass `vite build` / `tsc -b` / `audit_docs` due to `OWNERSHIP_BLOCKED` pre-existing incomplete commits (`ScreenCaptureDialog.tsx`, `store.ts`, `attachment-resize.node-test.mjs` left uncommitted in parallel tracks).

**Required actions before Owner approves merging to `main`:**
1. On a machine with Docker/PostgreSQL active, run `pytest tests/test_postgres_integration.py tests/test_postgres_axo_history_migration.py tests/geometry/test_step_editor_integration_closure.py -m postgres -v` against committed `HEAD` and verify live `:8000` backed by PostgreSQL 16 (`alembic upgrade head`).
2. Land or decouple the parallel uncommitted Attachment / Workspace WIP (`ScreenCaptureDialog.tsx`, `store.ts`, `attachment-resize.node-test.mjs`) and apply `patches/classroom-wip-rebase-onto-step-editor.patch` if Classroom removal lands alongside Step Editor.
3. Re-verify `npx tsc -b`, `npx vite build`, and `python backend/scripts/audit_docs_information_architecture.py` exit `0` on a clean checkout.
