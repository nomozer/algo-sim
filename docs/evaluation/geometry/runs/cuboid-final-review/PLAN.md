# cuboid-final-review — plan

`COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE` · closing run of the work `cuboid-visual-semantic-closure` after
W20 (no new W number; W1–W20 keep their names). Executed inline (one agent, no subagents). Ledger:
`.superpowers/sdd/cuboid-final-review/progress.md` (git-ignored). Spec: the task brief.

**Start.** Branch `fix/cuboid-visual-semantic-closure`, START_HEAD `4048ff83d14ad2a1fcd940d127590ca777dbc7cf`,
`origin/main` `a9492ee9…` (= `git ls-remote`, ancestor; the branch is 261 commits ahead and not on the remote).
Candidate `27c31de6…` and `CACHE_VERSION` 111 verified before any change; `LLM_ONLY`. Working tree: the user's
unstaged deletion of `frontend/public/favicon.svg` only — never staged, restored or committed.

**Constraints.** 0 live provider calls. No push, merge or branch deletion without explicit visual approval. No
force-push, amend, rebase or history rewrite. Stage by explicit path. Never read secrets or settings backups.
Historical reports, run artifacts, manifests and frozen evidence keep bytes and paths. No new family, OCR, multi-solid,
kernel or grounding-vocabulary work; the nine UI requests stay in ROADMAP, not implemented.

## Tasks

| # | Task | Done when |
|---|---|---|
| 1 | **Full docs inventory.** Every tracked file under `docs/` plus `AGENTS.md`, `README.md`, `DESIGN.md`: group, referrers (living vs frozen), dead links, authority, class (KEEP_CURRENT · KEEP_RESEARCH · KEEP_ARCHITECTURAL_HISTORY · MERGE_INTO_CANONICAL · DELETE_VERIFIED_DUPLICATE · DELETE_ABANDONED_OUT_OF_SCOPE · DELETE_REPRODUCIBLE_TEMP · REVIEW_REQUIRED · FROZEN_KEEP) with a reason. Script: `diagnostics/inventory_docs_cfr.py`. | `inventory/DOCS_INVENTORY.json` covers every file |
| 2 | **Act on the inventory.** Fix the dead pointers of living docs (absolute `file:///` links in research); split verbatim history out of the mixed living docs with clear pointers — CODE_INDEX (entries of code that no longer exists), STATUS_LEDGER (informatics-era status tables), COVERAGE (informatics-era sections; §2 and §5 stay, product code cites them); scope banner + factual fixes in DESIGN_BRIEF; stale examples in OPERATIONS/TEST_TIERS; delete only verified duplicates or reproducible temp. Each move/delete: exact path, reason, evidence, recovery, hash check right before. | docs audit + docs tests + code-index sync green; 0 dead links in living docs; history split byte-verified |
| 3 | **Wave numbering per work.** `docs/evaluation/RUN_NAMING.md` + short pointers in AGENTS/RULES: waves numbered within a work, new work on a new branch starts at W1, full id `<task-slug>-wNN`, short folder names, date/branch/commit/candidate inside, slug stable after the branch is deleted, W1–W20 not renamed, new work branches only from an integrated, updated `main`. | audit + rules tests green |
| 4 | **Refusal card for `CONSTRUCTION_REPLACED_BY_COORDINATES` (TDD).** Label "chưa kiểm chứng được phép dựng" (not "hệ dựng lệch với đề bài"); short message built from structured subjects ("Hệ chưa kiểm chứng được H là hình chiếu của S lên BD, vì điểm này được đặt bằng toạ độ thay vì dựng từ quan hệ trong đề. Hệ tạm dừng để tránh đưa ra kết quả chưa kiểm chứng."), no promise that resending fixes it, no machine ids; MISMATCHED and UNVERIFIED labels unchanged; controls: unverified, mismatched, served. | RED then GREEN backend + frontend tests |
| 5 | **Browser refusal evidence, desktop + mobile**, through the production boundary (envelope from `run_pipeline`, production build): code, label, message, no scene or readout, no raw token, no overflow, no console error or exception. Only the affected refusal surface, not the six families. | `results/` + `images/` |
| 6 | **Identity.** Candidate refreeze once the product is stable (`backend/app` changes); cache decision by evidence (refusals are never cached — prove it); `LLM_ONLY`. | `--verify` exit 0; cache decision recorded |
| 7 | **Authoritative verification** in a detached clean worktree: T3 full gate, identity gates, docs audit, link check, node harness, browser refusal check; evidence hashes and `git status` before/after. | every gate green, logs in `results/` |
| 8 | **Living docs + run package.** README, docs/README, CURRENT_STATE, AI_CONTEXT_BUNDLE, OPEN_ISSUES, ROADMAP, CODE_INDEX, STATUS_LEDGER, EVIDENCE_INDEX; additive correction for W20's scope (correctness closure + bounded cleanup; full docs review here); REPORT, HANDOFF (every required field), review checklist with exact image paths. | docs audit green |
| 9 | **Human review and merge.** No approval ⇒ stop at `READY_FOR_HUMAN_VISUAL_REVIEW`. With explicit approval and green gates: merge `main` directly, gate the integrated tree, push and verify, delete the merged branch. No PR. | HANDOFF fields true |

Commits by logical change: cleanup separate from the product fix.
