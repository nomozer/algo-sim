# Paired LLM_ONLY vs Hybrid live evaluation — protocol (DRAFT, closed for pre-registration)

**Status:** `DRAFT_AWAITING_OWNER_GO`. No live call has been made.

**How it becomes binding:** the Owner GO fixes three things: the corpus hash, the author, and the budget. From then on this file is the pre-registration. Later changes go into amendment files; this file is not edited.

**Executable form:** every rule below is implemented in `backend/scripts/run_paired_route_evaluation.py`, the harness. The approval binds that harness's hash, so the rules cannot change silently.

*Revision 2026-10-31.* This version closes the independent readiness review: B1–B3 and M1–M4 in `evaluation-readiness-review.md`. It changes the following from the previous draft:
- Curved solids are no longer an expected-refusal class.
- Oracles are exact numbers with π kept, not squared rationals.
- The refusal reason is a pre-registered class, not a raw error code.
- The asked-target rule, the technical-failure rule and the denominators are now fixed.

*Revision A (2026-10-31, before any corpus or live result exists).* Two acceptance defects are fixed. Neither one could favour Hybrid; both could only block a deserved GO.
- **A1, criterion 1.** The old rule was "Hybrid wrong-served = 0 **and** its Wilson upper bound ≤ the LLM_ONLY observed rate". That compared an interval bound with an observed rate, so it was unsatisfiable whenever LLM_ONLY was perfect: with 0/60 in both arms, Hybrid's upper bound is 6.02%, which is > 0%, so the result was NO-GO. Criterion 1 is now observed only: Hybrid shows 0 wrong-served, and none that the control does not also show. The Wilson interval is reported and compared with nothing.
- **A2, §5.1.** Stopping the **control** arm when it served an expected refusal left the pairs incomplete, so a GO became unreachable exactly when LLM_ONLY was the unsafe arm. Only Hybrid stops now; its criterion 1 has already failed. The control's wrong-serve is recorded, and its arm goes on.
- **§7 is now code.** `acceptance()` in the harness computes the verdict, and the run summary carries it. Before, §7 existed only as prose and no test covered it. The thresholds in criteria 2–7 are unchanged; only how undefined cases are treated is now fixed (§7).

## 1. Measurement metadata (actual values)

| field | value |
|---|---|
| `MEASUREMENT_CLASS` | `PREREGISTERED_LIVE_PAIRED_EVALUATION` for the planned run. Everything done so far is `OFFLINE_DETERMINISTIC_FIXTURE_TEST` or `DEVELOPMENT_DIAGNOSTIC`. |
| `HELD_OUT_CLAIM` | `NEW_UNOPENED_SET_REQUIRED`. Every corpus already in the repository is excluded as held-out. |
| `EVALUATOR_INDEPENDENCE` | `NOT_ESTABLISHED` until a named person who is not the implementer authors the set. Otherwise every result is an `IMPLEMENTER_AUTHORED_DIAGNOSTIC` and cannot satisfy D-13. |
| `AUTHORING_INDEPENDENCE` | `NOT_ESTABLISHED` (the same condition). |

## 2. Corpus

The authoring rules are in `heldout-authoring/README.md`.

**Composition: 60 problems.**
- **45 expected-serve:** each asks at least one exact quantity. Problems that only ask for a construction are excluded. Curved solids are **allowed** as expected-serve, with π oracles, because LLM_ONLY serves them in production. If Hybrid refuses them, that is a measured capability loss.
- **15 expected-refuse:** `refusal_class` is one of `OUT_OF_DOMAIN`, `CONTRADICTORY_DATA`, `MISSING_DATA` (5 each).
- **Proof requests ("Chứng minh …") are out of scope.** LLM_ONLY builds the figure for them by design (`geometry_program_generator.md`), so they are neither an expected refusal nor scorable as an exact-quantity serve. *Revision, readiness review round 2, N1.*
- **Numbers:** numeric data only. Symbolic units such as "cạnh a" are excluded, because the arms report unit coefficients differently.

**Oracle.**
- Each answer is written by the author before any run, by hand or with a CAS independent of the repository.
- Values are exact, written in the `radical.parse_exact` grammar (`8/3`, `2√6/3`, `36π`), keyed by kind: `distance` (lengths are distances), `angle_cos_sq`, `angle_cos`, `volume`, `area`, `lateral_area`, `radius`, `volume_ratio`, `residual_volume`.
- No model output may enter it.

**Integrity**, checked before any request:
- unique ids;
- unique texts after normalization (NFC, case, whitespace);
- an oracle on every expected-serve case;
- a pre-registered refusal class on every expected-refuse case.

**Contamination scan** (`--manifest`):
- **What it scans:** the whole repository except `.git`, vendor and build trees, and the corpus file itself.
- **Normalization:** NFC, case and whitespace normalization, with `\uXXXX` escapes decoded.
- **Exact match** blocks the run.
- **8-word shingle overlap** of at least 50% is reported for review.
- **Not detected:** paraphrase, a changed number in every shingle, and literals split across source lines. Independence rests on the author.

