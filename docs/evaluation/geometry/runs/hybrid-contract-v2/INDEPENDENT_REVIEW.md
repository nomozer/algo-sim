# INDEPENDENT_REVIEW.md — Backend Hybrid Session 3 (`hybrid-contract-v2`)

- **Reviewer Subagent**: `61217726-a797-4a91-b722-e4393c7e11c9` (Read-Only Independent Mathematical & Architecture Quality Gate Reviewer)
- **Audited Worktree**: `D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-backend-s3`
- **Branch**: `research/hybrid-backend-session3-contract-v2`
- **Base Commit SHA**: `227d447f5c1ca55a2c4bd68f3c8c583228902cfc` (`227d447f`, Session 2 HEAD)
- **Initial Audited Commit SHA**: `94893d72049baddc3f6bdea433e7a31157f8e8f5` (`94893d72`)
- **Post-Remediation Final Product Commit SHA**: `541803c867adfbc5e85a8109bd0307552090f9df` (`541803c8`)
- **Measured Product Tree SHA-256 (`backend/app`, 116 files)**: `173af8b2604dde4754a602eb868ceb07f8129263f7b80aa9601a9a203aec51d9`

---

## 1. Scope Audited

The independent read-only review audited `git diff 227d447f5c1ca55a2c4bd68f3c8c583228902cfc..HEAD` across:
1. `backend/app/simulation/geometry_functions/typed_fact_next.py` (`typed-fact-next/2`, `StatedIntersectionSpec`, `DerivedPlaneSectionSpecV2`, `TypedFactNextPayloadV2`, `parse_typed_fact_next_v2`, `convert_v1_to_v2`, P1 `_ARGS_LOI` input-boundary hardening)
2. `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py` (`BRIDGE_V2_VERSION = "typed-fact-next-bridge/2"`, `bridge_v2`)
3. `backend/app/simulation/geometry_functions/planner.py` (`PLANNER_VERSION = "geometry-fact-planner/13"`, `_dinh_cat_canh` cost-0/1/2 D6 derivation)
4. `backend/app/simulation/geometry_functions/registry.py` (`REGISTRY_VERSION = "geometry-functions/13"`, `intersect_line_plane` `PlanningContract`, closed Source Gate grammar G1–G7)
5. `backend/app/simulation/geometry_functions/engine.py` (`ENGINE_VERSION = "geometry-function-engine/11"`, `chung_chi_khep_kin` / `same_section_cycle`, `_bien_dich_mat_cat` section-before-area plane ownership)
6. `backend/app/ai/adapter4_route.py` (`ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"`, `ROUTE_D_SIMULATION_V4_SCHEMA_VERSION = "hybrid-route-d-simulation/4"`, `run_typed_fact_next_v2_route`)
7. `backend/app/ai/function_route.py` (`run_typed_fact_next_v2_planner_route`, `chay_sau_cau_noi`, `_an_dinh_thiet_dien_phu`)
8. `backend/app/ai/adapter3_simulation.py` (delegating closure verification to `dung.chung_chi_khep_kin`, technical refusal boundary)
9. `backend/app/ai/hybrid_preview.py` (refusal taxonomy classifications for `INVALID_PREMISE_ARGS`, `SCHEMA_VERSION_MISMATCH`, `ROUTE_LABEL_REQUIRED`)
10. `backend/tests/geometry/test_hybrid_contract_v2.py`
11. `docs/evaluation/geometry/runs/hybrid-contract-v2/` (`grammar-set.json`, `grammar-set.lock.json`, `verification/fuzz/`, `verification/grammar/`, `verification/evaluation/`)

---

## 2. Verification by Owner Decision (`D1`–`D6`)

### 2.1 `D1` — Canonical `typed-fact-next/2`, Bridge `/2`, Adapter `/4`, Converter & Backward Compatibility
- `StatedIntersectionSpec` (`typed_fact_next.py:327–340`) and `DerivedPlaneSectionSpecV2` (`typed_fact_next.py:343–370`) cleanly separate:
  - `stated_intersections`: edges the source text explicitly states are cut (`point: str | None`, `quote: str`), rejecting duplicate undirected edges and duplicate non-null point labels with `INVALID_DERIVED_SECTION`.
  - `declared_boundary`: optional candidate cycle (`min_length=3`), verified by the engine and never trusted.
