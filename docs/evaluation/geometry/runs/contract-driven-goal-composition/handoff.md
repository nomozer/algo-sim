# Integration Handoff — `research/contract-driven-goal-composition` $\times$ `research/semantic-extraction-v3`

- **Branch**: `research/contract-driven-goal-composition`
- **Worktree**: `.superpowers/worktrees/contract-driven-goal-composition`
- **Base Commit (`main` = `origin/main`)**: `4abc4afbb976babc4740bf22e42dc368a24c1b13`
- **Product Implementation Commit**: `1529faa7250c3a8691996284714272d52a947e49`
- **Branch State**: `FROZEN_PENDING_INTEGRATION` (`INTEGRATION_DEFERRED_PENDING_SEMANTIC_V3`)

---

## 1. File Overlap & Merge Surface

| File | Modified by `contract-driven-goal-composition` | Modified by `semantic-extraction-v3` | Overlap / Conflict Assessment |
|---|---|---|---|
| `backend/app/simulation/geometry_functions/planner.py` | Yes (`PLANNER_VERSION = "geometry-fact-planner/7"`, `_doc_toan_hang_mo_ta`, `_cau_hoi`, `_EffectResolver`) | **No** | Zero overlap. |
| `backend/app/simulation/geometry_functions/engine.py` | Yes (`ENGINE_VERSION = "geometry-function-engine/5"`, `_KIEM_DICH`, `kc2_dich`, `_dt2_tam_giac`, `_goc_duong_mat_cos2`) | **No** | Zero overlap. |
| `backend/app/simulation/geometry_functions/registry.py` | Yes (`REGISTRY_VERSION = "geometry-functions/6"`, lines `258`, `403`, `959–1012`, `2050–2059`) | Yes (lines `60–64`, `338–383`, `598–616`, `1352`, `1666–1792`) | **Shared file, disjoint Git hunks**: `semantic-extraction-v3` edits premise source coverage (`_khoi_dung`, `_MAO_TU_KHOI`, `NUMBER_PATTERN`); this branch edits `PlanningTerm`, `ask_area` `PlanningContract`, and `_kiem_result_binding` (`effect-chain`). |
| `backend/app/ai/fact_extraction.py` | **No** (untouched) | Yes (`RESPONSE_CONTRACT`, `_contract_v3()`, `schema_accepts`) | Zero Git overlap; see §2 for Schema-Contract v3 compatibility hypothesis. |

---

## 2. Schema & Grounding Compatibility

1. **Default Product Contract (`RESPONSE_CONTRACT = "flat"`)**:
   - Fully compatible out of the box. `TypedFact.model_json_schema()` (`aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`) and `function_declarations()` (`5ceb0f999d4d7c1e...`) are unchanged by this branch.
2. **Right-Prism Grounding (`_khoi_dung` in `semantic-extraction-v3`)**:
   - All 6 prism/cuboid/cube cases in `contract-driven-goal-composition/corpus.json` place the rightness cue (`lập phương`, `hộp chữ nhật`, `lăng trụ đứng`) immediately before the 2-face solid label (`ABCD.A'B'C'D'`, `ABC.A'B'C'`), matching `_khoi_dung(c)`.
3. **Compatibility Hypothesis for Research Schema-Contract v3 (`RESPONSE_CONTRACT = "v3"`)**:
   - *Note: `fact_extraction.py` and the `semantic-extraction-v3` worktree were not modified by this branch. The following is an unverified compatibility hypothesis to be tested on the combined integration candidate.*
   - In `semantic-extraction-v3`, `_contract_v3()` (`backend/app/ai/fact_extraction.py`) enumerates unnamed `point_kind` question variants over `for quantity in ("length", "distance")` (reflecting `main` at `4abc4afb`).
   - On the combined candidate, if `RESPONSE_CONTRACT == "v3"` is expected to accept unnamed `point_kind` area questions (`quantity == "area"`, `len(points_b) == 2`), test extending that comprehension in `_contract_v3()` to:
     ```python
     *[v("question", ("quantity", "point_kind", "points", "points_b"), quantity=one(quantity),
         point_kind=one(kind), points=labels(n, n),
         points_b=labels(1, 1) if quantity == "length" else labels(2, 2) if quantity == "area" else labels(2))
       for kind, n in (("midpoint", 2), ("centroid", 3)) for quantity in ("length", "distance", "area")],
     ```

---

## 3. Unresolved Architectural & Schema Limits

1. **`SCHEMA_REPRESENTATION_BLOCKER` on Unnamed `point_kind` + `quantity="angle"` (Slice B Unnamed, `unnamed-angle-line-plane-blocker`)**:
   - Under frozen `TypedFact`, when `point_kind` is set on `kind="question"`, `points` holds the descriptor's parent vertices and only a single flat `points_b: list[Label]` remains. Expressing a line–plane angle from an unnamed derived point requires both a named second line endpoint (`1` label) and the target plane's vertices ($\ge 3$ labels), which cannot be separated inside `points_b` without positional guessing.
   - Kept fail-closed (`REFUSED / UNSUPPORTED_CAPABILITY`).
2. **Slice B Named Scope**:
   - The 5 `angle_line_plane_slice_b` cases prove the independent Gram verifier `_goc_duong_mat_cos2` on **named** derived points (`midpoint`, `centroid`, `orthogonal_projection_line`), not unnamed goal composition.
3. **`centroid` Producer Contract**:
   - Remains an experimental ablation contract (`experimental_centroid_contract` in `measure_function_discovery.py` / `NEW[centroid]`), not enabled by default in production `REGISTRY` (`new/negative::centroid-without-contract` continues to refuse with `UNSUPPORTED_CAPABILITY` in production).
4. **Corpus Provenance**:
   - The 40-case `corpus.json` (`10` positive, `4` discovery, `4` held-out, `5` Slice B angle, `17` negative) is agent-authored and verified by the independent Fraction/Gram oracle (`oracle.py`), not human-expert-validated (`AGENT_AUTHORED_WITH_INDEPENDENT_ORACLE_NOT_HUMAN_VALIDATED`).

---

## 4. Verification Checklist on the Combined Integration Candidate

When `semantic-extraction-v3` completes and user gives **GO INTEGRATION**:
1. Create a clean integration worktree from latest `main` after merging `semantic-extraction-v3` and `contract-driven-goal-composition`.
2. Run focused Route D + Extraction suites:
   ```powershell
   pytest backend/tests/geometry/test_contract_driven_goal_composition.py `
          backend/tests/geometry/test_generalized_goal_entry.py `
          backend/tests/geometry/test_function_discovery_planning.py `
          backend/tests/geometry/test_result_binding_planning.py `
          backend/tests/geometry/test_source_grounding_reliability.py `
          backend/tests/geometry/test_source_grounding_review.py `
          backend/tests/geometry/test_schema_contract_v3.py `
          backend/tests/geometry/test_semantic_extraction_evaluation.py -v
   ```
3. Re-run `measure_goal_composition.py` (`run-all` into a fresh verification folder + `reconcile`) and confirm:
   - `prior_174_diffs_vs_baseline == 0`
   - `all_214_diffs_prod_vs_reversed == 0`
   - `true_safety_negatives_refused == 118` / `118` and `safety_wrong_served == 0` across all 7 arms.
4. Update shared indices (`docs/CODE_INDEX.md`, `docs/EVIDENCE_INDEX.md`), refreeze `EVALUATION_CANDIDATE.json`, run an independent review of the combined integration diff, and execute **Final Authoritative T3** on a clean detached worktree.
