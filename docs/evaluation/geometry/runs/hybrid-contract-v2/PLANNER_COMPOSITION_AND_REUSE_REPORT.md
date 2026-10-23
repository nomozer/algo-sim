# PLANNER_COMPOSITION_AND_REUSE_REPORT.md — Bounded Section-Vertex Derivation (`D6`) & IR Budget Audit (`D4`)

- **Run**: `hybrid-contract-v2` (Backend Hybrid Session 3)
- **Authorization**: `GO_HYBRID_SESSION3_CONTRACT_V2_LOCAL_RESEARCH` (`D4 KEEP 32`, `D6 GO-limited`)
- **Product Commit**: `69bd2fe48be1fd3afa6ce4112ccddda92a07d850`

---

## 1. Contract-Driven Section-Vertex Derivation (`D6 GO-limited`)

### 1.1 Registry `PlanningContract` (`backend/app/simulation/geometry_functions/registry.py:451–457`)
`REGISTRY["intersect_line_plane"]` declares an explicit `PlanningContract`:
```python
PlanningContract(
    inputs=(PlanningTerm("Line", ("L",)), PlanningTerm("Plane", ("Q",))),
    effect=PlanningTerm("Meet", ("X", "L", "Q")),
    source_policy="section_vertex",
    verifier="_construction_relation",
    call=(("point", "X"), ("line", "L"), ("plane", "Q")),
    fresh="I",
)
```
- Because `effect.kind == "Meet"` is never requested by any general descriptor or goal contract, general backward proof search (`_tim_day_chung_minh`) never selects `intersect_line_plane`.
- Only `planner._dinh_cat_canh` queries `_hop_dong_giao_diem()` for section-edge intersections on lateral edges of the target solid.

### 1.2 Cost-Ordered Candidate Selection (`backend/app/simulation/geometry_functions/planner.py:1192–1291`)
For each lateral edge `e = (u, v)` of the target solid `kh`:
- **Cost `0` (Reuse existing point)**:
  - `reuse_through_point`: the section plane's through-point `M` is already defined on `e` by a `midpoint` or `divide_segment` premise, or `M` is an endpoint of `e`. Zero new `intersect_line_plane` calls are emitted. Under `G7`, if `e` was also listed in `stated_intersections` with `point == M`, `M` is still reused at cost `0` while `"stated_point": "M"` is recorded in the `DINH_CAT_CANH` certificate so `registry._kiem_dinh_cat` validates the full stated cut list.
  - `reuse_intersection`: an existing `intersect_line_plane` call already intersects `e` with `plane`.
- **Cost `1` (Source-stated cut)**:
  - `named_intersection` (when `e` is in `stated_intersections` with `point = "N"`): emits `intersect_line_plane(point="N", line=[u, v], plane=plane)`.
  - `fresh_intersection` (when `e` is in `stated_intersections` with `point = None`): allocates a fresh internal label (`I, I1, ...`) and emits `intersect_line_plane`.
- **Cost `2` (Bounded `D6` planner-derived unstated cut)**:
  - `derived_fresh`: admitted **only** when `choices` is empty (the source did not state `e` and no through-point/intersection exists on `e`) **and** `(khep or e in bien)`, where:
    - `khep = bool(f.derive_cuts) and any(x.plane_ref == f.id for x in r.facts.values())` (a derived solid stands on this section), or
    - `e in bien` (the payload supplied an explicit `declared_boundary` to be verified).
  - Allocates a fresh internal label (`I, I1, ...`) and emits `intersect_line_plane` with `choice: "derived_fresh"`.
- **Early Return on Plane-Only Sections (`I-1` fix, `planner.py:1223–1224`)**:
  - When `not stated and not khep and f.boundary_edges is None` (a plane-only section requesting only `construct_plane_section` and/or `measurement(area)` without a derived solid or `declared_boundary`), `_dinh_cat_canh` returns immediately without emitting a vacuous `DINH_CAT_CANH` certificate.

### 1.3 Triple Verification Gate (`Source Gate` + `Engine Interior Parameter` + `Closure Certificate`)
1. **Source Gate (`registry._kiem_dinh_cat`, `registry.py:3685–3766`)**:
   - Verifies every `stated: True` vertex against `_cum_cat_canh` in the section quote.
   - Verifies that `derived_fresh` only appears when `d.get("derive")` is true and `(isinstance(d.get("derived"), dict) or e in bien)`, that `e` was not stated in the source, and that its label is fresh (`x not in nhan`).
   - Exempts validated `DINH_CAT_CANH` fresh labels from `UNKNOWN_LABEL` only on `ask_volume_ratio` and `ask_residual_volume` (`registry.py:1981–1982`).
2. **Engine Interior Parameter Check (`engine.kiem_dinh_cat`, `engine.py:1299–1330`)**:
   - Computes exact rational cut parameter `t` along each lateral edge via `_tham_so_giao_canh` and requires `0 < t <= 1` (`DEGENERATE_CONFIGURATION` if parallel or outside `(0, 1]`).
