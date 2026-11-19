# AXO HYBRID /9 — C60 Root-Cause Decomposition & 4-Arm Gold Intervention (`SLM_V9_BOTTLENECK_REPORT.md`)

- **Corpus:** `C60_BLIND_NLU` (`60` cases = `42` verified positives [`30` single, `12` multi-request], `13` negative/refusal, `5` non-scalar UI/construct)
- **Arm A (`AxoV7 + v2` current product route):** **`13/42` (`30.95%`)**, `wrong_served = 0`
- **Arm B (`Gold TypedFactNext /2` on raw source text -> Source Gate -> Planner -> Kernel):** **`15/42` (`35.71%`)**
- **Arm B (`Gold TypedFactNext /2` on meaning-preserving canonicalized text -> Source Gate -> Planner -> Kernel):** **`33/42` (`78.57%`)**
- **Arm C (`Gold slm-compact-clause/1` on raw text -> validator -> Source Gate -> Kernel):** **`5/42` (`11.90%`)**
- **Arm C (`Gold slm-compact-clause/1` on canonicalized text -> validator -> Source Gate -> Kernel):** **`18/42` (`42.86%`)**

## 1. Eight Mandatory §6 Questions Answered

1. **How many C60 positives solve correctly if extraction is perfect?** `15/42` on verbatim raw text (`Source Gate` unchanged) and **`33/42`** once paired with safe meaning-preserving Vietnamese surface normalization.
2. **How many still fail even with Gold Typed Facts?** `9` (`['D05', 'D13', 'L10', 'L12', 'L23', 'L28', 'L31', 'L36', 'L38']`): `D05`/`L12` ask distance to finite `đoạn thẳng` (unsupported downstream; distinct oracle from infinite line), `L10` asks `SC²` (schema lacks squared-length goal), `L28` asks triangle `area(SBC)` (check downstream Kernel capability), `L38` uses conditional `'Nếu ... thì ...'` policy block, and `D13`/`L31`/`L36` are stateless standalone context follow-ups missing solid declaration.
3. **Missing goal/schema contract cases (`TYPED_FACT_SCHEMA_LIMITATION`):** `['D09', 'L10', 'L19', 'L21', 'L22']` (in `compact_clause/1`, unnamed `@id` centroid/face-center/foot goals cannot be expressed directly without normalizer closure or schema extension).
4. **Multi-goal limitation cases (`MULTI_GOAL_CONTRACT_LIMITATION`):** `['D12', 'L23', 'L27', 'L28', 'L30']` — GBNF previously capped `g` at `<= 2` items (`goallistreq ::= goalitem ("," goalitem)?`), physically preventing `D12`, `L23`, `L27`, `L30` (3-goal items) from ever emitting all goals!
5. **Cases solvable purely by surface wording normalization:** `['D02', 'D03', 'D06', 'D09', 'D11', 'D12', 'L02', 'L03', 'L05', 'L07', 'L13', 'L19', 'L20', 'L21', 'L22', 'L25', 'L29', 'L30']`.
6. **Cases encountering Source Gate closed grammar gaps:** `['D02', 'D03', 'D06', 'D11', 'L12', 'L13', 'L21', 'L22', 'L25', 'L30', 'L38']`.
7. **Cases outside downstream geometry capability (`DOWNSTREAM_CAPABILITY_LIMITATION`):** `['D05', 'L12', 'L28']`.
8. **Cases where `Qwen3-0.6B-AxoV7` genuinely extracted wrong / incomplete / ungrounded:** `['D02', 'D03', 'D09', 'D11', 'D12', 'L02', 'L03', 'L05', 'L07', 'L19', 'L20', 'L21', 'L22', 'L23', 'L24', 'L25', 'L27', 'L29']`.

## 2. Multi-Label Root-Cause Counts (on 42 Verified Positives)

| Root Cause Label | Count |
|---|---:|
| `PARSER_COVERAGE_GAP` | 22 |
| `SOURCE_GATE_GRAMMAR_GAP` | 11 |
| `NORMALIZER_LANGUAGE_GAP` | 10 |
| `MODEL_SEMANTIC_ERROR` | 10 |
| `MODEL_ENTITY_BINDING_ERROR` | 6 |
| `SOURCE_GROUNDING_ERROR` | 6 |
| `TYPED_FACT_SCHEMA_LIMITATION` | 5 |
| `MULTI_GOAL_CONTRACT_LIMITATION` | 5 |
| `DOWNSTREAM_CAPABILITY_LIMITATION` | 3 |
| `MATHEMATICAL_AMBIGUITY` | 3 |
| `MODEL_GOAL_EXTRACTION_ERROR` | 2 |

