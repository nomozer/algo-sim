# Goal-directed composition inside the Hybrid B compiler: design for approval

Status: `HYBRID_GOAL_DIRECTED_COMPILER_DESIGN_AWAITING_APPROVAL`. Nothing in this document is implemented.

## Problem (from the benchmark, not assumed)

The 30-case benchmark (`backend/tests/geometry/hybrid_compiler_benchmark.py`, [report](report.md)) found 0 wrong served answers and 3 false refusals. Two of the three share one cause: **the compiler cannot introduce an auxiliary object to reach a goal.**

| Case | Goal | Library has | Why it is refused |
|---|---|---|---|
| B26 | distance from S to line BD | `orthogonal_projection_line`, `ask_length` | `_cau_hoi` maps each goal to exactly one `ask_*` by operand types; there is no `ask` for (point, line), so `UNSUPPORTED_CAPABILITY` |
| B27 | distance from *the midpoint of SC* (unnamed) to (SAB) | `midpoint`, `ask_distance_point_plane` | a Typed Fact cannot name an anonymous derived operand, and the compiler cannot create one |

The third (B28, "tâm của hình vuông" rejected because the centroid keyword is "trọng tâm") is a source-grammar issue, not composition. Widening it to "tâm" is unsafe: a triangle's circumcentre ("tâm đường tròn ngoại tiếp") is not its centroid. It is out of this design.

## What exists today (code, not intent)

- **Planner** (`geometry_functions/planner.py`): one pass, one rule per fact kind, definition expansion of depth 1, no search, no fact-to-fact inference (its own docstring).
- **Composition between stated constructions** happens in the **engine**: a fixed-point loop (`giai_phu_thuoc` / `_mot_buoc`) places a point once its operands exist. This is why chains such as midpoint → intersection → projection, reordered or renamed, are already served (B09–B16).
- **Nothing searches for a chain** from a goal to the stated facts.

## Options

| | A. New `ask_*` primitives (e.g. `ask_distance_point_line`) | B. Bounded goal decomposition rules in the compiler, with auxiliary objects | C. General goal-directed search (preconditions/effects, bounded BFS) |
|---|---|---|---|
| Fixes B26 | yes | yes | yes |
| Fixes B27 | no (still no way to name the operand) | yes, with an anonymous-operand Typed Fact form | yes, same schema need |
| Where it changes code | Registry; A's provider surface and token budget move again | `planner.py`, source gate (`kiem_nguon`), trace/scene provenance | as B, plus a search module and function precondition/effect metadata |
| Generality | one primitive per goal shape | one rule per goal shape, built only from existing functions | any chain within the bound |
| Auditability | high | high: rule name and auxiliary objects in the trace | lower: needs search trace and tie-breaking rules |
| Risk | low per primitive, grows the surface | moderate: auxiliary objects must never become givens | highest: search space, non-determinism, unproved chains |

**Recommendation: B.** It is the smallest change that closes both measured gaps without growing the Registry, and its rules are an explicit, bounded subset of what C would search. C should wait until the benchmark shows goals that B's rule table cannot express.

## Design B (for approval)

1. **Auxiliary object** = a point (or line/plane) the compiler introduces to reach a goal.
   - Fresh label from a reserved namespace that the text can never contain (for example `_H1`).
   - Provenance `DERIVED` with `binding: AUXILIARY`.
   - Never a premise, never quoted as a given.
   - Shown in Scene3D as an auxiliary object, with no learner-facing technical id.
2. **Decomposition table** (initial: one row, more only with benchmark evidence):
   - `distance(point P, line L)` ⇒ `orthogonal_projection_line(P, L) → _H`, then `ask_length(P, _H)`.
   - Bounded depth 2; deterministic; every expansion recorded in the trace as `goal → rule → calls`.
3. **Anonymous operand** in a Typed Fact (for B27):
   - The extractor emits a `point_def` whose `point` is a reserved placeholder, grounded by the quote "trung điểm của SC".
   - The question references that placeholder.
   - Same grounding rules as named points: the defining predicate and its operands must be in the quote.
4. **Source gate:**
   - An auxiliary call is accepted only if (a) it is produced by a registered decomposition rule, (b) every non-auxiliary operand is grounded in the goal fact's quote, and (c) its result is used only as an operand of that goal.
   - Any other unknown label is still `UNKNOWN_LABEL`.
5. **Fail-closed:** if a rule's precondition fails (for example P lies on L), refuse with the existing kernel code. Never sample a configuration.
6. **No second compiler or engine.** Rules live in `planner.py`; geometry stays in the engine and kernel.

## Tests to write first (if approved)

- **Benchmark:** B26 and B27 strict xfail become passes. All other 28 outcomes unchanged in both evaluations.
- **Mutants:**
  - an auxiliary label leaking into premises;
  - an auxiliary call not produced by a rule;
  - an auxiliary point colliding with a text label;
  - a rule firing on a negated or conditional goal.
- **Grounding negatives:** quote without the point; quote without the line; question in a "nếu … thì" clause.
- **A baseline:** A's function declarations and provider payload unchanged. If any shared schema changes, rerun the A suites.
- **Full backend + T3, candidate refreeze in a clean worktree.** `backend/app` changes, so the candidate must be refrozen.

## Not proposed

- Z3, CEGIS or a proof engine.
- Treating one sampled configuration as a proof.
- A second planner.
- Widening "tâm" to centroid.
