# ALGOSIM — Real-World End-to-End Reliability & Hybrid Gap Closure

Run `real-world-end-to-end-reliability` · WAVE_ID `REAL_WORLD_END_TO_END_RELIABILITY` · branch `feat/local-first-geometry-understanding` (not merged, not pushed) · `ALLOW_LIVE_AI=0`, **0 live Gemini calls**.

Baseline: HEAD `8d0fde3378c9b087bdbbc4c66e1a40aad3b532cc`, product `c61a3589782bde35b69e8376d8ebf136314e47f3`, measured-system tree `69bb83ba…` (freeze `--verify` MATCH before edits). Product commit of this run and final tree hash: see [`run.json`](run.json) and `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`.

Epistemic labels: **VERIFIED FACT** (machine receipt in this directory), **INFERENCE**, **HYPOTHESIS**, **NOT_MEASURED**, **BLOCKED**.

> External17 is a **development / diagnostic** corpus: every statement was read and diagnosed by the implementing agent. Nothing here is a blind or independent H-1 result.

## 1. What changed (product)

| Layer | Change | Evidence |
|---|---|---|
| Exact Kernel `engine.py` | **Height-invariance certification**: when a pyramid/prism height is not given and every asked quantity is a whitelisted vertex-only metric goal (length; point–plane, line–line, line–plane, plane–plane distance; line–line, line–plane angle), the engine re-runs at 5 exact samples h² ∈ {1,2,3,5,7}; identical exact answers ⇒ served with `scene_configuration {unique:false, kind:HEIGHT_INVARIANT_ILLUSTRATIVE, invariance_certificate}`; otherwise the original `MISSING_DIMENSION` refusal stands | [`planner_kernel_capability_closure.json`](planner_kernel_capability_closure.json) (11/11 probes) |
| Adapter `/4` | forwards `route_d.scene_configuration` on served responses | same |
| Local parser | part-to-part ratio point "E thuộc cạnh SC sao cho SE = 3EC" → existing `point_divides_segment` (k/(k+1)); malformed part pairs fail closed | [`parser_semantic_gap_closure.json`](parser_semantic_gap_closure.json) (2/2) |
| Frontend | learner note `#stage-illustrative-note` ("hình chỉ minh họa") for non-unique scenes; analyze-stage 503 message no longer shows photo-extraction copy | [`scene3d_browser_acceptance.json`](scene3d_browser_acceptance.json) |

Proof of the invariance rule (VERIFIED FACT for the math, INFERENCE that the guards cover every served path): with t = h², vertex coordinates are t-independent and the metric is G₂ ⊕ (t), so every Gram matrix is A + t·zzᵀ and its determinant is affine in t. Each whitelisted goal² is P(t)/Q(t) with degrees ≤ 2 and Q > 0; equal values at 5 distinct t force P ≡ cQ. New registry primitives: **0**. Per-problem handlers: **0**.

## 2. External17 — before / after (ORACLE_TEXT_DOWNSTREAM_REPLAY on verbatim transcriptions)

| Metric | Before (prior run) | After |
|---|---|---|
| Correct served | 4/17 | **6/17** |
| `MISSING_DIMENSION` refusals | 2/17 (both **false** refusals) | 0/17 |
| Wrong-served | 0 | **0/6** |
| `LIVE_AI_DISABLED` | 11/17 | 11/17 |
| Regressions | — | 0 |

Newly solved: `ext_prt_02#1` → 6 (printed key D.6), `ext_prt_03#1` → a√2/2; both carry the illustrative-scene label. **Correction:** the prior run reported those two refusals as correct clarifications; they were false refusals (CORRECTS `unified-angle-geometry-verified-image-to-3d`). Details: [`external17_before_after_comparison.json`](external17_before_after_comparison.json), [`external17_case_diagnostics.json`](external17_case_diagnostics.json).

## 3. Root causes of the 11 `LIVE_AI_DISABLED`

| Case | Proximate | Root | Why |
|---|---|---|---|
| 04 | parser | Planner/Kernel | ratio goal KC/KB, metric-free affine solve; oracle 1/2 |
| 05 | parser | Planner/Kernel | ratio point fixed; area-ratio S1/S2 goal, word order |
| 06 | parser | Planner/Kernel | compound goal; inverse height from angle with lateral plane (V oracle a³√15/4) |
| 07 | parser | output policy | `Â` notation + noun goal; canonical served 15√93/31; asks rounding |
| 11 | Source Gate | output policy | "chiều cao bằng a" unread; asks degrees (oracle 30°) |
| 12 | Source Gate | Typed/Bridge | no area premise (oracle 2√3) |
| 08, 10, 13, 14, 15 | parser | out of scope / image | vector sum, curved solids, diagram-only data |

Source: [`live_ai_disabled_root_cause_analysis.json`](live_ai_disabled_root_cause_analysis.json) with 12 canonical replays.

## 4. Answers to the 25 required questions

