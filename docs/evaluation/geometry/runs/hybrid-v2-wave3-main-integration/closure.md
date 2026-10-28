# Integration push and cleanup closure

Task: `HYBRID_V2_WAVE3_EVIDENCE_W3_F1_MAIN_INTEGRATION` · 2026-10-28.

**Operational status: `MERGED_PUSHED_VERIFIED_CLEANUP_COMPLETED`.** The integration was published and verified at `0a89dcace74b38ed87f5ab95c82b5aeeba835410`; this append-only closure commit publishes the cleanup receipts. Its final SHA and three-way equality are emitted in the session handoff after its normal push, avoiding a self-referential commit hash.

[Integration report](report.md) records the baseline, source/product/candidate SHAs, correction, Stage A/B merge modes and parents, all pre-push verification and limitations. Stage A: fast-forward `0943f0ee`. Stage B: normal merge `1ee44b89dc593ebc544a4fd6af96f698ff2bf4d7`, parents `0943f0ee6bd2a2b297827e39fa7c07054d716ea9` and `85f819f02971f31b193dac9be7a56dbe79362e2a`.

## Publication and safe cleanup

Normal `git push origin main` advanced GitHub from `e137623c` to `0a89dcac`. A subsequent fetch and remote query confirmed **local main = origin/main = GitHub main = `0a89dcace74b38ed87f5ab95c82b5aeeba835410`** before any cleanup. No force, squash, rebase, history rewrite or remote branch deletion was used.

[Cleanup receipt](verification/post-cleanup/cleanup.json):

| Worktree under `.superpowers/worktrees/` | Result | Local branch |
|---|---|---|
| `independent-section-holdout-wave3` | Removed, no residual | `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3` deleted with `-d` |
| `w3-f1-cross-sentence-plane-grounding` | Removed, no residual | `research/hybrid-v2-w3-f1-cross-sentence-plane-grounding` deleted with `-d` |
| `w3-f1-integration-verification` | Removed, no residual | Detached candidate; no branch |

The original W3-F1 T3 detached checkout was **not registered at preflight**; no path was guessed. The third row is the clean detached checkout created by this task at `b02b2c42` to independently verify the frozen product. Its candidate is an ancestor of main and the original T3 receipt is preserved on main.

All three worktrees were clean, their HEADs were ancestors of published main, no matching worker process was found, and no dependency junction/reparse point existed. Initial sandbox-only read restrictions were resolved with a scoped normal-user audit; no ACL was changed. Every ignored file was preserved before removal: **92 + 679 + 1 = 772 files**, including local SQLite files and test scratch data. Hash-verified ZIP archives and complete per-file inventories remain local in `.superpowers/backups/wave3-main-integration/<worktree>/`. Archive checksums and paths are in the receipt. These backups were not published because they preserve local data.

Worktrees were removed with `git worktree remove`, without force; branches were deleted only after successful removal. **ACL residuals: none. Skipped scoped worktrees: none.** All six unrelated historical/active worktrees remain registered and protected. This task did not alter their files, branches or HEADs.

## Post-cleanup verification

- [Product and evidence](verification/post-cleanup/product-and-evidence.json): **118/118 measured files MATCH**, full backend/app + frontend/src diff against frozen T3 candidate is empty; freeze **`918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72`**.
- Historical Wave 3: **31/31 Git blobs byte-identical**, checkout LF hashes match; original `20/72`, `72/72`, `0/144` and classification retained.
- Original W3-F1 run diff contains only three new correction/archive artifacts; all original run files and T3 receipt are unchanged. Original T3 raw log decompresses to the exact receipt SHA-256 `885333241d4d723d73edad5b8f2e98ccf3da0700361fbe4eb974893037ddb2f7`.
- [Candidate divergence](verification/post-cleanup/divergence.json): VALID, terminal declaration is W3-F1 and matches product `a609c487` and freeze `918d3404…`.
- [Gates](verification/post-cleanup/gates.json): freeze/cache130 MATCH, 41/41 preview fixtures, docs IA PASS, publication PASS. The final closure range is scanned again after commit, before its push.
- [Replay after worktree removal](verification/post-cleanup/wave3-post-feedback-replay.json): all 144 cases exactly match locked W3-F1 results, **29/72 positive served-correct, 72/72 negative refused, 62/72 correct reasons, 0/144 wrong-served**. Classification remains `POST_FEEDBACK_DEVELOPMENT_REGRESSION`.
- Root Python executable, pyvenv configuration and frontend node_modules fingerprints match their pre-cleanup values. Root Vite 6.4.3 and Vitest 4.1.10 remain readable and the Python environment executes the verification gates. Root dependencies were never linked away or deleted.
- Post-merge smoke remains **890 passed / 5 expected xfails / zero failed**. No product changes occurred afterward, so the existing Full T3 receipt remains applicable without a rerun.

For a fresh replay after cleanup, use `backend/.venv/Scripts/python.exe -B docs/evaluation/geometry/runs/hybrid-v2-wave3-main-integration/tools/replay.py --out <new-output-path>`. The small wrapper reuses the existing locked scorer and W3-F1 replay function, points them to the historical package on main, blocks outbound sockets and refuses existing output paths or writes inside either locked source run. It was verified after all research worktrees were removed. No duplicate scorer or product module was created.

**Remaining limitations:** 43 positive false refusals (F2 21, F3 16, F4 5, F5 1), ten negative reason disagreements; procedural AI independence only; no new blind holdout or live extraction result. `DEFAULT_MODE=LLM_ONLY`, Hybrid opt-in, cache130 and `ALLOW_LIVE_AI=0` remain; live provider calls **0**. No F2–F5 repair or production migration was opened.
