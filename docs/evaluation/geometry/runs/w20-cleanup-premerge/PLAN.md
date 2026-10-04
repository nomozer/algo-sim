# W20 — Repository cleanup and pre-merge correctness closure — plan

Executed inline in the same session (one agent, no subagents). Ledger:
`.superpowers/sdd/w20-cleanup-premerge/progress.md` (git-ignored). Spec: the W20 brief.

**Start.** Branch `fix/cuboid-visual-semantic-closure`, START_HEAD `2cb4ed8c` (W19 END_HEAD),
`origin/main` `a9492ee9`, candidate `d3b4cab9…`, `CACHE_VERSION` 110, `DEFAULT_MODE = LLM_ONLY`,
HUMAN_VISUAL_REVIEW `NOT_APPROVED`. Working tree: the user's unstaged deletion of
`frontend/public/favicon.svg` only — never staged, restored or committed.

**Global constraints.** 0 live Gemini requests. No push, merge or branch deletion without explicit visual
approval (running this task is not approval). No force-push, rebase, amend or history rewrite. Stage by
explicit path; no `Co-Authored-By` trailer. Never read secrets or settings. Historical reports, measurement
inputs/outputs, manifests and frozen artifacts stay byte-identical; corrections go in new layers. Labels are
never changed to turn a test green. Deletions by exact path only, after reading the content and checking
references.

## Tasks

| # | Task | Done when |
|---|---|---|
| 1 | **Register the literal-target probe before any fix.** `diagnostics/literal_target_corpus/LABELS.json` (27 rows, amendment_1 before any product change) + `diagnostics/probe_literal_target.py` (production boundary: `run_pipeline` with frozen LLM stages + `route.verify_and_compile`). | committed `f0edcd11`; before = 20/27 |
| 2 | **Literal-target fix (TDD).** RED tests first in `backend/tests/geometry/test_construction_binding_literal.py`, then the fix in ONE authority, `construction_binding.py`: each program name that directly denotes a text-relation target (§16.1) is followed along its `assign X = var Y` chain; a non-seed literal anywhere on the chain (the name's own coordinates, or an alias of a point defined by coordinates, a given vertex included) ⇒ status `DEFINED_BY_COORDINATES`, reason `CONSTRUCTION_REPLACED_BY_COORDINATES` (cause CONSTRUCTION, refused in every scope, not repaired), subjects `[text relation, what the program did]`. Coordinates are never read; equal values never create identity. Learner message states verifiability, never that the text is wrong. | RED seen for the stated reason; GREEN; W18 tests unchanged and green; fault injections recorded |
| 3 | **Re-measure.** Probe `--tag after`; W20 census over the W14–W18 corpora (imports the W18 census unchanged) compared row by row with the W18 census; `replay_demo_cases.py`. Any served row newly refused is listed with the reason; any change by another stage is a regression. | probe 26/27 with C7 explained or better; 0 changes outside `construction_binding` |
| 4 | **Frozen-evidence writer.** `reconcile_second_family_live_measurement.run_reconciliation(out_dir=…)`: explicit output folder; tests pass `tmp_path`; the frozen folder is only read. Regression: hashes of the frozen folder before/after the test equal, outputs land in `tmp_path`, `git status` unchanged. | RED (test writes into the frozen folder) → GREEN |
| 5 | **AGENTS.md / RULES.md.** The six short rules of the brief (B1–B6) + "code/tests are a reproduction basis, not an authority over product requirements", without duplicating rules elsewhere and without live numbers. | docs audit + rules-hygiene tests green |
| 6 | **Cleanup.** Inventory `docs/legacy/superpowers/`, `.superpowers/`, the W19-registered temp items and a bounded, mechanically checkable part of `D:/tmp` (AlgoSim only; settings backups never opened). Classes: KEEP_ACTIVE · KEEP_ARCHITECTURAL_HISTORY · KEEP_RESEARCH_EVIDENCE · DUPLICATE_SAFE_TO_DELETE · ABANDONED_OUT_OF_SCOPE_SAFE_TO_DELETE · REPRODUCIBLE_TEMP_SAFE_TO_DELETE · REVIEW_REQUIRED. Per deletion: content read, references checked (code, tests, tooling, docs, manifests), working-tree state, unique information moved first with provenance. | `inventory/CLEANUP_INVENTORY.json` + `inventory/DELETION_LOG.json`; dead references 0 |
| 7 | **Cache and candidate.** Real-row cache proof (W18 `proof_cache_row_w18.py` pattern) for rows served `ok` before and refused now ⇒ bump 110 → 111 in one commit with every pin, else no bump with the reason. Candidate: `--verify` the old one, refreeze once after the product is stable (backend/app changed), in a detached clean worktree. | lock and candidate verify exit 0 |
| 8 | **Authoritative verification** in a detached clean worktree at the measurement commit: T3 `full-gate.mjs` (pytest, vitest, build, demo replay, crash surface), node harness tests, docs audit, schema sync ×2, candidate/cache verify, `DEFAULT_MODE` guard, probe; frozen-evidence hashes and `git status` before/after. | every gate exit 0, logs in `results/` |
| 9 | **Living docs + run package.** README, docs/README, CURRENT_STATE, AI_CONTEXT_BUNDLE, OPEN_ISSUES (close the two issues with evidence), ROADMAP (keep the 9 UI requests and the family candidates), CODE_INDEX (no dead pointer), STATUS_LEDGER, EVIDENCE_INDEX, CLAIM_EVIDENCE_MAP if a claim changes, amendment addendum §16.5; `REPORT.md`, `HANDOFF.md` (every required field), `MANIFEST.json`. | docs audit + link check green |
| 10 | **Git closure.** Merge/push/branch deletion only with both issues closed, verification clean, historical evidence unchanged AND explicit visual approval. Without approval: hand off review items, the next slice from the capability matrix checked against code, and a branch name. | HANDOFF fields filled truthfully |

## Final decision (first match)

`CORRECTNESS_CLOSURE_INCOMPLETE` (an issue not closed with evidence) · `VERIFICATION_NOT_CLEAN` (any gate red)
· `READY_FOR_HUMAN_VISUAL_REVIEW` (everything green, no visual approval) · `INTEGRATED_ON_MAIN` (approval given
and merged, pushed, branch deleted).

## Skills

writing-plans (this plan) · executing-plans (inline) · systematic-debugging (task 2 root cause, any failure)
· test-driven-development (tasks 2 and 4) · verification-before-completion (tasks 7–9) · ponytail-review
(product diff, before the freeze) · karpathy-guidelines (surgical changes). Each is recorded in HANDOFF only
if it was actually invoked.
