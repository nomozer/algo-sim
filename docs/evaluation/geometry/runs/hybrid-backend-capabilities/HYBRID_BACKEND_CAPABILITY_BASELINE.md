# HYBRID BACKEND CAPABILITY BASELINE & COMPOSITION DEVELOPMENT REPORT

- **Run ID:** `hybrid-backend-capabilities`
- **Branch:** `feat/hybrid-backend-capabilities` (isolated backend worktree `.superpowers/worktrees/hybrid-backend-capabilities`)
- **Base Commit (`main = origin/main`):** `bb046fa22aceff47abe22aa783aa64fc65caee13` (`bb046fa22`)
- **Measured System Tree Hash:** `6e5e08c8a4ca0341b6c7c8ca57060fbaff74c7b86aa6ea3f12781005f494f8ed` (`so_file = 106` hashed entries across `MEASURED_SYSTEM_PATHS` = `105` unique files: `100` in `backend/app` + `5` in `frontend/src/simulations/domains/semantic`, with `semantic_program.schema.json` listed both via its directory and as an explicit path in `MEASURED_SYSTEM_PATHS`)
- **Scope:** **BACKEND ONLY** (`backend/app/**`, `backend/tests/**`, `backend/scripts/**`, `docs/**`; `frontend/**` untouched)
- **Measurement Class:** `OFFLINE_DETERMINISTIC_CAPABILITY_AND_REPLAY_DEVELOPMENT` (`ALLOW_LIVE_AI=0`, `0` live Gemini HTTP requests)
- **Status Tokens:**
  - `HYBRID_CAPABILITY_DEVELOPMENT_COMPLETE`
  - `PLANNER_DYNAMIC_COMPOSITION_VERIFIED`
  - `BACKEND_CAPABILITY_BASELINE_COMPLETE`
  - `PREVIOUS_CANDIDATE_VERIFIED`

---

## 1. Repository & Architecture State

