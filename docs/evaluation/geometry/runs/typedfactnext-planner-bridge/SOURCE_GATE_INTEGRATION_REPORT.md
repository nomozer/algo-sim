# SOURCE_GATE_INTEGRATION_REPORT — P3

## 1. Three grounding authorities on `main` 43247c9e

| authority | where | what it checks |
|---|---|---|
| Registry Source Gate | `registry.kiem_nguon` (+ engine `kiem_mat_viet`, `kiem_mo_ta`) | quote in source, labels in source, closed predicate grammar per function, clause role (premise / goal / condition / question / negation), premise coverage of every sentence before the first request, number ownership, question-context reading, planner certificates |
| Source Gate follow-up (SGH-02/04/09/10) | **already on `main`** (`68acc140` is an ancestor) | multi-goal question stripping, compound line premises |
| Adapter /3 | `_verify_quote_in_problem`, `_verify_number_in_quote` | quote is a substring; a stated number appears in its quote — nothing else |

Integration chosen (no third gate): TypedFactNext reaches `kiem_nguon` through the bridge (pure translation) and route B
— every bridged call is checked exactly like a route B call; the new cut / derived-pyramid constructs pass ONLY through a
planner certificate (`DINH_CAT_CANH`) that the gate re-binds to closed source wording.

## 2. The two reported defects — re-checked, root-caused, fixed RED-first

| defect | reported cause | actual root cause on 43247c9e | fix (one authority) | evidence |
|---|---|---|---|---|
| `divide_segment` + "SM = 1/3 SA" ⇒ `SOURCE_PREMISE_UNREAD` | `value_fields=()` | (a) premise coverage credits numbers only through `value_fields`; listing `ratio` would be wrong (the stated number need not equal t: "SM = 2MA" ⇒ 2 vs t = 2/3). (b) Then `QUESTION_CONTEXT_UNSUPPORTED`: the definition grammar `_CUM_DINH_NGHIA_DIEM` required "M là … điểm thuộc", while the binding grammar `_TY_SO` accepts "Điểm M thuộc cạnh SA sao cho …" | (a) the coverage pass credits exactly the coefficient span of a `_TY_SO` match that SOLVES to the call's ratio (`_ty_so_khop`, shared with `_ty_so_dung_nguon`); (b) the definition grammar accepts the same optional "là … điểm" as `_TY_SO` | RED then GREEN: `test_divide_segment_coefficient_is_owned_by_the_ratio_equation` (ratio 1/12, residual 11a³√3/12 vs closed form); controls still refuse: an extra unread number (`… và MB = 4` ⇒ `SOURCE_PREMISE_UNREAD`), a ratio that does not solve to the source |
| `hybrid_preview` ⇒ `PREVIEW_DEPENDENCY_INVALID` | `depends` holds fact IDs | **not reproduced**: no `depends` names a non-object. The sub-solid's lateral edges `canh_ben_S_M/N/P` are born at step 8 inside a GROUP event's `objects` list after M, N, P (steps 4–6); `_validate_scene` read births from `event["object"]` only (the frontend `objectsAt` reads `objects`) | births read from `object` and `objects` | RED then GREEN: `test_preview_accepts_edges_born_inside_a_group_event`; the unpatched validator loaded from `HEAD` refuses the same scene (fault injection); control `test_preview_still_refuses_an_edge_born_before_its_endpoint`; existing `dependency` / `dependency_order` tamper tests unchanged and green |

## 3. Requirements of P3 and where they are enforced

| requirement | enforcement | evidence |
|---|---|---|
| no fact absent from the source | every bridged call through `kiem_nguon`; fresh labels only inside a validated certificate; provider responses carrying bridge-only fields refused (`INTERNAL_FIELD_FROM_PROVIDER`) | `test_internal_fields_are_absent_from_the_provider_schema_and_refused_from_a_provider` |
| no important restrictive clause skipped | premise coverage; the plane definition's tail must be exactly the declared cut clause, else unread ⇒ refused | `test_the_cut_clause_is_bound_exactly_or_refused[extra_condition]`, eval `N-unread-condition` (Adapter /3 serves it) |
| volume ratio operands not swapped | Wave 3A ask binding (first named = numerator); an anonymous derived pyramid is not a ratio operand | eval `MR-inverted` served as the reciprocal; `N-anonymous-ratio-operand` refused (`UNKNOWN_LABEL`; Adapter /3 serves it); A3-DEV-07 refused (`'tính tỉ số thể tích' không gọi tên đúng đối tượng`) |
| points / solids with the same label not confused | a label is an identity in `TypedFact`; distinct points sharing a label are refused by the bridge (`BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY`); a certified derived pyramid is not counted as a source solid for a bare "thiết diện" | `test_bridge_refuses_what_typedfact_cannot_express[qualified]` |
| numbers, signs, units, relations unchanged | number ownership per call field (the ratio coefficient owns ONE occurrence it solved); existing unit policy | `test_a_number_the_ratio_equation_does_not_read_still_refuses`, `test_a_coefficient_that_does_not_solve_to_the_call_ratio_is_not_credited` |
| missing operand, compound clause, several goals | existing `FACT_INCOMPLETE`, `REQUEST_NOT_ANSWERED`, SGH-02/04/09/10 (merged) | existing suites green (focused run, §5); not re-measured by new cases |
| no false refusal of valid alternative wording | the definition grammar now matches its binding grammar; derived pyramid named in a ratio list ("hai khối chóp S.ABC và S.MNP") | `test_divide_segment_coefficient_is_owned…`, `test_a_named_derived_pyramid_may_follow_another_solid_in_the_ratio_list` |
| cut names and edges bound exactly | `_cum_cat_canh` (edges in source order, names only "lần lượt tại" all-named), `_kiem_dinh_cat` (lateral edges, named = source name, fresh = collision-free, reused = validated producer on that edge) | `test_the_cut_clause_is_bound_exactly_or_refused[no_clause/order/swapped_names]`, `test_swapped_cut_names_are_refused_without_any_later_question_to_catch_them` |

