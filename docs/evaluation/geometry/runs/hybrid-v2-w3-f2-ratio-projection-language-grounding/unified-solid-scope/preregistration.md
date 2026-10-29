# Preregistration — unified solid-scope validation

Registered before any product change, on HEAD `3cdba8eb` (product `c4d7b759`). Classification of every new
measurement: `POST_FEEDBACK_DEVELOPMENT_REGRESSION` / development security tests; nothing here is a blind holdout.
0 provider calls (`ALLOW_LIVE_AI=0`). Policy and rules R1–R6, D1–D4: `architecture-decision.md`.

## Inputs (unchanged committed files; LF SHA-256 recorded in `red.json`)

- `inputs/recovery-supplementary.json` `control` (two pyramids S.ABCD / T.ABCD) — served volume 4.
- `typedfact-next-adapter3-simulation/corpus-dev.json`: A3-DEV-02, A3-DEV-03, A3-DEV-09 with their `oracle_exact`.
- `simulation-coverage-visual-validation/corpus-dev.json`: demo1 (derived solid, ratio), demo6a (cylinder),
  demo6b (cone, derived solid) with their `expected_answers`.
- `inputs/development.json` W3-B02 (`/1` form, section area).
Fresh mutations are built in the test file from these inputs only; no case id or answer appears in product code.

## Expected outcomes (test file `backend/tests/geometry/test_unified_solid_scope.py`)

| group | negative → expected refusal | controls → expected |
|---|---|---|
| MAJOR 1 distance (S→ABCD) / angle (SC, ABCD), Adapter /3 and /4 | goal `solid_id` s2 → `SOURCE_OBJECT_MISMATCH`; foreign → `UNKNOWN_SOLID_ID`; `s1::S` under s2 → `SOURCE_OBJECT_MISMATCH`; midpoint M of SA (s1) under s2 → `SOURCE_OBJECT_MISMATCH` | s1, `s1::S`, absent scope, M under s1: SERVED, /3 and /4 equal answers |
| MAJOR 2 curved (demo6a, demo6b) | goal / premise / relation `solid_id` foreign → `UNKNOWN_SOLID_ID`; goal on a second declared solid vs `target.solid` → `SOURCE_OBJECT_MISMATCH`; `target.solid` foreign → `UNKNOWN_SOLID`; premise with `zz::O` under cyl → `SOURCE_OBJECT_MISMATCH`; `_run_curved_route` never entered for these; Bridge ownership validator entered for every curved payload | demo6a/6b SERVED with `expected_answers`; valid frame relation and explicit goal scope still SERVED |
| MAJOR 3 ratio/residual (A3-DEV-02/03/09, demo1) | goal-level `solid_id` foreign or a declared solid → `INVALID_MATH_GOAL` | unscoped SERVED with oracle |
| MINOR 4 relations (control, both adapters) | `shared_faces.solid_a` foreign, `coordinate_frame.solid_id` foreign → `UNKNOWN_SOLID_ID`; face SAB claimed for T.ABCD, frame s1 with anchor `s2::T` or `T` → `SOURCE_OBJECT_MISMATCH` | A3-DEV-02 valid shared face / frames SERVED |
| MINOR 5 derived (demo1) | volume goal on undeclared `ghost` → `UNKNOWN_SOLID_ID` | volume goal on declared derived `s_top`: Adapter /3 SERVED, Adapter /4 never `UNKNOWN_SOLID_ID` |
| MINOR 6 nested target (control, both adapters) | `target.solid_id` s2 or foreign under goal s1 / `target.solid` s1; `target.solid` `T.ABCD` with `target.solid_id` s1 → `SOURCE_OBJECT_MISMATCH` / `UNKNOWN_SOLID_ID` | `target.solid_id` s1 alone SERVED |
| NEW-1 ancestry (demo1, demo6b) | `parent_solid_id` foreign → `UNKNOWN_SOLID_ID`; another declared solid → `SOURCE_OBJECT_MISMATCH` (never `ADAPTER_INTERNAL_ERROR`) | explicit parent equal to the section's solid SERVED |
| metamorphic | replacing any one declared solid-scope value of a served control with `foreign`, or a premise/goal scope with another declared solid when one of its operands is owned only by the original solid, is never SERVED | — |

Existing locked codes are not changed: N006 `UNKNOWN_SOLID`, NEG08/23 `UNKNOWN_SOLID_ID`, all 96 W3-F2 development
expectations, 144 Wave 3 expectations.

## Mutants that must be killed (`mutations.json`)

remove R1 existence; remove R3 cross-solid comparison; derived solids dropped from the known set; remove nested
target check; remove R4 ratio/residual refusal; remove R6 relation sides; remove D2 goal-operand ownership; remove D3
curved pre-validation; Adapter /3 operand back to `inner or scope`; semantic refusal allowed to fall back; foreign
scope replaced by the first solid.

## Acceptance and STOP

GREEN requires every row above, 0 WRONG_SERVED on the safety matrix, no uncaught exception, every mutant killed,
locked 96/96, compatibility suite green. Any failure: STOP, checkpoint, no freeze, no Full T3. Later gates follow the
Owner GO §9–§14; a new BLOCKER/MAJOR from the independent review means `NOT_READY`.
