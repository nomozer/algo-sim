# Independent Technical Review Report — `HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR`

- **Reviewer Conversation ID**: `155dd101-7d6a-4edb-9606-b9b56b1bba45`
- **Overall Verdict**: `APPROVED_NO_FINDINGS`
- **Findings Summary**: `BLOCKER: 0`, `MAJOR: 0`, `MINOR: 0`, `NIT: 0`
- **Reviewed Worktree**: `.superpowers/worktrees/w2-m5-adapter4-category-a-identity-repair`
- **Reviewed Branch**: `research/hybrid-v2-w2-m5-adapter4-category-a-identity-repair`
- **Verified Commit Chain**:
  - Baseline `main`: `eb661971847c034500862299c5091f1f3d2a2998`
  - Product commit: `73ca8d92e74059680ce53b99692af396df37a2f8`
  - Test & evaluation artifacts commit: `7aa538aecf2d31c40887b7c6ee52f7e8219ea0eb`
  - Frozen Full T3 candidate commit: `b61f16995dfbe0110a639a2127d0fb5a9c3afde0`
- **Verified Measured Product Tree Hash**: `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` (`118` files)

---

## Item-by-Item Verification (Owner GO Section 7)

### 1. Product Diff Scope — `PASS`
- Independently inspected `git diff eb661971847c034500862299c5091f1f3d2a2998..b61f16995dfbe0110a639a2127d0fb5a9c3afde0 -- backend/app frontend/src`.
- Confirmed **ONLY** `backend/app/ai/adapter4_route.py` (`_validate_sections` and `_polygon_area_squared`) was modified across all product directories (`136 insertions(+), 18 deletions(-)`).
- Confirmed active runtime identities and policies remain untouched:
  - `REGISTRY_VERSION == "geometry-functions/19"`
  - `PLANNER_VERSION == "geometry-fact-planner/17"`
  - `ENGINE_VERSION == "geometry-function-engine/14"`
  - `ADAPTER_V4_VERSION == "hybrid-simulation-adapter/4"`
  - `ROUTE_D_SIMULATION_V4_SCHEMA_VERSION == "hybrid-route-d-simulation/4"`
  - `PLANE_SECTION_CERTIFICATE_VERSION == "plane-section-certificate/1"`
  - `CACHE_VERSION == "130"`
  - `CHE_DO_MAC_DINH == "LLM_ONLY"` (`che_do() == "LLM_ONLY"`)
  - `ALLOW_LIVE_AI == "0"`
- Confirmed zero diff against historical Holdout Wave 2 commit `ecdc26b012c8ce80d53524a98dc75cdcb020079d` under `docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2`.

### 2. Strict Separation of Category A and Category B — `PASS`
- Inspected `backend/app/ai/adapter4_route.py:256–276` and `:440–723`.
- Category A (`DINH_CAT_CANH`) and Category B (`ENGINE_DERIVED_SECTION` / `plane-section-certificate/1`) are strictly partitioned:
  - Lines `268–270`: If a section is in `dinh_cat_by_id` (Planner `DINH_CAT_CANH`) and simultaneously carries `certificate_category == "ENGINE_DERIVED_SECTION"` or `"certificate_version" in section`, `_validate_sections` immediately raises `PreviewInvalid("PREVIEW_RESULT_INVALID")`.
  - Lines `274–276`: Non-Category-B sections must match a `DINH_CAT_CANH` entry in `result.planner["auxiliary"]` when `result is not None`.
  - `_validate_engine_derived_section` (lines `440–723`) is completely untouched and has no cross-fallback from or to Category A.

### 3. No Silent Fallback or Weakening of Section Verification — `PASS`
- Inspected `point_of(label)` (`backend/app/ai/adapter4_route.py:241–254`), `_validate_sections` (`:256–401`), and `_polygon_area_squared` (`:403–437`):
  - **One-way canonical lookup**: `point_of(label)` rejects non-strings, empty strings, or any label containing `"_prime"`. It normalizes prime glyphs via `canon = name(label)`, resolves `pt = objects.get(ir_name(canon))`, verifies `pt.get("type") == "point3"`, and checks `name(str(pt["notation"])) == canon` when `notation is not None` (or `pt["id"] == label` for unnamed auxiliary points).
  - **Solid & Vertex Identity**: Verifies unique referenced `solid` in `obj["depends"]`, `name(solid["notation"]) == name(d_aux["solid"])`, self-consistent `vertex_ids`/`vertices`/`faces`, and distinct `point["id"]` and exact `Fraction` 3D coordinates (`seen_pt_ids`, `seen_xyz`, `>= 3` vertices).
  - **Edge Membership & Exact Rational Parameter $t \in [0, 1]$**: Resolves both endpoints of `vertex["edge"]` via `point_of`, verifies `frozenset(edge) in solid_edges`, checks `obj["vertex_sources"][index]` (`SOLID_VERTEX` vs `SOLID_EDGE_INTERSECTION`), and computes exact rational collinearity parameter $t$ across all 3 coordinates (`t in {0, 1}` for `SOLID_VERTEX`, `0 < t < 1` for `SOLID_EDGE_INTERSECTION`).
  - **Provenance & Statedness**: Enforces `_NGUON_GOC` membership, `notation` presence/absence, `stated` boolean agreement against `d_aux["stated_edges"]`, and `origin == "derived"` for `DERIVED_FRESH`.
  - **Cyclic Face-Adjacency & Boundary Order**: Verifies consecutive vertices in `obj["polygon"]` share at least one common face of `solid` (`fc & fn`), and when `boundary` is present, verifies `cycle(boundary, cert["boundary"])` and `cycle([point_of(label)["xyz"] for label in boundary], obj["polygon"])`.
  - **Coplanarity, Convexity & Exact Area-Squared Agreement**: `_polygon_area_squared` verifies in exact `Fraction` arithmetic that all polygon triangles share parallel cross-product normals (`ck.cross(c1).is_zero()`) with positive orientation (`lam > 0`) and `area_sq > 0`, and cross-checks `_binh_phuong(result.exec_result.final_memory[f"kq_{c['id']}"]) == area_sq` for any `ask_section_area` call on the cutting plane.

