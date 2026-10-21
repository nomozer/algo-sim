# SIMULATION CAPABILITY MATRIX — ALGOSIM 3D GEOMETRY SIMULATION

- **Campaign:** `simulation-coverage-visual-validation`
- **Authorization:** `GO_SIMULATION_COVERAGE_VISUAL_VALIDATION_LOCAL_RESEARCH`
- **Baseline `main` Commit:** `bd8d6a9dc3acc9a4204b616379001270bb6d39f9`
- **Branch:** `research/simulation-coverage-visual-validation`
- **Audit Scope:** 7-level end-to-end simulation capability audit across 15 shape and simulation feature categories prior to Session 1 P3/P4 fixes and expansions (with post-Session-1 target delta documented).

---

## 1. Seven-Level Capability Classification Summary (Baseline Before Session 1 Fixes)

| # | Shape / Capability | L1: Input Contract (`TypedFact` / `TypedFactNext`) | L2: Geometry Functions (`/11`) | L3: Exact Engine (`/9` + `curved.py`) | L4: Planner / Adapter (`/11` + `Adapter /3`) | L5: `Scene3D` Topology (`scene3d.py` + `subentities.ts`) | L6: Three.js Renderer (`scene3d-view.tsx`) | L7: Interactive Frontend (`Scene3DExplorer.tsx`) | Baseline Status (Pre-P3/P4) | Post-Session-1 Target Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Triangular pyramids** (`S.ABC`, `ABCD`) | Supported (`pyramid`, `TypedFactNext` `pyramid`) | Supported (`pyramid`, `regular_polygon`, `right_triangle`, `triangle_sides`, `perpendicular_line_plane`, `face_perpendicular_base`) | Supported (`_Dung` affine chart + Gram $G$) | Supported (`planner.py` + `adapter3_simulation.py`) | Supported (`solid` mesh + `face`/`edge` sub-entities) | Supported (`veKhongGian` + `BufferGeometry` + hidden-edge dashed pass) | Supported (orbit/zoom/pan, select, highlight, isolate, explode, step scrubber) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 2 | **Quadrilateral pyramids** (`S.ABCD`) | Supported (`pyramid`, `TypedFactNext` `pyramid`) | Supported (`pyramid`, `regular_polygon`, `rectangle`, `rhombus`, `trapezoid`, `parallelogram`) | Supported (`_Dung` affine chart + Gram $G$) | Supported (`planner.py` + `adapter3_simulation.py`) | Supported (`solid` mesh + 5 `face` + 8 `edge` sub-entities) | Supported (`veKhongGian` + `BufferGeometry` + hidden-edge dashed pass) | Supported (orbit/zoom/pan, select, highlight, isolate, explode, step scrubber) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 3 | **Regular pyramids** (`chóp tam/tứ/lục giác đều`) | Supported (`regular_pyramid`, `TypedFactNext` `regular=True`) | Supported (`regular_pyramid`, `regular_polygon` $k \in \{3,4,6\}$) | Supported (`regular_polygon_chart`, centroid foot $O$, exact Gram $G$) | Supported (`planner.py` + `adapter3_simulation.py`) | Supported (`solid` mesh + `face`/`edge` sub-entities + altitude $SO$) | Supported (`veKhongGian` maps affine chart to Euclidean 3D via Cholesky of $G$) | Supported (orbit/zoom/pan, select, highlight, isolate, explode, step scrubber) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 4 | **Derived sub-pyramids** (e.g. `M.ABC`, `S.ABMN`) | Supported (`pyramid` on derived points; `TypedFactNext` `DerivedSubSolidSpec` `sub_pyramid`) | Supported (`midpoint`, `divide_segment`, `centroid`, `pyramid`, `ask_volume`, `ask_volume_ratio`) | Supported (`_Dung` composite pyramids sharing root chart; `Adapter /3` convex-hull sub-solid) | Supported (`planner.py` + `adapter3_simulation.py` Slice A) | Supported (`solid` mesh with explicit `vertex_ids`, `faces`, `depends`) | Supported (distinct translucent mesh + edges over parent solid) | Supported (selectable in tree & canvas, step-ordered appearance) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 5 | **Multiple solids with shared faces** (e.g. `ABCD.EFGH` + `S.EFGH`, `S.ABC` + `M.ABC`) | Supported (`TypedFact` multi-`pyramid` + `shared_face`; `TypedFactNext` `SharedGeometryRelation`) | Supported (`pyramid`, `prism`, `shared_face`, `ask_volume_ratio`, `ask_residual_volume`) | Supported (`_Dung` single root chart + 3D SAT overlap guard; `Adapter /3` shared-face frame unification) | Supported (`planner.py` + `adapter3_simulation.py` Slice B) | Supported (multiple `solid` objects + per-solid `face`/`edge` sub-entities) | Supported (both solids rendered in shared world frame with hidden-edge pass) | Supported (per-solid tree roots, independent selection/isolation/explosion) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 6 | **Prisms** (`ABC.A'B'C'`, `ABCD.A'B'C'D'`) | Supported (`prism`, `TypedFactNext` `prism`) | Supported (`prism`, `right=True/False`, `perpendicular_line_plane` for oblique apex projection) | Supported (`_Dung` right & oblique prism translation $\vec{v} = A' - A$) | Supported (`planner.py` + `adapter3_simulation.py`) | Supported (`solid` mesh + base/top/lateral `face` & `edge` sub-entities) | Supported (`veKhongGian` + `BufferGeometry` + hidden-edge dashed pass) | Supported (orbit/zoom/pan, select, highlight, isolate, explode, step scrubber) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 7 | **Cuboids** (`Hình hộp chữ nhật`) | Supported (`prism` + `rectangle` base; `TypedFactNext` `prism` + `rectangle`) | Supported (`prism(right=True)`, `rectangle`, `segment_length`, `height`) | Supported (`_Dung` orthogonal chart $G = \text{diag}(a^2, b^2, c^2)$) | Supported (`planner.py` + `adapter3_simulation.py`) | Supported (`solid` mesh + 6 `face` + 12 `edge` sub-entities) | Supported (`veKhongGian` + `BufferGeometry`) | Supported (full interactive support) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 8 | **Cubes** (`Hình lập phương`) | Supported (`prism` + `regular_polygon` + `equal_length`; `TypedFactNext` `prism` + `square`) | Supported (`prism(right=True)`, `regular_polygon`, `equal_length`, `segment_length`) | Supported (`_Dung` $G = \text{diag}(a^2, a^2, a^2)$) | Supported (`planner.py` + `adapter3_simulation.py`) | Supported (`solid` mesh + 6 `face` + 12 `edge` sub-entities) | Supported (`veKhongGian` + `BufferGeometry`) | Supported (full interactive support) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 9 | **Plane sections (polyhedral)** (`Thiết diện đa diện`) | Supported (`section`, `TypedFactNext` `PlaneSectionSpec`) | Supported (`section`, `plane_through`, `plane_parallel`, `plane_two_lines`, `plane_perpendicular_line`) | Supported (`K.intersect_plane_solid` + `kiem_mat_cat` closed-cycle verification) | Supported (`planner.py` + `adapter3_simulation.py` two-phase verification) | Supported (`section` object + `deriveSectionSubEntities` vertices, edges, filled face) | Supported (amber outline + translucent section face + `Xem thiết diện` isolation) | Supported (cycle label `MNPQ`, vertex count, cut solid, plane inspector) | `FULL_END_TO_END` | `FULL_END_TO_END` |
| 10 | **Automatically derived section points** (`I1..Ik`) | Supported (`TypedFactNext` `derive_unnamed_intersections=True`, `DerivedObjectIdentity`) | Partial (`section` computes polygon vertices in kernel, but `TypedFact` `/3` does not bind `I1..Ik` point objects) | Supported (`K.intersect_plane_solid` exact rational edge-cut coordinates + ratios) | Supported in `Adapter /3` (`DerivedObjectIdentity` + `point3` injection for `I1..Ik`) | Supported (`point3` objects `I1..Ik` + `section.endpoint_entities` binding) | Supported (point markers + 2D sprite labels for `I1..Ik` + section cycle) | Supported (selectable `I1..Ik` points with cut-edge ratio metadata in inspector) | `FULL_END_TO_END` (via `TypedFactNext` + `Adapter /3`) | `FULL_END_TO_END` |
| 11 | **Residual region visualization** (`Phần còn lại / khối đa diện cắt cụt`) | Supported (`ask_residual_volume`; `TypedFactNext` `DerivedSubSolidSpec` `frustum_like`) | Supported (`ask_residual_volume` for volume; no dedicated residual mesh function in `/11`) | Supported (`engine.py` outward half-space containment + `Adapter /3` convex-hull `frustum_like` solid) | Partial (`engine.py` computes certified residual volume without fabricating a second mesh; `Adapter /3` constructs explicit `frustum_like` `solid` when declared) | Supported when declared via `Adapter /3` `DerivedSubSolidSpec` (`solid` mesh `ABMN.ABCD`); numeric-only in `/11` | Supported when declared via `Adapter /3` (`solid` mesh with faces/edges) | Supported when declared via `Adapter /3` (`ABMN.ABCD` selectable/explodable) | `PARTIAL` (`/11` numeric + parent/cut solids; `Adapter /3` full 3D `frustum_like` sub-solid) | `FULL_END_TO_END` (via `Adapter /3` `frustum_like` + `/11` parent/cut solids) |
| 12 | **Cylinders (Right circular cylinder)** (`Hình trụ tròn xoay`) | **Missing in `TypedFact` `/11` & `TypedFactNext` `/1`** (only in `SemanticProgram` / `RequestContract`) | **Unsupported** (`NO_SOLID` in `registry.py` / `engine.py`) | **Supported** in `curved.py` (`CurvedSolid` `"cylinder"`, exact $R^2, h^2, V, S_{xq}$, `intersect_plane_curved`, `intersect_plane_curved_ellipse`) | **Missing in `Adapter /3`** (only in `SemanticProgramInterpreter`) | **Buggy** (`construct_curved_solid` missing from `_HANH_DONG` $\to$ `STEP` instead of `CREATE`; `circle3`/`ellipse3` marked `MEASUREMENT`) | **Broken for scalar radius/height** (`scene3d-view.tsx:1478` requires `o.rim_point`, so scalar-radius cylinder is invisible; scalar-height cylinder not rotated from Y to Z axis!) | **Partial** (`curved_solid`, `circle3`, `ellipse3` missing from `HANG_MUC` & `laKhoi` in `interaction-state.ts`) | `PARTIAL` (Kernel exists; Renderer broken on scalar radius/height; `TypedFactNext`/`Adapter /3` missing) | `FULL_END_TO_END` (via `TypedFactNext` + `Adapter /3` + `curved.py` + fixed `scene3d-view.tsx`) |
| 13 | **Cones (Right circular cone)** (`Hình nón tròn xoay`) | **Missing in `TypedFact` `/11` & `TypedFactNext` `/1`** | **Unsupported** (`NO_SOLID` in `registry.py` / `engine.py`) | **Supported** in `curved.py` (`CurvedSolid` `"cone"`, exact $R^2, h^2, l^2 = R^2+h^2$, `intersect_plane_curved` parallel/conic) | **Missing in `Adapter /3`** | **Buggy** (`construct_curved_solid` $\to$ `STEP`; `circle3` section $\to$ `MEASUREMENT`) | **Broken for scalar radius/height** (`scene3d-view.tsx:1478` skips when `rim_point` is `null`; scalar-height cone not oriented along canonical Z axis) | **Partial** (`curved_solid` not in `laKhoi` / `HANG_MUC`) | `PARTIAL` (Kernel exists; Renderer broken on scalar radius/height; `TypedFactNext`/`Adapter /3` missing) | `FULL_END_TO_END` (via `TypedFactNext` + `Adapter /3` + `curved.py` + fixed `scene3d-view.tsx`) |
| 14 | **Spheres** (`Mặt cầu / Khối cầu`) | **Missing in `TypedFact` `/11` & `TypedFactNext` `/1`** | **Unsupported** (`NO_SOLID` in `registry.py` / `engine.py`) | **Supported** in `curved.py` (`CurvedSolid` `"ball"`, exact $R^2, V, S$, `intersect_plane_curved` circle when $d^2 < R^2$, fail-closed on $d^2 \ge R^2$) | **Missing in `Adapter /3`** | **Buggy** (`construct_curved_solid` $\to$ `STEP`; `circle3` section $\to$ `MEASUREMENT`) | **Broken for scalar radius** (`scene3d-view.tsx:1478` skips when `rim_point` is `null` — scalar-radius sphere completely invisible!) | **Partial** (`curved_solid` & `circle3` not in `HANG_MUC` / `laKhoi`) | `PARTIAL` (Kernel exists; Renderer broken on scalar radius; `TypedFactNext`/`Adapter /3` missing) | `FULL_END_TO_END` (via `TypedFactNext` + `Adapter /3` + `curved.py` + fixed `scene3d-view.tsx`) |
| 15 | **Frustums** (`Hình chóp cụt` & `Hình nón cụt`) | Polyhedral frustum: Supported in `TypedFactNext` (`frustum_like`). Cone frustum: **Unsupported** (`KHOI_CONG` only has `ball`, `cylinder`, `cone`) | Polyhedral: `ask_residual_volume`. Cone frustum: **Unsupported** | Polyhedral: Supported (`Adapter /3` `frustum_like` + `engine.py` residual). Cone frustum: **No analytical kernel (`KHOI_CONG` lacks `cone_frustum`)**; parallel plane cut on cone produces exact upper circle `Circle3` | Polyhedral: Supported in `Adapter /3`. Cone frustum: parallel-plane cut on cone supported via `cone` + `intersect_plane_curved`, standalone `cone_frustum` `BLOCKED_BY_KERNEL` | Polyhedral: `solid` mesh `ABMN.ABCD`. Cone + parallel cut: `cone` + `circle3` upper section + base `circle3` | Polyhedral: `BufferGeometry`. Cone frustum: standalone `CylinderGeometry(rTop, rBottom, h)` not wired to `curved.py` (`BLOCKED_BY_KERNEL`) | Polyhedral: `FULL_END_TO_END` via `Adapter /3`. Cone frustum: `BLOCKED_BY_KERNEL` as standalone primitive (cone + parallel circular section supported) | Polyhedral: `FULL_END_TO_END` (`Adapter /3`); Cone frustum: `UNSUPPORTED` (`BLOCKED_BY_KERNEL`) | Polyhedral: `FULL_END_TO_END`; Cone parallel-cut section: `FULL_END_TO_END`; Standalone `cone_frustum` primitive: `BLOCKED_BY_KERNEL` |

