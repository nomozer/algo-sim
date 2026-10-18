# EVIDENCE_INDEX.md — Chỉ mục bằng chứng và chuỗi đính chính (Master Evidence Index)

## WAVE_ID = HYBRID_PRE_MAIN_HARDENING

REPORT = docs/evaluation/geometry/runs/hybrid-pre-main-hardening/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-pre-main-hardening/
CLASSIFICATION = PRE_MAIN_HARDENING_VERIFIED (owner-approved GO_PRE_MAIN_BACKEND_SAFETY_HARDENING on research/hybrid-backend-integration 2620cffa; Hybrid off, LLM_ONLY default unchanged; independent review PASS 0 blocking; authoritative T3 FULL_PRODUCT_GATE_PASS at clean detached 1abc0a51 — verification/authoritative-t3.json)
CODE_COMMIT = 66328d22 (honest default-route guard) · 83e8390a (route-aware cache + per-call response contract) · 3afe2fdd (zero lengths, SPD Metric, 174-case answer regression); candidate freeze 81ba464f (product 3afe2fdd, tree_hash 7cd48f8c3d19299e95e5d31b341ec52120f0bc33b0e1ffc9cce03a2e9c37caf4, 110 files)
VERIFICATION = docs/evaluation/geometry/runs/hybrid-pre-main-hardening/run.json
MODEL_REQUEST_COUNT = 0 (offline only; ALLOW_LIVE_AI=0)
CORRECTS = HYBRID_BACKEND_INTEGRATION (cleanup-inventory.json: nonexistent SHA fdcf201c, research/hybrid-semantic-extraction-v2 wrongly SAFE_TO_DELETE with 14 unique commits, nonexistent nlu-extraction-eval, omitted branches/folders → cleanup-manifest.json; report claims: the "strict SPD metric guard" was test-only, "88/88 VERIFIED" is scene self-consistency not answer correctness, "174/174" locked status/code only; default-route guard test_Y was falsely green). Original files unchanged.
CORRECTED_BY = NONE

## WAVE_ID = HYBRID_BACKEND_INTEGRATION

REPORT = docs/evaluation/geometry/runs/hybrid-backend-integration/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-backend-integration/
CLASSIFICATION = COMBINED_BACKEND_VERIFIED_PENDING_MAIN_GO (integrating semantic-extraction-v3-runtime-revision bb014eb8, contract-driven-goal-composition a629ebee, and step-math-validation 0dd1da5c onto main 4abc4afb; 174/174 historical + 40/40 Slice A/B + 8/8 offline v3 cells + 148/148 baseline scenes + 88/88 combined scenes + 10/10 counterexamples PASS)
CODE_COMMIT = 7507312b (merge of semantic-extraction-v3-runtime-revision a94a54d0 + contract-driven-goal-composition 7507312b + step-math-validation f63dae86)
VERIFICATION = docs/evaluation/geometry/runs/hybrid-backend-integration/run.json (product_sha256 afab0a3ca3abfe3c3f7692d34be2aeadbd099b8d43b6543d8d234d19b5ef8443 across 110 files; historical v3 receipts at 6ba9033b… preserved untouched)
MODEL_REQUEST_COUNT = 0 (offline integration & verification only; ALLOW_LIVE_AI=0)
CORRECTS = NONE
CORRECTED_BY = HYBRID_PRE_MAIN_HARDENING

## WAVE_ID = STEP_MATH_VALIDATION

REPORT = docs/evaluation/geometry/runs/step-math-validation/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/step-math-validation/
CLASSIFICATION = STEP_MATH_VALIDATED_BASELINE_AND_FROZEN_BACKEND (148/148 served scenes verified across 11 mathematical invariant categories, 5,105 checks, 10/10 fault-injection counterexamples caught)
CODE_COMMIT = 0dd1da5c (independent oracle.py, audit_step_math_validation.py, test_step_math_validation.py)
VERIFICATION = docs/evaluation/geometry/runs/step-math-validation/run.json
MODEL_REQUEST_COUNT = 0
CORRECTS = NONE
CORRECTED_BY = NONE

## WAVE_ID = CONTRACT_DRIVEN_GOAL_COMPOSITION

REPORT = docs/evaluation/geometry/runs/contract-driven-goal-composition/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/contract-driven-goal-composition/
CLASSIFICATION = COMPLETE_LOCAL_CANDIDATE_READY_FOR_INTEGRATION_REVIEW (Slice A ask_area + Slice B ask_angle_line_plane contract-driven goal composition; 174/174 baseline + 40/40 new corpus PASS)
CODE_COMMIT = 1529faa7 (frozen branch HEAD a629ebee; product_sha256 540fc9d58b5ae060711aaacfb329b60f0bf18c44df3b1497faae432989ab1013)
VERIFICATION = docs/evaluation/geometry/runs/contract-driven-goal-composition/run.json
MODEL_REQUEST_COUNT = 0
CORRECTS = NONE
CORRECTED_BY = NONE

## WAVE_ID = SEMANTIC_EXTRACTION_V3_RUNTIME_REVISION

REPORT = docs/evaluation/geometry/runs/semantic-extraction-v3-runtime-revision/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/semantic-extraction-v3-runtime-revision/
CLASSIFICATION = OFFLINE_COMPLETE_AUTHORITATIVE_T3_PASS_AWAITING_LIVE_PILOT_GO (8/8 offline receipts COMPLETE; stalled task bufr6nkj1 verified and terminated; held-out split disclosed as REUSED_DIAGNOSTIC_NOT_FRESH_BLIND; stopped at GO_LIVE_PILOT_REQUIRED)
CODE_COMMIT = 283813b2 (possessive separator in _SAU_HOP_LE + pre-route split isolation in run_schema_contract_evaluation.py); candidate freeze 4fdb6308; offline runner review fix da5b407d; protocol lock 2b955ead; offline receipts 04b0db37
VERIFICATION = verification/authoritative-t3-20261018.json (candidate 6ba9033b… MATCH; independent review review-gates/revision.json PASS; targeted 445 passed / 1 xfailed; clean detached T3 at 04b0db37 FULL_PRODUCT_GATE_PASS: backend 10508 passed, frontend 68 files / 1079 passed, build PASS, demo 5/5, crash audit 6/6)
MODEL_REQUEST_COUNT = 0 (offline GOLD/REPLAY only; live authorization NONE)
CORRECTS = SEMANTIC_EXTRACTION_SCHEMA_CONTRACT (runtime regex backtracking in _SAU_HOP_LE, pre-route PILOT/LOCKED split isolation, and bounded sequential offline runner; original frozen lock at 5c58774d preserved byte-for-byte)
CORRECTED_BY = NONE

## WAVE_ID = SEMANTIC_EXTRACTION_SCHEMA_CONTRACT

REPORT = docs/evaluation/geometry/runs/semantic-extraction-schema-contract/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/semantic-extraction-schema-contract/
CLASSIFICATION = PARTIAL_PROTOCOL_RUNTIME_BLOCKER (0/8 completed offline receipts; original Claude task bufr6nkj1 remains active, stalled in frozen shared question grammar)
CODE_COMMIT = a28c2a19; candidate freeze f82414ce; protocol lock / measured source 5c58774d
VERIFICATION = verification/takeover-20261018.json (hashes/reviews MATCH; targeted 394 passed / 1 xfailed; full backend 10455 passed; frontend 1079; authoritative T3 NOT_RUN)
MODEL_REQUEST_COUNT = 0 (v3 takeover; GOLD/REPLAY are not extraction accuracy; no live authorization)
CORRECTS = NONE (new runtime blocker disclosed; previous reviews and measurements unchanged)
CORRECTED_BY = SEMANTIC_EXTRACTION_V3_RUNTIME_REVISION

## WAVE_ID = HYBRID_SEMANTIC_EXTRACTION_V2

REPORT = docs/evaluation/geometry/runs/hybrid-semantic-extraction-v2/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-semantic-extraction-v2/
CORRECTS = NONE (scorer /2 reported beside the frozen NLU scorer; its L01 artifact re-checked on the recorded receipt)
CORRECTED_BY = NONE
CLASSIFICATION = RESEARCH_BRANCH · LIVE PILOT MEASURED (results/live-pilot-analysis.md) · LOCKED NOT RUN · integration PENDING_OWNER_GO
CODE_COMMIT = 69fa9be8 (route-B prompt v2 + bounded Source Grounding); protocol lock 6ceb2508
VERIFICATION_COMMIT = candidate b5406c91… MATCH at 108fc086; identities + offline receipts at c640cd14; T3 FULL_PRODUCT_GATE_PASS at fa6d792e and, merged with main 8427c879, at b7b7e89e (verification/t3-merged.json)
MODEL_REQUEST_COUNT = 24 (paired dev pilot, owner GO pilot only; est. USD 0.123); LOCKED not run

Fresh 36-case corpus (dev 12 / heldout 24, 34 Fraction oracles), scorer grounded-source-obligations/2 (independent
review NOT_READY → LOCK_READY). GOLD served correct dev 1→2/12, heldout 2→2/24, 0 unsafe; prompt effect NOT_MEASURED.

## WAVE_ID = SCENE3D_ANNOTATION_CORRECTNESS

REPORT = docs/evaluation/geometry/runs/scene3d-annotation-correctness/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/scene3d-annotation-correctness/
CORRECTS = docs/evaluation/geometry/runs/scene3d-educational-finalization/report.md
CORRECTED_BY = NONE
CLASSIFICATION = SCENE3D_ANNOTATION_CORRECTNESS_INTEGRATED_ON_MAIN (`e218b5ef`, refreeze `b2352aae`; `integration.md`) · `HUMAN_VISUAL_REVIEW_PASS` (confirmed by user in session, 2026-10-17)
CODE_COMMIT = e218b5ef (frontend presentation-only: boundary-edge tangent alignment in `huongChanVuongGoc`, 2-segment textbook L-bracket + dash origin at foot in `vatNhanChung`, witness segment midpoint obstacles in `chieuNhan`; 0 backend/prompt changes)
VERIFICATION_COMMIT = 29127ba2 clean detached T3 FULL_PRODUCT_GATE_PASS (verification/t3-pass.json; pytest 10263 passed/1 skipped/2 deselected/9 xfailed, vitest 68 files/1079 passed, build PASS, demo 5/5 PASS, crash surface 6/6 PASS); candidate 57c7f5db… refrozen at b2352aae; independent review (review.md) PASS
MODEL_REQUEST_COUNT = 0

Mathematical audit and presentation fix across P1 (world-space `dot(u_world, v_world) = 0.000000` across all 9 witnesses; boundary-edge tangent alignment for `prism-midpoint-to-plane`; textbook 2-segment L-bracket + dash starting at foot $H$) and P2 (7-scene midpoint/solid/label verification, 3D distance $d_{3D}(C', (A'BD)) = 4/\sqrt{3} \approx 2.3094 > 0$ vs 2D perspective foreshortening at `(30°, 35°)`, and steep witness segment obstacle rects in `chieuNhan`). Verified across 68 Vitest files (1,079 tests), 30 full-size (`1280×900`) browser states, 6 comparison sheets (`visual/p1-cmp-*.png`), `scene3d-orbit-gate.mjs` `DAT`, and `hybrid-section-visual-check.mjs` PASS (`failures: []`). `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid NO-GO.

## WAVE_ID = SCENE3D_EDUCATIONAL_FINALIZATION

REPORT = docs/evaluation/geometry/runs/scene3d-educational-finalization/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/scene3d-educational-finalization/
CORRECTS = NONE
CORRECTED_BY = SCENE3D_ANNOTATION_CORRECTNESS (prose clarification for `marker: { u, v }` in report.md §2.3 EDU-4 and textbook 2-segment L-bracket refinement)
CLASSIFICATION = SCENE3D_EDUCATIONAL_FINALIZATION_INTEGRATED_ON_MAIN (`22df95d6`, merged `d4947610`, refreeze `7dc609bd`; `integration.md`) · `HUMAN_VISUAL_REVIEW_PASS` (confirmed by user in session, 2026-10-17)
CODE_COMMIT = 22df95d6 (shared frontend Scene3D modules EDU-1..EDU-8; 0 backend/prompt changes)
VERIFICATION_COMMIT = 8aabb4b9 clean detached T3 FULL_PRODUCT_GATE_PASS (verification/t3-pass.json; pytest 10263 passed/1 skipped/2 deselected/9 xfailed, vitest 68 files/1077 passed, build PASS, demo PASS, crash surface 6/6 PASS); candidate 57c7f5db… refrozen at 7dc609bd; independent review v2 (review.md) PASS 7/7
MODEL_REQUEST_COUNT = 0

49 full-size (`1280×900`) browser states across 12 scenes (`visual/after/audit-summary.json`, 0 console/page errors, 0 label overlaps, 0 unplaced annotations), 7 side-by-side comparison sheets (`visual/cmp-01..09-*.png`), `scene3d-orbit-gate.mjs` `DAT` on `p1`, `p6`, `p7` (`capPhat = 0`, `yen = 0.0°`), and `hybrid-section-visual-check.mjs` PASS (`failures: []`). `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid NO-GO.

## WAVE_ID = INDEPENDENT_NLU_EXTRACTION_EVALUATION

REPORT = docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/independent-nlu-extraction-evaluation/
CORRECTS = NONE
CORRECTED_BY = NONE
CLASSIFICATION = LIVE_BASELINE_MEASURED_INTEGRATED_ON_MAIN (b22c2269, pushed; integration.md) · locked: preregistered UNSAFE; correction layer corrections/ → P1 PASS, P2 NO
CODE_COMMIT = NONE (no product change; evaluation runner backend/scripts/run_nlu_extraction_evaluation.py)
VERIFICATION_COMMIT = candidate 57c7f5db… MATCH; live pilot at 6255a743, live locked at a9724519; review.md re-scored byte-identically
MODEL_REQUEST_COUNT = 76 (32 pilot + 44 locked; gemini-2.5-flash; est. USD 0.299)
CORRECTION_LAYER = corrections/scorer-unused-slots.json (beside, not instead of, results/live-locked/score.json)

Blind-authored corpus 60 (dev 16 / locked 44), oracle 56 values, implementer gold 319 facts; gold arm serves 8/44 locked.
Independence INDEPENDENT_AGENT_AUTHORED_NOT_HUMAN_VALIDATED. No live extraction claim until approval-request.md is GO.

## WAVE_ID = HYBRID_SEMANTIC_GROUNDING_RELIABILITY

REPORT = docs/evaluation/geometry/runs/hybrid-semantic-grounding-reliability/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-semantic-grounding-reliability/
CORRECTS = NONE (preregistration deviations recorded in corrections.json; current candidate divergence chains from Scene3D)
CORRECTED_BY = NONE
CLASSIFICATION = HYBRID_SEMANTIC_GROUNDING_INTEGRATED_ON_MAIN (bd20ac46, pushed; integration.md)
CODE_COMMIT = 94b3437b (final Registry/Engine; preserves Claude work plus review/historical fixes)
VERIFICATION_COMMIT = bd2dc080 clean detached T3 FULL_PRODUCT_GATE_PASS (verification/t3-attempt3.json; attempts 1–2 FAIL kept); candidate 57c7f5db… MATCH
MODEL_REQUEST_COUNT = 0

Offline authored Typed Facts:99 extraction cases (58 development +40 separate-author sentences mapped to41 cases),
13→0 wrong serves,21→16 false refusals; historical174 preserves answers/planner with two declared refusal-code changes.
Review hashes/results in review.md and verification/evaluation-summary.json. No human-held-out/live extraction claim;
Hybrid NO-GO, cache125, LLM_ONLY. Frozen input/oracle hashes at2e08922a verified unchanged.
Candidate metadata correction: run `candidate_divergence.json` CORRECTS its own initial `inputs/candidate_divergence.json`
(stale Scene3D fields only); original layer preserved, candidate hash unchanged.

## WAVE_ID = SCENE3D_VISUAL_CORRECTNESS

REPORT = docs/evaluation/geometry/runs/scene3d-visual-correctness/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/scene3d-visual-correctness/
CORRECTS = NONE
CORRECTED_BY = NONE
CLASSIFICATION = SCENE3D_VISUAL_CORRECTNESS_INTEGRATED_ON_MAIN (ee9689e6, pushed; integration.md)
CODE_COMMIT = a7388a40 (merge of Gemini 0ef0a20a, frontend) + 08021881 (FE-4) + f07ea069 (CONTRACT-BE-1, route D)
VERIFICATION_COMMIT = 0a33fcc8 clean detached T3 FULL_PRODUCT_GATE_PASS (verification/t3-pass.json); candidate 43e877ed… refrozen at 8f437980
MODEL_REQUEST_COUNT = 0

Integration scenes (`visual/scenes.json`) regenerated from the integrated backend; Scene3D harness D3D11 + SwiftShader receipts in `visual/receipts/`. Technical rendering only; no human visual approval or Hybrid enablement implied.

## WAVE_ID = GENERALIZED_GOAL_ENTRY

REPORT = docs/evaluation/geometry/runs/generalized-goal-entry/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/generalized-goal-entry/
CORRECTS = SCENE3D_ARCHITECTURE_VISUAL_RELIABILITY (interpretation only; scene-corrections.md)
CORRECTED_BY = NONE
CLASSIFICATION = GENERALIZED_GOAL_ENTRY_READY_FOR_INTEGRATION_DECISION
CODE_COMMIT = 193e634a (route D) + 289007a4 (Scene3D witness)
VERIFICATION_COMMIT = 5964f875 clean detached T3 FULL_PRODUCT_GATE_PASS (verification/t3-pass.json); candidate eaddb56c… refrozen at 297e6cce
MODEL_REQUEST_COUNT = 0

Preregistered new development corpus: length from an unnamed described point to one named point. Independent Fraction/Gram oracle; fixed/bounded/discovery baselines; production/removal/centroid/reversed/lying catalog variants. Exact report and final identities in the run package; no human approval or Hybrid enablement implied.

## WAVE_ID = GOAL_DIRECTED_FUNCTION_DISCOVERY

REPORT = docs/evaluation/geometry/runs/goal-directed-function-discovery/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/goal-directed-function-discovery/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = FUNCTION_DISCOVERY_SLICE_READY_FOR_REVIEW
CODE_COMMIT = cfa27baa (route D: geometry_functions planner/registry/engine, ai/function_route; 9fec9f43 + review fixes)
VERIFICATION_COMMIT = e6c5b0f1 clean detached T3 FULL_PRODUCT_GATE_PASS (verification/t3-pass.json); candidate 093359c2… refrozen at 81315986; independent review PASS_WITH_FINDINGS (run report §7)
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

Preregistered (`66593504`) development corpus, NOT_HELD_OUT, independent Fraction/Gram oracle: NEW 9/9 positives exact, 15/16
negatives with the registered code (deviation D-1), 0 wrong served; FIXED (`2a3c0787`) and BOUNDED (`8c24cb52`) 0/9; NEW identical
to BOUNDED on 125 regression cases; registry ablation (no-midpoint, no-plane-ask, +centroid 3/3, reversed identical, lying contract
refused by the engine). Scene3D harness SwiftShader + Intel D3D11 `PASS_CORE_CAUSAL_RENDERING` (6 fixtures, 0 errors).

## WAVE_ID = SCENE3D_ARCHITECTURE_VISUAL_RELIABILITY

