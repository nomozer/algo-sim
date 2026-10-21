# Simulation Coverage & Visual Validation Campaign Report (`simulation-coverage-visual-validation`)

- **Authorization:** `GO_SIMULATION_COVERAGE_VISUAL_VALIDATION_LOCAL_RESEARCH` (`LOCAL RESEARCH IMPLEMENTATION — TWO SESSIONS — NO GO MAIN — NO LIVE LLM CALLS`)
- **Branch:** `research/simulation-coverage-visual-validation`
- **Baseline `main` (`origin/main`):** `bd8d6a9dc3acc9a4204b616379001270bb6d39f9`
- **Session 1 Checkpoint Commit:** `e05e620866934ce0f6c184f1d0de5dbace67b4cf`
- **Final Product Commit:** `3298b901d2246650535aa4028845ddc2a44892c4`
- **Measured System Hash (`114` files):** `4d11a91790422b9508bc90921f4352687a4b8616c0f855886e76649d3a7dcf68`
- **Final Status:** `SIMULATION_COVERAGE_VISUAL_VALIDATION_READY_FOR_GO_MAIN_REVIEW`

---

## 1. Capability Inventory & 7-Level Audit (`SIMULATION_CAPABILITY_MATRIX.md`)

- Audited all 15 geometric shape and simulation capability families across 7 architectural levels (`L1` Input Contract $\to$ `L2` Geometry Functions $\to$ `L3` Exact Engine $\to$ `L4` Planner/Adapter $\to$ `L5` `Scene3D` Topology $\to$ `L6` Three.js Renderer $\to$ `L7` Interactive Frontend):
  - **Polyhedral families (1–11):** Triangular pyramids, quadrilateral pyramids, regular pyramids, derived sub-pyramids, multi-solids with shared faces, prisms, cuboids, cubes, polyhedral plane sections, automatically derived section points (`I1..Ik`), and polyhedral residual/frustum sub-solids (`ABMN.ABCD`) are `FULL_END_TO_END`.
  - **Curved families (12–14):** Right circular cylinders (`cylinder`), right circular cones (`cone`), and spheres (`sphere` / `"ball"`) upgraded from `PARTIAL` (analytical kernel only, broken scalar-radius/height rendering, missing `TypedFactNext`/`Adapter /3` wiring) to `FULL_END_TO_END`.
  - **Frustums (15):** Polyhedral frustum (`ABMN.ABCD`) and right circular cone cut by a parallel plane (`cone` + `Circle3` upper section + certified cone-frustum residual volume) are `FULL_END_TO_END`; standalone two-radius `cone_frustum` without a parent cone is explicitly classified `BLOCKED_BY_KERNEL` (`curved.py::KHOI_CONG` only defines single-radius `"ball"`, `"cylinder"`, `"cone"`).

---

## 2. Simulation Breakage Fixes (`P3`, `RED -> GREEN`)

1. **Scalar-Radius & Scalar-Height Curved Solid Rendering (`frontend/src/simulations/domains/geometry/scene3d-view.tsx`, `scene3d-model.ts`):**
   - `scene3d-view.tsx` previously required `o.rim_point` truthiness (`if (!o.center_point || !o.rim_point) return null`), rendering scalar-radius cylinders, cones, and spheres (`rim_point: null`, `radius_sq: R^2`) completely invisible (`0` pixels in baseline browser audit). Fixed to accept `o.rim_point || typeof o.radius_sq === "number"`.
   - `scene3d-view.tsx` and `scene3d-model.ts` previously ignored canonical Z-axis orientation (`HUONG_TRUC_CANONICAL = (0, 0, 1)`) when `apex_or_top` was `null` and height was given via `height_sq`. Fixed to orient scalar-height cylinders and cones along `(0, 0, 1)` and include `(center.x, center.y, center.z + h)` in `diemHuuHan` bounding box computation.
2. **Component Tree & Solid Isolation Classification (`frontend/src/simulations/domains/geometry/interaction-state.ts`):**
   - Added `segment3` (`"Cạnh & đoạn"`), `circle3` and `ellipse3` (`"Mặt & thiết diện"`), and `curved_solid` (`"Khối"`) to `HANG_MUC`, and included `curved_solid` in `laKhoi` so curved solids and curved sections appear in `semanticTree` and support `Chỉ xem phần này` isolation.
3. **Timeline Event Classification (`backend/app/simulation/semantic_program/scene3d.py`, `simulation_state.py`):**
   - Added `"construct_curved_solid": "CREATE"` to `_HANH_DONG` in `scene3d.py` and mapped `circle3`/`ellipse3` construction events to `CREATE` / `GEOMETRY_CONSTRUCTION` so curved solids and their sections appear as proper construction steps instead of `MEASUREMENT`.

---

## 3. Curved Solid Expansion (`P4`, `RED -> GREEN`)

