# Contract-Driven Goal Composition — Independent Quality Gate & Integration Readiness Report

- **Run ID**: `contract-driven-goal-composition`
- **Branch**: `research/contract-driven-goal-composition`
- **Worktree**: `.superpowers/worktrees/contract-driven-goal-composition`
- **Base Commit (`main` = `origin/main`)**: `4abc4afbb976babc4740bf22e42dc368a24c1b13`
- **Product Implementation Commit**: `1529faa7250c3a8691996284714272d52a947e49`
- **Independent Reviewer Subagent**: `024a6ace-3a20-4761-b1da-f6a24fc29de0` (read-only audit on `1529faa7`)
- **Quality Gate Verdict**: `INDEPENDENT_REVIEW_PASS` (`0 BLOCKER`, `2 IMPORTANT` resolved, `2 MINOR` resolved/documented)
- **Integration Verdict**: `READY_FOR_INTEGRATION` (`INTEGRATION_DEFERRED_PENDING_SEMANTIC_V3`)
- **Live Model Calls**: `0` (`ALLOW_LIVE_AI=0`)

---

## 1. P0 — Reconciliation of `new/negative::centroid-without-contract` (`wrong_served` in `ablation.json`)

### 1.1 Source Problem & Typed Facts
In `docs/evaluation/geometry/runs/goal-directed-function-discovery/corpus.json`, the problem:
> *"Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. Tính khoảng cách từ trọng tâm của tam giác SBC đến (SAD)."*

is registered in two splits with **byte-identical** `text` and `payload.facts`:
1. `new/negative::centroid-without-contract` with `expect = {"expected_codes": ["UNSUPPORTED_CAPABILITY"]}`: designed to verify that when `centroid` has **no** `PlanningContract` in the production catalog, the planner refuses fail-closed (`UNSUPPORTED_CAPABILITY`).
2. `new/discovery::centroid-to-plane` with `expect = {"expected_squared": {"q": "16/9"}}`: designed to verify that when the experimental `centroid` `PlanningContract` is injected (`NEW[centroid]`), the planner discovers `centroid -> ask_distance_point_plane` and serves the exact distance.

### 1.2 Independent Mathematical Verification
In the orthonormal chart $A=(0,0,0),\; B=(2,0,0),\; C=(2,2,0),\; D=(0,2,0),\; S=(0,0,3)$:
- The centroid of $\triangle SBC$ is:
  $$G = \frac{S + B + C}{3} = \left(\frac{4}{3}, \frac{2}{3}, 1\right).$$
- Plane $(SAD)$ is $x = 0$.
- The exact distance from $G$ to $(SAD)$ is:
  $$d(G, (SAD)) = \frac{4}{3}, \qquad d^2 = \frac{16}{9}.$$
Under `NEW[centroid]`, the route serves `answers = {"q": "4/3"}` and `squares = {"q": "16/9"}`, which is 100% mathematically exact and matches `new/discovery::centroid-to-plane`.

### 1.3 Taxonomy Separation (`ablation-reconciled.json`)
- **Safety Negatives (`213` safety-checked rows across all corpora)**: Invalid, contradictory, underdetermined, ungrounded, or schema-blocked inputs that must **always** be refused in every configuration. Across all 7 arms (`NEW[production]`, `NEW[centroid]`, `NEW[reversed]`, `NEW[no-area]`, `NEW[no-midpoint]`, `NEW[lying]`, `NEW[lying-area-verifier]`), **`safety_wrong_served = 0`**.
- **Capability-Disabled Negatives (`1` row: `new/negative::centroid-without-contract`)**: A valid, source-grounded problem whose expected refusal (`UNSUPPORTED_CAPABILITY`) holds only when the `centroid` contract is disabled.
  - Raw `ablation.json` is preserved untouched.
  - `backend/scripts/measure_goal_composition.py reconcile` writes `ablation-reconciled.json`, recording both `raw_outcome` and `reconciled_outcome` (`correct_refusal_disabled_capability` in production/disabled arms; `correct_served_enabled_capability` verified against oracle `16/9` in `NEW[centroid]`; `correct_refusal_lying_contract_caught` in `NEW[lying]`).

---

## 2. P1 — Independent Mathematical & Architecture Review Summary

An independent, read-only `research` subagent (`024a6ace-3a20-4761-b1da-f6a24fc29de0`) audited commit `1529faa7` across `registry.py`, `planner.py`, `engine.py`, `oracle.py`, `corpus.json`, `ablation.json`, `regression-174.json`, `test_contract_driven_goal_composition.py`, and `report.md`:

