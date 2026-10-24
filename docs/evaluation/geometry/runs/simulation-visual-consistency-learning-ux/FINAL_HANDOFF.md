# FINAL_HANDOFF.md — Simulation Visual Consistency & Learning UX (Two-Session Integrated Campaign)

- **Campaign ID:** `simulation-visual-consistency-learning-ux`
- **Owner Authorization:** `GO_SIMULATION_VISUAL_CONSISTENCY_LEARNING_UX_LOCAL`
- **Execution Mode:** `LOCAL IMPLEMENTATION AND RESEARCH VALIDATION — NO GO MAIN, NO PUSH, NO LIVE LLM CALLS, NO HYBRID PRODUCT ACTIVATION`
- **Overall Verdict:** `SIMULATION_VISUAL_CONSISTENCY_LEARNING_UX_READY_FOR_REVIEW`
- **Evaluation Classification:** `SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND` (`0` live LLM calls)

---

## 1. Branch, Worktree & Commit Identities

| Identity | Value |
|---|---|
| Repository | `D:\Documents\projects\algo-sim` |
| Isolated Campaign Worktree | `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-visual-consistency-learning-ux` |
| Branch | `research/simulation-visual-consistency-learning-ux` |
| Verified Baseline `main` / `origin/main` | `43247c9e9375a3dbf2b5223324a58e6f932ca596` |
| Session 1 Product Commit (P1–P5) | `9341a85771dba79376b46e69ac531c413f507b55` |
| Session 2 Product Commit (P6–P11) | `ec92c8ad81e52dcbf958f25184bea2958fd6be58` |
| Final Product Commit (`perpendicular_witness` TS interface) | `dbef50896c848b93433048b0469f9a78b6a3dbda` |
| Candidate Freeze & Full T3 Target Commit | `f5b6d152370bf91bde798a1b4c6c06c8d4aa2a58` |
| Measured System `tree_hash` (`114` entries) | `91ac973ebc2d42041809d957c55e2829f875c05e649e35b7eee9ebeac1e5d26d` |
| Untouched Sibling Worktrees | Root `D:\Documents\projects\algo-sim` (`research/hybrid-wave3a-volume-reasoning` @ `fe9f5554`), `D:\Documents\projects\algo-sim\.superpowers\worktrees\nl-to-scene3d-e2e-readiness` (`research/nl-to-scene3d-e2e-readiness` @ `25f57e31`) |

---

## 2. Session 1 Summary — Unified Geometry Visual System (P1–P5)

### P1 — Baseline Visual Audit ([`SIMULATION_VISUAL_BASELINE_AUDIT.md`](SIMULATION_VISUAL_BASELINE_AUDIT.md))
- Audited 14 representative geometry families (13 served 3D scenes + 1 fail-closed refusal) in headless Chromium + SwiftShader WebGL across desktop (`1440×900`) and compact (`1024×768`) viewports (`browser-baseline/baseline_audit_receipt.json`, `screenshots/before/*.png`).
- Identified and classified 6 concrete visual and interaction defects (`S1-F1..S1-F6`):
  1. `S1-F1` (`VISUAL_INCONSISTENCY`): Curved solid outer surfaces (`curved_solid`) used saturated violet `MAU.surface` (`0x7c3aed`) instead of the muted slate `MAU.mesh` (`0x647a96`) used by polyhedra.
  2. `S1-F2` (`VISUAL_INCONSISTENCY` / `GEOMETRIC_VISIBILITY_DEFECT`): Base circles (`duong_tron_day*`) and cutting circular/elliptical sections (`td_sec_*`) both rendered as bare amber rings (`MAU.polygon`) without translucent section disks (`section_fill:<id>`) or base vs. section role differentiation.
  3. `S1-F3` (`CAMERA_FRAMING_DEFECT`): `Scene3DPlayer` initialized at static `KHUNG_NHIN_MAC_DINH` (`[4.6, -5.2, 3.8]`), leaving shapes occupying only `10.5%–32.0%` of the canvas (`mean = 20.6%`) before manual reset, and `diemHuuHan` only sampled `anchor`, `apex_or_top`, `rim_point` on curved solids/curves instead of full 3D radial extents.
  4. `S1-F4` (`LABEL_READABILITY_DEFECT`): Undeclared auxiliary points (`A_prime`, `B_prime`, `O_prime`), sphere section radius (`r`), and symbolic given quantities (`R`, `h`) lacked canonical prime/symbolic `notation` in `_run_curved_route`.
  5. `S1-F5` (`INTERACTION_DEFECT`): `HANG_CU_THE` in `pick-target.ts` assigned unspecified types (`curved_solid`, `circle3`, `ellipse3`, `polygon3`) fallback rank `2` (`face`), allowing outer curved solid shells to steal raycast clicks from interior sections (`family9`, `family10`, `family12`).
  6. `S1-F6` (`INFORMATION_HIERARCHY_DEFECT`): Mode A (Simulation) vs. Mode B (Mathematical Analysis) separation was incomplete; `circle3`/`ellipse3` base vs. section categorization was conflated in the object tree.

