# Vietnamese NL → TypedFacts V2 — evaluation protocol (v1)

Run `hybrid-v2-nl-certificates-e2e`. Code: `backend/scripts/nl_eval_scoring.py`, `backend/scripts/run_nl_eval_offline.py`;
tests `backend/tests/geometry/test_nl_eval_scoring.py`. **Offline only: 0 provider calls.** Nothing here measures how well a
real model reads Vietnamese; it measures the deterministic stages and prepares the instrument for the day a live run is
approved.

## 1. What a "measurement" is here

| Arm | Extraction is | Measures | Provider |
|---|---|---|---|
| GOLD | the gold payload itself | validation + Source Gate + planner + exact engine | none |
| STRESS | an *unfaithful* payload (wrong value, wrong target, a non-premise turned premise) | whether the gate refuses what an extractor could wrongly emit | none |
| REPLAY | a recorded extraction (`ReplayExtractor`) | the same, for a recorded model output | none (recorded) |
| LIVE | the real model | extraction quality | **`LIVE_PROVIDER_GO_REQUIRED`** — not implemented in the runner |

`--live` exits with code 3 and prints `LIVE_PROVIDER_GO_REQUIRED`. The scorer and runner import no HTTP client and read no key
(pinned by `test_runner_has_no_provider_transport`).

## 2. Dataset item (`nl-eval-dataset/1`)

`id · family · split · problem_text · provenance{author_kind, origin, author, created} · exposure{label, in_tests, in_prompt,
seen_by_implementer} · gold{payload, expectation, contradiction} · stress_payloads[]`.

* `gold.payload` — the canonical `typed-fact-next/2` a *faithful* reader emits, with verbatim quotes (the gold TypedFacts and
  the gold provenance).
* `gold.expectation` — either `SERVE` with exact `values` (`{"q": "√17"}`; an angle is its exact `cos²`, the product's own
  quantity) or `REFUSE` with a `category` (`INSUFFICIENT · CONTRADICTORY · UNSUPPORTED · NOT_A_PREMISE · AMBIGUOUS ·
  UNPROVEN_RELATION`) and the gate codes that count as the right reason (`allowed_codes`).
* Values come from closed-form formulas written independently of the engine (`inputs/build_dev_dataset.py`), compared by the
  exact key `(power of π, sign, value²)` — never by float, never by string.

## 3. Splits, exposure, independence

| Split | Meaning | May tune code on it? | Claim ceiling |
|---|---|---|---|
| `DEV_AUTHORED` | written by the agent that implemented the pipeline | yes | `DEV_AUTHORED_NOT_INDEPENDENT` |
| `EXPOSED_PRIOR` | a former held-out set already seen (the 44 locked items of `independent-nlu-extraction-evaluation`) | yes, it is now development data | `DEV_OR_EXPOSED_NOT_INDEPENDENT` |
| `HOLDOUT` | authored by a party with no repository access, registered by hash **before** any tuning | **no** | `INDEPENDENT_HOLDOUT` only with a registered hash |

Rules enforced by `validate_dataset` / `claim_ceiling`:

1. A `HOLDOUT` item must be `FRESH` (not in tests, prompt or any fixture) and not `SAME_AGENT`.
2. The holdout is registered as `{dataset_sha256, registered_before_tuning: true, git_head, registered_at}` **before** code is
   tuned; editing a single character voids the registration (`claim_ceiling` falls back to
   `HOLDOUT_UNREGISTERED_TREAT_AS_DEV`).