REPORT = docs/evaluation/geometry/runs/scene3d-architecture-visual-reliability/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/scene3d-architecture-visual-reliability/
CORRECTED_BY = GENERALIZED_GOAL_ENTRY (scene-corrections.md; original artifacts unchanged)
CORRECTS = SCENE3D_VISUAL_PARITY_AUDIT
CLASSIFICATION = SCENE3D_ARCHITECTURE_IMPLEMENTATION_READY_FOR_REVIEW
CODE_COMMIT = SELF (frontend W1–W3 implementation on research/scene3d-visual-parity-audit; backend 55c657b8 unchanged)
VERIFICATION_COMMIT = SELF (Vitest 68 files / 1061 passed, Pytest geometry 7758 passed, Playwright 11/11 parity & oracle PASS, result-binding-visual-check PASS_CORE_CAUSAL_RENDERING; T3 NOT_RUN awaiting independent review)
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

Resolves all 2 CRITICAL, 5 IMPORTANT, and 2 NONBLOCKING W0 findings (`ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY`): `veKhongGian` transforms `o.perpendicular_witness` idempotently (`0.0` displacement across 11/11 cases); `scene3d-auxiliary.ts` preserves `perpendicular_witness.on` carrier lines (`gt_g`, `derived_H_line`) under default `aux=0` while hiding disposable planes (`mp1_gt_g`, `mp2_gt_g`) and off-solid translated points (`H`, `H1`); `hybrid-section-visual.tsx` enables `withSubEntities` by default (`after_same_all_rendered_objects = true` across all 9 harness cases); unselected `face` sub-entities act as transparent hit proxies; section sub-entities respect progressive `geometry_progress`; coincident points render `"B ≡ H"`; passive `surface` planes bound to defining points at `0.10` opacity; and W0 10/11 case metadata is reconciled (`section-MAB-trapezoid` included in both oracle and parity telemetry). Candidate not yet refrozen; no merge, no push.

## WAVE_ID = SCENE3D_VISUAL_PARITY_AUDIT

REPORT = docs/evaluation/geometry/runs/scene3d-visual-parity-audit/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/scene3d-visual-parity-audit/
CORRECTED_BY = SCENE3D_ARCHITECTURE_VISUAL_RELIABILITY
CORRECTS = NONE
CLASSIFICATION = SCENE3D_W0_BASELINE_AUDIT_COMPLETE
CODE_COMMIT = NONE (product 55c657b8 unchanged)
VERIFICATION_COMMIT = 4b51fde8 (W0 baseline audit on f83b4ed1, candidate 30808cb0… verified)
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

W0 visual parity and readability baseline audit (`ISSUE-ARCH-SCENE3D-CONSTRUCTION-READABILITY`) across Product (`/`) and Playwright Harness (`/scripts/hybrid-section-visual.html`). Proved backend Scene IR coordinates, planes, projection feet, and distances are 100% exact in Gram metric $G$, and isolated 2 CRITICAL (`FINDING-B1`, `FINDING-B2`), 5 IMPORTANT (`FINDING-D1..D3`, `FINDING-C2`, `FINDING-E1`), and 2 NONBLOCKING (`FINDING-A1`, `FINDING-D4`) frontend mapping, renderer, and harness divergences. Reconciled in `SCENE3D_ARCHITECTURE_VISUAL_RELIABILITY` (W0 oracle had 10 cases omitting `section-MAB-trapezoid` while W0 parity telemetry had 11 cases).

## WAVE_ID = RESULT_BINDING_FINAL_ACCEPTANCE

REPORT = docs/evaluation/geometry/runs/result-binding-final-acceptance/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/result-binding-final-acceptance/
CORRECTED_BY = NONE
CORRECTS = SHARED_ASK_GRAMMAR_SAFETY
CLASSIFICATION = FINAL_RESULT_BINDING_T3_PASS
CODE_COMMIT = 55c657b8 (product, independently code-reviewed)
VERIFICATION_COMMIT = 7f355a81 (refreeze checkpoint, candidate 30808cb0…, 110 files); T3 FULL_PRODUCT_GATE_PASS on a clean detached worktree at 7f355a81
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

Final refreeze (candidate 4b95dcc6… → 30808cb0…) from a clean detached worktree, with an append-only divergence layer chained through `corrects`. Authoritative T3 at the checkpoint: pytest 10046 passed / 0 failed (1 skipped, 2 deselected, 6 xfailed), vitest 1055/1055, build, demo 5/5, crash surface 6/6. The nine former candidate failures pass. Supplementary, not T3: locked corpus 18/18 and Benchmark 30 (19/9/0/2) byte-identical, two-line 45 (12/33) and 32 (11/21) identical except identity fields, grammar probe byte-identical (0 WRONG_SERVED), provider fingerprints unchanged. Integration readiness READY_FOR_REVIEW; no merge, no push.

## WAVE_ID = SHARED_ASK_GRAMMAR_SAFETY

REPORT = docs/evaluation/geometry/runs/shared-ask-grammar-safety/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/shared-ask-grammar-safety/
CORRECTED_BY = RESULT_BINDING_FINAL_ACCEPTANCE
CORRECTS = SOURCE_BOUND_RESULT_PLANNING_FALSE_SERVE_FIX
CLASSIFICATION = SHARED_ASK_GRAMMAR_SAFETY_BLOCKED
CODE_COMMIT = 5f1b576c (product); 9ce1298f (harness)
VERIFICATION_COMMIT = 5fc1645c (freeze 4b95dcc6…); T3 NOT_RUN
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

The sentence-level reading of asking sentences, the closed bracketed/rounding/unit grammar and the source-read reused foot together cut the preregistered probe from 47 (B) and 32 (A) WRONG_SERVED to 0. Locked corpus 18/18, benchmark 30 and two-line 45/32 are invariant; provider surfaces are unchanged. A harness bug made the protected favicon read as a dirty tree; it is fixed with RED/GREEN. The independent review of `9ce1298f` is BLOCK with C1–C4 and I1–I3. C2 and C3 are outside the approved scope. No merge, no push.

## WAVE_ID = SOURCE_BOUND_RESULT_PLANNING_FALSE_SERVE_FIX

REPORT = docs/evaluation/geometry/runs/source-bound-result-planning-false-serve-fix/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/source-bound-result-planning-false-serve-fix/
CORRECTED_BY = SHARED_ASK_GRAMMAR_SAFETY
CORRECTS = SOURCE_BOUND_RESULT_PLANNING
CLASSIFICATION = RESULT_BINDING_FALSE_SERVE_FIX_BLOCKED
CODE_COMMIT = 2427289a; 8da9ae31
VERIFICATION_COMMIT = 55fa87e7 (freeze a6ba6f32…); f25f2deb (freeze 7e993f8d…); T3 NOT_RUN
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

`_kiem_phu` now reads the auxiliary distance(point, line) ask on the source under the shared closed ask grammar, which closes IMPORTANT-1/2 of the `efb756aa` review. RED: 13/20 and 5/7. GREEN: 605 targeted tests. Locked corpus 18/18 and benchmark 30 are byte-identical; two-line 45/32 unchanged; provider surfaces unchanged. The independent review of `2427289a` returned BLOCK, with CRITICAL-1/2 in the shared grammar (also ordinary asks and Route A) and IMPORTANT-1 on the reused-foot splice. The `8da9ae31` delta is not independently reviewed. 8 pre-existing false serves remain. No merge, no push.

## WAVE_ID = SOURCE_BOUND_RESULT_PLANNING_MAIN_INTEGRATION

REPORT = docs/evaluation/geometry/runs/source-bound-result-planning-main-integration/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/source-bound-result-planning-main-integration/
CORRECTED_BY = NONE
CORRECTS = SOURCE_BOUND_RESULT_PLANNING_INTEGRATION_READINESS
CLASSIFICATION = RESULT_BINDING_MAIN_INTEGRATION_BLOCKED
CODE_COMMIT = NONE (product efb756aa unchanged)
VERIFICATION_COMMIT = d3323447 (preflight); main 2a3c0787 (probe comparison)
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

Fresh-context independent review of `10dd6d6e..efb756aa`: delta PASS (shared `_CHAN_TAN_NGU` back to main, no new serve in 36 probes). It found 2 IMPORTANT pre-existing false serves on the auxiliary distance(point, line) `_kiem_phu` path, identical on `main`. Following the task rule, there was no fast-forward and no push; the user's decision is pending. Preflight otherwise passes: ff-eligible, candidate MATCH, provider pins MATCH, corpus intact.

## WAVE_ID = SOURCE_BOUND_RESULT_PLANNING_INTEGRATION_READINESS

REPORT = docs/evaluation/geometry/runs/source-bound-result-planning-integration-readiness/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/source-bound-result-planning-integration-readiness/
CORRECTED_BY = SOURCE_BOUND_RESULT_PLANNING_MAIN_INTEGRATION
CORRECTS = SOURCE_BOUND_RESULT_PLANNING
CLASSIFICATION = RESULT_BINDING_MAIN_INTEGRATION_GO_AWAITING_APPROVAL
CODE_COMMIT = NONE (product efb756aa unchanged)
VERIFICATION_COMMIT = 11db61a1 (start); targeted gates on the readiness documentation commit (gates.json); reused T3 7b14fe04
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

Provider fingerprints recomputed in clean detached worktrees at `19140e2f`, `efb756aa`, `7b14fe04` and HEAD: A/B/declarations all INTENTIONALLY_CHANGED, backward compatible, `PlanningContract` absent from declarations (`provider-fingerprints.json`). Corrections (`corrections.json`): C1 draft hashes `442d1a0b…`/`be38f55f…` were not two-line-plane-section hashes (origin NOT_RECOVERABLE); C2 independent re-review covered `10dd6d6e`, the 3-line `efb756aa` delta reviewed here (session, not independent) NONBLOCKING; C3 stale `TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md` §2 hash/version. Fast-forward eligible; scene/corpus re-export byte-identical at final product; no merge/push.

## WAVE_ID = SOURCE_BOUND_RESULT_PLANNING

REPORT = docs/evaluation/geometry/runs/source-bound-result-planning/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/source-bound-result-planning/
CORRECTED_BY = SOURCE_BOUND_RESULT_PLANNING_INTEGRATION_READINESS
CORRECTS = NONE
CLASSIFICATION = RESULT_BINDING_INTEGRATION_REVIEW_READY
CODE_COMMIT = efb756aa
VERIFICATION_COMMIT = 7b14fe04
DOCUMENTATION_COMMIT_ROLE = SELF
MODEL_REQUEST_COUNT = 0

Source-bound result binding (`line_ref`) and bounded effect-driven point–line distance planning over `REGISTRY` effects (`PlanningContract` on `intersection_line`, `orthogonal_projection_line`, `ask_length`). RED `de5ea1a7` 18/18 `SCHEMA_INVALID` → GREEN 6/6 positive `SERVED` ($d^2 \in \{10/11, 5, 3, 10, 0, 10/11\}$), 12/12 negative `REFUSED` (`test_result_binding_planning.py` 72 passed; 18/18 `EXACT_MATCH` in `reconciliation.json`). Independent 11-dimension review (`review.md`) closed `CRITICAL-1`, `IMPORTANT-1`, `IMPORTANT-2`, `NONBLOCKING-1` via RED → GREEN at `efb756aa`. Browser harness (`visual/{swiftshader,gpu}/receipt.json`) 4 scenes `PASS_CORE_CAUSAL_RENDERING`, 0 errors. Historical two-line 45/32 and benchmark 30 invariant. Candidate `c0a8792f1c491ae4…` (110 files). Clean detached T3 `FULL_PRODUCT_GATE_PASS` at `7b14fe04` (`verification/t3-pass.json`, `verification/t3-authoritative.log` `29b09bf5…`: backend `9405 passed, 1 skipped, 2 deselected, 6 xfailed`, frontend Vitest `68 files / 1055 passed`, production build PASS, demo replay `5/5`, crash surface `6/6`).

## WAVE_ID = GOAL_DIRECTED_PLANNER_GENERALIZATION_AUDIT

REPORT = docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = NEXT_PLANNER_SLICE_DESIGN_READY_NO_PRODUCT_CHANGE
CODE_COMMIT = NONE (existing producta5a0797c)
VERIFICATION_COMMIT = 2a3c0787 (source baseline); a3907cc3 (diagnostic inputs before execution)
MODEL_REQUEST_COUNT = 0

14 diagnostic probes, not held-out; current-transport6correct serves/4correct refusals/1grounding false refusal;
3 separate proposed-field schema refusals with lower IR capability witnesses PASS. No general-search claim.
One next result-binding/effect-resolution slice design,6new positive/12negative development fixtures; not implemented.

## WAVE_ID = GROUP_A_MAIN_INTEGRATION

REPORT = docs/evaluation/geometry/runs/group-a-main-integration/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/group-a-main-integration/
CORRECTED_BY = NONE
CORRECTS = GROUP_A_INTEGRATION_READINESS
CLASSIFICATION = USER_AUTHORIZED_RESEARCH_INTEGRATION_MAIN_REMOTE_VERIFIED
CODE_COMMIT = a5a0797c
VERIFICATION_COMMIT = 5d73f7c2 (integration targeted); f227dd72 (inherited T3)
MODEL_REQUEST_COUNT = 0

User accepts disclosed limits for research integration only (`APPROVAL.md`). Main fast-forward and first push verified
at5d73f7c2; documentation publication commit has role SELF. Research branch retained, Hybrid off. Additive gzip archives
preserve three historical raw T3 logs' exact original bytes across Git text newline conversion; historical blobs/receipts unchanged.

## WAVE_ID = GROUP_A_INTEGRATION_READINESS

REPORT = docs/evaluation/geometry/runs/group-a-integration-readiness/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/group-a-integration-readiness/
CORRECTED_BY = GROUP_A_MAIN_INTEGRATION
CORRECTS = PEDAGOGICAL_CONSTRUCTION_SEQUENCING
CLASSIFICATION = GROUP_A_CONDITIONAL_GO_NO_MERGE_NO_PUSH
CODE_COMMIT = a5a0797c
VERIFICATION_COMMIT = d3c7381a (targeted clean detached); f227dd72 (reused authoritative T3)
MODEL_REQUEST_COUNT = 0

Fresh independent LOCAL re-review closes the missing final-fix review receipt. Technical gates PASS; human visual/scope
acceptance remains pending. Historical receipts keep their bytes; integration delta and preservation snapshots recorded.

## WAVE_ID = PEDAGOGICAL_CONSTRUCTION_SEQUENCING

REPORT = docs/evaluation/geometry/runs/pedagogical-construction-sequencing/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/pedagogical-construction-sequencing/
CORRECTED_BY = GROUP_A_INTEGRATION_READINESS
CORRECTS = SCENE3D_CONSTRUCTION_AUDIT
CLASSIFICATION = LOCAL_READY_FOR_HUMAN_VISUAL_REVIEW_NO_PUSH
CODE_COMMIT = a5a0797c
VERIFICATION_COMMIT = f227dd72
MODEL_REQUEST_COUNT = 0

Learner construction order of Hybrid scenes; resolves the auxiliary-before-solid limitation of `scene3d-construction-audit`.
Preregistered corpus 6 + 30; held-out ordering result is the first evaluation at `b0a853a0` (27/28 served), later runs are not
held-out. Candidate chain extended; review receipt `review.md`.

## WAVE_ID = SCENE3D_CONSTRUCTION_AUDIT

REPORT = docs/evaluation/geometry/runs/scene3d-construction-audit/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/scene3d-construction-audit/
CORRECTED_BY = PEDAGOGICAL_CONSTRUCTION_SEQUENCING
CORRECTS = TWO_LINE_PLANE_SECTION
CLASSIFICATION = LOCAL_READY_FOR_HUMAN_VISUAL_REVIEW_NO_PUSH
CODE_COMMIT = eea6f3df
VERIFICATION_COMMIT = b8e96a86
MODEL_REQUEST_COUNT = 0

Every learner step and point of the three served two-line scenes: math oracle + browser projection, before/after receipts.
Corrects the two-line visual limitation "some vertex labels suppressed" (renderer fix) and extends its candidate
divergence chain; two-line receipts stay unchanged. Review receipt `review.md`; T3 receipts in `verification/`.

## WAVE_ID = TWO_LINE_PLANE_SECTION

REPORT = docs/evaluation/geometry/runs/two-line-plane-section/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/two-line-plane-section/
CORRECTED_BY = NONE
CORRECTS = SOURCE_GROUNDING_INTEGRATION
CLASSIFICATION = LOCAL_RESEARCH_GROUP_A_GO_NO_PUSH
CODE_COMMIT = 2b42eb40
VERIFICATION_COMMIT = 69ff3a16
MODEL_REQUEST_COUNT = 0

New strict two-line plane/section composition, no second authority; intentional additive B surface change.
Candidate correction extends source-grounding-integration; historical bytes/labels stay unchanged.
Preregistered45 development +32 sealed heldout, independent algorithm/Gram oracle (same author).
Review receipt `review.md`; authoritative gates and final decision tracked in `run.json`/`report.md`.

## WAVE_ID = COMPACT_DSL_CLOSURE

REPORT = docs/evaluation/geometry/runs/compact-dsl-closure/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/compact-dsl-closure/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = COMPACT_DSL_NO_GO_ARCHIVED
CODE_COMMIT = NONE
VERIFICATION_COMMIT = NONE
MODEL_REQUEST_COUNT = 0

User-approved NO-GO for the Compact Geometry DSL and compact JSON as the AI → Hybrid wire format; Typed Facts JSON stays.
The research (runs `compact-geometry-dsl-spike` HOLD, corrected by `compact-dsl-format-evaluation` NO-GO) lives on the
archived local branch `research/compact-geometry-dsl` @ `3db08a1e` and in the verified incremental bundle
`.superpowers/preserved/compact-geometry-dsl-3db08a1e.bundle` (prerequisites on origin/main; local only, no off-machine
copy). Byte copies of the evaluation run.json, metrics and cost model are in `evaluation/`; SHA-256 of every research file
and the reopen trigger are in the report. Proxy tokens and a cost model only; Gemini usage NOT_MEASURED.

## WAVE_ID = SOURCE_GROUNDING_INTEGRATION

REPORT = docs/evaluation/geometry/runs/source-grounding-integration/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/source-grounding-integration/
CORRECTED_BY = TWO_LINE_PLANE_SECTION
CORRECTS = SOURCE_GROUNDING_COMPLETENESS
CLASSIFICATION = MAIN_INTEGRATED_PUSHED_T3_PASS_RESEARCH_CLOSURE
CODE_COMMIT = c30049fd
VERIFICATION_COMMIT = 27b81c51
MODEL_REQUEST_COUNT = 0

Independent final review uncovered a previously undeclared, preexisting numeric quote-overlap bypass; fixed in the
same semantic authority, RED 4 fail / 14 pass → GREEN 227 pass / 1 xfail. Focused independent follow-up NON-BLOCKING.
Candidate refrozen at c30049fd; additive divergence layer extends source-grounding-completeness. Historical bytes kept.
Clean detached T3 at integrated 27b81c51 PASS: backend 9161 / frontend 1053, build/demo/crash PASS. Provider pins unchanged,
benchmark byte-identical. Physical old worktrees removed; DSL/real-model refs kept and incrementally bundled local.
Push 7767c7e1..6e053b41 verified main = origin/main = ls-remote; Source Grounding branch deleted afterwards with -d.
The final documentation-only closure commit follows that verified push (role SELF); product/candidate unchanged.
Receipt: `runs/source-grounding-integration/verification/t3.log`, SHA256
`76a0e91659c7cd5237d2d743523ac6344d84868129dae3ff65d4f17c1cd9f17a`.

