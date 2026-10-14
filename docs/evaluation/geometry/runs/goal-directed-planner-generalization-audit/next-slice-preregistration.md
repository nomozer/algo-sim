# One proposed slice: source-bound result operands and bounded effect-driven point–line distance resolution

**DESIGN ONLY — implementation not authorized by this audit.** Development corpus: `next-slice-corpus.json`, 6 new positive
cases and12 fully specified negative mutations, plus listed current regressions. All may be read: NOT_HELD_OUT. Existing
probe outcomes/labels remain immutable. Source architecture locations/hashes: `source-map.json`.

## Problem, hypothesis and limits

Current Planner cannot feed an existing intersection_line result to an existing projection/measurement chain because
transport/FunctionSpec carry endpoint arrays and fixed recipes, not source-bound result identities and planning effects.

Hypothesis: one typed result reference plus small effect metadata on existing functions allows the existing Planner to
resolve a point–line distance goal through either a named line or an intersection-line output, reusing available producers
and a supplied foot, without a new recipe for each solid/vertex/dependency structure. Existing IR witnesses support
geometric feasibility; serving/source-grounded extraction of this new goal has NOT been demonstrated.

Scope is point–line distance, not arbitrary goals/search. No Group B, new Geometry Function, Kernel, Engine replacement,
second Planner/FactGraph, algebra language or DSL. Mathematical identity d(P,L)=|PF| for the orthogonal foot is retained
as a general theorem/contract, not erased in the name of generality. Existing plane/section rules remain unchanged.

## Interfaces and source contract

Modify existing `TypedFact` with nullable `line_ref: str | None` (fact ID, not point label/coordinates/program). Only:
question(distance, points_a=[P], line_ref=g), and projection(point=P, at=F, line_ref=g). Existing points/points_b line
representation and line_ref are mutually exclusive. ID g must identify an affirmative source-backed intersection_line
fact with two source-named planes. References may precede/follow definitions: validate the full ID map first. Reject absent,
wrong-kind, proof, condition, negated or ambiguous producers. Role tags stay separate; derived construction is not a GIVEN
relation. Existing transport's premise tag on an explicit construction definition does not authorize proof assumptions.
Allow producer roles premise (explicit definition) or question (explicit construction request), as for existing section
construction. In either case the output is DERIVED after geometric verification, never an assumed GIVEN relationship.
For this first result-reference path, each producer plane must use exactly3 distinct source labels; Engine must verify
noncollinearity. Four-or-more-point plane notation remains outside the new path until all-point coplanarity is certified;
do not silently take the first3 labels as evidence for an asserted larger plane. Existing non-reference paths are unchanged.

Question source must explicitly ask distance from P to the intersection of the same two planes; supported atomic phrase:
`Tính khoảng cách từ M đến giao tuyến của (SAC) và (SBD).` Plane order/label normalization are mathematical, not ID-based
source permission. Explicit projection on a derived line uses the analogous `Gọi H là hình chiếu vuông góc ...` phrase.
No arbitrary named-line language parser in this slice. New facts are tested through the actual fake-provider extraction
adapter; no claim about Gemini live reliability.

Existing ProjectionLineArgs: nullable Seg line and nullable str line_ref, exactly one required, point/image unchanged.
No dummy endpoints, fake coordinates or unsupported point names to fit a fixture. Runtime consumer resolves line_ref
through the plan's validated producer binding, never through an LLM object ID that bypasses Registry.

Add minimal internal Python dataclasses in existing registry.py (not a model transport or new DSL):
`PlanningContract(inputs, effect, source_policy, verifier)` on optional `FunctionSpec.planning`; input/effect terms are
closed semantic role tags for this domain, with operand placeholders. Contracts index existing source/geometry checks,
not a new authority that declares givens true. Function declarations continue excluding this metadata.

| Existing function | Typed needs / promised effect | Existing authority after execution |
|---|---|---|
| intersection_line | Two resolved source planes → Line(ref), unique intersection incident to both | Kernel.intersect_plane_plane; reject parallel/coincident |
| orthogonal_projection_line | Point(P), Line(L) → Foot(F,P,L) | Kernel project; exact incidence and Gram orthogonality |
| ask_length | Point(P), Foot(F,P,L) → AnswerDistance(P,L) | Existing measurement with the certified foot identity |

Metadata describes independent inputs/effects, not a tuple containing a full recipe. For direct named lines, Line(L) is
already available; for source-derived lines, resolver selects intersection_line; for a supplied source projection, Foot
is available after its producer verification and the extra projection is omitted. The terminal measurement's Foot contract
is the same distance identity already used by B26. Not every Registry function acquires planning metadata in this slice.

