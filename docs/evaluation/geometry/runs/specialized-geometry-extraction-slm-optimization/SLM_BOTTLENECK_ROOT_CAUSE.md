# AXO HYBRID /6 — Phase A Root-Cause Isolation & Gold Intervention Analysis

> **Campaign Stage:** Phase A (`Gate B1`)  
> **Baseline Commit Verified:** `463c6b0408e192a19ff1f25a1bff2a6c94e4e75f` (`feat/local-first-geometry-understanding`, untouched `/5` product code)  
> **Machine Evidence Artifact:** [`SLM_GOLD_INTERVENTION_RESULTS.json`](SLM_GOLD_INTERVENTION_RESULTS.json)  
> **Diagnostic Script:** [`backend/scripts/diagnose_slm_v5_bottlenecks.py`](../../../../backend/scripts/diagnose_slm_v5_bottlenecks.py)  
> **Live External AI Calls:** `0` (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`)

---

## 1. Executive Finding: Why `/5` Reason Codes Masked the Real Bottlenecks

Campaign `/5` reported `18` holdout positive failures (`10/28` served vs `9/28` Deterministic `v145`), surface-classified into `5 LOCAL_MODEL_EXTRACTION_ERROR`, `7 SOURCE_GROUNDING_GAP`, and `6 OTHER_REFUSAL`.  
Re-evaluating every case across **all 14 diagnostic layers** plus three controlled counterfactual interventions (**`Test A`** Deterministic `v145`, **`Test B`** `/5` Qwen3-0.6B `minimal_ops`, **`Test C_raw`** Verified Gold `TypedFactNext /2` on verbatim source, and **`Test C_canon`** Verified Gold `TypedFactNext /2` after span-audited non-typo surface canonicalization) **without bypassing `Source Gate` (`registry.kiem_nguon`)** establishes four proven findings:

1. **Zero `Planner /26`, `Registry /33`, or `Exact Kernel /24` mathematical failures on non-typo cases:**
   Once non-typo surface phrasings are mapped through a meaning-preserving, sentence-preserving canonicalizer (leaving diacritic typos un-rewritten), Verified Gold `TypedFactNext /2` achieves **`35/35` (`100.0%`)** downstream `SERVED` with exact oracle answers (`9/9` non-typo `DEV_CALIBRATION_16`, `26/26` non-typo `HOLDOUT_40`). The **only** Gold intervention failures are the **4 intentional Vietnamese diacritic typos** (`cal_p08_s2_f_typo`, `slm_h24_ocr_missing_tone_goc`, `slm_h26_ocr_missing_tone_chop`, `S2-F-S07`).
2. **Closed-grammar sentence poisoning inside `Source Gate` (`registry.py::_lien_ket_cau`) rejects `Test C_raw` even with perfect Gold `TypedFactNext /2`:**
   On raw un-normalized text, `Test C_raw` passes only **`3/10`** on `DEV_CALIBRATION_16` and **`16/28`** on `HOLDOUT_40` (`19/39` overall). Inspecting `registry.py` lines 2083–2133 (`_lien_ket_cau`) proves why: when verifying any role-bearing quantity (`regular_polygon.side`, `rhombus.side`, `height`, or unnamed segment), `kiem_nguon` parses the **entire containing sentence** via `_phan_tich_cau`. Any opaque `"mo"` clause anywhere in that sentence — conversational prefixes (`slm_h07`, `slm_h08`, `slm_h09`, `cal_p10`), OCR spacing inside parentheses `"( ABC )"` (`slm_h23`), universal lateral-edge wording `"tất cả các cạnh bên đều bằng a"` (`cal_p05`, `slm_h06`), inverted base syntax `"nhận ... làm đáy"` (`cal_p03`, `cal_p07`, `slm_h02`, `slm_h10`), `"ABCD là hình vuông"` (`cal_p09`), or standalone `"Biết G là trọng tâm..."` (`slm_h19`) — causes `_lien_ket_cau` to reject the entire sentence. **No SLM schema or prompt alone can pass `Source Gate` on those raw strings without meaning-preserving surface canonicalization.**
3. **Router premature short-circuit (`slm_invoked = False`) hid 2 raw-solvable holdout failures (`slm_h01`, `slm_h03`):**
   - `slm_h01_natural_pyramid_vol`: `Local Parser` returned `LOCAL_PARSE_AMBIGUOUS` even though `"cạnh a"` and `"SA bằng 3a"` remained unread in the sentence; `/5` `route_text_input_local_slm` never invoked the SLM (`Test C_raw = SERVED a³√3/4`).
   - `slm_h03_right_isosceles_dist`: Contrastive `", còn SA thì vuông góc..."` triggered `CONDITIONAL_CLAUSE` in `Source Gate` despite having no `"nếu"` or `"khi"`; SLM was skipped.
4. **Few-shot mode collapse + verbose 267-token output (`minimal_ops`) crippled both accuracy and CPU speed:**
   Across invoked cases (`n=28`), `/5` `minimal_ops` consumed `780–852` prompt tokens (`avg 815.2`) and emitted **`221–297` completion tokens (`avg 267.1`, median `6,972 ms`)**, largely from JSON schema pretty-print indentation and redundant field names (`clause_id`, `solid_type`, `notation`, `a`, `b`, `pt`, `val`, `unit`). Worse, showing two `S.ABC / SA ⊥ (ABC)` few-shot examples caused `Qwen3-0.6B` to copy `regular_polygon` and `SA=a` onto prisms (`cal_p06`, `slm_h04`, `slm_h10`), face-perpendicular pyramids (`cal_p07`, `slm_h14`), centroid altitudes (`slm_h19` `SG -> SA`), dihedral angles (`cal_p09`, `slm_h15`), and right-isosceles bases (`slm_h25`), while `/5` `select_clean_quote` clipped required prefixes on `slm_h21`.

---

## 2. Counterfactual Intervention Summary (`Test A / B / C_raw / C_canon`)

| Split | Total | `Test A` (Det `v145`) | `Test B` (`/5` Qwen3 `minimal_ops`) | `Test C_raw` (Gold on Raw Text) | `Test C_canon` (Gold + Non-Typo Canonicalization) | Non-Typo Downstream Ceiling |
|---|---:|---:|---:|---:|---:|---:|
| `DEV_CALIBRATION_16` Positives | 10 | `0/10` | `2/10` | `3/10` | `9/10` | `9/9` (`cal_p08` is typo) |
| `HOLDOUT_40` (`HISTORICAL_DIAGNOSTIC`) Positives | 28 | `9/28` | `10/28` (`9` Parser + `1` SLM) | `16/28` | `26/28` | `26/26` (`h24`, `h26` are typos) |
| `S2-F-S07` Typo Probe | 1 | `0/1` | `0/1` | `0/1` | `0/1` | Typo preserved un-rewritten (`0/0` non-typo) |
| **Combined Positives (Diagnostic Only)** | **39** | **9/39** | **12/39** | **19/39** | **35/39** | **35/35 (`100%` non-typo)** |
| All Negatives (`DEV_CAL 6` + `HOLDOUT 12`) | 18 | `18/18` refused | `18/18` refused | N/A | N/A | `0` false-served / `0` Mode A leaks |

### Exact `/5` Partition on `HOLDOUT_40` (`HISTORICAL_DIAGNOSTIC`)

- **Parser self-solved (SLM not invoked):** `9/28` (`slm_h11`, `slm_h12`, `slm_h13`, `slm_h16`, `slm_h17`, `slm_h18`, `slm_h20`, `slm_h22`, `slm_h27`)
- **Router prematurely skipped & failed (SLM not invoked):** `2/28` (`slm_h01`, `slm_h03`)
- **SLM runtime actually invoked on Positives:** `17/28`
  - **SLM genuinely rescued:** `1/17` (`slm_h28_split_dist_3a_4a` -> total `10/28`)
  - **SLM invoked & rejected by `/5` Grounding Validator:** `4/17` (`slm_h04`, `slm_h10`, `slm_h14`, `slm_h15`)
  - **SLM invoked, passed Validator, rejected downstream by `Source Gate`:** `12/17` (`slm_h02`, `slm_h05`, `slm_h06`, `slm_h07`, `slm_h08`, `slm_h09`, `slm_h19`, `slm_h21`, `slm_h23`, `slm_h24`, `slm_h25`, `slm_h26`)
  - **Downstream Planner / Exact Kernel rejections when grounded:** `0/17`
- **SLM runtime invoked on Holdout Negatives:** `6/12` (all safely refused; `6/12` refused deterministically by Parser or prompt-injection guard without runtime call)

---

## 3. Structural Relationship Audit: `slm_h28_split_dist_3a_4a` vs `cal_p02_dist_split` (`§8.E5`)

| Attribute | `cal_p02_dist_split` (`DEV_CALIBRATION_16`) | `slm_h28_split_dist_3a_4a` (`HOLDOUT_40`) |
|---|---|---|
| Raw Text | `Xét hình chóp S.ABC. Tam giác ABC đều có cạnh bằng a. Đường thẳng SA vuông góc với mặt phẳng (ABC), đồng thời độ dài đoạn SA bằng 2a. Hãy xác định khoảng cách từ A đến mặt phẳng (SBC).` | `Xét hình chóp S.ABC. Đáy ABC là tam giác đều cạnh 3a. Đường thẳng SA vuông góc với (ABC) và độ dài SA bằng 4a. Hãy tính khoảng cách từ A đến mặt phẳng (SBC).` |
| Topology & Solid | `pyramid(S.ABC)` | `pyramid(S.ABC)` |
| Base & Altitude | `regular_polygon(ABC)`, `SA ⊥ (ABC)` | `regular_polygon(ABC)`, `SA ⊥ (ABC)` |
| Goal | `distance(A, plane(SBC))` | `distance(A, plane(SBC))` |
| Parameters & Oracle | `side = a`, `SA = 2a` -> `2a√57/19` | `side = 3a`, `SA = 4a` -> `12a√273/91` |
| **Audit Conclusion** | **Isomorphic Parameter-Template Clone.** `/5`'s sole `+1` holdout improvement (`slm_h28`) is parameter-substituted template transfer from `cal_p02` (which was itself modeled directly on the `/5` prompt template) and cannot be cited as independent evidence of generalizing to a new geometric family. `SLM_NEW_HOLDOUT_MANIFEST.json` enforces structural/family disjointness against all development cases. | |

---

## 4. Per-Case Root-Cause Matrix (All 27 Failed Positives Across `DEV_CAL + HOLDOUT_40 + S2-F-S07`)

| Case ID | Split | Primary Failure Layer | Secondary Failure Layer | Test C Raw | Test C Canon | SLM-Only Solvable? | Downstream / Norm Needed? | Observed Evidence | Recommended Action | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| `cal_p03_sq_pyramid_angle` | `DEV_CAL` | `SLM_EXTRACTION_ERROR` | `SURFACE_SYNTAX_GAP` (`SOURCE_OBJECT_MISMATCH`) | `REFUSED:SOURCE_OBJECT_MISMATCH` | `SERVED:a³√2/3` | No | Yes | SLM hallucinated `SA=a` instead of `line_plane_angle(SC,(ABCD),45°)`; raw `"nhận ABCD làm..."` also outside `kiem_nguon`. | Closed E/Q slot filling + `VN04_NHAN_POLY_SHAPE`. | HIGH |
| `cal_p04_midpoint_dist` | `DEV_CAL` | `SLM_EXTRACTION_ERROR` | `NONE` | `SERVED:a/2` | `SERVED:a/2` | Yes | Optional | SLM emitted `regular_polygon(S,A,B,C)` and dropped `midpoint` & `right_angle`; Gold raw passes directly. | Closed E/Q slot filling + `"điểm chính giữa"` normalization. | HIGH |
| `cal_p05_regular_pyr_vol` | `DEV_CAL` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:UNGROUNDED_VALUE` | `SERVED:a³√2/12` | No | Yes | `"tất cả các cạnh bên đều bằng a"` opaque in `_lien_ket_cau`. | `VN05_ALL_LATERAL` + isolated value quote. | HIGH |
| `cal_p06_right_prism` | `DEV_CAL` | `SLM_EXTRACTION_ERROR` | `SURFACE_SYNTAX_GAP` (`UNGROUNDED_VALUE`) | `REFUSED:UNGROUNDED_VALUE` | `SERVED:3a³/4` | No | Yes | SLM classified prism as `pyramid`; raw `đồng thời cạnh bên ... có độ dài` opaque in `_lien_ket_cau`. | Explicit `pri` entity type + `VN05_DONG_THOI`. | HIGH |
| `cal_p07_face_perp_base` | `DEV_CAL` | `SLM_EXTRACTION_ERROR` | `SURFACE_SYNTAX_GAP` (`SOURCE_OBJECT_MISMATCH`) | `REFUSED:SOURCE_OBJECT_MISMATCH` | `SERVED:a³√3/6` | No | Yes | SLM hallucinated `SA ⊥ (ABCD), SA=a`; raw `"nhận hình vuông cạnh a làm đáy ABCD"` rejected. | Closed predicates (`face_perp`) + `VN04_NHAN_PYR_IMPLICIT`. | HIGH |
| `cal_p08_s2_f_typo` | `DEV_CAL` | `SOURCE_TYPO_UNSUPPORTED_BY_CLOSED_GATE` | `SOURCE_GATE` | `REFUSED:UNGROUNDED_VALUE` | `REFUSED:UNGROUNDED_VALUE` | No | Conservative Guard | Diacritic typo `"vuôg góc"`; intentionally not auto-rewritten (`§6.C2`). | Flag `TYPO_REQUIRES_CONFIRMATION` and refuse safely. | HIGH |
| `cal_p09_dihedral_dist` | `DEV_CAL` | `SLM_EXTRACTION_ERROR` | `SURFACE_SYNTAX_GAP` (`UNGROUNDED_VALUE`) | `REFUSED:UNGROUNDED_VALUE` | `SERVED:a√3/2` | No | Yes | SLM dropped `plane_plane_angle` & hallucinated `SA=a`; raw `"Cho chóp ... có ABCD là hình vuông"` opaque. | Closed angle code `ang_pp` + `VN03_BARE_CHOP` / `VN04`. | HIGH |
| `cal_p10_conversational` | `DEV_CAL` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:SOURCE_PREMISE_UNREAD` | `SERVED:a³` | No | Yes | `"Nhờ Axo giải giúp bài này:"` makes sentence 0 opaque in `_lien_ket_cau`. | Strip conversational prefix cleanly with span provenance (`VN02`). | HIGH |
| `slm_h01_natural_pyramid_vol` | `HOLDOUT_40` | `ROUTER_PREMATURE_SHORT_CIRCUIT` | `LOCAL_PARSER_COVERAGE` | `SERVED:a³√3/4` | `SERVED:a³√3/4` | Yes | Router fix | Parser returned `LOCAL_PARSE_AMBIGUOUS` despite `"cạnh a"`, `"SA bằng 3a"`; router skipped SLM. | Escalate false `LOCAL_PARSE_AMBIGUOUS` with unread quantities. | HIGH |
| `slm_h02_square_base_alt_order` | `HOLDOUT_40` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:UNGROUNDED_VALUE` | `SERVED:4a³/3` | No | Yes | `"nhận hình vuông ABCD có cạnh 2a làm đáy"` rejected by `_lien_ket_cau`. | `VN04_NHAN_SHAPE_POLY_DAY`. | HIGH |
| `slm_h03_right_isosceles_dist` | `HOLDOUT_40` | `ROUTER_PREMATURE_SHORT_CIRCUIT` | `SURFACE_GRAMMAR_SYNTAX` | `REFUSED:CONDITIONAL_CLAUSE` | `SERVED:a√10/5` | No | Yes | Contrastive `", còn SA thì vuông góc"` triggered `CONDITIONAL_CLAUSE`; router never invoked SLM/normalizer. | Escalate non-conditional `"thì"` + `VN05_CON_THI` + `right_iso_tri` expansion. | HIGH |
| `slm_h04_right_prism_mnp` | `HOLDOUT_40` | `SLM_EXTRACTION_ERROR` | `NONE` | `SERVED:3a³` | `SERVED:3a³` | Yes | No | SLM emitted prism as `pyramid`; Gold raw passes directly. | Deterministic solid kind (`pri`) + closed `E` table. | HIGH |
| `slm_h05_regular_square_pyramid` | `HOLDOUT_40` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:UNGROUNDED_VALUE` | `SERVED:a³√2/6` | No | Yes | `"đáy MNPQ có cạnh bằng a"` rejected unless normalized to `"có cạnh đáy bằng a"`. | `VN04_REG_PYR_BASE` + value-isolated quotes. | HIGH |
| `slm_h06_regular_tri_pyramid_dist` | `HOLDOUT_40` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:UNGROUNDED_VALUE` | `SERVED:a√165/15` | No | Yes | `"có đáy ABC cạnh a và các cạnh bên đều dài 2a"` outside `_phan_tich_cau`; also needs split quote per value (`AMBIGUOUS_VALUE_QUOTE`). | `VN04_REG_PYR_BASE` + `VN05_ALL_LATERAL` + isolated quotes. | HIGH |
| `slm_h07_conversational_student` | `HOLDOUT_40` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:UNGROUNDED_VALUE` | `SERVED:a√3/2` | No | Yes | `"Em đang ôn tập..., nhờ giải giúp bài sau:"` poisons sentence 0 in `_lien_ket_cau`. | `VN02_CONV_PREFIX`. | HIGH |
| `slm_h08_textbook_label_prefix` | `HOLDOUT_40` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:SOURCE_PREMISE_UNREAD` | `SERVED:a³√3/3` | No | Yes | `"Bài tập hình 11:"` + `"Đường cao SA vuông góc với (ABC) với độ dài SA=2a"` outside closed grammar. | `VN02_CONV_PREFIX` + `VN05_DUONG_CAO_SA_VUONG`. | HIGH |
| `slm_h09_polite_rectangle_base` | `HOLDOUT_40` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:SOURCE_PREMISE_UNREAD` | `SERVED:2a³√5/3` | No | Yes | `"Thưa thầy, bài cho..."` + `"Yêu cầu xác định..."` unread by `kiem_nguon`. | `VN02_CONV_PREFIX` + `VN05_YEU_CAU`. | HIGH |
| `slm_h10_colloquial_prism` | `HOLDOUT_40` | `SLM_EXTRACTION_ERROR` | `SURFACE_SYNTAX_GAP` (`OBJECT_NOT_IN_QUOTE`) | `REFUSED:OBJECT_NOT_IN_QUOTE` | `SERVED:a³√3` | No | Yes | SLM emitted `["A","A'","B","B'","C","C'"]` for line; raw `"lăng trụ ... nhận tam giác đều cạnh 2a làm đáy"` rejected. | `VN02/VN04_NHAN_IMPLICIT_TRI` + typed `E` arity. | HIGH |
| `slm_h14_face_perp_base_split` | `HOLDOUT_40` | `SLM_EXTRACTION_ERROR` | `NONE` | `SERVED:4a³√3/3` | `SERVED:4a³√3/3` | Yes | No | SLM hallucinated `SA ⊥ (ABCD)` + `SA=a` instead of `face_perpendicular_base(SAB, ABCD)`. | Closed `face_perp` code + zero `SA` hallucination. | HIGH |
| `slm_h15_plane_plane_angle_30` | `HOLDOUT_40` | `SLM_EXTRACTION_ERROR` | `NONE` | `SERVED:a√3/2` | `SERVED:a√3/2` | Yes | No | SLM omitted `plane_plane_angle((SBC),(ABC),30°)` and invented `SA=a`. | Closed `ang_pp` code + strict `Q` slot. | HIGH |
| `slm_h19_centroid_altitude` | `HOLDOUT_40` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:QUESTION_CONTEXT_UNSUPPORTED` | `SERVED:a³√3/6` | No | Yes | SLM hallucinated `SA` for `SG`, AND raw `"Biết G là trọng tâm... và SG..."` rejected `QUESTION_CONTEXT_UNSUPPORTED`. | Closed `E` ID for `SG` + `VN05_BIET_CENTROID`. | HIGH |
| `slm_h21_orthoproj_line_seg` | `HOLDOUT_40` | `VALID_OP_MISQUOTED_FOR_SOURCE_GATE` | `SLM_PARTIAL_OR_FRAGILE_QUOTE` | `SERVED:a√2/2` | `SERVED:a√2/2` | Yes | Quote Builder | SLM dropped `orthogonal_projection_line` and emitted `distance(A,(SBC))`; Gold raw serves `a√2/2`. | Full clause quote `"Gọi H là hình chiếu..."` + closed `proj`/`len` goal. | HIGH |
| `slm_h23_ocr_extra_spaces` | `HOLDOUT_40` | `SURFACE_SYNTAX_OUTSIDE_SOURCE_GATE_GRAMMAR` | `LOWERING_QUOTE_SELECTION` | `REFUSED:UNGROUNDED_VALUE` | `SERVED:a³√3` | No | Yes | Extra OCR spaces `"( ABC )"`, `"2a ,"` create opaque chunk in `_lien_ket_cau`. | `VN01_PARENS` / `VN01_PUNCT_SPACE`. | HIGH |
| `slm_h24_ocr_missing_tone_goc` | `HOLDOUT_40` | `SOURCE_TYPO_UNSUPPORTED_BY_CLOSED_GATE` | `SOURCE_GATE` | `REFUSED:UNGROUNDED_VALUE` | `REFUSED:UNGROUNDED_VALUE` | No | Conservative Guard | Typo `"vuông goc"` intentionally un-rewritten (`§6.C2`). | Flag `TYPO_REQUIRES_CONFIRMATION`, refuse safely. | HIGH |
| `slm_h25_paraphrase_perp_conj` | `HOLDOUT_40` | `VALID_OP_MISQUOTED_FOR_SOURCE_GATE` | `SLM_PARTIAL_OR_FRAGILE_QUOTE` | `SERVED:a√2` | `SERVED:a√2` | Yes | Quote Builder | SLM emitted `regular_polygon` for `"tam giác vuông cân tại B"`; Gold raw serves `a√2`. | Closed `right_iso_tri` expansion + full base clause quote. | HIGH |
| `slm_h26_ocr_missing_tone_chop` | `HOLDOUT_40` | `SOURCE_TYPO_UNSUPPORTED_BY_CLOSED_GATE` | `SOURCE_GATE` | `REFUSED:PREDICATE_NOT_IN_QUOTE` | `REFUSED:PREDICATE_NOT_IN_QUOTE` | No | Conservative Guard | Typo `"Hình chop"` intentionally un-rewritten (`§6.C2`). | Flag `TYPO_REQUIRES_CONFIRMATION`, refuse safely. | HIGH |
| `S2-F-S07` | `S2_INCOMPLETE` | `SOURCE_TYPO_UNSUPPORTED_BY_CLOSED_GATE` | `SOURCE_GATE` | `REFUSED:UNGROUNDED_VALUE` | `REFUSED:UNGROUNDED_VALUE` | No | Conservative Guard | Typo `"hình chop"` intentionally un-rewritten (`§6.C2`). | Flag `TYPO_REQUIRES_CONFIRMATION`, refuse safely. | HIGH |

---

## 5. Gate B1 Verdict & Engineering Implications for Phases B–D

- **Gate B1 (`Root-Cause Attribution`): `PASS`.**
- **Direct Architectural Consequences for AXO HYBRID /6:**
  1. **Phase B (`compact_clause`):** Eliminate free-form entity/value spelling & few-shot `SA` bias by deterministically constructing indexed Candidate Entity (`E`) & Candidate Quantity (`Q`) tables per problem and constraining `Qwen3-0.6B` with whitespace-free GBNF over closed predicate/goal codes (`<= 70` output tokens vs `/5`'s `267`).
  2. **Phase C (`slm-verified-normalizer/1`):** Apply span-audited, meaning-preserving surface canonicalization strictly *upstream* of `compact_clause` / `Source Gate` inside `local-slm`, NEVER mutating diacritic typos (`§6.C2`), negations, conditionals, or `Planner /26` / `Registry /33` / `Exact Kernel /24`, and preserve full clause quotes required by `kiem_nguon`.
  3. **Phase D (CPU Runtime):** Enable `cache_prompt=True`, persistent loopback HTTP keep-alive connection pooling (fixing `/5`'s Windows transient `WinError 10013` socket exhaustion discovered during diagnostic execution!), right-sized `max_tokens`, and 9-field versioned extraction caching.
