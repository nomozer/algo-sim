# W3-F2 unified solid-scope validation — report (NOT_READY)

Owner GO `HYBRID_V2_W3_F2_UNIFIED_SOLID_SCOPE_VALIDATION`, 2026-10-29. Classification of every new measurement:
`POST_FEEDBACK_DEVELOPMENT_REGRESSION` / development security tests (not a blind holdout). 0 provider calls.

## Baseline

main = origin/main = remote `996f114b`; research branch at `3cdba8eb` (product `c4d7b759`), clean, ancestry verified;
previous candidate `55bdd332` kept as historical reference only.

## Census and design

`solid-scope-census.md` / `solid-scope-entrypoint-matrix.json`: 17 solid-reference field groups × 9 entry points;
1234 committed payloads profiled. Beyond the six review findings it found NEW-1 (`parent_solid_id` contradicting the
section served), NEW-2 (contradictory relation sides served on Adapter /4), NEW-3 (internal errors on the curved
route). `architecture-decision.md`: one declared-scope policy (R1–R6) inside `TypedFactNextPayload` validation, so every
route applies it before dispatch, capability refusal or fallback; Bridge validator extended to measurement-goal
operands; curved route runs it before building geometry; redundant Bridge goal check removed.

## Changes

Product `9772ea37`: `typed_fact_next.py` (`_validate_declared_solid_scope`, `_solid_aliases`, `_qualified_refs`),
`typed_fact_next_bridge.py` (goal-operand ownership; removed volume-goal `_pham_vi_khoi` call),
`adapter3_simulation.py` (curved pre-validation). Tests: new `test_unified_solid_scope.py`; six earlier tests adapted
without changing any expected code (`test-adaptation-amendment.md`).

## Results

| item | result |
|---|---|
| RED `82ebf401` | 37 failed / 25 passed / 6 skipped (`red.json`) |
| GREEN `9772ea37` | 71 passed / 6 skipped (`green.json`); with earlier safety files 126 passed |
| mutants | 9 new + 8 retained killed (`mutations.json`); metamorphic foreign-scope never served |
| Gate A | safety matrix 43 rows: 33 negatives refused with expected codes, 10 controls served, 0 WRONG_SERVED (`gates.json`) |
| Gate B | no kernel/engine/Registry change; incidence witnesses and Fraction oracle agreement re-run |
| Gate C | locked 96/96 (ratio 24/24, projection 26/26, historical 20/21 + 1 locked refusal, isolated 1/1, negatives 24/24) |
| Gate D | compatibility 788 passed / 0 failed / 6 xfailed; fixtures 41/41; cache 130 MATCH; publication PASS (`compatibility.json`) |
| Wave 3 replay | 144 cases, identical to baseline: positives 50/72, negatives 72/72 refused (62 reason match), 0 WRONG_SERVED, 0 transitions |
| freeze | candidate `2c84558d` (separate commit), measured 118 files `f0521dcd…`; divergence `runs/hybrid-v2-w3-f2-unified-solid-scope/candidate_divergence.json` |
| T0/T1/T2 | executed on the frozen candidate: T0 12854 pytest passed / 0 failed; T1 872 + 24; T2 vitest 1417, tsc, build (`tiers.json`) |
| Full T3 | `FULL_PRODUCT_GATE_PASS` on clean detached `cd8de398` (`full-t3/receipt.json`) |
| independent review | **NOT_READY** — `review.md` |

## Why NOT_READY

`review.md`: F1 — this task introduced a false refusal of valid solid ids containing `-` (the qualified-reference
scanner splits on `-`); F2–F4 — further pre-existing fail-open slots the census did not list: scope of relation kinds
other than `shared_faces`/`coordinate_frame`, simulation-goal `target_solid_id`/`parent_solid_id` vs their refs or
section, derived-solid `apex_ref` and highlight refs on the curved route. Gate A is therefore FAIL despite the passing
matrix: the matrix was built from an incomplete census. Per Owner GO §14 the work stops here; Full T3 is not repeated.

## Next step (needs a new Owner GO)

1. Fix F1 by scanning qualified references with the existing `_QUALIFIED_REF_RE` per edge endpoint instead of a raw
   `-` split (edge keys are the only `X-Y` strings), plus a hyphenated-id control in the suite.
2. Extend the census to every model attribute mechanically (walk the pydantic models, not a hand list) and give each
   scope-bearing object one owning scope: every relation kind with `solid_id`/`solid_a`/`solid_b`, every simulation goal
   (`target_solid_id`, `parent_solid_id`, `target_section_id`, `apex_ref`, `target_refs`), with ownership of unqualified
   refs checked by the Bridge validator for all of them (and on the curved route).
3. Decide (Owner) whether `construct_object.parent_solid_id` is meaningful or must be refused like Decision A.
4. Then RED → GREEN → Gates → replay → freeze → T0–T2 → Full T3 → new independent review.
