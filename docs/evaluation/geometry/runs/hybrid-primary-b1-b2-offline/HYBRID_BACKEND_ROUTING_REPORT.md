# Internal Hybrid backend routing

`run_hybrid_offline(problem_text, extractor, *, policy, timeout_seconds, cancelled)` is a real product service. It calls the canonical extraction boundary, existing Adapter /4 route (bridge -> Planner -> Registry Source Gate -> exact engine), then product wrapper validation. It returns `HybridOfflineResult(response, receipt)`; the response can be passed directly to the existing frontend transport consumer.

`hybrid_offline_policy` reuses immutable RoutePolicy and the existing server-side `HYBRID_ROUTE_D_PREVIEW` research flag. It captures actual V2, /4 and Registry/Planner/Engine identities; it does not register a new runtime mode. A default call is disabled even if the environment flag is present: callers must explicitly supply an enabled policy. Hot identity changes refuse. No public HTTP endpoint, client activation flag or browser network caller was added. Existing operator preview remains a separate `/1` wrapper with its existing authorization contract.

No product cache is read or written. Existing main._policy_identity rejects preview policies; default policy still identifies cache127 and flat/LLM_ONLY. No automatic fallback exists. Refusal responses contain no scene, successful answers or raw exception details.

Deadline and cancellation are cooperative between synchronous stages, including a final check before release. They prevent late/cancelled results from being served. They do not preempt an injected extractor mid-call; a future live transport must enforce its own I/O timeout. This limit is explicit rather than hidden behind abandoned worker threads.

Receipts link request UUID, exact source SHA-256, policy fingerprint, extraction validation, combined Source Gate/Planner/Engine duration and Adapter validation. Separate uninstrumented engine/planner latencies are UNKNOWN. Technical extractor/provider/engine/scene failures stay technical in measurement; output/schema errors are not counted as correct geometry refusals.

Status: `HYBRID_OFFLINE_ROUTING_IMPLEMENTED`; internal opt-in only, production enablement NO-GO. Checkpoints and fresh export: see ARCHITECTURE_INVENTORY and results/offline/acceptance.json.
