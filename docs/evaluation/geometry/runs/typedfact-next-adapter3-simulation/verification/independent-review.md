# Independent Read-Only Review Report — TypedFactNext (`typed-fact-next/1`) & Adapter /3 (`hybrid-simulation-adapter/3`)

- **Verdict:** `INDEPENDENT_REVIEW_PASS`
- **Reviewer Conversation ID:** `4fb6baa0-4d1b-4b28-8f9b-59408ac91a2d`
- **Worktree Inspected:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\typedfact-next-adapter3-simulation`
- **Branch:** `research/typedfact-next-adapter3-simulation` (base `main` = `1613e0d3ebe16f0f2fe4be755052491ff581e51b`)
- **Candidate Commit:** `09f97a287dcaef10db30e1fcb1fcb98781107989` (Product Commit: `61d6f44b7d8dffd69fbda51979686ced5b00efd2`)
- **Measured System Hash:** `42f6ae2c8e290d00be2e11b439ca2499f58fe74cd84ab999e2cae2824c4b65d2` (`114` files)
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`)

---

## Item-by-Item Verification Findings

### 1. Contract Versioning & Backward Compatibility (`PASS`)
- **Coexistence without mutation:** Verified via `git diff --name-only 1613e0d3ebe16f0f2fe4be755052491ff581e51b..HEAD` that the only product files added are `backend/app/simulation/geometry_functions/typed_fact_next.py` and `backend/app/ai/adapter3_simulation.py`. Neither `planner.py` (`TypedFact` / `geometry-fact-planner/10`), `hybrid_preview.py` (`hybrid-preview-adapter/2`), `fact_extraction.py` (`hybrid-semantic-extraction/3`), `registry.py` (`geometry-functions/10`), nor `engine.py` (`geometry-function-engine/8`) was modified.
- **Closed Pydantic models & fail-closed validation:** `ClosedNextModel` enforces `ConfigDict(extra="forbid", frozen=True)` across `TypedFactNextPayload`, `SolidSpec`, `PremiseSpec`, `DerivedPlaneSectionSpec`, `GeometricRelationSpec`, `SimulationGoalSpec`, `MathGoalSpec`, and `DerivedObjectIdentity`.
- **Refusal taxonomy:** Fail-closed validation and execution refusal codes (`SCHEMA_VERSION_MISMATCH`, `INVALID_TYPED_FACT_NEXT`, `EMPTY_SOLIDS`, `EMPTY_SIMULATION_GOALS`, `AMBIGUOUS_REFERENCE`, `UNKNOWN_SOLID_ID`, `UNKNOWN_SECTION_ID`, `UNKNOWN_VERTEX_REF`, `SHARED_ENTITY_MISMATCH`, `COORDINATE_FRAME_DISCONNECTED`, `SECTION_NOT_CLOSED_ON_LATERAL_EDGES`, `DEGENERATE_DERIVED_SECTION`, `DEGENERATE_DERIVED_SOLID`, `SOURCE_QUOTE_NOT_FOUND`, `SOURCE_NUMBER_MISMATCH`, plus all Registry/Planner/Engine codes) are strictly enforced and tested in `backend/tests/geometry/test_typedfact_next_adapter3.py`.

### 2. Adapter /3 (`hybrid-simulation-adapter/3`) Orchestration & Verification (`PASS`)
- **Source grounding:** `_verify_quote_in_problem` and `_verify_number_in_quote` validate verbatim quote presence and numeric/ratio grounding against `problem_text` before invoking `_Dung.kiem()` (`kiem_nguon` / Registry `/10` Source Gate) and `_Dung.kiem_mat_cat()`. Non-homogeneous length units (`length_unit="1"` with symbolic `"a"`) are rejected with `NON_HOMOGENEOUS_LENGTHS`.
- **Solid-qualified reference resolution (`solid_id::label`):** `_Adapter3Compiler.resolve_ref` resolves explicit `solid_id::label` references against declared `SolidSpec.vertex_bindings` and rejects any unqualified reference whose local label maps to >1 distinct canonical points across solids with `AMBIGUOUS_REFERENCE`.
- **Two-phase section verification & IR folding:**
  - **Phase 1 (`run` lines 2016–2059):** Constructs `_Dung` with full auxiliary plane-spanning points (`X1, X2, F1, F2`), `mat_phu` (`MAT_SONG_SONG`, `MAT_VUONG_DUONG`, `MAT_HAI_DUONG`), and `intersect_line_plane` calls; executes `thu_khoi()`, `bo_cuc_day()`, `giai_phu_thuoc()`, `kiem()`, `kiem_mat_cat()`, and `_verify_geometric_relations_and_cuts()` (certifying exact rational cut ratios $0 < t \le 1$ on every lateral edge and non-collinearity of the section cycle).
  - **Phase 2 (`_rebuild_folded_dung` lines 1920–1993):** Folds verified rational cut ratios into `midpoint` ($t = 1/2$) or `divide_segment` ($t \in (0,1]\setminus\{1/2\}$) and replaces auxiliary plane triples with the verified section cycle `cycle[:3]`, re-running `_Dung` verification (`kiem()`, `kiem_mat_cat()`) before compiling to `SemanticProgramSpec` and executing `SemanticProgramInterpreter`. This preserves exact rational coordinates and symbolic certificates while keeping dummy auxiliary points out of `Scene3D` and staying within `MAX_MEMORY_DECLARATIONS = 32`.
