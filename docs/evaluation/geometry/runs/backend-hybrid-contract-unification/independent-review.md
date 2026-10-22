# Independent review — product `3553e4d4` (round 1)

Reviewer: a separate agent with fresh context, read-only, no repo edits; probes in the session scratch directory (not
committed). Scope: `git diff 82d3d255 3553e4d4`. Verdict: **`INDEPENDENT_REVIEW_PASS`** — 0 BLOCKER, 2 IMPORTANT, 3 MINOR.

## Findings and disposition

| # | sev | finding | disposition |
|---|---|---|---|
| 1 | IMPORTANT | The shared gate gives a verdict on **0 of the 7** Adapter /3 dev-corpus cases still served — all are `adapter3.substring_legacy` (`UNKNOWN_VERTEX_REF` ×2, `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` ×1, `BRIDGE_CUT_EDGES_NOT_STATED` ×4). Given their complete boundary as `cut_edges`, A3-DEV-03/04/06/09 become REFUSED `SOURCE_OBJECT_MISMATCH` (gate grammar does not bind "Dựng …, thiết diện bởi (α)"), so omitting `cut_edges` avoids the stricter gate. Refusal-only, no wrong serve. | **Reproduced** (main session re-ran the probe). Stated in `report.md` §P2 and §Answers 4; folded into D2/D3 of `CONTRACT_DECISION_PROPOSAL.md`. |
| 2 | IMPORTANT | The A3-DEV-10 correction asserted a known FALSE refusal as expected, giving no signal when the grammar is fixed. | **Fixed** (test-only): A3-DEV-10 and A3-DEV-03/04/06/09-with-complete-boundary are `xfail(strict=True)` in `test_typedfact_next_adapter3.py::test_gate_grammar_false_refusals_are_known_not_expected`; 07/08 (source defect) and 11 (code order) stay as corrections. |
| 3 | MINOR | `_shared_source_gate` maps `KeyError`/`TypeError` raised inside `lap_ke_hoach` (not only input parsing) to `INVALID_TYPED_FACT_NEXT`, which can hide a planner bug as an input error. Fails closed. | Recorded, not changed (would need a product change + re-freeze for a fail-closed path). Follow-up: narrow the `except` to `bridge()`. |
| 4 | MINOR | `gop_doi_tuong_trung` renames by exact string over all fields of later statements; safe because only `derived_<pt>_{line,plane}` names are dropped, but nothing enforces that. | Recorded. |
| 5 | MINOR (pre-existing) | Adapter /3 `run()` only catches `TuChoi`; 2223 payload mutations raised TypeError ×130, AttributeError ×170, TypedFactNextValidationError ×48, IndexError ×34, KeyError ×30 from `_compile_premises` / `parse_qualified_ref` — none through `_shared_source_gate`. | Recorded as a pre-existing Adapter /3 crash surface (not introduced here); follow-up issue. |

## Checks the reviewer reports as passing

- Closure certificate: incidence-only (affine-invariant), runs for every derived section before anything is served; true /
  reversed / rotated orders served, crossed / partial refused, with and without the gate (plane ∥ (SBC) probe crossing
  base edges); prism served with certificate when the gate is stubbed.
- Dedup: key covers the full operand schema; first occurrence always earlier; renaming before keying resolves chains;
  352 payloads × 2 routes and a merge-on/merge-off comparison show 0 answer / final-memory differences.
- Wiring: gate is the first statement of the polyhedral `try`; mixed curved+polyhedral goes to the curved route, labelled.
- Test edits other than #2 are sound; governance constants and frozen surfaces untouched; 0 `Co-Authored-By`.
- Reviewer's runs: requested 7 files 192 passed / 1 xfailed; 49 related test files 3566 passed / 10 xfailed.
- Not verified by the reviewer: the 9/49 budget recovery (measured by the main session in `session1-family-replay.json`).
