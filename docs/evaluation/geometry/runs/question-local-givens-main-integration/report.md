# Question-local givens — main integration, push and cleanup, LOCAL Windows, 2026-10-12

The user authorized, for this task only: fast-forward `research/question-local-givens` into `main`, commit the approved
SessionStart change, push `main` and delete merged branches. No force, no Hybrid enablement, no live model.

## Integration

- Preflight: `main` `232c1225`, `origin/main` `a6e27a78` (fetch and `git ls-remote` agree), branch tip `5fe14001`;
  `main` an ancestor, 44 files changed, no overlap with `.claude/` or the user's untracked `frontend/public/`.
  `docs/evaluation` changes: 30 additions plus the current-candidate file; no historical receipt modified.
- `git merge --ff-only research/question-local-givens`: `232c1225` → `5fe14001`. No merge commit, rebase or cherry-pick.
- `ebe4e463 chore(claude)`: `.claude/settings.json` only — `AGENTS.md` listed first in the SessionStart reading order.
  JSON parses; SessionStart prints the new line (exit 0); Bash guard still denies, Edit guard still prints
  CODE_INDEX; `node --test "scripts/*.node-test.mjs"` 112 passed. No secret or machine path in the diff.
- `git push origin main`: `a6e27a78..ebe4e463`, fast-forward, 41 commits. Afterwards `main`, `origin/main` and
  `git ls-remote origin refs/heads/main` are all `ebe4e4631fcc7a009003455465a9f3ec68d68c4c`. Before the push: no
  key-pattern addition and no `frontend/public/`, `CLAUDE.md`, `.env` or database in the pushed range.

## Verification (clean detached worktree at `5fe14001`)

- Candidate `25c85eed5e7433b0…`, 110 files: `--verify` PASS (also on the main checkout after the fast-forward).
- Question-local givens regressions 256 passed; Hybrid/geometry-functions cluster (19 files) 972 passed / 5 xfailed;
  provider pins A `912b22ef…`, B `396f1c9c…`, declarations `f2ec9698…` and divergence chain 120 passed; docs/identity 45 passed.
- Benchmark 30 cases, both arms 19/9/0/2, metrics SHA256 `febb5b60…` byte-identical.
- T3: **FULL_PRODUCT_GATE_PASS**, exit 0; backend 8764 passed / 1 skipped / 2 deselected / 5 xfailed; frontend 1053
  passed (68 files); typecheck/build PASS; demo 5/5; crash surface PASS. `verification/t3.log` SHA256
  `ca42fdda58621bc887ee0ef62130d9ed2917f5cb4cc05e3080c6c05427e9a772`.
- `CACHE_VERSION` 125, default `LLM_ONLY`, Hybrid not wired into `/api/analyze`; renderer unchanged, so no new
  Playwright pass. LIVE requests = 0.

## Cleanup

- Deleted with `git branch -d` after each tip was verified inside `origin/main`, with no worktree, tool or test
  consumer: `research/hybrid-simulation-capability-audit` (`9cfd0fca`), `research/hybrid-semantic-hardening`
  (`22edf7ff`), `research/question-local-givens` (`5fe14001`). The protective-ref condition in
  `../hybrid-main-integration/report.md` ("until a separately approved push") is met. Branches 7 → 4.
- Worktrees 3 → 2 registered (main, `dsl-spike`). This task's verification worktree removed after its node_modules
  junction was detached (target intact), 1,705,992,479 bytes. `question-local-givens` was deregistered by
  `git worktree remove`, but its directory (≈1.69 GB: tracked files now on `origin/main`, caches, an empty test
  database, a `.pytest_cache` unreadable to this account, part owned by CodexSandboxOffline) could not be deleted;
  the recursive delete was refused by the permission policy. Left in place, no ACL change.
- Kept: `research/compact-geometry-dsl` and `dsl-spike` (HOLD); `feat/real-model-pilot-tooling` (`471a2c79`, live
  Gemini evidence not on any remote); `docs/real-model-e2e-readiness` (on its remote, contained in the pilot branch;
  removable once that branch is pushed or retired). Locked A/B evidence, old scratch/databases, CodexSandboxOffline
  `geometry-library-expansion` and `frontend/public/` untouched.

Open: same-sentence unmarked change after "sau đó"/"rồi" (`ISSUE-ARCH-HYBRID-QUESTION-LOCAL-GIVENS`), B27/B28,
orbit P1, DSL HOLD. No live-model or default-mode GO.
