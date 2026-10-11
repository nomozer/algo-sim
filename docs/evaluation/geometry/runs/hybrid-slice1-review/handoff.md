# Hybrid B slice 1 review: handoff and integration procedure

Status: `HYBRID_SLICE1_INTEGRATION_AWAITING_APPROVAL`.
Next action: `HYBRID_SLICE1_MAIN_INTEGRATION_APPROVAL_DECISION` (the user's).
LIVE GEMINI CALLS = 0. PRODUCTION DEFAULT = `LLM_ONLY` (cache 125).

## 1. Summary

| Item | Value |
|---|---|
| Findings | Critical 0 · Important 2 (both fixed in `62f0b18e`) · Minor 6 (3 fixed, 3 recorded) · 2 pre-existing issues recorded — [`report.md`](report.md) §2 |
| Forgery | none found: route A has no declaration path, facts JSON is `extra="forbid"`, and tampered declarations are refused |
| Benchmark | 19 / 9 / **0** / 2, both evaluations; only B26 differs from the pre-change baseline |
| Candidate | `dda3a884…` (product `62f0b18e`, refreeze `9da4e853`), divergence declared; locked A/B `12da4768` untouched |
| Provider surfaces | unchanged (A `1e3f71ea…`, B `a4f368cb…`, declarations `41e090cd…`, pinned) |

## 2. Verification

| Check | Result |
|---|---|
| RED for the review findings, at `0e28d2f3` | 17 failed, 46 passed ([log](red-at-0e28d2f3.txt)) |
| `test_hybrid_goal_decomposition.py` | 68 passed (14 source mutants killed) |
| Hybrid / function-route cluster | 657 passed, 4 xfailed (B27, B28 × 2) |
| Benchmark re-measure (scratch directory) | rows byte-identical to [`after/metrics.json`](../hybrid-goal-decomposition/after/metrics.json) |
| Candidate `--verify` | exit 0 at `9da4e853` |
| T3 in a clean detached worktree at `72381252` | **FULL_PRODUCT_GATE_PASS**: pytest 8362 passed, 0 failed (1 skipped, 2 deselected, 4 xfailed); vitest 1051; build; demo replay; crash surface |

**Clean-up:**
- Registered worktrees: 2 → 3 → 2. `slice1-review-verify` was removed without `--force` after its `node_modules` junction was taken out with `rmdir`; the junction target is intact. 1 700 544 873 bytes freed.
- The research worktree is kept until integration, and its test-generated `backend/algosim.db` was removed.
- `.superpowers/worktrees/geometry-library-expansion` is unregistered: about 551 KB, owned by CodexSandboxOffline. It still needs an administrator; I did not change any ACL.

## 3. Integration plan (only after your approval; no PR)

`main` = `origin/main` = `548066a8` is the merge-base of the research branch, so `main` can be **fast-forwarded**: no merge commit, no rebase, no cherry-pick.

**Product files that change against `main`** (all on the Hybrid route, which the default `/api/analyze` route does not reach):
- `backend/app/ai/function_route.py`
- `backend/app/simulation/geometry_functions/{engine,planner,registry}.py`

Everything else is tests, scripts, docs and evidence.

In the main checkout (`D:\Documents\projects\algo-sim`, on `main`):

```powershell
git status --short                       # expect only: ?? frontend/public/
git fetch origin                          # confirm origin/main is still 548066a8
git merge --ff-only research/hybrid-compiler-capability-audit
backend/.venv/Scripts/python.exe backend/scripts/freeze_evaluation_candidate.py --verify   # run from backend/, PYTHONIOENCODING=utf-8
git push origin main                      # only with your explicit permission
```

**After the fast-forward:**
1. Rerun T3 on `main` in a clean detached worktree.
2. Record the integration in a docs commit, as in the main-integration run.

**Branch and worktree clean-up after a successful integration** (no `--force`):
- `git worktree remove .superpowers/worktrees/hybrid-compiler-audit`, then `git worktree prune`.
- `git branch -d research/hybrid-compiler-capability-audit`. This works only once the branch is merged.
- Keep `docs/real-model-e2e-readiness` and `feat/real-model-pilot-tooling`. The latter has one unpushed commit that records the only live run.

## 4. GO / NO-GO

- **Fast-forward `main` with slice 1 + review fix (offline): GO**, on your approval. T3 passes at `72381252`, and the candidate is verified and declared.
- **Real-model claim / pilot: NO-GO** (not measured).
- **Slice 2 (B27), B28, general goal-directed search: NO-GO** (not approved).

## 5. Open

- `ISSUE-ARCH-HYBRID-AUXILIARY-POINT-LIMITS`:
  - one wording only;
  - coinciding or redundant feet;
  - the auxiliary name can appear in refusal details;
  - `lap_ke_hoach` defaults the text to "".
- `ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK`: other `ask_*` paths, pre-existing, in routes A and B.
- `ISSUE-ARCH-ENGINE-CENTRE-LABEL-EXHAUSTION`: pre-existing crash.
- `ISSUE-ARCH-HYBRID-COMPILER-NO-GOAL-COMPOSITION` (B27) and `ISSUE-ARCH-HYBRID-SOURCE-CUE-CENTRE-OF-SQUARE` (B28).
- `ISSUE-ARCH-ORBIT-P1-SECTION-SCENE-DOES-NOT-SETTLE`: P1 on `main`.
