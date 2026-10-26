# Local main integration

Status: NOT_STARTED_AWAITING_OWNER_VISUAL_GO. Full T3 PASS and freeze MATCH at `3d6351d8`.

Preflight main: `9978e512a8a2a087475d792c0bd9db639c36acaa`, ancestor of candidate `9b99ad40`. Root Owner checkout is on `research/hybrid-wave3a-volume-reasoning`, HEAD `fe9f5554`, with 19 modified and 60 untracked files whose hashes are recorded in `preflight.json`.

No merge or ref update to main has occurred. Before an authorized merge, recheck the current refs, ancestry, all source identities and protected hashes. Use a separate clean main worktree and fast-forward only when Full T3 PASS, freeze MATCH and explicit Owner Visual GO are all present. The established F2 exception and independent-review deferral do not replace those gates.

Post-recovery main remains `9978e512a8a2a087475d792c0bd9db639c36acaa`, still an ancestor of the recovery branch. All 79 protected Owner file hashes match. Backend/frontend/T3-tool source inventory is recorded in `source-identity.json`; final documentation annotations do not change this tested source.

## Post-merge state (Claude takeover, 2026-10-26)

Status: **`LOCAL_MAIN_INTEGRATION_VERIFIED`**. The fast-forward happened before the Codex limit:
`main@{2026-10-26 20:50:06 +0700}: merge a9889031…: Fast-forward` (from `9978e512`), checked out in
`.superpowers/worktrees/local-main-integration`. No second merge, no push (main is 226 commits ahead of `origin/main`).
Product trees at `main` equal the Full T3 candidate `3d6351d8` (`backend/app` `280ffac0…`, `frontend/src` `f61fe7e9…`;
only 12 docs files differ), so Full T3 was not repeated. Post-merge smoke: freeze `--verify` MATCH (`3850e787…`, 118
files), LLM_ONLY default + `CACHE_VERSION` tests 2/2, main worktree clean before/after, root Owner 79/79 byte-identical.
Details: `CODEX_TO_CLAUDE_RESUME.md`.
