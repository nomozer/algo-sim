# ALGOSIM — GOAL-DRIVEN PLANNER & GENERALIZATION VERIFICATION REPORT

- **Run ID:** `hybrid-goal-driven-planner`
- **Date:** `2026-11-08`
- **Branch:** `feat/hybrid-goal-driven-planner` (isolated worktree `.superpowers/worktrees/hybrid-goal-driven-planner`, branched from `feat/hybrid-production-composition` at `fb291cba3069fa9f5fa8d28893c064b4ec523ae7`)
- **Base on `main`:** `main = origin/main = bb046fa22aceff47abe22aa783aa64fc65caee13`
- **Product Commit:** `6c961c884` (`6c961c88470388bc4bf7242d15d7a7a721ede1a5`, `measured_system.tree_hash = 2dcfff5328656264cb1df117874b8714cb2be7e5fe05e60ab233e2dc83fa1fca`)
- **Merged / Pushed:** `NO` / `NO` (`frontend/**` untouched, `0` live Gemini/provider calls, `ALLOW_LIVE_AI=0`)
- **Verdicts:**
  - `PHASE0_VERDICT = PREVIOUS_CANDIDATE_VERIFIED`
  - `GOAL_DRIVEN_PLANNER_VERDICT = GOAL_DRIVEN_COMPOSITION_VERIFIED`
  - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`

---

## 1. Phase 0 — Final Candidate Validation (`feat/hybrid-production-composition` at `fb291cba3`)

### 1.1 Mathematical Audit of `orthogonal_projection` and `off_plane(P, Q)` (Section II.1)

We audited `backend/app/simulation/geometry_functions/registry.py`, `planner.py`, and `engine.py` on the Phase 0 candidate (`fb291cba3` / product commit `93b0dfcef`) against the 4 mandatory mathematical questions:

1. **Which exact contract(s) in `registry.py` declared `requires=(("off_plane", ...),)`?**
   - **None.** Neither `orthogonal_projection.planning` (`PlanningContract(effect=EffectTerm("Point", ("H",)), descriptor="orthogonal_projection", inputs=(EffectTerm("Point", ("P",)), EffectTerm("Plane", ("Q",))), args={"point": "P", "plane": "Q", "image": "H"}, fresh=("H",))` at `registry.py` lines 1682–1684) nor `orthogonal_projection.planning_extra[0]` (`EffectTerm("Normal", ("Q", ("H", "Z")))` at `registry.py` lines 1685–1687) carried `requires=(("off_plane", ...),)`.
   - Instead, commit `73d055025` had placed an ad-hoc syntactic filter inside `parse_descriptor_inputs` (`registry.py` lines 560–566):
     ```python
     if isinstance(out[0], tuple) and out[0][:1] == ("desc",):
         ref_pts = out[1][1] if (isinstance(out[1], tuple) and out[1][:1] == ("named",)) else out[1]
         if isinstance(ref_pts, (list, tuple)) and set(out[0][2]) <= set(ref_pts):
             return None
     ```
2. **Did this filter apply to all `orthogonal_projection` descriptors or only auxiliary normal/distance contracts?**
   - Because it lived in `parse_descriptor_inputs`, it applied **globally** to every nested `(Point, Line)` and `(Point, Plane)` descriptor (`orthogonal_projection` and `orthogonal_projection_line`) whenever the inner descriptor's vertex tuple was a subset of the target line/plane vertices (`set(out[0][2]) <= set(ref_pts)`), rather than being scoped to the `Normal(Q)` witness contract (`orthogonal_projection.planning_extra[0]`).
3. **Did the system falsely refuse mathematically valid problems where $P \in Q$ (`proj_Q(P) = P`)?**
   - **YES.** Mathematically, for any point $P \in Q$, its orthogonal projection onto plane $Q$ is well-defined and equals $P$ itself ($H = \operatorname{proj}_Q(P) = P$).
   - **Concrete RED reproduction (`test_phase0_1_valid_in_plane_projection_not_falsely_refused`):** In pyramid $S.ABCD$ with square base $ABCD$ of side $2$, $SA \perp (ABCD)$, $SA = 2$, let $G$ be the centroid of $\triangle ABC$ ($G = (4/3, 2/3, 0) \in (ABCD)$) and $H$ be the orthogonal projection of $G$ onto $(ABCD)$ ($H = G = (4/3, 2/3, 0)$).
     - Goal `q1`: distance from $H$ to $(SBC)$ = $\frac{\sqrt{2}}{3}$ (`"√2/3"`).
     - Goal `q2`: length of segment connecting $H$ with $S$ = $\frac{2\sqrt{14}}{3}$ (`"2√14/3"`).
     - On unmodified `fb291cba3`, `parse_descriptor_inputs` returned `None` because `set(("A", "B", "C")) <= set(("A", "B", "C", "D"))`, causing `planner.py` to falsely refuse with `FACT_INCOMPLETE`.
4. **Where are degenerate zero-length segments or zero normal vectors handled when $H = P$?**
   - **Zero normal vector ($\vec{n} = Z - H = \vec{0}$ when $Z \in Q$):** Handled at the **planner precondition layer** by declaring `free=("Z",), requires=(("off_plane", "Z", "Q"),)` on `orthogonal_projection.planning_extra[0]` (`Normal(Q)`) together with structural coplanarity pruning in `_phap_tuyen` and `_EffectResolver._tren_mat` (`_diem_tren_mat`), backed up by the Exact Kernel check in `engine.py::_kiem_mat_rang_buoc` (`self.g(n, n) == 0 -> ENGINE_SELF_CHECK_FAILED` / `PLANE_NOT_UNIQUE`).
   - **Degenerate line ($[P, H]$ with $H = P$ used as a line in angle/distance/intersection):** Handled in `engine.py` (`kiem_mat_cat` lines 2499–2514, `_goc_duong_mat_cos2` line 3061, `_goc_hai_duong_cos2` line 3076) raising `DEGENERATE_LINE`.
   - **Degenerate measured segment ($[H, P]$ with $H = P$ in `ask_length` / `_kc2_do_dai`, Family E.9):** Handled in `engine.py::_Dung._kc2_do_dai` (`if d2 == 0: raise TuChoi("DEGENERATE_POINTS", ...)`), locked by `test_family_e9_projection_coinciding_with_source_point_degenerate_segment_refused`.

### 1.2 Exact Test Count Reconciliation (Section II.2)

All test counts on the Phase 0 candidate (`fb291cba3`) were reconciled without overlapping sums:

| Partition | Collected (`--collect-only`) | Deselected (`-m "not live_provider"`) | Selected Offline | Executed & Passed | Skipped | Failed |
|---|---:|---:|---:|---:|---:|---:|
| `backend/tests/geometry/**` | `11,952` | `1` | `11,951` | `11,951` | `0` | `0` |
| `backend/tests/` (outside `tests/geometry`) | `2,041` | `2` | `2,039` | `2,038` | `1` | `0` |
| **Total Backend (`pytest tests`)** | **`13,993`** | **`3`** | **`13,990`** | **`13,989`** | **`1`** | **`0`** |
| Targeted 6-suite composition subset (`test_route_d4_described_points.py`, `test_route_d_constraint_planes.py`, `test_production_dynamic_composition.py`, `test_hybrid_capability_composition.py`, `test_planner_recomposition_oracle.py`, `test_result_binding_planning.py`) | `199` | `0` | `199` | `199` | `0` | `0` |
| Frontend release gate (`npm run test:wave` = `vitest run` across `136` files + `tsc -b` + `vite build`) | `1,998` | `0` | `1,998` | `1,998` | `0` | `0` |

### 1.3 Full T3 Candidate Verification on `fb291cba3` (Section II.3)

- `backend/scripts/freeze_evaluation_candidate.py --verify`: **PASS** (`so_file = 106` hashed entries = `105` unique files, `tree_hash = 93f69bdd2ebe7a1092acef466579f23c0626a7cd2bc6b9d24b9e840bb212d4a9`).
- `backend/scripts/audit_docs_information_architecture.py`: **PASS** (`29` root `.md` files, `167` catalogued, `0` stale paths, `0` broken links).
- `backend/scripts/check_publication_safety.py --range main..HEAD`: **PASS** (`scanned=55 messages=11 violations=0`).
- Frontend `npm run test:wave`: **PASS** (`136` test files, `1,998` tests passed, `tsc -b` clean, `vite build` clean in `3.65s`).

---

## 2. Phase A — Architectural Audit of Existing Goal-Driven Planning (Section IV)

### 2.1 Five Mandatory Architectural Questions

1. **How are goals and subgoals represented in `planner.py`?**
   - Top-level questions (`TypedFact(kind="question", role="question")`) enter `_cau_hoi` (`planner.py` lines 1304–1434) and either match a goal `PlanningContract` (`c.goal == f.quantity`, producing an `Answer*` effect such as `AnswerLength`, `AnswerArea`, `AnswerDistancePlane`, `AnswerAngleLinePlane`, `AnswerAngleLines`) or invoke `k.resolver.distance(f, point, target)` producing `AnswerDistance(P, L)`.
   - Inside `_EffectResolver._resolve(kind, operands, depth)`, each subgoal is a typed need `(kind, operands)` where `kind` is one of `AnswerDistance`, `AnswerDistancePlane`, `AnswerLength`, `AnswerArea`, `AnswerAngleLinePlane`, `AnswerAngleLines`, `Foot`, `Point`, `Line`, `Plane`, `PerpLine`, `PerpDir`, or (via `_mat_rang_buoc` / `_phap_tuyen` and `_dinh_cat_canh`) `Normal(Q)` and `SectionVertex(edge, plane)`.
2. **How are Registry contracts (`produces`, `consumes`, `requires`, `cost`) represented and matched?**
   - Each `FunctionSpec` in `registry.py` carries `planning: PlanningContract | None` and `planning_extra: tuple[PlanningContract, ...]`.
   - `PlanningContract` (`registry.py` lines 489–506) declares:
     - `effect: EffectTerm` (`produces`, e.g., `EffectTerm("Foot", ("H", "P", "L"))`, `EffectTerm("PerpLine", ("P", "L", "W", ("P", "H")))`, `EffectTerm("Normal", ("Q", ("H", "Z")))`)
     - `inputs: tuple[EffectTerm, ...]` (`consumes`, e.g., `(EffectTerm("Point", ("P",)), EffectTerm("Line", ("L",)))`)
     - `requires: tuple[tuple[str, ...], ...]` (structural preconditions checked before sub-need expansion: `("off_line", "P", "L")`, `("off_plane", "Z", "Q")`)
     - `free: tuple[str, ...]` (free slot variables bound over vertices of the reference plane/solid, e.g., `free=("Z",)`).
   - Step cost is `0` when reusing an already-emitted call (`same_call` match or premise normal/projection reuse) and `1 + sum(sub.cost for sub in sub_choices)` when emitting a new construction call.
3. **How does the planner search, prune, and rank competing candidate plans?**
   - `_EffectResolver._resolve` enumerates all `(FunctionSpec, PlanningContract, env)` bindings matching `(kind, operands)` (plus `_dinh_nghia` property-definition locus regressions for `POINT_DEFINITIONS`).
   - **Precondition pruning:** Before expanding any sub-needs of a candidate, `_unmet(contract, env)` checks `contract.requires` (`off_line`, `off_plane`) using purely structural predicates (`_tren_duong`, `_tren_mat`, `_diem_tren_mat`) with **zero coordinates**. Violating candidates are pruned and recorded in `self.rejected` (`pruned_nodes`, `rejection_reasons`).
   - **Cost ranking & deterministic tie-breaking:** Valid candidates are ranked by `(choice.cost, choice.fn or "", _nhan_ra(choice))` (`planner.py` line 2310), guaranteeing that lower-cost plans (including cost-`0` premise or intermediate reuse) strictly beat higher-cost plans and ties are broken deterministically by function name and output label.
   - **Search budgets:** Bounded by `MAX_EFFECT_DEPTH = 4`, `MAX_EFFECT_NEEDS = 96`, `MAX_EFFECT_CANDIDATES = 48`, `MAX_RESULT_LINES = 4`, `MAX_RESULT_FEET = 16`, `MAX_CALLS = 64`; exceeding any bound fails closed with `PLAN_TOO_LARGE` (`outcome="SEARCH_EXHAUSTED"`).
4. **How are intermediate results reused across subgoals and across multiple math goals?**
   - Within `_EffectResolver`, `self.memo[(kind, operands)]` caches resolved `_Choice` objects across goals, and `_resolve` checks existing calls in `self.plan.calls` via `same_call(contract, call, env)`. When an existing call matches (or a memoized fresh construction is hit by a subsequent goal), `self.reused` (`reused_intermediates`) increments and `_emit` returns the existing call's output binding at `cost = 0` without emitting a duplicate call.
   - In `_phap_tuyen` (`Normal(Q)` subgoal for constrained planes), existing `perpendicular_line_plane`, `altitude`, and `orthogonal_projection` premises/calls on any structurally equivalent plane (`set(f.points) <= tren_q`) are reused at `cost = 0` (`reused_intermediates += 1` when reusing a projection).
5. **Three-Level Planning Taxonomy (Section IV.2):**
   - **Level 1 — Source-Explicit Construction (`SOURCE_EXPLICIT_SEQUENCE`):** Every intermediate geometric object is explicitly named and declared as a premise in the problem statement (`Gọi M là trung điểm... Gọi H là hình chiếu...`).
   - **Level 2 — Nested Descriptor Composition (`DISCOVERED_FUNCTION_COMPOSITION` over nested `DescribedPointSpec`):** The problem statement describes a nested chain of unnamed objects inside a goal phrase (`"khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên (ABCD) đến..."`), and `_EffectResolver` recursively resolves the nested `Point` descriptors (`search_generated_steps != []`).
   - **Level 3 — Goal-Driven Plan Discovery (`REGISTERED_DECOMPOSITION` / multi-step goal & locus regression):** The problem statement gives only the base solid/premises and a target relation/goal (e.g., distance from a point to a line or intersection line without naming the perpendicular foot $H$, section by a plane perpendicular to a face where no normal line is given, or a point defined only by a geometric property such as `orthocenter` / `circumcenter` requiring multi-locus `PerpLine` / `PerpDir` candidate search, precondition pruning, and `intersect_line_line`). Following `AGENTS.md` and C16/C18 rules, Level 3 goal/definition regressions are honestly classified in telemetry as `REGISTERED_DECOMPOSITION` when driven by declared goal/definition rules and `DISCOVERED_FUNCTION_COMPOSITION` only when `search_generated_steps` is non-empty.

---

## 3. Phase A — Discriminating Diagnostic Suite & Unmodified Baseline Attribution (Sections V–VI)

We created `backend/tests/geometry/test_goal_driven_planner_generalization.py` (`18` test functions covering Phase 0.1, Families A–E, and Section IX Ablation Tests 1–5) and executed it on the **unmodified** Phase 0 candidate (`fb291cba3`) before writing any product code changes:

- **Unmodified Baseline Result:** **`8 passed, 10 failed`** (`18` total test functions).

| Test Function | Family / Role | Unmodified Baseline (`fb291cba3`) | Root-Cause Attribution (Section VI Taxonomy) | Post-Fix (`feat/hybrid-goal-driven-planner`) |
|---|---|---|---|---|
| `test_phase0_1_valid_in_plane_projection_not_falsely_refused` | Phase 0.1 ($P \in Q$ projection) | **FAILED** (`FACT_INCOMPLETE`) | `3. overly_restrictive_precondition` (`parse_descriptor_inputs` rejected `set(out[0][2]) <= set(ref_pts)`) | **PASSED** (`√2/3`, `2√14/3`) |
| `test_family_a1_goal_only_point_to_line_distance` | Family A.1 (Goal-only $d(A, SB)$) | PASSED (`6√13/13`) | Baseline already supported | **PASSED** (`6√13/13`) |
| `test_family_a2_goal_only_point_to_intersection_line_distance` | Family A.2 (Goal-only $d(A, (SAD)\cap(SBC))$) | PASSED (`3`) | Baseline already supported | **PASSED** (`3`) |
| `test_family_a3_goal_only_constrained_plane_section_area` | Family A.3 (Constrained plane $\perp (SBC)$ section) | PASSED (`7√2/8`) | Baseline already supported | **PASSED** (`7√2/8`) |
| `test_family_b1_competing_perpline_plans_orthocenter_telemetry` | Family B.1 (Competing `PerpLine` plans, cost 1 vs cost 2) | **FAILED** (missing telemetry keys) | `4. missing_search_link` (`search_telemetry` lacked `candidate_count`, `pruned_nodes`, `rejection_reasons`, `selected_plan`, `plan_cost`) | **PASSED** (`2`, `plan_cost=3`, `pruned_nodes=6`) |
| `test_family_b2_competing_perpline_plans_circumcenter_precondition_pruning` | Family B.2 (`off_line` pruning forces cost-3 locus plan) | **FAILED** (missing `pruned_nodes`) | `4. missing_search_link` (telemetry exposure of `pruned_nodes=9`, `plan_cost=7`) | **PASSED** (`√3`, `plan_cost=7`, `pruned_nodes=9`) |
| `test_family_b3a_competing_normal_plans_selects_cost0_premise_on_structurally_equivalent_plane` | Family B.3a (`Normal(ANB)` selects cost-0 premise `SA` over cost-1 projection) | **FAILED** (chose cost-1 `orthogonal_projection` instead of cost-0 `premise`) | `4. missing_search_link` + `6. source_gate_certificate_gap` (`_phap_tuyen`, `registry.py`, and `engine.py` checked `set(f.points) == set(q)` instead of structural coplanarity `set(f.points) <= tren_q`) | **PASSED** (`3/2`, `producer="premise"`, `cost=0`) |
| `test_family_b3b_competing_normal_plans_reuses_existing_projection_at_cost0` | Family B.3b (`Normal(SBC)` reuses existing projection $K = \operatorname{proj}_{(SBC)}(A)$ at cost 0) | **FAILED** (emitted duplicate `orthogonal_projection`) | `5. intermediate_reuse_gap` + `6. source_gate_certificate_gap` (`_phap_tuyen` did not check `f.kind == "projection"` premises; `registry.py` and `engine.py` did not validate `projection` facts as `premise` normal witnesses) | **PASSED** (`7√2/8`, `1` projection call, `cost=0`, `reused_intermediates=1`) |
| `test_family_b3c_normal_contract_precondition_and_structural_tren_mat` | Family B.3c (`Normal(Q)` contract `free=('Z',)` + `requires=(('off_plane','Z','Q'),)` + structural `_tren_mat`) | **FAILED** (`nc.free == ()`) | `2. incomplete_precondition` (`orthogonal_projection.planning_extra[0]` lacked `free=("Z",)` and `requires=(("off_plane", "Z", "Q"),)`, and `_tren_mat` checked only literal `plane` labels) | **PASSED** |
| `test_family_c_implicit_auxiliary_taxonomy_comparison` | Family C (Level 1 vs Level 2 vs Level 3 comparison) | PASSED | Baseline already supported | **PASSED** |
| `test_family_d_shared_intermediate_results_across_multiple_goals` | Family D (Shared intermediates across goals) | PASSED (`2/3`, `√5`) | Baseline already supported | **PASSED** (`2/3`, `√5`, `reused_intermediates=2`) |
| `test_family_e9_projection_coinciding_with_source_point_degenerate_segment_refused` | Family E.9 (Degenerate 0-length segment $[H, M]$ when $H = M \in Q$) | **FAILED** (`FACT_INCOMPLETE` instead of `DEGENERATE_POINTS`) | `3. overly_restrictive_precondition` + `7. engine_or_kernel_gap` (`_Dung._kc2_do_dai` in `engine.py` did not refuse `d2 == 0` with `DEGENERATE_POINTS`) | **PASSED** (`REFUSED`, `DEGENERATE_POINTS`) |
| `test_family_e1_to_e8_and_e10_to_e13_negative_adversarial_matrix` | Family E.1–E.8, E.10–E.13 (12 negative/adversarial failure modes) | PASSED (`12/12` fail-closed) | Baseline already supported | **PASSED** (`12/12` fail-closed) |
| `test_section_ix_test1_explicit_vs_goal_only` | Section IX Test 1 (Explicit vs Goal-Only) | PASSED (`6√13/13`) | Baseline already supported | **PASSED** (`6√13/13`) |
| `test_section_ix_test2_remove_specialized_decomposition` | Section IX Test 2 (Remove specialized decomposition) | PASSED (`6√13/13`) | Baseline already supported | **PASSED** (`6√13/13`) |
| `test_section_ix_test3_remove_required_producer_fallback_and_refusal` | Section IX Test 3 (Remove producer -> higher-cost fallback & refusal) | **FAILED** (`KeyError: 'plan_cost'`) | `4. missing_search_link` (telemetry key) | **PASSED** (`plan_cost: 3 -> 5 -> REFUSED`) |
| `test_section_ix_test4_competing_plans_evaluation_and_selection` | Section IX Test 4 (Competing plans evaluation & selection) | **FAILED** (`KeyError: 'candidate_count'`) | `4. missing_search_link` (telemetry key) | **PASSED** (`candidate_count=17`, `plan_cost=3`) |
| `test_section_ix_test5_metamorphic_renaming_and_scaling` | Section IX Test 5 (Metamorphic vertex renaming & $k=3$ scaling) | **FAILED** (`KeyError: 'plan_cost'`) | `4. missing_search_link` (telemetry key) | **PASSED** (`plan_cost=3`, exact $k$ and $k^2$ scaling) |

---

## 4. Phase B — Minimal Product Implementation (Sections VII–VIII)

Only the proven gaps identified in Section 3 were modified across `3` backend files (`frontend/**` untouched, `CACHE_VERSION = 132` unchanged):

1. **`backend/app/simulation/geometry_functions/registry.py`:**
   - Removed the overly restrictive `set(out[0][2]) <= set(ref_pts)` filter from `parse_descriptor_inputs` so mathematically valid projections of in-plane points ($P \in Q \implies \operatorname{proj}_Q(P) = P$) are not falsely refused at the descriptor parser.
   - Declared `free=("Z",)` and `requires=(("off_plane", "Z", "Q"),)` on `orthogonal_projection.planning_extra[0]` (`EffectTerm("Normal", ("Q", ("H", "Z")))`), placing the off-plane precondition on the `Normal(Q)` witness contract where a zero vector $\vec{n} = Z - H = \vec{0}$ would be invalid.
   - Extended `_mat_rang_buoc_dung_nguon` so `w["producer"] == "premise"` accepts an existing `orthogonal_projection` premise call (`pc["fn"] == "orthogonal_projection"`, `w["vector"] == [pc["args"]["image"], pc["args"]["point"]]`) and accepts `perpendicular_line_plane` premises on structurally coplanar base/face planes (`set(pc["args"]["plane"]) != set(c["points"])` left to the Exact Kernel's Gram-metric verification).
2. **`backend/app/simulation/geometry_functions/planner.py`:**
   - Extracted shared structural coplanarity closure helper `_diem_tren_mat(q, facts, solids)` (closing `set(q)` over solid bases/lateral faces and `midpoint`, `divide_segment`, `centroid`, `intersect_line_line`, `intersect_line_plane`, `projection`, and `altitude` premises without coordinates).
   - Wired `_EffectResolver._tren_mat` to `_diem_tren_mat` so `requires=(("off_plane", ...),)` prunes all structurally coplanar points (e.g., face vertices and edge midpoints).
   - Extended `_phap_tuyen` so cost-`0` `Normal(Q)` candidates include:
     - `perpendicular_line_plane` and `altitude` premises whose target plane is structurally equivalent to $Q$ (`set(f.points_b) <= tren_q` / `set(kh.day) <= tren_q`), and
     - existing `projection` premises (`f.kind == "projection"`, `len(f.points) >= 3`, `set(f.points) <= tren_q`, `f.point not in tren_q`) yielding vector `[f.at, f.point]` at `cost = 0` (`reused_projection=True`, incrementing `k.resolver.reused`).
   - Enriched `k.search_telemetry` with `candidate_count`, `pruned_nodes`, `rejection_reasons`, `selected_plan`, and `plan_cost` while preserving all existing telemetry keys (`explored_states`, `candidate_evaluations`, `search_depth`, `reused_intermediates`, `classification`, `source_defined_steps`, `registered_decomposition_steps`, `search_generated_steps`).
3. **`backend/app/simulation/geometry_functions/engine.py`:**
   - Updated `_Dung._kc2_do_dai` (`ask_length`) to fail closed with `TuChoi("DEGENERATE_POINTS", ...)` when `d2 == 0` (the two endpoints of a measured segment coincide in the exact Gram metric, e.g., Family E.9).
   - Updated `_Dung._kiem_mat_rang_buoc` so a cost-`0` `premise` normal witness on a constrained plane verifies `perpendicular_line_plane` via exact Gram orthogonality against every pair of points of `c["points"]` (`self.g(self.diem(u) - self.diem(v), n) == 0`) when `c["points"]` names the same plane via structurally coplanar points (e.g., `(ANB)` vs `(ABCD)`), and verifies reused `projection` premise witnesses (`[f["at"], f["point"]]`).

---

## 5. Mandatory Ablation & Counterfactual Testing (Section IX)

All 5 mandatory ablation and counterfactual experiments in `test_goal_driven_planner_generalization.py` pass:

1. **Test 1 — Explicit vs Goal-Only (`test_section_ix_test1_explicit_vs_goal_only`):**
   - Compares explicit premise construction (`Gọi H là hình chiếu vuông góc của A lên SB. Tính độ dài đoạn thẳng nối A với H`) against goal-only problem (`Tính khoảng cách từ A đến đường thẳng SB`).
   - Both produce the exact same mathematical result `"6√13/13"` and valid `Scene3D` with `0` continuity issues; the explicit version maps `H` from the premise (`plan_cost = 0`), while the goal-only version discovers and emits `orthogonal_projection_line` (`plan_cost = 1`).
2. **Test 2 — Remove Specialized Decomposition (`test_section_ix_test2_remove_specialized_decomposition`):**
   - Compares direct `ask_distance_point_plane` against monkeypatching `ask_distance_point_plane` out of `REGISTRY` on a goal with a described point (`@m1` = midpoint of $SA$, distance to $(SBC)$ is $\text{distance}(A, SB)$ via projection).
   - When `ask_distance_point_plane` is removed and a `Foot`-based `AnswerDistancePlane` contract is registered on `ask_length`, `_EffectResolver` automatically regresses `AnswerDistancePlane(P, Q) -> Foot(H, P, Q) -> orthogonal_projection(P, Q, H) + ask_length(P, H)` (`plan_cost: 1 -> 2`) and produces the exact same answer `"√2/2"`.
3. **Test 3 — Remove Required Producer (`test_section_ix_test3_remove_required_producer_fallback_and_refusal`):**
   - On `orthocenter(SBC)`:
     - **Baseline:** Direct `PerpLine` contract on `orthogonal_projection_line` selected (`plan_cost = 3`, answer `"2"`).
     - **Case 3A (Fallback to alternative valid plan):** Removing the direct `PerpLine` contract from `orthogonal_projection_line` forces `_EffectResolver` to fall back to the 2-step `PerpDir + translate_point` contract chain (`plan_cost = 5`, `"translate_point"` in `selected_functions`, exact same answer `"2"`).
     - **Case 3B (No valid producer remains):** Removing both `PerpLine` and `PerpDir` from `orthogonal_projection_line` fails closed with `status == "REFUSED"` and `reason_code == "UNSUPPORTED_CAPABILITY"`.
4. **Test 4 — Competing Plans (`test_section_ix_test4_competing_plans_evaluation_and_selection`):**
   - Verifies that when both `cost = 1` (`orthogonal_projection_line` direct `PerpLine`) and `cost = 2` (`PerpDir + translate_point`) candidate plans exist for each altitude locus of `orthocenter(SBC)`, the planner evaluates `candidate_count = 17` candidates, prunes `6` invalid bindings (`off_line`), and deterministically selects the `plan_cost = 3` plan (`answers == {"q1": "0"}`).
5. **Test 5 — Metamorphic Geometry Testing (`test_section_ix_test5_metamorphic_renaming_and_scaling`):**
   - **Vertex Renaming ($S.ABCD \to P.MNPQ$, side $2$, height $3$):** Preserves identical `selected_functions`, `plan_cost = 3`, `search_depth = 3`, and exact answers (`q1 = "4/3"`, `q2 = "2/3"`).
   - **Linear Scaling ($k = 3$: side $2 \to 6$, height $3 \to 9$):** Preserves `plan_cost = 3`, scales 1D distances by $k = 3$ (`"4/3" -> "4"`, `"2/3" -> "2"`), and scales 2D triangle area by $k^2 = 9$ (`"√5" -> "9√5"`).

---

## 6. Performance & Search Complexity (Section XI)

Measured by `docs/evaluation/geometry/runs/hybrid-goal-driven-planner/tools/measure_goal_driven_planning.py` across the 10-case benchmark (`Phase0.1`, `A1`, `A2`, `A3`, `B1`, `B2`, `B3a`, `B3b`, `D`, `E9`), comparing the unmodified Phase 0 baseline (`feat/hybrid-production-composition`) against `feat/hybrid-goal-driven-planner` (receipt: `results/goal_driven_planning_metrics.json`):

| Metric | Unmodified Baseline (`fb291cba3`) | Goal-Driven Candidate (`feat/hybrid-goal-driven-planner`) | Notes |
|---|---:|---:|---|
| Planner CPU time `p50` / `p95` / `max` (ms) | `1.733` / `3.302` / `3.302` | `1.185` / `4.383` / `4.383` | Sub-5ms across all families; `Phase0.1` now plans & serves instead of refusing early |
| Exact Kernel CPU time `p50` / `p95` / `max` (ms) | `37.331` / `196.094` / `196.094` | `30.732` / `209.210` / `209.210` | `B3a` plan length reduced `10 -> 9`, `B3b` plan length reduced `11 -> 10` via cost-0 normal reuse |
| Warm offline route time `p50` / `p95` / `max` (ms) | `30.733` / `64.344` / `64.344` | `33.848` / `61.395` / `61.395` | `B3a` warm route `57.093 -> 55.602 ms`, `B3b` warm route `64.344 -> 61.395 ms` |
| Cold offline route time `p50` / `p95` / `max` (ms) | `154.898` / `303.231` / `303.231` | `185.786` / `370.572` / `370.572` | Includes `Scene3D` build + `validate_construction_continuity` on newly served `Phase0.1` |
| Max traced memory peak (KiB) | `820.59` | `774.56` | Bounded (`< 0.8 MiB`) |
| Max `explored_states` / `candidate_count` / `pruned_nodes` / `search_depth` | `24` / `20` / `9` / `4` | `24` / `20` / `9` / `4` | Strictly within `MAX_EFFECT_NEEDS=96`, `MAX_EFFECT_CANDIDATES=48`, `MAX_EFFECT_DEPTH=4` |

---

## 7. Full Regression, Candidate Freeze & Verification Gates (Section XII)

- **Targeted 7-suite planner & composition verification:** `217 passed in 7.26s` (`0` failed).
- **Full backend pytest (`pytest tests -q`):** `14,007 passed, 1 skipped, 3 deselected` (`14,011` collected total = `13,993` baseline + `18` new tests in `test_goal_driven_planner_generalization.py`; `0` failed).
- **Measured system freeze (`freeze_evaluation_candidate.py --verify`):** `so_file = 106` hashed entries (`105` unique files), `tree_hash = 2dcfff5328656264cb1df117874b8714cb2be7e5fe05e60ab233e2dc83fa1fca`, `CACHE_VERSION = 132` (unchanged: no provider schema/prompt change, and only previously refused in-plane nested projection cases or redundant auxiliary normal steps changed).
- **Documentation architecture audit (`audit_docs_information_architecture.py`):** **PASS**.
- **Publication safety gate (`check_publication_safety.py --range main..HEAD`):** **PASS** (`violations=0`).
