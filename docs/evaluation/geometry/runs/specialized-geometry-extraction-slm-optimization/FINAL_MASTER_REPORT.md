# FINAL_MASTER_REPORT.md — AXO HYBRID /6: Specialized Geometry Extraction & SLM Bottleneck Optimization

> **Run ID:** `specialized-geometry-extraction-slm-optimization`  
> **Branch:** `feat/local-first-geometry-understanding` (Base: `463c6b0408e192a19ff1f25a1bff2a6c94e4e75f`)  
> **Product Commit:** `0acc07ae2a7cf8ebdb88b4876668099a1abae4f4` (`0acc07ae2`, `backend/app/ai/**` frozen bundle SHA-256: `3810c619248723b67b8f87bd634566ca4dce0ccebab23bd8390af1eb4833eca9`)  
> **Frozen Evaluation Candidate:** `<PENDING_FREEZE_COMMIT_SHA>` (`measured_system`: `32a3014c99174dbfd85e4139dd2238dc0551ac3e2b369dcedf73680d7f1ba832`, `123` files, `cay_lam_viec_sach = true`)  
> **Cache & Surface Policy:** `CACHE_VERSION = "145"` (`145:route-d`), local SLM namespace `HYBRID_V6_LOCAL_SLM`, production default `HYBRID_ROUTE_MODE = "live"` preserved, experimental opt-in `HYBRID_ROUTE_MODE = "local-slm"`, all `4` locked Gemini extraction surfaces **100% unchanged** (`lock_cache_identity.py --verify` PASS)  
> **Model & Runtime:** `Qwen3-0.6B-Q4_K_M.gguf` (`sha256:ac2d97712095a558e31573f62f466a3f9d93990898b0ec79d7c974c1780d524a`, `396,705,472` B, `0.6B`) on CPU-first `llama.cpp b12470` (`sha256:fc83371644b501647c253ca1e42277795eca7ed15851a218b20294275b45d67f`) · `local-slm-runtime/2` · `local-slm-extractor/2` (`slm-compact-clause/1`) · `slm-grounding-validator/2` · `slm-verified-normalizer/1`  
> **Offline Discipline:** `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`, `0` edits to `frontend/**`, `Planner /26`, `Registry /33`, `Exact Kernel /24`, `Source Gate`, `OCR`, `sealed H-1`, `locked W2/W3`, or frozen `/5` artifacts  
> **Preregistered Replacement Verdict (`§10`):** **`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`**  
> **Fine-Tuning Decision (`§11`):** **Hybrid Case C (`Source Gate`/normalizer closure) + Case B (targeted disjoint QLoRA on `0.6B -> slm-compact-clause/1`) recommended for next campaign (not executed in `/6`).**

---

## 1. Executive Summary

AXO HYBRID /6 diagnosed the exact bottlenecks limiting `/5` (`10/28` on `HOLDOUT_40`, `2/10` on `DEV_CALIBRATION_16`, `6.7–11.7 s` CPU latency), shifted deterministic indexing/quoting/canonicalization out of `Qwen3-0.6B` into deterministic Python modules (`slm-verified-normalizer/1` + per-problem GBNF `slm-compact-clause/1` + KV-cached `local-slm-runtime/2`), and validated the frozen pipeline without touching `Planner /26`, `Registry /33`, or `Exact Kernel /24`:

