# Composite geometry — offline Route D contract

Wave 2C, run `composite-geometry`. Owner scope `GO_HYBRID_WAVE2C_LOCAL_RESEARCH`; Hybrid product NO-GO.

## Inputs, functions and preconditions

The existing `TypedFact` and Registry argument models are unchanged. An explicit `solid` premise declares each pyramid's
apex and ordered base. Each vertex is either a vertex of the determined root solid, or the uniquely verified output of
existing `midpoint`, `divide_segment`, `centroid`, intersection, projection or translation functions. Ratios remain offline
Route D inputs; the frozen flat provider does not offer them. No coordinates are accepted from extraction.

`pyramid(apex: Label, base: Poly)` now admits constructed bases. The engine chooses its sole root base from solids whose
vertices are not construction outputs, independently of alphabetical labels and fact order. Independent root bases remain
`UNSUPPORTED_MULTIPLE_BASES`. A derived base never seeds a new regular apex, metric, frame or orientation. Every vertex
must resolve before the solid can be constructed (`UNDERDETERMINED_POINT` / existing coded precondition failures).

All base vertices must be coplanar; the first three must span the plane. The exact kernel checks each face is simple and
nondegenerate. The apex must be off the base plane. The existing kernel retains authority over solid boundary and section
validity. An explicit section still goes through the existing intersection, boundary and closed-polygon checks.

Two declared pyramids may use the same point IDs and share a face. The optional closed source sentence
`Hai hình chóp <solid> và <solid> có mặt chung (<vertices>).` is validated against BOTH declared face tables, even if
extraction quoted it as part of a larger premise. A false face is `INCONSISTENT_FACTS`; unbound wording is
`SOURCE_OBJECT_MISMATCH`. Face identity is the full named vertex set, never mere coplanarity. No relative orientation
or placement is inferred from a bare gluing phrase. Distinct local vertices with the same display label require a future
contract; this version has a single named-point namespace.

## Exact output and provenance

The functions retain their existing IR/Scene3D outputs. For composite pyramids the engine emits `verify_solid` trace
entries with source call ID, point dependencies, `DERIVED` provenance and exact `volume_squared`. This certificate uses
Gram base-area squared × altitude squared / 9, independently of the interpreter's oriented boundary-volume algorithm.
Every asked composite pyramid volume must match that certificate before `SERVED`. This is numeric verification of a
uniquely constructed configuration; it does not promote observational proof goals to deductive proofs.

The internal topology value may be a map from a complete frozenset of IR vertex IDs to an existing `RequestContract`.
It is produced solely from source-bound solid calls and consumed by `formation.lop_khoi`. This is not a serialized
TypedFact/Adapter change. Conflicting topology roles for one vertex set refuse `AMBIGUOUS_REFERENCE`. All face indices
remain local to their solid, while shared points retain one global ID. No speculative geometry is rendered.

IR emission follows construction prerequisites separately for every solid: original solid, subsequent auxiliary points,
derived solid, then measurements. Formation supplies the same base/edge objects and roles as existing single solids.

## Planner and limits

No new search algorithm or case-family selector is introduced. Explicit point/solid premises use the existing declared
workflow and topological DAG; numeric questions select existing Registry functions. Described-point goals keep the
existing bounded typed-effect search. This is deterministic function composition, **not learned planning**.

Budgets unchanged: 64 calls, effect depth 3, 32 needs, 8 candidates, 4 result lines, 8 feet, 4 derived planes. Reuse and
source/operand binding remain enforced by the existing planner/source gate. Exceeding a budget refuses the whole plan.

Supported development slices: parallel-base child pyramids from named edge midpoint/rational points; multiple sub-pyramids
in one root chart with an explicit verified common face. Volume/area/length goals use existing contracts. Residual-solid
and volume-ratio goal quantities, unnamed section vertices, independent charts, qualified duplicate labels, arbitrary
gluing and broader shared-face wording remain unsupported or `BLOCKED_BY_CONTRACT`.

Governance unchanged: LLM_ONLY, flat, CACHE_VERSION 127, Adapter /2, ALLOW_LIVE_AI=0, no /api/analyze Hybrid enablement.
The formation change is conditional on an internal topology map supplied by Route D; the default route's inputs and
served content are unchanged, so no product-cache bump is needed.