---

## 2. Detailed Per-Shape Capability Inventory

### 2.1. Triangular Pyramids (`Hình chóp tam giác S.ABC` / `Tứ diện ABCD`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:**
  - Base triangle: `regular_polygon` (equilateral), `right_triangle` (right at vertex), `triangle_sides` (3 known sides satisfying strict triangle inequality and rational/chart constraints), or `perpendicular_lines` + two side lengths.
  - Apex placement: `perpendicular_line_plane` (known altitude foot on base vertex, midpoint, or centroid), `regular_pyramid` (foot at centroid), or `face_perpendicular_base` (lateral face $\perp$ base with lateral altitude foot on shared edge).
- **Required Constraints:** Strict positive squared lengths, triangle inequality, unique altitude foot determination (otherwise fail-closed `UNDERDETERMINED_POINT`).
- **Scene3D Representation:** `solid` object (`render: "mesh"`, `vertices`, `vertex_ids`, `faces` of length 4) + `point3` vertices + derived sub-entities (`4` `face` polygons, `6` `edge` segments).
- **Browser Rendering Status:** Verified in Chromium WebGL (`veKhongGian` maps affine coordinates to Euclidean coordinates via Cholesky factor of `chart_metric`; translucent mesh + solid front edges + dashed occluded edges).
- **User Interactions:** Orbit, zoom, pan, click vertex/edge/face/solid, dependency highlighting, `Chỉ xem phần này` (isolate), `Tách khối` (explode faces outward by `EXPLODE_DISTANCE = 0.6`), step-by-step construction playback.
- **Remaining Limitations:** General tetrahedron given only by 6 arbitrary edge lengths without an altitude foot or perpendicular face is refused (`UNDERDETERMINED_POINT`).

