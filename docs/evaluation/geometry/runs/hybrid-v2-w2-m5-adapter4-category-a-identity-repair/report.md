# Evaluation & Verification Report — Hybrid V2 W2-M5 Adapter `/4` Category A Identity Repair (`hybrid-v2-w2-m5-adapter4-category-a-identity-repair`)

- **Task:** `HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR`
- **Branch:** `research/hybrid-v2-w2-m5-adapter4-category-a-identity-repair`
- **Worktree:** `.superpowers/worktrees/w2-m5-adapter4-category-a-identity-repair`
- **Authoritative `main = origin/main`:** `eb661971847c034500862299c5091f1f3d2a2998`
- **Historical Holdout Wave 2 Commit (preserved untouched):** `ecdc26b012c8ce80d53524a98dc75cdcb020079d`
- **Product Repair Commit:** `73ca8d92e74059680ce53b99692af396df37a2f8`
- **Test & Evaluation Artifacts Commit:** `7aa538aecf2d31c40887b7c6ee52f7e8219ea0eb`
- **Frozen Full T3 Candidate:** `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`
- **Measured Product System:** `118` files, tree SHA-256 `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`
- **Product Files Modified (`eb661971..b61f1699`):** `backend/app/ai/adapter4_route.py` (`1` file only)
- **Component Versions & Cache Identity:**
  - `REGISTRY_VERSION`: `geometry-functions/19` (unchanged)
  - `PLANNER_VERSION`: `geometry-fact-planner/17` (unchanged)
  - `ENGINE_VERSION`: `geometry-function-engine/14` (unchanged)
  - `ADAPTER_V4_VERSION`: `hybrid-simulation-adapter/4` (unchanged)
  - `PLANE_SECTION_CERTIFICATE_VERSION`: `plane-section-certificate/1` (unchanged)
  - `CACHE_VERSION`: `130` (`NO_BUMP`)
  - `DEFAULT_MODE`: `LLM_ONLY` (Hybrid opt-in only)
  - `live_provider_calls`: `0` (`ALLOW_LIVE_AI=0`)
- **Final Wave Verdict:** `READY_FOR_OWNER_REVIEW`

---

## 1. Root-Cause Diagnosis & Architectural Repair (`73ca8d92`)

### 1.1 Why `W2-A07` and `W2-A10` Failed at Baseline (`eb661971`)

Both `W2-A07` and `W2-A10` are **complete Category A (`DINH_CAT_CANH`) sections** that pass Bridge `/2`, Source Gate `/19`, Planner `/17`, and Engine `/14` with `status == "SERVED"`:
- **`W2-A07`** (right triangular prism `ABC.A'B'C'`, section `(A'MN)` with `M` on `BB'` at $t=3/4$ and `N` on `CC'` at $t=1/2$, asking `section_area`):
  - Engine `/14` constructs `polygon_A_prime_M_N` with exact coordinates `A' = [0, 0, 5]`, `M = [6, 0, 15/4]`, `N = [0, 6, 5/2]` and computes `area_squared = 1875/8`, `answer = 25√6/4`.
- **`W2-A10`** (cube `ABCD.A'B'C'D'`, edge $a = 6$, section `(A'MN)` cutting `BB'`, `CC'`, `DD'` at `I` ($t=8/9$), `I1` ($t=4/9$), `I2` ($t=5/9$), `section_only`):
  - Engine `/14` constructs `polygon_I_A_prime_I2_I1` with exact 4-vertex cycle `[I, A', I2, I1]` and exact `area_squared = 504`.

In `backend/app/ai/adapter4_route.py`, `build_adapter4_response` invokes `_validate_sections(route_d.get("sections"), objects, result)`. Because `scene3d["objects"]` keys primed points by their canonical IR identifier `ir_name("A'") == "A_prime"` (with learner-facing `"notation": "A′"`), whereas `route_d["sections"][*]["vertices"][*]["label"]` and `section["boundary"]` preserve the source-facing label `"A'"`:
1. `adapter4_route.py:261` (`point = objects[vertex["label"]]`) raised `KeyError: "A'"`, caught at `adapter4_route.py:221` and mapped to `PREVIEW_VALIDATION_FAILED` (`CANNOT_BUILD_SOLIDS`).
2. `adapter4_route.py:287` (`[objects[label]["xyz"] for label in boundary]`) had the same raw `objects[label]` lookup for `declared_boundary` Category A sections.

### 1.2 Option 1 Canonical Lookup & Independent Exact Geometric Verification (`73ca8d92`)

Per Section 3 of the Owner GO, we implemented **Option 1** inside `backend/app/ai/adapter4_route.py`:
1. **Strict Category A vs Category B Partitioning:**
   - Category A (`DINH_CAT_CANH`) and Category B (`ENGINE_DERIVED_SECTION` / `plane-section-certificate/1`) remain strictly disjoint. Any section in `dinh_cat_by_id` that carries Category B fields (`certificate_category == "ENGINE_DERIVED_SECTION"` or `"certificate_version" in section`) is immediately rejected (`TAMPER-10`), and any non-Category-B section missing from `dinh_cat_by_id` is rejected.
