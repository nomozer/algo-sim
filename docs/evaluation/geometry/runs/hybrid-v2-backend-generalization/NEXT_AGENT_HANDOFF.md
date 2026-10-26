# Handoff — Hybrid V2 backend generalization (2026-10-26)

Read `report.md` first. Post-merge facts (merge SHA, push, cleanup) are in `POST_MERGE.md` once written; if it is
missing, the merge did not finish — see "Resume".

## State

- `main` before this task: `a9889031` (pushed to GitHub in this task: `43247c9e..a9889031`, 226 commits).
- Branch `research/hybrid-v2-backend-generalization`, worktree `.superpowers/worktrees/hybrid-v2-backend-generalization`.
- Product `eca4b44b`; freeze `cec477a5` (`ecae59e6…`, 118 files); Full T3 PASS on clean detached `7210a016`
  (`full-t3/receipt.json`).
- Engine `/13`, planner `/14`, registry `/13`, `CACHE_VERSION = "130"`, `LLM_ONLY` default, Hybrid opt-in, 0 live calls.

## Resume

```bash
git rev-parse main origin/main; git ls-remote origin refs/heads/main
git -C .superpowers/worktrees/hybrid-v2-backend-generalization status --short          # expect empty
git merge-base --is-ancestor main research/hybrid-v2-backend-generalization && echo FF_POSSIBLE
# merge only from the clean main worktree, ff-only, never force:
git -C .superpowers/worktrees/local-main-integration merge --ff-only research/hybrid-v2-backend-generalization
cd .superpowers/worktrees/local-main-integration/backend && PYTHONIOENCODING=utf-8 \
  ../../../../backend/.venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
git push origin main:main     # authorized for THIS task only, after the smoke above
```

## Answers (campaign questions)

| # | Question | Answer |
|---|---|---|
| 1 | GitHub `main` synced? | Yes for `a9889031` (verified local = origin = ls-remote). Backend merge push: see `POST_MERGE.md` |
| 2 | Commits per push | push 1: 226. push 2: see `POST_MERGE.md` |
| 3 | Named planes: many labels and label permutations, mathematically correct? | Yes: ≥ 3 labels, any order (crossed included), first non-collinear witness of the whole group, every label checked coplanar, full name shown; closed-form oracles on 5 families |
| 4 | Browser `/4` families | named planes #3, #4, #11, #12, #13 (28/28); point–line #3, #4, #11, #12 (16/16). Offline replay, not live NL |
| 5 | Engine/planner versions | engine /12 → /13, planner /13 → /14 (served output and plan identity changed); registry and bridge strings unchanged — `report.md` §5 |
| 6 | Can a cache hold a stale refusal? | No: default route never reaches this code; Hybrid V2 local is `no-store`; preview refuses the product cache |
| 7 | Second capability | Yes: `/2` point–line distance (`eca4b44b`), browser 16/16 |
| 8 | Unhandled incorrect-served cases | None known. Presentation gap: point–line answer labelled `d(S, H)` (foot) rather than `d(S, BD)` — correct value, construction step shown |
| 9 | Full T3 on the new candidate | PASS at `7210a016` |
| 10 | Backend merged and pushed? | see `POST_MERGE.md` |
| 11–13 | Cleanup, space, dirty/ACL trees | see `POST_MERGE.md` |
| 14 | 18-family matrix | no class change: 0 FULL / 9 PARTIAL / 7 RENDER_ONLY / 2 UNSUPPORTED; `/4` scope grew (report §8) |
| 15 | Missing before Hybrid can replace `LLM_ONLY` | independent review; pre-registered held-out extraction set (D-04); live paired measurement vs `LLM_ONLY` with Owner GO (D-11); `/api/analyze` wiring behind a flag with cache isolation and rollback (D-02/D-08/D-12); D-10 presentation from certificates (incl. the `d(S, H)` label); curved/composite/Oxyz families; Owner enablement decision (D-13) |

## Next useful work

1. D-10: name a decomposed point–line answer after the asked line (`d(S, BD)`), through the scene contract, with a
   browser row.
2. Sections and circumscribed spheres for #4/#12 on `/4`, same method (oracle → bridge → planner → engine → browser).
3. Owner decisions listed in `POST_MERGE.md` (unmerged research branches, ACL-locked directories, missing-path metadata).
