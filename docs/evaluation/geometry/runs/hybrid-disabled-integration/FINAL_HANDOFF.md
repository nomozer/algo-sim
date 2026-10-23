# Final handoff — Backend Hybrid disabled integration

Date 2026-10-23. Branch `research/hybrid-session4b-integration`, worktree
`.superpowers/worktrees/hybrid-session4b-integration`. Not merged, not pushed.

```text
STATUS                      = BACKEND_HYBRID_INTEGRATION_CANDIDATE_READY_FOR_OWNER_GO_MAIN
PRODUCTION_REPLACEMENT      = NO-GO
LIVE_PROVIDER_EVALUATION    = NOT_AUTHORIZED
MAIN_MERGE_PUSH             = NOT_AUTHORIZED
FRONTEND_CONSUMER (/4)      = FRONTEND_CONSUMER_ACCEPTANCE_OPEN (no caller exists; fixtures provided)
INVARIANTS                  = LLM_ONLY · flat · Hybrid NO-GO · ALLOW_LIVE_AI 0 · CACHE_VERSION 127 (no bump) · MAX_MEMORY_DECLARATIONS 32
CANDIDATE / T3 TARGET       = 2bbad1f2715c367736b4a5d783551b94b45fbb79 — FULL_PRODUCT_GATE_PASS, post-T3 lock MATCH
PRODUCT COMMIT              = 69bd2fe48be1fd3afa6ce4112ccddda92a07d850
MEASURED SYSTEM             = 413ee525d20874aa346b13df7e51019266f7d4701af56719c2a2ee736266b5df (116 entries, recomputed)
REVIEW                      = round 1 PASS @ b99f6420 · round 2 PASS @ 2bbad1f2
MODEL CALLS                 = 0
```

Read in order: [BACKEND_HYBRID_INTEGRATION_REPORT.md](BACKEND_HYBRID_INTEGRATION_REPORT.md) ·
[COMBINED_CONTRACT_COMPATIBILITY_MATRIX.md](COMBINED_CONTRACT_COMPATIBILITY_MATRIX.md) ·
[BACKEND_HYBRID_REMAINING_GAPS.md](BACKEND_HYBRID_REMAINING_GAPS.md) ·
[INDEPENDENT_REVIEW.md](INDEPENDENT_REVIEW.md) · [SAFE_WORKTREE_CLEANUP_REPORT.md](SAFE_WORKTREE_CLEANUP_REPORT.md).
Machine provenance: [run.json](run.json), `verification/full-t3/`, `results/`.

## Commits on top of `main` (`f10e6283`)

`561958fc` merge Session 3 · `14cdc25a` merge Session 4A · `84cd09e3` gateway docs sync · `b99f6420` verification
receipts · `2bbad1f2` review remediation (candidate) · final docs commit (this file; docs and receipts only — no
product path, so the T3 receipt still describes the product bytes; the docs gate was re-run on it).

## Conditions for the owner to allow merging into `main`

1. Owner reads the five reports above and accepts the scope: research code merged **disabled**; `/4` without a
   caller; `FRONTEND_CONSUMER_ACCEPTANCE_OPEN`; known gaps (B27/B28, D2/D3 xfails, hexagon IR cap, curved/qualified
   refusals on `/2`) are not blockers for a disabled merge.
2. `main` is still `f10e6283` (or `origin/main` `43247c9e` + that commit). If `main` moved, re-merge or fast-forward
   check, and if any product path changed on `main`, re-freeze and run a new Full T3 on the new candidate — this
   receipt does not cover a different tree.
3. Merge with `--ff-only` from this branch (it already contains `main`), so the reviewed and measured SHAs stay
   reachable; run `git log -1 --format=%B | grep -c Co-Authored-By` = 0; push only with explicit owner permission.
4. After merge: `freeze_evaluation_candidate.py --verify` MATCH on `main`; docs gate green.
5. Do not delete Session 1–3/4A branches until merged into `main`; commit or archive the untracked S1/S2 verification
   logs before removing their worktrees.

Not part of a GO main: production activation, default switch, `/4` caller, live pilot (needs its own owner GO per
`hybrid-session4a-readiness/OWNER_LIVE_EVALUATION_DECISION.md`), independent holdout.

## Workspace state

Root workspace untouched (7 pre-existing untracked entries). Removed five Hybrid temp worktrees and this run's T3
worktree; ~3.8 MB ACL-locked `.pyc` residue left. Disk D: 9,676 MB free at start → 18,948 after cleanup →
17,094 MB at hand-off (the integration worktree remains). Proposals for other worktrees are in the cleanup report;
none executed.

Next action: owner disposition on GO main for this candidate. No Session 4C/5 work was started.
