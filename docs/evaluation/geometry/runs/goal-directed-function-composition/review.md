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

## Round 2 — at HEAD `9f46a637` (product `b70e4769`, candidate `3a57f5d3`): `INDEPENDENT_REVIEW_PASS` (0 blocker, 0 important)

- I-1 resolved: report §0 compares against `pre-composition-main` only (16/16 vs 1/16), names `rule-based` / `no-composition` ablations, attributes novelty to this wave's contracts and makes no language-generalisation claim.
- N-1 resolved and general: markers read on `_bo_cum(...)`; conditionals and value assignments still read on raw text. Probes at HEAD vs a `git archive` of `452a398a`: 6 partial serves now `REQUEST_NOT_ANSWERED` (incl. a NAMED-ask hole that existed before), 2 former false refusals now serve correct values when both facts are present, 16 given/condition/value probes unchanged; controls still serve.
- Scope: `b70e4769` = `registry.py` (+4/−2) + new tests; `3a57f5d3` = candidate files only; `3a57f5d3..9f46a637` = docs + a 2-line harness docstring; 0 `Co-Authored-By`.
- Checks: 2006 targeted tests passed (22 files), freeze `--verify` MATCH (`e2109ef1…`), T3 receipt read (not re-run).

| # | Severity | Finding | Disposition |
|---|---|---|---|
| R2-N1 | NONBLOCKING | `evaluation-final-candidate/arm-pre-composition-main.json` is a byte copy of the first run (that arm runs `ce5b2575`, untouched by the fix); the final-candidate bundle has no pre arm | stated in report header and `run.json` |
| R2-N2 | NONBLOCKING (on `main`) | "Tính độ dài SC rồi so sánh với SA." serves √17 and drops the comparison (shared-ask-grammar `rồi`) at `ce5b2575`, `452a398a` and HEAD | outside this wave; recorded in `OPEN_ISSUES` |
| R2-N3 | NONBLOCKING | T3 receipt, review round 2 and handoff were uncommitted | committed with this record |
