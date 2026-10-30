# Paired LLM_ONLY vs Hybrid live evaluation — protocol draft (NOT YET PRE-REGISTERED)

- **Status:** `DRAFT_AWAITING_OWNER_GO`. No live call has been made.
- **Pre-registration:** this file becomes the pre-registration when the Owner GO fixes the corpus hash and the budget. After that it is frozen; any change becomes an amendment file and does not edit this one.

## 1. Measurement metadata (actual values, not aspirations)

| field | value for the planned run | why |
|---|---|---|
| `MEASUREMENT_CLASS` | `PREREGISTERED_LIVE_PAIRED_EVALUATION` (planned). Everything in this run so far is `OFFLINE_DETERMINISTIC_FIXTURE_TEST` or `DEVELOPMENT_DIAGNOSTIC`. | No offline result is live evidence. |
| `HELD_OUT_CLAIM` | `NEW_UNOPENED_SET_REQUIRED`. Wave 3, the W3-F2 development set, the W4 dev corpus and every corpus already in `docs/evaluation/` are **excluded as held-out**, because they have been opened and tuned against. | D-04 |
| `EVALUATOR_INDEPENDENCE` | `NOT_ESTABLISHED`. Implementation and evaluation are by the same agent family. An independent author must be named in the GO; otherwise every result is labelled `IMPLEMENTER_AUTHORED_DIAGNOSTIC`. | Owner rule: an implementer-made set is never an independent blind holdout. |
| `AUTHORING_INDEPENDENCE` | `NOT_ESTABLISHED` until a named human author (or the Owner) writes the problems and oracles without seeing system outputs. | |

## 2. Corpus

**Inclusion:**
- Vietnamese grade 11–12 solid-geometry problems.
- Each problem asks for at least one exact quantity of kind `volume`, `area`, `distance`, `angle` (cos²) or `length`, or is a section/area question.
- Families: the polyhedral families of `capability-inventory.md` plus deliberately out-of-scope items.

**Exclusion:**
- Any text that appears in `docs/evaluation/**` or `backend/tests/**`; this is checked by exact and normalized substring scan before freezing.
- Images.
- Problems whose answer needs nested radicals, unless they are labelled as expected refusals.

**Composition (proposed):**
- 60 problems: 45 expected-serve and 15 expected-refuse.
- The 15 expected-refuse are balanced across: out-of-scope domain, curved solid, contradictory data, missing data, and a request to prove.
- Stratified by family and question kind. Every stratum has at least 3 problems or is reported as `INSUFFICIENT_N`.

**Oracle:**
- Written by the author by hand (or with a CAS independent of this repo) **before** any system run.
- Exact value stored as squared rationals, keyed by `(case, kind)`. Both arms are scored through kind, because model-chosen names differ (`run_thesis_final_acceptance.py::_song_anh_witness`).
- For expected-refuse cases, the oracle gives the refusal class instead.
- The oracle is never derived from either arm's output. A corpus hash and an oracle hash are written to this protocol before the first call.

**Freeze:** `corpus.json` and `oracle.json` hashes go into the GO. They are not edited after any result is seen; errata go to an amendment and are reported.

## 3. Arms (same input text, same order randomization)

| arm | code path | requests per problem (measured offline) | prompt payload, measured |
|---|---|---|---|
| `LLM_ONLY` | production `run_pipeline` with the default `RoutePolicy`: `semantic_analyze` (1), then `semantic_program` (≤ `MAX_SEMANTIC_PROGRAM_ATTEMPTS` = 3) | 2–4 logical calls; each may retry transient HTTP errors up to `gemini.MAX_ATTEMPTS` = 4 | analyze 11 782 chars (schema sent); program 13 169 chars + contract facts per attempt (IR schema **not** sent: `$ref`) |
| `HYBRID` | `hybrid_offline.run_hybrid_offline` with `TransportExtractor` (provider schema = `TypedFactNextPayloadV2`), then the /4 route | 1 logical call | 8 297 chars (schema sent) |

**Model:** `gemini-2.5-flash`, the production default `GEMINI_MODEL`, for both arms. Temperature is each arm's production value (0.1 / `fact_extraction.TEMPERATURE`).

**Output cap:**
- Hybrid caps output at 3072.
- **LLM_ONLY production sends no `maxOutputTokens`.**
- The protocol keeps production behavior (no cap added). The budget must therefore reserve LLM_ONLY output at the model's own maximum, which the Owner verifies at GO time from the provider documentation.