- `_parse(model, raw)` (`typed_fact_next.py:719–732`) uses exact type identity (`type(raw) is model`) and enforces `raw.get("schema_version") == model._VERSION` (`SCHEMA_VERSION_MISMATCH`), preventing any cross-version acceptance between `/1` and `/2`.
- `convert_v1_to_v2(raw, route=...)` (`typed_fact_next.py:691–716`) requires an explicit `route in ("bridge", "adapter3")` (`ROUTE_LABEL_REQUIRED`). Under `route="bridge"`, `/1.cut_edges` maps to `stated_intersections`; under `route="adapter3"`, `/1.cut_edges` maps to `declared_boundary` and only `named_intersections` become `stated_intersections` (never fabricating unstated intersections).

### 2.2 `D2` — Unified Source Authority (`registry.kiem_nguon`) on Canonical `/2`
- `run_typed_fact_next_v2_route` (`adapter4_route.py:27–78`) delegates exclusively to `bridge_v2` $\to$ `FR.chay_sau_cau_noi` $\to$ `run_fact_route` $\to$ `lap_ke_hoach` $\to$ `run_function_route` $\to$ `dung_tu_loi_goi`, which unconditionally executes `registry.kiem_nguon`.
- Zero legacy substring fallback (`_verify_quote_in_problem` / `LEGACY_SOURCE_AUTHORITY`) exists on `/2` or `/4`.
- Every `SERVED` `/4` envelope carries `"source_verification": {"authority": "registry.kiem_nguon"}`.

### 2.3 `D3` — Closed Source Gate Grammar Expansion (`G1`–`G7`) & Locked Set Integrity
- `grammar-set.json` was locked at commit `4268f4e214125fe20c858930bc92b0c5798dfc67` before any grammar code change (`SHA-256 = 10c57be7b485d7b3f1a97183ff41b28988e70641e297e01cccf68d1434cc4abe`, verified byte-identical).
- G1–G7 (`registry.py`, `planner.py`) admit only closed, structurally verified Vietnamese forms:
  - **G1**: Per-edge cut list (`"cắt SB tại N, (và) (cắt) SC tại P"`).
  - **G2**: Restated plane subject (`"; (α) cắt ..."` / `", (α) cắt ..."` when `(α)` matches the preceding plane-definition clause).
  - **G3**: Through-point synonym (`"chứa (điểm) M"` for a single 1-letter point token; rejects 2-letter line tokens such as `"chứa SA"`).
  - **G4**: Point-first plane definition (`"Qua M dựng mặt phẳng (α) song song với ... / vuông góc với ..."`).
  - **G5**: Described derived pyramid (`"khối chóp đỉnh S cắt bởi (α)"`) bound via `ContextVar` `_KHOI_MO_TA` only when a validated derived pyramid stands on `(α)` with apex `S`.
  - **G6**: Multi-item construction lead-in (`"Dựng từng bước hình chóp, thiết diện bởi (α), khối chóp đỉnh S cắt bởi (α), làm nổi bật thiết diện"`), with partial-overlap masking `max(a, x) < min(b, y)` in `_kiem_du_kien_cau_hoi`.
  - **G7**: Redundant stated through-point cut (`"cắt SA, SB, SC lần lượt tại M, N, P"` where `M` is already the through-point on `SA`), reusing `M` at cost 0 (`reuse_through_point`) while recording `stated_point: "M"` for full cut-clause binding.
- Zero hardcoded case IDs, vertex labels, or expected answers.
- On the locked 47-case `/2` evaluation set (`after-p4b-grammar.json`): `22/22` positive cases `SERVED` with exact oracle answers (`wrong_served: []`, `served_without_gate: []`), `4/4` `REFUSE_GEOMETRY`, `2/2` `REFUSE_KERNEL`, `18/19` `REFUSE_SOURCE` (`NEG-per-edge-same-name` refused earlier at the `/2` schema boundary `DerivedPlaneSectionSpecV2` with `INVALID_DERIVED_SECTION` -> `REFUSE_OTHER`), total `46/47` match (`100%` serve/refuse binary accuracy).

### 2.4 `D4` — Keep IR Memory Budget at 32 (`MAX_MEMORY_DECLARATIONS = 32`)
- `MAX_MEMORY_DECLARATIONS = 32` in `validator.py:143` is untouched.
- Engine-level deduplication (`gop_doi_tuong_trung`, `engine.py:188–218`) eliminates redundant operand line/plane declarations while preserving `mp_td_<section_id>` (`surface_role="CUTTING_PLANE"`) distinct from `derived_<first_cut>_plane` (`non_visual` operand plane) for birth-order validity and visual ownership.
- In `engine.py:1444`, `_bien_dich_mat_cat` iterates `(*self.of("section"), *self.of("ask_section_area"))` (matching `kiem_mat_cat` at line 1266) so `section` always owns `mp_td_<section_id>`.

