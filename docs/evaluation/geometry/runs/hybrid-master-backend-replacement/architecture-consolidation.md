# Phase B — orchestration overlap, identity/provenance and planner recomposition

Read from the code at `e9c9b8e9` and later commits; 0 provider calls.

## Backend call graph (as is)

```text
POST /api/analyze ─┬─ HYBRID_V2_LOCAL=offline-replay ∧ loopback (declared gate, before any cache)
                   │     prepare_local_replay → Route D cache (ROUTE_D_CACHE_POLICY) ─hit→ stored /4 response
                   │                          └miss→ run_hybrid_offline: extract_typed_fact_next_v2 (TypedFactNext /2)
                   │                                 → run_typed_fact_next_v2_route → bridge_v2 → lap_ke_hoach (planner)
                   │                                 → engine (Source Gate kiem_nguon + exact kernel) → build_adapter4_response
                   └─ default: LLM_ONLY cache (normalized key, CACHE_VERSION[:fp]) ─miss→ run_pipeline
                          stage_semantic_analyze (LLM) → quyet_dinh_dinh_tuyen (compiler C: DISABLED under LLM_ONLY)
                          → stage_semantic_program (LLM, ≤3) → contract/static/grounding/coverage gates → interpreter
                          → geometry kernel → checkers/postconditions → scene3d
POST /api/preview/hybrid (operator only) → hybrid_preview.run_preview → run_ai_fact_route (flat facts)
                          → run_fact_route → planner → engine → adapt_result
```

## Overlap audit (three orchestrators)

| responsibility | LLM_ONLY | compiler C | Route D | single authority? |
|---|---|---|---|---|
| Source reading | LLM analyze + grounding gate | reads `RequestContract` (no text) | SG-3 Source Gate `registry.kiem_nguon` over verbatim quotes | **No.** There are two source authorities by design: LLM_ONLY grounds IR names, Route D grounds clauses. They merge only when LLM_ONLY retires. |
| Program/plan production | LLM synthesis | family compiler (`SUPPORTED_FAMILY*`) | Registry effect planner | **No.** These are the three producers that cutover reduces to one. |
| Exact geometry | `semantic_program` interpreter + `simulation/geometry` kernel | the same, via `SemanticProgramSpec` | the same, via `ir_builders` → interpreter | **Yes:** one interpreter, one kernel. |
| Scene formation | `simulation_state` → `scene3d` | same | same (`adapter4_route` wraps, carries) | **Yes.** |
| Vertex identity | names in IR | `GeometryFactGraph` | `typed_fact_next.canonical_vertex_ref` (Task 1 removed the bridge copy) | **Per route.** No shared identity crosses routes, because the routes never exchange objects. |
| Cache | normalized key + route fingerprint | same table, fingerprint `CACHE_VERSION:fp` | own namespace + `ROUTE_D_CACHE_POLICY` (D-02) | Isolated two-way, with tests. |

**Removed:** the bridge's private identity copy (Task 1).

**Kept, with reasons:**
- The preview flat-facts contract and the /4 TypedFactNext contract are two **input contracts** into the same `run_fact_route` → planner → engine. They are not two geometry authorities. Removing either changes a locked product contract: the preview fixtures, `HYBRID_PREVIEW_FRONTEND_CONTRACT.md`, and the /4 reader in the frontend.
- Compiler C stays, opt-in and disabled. No offline parity corpus exists in both `RequestContract` and TypedFactNext form.
- Adapter /3 stays, because it is the only owner of curved solids.

**No fourth orchestrator and no second planner were added.** Phase A extended the existing `HYBRID_V2_LOCAL` boundary.

## Canonical identity and provenance (extraction → Scene3D)

| property | lock |
|---|---|
| Exact source spans for every quote (Unicode code points, overlaps included); none on refusal; not provider-suppliable | `test_typed_fact_next_extraction.py` (Task 1) |
| Spans survive into the execution receipt (offsets only) | `test_hybrid_offline.py::test_receipt_carries_exact_source_spans_for_every_quote_and_none_on_refused_extraction` (Phase B) |
| One identity resolver: same label in different solids is ambiguous; qualified and derived namespaces resolve through the parent chart | `test_typedfactnext_planner_bridge.py::test_bridge_ownership_resolves_identity_through_the_one_canonical_resolver`, `test_unified_solid_scope.py`, `test_target_grammar_identity_recovery.py` (S8 mutant) |
| A qualified constructed point keeps its producer identity | `test_typedfactnext_planner_bridge.py::test_qualified_constructed_point_keeps_its_verified_producer_identity` |
| Ownership is proved before any capability exit (CIC-D1) | `test_target_grammar_identity_recovery.py::test_capability_exit_cannot_bypass_semantic_validation` |
| Each premise call carries its source quote into the plan (`calls[*].source.quotes`); planner-derived calls are marked `binding=AUXILIARY`, `provenance=DERIVED` | `recomposition-evidence.json` (observed), route tests |
| Scene labels come from source names, not machine IDs | `test_display_identity_source_names.py` |
| Invalid ownership, ambiguity and missing references are typed refusals on `/api/analyze` opt-in | `test_hybrid_route_d_cache_and_rollback.py` (`UNKNOWN_SOLID_ID`, `AMBIGUOUS_REFERENCE`, …) |

