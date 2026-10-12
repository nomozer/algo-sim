# Question-local givens implementation plan

Goal: prevent Hybrid and route A from serving an old figure when source question-local givens change its assumptions.
Authority: user request, Phase 2, 2026-10-12. Phase 1 gate: main 232c1225, clean detached T3 at 22edf7ff PASS.
Execution: implement inline; one independent LOCAL reviewer after the bounded change. No new semantic state, Typed Facts schema, provider surface, cache version or renderer change.

## Preflight

Branch research/question-local-givens, base 232c1225; tracked tree clean. CORE correctness blocker for faithful 3D geometry.
Reuse registry.kiem_nguon / clause and question grammars / exact number reader, source shape_constraint reader, planner calls and engine verification. No new solver or module. Expected source change: registry.py; tests: test_question_local_givens.py and directly affected honest regression controls; documents in this run and living context/contract.
Contract/cache/history: bounded source gate semantics only; CACHE_VERSION 125 and LLM_ONLY stay; old candidate/evidence immutable, refreeze/declaration after product commit.
Duplicate check: no existing local-given coverage gate; existing source spans and engine checks are the authorities. Dependency direction must stay registry → existing source readers, never semantic readers → registry. Stop if a second semantic state/provider schema/scoped replacement engine is needed.

## Task 1: Shared source coverage gate

- [x] Write negative route A/B tests for ignored local dimensions, narrow/broad ask quotes, repeated questions, compound givens, scope changes and altered relations. Write positive controls for matching givens and explicitly typed new consistent givens.
- [x] Run the test file on the integrated baseline and retain RED receipt (22 failed, 20 passed after correcting a test helper signature; no product change at RED).
- [x] Extend registry.kiem_nguon with transient source coverage checks: compare local assertions with the existing validated calls, preserve engine authority, refuse unread context. Never overwrite base facts or synthesize replacement geometry.
- [x] Run the new file and existing Hybrid/source gate cluster: 838 passed, 4 xfailed; benchmark/provider pins unchanged. Added RED→GREEN controls for model-omitted original facts, explicit units, question punctuation, follow-up givens and construction-only requests.
- [x] Commit the bounded source/test change (`06cd8cdf`).

Review focus: whole-question quotes must not cover unrelated assertions; short ask quotes must not hide surrounding givens; repeated clean asks must not authorize a later changed context; numeric notation/label/scale changes must preserve decisions; planner auxiliary skips must not bypass context verification.

## Task 2: Independent verification and handoff

- [x] Independent read-only LOCAL review: 3 Critical, 1 Important; executor reproduced 19 failures, fixed all in one pass; 861 passed, 4 xfailed. See review.md.
- [x] Refreeze candidate in clean detached worktree at final product commit e1f288ec (d4bc2b04); additive divergence correction, first candidate/failed gate retained; historical bytes unchanged.
- [x] Benchmark 30 unchanged, candidate/provider pins 27 pass; clean detached T3 at 678f5b7b PASS (8760 backend/1053 frontend, build/demo/crash). No model calls; renderer unchanged.
- [x] Update active contract, issue, code/evidence indexes, continuity and next action; docs audit PASS, docs/identity tests 51 pass/1 deselected. Evidence/docs staged separately from product and candidate.
- [x] Remove this turn's verification/scratch/junctions/processes; retain unmerged research checkout and all protected original refs/data. 3,564,113,243 bytes freed; 3→4 registered worktrees; no merge/push of Phase 2.

Unsupported scope changes remain refusals; supporting full scoped assumptions is a later user decision. Next proposed vertical slice: bounded multi-step construction of a plane through a point parallel/perpendicular to another plane, then section construction, using existing primitives.
