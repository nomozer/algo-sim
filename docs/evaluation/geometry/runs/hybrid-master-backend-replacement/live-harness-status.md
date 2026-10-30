# Live harness status — `backend/scripts/run_paired_route_evaluation.py`

**Locks:** `backend/tests/test_paired_route_evaluation.py`, offline, 0 provider calls.

| item | state | evidence |
|---|---|---|
| One scorer for both arms: learner-visible `scene3d` target quantities by producer kind, exact squared multisets, name-free; an extra or missing target is not correct | READY | `test_one_scorer_reads_learner_visible_targets_by_kind_as_exact_multisets` |
| Both arms on the same text: production `run_pipeline` (default `RoutePolicy`) vs `run_hybrid_offline` + `TransportExtractor` | READY (the code path exists; the live behavior is unmeasured) | harness source |
| Per-case dimensions: served, correct, wrong-served, false refusal, refusal-reason, latency, usage, USD (`UNKNOWN` when usage is missing), technical failure, Hybrid source spans | READY | `test_dry_run_scores_both_arms_and_pairs_them` |
| Statistics: Wilson 95%, exact McNemar on complete pairs, median/p90 latency, USD per served-correct; unpaired cases reported | READY | `test_statistics`, live stop test |
| Live gate: `ALLOW_LIVE_AI=1`, key, Owner approval file (`APPROVED_BY_USER`, written only by the Owner), corpus hash, model, caps; worst-case `max_requests × request ceiling ≤ max_usd` | READY | `test_live_is_refused_before_any_request` |
| Pre-request containment by count, the same `gemini.ApiBudget` for both arms; stop reasons `REQUEST_CAP`, `USD_80_PERCENT`, `SERVED_EXPECTED_REFUSAL`, `INFRASTRUCTURE_STREAK` | READY | `test_live_path_enforces_the_request_cap_before_sending` (fake provider) |
| Residual billing risk: a request already sent cannot be un-billed (finding carried from `hybrid-ab-pilot-readiness`) | DISCLOSED | protocol §5 |
| Real provider behavior, tokens, latency and cost | **NOT_MEASURED** | needs the Owner GO |
| Held-out corpus and oracle by an independent author | **NOT_ESTABLISHED** | needs a named author (protocol §1–2) |

**Overall:** `READY_FOR_LIVE_MEASUREMENT` for the harness. The **corpus** does not exist yet, and its independence is NOT_ESTABLISHED.

**Not reported as provider quality:** fake extractors and replay. The dry-run class is `OFFLINE_DETERMINISTIC_FIXTURE_TEST`.