2. **One-Way Canonical Point Lookup (`point_of(label)`):**
   - Rejects any label containing machine identifier `"_prime"` (`TAMPER-12`).
   - Normalizes prime glyphs via `canon = name(label)`, resolves `pt = objects.get(ir_name(canon))`, verifies `pt["type"] == "point3"`, and requires `name(str(pt["notation"])) == canon` when `notation is not None` (or `pt["id"] == label` for unnamed `DERIVED_FRESH` auxiliary points).
   - Used consistently for `vertex["label"]`, both endpoints of `vertex["edge"]`, `solid["vertex_ids"]`, and `section["boundary"]`.
3. **Independent Exact `Fraction` Geometric & Certificate Verification for Category A:**
   - **Solid & Face Structure:** Verifies unique referenced `solid` in `obj["depends"]`, `name(solid["notation"]) == name(d_aux["solid"])`, and self-consistent `vertex_ids`/`vertices`/`faces`.
   - **Edge Membership & Exact Collinearity Parameter $t \in [0, 1]$:** Verifies `frozenset(edge) in solid_edges`, checks `obj["vertex_sources"][index]` (`SOLID_VERTEX` vs `SOLID_EDGE_INTERSECTION`), and computes exact rational parameter $t$ on segment $AB$ across all 3 coordinates (`t in {0, 1}` for `SOLID_VERTEX`, `0 < t < 1` for `SOLID_EDGE_INTERSECTION`).
   - **Provenance & Statedness:** Verifies `provenance` against `_NGUON_GOC`, `notation` presence/absence (`DERIVED_FRESH` requires `notation is None` and `origin == "derived"`), and `vertex["stated"] == (frozenset(edge) in stated_edges)` (`TAMPER-11`).
   - **Cyclic Face-Adjacency, Coplanarity, Convexity & Area-Squared Cross-Check:** Verifies that consecutive vertices share a solid face (`fc & fn`), that all polygon triangles are coplanar with parallel positive normals and `area_sq > 0` (`_polygon_area_squared`), and that any `ask_section_area` call on the cutting plane matches `area_sq` in `result.exec_result.final_memory`.

---

## 2. RED / GREEN & Regression Results

### 2.1 Locked W2-M5 Development & Tamper Corpus (`inputs/development.json`, `inputs/oracle.json`)

| Stratum | Count | RED Before (`results/red-before.json`) | GREEN After (`results/green-after.json`) | Details |
|---|---:|---:|---:|---|
| Positive Category A primed-vertex cases (`W2-A07`, `W2-A10`, `DEV-POS-03..14`) | 14 | `0/14` (`14` `FALSE_REFUSAL`) | `14/14` (`0` `FALSE_REFUSAL`) | `14/14` `SERVED_CORRECT` with `100%` exact `Fraction` oracle match across triangular/quadrilateral/oblique prisms, cuboids, cubes, `section_area`, `section_only`, `volume_ratio`, `residual_volume`, and `declared_boundary` |
| Mandatory fail-closed tamper cases (`TAMPER-01..12`) | 12 | `12/12` | `12/12` | All 12 tamper modes (`MISSING_POINT_OBJECT`, `WRONG_OBJECT_TYPE`, `COORDINATE_MISMATCH`, `OFF_EDGE_VERTEX`, `EDGE_NOT_IN_SOLID`, `NON_COPLANAR_POLYGON`, `NON_SIMPLE_CYCLE_ORDER`, `DEGENERATE_ZERO_AREA`, `AREA_MEMORY_MISMATCH`, `CATEGORY_MIXING_SPOOF`, `FORGED_PROVENANCE_STATED`, `RAW_PRIME_LEAK_IN_NOTATION`) refused with `PREVIEW_VALIDATION_FAILED` |

### 2.2 Full 96-Case Holdout Wave 2 Post-Feedback Regression (`results/wave2-post-feedback-regression.json`)

- **Evidence Classification:** `POST_FEEDBACK_DEVELOPMENT_REGRESSION` (historical Holdout Wave 2 artifacts at `ecdc26b012c8ce80d53524a98dc75cdcb020079d` are preserved 100% untouched).
- **Historical Trajectory Across All 96 Holdout Wave 2 Cases:**

