# Baseline Audit — W2-A07 & W2-A10 First-Failure Diagnosis (`eb661971847c034500862299c5091f1f3d2a2998`)

- **Task ID**: `HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR`
- **Audited Baseline (`main`)**: `eb661971847c034500862299c5091f1f3d2a2998`
- **Frozen Product Tree Hash**: `8b94a5aa4a986e312ef423492b332bf25378868f6c9578767ba2ee7003c18369` (`118` files)
- **Active Versions**:
  - Registry: `geometry-functions/19`
  - Planner: `geometry-fact-planner/17`
  - Engine: `geometry-function-engine/14`
  - Adapter: `hybrid-simulation-adapter/4`
  - Certificate: `plane-section-certificate/1`
  - `CACHE_VERSION = 130`, `DEFAULT_MODE = LLM_ONLY`, `ALLOW_LIVE_AI = 0`

---

## 1. Executive Finding: `ADAPTER_SECTION_VERTEX_ID_CANONICALIZATION_GAP` vs `ADAPTER_PARTIAL_SECTION_COMPLETION_GAP`

We executed both `W2-A07` and `W2-A10` on baseline `eb661971847c034500862299c5091f1f3d2a2998` and inspected every stage from Bridge `/2` through `build_adapter4_response`.

1. **Both `W2-A07` and `W2-A10` are complete Category A (`DINH_CAT_CANH`) sections**, NOT partial-section completion gaps:
   - `W2-A07` (right triangular prism `ABC.A'B'C'`): the problem explicitly states that plane `(α)` passes through `A'` (on lateral edge `AA'`) and cuts lateral edges `BB'` and `CC'` at `M` and `N`. All 3 lateral edges (`AA'`, `BB'`, `CC'`) are covered (`3/3` vertices: `A'`, `M`, `N`).
   - `W2-A10` (cuboid `ABCD.A'B'C'D'`): the problem explicitly states that plane `(Q)` passes through `A'` (on lateral edge `AA'`) and cuts lateral edges `BB'`, `CC'`, and `DD'`. All 4 lateral edges (`AA'`, `BB'`, `CC'`, `DD'`) are covered (`4/4` vertices: `A'`, `I`, `I1`, `I2`).
2. **Why the label `ADAPTER_PARTIAL_SECTION_COMPLETION_GAP` appeared in the W2-M4 summary**:
   - In Holdout Wave 1 (`H042`), failure mode `M5` was genuinely a partial-section completion case (only 2 of 4 pyramid edges were stated as cut). When Holdout Wave 2 assigned the code `W2-M5` to the Adapter `/4` failure on `W2-A07` and `W2-A10`, the W2-M4 narrative report reused the Wave 1 `M5` prose description (`ADAPTER_PARTIAL_SECTION_COMPLETION_GAP`), whereas the Wave 2 evaluation report (`docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/report.md`) had already identified the true root cause as `ADAPTER_SECTION_VERTEX_ID_CANONICALIZATION_GAP` (`KeyError: "A'"`).
3. **Exact First Failing Operation in Product (`backend/app/ai/adapter4_route.py`)**:
   - File: `backend/app/ai/adapter4_route.py`, function `_validate_sections`, line `261`:
     ```python
     point = objects[vertex["label"]]
     ```
   - `objects` is constructed at line `220` as `{o["id"]: o for o in scene["objects"]}`.
   - For any primed point (such as `A'`), Engine `/14` (`ir_name("A'")`) stores `o["id"] = "A_prime"` and `o["notation"] = "A′"` in `scene3d["objects"]`, while Planner `/17` (`DINH_CAT_CANH`) and `_phong_bi(r)` preserve the learner-facing label `vertex["label"] = "A'"` in `route_d["sections"][0]["vertices"]`.
   - Indexing `objects["A'"]` directly without canonical lookup (`ir_name(name(vertex["label"]))`) raises `KeyError: "A'"`, which `build_adapter4_response` catches at line `221` (`except Exception:`) and converts into `refuse("PREVIEW_VALIDATION_FAILED", adapter=True)`.
   - A second identical uncanonicalized lookup exists in `_validate_sections` at line `287`:
     ```python
     cycle([objects[label]["xyz"] for label in boundary], obj["polygon"])
     ```
     which also raises `KeyError: "A'"` whenever a Category A section has a `declared_boundary` or derived solid referencing a primed vertex label such as `"A'"`.

