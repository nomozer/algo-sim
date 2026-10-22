# CONTRACT_V2_IMPLEMENTATION_REPORT.md — Canonical `typed-fact-next/2`, Bridge `/2`, and Adapter `/4`

- **Run**: `hybrid-contract-v2` (Backend Hybrid Session 3)
- **Authorization**: `GO_HYBRID_SESSION3_CONTRACT_V2_LOCAL_RESEARCH` (`D1 GO`, `D5 GO`)
- **Product Commit**: `541803c867adfbc5e85a8109bd0307552090f9df`

---

## 1. Root Contract Split Solved by `typed-fact-next/2`

In `typed-fact-next/1` (`DerivedPlaneSectionSpec`), the single field `cut_edges` carried two incompatible meanings across routes:
1. **Bridge (`typed-fact-next-bridge/1`)**: the lateral edges that the Vietnamese source text *explicitly states* are cut (`["SB", "SC"]`), paired with `named_intersections` (`{"S-B": "N", "S-C": "P"}`).
2. **Adapter `/3` (`hybrid-simulation-adapter/3`)**: the *complete cyclic section boundary* (`["SA", "SB", "SC"]`), including the edge containing the plane's through-point `M` even when the source text never stated `"cắt SA"`.

Session 2 proved each route's `/1` reading fail-closed (`SECTION_BOUNDARY_INCOMPLETE` on Adapter `/3`, `SOURCE_OBJECT_MISMATCH` on Bridge `/1`), eliminating any wrong-served divergence (`0` disagreements across `316` contract-parity cases), and proposed Option A (`typed-fact-next/2`) for Owner Decision `D1`.

---

## 2. Canonical Schema `typed-fact-next/2` (`backend/app/simulation/geometry_functions/typed_fact_next.py`)

### 2.1 `StatedIntersectionSpec` (`typed_fact_next.py:327–340`)
```python
class StatedIntersectionSpec(ClosedNextModel):
    edge: tuple[str, str]
    point: str | None = None
    quote: NonEmptyText
```
- `extra="forbid"` (closed Pydantic model).
- `edge` is validated as a 2-tuple of distinct point tokens (`_validate_distinct_tuple(..., 2, 2)`).
- `point` is either `None` (source states that the plane cuts `edge`, e.g. `"cắt SB, SC"`, without naming the intersection point) or a single valid point token (`"N"`).
- `quote` is the non-empty verbatim source substring stating the cut.

### 2.2 `DerivedPlaneSectionSpecV2` (`typed_fact_next.py:343–370`)
```python
class DerivedPlaneSectionSpecV2( _SectionPlaneBase):
    stated_intersections: tuple[StatedIntersectionSpec, ...] = ()
    declared_boundary: tuple[tuple[str, str], ...] | None = None
```
- `extra="forbid"` — legacy `/1` keys `cut_edges` and `named_intersections` are rejected at schema validation (`INVALID_TYPED_FACT_NEXT`).
- Rejects duplicate undirected edges in `stated_intersections` (`frozenset(s.edge)`) with `INVALID_DERIVED_SECTION`.
- Rejects duplicate non-null intersection point names in `stated_intersections` with `INVALID_DERIVED_SECTION` (pinning `NEG-per-edge-same-name`).
- `declared_boundary` is optional (`None` by default); when supplied, it must contain at least 3 distinct undirected edges (`min_length=3`), and is **verified** by the engine's exact closure certificate (`chung_chi_khep_kin` / `same_section_cycle`), never trusted.

### 2.3 Strict Version Dispatch (`parse_typed_fact_next` vs `parse_typed_fact_next_v2`)
- `_parse(model, raw)` (`typed_fact_next.py:719–747`) checks exact runtime class identity (`if type(raw) is model: return raw`, preventing subclass pass-through between `TypedFactNextPayloadV2` and `TypedFactNextPayload`) and requires `raw.get("schema_version") == model._VERSION`, raising `TypedFactNextValidationError("SCHEMA_VERSION_MISMATCH", ...)` on any mismatch.
- `/1` routes (`parse_typed_fact_next`, `bridge`, `run_typed_fact_next_planner_route`, `run_typed_fact_next_route`) never accept `/2`.
- `/2` routes (`parse_typed_fact_next_v2`, `bridge_v2`, `run_typed_fact_next_v2_planner_route`, `run_typed_fact_next_v2_route`) never accept `/1`.

### 2.4 Explicit Route-Labeled Converter (`convert_v1_to_v2`, `typed_fact_next.py:691–716`)
```python
def convert_v1_to_v2(raw: dict[str, Any], route: str | None) -> dict[str, Any]:
```
- Requires `route in ("bridge", "adapter3")`; any other value raises `TypedFactNextValidationError("ROUTE_LABEL_REQUIRED", ...)`.
- `route="bridge"`: converts `sec.cut_edges` (or `named_intersections` keys when `cut_edges` is empty) + `sec.named_intersections` into `stated_intersections`, with `declared_boundary` omitted.
- `route="adapter3"`: converts only `sec.named_intersections` into `stated_intersections` (never guessing or fabricating unstated cuts) and copies `sec.cut_edges` (when non-empty) into `declared_boundary` so the engine verifies cycle closure against the true 3D section polygon.

