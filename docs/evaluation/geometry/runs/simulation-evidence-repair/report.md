# Simulation evidence repair — local-only execution (`SIMULATION_EVIDENCE_REPAIR_W01`)

- **Authorization:** `GO_SIMULATION_EVIDENCE_REPAIR_LOCAL_ONLY`
- **Status / Verdict:** `SIMULATION_EVIDENCE_REPAIR_PARTIAL` (all raw-byte portability, scope-claim, and fresh Full T3 requirements completed and verified; one **IMPORTANT** browser/renderer visibility finding on `demo6b-curved-cone-frustum-cut` `td_sec_axial` `ownPixels = 0` remains open because product code is frozen in this repair scope)
- **Branch:** `research/simulation-evidence-repair` (branched from verified campaign source `d86c72031d8fc85cd4eef62d9379cd1690ba1417`)
- **Product commit (frozen, unchanged):** `3298b901d2246650535aa4028845ddc2a44892c4`
- **Frozen candidate commit:** `5f4ee58c48011e9e5d38d3209f7c97250032a976`
- **Measured system SHA256:** `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68` (`114` files)
- **Baseline `main` / `origin/main`:** `bd8d6a9dc3acc9a4204b616379001270bb6d39f9` (untouched; no merge, no push)
- **Live provider calls:** `0` (`ALLOW_LIVE_AI = 0`)

---

## 1. Historical Preservation & Three-Layer Raw T3 Identity Model

This additive correction preserves all 79 original campaign artifacts in `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/` byte-for-byte ([`historical-preservation.json`](historical-preservation.json)), as well as the reconciliation package in [`../simulation-evidence-reconciliation/report.md`](../simulation-evidence-reconciliation/report.md) and its backup under `preserved/verify-simulation-go-main-reconciliation/`. Zero files in `backend/` or `frontend/` were modified (`git diff 3298b901d2246650535aa4028845ddc2a44892c4 -- backend frontend` is empty).

The four original Full T3 raw logs from `simulation-coverage-visual-validation` are archived under `raw/original-t3/` with path-scoped `-text -diff` in [`.gitattributes`](.gitattributes), separating three distinct identities in [`original-raw-manifest.json`](original-raw-manifest.json) and verifying 4-way byte equality (`ORIGINAL_RUNTIME_BYTES = CORRECTIVE_ARCHIVE_BYTES = GIT_BLOB_BYTES = CLEAN_CHECKOUT_ARCHIVE_BYTES`) in [`archive-integrity.json`](archive-integrity.json):

| Stream | `ORIGINAL_RUNTIME_RAW_BYTES` (`D:\...\simulation-coverage-visual-validation`) | `HISTORICAL_NORMALIZED_GIT_BLOB` (`d86c7203:...`) | `CORRECTIVE_RAW_ARCHIVE` & `CLEAN_CHECKOUT` (`raw/original-t3/*`) | Bytes |
|---|---|---|---|---:|
| `attempt1-fail.stdout.log` | `e2074c0897550bda185a6f55ea4113e3a8324263fc7a0cf1e2743228207c03f6` | `2620186c4513cb7a9935f83de6397f5aa03fa38e2de4206ece553391701988e4` | `e2074c0897550bda185a6f55ea4113e3a8324263fc7a0cf1e2743228207c03f6` | `17,843` |
| `attempt1-fail.stderr.log` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `1,303` |
| `attempt2-pass.stdout.log` | `013f2e784e9fa828a055320468afe7137f080d2447615aec3c3d3970a2138e06` | `8274c4c26793ea001f892ee9c90f339f7fdeb93a43b5c92f3c8e409ca547ae6b` | `013f2e784e9fa828a055320468afe7137f080d2447615aec3c3d3970a2138e06` | `18,243` |
| `attempt2-pass.stderr.log` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `332` |

---

## 2. Scope & Capability Correction

Current scope authority is [`capability-matrix.md`](capability-matrix.md):

1. **Residual polyhedral solid mesh (`E`) is `NOT_IMPLEMENTED`:**
   - **A** (original pyramid/solid mesh), **B** (constructed upper sub-solid pyramid), **C** (exact cutting polygon/plane), and **D** (certified scalar residual volume) are supported and demonstrated.
   - **E** (an independently constructed residual polyhedral or frustum mesh in `Scene3D`) is **`NOT_IMPLEMENTED`**. Neither `DerivedSubSolidSpec` nor `frustum_like` exists in `backend/app`; `SimulationGoalSpec(goal_kind="construct_derived_solid")` compiles `fn="pyramid"` in `adapter3_simulation.py::_compile_derived_solids_and_goals`.
