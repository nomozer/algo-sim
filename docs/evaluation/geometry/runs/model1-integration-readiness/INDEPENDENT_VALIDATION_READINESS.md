# Independent validation readiness — local Model 1 (text)

Run `model1-integration-readiness` (AXO HYBRID /17), 2026-11-21. Audience: the owner and an evaluator who is **not**
part of the team that built or tuned Model 1.

**Status: `EXTERNAL_INDEPENDENCE = NOT_MEASURED`.** No third-party data or evaluator was available in this run. Nothing
below was executed as an independent evaluation; it is the protocol a reviewer can run without this team.

## 1. Why the existing evidence is not independent

| evidence | who wrote the problems | who wrote the oracle | exposed to tuning? | independence |
|---|---|---|---|---|
| Holdout-2 … Holdout-6, SLM-Independent-1 … 3 (`/14`–`/16`) | the agent team that also fixed Model 1 | same team (`build_holdout.py` + `scene_oracle.py`) | yes, from the run after each was measured | none |
| "0 containment matches against 29,423 prior strings" (`/16`) | — | — | — | string novelty only |

String novelty does not show semantic novelty. The Holdout-6 problems reuse the phrase families the team had just
repaired (`perpendicularity_diversity`, `slm_genuine_natural`, …), and the generator itself shipped a wrong-solid bug in
Holdout-5 (`P04`, `P05`, `S07`). This run also showed that the family design shaped the denominators: 11 of the 31
"SLM-required" Holdout-6 problems were SLM-required only because of a parser defect (`PARSER_SLM_ROUTING_AUDIT.json`).
A set designed by the people who know where the parser is weak measures that knowledge, not the product.

## 2. What counts as independent

All four must hold; otherwise report `NOT_MEASURED` (never a renamed synthetic set):

1. **Problem source** outside the team: textbook or exam problems with a citable origin (publisher, year, page or exam
   code), or problems chosen by a teacher who has not seen the parser, the prompts or any holdout.
2. **Selection** fixed before the run by a written sampling rule (§3), applied by the evaluator, not by the team.
3. **Oracle** written or checked by the evaluator: expected behaviour (serve / refuse / clarify), the expected exact
   answers, and the relations the scene must satisfy.
4. **One measurement** on a frozen candidate. A product change after reading the results ends the set's blind status;
   it becomes regression data.

## 3. Sampling plan

- Scope: the shipped text scope of Model 1 — pyramids (triangular/quadrilateral, apex foot stated), right/regular
  prisms, cube, cuboid, tetrahedra including the right-corner tetrahedron, with lengths, volumes, areas, distances and
  angles; Vietnamese, typed or from DOCX / PDF with a text layer. Images are out of scope (Vision is postponed).
- Strata (minimum per stratum in brackets): textbook canonical [15], exam wording [15], teacher's own wording [15],
  colloquial learner wording [10], must-refuse — missing data, contradiction, negation/condition, other subject [20].
- Size ≥ 75 problems (≥ 55 positive). With 55 positives a measured rate of 0.85 has a 95 % Wilson interval of about
  ±0.09 — enough to tell 0.85 from 0.70, not 0.85 from 0.80. State the interval with the rate.
- Duplicates: the evaluator drops a problem whose content (solid, relations, numbers) equals one in §1; the team may
  run the string-overlap tool (`docs/evaluation/geometry/harness/live-acceptance/prior_corpus.py`) and report counts
  only, without seeing the problems.

## 4. Oracle validation

- Each positive item: expected exact answers as fractions/radicals, the scene relations as in the shared
  `scene_oracle.py` relation vocabulary (`perp_lp`, `perp_ll`, `par_ll`, `len2`, …) and the solid's vertex labels.
- A second person checks every oracle line before the freeze; disagreements are resolved or the item is dropped
  **before** the run, never after.
- The team's `scene_oracle.py` is used only as an executor of the evaluator's relations; its self-check
  (`python scene_oracle.py --selfcheck`) must pass on the run's machine.

## 5. Procedure

1. Evaluator writes `ACCEPTANCE_MANIFEST.json` in the shape the shared harness reads (`valid_cases` / `negative_cases`,
   `original_input`, `gold_entities`, `gold_relations`, `metric_oracle`, `expected_behavior`) and records the source of
   every item in a `PROVENANCE.json` the team does not edit.
2. Freeze: `docs/evaluation/geometry/harness/live-acceptance/freeze_acceptance.py` hashes the manifest and criteria and
   binds the candidate (`backend/scripts/freeze_evaluation_candidate.py --verify` must pass at the measured commit).
3. Run the shared harness once (`live_browser_acceptance.mjs`, `scene_oracle.py`, `aggregate.py`) on a clean checkout of
   the frozen candidate, local-only (`HYBRID_ROUTE_MODE=local-only-scoped`, `ALLOW_LIVE_AI=0`), with the network monitor.
4. Report separately: system success, SLM fallback success, mathematical correctness, source grounding (0 ungrounded
   relations served), negative safety, browser UI, latency — each with its denominator and interval.
5. Publish manifest, provenance, oracle review and raw responses together. The team may read the results only after
   the evaluator has published them.

## 6. What is still `NOT_MEASURED`

- `EXTERNAL_INDEPENDENCE` — no external problem source or evaluator in this run.
- Prospective acceptance of any candidate after 157 (Holdout-6 and SLM-Independent-3 are exposed).
- Learner-facing usefulness (no study with learners or teachers).
- Real-hardware / VPS behaviour (see `RUNTIME_CAPACITY_REPORT.json`).