---

## 2. Step-by-Step Pipeline Traces on Baseline `eb661971847c034500862299c5091f1f3d2a2998`

### 2.1 Case `W2-A07`

- **Problem Text**:
  `Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, AB = 5, BC = 5 và cạnh bên AA' = 10. Mặt phẳng (α) đi qua điểm A' và vuông góc với đường thẳng AC', cắt các cạnh bên BB', CC' lần lượt tại M, N. Tính diện tích thiết diện của hình lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng (α).`
- **Bridge `/2` (`v2_bridge_to_legacy_dict`)**: `OK`
- **Source Gate `/19` (`validate_request_contract`)**: `OK` (valid contract)
- **Planner `/17` (`plan_geometry_with_trace`)**:
  - `supported = True`, `reason = None`
  - `auxiliary`:
    ```json
    [
      {
        "rule": "section vertices on the stated cut edges of a derived plane",
        "plane": "alpha",
        "solid": "ABC.A'B'C'",
        "goal": "td_alpha_ABC_A_prime_B_prime_C_prime",
        "point": "A'",
        "edges": [["A", "A'"], ["B", "B'"], ["C", "C'"]],
        "stated_edges": [["B", "B'"], ["C", "C'"]],
        "vertices": [
          {"label": "A'", "edge": ["A", "A'"], "provenance": "THROUGH_POINT_REUSE", "stated": false},
          {"label": "M", "edge": ["B", "B'"], "provenance": "SOURCE_NAMED", "stated": true},
          {"label": "N", "edge": ["C", "C'"], "provenance": "SOURCE_NAMED", "stated": true}
        ]
      }
    ]
    ```
- **Engine `/14` (`run_typed_fact_next_v2_route`)**:
  - `status = "SERVED"`, `reason = None`
  - `final_memory["kq_mg1"] = "25*sqrt(6)/4"`, `_binh_phuong("25*sqrt(6)/4") = Fraction(1875, 8)` (100% match with independent oracle `area_squared = 1875/8`, `boundary = [{"vertex": "A'"}, {"edge": ["B", "B'"], "t": "3/4"}, {"edge": ["C", "C'"], "t": "1/2"}]`).
  - `scene3d["objects"]` point and section entries:
    - `{"id": "A_prime", "type": "point3", "notation": "A′", "origin": "source", "xyz": [0.0, 0.0, 10.0]}`
    - `{"id": "M", "type": "point3", "origin": "derived", "xyz": [5.0, 0.0, 7.5]}` (`t = 3/4` on `BB'`)
    - `{"id": "N", "type": "point3", "origin": "derived", "xyz": [5.0, 5.0, 5.0]}` (`t = 1/2` on `CC'`)
    - `{"id": "td_alpha_ABC_A_prime_B_prime_C_prime", "type": "section", "depends": ["alpha", "khoi_ABC_A_prime_B_prime_C_prime"], "polygon": [[0.0, 0.0, 10.0], [5.0, 0.0, 7.5], [5.0, 5.0, 5.0]], "vertex_sources": [{"kind": "SOLID_VERTEX", "solid_vertex_index": 3}, {"kind": "SOLID_EDGE_INTERSECTION", "solid_edge_vertex_indices": [1, 4]}, {"kind": "SOLID_EDGE_INTERSECTION", "solid_edge_vertex_indices": [2, 5]}]}`
- **Section Category**: Category A (`DINH_CAT_CANH`), `plane_section_certificates = []`.
- **Adapter `/4` (`build_adapter4_response`)**:
  - Fails at `_validate_sections` (`backend/app/ai/adapter4_route.py:261`): `point = objects[vertex["label"]]` with `vertex["label"] == "A'"` raises `KeyError: "A'"`, caught at line `221` and converted into `status = "REFUSED"`, `reason_code = "PREVIEW_VALIDATION_FAILED"`.

### 2.2 Case `W2-A10`

- **Problem Text**:
  `Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật với AB = 3a, AD = 6a và cạnh bên AA' = 9a. Mặt phẳng (Q) đi qua điểm A' và vuông góc với đường thẳng AC', cắt các cạnh bên BB', CC', DD'. Xác định thiết diện của hình hộp chữ nhật ABCD.A'B'C'D' cắt bởi mặt phẳng (Q).`