2. **Standalone `cone_frustum` remains `BLOCKED_BY_KERNEL`:**
   - Only scalar residual volume certification (`parent_cone - upper_cone`) is supported for a cone cut by a plane parallel to its base (`demo6b`, `pos_05`).
3. **Authoritative 9-demo inventory (`demos/demo1..demo7*.json`) and `BACKEND_ONLY` ellipse browser scope:**
   - The 9-demo browser suite exercises 8 positive served scenes (`demo1`..`demo5`, `demo6a`, `demo6b`, `demo6c`) and 1 fail-closed refusal (`demo7`, plane $z=7$ outside sphere $R=5$).
   - Oblique cylinder/cone elliptic sections (`ellipse3`) are verified in backend positive corpus cases (`pos_09`, `pos_10`) and frontend unit/component tests (`simulation-coverage-fixes.test.tsx`), but are **`BACKEND_ONLY`** with respect to the 9-demo browser suite.
4. **Offline simulation vs live NL E2E:**
   - Prepared `TypedFactNext` payloads establish `OFFLINE_SIMULATION_E2E` only, not `LIVE_NATURAL_LANGUAGE_PRODUCT_E2E`.

---

## 3. New Browser Reproduction & Phase C Cone Visibility Root-Cause Analysis

A single fresh browser reproduction (`NEW_BROWSER_REPRODUCTION_NOT_ORIGINAL`) was executed on the clean `d86c7203` snapshot via `capture.py` ([`browser/invocation.json`](browser/invocation.json), [`browser/execution.json`](browser/execution.json), [`browser/validation.json`](browser/validation.json), [`browser/visual-receipt.json`](browser/visual-receipt.json)):

