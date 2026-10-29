# N2 amendment (version 2) — supplementary ownership tests under the locked V2 grammar

Authority: Owner GO §4 (supplementary N2 tests only; the locked V2 test is untouched).

## Superseded (v1)

`test_closed_input_contract.py::test_legacy_constructed_ownership_precedes_capability[{False,True}-solid_id]` and
`[...-solid]`. They put `solid_id`/`solid` **inside** a distance target. That form breaks the locked V2 grammar, so
`INVALID_MATH_GOAL` would be the correct first refusal and the test could no longer observe S8.
- Their inputs are kept verbatim as `cases.json#N2v1.*`, with the v1 expectation `SOURCE_OBJECT_MISMATCH`.
- Their v1 PASS is in `../source-grammar-adjudication/gate-a-v2-acceptance.log`.
- Their post-fix outcome is recorded in `green.json`. Nothing is deleted.

The `[goal]` parameter (goal-level `solid_id`) is still valid and stays.

## Replacement (v2): `test_cic_d1_locked_contract.py`

Structurally valid inputs: A3-DEV-02 plus M, the midpoint of SB, constructed in `pyr1`. The measurement goal is
`{segment: [...]}`, and no scope key appears inside the target.

| case | ownership assertion | expected on a3, pl, a4 |
|---|---|---|
| `N2v2.goal_solid_id` | `MathGoalSpec.solid_id = pyr2`, `[M, B]` | `SOURCE_OBJECT_MISMATCH` |
| `N2v2.goal_solid_id_qualified` | `solid_id = pyr2`, `[pyr2::M, B]` | `SOURCE_OBJECT_MISMATCH` |
| `N2v2.qualified_namespace` | no goal scope, `[pyr2::M, B]` | `SOURCE_OBJECT_MISMATCH` |
| `N2v2.control_own_point` | `solid_id = pyr1`, `[M, B]` | a3 SERVED MB = (√5/2)·a; pl/a4 `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` (capability: `pyr2` binds D→D1) |

The v1 in-target `solid` form named the solid by notation. A goal-level `solid_id` is an id, so that form has no
structurally valid equivalent. A namespace-qualified operand (`pyr2::M`) replaces it as the second assertion carrier.

Each negative proves the following:
1. It passes schema (`parse_typed_fact_next`).
2. S8 runs on the route (spy on `_kiem_pham_vi_tien_de`).
3. S8 itself raises `SOURCE_OBJECT_MISMATCH`, and the reason names goal `mb`.
4. On the same route, the own-point control reaches the capability refusal, so semantics came first.
5. Adapter /3 `_shared_source_gate` raises instead of falling back to `LEGACY_SOURCE_AUTHORITY`.
6. A `pyr2::M` that exists only in `pyr1` is never resolved globally.

## Post-registration addendum (found by the first GREEN run, after the product edit)

The mandatory mutant `s8_preflight` used the oracle `test_legacy_constructed_ownership_precedes_capability('solid_id', False)`.
That is the superseded v1 in-target form, which is now `INVALID_MATH_GOAL` at the schema, so it cannot observe S8.
The oracle now calls the still-valid `('goal', False)` form: goal-level `solid_id = pyr2`, expected
`SOURCE_OBJECT_MISMATCH`, unchanged. This is an N2 reference and falls inside §4. It was missed at registration
and is reported here, not folded silently into the registered SHA. The first GREEN attempt that showed it
(`1 failed, 790 passed, 6 skipped`) is recorded in `green.json#attempts`.

## Also amended: `oracle_shape` (same suite, same reason)

The `operand_shape` / `string_iteration` mutant oracle used `{solid_id: s1, segment: "SA"}`. Under the locked
grammar the scope key alone refuses that input, so the oracle would no longer isolate the shape guard. `solid_id` moves to
the goal. The input stays a malformed string segment, and the expected code `INVALID_MATH_GOAL` is unchanged. This
oracle is a supplementary test of the same closed-input suite, not a locked test. It is disclosed here for Owner
confirmation as a use of the §4 authority beyond the N2 tests themselves.
