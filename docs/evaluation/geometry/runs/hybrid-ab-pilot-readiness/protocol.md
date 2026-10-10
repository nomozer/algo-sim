# Hybrid A/B pilot readiness correction protocol

Status: **DRAFT FOR HUMAN REVIEW — NO LIVE RUN AUTHORIZED**  
Run: `hybrid-ab-pilot-readiness`  
Corrects: `hybrid-compiler-selection`  
Branch: `feat/text-to-geometry-functions`  
Preflight HEAD: `5c33406a5697c6f3bac4e56d443f8a9ca6a82fd7`  
Current frozen candidate: `e9d20aa2...` (product commit `91e2edf9`, frozen at `c748c682`)  
Cache identity: `CACHE_VERSION = "125"`  
Live Gemini calls in this run: **0**

This is an additive correction layer. Files in `hybrid-compiler-selection` remain byte-identical. After implementation and
verification, `docs/EVIDENCE_INDEX.md` must connect that run to this one with `CORRECTED_BY`; the historical results remain
historical observations, not rewritten results.

## 1. Scope and non-goals

This run does four bounded things:

1. closes wrong-object acceptance introduced by the `lập phương` and `chữ nhật` source-grounding cues;
2. makes the arm-B checker report only what it actually establishes on one constructed configuration;
3. certifies an offline P-AB1 runner with fake providers and hard budgets;
4. freezes a corrected development-pilot protocol before any model output is observed.

It does not add a general proof system, Z3/cvc5, a second FactGraph, a new planner, or a new rendering path. Both arms continue
to share the Geometry Function Registry, engine, IR, kernel, and Scene3D. It does not wire either arm into `run_pipeline`, does
not change `LLM_ONLY`, and does not authorize a paid request, merge, or push.

## 2. Source-grounding correction

### 2.1 Finding

The current gate checks call labels against the whole problem and checks `lập phương` / `chữ nhật` as substrings of a quote,
but it does not bind the shape phrase to the polygon named by the call. At preflight HEAD, both adversarial calls below are
accepted:

- a cube named `ABCD.EFGH` grounds `regular_polygon(KLMN)` even when the quote does not mention `KLMN`;
- a rectangular box named `ABCD.EFGH` grounds `rectangle(KLMN)` when `KLMN` is merely a different quadrilateral later in the
  same quote.

### 2.2 Required behavior

The five existing layers remain: quote location, clause role, negation scope, predicate/reference binding, and value binding.
No layer is relaxed.

For the two audited definitional cues, predicate/reference binding additionally requires a direct object witness:

- `lập phương` may ground `regular_polygon(vertices=V)` only when the same shape phrase names a cube and `V` is exactly one
  named face (base or top) of that cube;
- `chữ nhật` may ground `rectangle(vertices=V)` only when the same shape phrase directly names `V` as a rectangle, or names a
  rectangular box for which `V` is exactly one named face.

Matching remains deterministic and text-bound. A keyword on another object, a near-name, or labels elsewhere in the quote is
not a witness. Failure code: `OBJECT_NOT_IN_QUOTE`. Existing legitimate forms such as `hình lập phương`, `khối lập phương`,
`hình hộp chữ nhật`, `ABCD là hình chữ nhật`, and `đáy ABCD là hình chữ nhật` remain positive cases.

The independent oracle fixture is registered before implementation and covers: negation, conditionals, proof goals,
near-named objects, multiple solids/faces, correct keyword on the wrong object/relation, facts outside the quote, and
mathematically equivalent positive wording. Every row carries literal expected status/code for both A calls and B TypedFacts;
the oracle does not call a production helper to derive its expected value.

## 3. Checker semantics correction

### 3.1 Finding

`engine._kiem_tren_hinh` evaluates a relation on one deterministic construction. `run_fact_route` currently maps its Boolean
result to `HOLDS`/`FAILS`, then describes `HOLDS` as a proved goal and can describe a violated negated premise as globally
inconsistent. A single model observation does not establish entailment unless a separate proof certificate says it does.

### 3.2 Returned states

Every checked statement has one of these evidence states:

