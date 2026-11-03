# ALGOSIM_HYBRID_CUTOVER_FINAL_REPORT.md

> **Owner-Directed Architecture Cutover (`ALGOSIM — FINAL HYBRID ARCHITECTURE CUTOVER`)**
> Replaces `LLM_ONLY` with Hybrid `/4` as the official default production pipeline of AlgoSim, retires unused legacy execution modules, verifies full product regression (`FULL_PRODUCT_GATE_PASS`), integrates onto `main`, pushes to GitHub `origin/main`, and safely removes the merged backend worktree and local branch.

---

## 1. Mandatory Cutover & Validation Statuses

| Status Key | Verdict | Grounded Basis |
|---|---|---|
| `HYBRID_DEFAULT_CUTOVER_COMPLETE` | **`YES`** | `POST /api/analyze` routes exclusively through Hybrid `/4` (`HYBRID_ROUTE_MODE = live` by default; `staging-replay` for dev/test; `0` fallback paths to `LLM_ONLY`). |
| `LEGACY_EXECUTION_RETIRED` | **`YES`** | `pipeline.py::run_pipeline`, `stage_semantic_program`, LLM program-generation/repair prompts, Compiler C (`geometry_compiler/*`), and Adapter `/3` (`adapter3_simulation.py`) are physically deleted and verified unimportable. |
| `LEGACY_FULLY_RETIRED` | **`NO`** | `semantic_program/route.py` and the IR verifier remain as `COMPATIBILITY_REQUIRED` shared infrastructure for deterministic IR/Scene3D validation and T3 Gate 4 (`replay_demo_cases.py`), never as an LLM synthesis orchestrator. |
| `PRODUCTION_DEPLOYMENT_VERIFIED` | **`NO`** | Repository has no `.github/workflows` CI/CD auto-deploy pipeline; GitHub `origin/main` push is verified, while external cloud/staging deployment and post-cutover live smoke were not executed in this task. |
| `INDEPENDENT_H1_VALIDATION` | **`NOT_MEASURED`** | The external 60-case independent `H-1` holdout corpus has not been authored or measured (`H1_AUTHORING_INDEPENDENCE = NOT_ESTABLISHED`). Offline regressions are reported strictly as offline. |

---

## 2. Identity, Commits & Rollback Baseline

- **Product commit (`product_commit_sha`)**: `52205f45fb66966de7d5b471d471c92d1ea2ac91` (`52205f45`)
- **Frozen candidate commit**: `f5f2c14723e95a525ac38c97a960735312e7e3d0` (`f5f2c147`)
- **Candidate `measured_system` hash**: `765487a4b48e7d522ae2cccab6516bf01d50422d9f92cc48eabe7e944e021164` (`102` measured files, down from `119`; prior candidate `017bfb9f` preserved byte-for-byte in `frozen-evaluation-candidate-017bfb9f.json`)
- **Runtime versions**: `geometry-functions/33` · `geometry-fact-planner/26` · `geometry-function-engine/24` · `typed-fact-next/2` · `hybrid-simulation-adapter/4` · `CACHE_VERSION = 132` (`ROUTE_D_CACHE_POLICY = 132:route-d`)
- **Pre-cutover rollback version**: Git tag `pre-hybrid-cutover-f986e897` → `f986e897bd266d06d4a9c5fa78c05463b7b247bf` (verified backend API tests `14/14` PASS + frontend `tsc -b && vite build` PASS prior to merge)
- **Merge commit (`main`, `--no-ff`)**: `PENDING_MAIN_MERGE`
- **Remote push status (`origin/main`)**: `PENDING_REMOTE_PUSH`
- **Worktree & branch cleanup status**: `PENDING_POST_PUSH_CLEANUP`

---

## 3. Official Default API Route & New Configuration

### Default `POST /api/analyze` Pipeline
`Vietnamese Geometry Problem` → `Gemini` → `TypedFactNext /2` (`extract_typed_fact_next_v2`) → `Bridge /2` (`bridge_v2`) → `Source Gate` (`registry.kiem_nguon`) → `FactGraph & Planner /26` (`lap_ke_hoach`) → `Registry /33` (`dung_tu_loi_goi`) → `Compiler / IR` (`ir_exact_kernel_execute`) → `Exact Geometry Kernel` → `Adapter /4` (`build_adapter4_response`) → `Scene3D + Construction Steps + Explanation + Exact Results`.

- Verified by real HTTP call-graph spy in `backend/tests/geometry/test_hybrid_cutover_verification.py`: every stage above is invoked in sequence on `POST /api/analyze`, and no `LLM_ONLY` module exists or is imported.
- **Zero fallback**: missing API key, provider HTTP/timeout failure, schema mismatch, missing premise, contradiction, or out-of-scope input returns a sanitized HTTP `502`/`503`/`504` (`INFRASTRUCTURE_FAILURE`, `Cache-Control: no-store`) or typed refusal/clarification envelope — never falling back to program synthesis.

