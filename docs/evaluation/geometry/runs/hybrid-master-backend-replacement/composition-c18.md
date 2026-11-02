# Continuation 18 — genuine function composition: points named by a property

**Verdict (pending review and Full T3):** `GENUINE_FUNCTION_COMPOSITION_VERIFIED_OFFLINE`, in this scope only:
- `IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, offline, 0 provider calls;
- two topologies (pyramid S.ABCD, SA ⊥ base, two sizes; right prism ABC.A'B'C' with a right angle at A), every triangle
  of named points (vertices + two stated midpoints);
- two property-defined points (orthocenter, circumcenter) as the operand of a distance or length goal;
- search bound: depth 4, 96 needs, 48 candidates, 16 fresh points.

It does **not** say the planner can solve any geometry problem, nor that the C17 constraint planes are discovery (they
stay `REGISTERED_DECOMPOSITION`).

## 1. Why composition was never needed before (C16/C17, unchanged)

The kernel computes in exact coordinates and has a direct primitive for every measured quantity and for every point the
source describes by a construction (midpoint, foot, intersection). So a goal never *needs* an intermediate object,
except where the kernel lacks a primitive for the object itself. C16/C17 found no such object in the representable
domain; every served plan was a source description or a declared rule.

## 2. Where composition is necessary (§III of the directive)

Objects named by a **property** with no Registry function: the orthocenter ("trực tâm") and the circumcenter ("tâm
đường tròn ngoại tiếp") of a triangle. The C11 planning oracle (`backend/scripts/planning_oracle.py`) had labelled both
`MISSING_PRIMITIVE` — by a constant set (`UNSUPPORTED_PRIMITIVES`), not by search.

**Independent reachability (`composition-oracle.json`, `tools/composition_oracle.py`, no product import).**
- Target: the oracle solves each definition as a linear system in its own exact Euclidean coordinates, and re-checks all
  three conditions.
- DIRECT check: one call of any point-producing Registry function on all named points of the solid (vertices, stated
  midpoints): midpoint, centroid, foot on a line, foot on a plane, translate, line ∩ line, line ∩ plane.
- Forward search (the opposite direction of the planner's backward regression) from the triangle's three vertices: levels
  1–2 exhaustive, level 3 the final operation only (translate's vector restricted to level ≤ 1 — the one incomplete
  check). Its witness plans differ from the planner's (e.g. one orthocenter is the midpoint of C and the midpoint of
  AB in a specific triangle), which shows it does not copy the product's algorithm.

| oracle class | cases |
|---|---|
| `COMPOSITION_NECESSARY` (no named point, no single call reaches it) | **208** |
| `DIRECT_FUNCTION_SOLUTION` (one call reaches it, e.g. a hypotenuse midpoint; the foot of A on (A'BC)) | 136 |
| `SOURCE_POINT` (a right triangle's orthocenter is its vertex) | 136 |
| `DEGENERATE_TRIANGLE` (collinear triple) | 24 |

All 480 non-degenerate cases are `PROVEN_REACHABLE_WITHIN_BOUND` (the 208 necessary: 114 at level 2, 94 at level 3).

**Baseline `/25` (`composition-baseline-25.json`):** 480/480 reachable cases refused `INVALID_TYPED_FACT_NEXT`
(`REPRESENTATION_BLOCKED`); 24 degenerate refused. At the planner level `/25` had no producer for a property-defined
point (arm `no_definitions` below: 480 `UNSUPPORTED_CAPABILITY`), although every function the oracle's plans use exists:
a `REACHABLE_BUT_SEARCH_MISSED` gap of the search, behind a representation gap.

## 3. Design (one authority each; no parallel planner)

- **Contract** (`typed-fact-next/2`, additive): `DESCRIBED_POINT_FIELDS` gains `orthocenter` and `circumcenter`
  (`polygon`: three labels). Flat, v3 and Route A surfaces unchanged.
- **Registry `/31`, data only:**
  - `POINT_DEFINITIONS`: the textbook definition as loci — orthocenter = the common point of the three altitudes
    (through a vertex ⊥ the opposite side), circumcenter = of the three perpendicular bisectors (through a side's
    midpoint ⊥ that side). The descriptor contract has **no call**: no function builds the point.
  - Locus contracts on EXISTING functions, each a local fact naming no goal:
    `orthogonal_projection_line` → `PerpLine(X; P, L, W)` (line P–foot, precondition P ∉ L) and `PerpDir(U, Z; L, W)`
    (Z − foot(Z, L), Z a free point of the plane W); `translate_point` → `PerpLine` (P translated along a `PerpDir`).
  - New contract fields: `free`, `requires` (structural preconditions), `line` (the two slots a locus line spans).
- **Planner `/26`** (`_EffectResolver`, the existing resolver): a property-defined point regresses into one `PerpLine`
  need per locus; each need is solved like any other (all contracts with that effect, free slots bound to the plane's
  points, structural preconditions checked, rejected candidates recorded); the two cheapest loci are met by the ONE
  Registry contract `Point ← Line, Line`. A depth-exhausted alternative no longer aborts its siblings. A memo entry chosen
  before the plan grew is re-chosen (it may now reuse a call). Steps written inside a definition are `search_generated`.
  `_dinh_nghia` names no function (test).
- **Gate:** `_dinh_nghia_trong_chuoi` re-derives that the measured point is the chain's meet of two loci of ITS
  definition (from bound slots, never trusted); a named line may pass through a point the chain built.
- **Engine `/22`:** `_MO_TA` checks the whole definition (all three conditions, Gram metric). A definition without an
  engine predicate is never served (test).

## 4. Results on `/4` (`composition-probe.json`, HEAD `51142160`, backend clean)

| | cases | outcome |
|---|---|---|
| reachable | 480 | **480 served, exact** |
| degenerate | 24 | 24 refused `DEGENERATE_POINTS` |

0 wrong-served, 0 reachable-but-refused, 0 search exhausted.

**Composition (from the served certificate, checked against the oracle):** the 208 `COMPOSITION_NECESSARY` cases are
served by a chain of ≥ 2 distinct functions in which every fresh point is consumed downstream:
- orthocenter: `orthogonal_projection_line` ×2 → `intersect_line_line` (94);
- circumcenter: `midpoint` ×2, `orthogonal_projection_line` ×2, `translate_point` ×2 → `intersect_line_line` (114).

| label | 208 necessary | 272 not necessary |
|---|---|---|
| planner's own label | DISCOVERED | DISCOVERED |
| C15 rule, **computed** by the S-2/R-1 runner's unchanged `composition_label` | DISCOVERED | DISCOVERED |
| this report (oracle necessity) | **DISCOVERED_FUNCTION_COMPOSITION** | `COMPOSED_NOT_NECESSARY` |

The planner cannot know necessity (it has no coordinates), so its label overclaims on the 272; only the 208 are counted.

Search cost: at most 25 explored needs, depth 4; median 33 ms, max 226 ms per case.

## 5. Ablation (`composition-ablation.json`, evaluation-process monkeypatches)

| arm | served | refused | plans changed |
|---|---|---|---|
| candidate | 480 | 24 | — |
| translate locus removed | 240 (orthocenters) | 240 circumcenters `UNSUPPORTED_CAPABILITY` | 0 |
| foot locus removed | **480** | 24 | **240**: every orthocenter by another composition (translates), same answers |
| direction (`PerpDir`) removed | 240 | 240 circumcenters | 0 |
| structural preconditions ignored | 240 | **264 `DEGENERATE_POINTS`**: the cheapest contract (a foot of a midpoint on its own side) is degenerate; the engine refuses, nothing is served wrong | 0 |
| depth 3 (the C17 bound) | 240 | 240 `PLAN_TOO_LARGE` (`SEARCH_EXHAUSTED`) | 0 |
| loci in reverse order | 480 | 24 | **480**: another pair of loci, same answers |
| definitions removed (= `/25` planner) | 0 | 480 `UNSUPPORTED_CAPABILITY` | — |

What this shows, and what it does not:
- The plans come from the contracts: adding or removing ONE contract (data) changes which goals are reachable and how,
  with no planner code change.
- The choice is **not** free where it matters: ignoring the precondition picks an invalid producer for every
  circumcenter.
- Among *valid* alternatives the choice is free (reversed loci, foot vs translate): every valid composition yields the
  same point. The directive does not require distinct answers; we state it.
- There is no verification-driven retry: structural preconditions exclude every invalid candidate in this corpus, so no
  engine failure ever needed one (0 reachable-refused). A metric coincidence that structure cannot see would fail
  closed, not retry (`HYPOTHESIS`: none occurs here).

## 6. Generalization (`composition-metamorphic.json`)

1 044/1 044 hold on the pyramid (2, 2) and the prism: all labels renamed (K.PQRT, EFG.E'F'G'), the triangle's vertices
in reverse order, the premises in reverse order. Sizes: two pyramids are in the corpus. Contract-only change: test
`test_c18_plans_follow_the_definition_data…` gives "trực tâm" the circumcenter's loci as DATA: the planner composes the
other construction with no code change, and the engine's orthocenter predicate refuses it.

## 7. Source safety and adversarial controls (`test_route_d_function_composition.py`, 21 tests)

Refused, never served: kind swapped (`SOURCE_OBJECT_MISMATCH`), another triangle (`SOURCE_OBJECT_MISMATCH`), an invented
description (`QUOTE_NOT_IN_SOURCE`), "trọng tâm" in the source (`SOURCE_OBJECT_MISMATCH`), forged certificates (point =
a vertex, another definition, a consistent forgery whose meet is not of two loci — each `AUXILIARY_RULE_MISMATCH` with
its own reason), a definition without engine predicate (`UNSUPPORTED_CAPABILITY`), a collinear triangle.

## 8. Regression (all at the product commit `b2dd77de`, receipts at clean heads)

- C17 constraint-witness corpus re-run (`constraint-witness-probe-c18.json`): 1 531/1 531 rows identical to r3,
  planner labels included.
- phase-s (`inventory-phase-s.json`, `wave3-phase-s.json`): Wave 3 67/72, 72/72 negatives refused (62 exact reason),
  0 wrong-served, 0 transitions; locked 96/96; 203 probes 0 served negatives, 0 internal (the same 12 curved
  REFUSED → REFUSED).
- S-2 gold replay (`s2-pilot-gold-replay-c18.jsonl`) 35/36, R-1 gold replay (`r1-live-pilot-gold-replay-c18.jsonl`)
  composition labels unchanged (7 source-explicit, 4 registered, 0 planner disagreements).
- Preview fixtures 41/41 through the declared `/30 → /31`, `/25 → /26`, `/21 → /22` identity delta.
- One test re-pinned its budget (`test_available_foot_candidates_are_also_budgeted` sets the old bound 8 it was written
  for; the property it checks is unchanged). Seven version pins moved.

## 9. Known limits (all fail closed)

- Points named by a property only as an unnamed operand of a measure; "Gọi H là trực tâm …" (a named point) is not
  representable in `/2`; a section plane through such a point is refused (`UNKNOWN_LABEL`, test).
- Two definitions, one locus kind (`PerpLine`, in the triangle's plane). Incenter / bisectors need radicals the locus
  contracts do not produce (`MISSING_PRIMITIVE`, not measured here).
- Corpus generated by the implementer; the oracle shares no code with the product but the same author wrote both
  (`AUTHORING_INDEPENDENCE: NOT_ESTABLISHED`).
- Live extraction of the new kinds: `NOT_MEASURED` (protocol `constraint-extraction-pilot-protocol.md`).
