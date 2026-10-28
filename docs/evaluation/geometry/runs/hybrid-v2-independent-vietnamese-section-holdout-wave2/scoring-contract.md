# scoring-contract.md — Preregistered Scoring Contract (`hybrid-v2-independent-vietnamese-section-holdout-wave2`)

This contract specifies the exact, deterministic scoring rules implemented by `tools/evaluate_holdout_wave2.py` and verified by `tools/test_evaluate_holdout_wave2.py` **prior** to corpus creation.

---

## 1. Pipeline Under Test (Track A)

For each case in `inputs/holdout-wave2.json`:
1. Deep-copy `case["payload"]`.
2. Call `r = run_typed_fact_next_v2_route(payload)`.
3. Call `resp = build_adapter4_response(r, payload["problem_text"])`.
4. Define `served = (r.status == "SERVED" and resp["route_d"]["status"] == "SERVED" and resp["envelope"]["status"] == "ok")`.
5. Zero live AI calls (`os.environ["ALLOW_LIVE_AI"] = "0"`).

---

## 2. Exact Mathematical Oracle Comparison for Served Positive Cases

When `served` is `True`, the scorer checks all of the following against the case's frozen oracle entry `exp = expected[case["id"]]`:

1. **Oracle Entry Presence:** `exp` must exist (`exp is not None`).
2. **Declared Section Count & Section Object Presence:**
   - `len(route_d["sections"]) == len(payload["derived_sections"]) >= 1`.
   - `scene3d.objects` contains a `section` object `obj` with `id == f"td_{exp['section_id']}"` and `closed is True`.
3. **Solid Identity Agreement (Control 12):**
   - Let `solid_objs = [o for o in scene3d.objects if o["type"] == "solid" and o["id"] in (obj.get("depends") or [])]`.
   - There must be exactly 1 such `solid_obj`, and its normalized notation (`_norm_label(solid_obj.get("notation"))`) must match `_norm_label(exp["solid"])`. For Category B sections, `_norm_label(sec.get("solid"))` must also match `_norm_label(exp["solid"])`.
4. **Section Certificate Presence & Category Integrity (Controls 13 & 14):**
   - `route_d["sections"]` must contain the entry `sec` with `sec["section_id"] == exp["section_id"]`.
   - `sec.get("closure_certificate")` must be a dict with `verified is True` and a non-empty `rule`.
   - Determine observed category `obs_cat`:
     - If `sec.get("certificate_category") == "ENGINE_DERIVED_SECTION"` or `"certificate_version"` in `sec`: `obs_cat = "ENGINE_DERIVED_SECTION"` (Category B).
     - Otherwise: `obs_cat = "DINH_CAT_CANH"` (Category A).
   - **No Category A/B Certificate Mixing:**
     - `obs_cat` must equal `exp["expected_certificate_category"]`.
     - If `obs_cat == "ENGINE_DERIVED_SECTION"`: `sec.get("certificate_version")` must equal `"plane-section-certificate/1"`, no vertex in `sec["vertices"]` may have `stated is True`, and `(r.planner or {}).get("auxiliary")` must not contain a `DINH_CAT_CANH` rule for `exp["section_id"]`.
     - If `obs_cat == "DINH_CAT_CANH"`: `"certificate_version"` must not be present on `sec`, and `sec.get("certificate_category")` must not be `"ENGINE_DERIVED_SECTION"`.
5. **Exact Vertex Count (Controls 9 & 10):**
   - `len(obj["polygon"]) == exp["vertex_count"]` and `len(sec["vertices"]) == exp["vertex_count"]`.
6. **Canonical Boundary Descriptor Resolution (Controls 1, 2, 3, 6, 7, 8):**
   - Every vertex in `exp["boundary"]` is mapped to a canonical boundary descriptor:
     - Solid vertex `{"vertex": V}` $\rightarrow$ `("VERTEX", _norm_label(V))`.
     - Interior edge cut `{"edge": [U, V], "t": t}` ($0 < t < 1$): let `(a, b) = sorted((_norm_label(U), _norm_label(V)))`, and let `t_canon = Fraction(t)` if `_norm_label(U) == a` else `1 - Fraction(t)`. Canonical descriptor: `("EDGE", a, b, t_canon)`.
   - Every vertex `v` in `sec["vertices"]` is mapped to its canonical boundary descriptor and ordered by its polygon index in `obj["polygon"]`:
     - **Category B (`ENGINE_DERIVED_SECTION`):**
       - If `v.get("source_kind") == "SOLID_VERTEX"` (or `Fraction(v["t"]) in (0, 1)`): resolves to `("VERTEX", _norm_label(v.get("label") or v.get("entity_id")))`. Also verifies that `Fraction(v["t"]) == 0` corresponds to `edge[0]` and `Fraction(v["t"]) == 1` corresponds to `edge[1]`.
       - If `v.get("source_kind") == "SOLID_EDGE_INTERSECTION"`: `0 < Fraction(v["t"]) < 1` on `v["edge"] = [U, V]`, resolving to `("EDGE", a, b, t_canon)`.
     - **Category A (`DINH_CAT_CANH`):**
       - Look up the 3D coordinates of `v["label"]` and of the edge endpoints `U, V = v["edge"]` in `scene3d.objects` (or use `v.get("t")` if explicitly provided in a synthetic fixture without endpoint coordinates).
       - Compute exact `t_val` such that `xyz(P) = (1 - t_val) * xyz(U) + t_val * xyz(V)` for all 3 coordinates in exact `Fraction` arithmetic:
         - If `t_val == 0` (point coincides with solid vertex `U`, e.g., `THROUGH_POINT_REUSE`): resolves to `("VERTEX", _norm_label(U))`.
         - If `t_val == 1` (point coincides with solid vertex `V`, e.g., `THROUGH_POINT_REUSE`): resolves to `("VERTEX", _norm_label(V))`.
         - If `0 < t_val < 1` (genuine interior edge cut): resolves to `("EDGE", a, b, t_canon)`.
         - If `P` does not lie collinearly on segment `UV` with $0 \le t \le 1$: records an explicit boundary error.
   - **Set/Multiset Check:** The Counter of solid vertices and Counter of interior edge cuts `("EDGE", a, b, t_canon)` in the product section must equal the oracle's Counters.