- **Bridge `/2` (`v2_bridge_to_legacy_dict`)**: `OK`
- **Source Gate `/19` (`validate_request_contract`)**: `OK` (valid contract)
- **Planner `/17` (`plan_geometry_with_trace`)**:
  - `supported = True`, `reason = None`
  - `auxiliary`:
    ```json
    [
      {
        "rule": "section vertices on the stated cut edges of a derived plane",
        "plane": "Q",
        "solid": "ABCD.A'B'C'D'",
        "goal": "td_Q_ABCD_A_prime_B_prime_C_prime_D_prime",
        "point": "A'",
        "edges": [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]],
        "stated_edges": [["B", "B'"], ["C", "C'"], ["D", "D'"]],
        "vertices": [
          {"label": "A'", "edge": ["A", "A'"], "provenance": "THROUGH_POINT_REUSE", "stated": false},
          {"label": "I", "edge": ["B", "B'"], "provenance": "STATED_UNNAMED", "stated": true},
          {"label": "I1", "edge": ["C", "C'"], "provenance": "STATED_UNNAMED", "stated": true},
          {"label": "I2", "edge": ["D", "D'"], "provenance": "STATED_UNNAMED", "stated": true}
        ]
      }
    ]
    ```
- **Engine `/14` (`run_typed_fact_next_v2_route`)**:
  - `status = "SERVED"`, `reason = None`
  - `question_type = "section_only"`, `area_goal_id = null`, exact polygon `area_squared = 504` ($S = 6\sqrt{14}$), `boundary = [{"vertex": "A'"}, {"edge": ["B", "B'"], "t": "8/9"}, {"edge": ["C", "C'"], "t": "4/9"}, {"edge": ["D", "D'"], "t": "5/9"}]`.
  - `scene3d["objects"]` point and section entries:
    - `{"id": "A_prime", "type": "point3", "notation": "A′", "origin": "source", "xyz": [0.0, 0.0, 9.0]}`
    - `{"id": "I", "type": "point3", "origin": "derived", "xyz": [3.0, 0.0, 8.0]}` (`t = 8/9` on `BB'`)
    - `{"id": "I1", "type": "point3", "origin": "derived", "xyz": [3.0, 6.0, 4.0]}` (`t = 4/9` on `CC'`)
    - `{"id": "I2", "type": "point3", "origin": "derived", "xyz": [0.0, 6.0, 5.0]}` (`t = 5/9` on `DD'`)
    - `{"id": "td_Q_ABCD_A_prime_B_prime_C_prime_D_prime", "type": "section", "depends": ["Q", "khoi_ABCD_A_prime_B_prime_C_prime_D_prime"], "polygon": [[3.0, 0.0, 8.0], [0.0, 0.0, 9.0], [0.0, 6.0, 5.0], [3.0, 6.0, 4.0]], "vertex_sources": [{"kind": "SOLID_EDGE_INTERSECTION", "solid_edge_vertex_indices": [1, 5]}, {"kind": "SOLID_VERTEX", "solid_vertex_index": 4}, {"kind": "SOLID_EDGE_INTERSECTION", "solid_edge_vertex_indices": [3, 7]}, {"kind": "SOLID_EDGE_INTERSECTION", "solid_edge_vertex_indices": [2, 6]}]}`
- **Section Category**: Category A (`DINH_CAT_CANH`), `plane_section_certificates = []`.
- **Adapter `/4` (`build_adapter4_response`)**:
  - Fails at `_validate_sections` (`backend/app/ai/adapter4_route.py:261`): `point = objects[vertex["label"]]` with `vertex["label"] == "A'"` raises `KeyError: "A'"`, caught at line `221` and converted into `status = "REFUSED"`, `reason_code = "PREVIEW_VALIDATION_FAILED"`.

---

## 3. Name-System Inventory Across the Pipeline

