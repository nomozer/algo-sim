# scoring-contract.md — Preregistered Scoring Contract (`hybrid-v2-independent-vietnamese-geometry-holdout-wave3`)

This contract specifies the exact, deterministic scoring rules implemented by `tools/evaluate_holdout_wave3.py` and verified by `tools/test_evaluate_holdout_wave3.py` **prior** to corpus creation.

---

## 1. Pipeline Under Test (Track A)

For each case in `inputs/holdout-wave3.json`:
1. Deep-copy `case["payload"]`.
2. Call `r = run_typed_fact_next_v2_route(payload)`.
3. Call `resp = build_adapter4_response(r, payload["problem_text"])`.
4. Define `served = (r.status == "SERVED" and resp["route_d"]["status"] == "SERVED" and resp["envelope"]["status"] == "ok")`.
5. Zero live AI calls (`os.environ["ALLOW_LIVE_AI"] = "0"`).

---

## 2. Exact Mathematical Oracle Comparison for Served Positive Cases

When `served` is `True`, the scorer checks all of the following against the case's frozen oracle entry `exp = expected[case["id"]]`:

1. **Oracle Entry Presence (Control 22):**
   - `exp` must be a non-null dict; if `exp is None`, the scorer records `"no oracle entry for a served case"` and classifies the outcome as `WRONG_SERVED`.
2. **Declared Section Count & Section Object Presence:**
   - `len(route_d["sections"]) == len(payload["derived_sections"]) >= 1`.
   - `scene3d.objects` contains a `section` object `obj` with `id == f"td_{exp['section_id']}"` and `closed is True`.
3. **Solid Identity Agreement (Control 16):**
   - Let `dep_solids = [o for o in scene3d.objects if o["type"] == "solid" and o["id"] in (obj.get("depends") or [])]`.
   - There must be at least 1 such solid object, and its normalized notation (`_norm_label(dep_solids[0].get("notation"))`) must match `_norm_label(exp["solid"])`. For Category B sections, `_norm_label(sec.get("solid"))` must also match `_norm_label(exp["solid"])`.
4. **Section Certificate Presence & Category Integrity (Controls 13, 14, 15, 19):**
   - `route_d["sections"]` must contain the entry `sec` with `sec["section_id"] == exp["section_id"]`.
   - Determine observed category `obs_cat`:
     - If `sec.get("certificate_category") == "ENGINE_DERIVED_SECTION"` or `"certificate_version"` in `sec`: `obs_cat = "ENGINE_DERIVED_SECTION"` (Category B).
     - Otherwise: `obs_cat = "DINH_CAT_CANH"` (Category A).
   - **Category B Certificate Requirements:**
     - `sec.get("certificate_version") == "plane-section-certificate/1"`.
     - `sec.get("closure_certificate")` must be a dict with `verified is True` and a non-empty `rule`.
     - No vertex in `sec["vertices"]` may have `stated is True`, and `(r.planner or {}).get("auxiliary")` must not contain a `dinh-cat-canh` rule for `exp["section_id"]`.
   - **Category A Certificate Requirements:**
     - `"certificate_version"` must not be present on `sec`, and `sec.get("certificate_category")` must not be `"ENGINE_DERIVED_SECTION"`.
     - `sec.get("vertices")` must be a list of $\ge 3$ dicts, each carrying non-empty `label`, 2-endpoint `edge`, non-empty `provenance`, and boolean `stated`. If `sec.get("closure_certificate")` or `sec.get("boundary")` is non-null, `closure_certificate` must be a dict with `verified is True` and non-empty `rule`.
   - **Category Match:** `obs_cat` must equal `exp["expected_certificate_category"]`.
5. **Exact Vertex Count & Duplicate-Vertex Prohibition (Controls 3, 4, 5, 9):**
   - `len(obj["polygon"]) == exp["vertex_count"] >= 3` and `len(sec["vertices"]) == exp["vertex_count"] >= 3`.
   - Convert every 3D point in `obj["polygon"]` to an exact rational tuple `poly_frac = [tuple(Fraction(str(c)) for c in pt) for pt in obj["polygon"]]`.
   - All points in `poly_frac` must be pairwise distinct (`len(set(poly_frac)) == len(poly_frac)`). Any duplicate polygon vertex coordinate is rejected (`"duplicate polygon vertex coordinates"`).
6. **Polygon-Index Bijection & Non-Zero Fallback Rule (Control 1 & W2-A10 Guard):**
   - For each vertex `v` in `sec["vertices"]`:
     - Resolve exact rational coordinates `xyz_p`:
       - If `isinstance(v.get("xyz"), list) and len(v["xyz"]) == 3`: `xyz_p = tuple(Fraction(str(c)) for c in v["xyz"])`.
       - Else if `v.get("label")`: look up `xyz_p` via `_find_point_xyz(objects_by_id, v["label"])`, which compares `_norm_label(o.get("id"))` and `_norm_label(o.get("notation"))` against `_norm_label(v["label"])` (matching `"A'"`, `"A′"`, and `"A_prime"` identically).
     - Resolve `poly_idx`:
       - If `xyz_p is not None and xyz_p in poly_frac`: `poly_idx = poly_frac.index(xyz_p)`.
       - Else if `is_cat_b and isinstance(v.get("ordinal"), int) and 0 <= v["ordinal"] < len(poly_frac)`: `poly_idx = v["ordinal"]`.
       - **Otherwise: `poly_idx` is `None` (NEVER defaulted to `0` or loop index), and the scorer records an explicit mismatch `f"vertex {v.get('label') or v} could not be resolved to any polygon index in section.polygon"`.**
   - Across all vertices in `sec["vertices"]`, the resolved `poly_idx` values must form a bijection onto `{0, 1, ..., len(poly_frac) - 1}` (no duplicate polygon indices).