### 2.5 `D5` — Version Governance & Frozen Surfaces
- All 6 Session 3 version bumps (`geometry-functions/13`, `geometry-fact-planner/13`, `geometry-function-engine/11`, `typed-fact-next-bridge/2`, `hybrid-simulation-adapter/4`, `hybrid-route-d-simulation/4`) and all `/1` backward-compatible constants and frozen surface SHA-256 fingerprints (`485d3834...`, `4bff35bb...`, `7ea511a6...`, `aa9d93ee...`, `5ceb0f99...`, `CACHE_VERSION = 127`, `DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`) are verified.

### 2.6 `D6` — Bounded Unstated Lateral Cut Derivation (`DERIVED_FRESH`)
- `REGISTRY["intersect_line_plane"]` declares `PlanningContract(..., effect=PlanningTerm("Meet", ("X", "L", "Q")), source_policy="section_vertex", fresh="I")`.
- `_dinh_cat_canh` (`planner.py:1192–1291`) derives `derived_fresh` (cost 2) only when a closed boundary is required (`khep` — a derived solid stands on the section — or `e in bien` — a `declared_boundary` is supplied).
- `engine.kiem_dinh_cat` (`engine.py:1299–1361`) verifies `0 < t <= 1` on every lateral edge and proves closure via `chung_chi_khep_kin` (`same_section_cycle` against exact 3D `cross_section`).
- `_an_dinh_thiet_dien_phu` (`function_route.py:98–174`) strips all internal `I, I1, ...` labels from learner-facing `Scene3D`.

---

## 3. Findings & Remediation

### `BLOCKER` Findings
- **None.**

### `IMPORTANT` Findings (Remediated)
1. **[I-1] Plane-only `construct_plane_section` / `measurement(area)` on `/2` without `construct_derived_solid` or `declared_boundary` emitted vacuous `DINH_CAT_CANH` (`planner.py:1220`) — FIXED in `541803c867adfbc5e85a8109bd0307552090f9df`**:
   - **Cause**: On `/2`, `_section_fact_v2` sets `cut_edges = []` and `derive_cuts = True` when `stated_intersections` is empty. When a payload requested only `construct_plane_section` and/or `measurement(area)` without `construct_derived_solid` (`khep = False`) and without `declared_boundary` (`f.boundary_edges is None`), `_dinh_cat_canh` emitted a `DINH_CAT_CANH` certificate with `stated_edges: []` and `phai_khep = False`, which `registry._kiem_dinh_cat` refused with `AUXILIARY_RULE_MISMATCH`.
   - **Fix**: Added `if not stated and not khep and f.boundary_edges is None: return` in `planner._dinh_cat_canh` (`planner.py:1223–1224`) and pinned with `test_v2_plane_only_section_area_without_derived_solid_is_served` in `backend/tests/geometry/test_hybrid_contract_v2.py` (`47 passed`).
2. **[I-2] `EVALUATION_CANDIDATE.json` refreeze required for 116-file product tree — RESOLVED in P8 freeze step**:
   - **Cause**: Adding `backend/app/ai/adapter4_route.py` increased the measured `backend/app` file count from `115` to `116` (`173af8b2604dde4754a602eb868ceb07f8129263f7b80aa9601a9a203aec51d9`).
   - **Fix**: Registered `candidate_divergence.json` in `docs/evaluation/geometry/runs/hybrid-contract-v2/` and refroze `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` via `freeze_evaluation_candidate.py --write` for the clean detached Full T3 gate.

### `MINOR` Observations
- **[M-1]** Code symbol names `StatedIntersectionSpec` (`typed_fact_next.py:327`), `BRIDGE_VERSION` / `BRIDGE_V2_VERSION` (`typed_fact_next_bridge.py:24,26`), and `ADAPTER_V4_VERSION` (`adapter4_route.py:17`) are used consistently across all modules and tests; documented in `CONTRACT_V2_IMPLEMENTATION_REPORT.md`.

---

## 4. Final Verdict

- **Verdict**: **`INDEPENDENT_REVIEW_PASS`** (post-remediation at product commit `541803c867adfbc5e85a8109bd0307552090f9df`).
