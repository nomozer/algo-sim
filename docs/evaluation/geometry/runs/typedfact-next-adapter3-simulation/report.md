# TypedFactNext (`typed-fact-next/1`) + Adapter /3 (`hybrid-simulation-adapter/3`) — Simulation-First Contract Expansion (`typedfact-next-adapter3-simulation`)

- **Branch:** `research/typedfact-next-adapter3-simulation` (from `main` = `origin/main` = `1613e0d3ebe16f0f2fe4be755052491ff581e51b`)
- **Worktree Isolation:** `.superpowers/worktrees/typedfact-next-adapter3-simulation` (root checkout left untouched while another agent worked on Wave 3A)
- **Authorization:** `GO_TYPEDFACT_NEXT_ADAPTER3_OFFLINE_RESEARCH_IMPLEMENTATION` (local research only; no GO MAIN)
- **Product Commits:** `54e61480` (Session 1: contract, Adapter `/3`, Slices A & B) → `61d6f44b` (Session 2: two-phase IR section folding)
- **Candidate Freeze:** `09f97a287dcaef10db30e1fcb1fcb98781107989`, measured system hash `42f6ae2c8e290d00be2e11b439ca2499f58fe74cd84ab999e2cae2824c4b65d2` (`114` files)
- **Independent Review:** `INDEPENDENT_REVIEW_PASS` ([`independent-review.md`](verification/independent-review.md))
- **Authoritative Full T3:** `FULL_PRODUCT_GATE_PASS` at `7eadd56ba0480516accb9ec136594cb45176fda1` ([`authoritative-t3.json`](verification/authoritative-t3.json))
- **Architecture Contract:** [`TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](../../../architecture/TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md)

---

## 1. Executive Summary

This two-session campaign upgrades AlgoSim's geometry representation and orchestration around a **simulation-first** contract without mutating the existing `TypedFact` (`geometry-fact-planner/10`), `Adapter /2` (`hybrid-preview-adapter/2`), `Registry /10`, or `Engine /8`:

1. **`TypedFactNext` (`typed-fact-next/1`):** Closed Pydantic schema (`backend/app/simulation/geometry_functions/typed_fact_next.py`) supporting:
   - First-class simulation goals (`construct_solid`, `construct_plane_section`, `construct_derived_solid`, `highlight_geometry`, `show_construction_sequence`),
   - Automatic derived object identity (`DerivedObjectIdentity` with deterministic machine IDs `sec:<section_id>:edge:<U>-<V>`, explicit dependency graphs, and verbatim source provenance),
   - Solid-qualified vertex references (`solid_id::label`) and explicit geometric relations (`shared_vertices`, `shared_faces`, `section_membership`, `coordinate_frame`),
   - Optional certified mathematical goals (`volume_ratio`, `residual_volume`, `volume`, `area`, `distance`, `angle`).
2. **`Adapter /3` (`hybrid-simulation-adapter/3`):** Offline research adapter (`backend/app/ai/adapter3_simulation.py`) executing a two-phase verification pipeline:
   - **Phase 1:** Validates verbatim source grounding (`_verify_quote_in_problem`, `_verify_number_in_quote`, `kiem_nguon`), resolves solid-qualified identities (refusing bare ambiguous references across solids), runs `_Dung.kiem()` and `_Dung.kiem_mat_cat()` on full auxiliary cutting-plane constructions (`MAT_SONG_SONG`, `MAT_VUONG_DUONG`, `MAT_HAI_DUONG`), and certifies exact rational cut ratios $0 < t_k \le 1$ on every lateral edge.
   - **Phase 2 (`_rebuild_folded_dung`):** Folds certified cut ratios into `midpoint` ($t_k = 1/2$) or `divide_segment` ($t_k \ne 1/2$) and replaces auxiliary plane points with the certified section cycle before compiling to `SemanticProgramSpec` and executing `SemanticProgramInterpreter`, keeping `Scene3D` free of dummy construction points and within `MAX_MEMORY_DECLARATIONS = 32`.
3. **Simulation Slice A (Unnamed Section Vertices & Derived Sub-Solid):** Automatically derives unnamed lateral-edge section intersections (`notation = None`, descriptive Vietnamese labels `"Giao điểm của SB và (α)"`), closed section polygons (`sectionCycleLabel(scene, id) === null`), and derived top pyramids (`"Hình chóp cắt bởi (α) chứa đỉnh S"`) with exact rational volume ratios and residual volumes.
4. **Simulation Slice B (Multi-Solid Identity & Shared Geometry):** Resolves colliding local vertex names (`pyr1::D` vs. `pyr2::D`) into distinct canonical symbols (`D` vs. `D1` with `notation = "D(pyr2)"`) while unifying shared vertices (`A, B, C`) and shared faces (`SAB`) in a single root coordinate frame.

---

## 2. Executable Simulation Demos & Independent Oracle Evaluation

| Artifact / Suite | Classification | Result |
|---|---|---|
| [`demos/demo1-unnamed-section-pyramid.json`](demos/demo1-unnamed-section-pyramid.json) | Executable Demo 1 (Slice A) | `SERVED` — Pyramid `S.ABCD` + parallel plane `(α)` through midpoint `M` of `SA` + 3 auto-derived unnamed vertices + derived sub-solid (`volume_ratio = 1/8`, `residual_volume = 7a³/12`) |
| [`demos/demo2-multi-solid-shared-geometry.json`](demos/demo2-multi-solid-shared-geometry.json) | Executable Demo 2 (Slice B) | `SERVED` — Pyramids `S.ABC` and `D.ABC` sharing base `ABC` with colliding vertex label `D` (`pyr1::D` vs `pyr2::D`) |
| [`demos/demo3-step-by-step-construction-highlight.json`](demos/demo3-step-by-step-construction-highlight.json) | Executable Demo 3 (Playback & Highlight) | `SERVED` — Regular pyramid `S.ABC` cut by plane `(β) ⊥ SA` at $AM = \frac{1}{3}SA$, 7 playback steps, highlighted section & point (`volume_ratio = 1/27`) |
| [`demos/demo4-negative-underdetermined-refusal.json`](demos/demo4-negative-underdetermined-refusal.json) | Executable Demo 4 (Fail-Closed Refusal) | `REFUSED` (`UNDERDETERMINED_POINT`, `scene3d = null`) |
| [`corpus-dev.json`](corpus-dev.json) + [`eval-summary.json`](eval-summary.json) | `DEVELOPMENT_EVALUATION_NOT_BLIND` | **10/10** positive exact match against independent oracle ([`oracle_eval.py`](oracle_eval.py)), **6/6** negative refusal match, **`0` wrong serves** |
| [`adapter3-simulation-demos.test.tsx`](../../../../frontend/src/simulations/domains/geometry/adapter3-simulation-demos.test.tsx) | Frontend Three.js / `Scene3D` Verification | **4/4 passed** (`withSubEntities`, `deriveSectionSubEntities`, `sectionCycleLabel === null`, `VIEW.buildObject3D` Three.js mesh construction, `objectsAt` step playback, `select`/`isolate`/`explode`) |

---

## 3. Authoritative Full T3 & Regression Verification

- **Backend Full T3 (`pytest`):** `11,410 passed, 1 skipped, 2 deselected, 9 xfailed` (includes 19 new `test_typedfact_next_adapter3.py` tests, 174 historical rows, 41 Adapter `/2` fixtures, Wave 1 / 2A / 2B / 2C, SG-1..SG-6, SGH-01..18, Route A isolation, docs IA & telemetry).
- **Frontend Full T3 (`vitest`):** `71 test files, 1,150 passed` (includes `adapter3-simulation-demos.test.tsx`, `code-index-sync.test.ts`, `hybrid-preview-contract.test.ts`, `scene3d-page.test.tsx`).
- **Production Build (`tsc -b && vite build`):** `PASS`.
- **Thesis Demo Replay & Crash Surface:** `5/5` replay pass, `6/6` boundary refusals, `0` uncaught 500s.
- **Post-T3 Candidate Freeze Verification:** `MATCH` (`114` files, `42f6ae2c8e290d00be2e11b439ca2499f58fe74cd84ab999e2cae2824c4b65d2`).

---

## 4. Governance & Recommendation

- `DEFAULT_MODE = LLM_ONLY`
- `RESPONSE_CONTRACT = flat`
- `HYBRID_PRODUCT_ENABLEMENT = NO-GO`
- `ALLOW_LIVE_AI = 0` (`0` live requests)
- `CACHE_VERSION = 127` (`NO_BUMP`)
- **Recommendation:** `ADAPTER3_SIMULATION_RESEARCH_READY_FOR_GO_MAIN_REVIEW` (stopped at GO MAIN gate; no merge to `main` and no push performed).
