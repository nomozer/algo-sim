# Architecture Decision Record — W2-M5 Adapter `/4` Category A Identity Binding & Verification

- **Task ID**: `HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR`
- **Status**: `DECIDED_WITHIN_ADAPTER_SCOPE` (no architectural change outside `backend/app/ai/adapter4_route.py` required)

---

## 1. Decision Summary

1. **Root Cause Classification**:
   - Both `W2-A07` and `W2-A10` are complete Category A (`DINH_CAT_CANH`) section problems whose exact coordinates, polygon cycles, and areas are already computed and served by Planner `/17` and Engine `/14`.
   - Their refusal in `build_adapter4_response` is caused solely by an internal point-identity lookup mismatch in `_validate_sections` (`backend/app/ai/adapter4_route.py:261` and `:287`), where learner-facing vertex labels (`"A'"`) are used as raw dictionary keys into `objects` (`{o["id"]: o for o in scene["objects"]}`), which keys primed points by `ir_name("A'") == "A_prime"`.
   - Therefore, this defect is **100% solvable within `backend/app/ai/adapter4_route.py`** without modifying Registry `/19`, Planner `/17`, Engine `/14`, or the Category A / Category B contract boundary.

2. **Canonical Lookup Boundary (`_point(label)` in `_validate_sections`)**:
   - Canonicalization is applied **strictly at the internal `scene3d.objects` lookup boundary** inside `_validate_sections`:
     - Input `label` must be a non-empty `str` and must **not** contain `"_prime"` (preventing machine-ID leakage such as `"A_prime"` in Category A `vertices`, `edge`, or `boundary`).
     - `canon = name(label)` normalizes prime glyphs (`"″" -> "''"`, `"′" -> "'"`, `"’" -> "'"`).
     - `pt = objects.get(ir_name(canon))` resolves the `point3` object in `scene3d["objects"]`.
     - If `pt` is missing or `pt.get("type") != "point3"`, raise `PreviewInvalid("PREVIEW_RESULT_INVALID")`.
     - If `pt.get("notation") is not None` (named source points, which always carry `notation` for primed labels like `"A′"`), require `name(str(pt.get("notation"))) == canon`.
     - If `pt.get("notation") is None` (derived points or unprimed points without `notation`), require `pt["id"] == label`.
   - Learner-facing payloads (`route_d["sections"]`, `scene3d["objects"][*]["notation"]`, `steps`, `final_answer`) remain untouched.

3. **Independent Category A Geometric & Tamper Verification in `_validate_sections`**:
   To guarantee that canonical lookup never weakens fail-closed verification, `_validate_sections` enforces all Category A structural and geometric invariants:
   - **Category A / B Separation**: Category A sections must not carry `certificate_category` or `certificate_version`, and when `result is not None`, `section["id"]` must match a `DINH_CAT_CANH` entry (`d_aux`) in `result.planner["auxiliary"]`.
   - **Solid Identity**: Exactly one `solid` object in `scene3d["objects"]` must be referenced by `obj["depends"]`, its `vertex_ids`/`vertices`/`faces` must be self-consistent, and when `d_aux` is present, `name(solid["notation"]) == name(d_aux["solid"])`.
   - **Vertex Uniqueness**: `len(labels) == len(set(labels)) == len(obj["polygon"]) >= 3`, and resolved `point["id"]` and `point["xyz"]` sets must also have cardinality `len(obj["polygon"])` (blocking alias duplicates such as `"A'"` + `"A′"`).
   - **Edge Membership & Exact Rational Parameter $t \in [0, 1]$**:
     - Each `vertex["edge"]` must have 2 endpoints resolving via `_point` to `solid` vertices that form an actual face edge of `solid`.
     - `obj["vertex_sources"][index]` (`SOLID_VERTEX` vs `SOLID_EDGE_INTERSECTION`) must match `point["id"]` and `edge`.
     - Using exact `Fraction` arithmetic on `point["xyz"]` and the two edge endpoint coordinates, `point["xyz"]` must be collinear with the edge segment with parameter $t \in [0, 1]$ ($t \in \{0, 1\}$ for `SOLID_VERTEX`, $0 < t < 1$ for `SOLID_EDGE_INTERSECTION`).
   - **Cyclic Face-Adjacency Topology & Boundary**:
     - Consecutive vertices around `obj["polygon"]` (`0..m-1`) must share a common face of `solid`, preventing bow-tie or non-adjacent vertex permutations even when `boundary is None`.
     - When `boundary` is present, `[_point(label)["xyz"] for label in boundary]` must match `obj["polygon"]` up to cyclic shift/reversal (`cycle(...)`), and any derived solid on `sid` must match `same_section_cycle(...)` and `cross_section(...)`.
   - **Provenance & Statedness**:
     - `THROUGH_POINT_REUSE`: `point.get("notation") is not None`.
     - `SOURCE_NAMED`: `stated is True`, `point.get("notation") is not None`.
     - `STATED_UNNAMED` / `DERIVED_FRESH`: `point.get("notation") is None`, `point.get("role") == "Điểm dựng phụ"`, `stated == (provenance == "STATED_UNNAMED")`, and `origin == "derived"` for `DERIVED_FRESH`.
     - When `d_aux` is present, `vertex["stated"]` must equal membership of `frozenset(vertex["edge"])` in `d_aux["stated_edges"]`.
   - **Exact Area-Squared Agreement**:
     - When `result.chart_metric` is present, `_polygon_area_squared` verifies coplanarity, convexity, and positive area `area_sq > 0`, and any `ask_section_area` call on the same solid whose defining plane points lie on the section plane must satisfy `_binh_phuong(kq_<id>) == area_sq`.

4. **Version & Cache Policy**:
   - `ADAPTER_V4_VERSION` remains `"hybrid-simulation-adapter/4"` (this is a bugfix to Category A internal identity lookup and validation within the Adapter `/4` contract, and existing Adapter `/4` tests pin `ADAPTER_V4_VERSION == "hybrid-simulation-adapter/4"`).
   - `CACHE_VERSION` remains `130`: `DEFAULT_MODE` is `LLM_ONLY`, the prompt/schema/IR/cached preview format is unchanged, and all 41 stored preview fixtures in `docs/evaluation/preview-fixtures/v1/` remain 100% valid (`verified=41, errors=0`).
