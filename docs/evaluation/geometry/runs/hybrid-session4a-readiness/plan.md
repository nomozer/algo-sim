# Backend Hybrid Session 4A implementation plan

**Goal:** Reconcile Session 3 evidence, audit bounded planning, prepare offline extraction replay and an independent holdout protocol, and make four separate release decisions.
**Architecture:** Audit the pinned Session 3 candidate in a clean detached worktree. Keep reports and offline tooling on a new branch from local main; do not integrate product changes.
**Tech stack:** Existing Python venv, pytest, Git, standard-library receipt tooling.
**Spec:** Owner's attached `ALGOSIM — BACKEND HYBRID SESSION 4A` request, P0–P7.

## Constraints and preflight

- Active branch: `research/hybrid-session4a-readiness`, base `f10e6283dd3fd2cfdef189e1bef0ffdecf2be942`; new task, W1 in metadata.
- Original workspace: `research/hybrid-wave3a-volume-reasoning` at `fe9f555437498432427ae6bbd54402cdd59c7eb7`, with pre-existing untracked files; preserve all.
- Classification SUPPORTING: smallest offline tooling and evidence needed for geometry thesis readiness.
- Reuse `adapter4_route.run_typed_fact_next_v2_route`, `parse_typed_fact_next_v2`, existing source gate, Scene3D validator, freeze helper and historical receipts. No parallel geometry implementation.
- Source of truth: pinned source/tests and immutable receipts; reports are interpretations.
- Expected changes: this run directory, a pointer/correction entry in EVIDENCE_INDEX, CODE_INDEX entry for replay tooling. No runtime/schema/cache/frontend/history changes; no dependency cycles introduced.
- Defaults remain LLM_ONLY / flat / NO-GO / ALLOW_LIVE_AI=0 / CACHE_VERSION=127 / MAX_MEMORY_DECLARATIONS=32.
- No merge, push, delete, live provider calls or full T3 rerun. One worker; BLAS/OpenMP threads=1.
- Stop dependent live evaluation at a written owner decision; do not fabricate extraction outputs or independent holdout completion.

## Tasks and checks

- [x] P0: capture refs, worktrees, dirty state, ancestry, trees, frontend divergence and a read-only merge analysis; report integration limits.
- [x] P1: hash receipts, recount A–H units, fuzz mutation totals, locked-set scope, Route-B refusal identities and T3 provenance; append corrections without editing old evidence.
- [x] P2: inspect goal resolver vs section-specific planning/preprocessing/kernel; lock newly authored diagnostic combinations before running; measure them as development diagnostics, never blind holdout.
- [x] P3: write replay tests first; implement local-only provider-independent replay with strict source binding and staged refusal reporting; replay eligible existing sanitized extraction data separately from authored TypedFacts seam fixtures.
- [x] P4: write role-separated, preregistered three-track holdout protocol; execution pending independent evaluator.
- [x] P5/P7: six requested reports, owner live decision, run metadata, hashes, handoff and index; targeted checks and one read-only final review.

## Review focus

Count cases separately from route invocations; missing measurements remain UNKNOWN. Never classify technical failures as mathematical refusal. Scene schema validity is not browser rendering evidence. Replay cannot measure new provider quality, latency, tokens or cost. New diagnostics authored by implementer cannot establish independent generalization.

## Execution rulings

The owner supplied a complete specification and instructed immediate execution; proceed inline without an additional design/plan approval round. User's targeted-test requirement overrides skill defaults asking for full-suite reruns. No graph exists in this checkout; use direct source/receipt inspection rather than installing or generating a repo-wide graph. Remote freshness is limited to local tracking refs unless a separate read-only remote check succeeds.

Final checks: 201 passed / 1 xfailed in targeted source/cache/candidate/replay tests; eight documentation invariants passed. Source receipt bytes unchanged, original refs/status preserved. Reviewer found no important/critical issue; its minor provenance guard was fixed and checked in isolation. Full T3/provider/browser work was not repeated. No product bug was found that required a feature patch.
