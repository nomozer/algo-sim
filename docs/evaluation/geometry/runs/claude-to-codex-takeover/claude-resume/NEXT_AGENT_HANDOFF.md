# Next agent handoff — after the Claude resume

## Where

- Worktree `D:/Documents/projects/algo-sim/.superpowers/worktrees/s3d-hybrid-v2-claude`, branch
  `research/scene3d-hybrid-v2-claude-resume` (from Codex `e336e0df`). Run `git log --oneline e336e0df..HEAD` first.
- Do not write into `s3d-hybrid-v2` (Claude's preserved source), `s3d-hybrid-v2-codex` (Codex's tree; an idle Codex
  app-server is alive) or the root checkout (Owner's uncommitted UI work). Backups: root `.superpowers/backups/`.
- `frontend/node_modules` here is a junction to the root's; leave it. Dev server used for evidence: Vite on 3197.

## State

- Product `1faee1db`, candidate `96415cbd` (`3850e787…`). `freeze_evaluation_candidate.py --verify` must MATCH.
- Full T3: `FULL_PRODUCT_GATE_PASS` at `57a4d65c` (`t3-receipt.json`). Commits after it are docs-only; any product
  change needs a refreeze and a new T3 in a clean detached worktree (`tools/run-t3.py <worktree> <fresh out name>`).
  The detached worktree `t3-claude-resume` was left in place (no deletion without Owner approval).
- LLM_ONLY, cache130, live 0, no merge/push. Hybrid production NO-GO.

## Rules learned this session

- Git Bash `sed -i`/`cat >>` into `backend/app`, `frontend/src`, `backend/tests` slipped past the hook once — use Edit.
- `pytest -q` prints names only at the end: an interrupted run is mapped by character position onto `pytest --co -q`.
- The Adapter /2 fixture exporter refuses an uncommitted `backend/app`; commit, then `--out <new dir>`.
- New `candidate_divergence.json` layers must sit at `runs/<run>/` or `runs/<run>/inputs/` (the scanner's globs).
- Evidence dirs that hash raw bytes need a per-run `.gitattributes` `-text` before their first commit.

## Next useful work (Owner decides)

1. Owner review of `p0-after-size/` and `common-perpendicular-browser/`; decisions in `report.md` §14.
2. Hybrid slice candidates: non-right angle arc witness; four-label distance targets; independent holdout for
   skew distance (family 2).
3. LLM_ONLY common perpendicular only with a cache bump and a real legacy-row MISS test (pattern:
   `backend/tests/test_cache_right_angle_witness_invalidation.py`).
