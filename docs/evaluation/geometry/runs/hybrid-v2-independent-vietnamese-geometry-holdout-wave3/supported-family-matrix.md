# supported-family-matrix.md — Contract-Level Supported Family Matrix (Baseline `e137623c4f674135a8d7884b78614c132eb78085`)

This document defines the **contract-level** family and capability matrix of AlgoSim Hybrid V2 at authoritative baseline `e137623c4f674135a8d7884b78614c132eb78085` (Product commit `73ca8d92e74059680ce53b99692af396df37a2f8`, Frozen Full T3 candidate `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`, `118` product files, `measured_system.tree_hash = 1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`).

| Component | Version / Pin |
|---|---|
| Input Contract | `typed-fact-next/2` (`backend/app/simulation/geometry_functions/typed_fact_next.py`) |
| Bridge | `typed-fact-next-bridge/2` |
| Registry / Source Gate | `geometry-functions/19` |
| Planner | `geometry-fact-planner/17` |
| Engine | `geometry-function-engine/14` |
| Adapter | `hybrid-simulation-adapter/4` (`hybrid-route-d-simulation/4`) |
| Section Certificate | `plane-section-certificate/1` |
| Cache / Mode | `CACHE_VERSION = "130"` · `DEFAULT_MODE = LLM_ONLY` (Hybrid opt-in only) |

---

## 1. Supported Polyhedral Solid Families (`solids`)

| Family ID | `solid_type` in `/2` | Typical Notation | Contract-Level Base & Altitude Requirements |
|---|---|---|---|
| `triangular_pyramid` | `"pyramid"` | `S.ABC`, `A.BCD`, `S.MNP` | Triangular base (`base_vertices` length 3) with exact rational Gram metric: right triangle (`right_angle` at a base vertex + 2 legs, or leg + hypotenuse) or equilateral triangle (`base_is_equilateral_triangle` / `regular_polygon` + side length); apex placed via `perpendicular_line_plane` (e.g. `SA ⊥ (ABC)` + `segment_length` of `SA`), `regular_pyramid` + `height` (or lateral edge), or `orthogonal_projection` of apex onto a determined base vertex + length. |
| `quadrilateral_pyramid` | `"pyramid"` | `S.ABCD`, `S.MNPQ` | Quadrilateral base (`base_vertices` length 4): square (`base_is_square` + `side`, or `base_is_square` + separate `segment_length`) or rectangle (`rectangle` + 2 adjacent side lengths); apex placed via `perpendicular_line_plane` (e.g. `SA ⊥ (ABCD)` + `segment_length`), `regular_pyramid` + `height` (with square base), or `orthogonal_projection` of apex onto a base vertex + length. |
| `right_triangular_prism` | `"prism"` | `ABC.A'B'C'`, `MNP.M'N'P'` | `right_prism` (`base: ["A","B","C"], top: ["A'","B'","C'"]`) + right-triangle or equilateral-triangle base metric + lateral edge `segment_length` (e.g. `AA'`). |
| `oblique_triangular_prism` | `"prism"` | `ABC.A'B'C'`, `MNP.M'N'P'` | Triangular prism (`solid_type: "prism"`, without `right_prism`) + right-triangle or equilateral-triangle base metric + `orthogonal_projection` of a top vertex (e.g. `point: "A'"`, `image: "B"` or `"C"`, `plane: ["A","B","C"]`) onto a determined base vertex + `segment_length` of that perpendicular segment (e.g. `A'B`). |
| `cuboid` | `"prism"` | `ABCD.A'B'C'D'`, `MNPQ.M'N'P'Q'` | Rectangular cuboid: `right_prism` (`base: ["A","B","C","D"], top: ["A'","B'","C'","D'"]`) + `rectangle` (`vertices: ["A","B","C","D"]`) + 2 adjacent base edge lengths (`AB`, `AD`) + lateral edge length (`AA'`). |
| `cube` | `"prism"` | `ABCD.A'B'C'D'`, `MNPQ.M'N'P'Q'` | Cube: `right_prism` (`base: ["A","B","C","D"], top: ["A'","B'","C'","D'"]`) + `base_is_square` (`vertices: ["A","B","C","D"]`, `side: "<L>"`) + lateral edge `segment_length` (`AA' = "<L>"`). |

