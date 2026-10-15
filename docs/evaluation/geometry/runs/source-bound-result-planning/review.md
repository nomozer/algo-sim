# Independent Code & Evidence Review — `source-bound-result-planning` (2026-10-15)

- **Reviewer:** Fresh-context read-only `research` subagent (`conversationId = efce624a-8e4b-497d-959f-1b2c9c421f9b`)
- **Initial Audited Product Commit:** `b8112f357763c1f29601c666552bb82f5a97f1c1`
- **Final Re-Verified Product Commit:** `10dd6d6ebee34cdf8258b0e559c031e82931502a`
- **Final Verdict:** `PASS` (0 open `CRITICAL`, 0 open `IMPORTANT`, 0 open `NONBLOCKING`)

---

## 1. Eleven-Dimension Review Matrix

| # | Dimension | Initial Verdict | Final Verdict | Key Evidence / Code Locations |
|---:|---|---|---|---|
| 1 | Typed reference validity (`TypedFact.line_ref`, `ProjectionLineArgs.line_ref`, mutually exclusive with endpoints) | `PASS` | `PASS` | `planner.py:130`, `planner.py:293-339`, `registry.py:182-194` |
| 2 | Source-premise authority and quote coverage (`_kiem_result_binding`, `_kiem_nguon_dong`, atomic span checks, 3-label plane requirement) | `FAIL` (`[CRITICAL-1]`) | `PASS` | `registry.py:667-706`, `registry.py:725-737`, `registry.py:818-902` |
| 3 | Unknown/wrong/proof/conditional/negated producer safety (`UNKNOWN_DERIVED_REFERENCE`, `DERIVED_REFERENCE_TYPE_MISMATCH`, `GOAL_CLAUSE_NOT_PREMISE`, `CONDITIONAL_CLAUSE`, `NEGATED_CLAUSE`) | `PASS` | `PASS` | `planner.py:299-339`, `registry.py:854-861` |
| 4 | Finite-segment versus infinite-line semantics (`đoạn giao tuyến` refused as `SOURCE_OBJECT_MISMATCH`) | `PASS` | `PASS` | `registry.py:680` (`_CA_DOAN_GIAO_TUYEN`), `registry.py:862-867` |
| 5 | Correct line intersection uniqueness (parallel/coincident planes refused, collinear 3-point planes refused) | `PASS` (`[NONBLOCKING-1]`) | `PASS` | `engine.py:225-248`, `kernel.py:293-305`, `test_result_binding_planning.py:470-478` |
| 6 | Exact projection and Gram distance (zero-distance handling, no degenerate perpendicular witness when $d^2=0$, exact Kernel projection on the same resolved `Line3`) | `PASS` | `PASS` | `engine.py:706-733`, `function_route.py:322-335`, `test_result_binding_planning.py:95-134` |
| 7 | Alias coalescing and result reuse (equivalent `intersection_line` producers coalesced, supplied projection foot reused with 0 new constructions, repeated goals share memoized line/foot) | `FAIL` (`[IMPORTANT-1]`) | `PASS` | `planner.py:604-641`, `planner.py:703-755`, `registry.py:858-878` |
| 8 | Dependency cycles and budgets (`MAX_EFFECT_DEPTH=3`, `MAX_EFFECT_NEEDS=32`, `MAX_EFFECT_CANDIDATES=8`, `MAX_RESULT_LINES=4`, `MAX_RESULT_FEET=8`, `MAX_CALLS=64`, active-need cycle detection, point-line dependency cycles) | `PASS` | `PASS` | `planner.py:42-47`, `planner.py:570-665`, `planner.py:768-785` |
| 9 | Provider compatibility (`FC.surface_fingerprint()`, `FE.surface_fingerprint()`, `RG.function_declarations()` excluding `PlanningContract`, old fixtures compatible) | `PASS` | `PASS` | `registry.py:648-658`, `provider-surfaces.json`, `test_hybrid_goal_decomposition.py:322` |
| 10 | `LLM_ONLY` route isolation (`DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 125`, Route A refuses `line_ref` with `RESULT_BINDING_UNVERIFIED`) | `PASS` | `PASS` | `pipeline.py:36`, `main.py:28`, `registry.py:821-828` |
| 11 | Evidence integrity and benchmark coverage (`docs/evaluation/geometry/runs/source-bound-result-planning/` vs `next-slice-corpus.json` and `provider-surfaces.json`) | `FAIL` (`[IMPORTANT-2]`) | `PASS` | `reconciliation.json`, `report.md`, `provider-surfaces.json`, `visual/corpus-results.json` |

---

## 2. Findings & RED → GREEN Resolution

