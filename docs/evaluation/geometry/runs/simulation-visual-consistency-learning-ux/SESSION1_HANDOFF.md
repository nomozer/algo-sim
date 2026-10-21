# SESSION 1 HANDOFF — UNIFIED GEOMETRY VISUAL SYSTEM (`P1–P5`)

- **Run Slug:** `simulation-visual-consistency-learning-ux`
- **Branch:** `research/simulation-visual-consistency-learning-ux`
- **Base `main` SHA:** `43247c9e9375a3dbf2b5223324a58e6f932ca596`
- **Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\simulation-visual-consistency-learning-ux`
- **Execution Mode:** Local deterministic + real-browser headless Chromium WebGL (`0` live LLM calls)

---

## 1. Actual Product Changes Implemented (`P2–P4`)

1. **Unified Solid Surface Palette (`P2.A` / `P3`, Resolves `VI-01`):**
   - Updated `buildObject3D` in `frontend/src/simulations/domains/geometry/scene3d-view.tsx` so `curved_solid` (`cylinder`, `cone`, `ball`) uses the same muted slate-blue surface token `nen(MAU.mesh)` (`0x647a96`) and default transparency `0.22` (`0.36` when highlighted) as polyhedral `mesh` solids (`0x647a96`, `opacity: 0.22`), reserving `MAU.surface` (`0x7c3aed` purple) strictly for cutting planes (`plane3`).

2. **Unified Section vs Base Circle Visual Semantics (`P2.B–D` / `P3`, Resolves `VI-02` & `VI-03`):**
   - Updated `_attach_topology` in `backend/app/simulation/semantic_program/scene3d.py` to tag structural base circles (`duong_tron_day*` / `CONSTRUCT_BASE`) with `surface_role = "BASE_REGION"` and cutting circular/elliptical sections (`circle3` / `ellipse3`) with `surface_role = "SECTION_REGION"`.
   - Updated `o.render === "circle"` in `frontend/src/simulations/domains/geometry/scene3d-view.tsx`:
     - Structural base circles (`BASE_REGION` / `CONSTRUCT_BASE` / `duong_tron_day*`) render with dark slate boundary ring `net(MAU.canh)` (`0x1e293b`, solid front / dashed hidden back) and subtle slate cap fill (`polygon_fill:${id}`, `nen(MAU.mesh)`, `opacity: 0.12`).
     - Verified cutting circular sections (`SECTION_REGION`) render with warm amber perimeter ring `net(MAU.polygon)` (`0xf59e0b`, solid front / dashed hidden back) and translucent warm amber interior disk `section_fill:${id}` (`nen(MAU.polygon)`, `opacity: 0.28`, `renderOrder: THU_TU_TO_THIET_DIEN = 7`, `depthFunc: THREE.AlwaysDepth`, `depthWrite: false`, `LECH_THIET_DIEN`).
   - Updated `o.render === "ellipse"` in `frontend/src/simulations/domains/geometry/scene3d-view.tsx`:
     - Renders with warm amber perimeter ring `net(MAU.polygon)` (`0xf59e0b`, solid front / dashed hidden back) and translucent warm amber interior disk `section_fill:${id}` (`nen(MAU.polygon)`, `opacity: 0.28`, `renderOrder: THU_TU_TO_THIET_DIEN = 7`, `depthFunc: THREE.AlwaysDepth`, `depthWrite: false`, `LECH_THIET_DIEN`).
   - Updated `_hangMuc` in `frontend/src/simulations/domains/geometry/interaction-state.ts` so structural base circles (`BASE_REGION`) are grouped under `"Đa giác"` while cutting `circle3` / `ellipse3` sections are grouped under `"Thiết diện"`.

3. **Camera Framing & Object-Aware Bounds (`P4`, Resolves `CF-01` & `CF-02`):**
   - Updated `vuaKhungRef.current` in `frontend/src/simulations/domains/geometry/scene3d-view.tsx` so scenes without polyhedral edges (`ct.canh.length === 0`, i.e. curved solids) also use 2D projection fitting `khungNhinSuPham(diem, [], [], cam.fov, w / h, huong)` along the canonical viewing direction `[8, 5, 6]` instead of falling back to the loose bounding-sphere fit `khungNhinVua`.
   - Updated `diemHuuHan` in `frontend/src/simulations/domains/geometry/scene3d-model.ts` so `curved_kind === "cone"` expands `±r` only at the base center `anchor` and pushes the apex `dinh` as a single point (removing horizontal bounding-box bloat at the cone apex), and `o.render === "circle"` expands `±r` perpendicular to `normal` around `center`.

4. **Raycast Selection Specificity & Curved-Solid Display Names (`P2.F–G`, Resolves `ID-01` & `LR-01`):**
   - Updated `HANG_CU_THE` in `frontend/src/simulations/domains/geometry/pick-target.ts` to rank `segment3: 1`, `circle3: 3`, `ellipse3: 3` ahead of outer `curved_solid: 5` shells.
   - Updated `ten_hien_thi` in `backend/app/simulation/semantic_program/display_names.py` so free quantities with mathematical symbol identifiers (`R`, `h`, `r`) receive their symbol as `notation` and `label` instead of generic `"Đại lượng đo"`.
   - Updated `_run_curved_route` in `backend/app/ai/adapter3_simulation.py` to use canonical mathematical symbol names `A_prime`, `B_prime`, `O_prime`, `r` when undeclared so `ten_hien_thi` emits `"Điểm A′"`, `"Điểm B′"`, `"Điểm O′"`, and `"r"`.

---

## 2. Files Changed in Session 1

- `backend/app/simulation/semantic_program/display_names.py`
- `backend/app/simulation/semantic_program/scene3d.py`
- `backend/app/ai/adapter3_simulation.py`
- `frontend/src/simulations/domains/geometry/pick-target.ts`
- `frontend/src/simulations/domains/geometry/scene3d-model.ts`
- `frontend/src/simulations/domains/geometry/scene3d-view.tsx`
- `frontend/src/simulations/domains/geometry/interaction-state.ts`
- `frontend/src/simulations/domains/geometry/simulation-visual-consistency-session1.test.tsx`
- `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/build_audit_scenes.py`
- `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/run_visual_ux_audit.mjs`
- `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/SIMULATION_VISUAL_BASELINE_AUDIT.md`
- `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/demos/*`
- `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/browser-baseline/baseline_audit_receipt.json`
- `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/browser-session1/session1_audit_receipt.json`
- `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/screenshots/before/*.png`
- `docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/screenshots/session1-after/*.png`

---

## 3. Before / After Real-Browser Evidence Summary

| Scene ID | Primary Solid `ownPixels` (Before → After) | Section `ownPixels` (Before → After) | `slateSolid` Pixels (Before → After) | `section` Amber Pixels (Before → After) | Canvas Labels (After) |
|---|---|---|---|---|---|
| `family09_cylinder_and_sections` | `36,685` → `75,389` | `26,098` → `68,202` (`td_sec_parallel`), `7,468` → `30,164` (`td_sec_axial`) | `588` → `8,740` | `408` → `20,146` | `['O', 'O′', 'A', 'B', 'A′', 'B′']` |
| `family10_cone_frustum_cut` | `19,181` → `62,203` (`khoi_cone_main`), `4,700` → `15,233` (`khoi_cone_upper`) | `4,063` → `16,768` (`td_sec_cut`), `3,105` → `16,953` (`td_sec_axial`) | `286` → `5,424` | `226` → `7,680` | `['O', 'S', 'A', 'B', 'O′']` |
| `family11_sphere_plane_cut` | `25,665` → `171,807` | `29,346` → `102,286` (`td_sec_sph`) | `221` → `63` | `0` → `2,778` | `['I']` |
| `family12_cylinder_ellipse_section` | `35,545` → `57,993` | `8,822` → `14,642` (`td_sec_el`) | `553` → `5,840` | `0` → `660` | `['O', 'O′']` |

All 9 polyhedral scenes (`family01..family08`) remained byte-identical in visual metrics (`0` regressions), and across all 14 scenes `totalConsoleErrors = 0`, `totalPageErrors = 0`, `resetDiffFromDefault = 0`, `labelCollisions = 0`.

---

## 4. Unresolved Problems & Continuation State for Session 2 (`P6–P15`)

- **`IH-01` (`INFORMATION_HIERARCHY_DEFECT`):** Handled in **Session 2 (`P6–P8`)**:
  - Implement **Mode A — Simulation (Default)** and **Mode B — Mathematical Analysis (`"Phân tích toán học"`)** in `Scene3DExplorer.tsx` and `SimulationWorkspace.tsx`.
  - Implement explicit semantic information classification (`GIVEN_DIMENSION`, `GIVEN_RELATION`, `DERIVED_MEASUREMENT`, `CONSTRUCTION_STEP`, `GEOMETRY_IDENTITY`, `REQUESTED_RESULT`, `MATHEMATICAL_CERTIFICATE`, `ERROR_OR_REFUSAL`) in `scene3d-model.ts`.
  - Ensure construction timeline steps (`P8`) clearly distinguish given setup, auxiliary construction, section creation, and final mathematical analysis steps, and complete `P9–P15` browser UX acceptance, regression tests, `SIMULATION_VISUAL_UX_DEVELOPMENT_EVALUATION_NOT_BLIND`, candidate freeze, independent review, and clean detached Full T3.