- **A. Planner Composition (`planner.py`)**: Confirmed genuine contract-driven composition via `PlanningContract`, zero planner/engine edits when adding `centroid`, zero dependence on hardcoded labels (`M`/`G`/`H`) or `REGISTRY` order (`0/214` diffs between `production` and `reversed`), proper `AUXILIARY` / `DERIVED` provenance, and canonical `same_call` verification before reusing any existing premise point at cost `0`.
- **B. Registry & Source Grounding (`registry.py`)**: Confirmed `ask_area` `PlanningContract` matches `AskAreaArgs`, arity-2 unordered target pair verification, refusal of unknown/unbuilt labels, swapped operands, ungrounded quotes, and unanswered second asks (`REQUEST_NOT_ANSWERED`), and fail-closed refusal of all forged `effect-chain` certificates.
- **C. Engine & Exact Verifiers (`engine.py`)**: Confirmed `_KIEM_DICH`, `kc2_dich`, `_dt2_tam_giac`, and `_goc_duong_mat_cos2` compute exact Gram determinants independently of the kernel's `area_polygon` and `cos_sq_line_plane`, properly refuse collinear triangles (`COLLINEAR_POINTS`) and degenerate lines (`DEGENERATE_LINE`), and verify $0^\circ$, $90^\circ$, oblique angles, symbolic scaling `a`, and vertex permutations.
- **D. Independent Oracle (`oracle.py`)**: Confirmed `0` imports from `app`/`tests` and independently verified from first principles all `10` positive, `4` discovery, `4` held-out, and `5` Slice B angle cases in `corpus.json`.
- **E. Reviewer Findings & Resolution**:
  - **`BLOCKER`**: `0`.
  - **`IMPORTANT-1`** (`wrong_served: 1` on `new/negative::centroid-without-contract` in `ablation.json` under `NEW[centroid]` not explained in `report.md`): **Resolved** via `measure_goal_composition.py reconcile`, `ablation-reconciled.json`, `test_capability_disabled_negative_reconciliation`, and updated `report.md` §4.
  - **`IMPORTANT-2`** (stale identifiers/refusal codes/case IDs in `report.md` prose, e.g. `UNSUPPORTED_QUESTION_FORM` vs actual `UNSUPPORTED_CAPABILITY`, case ID names): **Resolved** in `report.md` and `run.json`.
  - **`MINOR-1`** (`chain(d)` upward input closure + final step descriptor check in `registry.py` inherited from prior wave): Documented; non-exploitable because `engine.py` verifies all calls and strips unused fresh points from `targets`.
  - **`MINOR-2`** (`cos2s` populated for rational lengths in `measure_goal_composition.py`): **Resolved** in `measure_goal_composition.py` (`str(ans_str).startswith("cos²=")`).

---

## 3. P2 — Generality & Schema Boundary Audit

| Category | Capability | Status | Evidence |
|---|---|---|---|
| **1. Default Production Registry (`REGISTRY_VERSION = geometry-functions/7`)** | Unnamed `midpoint -> ask_area` (4 solid families, reversed wording, symbolic `a`, multi-goal, named reuse); Named `orthogonal_projection` / `orthogonal_projection_line -> ask_area`; Named `midpoint` / `centroid` / `orthogonal_projection_line -> ask_angle_line_plane` verified by `_goc_duong_mat_cos2` | **Active in Production (`10/10` positive, `4/4` held-out, `5/5` Slice B)** | `ablation.json` (`NEW[production]`), `green-quality-gate.txt` |
| **2. Experimental Contract Injection (`NEW[centroid]`)** | Unnamed `centroid -> ask_area` and Named `orthogonal_projection_line` + Unnamed `centroid -> ask_area` (`pyramid-projection-and-unnamed-centroid-area`) | **Active when `centroid` `PlanningContract` is injected (`0/4 -> 4/4`, 0 planner/engine edits)** | `ablation.json` (`NEW[centroid]`), `test_slice_a_zero_planner_edit_discovery_centroid_to_area` |
| **3. Blocked by Frozen `TypedFact` Schema (`SCHEMA_REPRESENTATION_BLOCKER`)** | Unnamed `point_kind` (`midpoint` / `centroid`) + `quantity="angle"` (line–plane angle where one line endpoint is an unnamed derived point) | **Fail-closed (`REFUSED / UNSUPPORTED_CAPABILITY`)** | `corpus.json` (`unnamed-angle-line-plane-schema-blocker`), `test_slice_b_unnamed_point_kind_schema_representation_blocker` |

---

## 4. P5 — Compatibility with `research/semantic-extraction-v3` & `research/scene3d-plane-grid-camera`

1. **`research/scene3d-plane-grid-camera`**: Frontend-only worktree (`4abc4afb`); zero overlap with backend `geometry_functions`.
2. **`research/semantic-extraction-v3` (`d785277d`)**:
   - **Git diff**: Disjoint line ranges in `registry.py` (`semantic-extraction-v3`: lines `60–64`, `338–383`, `598–616`, `1352`, `1666–1792`; `contract-driven-goal-composition`: lines `258`, `403`, `959–1012`, `2050–2059`). Zero changes to `planner.py` or `engine.py` in `semantic-extraction-v3`.
   - **Source Grounding (`_khoi_dung`)**: All prism/cuboid/cube cases in `contract-driven-goal-composition/corpus.json` place the rightness cue immediately before the 2-face solid label and pass `_khoi_dung(c)`.
   - **Contract Compatibility Proposal for Schema-Contract v3 (`fact_extraction.py`)**:
     - Under default `RESPONSE_CONTRACT = "flat"`, both branches are 100% compatible without any change.
     - Under research `RESPONSE_CONTRACT = "v3"`, `_contract_v3()` in `semantic-extraction-v3` enumerates unnamed `point_kind` questions over `for quantity in ("length", "distance")`. At integration time, extending that comprehension in `_contract_v3()` to `for quantity in ("length", "distance", "area")` with `points_b=labels(1, 1) if quantity == "length" else labels(2, 2) if quantity == "area" else labels(2)` enables Schema-Contract v3 to accept unnamed `point_kind` area questions as well.
   - **Status**: `INTEGRATION_DEFERRED_PENDING_SEMANTIC_V3`.
