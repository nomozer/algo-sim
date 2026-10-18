# Hybrid Route D Preview Implementation Plan

> Execute inline with superpowers:executing-plans. Each behavior follows RED → GREEN. One independent read-only whole-branch review follows implementation.

**Goal:** A controlled offline runtime preview with default product behavior unchanged.
**Architecture:** Extend RoutePolicy snapshots; put D execution/adapter behind a separately guarded API boundary; reuse the semantic pipeline adapter and exact metric context.
**Tech Stack:** Existing FastAPI, Pydantic, Python 3.12, pytest; no dependency additions.
**Spec:** docs/architecture/HYBRID_ROUTE_D_PREVIEW.md and the owner P0–P9 requirements.

## Global constraints

LLM_ONLY / flat / Hybrid NO-GO / ALLOW_LIVE_AI=0. No frontend/src edits, main merge/push, live provider calls, or deletion. Preserve every source worktree, DB, research artifact and local GO MAIN package.

## Preflight

Branch research/hybrid-route-d-preview-wiring; clean start at main=origin/main=6592306db9f8851d23bccb1ebccca60b281a35ef. CORE: connect the existing deterministic geometry stack to a preview runtime. Reuse RoutePolicy, run_ai_fact_route, KetQuaTuyen, Metric, compile_semantic_program_to_envelope, validate_semantic_envelope_config, learner_reason and existing corpora/oracles. New responsibility: versioned preview adapter/API boundary, not another planner/engine. Expected product files: ai/pipeline.py, main.py, runtime_identity.py, new ai/hybrid_preview.py. Tests/architecture/run documentation change; no default cache/schema/history change. Dependency direction remains API → AI adapter → deterministic engine. Stop for source/main drift, unauthorized live execution, irreducible verification failures or destructive actions.

## Tasks

- [ ] Record default endpoint/pipeline parity baseline and clean regression baseline.
- [ ] RED endpoint authorization/OFF/ON, snapshot, cache isolation and policy identity tests.
- [ ] GREEN minimal RoutePolicy extension, offline fixture runtime, versioned adapter and guarded endpoint.
- [ ] RED/GREEN proof/unit/metric/dependency and mathematical/adversarial endpoint tests.
- [ ] Explicit import guard boundaries and runtime identity tests; run cache/contract/174/grounding/oracle regressions.
- [ ] Update live documentation, frontend handoff and preservation inventory; independent read-only review and fixes.
- [ ] Commit allowlisted files, new candidate freeze, clean detached authoritative T3, exact final handoff. Never merge/push main.

## Review focus

Unauthorized forwarded clients, env flips during a request, forged proof flags, incomplete scene dependencies, and symbolic dimensions must fail closed or preserve the original request snapshot. No fixture/network callback is accepted from clients. Exact default parity is checked against a hash recorded before product edits.
