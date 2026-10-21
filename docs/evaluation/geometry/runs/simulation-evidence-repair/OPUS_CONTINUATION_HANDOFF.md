# OPUS CONTINUATION HANDOFF — `SIMULATION_EVIDENCE_REPAIR_W01`

- **Authorization:** `GO_SIMULATION_EVIDENCE_REPAIR_LOCAL_ONLY`
- **Final Campaign Verdict:** `SIMULATION_EVIDENCE_REPAIR_PARTIAL` (`0 BLOCKER, 1 IMPORTANT (retained open on frozen product code), 0 MINOR`)
- **Date:** `2026-10-21`

---

## 1. Exact Branches, Worktrees, and Commit SHAs

| Worktree Path | Branch / Mode | Commit SHA | Status |
|---|---|---|---|
| `D:\Documents\projects\algo-sim` | `research/hybrid-wave3a-volume-reasoning` (root checkout) | `fe9f555437498432427ae6bbd54402cdd59c7eb7` | Preserved untouched (`2` untracked dirs `.claude/`, `tmp/`) |
| `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-coverage-visual-validation` | `research/simulation-coverage-visual-validation` | `d86c72031d8fc85cd4eef62d9379cd1690ba1417` | Preserved untouched (`0` dirty/untracked files) |
| `D:\Documents\projects\algo-sim\.superpowers\worktrees\verify-simulation-go-main` | Detached HEAD (reconciliation worktree) | `d86c72031d8fc85cd4eef62d9379cd1690ba1417` | Preserved untouched (uncommitted reconciliation files intact) |
| `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-evidence-repair` | `research/simulation-evidence-repair` | `DOCUMENTATION_COMMIT_ROLE = SELF` (parent `5c4a6ff90377add14a375b42436012156de2b143`, initial repair commit `48c34d886579948aa9c28019dd0559fd100f6dcd`) | Active repair worktree (clean) |
| `D:\Documents\projects\algo-sim\.superpowers\worktrees\verify-simulation-evidence-repair` | Detached HEAD (clean verification worktree) | Synced to `research/simulation-evidence-repair` HEAD | Clean detached verification worktree |

- **Verified `main` / `origin/main` / `ls-remote`:** `bd8d6a9dc3acc9a4204b616379001270bb6d39f9` (untouched; no merge, no push).
- **Original Product Commit (frozen):** `3298b901d2246650535aa4028845ddc2a44892c4`
- **Original Candidate Commit:** `5f4ee58c48011e9e5d38d3209f7c97250032a976`
- **Measured System Identity:** `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` (`114` files)

---

## 2. Exact Status of Phases A–F

- **Phase A (Live Execution State Recovery):** **COMPLETE** — Recovered Codex's live Full T3 subprocess (`PID 21152/19600/7376`) running on `verify-simulation-evidence-repair` at `48c34d886579948aa9c28019dd0559fd100f6dcd`, waited for clean completion (`exit_code: 0`, `610.9s`, `FULL_PRODUCT_GATE_PASS`), and ran the pending post-T3 candidate freeze verification (`t3/freeze-invocation.json` $\to$ `t3/freeze/execution.json`, `exit_code: 0`, `MATCH`).
- **Phase B (Completed Evidence Repair Verification):** **COMPLETE** — Verified 4-way byte equality (`ORIGINAL_RUNTIME_BYTES == CORRECTIVE_ARCHIVE_BYTES == GIT_BLOB_BYTES == CLEAN_CHECKOUT_ARCHIVE_BYTES`) on all 4 original T3 logs, verified all 79 historical campaign artifacts in `historical-preservation.json`, and confirmed zero diff in `backend/` and `frontend/` since `3298b901d2246650535aa4028845ddc2a44892c4`.
- **Phase C (Cone Visibility Investigation):** **COMPLETE** — Root-caused `demo6b-curved-cone-frustum-cut` `td_sec_axial` `ownPixels = 0` (`resetDiffFromDefault = 239`) in `frontend/src/simulations/domains/geometry/scene3d-view.tsx` without mutating frozen product/test code.
- **Phase D (Remaining P4–P8 Completion):** **COMPLETE** — Recorded `t3/validation.json`, updated `archive-integrity.json` across `original_t3` (4 files), `browser_artifacts` (57 files), and `t3_artifacts` (11 files), and updated `plan.md`, `capability-matrix.md`, `report.md`, `run.json`, `docs/CURRENT_STATE.md`, `docs/EVIDENCE_INDEX.md`, and `docs/ROADMAP.md`.
- **Phase E (Clean Detached Checkout Verification):** **COMPLETE** — Synced `verify-simulation-evidence-repair` and verified `all_equal: true` across all archived logs, browser artifacts, and new T3/freeze artifacts.
- **Phase F (Bounded Independent Read-Only Review):** **COMPLETE** — Independent subagent review (`verification/independent-review.md`) confirmed `SIMULATION_EVIDENCE_REPAIR_PARTIAL` (`0 BLOCKER, 1 IMPORTANT (retained open on frozen product code), 0 MINOR`).

---

## 3. Exact Raw Log Hashes (Original, Archive, Git Blob, Clean Checkout, New T3)

### 3.1 Original Campaign T3 Raw Logs (`raw/original-t3/*`)

