# PRODUCTION DYNAMIC FUNCTION COMPOSITION REPORT

> **Run ID:** `hybrid-production-composition`
> **Branch:** `feat/hybrid-production-composition`
> **Base Commit (Verified Phase 0 Candidate):** `ad311e043` (`feat/hybrid-backend-capabilities`)
> **Product Commit:** `73d055025` (`73d055025aa58cfb3d14be42e7f21e26a3eb9fa0`)
> **Measured System:** `so_file = 106` hashed entries (`105` unique files: `100` in `backend/app` + `5` in `frontend/src/simulations/domains/semantic`), `tree_hash = 8213236916b27d8519805d41150e9e44f1b86161b39f0877aca1c64bb7bb17f2`, `CACHE_VERSION = 132` (unchanged)
> **Phase 0 Verdict:** `PREVIOUS_CANDIDATE_VERIFIED`
> **Phase 1 Verdict:** `PRODUCTION_DYNAMIC_COMPOSITION_VERIFIED`
> **Live Provider Calls:** `0` (`ALLOW_LIVE_AI=0`)
> **Independent H-1 Status:** `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`

---

## 1. Phase 0 — Verification of Previous Candidate (`feat/hybrid-backend-capabilities`)

Before starting Phase 1, the previous candidate worktree (`.superpowers/worktrees/hybrid-backend-capabilities`, branch `feat/hybrid-backend-capabilities`) was audited, reconciled, and verified end-to-end:

1. **Evidence & Documentation Reconciliation (8 Items):**
   - **Item 1 (Test count 15 vs 17):** Added the 2 missing regression tests (`test_gap2_independent_secondary_unresolved_preserved_when_unrelated_to_primary` and `test_gap1_named_described_point_on_line_structural_rejection`) to `backend/tests/geometry/test_hybrid_capability_composition.py` (`17/17 PASS`).
   - **Item 2 (Measured system file count):** Documented the exact distinction across all docs and `run.json`: `3` declared `MEASURED_PATHS` entries, `106` hashed file entries (`so_file = 106` because `frontend/src/simulations/domains/semantic/semantic_program.schema.json` is listed both under its directory and explicitly), and `105` unique files (`100` in `backend/app/**` + `5` in `frontend/src/simulations/domains/semantic/**`).
   - **Item 3 (Registry function counts):** Reconciled exact counts from `registry.py`: `49` total registered `FunctionSpec` entries (`31` with `provider_offered=True`, `18` with `provider_offered=False`, `1` with `auxiliary_only=True`, and `30` exposed in `function_declarations()`).
   - **Item 4 (S-2 clarification numbers):** Distinguished C26 stored live-extraction replay on the S-2 36-case slice (`CLARIFY` status `3/6 -> 5/6`, strict `CORRECT_CLARIFICATION` `0/6 -> 3/6`, strict gold-projection E2E `26/36 -> 29/36`) from S-2 deterministic gold-extraction replay (`35/36` served, `1/36` intentional refusal `S2-17`).
   - **Item 5 (Cold-start vs warm performance):** Separated `cold_start_first_case_wall_ms = 551.414 ms` from warm execution (`warm_wall_p50_ms = 243.498 ms`, `warm_wall_p95_ms = 295.702 ms`, `warm_cpu_p50_ms = 250.0 ms`, `warm_peak_memory_max_kb = 1165.24 KiB`).
   - **Item 6 (Planner structural line inference):** Hardened `_tren_duong` in `planner.py` so `divide_segment` endpoints and `("desc", "midpoint"|"divide_segment"|"orthogonal_projection_line", ...)` points are recognized structurally on their carrier line before candidate emission.
   - **Item 7 (Local companion unresolved pruning):** Scoped `_repair_unresolved_clarifications` in `typed_fact_next_extraction.py` so companion unresolved pruning only drops empty-role sub-spans or simulation-action echoes when an actual math/clarification companion exists, preserving independent unresolved items.
   - **Item 8 (Commit & candidate freeze):** Committed on `feat/hybrid-backend-capabilities` (`3f87f693b` + `ad311e043`), verified `freeze_evaluation_candidate.py --verify` (`tree_hash = 6e5e08c8a4ca0341b6c7c8ca57060fbaff74c7b86aa6ea3f12781005f494f8ed`), `audit_docs_information_architecture.py` (`PASS`), `check_publication_safety.py` (`PASS`), and `test_s2_student_language_pilot_runner.py` (`106 passed`).

