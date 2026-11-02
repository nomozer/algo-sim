# Continuation 17 — constraint-to-witness planes on Hybrid `/4`

**Verdict:**
- **`GENUINE_DISCOVERY_NOT_ESTABLISHED`.**
- **New capability `CONSTRAINT_TO_WITNESS_SERVICE_VERIFIED_OFFLINE`.**

**Scope:**
- `IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, offline, 0 provider calls;
- the pyramid S.ABCD with SA ⊥ base (two sizes) and the right prism ABC.A'B'C';
- reference planes named by vertices or stated edge midpoints;
- two closed-grammar templates;
- the constraint vocabulary {contains points, ∥ a line, ⊥ a plane}.

## 1. Hypothesis tested

C16 left one hypothesis (`planner-generalization-c16.md` §3): goals with implicit objects are not representable in
`typed-fact-next/2`, and opening them would require planner-found intermediates.

- **Representation (`VERIFIED_OFFLINE`).** The `/24` candidate `3154a696` refuses all 352 unique cases of the first
  probe with `INVALID_TYPED_FACT_NEXT` (`constraint-witness-baseline-24.json`). After C17 they are served.
- **Discovery (`NOT_ESTABLISHED`).** Opening the representation did **not** produce search-based composition (§5).

## 2. Contract (`typed-fact-next/2`, additive; `/1` unchanged)

- `DerivedPlaneSectionSpecV2.plane_kind = "constrained"` carries `constraints: [PlaneConstraintSpec]`.
- Each constraint has a `kind` (`contains_points` 1–4, `parallel_to_line` 2, `perpendicular_to_plane` 3–4) and
  `operands`.
- The constraints say what the source states; they never encode a construction or a solution path.
- Operands are scoped by the section's solid (`scope_records` S5/S7/S8, census rows, scope tests).
- A described point in a constraint is refused.
- The bridge carries the constraints as the internal fact field `plane_constraints`. The locked flat `TypedFact` schema
  is unchanged.

## 3. Authorities on one path

**Source Gate** (`_kiem_mat_rang_buoc`, rule `MAT_RANG_BUOC`, registry `/30`):
- one closed-grammar definition must equal the stated constraint set;
- it must not be negated, conditional or a goal;
- every witness is checked against its producer: a stated line, a premise line stated ⊥ Q, or a function whose
  contract has a `Normal` effect;
- fresh labels are checked;
- the definition, section phrase and area ask are recorded as read.

**Planner** (`_mat_rang_buoc`, `_phap_tuyen`, `/25`):
- contained points are witnesses as they are;
- `∥ UV` gives `anchor + UV`;
- `⊥ Q` gives a `Normal(Q)` need. Producers are enumerated from premises and `Normal` contracts, with a free vertex Z
  off Q.
- Points on Q are excluded from **structure**: faces, plus stated edge midpoints; a set of shared points counts only if
  it is not collinear.

**Engine** (`/21`):
- ⊥ is checked in the Gram metric;
- **existence and uniqueness** come from the exact affine rank of all constraint vectors (`PLANE_NOT_UNIQUE`,
  `INCONSISTENT_FACTS`);
- for a `MAT_RANG_BUOC` plane only, the plane is built through its first independent triple. Every other plane keeps
  its first three points (review NIT-2);
- the plane is checked not to contain a stated ∥ line and not to be a face.

**Route** (`_chung_can_thiet`): a witness outside the engine's `span` becomes `verification_witness_steps`.

**Adapter `/4`** re-checks the relation and that every point lies on the plane.

## 4. Systematic measurement (`constraint-witness-probe-r2.json`, 1 531 generated cases, independent exact oracle)

| oracle | cases | product |
|---|---|---|
| UNIQUE | 407 | **407 served, exact area** |
| NOT_UNIQUE | 58 | 58 `PLANE_NOT_UNIQUE` |
| NO_PLANE (contradictory) | 290 | 290 `INCONSISTENT_FACTS` |
| LINE_IN_PLANE | 301 | 301 `LINE_CONTAINED_IN_PLANE` |
| NO_SECTION | 475 | 356 `SECTION_PLANE_IS_FACE`, 119 `PLANE_TOUCHES_EDGE` |

0 wrong-served, 0 reachable-but-refused.

**Gaps found and fixed at their authority**, with regression tests:
1. A normal ∥ two stated points made the first three collinear, so 7 cases were refused. The fix is the independent
   triple for `MAT_RANG_BUOC` planes.
2. Some witnesses only re-checked ⊥ and were still labelled. The engine's `span` plus the route now reclassify them.
3. **Review MINOR-1:** Q named through a midpoint ((SAM) = (SAB)) let the planner pick a vertex on Q, which was
   refused. Midpoint closure fixes it; the generator now includes such Q.

**Composition.** Under the reviewed C15 rule, **all 407 are `REGISTERED_DECOMPOSITION`**, because `MAT_RANG_BUOC` is a
declared rule. The product's own label agrees on all 407. In detail:

| label | cases |
|---|---|
| a necessary normal built through the rule's free vertex Z | 267 (in 74 of them the foot is a vertex of the solid) |
| a normal taken from a stated premise | 24 |
| translation along a stated line | 101 |
| a witness that only re-checks a stated relation | 15 |

## 5. Why this is not discovery (independent review, adversarial; ablation `constraint-witness-ablation-r2.json`)

| arm | built normal (267) | premise (24) | stated line (101) |
|---|---|---|---|
| `Normal` contract hidden | refused (`UNSUPPORTED_CAPABILITY` / `MISSING_PRIMITIVE`) | survive | survive |
| **last candidate instead of the cheapest** | **267 survive, same answers** | survive | survive |
| **premise never used, normal always built** | survive | **24 survive, same answers** | survive |

- **The choice does not matter.** Any candidate yields the same plane, so the "search" selects a free parameter of a
  fixed recipe: "⊥ Q ⇒ foot of some vertex off Q, then translate". That is a **registered decomposition with a
  contract-bound parameter**, not composition found by search.
- **Necessity is structural.** Two points plus one direction never span a plane, so the third witness is needed
  because the kernel cuts through three points. It is not a planning insight.
- **There is no backtracking.** Candidates are listed and the cheapest is taken. Structure excludes bad ones; the
  engine refuses a degenerate one (fault-injection test); nothing retries.
- The withdrawn C17 arm "one candidate allowed" showed only that several candidates exist.

**`INFERRED`:** genuine discovery would need a goal whose witnesses can be reached by **different** compositions with
different results, or by a chain of subgoals none of which a declared rule supplies, so that a wrong choice fails
verification and search must backtrack. No goal in the current vocabulary has that property. Measuring it needs such
goals, and a verify-and-backtrack loop between planner and engine (`HYPOTHESIS`).

## 6. Regression

- Wave 3 phase-r: 67/72, 72/72 negatives refused, 0 wrong-served, 0 transitions.
- Preview fixtures 41/41.
- C17 tests: 15 + 2 scope.
- Full T3 and the freeze: see the master state.

## 7. Known limits (from the review, all failing safe)

- Over-refusals: "Gọi (P) là mặt phẳng …" gives `QUESTION_CONTEXT_UNSUPPORTED`; a definition inside the question
  sentence and "khi (P) …" are refused.
- Two topologies only. No ⊥ + ∥ combinations, because the grammar refuses them.
- Live extraction of `constraints`: `NOT_MEASURED`.