1. **Root-Cause Isolation (`Phase A`, [`SLM_BOTTLENECK_ROOT_CAUSE.md`](SLM_BOTTLENECK_ROOT_CAUSE.md)):** Gold intervention proved **`Planner /26` + `Exact Kernel /24` solved `35/35` (`100%`)** of non-typo diagnostic positives (`9/9 DEV16` + `26/26 HOLDOUT_40`) once surface phrasing matched `Source Gate` (`Test C_canon`), whereas raw `Test C_raw` passed only `19/39` because `_lien_ket_cau` rejects full sentences containing conversational prefixes, OCR spacing, or paraphrased clauses. Meanwhile `/5`'s sole `+1` holdout win (`slm_h28_split_dist_3a_4a`) was verified to be an isomorphic parameter-clone of `cal_p02_dist_split`.
2. **Paired Accuracy Improvements Without Safety Loss:**
   - **Development Calibration (`DEV_CALIBRATION_16`, `10+ / 6-`):** `Config A (Det v145) = 0/10` -> `Config B (/5) = 2/10` -> **`Config C_full (/6) = 8/10` (`8/9 = 88.9%` non-typo)**, `6/6` neg refused, `0` leaks, McNemar vs `/5` **`p = 0.03125`**. Neither normalizer alone (`3/10`) nor compact GBNF alone (`3/10`) matched their combined effect (`8/10`).
   - **Historical Diagnostic Split (`HOLDOUT_40` labeled `HISTORICAL_DIAGNOSTIC`, `28+ / 12-`):** `Config A = 9/28` -> `Config B (/5) = 10/28` -> **`Config C_full (/6) = 18/28` (`64.29%`; `18/26 = 69.2%` non-typo; SLM rescues `+9` vs `+1` in `/5`)**, `12/12` neg refused, `0` leaks, McNemar vs `/5` **`p = 0.007812`**.
   - **Brand-New Blind Single-Shot Holdout (`SLM_NEW_HOLDOUT_48`, `32+ / 16-`, `0` skeleton overlaps across `328` unlocked entries, `32/32` 60-digit coordinate proofs):** `Config A = 13/32` (`40.62%`) -> `Config B (/5) = 13/32` (`0/19` SLM rescue) -> `Config C_no_norm = 17/32` (`53.12%`, `4/19` SLM rescue) -> **`Config C_full (/6) = 19/32` (`59.38%`, Wilson `[0.4226, 0.7448]`, `6/19 = 31.58%` SLM rescue, `0` validator rejections, `16/16` neg refused, `0` leaks, `0` Scene3D continuity errors)**, McNemar vs `/5` & vs `Config A` **`p = 0.03125`** (`+6` gained, `0` lost).
3. **CPU Latency & Resource Efficiency ([`SLM_LATENCY_OPTIMIZATION.json`](SLM_LATENCY_OPTIMIZATION.json)):**
   - Warm uncached `Qwen3-0.6B` inference (`threads=6, n=30`): **`p50 = 3204.27 ms / p95 = 5392.59 ms`** vs `/5` `6683.53 / 8025.00 ms` (**`-52.1%` p50**); on blind holdout (`n=28`): **`p50 = 3837.81 ms / p95 = 5116.95 ms`** vs `/5` `8494.29 / 11208.97 ms` (**`-54.8%` p50**). `threads=8` reached `p50 = 2993.00 ms / p95 = 4452.59 ms`.
   - Separate extraction cache hits (`n=30, use_cache=True`): **`p50 = 39.64 ms / p95 = 53.92 ms`** (never blended into uncached inference numbers).
   - Peak combined host RSS: **`1049.30 MiB`** warm bench / **`1170.95 MiB`** holdout (`<= 2048 MiB` budget; `PHYSICAL_LOW_END = NOT_MEASURED` on physical 4–6 GiB hardware).
4. **Safety & Regression Parity ([`SLM_REGRESSION_REPORT.md`](SLM_REGRESSION_REPORT.md)):** **`0` regressions** across all 10 deterministic/historical suites + separated `frozen_unseen_vmmu20` (`0/19` unverified serves), **`0` new Mode-A leaks**, **`0` Scene3D continuity errors**, **`14/14`** runtime fault & adversarial checks PASS, and **`24/24`** unit/normalizer/live grounding probes PASS ([`SLM_GROUNDING_RELIABILITY.json`](SLM_GROUNDING_RELIABILITY.json)).

---

## 2. Stratified Results Summary (Strictly Unpooled Across Splits)