### 4. Mathematical & Certificate Correctness of `W2-A07` and `W2-A10` — `PASS`
- Independently executed `W2-A07` and `W2-A10` against `run_typed_fact_next_v2_route` and `build_adapter4_response` and verified all artifacts (`inputs/development.json`, `inputs/oracle.json`, `results/red-before.json`, `results/green-after.json`, `results/wave2-post-feedback-regression.json`, `results/w2-a10-scorer-adjudication-receipt.json`):
  - `W2-A07`: Served with `status == "SERVED"`, Category A (`DINH_CAT_CANH`), vertices `["A'", "M", "N"]` (`A'` on `AA'`, `M` at $t = 3/4$ on `BB'`, `N` at $t = 1/2$ on `CC'`), exact `area_squared = 1875/8`, and formatted answer `"25√6/4"`.
  - `W2-A10`: Served with `status == "SERVED"`, Category A (`DINH_CAT_CANH`), `section_only`, 4-vertex cycle `[I (BB', t=8/9), A' (AA', vertex), I2 (DD', t=5/9), I1 (CC', t=4/9)]` matching oracle cycle `[A', BB'(8/9), CC'(4/9), DD'(5/9)]` under reversal, and exact polygon `area_squared = 504`.
  - Confirmed independent diagnosis of `evaluate_holdout_wave2.py:184-185`: `evaluate_holdout_wave2.py` defines `_find_point_xyz(objects_by_id, label)` at line `146` and uses it at line `232`, but line `184` checks `v["label"] in objects_by_id` directly (which is `False` for `"A'"` because `objects_by_id` is keyed by `"A_prime"`), causing `poly_idx` for `"A'"` to fall back to `0` and collide with `I` at `poly_raw[0]`. Confirmed `evaluate_holdout_wave2.py` itself was **not** modified.

### 5. 12 Mandatory Tamper Modes Refused (`TAMPER-01..12`) — `PASS`
- Inspected `results/tamper-results.json` and executed `backend/tests/geometry/test_w2_m5_adapter4_category_a_identity.py` (`17 passed in 2.04s`).
- Confirmed all 14 positive development cases (`14/14`) are served with exact oracle match (`results/red-before.json`: `0/14` before fix; `results/green-after.json`: `14/14` after fix).
- Confirmed all 12 mandatory tamper modes (`TAMPER-01..12`) plus 3 additional machine-ID leak tamper modes (`15/15` total tamper cases in pytest) fail closed with `PreviewInvalid("PREVIEW_RESULT_INVALID")` and `route_d.status == "REFUSED"`.

### 6. Zero `_prime` Machine-ID Leak to Learner Surface — `PASS`
- Independently verified across all 14 positive development cases and all 96 Wave 2 holdout cases (`learner_facing_source_identity_clean_count == 96/96`):
  - `route_d["sections"][*]["vertices"][*]["label"]`, `vertex["edge"]`, and `section["boundary"]` preserve `"A'"` (ASCII apostrophe) and never contain `"_prime"`.
  - `scene3d["objects"]["A_prime"]["notation"]` is `"A′"` (Unicode prime `\u2032`).
  - Zero occurrences of `"_prime"` in learner-facing `notation`, `label`, `value`, `formation.steps[*].learner_text`, `events[*].learner_text`, `events[*].explanation`, or `route_d.sections`.

### 7. Candidate Freeze & Detached Full T3 Gate — `PASS`
- Inspected `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`, `candidate_divergence.json`, `verification/scope-and-evidence.json`, `verification/cache-and-fixtures.json`, `verification/tiers.json`, and `verification/full-t3/receipt.json`:
  - `EVALUATION_CANDIDATE.json`: `"cay_lam_viec_sach": true`, `"product_commit_sha": "73ca8d92e74059680ce53b99692af396df37a2f8"`, `"so_file": 118`, `"tree_hash": "1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d"`.
  - `verification/full-t3/receipt.json`: `"candidate": "b61f16995dfbe0110a639a2127d0fb5a9c3afde0"`, `"detached": true`, `"verdict": "FULL_PRODUCT_GATE_PASS"`, `"source_integrity": "MATCH"`, `"12569 passed, 1 skipped, 2 deselected, 15 xfailed, 1 warning in 604.66s (0:10:04)"` (backend), `"Test Files 83 passed (83)"` / `"Tests 1417 passed (1417)"` (frontend), `"live_provider_calls": 0`.
  - Independently recomputed and verified SHA256 digests of all 7 locked evidence files in `verification/scope-and-evidence.json` and `verification/full-t3/full-t3.log` (`b62158a63210a4a7b7905a6224e20c7386e9788eac45b3bd722579396745b824`, `167652` bytes).