### 2.2. Quadrilateral Pyramids (`Hình chóp tứ giác S.ABCD`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:**
  - Base quadrilateral: `regular_polygon` (square), `rectangle`, `rhombus` (with angle or diagonal), `parallelogram` (with angle or diagonal), `trapezoid` (right trapezoid or isosceles trapezoid with determinable dimensions).
  - Apex placement: `perpendicular_line_plane` (foot at $A, B, C, D$, midpoint $M$, or base center $O$), `regular_pyramid`, or `face_perpendicular_base`.
- **Required Constraints:** Non-degenerate coplanar base cycle, positive edge lengths, determined altitude foot and height (direct `height`, lateral `segment_length`, `angle_line_plane`, or `angle_plane_plane`).
- **Scene3D Representation:** `solid` (`render: "mesh"`, 5 faces: 1 quad base + 4 triangular lateral faces) + 5 `point3` vertices + 5 `face` sub-entities + 8 `edge` sub-entities.
- **Browser Rendering Status:** Verified in Chromium WebGL.
- **User Interactions:** Full interactive support (orbit, zoom, pan, select, highlight, isolate, explode, step playback).
- **Remaining Limitations:** Irregular general quadrilaterals without parallel/orthogonal/equal-side structure are refused fail-closed.

### 2.3. Regular Pyramids (`Hình chóp đều S.ABC`, `S.ABCD`, `S.ABCDEF`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:** `regular_pyramid` ($k \in \{3, 4, 6\}$ base vertices), base side length, and one of: height $SO$, lateral edge $SA$, lateral-edge-to-base angle, or lateral-face-to-base dihedral angle.
- **Required Constraints:** Base vertex count $k \in \{3, 4, 6\}$ (for $k \notin \{3, 4, 6\}$, $\cos(2\pi/k) \notin \mathbb{Q}$ triggers deterministic refusal `UNSUPPORTED_REGULAR_POLYGON`); lateral edge squared must strictly exceed circumradius squared ($SA^2 > R^2$).
- **Scene3D Representation:** `solid` (`render: "mesh"`), base center $O$ (`point3`), altitude segment $SO$, and all derived `face` and `edge` sub-entities.
- **Browser Rendering Status:** Verified in Chromium WebGL (`veKhongGian` transforms the affine regular triangle/hexagon chart into exact Euclidean 3D proportions).
- **User Interactions:** Full interactive support.
- **Remaining Limitations:** Regular pentagon ($k=5$) or octagon ($k=8$) bases are intentionally refused because $\cos(2\pi/k) \notin \mathbb{Q}$.

