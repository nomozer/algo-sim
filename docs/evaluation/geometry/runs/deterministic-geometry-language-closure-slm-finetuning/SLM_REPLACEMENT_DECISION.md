# AXO HYBRID /7 — SLM Replacement Decision (`SLM_REPLACEMENT_DECISION.md`)

> **Verdict:** **`READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS`**  
> **Production Default Preserved:** `HYBRID_ROUTE_MODE = "live"` (Gemini 2.5 Flash remains default; `local-slm` remains explicit opt-in pending `GEMINI_PARITY`, `PHYSICAL_LOW_END`, `INDEPENDENT_H1_VALIDATION`, and Source Gate owner sign-off).  
> **Campaign:** `deterministic-geometry-language-closure-slm-finetuning` (AXO HYBRID /7)  
> **Frozen Product Commit (Commit 1):** `6310113f2202bc3a4919406b26fad08cb09b38c9` (`measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `123` files, `CACHE_VERSION = 145`)  
> **External AI Calls:** `0` (`ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`)

---

## 1. Pre-Registered Criteria Evaluation (Single-Shot `SLM_V7_HOLDOUT_112`)

Evaluated strictly on the frozen single-shot blind holdout [`SLM_V7_HOLDOUT_112`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_MANIFEST.json) (`80+ / 32-`, `0` exact/skeleton overlaps with train/val or any historical benchmark, `max_4gram = 0.3396`, `sealed_H1_unopened = true`, `locked_W2_W3_unopened = true`), [`SLM_V7_PERFORMANCE.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_PERFORMANCE.json), and [`SLM_V7_REGRESSION_RESULTS.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_REGRESSION_RESULTS.json).

### Evaluator Grader Disclosure (`v7h_p7_06`–`10` `cos²=` Format)

In [`SLM_V7_HOLDOUT_EVALUATION.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_EVALUATION.json) (`single_shot: true`, kept byte-immutable), `v7h_p7_06` through `v7h_p7_10` returned `SERVED` with exact answer strings matching the manifest oracle identically across **all four** configurations (`Config A`, `Config B`, `Config C`, `Config D`):

| Case | Config A / B / C / D `answer` | Manifest `oracle` | `EVI.same_value` Return | Audited Exact Match |
|---|---|---|---|---|
| `v7h_p7_06` | `cos²=2/3` | `cos²=2/3` | `None` (unparsed `cos²=` prefix) | Exact string match (`wrong_served = False`) |
| `v7h_p7_07` | `cos²=1/2` | `cos²=1/2` | `None` (unparsed `cos²=` prefix) | Exact string match (`wrong_served = False`) |
| `v7h_p7_08` | `cos²=2/5` | `cos²=2/5` | `None` (unparsed `cos²=` prefix) | Exact string match (`wrong_served = False`) |
| `v7h_p7_09` | `cos²=2/3` | `cos²=2/3` | `None` (unparsed `cos²=` prefix) | Exact string match (`wrong_served = False`) |
| `v7h_p7_10` | `cos²=2/3` | `cos²=2/3` | `None` (unparsed `cos²=` prefix) | Exact string match (`wrong_served = False`) |

Because all four configs produced the identical `cos²=...` exact strings on all five items, paired deltas (`B -> C`, `C -> D`, `A -> D`), Cohen's `h`, and McNemar exact `p`-values are invariant.

### Comparison Matrix on Blind Single-Shot `SLM_V7_HOLDOUT_112`

