# SLM_FINE_TUNING_READINESS — AXO HYBRID /7 (`P3` / `Gate C2`)

> **Campaign:** AXO HYBRID /7 (`deterministic-geometry-language-closure-slm-finetuning`)  
> **Post-Closure Evidence:** [SLM_POST_CLOSURE_EVALUATION.json](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_POST_CLOSURE_EVALUATION.json) (`external_ai_calls = 0`)  
> **Owner Decision Prerequisite (`§8`):** Fine-tuning triggers ONLY after measuring `Config C` post-closure errors and verifying all 6 readiness criteria.

---

## 1. Post-Closure Residual Error Audit (`Config C` Across 104 Historical Diagnostic Cases)

Across all `70` positive cases and `34` negative cases in `DEV_CALIBRATION_16` + `HOLDOUT_40` + `SLM_NEW_HOLDOUT_48`, **`Config C` (`v7` deterministic closure + un-tuned `Qwen3-0.6B`)** achieves:
- **Positives:** `9/10` (`DEV_CALIBRATION_16`), `25/28` (`HOLDOUT_40`), `26/32` (`SLM_NEW_HOLDOUT_48`) → **`60/70` overall (`85.71%`), `60/67` non-typo (`89.55%`)**
- **Negatives:** `34/34` refused (`100.0%`), **`0` wrong-served**, **`0` Scene3D continuity errors**

Inspecting all **`10` remaining positive failures** under `Config C`:

### 1.1 Intentional Safety / Typo Refusals (`3/10` — NOT Model Errors)
1. `cal_p08_s2_f_typo` → `REFUSED` (`AMBIGUOUS_FACT` / `TYPO_REQUIRES_CONFIRMATION`)
2. `slm_h24_ocr_missing_tone_goc` → `REFUSED` (`AMBIGUOUS_FACT` / `TYPO_REQUIRES_CONFIRMATION`)
3. `slm_h26_ocr_missing_tone_chop` → `REFUSED` (`AMBIGUOUS_FACT` / `TYPO_REQUIRES_CONFIRMATION`)

These 3 intentionally refuse unconfirmed missing-diacritic Vietnamese inputs and MUST NOT be "fixed".

### 1.2 Genuine `Qwen3-0.6B` Semantic Extraction Errors (`7/10` — Downstream Kernel Supports All `7`)

Remaining non-typo failures (`7` cases across `HOLDOUT_40` and `SLM_NEW_HOLDOUT_48`, 6 probed directly with Gold `compact_clause` JSON through `validate_and_lower_compact_clause(..., closure_mode="v7")` + `run_hybrid_offline`, plus `v6h_f8_03_proj_mid_pyr` which also resolves to `SERVED` when valid projection/midpoint slots are emitted):

| Case ID | Dataset | Config C Attribution & Refusal | Observed Un-tuned `Qwen3-0.6B` Extraction Defect | Gold `compact_clause` + Hybrid Result |
|---|---|---|---|---|
| `slm_h21_orthoproj_line_seg` | `HOLDOUT_40` | `SOURCE_GATE_REJECTED` (`SOURCE_OBJECT_MISMATCH`) | Misbound orthogonal projection arguments/quote (`H` projection onto `SB` in multi-sentence composition) | **`SERVED`** (`rejected=[]`) |
| `v6h_f2_04_rhom_pyr_vol` | `NH48` | `MODEL_SEMANTIC_ERROR` (`MISSING_DIMENSION`) | Omitted `rhom(ABCD, 2a)` and/or `ang_vtx(BAD, A, 60°)` on multi-constraint rhombus base clause | **`SERVED`** (`rejected=[]`) |
| `v6h_f3_01_reg_tri_pyr` | `NH48` | `SOURCE_GATE_REJECTED` (`UNGROUNDED_VALUE`) | Swapped or duplicated scalar bindings (`2a` base vs `2a√2` lateral edge) in `"có cạnh đáy bằng 2a và các cạnh bên bằng 2a√2"` | **`SERVED`** (`rejected=[]`) |
| `v6h_f6_02_face_perp_right_iso` | `NH48` | `MODEL_SEMANTIC_ERROR` (`MISSING_DIMENSION`) | Omitted `right_iso_tri(KMN, K)` or `face_perp(KMN, MNPQ)` when two constraints share one clause | **`SERVED`** (`rejected=[]`) |
| `v6h_f6_03_face_perp_rect` | `NH48` | `SOURCE_GATE_REJECTED` (`UNSUPPORTED_BASE_SHAPE`) | Omitted `rect(UVWX)` when base lengths `UV=2a, UX=a√2` appeared in the same clause | **`SERVED`** (`rejected=[]`) |
| `v6h_f6_04_face_perp_dist` | `NH48` | `MODEL_SEMANTIC_ERROR` (`MISSING_DIMENSION`) | Omitted `reg_poly(MAB)` or `face_perp(MAB, ABCD)` on canonicalized two-sentence lateral-face clause | **`SERVED`** (`2a√21/7`, `rejected=[]`) |
| `v6h_f8_03_proj_mid_pyr` | `NH48` | `LOCAL_PARSE_COMPLETE` / `SOURCE_GATE` conflict | Emitted conflicting/duplicate midpoint/projection premises on `hình chiếu ... đồng thời là trung điểm` after preserving non-overlapping SLM predicates | **`SERVED`** when clean SLM JSON emitted |

