# Integration — hybrid-semantic-grounding-reliability on `main`

- **Decision:** user GO in session, 2026-10-17 ("GO: ff + push + dọn"), for this integration only, asked once after
  the gates below were verified.
- **Pre-check:** after `git fetch`, `main` = `origin/main` = `1f635ed5`, unchanged since the branch was cut;
  `research/hybrid-semantic-grounding-reliability` (`bd20ac46`) descends from it. Gates at that tip: candidate
  `57c7f5db…` `--verify` MATCH, clean detached T3 at `bd2dc080` `FULL_PRODUCT_GATE_PASS`
  (`verification/t3-attempt3.json`; `bd20ac46` only adds documentation and receipts).
- **Merge:** fast-forward `main` `1f635ed5` → `bd20ac46` (8 commits: `2e08922a`, `94e56aa6`, `93c7bc97`, `94b3437b`,
  `b2154454`, `b4be4b98`, `bd2dc080`, `bd20ac46`). No rebase, no squash. Five run files created by the Codex sandbox
  could not be unlinked on checkout; they were byte-identical to the target blobs, so they were staged and the
  fast-forward then applied cleanly.
- **Push:** `git push origin main` without force; `git ls-remote origin refs/heads/main` = `bd20ac465fdbb49abf8519810765c966f38bc057`.
- **Cleanup:** `git branch -d research/hybrid-semantic-grounding-reliability` (merged by ancestry). The verification
  worktree's `frontend/node_modules` junction was unlinked alone with `rmdir` (target checked intact), then
  `git worktree remove .superpowers/worktrees/semantic-grounding-base-20261017` deregistered it but could not delete
  the folder. The leftover folder holds only a copy of committed files plus ignored build/test output; its deletion
  was not approved in this session and it remains. No remote branch deleted.
- **Kept:** `docs/real-model-e2e-readiness`, `feat/real-model-pilot-tooling`, `research/compact-geometry-dsl` (out of
  scope); `.superpowers/worktrees/goal-bounded`, `goal-fixed` and `backend/.tmp/pytest-*` (Codex sandbox ACL debt);
  untracked `frontend/public/` (user data).
- **Not implied:** Hybrid product enablement (NO-GO), live extraction (NOT_MEASURED), human held-out wording,
  general Vietnamese understanding. `LLM_ONLY`, `CACHE_VERSION = 125` unchanged.