### Simplified Configuration
- `HYBRID_ROUTE_MODE`: defaults to `"live"` in normal product execution (no opt-in `ALLOW_LIVE_AI=1` required).
  - `"staging-replay"`: retained explicitly for deterministic offline development/test (`REPLAY_STAGING_SIMULATED`, `simulated: true`, isolated cache namespace, never presented as live Gemini).
  - `"off"` or any unrecognized value: fails closed with HTTP `503 INVALID_HYBRID_ROUTE_MODE` (`no-store`).
- `ALLOW_LIVE_AI=0`: optional emergency operator kill-switch returning HTTP `503 LIVE_AI_DISABLED` (`no-store`).
- `GEMINI_API_KEY`: required in `"live"` mode; absence returns HTTP `503 MISSING_PROVIDER_API_KEY` (`no-store`).
- `CACHE_VERSION = "132"` (`ROUTE_D_CACHE_POLICY = "132:route-d"`): bumped from `131`; two-way cache isolation verified (`v131` rows never hit `v132` and vice versa; `staging-replay` rows never contaminate `live`).
- Retired obsolete flags: `GEOMETRY_COMPILER_MODE`, `HYBRID_V2_LOCAL`.

---

## 4. Retired Legacy Modules vs. Preserved Shared Components

### Deleted `LEGACY_ONLY` Files (`163` total: `18` product + `54` scripts + `91` tests)
- **Orchestrator & Adapter `/3` (`2` product files)**:
  - `backend/app/ai/pipeline.py` (`run_pipeline`, `stage_semantic_analyze`, `stage_semantic_program`, LLM repair loop)
  - `backend/app/ai/adapter3_simulation.py` (`Adapter /3`; `/4` covers all supported polyhedral, curved, sphere, described-point, and constrained-plane capabilities)
- **Compiler C (`6` product files)**:
  - `backend/app/simulation/geometry_compiler/__init__.py`, `compiler.py`, `contract_adapter.py`, `fact_graph.py`, `primitives.py`, `routing.py`
- **Legacy Synthesis/Analyze Skill Prompts (`10` product files)**:
  - `backend/app/ai/skills/{adapt,analyze,classify,edit,explain,geometry_analyze,geometry_program_generator,semantic_analyze,semantic_program,simulate}.md`
- **Pure-Legacy Tooling & Tests (`145` files)**:
  - `54` `LLM_ONLY` / Compiler C / Adapter `/3` evaluation scripts in `backend/scripts/` and `91` legacy-only test modules in `backend/tests/`.

### Preserved `HYBRID_REQUIRED`, `SHARED_COMPONENT` & `COMPATIBILITY_REQUIRED` Modules
- **Hybrid `/4` Core (`HYBRID_REQUIRED`)**: `route_policy.py`, `hybrid_offline.py`, `hybrid_preview.py` (`/api/preview/hybrid`), `typed_fact_next_extraction.py`, `adapter4_route.py`, `function_route.py`, `function_calling.py`, `simulation/geometry_functions/{typed_fact_next,typed_fact_next_bridge,registry,planner,engine,certificates,construction_continuity}.py`.
- **Exact Geometry Kernel & IR (`SHARED_COMPONENT`)**: `simulation/geometry/{exact,kernel,metric,primitives,radical,curved,sphere,polyhedron_checks}.py`, `simulation/semantic_program/{contract,request_contract,interpreter,validator,ir_static_check,hoisting,pipeline_adapter,scene3d,formation,section_provenance,visual_obligations,quantity_annotations,grounding_gate,coverage_gate,postconditions,obligations,geometry_exec,geometry_obligations,domain_profile,refusal_cause,scale_normalization,segment_relation}.py`.
- **Compatibility IR Route (`COMPATIBILITY_REQUIRED`)**: `simulation/semantic_program/route.py` (`verify_and_compile` for deterministic IR/Scene3D verification and T3 Gate 4 demo replay).
- **Ingestion, Transport, Auth, Classroom & Persistence (`SHARED_COMPONENT`)**: `ai/gemini.py`, `ai/skills/transcribe.md`, `ingestion/image_extraction.py` (`POST /api/image/extract`), `auth/*`, `classroom/*`, `persistence/*`, `runtime_identity.py`.
- **Frontend (`frontend/**`)**: `0` files modified during cutover; all Scene3D and construction continuity fields (`created_ids`, `reused_ids`, `highlighted_ids`, `retired_ids`, `step_summary`, `verification_refs`, `coordinate_frame_id`, `depends_on`, `preconditions`) preserved intact.

---

## 5. Post-Cutover Capabilities & Verification Results

### Supported Geometry & Simulation Capabilities
- **7 solid families**: pyramids, prisms, cuboids, cubes, spheres, cylinders, cones.
- **Plane sections & spheres**: Category A stated-cut sections (`DINH_CAT_CANH`), Category B engine-derived sections (`plane-section-certificate/1`), parallel/axial/sphere conic sections, circumscribed/inscribed spheres, sphere-plane tangency, composite multi-solid relations.
- **Planner & Symbolic Kernel**: unnamed described points (`@id`, orthocenter/circumcenter definition regression), constrained planes (`MAT_RANG_BUOC`), exact `Fraction` + normalized radical arithmetic, 4-layer `geometric-relation-certificate/1`, cumulative step-by-step Scene3D state (`7/7` continuity invariants), 5-part pedagogical `step_summary`, `route-d-clarification/1`, and fail-closed source grounding.