- **Exit code:** `0` (`timed_out: false`, `console_errors: 0`, `page_errors: 0`)
- **Streams:** `browser/stdout.log` (`201` bytes, SHA256 `ad82f193b678bf77177141f4e6173245cc14a70b0a1891d53ae1f4c97847cbcd`), `browser/stderr.log` (`0` bytes, SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`)
- **Outputs:** `8` served scenes + `1` refusal, `49` PNG screenshots under `browser/screenshots/`.
- **7 of 8 positive demos (`demo1`..`demo5`, `demo6a`, `demo6c`) and `demo7` refusal:** passed every visual check (`all_checks_passed: true`, `own_pixels_positive: true`, `camera_changes: true`, `camera_settled: true`, `selection_and_timeline: true`, `labels: true`).
- **Retained IMPORTANT visual finding on `demo6b-curved-cone-frustum-cut`:**
  - `khoi_cone_main`: `ownPixels = 19,195` (historical `19,195`) — **VISIBLE**
  - `khoi_cone_upper`: `ownPixels = 4,711` (historical `4,711`) — **VISIBLE**
  - `duong_tron_day_cone_main`: `ownPixels = 32,620` (historical `32,620`) — **VISIBLE**
  - `td_sec_cut` (parallel circular cut at $z=2$): `ownPixels = 4,017` (historical `4,017`) — **VISIBLE**
  - `td_sec_axial` (axial section triangle $SAB$, `type: "polygon3"`, `render: "polygon"`, `surface_role: "AUXILIARY_SURFACE"`): **`ownPixels = 0`** (historical `41`) — **FAIL (`own_pixels_positive: false`)**
  - Camera metrics: `initialSettled = true`, `orbitSettled = true`, `orbitDiffPixels = 20,762`, `zoomDiffPixels = 19,432`, `panDiffPixels = 32,641`, `resetDiffFromDefault = 239` (historical `0`).

### Root-Cause Analysis of `demo6b` `td_sec_axial` (`ownPixels = 0`) and `resetDiffFromDefault = 239`

1. **Screenshot & Scene Verification:**
   - `browser/screenshots/demo6b-curved-cone-frustum-cut_default.png` is byte-for-byte identical to the historical `simulation-coverage-visual-validation/screenshots/demo6b-curved-cone-frustum-cut_default.png` (SHA256 `d2c35dbfc5ddc2d2a8498c4b8c6cbedf31f1642a2d1f3eb8c8a985027f07567e`).
   - In both screenshots, the main cone (`khoi_cone_main`), derived upper cone (`khoi_cone_upper`), base circle (`duong_tron_day_cone_main`), and parallel circular cut (`td_sec_cut`) are clearly visible, along with vertex labels $O, S, A, B, O_1, A_1$ and front generator $SA$.
   - What has `ownPixels = 0` when toggled alone by `measureOwnPixels()` (`run_browser_audit.mjs` lines 163–192, threshold `max(|dR|,|dG|,|dB|) > 14`) is the axial triangle `td_sec_axial` ($S(0,0,4), A(3,0,0), B(-3,0,0)$).
2. **Exact Code Root Cause in `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (Genuine Renderer Occlusion Defect):**
   - **Interior fill occlusion (`scene3d-view.tsx` lines 1640, 1680–1696):**
     - `const thietDien = o.type === "section";` (line 1640).
     - At lines 1680–1695, the renderer comments that a cutting section inside a solid is occluded by `lopChieuSau` (the solid's opaque depth prepass at `renderOrder = 5`, lines 314–344, 1526) unless `depthTest: false` is set. However, it sets `depthTest: !thietDien`, which only disables `depthTest` for `o.type === "section"`, **not** for `o.type === "polygon3"`!
     - Because `adapter3_simulation.py` emits axial sections on cylinders/cones via `construct_polygon` (`type: "polygon3"`, `render: "polygon"`, `surface_role: "AUXILIARY_SURFACE"`), `thietDien` is `false`, so `polygon_fill:td_sec_axial` uses `depthTest: true`. Because every interior point of the axial triangle $SAB$ lies inside the cone behind its front lateral surface, the cone's opaque depth prepass (`lopChieuSau`, `colorWrite: false, depthWrite: true, depthTest: true, side: DoubleSide`, `renderOrder = 5`) writes nearer depth values over 100% of $SAB$'s interior before the transparent fill renders (`renderOrder = 16`). Thus 100% of `polygon_fill:td_sec_axial` fails the GPU depth test.
   - **Boundary loop occlusion (`scene3d-view.tsx` lines 712–715, 795–799, 1642–1665):**
     - Unlike `segment3` (which uses `duongHaiLuot` to create both a front `LessEqualDepth` solid line and a back `GreaterDepth` dashed line), `render === "polygon"` creates a single `THREE.LineBasicMaterial` with `depthTest: true` and no `GreaterDepth` hidden-line pass (lines 1644–1665), relying on `updateNonCanonicalVisibility` (line 712) to replace occluded segments with `canonicalEdgeMaterial` (`depthTest: false`).
     - However, `updateCanonicalEdgeVisibility` (line 796) only collects `occluders` from polyhedral solids (`child.userData?.solidSceneObject`), excluding `curved_solid`. In `demo6b`, `occluders` is empty (`occluders.length === 0`), so `updateNonCanonicalVisibility` returns early at line 715 (`if (occluders.length === 0) return;`).
     - Consequently, the border of `td_sec_axial` retains `depthTest: true` with no dashed hidden pass. Edge $SA$ is already drawn by the separate object `duong_sinh_S_A` (`segment3`), while the base diameter $AB$ ($z=0$) and back generator $SB$ (to $B(-3,0,0)$) lie behind the front half of the cone's opaque depth prepass from camera `(8, 3, 6)`. Hiding `td_sec_axial` alone therefore changes `0` pixels above threshold (`ownPixels = 0`).
   - **Why `resetDiffFromDefault = 239` occurred before `measureOwnPixels()`:**
     - `OrbitControls` is configured with `enableDamping = true` (`dampingFactor = 0.08`, line 2108). After `orbit`, `zoom`, and `pan` in `run_browser_audit.mjs`, clicking `[data-testid="reset-cam"]` increments `fitToken` on the same mounted controls instance, leaving a tiny sub-degree residual camera velocity (`239 / 880,640 = 0.027%` of canvas pixels). Because `measureOwnPixels()` runs immediately after `reset-cam` on that slightly shifted camera pose, the `41` marginal boundary pixels at $A$/$B$ that barely cleared threshold `+14` in the historical run fell below threshold in the new reproduction (`0` pixels).
3. **Minimal Reproducible Case & Governance Consequence:**
   - **Minimal Reproducer:** Render `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/demos/demo6b-curved-cone-frustum-cut.json` in `Scene3DView` (`1280×900`, default camera `(8, 3, 6)`), and toggle `obj.visible` on `[userData.sceneObjectId="td_sec_axial"]`: `countDiffPixels(basePng, hiddenPng) == 0` after `reset-cam`.
   - **Governance Handling:** Under `GO_SIMULATION_EVIDENCE_REPAIR_LOCAL_ONLY`, product code (`scene3d-view.tsx`) and test/harness code (`run_browser_audit.mjs`) are frozen and must not be modified. This finding is therefore retained truthfully as an open **IMPORTANT** visual/renderer defect requiring a separate owner-authorized product fix scope.

---

## 4. New Authoritative Full T3 & Post-T3 Candidate Freeze Verification

One fresh authoritative Full T3 gate (`NEW_AUTHORITATIVE_FULL_T3_NOT_HISTORICAL`) was executed in the clean detached worktree `D:\Documents\projects\algo-sim\.superpowers\worktrees\verify-simulation-evidence-repair` at commit `48c34d886579948aa9c28019dd0559fd100f6dcd` via `capture.py` ([`t3/invocation.json`](t3/invocation.json), [`t3/execution.json`](t3/execution.json), [`t3/validation.json`](t3/validation.json)):

- **Started / Finished (UTC):** `2026-10-21T07:35:16.089954+00:00` $\to$ `2026-10-21T07:45:27.992788+00:00` (`610.9s`)
- **Exit code / Verdict:** `0` (`timed_out: false`, **`FULL_PRODUCT_GATE_PASS`**)
- **Raw Stream Hashes (`RAW_BYTES_SHA256`):**
  - `t3/stdout.log`: `18,257` bytes, SHA256 `d2446b46ba4aba9fae7203cc6be401e820248087430b63b0d7cbe358af0edd33`
  - `t3/stderr.log`: `332` bytes, SHA256 `ccb6bf354a0674eeb1e49df9a880a000b75240079fdb849282bb899d81eeb58c`
- **Sub-gate Summary:**
  1. **Backend pytest:** `11,439 passed, 1 skipped, 2 deselected, 9 xfailed, 0 failed` (`595.4s`)
  2. **Frontend Vitest:** `72 passed (72)` files, `1,154 passed (1,154)` tests (`8.5s`)
  3. **Typecheck + production build (`tsc -b && vite build`):** `PASS` (`5.9s`)
  4. **Thesis demo replay:** `5/5` (`DEMO_REPLAY_PASS 5/5`, `REDUCED_CHAIN_CASES 1/1`, `0.6s`)
  5. **Demo crash boundary:** `6/6` (`NÉM RA NGOÀI (=500) 0`, `0.4s`)
- **Post-T3 Candidate Freeze Verification (`t3/freeze/execution.json`):**
  - Command: `python backend/scripts/freeze_evaluation_candidate.py --verify`
  - Exit code: `0` (`Candidate khớp bản đã đóng băng (mã sản phẩm: 114 file, 4d11a91790422b95…)`)
  - `t3/freeze/stdout.log`: `93` bytes, SHA256 `06f3c429768e8b03408400299290363b271fac389b56ec3e780dc7b1a92e9abf`
  - `t3/freeze/stderr.log`: `0` bytes, SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- **4-Way Clean-Checkout Archive Verification (`archive-integrity.json`):**
  - All 4 original T3 logs (`raw/original-t3/*`), all 57 browser reproduction artifacts (`browser/**`), and all 11 new T3/freeze artifacts (`t3/**`) match byte-for-byte between the repair worktree, committed Git blobs, and the clean detached checkout `verify-simulation-evidence-repair`.

---

## 5. Governance & Safety Invariants

- `DEFAULT_MODE = LLM_ONLY`
- `RESPONSE_CONTRACT = flat`
- `HYBRID_PRODUCT_ENABLEMENT = NO-GO`
- `ALLOW_LIVE_AI = 0` (`LIVE_PROVIDER_CALLS = 0`)
- `CACHE_VERSION = 127` (`NO_BUMP`)
- Root checkout (`D:\Documents\projects\algo-sim`), `simulation-coverage-visual-validation`, and `verify-simulation-go-main` preserved untouched; no merge to `main`, no push, no branch or worktree deletion.
