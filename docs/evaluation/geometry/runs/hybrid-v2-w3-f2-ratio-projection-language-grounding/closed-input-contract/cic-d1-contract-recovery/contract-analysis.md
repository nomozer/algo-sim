# Contract analysis — CIC-D1 (read-only, before any product edit)

Research HEAD `1490e3cd` (clean, `main` `996f114b` is an ancestor). Observations: `observed-*.json` from
`tools/cases.py run` on clean HEAD, detached clean `main` and detached clean pre-patch `5e44d5da`.

## Locked V2 contract

`82097186` / `3524bec8`: the Bridge `_distance_question` and `_angle_question` accept a target only when its key set is
**exactly** one alternative (`{point, plane}`, `{segment}`, `{line1, line2}`, `{line, plane}`, `{plane1, plane2}`,
`{point, line}`). Anything else is `INVALID_MATH_GOAL`. `target8` = `{point, plane, solid}` is in the locked refusal list.

## Root cause in the patch (`4b361c47`)

1. `typed_fact_next.py::_validate_goal_target` added `{solid, solid_id}` to every goal type's allowed key set. It then
   checked the alternatives on the operands **minus** those keys, so a scope key beside geometric operands passed.
2. `typed_fact_next_bridge.py::_distance_question` / `_angle_question` now read `measurement_operands(g)`. That helper
   **deletes** `solid`/`solid_id` and keeps going. This silent normalization is what CIC-D1-B forbids, and it bypassed
   the locked exact-key check.

## `/1` versus `/2` (CIC-D1-C)

| tree | `{point, plane, solid: pr}` (and the `solid_id`, notation, angle, segment, polygon forms) |
|---|---|
| `main` | a4 `INVALID_MATH_GOAL`; a3 (/1) SERVED; a3 also serves with a solid that does not exist (`zz`) — the key is ignored |
| `5e44d5da` | a4 `INVALID_MATH_GOAL`; a3 SERVED; the research rules R1/R3 use `target.solid*` only as a refusal check (unknown/conflicting solid) |
| HEAD | a4 SERVED (CIC-D1), a3 SERVED |

No active `/1` contract allows these forms:
- `docs/architecture/TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md` defines no target-level scope.
- The only `/1` behaviour on `main` is to ignore unknown keys. That is the fail-open the preregistered N5 closes
  ("unknown/inapplicable target keys → `INVALID_MATH_GOAL`").
- The R1/R3 rows give `target.solid`/`target.solid_id` a meaning on solid-valued goals, where they are the operand.
  They do not create a geometric-target grammar.
- No locked test needs these forms.
- None of the 662 `measurement` goals in the repository corpora/receipts (`docs/evaluation/**`, `backend/tests/**` JSON)
  uses a scope key beside geometric operands. Every multi-key target in them is exactly one alternative.
- The only V2 producer (`typed_fact_next_extraction.py`) emits `/2`.

Decision under CIC-D1-C: one closed grammar for `/1` and `/2`, enforced at the schema, which every route runs first.
`/1 → /2` conversion copies the target unchanged, so it cannot create an invalid target and does not skip V2 validation.
Disclosed consequence: on Adapter /3 (/1), these forms change from SERVED (fail-open on `main`) to
`REFUSED INVALID_MATH_GOAL`.

## Rule after the fix

For every goal type: when a target holds geometric operands (any key other than `solid`/`solid_id`), its key set must
equal one registered alternative exactly. Solid-valued alternatives (`volume`: `solid` | `solid_id`, also both together
when they name the same solid; `radius`, `lateral_area`, `area` by `solid`) are unchanged. Their consistency stays with
R1–R3 (`SOURCE_OBJECT_MISMATCH` on conflict). The Bridge reads `g.target` again, with no key removal.
`measurement_operands` is deleted.
