# AXO HYBRID /8 — FINAL MASTER REPORT: Independent Validation & Local AI Production Readiness

> **Run ID:** `independent-validation-local-ai-production-readiness`  
> **Campaign:** AXO HYBRID /8 — Independent Validation & Local AI Production Readiness  
> **Worktree & Branch:** `feat/local-first-geometry-understanding`  
> **Audited Product Candidate (Unmodified):** `6310113f2202bc3a4919406b26fad08cb09b38c9` (frozen in `9a9352d586caa360f82052ba1b76fe9b4227f26c`, `measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `123` files, `CACHE_VERSION = 145`, `HYBRID_ROUTE_MODE = "live"` default)  
> **`/8` Evaluation & Verification Code Commit:** `6ca84e5367f7dd2e21f58978ef8d4c196c7959cb` (`0` edits to `backend/app/**`, `frontend/**`, or frozen `/5–/7` evidence)  
> **Final `/8` Readiness Verdict:** **`EXPERIMENTAL_LOCAL` (Level 1)** (`HYBRID_ROUTE_MODE = "live"` preserved; **`READY_FOR_GEMINI_DEFAULT_REPLACEMENT_REVIEW` WITHHELD**) · **External AI Calls:** `0` (`ALLOW_LIVE_AI = "0"`)

---

## 1. Gate Summary (`D0–D10`) & Evidence Epistemic Tags

Every claim in this report uses explicit tags: **`VERIFIED`** (measured directly via executed code/tool output in `/8`), **`INFERRED`** (analytical deduction bounded by verified measurements), **`HYPOTHESIS`** (proposed causal mechanism), **`NOT_MEASURED`**, or **`BLOCKED`**.

| Gate | Description | Final Status | Primary Artifact / Evidence |
|---|---|---|---|
| **D0** | Baseline Integrity, Git/Candidate/Cache/GGUF & Frozen Run Verification | **`PASS` (`VERIFIED`)** | [`BASELINE_INTEGRITY_REPORT.md`](BASELINE_INTEGRITY_REPORT.md) |
| **D1** | Evaluator Correction (`axo-math-evaluator/2`) & Historical `/5–/7` Reconciliation | **`PASS` (`VERIFIED`)** | [`EVALUATOR_CORRECTION_REPORT.md`](EVALUATOR_CORRECTION_REPORT.md) · [`EVALUATOR_RECONCILIATION.json`](EVALUATOR_RECONCILIATION.json) |
| **D2** | Deep Failure Case Audit (`v7h_p8_01..05`, `p5_09`, `slm_h23`) & Capability Matrix (`26` categories) | **`PASS` (`VERIFIED`)** | [`SLM_FAILURE_CASE_AUDIT.md`](SLM_FAILURE_CASE_AUDIT.md) · [`SLM_CAPABILITY_MATRIX.json`](SLM_CAPABILITY_MATRIX.json) |
| **D3** | Independent External Corpus vs. Permissible Unseen Zero-Leakage Corpus (`77` items) | **`BLOCKED_EXTERNAL` / `PASS_PERMISSIBLE_UNSEEN`** | [`INDEPENDENT_DATASET_PROTOCOL.md`](INDEPENDENT_DATASET_PROTOCOL.md) · [`PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json`](PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json) |
| **D4** | System Resource (`n=100` stability, Win32 RAM, Concurrency `c=1,2,4,6`, `threads=2`) & Low-End Check | **`PASS_HOST` / `PHYSICAL_LOW_END = NOT_MEASURED`** | [`RESOURCE_READINESS_REPORT.md`](RESOURCE_READINESS_REPORT.md) · [`SYSTEM_RESOURCE_AND_CONCURRENCY_BENCHMARK.json`](SYSTEM_RESOURCE_AND_CONCURRENCY_BENCHMARK.json) |
| **D5** | Source Gate Ownership Boundaries & Adversarial Safety Boundary Suite | **`BLOCKED_OWNERSHIP`** (`8/8` tests pass) | [`SOURCE_GATE_OWNER_STATUS.md`](SOURCE_GATE_OWNER_STATUS.md) · [`test_source_gate_handoff_boundaries.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_source_gate_handoff_boundaries.py) |
| **D6** | Head-to-Head Live Gemini Parity & Non-Parity Historical Replay Diagnostic | **`NOT_MEASURED`** (`external_ai_calls = 0`) | [`GEMINI_PARITY_PROTOCOL.md`](GEMINI_PARITY_PROTOCOL.md) |
| **D7** | Real Student Pilot Protocol & Sealed `H-1` Governance | **`NOT_MEASURED`** (`sealed_H1` unopened) | [`REAL_STUDENT_PILOT_PROTOCOL.md`](REAL_STUDENT_PILOT_PROTOCOL.md) |
| **D8** | Scoped Local Routing Simulator & Comprehensive Baseline Regressions | **`PASS` (`VERIFIED`)** | [`LOCAL_ROUTING_READINESS.md`](LOCAL_ROUTING_READINESS.md) · [`SLM_V8_REGRESSION_REPORT.md`](SLM_V8_REGRESSION_REPORT.md) |
| **D9** | `16/16` Security/Fault Checks & Clean-Tree Full Backend Pytest (`15,026` passed, `0` failed) | **`PASS` (`VERIFIED`)** | [`SLM_V8_REGRESSION_RESULTS.json`](SLM_V8_REGRESSION_RESULTS.json) |
| **D10** | Release Readiness Verdict (`EXPERIMENTAL_LOCAL` / `Level 1`) & Governance Checks | **`PASS` (`VERIFIED`)** | [`SLM_RELEASE_READINESS_DECISION.md`](SLM_RELEASE_READINESS_DECISION.md) |

---

## 2. Executive Synthesis of `/8` Empirical Corrections to `/7` (`VERIFIED`)

1. **`cos²=` Evaluator Fix Confirmed (`69/80 -> 74/80 = 92.50%` on `SLM_V7_HOLDOUT_112`):** `evaluate_images.py:85-91` failed whenever both `answer` and `oracle` carried `"cos²=..."` (requiring the oracle to end in `"N°"`), while `nl_eval_scoring.py:58` conflated trig kinds by stripping `"^cos²="` blindly. `axo-math-evaluator/2` (`slm_math_evaluator_v2.py`, `56/56` unit tests) eliminates all 5 false errors across `Config A..D` (`39 -> 47 -> 58 -> 74 / 80`, **`0` true wrong-served across `/5–/8`**) and reconciles `> 900` historical rows with `0` hidden format bugs elsewhere.
2. **All 6 Remaining `/7` Positive Misses Are `MODEL_SEMANTIC_ERROR`, NOT a `Source Gate` Bug:** Live 13-field traces + Gold `compact_clause` interventions prove `v7h_p8_01..05` **all SERVE (`5/5`) natively with conversational prefixes present** once `rect(<base>)` is emitted — `AxoV7` omitted `rect(<base>)` solely when reordered `"Biết <base> là hình chữ nhật"` lacked the cue word `"đáy"`. `v7h_p5_09` was a genuine `AxoV7` argument swap `proj(pt="G", a="R", b="RST")` caught faithfully by `Source Gate`.
3. **Identified Model Checkpoint Over-Conservatism (`slm_h23_ocr_extra_spaces`):** `AxoV7` regressed vs base `Qwen3-0.6B-Q4_K_M` on short equilateral `S.ABC` + `SA ⊥ (ABC)` prompts (`Config C SERVED a³√3`, `Config D` emitted `u=[missing]` -> `AMBIGUOUS_FACT`), verified across clean and OCR-spaced probes (`0` unsafe impact).
4. **Severe OOD Linguistic Generalization Gap Revealed (`92.50% -> 30.95%` on `C60_BLIND_NLU`):** While `AxoV7` achieved `100%` (`12/12` + `5/5` OOS) on standard Vietnamese exam scans (`EXTERNAL17`), on unseen blind-authored natural conversational paraphrases (`C60_BLIND_NLU`) it scored **`13/42 (30.95%)`** (`+0 / -0` vs un-finetuned `Config C`, `p = 1.0`) with doubled Source Gate rejections (`6 -> 12`), proving `/7`'s fine-tuning captured template distribution rather than general Vietnamese paraphrasing — while safety held at **`0` wrong-served / `18/18` safe refusals**.
5. **Mixed-Complexity Warm Latency Exceeds `5.0 s` Tail Target (`p95 = 6,898.88 ms` over `n=100`):** While combined Working Set stays compact (`973.29 MiB <= 2,048 MiB`, `0` memory leak across `Q1 -> Q4`) and short single-clause prompts hit `p95 = 1,961.88 ms`, medium/long multi-clause prompts push mixed `n=100` warm uncached `p95` to `6,898.88 ms`, failing Level 3's `<= 5,000 ms` bar.

---

## 3. Direct Answers to All 18 Mandatory Validation Questions (`Q1–Q18`)

- **Q1. Has the `/7` evaluator bug (`v7h_p7_06..10` and math equivalence) been fixed without breaking mathematical soundness?**
  **Yes (`VERIFIED`).** Implemented exact typed `axo-math-evaluator/2` ([`slm_math_evaluator_v2.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/scripts/slm_math_evaluator_v2.py)) without mutating frozen `evaluate_images.py`; `56/56` adversarial & equivalence unit tests pass (`cos(x)`/`cos²(x)`/`cos(2x)` strictly separated, scalar vs trig distinguished, out-of-domain rejected, zero float probing).
- **Q2. What are the true corrected `/7` scores on `SLM_V7_HOLDOUT_112` (`Config A..D`) and how many true wrong-served errors exist?**
  **`Config A: 39/80 (48.75%)`, `Config B: 47/80 (58.75%)`, `Config C: 58/80 (72.50%)`, `Config D: 74/80 (92.50%, CI [84.59%, 96.52%])`, `32/32` negatives refused (`VERIFIED`).** True wrong-served errors under `axo-math-evaluator/2`: **`0`** across all 4 configs (`C -> D: +16 / -0, McNemar p = 3.1e-05`). Zero hidden discrepancies found in `/5`, `/6`, or `SLM_V7_ABLATION`.
- **Q3. Why did `v7h_p8_01..05` fail — conversational wrappers, `Source Gate`, `slm-verified-normalizer/2`, or `AxoV7` omission?**
  **`MODEL_SEMANTIC_ERROR` (`AxoV7` omission) (`VERIFIED`).** Whenever reordered `"Biết <base> là hình chữ nhật"` lacked `"đáy"`, `AxoV7` omitted `rect(<base>)`. Siblings `v7h_p8_06..10` with the same 5 conversational prefixes served (`5/5`), Gold `compact_clause` on `v7h_p8_01..05` served (`5/5`) cleanly through untouched `Source Gate`, and adding `"đáy"` alone caused `AxoV7` to extract `rect` and `SERVE`. Normalizer also rewrote `"Thưa thầy," -> "Cho"` on `p8_01`, but did not prevent Gold serving.
- **Q4. Why did `v7h_p5_09` fail?**
  **`MODEL_SEMANTIC_ERROR` (`VERIFIED`).** `AxoV7` swapped projection arguments (`proj(pt="G", a="R", b="RST")` + spurious `perp_lp("RS","RST")`), which `Source Gate` (`_C_CHIEU`) faithfully blocked with `SOURCE_OBJECT_MISMATCH` (`Gold SERVED 8a³√3`).
- **Q5. Is `slm_h23_ocr_extra_spaces` (`HOLDOUT_40` `25/28 -> 24/28`) a fine-tuned model regression, and what is its blast radius?**
  **Yes (`VERIFIED`).** `Config C` served `a³√3` while `AxoV7` emitted `g=[], u=[{"c":0,"k":"missing"}]` -> `REFUSED (AMBIGUOUS_FACT)`. Five `S.ABC` equilateral-base probes showed four variants (clean and OCR-spaced) trigger the same conservative `missing` tag, while `"Tính V của S.ABC."` (clean) extracted `vol` and hit `NOT_ASKED_IN_SOURCE`. Safety invariant intact (`0` wrong-served).
- **Q6. What is the exact capability matrix of `Qwen3-0.6B-AxoV7` (`VALIDATED_LOCAL_PRIMARY`, `EXPERIMENTAL`, `UNSUPPORTED`, `NOT_MEASURED`)?**
  **Measured across `140` positives + negative/baseline suites (`VERIFIED`):**
  - `VALIDATED_LOCAL_PRIMARY` (`>= 85%`, `n >= 5`, `0` wrong-served): `S.ABC` (`89.74%`), `S.ABCD` (`91.18%`), regular pyramid (`7/7`), right/regular prism (`20/20`), rectangular box (`5/5`), right/right-iso triangle (`97.06%`), equilateral/iso triangle (`94.87%`), square/rectangle base with explicit `"đáy"` (`88.68%`), rhombus/parallelogram/trapezoid (`12/12`), `perp_lp`/`face_perp` (`91.18%`), midpoint (`92.31%`), centroid (`5/5`), segment ratio (`5/5`), point-plane distance (`86.49%`), skew distance (`7/7`), line-plane angle (`5/5`), plane-plane premise (`19/19`), volume/area (`93.98%`).
  - `EXPERIMENTAL`: cube (`2/2`, `n < 5`), regular tetrahedron (`3/3`, `n < 5`), parallel relations (`3/3`, `n < 5`), orthogonal projection (`7/9 = 77.78%`), conversational + reordered rect without `"đáy"` (`5/10 = 50%`).
  - `NOT_MEASURED`: `goal_plane_plane_angle` (`0/0` in holdouts).
  - `UNSUPPORTED`: complex derived cross-sections (`sec`), multi-step intersections (`inter`), spheres/cones/cylinders, multi-solid compositions, non-Registry dynamic/extrema constructions.
- **Q7. Did we obtain and test a brand-new 100–150 external real-world student/teacher corpus?**
  **`BLOCKED_DATA_ACCESS` (`BLOCKED`).** No external real-world 100–150 problem dataset is present in the offline workspace, and agent-synthetic problems were strictly excluded (`INDEPENDENT_HOLDOUT_*` omitted). Instead, we executed a zero-leakage single-shot run on **`77` permissible unseen non-sealed repository items** (`C60_BLIND_NLU` `60` + `EXTERNAL17` `17`, `0` exact overlaps, `max_4gram = 0.1505` vs `/7` train+val).
- **Q8. How did `AxoV7` perform on unseen permissible phrasing (`C60_BLIND_NLU` + `EXTERNAL17`)?**
  **Sharp OOD drop on `C60`, `100%` on `EXTERNAL17`, `0` wrong-served overall (`VERIFIED`):**
  - `EXTERNAL17`: `Config D = 12/12 (100%)` positive + `5/5` safe OOS refusal (`Config A` also `12/12`).
  - `C60_BLIND_NLU`: `Config A = 12/42 (28.57%)`, `Config B/C/D = 13/42 (30.95%)`, `13/13` negatives refused, **`0` wrong-served** (`C -> D: +0 / -0, McNemar p = 1.0`, `A -> D: +1 c60_L14`, `Predicate F1 = 0.6698`, `Arg F1 = 0.4205`, Source Gate rejections `6 -> 12`). Combined: **`25/54 (46.30%)`**, **`18/18` neg/OOS refused**, **`0` wrong-served**.
- **Q9. What fails on unseen phrasing?**
  **Five verified buckets (`29` misses on `C60_BLIND_NLU`, `VERIFIED`):** unitless length tokens & quote-span mismatches (`6 UNGROUNDED_VALUE` + `1 AMBIGUOUS_VALUE_QUOTE` + `6 SOURCE_OBJECT_MISMATCH`), OOD geometry forms (`Tứ diện OABC`, `góc BAD = 135°`, right trapezoid, `"Tính cos²..."`: `3 INCONSISTENT_FACTS` + `2 NOT_ASKED_IN_SOURCE` + `1 BRIDGE_UNSUPPORTED_MEASUREMENT`), casual `"bằng mấy?"`/conditional questions (`4 AMBIGUOUS_FACT`), strict multi-request sub-goal drops (`2 REQUEST_NOT_ANSWERED`), and stateful UI prompts (`3 gate_out_of_scope`) + `1 SOURCE_PREMISE_UNREAD`.
- **Q10. Are latency, memory, and `n=100` consecutive uncached stability production-ready?**
  **Memory YES (`973.29 MiB <= 2,048 MiB`, `0` leak); Latency/Concurrency NO for general Level 3 (`VERIFIED`):** Over `n=100` mixed (`short/medium/long`) warm uncached calls (`threads=6`), `e2e p50/p95/max = 3,630.08 / 6,898.88 / 8,708.64 ms` (**fails `<= 5,000 ms`**, though short tier hits `p95 = 1,961.88 ms`), `Q1 -> Q4` WS drift `< 2 MiB`, `c=2 p95 = 9,721.52 ms`, `c=4 p95 = 18,580.68 ms`, `c=6 max_queue=2` cleanly rejects overflow (`ok=2, busy=4, recovery_ok=True`). Fast path (`n=30`) `p50/p95 = 51.50 / 72.65 ms`. Note `warm_cached_separate_n25_hits` read `4,315.38 ms` due to `local_slm_extractor.py:3544` bypassing cache when `runtime is not None` (`/7` verified singleton cache `36.45 / 49.50 ms`).
- **Q11. Has performance been verified on physical 4–6 GiB low-end student laptops?**
  **`NOT_MEASURED` (`NOT_MEASURED`).** Only simulated `threads=2, ctx=1536` (`e2e p50/p95 = 5,656.77 / 6,093.38 ms` on `15.78 GiB` host) was measured. Analytically (`INFERRED`), Windows 11 + Chromium/WebGL + backend+SLM (`0.97 GiB` WS) exceeds `4 GiB` physical RAM (unsafe swap risk) and leaves tight/unverified margins on `6 GiB`.
- **Q12. What is the status of the Source Gate handoff and `registry.py`?**
  **`BLOCKED_OWNERSHIP` (`BLOCKED`, `8/8` tests pass).** `registry.py` remained completely unmodified. Adversarial boundary tests confirm native Source Gate + `slm-verified-normalizer/2` safely block conditionals, negations, ungrounded quotes, swapped projection args, and ambiguous quantifiers. Notably, `/8` proved `_lien_ket_cau` needs NO change for `v7h_p8_01..05`.
- **Q13. Is `Qwen3-0.6B-AxoV7` at parity with Gemini 2.5 Flash?**
  **`GEMINI_PARITY = NOT_MEASURED` (`NOT_MEASURED`, `external_ai_calls = 0`).** Live cloud comparison was unauthorized. Historical offline replays on `{K-1, R-1, S-2}` and `C60` ran under different schema/contract versions (`CACHE_VERSION 125–132`) and test derived sections outside `slm-compact-clause/1`; they do not validate Gemini parity.
- **Q14. What about real student usability and sealed `H-1`?**
  **`REAL_STUDENT_USABILITY = NOT_MEASURED` · `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (`NOT_MEASURED`).** Full study protocol delivered (`30–45` students, `>= 85%` refusal comprehension target); `sealed_H1` and `locked_W2_W3` remain unopened (`0` rows touched), `k1/r1/s2` remain `PENDING_OWNER_DECISION`.
- **Q15. Can a strictly scoped local routing policy operate safely with instant rollback?**
  **Yes (`VERIFIED`).** Standalone `scoped-local-routing-sim/1` (`test_scoped_local_routing_policy.py` `4/4`) enforces fast-path bypass, SHA-256 verification, zero silent cloud fallback, exclusion of `EXPERIMENTAL` / `UNSUPPORTED` / `NOT_MEASURED` domains, and instant rollback (`qwen3-0.6b-axo-v7-q4_k_m` <-> `qwen3-0.6b-q4_k_m`) with **`0` wrong-served** across `189` simulated cases (`V7H_112` + `UNSEEN_77`).
- **Q16. Did `/8` preserve zero baseline regressions, `16/16` security checks, and full backend test health?**
  **Yes (`VERIFIED`).** `0` baseline regressions across all `11` baseline suites, `0` new Mode-A leaks, `0` internal `<think>`/`compact_clause` leaks, **`16/16`** security/runtime fault tests PASS, **`91/91`** SLM & `/8` pytests PASS, and clean-tree full backend pytest **`15,026 passed, 7 skipped, 3 deselected, 12 xfailed, 0 failed in 702.93s`** on `6ca84e536`.
- **Q17. Should `HYBRID_ROUTE_MODE` switch from `"live"` to `"local-slm"` now?**
  **NO (`VERIFIED`).** Production default **MUST remain `HYBRID_ROUTE_MODE = "live"`**. Overall readiness is calibrated to **`EXPERIMENTAL_LOCAL` (`Level 1`)** due to `30.95%` OOD `C60` accuracy, `6,898.88 ms` mixed uncached `p95`, `INDEPENDENT_EXTERNAL_CORPUS = BLOCKED_DATA_ACCESS`, `PHYSICAL_LOW_END = NOT_MEASURED`, `GEMINI_PARITY = NOT_MEASURED`, and `SOURCE_GATE_OWNER_HANDOFF = BLOCKED_OWNERSHIP`. Opt-in `local-slm` is safe for canonical textbook experiments on `>= 8 GiB` hosts.
- **Q18. What is the single highest-ROI roadmap after AXO HYBRID /8?**
  1. Collect a real `100–150` student/teacher pilot corpus (`P3`/`P7` protocols) + authorize live `GEMINI_PARITY` head-to-head (`P6` protocol) and physical `6 GiB` Windows measurement (`P4`).
  2. Expand `slm-verified-normalizer` & LoRA training data specifically to unitless lengths (`"cạnh 2"`), casual interrogatives, reordered base descriptions (`"Biết ABCD là hình chữ nhật"`), and `S.ABC` equilateral non-over-conservatism (`slm_h23`), while coordinating owner approval for `SOURCE_GATE_OWNER_HANDOFF` + `validate_and_lower_compact_clause` dict-type guard.
  3. Investigate two-tier hybrid routing (`local-slm` / deterministic fast-path first for verified polyhedra, explicit user-disclosed cloud escalation only when out-of-scope or unsupported).