**Contract gaps, recorded and not served:**
- Composite solids beyond explicit shared faces.
- Curved solids on /4.
- Identities across routes.
- Source spans are not yet carried into the /4 HTTP response, which is a frontend contract. They exist in the receipt.

## Planner recomposition: what kind of "planning" each case is

**Evidence:** `recomposition-evidence.json`, produced by `tools/recomposition_evidence.py` on independent payloads: the measurement-probe pyramid, and the right prism from the locked fixture.

| category | where it actually happens | evidence |
|---|---|---|
| **A. Goal-directed primitive composition** | Point–line distance. The planner decomposes the goal into `orthogonal_projection_line` (an auxiliary producer, `mg1_aux`, marked DERIVED) and then `ask_length`. The same decomposition runs on the pyramid and on the prism. Section planes go through `_EffectResolver` effect search (depth ≤ 3, candidates ≤ 8). | recomposition receipt; `test_goal_directed_function_composition.py::test_producer_and_goal_contracts_compose_without_a_pair_rule`, `::test_depth_bound_separates_single_and_multi_step_composition`, `::test_a_typed_need_depending_on_itself_is_a_cycle`; `test_contract_driven_goal_composition.py::test_ablation_goal_and_producer_contracts_and_registry_reversal` |
| **B. Section-specific handwritten orchestration** | Section closure (`engine` "THE section-closure authority", `_dinh_cat_canh`, the lateral-edge rule) | engine docstrings; W4 section tests |
| **C. Family compiler dispatch** | Compiler C only (`SUPPORTED_FAMILY*`). Route D's planner has 30 solid-kind references, which map solid declarations onto Registry solids. Question planning does not dispatch on family. | `planner.py` grep; recomposition receipt (the same `ask_*` primitives on both topologies) |
| **D. Schema/bridge normalization** | Most of each plan: premises become 1:1 calls (`pyramid`, `regular_polygon`, `perpendicular_line_plane`, `segment_length`, …) | recomposition receipt (the premise prefix of every plan) |
| **E. Exact execution verification** | `ask_*` primitives measured by the exact kernel, cross-checked by the engine; tampered certificates refused | `test_contract_driven_goal_composition.py::test_area_certificate_tampering_refuses`; D-05 |

**Measured answers to the Owner's questions:**
- **Primitives reused across families: yes.** `ask_distance_point_plane`, `ask_length`, `segment_length` and `orthogonal_projection_line` are shared by the pyramid and prism plans.
- **Goal decomposition into a dependency graph: yes, but shallow.** Measured: 1 derived step for point–line distance, and up to 3 for section planes. The other 9 of the 10 pyramid questions are a single kernel primitive over premise facts.
- **Producer selection by typed needs/effects: yes,** on the section path (`_EffectResolver`), and locked by the ablation test above.
- **Intermediate reuse: yes.** In the two-goal plan (d(A,(SBC)) and d(A,SC)) no identical call is built twice; premise producers are shared.
- **Cycle prevention: yes,** with `DEPENDENCY_CYCLE` and `DANGLING_DEPENDENCY` (`test_hybrid_wave1_dependency_planner.py::test_dependency_cycle_rejected_fail_closed`).
- **Pre/postconditions: yes.** Each call is checked by the engine and Source Gate, and source-policy violations are terminal.
- **Hardcoded family templates: not in question planning.** Solid declarations map to Registry solid primitives.

**Honest bound:** this is a **bounded effect planner with shallow decomposition**, not general-depth geometric reasoning. No failing case in this epic's independent probes shows a planner abstraction gap. The measured refusals are grammar (B01, B34–36), a kernel limit (A06), and out-of-contract curved solids or nested radicals. So no planner change is made. Phase B item 8 says not to add features without a failing case.
