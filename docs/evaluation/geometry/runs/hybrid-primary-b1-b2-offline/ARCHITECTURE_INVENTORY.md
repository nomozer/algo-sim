# Architecture inventory

Baseline C0 `5ee973406b75e19503158549a22bb3b24c5d9bf5`. Owner permits development from this baseline without merging main. Official sandbox Git escalation created one isolated research worktree; root and C0 worktrees remain untouched.

| Responsibility | Reused authority | B1/B2 delta |
|---|---|---|
| Source-only extraction | Session 4A ReplayExtractor seam; existing fact_extraction build_request/parse_response; function_calling._openapi | Product typed_fact_next_extraction module, injected replay/transport, no installed live transport |
| Canonical facts | simulation/geometry_functions/typed_fact_next.py::TypedFactNextPayloadV2 / parse_typed_fact_next_v2 | No schema/enum change; raw source/quote identity checked before normalization |
| Identity/grounding | Registry role helpers and kiem_nguon | Early premise-role checks; semantic completeness stays at the existing gate |
| Bridge/facts/planning | typed_fact_next_bridge.bridge_v2; function_route.chay_sau_cau_noi / run_fact_route; planner.lap_ke_hoach | Reused, no parallel parser, FactGraph, Planner or Engine |
| Exact geometry | geometry_functions.engine, exact kernel and SemanticProgramInterpreter | Unchanged; wrapper binds emitted coordinates/values/dimensions/display answers back to execution memory |
| Adapter | adapter4_route.run_typed_fact_next_v2_route, hybrid_preview validators, pipeline_adapter compiler | Product build_adapter4_response, source hash and sanitized refusal |
| Routing | pipeline.RoutePolicy / route_policy_snapshot; main._policy_identity | Internal hybrid_offline service, explicit existing research flag; cache excluded |
| Frontend | docPhanHoiHybrid, store, Scene3DExplorer | No product UI changes; new test consumes actual service wrappers |
| Evaluation | locked hybrid-contract-v2 grammar/oracle; check-adapter4-browser | Fresh service export, linked receipts and browser fixtures |

Old branch audit at baseline: semantic-extraction-v3 and its runtime-revision branch have no unique backend/app commits relative to C0. hybrid-semantic-extraction-v2 has unique product commits `fb3f4ee5` and `69fa9be8`; extraction-v2-safety has `e3827c00`. These affect earlier flat prompts/grounding, not an existing canonical V2 provider interface. None was merged wholesale or cherry-picked. Their research refs are preserved.

Product checkpoints: B1 `9b71fc3c`, wrapper `48d46bf1`, orchestration `c3c1eb80`. Only product AI-layer integration changed. Source Gate, planner, registry contracts, kernel, schema, IR budget and default endpoint are reused unchanged.