| state | exact meaning | may be shown as proved? |
|---|---|---|
| `TRUE_ON_CONFIGURATION` | true on the constructed configuration only | no |
| `PROVED_FROM_HYPOTHESES` | a checked proof certificate derives it from the hypotheses | yes |
| `FALSE_ON_CONFIGURATION` | false on the constructed configuration only | no |
| `UNVERIFIABLE` | the checker cannot evaluate it | no |

This run creates no general certificate producer, so `PROVED_FROM_HYPOTHESES` is a reserved state and is not emitted by the
configuration checker. The planner payload records, for every proof goal, `evidence_state`, `proof_status`, and
`can_present_as_proven`; only the reserved proved state permits the last field to be true. The old ambiguous strings `HOLDS`
and `FAILS` disappear from current arm-B output.

A proof goal does not become a premise. When independent numeric questions were answered, the route may return those answers
but must mark the proof obligation `UNVERIFIABLE` and `can_present_as_proven = false`; a proof-only request without a certified
proof is refused with `PROOF_UNVERIFIABLE`. A false-on-configuration observation is not renamed `PROOF_GOAL_FALSE`.

A negated premise is never silently ignored. Until a proof certificate can establish compatibility or contradiction, the route
refuses with `NEGATED_CLAUSE` and retains only the configuration observation. It must not return `INCONSISTENT_FACTS` merely
because one constructed configuration makes the positive proposition true.

No frontend currently consumes this experimental route. Regression tests nevertheless serialize the returned planner data and
prove that an unverified result carries no positive proof flag or proof wording.

## 4. Honest planner capability boundary

`geometry-fact-planner/1` currently provides deterministic:

- TypedFacts validation and clause-role handling;
- relation-type-to-function mapping;
- bounded definitional expansion;
- role-based reference resolution;
- dependency ordering of emitted function calls.

It does not search over alternative plans, optimize a plan, backtrack, establish general geometric entailment, or implement a
general goal-directed planner. A question determines which `ask_*` call is emitted, but premise selection and construction are
rule-driven over the full fact set, not backward planning from a goal. Current documentation may call it a deterministic rule
planner/compiler; it must not claim general Goal-Directed Planning.

## 5. P-AB1 corpus and identity lock

The development corpus has exactly 48 rows, namespaced to prevent ID collision:

- `g05/*`: the 16 immutable rows from `g05-real-model-pilot/PILOT_CASES.json` at branch
  `feat/real-model-pilot-tooling`, commit `471a2c79`;
- `paraphrase/P01` through `paraphrase/P10`: the ten positive paraphrase rows from
  `backend/tests/geometry/fixtures/paraphrase_cases.json`;
- `expansion/X01` through `expansion/X08`: all eight rows from `geometry_expansion_cases.json`;
- `hybrid/H01` through `hybrid/H14`: all fourteen rows from `hybrid_holdout_cases.json`, with the checker interpretation
  corrected by section 3 rather than by editing the historical fixture.

The new run owns a materialized `inputs/pilot_cases.json` and `inputs/oracle.json`. Canonical UTF-8 JSON hashes of both are
pinned in `run.json` and in the runner. The runner also pins the candidate/product commit, `CACHE_VERSION`, model target,
parameters, price table, schedule seed, arm surface fingerprints, and runner source hash before its first provider call. Any
mismatch is a preflight refusal.

Two execution modes have separate identities and may not borrow claims from one another:

| mode | locked corpus | samples | logical calls | claim boundary |
|---|---:|---:|---:|---|
| `SMOKE_AB` | 12 rows | 1 | 24 | apparatus/surface smoke only; no FULL_AB conclusion |
| `FULL_AB` | 48 rows | 3 | 288 | development-pilot comparison under §7 |

The twelve `SMOKE_AB` rows are selected before any model output and remain fixed:

`g05/X1`, `g05/P09`, `g05/NT2`, `g05/N02`, `paraphrase/P01`, `paraphrase/P08`, `expansion/X02`,
`expansion/X06`, `hybrid/H01`, `hybrid/H05`, `hybrid/H07`, and `hybrid/H13`.

