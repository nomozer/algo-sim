# Live harness status — `backend/scripts/run_paired_route_evaluation.py`

**Locks:** `backend/tests/test_paired_route_evaluation.py`, 27 tests, offline. The live path runs against a **mock provider**: `httpx.post` / `httpx.AsyncClient.post` are replaced, and the conftest transport guard still blocks the real network. A mock run is never live evidence.

| item | state | test |
|---|---|---|
| One name-free scorer for both arms: learner-visible `scene3d` targets by producer kind, as exact squared multisets; an extra or missing target is not correct | READY | `test_one_scorer_…` |
| Dry run never touches a provider | READY | `test_dry_run_…_never_touches_a_provider` |
| Corpus integrity before any request: duplicate id or text (duplicate request), missing oracle, unknown kind, refusal codes; contamination scan of opened material (`--manifest`) | READY | `test_an_invalid_corpus_…`, `test_contamination_scan_…` |
| Live authorization: `ALLOW_LIVE_AI`, key, Owner approval file (written only by the Owner), corpus hash, model, output reservation ≥ model limit, `max_requests × estimate ≤ max_usd` | READY | `test_live_is_refused_before_any_request` |
| **Hard USD cap, enforced per request on the exact payload:** before every send of either arm, `request_ceiling_usd(payload)` (input ≤ UTF-8 bytes; output ≤ the request's `maxOutputTokens`, else 65 536 including thinking) plus spend so far (unreported requests at their ceiling) must stay ≤ `max_usd` | READY | `test_cost_ceiling_…`, `test_the_ceiling_is_the_exact_payload_bound_per_request` |
| Request cap across both arms, including production `run_pipeline` → `call_gemini` | READY | `test_request_cap_…`, `test_the_real_llm_only_arm_is_held_by_the_same_request_cap` |
| Production-equivalent Hybrid transport: the existing `live_transport` (key in header), the same retry and 120 s timeout as `call_gemini`, a 480 s deadline instead of the replay default of 15 s | READY | `test_mock_rate_limit_…`, protocol §3 table |
| Failure modes are typed, counted and never scored as a model or geometry result: timeout, 429/5xx retry, 4xx, truncated (`MAX_TOKENS`), invalid JSON, blocked prompt, refused response | READY | `test_mock_transport_failures_…`, `test_mock_bad_provider_outputs_…` |
| Early stop: `SERVED_EXPECTED_REFUSAL`, `USD_80_PERCENT`, `INFRASTRUCTURE_STREAK`, `REQUEST_CAP`, `COST_CEILING`, `IDENTITY_CHANGED` (measured hash, cache version, model, prompt files, harness hash) | READY | the corresponding tests |
| A stopped run is final and honest: `completed: false`, stop reason, unpaired cases; the output file is never overwritten | READY | `test_request_cap_…`, `test_a_finished_run_is_never_overwritten` |
| Statistics: Wilson 95%, exact McNemar on complete pairs, latency median/p90, USD actual and upper | READY | `test_statistics`, dry run |
| Real provider behavior, tokens, latency, cost | **NOT_MEASURED** | needs the Owner GO |
| Held-out corpus by an independent author | **NOT_ESTABLISHED** | `heldout-authoring/` package ready; no author named |

**Overall:** the harness is `READY_FOR_LIVE_MEASUREMENT`. The evaluation is **not** runnable until the corpus exists and its author is named.