- Extended `backend/app/simulation/geometry_functions/typed_fact_next.py` (`typed-fact-next/1`) and `backend/app/ai/adapter3_simulation.py` (`hybrid-simulation-adapter/3`):
  - **Solids:** `cylinder` (right circular cylinder with `radius`, `height`), `cone` (right circular cone with `radius`, `height`), and `sphere` (sphere with `radius`).
  - **Derived Sections:**
    - `cylinder`: perpendicular circular section (`Circle3`), axial rectangle section (`polygon3` + `segment3` generators), and oblique elliptic section (`Ellipse3`).
    - `cone`: parallel-to-base circular section (`Circle3` with exact $r = R(1 - z/h)$), axial isosceles triangle section (`polygon3`), and oblique elliptic section (`Ellipse3`).
    - `sphere`: plane circular section (`Circle3` with exact $r = \sqrt{R^2 - d^2}$ when $d^2 < R^2$).
  - **Math Goals & Certificates:** Exact symbolic $\pi$-monomials and rational certificates for volume, lateral area, surface area, slant height, section area, section radius, and cone-frustum residual volume, delegating curved kind properties to `curved.py::KHOI_CONG` (single authority).
  - **Fail-Closed Refusals:** Non-positive radius/height (`TYPED_FACT_NEXT_NON_POSITIVE_VALUE`), missing radius/height (`TYPED_FACT_NEXT_UNDERDETERMINED_CONSTRUCTION`), plane missing or tangent to sphere $d \ge R$ (`TYPED_FACT_NEXT_INCONSISTENT_WITNESS`), cutting plane outside cone height $z \notin (0, h)$ (`TYPED_FACT_NEXT_INCONSISTENT_WITNESS`).

---

## 4. Executable Demo Suite & Real Browser Visual Acceptance (`P6`, `P7`, `P8`)

- **Interactive Demo Envelopes (`demos/demo1..demo7*.json`, `9` total):**
  1. `demo1-pyramid-derived-section.json` (Regular square pyramid `S.ABCD` + parallel plane section `MNPQ` + derived sub-solids `S.MNPQ` and `MNPQ.ABCD`)
  2. `demo2-unnamed-section-intersections.json` (Pyramid `S.ABCD` cut by `(ABM)` with automatically derived unnamed intersections `I1`)
  3. `demo3-multi-solid-shared-geometry.json` (Composite cube `ABCD.EFGH` + regular pyramid `S.EFGH` sharing top face `EFGH`)
  4. `demo4-step-by-step-construction.json` (Right triangular pyramid `S.ABC` with midpoint $M$, centroid $G$, altitude, and step-by-step dependencies)
  5. `demo5-selection-and-highlighting.json` (Right triangular prism `ABC.A'B'C'` with diagonal section `(A'BC)`)
  6. `demo6a-curved-cylinder-sections.json` (Right circular cylinder with perpendicular circular section `Circle3` and axial rectangle section `ABCD`)
  7. `demo6b-curved-cone-frustum-cut.json` (Right circular cone cut by parallel plane at $z = h/2$, highlighting upper circle section and frustum volume)
  8. `demo6c-curved-sphere-plane-cut.json` (Sphere of radius $R = 5$ cut by plane $z = 3$, producing circle section of radius $r = 4$)
  9. `demo7-invalid-geometry-safe-refusal.json` (Sphere of radius $R = 5$ with plane $z = 6 > R$, deterministically refused with `TYPED_FACT_NEXT_INCONSISTENT_WITNESS` and `scene3d: null`)
- **Real Browser Visual Acceptance (`visual-acceptance-receipt.json`, `screenshots/`):**
  - Headless Chromium WebGL verification across all 9 demos: `totalConsoleErrors = 0`, `totalPageErrors = 0`, `inkPixels > 519,000` on all 8 positive demos, `ownPixels > 0` for every primary object (`solid`, `curved_solid`, `section`, `polygon3`, `circle3`), `orbitDiffPixels > 0`, `zoomDiffPixels > 0`, `panDiffPixels > 0`, `selectionDiffPixels > 0`, `step0DiffPixels > 0`, `labelCollisions = 0`, and `labelsNotCollapsed = true`.
- **Simulation-Centered Offline Evaluation (`eval-summary.json`, `corpus-dev.json`):**
  - Explicitly labeled `DEVELOPMENT_EVALUATION_NOT_BLIND` (`15` cases: `10` positive + `5` negative):
  - `positive_served = 10/10`, `negative_refused = 5/5`, `wrong_serves = 0`, and `10/10` pass across all 8 simulation criteria (`scene3d_valid_v2`, `solid_topology_complete`, `derived_section_correct`, `derived_point_provenance_ok`, `multi_solid_identity_ok`, `curved_solid_render_ok`, `timeline_dependency_order_ok`, `math_certificate_consistent`).

---

## 5. Governance & Safety Invariants (`P13`)

- `DEFAULT_MODE = LLM_ONLY`
- `RESPONSE_CONTRACT = flat`
- `HYBRID_PRODUCT_ENABLEMENT = NO-GO`
- `ALLOW_LIVE_AI = 0` (`0` live model/provider calls)
- `CACHE_VERSION = 127` (`NO_BUMP`)
- Root checkout `D:\Documents\projects\algo-sim` (`research/hybrid-wave3a-volume-reasoning`) was never modified, switched, or reset.