## WAVE_ID = SOURCE_GROUNDING_COMPLETENESS

REPORT = docs/evaluation/geometry/runs/source-grounding-completeness/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/source-grounding-completeness/
CORRECTED_BY = SOURCE_GROUNDING_INTEGRATION
CORRECTS = NONE
CLASSIFICATION = RESEARCH_BRANCH_T3_PASS_AWAITING_INTEGRATION_DECISION
CODE_COMMIT = b264828f
VERIFICATION_COMMIT = 046ab48a
MODEL_REQUEST_COUNT = 0

Premise source coverage in the shared A/B gate (`SOURCE_PREMISE_UNREAD`). RED at 7767c7e1: 130 failed / 79 passed.
Four independent LOCAL reviews (two BLOCKING), Critical/Important closed RED → GREEN. Candidate 46ca75a2 (divergence
layer in `inputs/` extends the goal-directed main-integration layer; d84cd373 superseded before any measurement).
Clean detached T3 at 046ab48a PASS: backend 9143, frontend 1053, build/demo/crash PASS. Benchmark byte-identical.
Machine receipt: `runs/source-grounding-completeness/verification/t3.log`, SHA256
`e4813748ed1b5c99223685a9e3f4aa92ac13ba77ccae3a6e79a2ba5841efafe4`.

## WAVE_ID = GOAL_DIRECTED_SECTION_PLANNING_MAIN_INTEGRATION

REPORT = docs/evaluation/geometry/runs/goal-directed-section-planning-main-integration/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/goal-directed-section-planning-main-integration/
CORRECTED_BY = NONE
CORRECTS = GOAL_DIRECTED_SECTION_PLANNING
CLASSIFICATION = MAIN_INTEGRATED_PUSHED_T3_PASS
CODE_COMMIT = 4a4f065b
VERIFICATION_COMMIT = b653d381
MODEL_REQUEST_COUNT = 0

Final re-review before integration: BLOCKING C1 (anaphor bound from quotes) + I1 (definition rest read in the quote)
fixed 39896b6e; a verifier found one more Important (anaphor not closing the object) fixed 4a4f065b; RED → GREEN.
Candidate fd80c8c9 (divergence chain extended in `inputs/`). ff 132e9b23 → b653d381, push verified three ways.
Clean detached T3 at b653d381 PASS: backend 8934, frontend 1053, build/demo/crash PASS. Benchmark byte-identical.
Machine receipt: `runs/goal-directed-section-planning-main-integration/verification/t3.log`, SHA256
`abc3e3810f40a8097b49e371684ca779f6ccc2e252663542513cb732e6864ac3`.

## WAVE_ID = GOAL_DIRECTED_SECTION_PLANNING

REPORT = docs/evaluation/geometry/runs/goal-directed-section-planning/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/goal-directed-section-planning/
CORRECTED_BY = GOAL_DIRECTED_SECTION_PLANNING_MAIN_INTEGRATION
CORRECTS = NONE
CLASSIFICATION = PHASE_A_B_T3_PASS_AWAITING_INTEGRATION_DECISION
CODE_COMMIT = 68fbc844
VERIFICATION_COMMIT = a443d2a2
MODEL_REQUEST_COUNT = 0

Phase A: closed follow-up coverage in `registry._kiem_du_kien_cau_hoi` (125 tests, routes A/B). Phase B: route-B goal
decomposition `MAT_SONG_SONG` with planner-only `translate_point`; exact independent oracle; Scene3D harness
SwiftShader + GPU (`visual/`). Independent reviews ×3 (`review.md`). Candidate 6110cd67 (divergence chain extended in
`inputs/`); route B surface 396f1c9c → 4a20601f, route A unchanged. Benchmark byte-identical 19/9/0/2.
Clean detached T3 at a443d2a2 PASS: backend 8925, frontend 1053, build/demo/crash PASS.
Machine receipt: `runs/goal-directed-section-planning/verification/t3.log`, SHA256
`1845f98054c9e3bb31f63136d903c3f428d37d268ae8cdfee010291d0d12dc86`.

## WAVE_ID = QUESTION_LOCAL_GIVENS_MAIN_INTEGRATION

REPORT = docs/evaluation/geometry/runs/question-local-givens-main-integration/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/question-local-givens-main-integration/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = MAIN_INTEGRATED_PUSHED_T3_PASS
CODE_COMMIT = f56d8cb7
VERIFICATION_COMMIT = 5fe14001
MODEL_REQUEST_COUNT = 0

User-authorized ff-only `232c1225` → `5fe14001`, SessionStart commit `ebe4e463`, push `a6e27a78..ebe4e463`
(main = origin/main = ls-remote). Candidate 25c85eed verify PASS; benchmark byte-identical 19/9/0/2; clean detached
T3 at 5fe14001 PASS: backend 8764, frontend 1053, build/demo/crash PASS. Three merged Hybrid branches deleted with -d.
Machine receipt: `runs/question-local-givens-main-integration/verification/t3.log`, SHA256
`ca42fdda58621bc887ee0ef62130d9ed2917f5cb4cc05e3080c6c05427e9a772`.

## WAVE_ID = QUESTION_LOCAL_GIVENS_FINAL_REVIEW

REPORT = docs/evaluation/geometry/runs/question-local-givens-final-review/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/question-local-givens-final-review/
CORRECTED_BY = NONE
CORRECTS = QUESTION_LOCAL_GIVENS
CLASSIFICATION = FINAL_REVIEW_FIX_T3_PASS_AWAITING_INTEGRATION_DECISION
CODE_COMMIT = f56d8cb7
VERIFICATION_COMMIT = 8fa3ae4c
MODEL_REQUEST_COUNT = 0

Fresh LOCAL review of `232c1225..98852c8f`: no new false serve, arms identical. New false refusal "biết rằng" fixed
RED 2/2 → GREEN 256. Narrows the prior claim: an unmarked same-sentence change after "sau đó"/"rồi" is still served
(pre-existing, open). Candidate 25c85eed (110 files), divergence chain extended in this run's `inputs/`.
Benchmark byte-identical 19/9/0/2. Clean detached T3 at 8fa3ae4c PASS: backend 8764, frontend 1053, build/demo/crash PASS.
Machine receipt: `runs/question-local-givens-final-review/verification/t3.log`, SHA256
`89d1d99e4b9c6ef2c36a3298bd2d5ea668811ea9b1e409e3df7644c069a1fe41`.

## WAVE_ID = QUESTION_LOCAL_GIVENS

REPORT = docs/evaluation/geometry/runs/question-local-givens/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/question-local-givens/
CORRECTED_BY = QUESTION_LOCAL_GIVENS_FINAL_REVIEW
CORRECTS = HYBRID_SEMANTIC_HARDENING
CLASSIFICATION = BOUNDED_GIVENS_REPAIR_T3_PASS_AWAITING_INTEGRATION_DECISION
CODE_COMMIT = e1f288ec
VERIFICATION_COMMIT = 678f5b7b
MODEL_REQUEST_COUNT = 0

Shared A/B source coverage refuses changed/unverified question-local assumptions and preserves original facts;
positive same-sentence givens remain served. Baseline RED 34/28; independent review 3 Critical + 1 Important,
19/4 RED → 23 GREEN; connected cluster 861/4 xfail. Candidate d4bc2b04; additive correction at
`runs/question-local-givens/inputs/candidate_divergence.json`, retaining the first candidate and gate-failure receipt.
Benchmark 30 cases byte-identical 19/9/0/2; provider surfaces/cache/default unchanged. No live requests, merge or push.
Clean detached T3 at 678f5b7b PASS: backend 8760, frontend 1053, build/demo/crash PASS.
Machine receipt: `runs/question-local-givens/verification/t3.log`, SHA256
`d732b7347307271c137dbe5dee28c3acb132f015181858492bc9ca4c8029206b`.

## WAVE_ID = HYBRID_MAIN_INTEGRATION

REPORT = docs/evaluation/geometry/runs/hybrid-main-integration/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-main-integration/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = LOCAL_MAIN_INTEGRATED_T3_PASS
CODE_COMMIT = 624e7fc5
VERIFICATION_COMMIT = 22edf7ff
MODEL_REQUEST_COUNT = 0

User-authorized local fast-forward a6e27a78 → 22edf7ff; no push. Candidate d1410731 verified in a clean detached worktree.
T3 8675 backend / 1053 frontend PASS, build/demo/crash PASS. Benchmark 30 cases byte-identical to the locked after result.
Historical A/B/candidates unchanged; question-local givens still open at this integration point.

## WAVE_ID = HYBRID_SEMANTIC_HARDENING

REPORT = docs/evaluation/geometry/runs/hybrid-semantic-hardening/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-semantic-hardening/
CORRECTED_BY = QUESTION_LOCAL_GIVENS
CORRECTS = HYBRID_SLICE_REVIEW
CLASSIFICATION = HYBRID_HARDENING_AWAITING_INTEGRATION_DECISION
CODE_COMMIT = 624e7fc5
VERIFICATION_COMMIT = f44130d2
MODEL_REQUEST_COUNT = 0

S1 closes the residual gate false serves of HYBRID_SLICE_REVIEW (operand binding, equality values, clause roles):
residual probes 1/79 served (the correct reading). S2 finds the root cause of the "invisible intersection line" — a fixed
±6 display segment behind the camera — and corrects the earlier evidence: the review harness skipped the product frame
step veKhongGian. Browser acceptance on SwiftShader and a hardware GPU: 0 failures. Open: question-local givens.

## WAVE_ID = HYBRID_SLICE_REVIEW

REPORT = docs/evaluation/geometry/runs/hybrid-slice-review/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-slice-review/
CORRECTED_BY = HYBRID_SEMANTIC_HARDENING
CORRECTS = HYBRID_SECTION_SLICE
CLASSIFICATION = HYBRID_SLICE_REVIEW_AWAITING_INTEGRATION_DECISION
CODE_COMMIT = b3e946e9
VERIFICATION_COMMIT = 542e3894
MODEL_REQUEST_COUNT = 0

Independent review of S0 and the section slice. Critical 2 (C1 ask answered when not asked, C2 conditional / question
clauses as givens), Important 3, Minor 4, re-verification false refusals, N1, N2 and the yes/no false serve: all closed
RED → GREEN except M4. Independent exact oracle (no product import) equal on every area and edge topology. Scene3D
harness with real Hybrid scenes: sections visible, orbit/zoom/reset settle, the intersection line draws 0 pixels.
Residual gate false serves (A–D) declared, not fixed. Also corrects HYBRID_GATE_CLAUSE_ROLE_FIX (ask residual closed).

## WAVE_ID = HYBRID_SECTION_SLICE

REPORT = docs/evaluation/geometry/runs/hybrid-section-slice/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-section-slice/
CORRECTED_BY = HYBRID_SLICE_REVIEW
CORRECTS = NONE
CLASSIFICATION = HYBRID_S0_AND_SECTION_SLICE_AWAITING_REVIEW
CODE_COMMIT = eeceefbc
VERIFICATION_COMMIT = 3e0eebc8
MODEL_REQUEST_COUNT = 0

Sections, intersection lines and section areas on the Hybrid route through the existing IR. Independent Euclidean
oracle: trapezoid 117/16, triangle SAC 18, mid square 1, cube A'BD 12; parallel planes refused. Provider surfaces of
A and B change by design. Offline typed facts and route-A calls only; no real model, no browser, no human review.

## WAVE_ID = HYBRID_GATE_CLAUSE_ROLE_FIX

REPORT = docs/evaluation/geometry/runs/hybrid-gate-clause-role-fix/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-gate-clause-role-fix/
CORRECTED_BY = HYBRID_SLICE_REVIEW
CORRECTS = NONE
CLASSIFICATION = HYBRID_GATE_CLAUSE_ROLE_FIXED_ON_RESEARCH_BRANCH
CODE_COMMIT = 8129f4ed
VERIFICATION_COMMIT = 9a390c71
MODEL_REQUEST_COUNT = 0

Fix of the CRITICAL gate defect found by HYBRID_SIMULATION_CAPABILITY_AUDIT (clause role inside the quote) and of the
ask-gate question check, shared by routes A and B. T3 FULL_PRODUCT_GATE_PASS at 9a390c71 (pytest 8409/0, vitest 1051).

## WAVE_ID = HYBRID_SIMULATION_CAPABILITY_AUDIT

REPORT = docs/evaluation/geometry/runs/hybrid-simulation-capability-audit/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-simulation-capability-audit/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = HYBRID_SIMULATION_AUDIT_AWAITING_DECISION
CODE_COMMIT = a6e27a78
VERIFICATION_COMMIT = a6e27a78
MODEL_REQUEST_COUNT = 0

Audit of Hybrid simulation capability with offline typed-fact probes (27 passed, 5 strict xfail). Shared engine
builds sections (executable probe against an independent trapezoid oracle) that Hybrid cannot request. New CRITICAL
gate defect: a premise quote carrying its own "Nếu … thì"/"Chứng minh" is used as a given (served √17 where the
control is UNDERDETERMINED_POINT), in routes A and B; the default LLM_ONLY route does not use this gate. No product
change, no real-model claim, no browser or human review of Hybrid scenes.

## WAVE_ID = HYBRID_SLICE1_MAIN_INTEGRATION

REPORT = docs/evaluation/geometry/runs/hybrid-slice1-main-integration/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-slice1-main-integration/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = HYBRID_SLICE1_INTEGRATED_ON_LOCAL_MAIN
CODE_COMMIT = 62f0b18e
VERIFICATION_COMMIT = a246dd19
MODEL_REQUEST_COUNT = 0

Slice 1 (B26) and the review fixes fast-forwarded into main (548066a8 → a246dd19). On main in a clean worktree:
candidate dda3a884 verify 0, T3 FULL_PRODUCT_GATE_PASS (pytest 8362/0, vitest 1051). Offline evidence only; no
real-model accuracy claim. B27/B28 not approved.

## WAVE_ID = HYBRID_SLICE1_REVIEW

REPORT = docs/evaluation/geometry/runs/hybrid-slice1-review/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-slice1-review/
CORRECTED_BY = NONE
CORRECTS = HYBRID_GOAL_DECOMPOSITION
CLASSIFICATION = HYBRID_SLICE1_INTEGRATION_AWAITING_APPROVAL
CODE_COMMIT = 62f0b18e
VERIFICATION_COMMIT = 9da4e853
MODEL_REQUEST_COUNT = 0

Independent review of goal decomposition slice 1. Corrects two claims of HYBRID_GOAL_DECOMPOSITION: "negated,
conditional and proof-only goals are refused" (the gate answered clauses that do not ask the distance; now
NOT_ASKED_IN_SOURCE) and "collision excluded by construction" (H₁/H_1/ΔSHD escaped the label scanner; now
nhan_phu_da_dung). Benchmark 19/9/0/2 unchanged (rows byte-identical). Candidate dda3a884 declared. Reviewer
independent of the implementation session but the same model family; no real-model claim.

## WAVE_ID = HYBRID_GOAL_DECOMPOSITION

REPORT = docs/evaluation/geometry/runs/hybrid-goal-decomposition/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-goal-decomposition/
CORRECTED_BY = HYBRID_SLICE1_REVIEW
CORRECTS = NONE
CLASSIFICATION = HYBRID_GOAL_DECOMPOSITION_SLICE1_AWAITING_REVIEW
CODE_COMMIT = f874b4dd
VERIFICATION_COMMIT = d8d636b5
MODEL_REQUEST_COUNT = 0

Goal decomposition slice 1: distance(point, line) through a compiler-introduced auxiliary foot (DERIVED/AUXILIARY),
admitted by the source gate only through the planner's declaration. Benchmark (same 30 cases and oracle) moves from
18/9/0/3 to 19/9/0/2 in both evaluations; only B26 changes. RED baseline at 4a3a4938 kept as a log. Candidate
divergence declared as a correction layer of the important-fixes declaration. Compiler and fake-provider evidence
only — no real-model claim. Same author for tests, oracle and implementation.

## WAVE_ID = HYBRID_COMPILER_CAPABILITY_AUDIT

REPORT = docs/evaluation/geometry/runs/hybrid-compiler-capability-audit/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-compiler-capability-audit/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = HYBRID_GOAL_DIRECTED_COMPILER_DESIGN_AWAITING_APPROVAL
CODE_COMMIT = 267eeb58
VERIFICATION_COMMIT = 267eeb58
MODEL_REQUEST_COUNT = 0

30-case Hybrid B compiler benchmark with an oracle that imports nothing from the product, pre-registered before any
compiler change. Verified facts and fake-provider pipeline agree on all 30: 18 correct served, 9 correct refusals,
0 wrong served, 3 false refusals (missing composition ×2, keyword dependence ×1). Same author for cases and oracle; not
a population. The commit message of 267eeb58 states 19/8 — the measured 18/9 in `baseline/metrics.json` is
authoritative. No product change (candidate a8dc02fc verify 0).

## WAVE_ID = MAIN_INTEGRATION_READINESS

REPORT = docs/evaluation/geometry/runs/main-integration-readiness/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/main-integration-readiness/
CORRECTED_BY = NONE
CORRECTS = NONE
CLASSIFICATION = ALGOSIM_MAIN_INTEGRATION_READY_FOR_FINAL_APPROVAL
CODE_COMMIT = 74df2a78
VERIFICATION_COMMIT = 49cf739e
MODEL_REQUEST_COUNT = 0

Orbit gate recalibration lives in `docs/evaluation/geometry/runs/orbit-gate-v2/` (pre-registered v2 failed its
known-good validation and is kept; v3 validated: historical DAT ×3, two injections refused; one v3 batch run
under concurrent load kept as invalid). v3 is red identically on main 28ac1d61 and on the integration branch: the p1
scene allocates during orbit, does not settle and leaves later scenes unsettled (product defect, root cause UNKNOWN).
Projection perpendicular recoloured from the W12 blue to the auxiliary-line colour (74df2a78). Integration branch
built from main by fast-forward; candidate refrozen (product 74df2a78, tree a8dc02fc); T3 FULL_PRODUCT_GATE_PASS at
49cf739e. 31 colliding untracked files backed up and verified, not removed (owned by another account). No human
visual acceptance.

## WAVE_ID = FINAL_INTEGRATION_GATES

REPORT = docs/evaluation/geometry/runs/final-integration-gates/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/final-integration-gates/
CORRECTED_BY = NONE
CORRECTS = GEOMETRY_LIBRARY_IMPORTANT_FIXES
CLASSIFICATION = ALGOSIM_FINAL_INTEGRATION_GATES_AWAITING_APPROVAL
CODE_COMMIT = 4ad89909
VERIFICATION_COMMIT = ffe7fd68
MODEL_REQUEST_COUNT = 0

Withdraws the important-fixes attribution of the orbit-gate failure to the measurement environment: the
historical build passes the unmodified gate today, while main 28ac1d61 fails it identically (canvas 545→683 px
from layout commits already in main + a fixed 250 ms read truncating damping; camera reaches the exact
OrbitControls angle). Gate and threshold unchanged; replacement acceptance proposed, not applied. T3
FULL_PRODUCT_GATE_PASS in a clean detached worktree at ffe7fd68 (pytest 8198/0, vitest 1050). Intermittent
generator test 1/9, cause UNKNOWN, now self-reporting. Worktrees 8→2, 10.35 GB freed. No human visual acceptance.

