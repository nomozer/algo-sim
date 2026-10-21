# Independent Read-Only Review Report — `SIMULATION_EVIDENCE_REPAIR_W01`

- **Reviewer:** Independent Read-Only Subagent (`4760b297-e2f8-4d0e-b89c-a73ff2e69cc7`)
- **Reviewed Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-evidence-repair` (`research/simulation-evidence-repair`)
- **Clean Detached Verification Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\verify-simulation-evidence-repair` (`5c4a6ff90377add14a375b42436012156de2b143`)
- **Source / Product / Candidate Commits:** `d86c72031d8fc85cd4eef62d9379cd1690ba1417` / `3298b901d2246650535aa4028845ddc2a44892c4` / `5f4ee58c48011e9e5d38d3209f7c97250032a976` (`4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` across `114` files)
- **Review Mode:** Read-only (`ALLOW_LIVE_AI = 0`, `0` live model/provider calls, `0` file mutations)
- **Overall Campaign Status Confirmed:** `SIMULATION_EVIDENCE_REPAIR_PARTIAL`
- **Finding Counts:** `0 BLOCKER, 1 IMPORTANT (retained open on frozen product code), 0 MINOR`

---

## Checklist Verification

### 1. Raw-Byte Portability & Historical Preservation — **VERIFIED (`PASS`)**
- **Path-scoped binary/raw attributes (`.gitattributes`):** Marks `raw/** -text -diff`, `browser/** -text whitespace=cr-at-eol`, `browser/screenshots/** -text -diff`, `t3/** -text whitespace=cr-at-eol`, `checks/** -text whitespace=cr-at-eol`, `preserved/** -text -diff`, and `*.log -text -diff`.
- **4-Way Raw T3 Byte Identity (`original-raw-manifest.json`, `archive-integrity.json`):** All 4 original T3 logs under `raw/original-t3/` satisfy `ORIGINAL_RUNTIME_BYTES == CORRECTIVE_ARCHIVE_BYTES == GIT_BLOB_BYTES == CLEAN_CHECKOUT_ARCHIVE_BYTES` while explicitly distinguishing `historical_normalized_git_blob_sha256` on the two stdout logs:
  - `attempt1-fail.stdout.log`: `e2074c0897550bda185a6f55ea4113e3a8324263fc7a0cf1e2743228207c03f6` (historical normalized blob `2620186c4513cb7a9935f83de6397f5aa03fa38e2de4206ece553391701988e4`)
  - `attempt1-fail.stderr.log`: `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5`
  - `attempt2-pass.stdout.log`: `013f2e784e9fa828a055320468afe7137f080d2447615aec3c3d3970a2138e06` (historical normalized blob `8274c4c26793ea001f892ee9c90f339f7fdeb93a43b5c92f3c8e409ca547ae6b`)
  - `attempt2-pass.stderr.log`: `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0`
- **Historical & Product Immutability (`historical-preservation.json`, `integrity-preflight.json`, `git diff`):**
  - All 79 files in `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/` are untouched (`git diff --name-only d86c72031d8fc85cd4eef62d9379cd1690ba1417 -- docs/evaluation/geometry/runs/simulation-coverage-visual-validation` is empty).
  - Product and test trees (`backend/`, `frontend/`) are completely untouched relative to `3298b901d2246650535aa4028845ddc2a44892c4` (`git diff --name-only 3298b901d2246650535aa4028845ddc2a44892c4 -- backend frontend` is empty).

### 2. Truthful Scope & Capability Correction — **VERIFIED (`PASS`)**
- Across `capability-matrix.md`, `report.md`, `docs/CURRENT_STATE.md` (lines 1–20), `docs/EVIDENCE_INDEX.md` (lines 1–40), and `docs/ROADMAP.md` (lines 1–20):
  - **Residual polyhedral/frustum mesh `E` is `NOT_IMPLEMENTED`:** Explicitly separates **A** (original solid mesh), **B** (constructed upper sub-solid pyramid), **C** (exact cutting polygon/plane), and **D** (certified scalar residual volume) from **E** (independently constructed residual polyhedral/frustum mesh). Confirms `DerivedSubSolidSpec` and `frustum_like` do not exist in `backend/app` and `SimulationGoalSpec(goal_kind="construct_derived_solid")` compiles `fn="pyramid"`.
  - **Standalone `cone_frustum` is `BLOCKED_BY_KERNEL`:** Only scalar residual volume (`parent_cone - upper_cone`) is supported for a parallel cone cut.
  - **Oblique cylinder/cone ellipse coverage is `BACKEND_ONLY` for browser validation:** The 9-demo browser inventory (`demos/demo1..demo7*.json`) has 8 positive served scenes (`demo1`..`demo5`, `demo6a`, `demo6b`, `demo6c`) and 1 fail-closed refusal (`demo7`), with `ellipse_scenes: 0` (`pos_09` and `pos_10` are backend/unit-tested only).
  - **Offline vs Live E2E:** Prepared `TypedFactNext` payloads are accurately scoped to `OFFLINE_SIMULATION_E2E`, not `LIVE_NATURAL_LANGUAGE_PRODUCT_E2E`.