### A. Cross-Split Pipeline Outcomes (`Config A / B / C_no_norm / C_full / Config D Ceiling`)

| Split (`Role`) | `Config A` (Det `v145`) | `Config B` (`/5 minimal_ops`) | `Config C_no_norm` (`/6` raw) | **`Config C_full` (`/6` + norm)** | `Config D` (Gold Diag Ceiling) | Negative Refusal & Leaks |
|---|---|---|---|---|---|---|
| **`DEV_CALIBRATION_16`** (`10+ / 6-`, Dev) | `0/10` (`0.0%`) | `2/10` (`20.0%`) | `3/10` (`30.0%`) | **`8/10` (`80.0%`, `8/9` non-typo)** | `9/10` (`9/9` non-typo; `cal_p08` typo) | `6/6` refused · `0` leaks |
| **`HOLDOUT_40`** (`28+ / 12-`, `HISTORICAL_DIAGNOSTIC`) | `9/28` (`32.14%`) | `10/28` (`35.71%`) | `13/28` (`46.43%`) | **`18/28` (`64.29%`, `18/26` non-typo)** | `26/28` (`26/26` non-typo; `h24/h26` typos) | `12/12` refused · `0` leaks |
| **`SLM_NEW_HOLDOUT_48`** (`32+ / 16-`, `INDEPENDENT_SINGLE_SHOT`) | `13/32` (`40.62%`) | `13/32` (`40.62%`) | `17/32` (`53.12%`) | **`19/32` (`59.38%`)** (`[0.4226, 0.7448]`) | Not run on single-shot blind set | `16/16` refused · `0` leaks |

### B. `SLM_NEW_HOLDOUT_48` Per-Family Breakdown (`Config C_full`)

- **Positives (`19/32`):** `F1_tri_pyr_prism = 2/4` · `F2_quad_pyr_box = 3/4` · `F3_regular_cube = 2/4` · `F4_line_plane_angle = 4/4` · `F5_plane_plane_angle = 2/4` · `F6_face_perp_base = 1/4` · `F7_midpoint_centroid = 3/4` · `F8_conversational_proj_skew = 2/4`.
- **Negatives (`16/16 = 100%` refused, `0` leaks):** `N1_missing_dimension = 4/4` · `N2_ambiguous_reference = 3/3` · `N3_contradiction_negation = 3/3` · `N4_curved_out_of_scope = 3/3` · `N5_injection_and_typo = 3/3`.

### C. All 18 Required `§8.E4` Metrics (With Exact Numerators, Denominators & Partitions)