Each mode pins its own ordered corpus hash, oracle projection hash, canonical schedule hash, seed, and parameter hash. Smoke
artifacts use a distinct run ID/output directory and are rejected as input to the FULL_AB scorer. Approval for one mode does not
authorize the other; `FULL_AB` always requires a separate human approval after smoke review.

This remains `MEASUREMENT_CLASS = DEVELOPMENT_ARCHITECTURE_AB_PILOT`, `HELD_OUT_CLAIM = NO`, and
`EVALUATOR_INDEPENDENCE = PARTIAL`. The author has seen the corpus. It must never be described as an independent held-out set.

## 6. Runner contract

### 6.1 Arms and schedule

- A: `run_ai_function_route` with Gemini constrained function calling (`ANY`).
- B: `run_ai_fact_route` with Gemini structured TypedFacts followed by the deterministic planner.
- Same model target, temperature `0.0`, maximum output `3072`, and no content retry.
- `SMOKE_AB`: 12 × 1 × 2 = 24 logical calls. `FULL_AB`: 48 × 3 × 2 = 288 logical calls. Arm order is deterministically
  shuffled within each `(case, sample)` using a mode-specific pinned seed. No `LLM_ONLY` fallback exists.

Effective surface fingerprints for parameter version 2 (3072, awaiting human review) are:

- A: `f329e89155b162ad1e0cd03b6c437542b0be8175907c09153e4b508a2f75f8ee`
- B: `aa198078c47ffdf0e05e31b1726c62c1c218a87dc02e7d5698f144c11d27e2ce`

They are recomputed after implementation; a changed surface requires another human protocol review before live execution.

### 6.2 Hard caps and pre-request reservation

| cap | `SMOKE_AB` | `FULL_AB` |
|---|---:|---:|
| scheduled logical calls | 24 | 288 |
| logical-call hard cap | 24 | 300 |
| HTTP-attempt hard cap | 36 | 450 |
| accounted-token hard cap | 500,000 | 6,000,000 |
| estimated-cost hard cap | USD 0.60 | USD 7.00 |

Pricing is pinned at USD 0.30 / million input tokens and USD 2.50 / million output-plus-thinking tokens for
`gemini-2.5-flash`. Cost accounting is conservative: prompt tokens receive no cache discount; output cost uses candidates plus
thinking; accounted tokens are `max(total, prompt + candidates + thoughts)`.

Reservation is computed from the actual canonical payload immediately before every request; there is no fixed estimate that can
fall below a larger payload:

- `prompt_reserve = len(canonical_payload_utf8_bytes) + 4096` accounting units. This is a deliberately conservative local
  estimator, NOT a documented Gemini-tokenizer upper bound. The 4096 allowance is unverified provider framing margin.
  Neither bytes nor this margin are a provider guarantee; actual usage is checked after each response. A first-request
  reservation breach can already incur cost, so strict billed-cost containment is NOT certified by offline fixtures.
- `output_reserve = maxOutputTokens = 3072` tokens. Gemini documents `maxOutputTokens` as the hard maximum for the combined
  generated response **including thought tokens**; reserving candidates and thoughts separately at the same ceiling double-counts
  an impossible response.
- `token_reserve = prompt_reserve + output_reserve`.
- `cost_reserve = prompt_reserve × 0.30 / 10^6 + output_reserve × 2.50 / 10^6` USD.

