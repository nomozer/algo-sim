# Hybrid V2 offline frontend consumer implementation plan

Authorization: `GO_SESSION5_HYBRID_V2_OFFLINE_CONSUMER_RESEARCH`, 2026-10-23. Task `hybrid-offline-consumer-w01`.

Goal: consume real Adapter /4 output through the existing frontend without a route or provider transport.
Architecture: extend the existing Hybrid transport boundary; preserve Scene3D and engine geometry. Use Playwright fixture injection into the product store. Reuse Session 4A's source-only extractor seam for independent scoring preparation.
Stack: existing Python venv, React/TypeScript/Three.js/Vitest/Playwright; no installations.
Spec: Owner Session 5 P0–P8 in this conversation; no additional activation authorization.

## Pre-flight

- Root branch `research/hybrid-wave3a-volume-reasoning`, HEAD `fe9f555437498432427ae6bbd54402cdd59c7eb7`; dirty frontend and untracked campaign files preserved.
- Local main verified `3f6d737529af6fc79494fc3baeb340a7ca663b10`.
- One worktree `.superpowers/worktrees/hybrid-session5-offline-consumer`, branch `research/hybrid-session5-offline-consumer`.
- Milestone: backend disabled integration; /4 consumer open. Classification CORE consumer + SUPPORTING research/verification.
- Thesis relevance: authoritative geometry consumption before NL extraction measurement.
- Reuse: `docPhanHoiHybrid`, `dungHybridView`, `kiemHybridView`, `Scene3DExplorer`, `store.loadEnvelope`, `check_adapter4_consumer.py`, Session 4A `ReplayExtractor/replay_one`, Playwright and browser runner patterns.
- Expected files: Hybrid consumer/tests, minimal derived-point inspector wording if needed, offline export/browser/scoring tools, run reports, live indexes and candidate metadata.
- No schema/provider/cache/history migration. Duplicate search: no /4 frontend consumer; /2 boundary already owns answer binding. No new renderer or runtime dependency cycle.
- Risks: section metadata mismatch, missing derived provenance, hidden final answers by existing learner UX, visibility/topology and stale scene on refusal.
- Stop conditions: forbidden live/default/security/activation change; no safe route for geometry; resource exhaustion. Remote push separately blocked by audit finding.

## Global constraints

`LLM_ONLY`, `flat`, Hybrid product NO-GO, `ALLOW_LIVE_AI=0`, no public/HTTP endpoint, no /api/analyze integration, no locked corpus/oracle edits, no merge/push. One worker, one BLAS thread. Plans stay here. Fresh result directories only.

## Review focus

Malformed or mismatched metadata must fail closed; refused results cannot keep a successful scene; DERIVED_FRESH cannot appear as source givens; partial sections cannot fill early; residual scalar cannot synthesize mesh.

## Tasks

- [ ] P0: audit 22 committed logs, hash blobs, preserve root status/disk inventory, document traceback finding without rewriting history.
- [ ] P1/P2: add failing /4 real-fixture consumer tests (identity/answer/unit/source/certificate/topology/refusal mutations); extend existing boundary only; pass old + new tests; checkpoint commit.
- [ ] P3: fresh export of locked 47-case grammar through real /4, preserve producer/input hashes and refusal envelopes; browser product store injection at desktop/compact, all served/refused cases, all construction frames, selection/highlight and section topology; selected screenshots and receipt. Fix demonstrated bugs and repeat affected checks.
- [ ] P4/P5: reuse source-only replay, implement scoring seam using evaluator-held annotations after extraction only; timing/UNKNOWN usage metadata; test negation/conditionals/inventions/coverage and three-track separation; no new blind dataset or model call.
- [ ] P7: independent fresh-context code review, targeted backend/frontend/default isolation, candidate freeze; use the same development worktree detached clean at candidate for authoritative Full T3 if feasible (never a second worktree).
- [ ] P6/P8: preserve all receipts with SHA-256; seven named reports + audit, cleanup inventory and indexes; checkpoint commits. Retain branch and worktree if useful. Report exact reclaimed bytes, never disk drift as savings.

Execution: inline continuous campaign per Owner request. Skill approval prompts are superseded by the concrete authorized P0–P8 scope. Independent review is mandatory and separately dispatched; reviewer is not a holdout curator.