Internal shapes to implement (existing modules, no parsing language):
`PlanningTerm(kind: Literal["Point","Plane","Line","Foot","AnswerDistance"], operands: tuple[str,...])`;
`PlanningContract(inputs: tuple[PlanningTerm,...], effect: PlanningTerm, source_policy:
Literal["declared_intersection","projection_foot","distance_witness"], verifier: str)`.
Contract placeholders are role slots, not an expression evaluator. NeedFoot has operands(F,P,L); only output F may be
fresh/unbound. Other inputs must bind to explicit source values. Argument binding adapts L to either Seg or line_ref and
maps the chosen producer's existing typed args; no guessed endpoints. Descriptor/verifier names dispatch to existing
Registry/Engine checks, never arbitrary Python/eval. Match results remain tentative until those checks succeed.
ResultBinding uses opaque unique producer IDs, stable IR-name allocation and entity types; technical IDs stay out of learner text.
Route A lacks the Planner certificate and must refuse new result-reference auxiliaries, preserving its existing named-line
cases; the declared provider argument difference is still recorded rather than pretending its surface is byte-identical.

## Proposed resolver in the existing Planner

Internal `GeometryGoal(point, line)` and `ResultBinding(producer_id, entity_type)` are ephemeral views over KeHoach's
existing calls/source IDs, not another semantic state. No coordinates/metric arithmetic or new inferred premise stored
in Planner. Distinguish promised effects in a candidate plan from VERIFIED effects checked by Engine later.

`resolve_goal(goal, plan: KeHoach) -> PlannedBinding`: index FunctionSpec.planning by effect kind; unify source-bound
operands/role types, then recursively resolve unmet typed needs. Inputs must bind to explicit source objects/references;
do not enumerate arbitrary plane triples or invent a line. Existing explicitly declared point producers continue using
the old mapping/Engine dependency closure. Only the bound intersection/projection/measurement functions participate.

Prefer a compatible source-supplied foot, then the candidate with fewer new constructions; stable canonical operand
keys/function names break ties. Source validity and all original givens must be checked regardless of candidate choice.
Do not backtrack around contradictory facts or substitute another line when the requested intersection is nonunique.
Numeric domain verification remains Engine/Kernel fail-closed. No A*, numerical search or sampling is needed.

Bounds: maximum3 registered operator levels,32 need expansions,8 candidate branches,4 new line results,8 new feet,
and existing MAX_CALLS64. Active-need set detects cycles; memoize by normalized point + explicit line binding. Share the
same line/foot for repeated goals; preserve separate answer IDs/quotes. Fresh auxiliary labels use current policy and
never overwrite H/H1/H2 from the source. Exhaustion ⇒ PLAN_TOO_LARGE, never partial service.

Canonical line key swaps plane order and endpoint ordering but does not assume two different source planes coincide
merely because one numerical realization does. Completion means every requested answer has a grounded binding DAG,
all inputs verified, exact postconditions true, and existing final-memory/Scene3D gates pass. A planned effect is not proof.

## Engine/Registry integration and refusal

Extend existing `_Dung` canonical entity storage/dependency resolution to referenced line results. Existing points and
metric remain authoritative; a line table inside this Engine is not a second FactGraph. Resolve line coordinates using
the existing Kernel from the producer's plane points, then project with that SAME line. No duplicated geometry formula.
IR emission makes `gt_g` once before the consuming project_onto, after its supporting points; preserve solid-first
formation where dependencies permit. Adapt `_bien_dich_mat_cat` to avoid a second line assignment. `_construction_relation`
checks the bound Line3 and actual foot, not a metadata promise. Preserve ordinary point/line code paths.

Extend `registry._kiem_phu`/kiem_nguon with a source-bound result/foot certificate: producer IDs, input references/types,
selected Registry contract, source spans and intended goal. Validate all links against actual calls and source; never trust
client-supplied certificates or labels. Source policies call the current semantic grounding authority; activate the
existing closed atomic premise/goal coverage for this new path as Group A does. No second Vietnamese parser/state.
Keep PROOF_GOAL/CONDITION/NEGATION distinct; malicious long quotes/unread premise/value anchors must refuse on the new path.

Unknown ref ⇒ UNKNOWN_DERIVED_REFERENCE; wrong type ⇒ DERIVED_REFERENCE_TYPE_MISMATCH; contradictory source ⇒ existing
source/consistency codes; nonunique line ⇒ existing Kernel codes; cycles/budgets ⇒ existing dependency/PLAN_TOO_LARGE codes.
No LLM_ONLY fallback, fabricated foot, segment/infinite-line confusion or zero-distance fake direction. Zero distance is
valid when P lies on the unique line; render no misleading nonzero witness. These are structured refusals, not new features.

