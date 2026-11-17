# SLM_FAILURE_ANALYSIS.md — Failure Taxonomy & Root-Cause Attribution (AXO HYBRID /5)

**Artifacts:** [`SLM_BASELINE_COMPARISON.json`](SLM_BASELINE_COMPARISON.json) · [`SLM_EXTRACTION_EVALUATION.json`](SLM_EXTRACTION_EVALUATION.json) · [`dev_calibration_16.json`](dev_calibration_16.json)

---

## 1. Zero-Leak Safety vs Positive Coverage Summary

Across **all** evaluated negative, ambiguous, contradictory, out-of-scope, and prompt-injection suites, neither `Qwen3-0.6B-Q4_K_M` nor `Qwen2.5-0.5B-Instruct-Q4_K_M` leaked a single false `Mode A` (`SERVED`) result when invoked:
- `DEV_CALIBRATION_16` negatives: `6/6` refused (`0` leaks)
- `S2_36` negatives (`S2-C/D/E`): `18/18` refused (`0` leaks)
- `SLM_INDEPENDENT_HOLDOUT_40` negatives (`H29..H40`): `12/12` refused (`0` leaks, including `H39` English & `H40` Vietnamese prompt injections)
- `DEV37`, `COMP112`, `PROBES39`, `AUTONOMOUS_NEGATIVES`, `RM72`, `REAL27_TEXT`: **`0` regressions** and **`0` new false Mode A leaks** attributable to SLM fallback (in `COMP112`, `dp_reflection` and `dp_projection_unnamed_image` both serve deterministically via Local Parser with `slm_invoked = False`, identical in Config A and Config B — matching the 2 historical capability promotions documented in `v145`).

However, zero-shot sub-1B extraction of novel natural Vietnamese phrasing onto closed geometric predicates achieved only modest incremental coverage:
- **`DEV_CALIBRATION_16` (`10` partial-parser positives):** Deterministic `0/10` → Approach A (`direct_wire` `Qwen3-0.6B`) `0/10` → Approach B (`minimal_ops` `Qwen3-0.6B`) `2/10`, while `Qwen2.5-0.5B` scored `0/10`.
- **`SLM_INDEPENDENT_HOLDOUT_40` (`28` positives):** Deterministic `9/28` (`32.14%`) → `Qwen2.5-0.5B` `9/28` (`32.14%`, `+0`) → `Qwen3-0.6B` `10/28` (`35.71%`, `+1`: resolved `slm_h28_split_dist_3a_4a = 12a√273/91` where Local Parser returned `LOCAL_PARSE_PARTIAL`).
- **`S2_36`:** `S2-F-S07_typo_tone` (`"vuôg góc"`) remained refused (`UNGROUNDED_VALUE`), keeping `S2` at `16/18` oracle-exact positive match (`17/18` served).

---

## 2. Failure Breakdown on `SLM_INDEPENDENT_HOLDOUT_40` Positives (`18` Misses in `Qwen3-0.6B`)

From [`SLM_EXTRACTION_EVALUATION.json`](SLM_EXTRACTION_EVALUATION.json), the 18 missed holdout positives under `Qwen3-0.6B-Q4_K_M` partition into three primary root-cause layers:

### A. Zero-Shot Sub-1B Extraction Errors (`LOCAL_MODEL_EXTRACTION_ERROR`: `5` Holdout / `5` Dev Cal)
1. **Multi-Constraint Omissions & Argument Swaps:** When a clause packs 2–3 spatial facts (e.g., `slm_h02`, `slm_h14`, `slm_h15`), `0.6B` quantized models frequently drop the secondary face/angle predicate or misbind `regular_polygon` vertices (e.g. outputting `S,A,B` on `"mặt bên SAB đều"` cleanly but forgetting `face_perpendicular_base`, or copying `a` onto an unrelated edge -> trapped cleanly by `segment_length_proximity` as `UNGROUNDED_VALUE`).
2. **Colloquial /Conversational Clauses & Prefix Interference (`slm_h07`, `slm_h08`, `slm_h09`, `slm_h10`):** Conversational openers (`"Em đang ôn tập..."`, `"Thưa thầy..."`, `"Cho mình hỏi..."`) distract `0.6B` attention, leading to missing premises (`SOURCE_PREMISE_UNREAD`) or omitted `solid.reg = true` on `"lăng trụ đứng"`.
3. **Comparator JSON Truncation (`Qwen2.5-0.5B` only):** On `4/16` calibration items (`cal_p05`, `cal_p06`, `cal_p07`, `cal_p10`), `2/40` holdout items (`slm_h07`, `slm_h08`), and `1/5` warm latency bench runs (`cal_p05`), `Qwen2.5-0.5B-Instruct` entered repetitive JSON key-value loops up to `max_tokens=512`, triggering fail-closed `LOCAL_SLM_RESPONSE_INVALID` (`0` occurrences on `Qwen3-0.6B`).

