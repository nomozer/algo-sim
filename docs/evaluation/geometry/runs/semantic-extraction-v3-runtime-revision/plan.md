# Semantic Extraction v3 runtime revision plan

Owner spec: `GO_RUNTIME_RECOVERY_AND_OFFLINE_REVISION`, 2026-10-18 (session attachment); continuation of 7168d269.
Execution: inline RED/GREEN; one independent read-only reviewer for the completed revision.

## Preflight and boundaries

Branch `research/semantic-extraction-v3-runtime-revision`, start 7168d269, initially clean. One new worktree, explicitly
authorized from this checkpoint. CORE correctness/runtime repair plus SUPPORTING offline verification; no new extractor.
Baseline at identical source: backend 10455, frontend 1079, targeted 394 passed; preserved earlier receipts retain their own commit.
Reuse `_SAU_HOP_LE`, `_bo_cum`, `_vung_hoi`, existing flat/v3 harness, frozen scorer/executor, protocol preparation helpers,
candidate freezer and T3. No new parser/solver/schema dependency. Existing call sites and CODE_INDEX searched.

Files: Registry regex, schema-contract runner/tests, bounded offline launcher/tests, this run's preparation/preregistration,
review/evidence files, candidate manifest and CODE_INDEX/EVIDENCE_INDEX. Existing run inputs/reports remain byte-unchanged.
No Planner, Engine, PlanningContract or frontend source edits. No main/other worktree edits, live requests or integration.
Cache125, `LLM_ONLY`, default flat remain. Candidate and runner identity must change. No scorer/prompt/schema/gold/oracle semantics change.
Risk: preserve regex language and rejection boundaries; no timeout becomes a geometry refusal; keep split order/identities exact.
Stop on unrelated defects. h07 source/span was exposed during diagnosis; old held-out is reused diagnostic material, not fresh blind evidence.

## Tasks and checks

- [x] Revalidate task/start/cwd/output; preserve log; attempt non-forced stop, then exact verified forced tree stop; verify zero survivors.
- [x] Write/run bounded synthetic regex regression (whitespace, nonmatch, long Vietnamese/punctuation/Unicode, valid endings and invalid operands).
  Make the smallest semantics-preserving regex correction; rerun safety/grounding tests. Preserve RED/GREEN receipts.
- [x] Write/run split-call tests (12 dev / 24 held-out, both arms, GOLD/replay, preserved source order, failure isolation).
  Filter before route processing and GOLD reference scoring; keep full artifact identity. No frozen scorer/executor edits.
- [x] Add bounded sequential offline execution with actual child exit/duration/identity/receipt validation; test failure and timeout handling.
- [x] Assemble a new protocol using unchanged source/gold/oracle/scorer and new product/runner identity. Keep one-time lock and review gates.
- [x] Commit code, freeze candidate, obtain independent read-only review; fix only verified in-scope findings, then lock the revision.
- [x] Verify old task absent; run eight offline invocations into new destinations, stopping on first failed/incomplete receipt.
- [x] Verify identities and results; run final authoritative T3 by temporarily detaching this same clean worktree at the final candidate commit.
  Return to revision branch; commit report/receipts with measured-commit attribution. Do not create a second verification worktree.
- [x] Stop at `GO_LIVE_PILOT_REQUIRED`. No approval file; no merge/push. Keep both worktrees while approvals are pending.

Cleanup plan: retain original lock/attempt and this revision while live/integration decisions are pending; remove the revision worktree
only after an explicitly approved integration and a clean-state check. No automatic worktree removal in this task.