- **Scene3D & Kernel self-checks:** Verifies exact point coordinate agreement between `_Dung.pts` and `ket.final_memory`, closed section polygons, and squared volume certificate equality before enriching `Scene3D` with `formation.steps`, `events`, `display_group` highlights, and `attach_scene_perpendicular_certificates`.

### 3. Slice A (Unnamed Section Vertices & Derived Sub-Solid) & Slice B (Multi-Solid Identity & Shared Geometry) (`PASS`)
- **Slice A:** Unnamed lateral-edge intersections receive deterministic collision-free internal symbols (`I1, I2, ...`) and deterministic machine IDs (`sec:<section_id>:edge:<U>-<V>`) in `DerivedObjectIdentity` with explicit `dependencies` and `provenance`. In `Scene3D`, `notation` is set to `None` across unnamed `point3`, `segment3`, `polygon3`, and derived `polyhedron3` objects with descriptive Vietnamese labels (`"Giao điểm của SB và (α)"`, `"Hình chóp cắt bởi (α) chứa đỉnh S"`), preventing internal symbol leakage.
- **Slice B:** Multiple related solids (`S.ABC` and `D.ABC` sharing base `ABC` with colliding local label `D`, or adjacent pyramids sharing face `SAB`) are embedded in the shared `root` Gram chart; `shared_vertices`, `shared_faces`, and `coordinate_frame` relations are certified fail-closed.
- **Exact volume ratio & residual volume:** `_compute_certified_math_goals` computes exact rational volume ratios via `math.isqrt` on exact `Fraction` squared-volume certificates (`IRRATIONAL_VOLUME_RATIO` if non-square) and exact `Fraction`/`Radical` residual volumes $(1 - r)\,V(\text{parent})$, cross-checked against `(complement_ratio**2) * v2_parent`. Zero floating-point approximations and zero case-ID hardcoding.

### 4. Oracle & Frontend Demo Verification (`PASS`)
- **Explicit non-blind labeling:** Both `corpus-dev.json` and `eval-summary.json` carry `"measurement_class": "DEVELOPMENT_EVALUATION_NOT_BLIND"`.
- **Independent mathematical oracle (`oracle_eval.py`):** Evaluates 16 cases (`10` positive across Slice A and Slice B + `6` negative refusal cases) against independent first-principles exact rational expectations (`oracle_pyramid_similarity_section`), achieving `10/10` positive passed, `6/6` negative passed, and `0` wrong serves (`wrong_serves: 0`).
- **Frontend executable simulation demos (`adapter3-simulation-demos.test.tsx`):** Verifies all 4 demo artifacts (`demo1-unnamed-section-pyramid.json` .. `demo4-negative-underdetermined-refusal.json`, SHA-256 matched in `eval-summary.json`) through `withSubEntities`, `deriveSectionSubEntities`, `sectionCycleLabel === null`, Three.js `VIEW.buildObject3D` construction for every visual object, `objectsAt` step-by-step playback, target highlighting, and interactive `select` / `isolate` / `explode` state transitions.

### 5. Governance Invariants (`PASS`)
- `DEFAULT_MODE = "LLM_ONLY"` (`CHE_DO_MAC_DINH = "LLM_ONLY"` in `backend/app/simulation/geometry_compiler/routing.py`).
- `RESPONSE_CONTRACT = "flat"` (`RoutePolicy.response_contract = "flat"` in `backend/app/ai/pipeline.py`).
- `HYBRID_PRODUCT_ENABLEMENT = "NO-GO"` (no product route or default pipeline invokes Adapter `/3`).
- `CACHE_VERSION = "127"` (`backend/app/main.py` line 824 and `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` line 9).

---

## Defects, False-Serve Risks, or Governance Violations
- **0 defects found.** No blockers, no false-serve risks, and no governance violations were identified.