## WAVE_ID = GEOMETRY_LIBRARY_IMPORTANT_FIXES

REPORT = docs/evaluation/geometry/runs/geometry-library-important-fixes/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/geometry-library-important-fixes/
CORRECTED_BY = FINAL_INTEGRATION_GATES
CORRECTS = GEOMETRY_LIBRARY_EXPANSION
CLASSIFICATION = GEOMETRY_LIBRARY_IMPORTANT_FIXES_AWAITING_REVIEW
CODE_COMMIT = 4ad89909
VERIFICATION_COMMIT = 811896f8
MODEL_REQUEST_COUNT = 0

Fixes review findings I1–I3 of GEOMETRY_LIBRARY_INTEGRATION_REVIEW. Corrects the expansion run on three points,
without editing its artifacts: its scenes could re-root a tetrahedron (I1); its BRANCH_CANDIDATE product
provenance rule is withdrawn (I2; that manifest still matches the legacy rule); its "full backend 8166 PASS"
held only under ALGOSIM_* overrides (I3). New candidate a8dc02fc via standard refreeze; divergence declared as a
`corrects` layer. Plain backend 8198/0 at 811896f8 (one intermittent test in another run, cause UNKNOWN); orbit
gate red identically before the fix. No human visual acceptance, real-model or pilot claim.

## WAVE_ID = GEOMETRY_LIBRARY_INTEGRATION_REVIEW

REPORT = docs/evaluation/geometry/runs/geometry-library-integration-review/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/geometry-library-integration-review/
CORRECTED_BY = GEOMETRY_LIBRARY_IMPORTANT_FIXES
CORRECTS = NONE
CLASSIFICATION = GEOMETRY_LIBRARY_INTEGRATION_READINESS_AWAITING_APPROVAL
CODE_COMMIT = be6608a3
VERIFICATION_COMMIT = c6a99ac6
MODEL_REQUEST_COUNT = 0

Independent review; findings I1–I3 resolved by GEOMETRY_LIBRARY_IMPORTANT_FIXES (its report and screenshots
stay as recorded).

## WAVE_ID = GEOMETRY_LIBRARY_EXPANSION

REPORT = docs/evaluation/geometry/runs/geometry-library-expansion/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/geometry-library-expansion/
CORRECTED_BY = GEOMETRY_LIBRARY_IMPORTANT_FIXES
CORRECTS = NONE
CLASSIFICATION = GEOMETRY_LIBRARY_EXPANSION_AWAITING_REVIEW
CODE_COMMIT = a0eb1450
VERIFICATION_COMMIT = 815f06be
MODEL_REQUEST_COUNT = 0

New isolated shared-library work, not a rerun/correction of experimental A/B outcomes.
Before matrix audit.md, execution plan.md, new identity BRANCH_CANDIDATE.json and candidate_divergence.json;
diagnostics/ and offline-certification/ are separate new measurements. Current divergence declaration
supersedes the prior branch declaration only; historical candidate/results remain unchanged.
91 feature tests,74 fake calls/network0,34 renderer tests, local browser bounded visual check;
clean backend8166 PASS/1 skip/2 deselected,386.64s; geometry frontend695 PASS.
diagnostics/full-backend.xml and artifact-manifest.json register fresh bounded success.
No real-model, human visual acceptance or population-safety claim.

## WAVE_ID = HYBRID_COMPILER_SELECTION

REPORT = docs/evaluation/geometry/runs/hybrid-compiler-selection/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-compiler-selection/
CORRECTED_BY = HYBRID_AB_PILOT_READINESS
CORRECTS = NONE

Registration of the existing historical run (2026-10-10): parser fixtures, not Gemini quality. Its artifact bytes remain
unchanged. Read its source-binding / proof / negation interpretations together with the following correction layer.

## WAVE_ID = HYBRID_AB_PILOT_READINESS

REPORT = docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/report.md
ARTIFACT_DIRECTORY = docs/evaluation/geometry/runs/hybrid-ab-pilot-readiness/
CORRECTED_BY = NONE
CORRECTS = HYBRID_COMPILER_SELECTION
CLASSIFICATION = HYBRID_AB_PILOT_READINESS_AWAITING_REVIEW
CODE_COMMIT = cfe2ada5
RUNNER_COMMIT = 2f1b457c
MODEL_REQUEST_COUNT = 0

Authoritative current identity/caps: `run.json`; inputs/oracles: `inputs/`; post-review fake certification:
`fake-provider/verified/CERTIFICATION.json`; 344-pass focused/mutation journal, renderer metric, candidate divergence and
final clean full regression journal: `diagnostics/`, `report.md`, `handoff.md`. Pre-review fake artifacts remain unchanged,
superseded for current readiness, not pooled. Clean backend8068 PASS; bounded offline certification GO; both live modes remain NO-GO.
No population-safety, provider-budget proof or visual-acceptance claim.

> **Tài liệu Canonical cho việc tra cứu toàn bộ bằng chứng thực nghiệm, báo cáo và chuỗi đính chính.**
> Quy tắc bảo toàn: Báo cáo và artifact còn làm bằng chứng cho sản phẩm, nghiên cứu hiện hành hoặc khả năng tái lập phải giữ nguyên byte. Có thể đổi đường dẫn nếu mọi consumer/index/manifest được cập nhật; có thể xoá sau inventory khi đã xác minh không còn các vai trò ấy. Sai lệch của bằng chứng còn dùng được đính chính thông qua chuỗi `CORRECTED_BY`, không sửa kết quả lịch sử.
> Không có chu trình trong chuỗi đính chính (Acyclic DAG).

---

## 1. Chuỗi Đính Chính Tiêu Biểu (Primary Correction Chain)

```text
FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY (Đo live P03/P05: P03 valid, P05 valid, token ghi 0, trace false positives)
  │
  ▼ CORRECTED_BY
MODEL_VARIANCE_EVIDENCE_REVIEW (Đính chính offline: token 0 -> UNKNOWN, trace sửa, tách biệt outcome vs causality)
  │
  ▼ CORRECTED_BY
MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE (Đính chính provenance máy: commit 1 full SHA, JUnit telemetry, 2-run determinism)

DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING (Báo cáo và cấu trúc tài liệu ban đầu)
  │
  ▼ CORRECTED_BY
DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE (Đính chính provenance máy, loại bỏ hardcode)
  │
  ▼ CORRECTED_BY
DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL (Khép lại số liệu telemetry pytest bằng 2 bất biến số học và plugin hook máy)

PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION (Tiền đăng ký họ thứ hai: 95.5 điểm, manifest 8 ca)
  │
  ▼ CORRECTED_BY
SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE (Đính chính điểm THPT NOT_ESTABLISHED, 12 tầng kỹ thuật, ghi nhầm 94.0)
  │
  ▼ CORRECTED_BY
SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE (Đối soát mã nguồn: sửa 94.0->95.5, 6 primitives, RequestContract = CHANGE_REQUIRED, fail-closed INCOMPLETE)

PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW (Review merge: ghi nhầm nhãn hash manifest, ground truth và raw response do transcription error)
  │
  ▼ CORRECTED_BY
PRISM_MERGE_READINESS_EVIDENCE_IDENTITY_RECONCILIATION_OFFLINE (Đính chính danh tính bằng chứng máy: raw response f1bd804584..., manifest f5978eb5f7..., ground truth faf42e894f..., đường dẫn thực tế semantic_program)

CROSS_FAMILY_SCENE3D_PRODUCT_SEMANTIC_REPAIR (READY_FOR_HUMAN_VISUAL_REVIEW)
  │  phát hiện: bằng chứng hidden-line chưa đủ — không có oracle perspective độc lập, không có frozen camera identity, không có recovery audit
  ▼ CORRECTED_BY
CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR (sửa occlusion/oracle/formation → VERIFICATION_NOT_CLEAN)
  │  phát hiện: 28 lỗi "runner fixture" thật ra là REAL_PRODUCT_REGRESSION (HTTP 500); mobile recompute do khoá camera float thô
  ▼ CORRECTED_BY
VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR (mọi cổng tự động xanh → READY_FOR_HUMAN_VISUAL_REVIEW)
  │  review người: FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR (cạnh khuất không có điểm ảnh, playback, camera)
  ▼ CORRECTED_BY
HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE (w10 → READY_FOR_HUMAN_VISUAL_REVIEW)
  │  review người: FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR (W10-H1…H9: chóp/lăng trụ tam giác không công thức, ảnh xoay gần suy biến, …)
  ▼ CORRECTED_BY · SUPERSEDED_FOR_HUMAN_VERDICT
W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW (w11 → READY_FOR_HUMAN_VISUAL_REVIEW)
  │  review người: NEEDS_CHANGES (W11-H1…H5: timeline trộn bước tính, bước tĩnh, lớp lời giải, cam đậm hai nghĩa, GIVEN không có trong đề)
  ▼ CORRECTED_BY · SUPERSEDED_FOR_HUMAN_VERDICT
W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (w12 → READY_FOR_HUMAN_VISUAL_REVIEW)
  │  review người: NEEDS_CHANGES (W12-H1…H4: chóp/lăng trụ tam giác thiếu bước dựng riêng, không vá riêng hai họ, kênh giả định còn mở)
  ▼ CORRECTED_BY
W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION (w13, chỉ tài liệu → ARCHITECTURE_PREREGISTRATION_READY; không ảnh mới nên không SUPERSEDED_FOR_HUMAN_VERDICT)
  ▼ thực hiện tiền đăng ký · trả lời review w12 · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w12)
W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION (w14 → FORMATION_FOUNDATION_INCOMPLETE; Track B ASSUMPTION_POLICY_INCOMPLETE; chưa có review người)
  ▼ CORRECTED_BY (Track B: nguyên nhân gốc RC1–RC5 rồi đóng cổng; W15-D1 giải W14-D1) · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w14)
W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE (w15 → READY_FOR_HUMAN_VISUAL_REVIEW; chưa có review người)
  ▼ CORRECTED_BY (hai lỗ chứng chỉ: mặt phẳng cùng thực thể, yêu cầu chứng minh làm tiền đề; phần tô đè cạnh; ô từ chối trắng) · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w15)
W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE (w16 → READY_FOR_HUMAN_VISUAL_REVIEW; chưa có review người)
  ▼ CORRECTED_BY (giới hạn A′ đóng cho phép cắt; grounding không đọc yêu cầu chứng minh như dữ kiện ở mọi vùng; ảnh "cạnh 4" là lỗi bộ sinh fixture) · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w16)
W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS (w17 → READY_FOR_HUMAN_VISUAL_REVIEW; chưa có review người)
  ▼ CORRECTED_BY (phép dựng điểm — trung điểm, hình chiếu — gắn với quan hệ của đề theo danh tính; giới hạn phép dựng ngoài phép cắt đóng một phần) · SUPERSEDED_FOR_HUMAN_VERDICT (ảnh w17: hai công tắc thay bằng "Hiện tất cả")
W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS (w18 → READY_FOR_HUMAN_VISUAL_REVIEW; chưa có review người)
```

**Các điểm đính chính quan trọng đã được xác lập:**
1. **Kết quả retry P03 và P05:** Cả hai ca Analyze live đều thành công, hợp đồng dữ kiện hợp lệ, FactGraph và Primitive Compiler xử lý trọn vẹn, topology, `final_memory` và đáp số đều đạt. Lỗi `MODEL_MALFORMED_RELATION` không tái diễn.
2. **Token usage:** Hai request HTTP 200 có token ghi nhận ban đầu là `0` do giới hạn client đo lường; lớp đính chính đã chuẩn hóa thành `UNKNOWN`.
3. **Trace false-positive:** Quan hệ hợp lệ nhưng gắn nhãn sai lệch `MULTIPLE_STRUCTURAL_DEFECTS` đã được khắc phục bằng bộ đánh giá kind-aware trace.
4. **Historical root cause:** Nguyên nhân lịch sử của cụm lỗi P03/P05 vẫn là `NOT_ESTABLISHED` (nhất quán với giả thuyết biến thiên tự nhiên của mô hình - model variance).
5. **Commit label & identity:** Short SHA `3ba5afbb` có full SHA thực tế từ Git là `3ba5afbbd6b6e22781b03f29563c9d1589780603` (thay vì chuỗi ghép sai `3ba5afbbf46d...`). Phân loại: `COMMIT_ROLE_LABELING_ERROR` với `HISTORY_DRIFT = NO`.
6. **Tách biệt JUnit SHA-256:**
   - Worktree A (`CODE_HEAD = 18704f14`): focused sha256 = `955d5be51888496739bb5cba896f3068e52a806cbf18a8b163306dbddc360be8`, full backend sha256 = `a9307d083d06eb4f85e5094dbe1513e9a4f4d2f8cb8b77dcf95eb7f7b3c2e171`.
   - Worktree B (`END_HEAD = 2678cc65`): focused sha256 = `3c219c3ab81e1ec3c7c4a463fcf0092cd96843202736383b88dfc19b9bf15a3a`, full backend sha256 = `a36f82b9841569d4842637639809549fa97eb28d050b1507c472d86b6f19edbb`.

---

## 2. Bảng Danh Mục Các Wave Thực Nghiệm

## WAVE_ID = COMPLETION_RUNNER_REPAIR_OFFLINE
- **DATE:** 2026-09-17
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/completion-runner-repair-offline/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/completion-runner-repair-offline/
- **START_BASE:** bd370157
- **CODE_COMMIT:** 25c3f5b8
- **EVIDENCE_COMMIT_ROLE:** 35d84da0
- **CLASSIFICATION:** RUNNER_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = STRUCTURED_RELATION_SAFETY_REPAIR
- **DATE:** 2026-09-17
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/structured-relation-safety-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/structured-relation-safety-repair/
- **START_BASE:** 35d84da0
- **CODE_COMMIT:** 8dd5f8b6
- **EVIDENCE_COMMIT_ROLE:** cac49a09
- **CLASSIFICATION:** COMPILER_SAFETY_REPAIR
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** CORE_CONTRIBUTION

## WAVE_ID = N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION
- **DATE:** 2026-09-17
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/n04-targeted-rejection-registry-v2-preregistration/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/n04-targeted-rejection-registry-v2-preregistration/
- **START_BASE:** cac49a09
- **CODE_COMMIT:** 330334a0
- **EVIDENCE_COMMIT_ROLE:** d01254c2
- **CLASSIFICATION:** EVALUATION_PREREGISTRATION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** EVALUATION_METHODOLOGY

## WAVE_ID = COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY
- **DATE:** 2026-09-18
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/completion-measurement-repair-offline-post-safety/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/completion-measurement-repair-offline-post-safety/
- **START_BASE:** d01254c2
- **CODE_COMMIT:** e0fbbb22
- **EVIDENCE_COMMIT_ROLE:** e76419f4
- **CLASSIFICATION:** RUNNER_MEASUREMENT_REPAIR
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = RETRY_REMAINING_PREREGISTERED_CASES_POST_MEASUREMENT_REPAIR
- **DATE:** 2026-09-18
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark-completion-live-post-measurement-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark-completion-live-post-measurement-repair/
- **START_BASE:** e76419f4
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** 12df583a
- **CLASSIFICATION:** LIVE_EVALUATION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 12
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** EMPIRICAL_RESULTS

## WAVE_ID = ANALYZE_FAILURE_CLUSTER_DIAGNOSIS
- **DATE:** 2026-09-19
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/analyze-failure-cluster-diagnosis/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/analyze-failure-cluster-diagnosis/
- **START_BASE:** 12df583a
- **CODE_COMMIT:** 5806fec9
- **EVIDENCE_COMMIT_ROLE:** 0ff69cbb
- **CLASSIFICATION:** DIAGNOSIS_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = FRESH_PREREGISTERED_FAILURE_REPRODUCTION
- **DATE:** 2026-09-19
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction/
- **START_BASE:** 0ff69cbb
- **CODE_COMMIT:** 2dbf23c7
- **EVIDENCE_COMMIT_ROLE:** 45702b36
- **CLASSIFICATION:** REPRODUCTION_PREREGISTRATION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 1
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE
- **DATE:** 2026-09-20
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-offline/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-offline/
- **START_BASE:** 45702b36
- **CODE_COMMIT:** 866a1257
- **EVIDENCE_COMMIT_ROLE:** efee245c
- **CLASSIFICATION:** RUNNER_PERSISTENCE_REPAIR
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION
- **SUPERSEDES:** NONE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = SAFE_STRUCTURE_TRACE_REPAIR_EVIDENCE_RECONCILIATION
- **DATE:** 2026-09-20
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-evidence-reconciliation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-evidence-reconciliation/
- **START_BASE:** efee245c
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** c6c6448e
- **CLASSIFICATION:** RECONCILIATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE
- **THESIS_USE:** SUPPORTING_EVIDENCE

## WAVE_ID = FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY
- **DATE:** 2026-09-21
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/
- **START_BASE:** c6c6448e
- **CODE_COMMIT:** 934b4aeb
- **EVIDENCE_COMMIT_ROLE:** d09331ea
- **CLASSIFICATION:** LIVE_RETRY_EVALUATION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 2
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** MODEL_VARIANCE_EVIDENCE_REVIEW
- **SUPERSEDES:** NONE
- **THESIS_USE:** EMPIRICAL_RESULTS

## WAVE_ID = MODEL_VARIANCE_EVIDENCE_REVIEW
- **DATE:** 2026-09-21
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-review/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-review/
- **START_BASE:** d09331ea
- **CODE_COMMIT:** 3ba5afbb
- **EVIDENCE_COMMIT_ROLE:** 63eb0640
- **CLASSIFICATION:** EVIDENCE_REVIEW_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **SUPERSEDES:** FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY
- **THESIS_USE:** EMPIRICAL_RESULTS

## WAVE_ID = MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-provenance-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/model-variance-evidence-provenance-repair/
- **START_BASE:** 63eb0640
- **CODE_COMMIT:** 18704f14
- **EVIDENCE_COMMIT_ROLE:** 2678cc65
- **CLASSIFICATION:** PROVENANCE_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** MODEL_VARIANCE_EVIDENCE_REVIEW
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-handoff-hardening/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-handoff-hardening/
- **START_BASE:** 2678cc65
- **CODE_COMMIT:** 34c36872
- **EVIDENCE_COMMIT_ROLE:** c36f2042
- **CLASSIFICATION:** DOCS_HARDENING_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** ARCHITECTURE_HARDENING

