# Post-merge record — Hybrid V2 backend generalization (2026-10-26)

Status: **`HYBRID_V2_BACKEND_REMOTE_MAIN_INTEGRATED_VERIFIED`** — the opt-in backend code is on GitHub `main`. This does
**not** mean Hybrid may replace `LLM_ONLY` (`report.md` §10, `NEXT_AGENT_HANDOFF.md` row 15).

## Merge and pushes

| Step | Result |
|---|---|
| push 1 (Scene3D + watchdog) | `43247c9e..a9889031`, 226 commits, no force; local = origin = ls-remote `a9889031` |
| pre-merge recheck | `main` = `origin/main` = `ls-remote` = `a9889031`; branch descends from it; main worktree clean |
| merge | `git merge --ff-only research/hybrid-v2-backend-generalization` in `.superpowers/worktrees/local-main-integration` → `09bb911b` |
| what `09bb911b` adds after the T3 candidate `7210a016` | documentation only (no measured product file) |
| post-merge smoke | freeze `--verify` MATCH (`ecae59e6…`, 118 files); named-plane, point–line, preview-fixture, default-mode tests 97/97; worktree clean |
| push 2 (backend) | `a9889031..09bb911b`, 14 commits, no force; local = origin = ls-remote `09bb911b` |
| push 3 | this record, documentation only |

## Cleanup (no force, no prune, no ACL change)

| Removed | How | Bytes freed |
|---|---|---|
| worktree `t3-hybrid-v2-7210a016` (detached T3 checkout; receipt + raw streams committed in `full-t3/`) | junction link removed, `git worktree remove`; Git left the empty top folder (a shell had stood in it) — removed with a non-recursive `rmdir` | 3 797 801 886 |
| worktree `t3-sphere-final` (detached `7e545f66`, in main; `.superpowers/` held 0 files) | same | 3 722 303 526 |
| worktree `t3-sphere-final-2` (detached `104808d6`, in main; 0 files in `.superpowers/`) | same | 3 722 317 190 |
| worktree `hybrid-v2-backend-generalization` (this branch, merged and pushed) | same | 3 804 627 079 |
| **total** | | **15 047 049 681 (≈ 15.0 GB)** |

Every removal was preceded by: `git status` empty, HEAD reachable from `main`, no process command line naming the
path, every file and folder owned by the current user, junction proved to point at the root `frontend/node_modules`
(68 entries before and after), ignored content limited to caches, empty folders and `backend/algosim.db`.

Branches deleted with `git branch -d` from the `main` worktree (all ancestors of `main`, no worktree): 
`research/hybrid-v2-backend-generalization`, `research/f2-oracle-b3-e2e`, `research/hybrid-b3-v2-distance-bridge`,
`research/hybrid-backend-session2-contract`, `research/hybrid-backend-session3-contract-v2`,
`research/hybrid-session4a-readiness`, `research/hybrid-session4b-integration`, `research/hybrid-session5-offline-consumer`,
`research/publication-safety-remediation`, `research/scene3d-plane-section-display-identity`,
`research/scene3d-visual-correction`, `research/sphere-sample-source-authority`, `research/visual-closure-hybrid-readiness`
(13). No commit was lost. Remote branches were not touched.

## Kept, and why

| Item | Reason | Owner action that would allow removal |
|---|---|---|
| root checkout (`research/hybrid-wave3a-volume-reasoning`, HEAD `fe9f5554`) | Owner's uncommitted work: 79/79 protected files byte-identical to `preflight.json`, before and after | — |
| dirty worktrees `s3d-hybrid-v2`, `scene3d-visual-correction`, `visual-hybrid-integration`, `s3d-hybrid-v2-codex` (untracked) | uncommitted data | commit or discard by the Owner |
| `s3d-hybrid-v2-claude`, `t3-claude-resume` | live Vite servers | stop the servers |
| `windows-watchdog-recovery` | `IGNORED_ARTIFACT_BACKUP_INCOMPLETE`: 4975 Codex-sandbox files unreadable here | verify `pytest-temp` against the backup as the Codex sandbox account or an approved admin, then non-forced remove |
| orphan folder `scene3d-codex-takeover` (unregistered, 3.38 GB) | 658 items owned by `CodexSandboxOffline`, no Delete right | delete as the owning account (content = tracked files of `11188e7a` + caches) |
| `t3-sphere-visual-polish`, `verify-s3d-hybrid-v2-codex`, `verify-scene3d-codex-takeover`, `verify-sphere-main-integration` | clean and merged, but contain Codex-sandbox-owned items (removal would fail midway) | same as above |
| `b3-dist`, `hybrid-primary-b1-b2-offline`, `hybrid-session5-offline-consumer`, `hybrid-visual-candidate`, `sphere-src`, `svc-cand`, `t3-b1b2` | ignored `.superpowers/` evidence with real files (1 to 4992 files, up to 345 MB), not backed up | decide whether those ignored artifacts matter; back up, then remove |
| 20 missing-path worktree entries | metadata only; not pruned (prior instruction; `git worktree prune` cannot be scoped) | explicit GO for `git worktree prune` |
| unmerged branches `research/hybrid-semantic-extraction-v2` (13 unique commits), `integration/extraction-v2-safety` (1), `research/nl-to-scene3d-e2e-readiness` (1), `research/hybrid-next-architecture-gap-audit` (1), `feat/real-model-pilot-tooling` (4, includes a live-pilot record), `docs/real-model-e2e-readiness` (1, contained in `feat/real-model-pilot-tooling`), `research/compact-geometry-dsl` (7) | every one has commits whose changes are not in `main` (`git cherry`: `+`); not provably superseded | Owner decision per branch; deleting needs `-D` |

Registered worktrees: 47 at takeover → 40 now.

## Errata (commits are not rewritten)

- `1cff5458` says the collinear check replaced "a Gram division by zero": the case was already refused, as
  `SOURCE_OBJECT_MISMATCH`. The check itself was later withdrawn: such planes are served through a non-collinear witness.
- `b11349ae` body: read "engine /12 → /13, planner /13 → /14".