| Milestone | Positive `SERVED_CORRECT` (`48`) | Category B (`36`) | Category A (`12`) | `FALSE_REFUSAL` (`48`) | Negative Refused (`48`) | Genuine `WRONG_SERVED` (`96`) |
|---|---:|---:|---:|---:|---:|---:|
| Historical Raw (`d7a94d3c` / `ecdc26b0`, `scored-run-1`) | `3/48` (`6.25%`) | `3/36` | `0/12` | `43/48` | `48/48` (`33/48` reason) | `0/96` (`2` harness bugs on `W2-A01`, `W2-A03`) |
| Historical Adjudicated (`d7a94d3c` / `ecdc26b0`, `scored-run-2`) | `5/48` (`10.42%`) | `3/36` | `2/12` | `43/48` | `48/48` (`33/48` reason) | `0/96` |
| Source Gate `/19` (`d99f6149`) | `45/48` (`93.75%`) | `36/36` | `9/12` | `3/48` (`W2-A04`, `W2-A07`, `W2-A10`) | `48/48` (`36/48` reason) | `0/96` |
| W2-M4 Exact Radical (`051224ee` / `eb661971`) | `46/48` (`95.83%`) | `36/36` | `10/12` | `2/48` (`W2-A07`, `W2-A10`) | `48/48` (`36/48` reason) | `0/96` |
| **W2-M5 Category A Identity (`73ca8d92`, Raw Historical Scorer)** | **`47/48` (`97.92%`)** | **`36/36`** | **`11/12`** | **`0/48`** | **`48/48` (`36/48` reason)** | **`0/96`** (`1` scorer `objects_by_id` lookup bug on `W2-A10`) |
| **W2-M5 Category A Identity (`73ca8d92`, Scorer-Adjudicated)** | **`48/48` (`100.00%`)** | **`36/36`** | **`12/12`** | **`0/48`** | **`48/48` (`36/48` reason)** | **`0/96`** |

- **Independent Scorer Diagnosis on `W2-A10` ([`results/w2-a10-scorer-adjudication-receipt.json`](results/w2-a10-scorer-adjudication-receipt.json)):**
  - In frozen `evaluate_holdout_wave2.py` (`ecdc26b0`), `_find_point_xyz(objects_by_id, label)` is defined at line `146` to look up primed labels in `objects_by_id` and is called at line `232`, but line `184` wrote `elif v.get("label") and v["label"] in objects_by_id:`. Because `"A'" not in objects_by_id` (keyed by `"A_prime"`), `"A'"` falls through to `poly_idx = 0`, colliding with `I` at `poly_raw[0]` (`poly_idx = 0`) and scrambling the actual product cycle `[I, A', I2, I1]` into `[A', I, I2, I1]`.
  - When `evaluate_holdout_wave2.py:184` uses its own `_find_point_xyz(objects_by_id, v["label"])`, `W2-A10` scores `SERVED_CORRECT` (`boundary_cycle_match = True`, `area_squared = 504`), yielding **`48/48` (`100.00%`)** positive `SERVED_CORRECT` (`36/36` Category B, `12/12` Category A) and **`48/48`** negative safe refusals (`0/96` wrong-served, `96/96` learner-facing source-identity clean).

---

## 3. Tiered Verification (`T0`–`T3`) & Independent Review

- **T0 (`verification/impact-plan.json`, `verification/scope-and-evidence.json`, `verification/cache-and-fixtures.json`):**
  - Product diff (`eb661971..b61f1699`) is strictly `1` file (`backend/app/ai/adapter4_route.py`).
  - Cache identity lock `MATCH` (`CACHE_VERSION = 130`), `41/41` stored preview fixtures verified (`0` problems).
  - Publication safety scan over branch range `eb661971..b61f1699`: `exit_code = 0` (`0` violations).
- **T1 & T2 (`verification/t1-t2.log`, `verification/tiers.json`):** `670 passed in 65.63s` (`0` failures), including `test_w2_m5_adapter4_category_a_identity.py` (`17/17`), `test_adapter4_response.py`, `test_adapter4_plane_section_certificate.py`, `test_section_display_identity.py`, `test_display_identity_source_names.py`, `test_hybrid_contract_v2.py`, `test_hybrid_offline.py`, `test_holdout_failure_repair.py`, `test_radical_domain.py`, `test_source_gate_language.py`, `test_evaluation_candidate.py`, and `test_thesis_acceptance_matrix.py`.
- **Full T3 on Clean Detached Checkout (`verification/full-t3/receipt.json`, `verification/full-t3/full-t3.log`):**
  - Candidate SHA: `b61f16995dfbe0110a639a2127d0fb5a9c3afde0` (clean detached checkout, `source_tree_before = ""`, `source_tree_after = ""`).
  - Verdict: `FULL_PRODUCT_GATE_PASS` (`exit_code = 0`).
  - Backend pytest: `12569 passed, 1 skipped, 2 deselected, 15 xfailed, 1 warning in 604.66s (0:10:04)` (`0` failures).
  - Frontend vitest: `83 passed (83)` files, `1417 passed (1417)` tests.
  - Typecheck + production build: `PASS` (`7.7s`).
  - Thesis demo replay: `5/5 PASS` + `1/1 expected REFUSAL` (`0.7s`).
  - Demo crash surface: `6/6 PASS` (`0.4s`).
  - Post-T3 `freeze_evaluation_candidate.py --verify`: `MATCH` (`118` files, tree hash `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d`).
  - Log SHA-256: `b62158a63210a4a7b7905a6224e20c7386e9788eac45b3bd722579396745b824` (`167652` bytes).
- **Independent Review (`review.md`):** Audited by independent reviewer subagent (`155dd101-7d6a-4edb-9606-b9b56b1bba45`); verdict `APPROVED_NO_FINDINGS` (`0 BLOCKER, 0 MAJOR, 0 MINOR, 0 NIT`).
