# Handoff

Status: **READY_FOR_OWNER_REVIEW**. Read `report.md` first (11 sections).

- Branch `integration/axo-hybrid4-reliability`, worktree `.superpowers/worktrees/axo-hybrid4-integration`.
  Baseline `59ed17b4`; commits `ac71a439` (Codex work as found) → `e2f0cb90` (sample-record reopen fix, edge-case
  tests) → `5af750e8` (candidate refreeze) → docs-only evidence commit. `main` `bb61a804` untouched. Not merged, not pushed.
- Tested tree for T3: `5af750e8`, clean detached worktree — FULL_PRODUCT_GATE_PASS; node harness 0 fail.
- Seal: `freeze_evaluation_candidate.py --verify` matches (103 files `5ef50761…`). A later `frontend/src` change moves
  `product_commit_sha` ⇒ refreeze in a clean worktree, separate commit.
- Python: `D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe` (worktree has no venv). Vitest capped at 2
  workers in `vite.config.ts`. Run heavy suites one at a time.
- Pre-existing untracked artifacts of earlier runs (`perf/`, `two-tab-run-*`, `nav-after/`, `frontend/dist-*`,
  `frontend/debug.log`) are not from this task; left in place.
- Owner decisions: publication exceptions (98 pending + `28be1ef6`), merge/push, optional registered live run to
  explain the original prism screenshot warning.
- 0 provider calls.
