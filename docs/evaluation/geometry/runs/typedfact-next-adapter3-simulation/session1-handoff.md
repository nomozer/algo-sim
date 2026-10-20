# Session 1 Handoff — TypedFactNext (`typed-fact-next/1`) + Adapter /3 (`hybrid-simulation-adapter/3`)

- **Run Slug:** `typedfact-next-adapter3-simulation`
- **Authorization:** `GO_TYPEDFACT_NEXT_ADAPTER3_OFFLINE_RESEARCH_IMPLEMENTATION`
- **Branch:** `research/typedfact-next-adapter3-simulation`
- **Base `main` Commit:** `1613e0d3ebe16f0f2fe4be755052491ff581e51b`

---

## 1. Completed Milestones (P1–P4)

1. **P1 — Versioned TypedFactNext Contract (`typed-fact-next/1`):**
   - Implemented in [`backend/app/simulation/geometry_functions/typed_fact_next.py`](../../../../backend/app/simulation/geometry_functions/typed_fact_next.py) and specified in [`docs/architecture/TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](../../../architecture/TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md).
   - Coexists with unchanged `TypedFact` (`typed-facts/2` / `geometry-fact-planner/10`) and Adapter `/2` (`hybrid-preview-adapter/2`).
   - Covers simulation goals (`construct_object`, `construct_plane_section`, `construct_derived_solid`, `highlight_geometry`, `construction_sequence`), deterministic derived object identities (`DerivedObjectIdentity`), solid-qualified vertex references (`SolidQualifiedRef` / `solid_id::label`), geometric relations (`containment`, `shared_vertices`, `shared_faces`, `parallel`, `perpendicular`, `section_membership`, `coordinate_frame`), and optional certified math goals (`volume_ratio`, `residual_volume`, `measurement`).

2. **P2 — Offline Research Adapter /3 (`hybrid-simulation-adapter/3`):**
   - Implemented in [`backend/app/ai/adapter3_simulation.py`](../../../../backend/app/ai/adapter3_simulation.py).
   - Validates input schema, grounds quotes and numbers against `problem_text`, resolves solid-qualified and unqualified references fail-closed, orchestrates the existing Wave 1–2C Geometry Functions Engine (`_Dung`) and `SemanticProgramInterpreter`, and emits `Scene3D` (`scene3d/1`) + `SimulationState` (`simulation-state/1`) + preview-compatible `hybrid-Flat-preview/1` (`route_d` + `route_b`).

3. **P3 — End-to-End Slices:**
   - **Slice A (Unnamed Section Vertices & Derived Sub-Solid):** Supports cutting planes defined via `through_point_parallel_plane`, `through_point_perpendicular_line`, and `through_point_parallel_two_lines`; automatically synthesizes unnamed lateral-edge intersections with stable `derived_id` (`sec:<section_id>:edge:<U>-<V>`), verifies $0 < t \le 1$ segment bounds in the exact rational Gram chart, folds verified intersection ratios into IR edge divisions so dummy plane-spanning points do not pollute `Scene3D` or exceed `MAX_MEMORY_DECLARATIONS = 32`, constructs the derived sub-pyramid, and certifies exact `volume_ratio` and `residual_volume`.
   - **Slice B (Multi-Solid Identity & Shared Geometry):** Resolves `solid_id::label` bindings across multiple solids in one root coordinate frame, rejects ambiguous unqualified vertex references (`AMBIGUOUS_REFERENCE`), verifies `shared_vertices` and `shared_faces` (`SHARED_ENTITY_MISMATCH`), and constructs distinct `polyhedron3` objects with shared canonical vertices/faces in `Scene3D`.

4. **P4 — Scene3D Simulation Verification:**
   - Verified in [`backend/tests/geometry/test_typedfact_next_adapter3.py`](../../../../backend/tests/geometry/test_typedfact_next_adapter3.py) (`18 passed in 1.15s`): exact rational coordinates, `edge_ownership`, `surfaces`, `endpoint_entities` on `section`, `formation.steps` 1-to-1 timeline, `notation=None` on unnamed derived section vertices and derived sub-solids (zero leaked internal symbols), highlight groups, and fail-closed refusals.

---

## 2. Session 2 Continuation Plan (P5–P8)

- **P5:** Generate 4 executable simulation demo artifacts under `docs/evaluation/geometry/runs/typedfact-next-adapter3-simulation/demos/` and verify real `Scene3D` loading, Three.js `buildObject3D` rendering, sub-entity extraction, step playback, highlighting, and Demo 4 safe refusal in Vitest (`frontend/src/simulations/domains/geometry/adapter3-simulation-demos.test.tsx`).
- **P6:** Build the development evaluation corpus (`corpus-dev.json`, labeled `DEVELOPMENT_EVALUATION_NOT_BLIND`) and independent mathematical oracle (`oracle.py`), verifying `0` wrong serves across all positive and negative cases.
- **P7:** Update `docs/CODE_INDEX.md` and run all backward-compatibility regression suites.
- **P8:** Run `candidate_freeze.py`, independent read-only review (`INDEPENDENT_REVIEW_PASS`), authoritative Full T3 (`FULL_PRODUCT_GATE_PASS`), and record the final report stopping at the GO MAIN gate.
