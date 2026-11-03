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

- [x] Reconcile planner/Registry/engine contracts against the master requirements, using existing contract-driven composition tests and fresh independently authored geometry controls (`tests/geometry` incl. composition suites GREEN; `measurement-probe.json` 10/10 + 4/4 negatives).
- [x] Record family states as SUPPORTED_END_TO_END / SUPPORTED_WITH_LIMITS / REPRESENTABLE_ONLY / UNSUPPORTED with a route-specific meaning. Never elevate /3 or a prefilled payload to production /4 support (`capability-inventory.md`).
- [x] Add reusable primitives only where a concrete unsupported goal and an independent exact oracle justify them; each new behavior follows RED/GREEN and source/engine tamper tests. Keep the existing bounded effect resolver. **Outcome: none justified by measured gaps (grammar, kernel limit, out-of-contract curved/nested radicals).**
- [x] Track gaps that need a contract extension, exact construction, or certified curved/multi-object behavior; preserve served regression capabilities (gap table in `capability-inventory.md`; regression 0 transitions).

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

## Fifth continuation — curved solids on /4 (Owner option (b), 2026-10-31)

**RED baseline:** `tools/curved_probe.py`, 16 positives with hand π oracles plus 5 negatives. All refused with `BRIDGE_UNSUPPORTED_CURVED` at `23c20679`.

**Design:** one route, no new compiler. The IR (`construct_curved_solid`, `measure`) and the kernel (`geometry/curved.py`, exact `a·π^m·√b`) already exist.

1. **Bridge** `_bridge`: a curved `SolidSpec` becomes a solid fact with `solid_type` cylinder, cone or sphere, `center`/`top`/`rim`, and `radius`/`height` values (quote = the solid quote). Goals `volume`, `lateral_area`, `area` and `radius` on that solid become question facts.
2. **Planner:** curved solid fact → `curved_solid` call; questions → `ask_volume` (reused), `ask_lateral_area`, `ask_surface_area`, `ask_radius`. A `segment_length` on (apex, rim) of a cone is an ordinary premise call.
3. **Registry:**
   - `curved_solid` (construct): keywords trụ / nón / cầu; `radius` and `height` are value fields checked against the quote.
   - The new asks, with their keywords.
4. **Engine `_Dung`:** a curved solid owns a canonical pose: O at the origin, axis z, rim on x when r ∈ ℚ, top on z when h ∈ ℚ.
   - **Dimensions solved exactly:** r² from the radius; h² from the height, or from a slant SA via h² = SA² − r² (> 0, else `INCONSISTENT_FACTS`). Both stated and disagreeing ⇒ `INCONSISTENT_FACTS`. Missing ⇒ `MISSING_DIMENSION`.
   - **Emits:** IR `construct_curved_solid` plus `measure`.
   - **Certificate:** an independent closed-form value from (r², h²), compared exactly with the executed kernel value. A total area with two unlike terms ⇒ a typed refusal, never an approximation.
5. **Adapter /4:** curved scene objects pass `_validate_scene`. If they do not, fix the validator; never bypass it.
6. **Mixing** curved and polyhedral solids in one plan ⇒ a typed refusal (`MIXED_CURVED_POLYHEDRAL_UNSUPPORTED`) until a composite slice has its own certificates.

## Tenth continuation — student natural-language understanding (Owner Master Task, 2026-11-01)

Offline only; 0 provider calls. Development diagnostic, never a held-out claim. The locked live protocol, scorer, GO thresholds and 60-case corpus are not touched.

**Measured before any code change** (scratch experiments at product `fa1ed277`, re-measured by the probe below):
- SL-1: a simulation request ("Vẽ / Dựng / Mô phỏng / Cho mình xem hình chóp …", or a trailing "Vẽ hình …", "Hãy mô phỏng hình và điểm H.") is refused (`UNGROUNDED_VALUE`, `SOURCE_PREMISE_UNREAD`, `QUESTION_CONTEXT_UNSUPPORTED`) while the same givens opened by "Cho" are served. Root cause: the Source Gate's clause grammar opens a solid clause only with `cho|xét` (`_C_KHOI`), and no closed reader covers a sentence that only asks to show objects that the calls already build.
- SL-2: `typed-fact-next/2` has no honest exit. The flat contract has `ambiguous` and `unsupported`; `GROUNDED_GOAL_COMPLETENESS_CONTRACT.md` requires one. An extractor faced with "Mô phỏng điểm S là góc chiếu của hình lăng trụ xiên." can only guess or emit an invalid payload.

**Tasks:**
1. `tools/student_language_probe.py`: authored gold / adversarial extractions replayed through `run_hybrid_offline` (extraction validation → /4 → Adapter /4), with independent hand oracles; axes per case; scorer separate from extraction. Baseline receipt before the fix.
2. SL-1 in the Source Gate only: one closed simulation-request reader (verb + mentions of objects the validated calls already build), used by the clause grammar, the premise-region and the request-region coverage. It adds no fact. RED/GREEN + adversarial locks (numbers, new objects, negation, smuggled givens).
3. SL-2: additive `unresolved` entries on `/2` (closed kinds and roles), refused by the bridge with existing codes (`AMBIGUOUS_FACT`, `OUT_OF_SCOPE`) and a server-built `route-d-clarification/1` record in `route_d.refusal`. Never able to serve. Census + compatibility audit.
4. Other gaps the probe attributes, each at its own layer, or recorded only.
5. Regression (inventory replay, registered controls, all route-D suites), independent review, candidate re-freeze in its own commit, Full T3, write-back, one consolidated Owner decision point.
