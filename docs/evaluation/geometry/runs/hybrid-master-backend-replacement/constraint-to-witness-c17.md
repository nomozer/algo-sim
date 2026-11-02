# Continuation 17 — constraint-to-witness planes: implicit objects found, built and proved on Hybrid `/4`

**Scope of every claim below:**
- `IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, offline, 0 provider calls;
- two topologies (pyramid S.ABCD with SA ⊥ base at two sizes; right prism ABC.A'B'C');
- the constraint vocabulary {contains points, ∥ a line, ⊥ a plane};
- the normal search bound `MAX_NORMAL_CANDIDATES = 12`.

Verdict: see §7 (set after the independent review).

## 1. Why C16 found no discovery, and what changed

C16 measured that, on everything representable, served plans were source-explicit or declared rules, and that
`typed-fact-next/2` could not express a goal whose objects are implicit (`planner-generalization-c16.md` §3).

C17 tested that hypothesis by **opening the representation and changing nothing else first**. The `/24` candidate
`3154a696` refuses all 352 unique cases of §4 with `INVALID_TYPED_FACT_NEXT` (`constraint-witness-baseline-24.json`):
`REPRESENTATION_BLOCKED`, measured.

## 2. The contract (`typed-fact-next/2`, additive; `/1` unchanged and refuses the new kind)

- `DerivedPlaneSectionSpecV2.plane_kind = "constrained"` carries `constraints: [PlaneConstraintSpec]`.
- Each constraint has a `kind` (`contains_points` 1–4 labels, `parallel_to_line` 2, `perpendicular_to_plane` 3–4) and
  `operands`.
- The constraints say what the source states, never a construction.
- Operands are scoped by the section's solid (`scope_records`, S5/S7/S8, census rows and scope tests).
- A described point inside a constraint is refused by the bridge (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT`).
- The bridge carries the constraints as the internal fact field `plane_constraints`. The locked flat `TypedFact` schema
  fingerprint is unchanged.

## 3. Architecture: four authorities, one path

**Source Gate** (`registry._kiem_mat_rang_buoc`, rule `MAT_RANG_BUOC`):
- One closed-grammar definition of the named plane must equal the stated constraint set: "(P) đi qua X, Y[, Z] và
  vuông góc với (Q)", or "(P) chứa XY và song song với UV". It must not be negated, conditional or a goal.
- Every witness is checked against what produced it:
  - the anchor translated along a stated line; or
  - along a normal of a stated plane — either a premise line stated ⊥ to it, or `Z − H` with `H` written by a function
    whose **contract** has a `Normal` effect.
- Fresh labels must not collide with the source's.
- The definition, the section phrase and the area ask are recorded as read.

**Planner** (`planner._mat_rang_buoc`, `_phap_tuyen`, `/25`) — goal regression per constraint:
- contained points are witnesses as they are;
- `∥ UV` gives `anchor + UV`;
- `⊥ Q` opens a **`Normal(Q)` subgoal**. Its candidate producers are enumerated, not chosen by name:
  - every premise line stated ⊥ Q (cost 0);
  - every Registry contract with a `Normal` effect (today `orthogonal_projection`, `normal_witness` policy), with its
    free point `Z` bound to each solid vertex off Q. Vertices of a face holding Q's labels are rejected structurally
    and recorded.
- The cheapest candidate wins; ties go by the vertex's place in the solid, never by wording.
- Calls are written from the contract template (`render_call`).

**Engine** (`/21`, `_kiem_mat_rang_buoc`):
- every normal witness is ⊥ Q in the chart Gram metric, and non-zero;
- **existence and uniqueness from every stated constraint**: the affine rank of the constraint vectors is exactly 2.
  Below that is `PLANE_NOT_UNIQUE`; a vector off the span is `INCONSISTENT_FACTS`;
- the plane is built through the first non-collinear triple (`span`) of the coplanar list;
- a stated ∥ line inside the plane is `LINE_CONTAINED_IN_PLANE`; a face plane is `SECTION_PLANE_IS_FACE`.

