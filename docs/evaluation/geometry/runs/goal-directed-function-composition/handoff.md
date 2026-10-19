# Handoff — goal-directed function composition (Hybrid Wave 2A)

**Verdict: `WAVE2A_READY_FOR_GO_MAIN_REVIEW`** — stopped at the GO MAIN gate; not merged, not pushed.

## Identity

- Branch `research/hybrid-wave2a-function-composition` from `main` = `origin/main` = `ce5b2575`.
- Product `a45a043f` + `b70e4769` (review N-1 fix) · holdout lock `50ac258a` · final candidate freeze `3a57f5d3`
  (112 files, `e2109ef1cde5deaf9624acd19d19a622dc8d8e5747b749e146ad93996e728766`; superseded `594870fc` / `cddd83b8…`).
- Authoritative T3 at `9f46a637`: **`FULL_PRODUCT_GATE_PASS`** — backend 11076/0, frontend 70 files / 1146, typecheck +
  build, demo 5/5 (+1/1 reduced), crash 6/6 ([`authoritative-t3.json`](authoritative-t3.json),
  [`verification/t3-authoritative.log`](verification/t3-authoritative.log)). Superseded: `54db7183` FAIL (C2b, missing
  divergence layer), `452a398a` PASS before the N-1 fix.
- Independent review: round 1 `INDEPENDENT_REVIEW_FAIL` (I-1 overclaim) → round 2 **`INDEPENDENT_REVIEW_PASS`**
  ([`review.md`](review.md)).
- Candidate → final head: harness docstring + docs/evidence only.

## What a GO MAIN would integrate

Route D only (not wired to `/api/analyze`): `centroid` producer contract, angle goal contracts, route-B-only primitive
`ask_angle_lines`, typed goal-slot entry, independent line–line Gram verifier, slot-typed `effect-chain` gate, route A
refusal of unoffered functions, v3 research schema from goal contracts, request-coverage fix; versions
`geometry-functions/7`, `geometry-fact-planner/8`, `geometry-function-engine/6`. Cache **127** (no bump), `LLM_ONLY`,
`flat` surface unchanged, Adapter `/2` 41/41 (declared identity pairs), Hybrid product **NO-GO**, live calls **0**.

Results and limits: [`report.md`](report.md) (locked holdout 16/16 vs 1/16 for `main`; ablations; W2-EXP audit;
remaining gaps §10). Machine data: [`results/`](results/), [`run.json`](run.json).

## Owner GO MAIN steps (only after a separate `GO MAIN` in session)

Verify `main` = `origin/main` = `ce5b2575` and the branch head; `git merge --ff-only`; post-merge smoke (this run's
tests, 174 regression, fixtures, freeze `--verify`, build); `git push origin main` (no force); verify remote; preserve
evidence; `git branch -d research/hybrid-wave2a-function-composition`. No worktree of this run remains (all four
temporary worktrees removed in-task).
