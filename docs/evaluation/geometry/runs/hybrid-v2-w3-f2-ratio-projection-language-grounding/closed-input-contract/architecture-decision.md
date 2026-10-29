# Closed input contract — architecture decision

Owner GO HYBRID_V2_W3_F2_CLOSED_INPUT_CONTRACT_AND_LEGACY_OWNERSHIP_SAFETY, 2026-10-29.
Continuation at 5e44d5da434b1d1a8fd98a0f1f4527f40de3c6ed. CORE correctness repair, tests/evidence SUPPORTING.
Owner supplied remote main 996f114b3480efe1b0d075dd4342530aaa12ddae; same local main/origin/main; main ancestor of research HEAD.
Working tree before continuation: only the three audit files; preserve them byte for byte. No external provider calls.

## Decision and reuse

Extend typed_fact_next.py as canonical owner of kind-field and target-shape registries. No new product module/dependency.
Reuse _ARGS_LOI/_hinh_dung, parse_qualified_ref, resolve_solid_name, scope_records, _derived_parents and constructed-name discovery.
Bridge ownership preflight must run before every capability refusal; legacy fallback inherits semantic validation.
Adapt its existing propagation to qualified/canonical identity and named section points; a namespace never grants ownership.
Adapter /3 consumes the same resolved measurement scope; derived scopes resolve through declared lineage and verified constructed membership.
Curved dispatch runs namespace, existence, ownership and relation preflight; unsupported relations receive a typed capability refusal.
No curved geometric capability is added. Preserve curved controls with no unsupported relations and structural identity/root-frame controls.

allowed-fields.json is the preregistered policy snapshot. Runtime registry lives in typed_fact_next.py and must equal it.
Optional solid/section scope assertions retain their existing ownership meaning; target_refs are ownership assertions on simulation goals.
Explicit presence comes from model_fields_set, never all fields of a default-filled dump. Conversion uses exclude_unset to retain presence.
Raw references/quotes stay on the payload; downstream uses validated operand views rather than deleting scope/provenance from the payload.

## Boundaries and risks

Only typed_fact_next.py, typed_fact_next_bridge.py, adapter3_simulation.py, tests and run-local tooling/evidence may change.
No Planner/Registry/engine/kernel/radical/renderer/UI changes. CACHE_VERSION 130; DEFAULT_MODE LLM_ONLY; Hybrid opt-in; ALLOW_LIVE_AI=0.
No history rewrite/merge/push/cleanup. Avoid schema-to-Bridge import cycle: ownership remains in Bridge, called before capabilities;
schema owns declaration/field/shape validation. Deep checks reuse the same registry and enumeration, not independent field policies.
New public guard/helpers are required only where existing helpers erase scope or conflate capability and semantics; extend existing ones first.
Stop for out-of-scope product edits, locked-contract conflicts, Gate A failure or independent review BLOCKER/MAJOR. No automatic post-review repair.

Existing source of truth: active TypedFactNext contracts, code/tests, Owner GO. Baseline results: baseline-head.json (203 probes),
previous review raw probes, old closure evidence. Current measured product fbd8c1da54dc3fbafe1c3b4603417fc8b8ed22f5a1d8297bfac521da7b584b31 (118 files).
