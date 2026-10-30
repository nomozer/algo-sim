# Independent live-evaluation readiness review

**Reviewer:** a fresh-context subagent. It was read-only, made 0 network calls, and used mock providers only. Its probes stayed in the session scratch directory.

**First pass, harness at `c14189d6`:** `NOT_READY` — 3 BLOCKER, 4 MAJOR, 4 MINOR. The implementer verified each finding against the code before fixing it.

| id | finding | fix (harness, tests, protocol; no product code) |
|---|---|---|
| B1 | The scorer dropped π, so 36π scored correct against an oracle of 36 | The oracle uses the `radical.parse_exact` grammar, and served values are read with `radical.from_json` and compared as exact numbers. An unknown form gives `SCORER_ERROR` (`test_scorer_compares_exact_numbers_with_pi_…`). |
| B2 | "Curved = expected refuse" described a Hybrid limit, not a property of the problem, because LLM_ONLY serves curved solids. A served expected-refusal also stopped the whole run, which contradicted protocol §5.1. | Curved solids are now expected-serve with π oracles, and `REFUSAL_CLASSES` has no curved class. The arm that serves an expected-refusal is stopped on its own (`stopped_arms`) (`test_a_served_expected_refusal_stops_only_that_arm`). |
| B3 | The `assign.volume_ratio` / `assign.residual_volume` producers were missing; auxiliary targets made correct answers wrong; construction-only problems were unscorable | Those producers and `measure.angle_cos` are added. Primary rule: oracle ⊆ served targets of each asked kind. The strict sensitivity rule is reported. Construction-only problems are excluded by the corpus rule (`test_ratio_and_residual_producers_…`). |
| M1 | Paid results were lost on a crash, an existing output file, or a scorer exception | The JSONL output is created before the first request, each row is flushed, and scorer errors become `SCORER_ERROR` rows (`test_a_scorer_bug_never_loses_a_row`, dry-run JSONL test). |
| M2 | The same failure was classified differently in the two arms; technical failures on negatives counted as refusals | One rule: infrastructure = transport, provider or budget failures; a truncated or invalid model output = not served, in both arms. Technical failures on negatives are excluded and reported (`test_mock_bad_model_output_is_not_served_in_both_arms_alike`). |
| M3 | Protocol open or diverging from the code | Closed: seeded arm order; `PROVIDER_BLOCK` stop; McNemar for `wrong_served`; denominators defined; a pre-registered refusal-class map; the approval binds the measured-system and harness hashes; `evaluate` re-checks the approval against the exact corpus bytes (no TOCTOU); the production domain gate is applied on the Hybrid arm (found by the implementer); stored fields stated honestly; numeric units only; extraction and grounding are observable for Hybrid only. |
| M4 | Contamination scan gaps | Now: whole repository; NFC normalization; `\u` escapes decoded in every file; the corpus file is excluded from its own scan; an 8-word shingle near-match report; limits (paraphrase) stated (`test_contamination_scan_finds_opened_text_and_reports_its_limits`). |
| MINOR | Ceiling ordering, the tokens ≤ bytes assumption, approval re-check in `evaluate`, exact-only duplicates | The approval re-check and normalized duplicates are fixed. The tokens ≤ bytes assumption is stated in protocol §5. The order-based ceiling matching is kept: its error is bounded by input-size differences, with large output slack. |

**Tests:** `backend/tests/test_paired_route_evaluation.py`, 32 tests, all passing.

## Re-verification

Pending. See the second-pass section below once it has run.
