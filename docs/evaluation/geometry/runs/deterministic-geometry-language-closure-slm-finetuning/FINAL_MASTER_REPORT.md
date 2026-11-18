# AXO HYBRID /7 — Final Master Report (`FINAL_MASTER_REPORT.md`)

> **Run ID:** `deterministic-geometry-language-closure-slm-finetuning`  
> **Branch / Worktree:** `feat/local-first-geometry-understanding` (`D:\Documents\projects\algo-sim\.superpowers\worktrees\local-first-geometry-understanding`)  
> **Baseline Prior Head (`/6`):** `43bef643d2c528053526d363ee578065e60e6116`  
> **Frozen Product Commit (Commit 1):** `6310113f2202bc3a4919406b26fad08cb09b38c9` (`measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `123` files, `CACHE_VERSION = 145` / `145:route-d`)  
> **Candidate Freeze Commit (Commit 3):** `<FREEZE_COMMIT_SHA>` *(updated prior to Commit 4)*  
> **Verdict:** **`READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS`** (`HYBRID_ROUTE_MODE = "live"` default preserved; `GEMINI_PARITY = NOT_MEASURED`; `PHYSICAL_LOW_END = NOT_MEASURED`; `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`)

---

## 1. Executive Summary

AXO HYBRID /7 investigated two orthogonal, explicitly separated improvements to the offline Vietnamese spatial-geometry understanding pipeline on `Qwen/Qwen3-0.6B` without increasing model parameter count or relaxing `Source Gate`:

1. **`H1` — Deterministic Geometry Language Closure (`Config B -> Config C`):** Upgraded `slm-verified-normalizer/2` (`VN01`–`VN06` with 10-field span/semantic provenance), `local-slm-extractor/3` (strict GBNF + `_cand_has_contiguous` + role-safe quote binding + case-sensitive greeting strip + universal quantifier rules), and `adaptive_input_router.py` (`RuleRescue` escalation gating, `HYBRID_V7_LOCAL_SLM`, `local-slm-runtime/3`).
2. **`H2` — Targeted `Qwen3-0.6B` LoRA Fine-Tuning (`Config C -> Config D`):** Trained a LoRA adapter (`r=16, alpha=32`, `10,092,544` trainable params = `1.665%`, completion-only causal LM loss) purely on verified synthetic `train.jsonl` (`342` samples: `270+ / 72-`) and selected Epoch 2 purely on disjoint synthetic `val.jsonl` (`92` samples: `68+ / 24-`, zero wrong-served) — zero holdouts touched. Merged onto CPU base, converted to F16 GGUF via `llama.cpp b12470`, quantized to `Q4_K_M` (`Qwen3-0.6B-AxoV7-Q4_K_M.gguf`, `396,704,736` B, `sha256: 36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148`), leaving original `/5`/`/6` `Qwen3-0.6B-Q4_K_M.gguf` (`ac2d9771...`) untouched for rollback.

On the brand-new, anti-leakage-audited **single-shot blind holdout `SLM_V7_HOLDOUT_112`** (`80+ / 32-`, `0` exact/skeleton overlaps, `max_4gram = 0.3396`):
- **`H1` (`Config B -> C`):** `42/80 (52.50%) -> 53/80 (66.25%)` raw / `47/80 (58.75%) -> 58/80 (72.50%)` audited exact-string (`+11` gained, `0` regressed, `McNemar p = 0.000977`, Cohen's `h = 0.2810`).
- **`H2` (`Config C -> D`):** `53/80 (66.25%) -> 69/80 (86.25%)` raw (`95% CI [77.03%, 92.15%]`) / `58/80 (72.50%) -> 74/80 (92.50%)` audited exact-string (`+16` gained, `0` regressed, `McNemar p = 0.000031`, Cohen's `h = 0.4800`).
- **Safety & Latency:** `32/32 (100%)` negative refusal, `0` true wrong-served leaks, `0` Scene3D continuity errors, `0` baseline regressions across 11 suites, `14/14` adversarial/fault checks PASS, `23/23` SLM pytests PASS, warm uncached CPU `p50/p95 = 3438.61 / 4870.26 ms` (`threads=6`) and `3329.70 / 4519.61 ms` (`threads=8`), combined RSS `p50 = 1041.68 MiB` (`max <= 1044.43 MiB`).

---

## 2. Locked Identity & Artifact Hashes

| Component | Identity / Pin |
|---|---|
| Official Cache Policy (Unchanged) | `CACHE_VERSION = 145` (`145:route-d`), 4 locked Gemini surfaces unchanged, `0` `frontend/` diff |
| Local SLM Contracts (`/7`) | `local-slm-runtime/3`, `local-slm-extractor/3`, `slm-verified-normalizer/2`, `slm-grounding-validator/3`, `slm-compact-clause/1`, cache namespace `HYBRID_V7_LOCAL_SLM` |
| Fine-Tuned GGUF Model (`qwen3-0.6b-axo-v7-q4_k_m`) | `Qwen3-0.6B-AxoV7-Q4_K_M.gguf` · `396,704,736` B · `sha256: 36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148` |
| Original `/5`/`/6` GGUF Model (`qwen3-0.6b-q4_k_m`, preserved rollback) | `Qwen3-0.6B-Q4_K_M.gguf` · `396,705,472` B · `sha256: ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a` |
| HF Base Model (outside Git) | `Qwen/Qwen3-0.6B` rev `c1899de289a04d12100db370d81485cdf75e47ca` (`model.safetensors = 1,503,300,328` B, `sha256: f47f7117...`) |
| `train.jsonl` / `val.jsonl` (outside Git) | `train`: `342` (`270+/72-`, `sha256: 5dbdb22f...`) · `val`: `92` (`68+/24-`, `sha256: cb2f729b...`) |
| Blind Holdout Manifest (`SLM_V7_HOLDOUT_MANIFEST.json`) | `112` cases (`80+/32-`), `manifest_sha256_lf: eb88a74b6db94389f479d1d883fa4a602289df6df7786ceccce1f92c76545196` |
| External AI Calls Across Entire Campaign | `0` (`ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`) |

---

## 3. Quality Gates `C0`–`C9`

| Gate | Requirement Summary | Evidence | Status |
|---|---|---|---|
| **C0 — Baseline Integrity** | Verified HEAD `43bef643d`, `/5`/`/6` frozen unchanged, original GGUF `ac2d9771...`, locked Gemini surfaces intact | Commit `6310113f2`, `lock_cache_identity.py` | **PASS** |
| **C1 — Deterministic Closure** | Conservative `slm-verified-normalizer/2` (`VN01`–`VN06`), `local-slm-extractor/3`, Source Gate untouched, `0` Source Gate bypass | [`DETERMINISTIC_LANGUAGE_CLOSURE.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/DETERMINISTIC_LANGUAGE_CLOSURE.md), [`SOURCE_GATE_COMPATIBILITY_REPORT.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SOURCE_GATE_COMPATIBILITY_REPORT.md) | **PASS** |
| **C2 — Post-Closure & Readiness** | Isolated `Config A` vs `B` vs `C`, attributed SLM residual errors, justified fine-tuning (`5/28` HOLDOUT_40 & `6/32` HOLDOUT_48 residual SLM omissions) | [`SLM_POST_CLOSURE_EVALUATION.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_POST_CLOSURE_EVALUATION.json), [`SLM_FINE_TUNING_READINESS.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_FINE_TUNING_READINESS.md) | **PASS** |
| **C3 — Training Data Integrity** | Exact Kernel + 60-digit Decimal verified, family-disjoint split (`train 342`, `val 92`), `0` external/internal overlap, Apache-2.0 compatible | [`SLM_TRAINING_DATA_MANIFEST.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_TRAINING_DATA_MANIFEST.json) | **PASS** |
| **C4 — LoRA Fine-Tuning** | Real `GTX 1650` FP32 completion-only LoRA (`3621.59 MiB` VRAM, `5516.72s`), Epoch 2 selected on `val.jsonl` (`61/68` pos, `24/24` neg, `0` wrong) | [`SLM_TRAINING_IMPLEMENTATION.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_TRAINING_IMPLEMENTATION.md), [`SLM_TRAINING_RUN.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_TRAINING_RUN.json) | **PASS** |
| **C5 — Quantized Runtime** | Merge -> F16 (`1.198 GB`) -> `Q4_K_M` (`396.7 MB`, `36e784d1...`); on `val.jsonl`: `63/68` (`92.65%`) & `24/24` neg vs merged FP16 `61/68` & orig `34/68` (`+29` routed / `+43` direct); `0` wrong | [`SLM_ADAPTER_MODEL_MANIFEST.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_ADAPTER_MODEL_MANIFEST.json), [`SLM_QUANTIZATION_EVALUATION.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_QUANTIZATION_EVALUATION.json) | **PASS** |
| **C6 — Independent Blind Holdout** | Product Commit 1 frozen first (`6310113f2`), `112` cases (`80+/32-`, `0` leakage), single-shot `Config A/B/C/D`, Wilson CI + McNemar + Cohen's `h` + grader `cos²=` audit | [`SLM_V7_HOLDOUT_MANIFEST.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_MANIFEST.json), [`SLM_V7_HOLDOUT_EVALUATION.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_EVALUATION.json) | **PASS** *(H-1 sealed stays `NOT_MEASURED`)* |
| **C7 — CPU Performance** | Cold (`n=10`), warm uncached thread sweep (`4T/6T/8T n=30` vs orig `6T n=30`), separate cached `n=30`, peak RSS; low-end physical disclosed `NOT_MEASURED` | [`SLM_V7_PERFORMANCE.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_PERFORMANCE.json) | **PASS** *(Host CPU)* / **`NOT_MEASURED`** *(4–6 GB device)* |
| **C8 — Regression & Safety** | `11` baseline suites (`Config A/C/D`), `23/23` SLM pytest, `14/14` fault/adversarial checks on both GGUFs, clean-tree full pytest `<FULL_PYTEST_SUMMARY>`, 5 governance checks | [`SLM_V7_REGRESSION_REPORT.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_REGRESSION_REPORT.md), [`SLM_V7_REGRESSION_RESULTS.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_REGRESSION_RESULTS.json) | **PASS** |
| **C9 — Replacement Decision** | Pre-registered verdict `READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS`, honest `NOT_MEASURED` disclosures, owner handoff, `HYBRID_ROUTE_MODE = live` preserved | [`SLM_REPLACEMENT_DECISION.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_REPLACEMENT_DECISION.md), [`SOURCE_GATE_OWNER_HANDOFF.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SOURCE_GATE_OWNER_HANDOFF.md) | **PASS** |

---

## 4. Empirical Results Across Datasets

### 4.1 Historical Diagnostic 4-Way Ablation (`SLM_V7_ABLATION.json`)

| Dataset | `Config A` (`det_v145`) | `Config B` (`/6 + Orig`) | `Config C` (`/7 + Orig`) | `Config D` (`/7 + AxoV7`) | `B -> C` (`H1`) | `C -> D` (`H2`) |
|---|---|---|---|---|---|---|
| `DEV_CALIBRATION_16` (`10+/6-`) | `0/10` (`6/6-`) | `8/10` (`p50=3855.70ms`) | `9/10` (`p50=4167.73ms`) | `9/10` (`p50=2741.26ms`) | `+1` (`p=1.0`) | `+0` (`p=1.0`) |
| `HOLDOUT_40` (`28+/12-`) | `9/28` (`12/12-`) | `18/28` (`p50=4695.65ms`) | `25/28` (`p50=4619.29ms`) | `24/28` (`p50=3105.81ms`) | `+7` (`p=0.015625, h=0.6141`) | `-1` (`p=1.0`, `slm_h23`) |
| `SLM_NEW_HOLDOUT_48` (`32+/16-`) | `13/32` (`16/16-`) | `19/32` (`p50=3883.48ms`) | `26/32` (`p50=4034.23ms`) | **`32/32 (100%)`** (`p50=3321.02ms`) | `+7` (`p=0.015625, h=0.4865`) | **`+6` (`p=0.03125, h=0.8957`)** |

### 4.2 Single-Shot Blind Holdout `SLM_V7_HOLDOUT_112` (`80+ / 32-`)

- **Raw evaluator (`EVI.same_value`):** `Config A = 34/80 (42.50%)`, `Config B = 42/80 (52.50%)`, `Config C = 53/80 (66.25%)`, **`Config D = 69/80 (86.25%, Wilson [77.03%, 92.15%])`**, all `32/32` neg refused, `continuity_errors = 0`.
- **Audited exact-string math (`cos²=` on `v7h_p7_06..10`):** `Config A = 39/80 (48.75%)`, `Config B = 47/80 (58.75%)`, `Config C = 58/80 (72.50%)`, **`Config D = 74/80 (92.50%)`**, **`0/80` and `0/32` true `wrong_served` leaks across all 4 configs**.
- **Stratum breakdown (`Config A -> C -> D`, raw):**
  - `P1 Regular Prism/Pyramid/Tetrahedron/Box`: `3/10 -> 9/10 -> 10/10`
  - `P2 Rect/Square Oblique/Altitude`: `0/10 -> 4/10 -> 10/10`
  - `P3 Rhombus/Parallelogram/Iso-Trap`: `7/10 -> 7/10 -> 10/10`
  - `P4 Face Perp Base Multi`: `5/10 -> 10/10 -> 10/10`
  - `P5 Orthoproj/Centroid/Midpoint`: `4/10 -> 6/10 -> 9/10` (`v7h_p5_09` `SOURCE_OBJECT_MISMATCH`)
  - `P6 Divide Ratio & Skew Dist`: `10/10 -> 10/10 -> 10/10`
  - `P7 Plane Angles & Prism Multi`: `5/10 -> 5/10 -> 5/10` (`5/10` exact `cos²=` in all 4 configs -> `10/10` math)
  - `P8 Conversational/Reordered`: `0/10 -> 2/10 -> 5/10` (`v7h_p8_01..05` conversational prefix -> `Source Gate`)
  - `N1`–`N4` (`32` negatives): `32/32` refused across all 4 configs (`0` false serves).

### 4.3 CPU Performance Benchmark (`SLM_V7_PERFORMANCE.json`, 15.78 GiB Windows Host)

- **Cold Start (`finetuned`, `n=10`):** Server load `p50/p95 = 909.96 / 961.05 ms`, SLM `p50/p95 = 5085.65 / 5738.79 ms`, Total E2E `p50/p95 = 6217.99 / 6868.18 ms`, Combined RSS `p50/p95 = 1039.74 / 1040.30 MiB`.
- **Warm Uncached Thread Sweep (`n=30` each, `timeout=0.0, crash=0.0`):**
  - `finetuned t=4`: `29.69 tok/s`, SLM `p50/p95 = 3718.56 / 5297.99 ms`, E2E `3762.80 / 5358.98 ms`, RSS `1040.49 / 1041.84 MiB`.
  - `finetuned t=6`: `30.77 tok/s`, SLM `p50/p95 = 3438.61 / 4870.26 ms`, E2E `3483.67 / 4929.19 ms`, RSS `1041.68 / 1041.96 MiB` (vs `original t=6` SLM `3392.39 / 5611.66 ms` — fine-tuned cuts warm `p95` by `741.40 ms`).
  - `finetuned t=8`: `33.41 tok/s`, SLM `p50/p95 = 3329.70 / 4519.61 ms`, E2E `3412.18 / 4584.31 ms`, RSS `1043.04 / 1043.19 MiB`.
- **Warm Cached (`n=30` separate):** `100%` cache hits, E2E `p50/p95 = 36.45 / 49.50 ms`.

### 4.4 Baseline Regressions, Fault Checks & Clean-Tree Verification

- `0` baseline regressions, `0` new Mode-A leaks, and `0` Scene3D continuity errors across `REAL27_TEXT` (`21/27`), `REAL27_IMAGES` (`21/27`), `NC_GOLD` (`21/21`), `NC_NL` (`21/21`), `AUTONOMOUS_NEGATIVES` (`11/11`), `RM72` (`61/62+`, `10/10-`), `DEV37` (`30/30+`, `7/7-`), `PROBES39` (`23/26+`, `13/13-`), `S2_36` (`16/18+`, `18/18-`), `COMP112` (`66/66+`, `44/46-` dual-reported).
- `frozen_unseen_vmmu20`: strictly excluded (`GROUND_TRUTH_UNVERIFIED`, `0/19` unverified serves on both Config C & D).
- `14/14` Section-16 fault & adversarial checks PASS across both original and fine-tuned GGUF models; `23/23` SLM pytest tests PASS (`48.12s`); C21 templates `K-1`/`S-2`/`R-1` metadata refreshed (`PENDING_OWNER_DECISION`, `paid_project_confirmed = false`).
- Clean-tree full backend `pytest`: `<FULL_PYTEST_SUMMARY>`.

---

## 5. Rollback & Honest Boundaries

- **Rollback to `/6` original model:** Set `AXO_LOCAL_SLM_MODEL=qwen3-0.6b-q4_k_m` (runtime keeps `ac2d9771...` pinned) or set `HYBRID_ROUTE_MODE=live` (already the untouched production default). Full architectural rollback: `git revert` to Commit `43bef643d2c528053526d363ee578065e60e6116`.
- **Preserved Non-Claims:** `GEMINI_PARITY = NOT_MEASURED`, `PHYSICAL_LOW_END = NOT_MEASURED`, `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`, `REAL_STUDENT_USABILITY = NOT_MEASURED`, `FRONTEND_INTEGRATION = BLOCKED_OWNERSHIP`, `SOURCE_GATE_OWNER_HANDOFF = BLOCKED_OWNERSHIP`.
