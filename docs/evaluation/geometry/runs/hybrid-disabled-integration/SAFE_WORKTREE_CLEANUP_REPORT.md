# Safe worktree cleanup report

Run `hybrid-disabled-integration`, 2026-10-23. Owner GO covered cleaning **temporary worktrees created by the Hybrid
campaign** once safe; no branch was deleted; nothing outside that set was removed.

## Disk D: (MB, `df -m /d`)

| Point | Free |
|---|---:|
| Session start | 9,676 (93 % used) |
| After removing five campaign temp worktrees | 18,948 |
| After creating the integration and T3 worktrees | 15,244 |
| After removing this run's T3 worktree (`t3-hybrid-disabled-integration`, junction removed first, `git worktree remove` without force, fully deleted) | 17,094 |

Each full checkout costs ≈ 1.8 GB, almost all of it tracked `docs/evaluation/geometry` evidence; `frontend/node_modules`
is a junction to the root copy and `backend/.venv` is resolved from the root by the gates.

## Removed (`SAFE_TEMP_CLEANUP`)

All were detached, clean (or held only a change whose blob is already committed), and their HEAD is reachable from a
kept branch, so each can be recreated with `git worktree add --detach <path> <sha>`.

| Worktree | HEAD | Contained in | Non-cache content beyond the commit | Notes |
|---|---|---|---|---|
| `hybrid-session4a-s3-verify` | `84c729e0` | Session 3 branch | none (0 files outside the tree) | Session 4A verification checkout |
| `s1-freeze` | `404f0568` | Sessions 1–3 branches | `frontend/dist` (build output) | junction removed first |
| `s2-freeze` | `3553e4d4` | Sessions 2–3 branches | modified `EVALUATION_CANDIDATE.json` = blob `fd659522`, committed in `5beb0e86`; restored before removal | |
| `t3-s2` | `f1ae2238` | Sessions 2–3 branches | `frontend/dist` | junction removed first |
| `hybrid-backend-continuation-verify` | `76a7ce33` | Sessions 1–3 branches | `frontend/dist`; 0 files outside the tree | junction removed first |

Procedure: verify `frontend/node_modules` `LinkType = Junction` with target `D:\Documents\projects\algo-sim\frontend\node_modules`
→ `cmd /c rmdir <junction>` (removes the link only; root `node_modules` checked present afterwards) → `git worktree
remove <path>` without `--force`. For `hybrid-session4a-s3-verify` and `hybrid-backend-continuation-verify`, Git
de-registered the worktree but stopped with `Invalid argument`; the remaining files were compared with
`git ls-tree -r <HEAD>` (0 files not in the commit) and the exact directory was then deleted with no reparse point
inside. **Residue kept:** ~3.8 MB of ACL-locked `__pycache__/*.pyc` (Access denied, created by an earlier sandbox) in
those two directories; not forced, per the brief.

## Kept

| Class | Worktrees / directories |
|---|---|
| `ACTIVE_KEEP` | `hybrid-session4b-integration` (this run); root workspace (7 untracked user entries, untouched) |
| `INTEGRATION_SOURCE_KEEP` | `hybrid-backend-s1` (12 untracked verification logs), `hybrid-backend-s2` (10 untracked logs), `hybrid-backend-s3`, `hybrid-session4a-readiness`; their branches are merged into the integration branch but not into `main` |
| `EVIDENCE_KEEP` | the S1/S2 untracked logs above are not in Git — removing those worktrees would lose them; commit or archive them first |
| `UNRELATED_PRESERVE` | `extraction-v2-safety`, `geometric-visual-correctness-framing`, `hybrid-route-d-preview-wiring`, `hybrid-semantic-extraction-v2`, `nl-to-scene3d-e2e-readiness`, `scene3d-plane-grid-camera`, `scene3d-unified-visual-language` (287 dirty entries), `semantic-extraction-v3`, `semantic-extraction-v3-runtime-revision`, `simulation-coverage-visual-validation`, `simulation-visual-consistency-learning-ux`, `visual-ux-final-quality`, and detached `freeze-scene3d-metric-boundary`, `freeze-scene3d-metric-final`, `t3-scene3d-metric-boundary`, `t3-scene3d-pre-main`, `t3-scene3d-pre-main-2`, `verify-geometric-visual-correctness-framing`, `verify-visual-ux-final-quality` |
| `UNKNOWN_DO_NOT_DELETE` | unregistered directories `goal-bounded` (14,029 files), `goal-fixed` (13,571), `hybrid-offline-readiness-finalization` (24,362, real `node_modules`), `semantic-grounding-base-20261017` (14,213), `simulation-evidence-repair` (29), `t3-scene3d-metric-final` (218); near-empty `composite-baseline`, `composite-verification`, `docs`, `verify-simulation-go-main` |

## Proposals (owner decision, not executed)

1. The detached scene3d/visual verification worktrees above (~12 GB) look like completed T3/freeze checkouts of other
   campaigns; their owners should confirm the receipts are committed before removal.
2. The unregistered directories (~7 GB) are not Git worktrees any more; inspect ownership/ACL before deleting.
3. After an owner decision on `main`, Session 1–3 and 4A worktrees can go once the S1/S2 untracked logs are committed or
   archived. Their branches should stay until merged into `main`.