### Unsupported Solid Topologies (Must Refuse)
- Curved solids (`cylinder`, `cone`, `sphere`, `frustum`) $\rightarrow$ `BRIDGE_UNSUPPORTED_CURVED`.
- Non-identity multi-solid `vertex_bindings` $\rightarrow$ `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY`.
- Rhombus, general parallelogram, or general quadrilateral base without right-angle rectangular reduction $\rightarrow$ `UNSUPPORTED_BASE_SHAPE`.
- Regular polygons with $n \notin \{3, 4, 6\}$ $\rightarrow$ `UNSUPPORTED_REGULAR_POLYGON`.

---

## 2. Supported Cutting-Plane Categories & Relations (`derived_sections`)

### 2.1 Category B — Plane-Only Derived Sections (`ENGINE_DERIVED_SECTION`, `plane-section-certificate/1`)
The problem text defines the cutting plane by a `through_point` and a directional relation without stating the individual cut points on the solid's edges (`stated_intersections: []`).

| Relation ID | `plane_kind` in `/2` | Contract Requirements | Refusal Conditions |
|---|---|---|---|
| `perpendicular_line` | `"through_point_perpendicular_line"` | `through_point` (a determined point: solid vertex, `midpoint`, or `divide_segment` point on an edge) and `perpendicular_line: [U, V]` joining two vertices of the cut solid. | Reference line not joining two vertices of the solid, degenerate line, or plane does not cut the solid into a polygon of $\ge 3$ vertices / coincides with a face. |
| `parallel_plane` | `"through_point_parallel_plane"` | `through_point` and `parallel_plane: [U, V, W, ...]` ($\ge 3$ coplanar vertices of the solid defining a reference plane). | `through_point` lies inside `parallel_plane` (`DERIVED_PLANE_IS_REFERENCE`), plane coincides with a face (`SECTION_PLANE_IS_FACE`), or plane only touches a vertex/edge (`PLANE_TOUCHES_VERTEX`, `PLANE_TOUCHES_EDGE`, `PLANE_DOES_NOT_CUT`). |
| `parallel_two_lines` | `"through_point_parallel_two_lines"` | `through_point`, `parallel_line_a: [U, V]`, `parallel_line_b: [W, X]`, and `plane_name` (two non-parallel lines between vertices of the solid). | Parallel/collinear direction lines (`DEGENERATE_PLANE_DIRECTIONS`), `through_point` creates a face plane (`SECTION_PLANE_IS_FACE`), or plane does not cut the interior. |

### 2.2 Category A — Source-Stated Lateral-Edge Intersections (`DINH_CAT_CANH`)
The problem text defines the cutting plane via a `through_point` (which lies on one lateral edge — either as a solid vertex such as `A` or `A'` with $t \in \{0, 1\}$, or as a `midpoint` / `divide_segment` point on that lateral edge with $0 < t < 1$) and one of the three supported directional relations (`through_point_perpendicular_line`, `through_point_parallel_plane`, `through_point_parallel_two_lines`), **and** explicitly states that the plane cuts the remaining lateral edges (`stated_intersections` non-empty):
- **Lateral edges of a pyramid `S.B1..Bk`:** `[S, B1], [S, B2], ..., [S, Bk]`.
- **Lateral edges of a prism `B1..Bk.T1..Tk`:** `[B1, T1], [B2, T2], ..., [Bk, Tk]`.
- On the lateral edge that already contains `through_point`, the planner reuses `through_point` (`reuse_through_point`, cost 0); that edge is **not** listed in `stated_intersections`.
- On each of the remaining lateral edges cut by the plane, `stated_intersections` contains an entry `{"edge": [U, V], "point": "<LABEL>" | null, "quote": "..."}`:
  - If the Vietnamese text names the intersection points (e.g., `"cắt các cạnh bên SB, SC lần lượt tại M, N"` or `"cắt BB', CC', DD' lần lượt tại M, N, P"`), set `"point": "M"` etc. (Note: those intersection points are produced by the plane-edge intersection itself and must **not** also be declared as `divide_segment` / `midpoint` premises in `premises`).
  - If the Vietnamese text states the cut edges without naming the points (e.g., `"cắt các cạnh bên BB', CC', DD'"`), set `"point": null`.
