# Append-only amendment to the F7/R1/R2 preregistration (`ae81b65e`)

The preregistered bytes stay in git at `ae81b65e`, and `red.json` is unchanged. Both defects below are in the test
harness and were found at RED, before any product edit. Neither changes a product expectation.

1. **Three pyramid `pl` expectations.** The cases are `F7.pyr.radius.solid`, `F7.pyr.radius.section_id` and
   `F7.pyr.lateral_area.solid`.
   - The preregistration assumed `pl` reaches measurement mapping. It does not: the base payload
     `S.demo1.area.section` is already refused on `pl` as `BRIDGE_CUT_EDGES_NOT_STATED`, per the existing exact
     oracle (`observed-green.json`, product `6a09c06a`).
   - The builder now copies that base outcome for `pl`. The a3 and a4 expectations stay
     `BRIDGE_UNSUPPORTED_MEASUREMENT`.
   - The diff to `cases.json` is exactly those three values. The input hash moves from `82dbaddf…` to `aa4e2774…`,
     and `registration.json` keeps both hashes.
2. **The R2 derived-parent `ns` mutant.**
   - The mutant was detected: the valid two-root payload was rejected as `AMBIGUOUS_REFERENCE`. But this happened
     inside `_r2()` payload parsing, so it escaped as `TypedFactNextValidationError` rather than an `AssertionError`.
   - `_r2()` now parses a goal-free copy, so the mutant fails the identity assertions themselves. The same inputs and
     the same assertions are used.
   - On the unmodified product, the real-code oracle and the `scope` mutant passed both before and after this change.
3. **Count correction to `red.json`.** `red.json` says "29 failures" for the expected F7 set. The correct count is 27:
   13 a3 route cells, 13 no-internal-error cells and 1 absent mutation anchor. The total of 31 at RED is those 27
   plus 3 `pl` harness cells and 1 R2 harness cell.

Amended RED, run on unmodified product at `ae81b65e` (`red-amended.json`): 27 failed / 214 passed. All 27 are the
preregistered F7 cells. Every R1/R2 oracle and every mutant oracle passes, so R1/R2 = `TEST_GAP_CLOSED`, with no
product change.
