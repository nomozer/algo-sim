# GO main record — Hybrid V2 disabled integration

Owner authorization: `GO_MAIN_HYBRID_V2_DISABLED_LOCAL_ONLY` (2026-10-23). Local only; `PUSH_REMOTE = NOT_PERFORMED`.

## Merge

| Item | Value |
|---|---|
| `main` before | `f10e6283dd3fd2cfdef189e1bef0ffdecf2be942` (the SHA reviewed in `FINAL_HANDOFF.md`) |
| `origin/main` (local ref and `git ls-remote origin refs/heads/main`) | `43247c9e9375a3dbf2b5223324a58e6f932ca596`, unchanged |
| Integration HEAD | `9c7ed1b100b16506105d68a51073a30381ae1edf` |
| Method | in the clean integration worktree: `git checkout main` then `git merge --ff-only 9c7ed1b1…`; root checkout (dirty, another branch) untouched |
| `main` after merge | `9c7ed1b100b16506105d68a51073a30381ae1edf` — equal to integration HEAD |
| Reachable from `main` | S1 `82d3d255`, S2 `227d447f`, S3 `0f7b3a69` / `69bd2fe4` / `84c729e0`, 4A `ef6829d3`, candidate `2bbad1f2`, old main `f10e6283`, `origin/main` `43247c9e` |
| Product/test change after candidate `2bbad1f2` | none (`git diff --name-only 2bbad1f2 9c7ed1b1 -- backend frontend` empty) |

## Post-main acceptance (on `main` = `9c7ed1b1`)

| Check | Result |
|---|---|
| `freeze_evaluation_candidate.py --verify` | MATCH, 116 entries, `413ee525d20874aa…`, product commit `69bd2fe4` |
| Invariants (`verify_integration_invariants.py`) | CACHE_VERSION "127", LLM_ONLY, flat, MAX_MEMORY_DECLARATIONS 32, inherited ALLOW_LIVE_AI 0; default policy fingerprint `None`; `/api/analyze` ignores the preview env |
| Default surfaces vs old `main` `f10e6283` | same ten research files changed; `semantic_program/`, `ai/skills/`, `main.py`, `ai/pipeline.py`, `docs/schemas/`, `frontend/` unchanged; flat provider surface `485d3834…` unchanged |
| Contract versions | registry `/13`, planner `/13`, engine `/11`, Adapter `/4` (no caller) |
| Docs identity/IA, candidate, schema sync, API/cache, route-aware cache, production wiring, preview API/contract, contract V2/unification, structured relations (default-mode lock) | 405 passed, 1 xfailed (D2 owner decision) |
| Full T3 | not re-run: product and test trees equal the T3 target `2bbad1f2` (PASS) |

Hybrid product enablement stays NO-GO; no production readiness is claimed.

## Evidence preservation

Commit `77f7aaf7` adds 22 Session 1/2 verification logs that existed only in those worktrees, staged with
`core.autocrlf=false` so each blob is byte-exact; all 22 SHA-256 values were already cited by committed receipts and
were re-checked from `main` (0 mismatches). Logs are test output (red runs, T3 streams); no secret found by scan.
No external archive was made: C: and D: are the same physical SSD, so Git is the most durable local copy.

## Worktree retirement

| Worktree | Action | Result |
|---|---|---|
| `hybrid-backend-s2` | 10 preserved logs deleted by exact path (hash-checked against `main`); `git worktree remove` | removed |
| `hybrid-backend-s3` | junction removed (target verified); `git worktree remove` | removed |
| `hybrid-session4a-readiness` | `git worktree remove` de-registered it but stopped (`Directory not empty`); remaining files checked ⊆ `git ls-tree ef6829d3` (0 extra); deleted child by child | de-registered; **residue**: 26 ACL-locked tracked files (~0.5 MB, Codex sandbox owner) + 2 unreadable ignored draft dirs under `.superpowers/` |
| `hybrid-backend-s1` | 8 of its 12 logs are ACL-locked (owner `CodexSandboxOffline`, Users lack Delete); without force the worktree cannot be removed | **kept** — content preserved in `main`; needs an administrator to clear the sandbox ACL, then `git worktree remove` |
| `hybrid-session4b-integration` | is the `main` checkout used for this record; removed after this commit (junction first, no force) | see the final report of the session |

Branches kept (`research/hybrid-backend-integration-session1`, `…-session2-contract`, `…-session3-contract-v2`,
`research/hybrid-session4a-readiness`, `research/hybrid-session4b-integration`): all are merged into `main`, but
`main` exists only locally (not pushed), so they stay as redundant refs; `git branch -d` is safe once `main` is pushed.

Not touched (inventory and proposals in `SAFE_WORKTREE_CLEANUP_REPORT.md`): frontend/scene3d worktrees, the ~7 GB
unregistered directories, other campaigns' worktrees, the root checkout.

Disk D: free (MB): 17,093 before this step → 20,817 after S2/S3 → 22,658 after S4A.