### 2.4. Derived Sub-Pyramids (`Khối chóp con dẫn xuất`, e.g. `M.ABC`, `S.ABMN`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:**
  - Via `/11` (`engine.py`): Secondary `pyramid` call whose apex and/or base vertices are constructed points (`midpoint`, `divide_segment`, `centroid`, `orthogonal_projection`, `intersect_line_plane`) inside the root solid's chart.
  - Via `TypedFactNext` + `Adapter /3`: `DerivedSubSolidSpec` (`kind="sub_pyramid"`, e.g. `S.ABMN` bounded by apex $S$ and section vertices $A, B, M, N$).
- **Required Constraints:** Non-coplanar vertices (positive $6V > 0$), all vertices grounded in the root chart or section intersection.
- **Scene3D Representation:** Dedicated `solid` object (`render: "mesh"`) with its own `vertex_ids`, `faces`, `depends`, and per-solid `face`/`edge` sub-entities.
- **Browser Rendering Status:** Verified in Chromium WebGL.
- **User Interactions:** Independently selectable in the component tree (`Các thành phần của hình`) and 3D canvas; supports `Chỉ xem phần này` (isolating the sub-pyramid from the parent pyramid) and `Tách khối`.
- **Remaining Limitations:** In `/11`, derived bases must be triangles or rectangles/parallelograms/squares verified by `_da_giac_dan_xuat`.