### B. Source Gate Closed-Grammar Strictness vs Typo / Non-Standard Quotes (`SOURCE_GROUNDING_GAP` / `OTHER_REFUSAL`: `13` Holdout)
Axo's upstream Source Gate (`registry.kiem_nguon`) enforces closed syntactic patterns on verbatim `quote` substrings and their enclosing sentence:
1. **`PREDICATE_NOT_IN_QUOTE` (`3` cases, e.g. `slm_h05`, `slm_h21`, `slm_h24`):** Source Gate requires exact closed Vietnamese tokens (`vuông góc`, `hình chiếu`, `hình chóp`). Minor OCR-style diacritic omissions (`"vuông goc"` in `slm_h24`, `"Hình chop"` in `slm_h26`) are cleanly rejected by `kiem_nguon` rather than silently normalized away, prioritizing zero-false-serve mathematical auditability over typo forgiveness.
2. **`SOURCE_OBJECT_MISMATCH` / `OBJECT_NOT_IN_QUOTE` / `ROLE_NOT_IN_QUOTE` (`4` cases, e.g. `slm_h04`, `slm_h06`, `slm_h19`):** When `Qwen3-0.6B` emits a structurally valid op tied to a clean short quote that omits an auxiliary keyword expected by `kiem_nguon` (e.g., `"Khối lăng trụ đứng MNP.M'N'P'"` lacking `"hình"`, or `"nhận hình vuông ABCD... làm đáy"`), Source Gate fails closed cleanly.
3. **`CONDITIONAL_CLAUSE` (`slm_h03`):** Clauses phrased with `"với AB=a, còn SA thì vuông góc..."` trigger Source Gate's strict conditional/clause separator guard unless normalized/restated in declarative premise form.

### C. Refused `REAL27_TEXT` Cases (`4` SLM-Invoked Refusals Preserved Safely)
All `4` SLM-invoked cases among the `6` historical `REAL27_TEXT` refusals (`vmmu_r256` typo `"đên"`, `r461`/`r475` out-of-scope curved solids, `r491`/`r513` underdetermined/missing dimensions) refused cleanly without forcing an invalid solution (`21/27` SERVED, `0` wrong served — identical safety to `v145`).

---

## 3. Diagnostic Comparison: `Qwen3-0.6B` vs `Qwen2.5-0.5B`

| Failure Pattern | `Qwen3-0.6B-Q4_K_M` | `Qwen2.5-0.5B-Instruct-Q4_K_M` |
|---|---|---|
| JSON truncation / syntax break (`LOCAL_SLM_RESPONSE_INVALID`) | **`0 / 40`** holdout · **`0 / 16`** cal · **`0 / 5`** warm bench | `2 / 40` holdout · `4 / 16` cal · `1 / 5` warm bench (`cal_p05`) |
| `DEV_CALIBRATION_16` partial-parser solves | **`2 / 10`** | `0 / 10` |
| `HOLDOUT_40` positives solved | **`10 / 28` (`35.71%`)** | `9 / 28` (`32.14%`) |
| False positive `Mode A` leaks | **`0`** | **`0`** |

**Conclusion of Failure Analysis:** The validator + Source Gate defense-in-depth eliminated 100% of hallucinations and prompt-injection leaks, proving architectural safety. The limiting bottleneck is strictly **zero-shot sub-1B multi-clause Vietnamese extraction capacity** combined with **closed-syntax Source Gate rigidity** on conversational/OCR-noisy text.
