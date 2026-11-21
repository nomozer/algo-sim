# DETERMINISTIC_LANGUAGE_CLOSURE — AXO HYBRID /7 (`Gate C1`)

> **Campaign:** AXO HYBRID /7 (`deterministic-geometry-language-closure-slm-finetuning`)  
> **Scope:** Upstream deterministic layer ONLY (`slm-verified-normalizer/2`, `local-slm-extractor/3`, `slm-grounding-validator/3`, `local-slm-runtime/3`).  
> **Source Gate / Kernel / Production Cache Policy:** `registry.py`, `kiem_nguon`, `_lien_ket_cau`, `planner.py`, `engine.py`, `adapter4_route.py`, `CACHE_VERSION = 145` untouched.  
> **Measured Evidence:** [SLM_POST_CLOSURE_EVALUATION.json](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_POST_CLOSURE_EVALUATION.json) (`external_ai_calls = 0`, `--threads 6`).

---

## 1. Summary of Deterministic Upgrades (`P1`)

All `/7` deterministic changes are gated behind explicit version switches (`normalizer_version="v1"|"v2"`, `closure_mode="v6"|"v7"`) so the frozen AXO HYBRID /6 configuration (`Config B`, `normalizer_version="v1"`, `closure_mode="v6"`) reproduces `/6` scores identically side-by-side in `P2`/`P6` controlled ablations.

### 1.1 Ten-Field Span-Audited Provenance Contract (`slm-verified-normalizer/2`)
Every rewrite emitted by `normalize_for_slm_grounding(..., normalizer_version="v2")` in [slm_verified_normalizer.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/ai/slm_verified_normalizer.py) records all 10 required fields with monotonic original character position mapping (`_update_pos_map`) back to `norm0` and solid-aware sentence boundary detection (`_sentence_bounds` ignoring `.` inside solid notations such as `S.ABCD` or `GHK.G'H'K'`):

| Field | Description |
|---|---|
| `original_text` | Exact slice matched before rewrite (mapped back cleanly via `pos_map`) |
| `original_span` | `[orig_start, orig_end]` in normalized baseline text |
| `original_clause_id` | 0-based original sentence/clause index |
| `normalized_text` | Canonicalized output text |
| `transformation_rule_id` | Canonical rule identifier (`VN01_*` .. `VN05_*`) |
| `original_entity_refs` | Geometric vertices/segments/solids in the rewritten span |
| `scope` | Explicit semantic scope (`LATERAL_EDGES`, `ALL_SOLID_EDGES`, `BASE_EDGES`, `BASE_POLYGON`, `FACE_PLANE`, `CONTRASTIVE_FACT`, `PROJECTION_COMPOUND`, `PRISM_HEIGHT`, `CONVERSATIONAL_OPENER`, `SOLID_DECLARATION`, `LOCAL_CLAUSE`, `LOCAL_ENTITY`, `CLAUSE_CONNECTOR`, `TYPOGRAPHY`, `GOAL_MARKER`) |
| `polarity` | `"AFFIRMATIVE"` (rewrites skipped with `REJECTED_CONSERVATIVE` under conditional or negative polarity) |
| `semantic_equivalence_evidence` | Explicit justification string for semantic preservation |
| `validation_status` | `"VALIDATED_MEANING_PRESERVING"` (or `"REJECTED_CONSERVATIVE"` when blocked) |

---

## 2. Phrase Groups A–E & Extractor/Quote Closure

