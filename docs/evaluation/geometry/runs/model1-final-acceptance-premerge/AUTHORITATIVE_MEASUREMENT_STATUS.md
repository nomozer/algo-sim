# Authoritative measurement status — candidate 158

Run `model1-final-acceptance-premerge` (AXO HYBRID /18), 2026-11-21. Audience: the owner.

**`AUTHORITATIVE_DETACHED_COMPLIANCE = NOT_VERIFIED`** — `BLOCKED_OWNER_DECISION` (D3).

## 1. What the rules say

| source | text | requires |
|---|---|---|
| `AGENTS.md §2` (committed) | "Khi cần xác minh có thẩm quyền (authoritative verification), **tạo** git worktree detached sạch tại commit tương ứng." | a *created*, clean, detached worktree at the measured commit |
| `CLAUDE.md` §2 (local, gitignored) | "Đo có thẩm quyền (candidate freeze, full gate) chạy trong **worktree detached sạch** tại commit đang xét." | same |
| Owner standing policy (/13 onward, repeated in /17 and /18) | reuse the shared worktree; do not create a worktree without separate approval | no new worktree |

## 2. Four properties that are not the same

| property | candidate 158 measurements | status |
|---|---|---|
| detached HEAD | no — Full T3 ran at branch HEAD `b92b68a94` (`feat/model1-integration-readiness`) | not met |
| clean tracked tree at start | yes (`git status` 0 lines; one untracked report existed ~2 min early in T3, moved out; 0 failures) | met, with the recorded incident |
| isolated worktree (no shared `.superpowers/`, caches, `node_modules` state with other branches) | no — the shared development worktree, reused across /11–/18 | not met |
| reproducible environment identity | yes — freeze tree `bdb737bb…`, CACHE 158, GGUF `73f1484b…`, llama.cpp b12470 recorded in `FULL_T3_RECEIPT.json` | met |

A clean branch HEAD or a detached HEAD inside the shared worktree is **not** the procedure `AGENTS.md §2` prescribes.

## 3. Measurements on candidate 158 and their standing

| measurement | where | authoritative? |
|---|---|---|
| Full T3 `FULL_PRODUCT_GATE_PASS` (15,178 / 2,345, build, demo, crash) | shared worktree, branch HEAD `b92b68a94` | NOT_VERIFIED |
| routing regression (706 exposed cases, Holdout-6 + SLM-Ind-3 full route) | shared worktree, in-process | diagnostic only (exposed sets) |
| /18 identity + 579-test regression | shared worktree, branch `feat/model1-final-acceptance-premerge` | not an authoritative gate run |

No Full T3 was re-run in /18: no product code changed, and a second run in the same non-compliant location adds no authority.

## 4. Plan once the owner decides D3

**Option D3-a — one temporary detached worktree (owner writes the approval).**

```powershell
# run from the main checkout; does not touch main's working tree or its untracked folder
git worktree add --detach D:\Documents\projects\algo-sim\.superpowers\worktrees\measure-158 b92b68a94
# backend venv: use the main checkout's venv via ALGO_SIM_PYTHON; frontend: directory junction to the main node_modules
cmd /c mklink /J D:\Documents\projects\algo-sim\.superpowers\worktrees\measure-158\frontend\node_modules D:\Documents\projects\algo-sim\frontend\node_modules
# in the new worktree's frontend\ (logs OUTSIDE the worktree):
#   $env:ALLOW_LIVE_AI='0'; $env:ALGO_SIM_PYTHON='D:/Documents/projects/algo-sim/backend/.venv/Scripts/python.exe'
#   $env:LOCAL_SLM_CACHE_DIR='C:/Users/Bunny/AppData/Local/axo-slm'; npm run test:full *> D:\tmp\measure-158\full-t3.log
# then: freeze --verify, lock --verify, git status (must be empty), record HEAD/tree/model/runtime/command/result
# cleanup: stop every process using the worktree, remove the junction LINK ONLY, then remove the worktree from the main repo
cmd /c rmdir D:\Documents\projects\algo-sim\.superpowers\worktrees\measure-158\frontend\node_modules
git worktree remove D:\Documents\projects\algo-sim\.superpowers\worktrees\measure-158
```

Record in a receipt: commit, tree hash (`freeze --verify`), clean status before and after, model/runtime checksums,
exact command, result, and `git worktree list` before/after cleanup. The prospective set (if one exists by then) is
run in the same worktree on the same commit.

**Option D3-b — the owner amends `AGENTS.md §2`** to accept "clean tracked tree at a recorded commit in the shared
worktree" as authoritative. Then the existing `FULL_T3_RECEIPT.json` of /17 would meet the amended rule only if the
owner states that it applies retroactively; otherwise re-run once. The agent does not write that amendment.

## 5. Verdict

`AUTHORITATIVE_DETACHED_COMPLIANCE = NOT_VERIFIED` until D3 is decided and, for D3-a, the measurement above is run.
