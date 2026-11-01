# Continuation 13 Independent Adversarial Review — `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT`

- **Reviewer:** Independent `research` subagent (`fcc3f7ac-31ea-4cc3-9321-b586dc9f4605`)
- **Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-master-backend-replacement` (`research/hybrid-master-backend-replacement`)
- **Reviewed Product Slice:** `e4240c99bf9edcda672fcce641b7dd299680d659` + takeover hardening → final product commit `9503482a7480c2e8501efa8bcef0ce2c37776287` (`measured_system_hash = 773e440de0385d577040a9eca107706bfb2d3e4aec1d827b52c99c89d42ac7c3`, `118` files; `REGISTRY_VERSION = "geometry-functions/29"`, `PLANNER_VERSION = "geometry-fact-planner/23"`, `ENGINE_VERSION = "geometry-function-engine/20"`).
- **Live AI Policy:** `ALLOW_LIVE_AI = 0`, `0` provider calls, `USD 0` spend.
- **Final Verdict:** **`VERDICT: READY`** (`0 BLOCKER`, `0 MAJOR`, `0 MINOR`, `1 NIT` in Round 2).

---

## 1. Pre-Review Takeover Hardening (Before Round 1)

Before dispatching the independent reviewer, takeover audit of `e4240c99` identified and closed 6 concrete gaps via `RED → GREEN` TDD:

1. **Cross-solid scope laundering via shared `DescribedPointSpec` (`typed_fact_next.py::_described_consumer_scopes`, `scope_records`):** previously, if an unnamed `@o1` was referenced by two consumers on different scopes (e.g., an unscoped/`s1` goal and an `s2`-scoped goal), `scope_records` collapsed `len(scopes) > 1` to `None`, bypassing `S5`/`S7`/`S8` (`SOURCE_OBJECT_MISMATCH`). Fixed to emit a scoped ownership record per distinct non-`None` consumer solid scope (and propagate nested `@id` dependencies upward).
2. **Canonical-alias duplicate operands inside `DescribedPointSpec` (`typed_fact_next.py::_validate_goal_identities`):** `line1=["A", "s1::A"]` previously passed lexical `set()` distinctness; fixed to compare `canonical_vertex_ref` and refuse `INVALID_DESCRIBED_POINT`.
3. **Line–line `angle(line1, line2)` with unnamed described point on `/4` (`typed_fact_next_bridge.py::_cau_hoi_mo_ta`):** wired to existing `ask_angle_lines` `PlanningContract` (`cos² = 1/3` verified end-to-end on `/4`).
4. **Polygon arity ≥ 4 with `@id` (`_cau_hoi_mo_ta`) & curved section `through_point="@m1"` (`_phan_cong`):** guarded to refuse `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` (`CAPABILITY`) instead of `FACT_INCOMPLETE` / `INVALID_QUALIFIED_REF`.
5. **Full `SL-3` `đt` parity (`registry.py`):** extended `_KHOANG_CACH_DIEM_DUONG`, `_DICH_KHOANG_CACH`, and `orthogonal_projection_line` / `intersect_line_line` / `intersect_line_plane` / `ask_angle_*` phrases so `đt` works across point-to-line distance and described-point chains.
6. **Preview fixture `IDENTITY_DELTAS` (`export_hybrid_preview_fixtures.py`) & `S-2` `@id` projection (`run_s2_student_language_pilot.py`):** declared `("geometry-functions/28", "geometry-functions/29")` (`41/41` fixtures verified, `0` non-identity diffs) and normalized `@id` references in `project()`.

---

## 2. Round 1 Findings & Resolution (`NOT_READY`: `0 BLOCKER`, `1 MAJOR`, `3 MINOR`, `1 NIT`)

| ID | Severity | Location | Finding | Resolution (`9503482a`) |
|---|---|---|---|---|
| `MAJOR-1` | `MAJOR` | `typed_fact_next_bridge.py:340-341` | `_cau_hoi_mo_ta` mapped `distance` with `keys == {"line", "plane"}` and `@id` on `line` to a `TypedFact` with `points_a`, which has no `PlanningContract` (`ask_distance_line_plane.planning is None`), leaking to `planner.doc_du_kien` as `SCHEMA_INVALID` (`EXTRACTION_FAILED`) instead of `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` (`CAPABILITY`). | Narrowed line `340` to `g.goal_type == "angle"`; `distance(line, plane)` with `@id` now falls through to `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` (`test_r1_distance_line_plane_with_described_point_refuses_capability_not_schema_invalid`). |
| `MINOR-1` | `MINOR` | `registry.py:718, 723, 727, 729` | `re:(?<![\w/])k/c(?![\w/])` omitted `(?i)`, causing sentence-initial `"K/c …"` / uppercase `"K/C …"` on named distance asks to refuse `PREDICATE_NOT_IN_QUOTE`. | Added `(?i)` to all four `ask_distance_*` `re:` keywords (`test_sl3_kc_and_dt_shorthand_work_on_point_to_line_and_described_point_goals`). |
| `MINOR-2` | `MINOR` | `typed_fact_next_bridge.py:570, 858` | Whole-solid curved `measurement` branches in `_phan_cong` and `_bridge` did not require `set(g.target) <= {"solid", "solid_id"}`, dropping `target={"polygon": ["@m1", "O", "A"]}` into whole-solid `area` (`CURVED_WORDING_UNSUPPORTED` / `SOURCE_OBJECT_MISMATCH` instead of `CAPABILITY`). | Guarded both branches with `set(g.target) <= {"solid", "solid_id"}`, routing `@id` targets to `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` and non-`@id` extra targets to `BRIDGE_UNSUPPORTED_CURVED` (`test_r1_curved_polygon_area_goal_with_described_point_refuses_capability`). |
| `MINOR-3` | `MINOR` | `run_s2_student_language_pilot.py:106, 120` | `_canon` retained explicit `None` optional fields (emitted by Gemini under OpenAPI `nullable: True`) and did not `.strip()` `@id` string lookups. | `_canon` drops `v is None` dictionary entries and strips strings before `names.get(...)` (`test_r1_project_ignores_openapi_nullable_none_fields_and_outer_whitespace_on_described_refs`). |
| `NIT-1` | `NIT` | `typed_fact_next.py:986-988` | Legacy `typed-fact-next/1` (`PayloadV1`) with `@id` in `derived_sections[i].through_point` raises `INVALID_MATH_GOAL` (`EXTRACTION_FAILED`). | Kept by design (fail-closed; documented in `r1-described-points-audit.md`). |

---

## 3. Round 2 Verification (`VERDICT: READY`: `0 BLOCKER`, `0 MAJOR`, `0 MINOR`, `1 NIT`)

- Full `(goal_type × target_shape × @id position)` matrix verified through `bridge_v2` → `planner.doc_du_kien` and `run_hybrid_offline`: `0` `SCHEMA_INVALID` leaks; all supported shapes serve exact values; all unsupported `@id` shapes refuse `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` (`CAPABILITY`).
- Sentence-initial `"K/c"` and uppercase `"K/C"` verified across all 5 distance families (`ask_distance_point_plane`, `ask_distance_lines`, `ask_distance_line_plane`, `ask_distance_planes`, `distance(point, line)`).
- Raw byte + Python `ast.parse` string-literal scan across all modified files: **`0` unexpected ASCII control characters**.
- Targeted Continuation 13 & contract suites: **`265 passed`**.
- Preview fixtures (`fixtures-adapter-2-search-telemetry`): **`41/41 verified` (`problems: []`)**.
- Full geometry & hybrid sweep: **`14,019 passed`**, `0` functional/mathematical/grounding failures.
- Product locks verified intact: `DEFAULT_MODE == "LLM_ONLY"`, `CACHE_VERSION == "131"`, `0` new `GeometryFunction` primitives, `0` hardcoded case IDs / labels / answers, locked `flat` / `v3` / `function_calling` / `TypedFact` / `function_declarations` SHA-256 pins unchanged.
