# Hybrid Route D offline preview contract

Owner scope: GO_HYBRID_ROUTE_D_PREVIEW_WIRING, 2026-10-18. Default product mode remains LLM_ONLY; response contract remains flat. Hybrid product enablement and GO LIVE remain NO-GO.

POST /api/preview/hybrid requires HYBRID_ROUTE_D_PREVIEW=1, a server-configured HYBRID_ROUTE_D_PREVIEW_TOKEN of at least 32 characters, a matching X-AlgoSim-Preview-Token header, and a loopback socket peer. Forwarded headers do not grant access. OFF returns 404 before Route D imports or work. The endpoint is excluded from OpenAPI and sends Cache-Control: no-store.

This wave implements an offline runtime only. The application owner may configure app.state.hybrid_preview_fixtures as JSON data mapping exact problem text to provider-format responses. Missing fixtures refuse safely; request bodies cannot install facts or transports. No arbitrary callable or live provider transport is configured by this API. Neither API keys nor ALLOW_LIVE_AI=1 turn this preview into a live path. Tests install finite fixture data and exercise the actual endpoint.

RoutePolicy captures the preview enablement, flat response contract and D surface identity once at request entry. D identity includes Registry, Planner, Engine, extraction surface/contract and adapter/envelope versions. The existing analyze snapshot never selects D and retains its existing cache identity. Preview has no cache calls.

The response is a versioned hybrid-route-d-preview/1 representation: the existing validated semantic envelope plus Route D metadata. The adapter reuses compile_semantic_program_to_envelope and validate_semantic_envelope_config with the exact chart metric active. It preserves the complete Geometry IR, construction scene/timeline, exact answers, provenance, planner trace and goal observations. Served results require a valid SPD chart, successful kernel check, closed dependencies and safe proof observations. Refusals preserve their machine code while learner text is selected from Vietnamese messages, never raw provider/engine errors.

Goal observations retain proof_status=UNVERIFIABLE and can_present_as_proven=false. No observed configuration becomes a general proof. length_unit is retained both in scene3d and preview metadata; a missing/inconsistent symbolic unit refuses. Preview UI is not integrated; frontend/src is outside scope.

Default-route import guards declare only the explicit preview execution and diagnostic identity boundaries. Importing main and running LLM_ONLY must still never load Route D. Diagnostic identity may load D metadata only when that diagnostic function is invoked; it never executes extraction/planning.

Acceptance: endpoint-level safety and mathematical tests, recorded baseline LLM_ONLY parity, 174 historical cases, grounding/adversarial/oracle regressions, full backend/frontend/build/demo/crash/doc gates, independent read-only review, a new freeze and authoritative clean detached T3. No main merge/push and no cleanup in this wave.
