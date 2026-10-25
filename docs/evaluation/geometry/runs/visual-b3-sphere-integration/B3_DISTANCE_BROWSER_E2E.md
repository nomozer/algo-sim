# B3 distance — browser E2E (offline, authored TypedFacts)

Authorization `GO_LOCAL_F2_POLICY_REVIEW_B3_VERIFICATION_SPHERE_SOURCE_FIX`, 2026-10-25.

**Evidence class: OFFLINE authored `typed-fact-next/2` payloads → real Adapter /4 wrapper → product consumer in real
Chrome.** This does not certify LLM extraction quality. There was no provider call and no holdout.

## Path exercised

`build_fixtures.py` builds the payloads from `test_typed_fact_next_v2_distance_bridge._prism` and runs them through
`run_typed_fact_next_v2_route` + `build_adapter4_response` (the service's offline wrapper). This produces
`fixtures.json`, five `hybrid-route-d-simulation/4` responses. In the browser, `b3-distance-browser-e2e.mjs` feeds each
response to the product consumer `docPhanHoiHybrid`, then `loadEnvelope` / `loadUnsupported`, the way
`check-adapter4-browser.mjs` does. The existing checker could not be reused because it assumes a section in every
served scene.

| Fixture | Request | Oracle d² (closed form from the stated facts, not the engine) |
|---|---|---|
| B3-D1-point-plane-right | A′ to (ABC), right prism 6-8-12 | 144 |
| B3-D2-skew-lines | AA′ and BC | 2304/100 |
| B3-D3-point-plane-oblique | D′ to (DEF), oblique prism, A′ over the midpoint of BC | 576 |
| B3-R1-malformed-target | plane target with two labels | refusal `INVALID_MATH_GOAL` |
| B3-R2-missing-height | height removed | refusal `MISSING_DIMENSION` |

## Checks per served case (desktop 1440, mobile 390)

`consumed`; `witness_rendered` (an answer-tied witness is drawn when provided — a segment from the measured point with
its foot on the measured plane, or `annotation.witness` on the answer); `mode_a_hidden` (analysis closed: no analysis
panel and no measurement label shows the value); `mode_b_once` (after opening analysis the answer appears in exactly
one place, counting analysis panel + inspector + canvas labels); `value_matches_oracle` (displayed value squared equals
the fixture oracle); `engine_binding`; `inspector_no_new_math` (inspector numbers ⊆ problem-text numbers ∪ answer);
`no_internal_name`; `no_overflow`. Refusals: `no_scene`, `reason_shown`, `code_hidden`, `no_answer`.

## Result

**`B3_DISTANCE_BROWSER_PASS` — 10/10 rows** on the final integrated candidate `63faa5af` (0 page errors, 0 forbidden requests). `fixtures.json` regenerates byte-identical with the final backend.

| Fixture | 1440 | 390 | Shown | Witness |
|---|---|---|---|---|
| D1 point–plane, right prism | PASS | PASS | d(A′,(ABC)) = 12 | tied segment AA′ (foot A on (ABC)), drawn |
| D2 skew lines | PASS | PASS | d(AA′,BC) = 24/5 | **none provided** for this answer |
| D3 point–plane, oblique prism | PASS | PASS | d(D′,(DEF)) = 24 | on the answer (foot H on (DEF)), drawn |
| R1 malformed target | PASS | PASS | no scene; learner reason; no code | — |
| R2 missing height | PASS | PASS | no scene; learner reason; no code | — |

Places showing the answer: on opening analysis 1 (panel only); after selecting it, panel + inspector (+ canvas label for D1, D3).

## Discriminating power (fault injection on a copy of the fixtures)

| Fault | Detected by |
|---|---|
| D1 oracle changed to 145 | `value_matches_oracle` FAIL (both viewports) |
| D3 envelope answer changed to 25 | the consumer itself rejects ("đáp số q không khớp đại lượng kq_q của cảnh") → `consumed` FAIL |
| R1 refusal code replaced by learner text | the consumer rejects → `consumed` / `reason_shown` FAIL |

During development the harness crashed on the second fault instead of scoring it. It now records the row as a
failure.

## Findings for the Owner

1. **Witness for skew lines is not provided.** D2 shows the two lines highlighted and the correct 24/5, but the engine
   gives no common perpendicular. No witness is drawn, and the check records "not provided" instead of counting the
   prism's lateral right-angle marks (an earlier, looser version of this check did count them; it was tightened).
2. **The answer appears three times after the learner selects it.** On first opening "Phân tích toán học" it appears
   once. After the learner clicks the answer, the same statement also shows in the inspector and as a canvas label
   (D1, D3; D2 has no canvas label). The Owner's "Mode B shows the answer in exactly one place" is met in the opening
   state, not in the selected state. Whether inspector/label repeats count as "places" is a policy question. F1 only
   requires that the explanation **formula** is not repeated, and it is not.
3. **Four-label planes.** After review I-1 the bridge accepts exactly three plane labels. A face named by four labels
   ("(BCC′B′)") must be targeted with three of them.

Receipt: `verification/b3-browser/receipt.json` (screenshots per case × viewport × Mode A / Mode B-selected).