| Metric | Config A (`det_v145`) | Config B (`/6 + Orig Q4_K_M`) | Config C (`/7 + Orig Q4_K_M`) | Config D (`/7 + AxoV7 Q4_K_M`) |
|---|---:|---:|---:|---:|
| Raw Evaluator Positives (`EVI.same_value`) | `34/80` (`42.50%`) | `42/80` (`52.50%`) | `53/80` (`66.25%`) | `69/80` (`86.25%`, 95% CI `[77.03%, 92.15%]`) |
| **Audited Exact Math Positives** (`cos²=` string-verified) | **`39/80` (`48.75%`)** | **`47/80` (`58.75%`)** | **`58/80` (`72.50%`)** | **`74/80` (`92.50%`)** |
| Negatives Safely Refused (`32` total) | `32/32` (`100.0%`) | `32/32` (`100.0%`) | `32/32` (`100.0%`) | `32/32` (`100.0%`) |
| True Wrong-Served / Mode-A Leaks | `0/80` (`5` grader `cos²=`) | `0/80` (`5` grader `cos²=`) | `0/80` (`5` grader `cos²=`) | `0/80` (`5` grader `cos²=`) |
| Scene3D Continuity Errors | `0` | `0` | `0` | `0` |
| SLM Inference Latency (`t=6`, holdout `p50` / `p95` ms) | `n/a` | `4908.91 / 7111.78` | `5380.58 / 8779.58` | **`3727.57 / 4728.25`** |
| End-to-End Holdout Latency (`p50` / `p95` ms) | `10.56 / 67.47` | `3809.89 / 7126.19` | `4061.46 / 8743.80` | **`1846.59 / 4708.34`** |

### Hypothesis Isolation (`H1` and `H2`)

