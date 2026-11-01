# R-1 live described-point pilot — protocol (pre-registered, fifteenth continuation, 2026-11-01)

**Question.** On new Vietnamese texts that ask through an *unnamed* described point, does Gemini emit correct
`DescribedPointSpec`s, and does Hybrid `/4` then compose the existing Geometry Functions into a certified answer?
The S-2 pilot cannot answer this: 0/36 of its texts use such a point (`s2-r1-coverage.json`).

## 1. Measurement metadata

| field | value |
|---|---|
| `MEASUREMENT_CLASS` | `LIVE_DEVELOPMENT_PILOT` |
| `HELD_OUT_CLAIM` | none. The texts are implementer-authored and their gold is in the repo |
| `AUTHORING_INDEPENDENCE` | `NOT_ESTABLISHED` (author: the implementing agent) |
| `EVALUATOR_INDEPENDENCE` | scoring is deterministic code fixed before the run; the review is fresh-context, but the author is not independent |
| arm | one: the production opt-in Hybrid `/4` path, one source-only request per case |
| model | `gemini-2.5-flash`, bound in the approval; no fallback model |
| caps (proposed, not granted) | 18 HTTP requests including retries; USD 1.0. Planning estimate about USD 0.0244 per request |
| stops | as S-2 §5.6: request cap, USD cap, provider block, 3 consecutive infrastructure failures, identity change, interruption |
| approval | one Owner-written file, `pilot = "R-1"`, binding the corpus, measured system, runner, paired harness and scorer hashes; single use, no resume |

## 2. Corpus

`r1-live-pilot-corpus.json`, built once by `tools/build_r1_live_corpus.py`: 16 cases.

| stratum | n | content | expected |
|---|---|---|---|
| R1-A | 5 | one unnamed point in a measure goal: midpoint, projection on a plane, intersection of lines; distance, angle, area | SERVED |
| R1-B | 2 | the unnamed point fixes an auxiliary section plane (∥ a face, ⊥ an edge) | SERVED |
| R1-C | 2 | one described point reused by two goals; intersection → parallel plane → section | SERVED |
| R1-D | 2 | a right prism; relabelled pyramid `S.MNPQ` with givens in another order (vertex `M` is not the unnamed midpoint) | SERVED |
| R1-E | 2 | the description does not fix one point ("một cạnh bên"; a projection with no target) | CLARIFY |
| R1-F | 3 | registered boundary: D1 nested, D2 two described operands, a reflection (no primitive) | REFUSED_UNSUPPORTED |

Other properties of the corpus:
- No text repeats a C13 probe row or an S-2 text.
- Every oracle is a hand string. The builder recomputes it from hand coordinates in exact fractions before any system
  run.
- D1, D2 and the reflection case record their mathematical value only in `boundary_value`. Their expected outcome is
  the typed refusal the current contract requires.

## 3. Scoring (fixed in `run_s2_student_language_pilot.py` before any live request)

- **The eight S-2 metrics**, end to end, false refusal and attribution, unchanged.
- **`described_check`**, on each row whose gold describes a point. It reads the model's own `DescribedPointSpec`s:
  - `emitted`;
  - `kinds_match`: the same multiset of kinds;
  - `refs_resolve`: every `@id` refers to an emitted spec;
  - `quotes_verbatim`.

  Operands and goals are the scorer's goal metric, because `project` resolves each `@id` to its description.
- **`composition_label`**, one per row:
  - Served correctly: the planner's own `search_telemetry.classification`.
    `DISCOVERED_FUNCTION_COMPOSITION` counts only with at least one planner-originated step.
  - Served wrongly: `WRONG_SERVED`.
  - Expected refusal or clarification met: `CORRECT_REFUSAL`.
  - Failed, when the live extraction differs from gold: `EXTRACTION_FAILURE`.
  - Failed, when the gold reproduction ends the same way: the layer named by the code.
    - `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` or an extraction-group code: `REPRESENTATION_BLOCKED`.
    - Source-unverified: `SOURCE_GROUNDING_FAILURE`.
    - `PLAN_TOO_LARGE`: `PLANNER_SEARCH_FAILURE`.
    - Capability: `MISSING_PRIMITIVE`.
    - Result-unverified or inconclusive: `KERNEL_VERIFICATION_FAILURE`.
  - Anything else, and technical failures: `NOT_ESTABLISHED`.
- **Stated limit:** the public refusal surface does not say whether the bridge, the Source Gate or the planner refused.
  Apart from `PLAN_TOO_LARGE`, the layer label is the code's group. Each failed row is then traced by hand from its
  recorded extraction, and that trace is reported as proven or hypothesis.

## 4. Baseline (gold replay, 0 requests: `r1-live-pilot-gold-replay.jsonl`)

| measure | result |
|---|---|
| end to end | 16/16 |
| wrong-served | 0 |
| served exactly | 11/11 |
| served cases labelled `DISCOVERED_FUNCTION_COMPOSITION` with planner-made steps | 11/11 |
| correct refusals | 5/5 |
| `described_check` | 4/4 metrics at 1.0 |

This is the ceiling a live run is attributed against. The deterministic layers already serve these new texts from
gold, so the live run measures the **model's reading** of unnamed points.

## 5. What a result may and may not claim

**May claim:** "on 16 implementer-authored development texts, Gemini emitted correct described points in x/n cases,
and the route served y/11 exactly with 0 wrong-served".

**May not claim:** held-out accuracy; generalization beyond these strata; anything about D1/D2 beyond the boundary
holding.
