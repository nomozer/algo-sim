# W3-F2 scope census closure and hyphenated-id recovery — report (`NOT_READY`)

Owner GO `HYBRID_V2_W3_F2_SCOPE_CENSUS_CLOSURE_AND_HYPHENATED_ID_RECOVERY`, 2026-10-29. Development security tests /
`POST_FEEDBACK_DEVELOPMENT_REGRESSION`; 0 provider calls. Stopped at the pre-freeze review (Owner GO §12).

## Baseline

main = origin/main = remote `996f114b`; research HEAD `eb19c002` (product `9772ea37`), clean; ancestry verified.

## What was done

| step | result |
|---|---|
| mechanical census | `scope_field_census.py` (pydantic walk + `_ARGS_LOI` shapes + AST of route `target` reads): 185 field paths, 112 scope-bearing, all classified (`schema-field-inventory.json`, v2 after amendment 1); coverage gate `test_census_inventory_complete` enforces field → rules → tests → product code |
| preregistration | F1–F6 frozen; RED on candidate and on exported main / pre-unified / pre-closure trees (`red.json`): regressions of the previous task = the F1 family only |
| design | `architecture-amendment.md`: rules S1–S11, one enumeration `scope_records` iterated by the schema (S5–S7, S10) and the Bridge (S8); `split_edge_key` replaces every raw `-` split (6 sites) |
| product | `959e23a6` (F1–F6, Owner D-A, container-as-solid), `1262fbd5` (F7 residual ancestry, registered in `preregistration-amendment-1.md` before the fix) |
| tests | closure suite 87/87 incl. 9 closure mutants; four earlier oracles moved to cases only their layer decides (`test-adaptation-amendment.md`) |
| Gates A–D | PASS on the registered scope: locked 96/96; compatibility 875 passed / 0 failed; fixtures 41/41; cache 130 MATCH; publication PASS; the previous reviewer's 117 probes: no NEG served, no internal error (`gates.json`) |
| pre-freeze review | **NOT_READY** (`pre-freeze-review.md`): N1–N4 MAJOR, N5–N6 MINOR, N7 note — all pre-existing on main and 9772ea37, outside the registered census |
| not run (by contract) | Wave 3 replay, T0–T2, freeze, Full T3, final review |

## Why NOT_READY

The closure fixed every registered finding without regression, but the census is still not the whole input surface:
(N1) string-form operands are read per character by Adapter /3 and escape scope checks; (N2) the Adapter /3 legacy
fallback skips constructed-point ownership because the Bridge refuses its capability before running S8; (N3) fields
that have no meaning for their kind are still silently ignored on math goals and `derived_solid_id`; (N4) the curved
route never reads relations, so references inside them are unchecked beyond namespaces. These are the same class
(scope / provenance fail-open) the GO forbids.

## Next step (needs a new Owner GO)

1. Close the input surface instead of chasing fields: a per-kind **allowed-field table** for every math/simulation goal
   and relation kind (anything else present → typed refusal, D-D), and a **closed key set** for `MathGoalSpec.target`.
2. One operand grammar: list-shaped operand keys accept only lists (or a chain parsed once by the schema), never
   per-character strings.
3. Run the Bridge ownership validator (S8) before any capability refusal, so legacy fallback inherits it; Adapter /3
   legacy compile must scope goal operands with the same resolved goal scope as the schema.
4. Curved route: validate qualified label existence (S5 label check) and refuse relations it cannot consume, rather
   than ignore them.
5. Fix the census walker blind spots (`partial`, `set(t)`) and the N7 derived-scope regression.
6. Then: RED → GREEN → Gates → pre-freeze review → replay → T0–T2 → freeze → Full T3 → final review.