| File | Original Runtime / Corrective Archive / Committed Git Blob / Clean Checkout SHA256 | Historical Normalized Git Blob SHA256 (`d86c7203`) | Bytes |
|---|---|---|---:|
| `attempt1-fail.stdout.log` | `e2074c0897550bda185a6f55ea4113e3a8324263fc7a0cf1e2743228207c03f6` | `2620186c4513cb7a9935f83de6397f5aa03fa38e2de4206ece553391701988e4` | `17,843` |
| `attempt1-fail.stderr.log` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `1,303` |
| `attempt2-pass.stdout.log` | `013f2e784e9fa828a055320468afe7137f080d2447615aec3c3d3970a2138e06` | `8274c4c26793ea001f892ee9c90f339f7fdeb93a43b5c92f3c8e409ca547ae6b` | `18,243` |
| `attempt2-pass.stderr.log` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `332` |

### 3.2 New Browser Reproduction & New Authoritative Full T3 Raw Logs

| Stream Path | Repair Worktree / Committed Git Blob / Clean Checkout SHA256 | Bytes |
|---|---|---:|
| `browser/stdout.log` | `ad82f193b678bf77177141f4e6173245cc14a70b0a1891d53ae1f4c97847cbcd` | `201` |
| `browser/stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `0` |
| `t3/stdout.log` | `d2446b46ba4aba9fae7203cc6be401e820248087430b63b0d7cbe358af0edd33` | `18,257` |
| `t3/stderr.log` | `ccb6bf354a0674eeb1e49df9a880a000b75240079fdb849282bb899d81eeb58c` | `332` |
| `t3/freeze/stdout.log` | `06f3c429768e8b03408400299290363b271fac389b56ec3e780dc7b1a92e9abf` | `93` |
| `t3/freeze/stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `0` |

---

## 4. Browser Reproduction & Cone Visibility Finding Status

- **Browser Reproduction (`browser/validation.json`):** `8` served scenes + `1` refusal, `49` screenshots, `0` console/page errors, `ellipse_scenes: 0` (`ellipse_scope: "BACKEND_ONLY"`).
- **Retained Open IMPORTANT Finding (`FINDING-VISUAL-DEMO6B-AXIAL-SECTION-OCCLUDED`):**
  - In `demo6b-curved-cone-frustum-cut`, `khoi_cone_main` (`ownPixels = 19,195`), `khoi_cone_upper` (`4,711`), `duong_tron_day_cone_main` (`32,620`), and `td_sec_cut` (`4,017`) render visibly, whereas the axial section triangle `td_sec_axial` ($SAB$, `type: "polygon3"`, `render: "polygon"`, `surface_role: "AUXILIARY_SURFACE"`) has `ownPixels = 0` (`own_pixels_positive: false`, `resetDiffFromDefault = 239`).
  - **Root Cause (`frontend/src/simulations/domains/geometry/scene3d-view.tsx`):**
    1. `const thietDien = o.type === "section"` (line 1640) sets `depthTest: !thietDien`, so `polygon_fill:td_sec_axial` (`o.type === "polygon3"`) uses `depthTest: true` and is 100% occluded by the cone's opaque depth prepass `lopChieuSau` (`renderOrder = 5`, lines 314–344, 1526).
    2. `updateCanonicalEdgeVisibility` (line 796) excludes `curved_solid` from `occluders`, causing `updateNonCanonicalVisibility` to return early at line 715 (`if (occluders.length === 0) return;`) and leaving `td_sec_axial`'s boundary lines with `depthTest: true` and no dashed hidden-line pass.
    3. `OrbitControls.enableDamping = true` (line 2108) leaves a `239`-pixel camera reset delta after orbit/zoom/pan, shifting the 41 marginal boundary pixels from the historical capture below the `+14` per-channel threshold.
  - **Disposition:** Retained open without product/test code mutation under `GO_SIMULATION_EVIDENCE_REPAIR_LOCAL_ONLY`.

---

## 5. Remaining Owner Decisions Required

1. **Decision on `FINDING-VISUAL-DEMO6B-AXIAL-SECTION-OCCLUDED`:**
   - Whether to authorize a targeted frontend renderer fix wave in `scene3d-view.tsx` (e.g., treating `polygon3` with `surface_role === "AUXILIARY_SURFACE"` or section polygons inside curved solids with `depthTest: false` / two-pass hidden-line edges and zeroing `OrbitControls` damping on `reset-cam`) before GO MAIN, **or**
   - Whether to integrate the offline campaign with the cone axial-triangle occlusion explicitly documented as a known Scene3D limitation.
2. **Separate GO MAIN Authorization:**
   - No merge or push to `main` is authorized under `GO_SIMULATION_EVIDENCE_REPAIR_LOCAL_ONLY`.

---

## 6. Verification Commands

Run from `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-evidence-repair`:

```powershell
# 1. Verify frozen candidate identity (114 files, 4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68)
D:\Documents\projects\algo-sim\backend\.venv\Scripts\python.exe backend/scripts/freeze_evaluation_candidate.py --verify

# 2. Verify zero product/test changes since 3298b901d2246650535aa4028845ddc2a44892c4
git diff --name-only 3298b901d2246650535aa4028845ddc2a44892c4 HEAD -- backend frontend

# 3. Verify zero historical campaign artifact changes since d86c72031d8fc85cd4eef62d9379cd1690ba1417
git diff --name-only d86c72031d8fc85cd4eef62d9379cd1690ba1417 HEAD -- docs/evaluation/geometry/runs/simulation-coverage-visual-validation

# 4. Run documentation & governance test suites
D:\Documents\projects\algo-sim\backend\.venv\Scripts\python.exe -m pytest -q backend/tests/geometry/test_docs_information_architecture.py backend/tests/geometry/test_thesis_acceptance_matrix.py backend/tests/geometry/test_docs_test_telemetry.py backend/tests/geometry/test_evidence_identity_reconciliation.py
```