The pinned model input limit is 1,048,576 tokens and its model-level output limit is 65,536; this experiment deliberately keeps
the stricter request-level `maxOutputTokens = 3072`. Combined output/thought semantics follow the
[official Generate Content thinking documentation](https://ai.google.dev/gemini-api/docs/generate-content/thinking#token-limits-and-max_output_tokens).
These values were rechecked against the
[official Gemini 2.5 Flash model page](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash) on 2026-10-10; the pinned
prices match the [official pricing page](https://ai.google.dev/gemini-api/docs/pricing). The runner rejects a reservation above
the input context limit. After a response, observed usage is compared with
the reservation; any reservation breach stops the run and is reported, never silently absorbed. The initial implementation does
not call a remote token-count endpoint because live calls are forbidden in this run.

### 6.2.1 Budget-resolution amendment (2026-10-10)

The original draft treated one UTF-8 byte as a conservative prompt-token upper bound (plus 4096 framing) **and** reserved
`8192` for candidates plus another `8192` for thoughts. The second term was invalid: Gemini's documented output ceiling already
includes thought tokens. We evaluated every one of the 48 locked texts with the exact serialized A and B requests, without a
provider request. The table is a conservative local accounting calculation, not a certified provider upper bound or a claim
that bytes equal billed tokens.

| request output cap | smoke accounted tokens | smoke reserved USD | full accounted tokens | full reserved USD | disposition |
|---:|---:|---:|---:|---:|---|
| 2048 | 470,640 | 0.249326 | 5,645,322 | 2.991209 | less response margin; full needs cap amendment |
| 3072 | 495,216 | 0.310766 | 5,940,234 | 3.728489 | selected |
| 8192 | 618,096 | 0.617966 | 7,414,794 | 7.414889 | exceeds both original ceilings |

`3072` preserves the USD ceilings (USD 0.60 / USD 7.00), leaves 4,784 accounted-token headroom for smoke, and needs only the
FULL accounting cap amendment to 6,000,000. The cap is not an arbitrary truncation setting: the largest hand-audited expected
typed-fact response among the locked non-G05 corpus is 1,307 UTF-8 bytes, leaving material headroom below 3072 for a compact
function-call or JSON response. The actual largest fixture response envelope is 1,644 UTF-8 bytes in certification. Fixture
bytes do not measure actual output tokens or dynamic thinking allocation. This is still not live truncation evidence; any
`MAX_TOKENS` response stops the run and a live
pilot requires separate approval. Surface fingerprints and all mode identities are recomputed under this new parameter version.

Before every logical call and every HTTP attempt, the runner checks all four mode-specific global caps. Before an HTTP attempt it
additionally requires room for the payload-specific reservations. Counters are incremented before the operation. A cap hit
records a stop reason and performs no request. Missing or malformed `usageMetadata` stops the run because token/USD state is
unknown. The draft runner does not automatically retry a timeout or provider error; therefore ambiguous billing cannot be
hidden. HTTP-attempt accounting is still independent and future retry behavior cannot bypass its cap.

Other mandatory stops: missing/mismatched `modelVersion`, the FIRST provider error or non-STOP finish reason, a secret found
in any persisted artifact, or surface/corpus/oracle/parameter mismatch. Stopping at the first truncation is stricter than the
old 30%-of-ten threshold and avoids additional ambiguous billing. Bad model extraction quality alone never stops the run.

### 6.3 Persistence and observability

Before the first call, write and read back an atomic manifest. Each scheduled call then atomically persists:

- arm, case, sample, schedule position, payload hash, surface hash;
- logical-call and HTTP-attempt counters;
- redacted raw provider body;
- `usageMetadata`, `modelVersion`, `finishReason`, latency, and conservative USD estimate;
- route status/code, answer digest, planner trace for B, outcome class, and failure taxonomy.

Usage and totals are kept separately for A and B as well as globally. Resume never repeats a completed schedule row; an output
without a valid manifest or with a partial row fails closed. Secrets are redacted recursively before persistence, error strings
are redacted before logging, and the entire output tree is scanned after each row. Token-count field names are not themselves
redacted.

### 6.4 Failure taxonomy

Every unsuccessful row has exactly one primary source:

- `infrastructure`: timeout/network/HTTP/provider envelope, missing usage, persistence, or budget stop;
- `ai_extraction`: malformed or omitted calls/facts, quote/value/role/negation extraction errors;
- `compiler`: TypedFacts validation, unsupported planner rule, reference resolution, dependency planning;
- `geometry`: source-grounded plan rejected by geometry construction, IR, kernel, self-check, or Scene3D.

Outcome class remains separate: `correct_served`, `wrong_served`, `correct_refusal`, `false_refusal`, `unsupported`, or
`infrastructure`. Infrastructure rows are excluded from product-quality denominators and reported explicitly; they are never
counted as correct refusals.

## 7. Corrected comparison criteria

This is a development pilot, so effect sizes and problem-clustered bootstrap intervals are reported; no population-level
significance claim is made.

Primary safety endpoint:

- B is **non-inferior for wrong service** when the upper one-sided 95% problem-clustered bootstrap bound for
  `rate_B(wrong_served) - rate_A(wrong_served)` is at most +5 percentage points. If both arms have zero wrong service, the
  observed difference is zero and the *comparative* criterion is attainable.

Zero observed `wrong_served` in both arms means only “none was observed in this finite development sample.” It does not prove
either system safe and does not estimate the true error probability as zero. The report must include the denominator, a binomial
upper confidence bound for each arm, the clustered paired uncertainty for the difference, and the explicit text
`NO OBSERVED ERROR ≠ PROVED SAFE`. `SMOKE_AB` never evaluates this endpoint; only `FULL_AB` may report it.

Secondary utility endpoints:

- B is **superior for correct service** only when the lower one-sided 95% bound for the paired difference on positive problems
  is above zero;
- B is **non-inferior for false refusal** when the upper one-sided 95% bound for the paired difference is at most +10 points;
- correct refusal on negative problems, selective accuracy, and coverage are reported separately rather than joined in an
  impossible all-or-nothing rule;
- B token output is non-inferior when the upper one-sided 95% bound of the paired median ratio is at most 1.10.

Selection/assembly and extraction-error rates are mechanism diagnostics, not conjunctive win gates. The final result uses one
of: `SUPERIOR`, `NON_INFERIOR_NOT_SUPERIOR`, `INFERIOR`, `INCONCLUSIVE_STATISTICAL`, or `INCONCLUSIVE_INFRASTRUCTURE`.
Failure to establish non-inferiority is not evidence of inferiority: `INFERIOR` requires the lower bound to exceed a loss
margin; overlapping uncertainty yields `INCONCLUSIVE_STATISTICAL`. Bootstrap resampling retains repeated cluster weights
for the median paired output ratio as well as for rates. Answers are bound to sealed question signatures, never JSON order.
No wording converts association
between an arm and an error category into causality.

## 8. Independent confirmation set proposal

After the development pilot, a different evaluator should author and seal a confirmation set without seeing prompts, schemas,
planner rules, or pilot outputs. Target: at least 60 problems, balanced positive/negative and stratified across clause role,
negation, multi-object binding, definitional expansion, reference ambiguity, underdetermination, contradiction, and unsupported
capability. A second evaluator adjudicates disagreements; only text, obligations, exact answer/refusal oracle, and rationale are
released after sealing. The repository team may validate schema and duplicate detection without viewing labels. Until this is
done, `HELD_OUT_CLAIM` remains `NO`.

## 9. Offline certification and live gate

The fake-provider certification must execute the production A and B entry points for the exact 24-row `SMOKE_AB` schedule and
the exact 288-row `FULL_AB` schedule and prove: separate mode/corpus/schedule identities; branch separation; all cap checks;
missing usage/modelVersion; HTTP error; timeout; malformed response; redaction and leak stop; atomic persistence/resume;
taxonomy; fingerprints; no `LLM_ONLY` call; and deterministic scoring. Mutation checks must kill removed prechecks, swapped arm
labels, permissive missing usage, proof overclaim, wrong-object grounding, and using smoke rows in a full-pilot conclusion.

Only after targeted tests, geometry oracles, renderer metric checks, documentation audit, and the full backend suite pass may the
handoff say the runner is technically ready. Visual hidden-edge/label/face/interactivity acceptance is not implied by numeric 3D
metric checks. Even then the handoff remains `HYBRID_AB_PILOT_READINESS_AWAITING_REVIEW`; a human must separately approve
the paid run and its exact locked hashes. The live CLI requires all of `--live`, `ALLOW_LIVE_AI=1`, and a key supplied through the
approved environment variable; the fake-certification path accepts none of these and has no network-capable provider.
