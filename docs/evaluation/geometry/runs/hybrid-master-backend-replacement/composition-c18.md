# Continuation 18 — function composition for points named by a property

**Verdict:**
- **`GENUINE_DISCOVERY_NOT_ESTABLISHED`** (unchanged from C16/C17).
- **New capability `DEFINITION_REGRESSION_COMPOSITION_VERIFIED_OFFLINE`**: a point the source names only by a property
  (orthocenter, circumcenter of a triangle) — which no Registry function builds and which, in 202 goals, no single call
  reaches — is served exactly by composing existing functions.

The first draft claimed `GENUINE_FUNCTION_COMPOSITION_VERIFIED_OFFLINE`. The independent adversarial review (round 1,
`NOT_READY`, MAJOR-1/2) showed that by the C17 standard the plans are a **registered decomposition**: the definition
declares the loci and the meet; the locus contracts were written with their only consumer; every valid alternative gives
the same point and the free choices are forced by structure; nothing is retried. We accept it: the claim is withdrawn,
the product's provenance is corrected (§4), and discovery stays not established. We did not change the definition of
discovery to keep the positive.

**Scope:** `IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, offline, 0 provider calls; pyramid S.ABCD (SA ⊥ base, two
sizes) and right prism ABC.A'B'C' (right angle at A), every triangle of named points (vertices + two stated midpoints);
the centre as the operand of a distance or length goal; bound depth 4, 96 needs, 48 candidates, 16 fresh points **per
problem**.

## 1. Why composition was never needed before (C16/C17, unchanged)

The kernel computes in exact coordinates and has a direct primitive for every measured quantity and for every point the
source describes by a construction. A goal needs an intermediate object only where the kernel lacks a primitive for the
object itself. C16/C17 found none in the representable domain.

## 2. Where composition is necessary

The orthocenter ("trực tâm") and the circumcenter ("tâm đường tròn ngoại tiếp") of a triangle have no Registry function.
The C11 planning oracle had labelled both `MISSING_PRIMITIVE` by a constant set (`UNSUPPORTED_PRIMITIVES`), not by search.

**Independent reachability (`composition-oracle.json`, `tools/composition_oracle.py`, standard library only).** The
oracle solves each definition as a linear system in its own Euclidean coordinates; checks one call of every
point-producing Registry function on all named points (DIRECT); and searches FORWARD from the triangle's vertices
(levels 1–2 exhaustive; level 3 the final operation only, translate's vector restricted to level ≤ 1). Its witness plans
differ from the planner's, so it does not copy the product's algorithm.

| oracle class (per point) | cases |
|---|---|
| `COMPOSITION_NECESSARY` | 208 — of which **202** are necessary for the GOAL (review MINOR-3: 6 ask a distance to a face parallel to the triangle's plane, the same for every point of it) |
| `DIRECT_FUNCTION_SOLUTION` (e.g. a hypotenuse midpoint; the foot of A on (A'BC)) | 136 |
| `SOURCE_POINT` (a right triangle's orthocenter is its vertex) | 136 |
| `DEGENERATE_TRIANGLE` | 24 |

All 480 non-degenerate cases are `PROVEN_REACHABLE_WITHIN_BOUND`.

**Baseline `/25` (`composition-baseline-25.json`):** 480/480 refused `INVALID_TYPED_FACT_NEXT` (`REPRESENTATION_BLOCKED`).
Behind it, the `/25` planner had no producer for such a point (arm `no_definitions`: 480 `UNSUPPORTED_CAPABILITY`) though
every function the oracle's plans use exists.

## 3. Design (one authority each; no parallel planner)

- **Contract** (`typed-fact-next/2`, additive): `DESCRIBED_POINT_FIELDS` gains `orthocenter`, `circumcenter`
  (`polygon`, three labels). Flat, v3 and Route A surfaces unchanged.
- **Registry `/31`:** `POINT_DEFINITIONS` — the textbook definition as loci (altitudes; perpendicular bisectors through a
  side's midpoint), a descriptor contract with no call; declared as the rule `DINH_NGHIA_DIEM` in `AUXILIARY_RULES`.
  Locus contracts on existing functions: `orthogonal_projection_line` → `PerpLine` (point off the line) and `PerpDir`
  (`Z − foot(Z, L)`, Z a free point of the plane); `translate_point` → `PerpLine`. Fields `free`, `requires`, `line`.
- **Planner `/26`:** `_EffectResolver._dinh_nghia` regresses the definition into one `PerpLine` need per locus, each
  solved like any need (all contracts with that effect, free slots, structural preconditions, rejected candidates
  recorded); the two cheapest loci are met by the one `Point ← Line, Line` contract (chosen by signature; the locus line
  is bound through `contract.line` — review MINOR-1: the planner does depend on that library shape). A depth-exhausted
  alternative no longer aborts its siblings; a memo entry chosen before the plan grew is re-chosen. Steps under a
  definition are `registered`.
- **Gate:** `_dinh_nghia_trong_chuoi` re-derives that the measured point is the meet of two loci of ITS definition; only
  in such a chain may a named line pass through a point the chain built (review NIT, scoped).
- **Engine `/22`:** `_MO_TA` checks all three conditions of the definition (Gram metric); a definition without a
  predicate is never served.

## 4. Results on `/4` (`composition-probe-r2.json`)

480/480 reachable cases served exactly, 24/24 degenerate refused (`DEGENERATE_POINTS`); 0 wrong-served, 0
reachable-refused, 0 search exhausted. The 202 goal-necessary cases are served by a chain of ≥ 2 distinct functions in
which every fresh point is consumed: orthocenter `orthogonal_projection_line` ×2 → `intersect_line_line`; circumcenter
`midpoint` ×2, `orthogonal_projection_line` ×2, `translate_point` ×2 → `intersect_line_line`.

| label | value on all 480 |
|---|---|
| planner provenance (after review MAJOR-2) | `REGISTERED_DECOMPOSITION`, 0 `search_generated` steps |
| C15 rule, computed by the S-2/R-1 runner's unchanged `composition_label` | `REGISTERED_DECOMPOSITION` |
| oracle necessity | 202 `NECESSARY_COMPOSITION_SERVED`, 278 `COMPOSED_NOT_NECESSARY` |

Search cost: ≤ 25 needs, depth 4, tens of ms per case.

The independent reviewer re-attacked correctness on 636 new cases on four other topologies (non-orthonormal regular
S.ABC, S.ABC right at B, a cube, midpoints named H and I to collide with fresh labels): 0 wrong-served, 28/28 degenerate
refused.

## 5. Ablation (`composition-ablation-r2.json`)

| arm | served | refused |
|---|---|---|
| candidate | 480 | 24 |
| translate locus removed | 240 | 240 circumcenters `UNSUPPORTED_CAPABILITY` |
| foot locus removed | 480 | — (the same feet, re-derived through `PerpDir`, plus one redundant translate — review MINOR-2: not another construction) |
| `PerpDir` removed | 240 | 240 circumcenters |
| structural preconditions ignored | 240 | 264 `DEGENERATE_POINTS`: the cheapest contract (foot of a midpoint on its own side) is degenerate; the engine refuses it; nothing is retried |
| depth 3 | 240 | 240 `PLAN_TOO_LARGE` |
| loci reversed | 480 | — (another pair of loci, same answers) |
| definitions removed (= `/25`) | 0 | 480 |

The plans follow the declared definition and the contracts; among valid alternatives the choice does not matter. That is
why this is not discovery.

## 6. Generalization (`composition-metamorphic-r2.json`)

1 044/1 044 hold: labels renamed, triangle order reversed, premises reversed. Changing the definition DATA (orthocenter
given the circumcenter's loci) changes the plan with no code change, and the engine refuses the wrong point (test).

## 7. Source safety (`test_route_d_function_composition.py`)

Refused, never served: kind swapped, another triangle, an invented description, "trọng tâm" in the source, three forged
certificates (each `AUXILIARY_RULE_MISMATCH` with its own reason), a definition without engine predicate, a collinear
triangle, a section plane through a defined point.

## 8. Regression

- C17 corpus re-run: 1 531/1 531 rows identical to r3 (`constraint-witness-probe-c18-r2.json`).
- phase-s/phase-s2: Wave 3 67/72, 72/72 negatives (62 exact reason), 0 wrong-served, 0 transitions; locked 96/96; 203
  probes 0 served negatives.
- S-2 gold 35/36, R-1 labels unchanged; adding `DINH_NGHIA_DIEM` to `AUXILIARY_RULES` flips 0 gold labels.
- Preview fixtures 41/41 through the declared identity delta.
- **Declared behavioural transition (review MINOR-6):** the budget raise serves one pre-C18 plan that `/25` refused
  `PLAN_TOO_LARGE` (nine stated feet of S on BD, `test_available_foot_candidates_are_also_budgeted`): served √11,
  correct; the test locks both outcomes.

## 9. Known limits (all fail closed)

- Not measured, though served: a defined point in angle, area or point–line goals (the reviewer's spot checks, 4/4
  correct; no receipt) — review MINOR-4.
- The budget is per problem: 3–4 circumcenter goals in one problem are refused `PLAN_TOO_LARGE` — review MINOR-5.
- A right triangle's orthocenter is drawn as a fresh point on top of its source vertex.
- "Gọi H là trực tâm …" (a named point) is not representable; a section plane through a defined point is refused.
- Incenter / bisectors need radicals the locus contracts do not produce.
- Corpus authored by the implementer; oracle independent in code, not in authorship.
- Live extraction of the new kinds: `NOT_MEASURED` (`constraint-extraction-pilot-protocol.md`).

## 10. What genuine discovery would still need (`INFERRED`)

A goal whose subgoals no declared definition or rule names: e.g. a property the Registry states only as relations
between objects (not as loci), so that the planner must itself choose which relation becomes which locus, with
alternatives that differ in validity in ways structure cannot see — so that exact verification fails and the search
must retry. None of the measured goals has that property.
