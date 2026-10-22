# Backend Hybrid architecture decision — Session 1 continuation

Authority: `GO_BACKEND_HYBRID_LOCAL_CONTINUATION_ONLY`. Source baseline `43247c9e`; inherited product `8b5916e7`; corrected product `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee`. No production activation, provider calls, merge or push.

## Actual route inventory

| Route | Semantic extraction / input | Source authority / planning | Engine → Scene3D |
|---|---|---|---|
| Production | `ai/pipeline.py` LLM_ONLY → SemanticProgram | semantic source/assumption gates; LLM supplies bounded program | interpreter + exact kernel → simulation_state → scene3d |
| D-A research | `ai/function_calling.py` → calls | `registry.kiem_nguon`, LLM chose calls | `engine.dung_tu_loi_goi` → `function_route.run_function_route` |
| D-B research | `ai/fact_extraction.py` → TypedFact | `planner.lap_ke_hoach`; Registry Source Gate checks emitted calls | same exact engine, witnesses, quantity/goal classification |
| D-Next bridge research | authored `typed-fact-next/1` → `typed_fact_next_bridge.bridge` → TypedFact | same planner, same Registry gate | `run_typed_fact_next_planner_route` → same Scene3D, then declared unit/plane identity checks |
| Adapter /3 research | authored TypedFactNext | `_Adapter3Compiler` maps premises and decomposes planes itself; substring quote/number checks | builds `_Dung` directly, two-phase IR folding; curved route separate |

There is **no `/api/chat` endpoint in this candidate** (`backend/app/main.py`); the actual product entry is `/api/analyze`. `flat` is unchanged. `/api/preview/hybrid` remains a guarded operator route. The new bridge is an offline callable, not a new production HTTP endpoint.

## Decisions

| Capability | Decision | Evidence / scope |
|---|---|---|
| Polyhedral TypedFactNext → existing planner/Registry/engine | INTEGRATABLE_NOW | bridge + `test_typedfactnext_planner_bridge.py`; source-gated relation-plane cuts and derived pyramids, no fallback |
| Wave 3A exact volume ratio/residual over certified declared/derived solids | INTEGRATABLE_NOW | `engine._Dung`, ratio and residual certificates; existing `test_wave3a_volume_reasoning.py`, `test_wave3a_adapter3_integration.py`; no fabricated residual mesh |
| Ratio coefficient ownership and group event births | INTEGRATABLE_NOW | shared `_ty_so_khop`/coverage in Registry; `_validate_scene` reads `object` and `objects`; control/tamper tests |
| Internal bridge identity/unit constraints | INTEGRATABLE_NOW | preserve declared metadata; reject unknown namespaces/local vertices; invalid Any args refuse; compare source-gated section label; explicit `a` with numeric-only facts refuses `BRIDGE_UNSUPPORTED_LENGTH_UNIT` |
| A shared `cut_edges` meaning across bridge and Adapter /3 | REQUIRES_CONTRACT_CHANGE | same JSON has different semantics; inherited and fresh 60-case evaluation both find 18 wrong Adapter /3 numeric cases with bridge-style payloads |
| Full TypedFactNext as sole input, all Adapter /3 outcomes preserved | REQUIRES_CONTRACT_CHANGE | TypedFact remains planner input; qualified identity collisions, frames, curved geometry and presentation outcomes need migration/compatibility decisions |
| Live extraction into Next / production Hybrid | NOT_YET_SUPPORTED | no live authorization/evidence; default remains LLM_ONLY/flat; migration gates and owner GO absent |
| Two-line relation plane **with new cut clause**, derived prisms, independent frames, curved planner, plane equation bridge | NOT_YET_SUPPORTED | existing bridge/gate refuses; two-line planes without this cut slice existed before Session 1 |
| Residual frustum/polyhedron Scene3D mesh | NOT_YET_SUPPORTED | exact scalar relation exists; no verified residual topology operation in this slice |

## Answers supported by source

1. TypedFactNext is **not** a unified sole contract. It is an authoring contract bridged to TypedFact on a bounded subset, alongside the independent Adapter /3 compiler.
2. Planner has a real dependency DAG (`_sap_xep_phu_thuoc_loi_goi`), typed goal producer selection (`_EffectResolver`) with depth/need/candidate/call/foot budgets and memoization. New cut-vertex selection is deterministic cost-ranked case analysis, not general search. Existing input normalization and call deduplication are reused. No claim of unconstrained recomposition.
3. Adapter /3 is **not wired behind this Planner**. Bridge scenes use the existing function-route scene builder. Fresh intersection labels are hidden and redundant operand planes non_visual by deterministic presentation postprocessing (`_an_dinh_thiet_dien_phu`), not planner inference. Provenance resides in calls/source quotes, auxiliary certificates and engine trace; bridge does not emit every Adapter /3 derived_identity/simulation_goal outcome. Structural scene validity is not browser/UI acceptance.
4. Wave 3A ratio/residual functions are actual registered and certified engine capabilities, reused by both research routes and now on planner-derived pyramids; broader composite/curved scene semantics remain separate.
5. Development results are unchanged by the Codex safety fixes (fresh replay); new malformed/identity/unit constraints refuse rather than serve. This is bounded regression evidence, not proof of equivalent NLP/scene behavior across routes.
6. No frozen provider schema or version was changed by Codex. Claude had advanced internal Registry /12, Planner /12, Engine /10; TypedFactNext /1, Adapter /3, provider fingerprints and cache127 remain. Fixes tighten boundary validation within the approved contract. Contract proposal below remains unimplemented.
7. Production blockers: live extraction quality/evidence, split source authorities, cut_edges ambiguity, qualified/multiple-frame ownership, missing goal outcomes on bridge, resource limits, migration checklist and separate owner enablement.

## Contract proposal (decision only, no implementation)

Pin section input roles separately: source-stated edge constraints versus a complete geometric section boundary. Prefer additive explicitly named fields in a versioned TypedFactNext successor and a corresponding Adapter successor; do not silently reinterpret `/1.cut_edges`. Closed-boundary construction must verify every required edge/intersection and preserve source provenance. Old `/1` payloads retain their route-specific legacy meaning and must be rejected at an automatic cross-route boundary until explicitly migrated. Migrate fixtures with a declared route/version, dual-run against independent exact oracles, compare identity/ownership/goal outcomes, preserve old consumers, then seek owner contract GO. Solid-qualified canonical IDs/frames and full simulation goal outcomes need a separate explicit compatibility mapping. No version bump, adapter rewiring or new family is authorized by this proposal.