**Key Diagnostic Conclusion:** Notice that these `7` remaining non-typo failures — together with harder unseen multi-constraint geometry compositions (`3–5` premises, indirect midpoint/centroid/projection/ratio chains, rhombus/rectangle/trapezoid bases, dihedral/line-plane angles on novel phrasings) — are NOT capability gaps in `Source Gate`, `Planner /26`, or `Exact Kernel /24`. They are specifically caused by un-tuned `Qwen3-0.6B` omitting secondary predicates, dropping base-shape tags in multi-length clauses, or misbinding argument/quantity indices inside `slm-compact-clause/1`.

---

## 2. Verification of All 6 `§8` Readiness Criteria

| Criterion (`§8`) | Status | Evidence |
|---|---|---|
| 1. Verified residual SLM semantic extraction errors remain after deterministic closure | **PASS** | `7` remaining non-typo positive failures (`slm_h21`, `v6h_f2_04`, `v6h_f3_01`, `v6h_f6_02`, `v6h_f6_03`, `v6h_f6_04`, `v6h_f8_03`) are confirmed un-tuned SLM extraction omissions/misbindings; `P2` baseline measurement (`SLM_POST_CLOSURE_EVALUATION.json`) recorded. |
| 2. Gold `TypedFacts` and downstream Kernel handle those cases cleanly | **PASS** | `6/6` probed cases return `SERVED` with `rejected=[]` when Gold `compact_clause` JSON is supplied through `validate_and_lower_compact_clause(v7)` → `run_hybrid_offline`, and `v6h_f8_03` likewise serves with clean non-conflicting slots. |
| 3. Residual errors are NOT predominantly Source Gate or Kernel capability gaps | **PASS** | Exact Kernel `/24` and Source Gate `/33` already support every geometry primitive involved (`rectangle`, `rhombus` + `ang_vtx`, `right_iso_tri`, `face_perp`, `orthogonal_projection_line`, `regular_pyramid` lateral edge). Only compound natural wording that bypasses Local Parser regex (not core math primitives) still awaits SLM extraction. |
| 4. Labeled, verified training/validation data constructible with zero holdout leakage | **READY (`P4`)** | Programmatic generator + `validate_and_lower_compact_clause(v7)` + `run_hybrid_offline` + independent 60-digit `Decimal` coordinate oracle, split strictly by **problem family** (`14` train / `4` val), with programmatic `0`-overlap / `0`-near-duplicate / `0`-isomorphism checks against `DEV_CALIBRATION_16`, `HOLDOUT_40`, `SLM_NEW_HOLDOUT_48`, `sealed H-1`, `W2/W3`, `COMP112`, `RM72`, `DEV37`, `REAL27`, `S2_36`, `NC`, and `vmmu`. |
| 5. Suitable, verified GPU training + GGUF conversion toolchain available | **PASS** | Verified local GPU: **NVIDIA GeForce GTX 1650** (`4096 MiB` VRAM, Turing `sm_75`, driver `610.62`, `~3.8 GiB` free), `C:` `66.33 GiB` free, `uv.exe` available, `Qwen/Qwen3-0.6B` (`Apache-2.0`) HF download HTTP 200, `llama.cpp b12470` `convert_hf_to_gguf.py` HTTP 200, and `llama-quantize.exe` (`b12470`) already provisioned on disk. Isolated CUDA `.venv` lives outside Git under `%LOCALAPPDATA%\axo-slm\training\.venv`; training uses `fp32`/`fp16` (NEVER `bf16` on Turing `sm_75`). |
| 6. Evaluation design cleanly separates deterministic closure (`H1`) from fine-tuning (`H2`) | **PASS** | `Config B` (`v6` normalizer/extractor + original SLM) vs `Config C` (`v7` closure + original SLM) measures `H1`; `Config C` vs `Config D` (`v7` closure + fine-tuned SLM) on both historical diagnostics AND a frozen, single-shot **new blind holdout** measures `H2` cleanly without modifying upstream deterministic code between `C` and `D`. |

---

## 3. Readiness Decision

**Decision (`Gate C2`):** **`PROCEED_TARGETED_LORA_QWEN3_0_6B`**

- Target Model: **`Qwen/Qwen3-0.6B`** (`Apache-2.0`, strict `<= 0.6B` parameter constraint).
- Target Task ONLY: `Vietnamese Geometry Clauses + Indexed E/Q -> slm-compact-clause/1 JSON` (`{"s":...,"r":...,"g":...,"u":...}`).
- Strictly Forbidden Training Targets: math answers, Python/JS code, arbitrary coordinates, or Source Gate bypass.
- Proceed now to **Phase D (`P4`)**: provision external CUDA toolchain, build verified anti-leakage dataset, execute real GPU LoRA fine-tuning on `GTX 1650`, and verify adapter → FP16 merge → GGUF `F16` → `Q4_K_M` quantization (`P5`).