### P2–P4 — Unified Visual System, Curved Solid Presentation & Camera Framing
- **`frontend/src/simulations/domains/geometry/scene3d-view.tsx`:**
  - Unified `curved_solid` (`cylinder`, `cone`, `ball`) body shell with polyhedral `mesh` solids (`color: nen(MAU.mesh)` `0x647a96`, `opacity: 0.22` default / `0.36` highlighted), reserving `MAU.surface` (`0x7c3aed`) for cutting planes (`plane3`).
  - Differentiated `circle3` and `ellipse3` by `surface_role`: structural base circles (`BASE_REGION` / `CONSTRUCT_BASE` / `duong_tron_day*`) use dark slate ring `net(MAU.canh)` (`0x1e293b`) + subtle slate cap fill (`polygon_fill:${o.id}`, `opacity: 0.12`), whereas cutting sections (`SECTION_REGION`) use warm amber ring `net(MAU.polygon)` (`0xf59e0b`) + warm amber translucent disk (`section_fill:${o.id}`, `opacity: 0.28` / `0.42` highlighted, `renderOrder = THU_TU_TO_THIET_DIEN = 7`, `depthFunc: THREE.AlwaysDepth`, `depthWrite: false`, `LECH_THIET_DIEN`).
  - Auto-framed initial camera on scene load (`daTuKhungRef` invoking `vuaKhungRef.current()`) using `khungNhinSuPham(scene, [w, h])`, raising initial desktop canvas bbox coverage from `20.6%` (`min 10.5%`) to `37.6%` (`min 23.8%`, `max 45.8%`) with `resetDiffFromDefault = 0` across all 13 served scenes.
- **`frontend/src/simulations/domains/geometry/scene3d-model.ts` & `interaction-state.ts`:**
  - Extended `diemHuuHan` to include full 3D bounding extents (`±r` along all axes) for `curved_solid`, `circle3`, and `ellipse3`, while excluding unbounded `plane3`/`line3` and `CONSTRUCT_AUXILIARY_GEOMETRY` helpers from inflating camera zoom.
  - Updated `HANG_MUC` in `interaction-state.ts` so `circle3`/`ellipse3` with `surface_role === "BASE_REGION"` group under `"Đa giác"` while cutting sections group under `"Thiết diện"`.
- **`frontend/src/simulations/domains/geometry/pick-target.ts`:**
  - Added explicit raycast specificity ranks in `HANG_CU_THE`: `point3: 0`, `edge: 1`, `segment3: 1`, `face: 2`, `polygon3: 3`, `circle3: 3`, `ellipse3: 3`, `line3: 3`, `plane3: 3`, `section: 3`, `quantity: 4`, `solid: 5`, `curved_solid: 5`.
- **`backend/app/ai/adapter3_simulation.py`:**
  - Assigned canonical prime symbols (`A'`, `B'`, `O'`), sphere section radius symbol (`r`), symbolic quantity notations (`R`, `h`, `r`), and `surface_role` (`BASE_REGION` vs. `SECTION_REGION`) on curved-route `circle3`/`ellipse3` objects while keeping Route A (`display_names.py`, `scene3d.py`) and all frozen replay hashes (`CA_P1`, `CA_P6`) byte-identical to `main`.
- **Session 1 Handoff:** [`SESSION1_HANDOFF.md`](SESSION1_HANDOFF.md) + `browser-session1/session1_audit_receipt.json` + `screenshots/session1-after/*.png`.

---