### 2.5. Multiple Solids with Shared Faces (`Nhiều khối dùng chung mặt / cạnh / đỉnh`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:**
  - Via `/11` (`engine.py`): Two pyramids sharing a declared triangular face (`shared_face`) or sharing the root base on opposite/same sides, verified by 3D Separating Axis Theorem (`_hai_chop_cat_nhau`) to prevent volumetric interior overlap.
  - Via `TypedFactNext` + `Adapter /3`: Composite solids linked by explicit `SharedGeometryRelation` (`shared_face`, `shared_segment`, `shared_vertex`), e.g. cube/prism `ABCD.EFGH` + pyramid `S.EFGH` sharing top face `EFGH`.
- **Required Constraints:** Explicit shared relation required when vertex labels overlap across solids (ambiguous bare references are refused with `TYPED_FACT_NEXT_AMBIGUOUS_REFERENCE`); no 3D interior intersection (`OVERLAPPING_SOLIDS` / `TYPED_FACT_NEXT_INCONSISTENT_WITNESS`).
- **Scene3D Representation:** Multiple root `solid` objects in `Scene3D.objects`, each with its own `face` and `edge` sub-entities under its own tree node in `semanticTree`.
- **Browser Rendering Status:** Verified in Chromium WebGL.
- **User Interactions:** Each solid is a distinct root in `semanticTree`, can be selected, highlighted, hidden, or isolated independently.
- **Remaining Limitations:** Arbitrary boolean CSG union/intersection of overlapping solids is out of scope (interior overlap is refused fail-closed).

### 2.6. Prisms (`Hình lăng trụ đứng / xiên ABC.A'B'C'`, `ABCD.A'B'C'D'`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:** `prism(base, top, right=True/False)` with matching vertex counts on `base` and `top`, base shape (`regular_polygon`, `right_triangle`, `triangle_sides`, `rectangle`, `rhombus`, `parallelogram`, `trapezoid`), and either `right=True` + height/lateral edge or `right=False` + `perpendicular_line_plane([A', H], base)` where $H$ is a determined foot in the base plane.
- **Required Constraints:** Equal vertex count on `base` and `top`; determined lateral translation vector $\vec{v} = A' - A$.
- **Scene3D Representation:** `solid` (`render: "mesh"`, 2 base faces + $k$ quad lateral faces) + $2k$ `point3` vertices + $(k+2)$ `face` sub-entities + $3k$ `edge` sub-entities.
- **Browser Rendering Status:** Verified in Chromium WebGL.
- **User Interactions:** Full interactive support.
- **Remaining Limitations:** Oblique prisms without a known orthogonal projection of a top vertex onto the base plane are refused (`UNDERDETERMINED_POINT`).

### 2.7. Cuboids (`Hình hộp chữ nhật ABCD.A'B'C'D'`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:** `prism(right=True)` + `rectangle(base)` (or `TypedFactNext` `prism` with `base_shape="rectangle"`, `right_prism=True`) + 3 orthogonal dimensions ($AB, AD, AA'$).
- **Required Constraints:** Positive dimensions $a, b, c > 0$.
- **Scene3D Representation:** `solid` (`render: "mesh"`, 6 quad faces, 8 vertices, 12 edges).
- **Browser Rendering Status:** Verified in Chromium WebGL.
- **User Interactions:** Full interactive support.
- **Remaining Limitations:** None within standard Euclidean cuboid geometry.

### 2.8. Cubes (`Hình lập phương ABCD.A'B'C'D'`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:** `prism(right=True)` + `regular_polygon(base)` + `equal_length` / `height` (or `TypedFactNext` `prism` with `base_shape="square"`, `right_prism=True`, `height=side`).
- **Required Constraints:** Positive side length $a > 0$.
- **Scene3D Representation:** `solid` (`render: "mesh"`, 6 square faces, 8 vertices, 12 edges).
- **Browser Rendering Status:** Verified in Chromium WebGL.
- **User Interactions:** Full interactive support.
- **Remaining Limitations:** None.

### 2.9. Plane Sections (`Thiết diện mặt phẳng cắt khối đa diện`)
- **Classification:** `FULL_END_TO_END`
- **Supported Construction Inputs:**
  - Plane through 3 non-collinear points (`plane_through` / `section(solid, [M, N, P])`).
  - Plane through 1 point and parallel to 2 lines or a face (`plane_parallel` / `ParallelPlaneSectionSpec`).
  - Plane containing 1 line and parallel to another line (`plane_two_lines`).
  - Plane through 1 point and perpendicular to a line (`plane_perpendicular_line`).
