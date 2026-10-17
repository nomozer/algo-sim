# Integration — independent-nlu-extraction-evaluation on `main`

- **Decision:** owner GO INTEGRATION in session, 2026-10-17, for this run only.
- **Pre-check:** after `git fetch`, `main` = `origin/main` = remote = `76dca142`, an ancestor of the research branch tip
  `b22c2269`; exactly 3 commits (`6255a743` preregistration, `a9724519` live pilot, `b22c2269` locked baseline + review);
  working tree clean except the owner's untracked `frontend/public/`; scope 48 files, 0 under `backend/app` or `frontend`
  (only run documents, `backend/scripts/run_nlu_extraction_evaluation.py`, its test and the docs-audit allowlist).
- **Gates at the tip:** full backend pytest 10,263 passed / 0 failed / 9 xfailed / 1 skipped (offline); docs gate and
  harness tests pass; candidate `57c7f5db…` `--verify` MATCH (no product change ⇒ no refreeze, T3 not required).
- **Merge:** fast-forward `main` `76dca142` → `b22c2269` with `git fetch . HEAD:main` (refuses non-fast-forward). No
  rebase, no squash.
- **Push:** `git push origin main` without force; `git ls-remote origin refs/heads/main` = `b22c2269dbaced227ea89b4d191ff5b0634bba0c`.
- **Cleanup:** `git branch -d research/independent-nlu-extraction-evaluation` (merged by ancestry). No worktree existed for
  it (work was done in the main checkout). No remote branch deleted.
- **Kept:** `research/scene3d-educational-finalization` and its worktree (created outside this session), `docs/real-model-e2e-readiness`,
  `feat/real-model-pilot-tooling`, `research/compact-geometry-dsl`; untracked `frontend/public/`. Environment residuals owned
  by `CodexSandboxOffline` unchanged (`report.md`, "Environment residuals").
- **Results preserved as recorded:** locked answer under the frozen scorer **UNSAFE**; correction layer beside it
  (independently reviewed) **P1 PASS, P2 NO**. Nothing re-scored or re-run during integration.
- **Not implied:** Hybrid product enablement (NO-GO), `LLM_ONLY` unchanged, `CACHE_VERSION = 125`, no prompt/schema/model
  change, no human validation of labels.
