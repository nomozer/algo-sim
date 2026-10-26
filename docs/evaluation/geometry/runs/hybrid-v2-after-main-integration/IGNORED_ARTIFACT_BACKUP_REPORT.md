# Ignored-artifact backup of the recovery worktree

Status: **`IGNORED_ARTIFACT_BACKUP_INCOMPLETE`** (strict reading). The backup copy is complete against its own manifest,
but 4975 of the 5078 source files cannot be read by the current user, so source equality cannot be re-proved
independently. Consequence: the recovery worktree was **not** removed.

Checked by Claude on 2026-10-26, after Codex stopped. No backup process was running (process table: only VS Code
terminals, Vite servers, the Codex app-server host, two uvicorn servers and a Chrome window, PID 2276, showing
`OWNER_VISUAL_REVIEW.html` from this worktree). Nothing was copied,
overwritten or deleted in the backup folder.

## What was checked

| Item | Value |
|---|---|
| Source | `.superpowers/worktrees/windows-watchdog-recovery` (branch `research/windows-watchdog-t3-recovery`, HEAD `a9889031`, `git status` clean) |
| Backup | `.superpowers/backups/windows-watchdog-recovery-a9889031-20261026/` (`ignored/` + `manifest.json`) |
| `manifest.json` SHA-256 | `59598e1174e3495e94778a3f51ecad7748eb432e955ec0ad8021898ea37527a9` (complete JSON, `junctions: []`) |
| Manifest entries | 5078 files, 38 421 170 bytes |
| Files on disk under `ignored/` | 5078, none outside the manifest |
| Backup file == manifest (bytes + SHA-256), every file | 5078 / 5078 |
| Fresh source inventory (`git ls-files -o -i --exclude-standard`, `-z`) | 103 files readable |
| Source == backup == manifest, independently hashed | **103 / 103** |
| Source files unreadable (`Permission denied`) | **4975** (33 647 510 bytes), all under `.superpowers/t3-recovery-3d6351d8/pytest-temp/` |
| Reparse points in the readable source | none |

The 103 independently verified files include every raw Full T3 stream of the recovery run:
`.superpowers/t3-recovery-3d6351d8/receipt.json` (`bd881629…`, equal to `receipt_sha256` in `source-identity.json` and
to the committed `full-t3/receipt.json`), `stdout.log` (1 576 874 bytes, `f3f91d93…`) and `stderr.log` (`ccb6bf35…`).
**No raw T3 log is unpreserved.**

## Why 4975 files cannot be re-verified

`icacls` and `Get-Acl` on `pytest-temp` return *Access is denied* for `desktop-scqfjl8\bunny`. The folder was written by
the Codex Windows sandbox user (same pattern as the `__pycache__` folders found during cleanup, owner
`CodexSandboxOffline`, `BUILTIN\Users` only `RX,W`). Codex could read it when it made the copy; this session cannot.
Changing ownership or ACLs (`takeown`, `icacls /grant`) is forbidden by the campaign rules, so it was not attempted.

What is known: the content is pytest `tmp_path` scratch of the T3 run (fixture copies, per-test raw JSON), not receipts.
What is not known: whether each backup byte equals the source byte. The backup is self-consistent with Codex's manifest,
but that manifest is Codex's own claim.

## Recovery plan

- Read the backup: `.superpowers/backups/windows-watchdog-recovery-a9889031-20261026/ignored/<relative path>`; check
  against `manifest.json` (per-file `bytes`, `sha256`).
- To close this as `IGNORED_ARTIFACT_BACKUP_VERIFIED`: run the per-file hash comparison as a user that can read
  `pytest-temp` (the Codex sandbox account, or an Owner-approved administrator session), then remove the worktree with
  a normal, non-forced `git worktree remove`. Do not remove it before that: Git would also fail midway on the same ACL.