## 3. Session 2 Summary — Simulation-First Learning Experience (P6–P11)

### P6–P9 — Mode A (Simulation Default) vs. Mode B (Mathematical Analysis) & 8-Category Semantic Classification
- **`frontend/src/simulations/domains/geometry/scene3d-model.ts`:**
  - Extended `tapKetQuaCuoi` to capture all final requested results (`hybrid.answers`, `solutionAt(scene, cuoi).results` including leaf `MEASURE` readouts, `annotation.role === "result"`, `annotation.category === "result"`, `formation_roles` containing `"FINAL_RESULT"`, `display_group` containing `"target"`, and `kq_vcert*` volume certificate quantities, plus bidirectional `same_as`/`alias_of` propagation).
  - Implemented 8-category semantic classification (`LOAI_NGU_NGHIA_VAT`, `phanLoaiVat`: `GIVEN_OBJECT`, `DERIVED_OBJECT`, `AUXILIARY_OBJECT`, `GIVEN_DIMENSION`, `GIVEN_RELATION`, `DERIVED_MEASUREMENT`, `REQUESTED_RESULT`, `MATHEMATICAL_CERTIFICATE`) and `phanTichToanHocCuaCanh(scene, hybrid, routeD)` reading exclusively from verified backend `Scene3D`, `HybridPreviewView`, and `RouteDSimulationSummary` payloads.
- **`frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx`:**
  - **Mode A (Simulation — Default):** `moBang` initializes to `new Set()` and resets on every `scene` change. All final requested answers (`dapAnAn = tapKetQuaCuoi(day, hybrid)`) are hidden from the 3D canvas (`visibleReadoutBadgesDefault = []`), step readout strip, and object tree (`defaultPanelOpen = false` across all 13 served scenes).
  - **Mode B (Mathematical Analysis — On-Demand):** Accessible via the `"Phân tích toán học"` toolbar toggle (`data-panel="phan-tich"`, rendered only when `coPhanTichToan` is true). Displays `#geo3d-bang-phan-tich` with verified sections for `Kết quả cần tìm` (`REQUESTED_RESULT`), `Đại lượng dẫn xuất trung gian` (`DERIVED_MEASUREMENT`), `Kích thước & dữ kiện đã cho` (`GIVEN_DIMENSION` + `GIVEN_RELATION`), and `Chứng chỉ & quan hệ đã kiểm chứng` (`MATHEMATICAL_CERTIFICATE`), with interactive click-to-highlight binding to `Scene3D` entities.
  - Added semantic category badges (`phanLoaiVat`) to the selected-object inspector card (`.geo3d-the-chon`).

### P10 & P11 — Real-Browser UX Acceptance & Controlled Development Evaluation
- **Real-Browser Acceptance Receipt:** [`browser-after/visual_ux_acceptance_receipt.json`](browser-after/visual_ux_acceptance_receipt.json) + `92` PNG screenshots in [`screenshots/after/`](screenshots/after/).
- **Controlled Development Evaluation (`SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND`):** [`SIMULATION_VISUAL_UX_EVALUATION_REPORT.md`](SIMULATION_VISUAL_UX_EVALUATION_REPORT.md), [`corpus-dev.json`](corpus-dev.json), and [`eval-summary.json`](eval-summary.json):

| Dimension | Metric | Score |
|---|---|---|
| `D1` | Solid & Section Visibility Rate (`ownPixels > 0` default & orbited) | `1.0` (`13/13`) |
| `D2` | Hidden / Visible Edge Correctness Rate | `1.0` (`13/13`) |
| `D3` | Section Distinguishability Rate | `1.0` (`9/9` section scenes) |
| `D4` | Camera Framing Quality (`desktop 23.8%–45.8%`, `compact 20.6%–41.4%`, `0` clipped points, `resetDiff = 0`) | `1.0` (`13/13`) |
| `D5` | Label Readability & Non-Overlap (`collision_rate = 0.0`, `0` internal snake_case leaks) | `1.0` (`13/13`) |
| `D6` | Selection & Highlight Clarity (`pickHitMatchesTarget`, positive select/isolate pixel diffs) | `1.0` (`13/13`) |
| `D7` | Step Progression Clarity (`stepCount >= 2`, `stepProgressionDiffPixels > 0`) | `1.0` (`13/13`) |
| `D8` | Default Simulation Mode Compliance (`defaultPanelOpen = false`, `visibleReadoutBadgesDefault = []`) | `1.0` (`13/13`) |
| `D9` | Mathematical Analysis Mode Accuracy (`analysisToggleDiff > 0`, verified results & certificates) | `1.0` (`13/13`) |
| `D10` | Safe Refusal Clarity (`family13_invalid_geometry_refusal` `served = false`, `scene3d = null`, `<UnsupportedNotice>`) | `1.0` (`1/1`) |

