# Hybrid Reasoning & Generalization — Workstream B report

- **Run:** `hybrid-reasoning-generalization` · **date** 2026-11-09 · **branch** `feat/hybrid-reasoning-generalization`
- **Base:** `d79565b52ec19a7b1a75be28c09bb43cc0f6d146` (COMMON_BASE_SHA)
- **MEASUREMENT_CLASS** `OFFLINE_DEVELOPMENT_MATRIX` · **HELD_OUT_CLAIM** `NONE` · **EVALUATOR_INDEPENDENCE** `NONE`
  (same agent authored the cases and read the planner) · **live provider calls** 0 (`ALLOW_LIVE_AI=0`)
- **INDEPENDENT_H1_VALIDATION** `NOT_MEASURED`
- **Verdict:** `HYBRID_REASONING_IMPROVEMENT_VERIFIED` — on a development corpus only (see §10 limits)

Versions read from code (unchanged by this run): Planner `geometry-fact-planner/26`, Registry `geometry-functions/33`,
Engine `geometry-function-engine/24`, bridge `typed-fact-next-bridge/2`, schema `typed-fact-next/2`, Adapter /4,
`CACHE_VERSION = "132"`, `ROUTE_D_CACHE_POLICY = "132:route-d"`.

## 1. Method

`tools/reasoning_matrix.py` builds 72 hand-authored gold TypedFactNext /2 extractions (pyramid, prism, trirectangular
tetrahedron, ⊥, ∥, point–line, point–plane, angles, sections, property-defined points, nested descriptions, multi-goal,
intermediate reuse, negatives, clarification) and drives each through `run_hybrid_offline` (verbatim quotes → bridge_v2 →
Source Gate → planner → engine → Adapter /4 → Scene3D, `validate_construction_continuity`). Expected values come from
`docs/evaluation/geometry/custodian/geometry_oracle.py` (imports only `fractions`) on rational coordinates written in the
tool, or from a hand derivation in the case's `oracle` note (RE9 only). Lengths/areas/volumes
are compared as exact squares, angles as cos². Classes: `EXACT_SERVED`, `CORRECT_REFUSAL`, `CORRECT_CLARIFICATION`,
`FALSE_REFUSAL`, `NO_PLAN_DESPITE_PRIMITIVES` (refused although every needed Registry function exists), `WRONG_SERVED`,
`SEARCH_BUDGET_EXCEEDED`, `ADAPTER_OR_SCENE3D_ERROR`, `WRONG_REFUSAL_CLASS` (fail-closed, wrong taxonomy group).
Receipts: `results/matrix_before.json` (base), `results/matrix_after.json`, A/B timing receipts, `results/matrix_tables.md`
(rendered from JSON). Out-of-scope classes are listed in the receipt (`out_of_scope_not_run`), not run.

## 2. Baseline capabilities (base `d79565b52`)

| outcome | before | after |
|---|---:|---:|
| `EXACT_SERVED` | 47 | 56 |
| `CORRECT_REFUSAL` | 7 | 9 |
| `CORRECT_CLARIFICATION` | 1 | 1 |
| `FALSE_REFUSAL` | 6 | 0 |
| `NO_PLAN_DESPITE_PRIMITIVES` | 8 | 5 |
| `SEARCH_BUDGET_EXCEEDED` | 1 | 1 |
| `WRONG_REFUSAL_CLASS` | 2 | 0 |
| `WRONG_SERVED` | 0 | 0 |
| `ADAPTER_OR_SCENE3D_ERROR` | 0 | 0 |

The base already served exactly: named and described point–plane / point–line distances, nested descriptions
(depth 2), goal-only feet, prism distances/angles/skew lines, line–plane / plane–plane / line–line angles incl. described
points, parallel line–plane distance, sections (∥ base, ⊥ line through a vertex, constrained ⊥ plane), orthocenter /
circumcenter (right and equilateral faces, to a point / plane / line), described line–plane intersections, multi-goal
reuse of a described point and of a source-named foot. No wrong answer was served anywhere (0 `WRONG_SERVED`, 0 Scene3D
continuity issues). All 47 cases served before are byte-identical after (answers + classification + explored states +
candidates + pruned + depth + reuse + plan cost + selected plan).

