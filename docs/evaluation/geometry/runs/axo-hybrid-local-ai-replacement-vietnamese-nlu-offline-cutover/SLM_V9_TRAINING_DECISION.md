# AXO HYBRID /9 — Phase P3 Selective SLM Fine-Tuning Decision (`AxoV9-Q4_K_M`)

> **Campaign:** `AXO HYBRID /9 — Local AI Replacement, Vietnamese NLU Generalization & Offline Production Cutover`  
> **Phase:** `P3` (Triggered only on verified post-P2 SLM residual misses)  
> **Status:** `PROMOTED_WITH_VERIFIED_0_WRONG_SERVED` (`external_ai_calls = 0`, `sealed_corpora_opened = false`)

---

## 1. Gate Trigger Evidence (Post-P2 `AxoV7 + v9/v3`)

Before P3 training, P1 and P2 separated parser/normalizer gaps from true SLM extraction errors:

| Stage / Model | Closure | `C60_BLIND_NLU` Strict Positives (`42`) | `C60` Wrong-Served (`60`) | Remaining Solvable `C60` SLM Misses | Residual `/7` Holdout SLM Misses (`6`) |
| --- | --- | --- | --- | --- | --- |
| Baseline `AxoV7` (`Arm A`, pre-P2) | `v7 / v2` | `13 / 42` (`30.95%`) | `0` | — | — |
| `Arm B Gold TypedFactNext /2` (canon text) | Kernel oracle | `33 / 42` (`78.57%`) | `0` | — | — |
| Post-P2 `AxoV7` (`C60_POST_P2_V9_RESULTS.json`) | `v9 / v3` | `26 / 42` (`61.90%`: `23` fast-path + `3` SLM) | `0` | `7` (`D09, D11, L19, L21, L24, L27, L30`) | `6` (`v7h_p5_09`, `v7h_p8_01..05`) |

Deterministic P2 closure resolved `10` fast-path cases and lifted `C60` from `13/42` to `26/42` with `0` wrong-served, leaving **`13` verified downstream-solvable SLM misses** (`7` `C60` + `6` `/7` residual holdouts) plus `0/14` multi-goal extraction and `5/12` tetrahedron/prism/rect extraction on disjoint validation families (`SLM_V9_QUANTIZATION_COMPARISON.json`). Therefore P3 fine-tuning was justified by empirical bottleneck evidence.

---

## 2. Disjoint Training Corpus & Anti-Leakage Verification