| Group | Root Gap Verified in `/6` | Exact `/7` Upstream Fix | Negative / Safety Guard |
|---|---|---|---|
| **A — Universal Quantifiers** | `v6h_f3_01` (`"mọi cạnh bên dài 2a√2"`, `"mặt đáy có cạnh bằng 2a"`), `v6h_f3_03` (`"Xét tứ diện đều MNPQ có tất cả các cạnh bằng 3a"`) | `VN05_ALL_LATERAL`, `VN03_XET_TU_DIEN`, `VN05_TETRA_ALL_EDGES`, `VN04_REG_PYR_BASE` (requiring explicit `đáy`), plus deterministic `tetrahedron_expansion` in `validate_and_lower_compact_clause` (`closure_mode="v7"`) | Requires explicit universal quantifier (`tất cả`, `mọi`, `mỗi`, `các`, or explicit `đều`). Never rewrites singular `"cạnh bên dài 2a"`, partial `"một số các cạnh bên"`, `"chóp tam giác đều ... có cạnh bên"`, conditionals, or negations. |
| **B — Perpendicularity & Face Clauses** | `v6h_f6_04` (`", đồng thời mặt bên MAB là tam giác đều nằm vuông góc với mặt đáy (ABCD)"`), `v6h_f7_02` (`"KM vuông góc với mặt đáy (MNP)"`), `slm_h25` / `slm_h04` (`perp_lp` GBNF matching bare `"vuông"` / `"đứng"`) | `VN05_SPLIT_MAT_BEN_CLAUSE`, `VN05_NAM_VUONG_GOC_FACE`, updated `VN05_NAM_TRONG_FACE_PERP` (supporting optional parenthesized base `(ABCD)`), `VN05_VUONG_GOC_MAT_DAY_PAREN`; `build_compact_grammar_for_context(..., closure_mode="v7")` restricts `perp_lp` to explicit `"vuông góc" \| "⊥" \| "đường cao" \| "trục"` cues | Never matches 2-vertex segments/lines (`SA`, `AB`) for face perpendicularity; never rewrites negated `"không nằm vuông góc"` or `"không vuông góc với mặt đáy"`; preserves `v6` GBNF/quotes strictly under `closure_mode="v6"`. |
| **C — Contrastive Clauses** | `v6h_f8_02` (`", còn DD' thì có độ dài bằng 2a"`) triggered `CONDITIONAL_CLAUSE` | Extended `VN05_CON_THI` (`v2`) across `bằng`/`dài`/`có độ dài bằng`/`=` with full-sentence `_sentence_bounds` check | Strictly aborted whenever `nếu`, `khi`, `giả sử`, or sentence/clause negation (`không`, `chẳng`, `chưa`) appears anywhere in the real sentence. |
| **D — Base & Prism Forms** | `slm_h09` (`"Thưa thầy, bài cho..."`), `slm_h10` (`ABC.A'B'C'` missed `\b` after `'`), `v6h_f1_04` (`GHK.G'H'K', đáy GHK... và chiều cao GG'=2a`), `v6h_f5_02_pp_60_rect` diagnosis | `VN02_THUA_THAY_OPENER`, `_SOLID_TOKEN_RE` apostrophe fix in `VN04_NHAN_IMPLICIT_BASE`, `VN03_SOLID_COMMA_DAY`, `VN05_CHIEU_CAO_PRISM` (verified against prism base–top vertex pairs). Proved `v6h_f5_02_pp_60_rect` is ALREADY supported in Kernel (`engine.py:1459` `rectangle_chart`) | `VN05_CHIEU_CAO_PRISM` fires only when `lăng trụ đứng/đều` is in the same sentence AND segment connects corresponding base/top vertices. |
| **E — Quotes, Prefixes & Parser Reconciliation** | `/6` `_CONVERSATIONAL_PREFIX_RE` stripped segment `"EM "` (`re.IGNORECASE`) on `v6h_f5_03`; `select_clean_quote` matched scattered single letters (`slm_h03`, `slm_h23`, `v6h_f6_04`); `cal_p04`, `slm_h03`, `slm_h10`, `v6h_f1_04`, `v6h_f7_01`, `v6h_f8_03` failed downstream due to SLM misquotes/conflicts even when normalized `Local Parser /2` was `LOCAL_PARSE_COMPLETE` | Case-safe `_CONVERSATIONAL_PREFIX_RE`; boundary-enforced `_cand_has_contiguous` + `required_cues` in `select_clean_quote` & `_select_source_gate_quote`; `VN05_PROJ_MIDPOINT`; normalized `LOCAL_PARSE_COMPLETE` premise reconciliation in `validate_and_lower_compact_clause(..., closure_mode="v7")` (guarded by `not rejected_ops and not raw_slm_json.get("u")` + 0 unconsumed quantities + no conditional/negation) | Always preserves verbatim substring containment in `norm_text` and runs full `Source Gate` + `Planner /26` + `Exact Kernel /24`; `closure_mode="v6"` retains `/6` splitting & quote selection; ambiguous typos stay fail-closed (`TYPO_REQUIRES_CONFIRMATION`). |