## WAVE_ID = DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-evidence-provenance-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/docs-information-architecture-evidence-provenance-repair/
- **START_BASE:** c36f2042
- **CODE_COMMIT:** 27ed66aa
- **EVIDENCE_COMMIT_ROLE:** 02a7a860
- **CLASSIFICATION:** PROVENANCE_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL
- **SUPERSEDES:** DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = DOCS_TEST_TELEMETRY_RECONCILIATION_FINAL
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/docs-test-telemetry-reconciliation-final/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/docs-test-telemetry-reconciliation-final/
- **START_BASE:** 02a7a860
- **CODE_COMMIT:** dbb1ef1c
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** TELEMETRY_RECONCILIATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** DOCS_INFORMATION_ARCHITECTURE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/
- **START_BASE:** 6ec2e0d3
- **CODE_COMMIT:** abb377b8
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/
- **START_BASE:** 2a5b28eb
- **CODE_COMMIT:** 4a218d2d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** EVIDENCE_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **SUPERSEDES:** PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/
- **START_BASE:** dc444acd
- **CODE_COMMIT:** 4630f24d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SOURCE_SCOPE_RECONCILIATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/
- **START_BASE:** 65d09a89
- **CODE_COMMIT:** d0ba8bb7
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-vertical-slice/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-vertical-slice/
- **START_BASE:** f4a547ab
- **CODE_COMMIT:** 5a5534fe
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** VERTICAL_SLICE_IMPLEMENTATION_AND_VERIFICATION_OFFLINE
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES
- **CORRECTED_BY:** SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_FROZEN_BENCHMARK_ALIGNMENT_REPAIR_OFFLINE
- **DATE:** 2026-09-22
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-frozen-benchmark-alignment-repair/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-frozen-benchmark-alignment-repair/
- **START_BASE:** b4521d28
- **CODE_COMMIT:** 0714e929
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** REPORTING_AND_TEST_ASSERTION_EVIDENCE_MISMATCH
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE_OFFLINE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2
- **DATE:** 2026-09-23
- **REPORT:** docs/evaluation/reports/SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2.md
- **ARTIFACT_DIRECTORY:** NONE
- **START_BASE:** 8703fb50
- **CODE_COMMIT:** SELF
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** REGRESSION_REPAIR_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_REPAIR_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_REPAIR_OFFLINE
- **DATE:** 2026-09-23
- **REPORT:** docs/evaluation/semantic-benchmark/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/semantic-benchmark/
- **START_BASE:** c69eef96
- **CODE_COMMIT:** 6eb23e8d
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_SYNC_AND_CANDIDATE_REFREEZE_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (measured_system.tree_hash fc88b200… → 669ea2f1…, schema_hash 3db1e1c… → 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** SECOND_FAMILY_POST_VERTICAL_SLICE_FULL_REGRESSION_REPAIR_OFFLINE_GATE_2
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation-preregistration/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation-preregistration/
- **START_BASE:** 002b8da5
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/
- **START_BASE:** ef8af771
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 1
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-measurement-reconciliation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-measurement-reconciliation/
- **START_BASE:** 532f447e
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** HISTORICAL_EVIDENCE_INSUFFICIENT
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/
- **START_BASE:** 462645ec
- **CODE_COMMIT:** ab7d94eb
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PREREGISTRATION_OFFLINE
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = SECOND_FAMILY_LIVE_RETRY
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/
- **START_BASE:** 5d92afa2
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** SCHEMA_ACCEPTED_PIPELINE_PASS
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 1
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/prism-vertical-slice-merge-readiness/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/prism-vertical-slice-merge-readiness/
- **START_BASE:** d3fc1c72
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** MERGE_READINESS_REVIEW_PASS
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** PRISM_MERGE_READINESS_EVIDENCE_IDENTITY_RECONCILIATION_OFFLINE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = PRISM_MERGE_READINESS_EVIDENCE_IDENTITY_RECONCILIATION_OFFLINE
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/prism-merge-readiness-evidence-identity-reconciliation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/prism-merge-readiness-evidence-identity-reconciliation/
- **START_BASE:** f0d040f6
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** PASS_WITH_EVIDENCE_LABEL_CORRECTION
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = REFRESH_REMOTE_MAIN_AND_REVALIDATE_MERGE_BASE
- **DATE:** 2026-09-24
- **REPORT:** docs/evaluation/geometry/photo-problem-to-scene/remote-main-refresh-revalidation/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/photo-problem-to-scene/remote-main-refresh-revalidation/
- **START_BASE:** f0d8f4b2
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** REMOTE_INTEGRATION_READY
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (tree_hash 669ea2f1…, schema_hash 7610ff0…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 100)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_EVIDENCE

## WAVE_ID = CUBOID_CUBE_VISUAL_INTEGRITY
- **DATE:** 2026-09-26
- **REPORT:** NONE (artifact-only historical wave)
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/cuboid-cube-visual-integrity/
- **START_BASE:** 51e0c9ca
- **CODE_COMMIT:** 08c118f0
- **EVIDENCE_COMMIT_ROLE:** d9e79a00
- **CLASSIFICATION:** SUPERSEDED_EVIDENCE
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (historical fd9d61dd…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102)
- **CORRECTED_BY:** CUBOID_VISUAL_SEMANTIC_CLOSURE_AND_CROSS_FAMILY_REGRESSION_AUDIT
- **SUPERSEDES:** NONE
- **THESIS_USE:** HISTORICAL_ONLY

## WAVE_ID = CUBOID_VISUAL_SEMANTIC_CLOSURE_AND_CROSS_FAMILY_REGRESSION_AUDIT
- **DATE:** 2026-09-27
- **REPORT:** docs/evaluation/geometry/cuboid-cube-semantic-closure-20260927/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/cuboid-cube-semantic-closure-20260927/; docs/evaluation/geometry/cross-family-regression-20260927/
- **START_BASE:** d9e79a00
- **CODE_COMMIT:** 2822beb3
- **EVIDENCE_COMMIT_ROLE:** 40c20948
- **CLASSIFICATION:** PASS_WITH_EXPLICIT_TIER_A_EVIDENCE_GAPS
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 72516eb5…, clean product commit 2822beb3)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102)
- **CORRECTED_BY:** NONE
- **SUPERSEDES:** CUBOID_CUBE_VISUAL_INTEGRITY
- **THESIS_USE:** AUTHORITATIVE_WITH_DECLARED_SCOPE

## WAVE_ID = CLOSE_GENERIC_TIER_A_BROWSER_EVIDENCE_BEFORE_CUBOID_MERGE
- **DATE:** 2026-09-27
- **REPORT:** docs/evaluation/geometry/generic-tier-a-browser-closure-20260927/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/generic-tier-a-browser-closure-20260927/
- **START_BASE:** 1c83418a
- **CODE_COMMIT:** 2747f4b926511bd526e2eab541099f01e4b8acb5
- **MEASUREMENT_COMMIT:** 2747f4b926511bd526e2eab541099f01e4b8acb5
- **EVIDENCE_COMMIT_ROLE:** 7cee042c9a539f89970722ac56eb9f490d5e753b
- **CLASSIFICATION:** GENERIC_TIER_A_BROWSER_CLOSURE_PASS_MERGE_READY
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (product commit 2822beb3, tree_hash 72516eb5…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102)
- **CORRECTED_BY:** GENERIC_TIER_A_BROWSER_EVIDENCE_SEMANTIC_CORRECTION
- **SUPERSEDES:** NONE (closes the explicit NOT_MEASURED scope in the cuboid audit)
- **THESIS_USE:** HISTORICAL_ONLY

## WAVE_ID = GENERIC_TIER_A_BROWSER_EVIDENCE_SEMANTIC_CORRECTION
- **DATE:** 2026-09-27
- **REPORT:** docs/evaluation/geometry/generic-tier-a-browser-semantic-correction-20260927/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/generic-tier-a-browser-semantic-correction-20260927/
- **START_BASE:** 26479cc7
- **CODE_COMMIT:** NONE
- **EVIDENCE_COMMIT_ROLE:** da86db7f138b1a3a9293cb6fb9f5c64444faca71
- **CLASSIFICATION:** PRODUCT_REGRESSION_FOUND_AND_PRIOR_EVIDENCE_INVALIDATED
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (product commit 2822beb3, tree_hash 72516eb5…)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102)
- **CORRECTED_BY:** CROSS_FAMILY_SCENE3D_PRODUCT_SEMANTIC_REPAIR
- **SUPERSEDES:** CLOSE_GENERIC_TIER_A_BROWSER_EVIDENCE_BEFORE_CUBOID_MERGE
- **THESIS_USE:** AUTHORITATIVE_CORRECTION

## WAVE_ID = CROSS_FAMILY_SCENE3D_PRODUCT_SEMANTIC_REPAIR
- **DATE:** 2026-09-27
- **REPORT:** docs/evaluation/geometry/runs/20260927-cross-family-scene3d-product-semantic-repair/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/20260927-cross-family-scene3d-product-semantic-repair/
- **START_BASE:** 686a8e0e5f8540725c0a500429cc18a7faf1015a
- **CODE_COMMIT:** 5dd9f2b2851cdef64de0272f9a3d2b41bb05ad45
- **MEASUREMENT_COMMIT:** f5fefce02bf6f930c29b58a12979340ac2affe5d
- **EVIDENCE_COMMIT_ROLE:** 5f2f24f064d8f06de41e76353fb61ff5a74e7afa
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (72516eb5… -> 5d8eb3af…, product commit 5dd9f2b2)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102, fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR
- **SUPERSEDES:** NONE (repairs the regression identified by `GENERIC_TIER_A_BROWSER_EVIDENCE_SEMANTIC_CORRECTION`; does not rewrite that historical finding)
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_PENDING_HUMAN_VISUAL_REVIEW

## WAVE_ID = CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR
- **DATE:** 2026-09-28
- **REPORT:** docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/
- **START_BASE:** 532d436611d58023cfabac6020f1ad85e2446e16
- **CODE_COMMIT:** 50a31e0b7124cb038ff5c56dd9c856778a263725
- **ORACLE_HARNESS_COMMIT:** 1dab0f7db516e8ce8eee1280ded4d220a10018d5
- **MEASUREMENT_COMMIT:** e115c31df24efc35fe1d5590e3cab6737b5b13d8
- **EVIDENCE_COMMIT_ROLE:** 09934eb7d0850d3f1f6d5c4f4c79f93b33bb92d9
- **CLASSIFICATION:** VERIFICATION_NOT_CLEAN
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 5d8eb3af… -> 31725284…, CACHE_VERSION unchanged)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102, fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR
- **SUPERSEDES:** NONE (additively corrects the prior readiness conclusion; historical artifacts remain intact)
- **THESIS_USE:** AUTHORITATIVE_CORRECTION_NOT_READY_FOR_HUMAN_REVIEW
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `results/VERIFICATION_SUMMARY.json` · `inputs/human_expected_visibility.json` · `contact-sheet.png` (trong ARTIFACT_DIRECTORY) · recovery inventory `docs/evaluation/geometry/worktree-recovery/WORKTREE_RECOVERY_INVENTORY.json`
- **RUN_ID_POLICY:** LEGACY_LONG_RUN_ID — giữ nguyên đường dẫn; run mới theo `docs/evaluation/RUN_NAMING.md`