## Module scope and compatibility

- planner.py: validation, bound goal/need resolution, reuse/memoization; route existing B26 through the same resolver.
- registry.py: three planning contracts, exactly-one line argument validation, central source certificate checks.
- engine.py: canonical line bindings, dependency and IR emission adaptation, existing predicates/measurement reused.
- fact_extraction.py: describe semantic line_ref extraction, audit actual response schema/request/parse path.
- function_route.py: pass existing auxiliary binding metadata and verified trace; reuse projection witness/Scene3D builder.
- Reuse semantic_program IR/interpreter/formation/display names, metric/Kernel/measure, existing scene renderer/harness.
- No RequestContract or geometry_compiler FactGraph replacement; no frontend implementation expected.

Future A/B provider argument/TypedFact surfaces WILL change intentionally due the flat optional reference fields;
old fixtures remain valid. Gemini's flattened schema and deterministic exactly-one validation must agree. Freeze new
provider hashes, schema diff and candidate divergence only after implementation. No live extraction claim. Cache125 can
remain only if default route/import closure and its cached envelopes are unchanged; a contrary finding stops the slice
for an explicit cache/scope decision. This audit itself changes none of these product surfaces or cache/candidate bytes.

## RED → GREEN implementation plan for the next authorized turn

1. Add `backend/tests/geometry/test_result_binding_planning.py`: freeze this corpus, assert the three measured new goals
   serve exact d²10/11,5,3; current baseline RED=SCHEMA_INVALID. Keep all6 positive and12 negative labels; don't edit them
   after results. Add current named-line and supplied-foot control, ID/order/rename/metric/collision tests.
2. Typed field/signature/source-reference validation in existing models; test missing/wrong/proof/condition refs. Newly
   recognized but not implemented goals must return UNSUPPORTED_CAPABILITY safely, not crash or serve during transition.
3. Add three contracts and effect index/need resolution in existing Planner. Test supplied foot reuse, catalog order
   invariance, type-incompatible candidate exclusion, shared derived objects, cycle/budget stop. Tests must fail if the
   resolver is replaced by a goal/family-specific ordered function list. No recipe keyed by family/test/source numbers.
4. Adapt canonical Engine line dependency/binding and emit real existing IR. RED line-before-foot/duplicate-line tests;
   GREEN exact oracle incidence/orthogonality/distance, correct provenance and trace order. Keep every given checked.
5. Central Registry certificate/closed-source gate: RED all3 inherited grounding adversaries; GREEN fail-closed. Check
   fake-provider run_ai_fact_route through actual new schema, no schema change just to appease a hand-written fixture.
   Also mutate the source request to `Tính khoảng cách từ M đến đoạn giao tuyến của (SAC) và (SBD).`; require
   SOURCE_OBJECT_MISMATCH rather than silently interpreting a finite segment as the infinite referenced line.
6. Regressions: existing two-line45/32, historical30 separately unchanged labels, grounding/sequencing/domain tests.
   Freeze candidate/provider pins, independent local code review, authoritative clean T3, docs/identity and related browser
   harness on pyramid/prism/cuboid + refusal. Current orbit exception stays unresolved unless separately addressed.

## Independent oracle, frontend and GO/NO-GO

Independent analytic/rational oracle uses source dimensions and Gram. Fixtures reused; point-to-line square-distance can
also be checked with Gram minimization wᵀGw−(wᵀGd)²/(dᵀGd), not the Kernel projection implementation. Intersection
incidence and direction are checked against both plane covectors. At least one arbitrary translated/scaled chart checks
metric assumptions. Oracle author independence is partial (same implementer may code it); algorithm independence explicit.

GO only if all6 new structural positives + current named-line controls serve correctly,12 negatives and3 old grounding
adversaries fail closed, wrong served0, effects select different chains based on available producers, duplicate construction0,
answers/IDs deterministic, source bounds/metric/IR/trace/Scene3D correct, current regressions retained, candidate/review/T3
required gates PASS. New families/vertex renamings alone do not count as generalization. No scalar-only success omitting scene.
NO-GO if any wrong serve, source permission bypass, missing verification, new per-family recipe, second semantic authority,
nonunique result served or architecture expansion beyond this bound. Conservative grammar limits remain explicit.

Self-review: all data types/source/reference fields,3 operator roles, budgets, cycle/zero behavior, module boundaries,
provider/cache decisions, corpus/oracle/browser/review gates are specified. No essential algorithm choice deferred to
implementation; unexpected architectural requirements stop for the user. This does not promise general solution of all geometry.