1. **Layer of failure of the 11** — VERIFIED FACT: the parser was the proximate stage for 9 and the Source Gate (inside local verification) for 2. INFERENCE (from replays): the root layers are Planner/Kernel 3, output policy 2, Typed/Bridge 1, out-of-scope/image 5.
2. **Parser** — VERIFIED FACT: proximate in 9/11, sole root in 0/11.
3. **Typed Facts / Bridge** — INFERENCE: 1/11 (ext12, area premise).
4. **Planner/Kernel** — INFERENCE: 3/11 (04, 05, 06), plus the 2 false `MISSING_DIMENSION` refusals fixed here (02, 03#1).
5. **Missing data / out of scope** — VERIFIED FACT: true missing data 0/17. Out of scope or image-dependent: 5/17.
6. **What was fixed and why** — VERIFIED FACT: (a) the Kernel could not prove that an answer was independent of the height, so it produced false refusals; (b) the parser could not read part-to-part ratio points; (c) misleading UX copy. Each fix is general and covered by regression tests.
7. **New primitives** — VERIFIED FACT: 0 registry primitives. Added one engine certification step and one parser grammar rule for an existing primitive.
8. **Per-problem handlers** — VERIFIED FACT: none (renamed K.MNPQ probe served; dependent goals refused).
9. **External17 solved before/after** — VERIFIED FACT: 4/17 → 6/17.
10. **Correct refusals** — VERIFIED FACT: 11/17 fail closed, with 0 false `MISSING_DIMENSION`. INFERENCE: 5 are genuinely outside scope; 6 are solvable in principle (safe false negatives).
11. **Wrong-served** — VERIFIED FACT: 0 (6/6 served match the hand oracle; stated-height cross-check AA' = 2, 7 → 6).
12. **Real images solved with Local OCR** — VERIFIED FACT: 0/16 complete-problem images. Recorded local OCR is rejected by the fidelity gate on 38/38 images.
13. **Images needing Vision** — VERIFIED FACT: 16/16 complete-problem images.
14. **Live Vision** — NOT_MEASURED. A live plan exists in [`vision_live_readiness.json`](vision_live_readiness.json); it is BLOCKED pending owner approval.
15. **Offline reproducibility** — VERIFIED FACT: yes, via `tools/evaluate_real_world_reliability.py`, the browser harness and the cached images (SHA-256 38/38, 0 in Git).
16. **Wrong OCR/Vision facts passing the Source Gate** — VERIFIED FACT: none observed (corruption probes blocked; conflict → `NEEDS_CONFIRMATION`). NOT_MEASURED for live Vision output.
17. **Scene3D consistency** — VERIFIED FACT: continuity holds on 6/6 served. Invariant answers are labelled non-unique, and no scene is drawn for refusals (browser 12/12).
18. **UX defects** — VERIFIED FACT: one found by the real browser E2E: a text-analysis 503 showed the photo-extraction message. Fixed and asserted by the harness.
19. **Cold/warm latency** — VERIFIED FACT (host): cold parse p50 10.9 ms, cached 0.05 ms, router E2E p50 24.3 ms, single-thread cold p50 67 ms. The invariance path p50 is 116 ms (vs 41 ms with a stated height); a dependent-goal refusal after probing takes 105 ms (vs 23 ms without probing).
20. **Memory / Scene3D** — VERIFIED FACT (host headless Chrome): RSS Δ −0.02 MB over 50 requests; orbit fps 100–145; JS heap ≤ 18.5 MB. Physical low-end: NOT_MEASURED.
21. **Independent H-1** — NOT_MEASURED (no sealed independent corpus; [`independent_h1_readiness.json`](independent_h1_readiness.json)).
22. **Still unsupported** — ratio/area-ratio goals, inverse angle with a lateral plane, area premises, rounding/degree output, vector answers, curved real-world solids, diagram-only data, `Â` and noun-phrase goals, "đáy là hình vuông cạnh 2 tâm O" ordering (UNGROUNDED_VALUE).
23. **Kernel vs Vision** — INFERENCE: for printed images Vision is the bottleneck (0/16 local). On text, the top root is Kernel/output policy (5/11). HYPOTHESIS: run the owner-approved live Vision measurement first, then the output policy (rounding/degrees), then the Kernel ratio goals.
24. **Rust / another OCR model** — VERIFIED FACT: no Rust needed (kernel p50 13 ms). INFERENCE: local OCR quality, not speed, blocks image solving; a better OCR model is a HYPOTHESIS to be measured, not adopted here.
25. **Candidate level** — VERIFIED FACT: an offline, regression-green, frozen candidate for a development branch. NOT production-verified, NOT independently validated, live Vision NOT_MEASURED.

## 5. Gates

| Gate | Verdict |
|---|---|
| A Root-cause integrity | PASS (17/17 classified, 11/11 traced with replays) |
| B Hybrid correctness | PASS (0 wrong-served, 0 per-problem code) |
| C Image-to-geometry | PASS offline; live Vision NOT_MEASURED |
| D Scene3D & UX | PASS (host browser) |
| E External coverage | PASS (before/after with denominators; diagnostic corpus) |
| F Performance | PASS_HOST_AND_CONSTRAINED_MEASURED; physical low-end NOT_MEASURED |
| G Independent evaluation | NOT_MEASURED |
| H Release candidate | see [`full_regression_summary.json`](full_regression_summary.json) and candidate freeze |