## WAVE_ID = VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR
- **DATE:** 2026-09-28
- **REPORT:** docs/evaluation/geometry/runs/w09-verify-cleanup/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w09-verify-cleanup/
- **START_BASE:** 42c736ead3433d32d4cd2b1c3fd93c41e691d3ae
- **CODE_COMMIT:** f337323f599964246507017613cfe3c016e71a32 (backend) · 7b8528a95d364c6a624922d9acff789239ed3ef8 (frontend + harness)
- **MEASUREMENT_COMMIT:** defb77ede20bd952b08ac4996d3a2bf40bcfdb1a
- **EVIDENCE_COMMIT_ROLE:** 774377dd
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 31725284… -> 3bc9415b…, CACHE_VERSION unchanged)
- **CACHE_CHANGE:** NO (CACHE_VERSION 102, fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE (human review FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR, recorded additively in the w10 run; this run's files stay byte-identical)
- **SUPERSEDES:** NONE (additively corrects VERIFICATION_NOT_CLEAN of the occlusion wave; its artifacts and frozen registry remain byte-identical)
- **THESIS_USE:** HISTORICAL_AUTOMATION — human visual review FAILED afterwards; do not cite as visual acceptance. `inputs/REGISTERED_CAMERA_PREIMAGES.json` stays authoritative for the frozen registry.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `results/VERIFICATION_SUMMARY.json` · `results/BACKEND_FAILURE_RECONCILIATION.json` · `diagnostics/VERIFICATION_FAILURE_INVENTORY.json` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `inputs/REGISTERED_CAMERA_PREIMAGES.json` · `images/contact-sheet.png`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE
- **DATE:** 2026-09-29
- **REPORT:** docs/evaluation/geometry/runs/w10-pedagogical-playback/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w10-pedagogical-playback/
- **START_BASE:** be23e88d
- **CODE_COMMIT:** 9dc56ae1 · f5a3adf2 (backend + frontend) · 7a03e50d · f0deaa0d (frontend)
- **MEASUREMENT_COMMIT:** 40ce889fe83b7220195a89f50c22757a02770511 (post-processing 52de6f22)
- **EVIDENCE_COMMIT_ROLE:** 8a09a5d8
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 3bc9415b… -> 875bc19c… -> 8539acbc…)
- **CACHE_CHANGE:** YES (CACHE_VERSION 102 -> 103, user decision; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW (human review FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR, recorded additively in the w11 run; this run's files stay byte-identical)
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW — its images are no longer the ones a reviewer should judge; its automation stays valid for the w10 candidate `8539acbc…`
- **CORRECTS:** VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR (human review FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR)
- **SUPERSEDES:** NONE (w09 and occlusion-wave artifacts and the frozen registry remain byte-identical; the registry's expectations transfer to the new default camera only under `DECLARED_CAMERA_CHANGE`)
- **THESIS_USE:** HISTORICAL_AUTOMATION — human visual review FAILED afterwards (W10-H1…H9); do not cite as visual acceptance.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/VERIFICATION_SUMMARY.json` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/GOLDEN_REVIEW.json` · `images/playback/PLAYBACK_EVIDENCE.json` · `images/crops/CROPS_INDEX.json` · `images/contact-sheet.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `inputs/W09_HUMAN_VISUAL_REVIEW.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW
- **DATE:** 2026-09-29
- **REPORT:** docs/evaluation/geometry/runs/w11-pedagogical-polish/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w11-pedagogical-polish/
- **START_BASE:** b9193766
- **CODE_COMMIT:** f147dde6 (backend) · e186b4cf · e633ad0c · 60292ecf (frontend)
- **MEASUREMENT_COMMIT:** 39e5404686fdf25ddae310759c87c8c64dd8dc41 (trace post-processing ac19e03d)
- **EVIDENCE_COMMIT_ROLE:** 5e3dbab4
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 8539acbc… -> df04a613…, refrozen once)
- **CACHE_CHANGE:** YES (CACHE_VERSION 103 -> 104; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (human review NEEDS_CHANGES, W11-H1…H5, recorded additively in the w12 run; this run's files stay byte-identical)
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE — its images are no longer the ones a reviewer should judge; its automation stays valid for the w11 candidate `df04a613…`, except that its LLM route served a GIVEN length absent from the text (W11-H5, closed in w12)
- **CORRECTS:** HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE (human review FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR)
- **SUPERSEDES:** HUMAN_VISUAL_REVIEW_AND_PEDAGOGICAL_PLAYBACK_CLOSURE for the human verdict only (w10, w09, the occlusion wave and the frozen registry remain byte-identical; the registry's expectations transfer under `DECLARED_CAMERA_CHANGE`)
- **THESIS_USE:** HISTORICAL_AUTOMATION — human visual review NEEDS_CHANGES afterwards (W11-H1…H5); do not cite as visual acceptance.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/VERIFICATION_SUMMARY.json` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/SHEET.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/FORMULA_PROVENANCE_TRACE_BEFORE.json` · `diagnostics/FORMULA_PROVENANCE_TRACE_AFTER.json` · `inputs/W10_HUMAN_VISUAL_REVIEW.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE
- **DATE:** 2026-09-30 … 2026-10-01
- **REPORT:** docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/
- **START_BASE:** a4fd5fec
- **CODE_COMMIT:** 79eb1e59 · 8aaeae80 (backend) · 98b505ef · 233f8720 · 4014f311 (frontend) · d17550c3 (cache)
- **MEASUREMENT_COMMIT:** c243968b1ec263d2ab48040d569eec45efe9cfaa
- **EVIDENCE_COMMIT_ROLE:** 442584cf
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash df04a613… -> 8ffd6d46… -> 548f5b3b…, frozen three times; the last freeze moved only the product commit 8aaeae80 -> 4014f311)
- **CACHE_CHANGE:** YES (CACHE_VERSION 104 -> 105; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION (human review NEEDS_CHANGES, W12-H1…H4, recorded additively in the w13 run; this run's files stay byte-identical)
- **CORRECTS:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW (human review NEEDS_CHANGES)
- **SUPERSEDES:** W11_PEDAGOGICAL_FORMULA_VISUAL_POLISH_AND_HUMAN_REREVIEW for the human verdict only (w11, w10, w09, the occlusion wave and the frozen registry remain byte-identical); inside this run the attempts BROWSER-1 (e115eede) and BROWSER-2 (7b039621, committed in 399fc423) are superseded — `diagnostics/MEASUREMENT_ATTEMPTS.json`
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_548f5b3b — human visual review NEEDS_CHANGES afterwards (W12-H1…H4); do not cite as visual acceptance. It was the latest product measurement until w14 (candidate 40263983, measurement 380db58c); it stays valid for candidate 548f5b3b.
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION — its images are no longer the ones a reviewer should judge (w14 changes the formation of every polyhedral family); this run's files stay byte-identical.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/VERIFICATION_SUMMARY.json` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `results/BACKEND_COUNT_RECONCILIATION.json` · `images/<family>/SHEET.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/hue-gate-known-answer-e115eede/KNOWN_ANSWER.json` · `diagnostics/WORKTREE_CLEANUP.json` · `inputs/W11_HUMAN_VISUAL_REVIEW.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION
- **DATE:** 2026-10-01
- **REPORT:** docs/evaluation/geometry/runs/w13-geometry-preregistration/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w13-geometry-preregistration/
- **START_BASE:** bf5a7907
- **CODE_COMMIT:** NONE (no product code; the docs-audit allow-list in backend/scripts gained the W13/W14 action names)
- **MEASUREMENT_COMMIT:** NONE (offline reader probe only, run at bf5a7907)
- **EVIDENCE_COMMIT_ROLE:** SELF
- **CLASSIFICATION:** ARCHITECTURE_PREREGISTRATION_READY
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (548f5b3b…, product commit 4014f311; verify PASS)
- **CACHE_CHANGE:** NO (CACHE_VERSION 105; verify PASS)
- **CORRECTED_BY:** NONE
- **CORRECTS:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (human review NEEDS_CHANGES)
- **SUPERSEDES:** NONE (w12 stays the latest product automation; w13 adds no images, so nothing is superseded for the human verdict)
- **THESIS_USE:** ARCHITECTURE_AUDIT_AND_PREREGISTRATION — capability-by-layer matrix and the next-wave preregistration; not empirical results, not visual acceptance.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `inputs/W12_HUMAN_VISUAL_REVIEW.json` · `results/ABSOLUTE_ASSUMPTION_INVENTORY.json` · `results/REMAINING_GEOMETRY_CAPABILITY_MATRIX.json` · `diagnostics/SOURCE_GROUNDING_PHRASING_PROBE.json` · `docs/architecture/geometry_capability_matrix_v2.json` · `docs/architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md` · `docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION
- **DATE:** 2026-10-01 … 2026-10-02
- **REPORT:** docs/evaluation/geometry/runs/w14-generic-formation-assumption/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w14-generic-formation-assumption/
- **START_BASE:** ce9c672d
- **CODE_COMMIT:** 44f2dd32 (formation) · d537cf74 (trust policy) · 2f2c97b2 (length vocabulary) · 69d3c985 (sample text, frontend/src) · 733435ac (cache) · a2af56e4 (cleanup; last product commit)
- **MEASUREMENT_COMMIT:** 380db58c37da6088d8dba47647d15ba7ed77cf35
- **EVIDENCE_COMMIT_ROLE:** 54af39a4
- **CLASSIFICATION:** FORMATION_FOUNDATION_INCOMPLETE
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 548f5b3b… -> 40263983…, 105 files, frozen once at a2af56e4)
- **CACHE_CHANGE:** YES (CACHE_VERSION 105 -> 106; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE — w15 traced every Track B failure of this run to a root cause (RC1 coordinates classed as model realisation, RC2 `claimed` relations, RC3 stale demo contracts, RC4/RC5 invalid counterexample witnesses) and shipped the gate; decision W15-D1 settles W14-D1 (a refused program is not in the enforced formation set). This run's files stay byte-identical.
- **CORRECTS:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE (answers its human review W12-H1…H4, as preregistered in w13)
- **SUPERSEDES:** W12_PEDAGOGICAL_TIMELINE_AND_SOURCE_GROUNDING_CLOSURE for the human verdict only (w12, w13, the occlusion wave and the frozen registry remain byte-identical); nothing superseded inside this run
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE — w15 changes what the cross-section shows (the closed fill) and measures a new candidate; a reviewer judges the w15 images.
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_40263983 — not visual acceptance (no human review yet). It was the latest product measurement until w15 (candidate b3b7eb79, measurement c57ebd1b); it stays valid for candidate 40263983. Formation by shape class for compiler and LLM programs (six families and served gold COMPLETED; the refused gold negative n2 AMBIGUOUS_TOPOLOGY); assumption gate NOT shipped — the census is a corpus result inside the certificate scope (C0 ∪ C1 over PHEP_DO_C1), never a soundness proof; the frozen hidden-line expectations do not transfer to the four scenes S4 changed.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/FILMSTRIP.png` · `images/<family>/SHEET.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/S4_INVENTORY_AT_380db58c.json` · `diagnostics/OCCLUSION_TRANSFER_DIAGNOSTIC.json` · `diagnostics/ASSUMPTION_CENSUS.json` · `diagnostics/ASSUMPTION_MECHANISM_DECISION.json` · `diagnostics/SOURCE_GROUNDING_PHRASING_PROBE_W14.json` · `diagnostics/PROOF_CACHE_ROW_W14.json` · `diagnostics/TRUST_POLICY_CALLERS.json` · `diagnostics/WORKTREE_CLEANUP.json` · `inputs/W14_SCOPE_DECISIONS.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE
- **DATE:** 2026-10-02 … 2026-10-03
- **REPORT:** docs/evaluation/geometry/runs/w15-assumption-closure/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w15-assumption-closure/
- **START_BASE:** 4f6a0ab6
- **CODE_COMMIT:** 5dd8e7f5 (solid_faces) · cf57332b (reader + certificate) · 6fa6e582 (fully-read counterexample) · 2305f072 (phrasings, scope) · a1b17fef (symbol-key binding) · 45d014b0 (route wiring, U3) · 33b11a79 (U5) · 8239a2a4 (section fill) · 0579d559 (cache) · d41176f2 (review simplifications) · 909a3a2d (section fill without depth test) · 41a26f11 (final-review soundness fix; last product commit)
- **MEASUREMENT_COMMIT:** c57ebd1b4b34abe14947a97d8169dfead99ab622
- **EVIDENCE_COMMIT_ROLE:** 23cc880a (supersedes 751169dd, measured at e5b88647 on the intermediate candidate aaa5b5bd)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 40263983… -> b3b7eb79…, 107 files; frozen three times — d41176f2 and 909a3a2d gave the intermediate aaa5b5bd…, 41a26f11 gave b3b7eb79)
- **CACHE_CHANGE:** YES (CACHE_VERSION 106 -> 107 in 0579d559, real-row proof; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE — w16 reproduced two soundness gaps of this run's certificate at its RED commit: a plane-equation literal accepted for any proportional text equation, so five wrong-entity programs were served; a relation the text asks to prove read as a premise, so seven programs were served. W16 closed both. It also found that this run's fill was drawn over the solid edges, and that its sheets printed blank refusal cells (the builder read `negative[viewport]`). This run's files stay byte-identical.
- **CORRECTS:** W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION (Track B root causes RC1–RC5 and the shipped gate; W15-D1 settles W14-D1)
- **SUPERSEDES:** W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION for the human verdict only; inside this run, the evidence of 751169dd (M2) is superseded by 23cc880a (M3) after the final-review fix, and the failed first browser attempt is kept apart in `diagnostics/browser-attempt1-c1638891/`
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE — w16 changes how the cross-section fill sits against the edges, completes the refusal panels and measures a new candidate; a reviewer judges the w16 images.
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_b3b7eb79 — not visual acceptance (human review NOT_APPROVED). It was the latest product measurement until w16 (candidate 9bb0aaa7, measurement 7f3658b0); it stays valid for candidate b3b7eb79, with the two certificate gaps w16 closed. The assumption certificate (C0 ∪ C1 over volume/area/distance, closed vocabulary) is a corpus result inside the registered scope, never a general soundness proof; enforcement covers polyhedral texts only (U3).
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/FILMSTRIP.png` · `images/<family>/SHEET.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/ASSUMPTION_CENSUS_W15_R3.json` · `diagnostics/ASSUMPTION_MECHANISM_DECISION_W15_R3.json` · `diagnostics/TRACK_B_ROOT_CAUSE_TABLE.json` · `diagnostics/GOLD_ROW_VERIFICATION.json` · `diagnostics/PROOF_CACHE_ROW_W15.json` · `diagnostics/logs/FAULT_INJECTION_ASSUMPTION_GATE_FINAL.log` · `diagnostics/PONYTAIL_REVIEW.json` · `diagnostics/WORKTREE_CLEANUP.json` · `diagnostics/TEMP_FILE_INVENTORY.json` · `inputs/W15_SCOPE_DECISIONS.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE
- **DATE:** 2026-10-03
- **REPORT:** docs/evaluation/geometry/runs/w16-premerge-closure/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w16-premerge-closure/
- **START_BASE:** 8a339d17
- **CODE_COMMIT:** 24161657 (plane binding) · 93d4ec69 (goal clauses) · 29da8e5a (section fill under the edges, frontend/src) · 2ec02b3a (cache) · 6b120036 (primed plane names; last product commit)
- **MEASUREMENT_COMMIT:** 7f3658b00f48dae854e5ab2527ca0ff3f701f828
- **EVIDENCE_COMMIT_ROLE:** 705970dd (browser, occlusion, playback, sheets, T3, gates); the failed first browser attempt at 55cde06e is kept apart in `diagnostics/browser-attempt1-55cde06e/`
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash b3b7eb79… -> 9bb0aaa7…, 107 files; frozen twice — 2ec02b3a gave the intermediate 8d14469b…, 6b120036 gave 9bb0aaa7)
- **CACHE_CHANGE:** YES (CACHE_VERSION 107 -> 108 in 2ec02b3a, real-row proof; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS — w17 closed this run's declared limit A′ (a construct_section on a correctly pinned plane other than the one the text cuts was certified and served, area 9 where the text gives 16) and the goal-clause datum that grounding still read outside the polyhedral scope; it also traced this run's cube "cạnh 4" refusal image to a fixture-generator defect (the text stayed valid while the contract carried AB = 0). This run's files stay byte-identical.
- **CORRECTS:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE (plane-equation entity binding, goal clauses as premises, fill drawn over the edges, blank refusal cells)
- **SUPERSEDES:** W15_SOURCE_CONSTRAINT_AND_ASSUMPTION_CLOSURE for the human verdict only; inside this run, census round 1 and the first backend fault-injection run (before the primed-name fix) are superseded by round 2 and the final run
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS — w17 adds on-figure labels, the Số đo/Kết quả chips, cause-specific refusal panels and named group steps, and measures a new candidate; a reviewer judges the w17 images.
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_9bb0aaa7 — not visual acceptance (human review NOT_APPROVED). It was the latest product measurement until w17 (candidate d63d6fd4, measurement 99925723); it stays valid for candidate 9bb0aaa7, with limit A′ that w17 closed. The certificate scope of w15 is unchanged; inside it, "same entity" now holds for plane equations, and goal clauses are never premises. Declared limit A′: a construction that uses an entity other than the one the text names is not checked. The census is a corpus result inside the registered scope, never a general soundness proof.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/SHEET.png` · `images/<family>/FILMSTRIP.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/PROBE_W16_PHASE1_6d01511.json` · `diagnostics/ASSUMPTION_CENSUS_W16_R2.json` · `diagnostics/ASSUMPTION_MECHANISM_DECISION_W16_R2.json` · `diagnostics/PROOF_CACHE_ROW_W16.json` · `diagnostics/logs/FAULT_INJECTION_W16_FINAL.log` · `diagnostics/logs/FAULT_INJECTION_W16_FRONTEND.log` · `diagnostics/PONYTAIL_REVIEW.json` · `diagnostics/WORKTREE_CLEANUP.json` · `diagnostics/TEMP_FILE_INVENTORY.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS
- **DATE:** 2026-10-03 / 2026-10-04
- **REPORT:** docs/evaluation/geometry/runs/w17-operation-annotations/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w17-operation-annotations/
- **START_BASE:** dd6e86b0
- **CODE_COMMIT:** 2678b363 (operation binding) · 0b71502b (goal-only givens, refusal causes) · ce9a4c1f (group-step label) · 8e002028 (annotation binding) · fa5f8382 (labels and chips, frontend/src) · 2c7d4134, 240ecba5, dbb38b95 (Task 7, frontend/src) · fadfd10e (cache) · add4afb0 (ponytail) · d3817d5f (final-review fix; last product commit)
- **MEASUREMENT_COMMIT:** 99925723e6179e9f67852a2aa393db163dd07c4f
- **EVIDENCE_COMMIT_ROLE:** 781c14e5 (browser, occlusion, playback, sheets, T3, gates, frontend fault injections); kept apart: the complete measurement at c5592c1a on the intermediate candidate (`diagnostics/evidence-intermediate-c5592c1a/`, images at f07b0d24) and the failed attempt 1 at 83f101e4 (`diagnostics/browser-final-attempt1-83f101e4/`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 9bb0aaa7… -> d63d6fd4…, 109 files; frozen twice — add4afb0 gave the intermediate d4a24eba…, d3817d5f gave d63d6fd4)
- **CACHE_CHANGE:** YES (CACHE_VERSION 108 -> 109 in fadfd10e, real-row proof; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS — w18 checks point constructions (midpoints, projections) against the text relation by identity, closing part of this run's declared limit "constructions other than section cuts are not checked": before w18 a projection onto the wrong line or plane, a swapped "lần lượt" list, a renamed target and a same-coordinate identity swap were served. This run's files stay byte-identical.
- **CORRECTS:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE (declared limit A′, goal clauses read as data by grounding outside the polyhedral scope, the cube "cạnh 4" refusal image)
- **SUPERSEDES:** W16_PREMERGE_SOUNDNESS_AND_VISUAL_EVIDENCE_CLOSURE for the human verdict only; inside this run, the measurement at c5592c1a on the intermediate candidate is superseded by the one at 99925723, census round 1 by round 2, and the earlier fault-injection runs by run 3
- **SUPERSEDED_FOR_HUMAN_VERDICT:** W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS — w18 replaces the two chips with "Hiện tất cả" and a compact default, makes the inspector the one explanation place, draws distance witnesses, adds the W18 refusal panels, and measures a new candidate; a reviewer judges the w18 images.
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_d63d6fd4 — not visual acceptance (human review NOT_APPROVED). Inside the registered scope, a served section is cut by the plane and solid the text names, a value stated only in a goal clause is never a datum, and every refusal names its cause; the numbers on the figure are bound by the backend. The census is a corpus result inside the registered scope, never a general soundness proof; constructions other than section cuts are not checked against the text. It was the latest product measurement until w18 (candidate d3b4cab9).
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/SHEET.png` · `images/<family>/FILMSTRIP.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/OPERATION_BINDING_REPRODUCTION_bce0b7bb.json` · `diagnostics/NEGATIVE_FIXTURE_RECONCILIATION_0b71502b.json` · `diagnostics/ASSUMPTION_CENSUS_W17_R2.json` · `diagnostics/ASSUMPTION_MECHANISM_DECISION_W17_R2.json` · `diagnostics/PROOF_CACHE_ROW_W17.json` · `diagnostics/logs/FAULT_INJECTION_W17_R3.log` · `diagnostics/logs/FAULT_INJECTION_W17_FRONTEND_R3.log` · `diagnostics/PONYTAIL_REVIEW_W17.json` · `diagnostics/WORKTREE_CLEANUP.json` · `diagnostics/TEMP_FILE_INVENTORY.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS
- **DATE:** 2026-10-04
- **REPORT:** docs/evaluation/geometry/runs/w18-binding-focus/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w18-binding-focus/
- **START_BASE:** 0ec2bbbb
- **CODE_COMMIT:** 84ce7b70 (construction binding) · f2a040f9 (label roles, same_as, witness, S(T)) · b6868e19 (focused labels, one explanation place, witness layer; frontend/src) · 1e8c5658 (cache) · 7a06ee47 (ponytail; last product commit)
- **MEASUREMENT_COMMIT:** 0ca3accf7e921797e75aebcbc19e3a05b2557859
- **EVIDENCE_COMMIT_ROLE:** 4a9db1ff (browser, occlusion, playback, sheets, T3, gates, frontend fault injections run 2); kept apart: acceptance attempt 1 at 8caa8307 (`diagnostics/evidence-attempt1-8caa8307/`), superseded by the harness fix 1d8dfc6f
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash d63d6fd4… -> d3b4cab9…, 110 files; frozen once at 7a06ee47)
- **CACHE_CHANGE:** YES (CACHE_VERSION 109 -> 110 in 1e8c5658, real-row proof; lock 5cfb53a1; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE — w20 checks a text-relation target defined by coordinates (directly or through an alias chain) and refuses it in every scope, closing this run's deferred limit `ISSUE-ARCH-CONSTRUCTION-BINDING-LITERAL-TARGET` (amendment §17); the w18 artifacts stay as they are
- **CORRECTS:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS (point constructions — midpoints, projections — not checked against the text)
- **SUPERSEDES:** W17_OPERATION_BINDING_AND_ON_SCENE_ANNOTATIONS for the human verdict only; inside this run, acceptance attempt 1 (8caa8307) is superseded by attempt 2 (0ca3accf), the backend fault-injection runs 1–2 by run 3, and the frontend run 1 by run 2
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_d3b4cab9 — not visual acceptance (human review NOT_APPROVED). Inside the registered vocabulary (§16), a point the text defines as a midpoint or projection is built on the entities the text names, checked by identity; a mismatch is refused in every scope and named to the learner; numbers on the figure carry backend roles and one explanation place. The census is a corpus result, never a general proof; centres, intersections and unread phrasings are not checked.
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/HIDDEN_EDGE_CROPS.json` · `images/<family>/SHEET.png` · `images/<family>/FILMSTRIP.png` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_bb9f7004.json` · `diagnostics/CONSTRUCTION_BINDING_REPRODUCTION_84ce7b70.json` · `diagnostics/CONSTRUCTION_BINDING_CENSUS_W18.json` · `diagnostics/CONSTRUCTION_BINDING_DECISION_W18.json` · `diagnostics/PROOF_CACHE_ROW_W18.json` · `diagnostics/logs/FAULT_INJECTION_W18_R3.log` · `diagnostics/logs/FAULT_INJECTION_W18_FRONTEND_R2.log` · `diagnostics/PONYTAIL_REVIEW_W18.json` · `diagnostics/WORKTREE_CLEANUP.json` · `diagnostics/TEMP_FILE_INVENTORY.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W19_DOCS_REORGANIZATION_AND_RESEARCH_EVIDENCE_CURATION
- **DATE:** 2026-10-04
- **REPORT:** docs/evaluation/geometry/runs/w19-docs-organization/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w19-docs-organization/
- **START_BASE:** 6d0e6321
- **CODE_COMMIT:** NONE for the product. Docs tooling only: `backend/scripts/audit_docs_information_architecture.py` (`audit_docs_layout`, `PROJECT_DOCS`, `NAVIGATION_DOCS`, allowed next actions) and `backend/tests/geometry/test_docs_information_architecture.py` (four tests), one doc path in `backend/tests/geometry/test_curriculum_coverage.py`
- **MEASUREMENT_COMMIT:** NONE (no product measurement; verification of the final tree in a detached clean worktree, see `HANDOFF.md`)
- **EVIDENCE_COMMIT_ROLE:** a5c2e6f2 (structure + migration, inventory, migration map) · a44631a9 (claim map, hubs, closed docs root, catalog) · the documentation commit (state, report, handoff, verification)
- **CLASSIFICATION:** DOCS_REORGANIZED_AND_VERIFIED
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (d3b4cab96c69a09f…, `--verify` exit 0)
- **CACHE_CHANGE:** NO (110, `lock_cache_identity.py --verify` exit 0)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (no report or artifact is corrected)
- **SUPERSEDES:** as claim authority only — `THESIS_READINESS.md`, `thesis/CLAIM_EVIDENCE_MATRIX.md`, `research/CLAIM_TO_EVIDENCE_MAP.md` (archived byte-identical in `docs/legacy/research/`) by `docs/research/CLAIM_EVIDENCE_MAP.md`
- **THESIS_USE:** NAVIGATION_AND_CLAIM_AUTHORITY — no new measurement; the claim map quotes existing evidence only and lists 0 rows at HUMAN_REVIEWED
- **AUTHORITATIVE_FILES:** `README.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MANIFEST.json` · `inventory/INVENTORY.json` · `inventory/MIGRATION_MAP.json` · `verification/FROZEN_IDENTITY.json` · `verification/LINKS_FINAL.json` · `verification/OLD_PATH_CONSUMERS_FINAL.json` · `verification/logs/`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE
- **DATE:** 2026-10-04 → 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/w20-cleanup-premerge/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/w20-cleanup-premerge/
- **START_BASE:** 2cb4ed8c
- **CODE_COMMIT:** 65c90bde (construction binding §17) · bedb1040 (CACHE_VERSION 110 -> 111) · a4f771b3 (comments only) · 4e647861 + 654beda3 (`run_reconciliation(out_dir)` and its tests)
- **MEASUREMENT_COMMIT:** 5fbb397b7d485de183526451ae9003631c395d94 (authoritative verification in a clean detached worktree); probe, census and cache proof at 65c90bde
- **EVIDENCE_COMMIT_ROLE:** f0edcd11 (labels + before probe, before any fix) · 8b6a1a3a (after probe, census, fault injections r1–r2) · 31716373 (cleanup inventory + deletion log) · the documentation commit (T3, gates, final probe, fault injections r3, report, handoff, manifest)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash d3b4cab9… -> 2a15102b… (intermediate, bedb1040) -> 27c31de6…, 110 files; frozen twice, declared in `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`)
- **CACHE_CHANGE:** YES (CACHE_VERSION 110 -> 111 in bedb1040, real-row proof; lock ac241a8d; fingerprint b1714b56… unchanged)
- **CORRECTED_BY:** COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE (scope note only: W20 was a correctness closure plus a bounded cleanup; the full docs review is the run cuboid-final-review; W20 measurements and conclusions unchanged)
- **CORRECTS:** W18_CONSTRUCTION_BINDING_AND_FOCUSED_ANNOTATIONS (deferred limit: a text-relation target defined by coordinates was neither checked nor recorded by `construction_binding`)
- **SUPERSEDES:** inside this run only — fault-injection logs r1 and r2 by r3 (clean worktree), probe `before` (23 rows) by `before-r2` (27 rows, labels amended before any fix)
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_27c31de6 — not visual acceptance (human review NOT_APPROVED). Inside the §16.1 vocabulary, a text-relation target the program defines by coordinates is refused in every scope (claim C6 of `docs/research/CLAIM_EVIDENCE_MAP.md`)
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `diagnostics/literal_target_corpus/LABELS.json` · `results/LITERAL_TARGET_PROBE_before-r2_2cb4ed8c.json` · `results/LITERAL_TARGET_PROBE_after_65c90bde.json` · `results/LITERAL_TARGET_PROBE_final_5fbb397b.json` · `diagnostics/CONSTRUCTION_BINDING_DECISION_W20.json` · `diagnostics/PROOF_CACHE_ROW_W20.json` · `inventory/CLEANUP_INVENTORY.json` · `inventory/DELETION_LOG.json` · `results/logs/T3_FULL_GATE_5fbb397b.log` · `results/logs/GATES_5fbb397b.log` · `results/logs/FAULT_INJECTION_W20_r3.log`
- **RUN_ID_POLICY:** SHORT_RUN_ID (`wNN-short-slug`, `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE
- **RUN_ID:** cuboid-final-review (closing run of the work cuboid-visual-semantic-closure; no wave number)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/cuboid-final-review/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/cuboid-final-review/
- **START_BASE:** 4048ff83
- **CODE_COMMIT:** 284a9bfa (refusal card of §17: message from `reason_subjects`, label from `reason_code`) · fac2769e (tooling: focused browser check)
- **MEASUREMENT_COMMIT:** a1c53cdbf9cd35667f0e1d918584e880a67daab3 (authoritative verification in a clean detached worktree); cache proof at 284a9bfa against 4048ff83; inventories at 4048ff83 (before) and a1c53cdb (after)
- **EVIDENCE_COMMIT_ROLE:** 42dd1af5 (docs inventory, verbatim history split, cleanup log) · 284a9bfa (red and green logs) · 6ec40806 (cache proof) · a1c53cdb (refreeze, pre-freeze log) · the documentation commit (T3, gates, browser check and images, inventories, report, handoff) · the final docs-gate log commit
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES (learner-facing only)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (tree_hash 27c31de6… -> b2d4187a…, 110 files; frozen once at 284a9bfa, declared in `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`)
- **CACHE_CHANGE:** NO (111; `diagnostics/cache_proof/CACHE_DECISION_CFR.json`: served envelopes byte-identical, refusals never cached; lock `--verify` exit 0)
- **CORRECTED_BY:** CUBOID_INVARIANT_RECONCILIATION_AND_MERGE_HANDOFF (count only: the rows of ARCHITECTURE_MAP §5 with dead pointers were 24, not 22 — #9 and #12 inherit through "như trên"; this run's artifacts unchanged)
- **CORRECTS:** W20_REPOSITORY_CLEANUP_AND_PREMERGE_CORRECTNESS_CLOSURE (scope note only: W20's cleanup was bounded; the full docs review is this run)
- **SUPERSEDES:** inside this run only — browser check attempt 1 (stopped by the dist freshness guard) by attempt 2; the docs inventory committed in 42dd1af5 by the inventories measured at 4048ff83 and a1c53cdb
- **THESIS_USE:** AUTHORITATIVE_AUTOMATION_FOR_CANDIDATE_b2d4187a — not visual acceptance (human review NOT_APPROVED). The §17 refusal states the verification limit in learner terms; the docs keep one current authority per topic, with the informatics-era history kept verbatim in `docs/legacy/`
- **AUTHORITATIVE_FILES:** `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `REPORT.md` · `inventory/DOCS_INVENTORY.json` · `inventory/DOCS_INVENTORY_BEFORE_4048ff83.json` · `inventory/HISTORY_SPLIT.json` · `inventory/CLEANUP_LOG.json` · `diagnostics/cache_proof/CACHE_DECISION_CFR.json` · `results/BROWSER_REFUSAL_CFR.json` · `results/logs/T3_FULL_GATE_a1c53cdb.log` · `results/logs/GATES_a1c53cdb.log` · `images/`
- **RUN_ID_POLICY:** CLOSING_RUN_OF_A_WORK (short id set by the brief, an abbreviation of the task slug; `docs/evaluation/RUN_NAMING.md` — waves of new works use `<task-slug>-wNN`)

## WAVE_ID = CUBOID_INVARIANT_RECONCILIATION_AND_MERGE_HANDOFF
- **RUN_ID:** cuboid-acceptance (acceptance package of the work cuboid-visual-semantic-closure; no wave number)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/cuboid-acceptance/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/cuboid-acceptance/
- **START_BASE:** 903e874c
- **CODE_COMMIT:** NONE (documentation only; product bytes equal to candidate b2d4187a, product commit 284a9bfa)
- **MEASUREMENT_COMMIT:** the documentation commit of this run (invariant checks and docs gates in a clean detached worktree); product evidence reused, not re-measured: a1c53cdb (cuboid-final-review) and 0ca3accf (w18)
- **EVIDENCE_COMMIT_ROLE:** documentation commit (reconciliation, check script, living docs) · final log commit (`results/logs/INVARIANT_CHECKS_FINAL.log`, `results/logs/DOCS_GATES_FINAL.log`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (b2d4187a…, `--verify` in the clean worktree)
- **CACHE_CHANGE:** NO (111; no product byte changed)
- **CORRECTED_BY:** NONE
- **CORRECTS:** COMPLETE_DOCS_CLEANUP_AND_CUBOID_BRANCH_ACCEPTANCE (count only: 24 invariant rows with dead pointers, not 22)
- **SUPERSEDES:** NONE
- **THESIS_USE:** AUTHORITATIVE_RECONCILIATION_OF_ARCHITECTURE_MAP_§5 — 24 rows: 9 CURRENT_ENFORCED, 1 CURRENT_UNVERIFIED (#14, ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM), 14 HISTORICAL_NOT_APPLICABLE, 0 VIOLATED; not visual acceptance (human review NOT_APPROVED)
- **AUTHORITATIVE_FILES:** `RUN.json` · `HANDOFF.md` · `REPORT.md` · `results/INVARIANT_RECONCILIATION.json` · `diagnostics/invariant_checks_cacc.sh` · `diagnostics/cacc_gates.sh` · `results/logs/INVARIANT_CHECKS_FINAL.log` · `results/logs/DOCS_GATES_FINAL.log`
- **RUN_ID_POLICY:** CLOSING_RUN_OF_A_WORK (short id set by the brief; `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = CUBOID_ACCEPTANCE_AND_DIRECT_MAIN_INTEGRATION
- **RUN_ID:** cuboid-merge (review package and integration of the work cuboid-visual-semantic-closure; no wave number)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/cuboid-merge/REVIEW.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/cuboid-merge/
- **START_BASE:** 37b23f04
- **CODE_COMMIT:** NONE (documentation only; product commit 284a9bfa, candidate b2d4187a unchanged)
- **MEASUREMENT_COMMIT:** fixture transfer at 0ca3accf (w18 measurement) and 37b23f04, clean detached worktrees, offline generator; gates at the documentation commit of this run
- **EVIDENCE_COMMIT_ROLE:** documentation commit (REVIEW, HANDOFF, RUN.json, FIXTURE_TRANSFER.json, TRANSFER.log, scripts, living docs) · final log commit (`results/logs/GATES_FINAL.log`)
- **CLASSIFICATION:** MERGED_AND_PUSHED (user approval A–F in `APPROVAL.md`; main fast-forwarded to c282a5f3 and pushed; integrated-tree gates `results/logs/INTEGRATED_MAIN_GATES.log`)
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO
- **CACHE_CHANGE:** NO
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (extends the w18 visual evidence to candidate b2d4187a; w18 artifacts unchanged)
- **SUPERSEDES:** NONE
- **THESIS_USE:** TRANSFER_OF_W18_VISUAL_EVIDENCE_TO_CANDIDATE_b2d4187a — the regenerated w18 fixtures are byte-exact (manifest 10dbe2de…), the 32 current fixtures differ only in product_commit_sha/product_tree_sha, frontend changes are confined to the refusal card; not visual acceptance (human review NOT_APPROVED)
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `HANDOFF.md` · `RUN.json` · `results/FIXTURE_TRANSFER.json` · `results/logs/TRANSFER.log` · `diagnostics/fixture_transfer_cmerge.py` · `diagnostics/cmerge_gates.sh` · `results/logs/GATES_FINAL.log`
- **RUN_ID_POLICY:** CLOSING_RUN_OF_A_WORK (short id set by the brief; `docs/evaluation/RUN_NAMING.md`)

## WAVE_ID = REGULAR_SQUARE_PYRAMID_AND_PEDAGOGICAL_UI
- **RUN_ID:** regular-square-pyramid-w01 (task regular-square-pyramid, wave W1; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w01/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w01/
- **START_BASE:** 38d41588
- **CODE_COMMIT:** 3bdada32 · ae9c72a5 · b2d224f6 · 98e2b8f7 · 9d66c603 · de5b2331 · ad7172ab (final self-review fix)
- **MEASUREMENT_COMMIT:** ed37f9fa (clean detached worktree with a space in its path; browser suite attempt 3, occlusion, playback, builder); transferred to candidate 5234c37e at b5cf4503 (37/37 envelopes byte-identical, frontend/src unchanged); T3 and identity gates at the final documentation commit
- **EVIDENCE_COMMIT_ROLE:** 025bbff4 (evidence) · state commit (`diagnostics/logs/T3_FULL_GATE_*.log`, `GATES_*.log`, `MEASUREMENT_ATTEMPTS.json`, `MANIFEST.json`)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (b2d4187a… → 4629c3e8… at de5b2331, intermediate → 5234c37e… at ad7172ab; two freezes)
- **CACHE_CHANGE:** YES (CACHE_VERSION 111 -> 112 in de5b2331, real-row proof `diagnostics/PROOF_CACHE_ROW_W01.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (the w18/cuboid evidence describes b2d4187a and earlier candidates and stays as it is)
- **SUPERSEDES:** NONE
- **THESIS_USE:** REGULAR_SQUARE_PYRAMID_CERTIFICATE_AND_ROADMAP_0_1_UI — claim C7 and the W1 notes of B2/D5 in `docs/research/CLAIM_EVIDENCE_MAP.md`; offline only; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REPORT.md` · `HANDOFF.md` · `RUN.json` · `diagnostics/corpus/LABELS.json` · `diagnostics/PREREGISTRATION_CORRECTIONS.json` · `diagnostics/corpus/LABELS_R2.json` · `diagnostics/PROOF_CACHE_ROW_W01.json` · `diagnostics/PROOF_CACHE_ROW_W01_R2.json` · `diagnostics/SCOPE_LENGTH_CLUE_PROBE_1310658b.json` · `results/FIXTURE_TRANSFER_b5cf4503_r2.json` · `results/BROWSER_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = REGULAR_SQUARE_PYRAMID_PEDAGOGICAL_CLOSURE
- **RUN_ID:** regular-square-pyramid-w02 (task regular-square-pyramid, wave W2; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-05
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w02/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w02/
- **START_BASE:** e821b9b5 (W1 head)
- **CODE_COMMIT:** 2a63da7d · 9f454d6b · 71cf0e80 · 6ca3b35e · c86cf53c · e68fa199 (CACHE_VERSION 113) · 7a88a789 · c5142f07 · 527d642e · 75a0af9a · 70665542 (CRLF-safe test; divergence declaration at 113)
- **MEASUREMENT_COMMIT:** 94200b50403bdf823eb49697d54c0cb53e8e4ccb (cloud, clean detached CRLF worktree with a space in its path; browser suite, W2 probe, occlusion, playback, builder); earlier attempts at c453fae3, 527d642e, bac5d80f, 4a6af4e9 kept (`diagnostics/MEASUREMENT_ATTEMPTS.json`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (5234c37e… → d3de9c44…; four freezes, same tree hash, product commit 70665542; evidence of 94200b50 transferred, `results/EVIDENCE_TRANSFER_70665542.json`)
- **CACHE_CHANGE:** YES (CACHE_VERSION 112 -> 113 in e68fa199, row proof `diagnostics/PROOF_CACHE_ROW_W02.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** regular-square-pyramid-w03 — PC1-W2 restored to the W18 expectation (`annotation_id: d_kq`); the hidden-helper exemption of `no_static_frames`, the structured-reference check and `every_geometry_step_changes_the_figure` removed (the W12 invariant holds without it); `camera_settled_rotated_neutral` and cross-section `causal_restore` reclassified as environment (green locally at fe68b4ca). W2 artifacts unchanged
- **CORRECTS:** NONE (W1 artifacts unchanged; the W1 equal-value height rule is replaced in code, not in W1 evidence)
- **SUPERSEDES:** NONE
- **THESIS_USE:** REGULAR_SQUARE_PYRAMID_PEDAGOGICAL_CLOSURE — claims C8 and D6 in `docs/research/CLAIM_EVIDENCE_MAP.md`; cloud measurement, local acceptance and human review pending
- **AUTHORITATIVE_FILES:** `REPORT.md` · `HANDOFF.md` · `RUN.json` · `diagnostics/PROOF_CACHE_ROW_W02.json` · `diagnostics/PREREGISTRATION_CORRECTIONS.json` · `diagnostics/ENV_CAMERA_SETTLE_BASELINE.json` · `diagnostics/MEASUREMENT_ATTEMPTS.json` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `results/EVIDENCE_TRANSFER_70665542.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = REGULAR_SQUARE_PYRAMID_LOCAL_ACCEPTANCE
- **RUN_ID:** regular-square-pyramid-w03 (task regular-square-pyramid, wave W3; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-06
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w03/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w03/
- **START_BASE:** fe68b4ca (cloud W2 head, fast-forwarded)
- **CODE_COMMIT:** 824924d7 (H-W2-4) · 45beaed3 (H-W2-2; CACHE_VERSION 114) · a5d233ce (scenario tree-hash pin)
- **MEASUREMENT_COMMIT:** a5d233ce4e635b0228f04af55aa04f3407d4a8d8 (local, clean detached CRLF worktree with a space in its path; browser suite, W2 probe, occlusion, playback, builder); baseline at fe68b4ca (`diagnostics/baseline_fe68b4ca/`) and attempt 1 at 47941832 (`diagnostics/attempts/`) kept (`MEASUREMENT_ATTEMPTS.json`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit 0d0d1de3 after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at 4c0f9219)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (d3de9c44… → 5dec4572…; one freeze at 45beaed3)
- **CACHE_CHANGE:** YES (CACHE_VERSION 113 -> 114 in 45beaed3, row proof `diagnostics/PROOF_CACHE_ROW_W03.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-square-pyramid-w02 (PC1-W2; the hidden-helper gate exemption; the cloud classification of two browser gates) — by a new layer, W2 files untouched
- **SUPERSEDES:** NONE
- **THESIS_USE:** REGULAR_SQUARE_PYRAMID_LOCAL_ACCEPTANCE — local measurement of the W1/W2 claims; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `diagnostics/PROOF_CACHE_ROW_W03.json` · `diagnostics/baseline_fe68b4ca/` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = SHARED_SIMULATION_UI_CLOSURE
- **RUN_ID:** regular-square-pyramid-w04 (task regular-square-pyramid, wave W4; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-06
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w04/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w04/
- **START_BASE:** f3db0f6f (W3 head)
- **CODE_COMMIT:** ce44eb38 · 98b1ce8d · 270cae4e · a1c17714 · e41b0ab1 · aa754cb9 (CACHE_VERSION 115) · c8c49f3c · ecbe55c0 · 53e4bec5
- **MEASUREMENT_COMMIT:** 103494c4 (local, clean detached CRLF worktree with a space in its path; browser suite, W2 probe, W4 panels probe, SM control, occlusion, playback, builder); attempts 1–3 at d7154ab8 and 643b7d7a kept (`diagnostics/attempts/`, `MEASUREMENT_ATTEMPTS.json`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit b4f924c1 after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at d6e41d80)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (5dec4572… → 8a27a58b…; three freezes, same tree hash, product commit 53e4bec5)
- **CACHE_CHANGE:** YES (CACHE_VERSION 114 -> 115 in aa754cb9, row proof `diagnostics/PROOF_CACHE_ROW_W04.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (W1–W3 files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** SHARED_SIMULATION_UI_CLOSURE — presentation layer of the simulation (panels, layout, selection); human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `PLAN.md` · `diagnostics/PANEL_INVENTORY.md` · `diagnostics/PROOF_CACHE_ROW_W04.json` · `diagnostics/scene_hash/SCENE_DIFF.json` · `diagnostics/sm_overlap/` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/SM_OVERLAP_AFTER_103494c4.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = IMMERSIVE_SIMULATION_AND_ARCHITECTURE_SLICE
- **RUN_ID:** regular-square-pyramid-w05 (task regular-square-pyramid, wave W5; `docs/evaluation/RUN_NAMING.md`)
- **DATE:** 2026-10-06/07
- **REPORT:** docs/evaluation/geometry/runs/regular-square-pyramid-w05/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-square-pyramid-w05/
- **START_BASE:** 73bc404e (W4 head)
- **CODE_COMMIT:** c15e6fab · 470adc3a · 82225a7b (harness c1070389 · f01df0e5)
- **MEASUREMENT_COMMIT:** f01df0e5 (local, clean detached CRLF worktree with a space in its path; browser suite, W2 probe, W4 panels probe, W05 focus probe, occlusion, playback, builder); attempts 1–3 at a588f8db, c1070389, 74c91060 kept (`diagnostics/attempts/`, `MEASUREMENT_ATTEMPTS.json`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit 3b31aa18 after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at 4123fb4f)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (8a27a58b… → 5e1c0639…; two freezes, same tree hash, product commit 82225a7b)
- **CACHE_CHANGE:** NO (CACHE_VERSION 115; `diagnostics/cache_proof/CACHE_DECISION_W05.json`)
- **CORRECTED_BY:** regular-triangular-pyramid-w01 `corrections/W05_RECORD_CORRECTION.json` (attempt-4 record missing from `MEASUREMENT_ATTEMPTS.json`; REPORT §4 node harness 93/93 → 91 pass, 2 skipped, 0 fail; W5 files untouched)
- **CORRECTS:** regular-square-pyramid-w01 `LABELS_R2.json` row R2_L1 (by a new layer; W1 files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** focused simulation workspace (presentation) + chained-equality source reader; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `PLAN.md` · `diagnostics/TOOL_INVENTORY.md` · `diagnostics/SKILL_NOTES.md` · `diagnostics/corpus/LABELS_W05.json` · `diagnostics/cache_proof/` · `results/BROWSER_EVIDENCE.json` · `results/W05_FOCUS_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W02_CLOSURE_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE
- **RUN_ID:** regular-triangular-pyramid-w01 (task regular-triangular-pyramid, wave W1; `docs/evaluation/RUN_NAMING.md`; kept on `feat/regular-square-pyramid` by user instruction — `RUN.json`)
- **DATE:** 2026-10-07
- **REPORT:** docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/REPORT.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/
- **START_BASE:** e9435d67 (W5 head)
- **CODE_COMMIT:** 983cfc16 · 82beaf62 · df614b30 · 3487c0a7 · e7b92e49 · 1e90ca0e (harness 4e285690; cleanup 0d4c4f8b; labels/oracle/amendment §18 before the change dc0a804b)
- **MEASUREMENT_COMMIT:** 1bb11018 (attempt 3; local, clean detached CRLF worktree with a space in its path; suite, W02, W04, W05, occlusion, playback, builder, prune; W02 and W04 cross_section rerun alone at the same commit); attempts 1 (aa583ad9) and 2 (1bb11018) kept (`MEASUREMENT_ATTEMPTS.json`, `diagnostics/attempts/`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit c08a1eed after the measurement (results, images, inputs, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at aa845902; first T3 at d2e8a778 failed on a stale fixture-count lock, fixed)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (5e1c0639… → 92c9e198…; two freezes, same tree hash, product commit 1e90ca0e)
- **CACHE_CHANGE:** YES (CACHE_VERSION 115 -> 116 in 82beaf62; `diagnostics/cache_proof/CACHE_DECISION.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-square-pyramid-w05 record (`corrections/W05_RECORD_CORRECTION.json`; W5 files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** regular triangular pyramid / regular tetrahedron in a declared exact (ℚ³) domain with honest refusal outside it; selective image retention; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `REVIEW.md` · `REPORT.md` · `HANDOFF.md` · `RUN.json` · `MEASUREMENT_ATTEMPTS.json` · `PLAN.md` · `diagnostics/corpus/LABELS.json` · `diagnostics/oracle_rtp_w01.py` · `diagnostics/fault_injection_rtp_w01.py` · `diagnostics/cache_proof/CACHE_DECISION.json` · `inputs/REVIEW_SET.json` · `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` · `results/IMAGE_POLICY.json`
- **RUN_ID_POLICY:** TASK_WAVE (`<task-slug>-wNN`)

## WAVE_ID = EXACT_DIMENSIONS_AND_CAPTURE_POLICY
- **RUN_ID:** exact-dimensions (task exact-dimensions; `docs/evaluation/RUN_NAMING.md` naming policy 2026-10-07; same branch)
- **DATE:** 2026-10-07/08
- **REPORT:** docs/evaluation/geometry/runs/exact-dimensions/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/exact-dimensions/
- **START_BASE:** 4ceadd55
- **CODE_COMMIT:** 1c8f3cb4 · de6d3e35 · 14892061 · 0ed6332f · 6c89abcd · ed3ae208 (harness d4834d92, 2d62f69c; plan/labels/oracle before the change 1c91f90d)
- **MEASUREMENT_COMMIT:** 3bbb8052 (fixtures, build, scene controls, panels, focus) · fe83c46e (suite, occlusion) · d51db4e2 (playback, builder); local clean detached CRLF worktree with a space in its path; only failed steps rerun
- **EVIDENCE_COMMIT_ROLE:** evidence commit c5cae8af (results, images, fixtures, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 FULL_PRODUCT_GATE_PASS + identity gates at 4ef0a02e)
- **PRODUCT_CHANGE:** YES
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (92c9e198… → e1927f84…; product commit ed3ae208)
- **CACHE_CHANGE:** YES (CACHE_VERSION 116 -> 117 in ed3ae208; `cache/decision.json`; semantic environment b1714b56… unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** regular-triangular-pyramid-w01 `diagnostics/corpus/LABELS.json` rows N5, N5b, U1–U4 and regular-square-pyramid-w01 row U3_regular_triangular (by `label_corrections.json`; earlier files untouched); candidate register by `inputs/candidate_divergence.json`
- **SUPERSEDES:** NONE
- **THESIS_USE:** rational sizes via an affine chart + Gram metric derived from the text; source-side capture policy; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `labels.json` · `label_corrections.json` · `oracle.py` · `capture_counts.json` · `cache/` · `inputs/REVIEW_SET.json` · `inputs/candidate_divergence.json` · `results/BROWSER_EVIDENCE.json` · `results/PLAYBACK_EVIDENCE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W05_FOCUS_PROBE.json` · `images/` · `diagnostics/attempt1–3/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = REPO_CLEANUP
- **RUN_ID:** repo-cleanup (task repo-cleanup; same branch)
- **DATE:** 2026-10-08
- **REPORT:** docs/evaluation/geometry/runs/repo-cleanup/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/repo-cleanup/
- **START_BASE:** 2c2dfbbf
- **CODE_COMMIT:** 88769dc5 · 8ff42b58 · 67e11671 · 11bea4a7 · be4b8287
- **MEASUREMENT_COMMIT:** NONE (no browser or live measurement; candidate refreeze 372f78c2)
- **EVIDENCE_COMMIT_ROLE:** inventory and relocated snapshot in the run directory
- **CLASSIFICATION:** CLEANUP_COMPLETE (T3 FULL_PRODUCT_GATE_PASS at 645705ae; identity gates green at 2da4cdeb)
- **PRODUCT_CHANGE:** YES (dead code, unused /api/explain)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (e1927f84… → b4a33205…; product commit be4b8287)
- **CACHE_CHANGE:** NO (CACHE_VERSION 117; cache identity lock unchanged)
- **CORRECTED_BY:** NONE
- **CORRECTS:** exact-dimensions `inputs/candidate_divergence.json` (current candidate) by `runs/repo-cleanup/inputs/candidate_divergence.json`
- **SUPERSEDES:** NONE
- **THESIS_USE:** none
- **AUTHORITATIVE_FILES:** `report.md` · `handoff.md` · `run.json` · `inventory.json` · `code_index_removed_entries.md` · `relocated/capability-descriptors.json` · `inputs/candidate_divergence.json` · `diagnostics/freeze_be4b8287.log`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = DOCUMENTATION_AND_NAMING_CLEANUP
- **RUN_ID:** docs-cleanup (task docs-cleanup; same branch)
- **DATE:** 2026-10-08
- **REPORT:** docs/evaluation/geometry/runs/docs-cleanup/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/docs-cleanup/
- **START_BASE:** 2a7179a9
- **CODE_COMMIT:** a993aa8f · c1a291ba · 8c66249d · 9efb8af6 · artifact cleanup from `4acd1f61` · report organization `23aff0ad`/`a3448c71` · product/consolidation `f967ba24` · candidate `267c195a` · consumer/guard sync `838237fe`
- **MEASUREMENT_COMMIT:** NONE (0 model requests, 0 screenshots); independent manifests retained as `run-artifact-cleanup.json` and `run-report-organization.json`
- **EVIDENCE_COMMIT_ROLE:** one consolidated inventory plus independent historical manifests/logs
- **CLASSIFICATION:** CLEANUP_CONSOLIDATED_AND_OFFLINE_VERIFIED
- **PRODUCT_CHANGE:** cleanup NO; same delivery closes one separately scoped assumption-reason gap without changing serve/refuse decision
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** YES (`b4a33205…` → `7f3f042309dd1c54…`; 102 file; clean refreeze at product commit `f967ba24`)
- **CACHE_CHANGE:** YES (117 → 118 because cached refusal envelope changes)
- **CORRECTED_BY:** NONE
- **CORRECTS:** first-run unread-scope limitation; continuation and organization are histories inside this run
- **SUPERSEDES:** NONE
- **THESIS_USE:** none
- **AUTHORITATIVE_FILES:** `plan.md` · `inventory.md` · `report.md` · `handoff.md` · `run.json` · `run-artifact-cleanup.json` · `run-report-organization.json` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = MOBILE_CANVAS_FIT
- **RUN_ID:** mobile-canvas-fit (task mobile-canvas-fit; same branch)
- **DATE:** 2026-10-08
- **REPORT:** docs/evaluation/geometry/runs/mobile-canvas-fit/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/mobile-canvas-fit/
- **START_BASE:** 38a19c65
- **CODE_COMMIT:** c9bcdcdb (product) · harness b8615356 · a51c788b (candidate refreeze 002185a8; plan/review set/baseline 2d169347, 90921f53)
- **MEASUREMENT_COMMIT:** 90921f53 (local, clean detached CRLF worktree with a space in its path; D5 probe, suite, W02, W04, W05, occlusion, playback, builder; eight families); suite step for regular_triangular_pyramid rerun alone at a51c788b (stale suite expectation); baseline probe on a scratch build of 38a19c65 (`diagnostics/baseline_38a19c65/`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit 3f874fed after the measurement (results, images, fixtures, logs)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 + identity gates at the run's final documentation commit — `handoff.md` §2)
- **PRODUCT_CHANGE:** YES (frontend only: narrow-layout canvas height, steps panel scroll)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** product_commit_sha only (f967ba24 -> c9bcdcdb); measured-system tree 7f3f0423... unchanged
- **CACHE_CHANGE:** NO (CACHE_VERSION 118; no envelope changes)
- **CORRECTED_BY:** NONE
- **CORRECTS:** suite manifest `frontend/scripts/generic-tier-a-scenarios.json` (two oracle_source pins stale since 23aff0ad/f967ba24; T8 missing-height refusal expectation stale since f967ba24); living docs `AI_CONTEXT_BUNDLE.md` §1 (CACHE_VERSION 117) and `ROADMAP.md` §0 (docs-cleanup identity) — earlier run files untouched
- **SUPERSEDES:** NONE (earlier review packages stay; images of A-R8, B-R5, C-R1-R3, C-R9 now also exist on the final candidate)
- **THESIS_USE:** learner-facing simulation on phones (D5); human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `inputs/REVIEW_SET.json` · `results/MOBILE_LAYOUT_PROBE.json` · `results/BROWSER_EVIDENCE.json` · `results/rerun/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W05_FOCUS_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = PHONE_LANDSCAPE_LAYOUT
- **RUN_ID:** phone-landscape-layout (task phone-landscape-layout; same branch)
- **DATE:** 2026-10-08/09
- **REPORT:** docs/evaluation/geometry/runs/phone-landscape-layout/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/phone-landscape-layout/
- **START_BASE:** f6ebe946
- **CODE_COMMIT:** d8ad153b · 95a56a17 (product); candidate refreeze f884aa67, 5892fefd; plan/review set/baseline 9af3e8a3, 221ec0a0
- **MEASUREMENT_COMMIT:** 221ec0a0 attempt 3 (local, clean detached CRLF worktree with a space in its path; every step in one run: landscape/mobile probe over 7 viewports, full Tier-A suite, W02, W04, W05, occlusion, playback, builder); attempts 1 (9af3e8a3) and 2 (221ec0a0) kept (`MEASUREMENT_ATTEMPTS.json`, `diagnostics/attempts/`); baseline on a scratch build of f6ebe946 (`diagnostics/baseline_f6ebe946/`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit b1ba2575 after the measurement (results, images, fixtures, logs, attempt records)
- **CLASSIFICATION:** READY_FOR_HUMAN_VISUAL_REVIEW (T3 + identity gates at the run's final documentation commit — `handoff.md` §2)
- **PRODUCT_CHANGE:** YES (frontend only: short-landscape control column, 360 px play buttons)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** product_commit_sha only (c9bcdcdb -> d8ad153b -> 95a56a17); measured-system tree 7f3f0423... unchanged
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (earlier runs untouched; ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD resolved in OPEN_ISSUES)
- **SUPERSEDES:** NONE
- **THESIS_USE:** learner-facing simulation on phones in landscape and on small screens; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `MEASUREMENT_ATTEMPTS.json` · `inputs/REVIEW_SET.json` · `results/MOBILE_LAYOUT_PROBE.json` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W05_FOCUS_PROBE.json` · `results/OCCLUSION_MEASUREMENT.json` · `results/PLAYBACK_EVIDENCE.json` · `images/` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = FINAL_ACCEPTANCE
- **RUN_ID:** final-acceptance (task final-acceptance; same branch)
- **DATE:** 2026-10-09
- **REPORT:** docs/evaluation/geometry/runs/final-acceptance/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/final-acceptance/
- **START_BASE:** bc989cd2
- **CODE_COMMIT:** NONE (no product change)
- **MEASUREMENT_COMMIT:** bc989cd2 source (frontend/src identical to 95a56a17); scratch builds of that source and of main 38d41588 (removed detached worktree); two one-off probes (classroom band, emulated touch), 0 model requests
- **EVIDENCE_COMMIT_ROLE:** the run's documentation commit (results, probes, one image)
- **CLASSIFICATION:** READY_FOR_USER_ACCEPTANCE (identity re-verified; Tier-A 8/8 and T3 of phone-landscape-layout reused — same product)
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (7f3f0423..., --verify match)
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (phone-landscape-layout report §6 listed the classroom band as unmeasured; measured here, earlier files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** merge readiness of the branch; classroom band defect (pre-existing on main); emulated-touch support for E-R6/F-R7 (not a device check)
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `results/CLASS_BAND_PROBE.json` · `results/TOUCH_PROXY_PROBE.json` · `images/` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = CLASSROOM_BAND_FIT
- **RUN_ID:** classroom-band-fit (task classroom-band-fit; same branch)
- **DATE:** 2026-10-09
- **REPORT:** docs/evaluation/geometry/runs/classroom-band-fit/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/classroom-band-fit/
- **START_BASE:** 1086da7f
- **CODE_COMMIT:** 45f5a7f0 (product); candidate refreeze 83db0e97; plan/probe/baseline 9284202d, 6a1801e7
- **MEASUREMENT_COMMIT:** 6a1801e7 attempt 3 (local, clean detached CRLF worktree with a space in its path; every step in one run: class band probe 3 roles x 8 viewports, phone/landscape probe without a band, full Tier-A suite, W02, W04, W05); attempts 1-2 kept (`MEASUREMENT_ATTEMPTS.json`, `diagnostics/attempts/`); baseline on a scratch build of 95a56a17 (`diagnostics/baseline_95a56a17/`)
- **EVIDENCE_COMMIT_ROLE:** evidence commit 3095e4f0 after the measurement (results, fixtures, 3 images, logs)
- **CLASSIFICATION:** READY_FOR_USER_ACCEPTANCE (T3 + identity gates at the run's final documentation commit — `handoff.md` §2)
- **PRODUCT_CHANGE:** YES (frontend only: classroom band chip on tight screens, title floor, tool group no-wrap)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** product_commit_sha only (95a56a17 -> 45f5a7f0); measured-system tree 7f3f0423... unchanged
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE (final-acceptance recorded the defect and an unmeasured proposal; that proposal measured 15/24 here and was superseded by the user's chip decision — earlier files untouched)
- **SUPERSEDES:** NONE
- **THESIS_USE:** classroom mode on phones; human review NOT_APPROVED
- **AUTHORITATIVE_FILES:** `review.md` · `report.md` · `handoff.md` · `run.json` · `plan.md` · `MEASUREMENT_ATTEMPTS.json` · `results/CLASS_BAND_PROBE.json` · `results/MOBILE_LAYOUT_PROBE.json` · `results/BROWSER_EVIDENCE.json` · `results/W02_CLOSURE_PROBE.json` · `results/W04_PANELS_PROBE.json` · `results/W05_FOCUS_PROBE.json` · `images/` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = BROWSER_TEMP_LIFECYCLE
- **RUN_ID:** browser-temp-lifecycle (task browser-temp-lifecycle; same branch)
- **DATE:** 2026-10-09
- **REPORT:** docs/evaluation/geometry/runs/browser-temp-lifecycle/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/browser-temp-lifecycle/
- **START_BASE:** 7834ea4e
- **CODE_COMMIT:** 3cb0630a (test harness: frontend/scripts/browser-runner.mjs, compiler-scene-suite.mjs openFixture)
- **MEASUREMENT_COMMIT:** working tree of 3cb0630a's harness (local; real Chrome lifecycle scenarios, long session, probe smoke) + dry-run inventory of %TEMP%
- **EVIDENCE_COMMIT_ROLE:** the run's documentation commit (results JSON, diagnostics scripts)
- **CLASSIFICATION:** RESOLVED (harness); legacy %TEMP% cleanup awaits the user
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (7f3f0423..., product 45f5a7f0)
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** none (measurement infrastructure); reproducibility of browser runs
- **AUTHORITATIVE_FILES:** `report.md` · `handoff.md` · `run.json` · `results/LIFECYCLE_VERIFICATION.json` · `results/TEMP_INVENTORY.json` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = MERGE_READINESS
- **RUN_ID:** merge-readiness (task merge-readiness; same branch)
- **DATE:** 2026-10-09
- **REPORT:** docs/evaluation/geometry/runs/merge-readiness/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/merge-readiness/
- **START_BASE:** 6c334121
- **CODE_COMMIT:** f89a1a8b (housekeeping: favicon removal + .gitignore committed on the user's instruction; index.html icon link; second-family audit precheck accepts a committed favicon deletion)
- **MEASUREMENT_COMMIT:** none (no browser measurement); temp cleanup applied on the machine after the user's confirmation
- **EVIDENCE_COMMIT_ROLE:** the run's documentation commit (cleanup result, checklist)
- **CLASSIFICATION:** READY_FOR_USER_ACCEPTANCE (T3 + identity gates at the run's final documentation commit — `handoff.md` §2)
- **PRODUCT_CHANGE:** NO by the product_commit_sha definition (backend/app + frontend/src); the frontend BUILD changed (index.html icon link, public/favicon.svg removed)
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (7f3f0423..., product 45f5a7f0)
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** none (merge preparation)
- **AUTHORITATIVE_FILES:** `report.md` · `handoff.md` · `run.json` · `results/TEMP_CLEANUP.json` · `diagnostics/`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)

## WAVE_ID = FRONTEND_FREEZE
- **RUN_ID:** frontend-freeze (task frontend-freeze; same branch)
- **DATE:** 2026-10-09
- **REPORT:** docs/evaluation/geometry/runs/frontend-freeze/report.md
- **ARTIFACT_DIRECTORY:** docs/evaluation/geometry/runs/frontend-freeze/
- **START_BASE:** e0c0cec8
- **CODE_COMMIT:** NONE
- **MEASUREMENT_COMMIT:** NONE (no measurement; git fetch + identity checks only)
- **EVIDENCE_COMMIT_ROLE:** the run's documentation commit (user decision record, honest acceptance status, Cloud handoff)
- **CLASSIFICATION:** WAITING_FOR_EXPLICIT_MERGE_APPROVAL
- **PRODUCT_CHANGE:** NO
- **MODEL_REQUEST_COUNT:** 0
- **CANDIDATE_CHANGE:** NO (7f3f0423..., product 45f5a7f0)
- **CACHE_CHANGE:** NO (CACHE_VERSION 118)
- **CORRECTED_BY:** NONE
- **CORRECTS:** NONE
- **SUPERSEDES:** NONE
- **THESIS_USE:** scope decision (frontend paused; backend architecture next)
- **AUTHORITATIVE_FILES:** `report.md` · `handoff.md` · `run.json`
- **RUN_ID_POLICY:** TASK_NAME (naming policy 2026-10-07)
- **APPROVAL (2026-10-09):** `frontend-freeze/APPROVAL.md` — the user's verbatim decision: integrate the temporary frontend baseline with exceptions (C1–C6 viewed, not approved; P1–P6 PENDING; UX debt OPEN/DEFERRED; W14 not visually approved; W05 23/24); fast-forward main + push allowed; branch deletion not allowed; next: missing-family expansion on the existing architecture, then OCR
