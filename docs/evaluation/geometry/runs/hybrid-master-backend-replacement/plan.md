# Hybrid Backend Master Implementation Plan

> For agentic workers: use superpowers:executing-plans inline, with a fresh whole-change reviewer before integration. Continue the same Master Epic; internal tasks do not require new Owner GO.

**Goal:** complete the existing Hybrid backend and retire migrated LLM_ONLY orchestration after demonstrated production acceptance.
**Architecture:** reuse TypedFactNext /2, canonical identity/scope validation, the Registry effect planner, exact engine and Adapter /4. Extend their missing contracts; do not create parallel authorities.
**Tech stack:** existing Python/Pydantic backend and exact Fraction/Radical kernel; existing tests and frontend compatibility checks only.
**Spec:** `docs/architecture/HYBRID_BACKEND_MASTER_ARCHITECTURE_CONTRACT.md` and the Owner Master GO.

## Global constraints and review focus

Backend only; LLM_ONLY/cache131 baseline unchanged until justified migration; no hardcoded problem solution; zero live provider calls without a budget; immutable historical evidence; explicit path staging; no force/history rewriting; source verification is distinct from schema acceptance. Review repeated quotes, Unicode/whitespace offsets, qualified/derived identities, refusal leakage, reused producers and construction-order dependencies.

## Task 1: Canonical source references and one identity authority

Files: extend `backend/app/ai/typed_fact_next_extraction.py` and `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`; test `backend/tests/geometry/test_typed_fact_next_extraction.py` and an identity authority regression.

Interfaces: immutable `SourceReference(path, spans)` records on `ExtractionResult.source_references`; existing `extract_typed_fact_next_v2(text, extractor)` signature remains. `canonical_vertex_ref(payload, ref, scope)` remains the sole identity resolver; the bridge retains its typed refusal translation.

- [x] Write tests proving successful extraction supplies exact source offsets for all quote-bearing fields, repeated occurrences and Unicode/outer whitespace; refused extraction has no reference evidence; records cannot be mutated and raw later mutation does not affect them.
- [x] Run and observe RED for the missing reference API.
- [x] Extend the existing quote walker to collect immutable references while preserving its rejection semantics; return references only after full extraction validation. No provider schema or prompt change.
- [x] Replace the bridge's duplicate identity calculation with the existing canonical resolver, preserving code/detail translation. Verify qualified and derived identities through existing scope/identity suites; do not widen unsupported geometry.
- [x] GREEN: extraction, offline orchestration, bridge, ownership, locked identity and source-grounding suites. Measure offline extraction/grounding separately from live NLU.
- [x] Commit the bounded implementation and record cache/candidate/surface impact (`task1-green.json`).

## Task 2: Recomposition and capability inventory

- [ ] Reconcile planner/Registry/engine contracts against the master requirements, using existing contract-driven composition tests and fresh independently authored geometry controls.
- [ ] Record family states as SUPPORTED_END_TO_END / SUPPORTED_WITH_LIMITS / REPRESENTABLE_ONLY / UNSUPPORTED with a route-specific meaning. Never elevate /3 or a prefilled payload to production /4 support.
- [ ] Add reusable primitives only where a concrete unsupported goal and an independent exact oracle justify them; each new behavior follows RED/GREEN and source/engine tamper tests. Keep the existing bounded effect resolver.
- [ ] Track gaps that need a contract extension, exact construction, or certified curved/multi-object behavior; preserve served regression capabilities.

## Task 3: Runtime unification and migration

- [ ] Inventory production entry points, legacy synthesis calls, cache/policy identities and last consumers.
- [ ] Migrate verified capabilities into the single Hybrid orchestrator with no silent legacy fallback and compatible envelope/refusals.
- [ ] Measure baseline request count, tokens, repair attempts, latency, cost and success separately; unavailable provider measurements remain NOT_MEASURED. Benchmark any optimization before retaining it.
- [ ] Execute independent real-text evaluation only after an authorized provider budget and stop rules exist. Do not invent live evidence or coerce cutover when absent.
- [ ] Reassess all 20 migration gates. Switch production routing only on actual acceptance; then delete proven orphaned legacy orchestration with regression coverage and a last-consumer ledger.

## Task 4: Full acceptance, publication and cleanup

- [ ] Independent review answers all 15 Owner architecture questions against the actual final branch.
- [ ] Freeze a new candidate; run T0/T1/T2 and clean detached Full T3; retain hashes and product identity.
- [ ] Check exact publication range/head and current main ancestry/remote. Integrate/push non-force only when all applicable requirements pass; verify remote SHA/product hash.
- [ ] Final safe cleanup with before/after inventory; report the truthful final verdict and remaining limitations.

## Rulings

- Existing TypedFactNext /2 is the canonical request/fact representation; source references and identity indexes extend its interpretation, not a new graph/DSL or solver. The legacy `geometry_compiler/FactGraph` is not reused as the Hybrid planner.
- The Owner explicitly opted out of repeated design/phase questions; this plan implements the already authorized written architecture. A reviewer checks feasibility, not a new approval gate.
- Missing live authorization prevents production acceptance, but does not stop independent offline implementation and validation.