### 1.1 Git & Worktree Baseline
- **Repository:** `D:\Documents\projects\algo-sim` (`https://github.com/nomozer/algo-sim`)
- **Base `main` / `origin/main`:** `bb046fa22aceff47abe22aa783aa64fc65caee13` (`bb046fa22`)
- **Dedicated Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-backend-capabilities` on branch `feat/hybrid-backend-capabilities`
- **Untracked User Data Preserved:** Root worktree `.playwright-mcp/` and `.superpowers/` preserved untouched; zero modifications to `frontend/**`.

### 1.2 Active Hybrid `/4` Pipeline Identity
`Vietnamese Problem / Multi-Attachment Input -> [Unified Input Ingestion] -> Gemini (TypedFactNext /2) -> Source Gate -> Bridge /2 -> FactGraph -> Planner /26 -> Registry /33 -> Exact Geometry Kernel /24 + IR Interpreter -> Adapter /4 + Construction Continuity -> Scene3D + Pedagogical Steps + Exact Results`

| Component | Module Path | Version / Surface Identity |
|---|---|---|
| Production Route Policy | `backend/app/main.py`, `backend/app/ai/route_policy.py` | `default_route_mode = "HYBRID"`, `HYBRID_ROUTE_MODE = "live"` (default), `"staging-replay"` (dev/test), `"off"` -> HTTP `503 INVALID_HYBRID_ROUTE_MODE` (zero fallback to retired `LLM_ONLY`) |
| Cache Policy | `backend/app/main.py`, `backend/app/ai/adapter4_route.py` | `CACHE_VERSION = "132"`, `ROUTE_D_CACHE_POLICY = "132:route-d"` |
| Extraction Contract | `backend/app/simulation/geometry_functions/typed_fact_next.py`, `backend/app/ai/typed_fact_next_extraction.py` | `typed-fact-next/2` (`TYPED_FACT_NEXT_V2_SCHEMA_VERSION`), surface SHA-256 `4070fd8ca6d6f67375e4bb0138319290049d0d658a4ef3e5078073d7c3f8498c` (unchanged) |
| Bridge & Scope Gate | `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py` | `typed-fact-next-bridge/2`, `typed-fact-next-scope/1` |
| Geometry Registry & Source Gate | `backend/app/simulation/geometry_functions/registry.py` | `geometry-functions/33` (`49` registered `FunctionSpec` primitives: `31` `provider_offered=True` [`30` in `PROVIDER_FUNCTIONS` + `1` `auxiliary_only=True` (`translate_point`)], `18` `provider_offered=False` internal-only) |
| FactGraph & Goal-Directed Planner | `backend/app/simulation/geometry_functions/planner.py` | `geometry-fact-planner/26` |
| Exact Geometry Kernel | `backend/app/simulation/geometry_functions/engine.py`, `backend/app/simulation/geometry/` | `geometry-function-engine/24` (`Fraction` / `Radical` exact arithmetic, `plane-section-certificate/1`) |
| Shared IR & Scene3D Verifier | `backend/app/simulation/semantic_program/interpreter.py`, `route.py` | `COMPATIBILITY_REQUIRED` (`RequestContract` internal topology bridge only) |
| Adapter `/4` & Continuity | `backend/app/ai/adapter4_route.py`, `backend/app/simulation/geometry_functions/construction_continuity.py` | `hybrid-simulation-adapter/4`, envelope `hybrid-route-d-simulation/4`, `coordinate_frame_id = "canonical_chart_v1"` |
| Unified Multi-Modal Ingestion | `backend/app/ingestion/unified_input.py`, `backend/app/ai/image_extract.py` | `POST /api/input/prepare` (up to 10 attachments, 25 MB total, 10 MB per file), `POST /api/image/extract` |

---

## 2. Existing Capability Inventory

### 2.1 `TypedFactNext /2` & Source Gate (`typed_fact_next.py`, `typed_fact_next_extraction.py`, `registry.py`)
- **Contract Structure (`TypedFactNextPayloadV2`):**
  - `solids`: `pyramid`, `prism`, `cylinder`, `cone`, `sphere` (`SolidSpec`, with `circumscribes` / `inscribed_in` sphere-host bindings).
  - `premises`: 20 closed premise kinds (`regular_polygon`, `rectangle`, `rhombus`, `parallelogram`, `right_trapezoid`, `isosceles_trapezoid`, `right_triangle`, `isosceles_triangle`, `equilateral_triangle`, `right_prism`, `regular_pyramid`, `regular_prism`, `perpendicular_line_plane`, `perpendicular_lines`, `parallel_lines`, `segment_length`, `angle_value`, `midpoint`, `centroid`, `divide_segment`, `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`, `altitude`, `sphere_radius`, `cylinder_dimensions`, `cone_dimensions`).
  - `described_points` (`DescribedPointSpec`): `@id` references for `midpoint`, `centroid`, `orthocenter`, `circumcenter`, `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`.
  - `derived_sections` (`DerivedSectionSpecV2`): `through_point_parallel_lines`, `through_point_perpendicular_line`, `two_lines`, and `constrained` (`contains_points`, `parallel_to_line`, `perpendicular_to_plane`), plus optional `stated_intersections` and `named_intersections`.
  - `simulation_goals`: `construct_object`, `highlight_geometry`, `construct_section`, `construct_derived_solid`, `animate_parameter`.
  - `math_goals`: `measurement` (`volume`, `area`, `lateral_area`, `radius`, `distance`, `angle`), `volume_ratio`, `residual_volume`.
  - `unresolved` (`UnresolvedSpec`): `ambiguous`, `missing_operand`, `unrecognized_term`, `unsupported`.
- **Source Gate (`registry.kiem_nguon` & `typed_fact_next_extraction.py`):**
  - Enforces exact source identity (`REPLAY_SOURCE_IDENTITY_MISMATCH`), verbatim quote membership (`QUOTE_NOT_IN_SOURCE`), clause-role verification (`GOAL_CLAUSE_NOT_PREMISE`, `CONDITIONAL_CLAUSE`, `QUESTION_CLAUSE_NOT_PREMISE`), negation detection (`NEGATED_CLAUSE`), solid-kind vs symbol consistency (`SOURCE_OBJECT_MISMATCH`), number grounding (`UNGROUNDED_VALUE`), and premise-coverage verification (`SOURCE_PREMISE_UNREAD`).

### 2.2 FactGraph & Planner `/26` (`planner.py`)
- **Two-Stage Architecture:**
  1. **Foundation Layout (`_dat_khoi`, `_dat_chop`, `_dat_lang_tru`, `_dat_khoi_cong`):** Deterministically places solid bases (`square`, `rectangle`, `rhombus`, `parallelogram`, `right_trapezoid`, `triangle` right/isosceles/equilateral/3-side) and resolves vertical/oblique apex or top-prism translation from altitude, perpendicular lateral edge, regular-pyramid lateral edges, face-plane dihedral angles, or line-plane angles.
  2. **Backward Goal Regression & Auxiliary Decomposition:**
     - **Registered Auxiliary Rules (`AUXILIARY_RULES`):**
       - `CHAN_VUONG_GOC_MAT` (`projection_foot`): `orthogonal_projection` for point-plane distance and line-plane angle.
       - `KHOANG_CACH_DIEM_DUONG`: `orthogonal_projection_line` + `ask_length` for point-line distance.
       - `DUONG_SONG_SONG_QUA_DIEM` (`parallel_line_witness`): `translate_point` for skew-line angle.
       - `DOAN_VUONG_GOC_CHUNG` (`distance_witness`): `skew_perpendicular_Points` for skew-line distance.
       - `MAT_CAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`, `MAT_RANG_BUOC` (with `_phap_tuyen` normal-candidate search), `DINH_CAT_CANH` (section cut vertices), `KHOI_DAN_XUAT` (derived pyramid on a section).
     - **General Backward Effect Resolver (`_EffectResolver`):**
       - Regresses typed needs (`Point`, `Line`, `Plane`, `PerpLine`, `AnswerDistance`, `AnswerLength`, `AnswerAngle`, `AnswerArea`) over all Registry `PlanningContract`s.
       - Regresses points defined by geometric properties (`POINT_DEFINITIONS`: `orthocenter`, `circumcenter`) via locus intersection (`_dinh_nghia`: 3 candidate `PerpLine` loci -> structural precondition filtering `_unmet` / `_tren_duong` -> selects 2 cheapest valid loci -> `intersect_line_line`).
       - Memoizes and reuses already-emitted identical calls at cost `0` (`reused_intermediates`).

### 2.3 Registry `/33` (`registry.py`)
- **`49` Registered Functions (`FunctionSpec` in `REGISTRY`):**
  - **`31` `provider_offered=True`:** `30` exposed in `PROVIDER_FUNCTIONS` + `1` with `auxiliary_only=True` (`translate_point`).
  - **`18` `provider_offered=False` (internal-only):** internal base/solid/section/measurement helpers (`quad_square`, `quad_rectangle`, `quad_rhombus`, `quad_parallelogram`, `quad_right_trapezoid`, `pyramid_regular_base`, `pyramid_right_triangle_base`, `pyramid_triangle_base`, `prism_regular_base`, `prism_right_triangle_base`, `prism_triangle_base`, `derived_pyramid`, `section`, `section_through_parallel`, `section_by_two_lines`, `ask_section_area`, `ask_section_Through_parallel_area`, `ask_section_by_two_lines_area`).
  - **14 Solid / Base Builders:** `pyramid`, `regular_pyramid`, `prism`, `regular_prism`, `pyramid_regular_base`, `pyramid_right_triangle_base`, `pyramid_triangle_base`, `prism_regular_base`, `prism_right_triangle_base`, `prism_triangle_base`, `quad_square`, `quad_rectangle`, `quad_rhombus`, `quad_parallelogram`, `quad_right_trapezoid`, `cylinder`, `cone`, `sphere`.
  - **15 Point / Line / Section / Derived-Solid Constructors:** `midpoint`, `divide_segment`, `centroid`, `orthogonal_projection`, `orthogonal_projection_line`, `translate_point`, `intersection_line`, `intersect_line_line`, `intersect_line_plane`, `section`, `section_through_parallel`, `section_by_two_lines`, `derived_pyramid`, `circumscribed_sphere`, `inscribed_sphere`.
  - **16 Measurement / Goal Evaluators:** `ask_volume`, `ask_volume_ratio`, `ask_residual_volume`, `ask_area`, `ask_section_area`, `ask_section_Through_parallel_area`, `ask_section_by_two_lines_area`, `ask_lateral_area`, `ask_total_area`, `ask_radius`, `ask_length`, `ask_distance_point_plane`, `ask_distance_line_plane`, `ask_distance_planes`, `ask_distance_lines`, `ask_angle_line_plane`, `ask_angle_plane_plane`, `ask_angle_lines`.

### 2.4 Exact Geometry Kernel `/24` & IR Verification (`engine.py`, `radical.py`, `curved.py`, `interpreter.py`)
- **Exact Symbolic Representation:** All coordinates and Gram metrics live in $\mathbb{Q}(\sqrt{d})$ (`Fraction` and normalized `Radical` with square-factor extraction before `MAX_RADICAND = 10**12`, `MAX_ABS_COEF = 10**12`).
- **Independent Self-Check Certificates (`KetQuaTuyen`):**
  - Re-verifies every premise, perpendicularity, parallelism, incidence, triangle center (`orthocenter` all 3 altitudes, `circumcenter` all 3 equidistant vertices + coplanarity), and section polygon (`plane-section-certificate/1`: Category A `DINH_CAT_CANH` and Category B `ENGINE_DERIVED_SECTION` verifying closure, coplanarity, convexity, non-collinearity, and `area²`).
  - Curved solids (`curved.py`): exact rational/radical volumes, surface areas, radii, plane sections of spheres/cylinders, and circumscribed/inscribed spheres of polyhedra and axial solids.

### 2.5 Adapter `/4`, `Scene3D` & Construction Continuity (`adapter4_route.py`, `function_route.py`, `construction_continuity.py`)
- Builds `Scene3D` (`objects`, `events`, `formation.steps`) and enriches every step with `step_id`, `coordinate_frame_id = "canonical_chart_v1"`, `depends_on`, `preconditions`, `created_ids`, `reused_ids`, `highlighted_ids`, `retired_ids`, `verification_refs`, and 5-part pedagogical `step_summary` (`what`, `inputs`, `validity`, `result`, `next_use`).
- Fail-closed `validate_construction_continuity(scene)` checks 7 invariants (`DEPENDENCY_BEFORE_CREATION`, `OBJECT_IDENTITY_MUTATION`, `GEOMETRIC_STEP_CONTRADICTION`, `MISSING_OBJECT_PROVENANCE`, `UNEXPLAINED_OBJECT_DISAPPEARANCE`, `MEASUREMENT_USES_UNDETERMINED_OBJECT`, `SECTION_OR_INTERSECTION_MISMATCH`).

### 2.6 Backend Image Extraction & Multi-Attachment Ingestion (`unified_input.py`, `image_extract.py`)
- `POST /api/input/prepare`: supports ordered `attachments` (`MAX_PREPARE_ATTACHMENTS = 10`, `MAX_TOTAL_ATTACHMENT_BYTES = 25 MB`, per-file `<= 10 MB`), magic-byte MIME validation (PNG, JPEG, WEBP, GIF, PDF, DOCX, TXT), overlap deduplication (`merge_overlapping_problem_segments`), diagram-only attachment pairing, multi-problem `needs_selection` + `selected_candidate_id`, and fail-closed `needs_confirmation`/`rejected`.
- `POST /api/image/extract` & `read_problem_image`: honors `ALLOW_LIVE_AI=0`, sends credentials only via `x-goog-api-key` header, and enforces timeout/size ceilings.

---

## 3. Planner Composition Analysis

### 3.1 How Planner `/26` Composes Registered Functions
Planner `/26` (`backend/app/simulation/geometry_functions/planner.py`) performs goal-directed composition through two complementary mechanisms:
1. **Backward Effect Search (`_EffectResolver._resolve` & `_dinh_nghia`):**
   - Each goal or unnamed described operand is translated into a typed need (`Point`, `Line`, `Plane`, `PerpLine`, `AnswerDistance`, `AnswerLength`, `AnswerAngle`, `AnswerArea`).
   - `_EffectResolver` searches all `PlanningContract`s in `REGISTRY` whose `effect.kind` matches the need, expands free slots (`contract.free`) over the vertices of the active plane `W`, checks structural preconditions (`_unmet` / `off_line` via `_tren_duong`) *before* coordinate evaluation, recursively resolves child input needs (`depth + 1`), and checks if an identical call already exists in `plan.calls` (`same_call`) to reuse at `cost = 0` (`reused_intermediates += 1`).
   - For property-defined points (`POINT_DEFINITIONS`: `orthocenter`, `circumcenter`), `_dinh_nghia` generates 3 candidate `PerpLine` locus sub-needs, prunes degenerate candidates structurally (`off_line`), selects the 2 lowest-cost valid loci (`orthogonal_projection_line` + `line_perpendicular_through_point` when off-line, or `midpoint` + `line_perpendicular_in_plane`), and composes them into `intersect_line_line`.
2. **Constrained-Plane Witness Search (`MAT_RANG_BUOC` & `_phap_tuyen`):**
   - For a plane defined by relational constraints (`contains_points`, `parallel_to_line`, `perpendicular_to_plane`), `_phap_tuyen` searches for the lowest-cost `Normal(Q)` producer: either a cost-0 stated perpendicularity premise or a cost-1 `orthogonal_projection` from a solid vertex `Z` structurally proven not to lie on plane `Q`, followed by `translate_point` witness construction.

### 3.2 Honest C16/C17/C18 Provenance Taxonomy
As locked in `planner.py:2081-2091` and `planner.py:2355-2360` (and verified by `test_planner_recomposition_oracle.py` and `test_route_d_function_composition.py`):
- `SOURCE_EXPLICIT_SEQUENCE`: `planner_originated_steps == []` or all planner steps are `source_defined` (steps directly realizing a single stated `DescribedPointSpec` descriptor or `DEFINITION_FUNCTIONS`).
- `REGISTERED_DECOMPOSITION`: `planner_originated_steps` contains steps tagged `'registered'` (steps emitted under `POINT_DEFINITIONS` locus regression `under=True` or contracts whose `source_policy` is in `_RULE_POLICIES`), with `search_generated_steps == []`.
- `DISCOVERED_FUNCTION_COMPOSITION`: emitted only when `search_generated_steps` is non-empty (i.e. a contract with `descriptor is None`, `source_policy not in _RULE_POLICIES`, and `under=False` is selected by `_EffectResolver`). Under the current production `REGISTRY /33`, all registered contracts either carry a `descriptor` or belong to `_RULE_POLICIES` / `POINT_DEFINITIONS`, so production runs classify multi-step locus/rule compositions as `REGISTERED_DECOMPOSITION`. However, `_EffectResolver` is contract-driven: registering a new `PlanningContract` with `descriptor=None` and `source_policy="goal_decomposition"` is immediately discovered and composed without modifying `planner.py` (proven in `test_contract_only_extension_and_ablation_in_effect_resolver`).

### 3.3 Discriminating Composition Probes & Search Telemetry
All probes are locked in `backend/tests/geometry/test_hybrid_capability_composition.py` and profiled in `docs/evaluation/geometry/runs/hybrid-backend-capabilities/results/capability_telemetry_metrics.json`:

| Probe Case | Solid Topology | Goal(s) | `explored_states` | `candidate_evaluations` | `max_depth_reached` | `pruned_nodes` | `reused_intermediates` | `planner_originated_steps` | Classification | Exact Answer(s) |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| **Case 1** (`test_case1`) | Pyramid `S.ABCD` | $V(S.ABCD)$, $d(A, (SBC))$ | `4` | `3` | `1` | `0` | `0` | `1` (`projection_foot`) | `SOURCE_EXPLICIT_SEQUENCE` / `REGISTERED_DECOMPOSITION` | `8/3`, `√2` |
| **Case 2** (`test_case2`) | Pyramid `S.ABCD` | $d(A, SB)$ (named point to line) | `0` | `0` | `0` | `0` | `0` | `1` (`g1_foot`) | `REGISTERED_DECOMPOSITION` | `√2` |
| **Case 3a** (`test_case3a`) | Pyramid `S.ABCD` ($M = \text{mid}(AB)$) | $d(\text{orthocenter}(CDM), (SAB))$ & $d(\text{circumcenter}(CDM), (SAB))$ | `24` | `29` | `3` | `9` | `1` (shared foot on $CD$) | `10` (`8` registered + `2` foot) | `REGISTERED_DECOMPOSITION` | `3/2`, `5/4` |
| **Case 3b** (`test_case3b`) | Right Prism `ABC.A'B'C'` ($M = \text{mid}(BC)$) | $d(\text{orthocenter}(BC'M), (ABC))$ & $d(\text{circumcenter}(BC'M), (ABC))$ | `24` | `29` | `3` | `9` | `1` (shared foot) | `10` | `REGISTERED_DECOMPOSITION` | `25/4`, `33/8` |
| **Case 4** (`test_case4`) | Pyramid `S.ABCD` | Unsupported `lateral_area` on polyhedron; `orthocenter` ablations | N/A | N/A | N/A | N/A | N/A | `0` | Refused fail-closed (`BRIDGE_UNSUPPORTED_MEASUREMENT` / `UNSUPPORTED_CAPABILITY`) | Refused (`0` wrong-served) |

---

## 4. Test & Corpus Map

| Area | Primary Test Suites (`backend/tests/`) | Offline Evaluation Corpora (`docs/evaluation/`) |
|---|---|---|
| `TypedFactNext /2` Schema & Extraction | `tests/geometry/test_typed_fact_next.py`, `tests/geometry/test_typed_fact_next_extraction.py` | `runs/hybrid-live-extraction-retest/full/{k1,s2,r1}-live.jsonl` (70 captured live Gemini payloads) |
| Bridge `/2` & Solid Scope (`S8`) | `tests/geometry/test_typed_fact_next_bridge.py`, `tests/geometry/test_route_d4_described_points.py` | `runs/hybrid-master-backend-replacement/{k1,s2,r1}-*-corpus.json` (70 gold + oracle cases) |
| Source Gate (`registry.kiem_nguon`) | `tests/geometry/test_source_gate_hardening.py`, `tests/geometry/test_route_d_semantic_shape_invariants.py` | `runs/hybrid-backend-reliability/results/source-gate-distortion.json` (50 distortion cases) |
| Planner `/26` & Dynamic Composition | `tests/geometry/test_planner_recomposition_oracle.py`, `tests/geometry/test_planner_defined_points.py`, `tests/geometry/test_route_d_function_composition.py`, `tests/geometry/test_hybrid_capability_composition.py` | `runs/hybrid-v2-independent-vietnamese-geometry-holdout-wave3/` (144 cases: 72 pos, 72 neg) |
| Exact Kernel `/24` & Curved Solids | `tests/geometry/test_exact_radical.py`, `tests/geometry/test_curved_solids.py`, `tests/geometry/test_hybrid4_three_point_plane_sections.py` | `semantic-benchmark/dev/cases.json` (20 cases), `sealed/cases.json` |
| Adapter `/4`, `Scene3D` & Continuity | `tests/geometry/test_construction_continuity.py`, `tests/geometry/test_final_backend_product_completion.py`, `tests/geometry/test_hybrid_cutover_verification.py` | `runs/hybrid-backend-reliability/results/http-e2e-summary.json` (994 replay texts) |
| Multi-Image & Document Ingestion | `tests/test_multi_image_prepare.py`, `tests/test_unified_input_20_cases.py`, `tests/test_image_extract_api.py` | Synthetic & fixture image/PDF/DOCX/TXT suites in `tests/` |

---

## 5. Capability Matrix

| Capability Domain | Sub-Capability / Construct | Status | Notes / Refusal Boundary |
|---|---|---|---|
| **Solids & Bases** | Pyramid (`S.ABC`, `S.ABCD`) with square, rectangle, rhombus, parallelogram, right-trapezoid, right/isosceles/equilateral/3-side triangle base | **SUPPORTED** | Exact coordinates in $\mathbb{Q}(\sqrt{d})$. |
| **Solids & Bases** | Right prism & oblique prism (`ABC.A'B'C'`, `ABCD.A'B'C'D'`) | **SUPPORTED** | Oblique prism supported when lateral edge projection onto base is specified; lateral-edge angle alone refuses `UNSUPPORTED_CAPABILITY`. |
| **Solids & Bases** | Standalone & composite `sphere`, `cylinder`, `cone`, circumscribed/inscribed spheres | **SUPPORTED** | Exact symbolic $\pi$ factors and radical radii/volumes/areas. |
| **Auxiliary Points** | `midpoint`, `divide_segment` (rational ratio), `centroid`, `orthogonal_projection` (point-plane), `orthogonal_projection_line` (point-line), `intersect_line_line`, `intersect_line_plane` | **SUPPORTED** | Both named premises and unnamed `@id` `DescribedPointSpec` (depth 1). |
| **Property-Defined Points** | `orthocenter`, `circumcenter` via `_EffectResolver._dinh_nghia` locus regression | **SUPPORTED** | Composes 2 perpendicular/bisector loci + `intersect_line_line`; engine certifies all 3 loci. |
| **Derived Sections** | Plane through 3 points (`(MNP)`), through point $\parallel$ 2 lines, through 2 intersecting/parallel lines, through point $\perp$ line (pyramid), constrained plane (`MAT_RANG_BUOC`) | **SUPPORTED** | Category A (`DINH_CAT_CANH`) and Category B (`ENGINE_DERIVED_SECTION`, `plane-section-certificate/1`). Structural coplanarity in `_phap_tuyen` now covers `midpoint`, `divide_segment`, `centroid`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`. |
| **Derived Sections** | Partial stated lateral cuts (`ISSUE-ARCH-PARTIAL-STATED-CUT-NAMING`) | **PARTIAL** | Refuses fail-closed with `SECTION_BOUNDARY_INCOMPLETE` when stated cuts omit a cut edge of the closed polygon. |
| **Math Goals** | `volume`, `volume_ratio` (rational), `residual_volume`, `area` (face/triangle/section), `lateral_area` (curved), `radius` (curved/sphere), `distance` (point-point, point-line, point-plane, line-plane, plane-plane, skew lines), `angle` (line-line, line-plane, dihedral) | **SUPPORTED** | Certified in exact `Fraction`/`Radical` arithmetic. |
| **Nested Described Points** | Depth $\ge 2$ `@id` inside `@id` or two `@id` operands in one goal | **MISSING (Fail-Closed)** | Refuses `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` until Source Gate effect-chain certification is generalized. |
| **Clarification Recovery** | `UnresolvedSpec` (`ambiguous`, `missing_operand`, `unrecognized_term`) -> `route-d-clarification/1` | **SUPPORTED** | Now normalizes cascading secondary ellipsis items and incomplete `math_goals` while preserving `OUT_OF_SCOPE` precedence for nested `unsupported` operands. |
| **Diacritic-Free Input** | Unaccented Vietnamese geometry input (`ISSUE-ARCH-ROUTE-D-DIACRITIC-FREE-INPUT`) | **PARTIAL (Offline Prototype)** | Refuses `GATE_OUT_OF_SCOPE` on production route; offline prototype `backend/scripts/s1_diacritic_offline.py` awaits Owner decision `S-1`. |

---

## 6. Prioritized Gap List

From our Phase A capability discovery across the codebase and captured C26/Wave-3 corpora, we identified and ranked the concrete backend capability gaps:

1. **[SELECTED — HIGHEST IMPACT ON PLANNER COMPOSITION & CONSTRAINED SECTIONS] Proven Gap 1: Incomplete Structural Incidence Propagation in `planner._phap_tuyen` and `_EffectResolver._tren_duong` (`backend/app/simulation/geometry_functions/planner.py`)**
   - **Root Cause Layer:** `Planner /26` (`planner.py:1758-1777` and `planner.py:2118-2122`).
   - **Evidence:** When a constrained section plane `(P)` is perpendicular to a reference plane `Q` named using a non-midpoint constructed point on a solid edge or face — such as `M` dividing `AB` (`divide_segment`), `G` centroid of `SAB` (`centroid`), `H` projection onto `SB` (`orthogonal_projection_line`), or `O = AC ∩ BD` (`intersect_line_line`) — `_phap_tuyen` only recognized `point_kind == "midpoint"` when computing which solid vertices lie on `Q` (`tren_q`). Consequently, for `Q = (SAM)` (which is face `(SAB)`), `_phap_tuyen` failed to infer that vertex `B` lies on `(SAM)`, selected `Z = B` as the normal-projection vertex, and emitted `orthogonal_projection(point=B, plane=[S, A, M])`, which crashed in the Exact Kernel with `ENGINE_SELF_CHECK_FAILED` (`projected point coincides with foot`). Similarly, `_EffectResolver._tren_duong` only checked `midpoint` premises when evaluating `off_line` preconditions.
2. **[SELECTED — HIGHEST IMPACT ON LIVE EXTRACTED CLARIFICATION RELIABILITY] Proven Gap 2: Live-Observed C26 Multi-Unresolved & Incomplete-Goal Wire-Shape Refusals (`backend/app/ai/typed_fact_next_extraction.py`)**
   - **Root Cause Layer:** `TypedFactNext /2` Extraction Wire-Shape Normalization (`typed_fact_next_extraction.py`).
   - **Evidence:** In captured C26 live Gemini 2.5 Flash outputs (`docs/evaluation/geometry/runs/hybrid-live-extraction-retest/full/s2-live.jsonl`), 3 of the 6 `CLARIFY` cases in `S-2` failed to produce a verified clarification:
     - `S2-C-D05_projection_missing_target`: Gemini emitted a valid verbatim `unresolved[0]` (`quote="Gọi H là hình chiếu của S"`, `missing_roles=["target_line_or_plane"]`, `candidate_relations=["orthogonal_projection"]`) plus a cascading secondary `unresolved[1]` on the simulation sentence with an ellipsis (`quote="Mô phỏng ... điểm H"`), causing `_check_quotes` to reject the entire payload with `QUOTE_NOT_IN_SOURCE`.
     - `S2-C-C04_angle_plane_missing`: For `"Tính góc giữa SB và mặt phẳng."`, Gemini emitted both `unresolved[0]` (`quote="mặt phẳng"`, `kind="missing_operand"`) and a partial `math_goals[0]` (`target={"line": ["S", "B"]}` missing `"plane"`), causing `parse_typed_fact_next_v2` to reject with `INVALID_MATH_GOAL` before `bridge_v2` could return `AMBIGUOUS_FACT` (`route-d-clarification/1`).
     - `S2-C-A01_goc_chieu`: Gemini emitted a specific `ambiguous` entry `unr2` (`missing_roles` + `candidate_relations` populated) alongside empty-role/empty-relation companion entries `unr1` and `unr3`, causing `bridge_v2` to pick `unr1` (`WRONG_REASON_CLARIFICATION`).
3. **[DEFERRED — REQUIRES KERNEL/ADAPTER CONTRACT DESIGN] `ISSUE-ARCH-PARTIAL-STATED-CUT-NAMING`**: Partial stated lateral cut vertices in `DINH_CAT_CANH` (`SECTION_BOUNDARY_INCOMPLETE`).
4. **[DEFERRED — REQUIRES SOURCE GATE EFFECT-CHAIN DESIGN] Depth-2 Nested `DescribedPointSpec` (`@id` inside `@id`)**: Currently refuses fail-closed with `BRIDGE_UNSUPPORTED_DESCRIBED_POINT`.
5. **[DEFERRED — GATED ON OWNER DECISION `S-1`] `ISSUE-ARCH-ROUTE-D-DIACRITIC-FREE-INPUT`**: Unaccented Vietnamese input normalization.

---

## 7. Implemented Improvements

### 7.1 Improvement 1 — Structural Collinearity & Face-Coplanarity Closure in `planner.py`
- **File Modified:** `backend/app/simulation/geometry_functions/planner.py`
- **Design & Implementation:**
  1. Added `_bo_ba_thang_hang(facts) -> list[tuple[str, str, str]]` extracting all purely structural collinear triples `(P, A, B)` from non-negated premises:
     - `point_def` with `point_kind in ("midpoint", "divide_segment")` on segment `(A, B)`
     - `projection` (`orthogonal_projection_line`) with foot `at` on line `(A, B)`
     - `point_def` with `point_kind == "intersect_line_line"` on both input segments `points_a` and `points_b`
     - `point_def` with `point_kind == "intersect_line_plane"` on the input line `points_a`
  2. Extended `_phap_tuyen(q_mat, kh, k)` to propagate both `_bo_ba_thang_hang` collinear triples and `centroid` triangle-face premises (`trong_tam`) in a 3-pass structural fixed-point closure over the solid's faces `mats` and target plane `tren_q`. Any solid vertex lying on the same face as `q_mat` is structurally rejected (`rejected: "lies on the plane (solid structure)"`) before candidate selection.
  3. Extended `_EffectResolver._tren_duong(self, p, line)` to check both `any(x == p and {a, b} == ends for x, a, b in _bo_ba_thang_hang(self.facts.values()))` and unnamed described points `("desc", kind, ...)` on `ends` (`midpoint`, `divide_segment`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`), recognizing points defined on segment/line `ends` while preserving Engine-level `COLLINEAR_POINTS` refusal (`K-D01`, `K-D02`) when a degenerate collinear triangle is passed as a triangle-center goal.

### 7.2 Improvement 2 — Live-Observed Clarification Wire-Shape Normalization in `typed_fact_next_extraction.py`
- **File Modified:** `backend/app/ai/typed_fact_next_extraction.py`
- **Design & Implementation:**
  - Added `_repair_unresolved_clarifications(out, text)` inside `_repair_observed_wire_shapes(out)` (which runs on both live `TransportExtractor` and offline `extract_typed_fact_next_v2`):
    1. When `unresolved` contains a primary entry `p` (`kind in ("ambiguous", "missing_operand")`, verbatim `p["quote"] in text`, non-empty `missing_roles`, and non-empty `candidate_relations`), a secondary entry `u` is pruned **only** when bound to `p` via one of three closed local companion relations:
       - Non-verbatim ellipsis reference (`"..." in u["quote"]`) mentioning `p["subject_ref"]` (e.g. `S2-C-D05`),
       - Empty-role/empty-relation `ambiguous`/`missing_operand` sub-span literally contained inside `p["quote"]` (`u["quote"] in p["quote"]`, e.g. `unr1` in `S2-C-A01`),
       - Empty-role/empty-relation simulation-verb wrapper (`Mô phỏng/Vẽ/Dựng...`) mentioning `p["subject_ref"]` in the same sentence as `p["quote"]` (e.g. `unr3` in `S2-C-A01`) — **never** pruning `u["kind"] == "unsupported"` when nested inside or sharing `subject_ref` with a geometric relation (`R1-F03`), and **never** dropping independent `unresolved` items in other clauses or on other subjects.
    2. When `math_goals` contains an incomplete target dict (`not shape_valid`) whose `mg["quote"]` is verbatim in `text` and contains the verbatim `u["quote"]` of a `missing_operand`/`ambiguous` `unresolved` entry, the incomplete goal is folded into that `unresolved` entry (widening `u["quote"]` to the verbatim `mg["quote"]` when `u["quote"]` is a sub-phrase), preventing `INVALID_MATH_GOAL` from masking a genuine `route-d-clarification/1` response.
  - **Fail-Closed Guarantees Preserved:** Single non-verbatim `unresolved` quotes still fail with `QUOTE_NOT_IN_SOURCE`; incomplete `math_goals` without a matching verbatim `unresolved` entry still fail with `INVALID_MATH_GOAL`; nested `unsupported` operands (`R1-F03`) still refuse with `OUT_OF_SCOPE`; independent `unresolved` items in different clauses/subjects are preserved (`test_gap2_multiple_independent_unresolved_items_preserved`).

---

## 8. Before / After Verification

### 8.1 Proven Gap 1 — Constrained-Plane Normal Search & Collinear Preconditions

| Case | Problem / Plane Constraint | Before Fix | After Fix |
|---|---|---|---|
| **Gap 1A** (`test_gap1a`) | $M$ divides $AB$ ($AM = \frac{1}{3}AB$); section $(P)$ through $S, N \perp (SAM)$ | `REFUSED` (`ENGINE_SELF_CHECK_FAILED`: rejected only $\{A, S\}$, selected $B \in (SAM)$) | **`SERVED` (`VERIFIED`)**, rejected $\{A, B, S\}$, selected $C$, exact area `√5` |
| **Gap 1B** (`test_gap1b`) | $G$ centroid of $\triangle SAB$; section $(P)$ through $S, N \perp (SAG)$ | `REFUSED` (`ENGINE_SELF_CHECK_FAILED`: rejected only $\{A, S\}$, selected $B \in (SAG)$) | **`SERVED` (`VERIFIED`)**, rejected $\{A, B, S\}$, selected $C$, exact area `√5` |
| **Gap 1C** (`test_gap1c`) | $H$ projection of $A$ on $SB$; section $(P)$ through $S, N \perp (SAH)$ | `REFUSED` (`ENGINE_SELF_CHECK_FAILED`: rejected only $\{A, S\}$, selected $B \in (SAH)$) | **`SERVED` (`VERIFIED`)**, rejected $\{A, B, S\}$, selected $C$, exact area `√5` |
| **Gap 1D** (`test_gap1d`) | $O = AC \cap BD$; section $(P)$ through $S, N \perp (SCO)$ | `REFUSED` (`ENGINE_SELF_CHECK_FAILED`: rejected only $\{C, S\}$, selected $A \in (SCO)$) | **`SERVED` (`VERIFIED`)**, rejected $\{A, C, S\}$, selected $B$, exact area `√17/2` |
| **Gap 1E** (`test_gap1e` & `test_gap1_extension`) | `_EffectResolver._tren_duong` for `divide_segment` $M \in AB$ (inside or extension $k = 3/2$) and unnamed `("desc", ...)` points on $AB$ | `False` (only checked `midpoint`) | **`True`** (while keeping `_tren_duong("B", ("named", ("A", "M"))) == False` so `K-D01`/`K-D02` refuse `COLLINEAR_POINTS`) |
| **Negative Twins** (`test_gap1_negative_twins`) | Through $A, S \perp (ABCD)$ (non-unique); through $A, M, N \perp (SAM)$ (coincides with base) | `REFUSED` (`PLANE_NOT_UNIQUE` / `SECTION_PLANE_IS_FACE`) | **`REFUSED` (`PLANE_NOT_UNIQUE` / `SECTION_PLANE_IS_FACE`, `0` wrong-served)** |

### 8.2 Proven Gap 2 — C26 Live-Replay Clarification Recovery (`70` Cases Across `K-1`, `S-2`, `R-1`)

| Metric / Case | Before Fix | After Fix | Delta |
|---|---|---|---|
| `S2-C-D05_projection_missing_target` | `REFUSED` (`QUOTE_NOT_IN_SOURCE`, `WRONG_REASON_REFUSAL`) | **`CLARIFY` (`AMBIGUOUS_FACT`, `MISSING_DATA`, `CORRECT_CLARIFICATION`)** | **Fixed (`RED -> GREEN`)** |
| `S2-C-C04_angle_plane_missing` | `REFUSED` (`INVALID_MATH_GOAL`, `WRONG_REASON_REFUSAL`) | **`CLARIFY` (`AMBIGUOUS_FACT`, `MISSING_DATA`, `CORRECT_CLARIFICATION`)** | **Fixed (`RED -> GREEN`)** |
| `S2-C-A01_goc_chieu` | `CLARIFY` (`WRONG_REASON_CLARIFICATION`, picked `unr1`) | **`CLARIFY` (`AMBIGUOUS_FACT`, `AMBIGUOUS`, `CORRECT_CLARIFICATION`, picked `unr2`)** | **Fixed (`RED -> GREEN`)** |
| `R1-F03` (nested `unsupported` operand) | `REFUSED` (`OUT_OF_SCOPE`, `capability_gap`) | **`REFUSED` (`OUT_OF_SCOPE`, `capability_gap`)** | **Preserved** |
| `S-2` `CLARIFY` Status + `route-d-clarification/1` | `3 / 6` (`50.0%`) | **`5 / 6` (`83.3%`)** | **`+2` cases** |
| `S-2` Strict Gold-Verified `CORRECT_CLARIFICATION` | `0 / 6` (`0.0%`) | **`3 / 6` (`50.0%`)** | **`+3` cases** |
| `S-2` Strict Gold-Projection End-to-End Correct | `26 / 36` (`72.22%`) | **`29 / 36` (`80.56%`)** | **`+3` cases** |
| Combined 70-Case C26 Positive Served Exact Oracle | `40 / 41` (`97.56%`) | **`40 / 41` (`97.56%`)** | **Preserved (`0` regressions)** |
| Combined 70-Case C26 Non-Positive Refused / Clarified | `29 / 29` (`100.0%`) | **`29 / 29` (`100.0%`)** | **Preserved (`0` wrong-served)** |
| Gold Replay Baselines (`K-1` / `S-2` / `R-1`) | `16/16` · `35/36` · `18/18` | **`16/16` · `35/36` · `18/18`** | **100% Locked** |

### 8.3 CPU, Memory & Latency Measurements
From `docs/evaluation/geometry/runs/hybrid-backend-capabilities/results/capability_telemetry_metrics.json`:
- **8 Profiled Composition & Constrained-Section Cases (`Case 1`, `Case 2`, `Case 3a`, `Case 3b`, `Gap 1A–1D`):**
  - Cold-Start First Case (`Case1_Direct_Primitive`, includes initial module/schema setup): `wall = 551.41 ms`, `peak_memory = 954.09 KB`
  - Warm Steady-State (`7` subsequent cases): `warm_wall_p50_ms = 243.50 ms`, `warm_wall_p95_ms = 295.70 ms`, `warm_cpu_p50_ms = 250.00 ms`, `warm_peak_memory_max_kb = 1,165.24 KB`
  - All 8 Cases Combined (including cold start): `wall_p50_ms = 246.82 ms`, `wall_p95_ms = 551.41 ms`, `cpu_p50_ms = 250.00 ms`, `peak_memory_max_kb = 1,165.24 KB`
- **70 C26 Offline Live-Replay Cases (`K-1`, `S-2`, `R-1`, exact values from `capability_telemetry_metrics.json`):**
  - `K-1` (`16` cases): `latency_p50_ms = 39.41 ms`, `latency_p95_ms = 57.37 ms`
  - `S-2` (`36` cases): `latency_p50_ms = 13.10 ms`, `latency_p95_ms = 27.65 ms`
  - `R-1` (`18` cases): `latency_p50_ms = 21.35 ms`, `latency_p95_ms = 59.88 ms`

---

## 9. Remaining Open Items

1. **`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`**: External author-curated holdout `H-1` remains unmeasured (C26 and offline replay are developer-curated pilots/replays, not independent `H-1` validation).
2. **`ISSUE-ARCH-PARTIAL-STATED-CUT-NAMING`**: Partial stated lateral cut vertices in `DINH_CAT_CANH` refuse fail-closed with `SECTION_BOUNDARY_INCOMPLETE` when unstated lateral edges are also cut.
3. **`ISSUE-ARCH-ROUTE-D-DIACRITIC-FREE-INPUT`**: Unaccented Vietnamese geometry input remains gated on Owner decision `S-1`.
4. **Depth $\ge 2$ Nested `DescribedPointSpec` (`BRIDGE_UNSUPPORTED_DESCRIBED_POINT`)**: Describing a point via another unnamed `@id` point or using two `@id` points in one measurement goal remains fail-closed until Source Gate effect-chain certification is generalized.

---

## 10. Phase 0 Candidate Validation & Reconciliation (`PREVIOUS_CANDIDATE_VERIFIED`)

1. **Edge-Case Hardening Verified (`test_hybrid_capability_composition.py` — `17/17 PASS`):**
   - `test_gap1_extension_collinearity_and_described_point_on_line_precondition`: verifies `_bo_ba_thang_hang` and `_EffectResolver._tren_duong` on points dividing a segment with extension ratio ($k = 3/2 > 1$) and on unnamed `("desc", ...)` points (`divide_segment`, `orthogonal_projection_line`, `intersect_line_line`).
   - `test_gap2_multiple_independent_unresolved_items_preserved`: verifies that `_repair_unresolved_clarifications` never drops an independent `unresolved` item in another clause or on another subject (`u_k` on `K`) when a structured `unresolved` item (`u_h` on `H`) is also present.
2. **Numerical Reconciliation Across Report, `run.json`, `capability_telemetry_metrics.json`, and `EVALUATION_CANDIDATE.json`:**
   - **Registry `/33` counts:** `49` total `FunctionSpec` in `REGISTRY` = `31` `provider_offered=True` (`30` exposed in `PROVIDER_FUNCTIONS` + `1` `auxiliary_only=True` `translate_point`) + `18` `provider_offered=False` (internal-only).
   - **Candidate file counts:** `EVALUATION_CANDIDATE.json` hashes `so_file = 106` entries across `MEASURED_SYSTEM_PATHS` = `105` unique files (`100` in `backend/app` + `5` in `frontend/src/simulations/domains/semantic`), because `frontend/src/simulations/domains/semantic/semantic_program.schema.json` appears both inside the `frontend/src/simulations/domains/semantic` directory walk and as an explicit path in `MEASURED_SYSTEM_PATHS`.
   - **Clarification before/after metrics:** `S-2` `CLARIFY` status recovered: `3/6 -> 5/6`; strict gold-verified `CORRECT_CLARIFICATION`: `0/6 -> 3/6`; `S-2` strict gold-projection E2E: `26/36 -> 29/36`.
   - **Latency separation:** Cold-start first case (`551.41 ms`) vs warm steady-state (`warm_wall_p50_ms = 243.50 ms`, `warm_wall_p95_ms = 295.70 ms`) and C26 study replay (`K-1` `39.41 ms` / `57.37 ms`, `S-2` `13.10 ms` / `27.65 ms`, `R-1` `21.35 ms` / `59.88 ms`) match `results/capability_telemetry_metrics.json` to the decimal.
3. **Verdict Token:** `PREVIOUS_CANDIDATE_VERIFIED`.