Source manifest: [`SLM_V9_TRAINING_MANIFEST.json`](./SLM_V9_TRAINING_MANIFEST.json) (stored outside git under `C:\Users\Bunny\AppData\Local\axo-slm\training\datasets_v9\`, generated with `external_ai_calls = 0` and 100% Exact Kernel /24 verification):

- **Training split (`train_v9.jsonl`):** `474` examples (`386` positives / `88` negatives across `19` families), SHA-256 `4432a5c7bb470750df84c5d8eaa1cde9212849e1cd0f354af8954aa05a882342`.
- **Disjoint Validation split (`val_v9.jsonl`):** `126` examples (`94` positives / `32` negatives across `7` held-out validation families: `VL01_FACE_PERP_RECT_ANG_DIST=24`, `VL02_RHOM_MID_SKEW_DIST=24`, `VL03_PRISM_PROJ_AREA=20`, `VL04_MIXED_NEG_ADVERSARIAL=24`, `VL9_MULTI_GOAL_DISJOINT=14`, `VL9_TETRA_PRISM_RECT_DISJOINT=12`, `VL9_NEG_DISJOINT=8`), SHA-256 `86e25ae9561ff878fe2a453ed40d4f80f5721e742935c6e7534170710bdc42e8`.
- **Anti-leakage check vs. `565` unlocked external items** (`C60_BLIND_NLU`, `COMP112`, `DEV37`, `DEV_CALIBRATION_16`, `EXTERNAL17_REAL_TRANSCRIPTIONS`, `HOLDOUT_40`, `NC_NL`, `PROBES39`, `REAL27`, `S2_36`, `SLM_NEW_HOLDOUT_48`, `SLM_V7_HOLDOUT_112`):
  - `exact_normalized_overlaps_external = 0`
  - `structural_skeleton_overlaps_external = 0`
  - `max_4gram_jaccard_external = 0.3611` (`tr07_159~HOLDOUT_40`)
  - `train_val_family_overlaps = 0`
  - `train_val_structural_skeleton_overlaps = 0`
- `sealed_H1` and `locked_W2_W3` were never opened (`sealed_corpora_opened = false`).

---

## 3. LoRA Training, Epoch Selection & Quantization Parity

Training run [`SLM_V9_TRAINING_RUN.json`](./SLM_V9_TRAINING_RUN.json) on `NVIDIA GeForce GTX 1650` (`torch 2.6.0+cu124`, base `Qwen/Qwen3-0.6B` rev `c1899de289a04d12100db370d81485cdf75e47ca`, `10,092,544` trainable LoRA params / `606,142,464` total, `training_wall_time_s = 9804.3`):

| Epoch | `train_loss` | `val_loss` | HF Unconstrained Greedy Pos (`94`) | Neg Safe Refused (`32`) | Wrong-Served | Overall (`126`) |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | — | `0.3277` | `0 / 94` (`0.00%`) | `32 / 32` | `0` | `32 / 126` (`25.40%`) |
| `1` | `0.0429` | `0.0205` | `66 / 94` (`70.21%`) | `32 / 32` | `0` | `98 / 126` (`77.78%`) |
| `2` | `0.0025` | `0.0251` | `57 / 94` (`60.64%`) | `32 / 32` | `0` | `89 / 126` (`70.63%`) |
| **`3` (selected)** | `0.0002` | `0.0203` | **`70 / 94` (`74.47%`)** | **`32 / 32`** | **`0`** | **`102 / 126` (`80.95%`)** |

Constrained `llama-server.exe` + GBNF vs. unconstrained HF FP16 comparison ([`SLM_V9_QUANTIZATION_COMPARISON.json`](./SLM_V9_QUANTIZATION_COMPARISON.json)):

| Variant | Runtime / Decoding | Positives Exact (`94`) | Negatives Safe (`32`) | Wrong-Served | Overall (`126`) | Key Per-Family Gain |
| --- | --- | --- | --- | --- | --- | --- |
| `axov7_q4km_baseline_under_v9_closure` | `Q4_K_M` + GBNF | `70 / 94` (`74.47%`) | `32 / 32` | `0` | `102 / 126` (`80.95%`) | `VL9_MULTI_GOAL_DISJOINT: 0/14`, `VL9_TETRA_PRISM_RECT_DISJOINT: 5/12` |
| `axov9_merged_fp16_hf` | Merged FP16 unconstrained | `70 / 94` (`74.47%`) | `32 / 32` | `0` | `102 / 126` (`80.95%`) | `VL9_MULTI_GOAL_DISJOINT: 14/14`, `VL9_TETRA_PRISM_RECT_DISJOINT: 12/12` |
| **`axov9_q4km_gguf`** | **`Q4_K_M` + `llama-server` GBNF** | **`94 / 94` (`100.00%`)** | **`32 / 32` (`100.00%`)** | **`0`** | **`126 / 126` (`100.00%`)** | **`VL01=24/24`, `VL02=24/24`, `VL03=20/20`, `VL9_MG=14/14`, `VL9_TET=12/12`** |

- Exported GGUF artifact: `C:\Users\Bunny\AppData\Local\axo-slm\models\qwen3-0.6b-axo-v9-q4_k_m\Qwen3-0.6B-AxoV9-Q4_K_M.gguf` (`396,704,736` bytes, SHA-256 `73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35`).
- Finding: GBNF clause-scoped grammar eliminates rare structural drift seen in unconstrained FP16 decoding and achieves `100.00%` exact end-to-end accuracy on `val_v9.jsonl` with `0` wrong-served.

---

## 4. Post-P3 Live Evaluation (`C60_BLIND_NLU` + `/7` Residual Holdouts)

Executed [`evaluate_p2_and_p3_residual_v9.py`](../../../../../backend/scripts/evaluate_p2_and_p3_residual_v9.py) with `--model v9` -> [`C60_POST_P3_V9_RESULTS.json`](./C60_POST_P3_V9_RESULTS.json):

- **`C60_BLIND_NLU` strict exact (`42` positives):** **`32 / 42` (`76.19%`)** (`23` deterministic fast-path + **`9` SLM-grounded**), representing **`32 / 33` (`96.97%`)** of all `C60` cases solvable by `Arm B Gold TypedFactNext /2` (`canon`), and up from `13/42` (`30.95%`) baseline and `26/42` (`61.90%`) post-P2.
- **Wrong-served on `C60` (`60` cases = `42+ / 18-`):** **`0 / 60`**.
- **Newly resolved `C60` SLM cases (`AxoV7 -> AxoV9`):** `+6` (`D09`, `D11`, `L19`, `L21`, `L24`, `L30`).
- **Remaining misses (fail-closed, non-wrong-served):**
  - `C60` solvable miss: `1` (`L27`, refused fail-closed `REQUEST_NOT_ANSWERED`).
  - `/7` residual holdouts (`6` checked): `0 / 6` served (`v7h_p5_09`, `v7h_p8_01..05` refused fail-closed `SOURCE_PREMISE_UNREAD`, `wrong_served = 0`).

---

## 5. Promotion Decision & Frozen Model Preservation

- **Decision:** **`PROMOTE_AXOV9_Q4_K_M_AS_V9_LOCAL_MODEL`** (`promoted = True`), registered in [`local_slm_runtime.py`](../../../../../backend/app/ai/local_slm_runtime.py) as `V9_LOCAL_SLM_MODEL_KEY = "qwen3-0.6b-axo-v9-q4_k_m"`.
- **Frozen /7 & /6 Checksums Verified Unchanged:**
  - `Qwen3-0.6B-AxoV7-Q4_K_M.gguf`: `36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148`
  - `Qwen3-0.6B-Q4_K_M.gguf`: `ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a`