| a second cut clause contradicting the bound one (review round 1, BLOCKER 1) | after the certificates, EVERY cut clause the source writes must fullmatch a declared `_cum_cat_canh` pattern, else `SOURCE_OBJECT_MISMATCH` (the generic coverage span can no longer read an undeclared cut) | `test_a_second_cut_clause_that_contradicts_the_bound_one_is_refused[3]`, `test_restating_the_same_cut_clause_is_consistent` |
| a negated or contrastive request for the derived pyramid (review rounds 1–3) | the clause leading to the phrase must fullmatch a CLOSED set of positive lead-ins (`_MO_KHOI_TREN_THIET_DIEN`: empty after a connector, a request verb, the ratio / residual openers), AND the whole sentence carries no negation / exclusion word (`_LOAI_TRU_YEU_CAU`, which catches a negation governing a list: "không dựng mặt đáy và khối chóp …", and "… hay không?"), else `NEGATED_CLAUSE` | `test_a_negated_derived_pyramid_request_is_refused[4]`, `test_a_derived_pyramid_without_a_known_positive_lead_in_is_refused[5]`, `test_a_negation_governing_a_list_or_following_the_derived_pyramid_is_refused[3]`, controls `…after_a_positive_lead_in_is_served[4]`, `test_a_ratio_question_without_a_request_verb_is_served` |

Fault injections (scratch, not committed): forcing the tail reader to accept anything makes `no_clause` SERVED; forcing the
cut pattern to accept anything makes the construction-only swapped-names case SERVED; disabling only the global cut-clause
check (coverage left generic) makes the review's contradicting request SERVED with 1/8 — all three checks are load-bearing.

Pre-existing gap noted, not changed: the shared negation lexicon `PHU_DINH` has no request verbs, so "… nhưng không dựng
thiết diện" around OTHER request objects is still read only by the existing question-context rules.

## 4. Not done / limits

- The two-lines relation plane (`MAT_HAI_DUONG`) does not accept a cut clause yet (fail-closed refusal).
- The planner does not add a cut the source does not state (an open cycle is refused even when the plane does cut the
  edge) — conservative by design; a future rule may construct it as a verified consequence.
- Adapter /3 keeps its substring grounding; it is not removed or rewired in this session.
- The derived-pyramid lead-in is a closed list and its sentence may hold no negation word: positive requests worded
  outside it are refused (fail-closed false refusals): "không quên dựng …" (regression-pinned), "Tính tỉ số giữa thể tích
  khối chóp S.MNP và thể tích khối chóp S.ABC.", "Gọi V1, V2 lần lượt là thể tích … Tính V1/V2.", and any sentence that
  also negates something else ("… không cần vẽ đường cao …").
- The global cut-clause rule reads cut clauses of the `_CAT_CANH_CHUNG` shape ("cắt (các cạnh) XY, … (lần lượt tại …)");
  other wordings of a cut are not read as cuts and so cannot certify one either. Prisms whose labels carry a Unicode
  prime are refused before this rule (label grammar).

## 5. Focused verification

Sequential focused pytest over planner / Registry / engine / preview / Adapter /3 / Wave 3A / schema suites (after
review round 3, `verification/focused-pytest-post-review3/`): 1902 passed, 1 xfailed, 1 failed — the failure is `test_version_constants_surface_fingerprints_and_historical_receipt_preservation`
comparing the live measured tree with the frozen candidate (expected until the candidate is re-frozen in G5). Frozen
provider fingerprints (`flat`, `v3`, function declarations, `TypedFact` schema) are asserted unchanged by the existing
fingerprint tests in that run. Raw logs: `verification/`.
