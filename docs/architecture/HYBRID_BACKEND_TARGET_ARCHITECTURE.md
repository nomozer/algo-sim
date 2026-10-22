# HYBRID_BACKEND_TARGET_ARCHITECTURE — research target and Session 1 decision

**Continuation clarification (2026-10-22):** §4 means two-line relation planes without the new cut clause; combining them with stated cut-edge/derived-solid construction remains unsupported. Adapter /3 is still a separate compiler. The bridge validates structural namespaces, transports declared units/plane names, and orchestration rejects mismatches against source-gated engine output. It does not parse source text. Full source/identity/outcome parity and `cut_edges` semantics require the decision in `../evaluation/geometry/runs/backend-hybrid-continuation/BACKEND_HYBRID_ARCHITECTURE_DECISION.md`.

Status: research architecture, 2026-10-22, run [`typedfactnext-planner-bridge`](../evaluation/geometry/runs/typedfactnext-planner-bridge/plan.md).
Product unchanged: `LLM_ONLY`, response contract `flat`, Hybrid product enablement **NO-GO**, `CACHE_VERSION = 127`.

## 1. Four routes today (`main` 43247c9e)

| route | input | grounding | who chooses functions | kernel | Scene3D |
|---|---|---|---|---|---|
| Production | text → LLM `SemanticProgramSpec` | `semantic_source_gate`, assumption gate | the LLM writes the program | interpreter + exact kernel | `pipeline._dung_scene3d` |
| D-A function calling | text → LLM tool calls | `registry.kiem_nguon` | the LLM | `engine._Dung` → IR → kernel | `function_route` |
| D-B TypedFact | `TypedFact` facts | `registry.kiem_nguon` + engine `kiem_mat_viet` / `kiem_mo_ta` | `planner.lap_ke_hoach` (rules + `_EffectResolver`) | same | same |
| D-Next | `TypedFactNextPayload` (authored JSON) | quote substring + number in quote only | `adapter3._Adapter3Compiler` hand-written table | `_Dung` built directly, two-phase folding; curved route separate | `adapter3` |

Fragmentation (measured in the [baseline audit](../evaluation/geometry/runs/typedfactnext-planner-bridge/BACKEND_INTEGRATION_BASELINE_AUDIT.md)): two fact-to-call mappers,
two copies of the three relation-plane decompositions, two grounding authorities; the planner lacks section vertices on
cut edges and derived sub-solids, which only Adapter /3 has.

## 2. Target research pipeline

`Verified TypedFactNext` → **bridge** (pure translation) → `TypedFact` (+ internal, provider-hidden fields) →
**Source Gate** `kiem_nguon` (closed grammar, clause roles, premise coverage, number ownership, planner certificates) →
**Planner** `lap_ke_hoach` (typed goal entry, bounded producer selection with reuse) → **trusted Registry functions** →
**Engine** `_Dung` (exact chart, postconditions, certificates) → IR → interpreter + kernel → **verified Scene3D**.

Responsibilities, one owner each:

| layer | owns | never does |
|---|---|---|
| Bridge | rename TypedFactNext fields onto TypedFact; refuse constructs TypedFact cannot express | add a fact, infer a relation, read the text |
| Source Gate | every call / certificate bound to closed source wording; numbers owned; roles (premise / goal / condition / negation) | compute geometry |
| Planner | which Registry functions, in which dependency order, reusing equivalent producers | coordinates, truth of a relation |
| Engine / kernel | coordinates, exact checks, certificates | accept a call the gate did not validate |

## 3. Answers to the design questions

- **Common IR?** TypedFactNext stays the richer authoring contract; the planner input stays `TypedFact`. A bridge is
  feasible for the polyhedral subset because every TypedFactNext premise kind already maps to one Registry function, and
  the missing capability (cut-edge vertices, derived solid) needs two internal references, not a new IR. Internal fields
  are `SkipJsonSchema` on `TypedFact`: provider-facing schemas and frozen fingerprints stay byte-identical, and the
  provider parse path refuses them.
- **Planner reuse.** `lap_ke_hoach`, `_anh_xa`, the relation-plane decompositions with their derived-plane memo, the
  dependency ordering with cycle / dangling refusal, the call de-duplication, the effect budgets.
- **Which Adapter /3 operations are geometry functions.** Real Registry functions: every premise kind, `translate_point`,
  `orthogonal_projection_line`, `intersect_line_plane`, `section`, `pyramid`, `ask_*`. Orchestration only: plane
  decomposition choice, per-edge vertex allocation, label allocation, two-phase folding, highlight / sequence metadata,
  scene enrichment.
- **Shared points / edges / faces across solids.** Solid identity is its call and canonical name; vertices are global
  labels. A label shared by two solids with different points (`pyr1::D` ≠ `pyr2::D`) is not expressible in `TypedFact`;
  the bridge refuses it (`BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY`) instead of renaming points the source does not name.
- **Construction-only goals.** A relation-plane `section` with role `question`, or a derived solid with role `question`,
  is a plan with no `ask_*`; the route serves the scene with no numeric answer.
- **No unlicensed inference.** The planner only reuses a producer whose effect is already established by a validated
  call (a point produced on the cut edge that defines the plane; an identical intersection). The cut clause itself must be
  read from the source by the gate; the engine re-verifies every vertex (0 < t ≤ 1, edge not in plane).

## 4. Decision

**`BRIDGE_FEASIBLE`** for: pyramids and prisms; premise kinds of Adapter /3; relation planes
`through_point_parallel_plane`, `through_point_perpendicular_line`, `through_point_parallel_two_lines`; sections with
stated cut edges and named or unnamed vertices; derived pyramid over such a section; construction-only goals; volume ratio
and residual volume over solids the source names.

Refused by the bridge (typed, no fallback to Adapter /3 inside the bridge): curved solids, `plane_equation`,
`parallel_to_base_at_distance`, `parallel_to_base_at_ratio`, `axial_section`, solid-qualified label collisions, derived
prism solids, math goals whose operands the source does not name. These stay on Adapter /3 as research and are
classified not-yet-planned.

No provider-facing contract change and no new IR statement kind are required; therefore no versioned contract proposal
is opened in Session 1.
