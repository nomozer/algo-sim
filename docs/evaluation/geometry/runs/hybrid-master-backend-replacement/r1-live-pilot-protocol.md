# R-1 live described-point pilot — protocol (pre-registered, fifteenth continuation, 2026-11-01; revision A)

**Question.** On new Vietnamese texts that ask through an *unnamed* described point, does Gemini emit correct
`DescribedPointSpec`s, and does Hybrid `/4` then build a certified exact answer from the existing Geometry Functions?
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
| caps (proposed, not granted) | 18 HTTP requests including retries, which is one per case and leaves no retry; USD 1.0. Planning estimate about USD 0.0244 per request, about USD 0.44 in all |
| stops | as S-2 §5.6: request cap, USD cap, provider block, 3 consecutive infrastructure failures, identity change, interruption |
| approval | one Owner-written file, `pilot = "R-1"`, binding the corpus, measured system, runner, paired harness and scorer hashes; single use, no resume |

## 2. Corpus

`r1-live-pilot-corpus.json`, built once by `tools/build_r1_live_corpus.py`: 18 cases.

| stratum | n | content | expected |
|---|---|---|---|
| R1-A | 5 | one unnamed point in a measure goal: midpoint, projection on a plane, intersection of lines; distance, angle, area | SERVED |
| R1-B | 2 | the unnamed point fixes an auxiliary section plane (∥ a face, ⊥ an edge) | SERVED |
| R1-C | 2 | one described point reused by two goals; intersection → parallel plane → section | SERVED |
| R1-D | 2 | a right prism; relabelled pyramid `S.MNPQ` with givens in another order (vertex `M` is not the unnamed midpoint) | SERVED |
| R1-E | 2 | the description does not fix one point ("một cạnh bên"; a projection with no target) | CLARIFY |
| R1-F | 3 | registered boundary: D1 nested, D2 two described operands, a reflected point (no `DescribedPointSpec` kind) | REFUSED_UNSUPPORTED |
| R1-G | 2 | paraphrases outside the standard frames ("đường thẳng đi qua A và …", "điểm chính giữa cạnh … tới …") | SERVED |

Every oracle is a hand string. The builder recomputes each from hand coordinates in exact fractions, and does the
same for the boundary values of R1-F (`boundary_value`).

**Disclosed narrowness:**
- No text copies a C13 probe row or an S-2 text, but the question frames do: "Tính độ dài đoạn thẳng nối … với …",
  the section request sentence, and "tam giác tạo bởi".
- 12 of 18 texts share one premise sentence.
- D01 reuses the C7 prism's base.
- R1-G is the only stratum outside these frames. The stated outcome of the corpus is therefore narrower than "any
  student wording".

## 3. Scoring (fixed in `run_s2_student_language_pilot.py` before any live request)

- **The eight S-2 metrics**, end to end, false refusal and attribution, unchanged.
  - CLARIFY cases accept either `AMBIGUOUS` or `MISSING_DATA`, as in S-2. This is lenient by design.
  - `extraction_accuracy` compares labels in strict form. In R1-B01, the model may name (ABCD) by another correct
    triple of labels; that counts as different, so the metric is a lower bound.
- **`described_check`**, on each row whose gold describes a point. It reads the model's own `DescribedPointSpec`s:
  - `emitted`;
  - `kinds_match`: the same multiset of kinds;
  - `refs_resolve`: some `@id` is used, and every `@id` refers to an emitted spec;
  - `quotes_verbatim`: every quote is non-blank and appears in the text.

  Operands and goals are the scorer's goal metric, because `project` resolves each `@id` to its description.