---

## 4. P12 Independent Review & P13 Authoritative Full T3 Gate

- **Independent Review ([`INDEPENDENT_REVIEW.md`](INDEPENDENT_REVIEW.md)):**
  - Reviewer Subagent: `4683a88d-cbb7-40f1-a0e5-9b07575c1851`
  - Verdict: **`INDEPENDENT_REVIEW_PASS`** (`0 BLOCKER, 0 IMPORTANT, 0 MINOR`) across all 6 review checklist items (no hardcoded cases, no fake Scene3D or fake answers, no answer leakage in Mode A, no mathematical authority moved to frontend, unified visual semantics across polyhedra and curved solids, and preserved governance invariants) for `ec92c8ad81e52dcbf958f25184bea2958fd6be58` and the TypeScript `perpendicular_witness` interface delta `dbef50896c848b93433048b0469f9a78b6a3dbda`.
- **Authoritative Full T3 Gate ([`t3/validation.json`](t3/validation.json), [`t3/execution.json`](t3/execution.json), [`t3/freeze/execution.json`](t3/freeze/execution.json)):**
  - Executed on clean detached worktree at `f5b6d152370bf91bde798a1b4c6c06c8d4aa2a58` (`product_commit_sha = dbef50896c848b93433048b0469f9a78b6a3dbda`, `measured_system.tree_hash = 91ac973ebc2d42041809d957c55e2829f875c05e649e35b7eee9ebeac1e5d26d` across `114` entries):
    - **Backend `pytest`:** `PASS` (`11,442 passed, 1 skipped, 2 deselected, 9 xfailed in 479.01s`)
    - **Frontend `vitest`:** `PASS` (`74 test files, 1,166 tests passed in 7.81s`)
    - **`tsc -b && vite build`:** `PASS` (`6.8s`, `built in 2.58s`)
    - **Thesis demo replay:** `PASS` (`5/5` demo cases + `1/1` reduced chain)
    - **Demo crash surface:** `PASS` (`6/6` boundary cases, `0` escaped 500s)
    - **Overall Verdict:** **`FULL_PRODUCT_GATE_PASS`** (`500.0s`, `exit_code = 0`, `snapshot_dirty_after = []`)
    - **Post-T3 Candidate Freeze Verification:** **`MATCH`** (`exit_code = 0`, `Candidate khớp bản đã đóng băng (mã sản phẩm: 114 file, 91ac973ebc2d4204…).`)
    - *(Note: Attempt 1 T3 logs where `tsc -b` caught the missing optional `perpendicular_witness` fields on `QuantityAnnotation["witness"]` are transparently preserved in [`t3/attempt1-fail/`](t3/attempt1-fail/).)*

---

## 5. Governance Invariants & Remaining Architectural Boundaries

- `DEFAULT_MODE = LLM_ONLY` (`backend/app/simulation/geometry_compiler/routing.py`)
- `RESPONSE_CONTRACT = flat` & `hybrid_preview_enabled = False` (`backend/app/ai/pipeline.py`)
- `HYBRID_PRODUCT_ENABLEMENT = NO-GO`
- `ALLOW_LIVE_AI = 0` (`0` live provider calls)
- `CACHE_VERSION = "127"` (`NO_BUMP`)
- **Truthful Capability Boundaries Preserved:**
  - Residual polyhedral/frustum 3D mesh `E` remains `NOT_IMPLEMENTED` (residual volumes are certified scalar goals without fabricated residual 3D meshes).
  - Standalone `cone_frustum` remains `BLOCKED_BY_KERNEL`.
  - Oblique cone `ellipse3` browser validation remains `BACKEND_ONLY` (oblique circular cylinder `ellipse3` section `family10_cylinder_ellipse_cut` is verified in real Chromium WebGL with `ownPixels = 9,233`).
