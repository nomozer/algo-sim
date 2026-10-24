# Claude takeover checkpoint

Authorization: `GO_HYBRID_B1_B2_TAKEOVER_AND_SCENE3D_VISUAL_RESEARCH_LOCAL` (2026-10-24). Claude took over the Codex B1/B2 run after Codex hit its usage limit. Shared workspace confirmed: same local repository, same worktree `.superpowers/worktrees/hybrid-primary-b1-b2-offline`.

## State found (read from Git and files, not from the Codex screenshot)

| Item | Observed |
|---|---|
| Worktree | detached HEAD `d8a22dbe` = tip of `research/hybrid-primary-b1-b2-offline`; no staged or modified tracked files |
| Codex commits on C0 `5ee97340` | `9b71fc3c` B1 extraction, `48d46bf1` Adapter /4 producer, `c3c1eb80` B2 orchestration (product commit), `97072a72` offline/frontend evidence, `795cc241` browser/migration docs, `d8a22dbe` candidate freeze |
| "Edited 24 files" | All committed. The only untracked path was `verification/full-t3/execution.json`, written by the launcher after T3 finished |
| Running processes | None from this run (only the Playwright MCP server) |
| Full T3 attempt 1 | **Completed, FAIL**, exit 1, 643.6 s, target `d8a22dbe`. pytest 11834 passed / **2 failed** / 1 skipped / 15 xfailed; vitest 1293/1293; build, demo replay and crash surface PASS. Post-T3 `--verify` MATCH (118 files, `71dd6aa6…`) |
| PASS_WITH_LIMITS | INDEPENDENT_REVIEW.md: no Critical; six Important groups fixed with RED->GREEN regressions; no second independent review of the fix diff; live quality and independent holdout not evaluated |

Attempt-1 receipt is committed unchanged at `verification/full-t3/execution.json`. Raw logs stay in ignored scratch. Their SHA-256 matches the receipt (stdout `c67d03b3…`, stderr `ccb6bf35…`).

## Root cause of the attempt-1 failure

Both failures are `tests/geometry/test_schema_contract_offline.py` watchdog tests (`test_watchdog_is_incomplete_runtime_failure_not_geometry_refusal`, `test_windows_watchdog_terminates_the_invocation_child_tree`). `backend/scripts/run_schema_contract_offline.py::invoke` calls `taskkill /F /PID <pid> /T`. Inside the Codex sandbox that call returned non-zero, so the harness raised `WATCHDOG_TERMINATION_FAILED`. Neither file is in the B1/B2 diff (C0..d8a22dbe). The last change to them was `da5b407d`, which predates C0.

Re-run outside the sandbox on the same candidate tree: `pytest tests/geometry/test_schema_contract_offline.py` gives **14 passed** (both watchdog tests included). Classification: environmental (sandbox process-tree ACL), not a product or B1/B2 defect. No test or harness was edited.

## What Claude takes over

1. Re-run authoritative Full T3 once, outside the sandbox. It runs on a clean detached checkout of this docs-only commit, which changes no `MEASURED_SYSTEM_PATHS` (the candidate hash must still match). The receipt goes to `verification/full-t3-rerun/`, because attempt 1's directory cannot be reused (Codex ACL).
2. Write FINAL_OWNER_HANDOFF.md and run.json (Codex had not created them).
3. Scene3D visual-reference research (owner P3). It is isolated from the B1/B2 candidate and must not alter it.

## Report name mapping (no duplicate reports)

| Requested name | Existing authoritative file |
|---|---|
| HYBRID_B1_B2_IMPLEMENTATION_REPORT | ARCHITECTURE_INVENTORY.md + ADAPTER4_WRAPPER_INTEGRATION.md |
| NL_EXTRACTION_V2_STATUS | NL_TYPEDFACTS_V2_IMPLEMENTATION.md |
| HYBRID_BACKEND_ROUTING_REPORT | HYBRID_BACKEND_ROUTING_REPORT.md |
| OFFLINE_E2E_ACCEPTANCE | OFFLINE_E2E_ACCEPTANCE.md |
| PLANNER_GENERALIZATION_GAPS | PLANNER_GENERALIZATION_GAP_REPORT.md |
| INDEPENDENT_REVIEW | INDEPENDENT_REVIEW.md |

## Open at takeover

- Authoritative T3 PASS: pending the re-run.
- Independent holdout: NOT_EXECUTED. Live extraction quality: UNKNOWN.
- Pre-existing category mismatch `NEG-per-edge-same-name` preserved (OFFLINE_E2E_ACCEPTANCE.md).
- Governance unchanged: LLM_ONLY, flat, Hybrid NO-GO, live 0, cache 127, memory 32, REMOTE_SECURITY_BLOCKED, 27 publication exceptions PENDING.