- **Required Constraints:** Cutting plane must not be degenerate (`NotCoplanarError` if points are collinear) and must intersect the solid's interior/faces in a closed polygon of $\ge 3$ vertices (`SectionError` / `kiem_mat_cat`).
- **Scene3D Representation:** `section` object (`render: "polygon"`, `polygon` ordered cycle of exact 3D points, `steps` with `face_index`) + `deriveSectionSubEntities` (`section::vertex:i`, `section::edge:i`, `section::face:0`).
- **Browser Rendering Status:** Verified in Chromium WebGL (amber boundary polygon + translucent filled section face + `Xem thiết diện` button isolating the section inside the translucent parent solid).
- **User Interactions:** Selecting the section opens the dedicated `Thiết diện` inspector showing cycle name (`MNPQ`), vertex count, vertex list, cut solid, cutting plane, and `Xem thiết diện` isolation button.
- **Remaining Limitations:** Plane sections on curved solids (`cylinder`, `cone`, `sphere`) produce `circle3` or `ellipse3` rather than polygonal `section` objects — see items 12–14.

### 2.10. Automatically Derived Section Points (`Giao điểm thiết diện vô danh I1..Ik`)
- **Classification:** `FULL_END_TO_END` (via `TypedFactNext` + `Adapter /3`)
- **Supported Construction Inputs:** `PlaneSectionSpec` (`through_points` or `parallel_plane`) with `derive_unnamed_intersections=True` in `TypedFactNext`.
- **Required Constraints:** Whenever the cutting plane crosses a solid edge at an interior point not already named by a declared point in the specification, `Adapter /3` deterministically mints `I1`, `I2`, ... ordered by canonical edge order, recording `DerivedObjectIdentity` (`cut_edge`, exact `ratio_num`/`ratio_den`, `dependencies`, `source_span`).
- **Scene3D Representation:** Explicit `point3` objects (`I1..Ik`) in `Scene3D.objects` + `section.endpoint_entities` binding each section polygon vertex to its named or derived point ID.
- **Browser Rendering Status:** Verified in Chromium WebGL (`I1..Ik` render as interactive 3D point markers with sprite labels and appear in the section cycle label, e.g. `MNI1I2`).
- **User Interactions:** Clicking `I1` in the 3D scene or component tree highlights the parent edge and cutting plane and displays its role in the inspector.
- **Remaining Limitations:** Only active on the `TypedFactNext` + `Adapter /3` simulation route (`/11` leaves unnamed section vertices as `section::vertex:i` sub-entities).

### 2.11. Residual Region Visualization (`Phần khối còn lại / hình chóp cụt sau khi cắt`)
- **Classification:** `PARTIAL` in `/11` (exact volume + parent/subtracted solids visualized); `FULL_END_TO_END` in `TypedFactNext` + `Adapter /3` (`DerivedSubSolidSpec` `kind="frustum_like"`).
- **Supported Construction Inputs:**
  - In `/11`: `ask_residual_volume(original_solid, subtracted_solids)` computes the certified residual volume $V_{\text{parent}} - \sum V_{\text{cut}}$ after verifying outward half-space vertex containment and shared boundary faces, while displaying the parent solid and subtracted pyramid(s) in `Scene3D`.
  - In `TypedFactNext` + `Adapter /3`: `DerivedSubSolidSpec(id="ABMN.ABCD", kind="frustum_like", parent_solid_id=..., vertex_ids=[...])` explicitly constructs the 6-face polyhedral frustum mesh in `Scene3D` using exact convex-hull topology (`_convex_hull_faces`) and certifies its volume.
- **Required Constraints:** Vertices must span a non-degenerate 3D convex polyhedron ($6V > 0$) contained in the parent solid.
- **Scene3D Representation:** In `Adapter /3`, `ABMN.ABCD` is a full `solid` object (`render: "mesh"`) with 6 faces (`ABCD`, `ABMN`, `ABM`, `BCN`, etc.) and 8 vertices.
- **Browser Rendering Status:** Verified in Chromium WebGL.
- **User Interactions:** Full selection, isolation (`Chỉ xem phần này` shows only the residual frustum `ABMN.ABCD`), and face explosion (`Tách khối`).
- **Remaining Limitations:** Non-convex residual polyhedra (after multiple non-disjoint cuts) are not triangulated as a single convex hull mesh.

