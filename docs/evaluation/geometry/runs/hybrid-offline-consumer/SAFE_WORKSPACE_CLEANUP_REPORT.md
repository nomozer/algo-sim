# Safe workspace cleanup report

Only one Session 5 development worktree was created, from verified local main. No other worktree, branch or orphan directory was deleted. `results/workspace-inventory.json` lists 22 registered worktrees and owner-review candidates. The ACL-locked S1 worktree was not forced or modified. Frontend campaign trees and root checkout remain preserved.

Disk D: before worktree creation **25,700,540,416 bytes free** (host observation); P0 after creation and consumer tooling **see `results/preflight.json`**. Later disk-free values are observations, not reclaimed-space evidence; concurrent campaigns can change them.

**Reclaimed: 0 bytes.** No installed environment, `node_modules` copy or package download was made. Python uses `D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe` directly. Session 5 `frontend/node_modules` is a junction to `D:/Documents/projects/algo-sim/frontend/node_modules`. It must be unlinked as a junction before any future worktree retirement; never recursively delete its shared target.

The development worktree and backup branch are retained for review. Evidence is committed at checkpoints. Failed backend temp-setup raw streams are kept locally under `.superpowers/session5-attempts/backend-targeted-initial/`, with original command/exit/hash metadata in `results/backend-targeted-initial-summary.json`. New failed/timed-out check streams are withheld from Git and retained under the task's ignored `.superpowers` location. This is not a remote archive or a second physical backup.

## Owner-only candidate table (no deletion authorization exercised)

| Candidates | Required checks before any retirement |
|---|---|
| Detached `freeze-scene3d-*`, `t3-scene3d-*`, `verify-*` entries in inventory | Other campaign owner confirms completion/evidence, clean tree, durable HEAD ref, no process/agent and safe junctions; actual reclaim size UNKNOWN. |
| `goal-bounded`, `goal-fixed`, `hybrid-offline-readiness-finalization`, `semantic-grounding-base-20261017`, `simulation-evidence-repair`, `t3-scene3d-metric-final` unregistered directories | Ownership, contents, unique evidence and ACL/junction inventory first; no deletion by Session 5. |
| `hybrid-backend-s1` | ACL-locked; retain. No force, ACL override or owner change. |
| Session 5 own worktree | Retain until review; future cleanup requires all evidence/raw receipts recoverable, clean tree, durable research branch, stopped Vite/browser/processes and explicit junction-target verification. |

Cleanup of another campaign or the repository's frozen corpus/oracle is outside the granted scope. No saved-space claim is inferred from prior Session 4 cleanup.
