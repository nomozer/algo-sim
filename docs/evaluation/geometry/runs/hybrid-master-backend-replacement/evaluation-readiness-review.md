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

## Round 2: re-verification of `edbc54b7` by the same reviewer — `NOT_READY`

**Closed:** B1, M1, and the curved-solid part of B2. The producer part of B3 and most of M2 and M3 were also confirmed closed.

**Open:**

| id | finding | fix |
|---|---|---|
| N1 BLOCKER | Proof requests were an expected-refuse class, but LLM_ONLY builds the figure for them by design (`geometry_program_generator.md:68-70`). This is the same flaw as curved solids. `not_simulation_suitable` was mapped to `OUT_OF_DOMAIN`. | `PROOF_REQUEST` is removed, and proof requests are out of scope (protocol §2). `not_simulation_suitable` → `NOT_SIMULATION_SUITABLE`, its own class. Refuse classes: 5 each of 3 (`test_proof_requests_are_out_of_scope_…`). |
| N2 BLOCKER | The lenient primary rule scored "shown 12 and 13" as correct against an oracle of 12, and GO criterion 1 used it. | The **strict** rule is now primary for `served_correct` and `wrong_served`. Lenient is a sensitivity check only. Targets of unasked kinds are reported as `unverified_extra_targets`; that limitation is stated (`test_a_wrong_value_the_learner_sees_is_never_correct`). |
| M4 REGRESSED (MAJOR) | The skip set was matched on the absolute path, so a checkout under `.superpowers/` scanned nothing. | Matched on the repo-relative path (`test_contamination_scan_works_inside_a_checkout_under_a_skipped_name`). **Probe on the real repository:** a sample text was found in 5 files, `geometry-samples.json` included, and a fresh text in none (51 s). |
| N3 MAJOR | An interrupted run was reported `completed: true` | `INTERRUPTED:<type>`, `completed: false`, rows kept (`test_an_interrupted_run_is_reported_as_interrupted`) |
| m1 | Decimal oracles were accepted | Refused (`test_decimal_oracles_are_refused`) |
| m2 | `NO_CANDIDATE` and internal faults were asymmetric between the arms | `NO_CANDIDATE`, `ROUTE_INTERNAL_ERROR` and `ADAPTER_INTERNAL_ERROR` are infrastructure on Hybrid. An LLM_ONLY provider block cannot be detected by code; it counts as technical and feeds the streak (protocol §5.4). |

**Tests:** 38/38.

## Round 3

Pending.
