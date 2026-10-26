# NL → TypedFacts V2 → Envelope — audit and gap matrix

Run `hybrid-v2-nl-certificates-e2e`, 2026-10-27, branch `research/hybrid-v2-nl-certificates-e2e` from `main` `dd557f8f`.
Method: trace which code actually runs, then probe the deterministic stages with wording variants whose gold values come from
closed-form formulas. **Everything below is measured on DEV_AUTHORED data written by the implementing agent**
(`results/dev-authored-gold-stress.json`, `NOT_INDEPENDENT`). Extraction quality of a real model is **NOT_MEASURED** (0 live calls).

## 1. What actually runs

```
Vietnamese text
  → Extraction            LLM only (`ai/typed_fact_next_extraction.TransportExtractor`; no deterministic NL parser exists).
                          Offline: `ReplayExtractor` (recorded) — what `/api/analyze` uses under HYBRID_V2_LOCAL=offline-replay.
  → TypedFacts V2 gate    `extract_typed_fact_next_v2`: schema + source identity + verbatim quotes + role/negation of every
                          premise quote (deterministic).
  → Source Gate           `registry.kiem_nguon` (5 tiers: quote, labels, predicate+reference, number binding, ask grammar).
  → Planner → Engine      exact (ℚ/radical) kernel, independent checks; refuses with a code, never approximates.
  → Envelope              `adapter4_route` → /4; `function_route` presents the certificate (D-10: asked-line naming).
```

Consequence: *understanding* a sentence is the LLM's job and is unmeasured here; what is deterministic — and therefore
measurable offline — is whether the system **serves the right thing and refuses the rest** for a given faithful extraction, and
whether it refuses an unfaithful one.

## 2. Requested probes

| Probe | Result (GOLD arm, gold = faithful extraction) |
|---|---|
| "Tính góc giữa SC và mặt phẳng (ABCD)" — 4 wordings (đường thẳng SC / mặt đáy / tạo bởi / "bao nhiêu?") | all served, exact `cos² = 32/41` for s=4, h=3; renamed labels and other sizes follow the formula |
| same, "… mặt phẳng đáy (ABCD)" (word + labels) | **refused** `NOT_ASKED_IN_SOURCE` — valid wording refused (gap NL-3) |
| "Tính **số đo** góc …" | refused `QUESTION_CONTEXT_UNSUPPORTED` — **by design**: the product states an angle as its exact cos², never the degree measure (`registry._kiem_don_vi_hoi`); not a gap |
| "Tìm khoảng cách từ S đến BD" — tính/tìm, đến/tới, "đường thẳng BD", "điểm S", "bằng bao nhiêu?" | all served, `√17` (d² = h² + s²/2) |
| "Tính d(S, BD)" | refused `SOURCE_OBJECT_MISMATCH` — safe refusal of a notation (gap NL-4) |
| "Cho hình chóp S.ABCD có SA vuông góc với đáy" — 6 premise wordings (⊥ (ABCD), ⊥ đáy, ⊥ mặt đáy (ABCD), "cạnh bên SA ⊥ đáy ABCD", ⊥ mặt phẳng đáy, `⊥`) | all served |
| plane named by several labels `(BCC'B')` — `'`/`′`, label order, "mặt bên BCC'B'", "mp(…)", "(…)" | all served `24/5` |
| "… mặt phẳng chứa mặt bên (BCC'B')" | refused `SOURCE_OBJECT_MISMATCH` (gap NL-5, conservative) |
| two wordings of one assumption | equal values on all variants (side ×8, ⊥ ×6, length ×5, goal ×9) |
| insufficient data (no height / no ⊥) | refused `MISSING_DIMENSION` / `UNDERDETERMINED_POINT` |
| relation to be *proved* / conditional / negated | refused by role (`GOAL_CLAUSE_NOT_PREMISE`, `CONDITIONAL_CLAUSE`, `NEGATED_CLAUSE`) also when an extractor wrongly makes it a premise (STRESS 3/3) |
| contradictory data (SA = 3 and 5; side 4 but AC = 4) | refused `INCONSISTENT_FACTS` (2/2) |
| unknown label in the question | refused `UNDERDETERMINED_POINT` |
| extractor mistakes (target ≠ quote, value ≠ quote ×2, plane ≠ quote) | refused (STRESS 4/4): `SOURCE_OBJECT_MISMATCH`, `UNGROUNDED_VALUE` ×2, `PLANE_NOT_IN_QUOTE` |

## 3. Gap matrix (stage × finding)

| id | stage | finding | class | disposition |
|---|---|---|---|---|
| NL-0 | Extraction | no measurement of any real model on V2; the 44-item locked set of the earlier run is spent (scored live once, `UNSAFE` by the frozen scorer = 1 scorer artifact) | **unmeasured** | needs an independent holdout + a separate Owner GO — protocol + brief written, nothing run |
| NL-1 | Source Gate | `Đáy ABCD là hình vuông, cạnh 4` / `… với cạnh 4` / `… và có cạnh 4` / `… có độ dài cạnh bằng 4` refused `UNGROUNDED_VALUE` | valid wording refused | **FIXED** (`registry._C_DAY` takes the connectors of `_CANH_SAU_DAY`); 8 wordings × 3 sizes served with the formula value; 11 negative-metamorphic cases keep refusing (other edge, disjunction, inequality, "khoảng", "gấp đôi", symbol, second role number, other object) — `test_base_side_wording_variants.py` |
| NL-2 | Source Gate | side in parentheses `(cạnh 4)`; "Hình vuông ABCD cạnh 4 là đáy." | valid wording refused | open, pinned by tests, left refusing |
| NL-3 | Source Gate | `mặt phẳng đáy (ABCD)` in a question | valid wording refused | open, pinned |
| NL-4 | Source Gate | `d(S, BD)` notation in a question | valid wording refused | open, pinned |
| NL-5 | Source Gate | `mặt phẳng chứa mặt bên (BCC'B')` | valid wording refused | open, pinned |
| NL-6 | Presentation | answer named `d(S, H)` (the foot), not the asked `d(S, BD)` | wrong name, right value | **FIXED** (D-10, commit `4eae907d`) |
| NL-7 | all | no incorrect-served case found in any probe (51 gold items, 7 stress payloads) | — | not a proof: DEV data written by the implementer |

NL-2…NL-5 are exposed in the dataset as `note: KNOWN_GAP` items and pinned by `test_known_wording_gaps_stay_visible`; closing
one must change that list on purpose. They were **not** loosened here: the clause grammar was rewritten after several review
rounds precisely because wider reading produced false serves, and a gap whose fix needs a new grammar clause belongs to a wave
with fresh held-out data.

## 4. Numbers (DEV_AUTHORED, 51 items, offline, 0 provider calls)

GOLD arm: `CORRECT_SERVED 38 · INCORRECT_SERVED 0 · CORRECT_REFUSED 9 · INCORRECT_REFUSED 4 · EXTRACTION_FAILURE 0`
(the 4 are NL-2…NL-5). Contradiction items 2/2 refused by the gate. STRESS arm (7 unfaithful payloads): `CORRECT_REFUSED 7`.
These counts say the **harness works and the gate refuses what it should on this data**; they say nothing about how often a
real model emits the faithful payload.