---

## 2. Baseline Analysis — Why Production Routes Had `search_generated_steps == []`

In the baseline architecture (`planner.py` `/26`, `registry.py` `/33`, `typed_fact_next_bridge.py` `/2`, `engine.py` `/24`), planner executions fall into three capability classes:

1. **`SOURCE_EXPLICIT_SEQUENCE`:** Every construction step is explicitly named and declared in the problem premises (`planner_originated_steps == []` or only solid-definition restatements in `source_defined_steps`).
2. **`REGISTERED_DECOMPOSITION`:** The planner expands a registered macro/rule (`AUXILIARY_RULES`, `POINT_DEFINITIONS` such as `orthocenter`/`circumcenter` via `_dinh_nghia`, `MAT_RANG_BUOC` via `_mat_rang_buoc`, or `_RULE_POLICIES` such as `projection_foot`, `distance_witness`, `section_vertex`, `declared_intersection`).
3. **`DISCOVERED_FUNCTION_COMPOSITION`:** `_EffectResolver` chains multiple production `PlanningContract`s backward from a typed goal where an intermediate construction step is neither a source-named premise nor a pre-registered macro rule (`search_generated_steps != []`).

### Identified Production Composition Gap

In baseline:
- `TypedFactNextPayloadV2` (`typed_fact_next.py`) already defined `MAX_DESCRIBED_DEPTH = 2` and allowed `DescribedPointSpec` operands to reference another `@described_id`.
- However, `_mo_ta_phang` in `typed_fact_next_bridge.py` unconditionally refused **all** nested `@id` references (`if any(is_described_ref(x) for x in d.point_operands()): raise TuChoi("BRIDGE_UNSUPPORTED_DESCRIBED_POINT", ...)`).
- Consequently, every `DescribedPointSpec` reaching `_EffectResolver` on the production `Hybrid /4` route had depth `1` (a single descriptor contract whose inputs were already named points/lines/planes), which `_EffectResolver._emit` tagged as `source_defined` (`contract.descriptor` with zero producer child inputs) followed by a `registered` goal/foot step (`_RULE_POLICIES`).
- Thus, `_EffectResolver` never executed a multi-contract descriptor composition chain (`Point <- Point <- ...`) on the production route, leaving `search_generated_steps == []` across all production runs.

---

## 3. Selected Production `PlanningContract`s & Minimal Safe Extension

### 3.1 Audited Production Contracts Participating in Composition

