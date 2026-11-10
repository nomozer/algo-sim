# ALGOSIM — Real-World End-to-End Reliability & Hybrid Gap Closure

Run `real-world-end-to-end-reliability` · WAVE_ID `REAL_WORLD_END_TO_END_RELIABILITY` · branch `feat/local-first-geometry-understanding` (not merged, not pushed) · `ALLOW_LIVE_AI=0`, **0 live Gemini calls**.

- **Baseline:** HEAD `8d0fde3378c9b087bdbbc4c66e1a40aad3b532cc`, product `c61a3589782bde35b69e8376d8ebf136314e47f3`, measured-system tree `69bb83ba51b834f6…` (`108` files, `CACHE_VERSION = 132`, `freeze --verify` MATCH before edits).
- **Candidate after this run:** product `7994da7a64c8dc288c4de972df2d8d1db65e0c20`, measured-system tree `3754cbd18f58ddfb913fb61efd3dd078b0767770cff935a975cc8c258a1859fa` (`108` files, `CACHE_VERSION = 132`; see [`run.json`](run.json) and `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`).

Epistemic labels: **VERIFIED FACT** (machine receipt in this directory), **INFERENCE**, **HYPOTHESIS**, **NOT_MEASURED**, **BLOCKED**.

> External17 is a **development / diagnostic** corpus: every statement was read and diagnosed by the implementing agent. Nothing here is a blind or independent H-1 result (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`).

## 1. What changed (product)

| Layer | Change | Evidence |
|---|---|---|
| Exact Kernel `engine.py` | **Height-invariance certification**: when a pyramid/prism height is not given and every asked quantity is a whitelisted vertex-only metric goal (length; point–plane, line–line, line–plane, plane–plane distance; line–line, line–plane angle), the engine re-runs at 5 exact samples h² ∈ {1,2,3,5,7}; identical exact answers ⇒ served with `scene_configuration {unique:false, kind:HEIGHT_INVARIANT_ILLUSTRATIVE, invariance_certificate}`; otherwise the original `MISSING_DIMENSION` refusal stands | [`planner_kernel_capability_closure.json`](planner_kernel_capability_closure.json) (11/11 probes) |
| Adapter `/4` | forwards `route_d.scene_configuration` on served responses | same |
| Local parser | part-to-part ratio point "E thuộc cạnh SC sao cho SE = 3EC" → existing `point_divides_segment` (k/(k+1)); malformed part pairs fail closed | [`parser_semantic_gap_closure.json`](parser_semantic_gap_closure.json) (2/2) |
| Frontend | learner note `#stage-illustrative-note` ("hình chỉ minh họa") for non-unique scenes; analyze-stage 503 message no longer shows photo-extraction copy | [`scene3d_browser_acceptance.json`](scene3d_browser_acceptance.json) (12/12 + image) |

Proof of the invariance rule (**VERIFIED FACT** for the algebra; **INFERENCE** that the guards cover every served path): with t = h², vertex coordinates are t-independent and the metric is G₂ ⊕ (t), so every Gram matrix is A + t·zzᵀ and its determinant is affine in t (matrix determinant lemma). Each whitelisted goal² is P(t)/Q(t) with degrees ≤ 2 and Q > 0; equal values at 5 distinct t force P ≡ cQ. New registry primitives: **0**. Per-problem handlers: **0**.

## 2. External17 — before / after & Section 8.5 acceptance metrics (`ORACLE_TEXT_DOWNSTREAM_REPLAY`)

| Metric | Before (prior run) | After |
|---|---|---|
| Correct Solve Rate (External17 all / in-scope polyhedral) | 4/17 (4/12) | **6/17 (6/12)** |
| Served Answer Accuracy | 4/4 | **6/6** |
| Wrong-Served Rate (over served / over all 17) | 0/4 (0/17) | **0/6 (0/17)** |
| False `MISSING_DIMENSION` Refusals | 2/17 (both **false** refusals) | **0/17** |
| Correct Refusal Rate (out-of-scope/diagram-only; all unserved fail-closed offline) | 5/5 (11/11) | **5/5 (11/11)** |
| Image-to-Solution Success (zero-AI from raw pixels / recorded Vision / live Vision) | 0/16 / 1/16 / `NOT_MEASURED` | **0/16 / 1/16 / `NOT_MEASURED`** |
| Local-Only Solve Rate (verbatim text / raw external images) | 4/17 / 0/16 | **6/17 / 0/16** |
| Provider Dependency Rate (raw images / verbatim text) | 16/16 / 11/17 | **16/16 / 11/17** (5 out-of-scope even with AI) |

Newly solved: `ext_prt_02_hd_q_7922924#1` → `6` (printed key `D. 6`), `ext_prt_03_hd_q_7907931#1` → `a√2/2`; both carry the illustrative-scene label. **Correction:** the prior run reported those two refusals as correct clarifications; they were false refusals (`CORRECTS unified-angle-geometry-verified-image-to-3d`). Details: [`external17_before_after_comparison.json`](external17_before_after_comparison.json), [`external17_case_diagnostics.json`](external17_case_diagnostics.json).

## 3. Root causes of the 11 `LIVE_AI_DISABLED` (Replay 1 + Replay 2 `TypedFactNext/2` + Replay 3)

| Case | Proximate (Replay 1) | Replay 2 (`run_typed_fact_next_v2_route` verbatim / paraphrase) | Root | Why |
|---|---|---|---|---|
| 04 | parser (`A`) | metric-free trapezoid + parallel plane + ratio goal unsupported | Planner/Kernel (`F`) | ratio goal KC/KB, metric-free affine solve; oracle `1/2` |
| 05 | parser (`A`) | `SE=3EC` ratio fixed (`√11/2` served); `S1/S2` area-ratio unsupported | Planner/Kernel (`F/C`) | area-ratio goal on metric-free parallelogram + word order |
| 06 | parser (`A`) | verbatim `TypedFactNext/2` passes Source Gate + Planner → Kernel `MISSING_DIMENSION`; known-base serves `a√15/5` | Planner/Kernel (`F`) | inverse height from angle with lateral plane (`V = a³√15/4`) + compound goal |
| 07 | parser (`A`) | verbatim `TypedFactNext/2` → Source Gate `PREDICATE_NOT_IN_QUOTE` on `Â = 60°`; canonical height-free paraphrase serves `15√93/31` via height-invariance | Output policy | asks decimal rounding ("làm tròn kết quả đến hàng phần mười") + `Â` + noun goal |
| 11 | Source Gate (`D`) | verbatim `TypedFactNext/2` → Source Gate `UNGROUNDED_VALUE` on `chiều cao bằng a`; explicit edge + "số đo góc" → `QUESTION_CONTEXT_UNSUPPORTED` | Output policy | asks degrees (`30°`) + regular-prism height grounding |
| 12 | Source Gate (`A/D`) | verbatim `TypedFactNext/2` → `NOT_ASKED_IN_SOURCE` on `… bằng` + no face-area premise; side-given serves `2√3` | Typed/Bridge (`C`) | no face-area premise (`ABB'A' = 12`) + MC stem `… bằng` |
| 08, 10, 13, 14, 15 | parser | outside polyhedral metric scope / diagram-only heights (`15`) | Out of scope / image (`G/I`) | vector sum (`08`), curved solids (`10,13,14`), diagram-only data (`15`) |

Source: [`live_ai_disabled_root_cause_analysis.json`](live_ai_disabled_root_cause_analysis.json).

## 4. Answers to the 25 required questions

1. **Layer of failure of the 11** — **VERIFIED FACT**: on Replay 1 (local text), the parser was the proximate stage for `9/11` and the Source Gate (inside local verification) for `2/11`. Via Replay 2 (`Validated TypedFactNext/2` + canonical paraphrases), the root layers are Planner/Kernel `3` (`04, 05, 06`), output policy `2` (`07, 11`), Typed/Bridge `1` (`12`), and out-of-scope/image `5` (`08, 10, 13, 14, 15`).
2. **Parser** — **VERIFIED FACT**: proximate in `9/11`, sole root in `0/11`.
3. **Typed Facts / Bridge** — **VERIFIED FACT** (Replay 2): `1/11` (`ext12`, missing face-area premise in `TypedFactNext/2`, alongside `NOT_ASKED_IN_SOURCE` on MC stem `… bằng`).
4. **Planner/Kernel** — **VERIFIED FACT** (Replay 2 on `06` + capability audit on `04, 05`): `3/11` (`04, 05, 06`), plus the `2` false `MISSING_DIMENSION` refusals fixed in this run (`02, 03#1`).
5. **Missing data / out of scope** — **VERIFIED FACT**: true missing mathematical data on self-contained text statements `0/17`; diagram-only missing from text `1/17` (`ext15`, `"Chiều cao đo được ghi trên hình"` — `NOT_RECOVERABLE` from text alone); out-of-scope or diagram-dependent overall `5/17`.
6. **What was fixed and why** — **VERIFIED FACT**: (a) Exact Kernel height-invariance certification so height-independent goals no longer trigger false `MISSING_DIMENSION` refusals; (b) parser stage `5b-3` part-to-part ratio points (`SE = 3EC`); (c) frontend `#stage-illustrative-note` for non-unique scenes and analyze-stage `503` error copy. Each fix is general and locked by regression tests.
7. **New primitives** — **VERIFIED FACT**: `0` new registry primitives (`geometry-functions/33` unchanged). Added one engine certification step (`certify_height_invariance`) and one parser grammar rule targeting existing `point_divides_segment`.
8. **Per-problem handlers** — **VERIFIED FACT**: `0` (verified on renamed `K.MNPQ` -> `2√2`, equilateral prism `AA'–BC` -> `a√3`, and `7` negative height-dependent / constructed-operand probes).
9. **External17 solved before/after** — **VERIFIED FACT**: `4/17 → 6/17` (`ORACLE_TEXT_DOWNSTREAM_REPLAY`).
10. **Correct refusals** — **VERIFIED FACT**: `11/17` fail closed offline (`0` false `MISSING_DIMENSION`, `5/5` genuinely out-of-scope/diagram-only items refused). `6/12` in-scope polyhedral items remain safe false negatives offline due to the documented gaps above.
11. **Wrong-served** — **VERIFIED FACT**: `0` (`6/6` served match independent hand derivations and printed MC keys where present; stated-height cross-check `AA' = 2, 7 -> 6`).
12. **Real images solved with Local OCR** — **VERIFIED FACT**: `0/16` complete-problem images (`38/38` raw external OCR outputs safely rejected by `verify_ocr_input_fidelity` / `reconcile_dual_ocr_texts`).
13. **Images needing Vision** — **VERIFIED FACT**: `16/16` complete-problem external images.
14. **Live Vision** — **NOT_MEASURED** (`ALLOW_LIVE_AI=0`, `0` live Gemini calls). Pre-registered protocol in [`vision_live_readiness.json`](vision_live_readiness.json) is **BLOCKED** pending owner approval.
15. **Offline reproducibility** — **VERIFIED FACT**: yes, via `tools/evaluate_real_world_reliability.py`, `tools/e2e_browser_acceptance.mjs`, and the `38` SHA-256-verified cached images (`0` tracked in Git).
16. **Wrong OCR/Vision facts passing the Source Gate** — **VERIFIED FACT** (offline): `0` observed (`11/11` single/shared-dual OCR corruption probes blocked; competing OCR vs Vision facts route to `NEEDS_CONFIRMATION`). **NOT_MEASURED** on live Vision output.
17. **Scene3D consistency** — **VERIFIED FACT**: `validate_construction_continuity` passes on `6/6` served External17 cases; height-invariant scenes carry `unique=false` + `#stage-illustrative-note`; refusals render `0` canvases (`12/12` browser cases at `100%` and `110%` zoom).
18. **UX defects** — **VERIFIED FACT**: real browser E2E found that text-analysis `503 LIVE_AI_DISABLED` displayed the photo-extraction message (`"Chức năng trích xuất ảnh…"`). Fixed via stage-aware `analyzeErrorMessage` in `photo-problem-flow.ts` / `ProblemInput.tsx` and locked by unit + Playwright E2E assertions.
19. **Cold/warm latency** — **VERIFIED FACT** (host): cold parse `p50 = 10.9 ms`, warm cached parse `p50 = 0.05 ms`, router E2E warm `p50 = 24.3 ms`, single-thread cold subprocess `p50 = 67.1 ms`. Height-invariance path (cold parser + 6 exact engine passes) `p50 = 115.8 ms` vs stated-height `p50 = 41.1 ms`; dependent refusal after probe `p50 = 105.3 ms` vs unprobed volume refusal `23.3 ms`.
20. **Memory / Scene3D** — **VERIFIED FACT** (host + headless Chrome): Python RSS across `50` requests `107.7 → 107.7 MB` (`VietOCR-HW ONNX` unloaded by default); Scene3D orbit `100–145 FPS`, JS heap `≤ 18.5 MB`. Physical 2–4 core / 4 GB device: **NOT_MEASURED** (`PHYSICAL_LOW_END_NOT_MEASURED`).
21. **Independent H-1** — **NOT_MEASURED** (`8`-layer anti-contamination scan and candidate source inventory recorded in [`independent_h1_readiness.json`](independent_h1_readiness.json); `INDEPENDENT_GROUND_TRUTH_PENDING`).
22. **Still unsupported** — **VERIFIED FACT**: length-ratio and area-ratio goals on metric-free bases (`04, 05`), inverse base height from angle with a lateral plane (`06`), decimal rounding & degree-valued angle output policy (`07, 11`), face-area premises (`12`), `"chiều cao bằng a"` grounding on `khối lăng trụ tam giác đều` (`11`), Unicode `Â = 60°` & noun/MC-stem goals without `"Tính"` (`07, 12`), `"đáy là hình vuông cạnh 2 tâm O"` ordering (`UNGROUNDED_VALUE`), vector-valued goals (`08`), curved real-world solids (`10, 13, 14, 15`), and diagram-only dimensions (`15`).
23. **Kernel vs Vision** — **INFERENCE**: on raw photos, Vision is the primary gate (`0/16` solved by local OCR alone). On text, downstream policy/schema/Kernel gaps account for all `6` remaining in-scope polyhedral refusals (`0` are parser-only). **HYPOTHESIS**: run owner-approved live Vision evaluation first to measure real transcription fidelity, then address exact special-angle degree/rounding output policy (`07, 11`) and face-area / ratio goals (`12, 04, 05`).
24. **Rust / another OCR model** — **VERIFIED FACT**: `NO_RUST_NEEDED` (Exact Kernel `p50 ~ 13 ms` in pure Python `Fraction`/`Radical`). **INFERENCE**: local OCR fails on math symbols/layout fidelity (`CER`/symbol recall), not CPU speed; evaluating another lightweight OCR model requires an uncontaminated image split (**HYPOTHESIS**, not bundled in default runtime).
25. **Candidate level** — **VERIFIED FACT**: offline regression-verified, frozen development-branch candidate (`14,153` backend pytest passed, `0` failed, `15` strict XFAILs; `2,010/2,010` Vitest passed; `12/12 + image` Chrome E2E + `9/9` branding; `5/5` demo replay; `6/6` crash surface; docs IA & publication safety `PASS`; `freeze --verify` `MATCH`). **NOT** production-deployment verified, **NOT** independently H-1 validated, live Vision **NOT_MEASURED**.

## 5. Gates

| Gate | Verdict |
|---|---|
| A Root-cause integrity | **PASS** (`17/17` 20-field traces, `11/11` traced via Replay 1 + Replay 2 `TypedFactNext/2` + Replay 3) |
| B Hybrid correctness | **PASS** (`0` wrong-served, `0` per-problem handlers, `15` strict XFAILs preserved) |
| C Image-to-geometry | **PASS** offline (`38/38` noisy OCR blocked, Routes A/B/C/D verified); live Vision `NOT_MEASURED` |
| D Scene3D & UX | **PASS** (host Chrome `100%` & `110%` zoom, `12/12 + image`, UX `503` defect fixed) |
| E External coverage | **PASS** (`4/17 → 6/17`, `0/17` false `MISSING_DIMENSION`, all 8 metrics with denominators) |
| F Performance | **PASS_HOST_AND_CONSTRAINED_MEASURED**; physical low-end `NOT_MEASURED` |
| G Independent evaluation | **NOT_MEASURED** (`8`-layer scanner run; no sealed independent human-verified corpus) |
| H Release candidate | **PASS** (full regression green, docs IA + publication safety `PASS`, candidate frozen on clean tree, not merged/pushed) |
