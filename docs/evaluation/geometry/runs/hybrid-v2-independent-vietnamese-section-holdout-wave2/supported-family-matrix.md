# supported-family-matrix.md — Contract-Level Supported Family Matrix (Baseline `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c`)

This document defines the **contract-level** family and capability matrix of AlgoSim Hybrid V2 at frozen baseline `d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c` (Product commit `e3678608f1f7110d7046c9c43c312c69d7614f55`, T3 candidate `e7bcff316ee6d443e753105a887e0689ea04848b`, `118` product files, `measured_system.tree_hash = 84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`).

| Component | Version / Pin |
|---|---|
| Input Contract | `typed-fact-next/2` (`backend/app/simulation/geometry_functions/typed_fact_next.py`) |
| Bridge | `typed-fact-next-bridge/2` |
| Registry / Source Gate | `geometry-functions/18` |
| Planner | `geometry-fact-planner/17` |
| Engine | `geometry-function-engine/14` |
| Adapter | `hybrid-simulation-adapter/4` (`hybrid-route-d-simulation/4`) |
| Section Certificate | `plane-section-certificate/1` |
| Cache / Mode | `CACHE_VERSION = "130"` · `DEFAULT_MODE = LLM_ONLY` (Hybrid opt-in only) |

---

## 1. Supported Polyhedral Solid Families (`solids`)

| Family ID | Solid Type in `/2` | Typical Notation | Contract-Level Base & Altitude Requirements |
|---|---|---|---|
| `triangular_pyramid` | `solid_type: "pyramid"` | `S.ABC`, `A.BCD` | Triangular base (`base_vertices` length 3) with exact rational Gram metric (equilateral triangle, right triangle with 2 sides, or triangle with 3 sides satisfying triangle inequality); apex placed via `perpendicular_line_plane` (e.g. `SA ⊥ (ABC)`), `regular_pyramid` + `height`, or `altitude` / `orthogonal_projection` onto a determined base point with given length. |
| `quadrilateral_pyramid` | `solid_type: "pyramid"` | `S.ABCD` | Quadrilateral base (`base_vertices` length 4): square (`base_is_square` / `regular_polygon`), rectangle (`rectangle` + 2 adjacent sides), or right trapezoid (2 consecutive right angles + 3 lengths with rational layout); apex placed via `perpendicular_line_plane`, `regular_pyramid` + `height`, or `altitude` / `orthogonal_projection` onto a determined base point. |
| `right_triangular_prism` | `solid_type: "prism"` | `ABC.A'B'C'` | Triangular base with exact rational layout + `right_prism` premise (or lateral edge perpendicular to base) + lateral edge length / height. |
| `oblique_triangular_prism` | `solid_type: "prism"` | `ABC.A'B'C'` | Triangular base with exact rational layout + projection (`orthogonal_projection` / `altitude` / `perpendicular_line_plane`) of a top vertex onto a determined base point + lateral edge or altitude length. |
| `cuboid` | `solid_type: "prism"` | `ABCD.A'B'C'D'` | Rectangular cuboid: `right_prism` + `rectangle` base + 2 adjacent base edge lengths + lateral edge length. |
| `cube` | `solid_type: "prism"` | `ABCD.A'B'C'D'` | Cube: `right_prism` + `base_is_square` base + base edge length + equal lateral edge length. |

### Unsupported Solid Topologies (Must Refuse)
- Curved solids (`cylinder`, `cone`, `sphere`, `frustum`) $\rightarrow$ `BRIDGE_UNSUPPORTED_CURVED`.
- Non-identity multi-solid `vertex_bindings` $\rightarrow$ `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY`.
- Rhombus, general parallelogram, or general quadrilateral base without right-angle rectangular/right-trapezoid reduction $\rightarrow$ `UNSUPPORTED_BASE_SHAPE`.
- Regular polygons with $n \notin \{3, 4, 6\}$ $\rightarrow$ `UNSUPPORTED_REGULAR_POLYGON`.

---

## 2. Supported Cutting-Plane Categories & Relations (`derived_sections`)

### Category B — Plane-Only Derived Sections (`ENGINE_DERIVED_SECTION`, `plane-section-certificate/1`)
The problem text defines the cutting plane by a point and a directional relation without stating the individual cut points on the solid's edges (`stated_intersections` is empty `[]`).

