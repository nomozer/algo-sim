# SLM_FINE_TUNING_DECISION.md — Empirical Fine-Tuning Recommendation (`§11`)

> **Campaign:** `specialized-geometry-extraction-slm-optimization` (AXO HYBRID /6)  
> **Model Under Study:** `Qwen3-0.6B-Q4_K_M` (`396,705,472` B, CPU-first, zero parameter growth)  
> **Scope Constraint (`§11` / `§12`):** Zero fine-tuning or distillation executed in `/6`; this document delivers an evidence-based empirical recommendation across Cases A, B, C, and D.

---

## 1. Empirical Error Partition Across Zero-Shot `/6` (`config_c_v6_compact_full`)

### A. On Blind Single-Shot `SLM_NEW_HOLDOUT_48` (`32+ / 16-`, `SLM_NEW_HOLDOUT_EVALUATION.json`)
- **Total positives served:** **`19/32` (`59.38%`)**, up from `13/32` (`40.62%`) in both Deterministic `v145` (`Config A`) and `/5 minimal_ops` (`Config B`, SLM rescue `0/19 -> 6/19`, McNemar `p = 0.03125`, `16/16` negative refusal, `0` Mode-A leaks, `0` Scene3D continuity errors).
- **Schema / Grounding Failures:** `schema_valid_slm_rate = 1.0` (`28/28`), **`slm_rejected_by_validator = 0/19`** on positives. Zero malformed JSONs or validator-blocked hallucinations.
- **Root Partition of the `13` Failed Positives (`all slm_invoked = True, grounding_status = GROUNDED_AND_LOWERED`):**
  1. **Bounded Genuine `Qwen3-0.6B` Semantic Extraction Errors (~6/13 cases — Case B):**
     - `v6h_f1_03_right_prism_right` (`MISSING_DIMENSION`), `v6h_f2_04_rhom_pyr_vol` (`MISSING_DIMENSION`), `v6h_f6_02_face_perp_right_iso` (`MISSING_DIMENSION`), `v6h_f5_03_pp_45_tri_dist` (`ROLE_NOT_IN_QUOTE`), `v6h_f7_02_mid_dist_split` (`UNGROUNDED_VALUE`), `v6h_f8_03_proj_mid_pyr` (`SOURCE_OBJECT_MISMATCH`).
     - In multi-constraint Vietnamese sentences with unfamiliar geometric roles (rhombus angles, face-perpendicular right-isosceles triangles, plane-plane dihedral angles with indirect base edges, or midpoint altitude projections), zero-shot `Qwen3-0.6B` still omits one premise relation or assigns a quantity/role to the wrong clause.
  2. **Deterministic Surface Grammar / `Source Gate` Phrasing Gaps (~7/13 cases — Case C):**
     - `v6h_f3_01_reg_tri_pyr` (`"mọi cạnh bên dài 2a√2"` — `"mọi"` not normalized like `"tất cả các"`), `v6h_f3_03_reg_tet_vol` (`"tứ diện đều MNPQ có tất cả các cạnh bằng 3a"`), `v6h_f1_04_right_prism_equi` (`PREDICATE_NOT_IN_QUOTE` on prism height/base clause phrasing), `v6h_f5_02_pp_60_rect` (`UNSUPPORTED_BASE_SHAPE` downstream base capability), `v6h_f6_03_face_perp_rect` & `v6h_f6_04_face_perp_dist` (`"nằm vuông góc với đáy"` / `"nhận ... làm đáy, đồng thời mặt bên ..."`), `v6h_f8_02_textbook_box` (`", còn DD' thì có độ dài bằng 2a"` -> `CONDITIONAL_CLAUSE` triggered on `"còn ... thì ..."` with quantity instead of `"vuông góc"`).

### B. On Gold-Annotated Diagnostic Splits (`SLM_EXTRACTION_ABLATION.json`)
- **`DEV_CALIBRATION_16` (`10+`):** `Config C_full` achieves `8/10` (`8/9` non-typo; `cal_p08` is an intentional diacritic typo refused safely via `TYPO_REQUIRES_CONFIRMATION`). Only `cal_p04_midpoint_dist` failed due to a remaining phrasing/SLM extraction miss (`Typed Facts exact match = 8/10`, up from `3/10` in `/5`).
- **`HOLDOUT_40` (`HISTORICAL_DIAGNOSTIC`, `28+`):** `Config C_full` achieves `18/28` (`18/26` non-typo vs `26/26` Gold canonical ceiling). All `2` typo items (`slm_h24`, `slm_h26`) failed safely via `TYPO_REQUIRES_CONFIRMATION`. All remaining `8` non-typo misses (`slm_h03, h04, h09, h10, h19, h21, h23, h25`) passed `slm-grounding-validator/2` (`val_rej = 0`) and failed at `Source Gate` (`Typed Facts exact match = 21/28 = 75.0%` vs `15/28 = 53.6%` in `/5`; Predicate Recall `89.91%`, Argument Binding `89.91%`, Quantity Binding `90.62%`).

---

## 2. Explicit Evaluation of Decision Cases A, B, C, and D (`§11`)