### Regression, API, Frontend & Authoritative Full T3 (`full-t3-f5f2c147.json`)
- **Offline geometry regressions (strictly offline, not independent live validation)**:
  - C26 70-case captured-wire replay: `40/41` (`97.56%`) positive served exact (`K-1` `10/10`, `S-2` `17/18`, `R-1` `13/13`), `29/29` negative refused, `0` wrong-served, `0` continuity violations.
  - Wave 3 gold replay: `72/72` positive served exact, `72/72` negative refused, `0` wrong-served.
  - Gold pilot suites: `K-1` `16/16`, `S-2` `35/36`, `R-1` `18/18`; preview fixtures `41/41` exact regeneration.
- **Direct `POST /api/analyze` API integration (`test_hybrid_cutover_verification.py`)**: `11/11` scenarios PASS (valid problem, missing data, contradictory data, out-of-scope domain, simulation goal, computation goal, multi-goal query, provider failure, missing API key, two-way cache hit/miss & `131`↔`132` isolation, `staging-replay`).
- **Clean Detached Full T3 (`hm-t3-f5f2c147` at `f5f2c14723e95a525ac38c97a960735312e7e3d0`)**: **`FULL_PRODUCT_GATE_PASS`** (`465.3 s`, `0` live provider calls, `pre_freeze_verify_exit = 0`, `post_freeze_verify_exit = 0`, clean tree before & after):
  1. Backend `pytest -q`: **`13,762 passed`**, `0 failed`, `0 errors` (`7 skipped`, `2 deselected`, `9 xfailed`).
  2. Frontend `vitest run`: **`85/85` files, `1,502/1,502` tests passed** (`0` `frontend/**` edits).
  3. TypeScript & Production Build (`tsc -b && vite build`): **PASS**.
  4. Thesis Demo Replay (`replay_demo_cases.py`): **`5/5` + `1/1` PASS**.
  5. Demo Crash Surface (`audit_demo_crash_surface.py`): **`6/6` PASS** (`0` HTTP 500s).
- **Publication safety (`check_publication_safety.py --range main..HEAD`)**: **`PASS`** (`violations = 0`, `pending_exception = 0`).
- **New live Gemini smoke status**: **`NEW_LIVE_SMOKE_NOT_MEASURED`** (`0` live Gemini calls issued; no live smoke spend authorized, C26/H-1 budgets untouched).

---

## 6. Deployment Rollback Procedure (Post-`LLM_ONLY` Retirement)

`HYBRID_ROUTE_MODE=off` is **not** a rollback to `LLM_ONLY` (it returns HTTP `503 INVALID_HYBRID_ROUTE_MODE` because `LLM_ONLY` execution code has been retired). Rollback after cutover is a **deployment version rollback**:

1. **Immediate emergency traffic stop (optional)**: set `ALLOW_LIVE_AI=0` on the backend service to halt outbound Gemini calls cleanly (`503 LIVE_AI_DISABLED`, `no-store`) while redeploying.
2. **Redeploy pre-cutover release**: build and deploy the backend/frontend image from tag `pre-hybrid-cutover-f986e897` (`f986e897bd266d06d4a9c5fa78c05463b7b247bf`).
3. **Forward Git revert (if rolling back `main` without history rewrite)**: run `git revert -m 1 <merge_commit_sha>` on a new commit and push non-force — **never** use `git reset --hard` or `git push --force` on `main`.
4. **Cache & database compatibility**: SQLite schema (`accounts`, `classroom`, `persistence`, `response_cache`) is backward-compatible; `v132` (`132:route-d`) cache keys are isolated from `v131`, so rolling back to `pre-hybrid-cutover-f986e897` neither corrupts nor serves post-cutover rows.

---

## 7. Remaining Limitations

1. **`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`**: Paired or standalone live generalization on an externally authored 60-case Vietnamese holdout (`H-1`) remains unmeasured.
2. **`NEW_LIVE_SMOKE_NOT_MEASURED` & `PRODUCTION_DEPLOYMENT_VERIFIED = NO`**: Post-cutover live Gemini staging smoke and cloud production deployment verification require Owner live operational run/deployment.
3. **Known open product boundaries (`docs/OPEN_ISSUES.md`)**: diacritic-free Vietnamese geometry input (`ISSUE-ARCH-ROUTE-D-DIACRITIC-FREE-INPUT`, gated on Owner policy `S-1`), partial stated-cut vertex naming (`ISSUE-ARCH-PARTIAL-STATED-CUT-NAMING`, fails closed `SECTION_BOUNDARY_INCOMPLETE`), history reopen `scene3d` persistence (`ISSUE-ARCH-HISTORY-REOPEN-DROPS-SCENE3D`, frontend scope), `GENUINE_DISCOVERY_NOT_ESTABLISHED` (planner compositions are source-explicit or registered decompositions), and `PEDAGOGICAL_HUMAN_VALIDATION = NOT_EVALUATED`.
