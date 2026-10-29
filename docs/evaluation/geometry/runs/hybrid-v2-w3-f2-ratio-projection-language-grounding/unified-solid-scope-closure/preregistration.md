# Preregistration — scope census closure and hyphenated-id recovery

Owner GO `HYBRID_V2_W3_F2_SCOPE_CENSUS_CLOSURE_AND_HYPHENATED_ID_RECOVERY`, 2026-10-29. Registered on HEAD `eb19c002`
(product `9772ea37`) before any product edit. Classification: development security tests /
`POST_FEEDBACK_DEVELOPMENT_REGRESSION`; nothing here is a blind holdout. 0 provider calls.

## Frozen findings (from `../unified-solid-scope/review.md`)

F1 MAJOR hyphenated solid ids falsely refused (regression of `9772ea37`; also the pre-existing `split("-")` of
`/1` named-intersection keys); F2 MAJOR relation scope of every kind; F3 MAJOR simulation-goal scope of every kind;
F4 MAJOR curved apex / highlight / relation ownership; F5 MINOR internal errors / alias on the curved route and
malformed targets; F6 MINOR Bridge alias for area/volume goals and plane-pair operand keys.

## Owner decisions applied

D-A: `parent_solid_id` is refused (`INVALID_SIMULATION_GOAL`) on every simulation-goal kind except
`construct_derived_solid`, where it must exist and equal its section's solid. The same rule (field present without
documented meaning for the kind) refuses `target_solid_id` on `construct_derived_solid`. Corpus check before
registration: 0 of 1234 committed payloads use either combination (`construct_object.parent_solid_id` 0,
`construct_derived_solid.target_solid_id` 0), so no locked expectation conflicts; no contract conflict found.
D-B/D-C/D-D as written in the GO.

## Inputs (LF SHA-256 in `red.json`)

`../inputs/recovery-supplementary.json` (control), `typedfact-next-adapter3-simulation/corpus-dev.json` (A3-DEV-02,
-03, -07 with `oracle_exact`), `simulation-coverage-visual-validation/corpus-dev.json` (demo1, demo6b),
`schema-field-inventory.json`. A3-DEV-07 is refused by the Source Gate on main as well (question quote), so it is used
only for verdict-invariance under hyphenated renaming, not as a served control.

## Tests and expected outcomes — `backend/tests/geometry/test_scope_census_closure.py`

Every negative names its exact code; every control is SERVED on the routes that have the capability and keeps the base
payload's outcome elsewhere. Groups: F1 tokenizer grammar, hyphenated controls (all routes, answers equal), hyphenated
negatives (unknown / foreign / scope), shared-label ambiguity (`AMBIGUOUS_REFERENCE`); premise; section (through point,
parallel plane, named key); measurement scope and operands; ratio/residual operands; every relation kind (contradicted
and foreign); every simulation-goal kind incl. section-bound, derived apex, derived `target_solid_id`, unknown highlight
token, highlight of another scope's section; D-A on four kinds; F4 curved (apex, qualified apex, highlight, qualified
highlight, relation operand) with `_run_curved_route` never entered; F5 curved alias served, malformed section id /
operand typed; F6 Bridge alias served, operand keys ⊇ keys read by routes, plane-pair contract; metamorphic hyphen
rename (verdict and answers unchanged on all routes) and foreign scope never served; coverage gate.

## RED baseline classification (same suite on exported trees, `red.json`)

main `996f114b`: 56 failed; pre-unified `3cdba8eb`: 42 failed; candidate `9772ea37`: 34 failed. Regressions of the
previous task (fail on candidate, pass on a baseline): the F1 family only. Everything else is pre-existing.

## Mutants (`mutation-results.json`)

hyphen split restored; qualified-reference guard removed; relation scope removed; simulation-goal target scope removed;
parent validation removed; highlight token validation removed; apex ownership removed; curved pre-dispatch removed;
terminal semantic refusal removed; explicit scope replaced by default — each must make an oracle fail.

## Acceptance / STOP

As the Owner GO §11–§15: GREEN on every row, 0 WRONG_SERVED, no false refusal of controls, locked 96/96, compatibility
green; then an independent adversarial review **before** freeze and Full T3; any BLOCKER/MAJOR → `NOT_READY`, stop.
