# Goal decomposition, slice 1: distance from a point to a line

Status: `HYBRID_GOAL_DECOMPOSITION_SLICE1_AWAITING_REVIEW`.

- Approved scope: design option B, **slice 1 only (B26)**. B27 (Typed Facts schema change) is not approved and not done; B28 remains a separate source-grounding issue.
- Branch `research/hybrid-compiler-capability-audit`, LOCAL. Not merged, not pushed, no PR.
- LIVE GEMINI CALLS = 0. Production default `LLM_ONLY` and `CACHE_VERSION` 125 are unchanged.

## 1. What changed

The design and plan are in [`../hybrid-compiler-capability-audit/design.md`](../hybrid-compiler-capability-audit/design.md) and [`plan.md`](../hybrid-compiler-capability-audit/plan.md).

| Where | Change |
|---|---|
| `planner.py` | `_phan_ra`: distance(point, line) → `orthogonal_projection_line(P, XY, image=<aux>)` → `ask_length(P, <aux>)`. It runs only for a question fact that is not negated. Conditional and ambiguous facts were already refused before planning, and proof goals and negated facts never reach the rule. Depth 1, deterministic. The trace step `decompose_goal` records goal → rule → calls. `PLANNER_VERSION` is now geometry-fact-planner/3 |
| `registry.py` | `AUXILIARY_RULES` (one row). `_kiem_phu` in `kiem_nguon` admits an auxiliary **only** through the planner's declaration (§3) |
| `engine.py`, `function_route.py` | The declaration is passed only by `run_fact_route`. The engine marks the placed foot `provenance: DERIVED, binding: AUXILIARY` |
| Not changed | Typed Facts schema, prompt, function declarations, both provider surfaces (fingerprints pinned in a test), IR, kernel, Scene3D, frontend. No second planner, solver or engine |

## 2. Results

**Benchmark**: same 30 cases, same oracle and expectations. Only B26's strict-xfail marker was removed, as the pre-registration requires.

| | before ([baseline](../hybrid-compiler-capability-audit/baseline/metrics.json)) | after ([after](after/metrics.json)) |
|---|---|---|
| correct served | 18 | **19** |
| correct refusal | 9 | 9 |
| **wrong served** | **0** | **0** |
| false refusal | 3 (B26, B27, B28) | 2 (B27, B28) |

- The figures are identical in both evaluations (verified facts, fake-provider pipeline).
- Only B26 changed: false refusal → correct served, √11 = the oracle's `dist²(S, BD) = 11`.
- The outcomes and codes of the other 29 cases are unchanged.

**Focused tests**: `tests/geometry/test_hybrid_goal_decomposition.py`, 40 tests.

**RED at `4a3a4938`** (new tests copied into a clean worktree of the unchanged code; log [`red-baseline-at-4a3a4938.txt`](red-baseline-at-4a3a4938.txt)):
- 38 failed: every positive, refusal, gate and mutant test, plus B26 in both evaluations of the benchmark.
- 4 passed before and after: the properties that already held (negated, proof and conditional facts are not decomposed; provider surfaces unchanged).

**GREEN**: 40/40. The hybrid/function-route cluster gives 629 passed, 4 xfailed (B27, B28 × 2).

| Requested scenario | Test | Result |
|---|---|---|
| S off BD | `test_point_off_the_line_b26` | √11 (oracle 11) |
| S on BD | `test_point_on_the_line_is_distance_zero` | 0; the foot coincides with O. Route A gives the same 0 for the *stated* projection, so the contract is unchanged |
| line undetermined / degenerate | `test_line_not_determined`, `test_degenerate_line` | `UNDERDETERMINED_POINT` (M never defined); `DEGENERATE_POINTS` (BB) |
| missing data | `test_missing_data` | refused (`MISSING_DIMENSION`/`UNDERDETERMINED_POINT`) |
| contradictory | `test_contradictory_data` | `INCONSISTENT_FACTS` |
| several configurations | `test_several_configurations_are_refused` | `UNDERDETERMINED_POINT`. The height is given but the foot is not; the distance to BD depends on the apex, so nothing is sampled |
| renamed points | `test_renamed_points` | T.MNPQ: dist(T, NQ) = oracle |
| reordered clauses | `test_reordered_clauses_and_facts` | reversed sentences and facts give the same answer and the same label H |
| auxiliary label collision | `test_auxiliary_label_avoids_every_label_of_the_text`, tamper `label="S"` | text has H → H1; H and H1 → H2; a forced collision gives `AUXILIARY_LABEL_COLLISION` |
| dependencies between constructions | `test_dependency_on_derived_points`, `test_two_goals_get_distinct_auxiliaries` | derived point (M), derived line (SO, AO), foot built after its operand; two goals get H and H1 |
| metamorphic scaling | `test_scaling_multiplies_the_squared_distance` | side 4, SA 6 → 4 × 11 |

