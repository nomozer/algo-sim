# Independent review — goal-directed function composition

Reviewer: independent read-only subagent (no repository writes, no live calls). Scope: `ce5b2575..HEAD`.

## Round 1 — at HEAD `452a398a` (product `a45a043f`, candidate `594870fc`): `INDEPENDENT_REVIEW_FAIL` (0 blocker, 1 important)

The reviewer found no wrong serve and no ungrounded construction in ~50 adversarial `run_fact_route` probes (HEAD and a
`git archive` of `ce5b2575`, scratch only), 209 + 579 + 5 targeted tests passed, freeze `--verify` MATCH, holdout /
oracle hashes match the lock, 0 `Co-Authored-By` trailers.

| # | Severity | Finding | Disposition |
|---|---|---|---|
| I-1 | IMPORTANT | The "rule-based" arm is the production planner with described points refused — an ablation equal to `no-composition` on every aggregate; report §0 used it as comparative evidence, and the "novel" combinations come from contracts added in this wave | report §0/§4 restated against `pre-composition-main` (the only independent baseline), arms named ablations, novelty attributed to this wave's contracts, data-toggle evidence cited; harness docstring corrected. Arm ids kept in `results/` for traceability |
| N-1 | NONBLOCKING | A described length/angle goal followed by a second ask in the same sentence was served with the second ask silently dropped ("với" inside the object phrase read as a given marker); pre-existing for length, extended to angles | **fixed** in product `b70e4769` (`_duoc_hoi`/`_vung_hoi` read markers on `_bo_cum(...)`), RED 3/3 → GREEN, candidate refrozen `3a57f5d3`, evaluation re-run on the final candidate: identical metrics |
| N-2 | NONBLOCKING | Holdout authored by the implementer after the code; lock-to-commit window (~56 min) not checkable from git; holdout wordings are the author's closed grammar | stated in report §0 (no language-generalisation claim) |
| N-3 | NONBLOCKING | `FUNCTION_NOT_OFFERED` only in route A `parse_response`; no preview refusal class | recorded in report §10 |
| N-4 | NONBLOCKING | The blocker-row code override lives in three ad-hoc dicts | recorded in report §10; every override still requires REFUSED with no answer and no scene |

## Round 2

Pending — re-review of the fixes on the final candidate.
