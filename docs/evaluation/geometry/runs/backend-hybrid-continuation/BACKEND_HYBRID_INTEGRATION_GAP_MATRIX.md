# Backend Hybrid integration gap matrix

Scope is the user's P0–P6 priority matrix, not the older roadmap numbering. Read alongside architecture decision and final handoff. Offline authored-input development evidence only; `ALLOW_LIVE_AI=0`.

| Priority | Status | What is present / missing | Sources, tests and receipts |
|---|---|---|---|
| P0 Wave 3A decision + research stability | PARTIAL | exact ratio/residual integrated on declared and planner-derived pyramids; Session 1 bridge local. Full Adapter /3 unification and cut_edges semantic decision remain. No GO MAIN | `geometry_functions/registry.py`, `engine.py`, `typed_fact_next_bridge.py`; Wave3A suites; architecture decision; final T3 receipt in handoff |
| P1 AI → JSON facts/source correctness | PARTIAL | ratio span ownership fixed; restrictive clauses, negation, ambiguous/missing facts fail closed; bridge input constraints tested. No Next provider extractor/live E2E, frozen flat provider cannot emit bridge-only fields | `ai/fact_extraction.py::parse_response`, `registry._kiem_vung_tien_de/_ty_so_khop`, bridge; bridge tests + existing Source Gate suites; inherited SOURCE_GATE_INTEGRATION_REPORT; development replay |
| P2 Planner/Engine → Adapter/Scene3D | PARTIAL | existing function-route scene builder supports bridge slice with exact certificates, source quotes, goal ownership and group-event births. Adapter /3 still independent; bridge highlight/sequence/construct_object goals listed as no-new-fact goals rather than Adapter /3 outcome parity | `ai/function_route.py`, `hybrid_preview._validate_scene`, `adapter3_simulation.py`; preview tamper and bridge tests; `planner-composition-final.json` scene 40/40 |
| P3 New-problem composition/reuse evaluation | PARTIAL | real bounded dependency DAG and typed producer resolver; new per-edge cost-ranked selection, memoized plane, derived pyramid → ratio/residual. 60 cases, 6 metamorphic relations, one generated family; no new blind/general NLP result | `planner._EffectResolver/_dinh_cat_canh/_khoi_tren_thiet_dien/_sap_xep_phu_thuoc_loi_goi`; dependency/function-composition/bridge suites; inherited evaluation and fresh replay |
| P4 Backend exact 3D semantics | PARTIAL; UI OUT_OF_SCOPE | structural scene metric/dependencies valid on 40/40 bridge scenes; numeric quantities and certificates checked; no invented residual mesh. Browser rendering, camera/palette/renderer and learner approval outside this backend session | `engine.kiem_dinh_cat`, ratio/residual certificates, scene builder, `hybrid_preview._validate_scene`; adapter/preview/Wave3A suites. No new browser evidence |
| P5 Quality, time, compute, tokens, reproducibility | PARTIAL | actual command wall times/exit codes/hash receipts; progressive sequential pytest and one final detached T3. Quality denominators explicit. No live/token/cost measurement, CPU/RSS profiler, statistical generalization or service latency benchmark | `verification/*/execution.json`, frozen candidate and post-T3 verification, development replay timings (local only). Provider requests=0; provider token use for evaluation NOT_APPLICABLE, production token/latency UNKNOWN |
| P6 New geometry families | OUT_OF_SCOPE | no justified new family campaign opened; bridge curved/prism-derived/frame gaps recorded, not implemented | existing curved Adapter /3 remains untouched; architecture decision NOT_YET_SUPPORTED entries |

## Status of named findings

- DEV-F2-02: **DONE within deterministic fact route**, not live extraction. Registry credits only the coefficient span actually solved by the source ratio equation. Extra unread number / wrong ratio controls still refuse. Both normal SIMSON (ratio 1/12) and parallel cut cases are covered.
- HOLD-F2-01: **DONE for reproduced preview failure**. The hypothesized fact-ID dependency cause was not reproduced. Actual bug was group-event birth handling; geometric dependencies were already object IDs. An edge born before its endpoint still refuses. No locked holdout was edited or rebranded as blind.
- Candidate governance error: **DONE at targeted guard**, new immutable T3 required for final product. Original failure remains recorded.
- Full sole Next contract, Adapter /3 source-gate parity and closure semantics: **BLOCKED_BY_CONTRACT** for automatic unification; owner proposal only.
- Live NLP E2E: **NOT_STARTED in this session**, no provider permission. Offline TypedFact evidence cannot establish live NL success.

## Completion boundary

Research Session 1 can be reviewed independently of a wholesale architecture replacement. Requirements to replace the old architecture are not met. Further session needed for owner-approved cut_edges/multi-solid/goal-outcome contract decision, then adapter/source-gate migration and separately budgeted live extraction evaluation. Do not infer GO_MAIN or production readiness from local gates.
