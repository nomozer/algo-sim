# Hybrid Backend Master Architecture Contract

Status: active target contract for `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`, authorized by the Owner on 2026-10-30. This contract defines the target and migration constraints; it is not a claim that all capabilities are implemented. Implementation status and evidence live in `../evaluation/geometry/runs/hybrid-master-backend-replacement/HYBRID_MASTER_EPIC_CURRENT_STATE.md`.

## Intent and scope

Replace legacy LLM_ONLY geometry orchestration with one primary Hybrid backend. AI remains responsible for extracting Vietnamese mathematical intent and source facts; deterministic code owns planning, coordinates, mathematics, verification and scene formation. Backend only. No frontend redesign, OCR/YOLO, alternative V3 architecture, new DSL without measured benefit, or live provider calls without a registered budget and stop rules.

```text
Vietnamese problem -> AI structured facts -> semantic grounding
 -> canonical fact/entity graph -> deterministic construction planner
 -> primitive compiler / construction IR -> trusted geometry functions
 -> interpreter / exact kernel -> geometry and scene verification
 -> certified Scene3D + formation timeline
```

These are logical responsibilities, not a requirement for a new module at every arrow. Existing correct components must be reused.

## Existing owners and the target

| Responsibility | Existing owner to reuse | Required boundary |
|---|---|---|
| Production API and policy snapshot | `backend/app/main.py`, `ai/pipeline.py::RoutePolicy` | AS-IS remains LLM_ONLY until migration gates pass; explicit Hybrid routing must never silently fall back |
| Source-only canonical extraction | `ai/typed_fact_next_extraction.py` | TypedFactNext /2, verbatim source identity, exact quote references; extraction validation is not geometric certification |
| Canonical fact/entity representation | `simulation/geometry_functions/typed_fact_next.py` | TypedFactNext /2 is the existing authoritative request representation; extend it when needed rather than introduce a competing facts schema |
| Identity, scope and ownership | `typed_fact_next.py::canonical_vertex_ref`, scope rules S1–S11, bridge S8 | One canonical identity resolver; ownership must be established before capability dispatch; namespace removal must not change identity |
| Grounding and premise semantics | `typed_fact_next_bridge.py`, `geometry_functions/registry.py::kiem_nguon` | Schema/scope validation, verbatim references, premise roles, contradiction checks and geometric checks retain their actual separate authorities; present one coherent refusal model without duplicating them |
| Construction planning | `geometry_functions/planner.py` | Reuse `_EffectResolver`, `PlanningContract`, effect search, bounded dependency DAG and producer reuse; do not build another planner or family dispatcher |
| Primitive contracts | `geometry_functions/registry.py` | Typed inputs/effects, source policy, preconditions, postconditions, verifier and dependencies; adding a JSON relation name alone adds no capability |
| Compilation and exact execution | `geometry_functions/engine.py`, `simulation/geometry/`, semantic interpreter | Fraction/Radical and existing exact objects/operations; independent checks of proposed plan effects; no coordinate or answer from AI |
| Scene and formation | `semantic_program/simulation_state.py`, `scene3d.py`, `formation.py` | Verified IR/trace is authoritative; stable identities, causal dependencies, certified explanations and deterministic replay |
| Consumer envelope | `ai/adapter4_route.py` | Thin validation/transport adapter; no independent construction authority |

The old `geometry_compiler/fact_graph.py` and family compiler are a separate historical opt-in slice, not the target Hybrid planner. Adapter /3 is a compatibility baseline with capabilities /4 has not yet migrated. Neither may be removed before its last required consumer/capability is accounted for.

## Canonical facts, identity and provenance

The canonical graph is the entity/relation/dependency interpretation of the existing typed request, not a second solver or a parallel mutable database. Its declarations, relations and goals come from TypedFactNext /2; planned constructions and their certified effects extend it through the existing plan/IR trace.