**Negatives at the gate**:
- conditional ("Nếu khoảng cách … thì …") → `CONDITIONAL_CLAUSE`;
- proof ("Chứng minh rằng khoảng cách …") → `GOAL_CLAUSE_NOT_PREMISE`;
- negated quote → `NEGATED_CLAUSE`;
- quote names another point or another line, or has no "khoảng cách" → `SOURCE_OBJECT_MISMATCH`.

**Mutation**: 9 source mutants of the new code are run in process and all 9 are killed.
- Gate: no collision check, no structural match, no conditional check, no proof check, no negation check, no point/line binding.
- Planner: decomposes negated goals, ignores taken labels, asks the wrong segment.

**A compatibility**:
- A's function declarations and both provider surfaces are byte-identical (A `1e3f71ea…`, B `a4f368cb…`, declarations `41e090cd…`).
- `function_calling.py` never mentions an auxiliary.
- The same calls without the declaration are still refused `UNKNOWN_LABEL`.
- A suites pass; the locked A/B candidate `12da4768` and historical evidence are untouched.

**Gates**: candidate refrozen in its own commit; T3 in a clean worktree — see [`handoff.md`](handoff.md) §2.

## 3. Source decision for every auxiliary

| Item | Decision |
|---|---|
| What it is | A **point the compiler introduces**: the foot of the perpendicular from P to line XY. Provenance `DERIVED`, binding `AUXILIARY`. **Never GIVEN**: it is not a premise and no fact call mentions it |
| Its source | The question sentence itself ("Tính khoảng cách từ S đến BD."). Both calls carry exactly that quote, and nothing else is added: no assumption, coordinate or value |
| Who may create it | Only the planner, by the registered rule `distance(point,line)`, through a declaration passed beside the plan. Route A has no way to pass one |
| Gate checks | rule known · label ∉ text labels · the two calls match the rule exactly · quote ⊂ source · not negated · not in a "nếu … thì" or proof clause **at the matched phrase** · "khoảng cách từ P đến (đường thẳng) XY" binds the same P and XY |
| Label | First of H, H1, H2, … absent from the text and from all facts. It is shown to the learner as the foot's name |
| Geometry | Built by the existing engine and kernel; the incidence and orthogonality relation is verified independently (`relation_verified`) |

## 4. Defect found during the work

- My first gate version read the clause role at the start of the quote. A question quote that itself begins "Nếu khoảng cách … thì …" was therefore **served**.
- The gate now reads the role at the matched phrase, as the construction gate already does for quotes that carry their own "Nếu".
- A test and a mutant pin this behaviour.

## 5. Limits (also `ISSUE-ARCH-HYBRID-AUXILIARY-POINT-LIMITS`)

- **Departure from the design text: the label is fresh, not taken from a syntactically reserved namespace.**
  - The design suggested `_H1`, but the Registry `Label` pattern is part of A's provider surface, so changing it would break the "no provider change" constraint.
  - Collision is excluded by construction and re-checked at the gate.
- **Only one wording.** Other phrasings are refused (`SOURCE_OBJECT_MISMATCH`). They are not measured; the benchmark has only this wording.
- **Point on the line.** The answer is 0 and the foot is drawn on the point under a second label. This is the same as route A for a stated projection. No human visual review.
- **Kernel codes are missing from the refusal taxonomy.** Codes raised by the kernel (`DEGENERATE_POINTS`) are not in the benchmark's `REFUSAL_CLASS`, whose completeness test reads only `TuChoi` literals. No benchmark case reaches them.
- **No real-model evidence.**
  - Compiler evidence (verified facts) and fake-provider evidence say nothing about whether Gemini extracts the (point, line) distance question correctly.
  - The extraction prompt is unchanged and was not measured.
- **Out of scope:** B27 and B28 are still false refusals. No browser gate was run: route D is not wired to the UI, and the frontend did not change.