3. **Engine Closure Certificate (`engine.chung_chi_khep_kin`, `engine.py:1341–1361`)**:
   - Whenever `derived`, `declared_boundary`, or `derived_fresh` is present (`engine.py:1336–1339`), computes the true 3D cross-section polygon `cross_section(Polyhedron(...), self._plane(mat[:3])).polygon` and requires `same_section_cycle([Vec3(*self.pts[p]) for p in vong], that)` (dihedral group equivalence: cyclic rotation or reversal of the true 3D polygon cycle), refusing with `SECTION_BOUNDARY_INCOMPLETE` otherwise.
4. **Learner-Facing Label Stripping (`function_route._an_dinh_thiet_dien_phu`, `function_route.py:98–174`)**:
   - Strips all `fresh_intersection` and `derived_fresh` internal labels (`I, I1, ...`) from `Scene3D` points, segments, polygons, polyhedra, events, and formation steps (`0` label leaks across all `50/50` served Session 1 `/2` cases).

---

## 2. Planner Composition & Reuse Metrics (`session3-evaluation-summary.json`)

Across the **49 served Session 1 family cases** (`session1-family-replay.json`) and **38 composition plans** (`family_f_ir_budget_and_composition.composition`):

| Metric | Session 1 Replay (`49` served) | Family F Composition (`38` plans) |
|---|---:|---:|
| `duplicate_calls` | `0` | `0` |
| `plane_constructions_per_section` | `[1]` | `[1.0]` |
| `dag_depth` (`[min, max]`) | `[4, 5]` | `[4, 5]` |
| `declarations` (`[min, max]`) | `[18, 30]` | `[18, 30]` |
| `selection_counts.reuse_through_point` | `49` | `38` |
| `selection_counts.named_intersection` | `104` | `90` |
| `selection_counts.fresh_intersection` | `14` | `5` |
| Distinct multi-function composition patterns | `8` | — |

---

## 3. IR Memory Budget Audit (`D4 KEEP 32`)

### 3.1 Why `mp_td_<section_id>` Remains Distinct from `derived_<first_cut>_plane`
In `engine.py`, a section problem with cut-edge intersections emits:
1. `derived_<first_cut>_plane` (`non_visual` auxiliary plane constructed before the first `intersect_line_plane` call so that cut points `N, P, Q` can be intersected in topological birth order).
2. `mp_td_<section_id>` (`surface_role="CUTTING_PLANE"` visual cutting plane emitted by `_bien_dich_mat_cat`).

Keeping `mp_td_<section_id>` distinct from `derived_<first_cut>_plane` preserves three invariants while staying well inside the `32`-declaration budget (`MAX_MEMORY_DECLARATIONS = 32` in `validator.py:143`):
- **Topological birth order (`_validate_scene`)**: `derived_<first_cut>_plane` must precede `intersect_line_plane(N, ...)`, whereas `mp_td_<section_id>` is bound to the `section` goal step.
- **Visual ownership (`_an_dinh_thiet_dien_phu`)**: `derived_<first_cut>_plane` is marked `non_visual` (`style="hidden"`), whereas `mp_td_<section_id>` carries `surface_role="CUTTING_PLANE"` for Scene3D rendering.
- **Deduplication of all other operand planes/lines (`gop_doi_tuong_trung`)**: `gop_doi_tuong_trung` (`engine.py:188–218`) collapses all subsequent `derived_<cut_i>_plane` and duplicate line declarations onto the first declaration (`plane_constructions_per_section = 1.0`, `ir_duplicate_constructs = 1` per section plan).

### 3.2 Budget Probe Results (`family_f_ir_budget_and_composition.budget`)

| Probe ID | Base Polygon | Plane Relation | Status (Cap = 32) | Code | IR Declarations (Uncapped) | Duplicate Constructs |
|---|---|---|---:|---|---:|---:|
| `BUD-equilateral0-parallel` | Triangle (`3`) | Parallel to base | `SERVED` | `null` | `24` | `1` |
| `BUD-equilateral0-perpendicular` | Triangle (`3`) | Perpendicular to `SA` | `SERVED` | `null` | `27` | `1` |
| `BUD-square1-parallel` | Square (`4`) | Parallel to base | `SERVED` | `null` | `27` | `1` |
| `BUD-square1-perpendicular` | Square (`4`) | Perpendicular to `SA` | `SERVED` | `null` | `30` | `1` |
| `BUD-rectangle2-parallel` | Rectangle (`4`) | Parallel to base | `SERVED` | `null` | `27` | `1` |
| `BUD-rectangle2-perpendicular` | Rectangle (`4`) | Perpendicular to `SA` | `SERVED` | `null` | `30` | `1` |
| `BUD-hexagon-parallel` | Hexagon (`6`) | Parallel to base | `REFUSED` | `IR_MEMORY_BUDGET_EXCEEDED` | `33` | `1` |
| `BUD-hexagon-perpendicular` | Hexagon (`6`) | Perpendicular to `SA` | `REFUSED` | `IR_MEMORY_BUDGET_EXCEEDED` | `36` | `1` |

All triangular and quadrilateral pyramid/prism section + derived solid + volume ratio + residual volume problems fit within `18–30 <= 32` declarations, while hexagonal pyramids (`33–36` declarations) fail closed with `IR_MEMORY_BUDGET_EXCEEDED` in accordance with Owner Decision `D4 KEEP 32`.