- Points have one canonical identity from declared vertex bindings and explicit ownership. Labels are display/source names, not namespace authority. Segments and infinite lines remain distinct types. A plane's declared defining points do not prove arbitrary coplanarity or equality with another plane.
- Polygon/polyhedron/pyramid/prism topology uses the existing ordered vertex and solid declarations. Multiple solids and shared objects must retain scope. RequestContract remains the legacy public analyze contract until a compatible migration is demonstrated; do not force the target into its single `solid_topology` field.
- Given facts retain source references; constructed entities retain producer/dependency references; derived facts retain the trusted rule and parent facts. A representable entity/relation is not necessarily executable.
- A source reference identifies the extraction field and every exact half-open occurrence in the original source, using Python Unicode code-point offsets. It does not select one occurrence silently or assert that a quote is a valid premise. Whitespace/source identity checks happen before model normalization. Reference records are immutable and are absent on refused extraction.
- Grounding/certification must not be inferred from a model's `role`, source-shaped strings, schema acceptance or a source-span count. Geometry verification belongs to the existing source gate/engine.
- Canonical ownership and provenance must survive into plan, IR and Scene3D. Structural equality of labels is not a theorem of geometry.

Existing perpendicular/parallel/intersection relations execute only through their verified contracts. Tangency, concentricity, inscribed/circumscribed relations, curved and composite objects require mathematical verification before an end-to-end support claim. No placeholder relation may be treated as solved.

## Planner and primitive acceptance

The planner must backward-chain from goals through Registry effects, reuse available producers, form an acyclic dependency graph, order construction, and refuse missing preconditions or exceeded budgets. Every selected primitive must be independently checked by the engine; source-policy violations are terminal. No family ID, case ID, expected answer or copied whole-family script may control planning.

Recomposition evidence must show shared primitives across different topologies, distinct dependency chains, reuse rather than duplicated construction, safe unsupported/degenerate refusal and engine rejection of a tampered plan. Gold TypedFacts and replay are deterministic-planner evidence; they are not evidence of live Vietnamese understanding.

## Unified sanity and refusal boundary

Reuse the current typed codes and classifier. Preserve distinctions between absent premise, unknown entity, ambiguous reference, unsupported capability, geometric inconsistency, impossible/degenerate construction, source/ownership violation, resource exhaustion and internal error. A timeout or provider fault is not a mathematical contradiction. No invalid request may bypass grounding through a compatibility fallback. Refused output must not carry a served scene or an invented answer.

## Scene contract

The renderer derives no mathematics. Stable object IDs, canonical formula/entity mapping, typed provenance, labels without internal names, causal explanations, construction dependencies, edge ownership, visibility and highlight semantics, and forward/backward formation metadata must follow verified geometry. Keep W4 exact section-edge justification and existing perpendicular witnesses. Do not add narration-only construction events.

## Migration and retirement

Track `OLD_COMPONENT -> NEW_OWNER -> MIGRATION_TEST -> LAST_CONSUMER -> REMOVAL_STATUS` in the task run. Migrate verified capabilities and preserve meaningful regressions before removing code. Do not remove exact algorithms, active public contracts or historical evidence. At cutover there must be one production orchestrator, and every production entry point must demonstrably reach Hybrid; a mode-name change alone is insufficient. Unmigrated legacy orchestration remains explicitly active until the acceptance gates pass.

All 20 gates in `../MIGRATION_CHECKLIST.md` remain required. Reassess stale entries against code/evidence without weakening their acceptance purpose. Real-text independent extraction, differential correctness, reliability, latency, token usage/cost where measurable, API compatibility, new candidate freeze, T0/T1/T2, clean detached Full T3 and independent architecture review are required before production cutover. Missing measurements are UNKNOWN/NOT_MEASURED, never zero. No live budget is currently authorized.

## Evidence and final verdict

W4 closure and safe cleanup are recorded in `../evaluation/geometry/runs/geometry-generalization-and-pedagogical-construction/integration/`. New evidence belongs to the Master task run; old oracles/receipts remain unchanged. W4 publication approval does not exempt new blobs. Integrate only with exact publication checks, non-force push and live SHA read-back.

`HYBRID_REMOTE_VERIFIED_LEGACY_RETIRED` requires actual production replacement in the declared scope, retirement of the corresponding legacy paths, every acceptance gate, and verified remote identity. Otherwise report `HYBRID_READY_FOR_OWNER_REVIEW` or `HYBRID_NOT_READY`, with precise remaining work; use `PARTIAL_MIGRATION` when only part has migrated. The Master Epic continues without phase-by-phase technical approval, subject to the Owner's stop boundaries.