## 3. Real gaps found (B.4 taxonomy)

| gap | cases | B.4 class | root cause | status |
|---|---|---|---|---|
| **G1a** | PE2 PE3 PE4 PE5 PE6 RE3 (+N8 class) | FactGraph missing a derivable relation | `engine._Dung._tam_giac` derived a triangle-base side by Pythagoras only from a `right_angle` whose three points ARE the base; "OA, OB, OC đôi một vuông góc" is extracted as three `perpendicular_lines` (extraction §2), and for "tứ diện OABC" the base is ABC (notation O.ABC, extraction §1): AB² = OA² + OB² was never derived ⇒ `MISSING_DIMENSION` | **fixed** |
| **G1b** | PE2 PE3 PE4 PE6 RE3 PY1 PY2 (+N10 class) | kernel unable to lay out a determined figure | no layout rule placed a pyramid apex from three lateral edge lengths (only: regular centre, ⊥ base, ⊥ two base lines, face ⊥ base) ⇒ `UNDERDETERMINED_POINT` | **fixed** |
| **G5** | MG7 | Source Gate rejecting a validly-evidenced inference / intermediate reuse | the planner correctly reuses the goal-only foot `H` of `d(A, SC)` for a second goal on "hình chiếu vuông góc của A lên SC"; the chain verifier (`registry._kiem_result_binding`) collected a fresh call's goal quotes only from `effect-chain` certificates, not from the `distance(point,line)` certificate that built the foot — `_kiem_phu` already uses the union over every certificate naming the construct ⇒ `AUXILIARY_RULE_MISMATCH` in both goal orders | **fixed** |
| G6 | MG9 | depth/candidate budget failure | three property-defined points in one problem: the effect-search candidate budget (48) is per problem (≈18 per definition) ⇒ `PLAN_TOO_LARGE`. A per-goal budget was implemented and **reverted**: the plan then needs 34 IR memory declarations > `semantic_program.validator.MAX_MEMORY_DECLARATIONS = 32` (`IR_MEMORY_BUDGET_EXCEEDED`), a contract bound — no learner benefit | not fixed (strict xfail) |
| G2 | PL5 PA3 | primitives exist, no plan | described point inside a `line` operand of a distance goal: bridge `_cau_hoi_mo_ta` has no goal contract (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT`) | bridge contract — proposal §8 |
| G3 | MG5 | primitives exist, no plan | two described points in one goal: bridge has no source certificate | bridge contract — proposal §8 |
| G4 | SE3 | Source Gate rejecting a validly-evidenced inference | "Mặt phẳng (Q) đi qua M, N, P … cắt bởi mặt phẳng (Q)": bridge `_la_mat_qua_ba_diem` renames a contains-3-points plane "(MNP)" even when the source names it "(Q)"; the gate then rejects "(Q)" (`SOURCE_OBJECT_MISMATCH`). "(MNP)" wording is served | bridge — proposal §8 |
| G7 | RE10 | primitives exist, no plan | a description nested through a property-defined point (projection of an orthocenter): bridge has no source certificate | bridge contract — proposal §8 |

Not gaps (checked): wrong precondition — none found (PL6 point on its line serves `0`; PR8 orthocenter coinciding
with a vertex serves exactly); bad ranking among valid plans — none observed (all served plans exact, plan costs
unchanged); adapter not showing the construction chain — 0 continuity issues on every served case.

### Cases, oracle, negatives (per fixed gap)

- **G1** input "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc, OA = 1, OB = 2, OC = 3." Oracle frame T: O(0,0,0),
  A(1,0,0), B(0,2,0), C(0,0,3). Expected / actual after: d(O,(ABC))² = 36/49 → `6/7`; cos²((ABC),(OBC)) = 36/49 → `36/49`;
  d(O,BC)² = 36/13 → `6√13/13`; V² = 1 (oracle interior-point decomposition) → `1`; orthocenter(ABC)–O = foot of O →
  `6/7`; apex-A reading A.OBC → `6/7`. PY1/PY2: S.ABC right at A (3, 4), SA = SB = SC = 13/2, frame Y with S(3/2, 2, 6)
  asserted by the oracle: d(A,(SBC))² = 144/25 → `12/5`, d(S,(ABC)) = 6 → `6`. Negatives: N8 stated AB = 3 contradicts
  OA ⊥ OB (AB² must be 5) → `INCONSISTENT_FACTS`; N9 OC missing → `MISSING_DIMENSION`; N10 SA = SB = SC = 2 shorter than
  the circumradius 5/2 → `INCONSISTENT_FACTS`; fault injections: two ⊥ pairs only → `MISSING_DIMENSION`; OA ⊥ BC (no
  shared endpoint) never read as a right angle → `MISSING_DIMENSION`. Ablation: with the trilateration rule disabled,
  PE5 (A.OBC) still serves `6/7` (G1a alone), PE2/PY1/N10 fall back to `UNDERDETERMINED_POINT` (G1b needed).
- **G5** input: square pyramid side 2, SA = 2, "Tính khoảng cách từ A đến đường thẳng SC. Tính độ dài đoạn thẳng nối hình
  chiếu vuông góc của A lên SC với S." Oracle: d² = 8/3 → `2√6/3`; foot (2/3,2/3,4/3), |HS|² = 4/3 → `2√3/3`; one
  `orthogonal_projection_line` call shared by both goals. Fault injections: removing the decomposition certificate →
  `AUXILIARY_RULE_MISMATCH`; forging its quote → refused.

Tests: `backend/tests/geometry/test_hybrid_reasoning_generalization.py` — run against the exported base `backend/app`:
10 RED (G1 ×6, G1b ×2, negatives N8/N10, G5 served) + the 6 strict-xfail reproductions failing as expected; all
controls (fault injections, unchanged-layout control, typed-refusal companions) pass on both. After: 23 passed,
6 strict xfail (G6, G2 ×2, G3, G4, G7).

**Historical receipts moved** (declared delta layers, receipts byte-identical, written by
`tools/remeasure_historical_deltas.py`, 0 model calls): `independent-nlu-extraction-evaluation` gold row **D08**
("Tứ diện OABC … OA = 2, OB = 3, OC = 6 … Tính độ dài OH") `REFUSED MISSING_DIMENSION` → `SERVED 18/7`, equal to that
corpus's preregistered independent value (`value_squared 18/7`, `agent1_oracle.py`) — `results/historical-gold-delta.json`;
`semantic-extraction-v3-runtime-revision` offline cells: **dev02** (PILOT, gold+replay, flat+v3) and **h16** (**LOCKED**,
gold+replay, flat arm only) `FALSE_REFUSAL_CAPABILITY_GAP (MISSING_DIMENSION)` → `CORRECT_COMPLETE` (both trirectangular
tetrahedra, both requests matched by that harness's gold) — `results/historical-regression-delta.json`. h16 sits in a
LOCKED split: it was not seen while authoring the matrix or the fix (found by the full suite afterwards), and it is
declared here rather than absorbed; no claim on the LOCKED set is made from it. Consumers updated:
`test_nlu_extraction_evaluation.py` (layer list) and `test_hybrid_backend_integration.py::_after_delta` (layered).

## 4. Product changes (planner / registry / engine)

- `planner.py`: **no change** (the G6 attempt was reverted, §3).
- `engine.py`: `_tam_giac` (+ right angles as `perpendicular_lines` sharing an endpoint; a right angle at a vertex
  outside the base gives the base side XY² = VX² + VY², or `INCONSISTENT_FACTS` if a stated XY disagrees) and
  `_dinh_tu_ba_canh_ben` (last rule of `_mot_buoc`: apex of the root pyramid by exact trilateration in the Gram chart;
  every other lateral length remains a fact the built figure is checked against).
- `registry.py`: one loop in `_kiem_result_binding` adds `distance(point,line)` certificate quotes to `chain_quotes`.
- No new Registry function, contract, descriptor, version string, label/case/answer literal, LLM planning, or budget
  change. Both engine rules can only fire where the base previously refused (a None base side ⇒ `MISSING_DIMENSION`; an
  unplaced apex ⇒ `UNDERDETERMINED_POINT`), which is why every previously served case is unchanged.

## 5. Planning levels, competing plans, ablation

Telemetry is not relabelled. After the fix the tetrahedron cases are `SOURCE_EXPLICIT_SEQUENCE` (layout only) or
`REGISTERED_DECOMPOSITION` (PE4 foot, RE3 definition); MG7 `REGISTERED_DECOMPOSITION`. **No new GOAL_DRIVEN_DISCOVERY
claim is made**: every property-defined point case reports `REGISTERED_DECOMPOSITION` with `search_generated_steps = 0`;
`DISCOVERED_FUNCTION_COMPOSITION` appears only where it did on the base (PP5, MG4 nested descriptions). Competing plans
were exercised by the existing definition search (RE1/RE5–RE8: 17–21 candidates, up to 15 structurally pruned, depth 4)
and are unchanged. Ablations of this run are layout/verifier ablations (§3), not planner ones.

## 6. Search complexity (same corpus)

| metric | before | after |
|---|---:|---:|
| explored states max | 48 | 48 |
| candidate evaluations max | 39 | 39 |
| pruned nodes max | 15 | 15 |
| search depth max | 4 | 4 |
| reused intermediates (sum) | 14 | 15 (MG7 reuse) |
| search exhausted cases | 1 (MG9) | 1 (MG9) |

Budgets unchanged: depth 4, needs 96, candidates 48, fresh points 16, calls 64.

## 7. Exact verification

Every served answer equals the oracle (56/56 after); `kiem` re-checks every stated fact (incl. the three ⊥ pairs, all
lateral lengths) in the exact Gram metric; 0 Scene3D continuity issues.

## 8. Shared-contract proposals (NOT implemented)

1. **G2** — allow a described ref in a distance goal's `line` operand: bridge `_cau_hoi_mo_ta` maps
   `{"point": X, "line": [Y, "@d"]}` to an `AnswerDistance` need whose `Line` is spanned by the built point (a `line`
   slot contract already exists for angles). Impact on Workstream A: none on OCR; extraction prompt unchanged (it already
   allows `line=A,@m1` for angles).
2. **G3/G7** — source certificate for two described points in one goal and for a description nested through a defined
   point (bridge + `_kiem_result_binding`). Impact on A: none.
3. **G4** — `_la_mat_qua_ba_diem` should keep a source-given plane name (`plane_name ≠ "α"`) for display and question
   matching. Impact on A: none.
4. **G6** — `MAX_MEMORY_DECLARATIONS = 32` (IR contract) bounds problems with ≥3 property-defined points; raising it is
   an IR-contract decision, out of this workstream.

## 9. Performance (same 72-case corpus, same machine; planner/kernel CPU measured outside the route)

Interleaved A/B (base = `git archive d79565b52 backend/app` loaded via `BENCHMARK_BACKEND_ROOT`; it reproduces
`matrix_before` outcomes exactly), receipts `results/matrix_ab{1,2}_{before,after}.json`, ms:

| metric (all 72 cases) | before 1 | after 1 | before 2 | after 2 |
|---|---:|---:|---:|---:|
| planner CPU p50 / p95 | 0.892 / 2.614 | 0.862 / 2.637 | 0.909 / 2.551 | 0.846 / 2.570 |
| kernel CPU p50 / p95 | 11.845 / 28.372 | 12.106 / 25.433 | 12.555 / 25.397 | 11.914 / 24.714 |
| full offline route, cold p50 / p95 | 107.094 / 204.911 | 104.776 / 210.399 | 104.750 / 206.145 | 105.134 / 203.319 |
| full offline route, warm p50 / p95 | 20.025 / 36.871 | 19.865 / 37.030 | 20.282 / 37.008 | 19.869 / 36.007 |
| peak traced memory max (KiB) | 2347.12 ¹ | 898.38 | 878.18 | 897.69 |

On the 47 cases served in both (same work): planner p50 0.933/0.923/0.997/0.917, kernel p50 13.548/12.972/13.325/
13.275, warm p50 22.126/21.789/22.001/22.555 — no measurable change. Search telemetry §6 is identical. ¹ first run in a
fresh process (import-time allocations traced); not reproduced in run 2. "Cold" = first `run_hybrid_offline` of a case
(process-level caches already warm after the first case). The single-shot `matrix_after.json` timings were taken while
another workstream loaded the machine and are NOT used for comparison (outcomes only).

Post-flight (RULES §2b): reused — `run_hybrid_offline`, `ReplayExtractor`, `geometry_oracle`, `_mot_buoc`/`_dat_ngoai_day`/
`do_dai`/`g`, `chain_quotes`; created — `tools/reasoning_matrix.py`, `test_hybrid_reasoning_generalization.py`, two engine
methods' worth of logic (one new method); duplicate check — no second planner/registry/oracle/H-1 framework.

## 10. Gates, cache, H-1, limits

- **Targeted**: new suite 23 passed + 6 strict xfail; planner/composition regression (`test_goal_driven_planner_generalization`,
  `test_hybrid_goal_decomposition`, `test_production_dynamic_composition`, `test_hybrid_capability_composition`,
  `test_route_d4_described_points`, `test_planner_recomposition_oracle`, `test_result_binding_planning`,
  `test_route_d_constraint_planes`) green.
- **Full backend** `pytest -q` (from `backend/`, `ALLOW_LIVE_AI=0`, final tree): **14017 passed, 7 skipped, 3 deselected,
  15 xfailed, 0 failed** (426.6 s). The first full run before re-freezing showed 16 failures: 13 measured-system drift
  (candidate verify, tree-hash pins, K-1/S-2/R-1 approval templates bound to `runtime_identity`) and 3 historical receipts
  moved by the product change (D08, dev02, h16 — §3). Resolution: re-freeze (separate commits), sync `measured_system`
  in the three PENDING_OWNER_DECISION templates (`hybrid-master-backend-replacement/{k1,s2,r1}-owner-approval.template.json`,
  same pattern as earlier runs; no approval field touched), declared delta layers.
- **Docs IA** `tests/geometry/test_docs_information_architecture.py`: green (inside the full run and separately).
- **Candidate**: `freeze_evaluation_candidate.py` → `--verify` MATCH, 106 entries, tree
  `a9993e28fe3c64a053051f5fbcd87f9079638df4f72128a17d4b0d3c1e2916cb` (was `6290986d…`), product commit `5e273f130`.

- **CACHE_VERSION**: not bumped (stays `132`). Only SERVED rows are cached (`main.py::_served_route_d`, store only when
  `status == "SERVED"`); the changes turn previously REFUSED inputs into SERVED or change a refusal code, and all 47
  previously served matrix cases are byte-identical; no prompt / schema / provider / capability surface changed
  (`test_cache_identity` green).
- **H-1**: `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`. A preregistration, template and integrity files already exist in
  `docs/evaluation/geometry/runs/hybrid-independent-h1/` (reused, untouched); no H-1 result is reported.
- **Limits**: development corpus written by the implementer (no held-out claim); the gain is concentrated in one
  configuration family (pyramids whose apex is fixed by lateral edges, incl. the trirectangular tetrahedron); bridge-level
  gaps G2/G3/G4/G7 and the IR bound G6 remain; trilateration needs three non-collinear base points with stated lateral
  lengths and places the apex above the base (the mirror image is congruent); a stated base side contradicting a right
  angle outside the base is refused at layout, inside the base as before.