7. **Cyclic Polygon Order Equivalence (Controls 4 & 5):**
   - Ordering the product's canonical vertex descriptors by their position in `obj["polygon"]` yields `prod_ring`.
   - `prod_ring` must be cyclically equivalent to `oracle_ring` up to starting vertex rotation or polygon orientation reversal:
     $$\exists\, r \in \{\text{oracle\_ring}, \text{reversed}(\text{oracle\_ring})\},\ \exists\, i \in \{0, \dots, m-1\}:\ \text{prod\_ring} = r[i:] + r[:i].$$
8. **Exact Area Squared Verification (Control 11):**
   - For Category B, `Fraction(sec["closure_certificate"]["area_squared"])` must equal `Fraction(exp["area_squared"])`.
   - Whenever `exp.get("area_goal_id")` is non-null, `f"kq_{exp['area_goal_id']}"` must be present in `r.exec_result.final_memory`, and `_square(r.exec_result.final_memory[f"kq_{exp['area_goal_id']}"])` must equal `Fraction(exp["area_squared"])` in exact rational arithmetic.

Any failure of checks 1–8 records a non-empty `oracle_mismatches` list and classifies the case as `WRONG_SERVED`.

---

## 3. Refusal Taxonomy & Negative Case Scoring (Controls 15 & 16)

When `served` is `False`:
1. Extract `code = (resp["route_d"].get("refusal") or {}).get("code") or r.code` and `reason = (resp["route_d"].get("refusal") or {}).get("detail") or r.reason or ""`.
2. Map `(code, reason)` to a coarse category via `tools/refusal_taxonomy.json`:
   - Base code is `code.split(":")[0].strip()`.
   - Special refinement for `ENGINE_EXECUTION_FAILED`:
     - If `reason` contains `"Không tách được căn"` (the exact-radical factorization cap in `Radical`), classify under `UNSUPPORTED_CAPABILITY` (and record `subcode = "RADICAL_DOMAIN_OVERFLOW"`).
     - If `reason` matches a known kernel geometric degeneracy (`"trùng nhau"`, `"thẳng hàng"`, `"song song"`, `"không cắt"`, `"suy biến"`), classify under `GEOMETRY_DEGENERATE`.
     - Otherwise, classify under `INTERNAL_OR_VALIDATION`.
   - Any code not present in `tools/refusal_taxonomy.json` maps to `"UNMAPPED"`.
3. For `expected_disposition == "REFUSE"`:
   - If `category in case["acceptable_categories"]` and `category != "INTERNAL_OR_VALIDATION"`: outcome is `REFUSED_CORRECT_REASON`.
   - Otherwise: outcome is `REFUSED_REASON_DISAGREEMENT`.

---

## 4. Scene3D Learner-Facing Semantics Evaluation (Section 10)

For every served case, evaluate Scene3D semantics in two strictly separated tracks:

### Track 10.A — Source-Identity Correctness (`source_identity_leaks`)
Identify all planner-synthesized fresh auxiliary labels `aux_fresh` from `(r.planner or {}).get("auxiliary")` that do **not** appear as standalone tokens in `problem_text` using Unicode-aware boundaries `(?<![\w']){re.escape(a)}(?![\w'])`.
A **10.A Source-Identity Leak** occurs if and only if:
1. A `point3` object in `scene3d.objects` corresponding to `a in aux_fresh` has `origin == "given"` (masquerading as a source-given point), **or**
2. Any `section`, `plane3`, `solid`, or `quantity` object in `scene3d.objects` contains `a in aux_fresh` as a standalone token `(?<![\w']){re.escape(a)}(?![\w'])` in its `name`, `label`, or `notation`, **or**
3. Any `section` object has non-empty `identity_diagnostics`.

### Track 10.B — Pedagogical Auxiliary Display (`pedagogical_auxiliary_display`)
For each `a in aux_fresh`, inspect whether a `point3` object for `a` exists in `scene3d.objects` with `notation == a` (or appears in `point3`/`segment`/`line3` construction labels):
- Record whether `origin == "derived"` and `role == "Điểm dựng phụ"` (visibly distinguished from source-given points, which have `origin == "given"` and `role == "Điểm cho trước"`).
- Track under `r2_auxiliary_notation_observed` (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`), separate from Track 10.A and separate from primary mathematical correctness.