---

## 3. Unit & Adversarial Verification

Executed cleanly offline (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`) across:
- [test_slm_language_closure.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_slm_language_closure.py) (`9` tests)
- [test_slm_compact_extraction.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_slm_compact_extraction.py) (`5` tests)
- [test_local_slm_understanding.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_local_slm_understanding.py) (`5` tests)

**Result:** **`19 passed, 0 failed in 47.62s`** (1 warning from upstream `starlette.testclient`).

---

## 4. `P2` Measured Impact (`Config B -> Config C`, Hypothesis `H1`)

Measured in [SLM_POST_CLOSURE_EVALUATION.json](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_POST_CLOSURE_EVALUATION.json) (`external_ai_calls = 0`, `threads = 6`, historical diagnostic datasets — NOT claimed as `/7` independent blind holdout):

| Dataset | Config A (`det_v145`) | Config B (`v6` Original SLM) | Config C (`v7` Closure Original SLM) | `B -> C` Net Gain (`H1`) | Lost Cases | McNemar Exact `p` / Cohen `h` | Wrong-Served / Continuity Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`DEV_CALIBRATION_16`** (`10` pos, `6` neg) | `0/10` (`0.0%`), `6/6` neg | **`8/10`** (`80.0%`, `8/9` non-typo), `6/6` neg *(matches `/6`)* | **`9/10`** (`90.0%`, **`9/9` = 100% non-typo**), `6/6` neg | **`+1`** (`cal_p04_midpoint_dist`) | **`0`** | `p = 1.0`, `h = 0.2838` | `0` / `0` |
| **`HOLDOUT_40`** (`28` pos, `12` neg) | `9/28` (`32.14%`), `12/12` neg | **`18/28`** (`64.29%`, `18/26` non-typo), `12/12` neg *(matches `/6`)* | **`25/28`** (`89.29%`, **`25/26` = 96.15% non-typo**), `12/12` neg | **`+7`** (`h03`, `h04`, `h09`, `h10`, `h19`, `h23`, `h25`) | **`0`** | **`p = 0.015625`**, `h = 0.6141` | `0` / `0` |
| **`SLM_NEW_HOLDOUT_48`** (`32` pos, `16` neg) | `13/32` (`40.62%`), `16/16` neg | **`19/32`** (`59.38%`), `16/16` neg *(matches `/6`)* | **`26/32`** (`81.25%`), `16/16` neg | **`+7`** (`f1_03`, `f1_04`, `f3_03`, `f5_02`, `f5_03`, `f7_02`, `f8_02`) | **`0`** | **`p = 0.015625`**, `h = 0.4865` | `0` / `0` |

Gold-split `TypedFacts` exact match & slot accuracy (`DEV_CALIBRATION_16` / `HOLDOUT_40`, `Config B -> Config C`):
- `DEV_CALIBRATION_16`: `typed_facts_exact_match` `8/10 (80.0%) -> 9/10 (90.0%)`; `predicate_recall` `29/35 (82.86%) -> 32/35 (91.43%)`; `entity_precision` `42/42 -> 44/44 (100%)`.
- `HOLDOUT_40`: `typed_facts_exact_match` `21/28 (75.0%) -> 24/28 (85.71%)`; `predicate_recall` `98/109 (89.91%) -> 100/109 (91.74%)`; `predicate_precision` `98/102 (96.08%) -> 100/102 (98.04%)`.

`H1` is **STRONGLY CONFIRMED** on the `104` historical diagnostic cases (`45/70 -> 60/70` total positive, `+15` gained, `0` regressed, `34/34` negatives safely refused, `0` wrong-served) without changing model weights, scaling parameters beyond `0.6B`, or relaxing `Source Gate` — and without masking the remaining multi-constraint SLM extraction gaps evaluated in [SLM_FINE_TUNING_READINESS.md](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_FINE_TUNING_READINESS.md).