| Function (`REGISTRY`) | Input Terms | Output Effect | Preconditions / Verifier | Role in Multi-Step Composition |
| :--- | :--- | :--- | :--- | :--- |
| `midpoint` | `Point(A), Point(B)` | `Point(M)` | `descriptor="midpoint"`, `2M = A + B` | Inner derived point producer (`@d1`) |
| `centroid` | `Point(A), Point(B), Point(C)` | `Point(G)` | `descriptor="centroid"`, non-collinear `ABC`, `3G = A + B + C` | Inner derived point producer (`@d1`) |
| `intersect_line_line` | `Line(L1), Line(L2)` | `Point(I)` | `descriptor="intersect_line_line"`, coplanar intersecting lines | Inner derived point producer (`@d1`) |
| `intersect_line_plane` | `Line(L), Plane(Q)` | `Point(I)` | `descriptor="intersect_line_plane"`, line cuts plane | Inner derived point producer (`@d1`) |
| `orthogonal_projection` | `Point(P), Plane(Q)` | `Point(H)` | `requires=(("off_plane", "P", "Q"),)`, `descriptor="orthogonal_projection"` | Outer composed projection producer (`@d2` consuming `@d1`) |
| `orthogonal_projection_line` | `Point(P), Line(L)` | `Point(H)` / `Foot(F, P, L)` | `requires=(("off_line", "P", "L"),)`, `descriptor="orthogonal_projection_line"` | Outer composed projection producer (`@d2`) AND line-distance foot witness |
| `ask_distance_point_plane` | `Point(P), Plane(Q)` | `AnswerDistance(P, Q)` | `verifier="distance_point_plane"` | Goal consumer of composed point `@d2` |
| `ask_length` | `Point(P), Foot(F, P, L)` / `Point(P), Point(Q)` | `AnswerDistance(P, L)` / `AnswerLength(P, Q)` | `verifier="distance_point_line"` / `"length"` | Goal consumer of composed point `@d2` (including 4-step chain via `Foot`) |
| `ask_area` | `Point(A), Point(B), Point(C)` | `AnswerArea(A, B, C)` | `verifier="area"` | Multi-goal consumer sharing composed point `@d2` |

### 3.2 Minimal Safe Changes Across the 4 Modules

1. **`backend/app/simulation/geometry_functions/registry.py`:**
   - Added structural precondition `requires=(("off_plane", "P", "Q"),)` to `orthogonal_projection.planning` (`Point(P), Plane(Q) -> Point(H)`), ensuring `_EffectResolver._unmet` rejects projecting a point onto a plane it already lies on.
   - Added recursive phrase builder `_cum_mo_ta_cay(op)` and recursive `effect-chain` validation in `kiem_nguon` so that a 2-level `effect-chain` certificate (`cert["operand"]["nested"]`) verifies every call in `cert["chain"]` against its `PlanningContract` template AND verifies the full nested Vietnamese description verbatim in the problem text and goal quote.
2. **`backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`:**
   - Extended `_mo_ta_phang` and `_mo_ta_cua` for bounded depth-2 projection chains (`d.kind in ("orthogonal_projection", "orthogonal_projection_line")` whose `d.point` references a depth-1 `@inner` with a direct `PlanningContract` descriptor `c.call != ()` and explicit `"của"` phrasing grounded inside `d.quote`), emitting `point_tree = {"point_kind": inner.kind, "points": ...}` on the bridged `TypedFact`.
   - Preserved `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` fail-closed refusal for depth `>= 3`, non-projection outer kinds (such as `D1` in `r1-described-point-probe.json`), dual described points (`D2`), and property-defined inner points (`orthocenter`, `circumcenter`).
3. **`backend/app/simulation/geometry_functions/planner.py`:**
   - Extended `_cay_mo_ta` to recursively build nested `("desc", outer_kind, (inner_desc, target))` terms from `f.point_tree`.
   - Extended `_EffectResolver._tren_duong` and `_tren_mat` to inspect nested `("desc", ...)` terms structurally, and updated `_EffectResolver._resolve` reuse matching so fresh calls are reused across multiple goals when their resolved child labels match (`reused_intermediates`).
   - Updated `_EffectResolver._emit` step provenance so a descriptor step that composes a non-trivial producer child (`composed = bool(contract.descriptor) and any(ch.fn is not None for ch in choice.inputs)`) is recorded as `'search_generated'`, yielding `classification == "DISCOVERED_FUNCTION_COMPOSITION"` and `search_generated_steps != []`.
   - Extended `_EffectResolver._chuoi` to attach `cert["operand"]["nested"]` for 2-level composed points.
4. **`backend/app/simulation/geometry_functions/engine.py`:**
   - Extended `_Dung.kiem_chuoi` to verify `cert["operand"]["nested"]` in the exact Euclidean coordinate frame (`_kiem_mo_ta_diem` on both the inner point label `G` and the outer projected point label `H`, plus exact goal distance/length/area agreement).

---

## 4. Discriminating Composition Proof (Test Families A–D) & Ablation Study