## 3. Arms and order

- **LLM_ONLY:** production `run_pipeline` with the default `RoutePolicy`. That is `semantic_analyze` (1 call), then `semantic_program` (up to 3 calls).
- **HYBRID:** the production opt-in path minus HTTP. It runs the same domain gate as `/api/analyze` (`main._ngoai_pham_vi`), then `run_hybrid_offline` with `TransportExtractor`.
- **Order:** each case runs both arms in a seeded order, `arm_order` with seed `hybrid-master-paired/2026-10-31`. Requests are sequential.

### Production equivalence (verified against code; confirmed by the readiness review)

| setting | LLM_ONLY | HYBRID | note |
|---|---|---|---|
| Model | `gemini.MODEL` | same | `gemini-2.5-flash`; access must be checked (`provider-facts.md`) |
| Prompt and schema | `app/ai/skills/*.md`; analyze schema sent; IR schema **not** sent (`$ref`) | `TransportExtractor` instruction + `TypedFactNextPayloadV2` schema | both hashed in `runtime_identity` |
| Output cap | **none**; model limit 65 536, thinking included | 8192 | production as is; no cap added to the control arm |
| Temperature | 0.1 | 0.0 | production as is |
| Retry and timeout | transient 429/5xx, 4 attempts, backoff, 120 s per attempt | same (`hybrid_transport`) | |
| End-to-end deadline | none | 480 s (`HYBRID_LIVE_DEADLINE_S`) | Before cutover, the production live Hybrid deadline must be set to this measured value. |
| Cache | none (`run_pipeline` called directly) | none | |
| Cost accounting | `usageMetadata`; a request without usage is charged at its ceiling | same | |

## 4. Scoring (one scorer, both arms)

**What is read:** the learner-visible `scene3d` objects of type `quantity` in display group `target`, keyed by producer kind. Values are compared as exact numbers (`radical.from_json`). An unreadable exact form gives `SCORER_ERROR`; it is never guessed.

**Per-case fields:**

| field | definition |
|---|---|
| `served` | envelope `status == ok` with scene objects |
| `served_correct` (**primary**) | served, expected-serve, and for every asked kind the shown target values are exactly the oracle's: each oracle value is shown, and **no other value of that kind is shown**. A wrong value the learner sees is never correct. *Revision, round 2, N2.* |
| `served_correct_lenient` (**sensitivity only**) | every oracle value is shown, whatever else of that kind is shown. This is reported and does not feed any criterion. |
| `unverified_extra_targets` | Targets of kinds the oracle does not ask. They are reported per case and per arm and are **not scored**. Their correctness rests on each arm's exact kernel; this is a stated limitation. |
| `wrong_served` | served and not `served_correct`; this includes any served expected-refuse case |
| `false_refusal` | expected-serve and not served, excluding technical failures |
| `refusal_reason_correct` | the arm's class equals the case's `refusal_class` |

**Refusal class per arm (fixed map):**
- **Both arms:** `failure_category = out_of_scope` → `OUT_OF_DOMAIN`; `not_simulation_suitable` → `NOT_SIMULATION_SUITABLE`, a class of its own that never matches an expected class.
- **Hybrid:** `classify_refusal(code).group`, with `INVALID_DATA` → `CONTRADICTORY_DATA` and `MISSING_DATA` → `MISSING_DATA`.
- **Anything else in either arm:** `UNSPECIFIC`, which is never correct. LLM_ONLY's `geometry_generation_failed` states no reason, and that is recorded as such.

**Technical (infrastructure) failure, one rule for both arms:**
- **Counts as technical:**
  - transport or HTTP errors after retries;
  - a deadline or budget stop;
  - a provider block or refusal, including an empty candidate list;
  - an internal fault of our code (Hybrid's `ROUTE_INTERNAL_ERROR` / `ADAPTER_INTERNAL_ERROR`, LLM_ONLY's raised exceptions);
  - an exception raised out of the arm.
- **Not technical:** a truncated or invalid model output. In LLM_ONLY it ends as `geometry_generation_failed`; in Hybrid it is `RESPONSE_TRUNCATED` / `JSON_INVALID`. Both count as **not served**.
- **How technical failures are scored:** they count as not `served_correct`, are never counted as false refusals or as refused negatives, and are reported separately.

**Denominators:**
- served-correct: over expected-serve cases;
- wrong-served: over all cases;
- refusal-reason accuracy: over expected-refuse cases.

**Other per-case data:**
- latency;
- usage (input, output, thinking and cached tokens);
- HTTP requests;
- `repair_attempts` (LLM_ONLY: `semantic_program` calls − 1; Hybrid: 0);
- `usd` (actual) and `usd_upper` (ceiling);
- for Hybrid: `extraction_valid`, `source_grounding` and source spans. LLM_ONLY exposes only `stage_reached`; its extraction and grounding are **not observable** separately.

**Per arm:**
- rates with Wilson 95% intervals;
- the number of technical failures and scorer errors;
- latency median and p90;
- USD total, upper bound, and per served-correct.

