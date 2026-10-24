# Hybrid primary B1/B2 offline implementation plan

**Authorization:** GO_AUTONOMOUS_HYBRID_B1_B2_LOCAL_DEVELOPMENT (2026-10-24).
**Baseline:** C0 `5ee973406b75e19503158549a22bb3b24c5d9bf5`; main remains `9978e512a8a2a087475d792c0bd9db639c36acaa`.
**Goal:** source text -> injected offline extractor -> canonical V2 -> existing Source Gate / Planner / exact engine -> product Adapter /4 wrapper -> existing frontend consumer.
**Architecture:** reuse the canonical schema, transport parser, bridge, route, scene/envelope validation and RoutePolicy. Add a source-only extraction boundary and an internal orchestrator. Promote wrapper production from the evaluation harness into the owning product adapter. No HTTP route or parallel geometry implementation.
**Tech stack:** existing Python/Pydantic, pytest, TypeScript/Vitest and Playwright; no dependency additions.
**Spec:** owner B1/B2 request and autonomous continuation supplied in this conversation; existing V2 and frontend contracts remain authoritative.

## Constraints

- LLM_ONLY / flat / Hybrid NO-GO / live0 / cache127 / memory32 unchanged.
- No provider calls, public endpoint, push, main integration or publication approvals.
- All work occurs in this newly created research worktree. Existing research checkouts and evidence remain untouched.
- Authored replay fixtures test integration, not model extraction accuracy or an independent holdout.
- Technical failures retain their stage and never become correct geometry refusals in measurement.
- Source identity is checked before canonical schema whitespace normalization. Quotes are checked, but semantic coverage remains owned by Registry.
- Cooperative timeout/cancellation is checked between synchronous stages; it does not terminate arbitrary injected Python code in mid-call. No live transport is installed.

## Review focus

1. Dropped source goals, negation or conditions must not become a served partial solution.
2. Spoofed source text or quotes must fail before geometry execution.
3. Refusal after success must carry no previous scene, answer or unverified trace.
4. Off/default policy must not invoke an extractor, import through the default route or enter the LLM_ONLY cache.
5. Tampered scene, metric, answer binding or certificate must fail at the wrapper/consumer boundary.

## Checkpoints

- [ ] B1 extraction contract: `app/ai/typed_fact_next_extraction.py` and `tests/geometry/test_typed_fact_next_extraction.py`. Test RED, implement strict source/schema/quote validation using existing transport mechanics; run GREEN.
- [ ] Adapter /4 wrapper: extend `app/ai/adapter4_route.py::build_adapter4_response(result, problem_text)` and `tests/geometry/test_adapter4_response.py`. Test real served/refused results and corrupt result boundaries RED -> GREEN.
- [ ] B2 internal service: `app/ai/hybrid_offline.py::run_hybrid_offline(problem_text, extractor, *, policy, timeout_seconds, cancelled)` returns response plus sanitized linked stage receipt; policy helper reuses RoutePolicy. Test disabled/default/cache isolation, source-only extraction, real exact results, omission/technical errors/deadline/cancellation RED -> GREEN.
- [ ] Offline E2E exporter calls the product service for the existing locked development grammar set. It preserves the corpus and oracle, writes fresh wrappers and receipts, labels authored replay, and feeds those exact wrappers through frontend tests and browser acceptance.
- [ ] Independent branch/evidence review; fix consequential findings with regression tests. Freeze clean candidate at a dedicated commit, run Full T3 once on that candidate, then post-T3 verify. Docs-only updates do not require another T3.
- [ ] Final reports: architecture/extraction/routing/wrapper/E2E/planner/migration/security/review/handoff, run metadata and sanitized machine receipts in this run. Unknown/unmeasured evidence remains explicit.

## Interface agreement

B1 returns `ExtractionResult(payload, code, diagnostics)`; it accepts an `Extractor.extract(problem_text)` object. Replay outputs are deep-copied. Semantic completeness is checked only in the existing /4 route, avoiding a second planner run.

B2 calls B1, then `run_typed_fact_next_v2_route(payload)`, then the product wrapper builder. Route execution latency is measured as a combined Source Gate/Planner/Engine stage; uninstrumented individual latencies stay UNKNOWN.

## Git and integration

Official sandbox escalation created `research/hybrid-primary-b1-b2-offline` from C0. Git mutations use the official permission mechanism; ACLs are not changed. Checkpoints stage exact filenames only. Main and remote remain untouched. Keep the branch/worktree for owner review.
