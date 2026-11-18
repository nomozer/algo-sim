# AXO HYBRID /8 — Independent Dataset Protocol & Unseen Evaluation (`INDEPENDENT_DATASET_PROTOCOL.md`)

> **Status (`INDEPENDENT_EXTERNAL_CORPUS`):** **`BLOCKED_DATA_ACCESS`** (no fresh 100–150 external real student/teacher pilot corpus is available under workspace/offline constraints; AI synthesis of a substitute cohort is prohibited and omitted — `INDEPENDENT_HOLDOUT_MANIFEST.json` / `INDEPENDENT_HOLDOUT_EVALUATION.json` are **not created**).  
> **Permissible Zero-Leakage Unseen Evaluation (`PERMISSIBLE_UNSEEN_CORPUS`):** Executed once single-shot (`single_shot = true`, `external_ai_calls = 0`, `ALLOW_LIVE_AI = "0"`) on **`77` non-sealed repository items** never used in `/5`, `/6`, or `/7` SLM development, training, or hyperparameter tuning.  
> **Evaluator:** `axo-math-evaluator/2` ([`slm_math_evaluator_v2.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/slm_math_evaluator_v2.py)) · **Frozen Product Commit:** `6310113f2202bc3a4919406b26fad08cb09b38c9` (`measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `123` files)  
> **Machine Evidence:** [`PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json) (`sha256_lf = 147f3ff53ec4e32b00971cce70645be89a3034326b54d666e5ce9e7fb88fd693`) · [`PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json)

---

## 1. Access Boundary & Anti-Leakage Verification (`VERIFIED` + `BLOCKED_DATA_ACCESS`)

1. **Blocked External Acquisition (`INDEPENDENT_EXTERNAL_CORPUS = BLOCKED_DATA_ACCESS`):** Collecting 100–150 brand-new external student/teacher solid-geometry problems with human-verified ground truth requires external school/platform data acquisition that is absent in this offline repository workspace. Per AXO HYBRID /8 rules, agent-generated synthetic lookalikes cannot be labeled as an external human cohort.
2. **Sealed / Locked Boundaries Respected:** `sealed_H1`, `locked_W2_W3`, and `SLM_V7_HOLDOUT_112` were **not** opened or reused as the `/8` unseen test.
3. **Permissible Zero-Leakage Corpus (`77` items total):** Assembled cleanly in [`PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness/PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json) from two repository sources strictly excluded from all `/5`, `/6`, and `/7` SLM training/validation/calibration splits:
   - **`C60_BLIND_NLU` (`60` items):** Blind subagent-authored (zero repo access, 2026-10-17) natural-language geometry prompts covering diverse school/conversational phrasing (`A`–`F` groups: `42` `VERIFIED_POSITIVE` = `30` single-request + `12` multi-request; `13` refusal/negatives; `5` non-scalar UI/construction turns).
   - **`EXTERNAL17_REAL_TRANSCRIPTIONS` (`17` items):** Real exam/handwritten transcriptions (`A3_VMMU_EXAM_SCAN_MIT` + `B1_HANDWRITTEN_PROBLEM_STATEMENT`: `12` `VERIFIED_POSITIVE` = `11` single-request + `1` multi-request; `5` `OOS_OR_DIAGRAM_DEPENDENT`).
4. **Anti-Leakage Audit Against `/7` Training/Validation (`434` rows) & Prior `/5–/7` Holdouts (`200` rows):**
   - `exact_text_overlaps = 0`
   - `max_4gram_jaccard_vs_v7_train_val = 0.1505` (`< 0.25`, `zero_leakage_vs_train_val_lt_0_25 = true`)
   - `max_4gram_jaccard_vs_prior_slm_holdouts = 0.4615` (`< 0.55`, `zero_leakage_verified_all_lt_0_55 = true`)

---

## 2. Single-Shot Evaluation Results Across Configs A, B, C, D (`VERIFIED`)

All four pipeline configurations ran single-shot (`evaluate_slm_v8_unseen_corpora.py`, `external_ai_calls = 0`, `threads = 6`, `cache_prompt = True`, `use_cache = False` per prompt):

| Metric | Config A (`det_v145`) | Config B (`/6 + Orig Q4_K_M`) | Config C (`/7 + Orig Q4_K_M`) | Config D (`/7 + AxoV7 Q4_K_M`) |
|---|---:|---:|---:|---:|
| **Overall Positives (`54`)** | `24/54` (`44.44%`) | `25/54` (`46.30%`) | `25/54` (`46.30%`) | `25/54` (`46.30%`) |
| Overall Wilson 95% CI | `[32.00%, 57.62%]` | `[33.69%, 59.39%]` | `[33.69%, 59.39%]` | `[33.69%, 59.39%]` |
| Single-Request Positives (`41`) | `21/41` (`51.22%`) | `22/41` (`53.66%`) | `22/41` (`53.66%`) | `22/41` (`53.66%`) |
| Multi-Request Strict All (`13`) | `3/13` (`23.08%`) | `3/13` (`23.08%`) | `3/13` (`23.08%`) | `3/13` (`23.08%`) |
| **`C60_BLIND_NLU` Positives (`42`)** | `12/42` (`28.57%`) | `13/42` (`30.95%`) | `13/42` (`30.95%`) | **`13/42` (`30.95%`)** |
| `C60` Wilson 95% CI | `[17.17%, 43.57%]` | `[19.07%, 46.03%]` | `[19.07%, 46.03%]` | `[19.07%, 46.03%]` |
| `C60` Single / Multi Strict | `10/30` · `2/12` | `11/30` · `2/12` | `11/30` · `2/12` | `11/30` · `2/12` |
| **`EXTERNAL17` Positives (`12`)** | `12/12` (`100.0%`) | `12/12` (`100.0%`) | `12/12` (`100.0%`) | **`12/12` (`100.0%`)** |
| `EXTERNAL17` Wilson 95% CI | `[75.75%, 100.0%]` | `[75.75%, 100.0%]` | `[75.75%, 100.0%]` | `[75.75%, 100.0%]` |
| **Safe Refusals (`18` Neg / OOS)** | **`18/18` (`100.0%`)** | **`18/18` (`100.0%`)** | **`18/18` (`100.0%`)** | **`18/18` (`100.0%`)** |
| **Wrong-Served (Pos + Neg/OOS)** | **`0`** (`0` / `0`) | **`0`** (`0` / `0`) | **`0`** (`0` / `0`) | **`0`** (`0` / `0`) |
| False Refusals on Positives | `30` | `29` | `29` | `29` |

### Paired Statistical Comparisons (`n = 54` Verified Positives)

| Comparison | Gained (`b01`) | Lost (`b10`) | Rescued / Changed IDs | Exact McNemar `p` | Cohen's `h` |
|---|---:|---:|---|---:|---:|
| `Config B -> Config C` (`/6 -> /7` deterministic closure on base SLM) | `0` | `0` | none | `1.0` | `0.0` |
| **`Config C -> Config D` (`/7` AxoV7 fine-tuning)** | **`0`** | **`0`** | none | **`1.0`** | **`0.0`** |
| `Config A -> Config D` (total local AI pipeline gain) | `1` | `0` | `c60_L14` (`cos²=25/169`) | `1.0` | `0.0372` |

*(Contrast with `/7` in-distribution holdout `SLM_V7_HOLDOUT_112`: `Config D` achieved `74/80 = 92.50%` under `axo-math-evaluator/2`, with `C -> D` gaining `+16` cases, `p = 3.1e-05`, while on unseen free-form `C60_BLIND_NLU` `AxoV7` yielded `0` net end-to-end gain over `Config C` and only `+1` total over deterministic `Config A`.)*

---

## 3. Group Breakdown, Stage Separation & Layer Extraction F1 (`VERIFIED`)

### By Corpus Group (`Config A` -> `Config D`)

| Group | Verified Positives | `Config A` | `Config B` / `C` / `D` | Safe Refusals (`Neg/OOS`) |
|---|---:|---:|---:|---:|
| `A` (`C60` standard-ish paraphrases) | `10` | `4/10` (`40.0%`) | `4/10` (`40.0%`) | `0/0` |
| `B` (`C60` paraphrased premises/angles) | `10` | `4/10` (`40.0%`) | **`5/10` (`50.0%`)** (`+c60_L14`) | `1/1` (`100%`) |
| `C` (`C60` alternate constructions) | `7` | `2/7` (`28.57%`) | `2/7` (`28.57%`) | `0/0` |
| `D` (`C60` multi-request problems) | `11` | `2/11` (`18.18%`) | `2/11` (`18.18%`) | `0/0` |
| `E` (`C60` follow-up/UI turns) | `3` | `0/3` (`0.0%`) | `0/3` (`0.0%`) | `3/3` (`100%`) |
| `F` (`C60` adversarial/conditional negatives) | `1` | `0/1` (`0.0%`) | `0/1` (`0.0%`) | `9/9` (`100%`) |
| `EXTERNAL17 (LICENSE_UNVERIFIED)` | `9` | `9/9` (`100.0%`) | `9/9` (`100.0%`) | `1/1` (`100%`) |
| `EXTERNAL17 (MIT)` | `3` | `3/3` (`100.0%`) | `3/3` (`100.0%`) | `4/4` (`100%`) |

### Stage Separation & `C60` Layer Extraction Metrics (`Config A -> B -> C -> D`)

| Indicator | Config A | Config B | Config C | Config D (`AxoV7`) |
|---|---:|---:|---:|---:|
| Parser Complete Across All `77` | `34` | `34` | `34` | `34` |
| SLM Invocations / Rate | `0` (`0.0%`) | `36` (`46.75%`) | `36` (`46.75%`) | `36` (`46.75%`) |
| SLM End-to-End Positive Rescues | `0` | `1` (`c60_L14`) | `1` (`c60_L14`) | `1` (`c60_L14`) |
| Source-Grounding Valid Count | `34` | `53` | `53` | `49` |
| Invented / Rejected Premise Refusals (`Source Gate`) | `0` | `7` | `6` | **`12`** |
| `C60` Entity Exact Match (Gold `60`) | `21/60` | `21/60` | `21/60` | `21/60` |
| `C60` Typed Facts Exact Match (Gold `60`) | `12/60` | `12/60` | `12/60` | `12/60` |
| `C60` Predicate F1 (P / R / F1) | `0.7586 / 0.3713 / 0.4986` | `0.7254 / 0.5907 / 0.6512` | `0.7306 / 0.5949 / 0.6558` | **`0.7526 / 0.6034 / 0.6698`** |
| `C60` Argument Binding F1 (P / R / F1) | `0.8119 / 0.3581 / 0.4970` | `0.5031 / 0.3581 / 0.4184` | `0.5190 / 0.3581 / 0.4238` | `0.5093 / 0.3581 / 0.4205` |
| `C60` Quantity Binding F1 (P / R / F1) | `0.8491 / 0.3750 / 0.5202` | `0.8491 / 0.3750 / 0.5202` | `0.8491 / 0.3750 / 0.5202` | `0.8491 / 0.3750 / 0.5202` |

---

## 4. Root-Cause Diagnosis of the OOD Generalization Drop (`92.50% -> 30.95%` on `C60`)

Why did `Config D` reach `74/80 (92.50%)` on `SLM_V7_HOLDOUT_112` yet stall at `13/42 (30.95%)` on `C60_BLIND_NLU` (while historical `Gold TypedFacts` itself only served `10/60` under older `v125` contracts)? Inspecting all **`29` missed `C60` positives** in `Config D` reveals five distinct mechanisms (`grounding_status` + `refusal_code`):

1. **Ground-Truth Numerical Token & `Source Gate` Binding Mismatches (`7` `UNGROUNDED_VALUE` / `AMBIGUOUS_VALUE_QUOTE` + `6` `SOURCE_OBJECT_MISMATCH`):**
   - `C60` uses natural unitless numbers (`"cạnh 2"`, `"AA' = 12"`, `"AB = 3"`) and lowercase/shorthand phrasings (`c60_D02`, `c60_D03`, `c60_D09`, `c60_L03`, `c60_L20`, `c60_L29`). Even when `AxoV7` emits a candidate clause (`GROUNDED_AND_LOWERED` = `13` cases, `REJECTED_UNGROUNDED_TOKEN` = `5`), quote spans or argument role bindings fail `Source Gate` checks (`SOURCE_OBJECT_MISMATCH = 6`, `UNGROUNDED_VALUE = 6`, `AMBIGUOUS_VALUE_QUOTE = 1`, `SOURCE_PREMISE_UNREAD = 1`).
2. **Genuine OOD Geometry Grammar Outside `/7` Training (`3` `INCONSISTENT_FACTS` + `2` `NOT_ASKED_IN_SOURCE` + `1` `BRIDGE_UNSUPPORTED_MEASUREMENT`):**
   - Trirectangular tetrahedron `"Tứ diện OABC có OA, OB, OC đôi một vuông góc..."` (`c60_L19`, `c60_L23`), parallelogram with obtuse angle `"góc BAD = 135°"` (`c60_L12`), right trapezoid (`c60_D05`), direct `"Tính cos² của góc giữa..."` (`c60_D06`, `c60_L13`), and `"Tính góc nhị diện..."` / `"ratio"` bridge forms (`c60_L28`) fall outside `/7`'s LoRA training distribution. Note that `invented_premise_refusals` doubled from `6` (`Config C`) to `12` (`Config D`), showing the fine-tuned adapter attempted to project unfamiliar phrasings onto memorized `/7` clause schemas — which `Source Gate` cleanly caught (`0` wrong-served).
3. **Casual / Conditional Interrogative Forms (`4` `AMBIGUOUS_FACT`):**
   - Colloquial questions without canonical verbs (`c60_L02`, `c60_L05` `"Điểm A cách mặt phẳng (A'BD) bao nhiêu..."`, `c60_L07`, `c60_L38` `"Nếu cạnh ... bằng 3 thì..."`) returned `REJECTED_NO_GROUNDED_GOAL` or `SLM_REPORTED_UNRESOLVED`.
4. **Strict Multi-Request Execution Gaps (`2` `REQUEST_NOT_ANSWERED`):**
   - `c60_L27` and `c60_L30` ask two questions in one text where partial / ungrounded goal extraction left one requested sub-question unanswered under `strict_all` scoring.
5. **Stateless Context-Dependent UI Prompts (`3` `gate_out_of_scope`):**
   - `c60_D13` (`"Giờ tính độ dài đoạn AH vừa dựng giúp mình."`), `c60_L31`, and `c60_L36` reference hidden prior turns or viewer visibility controls, which stateless single-turn `/api/analyze` correctly rejects out of scope.

---

## 5. Key Takeaways for Release Readiness

- **Safety held at `100%` under severe OOD shift:** Across `77` unseen items (`54` positives + `18` negatives/OOS + `5` UI/construct), `Config D` committed **`0` wrong-served answers** and achieved **`18/18` safe refusals**, confirming the `Source Gate` + `Exact Kernel /24` safety net works as designed even when the 0.6B SLM misses OOD syntax.
- **External vs. synthetic benchmark sensitivity is extreme:** On standard Vietnamese exam transcriptions (`EXTERNAL17`), the stack achieves **`12/12` (`100%`)** with `0` wrong-served and `5/5` safe OOS refusals; on unconstrained conversational paraphrases (`C60_BLIND_NLU`), `AxoV7` remains **`13/42` (`30.95%`)** with `0` gain over un-finetuned `Config C` — proving that `/7`'s `92.50%` blind-holdout score reflects **in-distribution template competence**, not arbitrary conversational NLU generalization.