| Relation ID | `plane_kind` in `/2` | Contract Requirements | Refusal Conditions |
|---|---|---|---|
| `perpendicular_line` | `through_point_perpendicular_line` | `through_point` (a determined point: solid vertex, midpoint, or ratio point on an edge) and `perpendicular_line` joining two vertices of the cut solid. | Reference line not joining two determined vertices, degenerate line, or plane does not cut the solid into a polygon ($\ge 3$ vertices) / coincides with a face. |
| `parallel_plane` | `through_point_parallel_plane` | `through_point` and `parallel_plane` ($\ge 3$ coplanar vertices of the solid defining a reference plane). | `through_point` lies inside `parallel_plane` (`DERIVED_PLANE_IS_REFERENCE`), plane coincides with a face (`SECTION_PLANE_IS_FACE`), or plane only touches a vertex/edge (`PLANE_TOUCHES_VERTEX`, `PLANE_TOUCHES_EDGE`, `PLANE_DOES_NOT_CUT`). |
| `parallel_two_lines` | `through_point_parallel_two_lines` | `through_point` and `parallel_lines` (two non-parallel lines `[U, V]`, `[W, X]` between vertices/points of the solid). | Parallel/collinear direction lines (`DEGENERATE_PLANE_DIRECTIONS`), `through_point` creates a face plane (`SECTION_PLANE_IS_FACE`), or plane does not cut the interior. |

### Category A — Source-Stated Edge Intersections (`DINH_CAT_CANH`)
The problem text explicitly states or names the points where the cutting plane intersects edges of the solid (`stated_intersections` is non-empty), optionally combined with a `through_point` (which may coincide with a solid vertex or be an interior point) and/or a directional relation (`through_point_perpendicular_line`, `through_point_parallel_plane`, `through_point_parallel_two_lines`, or `three_points`).
- Every stated intersection specifies `edge: [U, V]` and either a named point (`point: "M"`, placed on `edge` by a `midpoint` or `point_on_segment_ratio` premise) or an unnamed intersection (`point: null`).
- When a Category A section passes through a solid vertex (e.g., `through_point = "A"`), that vertex is a `SOLID_VERTEX` in the mathematical boundary (`{"vertex": "A"}`), whereas strict interior edge cuts ($0 < t < 1$) are `{"edge": ["U", "V"], "t": "p/q"}`.

### Unsupported Cutting-Plane Specifications (Must Refuse)
- `parallel_to_base_at_distance`, `parallel_to_base_at_ratio`, `plane_equation`, `axial_section` $\rightarrow$ `BRIDGE_UNSUPPORTED_PLANE_KIND`.
- Plane through a point perpendicular to a **plane** $\rightarrow$ `PLANE_NOT_UNIQUE`.

---

## 3. Supported Question Types (`simulation_goals` & `math_goals`)

1. **`section_only`**:
   - `simulation_goals`: `[{"goal_id": "...", "kind": "construct_plane_section", "target": "<section_id>", "solid_id": "<solid_id>", "quote": "..."}]`
   - `math_goals`: `[]`
2. **`area_only`**:
   - `simulation_goals`: `[{"goal_id": "...", "kind": "construct_plane_section", "target": "<section_id>", "solid_id": "<solid_id>", "quote": "..."}]`
   - `math_goals`: `[{"goal_id": "...", "kind": "measurement", "goal_type": "area", "target": "<section_id>", "solid_id": "<solid_id>", "quote": "..."}]`
   - The problem text asks for the area of the section (or the area of the named section polygon / anaphoric `"diện tích của nó"` referring unambiguously to the section) without a separate `"Xác định thiết diện"` sentence.
3. **`section_and_area`**:
   - Both `construct_plane_section` and `measurement` (`goal_type: "area"`) are asked in the problem text (either in two sentences/clauses or a combined request such as `"Xác định thiết diện ... và tính diện tích của thiết diện đó"`).

---

## 4. Homogeneous Length Units

- All lengths in a problem must be either purely numeric (`length_unit = "1"`, e.g. `"2"`, `"3"`, `"6"`) or purely symbolic in `a` (`length_unit = "a"`, e.g. `"a"`, `"2a"`, `"a√3"`).
- Mixing symbolic `a` lengths and bare numeric lengths in the same problem is refused (`NON_HOMOGENEOUS_LENGTHS`).
