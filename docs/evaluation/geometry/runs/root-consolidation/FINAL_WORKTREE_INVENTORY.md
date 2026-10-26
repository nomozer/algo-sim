# Final worktree inventory

Before: **16 registered worktrees / 15 local branches**. After old-checkout consolidation: **6 registered worktrees /
10 local branches**, excluding the temporary documentation integration worktree/ref. These final counts require that
temporary worktree/ref to be removed after integration; the local final-verification.json records the actual result.
Ten old registrations and five merged branches were removed. Eight old checkout directories were physically removed;
two newly unregistered remnants remain quarantined. No force or ACL modification was used.

Registered baseline for the next agent (prefix `D:/Documents/projects/algo-sim/`):

- root: clean `main`.
- `.superpowers/worktrees/s3d-hybrid-v2`: 108 dirty files, snapshot preserved.
- `.superpowers/worktrees/s3d-hybrid-v2-codex`: 69 dirty files, snapshot preserved.
- `.superpowers/worktrees/scene3d-visual-correction`: 470 dirty files, snapshot preserved.
- `.superpowers/worktrees/visual-hybrid-integration`: 210 dirty files, snapshot preserved.
- `.superpowers/worktrees/windows-watchdog-recovery`: clean merged source, retained under the special preservation rule.

Original per-file snapshots cover **857 other dirty files** and **9669 readable hidden files**. The original hidden scan
had one unreadable directory in primary; the owning-user supplement subsequently preserved another **4958** files there.
These are separate manifests, not an assertion that all ignored bytes in every checkout have been backed up.

| Old worktree | Dirty files | Other ignored snapshots | Initial hidden snapshots | Final disposition |
|---|---:|---:|---:|---|
| `hybrid-primary-b1-b2-offline` | 0 | 1 | 4254 | Registration/ref removed (HEAD merged); original 4254 hidden files plus 4958 owning-account files backed up; orphan retained, see limitations below |
| `hybrid-session5-offline-consumer` | 0 | 1 | 42 | Registration/ref removed (HEAD merged); original meaningful files backed up; ACL-blocked orphan retained |
| `hybrid-visual-candidate` | 0 | 1 | 1 | PHYSICALLY_REMOVED; merged source recoverable from Git, valuable ignored/hidden files verified in backup |
| `local-main-integration` | 0 | 2 | 0 | PHYSICALLY_REMOVED; merged source recoverable from Git, valuable ignored/hidden files verified in backup |
| `s3d-hybrid-v2` | 108 | 38 | 0 | UNKNOWN_PRESERVE; original dirty files and refs retained |
| `s3d-hybrid-v2-claude` | 0 | 38 | 0 | PHYSICALLY_REMOVED; merged source recoverable from Git, valuable ignored/hidden files verified in backup |
| `s3d-hybrid-v2-codex` | 69 | 38 | 59 | UNKNOWN_PRESERVE; original dirty files and refs retained |
| `scene3d-visual-correction` | 470 | 74 | 1128 | UNKNOWN_PRESERVE; original dirty files and refs retained |
| `t3-claude-resume` | 0 | 38 | 0 | PHYSICALLY_REMOVED; merged source recoverable from Git, valuable ignored/hidden files verified in backup |
| `t3-sphere-visual-polish` | 0 | 2 | 0 | PHYSICALLY_REMOVED; merged source recoverable from Git, valuable ignored/hidden files verified in backup |
| `verify-s3d-hybrid-v2-codex` | 0 | 1 | 0 | PHYSICALLY_REMOVED; merged source recoverable from Git, valuable ignored/hidden files verified in backup |
| `verify-scene3d-codex-takeover` | 0 | 2 | 0 | PHYSICALLY_REMOVED; merged source recoverable from Git, valuable ignored/hidden files verified in backup |
| `verify-sphere-main-integration` | 0 | 1 | 0 | PHYSICALLY_REMOVED; merged source recoverable from Git, valuable ignored/hidden files verified in backup |
| `visual-hybrid-integration` | 210 | 1 | 0 | UNKNOWN_PRESERVE; original dirty files and refs retained |
| `windows-watchdog-recovery` | 0 | 1 | 4185 | QUARANTINED_PRESERVE |

Ordinary `git worktree remove` successfully deregistered the ten eligible old trees, but most removals initially returned
Windows permission/junction errors. Each remainder was then classified against its original Git tree or a verified local
snapshot, with cache/dependency directories identified separately. The junction to root frontend/node_modules was removed
as a link without recursion before deleting verified remnants with their existing owning account. Successful physical
removals and exact item/hash checks are in orphan-*.json and remnant-removal*.json in the local backup. The root dependency
directory stayed at 73 top-level entries. A failed Git removal is never counted as a successful physical removal.

Exact quarantined paths under `.superpowers/worktrees/`:

- `windows-watchdog-recovery`: 4185 readable hidden files backed up now do **not** verify the previous 4975-file pytest-temp
  source set. Do not delete this tree until that exact source comparison succeeds.
- `scene3d-codex-takeover`: pre-existing unregistered orphan; untouched. Its ownership and preservation case remains open.
- `hybrid-primary-b1-b2-offline`: new unregistered remainder. The sandbox scan still cannot enter the owning-user
  pytest-of-Bunny directory, whose 4958 original files were separately backed up with that user's permissions. Another
  1272 remaining nested test-repository Git metadata files are unclassified by the original backup (which excluded nested
  .git directories). Keep these originals; do not infer their dispensability from the branch being merged. The complete
  21887-file remainder scan and its precise error/path lists are local in orphan-hybrid-primary-b1-b2-offline.json.
- `hybrid-session5-offline-consumer`: new unregistered remainder. A 16279-file non-cache scan matched Git/snapshots with
  zero unknowns/errors; ordinary deletion under each owning account still encountered differing ACLs, including a Python
  bytecode cache. Retain the remainder rather than changing permissions. Every original meaningful ignored/hidden file
  has its verified backup; source is recoverable from merged HEAD 5ee97340.

The five deleted merged refs are research/hybrid-wave3a-volume-reasoning, research/scene3d-section-inspector-c0,
integration/hybrid-visual-candidate, research/scene3d-hybrid-v2-claude-resume and research/hybrid-primary-b1-b2-offline.
The five divergent research refs remain deliberately local; their bundle and disposition are in the companion report.

All identified old AlgoSim Vite servers were stopped: PIDs 25844, 21212, 20724, 19832, 15752 and 5648. The last two relative
command lines were resolved through read-only process current-directory inspection to scene3d-codex-takeover/frontend and
.superpowers/scene3d-takeover-before/frontend before stopping them. Root backend PID 15428 was stopped; child 1900 exited
with its parent. Other Claude/browser/MCP processes were not terminated. Owner confirmed exclusive write authorization;
final process receipts check for remaining AlgoSim servers. Physical cleanup verdict remains
**CLEAN_ROOT_MAIN_WITH_QUARANTINED_ACL_ARTIFACTS**.
