# Architecture Decision — Category A vs Category B Section Certificates in Adapter `/4`

- **Task**: `HYBRID_V2_ADAPTER4_PLANE_ONLY_SECTION_CERTIFICATE`
- **Decision**: Separate **Category A (`DINH_CAT_CANH`)** source-grounded cut-vertex certificates from **Category B (`plane-section-certificate/1`)** Engine-derived plane section certificates, and verify both deterministically in `engine.py` and `adapter4_route.py`.

---

## 1. Two Distinct Categories of Section Certificates

| Aspect | Category A (`DINH_CAT_CANH`) | Category B (`plane-section-certificate/1`) |
|---|---|---|
| **When Used** | Problem text explicitly states/names cut edges (`stated_intersections` non-empty), declares an edge boundary (`declared_boundary`), or constructs a derived solid (`construct_derived_solid`, rule `D6`). | Problem defines a verified cutting plane (`MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`, or named plane) and requests the section and/or section area without edge-cut point declarations. |
| **Point Variables** | Planner allocates point calls (`intersect_line_plane`) on lateral edges (`_canh_ben`). | No fake `DINH_CAT_CANH` point variables are fabricated; `section.cross_section(solid, plane)` computes the exact polygon vertices over `Fraction`. |
| **Supported Edges** | Lateral edges of pyramid/prism (`_canh_ben`). | All topological edges and vertices of the polyhedron (base, top, and lateral edges). |
| **Trusted Producer** | `planner._dinh_cat_canh` + `engine.kiem_dinh_cat` + `engine.chung_chi_khep_kin` | `engine._Dung.kiem_chung_chi_thiet_dien` (`PLANE_SECTION_CERTIFICATE_PRODUCER = "engine.kiem_chung_chi_thiet_dien"`) |
| **Allowed Vertex Provenance** | `THROUGH_POINT_REUSE`, `SOURCE_NAMED`, `STATED_UNNAMED`, `REUSED_INTERSECTION`, `DERIVED_FRESH` | `THROUGH_POINT_REUSE`, `SOLID_VERTEX_INTERSECTION`, `ENGINE_DERIVED_EDGE_CUT` (always `stated: False`) |

---

## 2. Category B Certificate Schema (`plane-section-certificate/1`)

Each Category B section certificate in `KetQuaTuyen.section_certificates` and `route_d["sections"]` has the following closed structure:

```json
{
  "section_id": "sec",
  "certificate_category": "ENGINE_DERIVED_SECTION",
  "certificate_version": "plane-section-certificate/1",
  "producer": "engine.kiem_chung_chi_thiet_dien",
  "engine_version": "geometry-function-engine/14",
  "solid": "ABC.A'B'C'",
  "solid_object_id": "khoi_ABC_A_primeB_primeC_prime",
  "plane_object_id": "mp_td_sec",
  "plane_points": ["M", "H2", "H3"],
  "plane_rule": "section(plane through point perpendicular to a line)",
  "through_point": "M",
  "plane_relation": {
    "kind": "perpendicular_line",
    "point": "M",
    "perpendicular_to": ["A", "B"]
  },
  "plane_equation": {
    "normal": ["36", "0", "0"],
    "offset": "18"
  },
  "calls": ["sec", "q"],
  "boundary": [
    "section:td_sec:point:on:khoi_ABC_A_primeB_primeC_prime::edge:A-B",
    "section:td_sec:point:on:khoi_ABC_A_primeB_primeC_prime::edge:B-C",
    "section:td_sec:point:on:khoi_ABC_A_primeB_primeC_prime::edge:B_prime-C_prime",
    "section:td_sec:point:on:khoi_ABC_A_primeB_primeC_prime::edge:A_prime-B_prime"
  ],
  "vertices": [
    {
      "ordinal": 0,
      "entity_id": "section:td_sec:point:on:khoi_ABC_A_primeB_primeC_prime::edge:A-B",
      "label": null,
      "xyz": ["1/2", "0", "0"],
      "source_kind": "SOLID_EDGE_INTERSECTION",
      "solid_vertex_index": null,
      "solid_edge_vertex_indices": [0, 1],
      "edge": ["A", "B"],
      "t": "1/2",
      "provenance": "ENGINE_DERIVED_EDGE_CUT",
      "stated": false
    }
  ],
  "closure_certificate": {
    "certificate_version": "plane-section-certificate/1",
    "producer": "engine.kiem_chung_chi_thiet_dien",
    "verified": true,
    "rule": "engine_derived_plane_section",
    "boundary": ["..."],
    "polygon": [["1/2", "0", "0"], ["..."]],
    "area_squared": "2304"
  },
  "declared_boundary": null
}
```

