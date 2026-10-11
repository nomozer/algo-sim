# Hybrid B compiler capability audit

Status: `HYBRID_GOAL_DIRECTED_COMPILER_DESIGN_AWAITING_APPROVAL`.

- Branch `research/hybrid-compiler-capability-audit` from `main` `548066a8`, worktree `.superpowers/worktrees/hybrid-compiler-audit`.
- Not merged, not pushed, no PR.
- LIVE GEMINI CALLS = 0. Production default `LLM_ONLY` unchanged. `CACHE_VERSION` 125 unchanged.
- No file under `backend/app` or `frontend/src` changed, so candidate `a8dc02fc…` (product `74df2a78`) still holds. The locked A/B candidate `12da4768…` is untouched.

## 1. What this run did

1. **Recorded the architecture decision.**
   - ADR: [`HYBRID_B_TARGET_ARCHITECTURE_DECISION.md`](../../../../architecture/HYBRID_B_TARGET_ARCHITECTURE_DECISION.md).
   - Hybrid B is the preferred direction inside Text-to-Geometry Functions; A stays as the baseline.
   - The decision rests on offline evidence only. It changes no default and adds no second engine.
2. **Answered the ten capability questions from the code** (§3).
3. **Pre-registered a new 30-case Vietnamese benchmark** before touching the compiler (commit `267eeb58`).
   - It has an oracle independent of the product.
   - It is scored in two separate evaluations.
4. **Measured the benchmark** (§4) and diagnosed every miss (§5).
5. **Did not change the compiler.**
   - None of the three gaps can be closed with a small rule without either making the source gate less strict or changing the Typed Facts schema.
   - The design with compared options is in [`design.md`](design.md) and the plan in [`plan.md`](plan.md); both are waiting for approval.

## 2. Pre-flight

| Item | Value |
|---|---|
| `main` | `548066a8` = `origin/main`. Only `?? frontend/public/` is dirty; it belongs to the user and was not touched |
| Research branch | `research/hybrid-compiler-capability-audit`, 1 benchmark commit + the docs commit of this run |
| `docs/real-model-e2e-readiness` | `4cfa547f`, 1 commit ahead of and 57 behind `main` (base `28ac1d61`), same as `origin`. Survey doc only (2 files). Merges cleanly. Kept as is |
| `feat/real-model-pilot-tooling` | `471a2c79`, 4 commits ahead of and 57 behind `main`, and **1 ahead of `origin`**: the unpushed commit records one live `gemini-2.5-flash` run. It contains the e2e-readiness commit, 70 files in total, measures the `LLM_ONLY` route through `run_pipeline`, and merges cleanly. Kept as is |
| Backups and the user's files | not touched |

- Neither old branch is deleted, merged or rebased.
- The tooling branch's unpushed commit is the only record of a live run, so it must not be lost by a branch clean-up.

## 3. Capability matrix: the ten questions

Answers come from reading `geometry_functions/planner.py`, `engine.py`, `registry.py`, `ai/function_route.py` and `ai/fact_extraction.py`, and are checked against the benchmark.

| # | Question | Answer (code) | Evidence |
|---|---|---|---|
| 1 | How does the compiler choose a function? | A fixed lookup by fact kind and operand type: `_anh_xa` (relations), `_do_dai` (lengths), `_cau_hoi` (goals). One fact gives one call; a definition expands at most one level deep | `planner.py` docstring: "no fact-to-fact inference" |
| 2 | Multi-step problems? | **Yes, if every intermediate construction is stated.** The planner emits the stated constructions; the engine's fixed-point loop (`giai_phu_thuoc`/`_mot_buoc`) places each point once its operands exist | B09, B10, B12 (3-step chains) served |
| 3 | Goal-directed planning (search from the goal back to the givens)? | **No.** Nothing searches. Calling the current mechanism "goal-directed" would be wrong | B26 refused although its two-step chain exists in the Registry |
| 4 | Dependency cycles? | `DEPENDENCY_CYCLE` only for declared `depends_on` (Registry, A side). A point-level cycle in facts never resolves and ends as `UNDERDETERMINED_POINT`, which is fail-closed but has a less precise diagnosis | engine loop; no benchmark case |
| 5 | Intermediate points in any order? | Yes, if stated: order in the text does not matter | B13, B14 (reversed) served |
| 6 | GIVEN vs DERIVED? | Yes: provenance on every object, and the source gate checks that each given is quoted | `kiem_nguon`; grounding tests |
| 7 | Not-unique figure vs invariant answer? | **Partly.** A volume that is invariant under the free foot of the height is refused as `FIGURE_NOT_UNIQUE`. Any other goal on such a figure is refused as `UNDERDETERMINED_POINT`, so the refusal is correct but the diagnosis is not "not unique" | B21 (volume) `FIGURE_NOT_UNIQUE`; B22 (distance) `UNDERDETERMINED_POINT` |
| 8 | Missing data / contradiction? | Fails closed: `MISSING_DIMENSION`, `INCONSISTENT_FACTS` (the engine re-checks every fact on the built figure) | B17–B20 |
| 9 | Depends on keywords? | **Yes, at the source gate.** A predicate is accepted only if its cue occurs in the quote; the centroid cue is "trọng tâm" | B28 refused `PREDICATE_NOT_IN_QUOTE` |
| 10 | Library has the parts, compiler cannot compose them? | **Yes, two cases:** point→line distance (B26) and an unnamed derived operand in the question (B27) | §5 |