### `[CRITICAL-1]` Enclosing-Sentence Verification Bypass via Truncated Quotes and Modifier Clauses in `_kiem_result_binding` & `_kiem_phu`
- **Finding:** `_kiem_result_binding` (`registry.py:833-895`) and `_kiem_phu` (`registry.py:733-736`) validated regex fullmatches or trailing value assignments against the extracted quote `q` rather than the full enclosing source sentence `de[slice(*_bien_cau(de, ...))]`, and used `_duoc_hoi` instead of `_hoi_dung_cum` on `line_ref` distance questions, allowing:
  1. Truncated `intersection_line` producer quotes hiding a prove prefix (`Chứng minh tồn tại giao tuyến...`) or conditional prefix (`Nếu tồn tại giao tuyến...`).
  2. Truncated `orthogonal_projection_line` quotes hiding a prove prefix (`Chứng minh H là hình chiếu...`).
  3. Truncated `line_ref` distance question quotes hiding a trailing given value (`... = 2.`).
  4. Modifier-wrapped `line_ref` distance questions (`Tính bình phương khoảng cách...` or `... khi đổi cạnh = 2.`).
  5. Truncated named-line distance question quotes hiding a trailing given value (`Tính khoảng cách từ S đến BD = 1.`).
- **RED → GREEN Fix:**
  - Added `test_enclosing_sentence_outside_truncated_quote_or_modifier_is_refused` (6 parametrized adversarial cases covering all 5 bypass vectors) in `backend/tests/geometry/test_result_binding_planning.py` — confirmed **RED** (`6 failed`).
  - Updated `backend/app/simulation/geometry_functions/registry.py` (`_CHAN_TAN_NGU`, `_GAN_GIA_TRI`, `_kiem_phu`, `_kiem_result_binding`) to locate `vt = de.find(q)` and validate against the full enclosing sentence `cau = de[slice(*_bien_cau(de, vt, vt + len(q)))].strip()`, enforce `_hoi_dung_cum` on `line_ref` goals and supplied named-line feet, and reject `bình phương`/`nửa` object modifiers and `đổi`/`thay`/`cộng`/`trừ`/`nhân`/`chia` arithmetic tails.
  - Confirmed **GREEN** across `test_result_binding_planning.py`, `test_source_gate_clause_role.py`, and `test_hybrid_goal_decomposition.py`.

### `[IMPORTANT-1]` Unreferenced Duplicate `intersection_line` Premises Bypass Alias Coalescing and Emit Duplicate Kernel Lines
- **Finding:** `_EffectResolver` only coalesced `intersection_line` facts when referenced via `resolve_line(fid)`. Two equivalent `intersection_line` premises that were not referenced by any `line_ref` emitted two identical `intersection_line` calls (`gt_g1`, `gt_g2`), or both a coalesced call and a duplicate unreferenced call.
- **RED → GREEN Fix:**
  - Added `test_unreferenced_intersection_line_deduplication_and_coexistence` in `backend/tests/geometry/test_result_binding_planning.py` — confirmed **RED** (`1 failed`).
  - Updated `_bind_result_dependencies` (`backend/app/simulation/geometry_functions/planner.py:703-755`) to canonicalize and deduplicate unreferenced `intersection_line` facts by plane-pair key `(frozenset(points_a), frozenset(points_b))`, skipping unreferenced duplicates or absorbing them into an already-planned canonical `intersection_line` call's `aliases` list.
  - Confirmed **GREEN**.

### `[IMPORTANT-2]` Narrative Discrepancy in `report.md` vs Locked Corpus and Provider Surfaces
- **Finding:** `docs/evaluation/geometry/runs/source-bound-result-planning/report.md` (lines 13, 23–24) listed stale provider hashes (`912b22ef…`, `442d1a0b…`, `be38f55f…`) and inaccurate corpus case IDs/values drafted from memory, even though `provider-surfaces.json`, `visual/corpus-results.json`, and `test_result_binding_planning.py` matched the locked `next-slice-corpus.json` and canonical serializer hashes 100%.
- **Resolution:** Recorded full machine-verified reconciliation in [`reconciliation.json`](reconciliation.json) and corrected `report.md` to match the locked corpus (`derived-line-pyramid` $10/11$, `derived-line-cuboid` $5$, `derived-line-prism` $3$, `different-direction-decomposition` $10$, `zero-distance` $0$, `shared-line-foot-two-goals` $10/11$, plus the exact 12 negative case IDs and refusal codes) and canonical provider surface fingerprints (`7ea511a6…`, `485d3834…`, `5ceb0f99…`).

### `[NONBLOCKING-1]` Explicit Test Coverage for Collinear 3-Point Plane Refusal in `intersection_line`
- **Finding:** Engine (`engine.py:228-235`) and Kernel (`kernel.py:293-305`) already refused 3 distinct collinear points (`Plane3` normal = $\vec{0}$) with `INVALID_COPLANARITY`, but no test in `test_result_binding_planning.py` explicitly exercised that path.
- **Resolution:** Added `test_collinear_three_point_plane_in_intersection_line_is_refused` in `backend/tests/geometry/test_result_binding_planning.py` and verified `PASS`.