| Layer | Representation of Primed Vertex (`A'`) | Representation of Stated Unnamed Cut (`I` on `BB'`) | Representation of Source-Named Cut (`M` on `BB'`) |
|---|---|---|---|
| Problem Text / Bridge `/2` | `"A'"` | Edge cut on `["B", "B'"]` | `"M"` on `["B", "B'"]` |
| Planner `/17` (`DINH_CAT_CANH` `vertices`) | `{"label": "A'", "edge": ["A", "A'"], "provenance": "THROUGH_POINT_REUSE", "stated": false}` | `{"label": "I", "edge": ["B", "B'"], "provenance": "STATED_UNNAMED", "stated": true}` | `{"label": "M", "edge": ["B", "B'"], "provenance": "SOURCE_NAMED", "stated": true}` |
| Engine `/14` (`ir_name`) | `"A_prime"` | `"I"` | `"M"` |
| `scene3d["objects"]` | `{"id": "A_prime", "notation": "A′", "origin": "source", ...}` | `{"id": "I", "origin": "derived", ...}` (no `notation`) | `{"id": "M", "origin": "derived", ...}` (no `notation`) |
| `route_d["sections"][*]["vertices"]` | `{"label": "A'", "edge": ["A", "A'"], "provenance": "THROUGH_POINT_REUSE", "stated": false}` | `{"label": "I", "edge": ["B", "B'"], "provenance": "STATED_UNNAMED", "stated": true}` | `{"label": "M", "edge": ["B", "B'"], "provenance": "SOURCE_NAMED", "stated": true}` |
| Adapter `/4` `_validate_sections` (Internal Lookup) | Must resolve `vertex["label"] = "A'"` via `ir_name(name("A'")) -> "A_prime"` in `objects` while verifying `name(objects["A_prime"]["notation"]) == "A'"` | Resolves `"I"` via `ir_name(name("I")) -> "I"` and endpoints `["B", "B'"] -> ["B", "B_prime"]` | Resolves `"M"` via `ir_name(name("M")) -> "M"` and endpoints `["B", "B'"] -> ["B", "B_prime"]` |

---

## 4. Secondary Finding in the Frozen Wave 2 Scorer (`evaluate_holdout_wave2.py:184`)

During baseline diagnosis of `W2-A10`, we also inspected `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/tools/evaluate_holdout_wave2.py` (frozen at `ecdc26b012c8ce80d53524a98dc75cdcb020079d`).

- At line `146`, `evaluate_holdout_wave2.py` defines `_find_point_xyz(objects_by_id, label)` specifically to look up primed point labels (`"A'"`) in `objects_by_id` (`"A_prime"`, `"A′"`), and calls `_find_point_xyz` at line `232` to compute the vertex's edge interpolation parameter.
- However, at lines `184–185` (when computing `poly_idx` to sort `sec["vertices"]` into `td_sec["polygon"]` cyclic order), `evaluate_holdout_wave2.py` wrote:
  ```python
  elif v.get("label") and v["label"] in objects_by_id:
      pt_xyz = objects_by_id[v["label"]].get("xyz")
  ```
  instead of calling `_find_point_xyz(objects_by_id, v["label"])`!
- Because `"A'" in objects_by_id` is `False` (the key in `objects_by_id` is `"A_prime"`), `evaluate_holdout_wave2.py` falls back to `poly_idx = idx_fallback = 0` for `A'`. Meanwhile, in `W2-A10`, `td_sec["polygon"]` starts at `I` (`poly_raw[0]`), so `I` ALSO gets `poly_idx = 0`. Sorting by `poly_idx` collides at `0` (`(0, A')` and `(0, I)`), scrambling the valid 4-cycle `[I (BB'), A' (AA'), I2 (DD'), I1 (CC')]` into `[A' (AA'), I (BB'), I2 (DD'), I1 (CC')]`!
- In accordance with repository rules, we do **not** touch the frozen historical file `evaluate_holdout_wave2.py` from `ecdc26b012c8ce80d53524a98dc75cdcb020079d`. Instead, in `results/wave2-post-feedback-regression.json` and `results/w2-a10-scorer-adjudication-receipt.json`, we report both the unmodified historical scorer output (`47/48`, where `W2-A07` is `SERVED_CORRECT` and `W2-A10` is `SERVED` with exact area `504` and valid 4-cycle `[BB', AA', DD', CC']`) and the scorer-adjudicated result (`48/48` `SERVED_CORRECT` when line `184` uses `_find_point_xyz`).
