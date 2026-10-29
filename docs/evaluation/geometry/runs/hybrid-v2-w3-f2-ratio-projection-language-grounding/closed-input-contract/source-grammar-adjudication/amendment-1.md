# Amendment 1 — acceptance manifest v1 → v2 (source-grammar adjudication)

Version: `acceptance-manifest.json` v2, superseding v1 (`../green.json#command`, test file sha256_lf `053f41f5…`).
Authority: Owner decision 2026-10-30, recorded in `owner-adjudication-addendum.md`. Registered before any test edit or
Gate A rerun. The commit that contains this file is the registration point. It precedes the commit that edits tests.

## What changes

| v1 | v2 |
|---|---|
| `test_fresh_geometry_positive_scope_aliases[4]` in the acceptance file | moved unchanged in input and expectation to `PENDING_SOURCE_GRAMMAR_SUPPORT`: `backend/tests/geometry/source_grammar_pending_diagnostics.py` reads `pending-source-grammar-controls.json`. The file is not collected by default (name outside `test_*.py`) and is run by explicit path as a diagnostic. |
| — | `test_supported_positive_controls_are_registered` (SHA-256 of the registered inputs equals the manifest) + `test_supported_positive_scope_aliases[id,notation,nested_id,goal_id]` (all three routes SERVED, `{'vol': '12'}`, Adapter /3 authority `registry.kiem_nguon`) |

Every other acceptance node, oracle, expected code and locked corpus is unchanged. No xfail, skip or deselect.
The v1 result (4 failed / 630 passed / 6 skipped) stays the recorded v1 outcome. It is not rewritten.

## Registration order (each step is a separate artifact)

1. `tools/controls.py build`: the pending inputs are rebuilt from the v1 test source at `4b361c47` and asserted equal to
   `../source-control-analysis.json#payloads`. The supported inputs are derived from them by changing two wording strings
   only (`supported-positive-controls.json#changes`).
2. Qualification, read-only, before registration: `tools/controls.py run` on clean detached `main` `996f114b` and on clean
   research HEAD `4b361c47` (receipts `qualification-*.json`; SHAs in the manifest).
3. Registration: `acceptance-manifest.json` fixes the input SHAs, expected outcomes and rationale.
4. Only then: the test edit and the Gate A rerun, reported as two results (`gate-a-v2.json`).

## Limits stated up front

- The expected outcomes of the supported controls were fixed after the qualification run on HEAD had been observed.
  Their basis is the N1 contract ("valid list + all scope aliases retain exact outcomes"), not the observation. The
  four wordings tried during diagnosis are listed in `owner-adjudication-addendum.md`. The retained wording is the
  locked supplementary control's, not one picked by trial.
- These controls are development positives, not a blind holdout.
- Supporting the pending wording would need a separately authorised change to the Registry request coverage reader.
