# Handoff — W3-F2 unified solid-scope validation: NOT_READY

Branch `research/hybrid-v2-w3-f2-ratio-projection-language-grounding`, worktree
`.superpowers/worktrees/w3-f2-ratio-projection-language-grounding`; the commit containing this file is the
checkpoint (`git log -1`). main = origin/main `996f114b`. No merge, push or cleanup was done.

Read: `report.md` → `review.md` → `solid-scope-census.md` → `architecture-decision.md` → `test-adaptation-amendment.md`.

- Product `9772ea37`; candidate `cd8de398` (freeze commit `2c84558d`) with Full T3 PASS — valid regression evidence
  for that candidate only. Any product change invalidates freeze and T3: re-freeze in a separate commit (the
  divergence chain's next layer must `corrects` `runs/hybrid-v2-w3-f2-unified-solid-scope/candidate_divergence.json`,
  in a run dir whose root or `inputs/` slot is free), run T3 in a new clean detached worktree with a new output dir.
- Open: F1 (regression: hyphenated solid ids falsely refused), F2–F4 (relation kinds, simulation-goal scope,
  curved `apex_ref`/highlight refs), F5–F6 minors. Recommended fix path in `report.md` §Next step; Owner decision
  needed on `construct_object.parent_solid_id`.
- Worktrees kept: `w3-f2-adapter3-t3` (`6516d5d4`), `w3-f2-solid-scope-t3` (`55bdd332`), `w3-f2-unified-scope-t3`
  (`cd8de398`); the last two have a `frontend/node_modules` junction — remove the junction before any worktree removal.
- Environment: root `backend/.venv`, `ALLOW_LIVE_AI=0`, UTF-8, `-B`, pytest `-p no:cacheprovider` with a fresh
  `.superpowers/f2/<name>` basetemp. `frontend/dist/assets` in the research worktree is ACL-locked by an earlier Codex
  sandbox: build with `--outDir` elsewhere. T0 must run without `--dry`.
- Invariants: `LLM_ONLY` default, `CACHE_VERSION` 130, Hybrid opt-in, historical receipts and Wave 3 holdout unchanged.
