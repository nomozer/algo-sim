# Integration — scene3d-visual-correctness on `main`

- **Decision:** user GO in session, 2026-10-17 ("GO: ff + push + dọn"), for this integration only.
- **Pre-check:** after `git fetch`, `main` = `origin/main` = `6d8ead99`, unchanged since the branch was cut;
  `integration/scene3d-visual-correctness` (`ee9689e6`) descends from it and contains `research/scene3d-visual-correctness`
  (`0ef0a20a`). Gates at that tip: candidate `43e877ed…` `--verify` MATCH, clean detached T3 at `0a33fcc8`
  `FULL_PRODUCT_GATE_PASS` (`verification/t3-pass.json`; `ee9689e6` only adds the T3 record).
- **Merge:** fast-forward `main` `6d8ead99` → `ee9689e6` (8 commits: Gemini `0ef0a20a`, merge `a7388a40`, `08021881`,
  `f07ea069`, `e460cfac`, `8f437980`, `0a33fcc8`, `ee9689e6`). No rebase, no squash.
- **Push:** `git push origin main` without force; `git ls-remote origin refs/heads/main` = `ee9689e6f73b418510f5c215d787d4e606c57a58`.
- **Cleanup:** `git branch -d integration/scene3d-visual-correctness` and `git branch -d research/scene3d-visual-correctness`
  (both merged by ancestry). `git worktree remove .superpowers/worktrees/scene3d-visual-correctness` deregistered the
  worktree (status clean, only ignored `__pycache__`), but could not delete its folder. Its `frontend/node_modules`
  was a junction to the main checkout's `node_modules`. The link alone was removed with `rmdir`, and the target was
  checked intact. Then the remaining copy of committed files was deleted. No remote branch deleted.
- **Kept:** `docs/real-model-e2e-readiness`, `feat/real-model-pilot-tooling`, `research/compact-geometry-dsl` (out of
  scope); untracked `frontend/public/` (user data). Environment residuals with Codex sandbox ACLs are unchanged
  (`report.md`, "Environment residuals").
- **Not implied:** Hybrid product enablement (NO-GO), human visual acceptance (`HUMAN_VISUAL_REVIEW_PENDING`), live extraction.