- **`composition_label`**, one per row. Revision A changed this definition after review MAJOR-1.
  - **Why it changed:** the planner calls every step it adds its own. That includes the step that only builds the
    point the model described, so its self-label `DISCOVERED_FUNCTION_COMPOSITION` is not evidence.
  - **A correctly served row** is labelled by its planner-made steps, after removing every step that has the kind and
    input operands of an emitted `DescribedPointSpec`:
    - no step left: `SOURCE_EXPLICIT_SEQUENCE`;
    - only functions of the registered auxiliary rules (`registry.AUXILIARY_RULES`): `REGISTERED_DECOMPOSITION`;
    - anything else: `DISCOVERED_FUNCTION_COMPOSITION`.
    - **Limit:** the registered check is by function name, so it can only undercount discovery, never overcount it.
  - **Other rows:**
    - a wrong serve: `WRONG_SERVED`;
    - an expected refusal or clarification that is met: `CORRECT_REFUSAL`;
    - a live extraction that differs from gold: `EXTRACTION_FAILURE`;
    - a gold reproduction that ends the same way: the layer the code names. `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` or an
      extraction-group code is `REPRESENTATION_BLOCKED`; source-unverified is `SOURCE_GROUNDING_FAILURE`;
      `PLAN_TOO_LARGE` is `PLANNER_SEARCH_FAILURE`; capability is `MISSING_PRIMITIVE`; result-unverified or
      inconclusive is `KERNEL_VERIFICATION_FAILURE`;
    - anything else, and technical failures: `NOT_ESTABLISHED`.
  - **Limit:** the public refusal surface does not say whether the bridge, the Source Gate or the planner refused.
    Each failed row is therefore traced by hand from its recorded extraction, and that trace is reported as proven or
    hypothesis.

## 4. Baseline (gold replay, 0 requests: `r1-live-pilot-gold-replay.jsonl`, locked by a test)

| measure | result |
|---|---|
| end to end | 16/18 |
| wrong-served | 0 |
| served exactly | 11/11 of R1-A to R1-D |
| composition of those 11 | 7 `SOURCE_EXPLICIT_SEQUENCE`, 4 `REGISTERED_DECOMPOSITION`, **0 `DISCOVERED_FUNCTION_COMPOSITION`** |
| correct refusals | 5/5 |
| R1-G | both refused at the Source Gate on **gold** (`SOURCE_OBJECT_MISMATCH`): a deterministic false refusal |
| `described_check` on gold | 4/4 metrics at 1.0 |

A live run is attributed against this ceiling. On these texts the deterministic layers serve the stated reading, so
the live run measures **the model's reading** of unnamed points. The route's own contribution is bounded: it applies
registered rules; it does not search for compositions (§5).

**The same rule applied to the C13 probe** (`r1-composition-relabel.json`): its 9 planner-labelled `DISCOVERED` chains
are 6 `SOURCE_EXPLICIT_SEQUENCE` and 3 `REGISTERED_DECOMPOSITION`.

## 5. What a result may and may not claim

**May claim:** "on 18 implementer-authored development texts, Gemini emitted correct described points in x/n cases,
and the route served y/13 exactly with z wrong-served". It may also state the composition labels as measured.

**May not claim:**
- held-out accuracy;
- generalization beyond these strata and frames;
- that the planner *discovers* compositions. On every current text it realizes the stated description or applies a
  registered rule;
- anything about D1/D2 beyond the boundary holding.

## Revision A (review round 1, before any approval)

1. **MAJOR-1:** the composition label was redefined (§3). The 16-case baseline that showed "11/11 DISCOVERED" is
   superseded (§4).
2. **MINOR-1:** a blank quote no longer counts as verbatim, and three `described_check` conditions are now tested.
3. **MINOR-2:** a test locks the corpus and the gold-replay receipt.
4. **MINOR-3:** the narrowness is disclosed (§2), and stratum R1-G was added. The corpus is now 18 cases.
5. **MINOR-4, NIT-4, NIT-5:** disclosed in §3. The S-2 output gains only the additive keys `study` and `search`.
6. **NITs 1–3:** F03 has a boundary value, every check is computed from coordinates, and F03's boundary is stated as
   the `DescribedPointSpec` kind vocabulary.