**Route** (`function_route._chung_can_thiet`): a search-generated witness outside the engine's `span` only re-checks a
stated relation, so it moves to `verification_witness_steps`. Telemetry never claims a step the figure did not need.

**Adapter `/4`** re-checks:
- that the plane relation is the stated constraints;
- that every witness and stated point lies on the plane;
- the face rule.

## 4. Systematic measurement (`constraint-witness-probe.json`, 1 377 generated cases)

**Families:**
- F1: two points ⊥ a plane;
- F2: a line ∥ a line;
- F3: three points ⊥ a plane — over-determined.

**Oracle:** independent exact fractions, no product import.

| oracle | cases | product |
|---|---|---|
| UNIQUE | 352 | **352 served, exact area** |
| NOT_UNIQUE | 52 | 52 `PLANE_NOT_UNIQUE` |
| NO_PLANE (contradictory) | 289 | 289 `INCONSISTENT_FACTS` |
| LINE_IN_PLANE | 301 | 301 `LINE_CONTAINED_IN_PLANE` |
| NO_SECTION | 383 | 282 `SECTION_PLANE_IS_FACE`, 101 `PLANE_TOUCHES_EDGE` |

0 wrong-served, 0 reachable-but-refused, after the two fixes below.

**Gaps the oracle exposed and their root-cause fixes**, both regression-locked:
1. **7 reachable cases refused `COLLINEAR_POINTS`.** A normal parallel to two stated points made the first three
   points collinear.
   - Fix: the engine builds through the first independent triple. This is identical for every plane served before.
   - Fix: the planner lists stated points first.
2. **25 cases kept a DISCOVERED label** although the stated points already spanned the plane.
   - Fix: the engine reports its `span`, and the route reclassifies.

**Composition**, from the served **certificate** plus the oracle's necessity test, never from telemetry:

| label | cases |
|---|---|
| a necessary normal constructed by the planner, foot label absent from the source | **202** |
| a necessary normal reused from a stated premise | 24 |
| stated-line translation only (one producer, as `MAT_HAI_DUONG`) | 101 |
| witness only re-checks a stated relation | 25 |

The product label agrees with this classification on every served case.

## 5. Ablation (`constraint-witness-ablation.json`, the 352 unique cases; process-local monkeypatch)

| arm | the 202 constructed | the 24 premise | the 101 stated-line |
|---|---|---|---|
| `Normal` contract hidden | **202 refuse** `UNSUPPORTED_CAPABILITY` (outcome `MISSING_PRIMITIVE`) | survive | survive |
| normal search capped to 1 candidate | **202 exhaust** `PLAN_TOO_LARGE` (`SEARCH_EXHAUSTED`) | 24 exhaust | survive |
| `/24` baseline (`3154a696`) | refused: representation | refused | refused |

So each of the 202 depends on the contract-driven search, and each had at least two candidate producers.

**Contract-only extension:** a Registry entry carrying only a `Normal` contract is selected with no dispatch code
(`test_c17_a_function_known_only_by_its_normal_contract…`). This is planner level only, because the clone has no IR.

## 6. Regression

- Wave 3 phase-r: 67/72, 72/72 negatives refused (62 exact reason), 0 wrong-served, 0 transitions.
- Preview fixtures 41/41.
- C17 tests: 14 + 2 scope.
- Full T3 and the freeze follow the review.

## 7. Verdict and limits

VERDICT_PENDING_REVIEW

**What is *not* claimed:**
- generalization beyond these two topologies and three constraint kinds;
- other implicit objects (a described line, a point fixed by a property);
- live extraction: no model has produced `constraints`, so `LIVE_EXTRACTION_NOT_MEASURED`;
- that `MAT_RANG_BUOC` is not a rule. It is a **declared witness vocabulary**. What is searched is which producer meets
  each subgoal, and which point it starts from.