All 11 tests in [`backend/tests/geometry/test_production_dynamic_composition.py`](../../../../backend/tests/geometry/test_production_dynamic_composition.py) pass (`11/11 PASS`):

| Test ID | Family / Purpose | Discovered Production Chain (`plan.calls` suffix) | Exact Answer & Oracle Match | Classification & Telemetry |
| :--- | :--- | :--- | :--- | :--- |
| `test_family_a1_*` | **Family A:** 3-step sequential composition (Pyramid `S.ABCD`) | `centroid(SBC) -> orthogonal_projection((ABCD)) -> ask_distance_point_plane((SAD))` | `4/3` (`Fraction(4, 3)`) | `DISCOVERED_FUNCTION_COMPOSITION`, `search_generated_steps=['q1_aux2']`, `depth=3` |
| `test_family_a2_*` | **Family A:** 4-step sequential composition to named line `AB` | `centroid(SBC) -> orthogonal_projection((ABCD)) -> orthogonal_projection_line(AB) -> ask_length` | `2/3` (`Fraction(2, 3)`) | `DISCOVERED_FUNCTION_COMPOSITION`, `search_generated_steps=['q1_aux2']`, `depth=3`, `reused=2` |
| `test_family_a3_*` | **Family A:** 3-step sequential composition with line projection | `midpoint(SC) -> orthogonal_projection_line(BD) -> ask_distance_point_plane((SAB))` | `1` (`Fraction(1, 1)`) | `DISCOVERED_FUNCTION_COMPOSITION`, `search_generated_steps=['q1_aux2']`, `depth=3` |
| `test_family_b1_*` | **Family B:** Shared 2-step intermediate `@h1` across distance + area goals | `centroid -> orthogonal_projection -> orthogonal_projection_line -> ask_length` + `ask_area` | `q1 = 2/3`, `q2 = √5` | `DISCOVERED_FUNCTION_COMPOSITION`, `reused_intermediates=4`, `centroid` & `orthogonal_projection` built once |
| `test_family_c1_*` | **Family C:** Pyramid with ratio point `divide_segment(SC, 2/3)` + 2-step composition | `divide_segment -> centroid(EAB) -> orthogonal_projection((ABCD)) -> ask_distance_point_plane + ask_length` | `q1 = 5/3`, `q2 = √29/3` | `DISCOVERED_FUNCTION_COMPOSITION`, `reused_intermediates=2`, `search_generated_steps=['q1_aux2']` |
| `test_family_c2_*` | **Family C:** Right triangular prism `ABC.A'B'C'` 4-step composition + multi-goal reuse | `midpoint(B'C') -> orthogonal_projection((ABC)) -> orthogonal_projection_line(AC) -> ask_length + ask_distance_point_plane` | `q1 = 1`, `q2 = 1` | `DISCOVERED_FUNCTION_COMPOSITION`, `reused_intermediates=4`, `search_generated_steps=['q1_aux2']` |
| `test_family_d1_*` | **Family D:** Source Gate mismatch (`polygon=["S","C","D"]` vs quote `"tam giác SBC"`) | Refused before execution | `REFUSED` (`SOURCE_OBJECT_MISMATCH`) | `0` wrong-served |
| `test_family_d2_*` | **Family D:** Out-of-scope inner property point (`orthocenter` inside `orthogonal_projection`) | Refused at bridge boundary | `REFUSED` (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT`) | `0` wrong-served |
| `test_family_d3_*` | **Family D:** Degenerate/collinear inner triangle (`ABM` where `M = mid(AB)`) | Refused by Exact Kernel | `REFUSED` (`COLLINEAR_POINTS`) | `0` wrong-served |
| `test_family_d4_*` | **Family D:** Search depth budget cap (`MAX_EFFECT_DEPTH=2`) & tampered nested certificate | Refused fail-closed | `REFUSED` (`PLAN_TOO_LARGE` / `AUXILIARY_RULE_MISMATCH`) | `0` wrong-served |
| `test_section_vii_ablation_*` | **Section VII Ablation:** Explicit premises (`G`, `H`) vs ablated premises (goal-only) vs contract ablation | Identical 4-step call sequence & exact answer `2/3`; contract ablation fails closed | `2/3` (`REGISTERED_DECOMPOSITION` -> `DISCOVERED_FUNCTION_COMPOSITION` -> `REFUSED`) | Proves genuine dynamic composition from `PlanningContract`s |

---

## 5. Performance & Search Telemetry (`results/production_composition_metrics.json`)

Measured by [`docs/evaluation/geometry/runs/hybrid-production-composition/tools/measure_production_composition.py`](tools/measure_production_composition.py):

- **Planner-only CPU time:** `p50 = 1.782 ms`, `max = 3.957 ms`
- **Full Hybrid route warm latency (3-run median per case):** `p50 = 40.794 ms`, `p95 = 55.332 ms`
- **Full Hybrid route cold-start latency:** first case `1599.860 ms` (module/schema initialization), subsequent cases `p50 = 216.517 ms`
- **Peak traced memory:** `max = 1891.28 KiB` (cold first case), warm/subsequent cases `418.28 – 607.71 KiB`

| Case ID | Classification | `explored_states` | `candidate_evaluations` | `max_depth_reached` | `reused_intermediates` | `search_generated_steps` | `planner_cpu_ms` | `route_warm_ms` |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| `A1-centroid-proj-plane-dist` | `DISCOVERED_FUNCTION_COMPOSITION` | `9` | `4` | `3` | `0` | `["q1_aux2"]` | `3.957` | `22.948` |
| `A2-centroid-proj-plane-line-dist` | `DISCOVERED_FUNCTION_COMPOSITION` | `9` | `4` | `3` | `2` | `["q1_aux2"]` | `1.782` | `40.992` |
| `A3-midpoint-proj-line-plane-dist` | `DISCOVERED_FUNCTION_COMPOSITION` | `8` | `4` | `3` | `0` | `["q1_aux2"]` | `1.261` | `30.741` |
| `B1-shared-intermediate-two-goals` | `DISCOVERED_FUNCTION_COMPOSITION` | `12` | `5` | `3` | `4` | `["q1_aux2"]` | `2.040` | `40.794` |
| `C1-ratio-centroid-proj-multi-goal` | `DISCOVERED_FUNCTION_COMPOSITION` | `11` | `5` | `3` | `2` | `["q1_aux2"]` | `1.763` | `42.257` |
| `C2-right-prism-four-step-multi-goal` | `DISCOVERED_FUNCTION_COMPOSITION` | `11` | `6` | `3` | `4` | `["q1_aux2"]` | `2.098` | `55.332` |
| `Ablation-Control-Explicit-Premises` | `REGISTERED_DECOMPOSITION` | `5` | `2` | `2` | `0` | `[]` | `1.295` | `32.267` |

---

## 6. Scope Boundaries & Remaining Limitations

1. **Nested Described Points Scope (Section IX):** Only bounded depth-2 compositions where the outer operator is a projection (`orthogonal_projection`, `orthogonal_projection_line`) and the inner operator is a direct `PlanningContract` descriptor (`midpoint`, `centroid`, `intersect_line_line`, `intersect_line_plane`, `orthogonal_projection`, `orthogonal_projection_line`) with explicit `"của"` source grounding are enabled. General depth `>= 3` trees, dual-described segments (`D2`), and property-defined inner points (`orthocenter`, `circumcenter`) remain fail-closed (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT`).
2. **Scientific & Deployment Boundaries (Section XII):**
   - `HYBRID_DEFAULT_CUTOVER_COMPLETE = YES`
   - `LEGACY_EXECUTION_RETIRED = YES`
   - `LEGACY_FULLY_RETIRED = NO`
   - `PRODUCTION_DEPLOYMENT_VERIFIED = NO`
   - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (diagnostic and ablation suites prove production dynamic composition capability, not independent H-1 generalization).
