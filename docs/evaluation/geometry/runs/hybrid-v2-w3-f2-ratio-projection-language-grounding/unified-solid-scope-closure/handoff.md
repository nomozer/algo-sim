# Handoff — W3-F2 scope census closure: NOT_READY (stopped at pre-freeze review)

Branch `research/hybrid-v2-w3-f2-ratio-projection-language-grounding`, worktree
`.superpowers/worktrees/w3-f2-ratio-projection-language-grounding`; the commit containing this file is the checkpoint
(`git log -1`). main = origin/main `996f114b`. No merge, push, cleanup, freeze or Full T3 in this task.

Read: `report.md` → `pre-freeze-review.md` → `architecture-amendment.md` → `preregistration.md` (+ amendment 1) →
`test-adaptation-amendment.md`.

- Product `1262fbd5` (closure) is NOT frozen. The current `EVALUATION_CANDIDATE.json` still points at `9772ea37`
  (candidate `2c84558d`), so freeze-identity tests are red on this tree by design until a new freeze; the last
  divergence layer is `runs/hybrid-v2-w3-f2-unified-solid-scope/candidate_divergence.json`.
- Open: N1–N4 MAJOR, N5–N6 MINOR, N7 note (`pre-freeze-review.md`); recommended path in `report.md` §Next step.
- Coverage gate: `backend/tests/geometry/test_scope_census_closure.py::test_census_inventory_complete` reads
  `schema-field-inventory-v2.json`; extend the census (`backend/tests/geometry/scope_field_census.py`) and regenerate a
  new inventory version with `tools/build_inventory.py <version>` (exclusive-create, earlier versions kept).
- Worktrees kept: `w3-f2-adapter3-t3` (`6516d5d4`), `w3-f2-solid-scope-t3` (`55bdd332`), `w3-f2-unified-scope-t3`
  (`cd8de398`) — the last two have a `frontend/node_modules` junction; remove the junction before any removal.
- Environment: root `backend/.venv`, `ALLOW_LIVE_AI=0`, UTF-8, `-B`, pytest `-p no:cacheprovider` with a fresh
  `.superpowers/f2/<name>` basetemp; `frontend/dist/assets` is ACL-locked (build with `--outDir`); T0 without `--dry`;
  baselines are compared by `git archive <sha> backend` into scratch (never `rm -rf` in the session).
- Invariants: `LLM_ONLY` default, `CACHE_VERSION` 130, Hybrid opt-in, historical receipts unchanged.
