# Claude handoff — W3-F2 Adapter /3 safety recovery: NOT_READY

Date 2026-10-29. Branch `research/hybrid-v2-w3-f2-ratio-projection-language-grounding` in worktree
`.superpowers/worktrees/w3-f2-ratio-projection-language-grounding`; the commit containing this file is the final
checkpoint (`git log -1`). Main / origin main remain `996f114b`. No merge, push or cleanup.

Read in order: `codex-to-claude-takeover.md` (state recovered, real stop reason), `solid-scope-recovery-report.md`
(fix, gates, replay, freeze, T3), `review-solid-scope.md` (why NOT_READY), `verification/review-solid-scope-repro.txt`.

- Product: `393864d1` (solid-valued operands vs declared scope, Bridge + Adapter /3), `c4d7b759` (N006 locked code,
  Registry /21 pins). Candidate frozen `55bdd332`; Full T3 PASS `96cd4c23`
  (`verification/full-t3-solid-scope/receipt.json`). These remain valid regression evidence for that candidate only.
- Open: review findings 1–3 (MAJOR, pre-existing on main): Adapter /4 distance/angle goal scope, Adapter /3 curved
  route scope, ratio/residual goal `solid_id`. Minor 4–6 listed in the review. Owner decisions (a)–(c) in the report §7.
- Any product change invalidates the `55bdd332` freeze and T3: re-freeze in a separate commit, run Full T3 in a new
  clean detached worktree with a new output directory (the runner refuses existing ones).
- Environment: root `backend/.venv/Scripts/python.exe`, `ALLOW_LIVE_AI=0`, UTF-8, `-B`, pytest
  `-p no:cacheprovider --basetemp=.superpowers/f2/<new>`; T0 `node scripts/impact.mjs --base main` must run for real
  (not `--dry`). Ignored dirs with Codex sandbox ACLs are unreadable; leave them. Takeover backup:
  `D:/Documents/projects/algo-sim/.superpowers/backups/w3-f2-codex-takeover-20261029/`.
- Worktrees kept: `w3-f2-adapter3-t3` (Codex's aborted T3 at `6516d5d4`), `w3-f2-solid-scope-t3` (passing T3 at
  `55bdd332`, `frontend/node_modules` is a junction — remove the junction first if the worktree is ever removed).
- Invariants: `LLM_ONLY` default, `CACHE_VERSION` 130, Hybrid opt-in, Wave 3 holdout and earlier receipts unchanged.