## 4. Benchmark

- Module: `backend/tests/geometry/hybrid_compiler_benchmark.py`; tests: `test_hybrid_compiler_benchmark.py`.
- Pre-registered in `267eeb58`, before any compiler change. This run made no compiler change.
- The case texts are original. The data are fixed: square base side 2, `SA ⊥ (ABCD)`, `SA = 3`, plus a cube, a triangular prism and regular pyramids.

**Independence and limits of the oracle**

- The oracle computes exact rational squared answers from its own coordinates and formulas: projection, intersection, plane distance, Cayley–Menger volume.
- It imports nothing from the product. An AST test enforces this.
- 17 values are pinned by hand in `test_oracle_matches_hand_derived_values`.
- The same author wrote the cases, the oracle and the expectations, so the evaluator is independent in code but not in authorship.
- The cases are not held out from the compiler's design. They test known shapes of Grade 11–12 problems, not a population.

**Two evaluations, kept apart**

- **facts**: verified Typed Facts → `run_fact_route`. Tests the compiler only.
- **pipeline**: the Vietnamese text → `run_ai_fact_route` with a fake provider that returns those facts. Adds schema validation, quotes and source grounding. It says nothing about what a real model would extract.

**Results** (`baseline/metrics.json`, written by `backend/scripts/measure_hybrid_compiler_benchmark.py`)

| | facts | pipeline |
|---|---|---|
| correct served (answer equals the oracle) | 18 | 18 |
| correct refusal | 9 (underconstrained 3, contradictory 2, figure not unique 1, unsupported 3) | 9 |
| **wrong served** | **0** | **0** |
| false refusal | 3 (missing composition 2, keyword dependence 1) | 3 |
| live model calls | 0 | 0 |

- Both evaluations agree case by case on outcome and code: 30/30, enforced by `test_both_evaluations_agree_on_correct_facts`.
- Tests: 92 passed, 6 strict xfail (the three gaps × two evaluations).
- Mutation:
  - A wrong value (`√12` for `√11`) is scored `wrong_served`.
  - A refusal of a solvable case is scored `false_refusal`.
  - A refusal code the classifier does not know fails `test_every_refusal_code_of_the_route_is_classified`, which reads every code in the route source.

**Correction.** The message of commit `267eeb58` says "19 correct served, 8 correct refusals". The measured numbers are **18 and 9**. The commit is not amended, because evidence refers to it. This report is the correction.

**By tier**

| Tier | Cases | Outcome |
|---|---|---|
| simple | B01–B04 | 4 served |
| two primitives | B05–B08, B29, B30 | 6 served |
| chain | B09, B10 | 2 served |
| derived input | B11, B12 | 2 served |
| reordered | B13, B14 | 2 served |
| renamed | B15, B16 | 2 served |
| missing data | B17, B18 | 2 correct refusals |
| contradictory | B19, B20 | 2 correct refusals |
| multi-configuration | B21, B22 | 2 correct refusals (see Q7) |
| unsupported goal | B23 (cross-section area), B24 (given angle), B25 (circumsphere) | 3 correct refusals `OUT_OF_SCOPE` |
| composition | B26, B27, B28 | **3 false refusals** |

## 5. Gaps and root causes

| Case | Text (question) | Code | Root cause | Smallest honest fix |
|---|---|---|---|---|
| B26 | "Tính khoảng cách từ S đến BD." (√11) | `UNSUPPORTED_CAPABILITY` | `_cau_hoi` has no (point, line) distance goal. The parts exist (`orthogonal_projection_line` + `ask_length`), but the compiler would have to create an **auxiliary foot point** that the text never names, and the source gate rejects unnamed labels | design option B: decomposition rule plus auxiliary objects |
| B27 | "Tính khoảng cách từ trung điểm của SC đến (SAB)." (1) | `OUT_OF_SCOPE` | Typed Facts can only reference **named** points. "trung điểm của SC" inside the question has no name to bind | Typed Facts schema: an anonymous operand form |
| B28 | "Gọi O là tâm của hình vuông ABCD." (√(9/13)) | `PREDICATE_NOT_IN_QUOTE` | the centroid cue is "trọng tâm". Adding "tâm" is **unsafe**: "tâm đường tròn ngoại tiếp" of a triangle is not its centroid | context-restricted cue ("tâm của hình vuông/hình bình hành/…") — a separate grounding decision |

Why there is no fix in this run:

- Every fix touches either the source gate or the Typed Facts schema.
- The source gate is a soundness boundary. The schema change alters B's extraction surface (schema and prompt hash), and with it the frozen token ceiling of a future A/B pilot.
- So none is a "small compiler rule". Per the brief, this run stops at design and plan.

## 6. Limits

- Offline only; there is no evidence about real Gemini extraction.
- One author, 30 cases and fixed data. This is not a population, so do not report the 0 wrong served as an error rate.
- The pipeline evaluation uses faithful facts. Extraction errors are out of scope.
- A was not run on this benchmark: the brief asks about the compiler. A's evidence stays as it was.
- Human visual acceptance: not applicable (no scene change).

## 7. Tests run

See [`handoff.md`](handoff.md) §3 for the commands and counts.