7. **Canonical Boundary Descriptor Resolution (Controls 1, 10, 11, 12, 17):**
   - Every vertex in `exp["boundary"]` is mapped to a canonical boundary descriptor:
     - Solid vertex `{"vertex": V}` $\rightarrow$ `("VERTEX", _norm_label(V))`.
     - Interior edge cut `{"edge": [U, V], "t": t}` ($0 < t < 1$): let `(a, b) = sorted((_norm_label(U), _norm_label(V)))`, and let `t_canon = Fraction(t)` if `_norm_label(U) == a` else `1 - Fraction(t)`. Canonical descriptor: `("EDGE", a, b, t_canon)`.
   - Every vertex `v` in `sec["vertices"]` is mapped to its canonical boundary descriptor using exact `Fraction` arithmetic (handling both `SOLID_VERTEX` / `THROUGH_POINT_REUSE` at $t \in \{0, 1\}$ and strict interior cuts at $0 < t < 1$, and normalizing reversed edge orientation `[V, U]` with parameter $1 - t$).
   - **No Duplicate Descriptors & Exact Multiset Match:** All canonical descriptors in the product section must be pairwise distinct, and the Counter of solid vertices and Counter of interior edge cuts must equal the oracle's Counters.
8. **Cyclic Polygon Order Equivalence (Controls 6, 7, 8):**
   - Ordering the product's canonical vertex descriptors by their unique `poly_idx` in `obj["polygon"]` yields `prod_ring`.
   - `prod_ring` must be cyclically equivalent to `oracle_ring` up to starting vertex rotation or polygon orientation reversal:
     $$\exists\, r \in \{\text{oracle\_ring}, \text{reversed}(\text{oracle\_ring})\},\ \exists\, i \in \{0, \dots, m-1\}:\ \text{prod\_ring} = r[i:] + r[:i].$$
   - Any non-cyclic permutation (such as a bow-tie self-intersecting order `[v0, v2, v1, v3]` on $\ge 4$ vertices) fails `_same_cycle` and is rejected as `WRONG_SERVED`.
9. **Exact Area Squared Verification (Control 18):**
   - For Category B, `Fraction(sec["closure_certificate"]["area_squared"])` must equal `Fraction(exp["area_squared"])`.
   - Whenever `exp.get("area_goal_id")` is non-null, `f"kq_{exp['area_goal_id']}"` must be present in `r.exec_result.final_memory`, and `_square(r.exec_result.final_memory[f"kq_{exp['area_goal_id']}"])` must equal `Fraction(exp["area_squared"])`.

Any failure of checks 1–9 records a non-empty `oracle_mismatches` list and classifies the case as `WRONG_SERVED`.

---

## 3. Refusal Taxonomy & Negative Case Scoring (Controls 20, 21)

When `served` is `False`:
1. If an unhandled Python exception occurred during product execution (`run_typed_fact_next_v2_route` or `build_adapter4_response`), `product_exception = True`, `category = "INTERNAL_OR_VALIDATION"`, and the case is scored as `FALSE_REFUSAL` (if `expected_disposition == "SERVE"`) or `REFUSED_REASON_DISAGREEMENT` (if `expected_disposition == "REFUSE"`).
2. Otherwise, extract `code` and `reason` and map `(code, reason)` to `(category, subcode)` using frozen `refusal-taxonomy.json`:
   - `INTERNAL_OR_VALIDATION` and `UNMAPPED` are **never** acceptable refusal categories for any case.
   - For `expected_disposition == "REFUSE"`:
     - If `category in case["acceptable_categories"]` and `category not in ("INTERNAL_OR_VALIDATION", "UNMAPPED")`: `REFUSED_CORRECT_REASON`.
     - Otherwise: `REFUSED_REASON_DISAGREEMENT`.
   - For `expected_disposition == "SERVE"`: `FALSE_REFUSAL`.

---

## 4. Learner-Facing Scene3D Semantics (Track C — Control 2)

For every served case, evaluate learner-facing Scene3D semantics:
1. **Machine-ID Leakage Guard (`_prime` Leak Check):**
   - Inspect `name`, `label`, and `notation` on every object in `scene3d.objects`, plus `envelope.answer`. Any occurrence of the raw internal substring `"_prime"` on a learner-facing string is recorded in `source_identity_leaks` as `f"{oid}.{key}:_prime_leak"`.
2. **Fresh Auxiliary Label Leakage Guard (`source_identity_leaks`):**
   - Identify all planner-synthesized fresh auxiliary labels `aux_fresh` from `(r.planner or {}).get("auxiliary")` that do not appear as standalone tokens in `problem_text`.
   - Record a leak if any `point3` object for `a in aux_fresh` has `origin == "given"` or `role == "Điểm cho trước"`, if `a` appears in any `section`, `plane3`, `solid`, or `quantity` object's `name`, `label`, or `notation`, or if any `section` object has non-empty `identity_diagnostics`.
3. **Pedagogical Auxiliary Display (`pedagogical_auxiliary_points`):**
   - Track whether auxiliary construction points (`a in aux_fresh`) displayed as `point3` objects carry `origin == "derived"` and `role == "Điểm dựng phụ"`.