---

## 3. Exact Mathematical & Structural Verification Rules (§4.2)

Both `engine._Dung.kiem_chung_chi_thiet_dien` (producer + self-check) and `adapter4_route._validate_engine_derived_section` (consumer boundary check) verify in exact `Fraction` arithmetic:

1. **Solid Identity**: `solid_object_id` exists in `scene3d["objects"]` with `type == "solid"`, is in `td_<sid>["depends"]`, matches `section["solid"]`, and its `vertex_ids`, `vertices`, and `faces` match the Engine solid.
2. **Verified Cutting Plane**: `plane_object_id` (`mp_td_<sid>`) exists in `scene3d["objects"]` with `type == "plane3"`, is in `td_<sid>["depends"]`, its `depends` match `plane_points`, `through_point` is in `plane_points`, `plane_rule` and `plane_relation` match the verified `planner["auxiliary"]` record, and `plane_equation` (`normal`, `offset`) matches `final_memory[plane_object_id]` and satisfies `normal · P == offset` for all 3 `plane_points`.
3. **Exact Plane Membership**: Every section vertex coordinate $P_i \in \mathbb{Q}^3$ satisfies `normal · P_i == offset`.
4. **Solid Boundary Membership**: Every section vertex has either:
   - `source_kind == "SOLID_VERTEX"` with `0 <= solid_vertex_index < len(vertex_ids)` and $P_i = V_{\text{solid\_vertex\_index}}$, or
   - `source_kind == "SOLID_EDGE_INTERSECTION"` with `solid_edge_vertex_indices == [ia, ib]` ($0 \le ia < ib < \text{len}(\text{vertex\_ids})$) forming a topological edge of `solid["faces"]`.
5. **Supporting Edge & Exact Parameter $t \in [0, 1]$**:
   - `edge == [u, v]` maps to topological edge `(ia, ib)` ($ia < ib$) of `solid["faces"]`.
   - Exact rational parameter $t = \text{Fraction}(v[\text{"t"}]) \in [0, 1]$ satisfies $(1 - t) V_{ia} + t V_{ib} = P_i$.
   - For `SOLID_VERTEX`, $t \in \{0, 1\}$ and `solid_vertex_index == (ia if t == 0 else ib)`.
   - For `SOLID_EDGE_INTERSECTION`, $0 < t < 1$ strictly, and the edge is not parallel to the cutting plane (`normal · (V_{ib} - V_{ia}) != 0`).
6. **Endpoint Canonicalization**: All vertex coordinates `xyz` and `entity_id`s are pairwise distinct, and no `SOLID_EDGE_INTERSECTION` vertex coincides with any solid vertex ($P_i \notin \{V_0, \dots, V_{n-1}\}$).
7. **Valid Cyclic Polygon Boundary**: `len(vertices) >= 3`, `[v["xyz"] for v in vertices] == obj["polygon"] == closure_certificate["polygon"]`, every consecutive pair $(v_i, v_{(i+1) \bmod m})$ shares at least one topological face of `solid["faces"]`, and `obj["endpoint_entities"]` matches `boundary` with `anonymous_coordinate_fallback == False`.
8. **Nondegeneracy & Interior Cut**: For derived planes (`MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`), the section vertices do not all lie on a single face of `solid["faces"]`. In the chart Gram metric $G$, fan triangulation from $P_0$ has coplanar, identically oriented triangles ($c_k \times c_1 = 0$, $\lambda_k = (c_k \cdot c_1)/(c_1 \cdot c_1) > 0$) with positive squared area:
   $$S^2 = \left(\sum_{k=1}^{m-2} \lambda_k\right)^2 \cdot \frac{g(u_1, u_1) g(v_1, v_1) - g(u_1, v_1)^2}{4} > 0$$
9. **Engine / Kernel Agreement**: `final_memory["td_<sid>"].polygon` equals `obj["polygon"]` and `closure_certificate["area_squared"] == str(S^2)`.
10. **Exact Area Answer Agreement**: Whenever an `ask_section_area` call targets the section, `_binh_phuong(final_memory["kq_<ask_id>"]) == S^2` and `answer_exact["<ask_id>"]["coef"] == dinh_dang(final_memory["kq_<ask_id>"])`.