- All cut points on the lateral edges must lie strictly within the segment ($0 \le t \le 1$) and form a closed convex polygon of $\ge 3$ vertices.

### 2.3 Supported Natural Vietnamese Phrasings in Registry `/19`
Registry `/19` supports both canonical textbook phrasings and natural Vietnamese variants when accurately quoted from `problem_text`:
- Right angle: `"vuông tại A"`, `"tam giác vuông ở A"`, `"có góc ABC = 90°"`, `"AB ⊥ BC"`.
- Perpendicular line-plane: `"SA vuông góc với mặt phẳng (ABC)"`, `"SA vuông góc với đáy"`, `"có đường cao SA"`, `"SA ⊥ (ABC)"`.
- Orthogonal projection: `"hình chiếu vuông góc của A' trên mặt phẳng (ABC) trùng với B"`, `"chân đường cao hạ từ A' xuống (ABC) là B"`.
- Midpoint & segment division: `"M là trung điểm của SA"`, `"điểm M trên cạnh SA sao cho SM = 1/3 SA"`, `"điểm M thuộc đoạn SA thỏa mãn AM = 2/5 AS"`.
- Parallel/perpendicular plane relations: `"song song với mặt phẳng (ABC)"`, `"song song với đáy (ABC)"`, `"song song với hai đường thẳng AB và SC"`, `"vuông góc với đường thẳng SB"`.

---

## 3. Supported Question Types (`simulation_goals` & `math_goals`)

1. **`section_only`**:
   - Problem text asks to determine/identify the section (e.g., `"Xác định thiết diện của ... cắt bởi mặt phẳng ..."`).
   - `simulation_goals`: `[{"goal_id": "sg1", "kind": "construct_plane_section", "target_section_id": "sec", "target_solid_id": "s1", "quote": "..."}]`
   - `math_goals`: `[]`
2. **`area_only`**:
   - Problem text asks only for the area of the section (e.g., `"Tính diện tích thiết diện của ... cắt bởi mặt phẳng ..."`), without a separate `"Xác định thiết diện"` sentence.
   - `simulation_goals`: `[{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "..."}]`
   - `math_goals`: `[{"goal_id": "mg1", "kind": "measurement", "goal_type": "area", "solid_id": "s1", "target": {"section_id": "sec"}, "quote": "..."}]`
3. **`section_and_area`**:
   - Problem text asks both to determine the section and to compute its area.
   - `simulation_goals`: `[{"goal_id": "sg1", "kind": "construct_plane_section", "target_section_id": "sec", "target_solid_id": "s1", "quote": "..."}]`
   - `math_goals`: `[{"goal_id": "mg1", "kind": "measurement", "goal_type": "area", "solid_id": "s1", "target": {"section_id": "sec"}, "quote": "..."}]`

---

## 4. Homogeneous Length Units

- Every problem must use either purely numeric lengths (`length_unit = "1"`, e.g. `"4"`, `"7"`, `"10"`) or purely symbolic lengths in `a` (`length_unit = "a"`, e.g. `"3a"`, `"5a"`, `"a√3"`).
- Mixing bare numeric lengths and symbolic `a` lengths in the same problem is refused (`NON_HOMOGENEOUS_LENGTHS`).
