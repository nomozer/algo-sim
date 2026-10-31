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

## Round 3: re-verification of `cbab8fde` — `LIVE_EVALUATION_READINESS_REVIEW_READY`

All round-2 items (N1, N2, M4, N3, m1, m2) are **CLOSED**, with evidence from new mock probes. 0 network calls, and no approval value was written.

**Auxiliary-target check under the strict rule.** Of 38 served Hybrid replays with targets, 14 show several values of one kind (auxiliary volumes). All 14 ask only for a ratio or remaining volume, so `volume` is an unasked kind there: it is reported, not penalized. No legitimate answer is failed.

**New, MINOR only:**

| id | finding | disposition |
|---|---|---|
| n1 | Inferred, not observed: a problem asking for a volume **and** a ratio or remaining volume would make Hybrid's auxiliary volume targets fail the strict rule. This works only against Hybrid, so it cannot produce a false GO, and the lenient rule flags any reversal. | Authoring rule added: ask for those quantities in separate problems. |
| n2 | Equal values listed twice in the oracle but shown once fail | Authoring rule added: write each distinct value once. |

**The verdict covers the harness and protocol only.** The run remains blocked outside them:
- `EVALUATOR_INDEPENDENCE` and `AUTHORING_INDEPENDENCE` are `NOT_ESTABLISHED`;
- no corpus has been authored;
- there is no Owner GO.

No live result exists.

## Acceptance contract (protocol §7, revisions A and B)

**Why this exists.** The Owner found that the §7 criterion 1 rule (Hybrid's Wilson upper bound ≤ LLM_ONLY's observed rate) was unsatisfiable: with 0/60 in both arms, the upper bound is 6.02%, which is > 0%. §7 also existed only as prose.

**Revision A, `5bec390f`:**
- `acceptance()` makes §7 executable;
- criterion 1 is now observed only;
- the control arm is never stopped (A2).

**Round 1, a fresh-context reviewer:** read-only, 0 network calls. Verdict `ACCEPTANCE_CONTRACT_REVIEW_NOT_READY`.
- **Verified correct:**
  - Wilson: 0/60 → (0, 0.06017); 9/10 → (0.5958, 0.9821).
  - Exact McNemar, against an independent pmf reference.
  - The criterion 2 denominator.
  - The thresholds of criteria 2–7 are unchanged.
  - A2 is justified and unbiased.
  - Precondition 0 rejects incomplete, stopped, duplicate, missing, empty and mis-composed runs.

| id | finding | disposition |
|---|---|---|
| B1 BLOCKER | Criterion 5 read actual USD. Out-of-domain cases refused by the deterministic gate make 0 requests and have no usage, so their USD is `UNKNOWN`, criterion 5 becomes not evaluable, and the result is always NO-GO. | **Fixed.** Criterion 5 reads the §3 charged cost, `usd_charged_total`, where a 0-request row costs 0.0. `test_a_deserved_go_is_reachable_end_to_end_with_zero_call_domain_gate_refusals` drives a GO through `evaluate()` with 5 zero-call OOD rows. Reverting to actual USD fails it. |
| M1 MAJOR | A technical failure without usage had the same effect. The actual-USD rule also contradicted protocol §3. | **Fixed** by the same single rule. |
| m1 | McNemar can never bind beside −5 pp when n = 45 | **Stated** in protocol revision B; thresholds unchanged |
| m2 | No floor on served-correct, so a collapsed control arm can still give a GO | **Stated.** The verdict flags `CONTROL_ARM_DEGENERATE`; it is not a criterion. |
| m3 | The interval counted technical failures as exercised | **Fixed:** the interval is over exercised rows |
| m4 | Revision A was framed as purely neutral | **Fixed:** the dropped comparative claim is stated |
| m5 | Counts, not identity; `stop_reason` was not read | **Fixed:** `stop_reason` must be null, and the paired ids must equal the corpus ids |
| m6 | Criterion-7 fields were not required in the approval | **Fixed:** `check_approval_terms` requires them to be stated |

**Tests:** 46/46.

**Round 2, the same reviewer, re-verifying `9e2cfe80`: `NOT_READY`.**
- **Re-probed and closed:** B1, M1, m3 (the interval over exercised rows), m5, and m6.

| id | finding | disposition |
|---|---|---|
| N1 BLOCKER | The B1/M1 fix put criterion 5 on charged cost (an upper bound) for **both** arms. Requests without usage are charged at their ceiling, and LLM_ONLY's ceiling is about 7× Hybrid's (no output cap). So one unbilled LLM_ONLY 429 turned a true criterion-5 failure into a GO. | **Fixed:** the comparison is now conservative. Hybrid is charged its upper bound (`usd_charged_total`), and LLM_ONLY its lower bound (`usd_reported_total`). The test covers the reviewer's probe, an LLM_ONLY 429 that stays NO-GO, and a Hybrid 429 that is charged against Hybrid. A mutant that puts the control on charged cost fails it. |
| N2 MAJOR | §7.5 still said "any `UNKNOWN` usage ⇒ not evaluable", which contradicted the code on the 0-request rows | **Fixed:** §7.5 states exactly two not-evaluable cases. |
| m-a | `arm_upper` matches ceilings by send order | **Stated** in §7.5. The effect is about USD 0.0004 per request. |
| m-b | `CONTROL_ARM_DEGENERATE` fires only at 0 served-correct | **Accepted** as stated: it is a flag, not a criterion. |
| m-c | The B1/M1 record did not say the rule moved to an upper bound | **Recorded here.** Revision C supersedes it. |

**Tests:** 46/46.

**Round 3, re-verifying `383fd4f7`: `NOT_READY`.**
- **Closed:** N1 and N2. A deserved GO is still reachable end to end, and Hybrid's upper bound cannot be under-counted live, because `usd_upper ≥ usd` and every send is reserved.

| id | finding | disposition |
|---|---|---|
| N3 MAJOR | The control's lower bound priced cached prompt tokens at the full input price. Implicit caching is on by default for 2.5 models, so that overstates LLM_ONLY's cost and could turn a true criterion-5 failure into a GO. | **Fixed:** `usd(..., floor=True)` prices `cached_content_tokens` at 0, and each row carries `usd_floor`. Revision D. A test covers it. |
| m-d | The descriptive `usd_per_served_correct` could disagree with the criterion | **Labelled** in §7.5 as descriptive; criterion 5 does not read it. |
