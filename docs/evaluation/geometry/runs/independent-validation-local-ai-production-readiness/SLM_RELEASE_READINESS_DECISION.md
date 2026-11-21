# AXO HYBRID /8 — SLM Release Readiness Decision (`SLM_RELEASE_READINESS_DECISION.md`)

> **Final `/8` Readiness Verdict:** **`EXPERIMENTAL_LOCAL` (Level 1 — Research & Scoped Opt-In Candidate Only)**  
> **Production Default Preserved:** **`HYBRID_ROUTE_MODE = "live"`** (`Gemini 2.5 Flash` remains default; **NO** promotion of `local-slm` to production default)  
> **Evaluated Candidate:** Frozen `/7` candidate `6310113f2202bc3a4919406b26fad08cb09b38c9` (`measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `123` files, `CACHE_VERSION = 145`) + `/8` test commit `6ca84e5367f7dd2e21f58978ef8d4c196c7959cb`  
> **Pin & Instant Rollback Status:** `qwen3-0.6b-axo-v7-q4_k_m` (`sha256: 36e784d1...`) remains opt-in (`HYBRID_ROUTE_MODE=local-slm`), with zero-code rollback to `qwen3-0.6b-q4_k_m` (`sha256: ac2d9771...`).

---

## 1. Decision Calibration Across `/7` -> `/8` (`/8 §17` Scale)

In AXO HYBRID /7, `Qwen3-0.6B-AxoV7-Q4_K_M` earned `READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS` based on in-distribution single-shot performance (`69/80` raw / `74/80 = 92.50%` corrected on `SLM_V7_HOLDOUT_112`) and `n=30` warm host timing (`p95 = 4,870.26 ms`).

In AXO HYBRID /8, independent stress testing across unseen out-of-distribution phrasings (`C60_BLIND_NLU` + `EXTERNAL17`), a larger `n=100` multi-tier CPU stress run, and strict anti-fabrication accounting **calibrates the overall readiness classification downward to `EXPERIMENTAL_LOCAL` (Level 1)** for general natural-language usage, while documenting a **strictly scoped opt-in envelope** (`VALIDATED_LOCAL_PRIMARY` canonical/textbook Vietnamese geometry on `>= 8 GiB` RAM single-user machines):

| Level (Per `/8 §17`) | Criterion | Observed `/8` Evidence | Met? |
|---|---|---|---|
| **Mandatory Safety Invariants** *(Required for any local mode)* | `0` wrong-served answers (`0` Mode-A bypasses), `0` Scene3D continuity errors, `0` internal token leaks, `0` baseline regressions, `16/16` security/fault checks, fail-closed `Source Gate` + `Exact Kernel /24` | `0` wrong-served across `SLM_V7_HOLDOUT_112` (`axo-math-evaluator/2`), `NH48`, `HOLDOUT_40`, `DEV16`, `REAL27`, `NC`, `RM72`, `S2_36`, `COMP112` (`0` new), and **`0/77` wrong-served on `C60 + External17`**; `18/18` unseen neg/OOS safely refused; `16/16` security checks PASS; `15,026` backend pytest (`0` failed) | **PASS (`100%`)** |
| **Level 1 (`EXPERIMENTAL_LOCAL`)** | Works cleanly on curated test suites, enforces hard safety gates, yet lacks external real-world validation, unseen conversational generalization, or physical low-end hardware proof | Verified `74/80 (92.50%)` on `V7H_112` and `12/12 (100%)` on `EXTERNAL17`, `973.29 MiB` peak WS, **`0` safety violations**, while `C60_BLIND_NLU = 13/42 (30.95%)`, `INDEPENDENT_EXTERNAL_CORPUS = BLOCKED_DATA_ACCESS`, `PHYSICAL_LOW_END = NOT_MEASURED`, `REAL_STUDENT_USABILITY = NOT_MEASURED` | **SELECTED VERDICT** |
| **Level 2 (`READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS`)** | Registered accuracy threshold (`>= 65%`) verified across valid unseen cohorts + well-defined scope + verified performance inside deployment envelope | **FAILS ON OPEN PHRASING:** Overall unseen permissible corpus is **`25/54 (46.30%)`** (`C60_BLIND_NLU = 13/42 = 30.95%`, `C -> D: +0 / -0`), external 100–150 student/teacher cohort is **`BLOCKED_DATA_ACCESS`**, and physical 4–6 GiB hardware is **`NOT_MEASURED`**. (Met *only* within canonical textbook wording `External17 = 12/12`, `V7H_112 = 74/80` on `>= 8 GiB` host!) | **NOT MET GENERALLY** |
| **Level 3 (`READY_FOR_GEMINI_DEFAULT_REPLACEMENT_REVIEW`)** | Strong OOD & human generalization (`>= 85%`), warm uncached `p95 <= 5,000 ms`, `GEMINI_PARITY` verified, `PHYSICAL_LOW_END` verified, `INDEPENDENT_H1_VALIDATION`, `REAL_STUDENT_USABILITY`, `SOURCE_GATE_OWNER_HANDOFF` | **FAILED / BLOCKED ON MULTIPLE GATES:** `n=100` mixed warm uncached `p95 = 6,898.88 ms` (`> 5,000 ms`), `C60 = 30.95%`, `GEMINI_PARITY = NOT_MEASURED`, `PHYSICAL_LOW_END = NOT_MEASURED`, `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`, `REAL_STUDENT_USABILITY = NOT_MEASURED`, `SOURCE_GATE_OWNER_HANDOFF = BLOCKED_OWNERSHIP`, derived sections & curved/multi-solid unsupported | **WITHHELD** |

---

## 2. Quantified Evidence Behind Withholding Level 2 (General) and Level 3

1. **Template Memorization vs. True Linguistic Generalization (`P3`, `VERIFIED`):**
   - On `SLM_V7_HOLDOUT_112` (synthetic 8-stratum problems adhering to structured training-style Vietnamese geometry sentences), fine-tuning lifted `Config C -> Config D` by **`+16` cases (`72.50% -> 92.50%`, `p = 3.1e-05`)**.
   - On `C60_BLIND_NLU` (blind-authored independent conversational phrasings with unitless lengths `"cạnh 2"`, casual questions `"bằng mấy?"`, `Tứ diện OABC`, right trapezoid, obtuse parallelogram, multi-request prompts), **`Config D` scored `13/42 (30.95%)`** — identical to un-finetuned `Config C` (`13/42`, **`0 gained / 0 lost, McNemar p = 1.0`**) and only `+1` above deterministic `Config A` (`12/42`, `c60_L14`), while Source Gate rejections of SLM proposals doubled from `6` (`Config C`) to `12` (`Config D`).
   - Fine-tuning `0.6B` with `342` curated examples improved **in-template precision**, NOT broad open-ended Vietnamese NLU.
2. **Real `P2` Failure Root Cause Attribution (`VERIFIED`):**
   - `v7h_p8_01..05` (`5/6` `/7` misses) were proven to be **`MODEL_SEMANTIC_ERROR`s** (`AxoV7` omitted `rect(<base>)` whenever reordered `"Biết <base> là hình chữ nhật"` lacked `"đáy"`), NOT a `Source Gate` conversational-prefix defect (`Gold` `SERVED 5/5`, and adding `"đáy"` alone made `AxoV7` serve).
   - `slm_h23_ocr_extra_spaces` (`HOLDOUT_40`) is a **confirmed checkpoint over-conservatism regression** (`Config C SERVED a³√3`, `Config D` emitted `u=[missing]` -> `REFUSED`).
3. **Mixed-Complexity CPU Tail Latency (`P4`, `VERIFIED`):**
   - While short single-clause prompts finish quickly (`p95 = 1,961.88 ms`) and combined backend+SLM RAM stays compact (`973.29 MiB <= 2,048 MiB`, `0` leak over `n=100`), real multi-clause problems push mixed `n=100` warm uncached `p95` to **`6,898.88 ms`** (`> 5,000 ms`), and `c=2`/`c=4` concurrent requests serialize to `9,721.52 ms` / `18,580.68 ms` `p95`.
4. **Unmeasured / Blocked External & Human Gates:**
   - `INDEPENDENT_EXTERNAL_CORPUS = BLOCKED_DATA_ACCESS`
   - `PHYSICAL_LOW_END = NOT_MEASURED` (`4 GiB` analytically unsafe under Win11 + Chromium + `0.97 GiB` SLM)
   - `GEMINI_PARITY = NOT_MEASURED` (`external_ai_calls = 0`)
   - `REAL_STUDENT_USABILITY = NOT_MEASURED`
   - `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (`sealed_H1` unopened)
   - `SOURCE_GATE_OWNER_HANDOFF = BLOCKED_OWNERSHIP`

---

## 3. Authorized Operational Envelope Today & Exit Criteria

### Permitted Usage Today (`HYBRID_ROUTE_MODE = "local-slm"` Opt-In Only)
- Allowed as an **opt-in offline / laboratory experimental route** on **`>= 8 GiB` RAM, single-user** machines with **canonical / textbook single-solid polyhedron problems** (`External17 = 12/12`, `SLM_V7_HOLDOUT_112 = 74/80`, `0` wrong-served).
- Must keep `HYBRID_ROUTE_MODE = "live"` untouched as production default.
- Must enforce the 6 scoped fail-closed routing checks (never promote derived sections, curved solids, `goal_plane_plane_angle`, `Experimental` reordered base phrasings without `"đáy"`, or low-end 4–6 GiB deployments silently).

### Concrete Exit Criteria to Upgrade Decision Beyond `EXPERIMENTAL_LOCAL`
1. **To `READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS` (General Unseen Level 2):**
   - Acquire & evaluate a real 100–150 external student/teacher corpus (`>= 65%` positive accuracy with `0` wrong-served, including casual phrasing & unitless dimensions) after targeted diverse LoRA + `slm-verified-normalizer/2` unitless/colloquial hardening.
   - Measure physical 6 GiB (and verify min-spec RAM floor = `6 GiB` or `8 GiB`) end-to-end with browser + OCR active (`PHYSICAL_LOW_END`).
   - Run an ethics-approved real student/teacher pilot (`>= 85%` refusal comprehension).
2. **To `READY_FOR_GEMINI_DEFAULT_REPLACEMENT_REVIEW` (Level 3):**
   - Achieve `>= 85%` on unseen external corpus, `<= 5,000 ms` `p95` across all complexity tiers, full `GEMINI_PARITY` head-to-head execution on `Strata 1–5`, resolved `SOURCE_GATE_OWNER_HANDOFF`, derived-section coverage (or explicit hybrid escalation router), and `INDEPENDENT_H1_VALIDATION` PASS.
