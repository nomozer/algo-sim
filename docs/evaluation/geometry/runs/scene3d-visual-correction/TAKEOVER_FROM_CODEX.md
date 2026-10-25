# Takeover from Codex — Scene3D visual correction

Authorization `GO_CLAUDE_TAKEOVER_SCENE3D_VISUAL_CORRECTION_LOCAL`, 2026-10-25. Continuation of Codex's campaign
`GO_LOCAL_SCENE3D_VISUAL_CORRECTION_AND_HYBRID_READINESS`. This is not a restart.

## 1. Where Codex was working

| Item | Value |
|---|---|
| Worktree | `.superpowers/worktrees/scene3d-visual-correction` |
| Branch | `research/scene3d-visual-correction`, created from `main` `9978e512`, fast-forwarded to candidate `fe5f40b7` |
| Codex commits | **none**. All Codex work was uncommitted: 11 modified tracked files, plus the untracked run directory |
| Codex session | `~/.codex/sessions/2026/10/25/rollout-2026-10-25T17-21-48-…jsonl` (554 records, read-only) |
| Codex processes still alive at takeover | Vite on `:3156` (owner `CodexSandboxOffline`, serving this worktree). Not touched |

## 2. Preservation (before any edit)

Everything Codex left was copied out before Claude changed a byte. Location: the session scratchpad, folder
`codex-svc-preserve/`.

| Artifact | SHA-256 / count |
|---|---|
| `tracked.patch` (diff of the 11 tracked files against `fe5f40b7`) | `8113f22ec86e9193c9cabba7a8454b80a3a5433798a73aed353516cb37668b96` |
| `untracked-and-ignored.tar` (320 entries, incl. ignored `.superpowers/vitest-*.json`) | `aab8dc3c7e8fb473c467dfbb2055a268ce459e900d99204a0edf1bc55284c6d2` |
| `sha256.txt` | per-file hashes, 331 lines |
| `untracked.txt`, `archive-list.txt`, `base-head.txt` | inventories |

Codex's `plan.md` is owned by the Windows account `CodexSandboxOffline`. It was read but not modified. The source files
are owned by `Bunny` (Codex escalated for those writes). No ACL was changed. Nothing was deleted.

## 3. How Codex stopped

Read from Codex's own session log, not inferred:

1. Codex announced the `requesting-code-review` step: "dispatch a separate-context reviewer… this is a review within
   the same campaign; `INDEPENDENT_REVIEW_PENDING` and Owner visual approval stay separate". **No reviewer was
   dispatched.** The log after that point holds one tool call and the end of the task.
2. That one call was a checkpoint: `git add` of exactly its 11 files, `git diff --cached --check`, then
   `git commit -m 'fix(scene3d): correct curved visibility, contours and answer presentation'`. It required sandbox
   escalation.
3. The auto-review of that escalation **failed for quota**: "Automatic approval review failed: You've hit your usage
   limit… This is a review failure, not a determination that the action is unsafe." This is the "denied `pwsh.exe`
   command" in the Owner brief. Nothing was staged (`git diff --cached` was empty at takeover), and nothing was
   committed.
4. Codex's browser "after" matrix receipt is timestamped 17:53, four minutes after the session ended at 17:49. It was a
   detached background process from the same session that completed on its own.

## 4. Classification of Codex's plan

| Codex plan item | State at takeover | Evidence |
|---|---|---|
| Git state, governing docs, reference located | DONE_AND_VERIFIED | plan ledger; branch/HEAD re-checked |
| Reference HTML executed and compared; hash note | IMPLEMENTED_NOT_VERIFIED | `verification/reference/receipt.json`, 18/18 shapes. The hash question was left "pending" and is resolved in `HTML_REFERENCE_COMPARISON.md` §1 |
| Curved visibility (ray/volume, cone slope, caps, distant camera, transformed scene) | IMPLEMENTED_NOT_VERIFIED | code + tests present; vitest 1371/1371 in Codex's own `vitest-final.json`, started 3 s after the last edit |
| Hover ≠ selection, reset across scenes, terracotta fill identity | IMPLEMENTED_NOT_VERIFIED | `scene3d-unified-materials.test.ts`, `scene3d-focus-mode.test.tsx` |
| Supplemental role checker hardening | IN_PROGRESS | Codex's last browser run: 21/30 baselines, ellipse failing at several cameras |
| Mode A / Mode B through real DOM | IN_PROGRESS | product change present; browser matrix captured frames but asserted only "no result label on canvas" |
| Browser before/after family matrix | IMPLEMENTED_NOT_VERIFIED | `verification/before` 6/6, `verification/after` 24/24 at 17:53, both before Claude's renderer fixes |
| Dev server start/restart/force/HMR | NOT_STARTED | none |
| Official suite, Full T3, freeze | NOT_STARTED | none |
| Review | NOT_STARTED (interrupted, see §3) | none |
| Reports | NOT_STARTED | only `plan.md` |

## 5. What Claude did with it

Kept every Codex change. Continued from Codex's own failing evidence (21/30 role-aware baselines):

- found and fixed two renderer defects that Codex's browser runs exposed (see `SCENE3D_VISIBILITY_CORRECTION.md` §3–§4);
- completed the role-aware checker: curve arcs scored as arcs, and a three-way verdict that separates a wrong frame from
  one the camera cannot show;
- verified the remaining plan items and ran the gates listed in `FINAL_OWNER_HANDOFF.md`;
- reverted one Codex change that the locked official suite rejected. Codex had hidden final results in Mode B as well
  as Mode A, which took the suite from 7/8 to 0/8 (`b8b3311b`). Codex's inspector link was kept
  (`OFFICIAL_VISUAL_SUITE_RESULTS.md` §2).

Codex's changes and Claude's changes are committed separately on the same branch, so authorship stays traceable.