### 2.5 P1 Input-Boundary Hardening (`typed_fact_next.py:148–215`)
- Added `_ARGS_LOI` and `_kiem_args` on `PremiseFactSpec` so malformed premise argument shapes (`vertices`, `base`, `top`, `segment`, `line`, `line1`, `line2`, `plane`, `plane1`, `plane2`, `point`, `side`, `value`, `ratio`, `angle_deg`) fail closed at the schema boundary with `INVALID_PREMISE_ARGS` instead of raising uncaught `TypeError`/`KeyError`/`ValueError` inside downstream bridge/adapter code.
- Verified by 500-case deterministic fuzzing (`verification/fuzz/p1-adapter3.json`, `verification/fuzz/p1-planner.json`, `verification/fuzz/p3-v2.json`: `crashes = []`).

---

## 3. Bridge `/2` & Adapter `/4` Architecture

| Layer | `/1` Preserved Surface | `/2` Canonical Surface (Session 3) |
|---|---|---|
| Payload Schema | `typed-fact-next/1` (`TypedFactNextPayload`) | `typed-fact-next/2` (`TypedFactNextPayloadV2`) |
| Bridge | `typed-fact-next-bridge/1` (`bridge`) | `typed-fact-next-bridge/2` (`bridge_v2`) |
| Planner Route | `run_typed_fact_next_planner_route` | `run_typed_fact_next_v2_planner_route` |
| Simulation Adapter | `hybrid-simulation-adapter/3` (`run_typed_fact_next_route`) | `hybrid-simulation-adapter/4` (`run_typed_fact_next_v2_route`) |
| Route-D Schema | `hybrid-route-d-simulation/3` | `hybrid-route-d-simulation/4` |
| Registry / Planner / Engine | `/12`, `/12`, `/10` (Session 2) | `geometry-functions/13`, `geometry-fact-planner/13`, `geometry-function-engine/11` |
| Source Gate Authority | `/1` Bridge: `registry.kiem_nguon`; `/1` Adapter `/3`: `registry.kiem_nguon` with `legacy_substring_fallback` | `/2` Bridge & Adapter `/4`: **100% `registry.kiem_nguon`** (0 fallback) |

### 3.1 Adapter `/4` Delegation (`backend/app/ai/adapter4_route.py`)
`run_typed_fact_next_v2_route(raw)` is a thin, single-authority adapter (`79` lines) that delegates all planning, source verification, geometric construction, exact calculation, and Scene3D synthesis to `bridge_v2` + `FR.chay_sau_cau_noi`:
1. Validates `raw` via `bridge_v2(raw)` (`parse_typed_fact_next_v2`).
2. Executes `FR.chay_sau_cau_noi(b)` (`run_fact_route` $\to$ `lap_ke_hoach` $\to$ `kiem_nguon` $\to$ `dung_tu_loi_goi` $\to$ `_an_dinh_thiet_dien_phu`).
3. Emits `route_d` with `schema_version = "hybrid-route-d-simulation/4"`, `adapter_version = "hybrid-simulation-adapter/4"`, `bridge_version = "typed-fact-next-bridge/2"`, and `source_verification = {"authority": "registry.kiem_nguon"}`.

---

## 4. Dual-Run Verification Summary (`/1` vs `/2`)

- **Session 1 60-case benchmark (`family_b_session1_dual_run`)**:
  - `49/49` cases served by `/1` Bridge are `SERVED` by `/2` Adapter `/4` (`convert_v1_to_v2(..., route="bridge")`) with `49/49` (`100%`) exact answer agreement.
  - `S-open-cycle` (`"cắt SB."` + `"Dựng khối chóp đỉnh S cắt bởi (α)."`) is newly `SERVED` (`50` total served on `/2`) with exact oracle answer via `D6` (`derived_fresh`).
  - `6/6` invalid cases refused (`0` wrong-served), `50/50` valid scenes, `0` label leaks, `50/50` `authority == "registry.kiem_nguon"`.
- **316-case contract parity grid (`family_c_contract_parity`)**:
  - `/1` Bridge (`36/316`) and `/2` Adapter `/4` from `bridge` conversion (`36/316`) match `100%`.
  - `/1` Adapter `/3` (`20/316`) and `/2` Adapter `/4` from `adapter3` conversion (`20/316`) match `100%`.
  - `0` disagreements and `0` wrong-served across all 316 cases.
- **20-case negative control family (`family_e_negative_controls`)**:
  - `/1` Adapter `/3` had 1 known false serve (`N-anonymous-ratio-operand-triangle/convention`) via legacy substring fallback.
  - `/2` Adapter `/4` serves **`0/20`** (`100%` refused fail-closed).