## 3. Case-by-Case Summary Table (All Unserved Positives + Non-Scalar)

| Case | Req | Arm A (`/7`) | Arm B Raw | Arm B Canon | Arm C Canon | Labels | Exact Reason |
|---|---:|---|---|---|---|---|---|
| `D02` | 1 | `REFUSED:AMBIGUOUS_VALUE_QUOTE` | `False:UNGROUNDED_VALUE` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, NORMALIZER_LANGUAGE_GAP, SOURCE_GATE_GRAMMAR_GAP, MODEL_SEMANTIC_ERROR` | AMBIGUOUS_VALUE_QUOTE |
| `D03` | 1 | `REFUSED:UNGROUNDED_VALUE` | `False:OBJECT_NOT_IN_QUOTE` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, NORMALIZER_LANGUAGE_GAP, SOURCE_GATE_GRAMMAR_GAP, MODEL_SEMANTIC_ERROR` | UNGROUNDED_VALUE |
| `D05` | 1 | `REFUSED:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'right_tri', 'reason': 'OUT_OF_RANGE_ENTITY_LABEL:ABD'}]` | `DOWNSTREAM_CAPABILITY_LIMITATION` | Asks distance to finite đoạn thẳng (not infinite đường thẳng); Registry/Kernel lacks finite point-segment distance. |
| `D06` | 1 | `REFUSED:NOT_ASKED_IN_SOURCE` | `False:NOT_ASKED_IN_SOURCE` | `True:None` | `True:None` | `SOURCE_GATE_GRAMMAR_GAP, NORMALIZER_LANGUAGE_GAP, PARSER_COVERAGE_GAP` | NOT_ASKED_IN_SOURCE |
| `D09` | 1 | `REFUSED:UNGROUNDED_VALUE` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `False:COMPACT_SCHEMA_LIMITATION_UNRESOLVED` | `PARSER_COVERAGE_GAP, TYPED_FACT_SCHEMA_LIMITATION, MODEL_ENTITY_BINDING_ERROR, SOURCE_GROUNDING_ERROR` | UNGROUNDED_VALUE |
| `D11` | 2 | `REFUSED:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, NORMALIZER_LANGUAGE_GAP, SOURCE_GATE_GRAMMAR_GAP, MODEL_SEMANTIC_ERROR` | SOURCE_OBJECT_MISMATCH |
| `D12` | 3 | `REFUSED:UNGROUNDED_VALUE` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'len', 'reason': "UNGROUNDED_SEGMENT_PAIR:AA'"}]` | `PARSER_COVERAGE_GAP, MULTI_GOAL_CONTRACT_LIMITATION, MODEL_ENTITY_BINDING_ERROR, SOURCE_GROUNDING_ERROR` | UNGROUNDED_VALUE |
| `D13` | 1 | `REFUSED:gate_out_of_scope` | `False:NO_GOLD_PAYLOAD` | `False:NO_GOLD_PAYLOAD` | `False:COMPACT_NOT_REPRESENTABLE` | `MATHEMATICAL_AMBIGUITY` | Stateless single-turn input lacks referenced prior scene/solid ('vừa dựng', 'giao điểm ấy'). |
| `L02` | 1 | `REFUSED:AMBIGUOUS_FACT` | `False:SOURCE_PREMISE_UNREAD` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, MODEL_GOAL_EXTRACTION_ERROR` | AMBIGUOUS_FACT |
| `L03` | 1 | `REFUSED:UNGROUNDED_VALUE` | `False:CONDITIONAL_CLAUSE` | `True:None` | `True:None` | `MODEL_ENTITY_BINDING_ERROR, SOURCE_GROUNDING_ERROR` | UNGROUNDED_VALUE |
| `L05` | 1 | `REFUSED:AMBIGUOUS_FACT` | `False:OBJECT_NOT_IN_QUOTE` | `True:None` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'len', 'reason': "UNGROUNDED_SEGMENT_PAIR:AA'"}]` | `PARSER_COVERAGE_GAP, MODEL_ENTITY_BINDING_ERROR, SOURCE_GROUNDING_ERROR` | AMBIGUOUS_FACT |
| `L07` | 1 | `REFUSED:AMBIGUOUS_FACT` | `False:OBJECT_NOT_IN_QUOTE` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, MODEL_GOAL_EXTRACTION_ERROR` | AMBIGUOUS_FACT |
| `L08` (NS) | 2 | `REFUSED:UNGROUNDED_VALUE` | `REFUSED` | `REFUSED` | `REFUSED` | `OUT_OF_SCOPE` | Requests drawing angle + free-form narrative explanation. |
| `L10` | 1 | `REFUSED:INCONSISTENT_FACTS` | `False:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `False:COMPACT_SCHEMA_LIMITATION_UNRESOLVED` | `TYPED_FACT_SCHEMA_LIMITATION, PARSER_COVERAGE_GAP` | Asks SC² directly; TypedFactNext /2 and Registry /33 expose length(SC), not squared length. |
| `L12` | 1 | `REFUSED:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `DOWNSTREAM_CAPABILITY_LIMITATION, SOURCE_GATE_GRAMMAR_GAP` | Asks distance to finite đoạn thẳng (not infinite đường thẳng); Registry/Kernel lacks finite point-segment distance. |
| `L13` | 1 | `REFUSED:NOT_ASKED_IN_SOURCE` | `False:NOT_ASKED_IN_SOURCE` | `True:None` | `True:None` | `SOURCE_GATE_GRAMMAR_GAP, NORMALIZER_LANGUAGE_GAP, PARSER_COVERAGE_GAP` | NOT_ASKED_IN_SOURCE |
| `L17` (NS) | 1 | `REFUSED:MISSING_DIMENSION` | `REFUSED` | `REFUSED` | `REFUSED` | `PARSER_COVERAGE_GAP, MODEL_GOAL_EXTRACTION_ERROR, TYPED_FACT_SCHEMA_LIMITATION` | construct_intersection_line is supported in TypedFactNext /2 & Exact Kernel, not in compact_clause/1. |
| `L18` (NS) | 1 | `REFUSED:MISSING_DIMENSION` | `REFUSED` | `REFUSED` | `REFUSED` | `PARSER_COVERAGE_GAP, MODEL_GOAL_EXTRACTION_ERROR, TYPED_FACT_SCHEMA_LIMITATION` | construct_intersection_line is supported in TypedFactNext /2 & Exact Kernel, not in compact_clause/1. |
| `L19` | 1 | `REFUSED:INCONSISTENT_FACTS` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `False:COMPACT_NOT_REPRESENTABLE` | `PARSER_COVERAGE_GAP, TYPED_FACT_SCHEMA_LIMITATION, MODEL_SEMANTIC_ERROR` | INCONSISTENT_FACTS |
| `L20` | 1 | `REFUSED:UNGROUNDED_VALUE` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'len', 'reason': "UNGROUNDED_SEGMENT_PAIR:AA'"}]` | `PARSER_COVERAGE_GAP, MODEL_ENTITY_BINDING_ERROR, SOURCE_GROUNDING_ERROR` | UNGROUNDED_VALUE |
| `L21` | 1 | `REFUSED:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, TYPED_FACT_SCHEMA_LIMITATION, NORMALIZER_LANGUAGE_GAP, SOURCE_GATE_GRAMMAR_GAP, MODEL_SEMANTIC_ERROR` | SOURCE_OBJECT_MISMATCH |
| `L22` | 1 | `REFUSED:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'right_tri', 'reason': 'OUT_OF_RANGE_ENTITY_LABEL:BAC'}]` | `PARSER_COVERAGE_GAP, TYPED_FACT_SCHEMA_LIMITATION, NORMALIZER_LANGUAGE_GAP, SOURCE_GATE_GRAMMAR_GAP, MODEL_SEMANTIC_ERROR` | SOURCE_OBJECT_MISMATCH |
| `L23` | 3 | `REFUSED:INCONSISTENT_FACTS` | `False:BRIDGE_UNSUPPORTED_MEASUREMENT` | `False:BRIDGE_UNSUPPORTED_MEASUREMENT` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'len', 'reason': 'GOAL_CLAUSE_USED_AS_PREMISE:clause_1'}, {'op': 'len', 'reason': 'GOAL_CLAUSE_USED_AS_PREMISE:clause_1'}]` | `PARSER_COVERAGE_GAP, MULTI_GOAL_CONTRACT_LIMITATION, MODEL_SEMANTIC_ERROR` | INCONSISTENT_FACTS |
| `L24` | 2 | `REFUSED:SOURCE_PREMISE_UNREAD` | `True:None` | `True:None` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'goal:ang_pp', 'reason': 'INVALID_ANGLE_GOAL_TARGET'}]` | `PARSER_COVERAGE_GAP, MODEL_SEMANTIC_ERROR` | SOURCE_PREMISE_UNREAD |
| `L25` | 2 | `REFUSED:SOURCE_OBJECT_MISMATCH` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, NORMALIZER_LANGUAGE_GAP, SOURCE_GATE_GRAMMAR_GAP, MODEL_SEMANTIC_ERROR` | SOURCE_OBJECT_MISMATCH |
| `L27` | 3 | `REFUSED:REQUEST_NOT_ANSWERED` | `True:None` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, MULTI_GOAL_CONTRACT_LIMITATION, MODEL_SEMANTIC_ERROR` | REQUEST_NOT_ANSWERED |
| `L28` | 2 | `REFUSED:BRIDGE_UNSUPPORTED_MEASUREMENT` | `False:BRIDGE_UNSUPPORTED_MEASUREMENT` | `False:BRIDGE_UNSUPPORTED_MEASUREMENT` | `False:BRIDGE_UNSUPPORTED_MEASUREMENT` | `DOWNSTREAM_CAPABILITY_LIMITATION, MULTI_GOAL_CONTRACT_LIMITATION, PARSER_COVERAGE_GAP` | Multi-goal includes triangle area(SBC); Registry/Kernel returns BRIDGE_UNSUPPORTED_MEASUREMENT. |
| `L29` | 2 | `REFUSED:UNGROUNDED_VALUE` | `False:SOURCE_OBJECT_MISMATCH` | `True:None` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'len', 'reason': "UNGROUNDED_SEGMENT_PAIR:AA'"}]` | `PARSER_COVERAGE_GAP, MODEL_ENTITY_BINDING_ERROR, SOURCE_GROUNDING_ERROR` | UNGROUNDED_VALUE |
| `L30` | 3 | `REFUSED:REQUEST_NOT_ANSWERED` | `False:NOT_ASKED_IN_SOURCE` | `True:None` | `True:None` | `PARSER_COVERAGE_GAP, MULTI_GOAL_CONTRACT_LIMITATION, NORMALIZER_LANGUAGE_GAP, SOURCE_GATE_GRAMMAR_GAP` | REQUEST_NOT_ANSWERED |
| `L31` | 1 | `REFUSED:gate_out_of_scope` | `False:NO_GOLD_PAYLOAD` | `False:NO_GOLD_PAYLOAD` | `False:COMPACT_NOT_REPRESENTABLE` | `MATHEMATICAL_AMBIGUITY` | Stateless single-turn input lacks referenced prior scene/solid ('vừa dựng', 'giao điểm ấy'). |
| `L32` (NS) | 2 | `REFUSED:gate_out_of_scope` | `REFUSED` | `REFUSED` | `REFUSED` | `OUT_OF_SCOPE` | UI styling/camera command rather than new geometry problem. |
| `L35` (NS) | 1 | `REFUSED:gate_out_of_scope` | `REFUSED` | `REFUSED` | `REFUSED` | `OUT_OF_SCOPE` | UI styling/camera command rather than new geometry problem. |
| `L36` | 2 | `REFUSED:gate_out_of_scope` | `False:NO_GOLD_PAYLOAD` | `False:NO_GOLD_PAYLOAD` | `False:COMPACT_NOT_REPRESENTABLE` | `MATHEMATICAL_AMBIGUITY` | Stateless single-turn input lacks referenced prior scene/solid ('vừa dựng', 'giao điểm ấy'). |
| `L38` | 1 | `REFUSED:AMBIGUOUS_FACT` | `False:CONDITIONAL_CLAUSE` | `False:CONDITIONAL_CLAUSE` | `False:LOWER_FAIL:UNGROUNDED_VALUE:[{'op': 'reg_poly', 'reason': 'UNGROUNDED_POINT:B'}]` | `SOURCE_GATE_GRAMMAR_GAP, NORMALIZER_LANGUAGE_GAP` | Uses 'Nếu ... thì ...' conditional form; safety policy treats 'nếu' clauses as hypothetical/non-assertive unless rewritten affirmatively. |