### 2.12. Cylinders — Right Circular Cylinder (`Hình trụ tròn xoay`)
- **Baseline Classification (Pre-P3/P4):** `PARTIAL` (Analytical kernel in `curved.py` + `SemanticProgram` exists; **3 bugs in `scene3d.py` / `scene3d-view.tsx` / `scene3d-model.ts` break scalar-radius/scalar-height rendering**; **not yet wired into `TypedFactNext` + `Adapter /3`**).
- **Post-Session-1 Classification:** `FULL_END_TO_END`
- **Analytical Geometric Model vs. Triangulated Display Mesh:**
  - **Analytical Model (`curved.py`):** `CurvedSolid(kind="cylinder", center=O, rim=A|None, top=O'|None, radius_sq=R^2, height_sq=h^2)`. Exact rational $R^2, h^2 \in \mathbb{Q}_{>0}$; exact symbolic $\pi$-monomials for volume $V = \pi R^2 h$ and lateral area $S_{xq} = 2\pi R h$; exact plane-cylinder intersection (`intersect_plane_curved` $\to$ `Circle3` when cutting plane $\perp$ axis at $0 \le t \le h$; `intersect_plane_curved_ellipse` $\to$ `Ellipse3` when cutting plane is oblique and doesn't cut caps; axial rectangle polygon section via points on top/bottom rims).
  - **Display Mesh (`scene3d-view.tsx`):** `THREE.CylinderGeometry(r, r, h, 48)` (48-segment tessellation) + 2 circular rim rings (`vongTron`).
- ** Deficiencies Found in Baseline Audit (Fixed in P3/P4):**
  1. `scene3d-view.tsx:1478` checked `o.rim_point` truthiness, causing scalar-radius cylinders (`rim_point: null`, `radius_sq: R^2`) to return `null` and never render!
  2. `scene3d-view.tsx:1511` & `scene3d-model.ts:845` did not orient or bound scalar-height cylinders (`apex_or_top: null`, `height_sq: h^2`) along canonical axis `HUONG_TRUC_CANONICAL = (0, 0, 1)`.
  3. `scene3d.py:496` omitted `"construct_curved_solid"` from `_HANH_DONG`, emitting `STEP` instead of `CREATE`.
  4. `TypedFactNext` and `Adapter /3` lacked `cylinder` solid specification and perpendicular/axial section compilation.

### 2.13. Cones — Right Circular Cone (`Hình nón tròn xoay`)
- **Baseline Classification (Pre-P3/P4):** `PARTIAL` (Analytical kernel in `curved.py` exists; scalar-radius/height rendering broken in `scene3d-view.tsx`; not wired into `TypedFactNext` + `Adapter /3`).
- **Post-Session-1 Classification:** `FULL_END_TO_END`
- **Analytical Geometric Model vs. Triangulated Display Mesh:**
  - **Analytical Model (`curved.py`):** `CurvedSolid(kind="cone", center=O, rim=A|None, top=S|None, radius_sq=R^2, height_sq=h^2)`. Exact rational $R^2, h^2$, slant height squared $l^2 = R^2 + h^2$, volume $V = \frac{1}{3}\pi R^2 h$, lateral area $S_{xq} = \pi R l$; parallel-base plane cut at height $z \in (0, h)$ yields exact `Circle3` with radius $r = R(1 - z/h)$ (`intersect_plane_curved`); axial plane through apex $S$ and base diameter $AB$ yields exact isosceles triangle $\triangle SAB$.
  - **Display Mesh (`scene3d-view.tsx`):** `THREE.ConeGeometry(r, h, 48)` + base circular rim ring (`vongTron`).
- **Deficiencies Found in Baseline Audit (Fixed in P3/P4):** Same 4 issues as Cylinder (scalar-radius invisibility, scalar-height Z-axis orientation/bounds, `construct_curved_solid` event action, and `TypedFactNext` + `Adapter /3` wiring).

### 2.14. Spheres (`Mặt cầu / Khối cầu`)
- **Baseline Classification (Pre-P3/P4):** `PARTIAL` (Analytical kernel in `curved.py` exists; scalar-radius sphere completely invisible in `scene3d-view.tsx:1478`; not wired into `TypedFactNext` + `Adapter /3`).
- **Post-Session-1 Classification:** `FULL_END_TO_END`
- **Analytical Geometric Model vs. Triangulated Display Mesh:**
  - **Analytical Model (`curved.py`):** `CurvedSolid(kind="ball", center=O, rim=A|None, radius_sq=R^2)`. Exact rational $R^2 \in \mathbb{Q}_{>0}$, volume $V = \frac{4}{3}\pi R^3$, surface area $S = 4\pi R^2$; plane intersection (`intersect_plane_curved`) computes exact projection $O'$ of center $O$ onto plane $(\alpha)$ and distance squared $d^2 = |OO'|^2$:
    - If $d^2 < R^2$: exact `Circle3(center=O', normal=n_\alpha, radius_sq=R^2 - d^2)`.
    - If $d^2 = R^2$ (tangent point) or $d^2 > R^2$ (disjoint): deterministic fail-closed `GeometryError` / `TYPED_FACT_NEXT_INCONSISTENT_WITNESS`.
  - **Display Mesh (`scene3d-view.tsx`):** `THREE.SphereGeometry(r, 40, 24)` + 3 orthogonal great-circle wireframe rings (`vongTron` along X, Y, Z normals) + translucent filled disc & boundary ring for any `circle3` plane section.
- **Deficiencies Found in Baseline Audit (Fixed in P3/P4):** Scalar-radius invisibility in `scene3d-view.tsx:1478`, `construct_curved_solid` / `circle3` timeline events in `scene3d.py`, `interaction-state.ts` tree categorization, and `TypedFactNext` + `Adapter /3` support.

### 2.15. Frustums (`Hình chóp cụt` & `Hình nón cụt`)
- **Polyhedral Frustum (`Hình chóp cụt` / `Khối đa diện cắt cụt`):**
  - **Classification:** `FULL_END_TO_END` (via `TypedFactNext` + `Adapter /3` `DerivedSubSolidSpec` `kind="frustum_like"` + `residual_volume` goal).
  - **Supported Inputs:** Pyramid cut by a plane intersecting all lateral edges (e.g. `S.ABCD` cut by plane `(ABMN)` or parallel plane `(MNPQ)`), with `DerivedSubSolidSpec(kind="frustum_like")` constructing the lower frustum `ABMN.ABCD` or `MNPQ.ABCD`.
- **Right Circular Cone Frustum (`Hình nón cụt`):**
  - **Classification:**
    - **Cone with parallel cutting plane (`cone` + `intersect_plane_curved`):** `FULL_END_TO_END` after Session 1 P4 — constructs the parent right circular cone, cutting plane $\perp$ axis at $z \in (0, h)$, and exact upper circular section `Circle3` ($r = R(1 - z/h)$), while computing exact residual/frustum volume $V_{\text{frustum}} = V_{\text{cone}} - V_{\text{upper\_cone}} = \frac{1}{3}\pi h_{\text{cut}}(R^2 + Rr + r^2)$ via certified cone ratio when requested, or visualizing the cone + parallel circular cut.
    - **Standalone `cone_frustum` primitive without parent cone:** `BLOCKED_BY_KERNEL` — `backend/app/simulation/geometry/curved.py` (`KHOI_CONG`) and `simulation_state.py` (`CurvedSolid`) only define 3 curved primitives (`"ball"`, `"cylinder"`, `"cone"` with a single `radius_sq`). Per P4 rules (*"If an analytical kernel or required contract is missing, do not falsely declare full support... classify as BLOCKED_BY_CONTRACT or BLOCKED_BY_KERNEL with concrete evidence"*), standalone `cone_frustum` without a parent cone is explicitly classified as `BLOCKED_BY_KERNEL` (`curved.py::KHOI_CONG` has no two-radius `r1_sq, r2_sq` primitive).

---

## 3. Post-Session-2 Verification & Visual Acceptance Summary (P3–P9)

- **P3 — Simulation Breakage Fixes (`RED -> GREEN`):**
  - Fixed scalar-radius (`rim_point: null`, `radius_sq: R^2`) and scalar-height (`apex_or_top: null`, `height_sq: h^2`) `curved_solid` rendering and Z-axis bounding box in `frontend/src/simulations/domains/geometry/scene3d-view.tsx` and `scene3d-model.ts`.
  - Classified `segment3`, `circle3`, `ellipse3`, and `curved_solid` in `frontend/src/simulations/domains/geometry/interaction-state.ts` (`HANG_MUC` & `laKhoi`).
  - Mapped `construct_curved_solid` to `CREATE` and `circle3`/`ellipse3` events to `CREATE` / `GEOMETRY_CONSTRUCTION` in `backend/app/simulation/semantic_program/scene3d.py` & `simulation_state.py`.
- **P4 — Curved Solid Expansion (`RED -> GREEN`):**
  - Extended `backend/app/simulation/geometry_functions/typed_fact_next.py` (`typed-fact-next/1`) and `backend/app/ai/adapter3_simulation.py` (`hybrid-simulation-adapter/3`) to compile and certify right circular cylinders (`cylinder`), right circular cones (`cone`) + parallel circular sections (`Circle3`) and oblique elliptic sections (`Ellipse3`), and spheres (`sphere` / `"ball"`) + plane circular sections (`Circle3`), delegating kind dispatch to `curved.py::KHOI_CONG`.
- **P6 & P7 — Executable Demo Suite & Real Browser Visual Acceptance (`visual-acceptance-receipt.json`):**
  - `9` deterministic demo envelopes in `demos/demo1..demo7*.json` (`8` positive interactive `Scene3D` demos + `1` fail-closed refusal demo).
  - Audited in headless Chromium WebGL (`run_browser_audit.mjs`): `totalConsoleErrors = 0`, `totalPageErrors = 0`, `inkPixels > 519,000` on all 8 positive demos, `ownPixels > 0` for every primary object (`solid`, `curved_solid`, `section`, `polygon3`, `circle3`), `orbitDiffPixels > 0`, `zoomDiffPixels > 0`, `panDiffPixels > 0`, `selectionDiffPixels > 0`, `step0DiffPixels > 0`, `labelCollisions = 0`, and `labelsNotCollapsed = true`.
- **P8 — Simulation-Centered Offline Evaluation (`eval-summary.json`, `corpus-dev.json`):**
  - `DEVELOPMENT_EVALUATION_NOT_BLIND` (`15` cases: `10` positive + `5` negative): `10/10` positive served, `5/5` negative refused with exact refusal codes, `0` wrong serves, and `10/10` pass across all 8 simulation criteria (`scene3d_valid_v2`, `solid_topology_complete`, `derived_section_correct`, `derived_point_provenance_ok`, `multi_solid_identity_ok`, `curved_solid_render_ok`, `timeline_dependency_order_ok`, `math_certificate_consistent`).