### 3. New Browser Reproduction & Cone Visibility Finding — **VERIFIED (`PASS` — 1 IMPORTANT Retained Open)**
- **Explicit Provenance Labeling:** `browser/invocation.json` (`"run_kind": "NEW_BROWSER_REPRODUCTION_NOT_ORIGINAL"`), `browser/execution.json` (`"run_kind": "NEW_BROWSER_REPRODUCTION_NOT_ORIGINAL"`), and `browser/validation.json` (`"group": "NEW_BROWSER_REPRODUCTION_NOT_ORIGINAL"`, `"status": "REPRODUCTION_CAPTURE_COMPLETE_VISUAL_FINDING_OPEN"`) clearly label the run as a new reproduction (8 served + 1 refusal, 49 screenshots, 0 console/page errors).
- **Truthful Retention & Root-Cause Explanation (`report.md` §3, `run.json`, `browser/validation.json` lines 1008–1067, 1185–1196):**
  - Retains the open **IMPORTANT** finding `FINDING-VISUAL-DEMO6B-AXIAL-SECTION-OCCLUDED` on `demo6b-curved-cone-frustum-cut` `td_sec_axial` (`ownPixels = 0` vs historical `41`, `resetDiffFromDefault = 239`, `own_pixels_positive: false`, `all_checks_passed: false`), while `khoi_cone_main` (`19,195`), `khoi_cone_upper` (`4,711`), `duong_tron_day_cone_main` (`32,620`), and `td_sec_cut` (`4,017`) remain visible.
  - Accurately identifies the dual renderer occlusion mechanism in `frontend/src/simulations/domains/geometry/scene3d-view.tsx`:
    1. `const thietDien = o.type === "section"` (line 1640) sets `depthTest: !thietDien`, leaving `polygon_fill:td_sec_axial` (`o.type === "polygon3"`) with `depthTest: true` behind the cone's `curved_solid` `lopChieuSau` opaque depth prepass (`renderOrder = 5`), occluding 100% of the interior fill.
    2. `updateCanonicalEdgeVisibility` (line 796) excludes `curved_solid` from `occluders`, causing `updateNonCanonicalVisibility` to return early at line 715 (`if (occluders.length === 0) return;`) and leaving `td_sec_axial`'s boundary lines without a dashed hidden-line pass.
    3. `OrbitControls` damping leaves a `239`-pixel residual camera pose difference after `reset-cam`, shifting the 41 marginal boundary pixels from the historical capture below the `+14` per-channel diff threshold (`ownPixels = 0`).
  - Confirmed that neither frozen product code (`scene3d-view.tsx`) nor harness code (`run_browser_audit.mjs`) was mutated.

### 4. New Authoritative Full T3 & Post-T3 Freeze Verification — **VERIFIED (`PASS`)**
- **Single Clean Full T3 Pass (`t3/invocation.json`, `t3/execution.json`, `t3/validation.json`):**
  - Labeled `NEW_AUTHORITATIVE_FULL_T3_NOT_HISTORICAL`, executed in clean detached worktree `verify-simulation-evidence-repair` at `48c34d886579948aa9c28019dd0559fd100f6dcd` (`attempt_limit: 1`, `exit_code: 0`, `timed_out: false`, `duration_seconds: 610.9`, verdict `FULL_PRODUCT_GATE_PASS`, `snapshot_dirty_after: []`).
  - Sub-gates: Backend pytest `11,439 passed, 1 skipped, 2 deselected, 9 xfailed, 0 failed` (`595.4s`); Frontend Vitest `72` files / `1,154 passed, 0 failed` (`8.5s`); `tsc -b && vite build` `PASS` (`5.9s`); Thesis demo replay `5/5` (`REDUCED_CHAIN_CASES 1/1`, `0.6s`); Demo crash boundary `6/6` (`escaped_500: 0`, `0.4s`).
  - Raw stream hashes (`RAW_BYTES_SHA256`): `t3/stdout.log` (`18,257` bytes, `d2446b46ba4aba9fae7203cc6be401e820248087430b63b0d7cbe358af0edd33`), `t3/stderr.log` (`332` bytes, `ccb6bf354a0674eeb1e49df9a880a000b75240079fdb849282bb899d81eeb58c`).
- **Post-T3 Freeze Verification (`t3/freeze/execution.json`, `t3/validation.json`):**
  - `python backend/scripts/freeze_evaluation_candidate.py --verify` exited `0` (`status: "MATCH"`, `114` files, `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`; `t3/freeze/stdout.log` `93` bytes, SHA256 `06f3c429768e8b03408400299290363b271fac389b56ec3e780dc7b1a92e9abf`).
- **Clean-Checkout Archive Integrity (`archive-integrity.json`):**
  - `"all_equal": true` across all 4 original T3 logs, all 57 browser artifacts, and all 11 new T3/freeze artifacts between committed Git blobs and clean detached checkout `5c4a6ff90377add14a375b42436012156de2b143`.

---

## 5. Overall Review Verdict

- **Artifact Completeness & Truthfulness:** **CONFIRMED.** Every evidence-repair artifact, hash manifest, capability matrix row, and top-level state/index/roadmap entry is internally consistent, byte-verified across Git blobs and clean detached checkout, and preserves historical artifacts and frozen product/test code untouched.
- **Retained Open Finding:** `1 IMPORTANT` (`FINDING-VISUAL-DEMO6B-AXIAL-SECTION-OCCLUDED`: `demo6b-curved-cone-frustum-cut` `td_sec_axial` `ownPixels = 0`, `resetDiffFromDefault = 239` on frozen `scene3d-view.tsx`).
- **Campaign Verdict:** **`SIMULATION_EVIDENCE_REPAIR_PARTIAL` (`0 BLOCKER, 1 IMPORTANT (retained open on frozen product code), 0 MINOR`)**.