## 4. Scoring (per case, per arm; every dimension recorded separately)

**Per-case dimensions:**
- `extraction_valid`: Hybrid: `ExtractionResult.code is None`. LLM_ONLY: a `RequestContract` was produced.
- `source_grounding`: Hybrid: receipt `source_references` cover every quote and the Source Gate verified. LLM_ONLY: grounding gate passed.
- `served`, `served_correct`: every oracle `(kind → value²)` matches exactly.
- `wrong_served`: served while any oracle value mismatches, or an expected-refuse case was served.
- `false_refusal`, `refusal_reason_correct`: the refusal class is in the oracle's acceptable classes, using `hybrid_preview.classify_refusal` groups and the LLM_ONLY `error_code` taxonomy.
- `scene_valid`: Hybrid: /4 `route_d.status == SERVED` with validated `scene3d`. LLM_ONLY: envelope `status == ok` with `scene3d`.
- `latency_s`: wall time of the arm, excluding queueing.
- Usage, read from provider `usageMetadata` through `app.ai.telemetry`:
  - `input_tokens`, `output_tokens`, `thinking_tokens`, `cached_tokens`;
  - `requests`, `http_attempts`, `repair_attempts`.
- Schema/system overhead, as payload chars minus problem chars.
- `usd`: computed from the usage at the prices fixed in the GO.

**Missing usage:** recorded as `UNKNOWN`, never 0.

**Per-arm aggregates:**
- Rates with Wilson 95% intervals.
- A paired exact McNemar test on `served_correct` and on `wrong_served`.
- Median and p90 latency.
- Tokens and USD per problem, and per served-correct problem.

**Fake extractors and replay** measure the deterministic tail only. They are never reported as provider quality.

## 5. Early-stop rules (checked after every case)

1. Any `wrong_served` on an expected-refuse case in either arm: stop that arm; report it as a safety finding.
2. Accounted spend reaches 80% of the approved USD cap, or the request cap is reached: stop both arms at the case boundary.
3. Three consecutive transport or technical failures, or a provider block or safety refusal: stop and report `INFRASTRUCTURE`. This is not counted as a model failure.
4. A corpus or oracle hash mismatch, or a code-identity change (candidate hash, prompt fingerprint, `CACHE_VERSION`): stop before the next call.
5. **Carried forward from `hybrid-ab-pilot-readiness`:** a pre-request reservation cannot stop provider billing after a request is sent. The approved cap is therefore enforced by the conservative reservation, and the residual overspend risk is stated in the GO, not hidden.

## 6. Data sent to the provider and privacy

**Sent:** only the problem text, plus each arm's system prompt and schema, to Google Gemini `generativelanguage.googleapis.com/v1beta` with the Owner's API key.

**Not sent:** images, learner data, account data, cookies or repository content.

**Corpus content:** authored problems only, with no personal data.

**Storage:**
- Responses are stored locally in the run directory.
- Request and response bodies are stored only as hashes plus the decoded structured output.
- API keys and headers are never written (the pilot's redaction rule is reused).
- Provider-side retention follows the Owner's Gemini API terms. The Owner confirms this in the GO.

## 7. GO / NO-GO criteria for Hybrid production (pre-registered)

Hybrid may become the production default (D-13) only if **all** of these hold on the frozen held-out set:

1. Hybrid `wrong_served` = 0, and its upper 95% bound is ≤ the LLM_ONLY observed rate.
2. Hybrid `served_correct` is not worse than LLM_ONLY: the McNemar test does not favour LLM_ONLY at α = 0.05, and the point-estimate difference is ≥ −5 pp.
3. Expected-refuse cases: Hybrid refuses 100%, and its refusal-reason accuracy is ≥ LLM_ONLY's.
4. Hybrid median latency ≤ LLM_ONLY's, and its p90 ≤ 1.5 × LLM_ONLY's.
5. Hybrid USD per served-correct problem ≤ LLM_ONLY's.
6. Infrastructure failures ≤ 5% per arm.
7. `EVALUATOR_INDEPENDENCE` and `AUTHORING_INDEPENDENCE` are established. Otherwise the result is a diagnostic and **cannot** satisfy D-13.

Failing any criterion means NO-GO. The report states which criterion failed; thresholds are never re-tuned after results.

## 8. Harness state

See `live-harness-status.md`. The run is not started until every harness item there is `READY`.