- **Hypothesis `H1` (`Config B -> Config C`, deterministic upstream closure):**
  `+11` gained / `0` regressed (`+13.75 pp`, Cohen's `h = 0.2810`, exact two-sided McNemar `p = 0.000977`).
  Rescued `v7h_p1_04/06/07/08` (regular pyramid/tetrahedron surface forms), `v7h_p4_06..10` (`right_iso_tri` + `face_perp`), and `v7h_p8_07/08` (`v7` conversational/connector closure).
- **Hypothesis `H2` (`Config C -> Config D`, targeted `Qwen3-0.6B` LoRA fine-tuning):**
  `+16` gained / `0` regressed (`+20.00 pp`, Cohen's `h = 0.4800`, exact two-sided McNemar `p = 0.000031`).
  Rescued multi-constraint rectangle/square pyramids (`v7h_p2_01/03/05/07/08/09`), parallelogram & isosceles trapezoid pyramids (`v7h_p3_05/06/07`), prism/cuboid multi-dimension & midpoint/orthoproj (`v7h_p1_09`, `v7h_p5_06/08/10`), and reordered conversational inputs (`v7h_p8_06/09/10`).
- **Cumulative Local Gain (`Config A -> Config D`):**
  `+35` gained / `0` regressed (`+43.75 pp`, Cohen's `h = 0.9616`, exact two-sided McNemar `p = 0.0`).

---

## 2. Gate-by-Gate Evaluation Against Pre-Registered Levels

| Criterion | Threshold | Observed (`/7` Config D) | Status |
|---|---|---|---|
| **Mandatory Safety Invariants** | `0` new Mode-A leaks, `0` Scene3D continuity errors, `0` regressions on deterministic baseline, `0` external AI calls, `0` holdout overlaps, `14/14` fault checks | `0` new Mode-A leaks (`11` baseline suites + holdout), `0` continuity errors, `0` regressions (`REAL27`, `NC`, `AUTONEG`, `RM72`, `DEV37`, `PROBES39`, `S2_36`, `COMP112`), `0` external AI calls, `0` overlaps, `14/14` faults PASS, `23/23` SLM pytests PASS | **PASS** |
| **Mức 2 (`READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS`)** | Holdout positive `>= 65%`, negative `100%`, warm `p95 <= 12000 ms`, RSS `<= 2048 MiB` | `86.25%` raw (`92.50%` audited) `>= 65%`; `32/32 = 100%` neg; warm `p95 = 4870.26 ms` (`6T`) / `5297.99 ms` (`4T`) / `4519.61 ms` (`8T`); warm peak RSS `1043.19 MiB` (`cold 1040.63 MiB`, holdout `1044.43 MiB`) | **PASS** |
| **Mức 3 Accuracy / Latency / RAM** | Holdout `>= 85%`, warm `p95 <= 5000 ms`, RSS `<= 2048 MiB` | `86.25%` raw (`92.50%` audited); `6T` warm `p95 = 4870.26 ms`, `8T = 4519.61 ms`, holdout `p95 = 4728.25 ms` (note `4T = 5297.99 ms` > 5000 ms, cold `p50 = 6217.99 ms`); RSS `<= 1044.43 MiB` | **PASS AT `6T`/`8T` HOST** |
| **Mức 3 Gemini Parity & Deployment Gates** | Live Gemini comparison, derived plane/section/multi-solid parity, low-end 4–6 GB device check, independent H-1, Source Gate ownership | `GEMINI_PARITY = NOT_MEASURED` · `PHYSICAL_LOW_END = NOT_MEASURED` · `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` · `REAL_STUDENT_USABILITY = NOT_MEASURED` · `SOURCE_GATE_OWNER_HANDOFF = BLOCKED_OWNERSHIP` | **BLOCKED / NOT_MEASURED** |

---

## 3. Why `READY_TO_REPLACE_GEMINI_DEFAULT` Is Explicitly Withheld

Although `Config D` clears all Mức 2 gates and reaches `86.25%` raw (`92.50%` audited) on the 8-stratum single-shot blind holdout with `4870.26 ms` warm `p95` at 6 threads:

1. **`GEMINI_PARITY = NOT_MEASURED`:** No live Gemini calls were executed (`ALLOW_LIVE_AI = 0`); head-to-head equivalence on arbitrary natural language, derived cross-sections, intersection lines, spheres, and multi-solid configurations has not been measured.
2. **`PHYSICAL_LOW_END = NOT_MEASURED`:** Benchmarks ran on a 15.78 GiB Windows development host (`AMD64`, 12 logical CPUs); cold-start (`909.96 ms` load + `5085.65 ms` first inference) and `1044 MiB` combined RSS have not yet been verified under memory pressure on physical 4–6 GiB RAM laptops.
3. **`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`:** Sealed `H-1` and locked `W2/W3` remain unopened (`0` rows read).
4. **Remaining 6 Unserved Holdout Positives in `Config D`:**
   - `v7h_p8_01..05` (`5` cases): conversational preambles (`"Thưa thầy, nhờ giải bài: "`, `"Đề thi thử: "`, etc.) cause `SOURCE_PREMISE_UNREAD` inside unmodified `Registry /33` (`registry.py`) because `SOURCE_GATE` does not strip conversational wrappers (awaiting owner approval in [`SOURCE_GATE_OWNER_HANDOFF.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SOURCE_GATE_OWNER_HANDOFF.md)).
   - `v7h_p5_09`: one remaining `SOURCE_OBJECT_MISMATCH` (`Config D` prediction rejected cleanly by `Source Gate`, `0` wrong-served).
5. **Derived Sections & Multi-Solid Scope Constraint:** `/7` fine-tuning targeted `slm-compact-clause/1` single-solid polyhedral extraction (`pyramids`, `prisms`, `tetrahedra`, `cuboids/cubes`, `orthogonal projections`, `centroids`, `midpoints`, `divide ratios`, `angles`, `distances`). Cross-section (`sec`), intersection line (`inter`), and sphere circumscription (`sphere`) relations remain outside the fine-tuned SLM's validated primary guarantee.

---

## 4. Operational Recommendation & Next Steps

- Keep **`HYBRID_ROUTE_MODE = "live"`** untouched as production default.
- Pin **`qwen3-0.6b-axo-v7-q4_k_m`** (`sha256: 36e784d135627225e0b9c11b097c9a36222ee1e0e3f6f1d6116cc3060ac5e148`, `396,704,736` bytes) as the default model for opt-in `HYBRID_ROUTE_MODE = "local-slm"` (`threads=6` or `8`), with instant zero-code rollback via `AXO_LOCAL_SLM_MODEL=qwen3-0.6b-q4_k_m` (`ac2d9771...`).
- **Owner-gated prerequisites before promoting `local-slm` to default:**
  1. Owner review & approval of [`SOURCE_GATE_OWNER_HANDOFF.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SOURCE_GATE_OWNER_HANDOFF.md) (including conversational prefix handling in `registry.py`).
  2. Physical 4–6 GiB RAM device CPU verification (`PHYSICAL_LOW_END`).
  3. Authorized head-to-head live Gemini parity check (`GEMINI_PARITY`) and sealed `H-1` validation (`K-1` / `S-2` / `R-1` currently `PENDING_OWNER_DECISION`, `paid_project_confirmed: false`).
