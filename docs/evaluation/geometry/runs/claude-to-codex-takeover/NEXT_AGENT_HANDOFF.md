# Next agent handoff — Claude to Codex continuation

## Exact checkpoint

Branch: `research/scene3d-hybrid-v2-codex`.
Worktree: `D:/Documents/projects/algo-sim/.superpowers/worktrees/s3d-hybrid-v2-codex`.
Product HEAD: `f9e8697282d8cfaaa4f06bf670c6eb6df6a875c5`.
Frozen checkpoint/current HEAD at handoff creation: `e336e0dfee30968b27887bcf446d9ec7ad610f54`.
Clean detached verification worktree: `../verify-s3d-hybrid-v2-codex` at e336e0df.
No merge/push/live calls. LLM_ONLY/cache130; Hybrid production NO-GO.

Claude source remains at 3dcd6d9f and byte-identical to the backup (`preservation-recheck.json`,112 files). Recovery archive: root `.superpowers/backups/claude-to-codex-20261026-133857/uncommitted.zip`; sha256 `8db6107d6096e62b374b0c11ee982beade0f0d4da6a2d712206aca2f2401ca01`. Source writer could not be ruled out, so never edit it concurrently. Do not delete worktrees, branches, caches owned by others or change ACLs.

## Complete product work

Preserved Claude angle bridge and local replay UI path. Fixed operand-bound skew-claim check, taxonomy, engine/12 identity, NFC/NFD verbatim provenance, image rejection before Vision ingestion and local out-of-scope no-store. Targeted backend80+197, skew9, HTTP12; frontend152; build PASS. Actual input UI/HTTP20/20 in `browser-auth-settled/receipt.json` (pre-final no-store-only fix; that branch is covered by HTTP tests). Corpus43:22served/0wrong/0false-refusal/1category mismatch. See report.md, review.md and families.md. No partial production edit remains.

## In-flight verification — inspect before starting another run

Full T3: root `.superpowers/claude-to-codex-t3-e336e0df-owned/`, launcher PID in `running.json`, stdout/stderr remain ignored. Wrapper session86217. It runs on the clean detached worktree; DO NOT edit that tree. After completion copy receipt.json only into this run (raw tracebacks stay outside Git), inspect every failure and post-freeze status. Initial ownership startup failure is retained separately; retry uses process-local GIT_CONFIG_COUNT/safe.directory for the exact worktree, no global Git setting.

Official Visual: `official-playwright/` on the frozen product build, session96424. Existing unchanged `../visual-closure-hybrid-readiness/browser-playwright-transport.mjs` supplies transport only. Native run failed CDP Page.enable; startup/infrastructure receipts retained. Do not change oracle F2 or thresholds. Inherited true score7/8; replacement role-aware2 PASS/10 UNCERTIFIABLE, faults10/10 on certified views only.

Owned dev server8193 and Vite3193 have been stopped. Verification node_modules paths are junctions to root frontend/node_modules; leave them in place (no cleanup requested).

## Next actions

1. Inspect T3 receipt and official BROWSER_EVIDENCE/scenario JSON; preserve failures. Fix only actual new correctness failures, with targeted RED/GREEN; refreeze if product changes.
2. Record actual verification results and remaining scope gaps in report.md and living indexes. Checkpoint docs/evidence with an explicit git-add allowlist. Never stage root UI changes.
3. Recheck source-backup hashes and git status; final handoff must state remaining untracked evidence paths and exact final HEAD.
4. Replacement readiness remains partial: no common-perpendicular witness for skew distance; angle arcs absent for non-right angles; four-label targets explicitly refuse; curved/composite/coordinate bridge goals unsupported;18 full reference families remain0FULL/9PARTIAL/7RENDER_ONLY/2UNSUPPORTED; independent extraction quality UNKNOWN; independent Owner review and visual approval PENDING. Do not enable Hybrid default.

## Safe resume commands (PowerShell)

```powershell
Set-Location D:/Documents/projects/algo-sim/.superpowers/worktrees/s3d-hybrid-v2-codex
git log -4 --oneline
git status --short
Get-Content D:/Documents/projects/algo-sim/.superpowers/claude-to-codex-t3-e336e0df-owned/receipt.json
Get-Content docs/evaluation/geometry/runs/claude-to-codex-takeover/official-playwright/BROWSER_EVIDENCE.json
& D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe backend/scripts/freeze_evaluation_candidate.py --verify
```

If Git invoked inside Python reports dubious ownership, pass `git -c safe.directory=<the exact intended worktree>` or process-local GIT_CONFIG_*; do not mutate global config or ACLs. Test tmp_path needs a fresh base directory under this worktree's `.superpowers/tmp` whose parent already exists.
