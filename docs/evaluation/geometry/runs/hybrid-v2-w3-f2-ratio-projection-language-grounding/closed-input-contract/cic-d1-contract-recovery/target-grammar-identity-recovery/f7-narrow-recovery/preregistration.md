# Preregistration: F7 narrow repair, R1/R2 test-only closure

This was locked at research HEAD `1b1a9ed2`, before any product edit. It is a development security regression, not a
blind holdout, with 0 provider calls. Owner decisions: D1 F7 narrow repair; D2 R1/R2 test only; D3 R3 deferred;
D4 publication not approved.

**Inputs.** `cases.json` (47 cases) is built by `tools/build_cases.py` from committed sources only:
- the parent `cases.json`;
- the existing exact oracle in `observed-green.json` (product `6a09c06a`);
- the independent reviewer's `pre-freeze-review/probes.json` and `out-head.json`.

`registration.json` fixes the LF SHA-256 of the inputs and of the initial test file.

**Expected outcomes.** They come from the contract and the existing oracle, not from the runtime under test:
- **F7.** All 8 prism cells and 3 pyramid cells (`radius {solid}`, `radius {section_id}`, `lateral_area {solid}`) must
  be schema-valid on /1 and /2 and `REFUSED BRIDGE_UNSUPPORTED_MEASUREMENT` on a3, pl and a4. The two mixed goal lists
  must be refused whole on a3 with that code, with no answers or scene.
- **F7 negatives.** They keep their semantic codes (`INVALID_MATH_GOAL`, `UNKNOWN_SOLID`, `UNKNOWN_SOLID_ID`) on
  every route. A blank operand gives `INVALID_MATH_GOAL`.
- **Controls.** These are prism distance, the pyramid section area, the pyramid ratio/residual/section/volume set, and
  cylinder, cone and sphere volume, radius and lateral area. They keep their schema result, every route
  status/code, and their exact a3 answers.
- **L-AREA.** Polyhedral `area {solid}` stays `INVALID_MATH_GOAL` on a3. This is a pre-existing typed refusal,
  recorded and not changed.
- **No internal errors.** No case returns `ADAPTER_INTERNAL_ERROR` or `ROUTE_INTERNAL_ERROR` on any route.

**R1 (test only).**
- The cases `ghost::A` repeated with `A` in either order (`UNKNOWN_SOLID_ID`), foreign ownership `pr::B, B` with goal
  `solid_id: other` (`SOURCE_OBJECT_MISMATCH`), and the same-point alias under `pr` (`INVALID_MATH_GOAL`) must all
  refuse at the payload layer while the child `MathGoalSpec` accepts them.
- The two positives (`pyr1::D`/`pyr2::D`, `pyr1::D`/`S`) must be served with the reviewer's independently observed
  exact answers.
- A behavioural mutant that runs the identity check before the namespace/ownership check must fail the oracle.

**R2 (test only).**
- Setup: two root solids, plus a derived `top_pyramid` of `main_pyramid`. The second root binds `S -> T`.
- `top_pyramid::S` and scoped `S` must resolve to `main_pyramid::S`, never to `other::S`. Unscoped `S` must give
  `AMBIGUOUS_REFERENCE`.
- Derived aliases of the parent give `INVALID_MATH_GOAL`. The constructed `M` with derived `S` is schema-valid, and so
  is `top::S` with `other::S`.
- Schema-valid R2 inputs are not served on any route by an incomplete fixture: they are refused cleanly, with no
  internal error. The single-root control is served at `1·a`.
- Both derived-parent mutants must fail the oracle.
- If every R2 test passes before any product edit, R1/R2 are recorded as `TEST_GAP_CLOSED`. Any R1/R2 failure is a new
  finding and triggers STOP.

**Mutation guards for F7.**
- Removing the new terminal refusal must make the prism radius oracle fail.
- A planted `KeyError` must still surface as `ADAPTER_INTERNAL_ERROR`; there is no generic masking.

**RED expectation.** Only F7 cases fail, and they fail by returning `ADAPTER_INTERNAL_ERROR`. The F7 mutation test
also fails at RED because its source anchor does not exist yet. All other tests pass, R1/R2 included.

**Excluded.** R3 (deferred minor, not closed), publication exceptions, the Registry, the Planner, the kernel, the UI,
history edits and `CACHE_VERSION` (130).
