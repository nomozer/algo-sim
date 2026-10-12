# S0 + section slice review: handoff and integration procedure

Status: `HYBRID_SLICE_REVIEW_AWAITING_INTEGRATION_DECISION`.
Next action: `HYBRID_SLICE_REVIEW_INTEGRATION_DECISION` (the user's).
LIVE GEMINI CALLS = 0. PRODUCTION DEFAULT = `LLM_ONLY` (cache 125).

## 1. Summary

| Item | Value |
|---|---|
| Findings | Critical 2 · Important 3 · Minor 4, plus re-verification findings (false refusals, N1, N2, yes/no). All closed except M4 — [`report.md`](report.md) §2 |
| Residual | pre-existing gate false serves A–C and new-surface D, M4 — `ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES` (report §5) |
| Oracle | independent exact oracle, all areas and edge topologies equal (report §3) |
| Scene3D | harness with real Hybrid scenes: 6/6 load, 0 console errors, orbit/zoom/reset settle; intersection line invisible — `ISSUE-ARCH-SCENE3D-INTERSECTION-LINE-INVISIBLE` (report §4) |
| Benchmark | 19 / 9 / 0 / 2, rows byte-identical |
| Candidate | `451b046c…` (product `b3e946e9`, refreeze `542e3894`), divergence declared; locked A/B `12da4768` untouched |
| Provider surfaces | unchanged since `hybrid-section-slice` |

## 2. Integration plan (only after your approval; no PR)

`main` = `origin/main` = `a6e27a78` is an ancestor of the research branch, so `main` can be **fast-forwarded**: no merge commit, no rebase, no cherry-pick.

**Product files that change against `main`** (all on the Hybrid route, which the default `/api/analyze` route does not reach):
- `backend/app/ai/fact_extraction.py` (one extraction-prompt rule of route B; the default prompt surface is not touched)
- `backend/app/simulation/geometry_functions/{engine,planner,registry}.py`

In the main checkout (`D:\Documents\projects\algo-sim`, on `main`):

```powershell
git status --short                       # expect only: ?? frontend/public/
git fetch origin                          # confirm origin/main is still a6e27a78
git merge --ff-only research/hybrid-simulation-capability-audit
backend/.venv/Scripts/python.exe backend/scripts/freeze_evaluation_candidate.py --verify   # run from backend/, PYTHONIOENCODING=utf-8
git push origin main                      # only with your explicit permission
```

After the fast-forward:
1. Rerun T3 on `main` in a clean detached worktree.
2. Record the integration in a docs commit.
3. Without `--force`: `git worktree remove .superpowers/worktrees/simulation-audit`, `git worktree prune`, then `git branch -d research/hybrid-simulation-capability-audit`.

**Keep:**
- `docs/real-model-e2e-readiness`;
- `feat/real-model-pilot-tooling`, which holds an unpushed evidence commit;
- `research/compact-geometry-dsl`, the DSL spike. It is not for `main`.

## 3. GO / NO-GO

- **Fast-forward `main` (offline, research route): GO with declared residual risk**, on your approval. T3: see `run.json`.
- **Hybrid in the product, or a live pilot: NO-GO.** Groups C and D of the residual false serves must be fixed, and the intersection line must render.
- **Slice 2 (parallel constructions), slice 3 (wording breadth): not approved.**

## 4. Recommended next wave

Bind ask operands to the quote: every point, plane, segment and solid of an `ask_*` must be in the asked object phrase, with modifiers (bình phương, nửa, phần còn lại, khi … thay đổi) refused. Then the same for sections named twice in one quote. This closes groups C and D at one authority (`_kiem_cau_hoi`), without new blockers.
