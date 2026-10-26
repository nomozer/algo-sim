# Safe cleanup

Status: NOT_STARTED_AWAITING_LOCAL_MAIN_MERGE.

P0 inventoried 45 registered worktrees, including 11 missing paths, and recorded dirty-file hashes. Active Vite usage was found in s3d-hybrid-v2, s3d-hybrid-v2-claude and t3-claude-resume. No worktree, branch, missing-path metadata, evidence, receipt, backup or junction has been removed.

P6 requires a fresh inventory after verified main integration. P0 inventory alone does not authorize any removal. Dirty/active trees and unique evidence must remain protected; standard worktree removal and merged-branch deletion must use no force.

## Claude takeover — cleanup executed (2026-10-26)

Status: **`LOCAL_MAIN_CLEANUP_PARTIAL_SAFE`**. Main was verified first (`CODEX_TO_CLAUDE_RESUME.md`). Every removal used
normal `git worktree remove` (no `--force`) and `git branch -d` (no `-D`); no `prune`, `clean`, `reset`, `takeown`,
`icacls` change or recursive delete into a junction.

### Inventory

| | Registered | Missing path | Dirty (tracked) | Untracked-only |
|---|---|---|---|---|
| Before (fresh, after main verified) | 47 | 20 | 4 (root 19/60, `s3d-hybrid-v2` 6/102, `scene3d-visual-correction` 1/469, `visual-hybrid-integration` 1/209) | 1 (`s3d-hybrid-v2-codex`, 69) |
| After cleanup | 42 | 20 | same 4 | same 1 |
| After adding the backend worktree | 43 | 20 | same 4 | same 1 |

Raw inventories: `cleanup/inventory-before.json`, `cleanup/inventory-after.json`.

### Selection rule

`SAFE_TO_REMOVE` only when all hold at removal time: `git status` empty; HEAD reachable from `main`; no process command
line references the path; ignored content limited to `frontend/node_modules` (junction), `frontend/dist`,
`frontend/.vite-cache`, `__pycache__`, `backend/algosim.db`; every file and folder owned by the current user (added after
the first failure, see below); not the root, not `local-main-integration` (holds `main`), not the new backend worktree.

Every `frontend/node_modules` in these worktrees is a junction to the **root** `frontend/node_modules`, which live Vite
servers use. Before each removal the junction was proved a junction to that target and removed as a link only
(`os.rmdir`); the root `node_modules` entry list (68 entries, `vite/package.json` present) was compared before and after
every step.

### Removed

| Worktree | HEAD (in main) | Branch | Bytes freed (no junction) | `algosim.db` backup SHA-256 |
|---|---|---|---|---|
| `s3d-v129-base` | `11188e7a` | detached | 3 365 677 876 | — |
| `svc-sphere-final` | `39b6dbbe` | detached | 3 681 008 120 | — |
| `s3d-visual-freeze` | `3dcd6d9f` | detached | 3 477 376 856 | `53745594170b93bce7175ca32903be1610b209f6c60f58918cbf9e540b58d54e` |
| `scene3d-html-port` | `7f90d9b3` | `research/scene3d-html-visual-port` deleted (`-d`) | 2 093 662 076 | `1ec28d16db52424e129d96adad5719c007cf161938d0dfff681a34e640c0aa3f` |

Freed: **12 617 724 928 bytes (≈ 12.6 GB)**. Backups (159 744 bytes each, re-hashed after copy):
`.superpowers/backups/cleanup-20261026-claude/<worktree>/backend/algosim.db`.

### Partial: `scene3d-codex-takeover`

`git worktree remove` stopped with `failed to delete …: Invalid argument` (rc 255) after removing the worktree metadata,
`.git`, `.claude`, `.gitignore`, `AGENTS.md`, `backend/alembic*`, `backend/algosim.db` (backed up first:
`83c9f379ba089a9d21a12acac20622e72cb1018894fc3db1403e07089bae8165`) and some `.py` files. Root cause: 658 items, among them
`__pycache__` and tracked evidence folders, are owned by `CodexSandboxOffline`; the current user has `RX,W` but no Delete
right. Nothing was forced. Left as an **unregistered orphan directory** of 3 375 637 533 bytes containing only tracked
files of `11188e7a` (reachable from `main`), `.pyc`, `dist`, `.vite-cache`. Its branch `research/scene3d-codex-takeover`
(`11188e7a`, in main) was deleted with `-d`. Disk space here was **not** freed.

The owner-of-every-item check was added after this failure and validated on this directory (it reports the 658 items)
before it was trusted for the next candidates.

### Kept

| Class | Worktrees |
|---|---|
| `DIRTY_PRESERVE` | root checkout; `s3d-hybrid-v2`; `scene3d-visual-correction`; `visual-hybrid-integration`; `s3d-hybrid-v2-codex` (untracked) |
| `ACTIVE_PROCESS_PRESERVE` | `s3d-hybrid-v2-claude` and `t3-claude-resume` (Vite); `windows-watchdog-recovery` (Chrome PID 2276 on the Owner review page) |
| `UNIQUE_EVIDENCE_PRESERVE` | 12 clean trees with an ignored `.superpowers/` folder not inspected or backed up: `b3-dist`, `hybrid-primary-b1-b2-offline`, `hybrid-session5-offline-consumer`, `hybrid-visual-candidate`, `sphere-src`, `svc-cand`, `t3-b1b2`, `t3-sphere-final`, `t3-sphere-final-2`, `t3-sphere-visual-polish`, `verify-s3d-hybrid-v2-codex`, `verify-scene3d-codex-takeover` |
| `UNKNOWN_PRESERVE` (ACL) | `verify-sphere-main-integration` — its `backend/algosim.db` is owned by the Codex sandbox, removal would fail midway |
| `UNKNOWN_PRESERVE` (backup unproved) | `windows-watchdog-recovery` — `IGNORED_ARTIFACT_BACKUP_INCOMPLETE` |
| integration | `local-main-integration` (checks out `main`); new `hybrid-v2-backend-generalization` |
| `MISSING_PATH_METADATA_PRESERVE` | all 20 missing-path entries, not pruned |

Root Owner checkout: 79/79 protected files byte-identical to `preflight.json` before and after; HEAD `fe9f5554`.
No `.superpowers/backups` content was removed.