| Case | Hypothesis | Verdict Against `/6` Evidence |
|---|---|---|
| **Case A** | Compact extraction improves both accuracy and latency cleanly -> stay zero-shot & tune prompts/rules alone | **PARTIALLY TRUE ONLY:** `/6` doubled blind SLM rescues (`0/19 -> 6/19`) and cut warm uncached `p50` CPU latency by `52%` (`6683.53 -> 3204.27 ms` warm bench; `8494.29 -> 3837.81 ms` blind holdout). However, zero-shot `0.6B` stalls at **`59.38%` (`19/32`)** blind holdout exact rate — below both `>= 65%` local-primary and `>= 85%` Gemini-replacement gates. Pure zero-shot prompt tuning is unlikely to cross `85%`. |
| **Case B** | Errors are dominated by SLM predicate/argument binding limits -> targeted **LoRA / QLoRA** on `0.6B` | **SUPPORTED (Primary Model-Side Bottleneck):** On the `13` blind holdout misses, `Qwen3-0.6B` had `0` schema errors and `0` validator rejections, yet still dropped secondary constraints or mis-scoped clauses on multi-clause prompts (~`6/13` cases), while missing unseen surface phrasings. Targeted LoRA/QLoRA fine-tuning of `Qwen3-0.6B -> slm-compact-clause/1` directly targets this without increasing `0.6B` model size or runtime RAM (`~1.04–1.17 GiB`). |
| **Case C** | Gold Typed Facts itself fails downstream -> prioritize Typed Facts / Source Gate / Planner / Kernel instead of fine-tuning | **CO-PRIMARY BOTTLENECK ON UNSEEN PHRASING:** `SLM_GOLD_INTERVENTION_RESULTS.json` proved `Test C_raw = 19/39` vs `Test C_canon = 35/35` non-typo (`DEV16 + HOLDOUT_40`). Even in `/6`, `~7/13` blind holdout misses involved phrasing forms (`"mọi cạnh bên"`, `"nằm vuông góc"`, `"còn DD' thì có độ dài"`, rectangle dihedral support) where `Source Gate` (`_lien_ket_cau`) / `slm-verified-normalizer` rejected even valid extractions. LoRA alone **cannot** bypass missing downstream `Source Gate` / base-shape coverage. |
| **Case D** | SLM adds negligible value over Deterministic Parser `v145` -> drop SLM | **REJECTED:** `/6` achieved a statistically significant paired gain over Deterministic `v145` on blind single-shot holdout (`19/32` vs `13/32`, `+6` net positives, `0` losses, McNemar `p = 0.03125`) as well as `HOLDOUT_40` (`18/28` vs `9/28`, `+9`, `p = 0.003906`) and `DEV_CALIBRATION_16` (`8/10` vs `0/10`, `+8`, `p = 0.007812`). |

---

## 3. Concrete Next-Stage Recommendation: **Hybrid Case C First, Followed by Case B (LoRA on `slm-compact-clause/1`)**

1. **Step 1 — Close Deterministic Upstream/Downstream Surface Gaps (`Case C`, Zero Training Cost):**
   - Extend span-audited `slm-verified-normalizer/1` + router escalation with the newly discovered blind-holdout phrasings (e.g., `"mọi cạnh bên dài"`, `"tất cả các cạnh bằng"`, `"nằm vuông góc"`, contrastive `"còn <SEG> thì có độ dài"`), and register `Source Gate` support for confirmed base/dihedral patterns (`UNSUPPORTED_BASE_SHAPE` rectangle dihedral in `v6h_f5_02`, regular tetrahedron `"tất cả các cạnh bằng"`). Fix minor `/6` quote edge cases (e.g. `VN05_ALL_LATERAL` regular pyramid `SLM` + `Source Gate` interactions).
   - Keep `Planner /26` backward-chaining (`MG9` auxiliary scaling) and explicit learner typo confirmation separated into their own campaigns.
2. **Step 2 — Targeted QLoRA / LoRA Fine-Tuning of `Qwen3-0.6B-Q4_K_M` (`Case B`, Strictly Disjoint Data):**
   - Train a compact **QLoRA adapter (`r=16, alpha=32`) merged back into `Qwen3-0.6B-Q4_K_M`** strictly mapping `(indexed [c] Vietnamese clauses + E/Q tables) -> slm-compact-clause/1 JSON` (~100 output tokens, keeping runtime footprint `~1.05 GiB`).
   - **Strict Contamination Firewall:** Construct the fine-tuning dataset exclusively from synthetic parametric perturbations + already-public development corpora (`RM72`, `DEV37`, `PROBES39`, `NC`, `DEV_CALIBRATION_16`), keeping `HOLDOUT_40`, `SLM_NEW_HOLDOUT_48`, `H-1`, and `W2/W3` **100% excluded** (creating a fresh post-LoRA holdout before any release verdict).
3. **Do NOT Scale Up Model Size Unless Post-LoRA + Case-C Re-Evaluation Plateaus Below `85%`:** Only after combining Case C lexical/Source-Gate completion with `Qwen3-0.6B` compact LoRA should larger models (`1.5B–1.7B`) be evaluated against 4–6 GiB RAM limits.