**Paired:** exact McNemar on complete pairs, for `served_correct` and for `wrong_served`. Unpaired cases from a stopped run are listed, not scored as pairs.

**Stored per row (JSONL, flushed as each row completes):**
- the served target values, refusal code and class, and stage;
- usage, latency and cost;
- the Hybrid source spans.

This is enough to re-score. Full model responses are not stored.

## 5. Early stop (checked after each arm; spend checked before every request)

1. **Hybrid serves an expected-refuse case:** the Hybrid arm stops (`stopped_arms`) and the event is reported as a safety finding; criterion 1 has failed. LLM_ONLY continues. **If LLM_ONLY serves one,** it is recorded as wrong-served and its arm continues (A2).
2. **Spend:** accounted spend reaches 80% of `max_usd` (`USD_80_PERCENT`).
3. **Caps:** the request cap is reached (`REQUEST_CAP`), or the next request's exact ceiling would exceed `max_usd` (`COST_CEILING`).
4. **Infrastructure:** 3 consecutive technical failures (`INFRASTRUCTURE_STREAK`), or a provider block or refusal (`PROVIDER_BLOCK`). A block is detectable by code only in the Hybrid arm; in LLM_ONLY it surfaces as an exception, counts as technical, and feeds the streak.
6. **Interruption:** an interrupted run writes `stop_reason = INTERRUPTED:<type>` and `completed: false`. Its rows are kept.

Oracle values must be exact strings. Decimals are refused before any request.
5. **Identity:** a change in the measured system, cache version, model, prompt files or harness (`IDENTITY_CHANGED`).

**Hard cap.** Before every HTTP request of either arm, `CostCappedBudget` checks this inequality on the **exact payload**:

> spend so far (requests without usage counted at their own ceiling) + the next request's ceiling ≤ `max_usd`

- **Input bound:** input tokens are taken as at most the UTF-8 bytes of the whole request JSON, including system instruction and schema. This is an assumption: byte-fallback tokenization.
- **Output bound:** output is bounded by the request cap, or else by 65 536 tokens including thinking, as documented by the provider.
- **Second line:** a provider prepay balance or spend cap is recommended. It can overshoot by about 10 minutes of usage, so it is not the primary cap.
- **Defaults without a GO:** `MAX_AUTHORIZED_LIVE_REQUESTS = 0` and `MAX_AUTHORIZED_LIVE_SPEND_USD = 0`.

## 6. Data and privacy

**Sent:** only problem texts, plus each arm's prompt and schema. The run uses a **paid** Gemini project; the free tier allows product use and human review of the content (`provider-facts.md`). Keys and headers are never written.

## 7. GO / NO-GO for Hybrid production (pre-registered)

Every criterion must hold on the frozen held-out set. The harness computes them in `acceptance()`, and the summary record carries the verdict. Each criterion is true, false or **not evaluable**; not evaluable counts as a failure.

0. **Preconditions.** The composition is exactly as pre-registered: 45 serve, plus 5 of each refusal class. The run is complete: `completed`, no stopped arm, and both arms having one row per case, all paired. An incomplete, unequal or empty run is **never a GO**. Criterion 1 is still applied to the rows it has, so a Hybrid wrong-serve makes it a determinate NO-GO.
1. **(A1)** Hybrid has **0 observed** `wrong_served`, and **no excess** over the control: `wrong_served_only_HYBRID` = 0 on the complete pairs. The Wilson 95% interval of each arm's wrong-served rate is reported as uncertainty. It is not compared with the other arm's observed rate. A result of 0/60 means a true rate ≤ about 6% is consistent with the data; it never means production makes no errors.
2. `served_correct` (primary) is not worse: the McNemar test does not favour LLM_ONLY at α = 0.05, and the difference is ≥ −5 pp. The lenient sensitivity rule is reported, and any reversal is flagged; it never overrides the primary rule.
3. Hybrid refuses 100% of expected-refuse cases, with technical failures excluded and reported. Its refusal-reason accuracy is ≥ LLM_ONLY's.
4. Hybrid latency: median ≤ LLM_ONLY's, and p90 ≤ 1.5× LLM_ONLY's.
5. Hybrid USD per served-correct ≤ LLM_ONLY's. When LLM_ONLY has 0 served-correct, its value is ∞. When Hybrid has 0 served-correct, or any usage is `UNKNOWN`, the criterion is not evaluable.
6. Technical failures are ≤ 5% per arm (at most 3 of 60), and there are 0 scorer errors.
7. `EVALUATOR_INDEPENDENCE` and `AUTHORING_INDEPENDENCE` are established. They are read from the Owner-written approval file: `corpus_author` must be non-empty, and `authoring_independence` and `evaluator_independence` must both be `ESTABLISHED`. The harness never writes them.

Any failure is a NO-GO, reported with the failing criterion. Thresholds are never re-tuned. The 60 problems cover only the strata they sample; they are not evidence about all of grade 11–12 geometry.
