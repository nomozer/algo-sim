# BACKEND_MIGRATION_READINESS.md — 20 Compiler-First Gates (`GATE-01..20`) & 13 Route-D Hybrid Gates (`D-01..13`)

- **Run**: `hybrid-contract-v2` (Backend Hybrid Session 3)
- **Authorization**: `GO_HYBRID_SESSION3_CONTRACT_V2_LOCAL_RESEARCH`
- **Product Commit**: `69bd2fe48be1fd3afa6ce4112ccddda92a07d850`
- **Default Production Mode**: `DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `HYBRID_PRODUCT_ENABLEMENT = NO-GO`, `CACHE_VERSION = 127` (`NO_BUMP`)

---

## 1. Session 3 Acceptance Criteria (`S3-1`..`S3-7`)

| Gate | Requirement | Observed in Session 3 (`hybrid-contract-v2`) | Status |
|---|---|---|---|
| **S3-1** | Canonical `typed-fact-next/2`, `bridge_v2` `/2`, Adapter `/4`, route-D `/4`, converter `/1 → /2`, dual-run & `/1` compatibility (`D1`, `D5`) | Implemented & verified (`47 passed` in `test_hybrid_contract_v2.py`, `49/49` Session 1 `/1` vs `/2` answer agreement, `316/316` contract parity `0` disagreements) | **PASS** |
| **S3-2** | Unified Source Gate authority (`registry.kiem_nguon`) on canonical `/2` (`0` legacy substring fallback) (`D2`) | `100%` (`50/50` Session 1 `/2`, `22/22` locked grammar `/2`) carry `authority == "registry.kiem_nguon"`; `0` served without gate | **PASS** |
| **S3-3** | Closed grammar expansion (`G1`–`G7`) on pre-locked evaluation set (`D3`) | Locked `grammar-set.json` (`10c57be7...`, `47` cases): `22/22` (`100%`) positive served with exact oracle answers, `25/25` (`100%`) negatives refused (`46/47` category match) | **PASS** |
| **S3-4** | Bounded unstated lateral cut derivation (`D6`) with closure certificate | `intersect_line_plane` `PlanningContract` (`effect=Meet`, `fresh="I"`), cost-2 `derived_fresh` only when closed boundary required, `same_section_cycle` verified, `0` internal label leaks | **PASS** |
| **S3-5** | Keep IR memory budget at `32` (`D4 KEEP 32`) & deduplicate redundant constructs | `MAX_MEMORY_DECLARATIONS = 32` unchanged; `1.0` plane construction per section; all 3- and 4-sided pyramid/prism section plans use `18–30 <= 32` declarations | **PASS** |
| **S3-6** | Zero `wrong_served` & zero uncaught crashes across fuzz and evaluation suites | `0` `wrong_served` across all `47 + 60 + 316 + 33 + 20 + 16 + 60` evaluations; `0` crashes across `3 × 500` deterministic fuzz runs (`p1-adapter3.json`, `p1-planner.json`, `p3-v2.json`) | **PASS** |
| **S3-7** | Governance & default-route isolation (`LLM_ONLY`, `flat`, `CACHE_VERSION = 127`, `ALLOW_LIVE_AI = 0`) | Verified by `test_hybrid_backend_integration.py`, `test_evaluation_candidate.py`, and authoritative clean detached Full T3 (`FULL_PRODUCT_GATE_PASS`) | **PASS** |

---

## 2. Route-D Hybrid Readiness Checklist (`docs/MIGRATION_CHECKLIST.md §2`, `D-01`..`D-13`)

| Gate | Name | Status After Session 3 | Session 3 Impact & Remaining Blocker |
|---|---|---|---|
| **D-01** | Default route (`LLM_ONLY`) does not touch Route D | **PROVED** | Preserved (`main.py` and `pipeline.py` have 0 imports of `fact_extraction`, `function_route`, `adapter3_simulation`, or `adapter4_route`). |
| **D-02** | Route-aware cache identity | **PARTIAL** | `RoutePolicy` isolates preview/research routes; `/api/analyze` default `LLM_ONLY` cache (`CACHE_VERSION = 127`) untouched (`NO_BUMP`). |
| **D-03** | Per-request configuration snapshot | **PROVED** | Preserved (`test_response_contract_is_one_snapshot_per_call`). |
| **D-04** | Extraction contract (`flat` vs `v3` / `typed-fact-next/2`) | **RESEARCH_PROVED_OFFLINE (`typed-fact-next/2`) / PRODUCTION `flat`** | **Major Session 3 advancement**: `typed-fact-next/2` resolves the `/1.cut_edges` contract split between Bridge and Adapter `/3`. Live provider extraction into `typed-fact-next/2` on a newly sealed held-out set remains a future owner-gated wave. |
| **D-05** | Mathematical exactness & independent oracle | **PROVED (Offline Corpora)** | **Strengthened in Session 3**: `174` historical cases + `60` Session 1 cases (`50/50` served on `/2`) + `47` locked grammar cases (`22/22` positive served) + `316` parity cases + `33` metamorphic cases verified against independent exact `Fraction`/SymPy oracles with `0` `wrong_served`. |
| **D-06** | Fail-closed on degenerate / malformed / contradictory inputs | **PROVED** | **Strengthened in Session 3**: P1 schema-boundary validation (`INVALID_PREMISE_ARGS`), technical fault boundaries (`ADAPTER_INTERNAL_ERROR` / `ROUTE_INTERNAL_ERROR`), and exact section closure certificate (`SECTION_BOUNDARY_INCOMPLETE`, `DEGENERATE_CONFIGURATION`). |
| **D-07** | Adapter envelope & refusal taxonomy | **PROVED (Preview `/2` & Simulation `/4`)** | **Strengthened in Session 3**: `hybrid-simulation-adapter/4` (`hybrid-route-d-simulation/4`) unifies Bridge and Adapter onto a single planner+engine pipeline with `100%` `registry.kiem_nguon` authority and complete refusal taxonomy coverage (`test_hybrid_preview_contract.py`). |
| **D-08** | Flag-gated preview API (`POST /api/preview/hybrid`) | **PROVED (Preview)** | Preserved; production `/api/analyze` enablement remains `NO-GO`. |
| **D-09** | Runtime diagnostics & observability | **PROVED** | Preserved (`GET /api/diagnostics/runtime`). |
| **D-10** | Certificate-backed presentation in `Scene3D` | **OPEN (Frontend Branch Scope)** | Backend emits exact `perpendicular_witness`, `section_closure`, `volume_ratio`, and `residual_volume` certificates and strips internal `I, I1` labels (`_an_dinh_thiet_dien_phu`); frontend renderer consumption belongs to the frontend worktree. |
| **D-11** | Paired live evaluation against `LLM_ONLY` | **NOT_STARTED** | Requires Owner GO, preregistered budget/stop rules, and a newly sealed held-out benchmark (`ALLOW_LIVE_AI = 0` in Session 3). |
| **D-12** | Rollback mechanism | **PARTIAL** | Flag disablement is immediate; route-aware cache isolation is tested once Route D is cached. |
| **D-13** | Product enablement decision | **NO-GO (`HYBRID_PRODUCT_ENABLEMENT = NO-GO`)** | Remains `NO-GO` until `D-04`, `D-10`, `D-11`, `D-12` are completed and approved by Owner. |

---

## 3. 20 Canonical Compiler-First Gates (`docs/MIGRATION_CHECKLIST.md §1`, `GATE-01`..`GATE-20`)

Session 3 strictly obeys `AGENTS.md §3`: `DEFAULT_MODE` remains `LLM_ONLY`, and no gate status in `docs/MIGRATION_CHECKLIST.md` is inflated from offline research results:

| Gate | Title | Canonical Status | Session 3 Notes |
|---|---|---|---|
| **GATE-01** | Structured Analyze | `PROVED_ON_PILOT` | Unchanged (`LLM_ONLY` default untouched). |
| **GATE-02** | Contract Validation | `PROVED_ON_PILOT` | Unchanged on Route C (`RequestContract`); Route D canonical contract `/2` proved offline. |
| **GATE-03** | FactGraph Safety | `PROVED_ON_PILOT` | Unchanged on Route C; Route D fail-closed verified across `3 × 500` fuzz payloads + negative suites. |
| **GATE-04** | Primitive Coverage | `PARTIAL` | Unchanged on Route C; Route D covers pyramids, prisms, composite solids, plane sections, derived solids, volume ratios, and residual volumes. |
| **GATE-05** | Compiler Correctness | `PROVED_ON_PILOT` | Unchanged on Route C; Route D engine (`geometry-function-engine/11`) verified with `0` `wrong_served`. |
| **GATE-06** | Topology Verification | `PROVED_ON_PILOT` | Unchanged on Route C; Route D adds exact cyclic section closure certificate (`chung_chi_khep_kin`). |
| **GATE-07** | Final-Memory & Answer Correctness | `PROVED_ON_PILOT` | Unchanged on Route C; Route D exact answers verified across all offline families. |
| **GATE-08** | Visual Quality & Fidelity | `PROVED_ON_PILOT` | Unchanged (`0` internal label leaks on Route D `/2`). |
| **GATE-09** | Layout & Camera | `PARTIAL` | Unchanged. |
| **GATE-10** | Hidden Lines Detection | `NOT_STARTED` | Unchanged. |
| **GATE-11** | Compiler-First Routing | `NOT_STARTED` | Opt-in `DETERMINISTIC_FIRST` only; default `LLM_ONLY` untouched. |
| **GATE-12** | Fallback Mechanism | `NOT_STARTED` | Unchanged. |
| **GATE-13** | Canary Deployment | `NOT_STARTED` | Unchanged. |
| **GATE-14** | Rollback Mechanism | `NOT_STARTED` | Unchanged. |
| **GATE-15** | Holdout Benchmark | `NOT_STARTED` | Unchanged (Session 3 evaluation is explicitly classified `DEVELOPMENT_EVALUATION_NOT_BLIND`). |
| **GATE-16** | Token & Latency Measurement | `PARTIAL` | Offline Session 3 p50 latency is `33.0 ms`, max `49.5 ms`, `0` provider tokens. |
| **GATE-17** | Unsafe Acceptance Gate | `PROVED_ON_PILOT` | Strengthened offline on Route D (`100%` negative refusal across Family A and Family E). |
| **GATE-18** | Observability & Diagnostics | `PARTIAL` | Unchanged. |
| **GATE-19** | Cache & Version Policy | `PRODUCTION_READY` (`LLM_ONLY`) | `CACHE_VERSION = 127` (`NO_BUMP`) preserved and verified. |
| **GATE-20** | User & Pedagogical Evaluation | `NOT_STARTED` | Unchanged. |