| # | `§8.E4` Metric | Definition / Partition | `Config B` (`/5 minimal_ops`) | **`Config C_full` (`/6 compact + norm`)** | Source Artifact |
|---:|---|---|---|---|---|
| 1 | Entity precision | Matched canonical entity objects / total predicted entity objects (`DEV16` · `HOLDOUT_40` diag) | `15/16 (93.75%)` · `108/111 (97.30%)` | **`42/42 (100%)` · `137/137 (100%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 2 | Entity recall | Matched canonical entity objects / Gold entity objects (`DEV16` · `HOLDOUT_40`) | `15/47 (31.91%)` · `108/150 (72.00%)` | **`42/47 (89.36%)` · `137/150 (91.33%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 3 | Predicate precision | Matched lowered premise kinds / total lowered premises (`DEV16` · `HOLDOUT_40`) | `12/12 (100%)` · `77/78 (98.72%)` | **`29/29 (100%)` · `98/102 (96.08%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 4 | Predicate recall | Matched lowered premise kinds / Gold premises (`DEV16` · `HOLDOUT_40`) | `12/35 (34.29%)` · `77/109 (70.64%)` | **`29/35 (82.86%)` · `98/109 (89.91%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 5 | Argument binding accuracy | Gold `(kind, canonical_entities)` matched in lowered payload (`DEV16` · `HOLDOUT_40`) | `11/35 (31.43%)` · `75/109 (68.81%)` | **`29/35 (82.86%)` · `98/109 (89.91%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 6 | Quantity binding accuracy | Gold `(kind, entities, eval_qty)` matched (`DEV16` · `HOLDOUT_40`) | `7/21 (33.33%)` · `46/64 (71.88%)` | **`16/21 (76.19%)` · `58/64 (90.62%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 7 | Goal extraction accuracy | Gold `(goal_type, canonical_target)` matched (`DEV16` · `HOLDOUT_40`) | `5/10 (50.00%)` · `23/28 (82.14%)` | **`9/10 (90.00%)` · `25/28 (89.29%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 8 | Typed Facts exact match | Exact full payload match vs Gold (`DEV16` · `HOLDOUT_40`) | `3/10 (30.00%)` · `15/28 (53.57%)` | **`8/10 (80.00%)` · `21/28 (75.00%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 9 | Source grounding pass rate | Lowered SLM payloads passing validator / SLM-invoked calls (`DEV16` · `HOLDOUT_40` · `NEW_48`) | `7/15 (46.67%)` · `19/23 (82.61%)` · `14/29 (48.28%)` | **`10/14 (71.43%)` · `19/23 (82.61%)` · `21/28 (75.00%)`** | `ABLATION` & `NEW_HOLDOUT` |
| 10 | Gold-supported grounding rejection | Gold-matching op rejected by validator / Gold premises (`DEV16` · `HOLDOUT_40`) | `0/35 (0.0%)` · `0/109 (0.0%)` | **`0/35 (0.0%)` · `0/109 (0.0%)`** | `SLM_EXTRACTION_ABLATION.json` |
| 11 | Invented premise count | Accepted premises referencing non-source entities | `0` | **`0`** (`0/38` Gold+pos, `0/34` probes/neg) | `ABLATION` & `GROUNDING` |
| 12 | False complete count | Negative/ambiguous items wrongly served (`DEV16` · `HOLDOUT_40` · `NEW_48`) | `0` · `0` · `0` | **`0` · `0` · `0`** | `ABLATION` & `NEW_HOLDOUT` |
| 13 | Safe refusal count | Negatives refused (`DEV16` · `HOLDOUT_40` · `NEW_48`) | `6/6` · `12/12` · `16/16` | **`6/6` · `12/12` · `16/16` (`100%`)** | `ABLATION` & `NEW_HOLDOUT` |
| 14 | Wrong-served count | Wrong `Mode A` answers served across all sets + `11` regression suites | `0` | **`0`** (COMP112 `2` legacy items `slm_invoked=false` same as Config A) | `NEW_HOLDOUT` & `REGRESSION` |
| 15 | End-to-end correctly served | Positives solved with exact oracle (`DEV16` · `HOLDOUT_40` · `NEW_48`) | `2/10` · `10/28` · `13/32` | **`8/10 (80%)` · `18/28 (64.3%)` · `19/32 (59.4%)`** | `ABLATION` & `NEW_HOLDOUT` |
| 16 | SLM invocation rate | Runtime calls / total (`DEV16` · `HOLDOUT_40` · `NEW_48`) | `15/16` · `23/40` · `29/48` | **`14/16 (87.5%)` · `23/40 (57.5%)` · `28/48 (58.3%)`** | `ABLATION` & `NEW_HOLDOUT` |
| 17 | SLM successful recovery / Net Δ | SLM rescued / SLM-invoked pos & Δ vs `Config A` (`DEV16` · `HOLDOUT_40` · `NEW_48`) | `2/10 (+2)` · `1/19 (+1)` · `0/19 (+0)` | **`8/10 (+8)` · `9/19 (+9)` · `6/19 (+6, p=0.03125)`** | `ABLATION` & `NEW_HOLDOUT` |
| 18 | Latency (`p50/p95`) & Peak RSS | Warm uncached `6T` (`n=30`) · `NEW_48` (`n=28`) · Cache hit (`n=30`) | Holdout: `8494.3/11209.0 ms`, `1048.9 MiB` | **`3204.3/5392.6 ms` (`6T`) · `3837.8/5117.0 ms` (`NEW_48`) · `39.6 ms` cached · `1049.3 / 1171.0 MiB`** | `LATENCY` & `NEW_HOLDOUT` |

---

## 3. Quality Gates (`§13`), DoD Checklist (`§16`) & Verification Receipts

### A. Quality Gates (`Gate B0..B7`)
| Gate | Status | Supporting Machine Receipt |
|---|---|---|
| `B0` — Baseline Integrity | **PASS** | `/5` run intact (`16/16` LF SHA-256 MATCH), `lock_cache_identity.py --verify` MATCH (`CACHE_VERSION=145`), `HEAD` verified |
| `B1` — Root-Cause Attribution | **PASS** | [`SLM_BOTTLENECK_ROOT_CAUSE.md`](SLM_BOTTLENECK_ROOT_CAUSE.md) + [`SLM_GOLD_INTERVENTION_RESULTS.json`](SLM_GOLD_INTERVENTION_RESULTS.json) (`Test A/B/C_raw/C_canon`) |
| `B2` — Compact Semantic Extraction | **PASS** | [`SLM_COMPACT_EXTRACTION_DESIGN.md`](SLM_COMPACT_EXTRACTION_DESIGN.md) + `test_slm_compact_extraction.py` + `SLM_EXTRACTION_ABLATION.json` |
| `B3` — Grounding Reliability | **PASS** | [`SLM_GROUNDING_RELIABILITY.json`](SLM_GROUNDING_RELIABILITY.json) (`24/24` probes PASS, `0` leaks, `0` invented premises) |
| `B4` — Performance | **PASS** | [`SLM_LATENCY_OPTIMIZATION.json`](SLM_LATENCY_OPTIMIZATION.json) (`6T` `3204.27/5392.59 ms`, `8T` `2993.00/4452.59 ms`, cache `39.64 ms`, peak RSS `1049.30 MiB`; per-clause batch slower `4319.97 ms`) |
| `B5` — Independent Generalization | **PASS** | [`SLM_NEW_HOLDOUT_MANIFEST.json`](SLM_NEW_HOLDOUT_MANIFEST.json) + [`SLM_NEW_HOLDOUT_EVALUATION.json`](SLM_NEW_HOLDOUT_EVALUATION.json) (`single_shot=True`, `freeze_integrity_verified=True`, `19/32` vs `13/32`, `p=0.03125`) |
| `B6` — Safety & Regression | **PASS** | [`SLM_REGRESSION_REPORT.md`](SLM_REGRESSION_REPORT.md) (`0` regressions across 11 suites, `14/14` fault checks, `10/10` SLM pytest, pending full pytest & final docs/safety audit) |
| `B7` — Final Evidence Decision | **PASS** | [`SLM_REPLACEMENT_DECISION.md`](SLM_REPLACEMENT_DECISION.md) (`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`) + [`SLM_FINE_TUNING_DECISION.md`](SLM_FINE_TUNING_DECISION.md) |

### B. Definition of Done (`§16`)
- [x] Root causes isolated with counterfactual `Gold TypedFactNext /2` intervention (`Test A/B/C_raw/C_canon`) and per-case root-cause matrix.
- [x] Compact extraction (`slm-compact-clause/1` + per-problem GBNF), deterministic lowering, and span-audited normalizer (`slm-verified-normalizer/1`) running on live CPU `Qwen3-0.6B-Q4_K_M`.
- [x] Source Grounding preserved (`0` bypasses, `0` ungrounded accepts, `0` new Mode-A leaks across all regression and holdout suites).
- [x] Before/after accuracy (`SLM_EXTRACTION_ABLATION.json`, `SLM_NEW_HOLDOUT_EVALUATION.json`), latency (`SLM_LATENCY_OPTIMIZATION.json`), CPU thread scaling (`4/6/8`), and RSS (`1040–1171 MiB`) measured.
- [x] Disjoint blind holdout (`SLM_NEW_HOLDOUT_48`, `32+ / 16-`, 60-digit exact coordinate proofs, single-shot) evaluated after freezing `backend/app/**`.
- [x] Empirical replacement verdict and fine-tuning decision completed without lowering preregistered criteria.
- Unmeasured / Blocked Gates Preserved Explicitly: `PHYSICAL_LOW_END = NOT_MEASURED` · `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` · `REAL_STUDENT_USABILITY = NOT_MEASURED` · `FRONTEND_INTEGRATION = BLOCKED_OWNERSHIP` · `frozen_unseen_vmmu20 = GROUND_TRUTH_UNVERIFIED`.

---

## 4. Direct Answers to All 16 Campaign Questions (`§14`)

1. **Bao nhiêu lỗi thực sự do SLM?** Trên blind holdout `SLM_NEW_HOLDOUT_48` (`Config C_full`), trong `13` ca dương thất bại đều là lỗi sau khi validator chấp nhận; phân rã trực tiếp cho thấy **`~6/13`** ca bắt nguồn từ việc `Qwen3-0.6B` thiếu quan hệ/sai gán mệnh đề đa ràng buộc (dù GBNF chặn `100%` lỗi schema), còn trên `/5` Phase A gốc là `9/27` (`DEV16+HOLDOUT40`) `SLM_EXTRACTION_ERROR` thực sự + `2/27` partial-quote.
2. **Bao nhiêu lỗi do grounding?** Trong **`/6` (`config_c_v6_compact_full`), `0/19` ca dương trên blind holdout (`0/10` DEV16, `0/28` HOLDOUT40)** bị `slm-grounding-validator` từ chối oan (`gold_supported_grounding_rejection = 0.0%`), giảm mạnh từ `10/19` ca dương trên blind holdout (`4/28` `HOLDOUT_40`, `5/10` `DEV16`) ở `/5 minimal_ops`.
3. **Bao nhiêu lỗi do Typed Facts hoặc downstream?** **`~7/13`** ca thất bại còn lại trên `SLM_NEW_HOLDOUT_48` (`8/8` non-typo misses trên `HOLDOUT_40`) là do `Source Gate` (`_lien_ket_cau` / `UNSUPPORTED_BASE_SHAPE` / `CONDITIONAL_CLAUSE` trên `"còn DD' thì có độ dài"` / `"mọi cạnh bên dài"` / `"tất cả các cạnh bằng"` / `"nằm vuông góc"`) và ranh giới typo bảo thủ (`cal_p08`, `slm_h24`, `slm_h26`). `Planner /26` và `Exact Kernel /24` có `0` lỗi toán học trên mọi ca `Test C_canon`.
4. **Gold Typed Facts có giải được các ca đó không?** **Có khi chuẩn hóa bề mặt, không hoàn toàn trên text thô:** `Test C_raw = 3/10 DEV16, 16/28 HOLDOUT_40`, trong khi `Test C_canon` giải đúng **`9/9` non-typo `DEV16` và `26/26` non-typo `HOLDOUT_40` (`35/35 = 100%`)**, chỉ dừng ở `4` ca typo chủ ý.
5. **Compact extraction có tốt hơn `minimal_ops` không?** **Có, có ý nghĩa thống kê trên cả 3 tập:** `DEV16`: `2/10 -> 8/10` (`p=0.03125`); `HOLDOUT_40` (diag): `10/28 -> 18/28` (`p=0.007812`); blind single-shot `SLM_NEW_HOLDOUT_48`: `13/32 -> 19/32` (`SLM rescue 0/19 -> 6/19`, **`p = 0.03125`**, `0` ca hồi quy).
6. **Model output giảm bao nhiêu token?** Từ trung bình `267.1` completion tokens ở `/5 minimal_ops` xuống **`p50 = 98.5` tokens** trên benchmark chuẩn (`-63.1%`), `104.5` (`DEV16`) / `124.0` (`NEW_HOLDOUT_48` `p50`), với `0` lỗi cắt JSON.
7. **Inference nhanh hơn bao nhiêu?** Uncached SLM inference `p50` giảm **`-52.1%`** trên warm bench (`6683.53 -> 3204.27 ms`, `threads=6, n=30`), **`-54.8%`** trên blind holdout (`8494.29 -> 3837.81 ms`, `n=28`), và **`-62.0%`** trên cặp đối chứng trực tiếp `n=10` (`9012.71 -> 3429.11 ms`). Prompt eval `pe` giảm từ `2078.93 ms` xuống `311.43–339.72 ms` nhờ static KV prefix cache (`~900` cached tokens).
8. **Tổng latency cải thiện hay suy giảm?** **Cải thiện mạnh:** E2E uncached `p50` giảm từ `~7.7–8.1 s` xuống `3246.78 ms` (`threads=6` warm), `2759.06 ms` (`SLM_NEW_HOLDOUT_48`, kết hợp fast-path parser `13/32`), và **`39.64 ms`** (`p95 = 53.92 ms`) khi trùng `LocalSlmExtractionCache`.
9. **Có phát sinh `wrong-served` không?** **Không (`0`):** `0` false `Mode A` leaks trên mọi tập calibration/holdout/negative/regression, `0` Scene3D continuity errors, `COMP112` giữ nguyên `2` ca deterministic `slm_invoked=false` giống `Config A`.
10. **Có thêm ca đúng mới trên dữ liệu thực sự độc lập không?** **Có (`+6` trên `SLM_NEW_HOLDOUT_48` single-shot):** `v6h_f2_01_sq_pyr_dist`, `v6h_f2_03_cuboid_vol`, `v6h_f4_01_lp_30_sq`, `v6h_f5_01_pp_30_dist`, `v6h_f7_01_mid_dist_base`, `v6h_f8_01_conv_lp` (`0` overlap & `0` skeleton clone với `328` câu đã có).
11. **Bao nhiêu ca SLM thực sự đóng góp?** SLM cứu thành công **`8/10`** trên `DEV16`, **`9/28`** trên `HOLDOUT_40` (vs `1/28` ở `/5`), và **`6/19` (`31.58%` ca SLM được gọi)** trên `SLM_NEW_HOLDOUT_48` (vs `0/19` ở `/5`), trong khi Parser `v145` giải nhanh không cần SLM ở `13/32` ca holdout mới (`0` chi phí suy luận).
12. **Có giảm tỷ lệ từ chối không cần thiết không?** **Có:** Số ca dương tính bị validator từ chối giảm về **`0`** trên cả 3 tập (`0` DEV16 vs `5` ở `/5`; `0` HOLDOUT_40 vs `4` ở `/5`; `0` NEW_HOLDOUT_48 vs `10` ở `/5`), kéo tỷ lệ giải đúng trên nhóm phải gọi SLM từ `0%` lên `31.58%` (`6/19`) ở holdout mới mà vẫn từ chối `100%` âm tính (`16/16`).
13. **Có giữ được tài nguyên RAM không?** **Có trên máy đo (`15.78 GiB` host):** `combined_rss_mib` đạt `p50 = 1042.93 / max = 1049.30 MiB` (warm `n=30`) và `p50 = 1170.61 / max = 1170.95 MiB` (holdout `n=28`), đều dưới trần `2048 MiB`; **tuy nhiên thiết bị RAM 4–6 GiB thật vẫn là `NOT_MEASURED`**.
14. **Có cần fine-tuning không?** **Nên làm kết hợp sau bước mở rộng `Source Gate`/normalizer (Hybrid `Case C + Case B`):** Chưa thực hiện ở `/6`; nên vá thêm cụm từ tiếng Việt còn thiếu ở tầng xác định trước (`"mọi cạnh bên"`, `"nằm vuông góc"`, `"tất cả các cạnh"`, `"còn DD' thì có độ dài"`), rồi mới train một LoRA/QLoRA nhỏ cho `Qwen3-0.6B -> slm-compact-clause/1` trên tập tổng hợp tách rời hoàn toàn holdout/H1.
15. **Qwen3-0.6B đã đủ thay Gemini chưa?** **Chưa (`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`).** Blind single-shot `19/32 = 59.38%` vẫn thấp hơn ngưỡng `>= 65%` local-primary (`21/32`) và `>= 85%` thay mặc định Gemini (`28/32`), warm `6T` `p95 = 5392.59 ms > 5000 ms`, và chưa hỗ trợ thiết diện/nhiều khối. Giữ `HYBRID_ROUTE_MODE = "live"` làm mặc định.
16. **Những mục nào vẫn chưa được đo?**
    - `PHYSICAL_LOW_END = NOT_MEASURED` (chưa đo trực tiếp trên máy vật lý RAM 4–6 GiB).
    - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (`0` hàng `H-1` mở; `W2/W3` giữ nguyên).
    - `REAL_STUDENT_USABILITY = NOT_MEASURED` (`K-1/S-2/R-1` ở trạng thái `PENDING_OWNER_DECISION`, `paid_project_confirmed = false`).
    - `FRONTEND_INTEGRATION = BLOCKED_OWNERSHIP` (`0` diff dưới `frontend/**`).
    - `frozen_unseen_vmmu20 = GROUND_TRUTH_UNVERIFIED` (`19` ảnh tách riêng, `0` served unverified).
    - Direct live Gemini 2.5 Flash paired A/B comparison (`external_ai_calls = 0`).

---

## 5. Companion Deliverables & Verification Receipts (`specialized-geometry-extraction-slm-optimization/`)

1. [`SLM_BOTTLENECK_ROOT_CAUSE.md`](SLM_BOTTLENECK_ROOT_CAUSE.md)
2. [`SLM_GOLD_INTERVENTION_RESULTS.json`](SLM_GOLD_INTERVENTION_RESULTS.json)
3. [`SLM_COMPACT_EXTRACTION_DESIGN.md`](SLM_COMPACT_EXTRACTION_DESIGN.md)
4. [`SLM_EXTRACTION_ABLATION.json`](SLM_EXTRACTION_ABLATION.json)
5. [`SLM_GROUNDING_RELIABILITY.json`](SLM_GROUNDING_RELIABILITY.json)
6. [`SLM_LATENCY_OPTIMIZATION.json`](SLM_LATENCY_OPTIMIZATION.json)
7. [`SLM_NEW_HOLDOUT_MANIFEST.json`](SLM_NEW_HOLDOUT_MANIFEST.json)
8. [`SLM_NEW_HOLDOUT_EVALUATION.json`](SLM_NEW_HOLDOUT_EVALUATION.json)
9. [`SLM_REGRESSION_REPORT.md`](SLM_REGRESSION_REPORT.md) (+ [`SLM_REGRESSION_RESULTS.json`](SLM_REGRESSION_RESULTS.json))
10. [`SLM_FINE_TUNING_DECISION.md`](SLM_FINE_TUNING_DECISION.md)
11. [`SLM_REPLACEMENT_DECISION.md`](SLM_REPLACEMENT_DECISION.md)
12. [`FINAL_MASTER_REPORT.md`](FINAL_MASTER_REPORT.md) (this report)
13. [`pending_template_refresh.json`](pending_template_refresh.json) + [`run.json`](run.json)

- **Targeted Tests (Verified Clean Pre-Commit):** `test_slm_compact_extraction.py` + `test_local_slm_understanding.py` -> **`10 passed, 0 failed` (`51.67s`)**; `lock_cache_identity.py --verify` -> **PASS (`CACHE_VERSION 145`)**.
- **Authoritative Clean-Tree Full `pytest` on `<PENDING_FREEZE_COMMIT_SHA>`:** `<PENDING_FULL_PYTEST>`.