3. If the same agent authors gold and implementation tests, the data is `DEV_AUTHORED`, whatever it is called.
4. Opening a holdout to adjust code converts it to `EXPOSED_PRIOR`; it can never be claimed independent afterwards.
5. The 60 cases of the earlier run (dev 16 + locked 44) are **EXPOSED**: the locked 44 were scored once live (UNSAFE by the
   frozen scorer, one scorer artifact — see that run's report); they are no longer held out for anything.

**Status of this run:** the only dataset is `inputs/nl_dev_authored.json` (51 items, `SAME_AGENT`, `EXPOSED`). **There is no
independent holdout.** `protocol/HOLDOUT_AUTHORING_BRIEF.md` is the request for one.

## 4. Scoring — separate layers, nothing summed

`entity` (labels named) · `facts` (canonical premise multiset: precision/recall; planes are vertex sets, segments undirected,
numbers exact, quotes excluded) · `provenance` (every quote verbatim in the source and carrying the labels of its own fact) ·
`goal` (canonical goal type + target) · `outcome` · `contradiction` · `e2e`.

Outcomes: `CORRECT_SERVED · INCORRECT_SERVED · CORRECT_REFUSED · INCORRECT_REFUSED · EXTRACTION_FAILURE`.

* gold SERVE: served with the exact value ⇒ correct; served with anything else (also *no* value, or a non-exact string) ⇒
  `INCORRECT_SERVED`; refused by the gate ⇒ `INCORRECT_REFUSED`.
* gold REFUSE: served ⇒ `INCORRECT_SERVED`; refused by the gate ⇒ `CORRECT_REFUSED` (the row records whether the code was in
  `allowed_codes`; a wrong reason is flagged, not hidden).
* A refusal that is **not** a gate verdict (no/unusable extraction, schema mismatch, provider or internal error) is
  `EXTRACTION_FAILURE` for either gold: it can neither prove the system safe nor wrong. The role/quote checks of the
  extraction validator (`CONDITIONAL_CLAUSE`, `NEGATED_CLAUSE`, `GOAL_CLAUSE_NOT_PREMISE`, `QUOTE_NOT_IN_SOURCE`) *are* verdicts.
* `e2e` is two ratios with their denominators — `correct_served / gold-SERVE items` and `correct_served / served` — never one
  accuracy.

## 5. Budget and stop policy (shared by offline replay and a future live run)

`StopPolicy(max_items, stop_on_incorrect_served=True, max_extraction_failures=5)`: stop at the first `INCORRECT_SERVED` (the
one outcome the product must never produce), on budget exhaustion, or when extraction failures exceed the cap. The runner
refuses to overwrite an existing artifact.

## 6. Reused from G05 (`feat/real-model-pilot-tooling` @ `471a2c79`, read only, not merged)

| G05 piece | Disposition |
|---|---|
| exact-value key (`khoa_chinh_xac`: compare `(π, sign, value²)`, floats ungradable) | **reused as a concept**, rewritten in `exact_key` / `same_value` (also strips the `cos²=` prefix of V2 answers) |
| rule "provider/schema failure is never a correct refusal" | **reused** (`EXTRACTION_FAILURE`) |
| outcome taxonomy (`SERVED_CORRECT/WRONG`, `REFUSED_CORRECT/WRONG`, …) | **adapted** to the four requested outcomes + `EXTRACTION_FAILURE` |
| budget / stop policy | **adapted** (`StopPolicy`) |
| fake-provider tests | **adapted**: `ReplayExtractor` + stress payloads instead of a fake transport |
| `g05_pilot_scene_replay.py`, `run_g05_real_model_pilot.py`, `certify_g05_real_model_pilot.py` | **not reused**: built for the retired LLM_ONLY semantic-program route, `analyze → program → IR` stages, cache 125/pre-V2 |
| raw live responses, tokens, secrets | **not copied** |

No historical live number is used to describe the current model or the current system.

## 7. Live pilot — approval packet (NOT approved, NOT run)

`LIVE_PROVIDER_GO_REQUIRED`. Before any call the Owner must approve, in writing: provider/model id; the registered holdout
hash and its author-independence statement; `max_items` and a USD ceiling; `stop_on_incorrect_served`; that the prompt and
schema are frozen (surface fingerprint recorded); `ALLOW_LIVE_AI=1` scoped to that run; and where raw responses are stored
(redacted, outside the repository). Until then every statement about extraction quality is `NOT_MEASURED`.
