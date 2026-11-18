# SLM Fine-Tuning Implementation (`/7`)

## 1. Objective & Data Scope Integrity
- **Task:** Supervised Fine-Tuning (`SFT`) with Low-Rank Adaptation (`LoRA`) on `Qwen/Qwen3-0.6B` (`revision: c1899de289a04d12100db370d81485cdf75e47ca`) strictly for `slm-compact-clause/1` structured slot extraction.
- **Anti-Contamination Rule:** Training used solely synthetic verified `train.jsonl` (`342` samples) and checkpoint selection used solely disjoint `val.jsonl` (`92` samples). Zero prior holdouts (`DEV_CALIBRATION_16`, `HOLDOUT_40`, `SLM_NEW_HOLDOUT_48`, blind `SLM_V7_HOLDOUT_112`, sealed `H-1`, locked `W2/W3`) were touched during training or selection.

## 2. Prompt-Completion Tokenization & Loss Masking Alignment
- Chat prompt built using `tokenizer.apply_chat_template(messages[:2], tokenize=False, add_generation_prompt=True, enable_thinking=False)`, matching production `llama-server.exe --jinja --reasoning off` bit-for-bit (`<|im_start|>assistant\n<think>\n\n</think>\n\n`).
- Target string = compact canonical JSON + `<|im_end|>` (`prefix_mismatch = 0` across all `342` train + `92` val items).
- Completion-only cross-entropy loss (`labels = -100` on all prompt tokens) computed cleanly by slicing transformer hidden states to unmasked completion positions before `lm_head`, avoiding full-sequence `[B, T, 151936]` logit tensor blow-up on 4 GiB VRAM.

## 3. Hardware & Precision Engineering (`NVIDIA GeForce GTX 1650`, `TU117`, `4095 MiB`)
- `TU117` (`sm_75`) lacks `bf16` and `FP16` Tensor Cores (`pure_fp32` profiled at `3.47 s/step` vs `12.62 s/step` in `pure_fp16` on identical sequence length).
- Weights kept in `torch.float32`, `gradient_checkpointing_enable(use_reentrant=False)`, `pm.train()`, `use_cache=False`, `batch_size=1`, `grad_accum=4`, `AdamW(lr=0.0002)` with linear warmup + cosine decay (`seed=42`).
- **Measured peak CUDA memory allocated:** `3621.59 MiB` (< `4095 MiB`, zero WDDM swap).
- **Trainable LoRA parameters:** `10,092,544` / `606,142,464` (`1.6650%`, `r=16, alpha=32`, all attention + MLP projections).

## 4. Epoch Trajectory & Disjoint Validation Selection (`val.jsonl` only)

| Epoch | Train Loss | Val Loss | Val Pos Exact (`SERVED` + Decimal-60) | Val Neg Safe Refusal | Wrong-Served |
|---:|---:|---:|---:|---:|---:|
| 0 | n/a | 0.3528 | *(base val_loss anchor)* | - | - |
| 1 | 0.0470 | 0.0369 | 35/68 (51.47%) | 24/24 | 0 |
| 2 | 0.0040 | 0.0269 | 61/68 (89.71%) | 24/24 | 0 |
| 3 | 0.0001 | 0.0286 | 61/68 (89.71%) | 24/24 | 0 |

- **Selected Checkpoint:** Epoch `2` (criteria: `wrong_served == 0`, maximum `val` exact accuracy, tie-broken by minimum `val_loss`).
- **Best Adapter Storage (outside Git):** `C:\Users\Bunny\AppData\Local\axo-slm\adapters\qwen3-0.6b-axo-v7-lora\best`
- **Total Wall Time:** `5516.7 s`
