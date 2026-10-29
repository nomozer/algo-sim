# Preregistration — CIC-D1 (locked before the product edit)

Research HEAD `1490e3cd`. Development security regression, not a blind holdout. Offline, 0 provider calls.
Inputs and SHA-256: `registration.json` (`cases.json`, the three `observed-*.json`, `tools/cases.py`, both test files).

## Expected outcomes

| group | cases | expected |
|---|---|---|
| locked | `test_malformed_distance_target_is_refused[target8]` (16 params, unedited) | all pass; `target8` `REFUSED INVALID_MATH_GOAL` |
| NEG_LOCKED_GRAMMAR | 16 = {distance point–plane, distance segment, angle line–plane, area polygon} × {`solid`, `solid_id`, notation, `solid`+`solid_id`} inside the target | schema raises `INVALID_MATH_GOAL` for `/1` and `/2`; a3, pl, a4 `REFUSED INVALID_MATH_GOAL` |
| CONTROL_UNCHANGED | 11 = the same four targets without scope keys, and with goal-level `solid_id`; volume `{solid}`, `{solid_id}`, `{solid, solid_id}` | identical (status, code, exact answer) to `observed-head-1490e3cd.json` on every route |
| NEG_OWNERSHIP (N2 v2) | 3 | `SOURCE_OBJECT_MISMATCH` everywhere, with proofs 1–6 of `n2-amendment.md` |
| POS_OWNERSHIP_CONTROL | 1 | a3 SERVED MB = (√5/2)·a (independent oracle); pl/a4 `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` |
| HISTORICAL_V1_SUPERSEDED | 4 = v1 N2 in-target forms | not acceptance; post-fix outcome recorded (`INVALID_MATH_GOAL` under the locked grammar) |

## Mutants (each oracle must pass on the real code and fail on the mutant)

- `remove_closed_target_rule`: schema rule off, so /1 Adapter /3 serves `F.distance_point_plane.solid`.
- `remove_s8`: no S8 in `_bridge`, so the Planner returns a capability code for `N2v2.goal_solid_id`.
- `capability_before_s8`: S8 moved after the solid-capability loop.
- `semantic_fallback`: Adapter /3 falls back on a semantic refusal.
- `discard_target_scope_keys`: schema rule off, and the Bridge strips `solid`/`solid_id` (the CIC-D1 mechanism), so
  `target8` is served on Adapter /4.

The 9 mandatory mutants of `test_closed_input_contract.py` must stay killed.

## RED (this registration, before the product edit): `red.json`

67 failed / 446 passed (`red.log`). The failures are `target8`, the 16 schema cases and 48 route cases of
NEG_LOCKED_GRAMMAR, and `remove_closed_target_rule` and `discard_target_scope_keys`; their oracles cannot hold yet.
N2 v2, the controls and the other mutants already pass on HEAD: N2 was fixed by `4b361c47`. On `main` and `5e44d5da`
they fail (`observed-*.json`), so they are regression guards, not RED tests.

Harness correction before registration: the first RED run showed `semantic_fallback` failing only because its oracle
raised `pytest.fail` ("DID NOT RAISE") instead of `AssertionError`. The mutant had been killed. The oracle now asserts the
gate's refusal code. No expectation changed. That first log is not kept as evidence; it was superseded before registration.

## Acceptance after GREEN

Gate A = acceptance manifest v2 + these tests + 203 reviewer probes (0 negative served, 0 internal, 0 positive loss).
The four source-grammar diagnostics stay `PENDING_SOURCE_GRAMMAR_SUPPORT`. Gates B–D as in Owner GO §7.
