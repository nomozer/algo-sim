# Baseline Audit — Adapter `/4` Plane-Only Section Certificate

- **Baseline Commit**: `a3ee14a707f35dddd70a52f551d23beb16476c41`
- **Branch**: `research/hybrid-v2-adapter4-plane-section-certificate`
- **Component Versions**:
  - `REGISTRY_VERSION = "geometry-functions/17"`
  - `PLANNER_VERSION = "geometry-fact-planner/16"`
  - `ENGINE_VERSION = "geometry-function-engine/14"`
  - `ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"`
  - `CACHE_VERSION = "130"`
  - `DEFAULT_MODE = "LLM_ONLY"`

---

## 1. Exact Mechanism of the `ADAPTER_INTEGRATION_GAP`

### 1.1 Planner & Engine Execution on Plane-Only Derived Sections
1. When a problem specifies a cutting plane by geometric relation (`through_point_perpendicular_line`, `through_point_parallel_plane`, or `through_point_parallel_two_lines`) without stating individual edge-cut points (`stated_intersections = ()`, `declared_boundary = None`, and no `construct_derived_solid` goal):
   - In `backend/app/simulation/geometry_functions/planner.py`:
     - `_mat_qua_diem` (lines 1056–1125) or `_mat_vuong_duong` (lines 1128–1191) emits the auxiliary plane construction (`translate_point` and, for `MAT_VUONG_DUONG`, `orthogonal_projection_line`) and records the derived plane entry `d` in `k.auxiliary` with `rule` in `{MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG}`.
     - `_dinh_cat_canh` (lines 1209–1310) checks `if not stated and not khep and f.boundary_edges is None: return` (lines 1240–1241) and returns without emitting a `DINH_CAT_CANH` entry. (Moreover, `_dinh_cat_canh` only inspects lateral edges `_canh_ben(kh)`, whereas general plane sections—such as `right-base`, `cuboid-base`, `cube-diagonal`, etc.—intersect base and/or top edges as well as lateral edges.)
   - In `backend/app/simulation/geometry_functions/engine.py`:
     - `_kiem_mat_phu` (lines 1468–1511) and `_kiem_mat_vuong_duong` (lines 1451–1466) deterministically verify the cutting plane in the chart Gram metric (passing through `point`, parallel/perpendicular to the reference object, distinct from the reference plane, and not a boundary face of the solid via `SECTION_PLANE_IS_FACE`).
     - `_bien_dich_mat_cat` (lines 1523–1548) deduplicates sections by normalized plane equation `_khoa_mat_cat(c)` and emits `construct_plane` (`mp_td_<sid>`) and `construct_section` (`td_<sid>`).
     - During `SemanticProgramInterpreter().execute(spec)` (line 1826), `section.cross_section(sol, pl)` (`backend/app/simulation/geometry/section.py:526–605`) computes the exact `Section(polygon, steps, vertex_sources)` over `Fraction`, where each vertex carries an exact `SectionVertexSource`:
       - `SectionVertexSource("SOLID_VERTEX", solid_vertex_index=index)` when the cutting plane passes through solid vertex `index`, or
       - `SectionVertexSource("SOLID_EDGE_INTERSECTION", solid_edge_vertex_indices=(ia, ib))` when the cutting plane intersects topological solid edge `(ia, ib)` strictly in its interior ($0 < t < 1$).
   - In `backend/app/simulation/semantic_program/scene3d.py` (`_attach_topology`, lines 220–280):
     - `td_<sid>` is emitted with `type: "section"`, `polygon`, `vertex_sources`, `endpoint_entities` (with `entity_id` bound to either the solid vertex ID or `section:td_<sid>:point:on:<solid_id>::edge:<u>-<v>` and `anonymous_coordinate_fallback: False`), and `boundary_edge_ids`.

### 1.2 Exact Failure Point in `adapter4_route.py`
1. In `backend/app/ai/adapter4_route.py`:
   - `_phong_bi(r)` (lines 55–72) builds `route_d["sections"]` by filtering `(r.planner or {}).get("auxiliary") or []` exclusively for `d.get("rule") == DINH_CAT_CANH`:
     ```python
     for d in (r.planner or {}).get("auxiliary") or [] if served else []:
         if d.get("rule") != DINH_CAT_CANH:
             continue
     ```
     Consequently, for every plane-only section (both prism/cuboid/cube and pyramid), `r.route_d["sections"]` is `[]`.
   - When `build_adapter4_response(result, problem_text)` runs, it calls `_validate_sections(route["sections"], objects)` (line 190).
   - At line 262 of `adapter4_route.py`:
     ```python
     if len(ids) != sum(o["type"] == "section" for o in objects.values()):
         raise PreviewInvalid("PREVIEW_RESULT_INVALID")
     ```
     Because `len(ids) == 0` while `objects` contains `td_<sid>` (`type == "section"`), `_validate_sections` raises `PreviewInvalid("PREVIEW_RESULT_INVALID")`, and `build_adapter4_response` refuses the valid, Engine-verified result!

---

## 2. Secondary Presentation Audit Finding (`function_route.py`)

During baseline inspection of plane-only prism parallel-plane sections (e.g. `CORPUS-DEV10-prism-area` with `stated_intersections = []`, where plane `(α)` passes through midpoint `M` of `AA'` parallel to `(ABC)`):
- The planner constructs auxiliary points `H = M + AB` and `H1 = M + AC` (`d["labels"] = ["H", "H1"]`).
- Because `ABC.A'B'C'` is a prism, `H` and `H1` have the exact same coordinates as the intersections of `(α)` with lateral edges `BB'` and `CC'`.
- `display_names.py` matches section polygon coordinates against named points in memory and names the section `"Thiết diện HMH1"` (`notation: "HMH1"`) and its area `"Diện tích HMH1"` (`notation: "S(HMH1)"`).
- When `DINH_CAT_CANH` was present, `_an_dinh_thiet_dien_phu` (`function_route.py:259–277`) stripped `"HMH1"` and renamed the section `"Thiết diện bởi (α)"`. Without `DINH_CAT_CANH`, `"HMH1"` leaked into the learner-facing `scene3d` objects and events.
- **Fix**: In `function_route.py` (`_vai_mat_cat`), strip any section notation that leaks planner-internal auxiliary plane labels (`d["labels"]` / `d["feet"]`) on plane-only derived sections, renaming the section to `"Thiết diện bởi <plane>"` and rewriting its dependent quantities/events/steps via `_thay_ten`.
