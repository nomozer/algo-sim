# Run Report — Hybrid V2 Holdout Failure Repair (`HYBRID_V2_HOLDOUT_FAILURE_REPAIR`)

## 1. Executive Summary

- **Task**: `HYBRID_V2_HOLDOUT_FAILURE_REPAIR`
- **Authoritative Baseline (`main = origin/main`)**: `129c1a952393808bfcdb6ecb48677c09b2ed6293`
- **Branch & Worktree**: `research/hybrid-v2-holdout-failure-repair` in `.superpowers/worktrees/holdout-failure-repair`
- **Preserved Holdout Worktree (Untouched)**: `research/hybrid-v2-independent-vietnamese-section-holdout` (`f7f177a626c33bb13aa40d3a904c82266ed8a276`) in `.superpowers/worktrees/independent-section-holdout`
- **Final Product Commit**: `e3678608f1f7110d7046c9c43c312c69d7614f55`
- **Frozen Full T3 Candidate Commit**: `e7bcff316ee6d443e753105a887e0689ea04848b` (`measured_system.tree_hash = 84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`, `so_file = 118`)
- **Versions**:
  - `REGISTRY_VERSION`: `geometry-functions/18` (bumped from `/17`)
  - `PLANNER_VERSION`: `geometry-fact-planner/17` (bumped from `/16`)
  - `ENGINE_VERSION`: `geometry-function-engine/14` (unchanged)
  - `ADAPTER_V4_VERSION`: `hybrid-simulation-adapter/4` (unchanged)
  - `PLANE_SECTION_CERTIFICATE_VERSION`: `plane-section-certificate/1` (unchanged)
  - `CACHE_VERSION`: `130` (unchanged, `NO_BUMP`)
  - `DEFAULT_MODE`: `LLM_ONLY` (unchanged, Hybrid opt-in only)
- **Live Provider Calls**: `0` (`ALLOW_LIVE_AI = 0`)
- **R2 Status**: `R2_AUXILIARY_POINT_NOTATION_DEFERRED`
- **Final Decision**: **`READY_FOR_OWNER_REVIEW`**

---

## 2. Preflight & Evidence Reconciliation (Section 1 & Section 3.A)

As documented in [`baseline-audit.md`](baseline-audit.md):

1. **Authoritative Holdout Evidence (`results/scored-run-1/summary.json`, `results/scored-run-1/track-a.json`, `results/analysis.json`, `review.md` at product `129c1a95` / freeze `6c7f6d5b`)**:
   - **9/42 `SERVED_CORRECT` (`21.4%`, `9/9 = 100%` exact-oracle agreement)**: `H001`, `H003`, `H009`, `H014`, `H020`, `H021`, `H025`, `H027`, `H031`.
   - **33/42 `FALSE_REFUSAL` (`78.6%`) — First-Refusal-Layer Breakdown (`scored-run-1/track-a.json` & `summary.json`)**:
     - `SCHEMA_INVALID` (category `INPUT_INVALID` — M1 `plane_name` `'α'`/`'β'` on `through_point_parallel_two_lines` rejected by `planner.py:105`): **12 cases** (`H005, H006, H011, H012, H017, H018, H023, H024, H029, H030, H035, H036`).
     - `UNKNOWN_SOLID` (category `INPUT_INVALID` — M2 omitted `solid` on `height`/`altitude` in single-solid problems): **3 cases** (`H008, H010, H040`).
     - `SOURCE_OBJECT_MISMATCH` (category `SOURCE_GROUNDING` — M3 section wording and 4-vertex coplanar solid reference planes): **14 cases** (`H004, H007, H013, H016, H019, H022, H026, H028, H032, H033, H034, H037, H039, H042`).
     - `SOURCE_PREMISE_UNREAD` (category `SOURCE_GROUNDING` — M4 compound premise clause): **1 case** (`H002`).
     - `UNSUPPORTED_CAPABILITY` (category `UNSUPPORTED_CAPABILITY` — M5 section-area question binding): **3 cases** (`H015, H038, H041`).
   - **42/42 Negatives Refused (`100%`), `0/84` Wrong-Served (`0.0%`)**:
     - **23/42 `REFUSED_CORRECT_REASON` (`54.8%`)**: `H043, H044, H045, H046, H049, H050, H056, H057, H058, H060, H061, H063, H064, H065, H066, H067, H069, H078, H079, H081, H082, H083, H084`.
     - **19/42 `REFUSED_REASON_DISAGREEMENT` (`45.2%`)**: `H047, H048, H051, H052, H053, H054, H055, H059, H062, H068, H070, H071, H072, H073, H074, H075, H076, H077, H080`.
2. **First-Refusal-Layer Counts vs. Post-Hoc Multi-Blocker Causal Mechanisms (`review.md §2.3 R1`)**:
   - The 5 counts above (`M1: 12`, `M2: 3`, `M3: 14`, `M4: 1`, `M5: 3`) are **first-refusal-layer** counts. Several cases carry stacked downstream defects:
     - Among the 12 M1 (`SCHEMA_INVALID`) cases, fixing M1 alone serves only `H029`; the other 11 then encounter secondary M2/M3/M4 blockers (`H018, H030` also omit `solid` on `height`/`altitude`; `H005, H024` hit compound premise/semicolon coverage; `H006, H011, H012, H017, H023, H030, H035, H036` hit `MAT_HAI_DUONG` / `_kiem_nguon_dong` Source Gate rules).
     - Among the 3 M2 (`UNKNOWN_SOLID`) cases (`H008, H010, H040`), fixing M2 alone serves `0/3` because `H008` then hits M3 (`SOURCE_OBJECT_MISMATCH`), `H010` hits M2 plural quantifier (`"các cạnh đáy bằng 4"`), and `H040` hits M5 (`"Tính diện tích tứ giác AEFK"`).
     - Among the 14 M3 (`SOURCE_OBJECT_MISMATCH`) cases, `H019, H022, H028` also contain M4 compound premise clauses (`"đáy là..."`, `"trùng với"`, `"các kích thước"`).
3. **Prose Summary Discrepancy Reconciled**:
   - Earlier conversational prose summaries transposed 4 pairs of adjacent case IDs (`H008↔H009`, `H014↔H016`, `H025/H027↔H028/H030`, `H039↔H040`) between the served and refused lists; the frozen `scored-run-1/track-a.json`, `summary.json`, `analysis.json`, and `review.md` agree 100% and govern as authoritative historical records. No historical holdout files were modified.

---

## 3. Root Causes & Repairs (`M1–M5`) and `R2` Deferral

### 3.1 Changed Product Files (3 files under `backend/app/`, 0 under `frontend/src/`)

- [`backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`](../../../../../backend/app/simulation/geometry_functions/typed_fact_next_bridge.py) (`+20 / -6`)
- [`backend/app/simulation/geometry_functions/planner.py`](../../../../../backend/app/simulation/geometry_functions/planner.py) (`+75 / -5`)
- [`backend/app/simulation/geometry_functions/registry.py`](../../../../../backend/app/simulation/geometry_functions/registry.py) (`+286 / -50`)

### 3.2 Defect Class M1 — Plane Identifier Contract Alignment & `MAT_HAI_DUONG` / `_kiem_nguon_dong` Parity

- **Root Cause**: `typed_fact_next.py:67` accepted Greek plane names `[α-ω]'?`, whereas `planner.py:105` typed `TypedFact.plane_name` as `Label` (`^[A-Z][0-9]*'?$`), rejecting all Greek plane names (`α`, `β`) with `INVALID_FACT:1:plane_name`. Furthermore, `MAT_HAI_DUONG` used a narrower source matcher (`_mat_hai_duong_dung_nguon`) than `MAT_SONG_SONG`/`MAT_VUONG_DUONG`, and `_kiem_nguon_dong` did not delegate compound sentences to `_cau_tien_de_dong_hop_le`.
- **Fix**:
  - Defined `PlaneName` (`^([A-Z][0-9]*'?|[α-ω]'?)$`) for `TypedFact.plane_name` in `planner.py` while keeping `Label` (`^[A-Z][0-9]*'?$`) strictly for point/vertex fields and preserving the exact `TypedFact.model_json_schema()` SHA-256 (`aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`).
  - Unified `MAT_HAI_DUONG` source binding with `mat_song_song_dung_nguon(..., hai_duong=lines, ten_khai=d.get("plane_name"))` while retaining the strict `defs_span + refs_span` guard on `(plane_name)` occurrences.
  - Enabled `_cau_tien_de_dong_hop_le(..., allow_single=True)` validation in `_kiem_nguon_dong` for clean premise sentences.

### 3.3 Defect Class M2 — Deterministic Single-Solid Resolution & Plural Role Quantifiers

- **Root Cause**: When a `height` or `altitude` fact omitted `solid` in a single-solid problem, Bridge/Planner refused with `MISSING_FACT_FIELD` (`H008, H010, H040`), and SG-3 (`_C_VAI`, `_C_DAY`, `_C_NOI`) did not allow plural quantifiers `các|mọi|mỗi` (`"có các cạnh đáy bằng 4"`).
- **Fix**:
  - Resolved omitted `solid` on `height` and `altitude` deterministically to the unique root solid if and only if `len(solids) == 1`, while refusing `UNKNOWN_SOLID` on 0 solids or unknown explicit solid IDs (`N006`), `AMBIGUOUS_REFERENCE` on `>= 2` solids (`N004`), and `UNGROUNDED_VALUE` on conflicting solid-kind ownership (`N005`).
  - Added `(?:(?:các|mọi|mỗi)\s+)?` and optional `độ dài` prefix support to `_C_DAY`, `_C_VAI`, and `_C_NOI`.

### 3.4 Defect Class M3 — Bounded Source Gate Section Wording & 4-Vertex Coplanar Solid Planes

- **Root Cause**: Valid Vietnamese section phrasings (`khi (bị )?cắt bởi`, `thiết diện tạo bởi <khối> và mặt phẳng (...)`, `thiết diện <POLY>`, `đường chéo / cạnh bên` before perpendicular lines, `Tính theo a ...`, and 4-vertex coplanar solid reference planes such as `(BCC'B')`, `(BDD'B')`, `(BCD'A')` represented by 3 points in `parallel_plane`) were rejected by `registry.py`.
- **Fix**:
  - Expanded `_CAT_BOI`, `_DAN_THIET_DIEN`, `_QUA_VUONG_DUONG`, `_DIEM_TRUOC_VUONG_DUONG`, `_GIUA_HOP_LE`, `_CHAN_TAN_NGU`, and `_kiem_don_vi_hoi` in a closed, fail-closed manner.
  - Added `_mat_coplanar_khoi(calls, solid)` in `registry.py` so a 3-point `parallel_plane` `q` matches a 4-vertex source plane `tap` if and only if `frozenset(q) < tap` and `tap` is a mathematically coplanar 4-vertex plane of the declared solid (4-gon base/top, lateral face, vertical diagonal plane, or opposite-edge diagonal plane `{b_i, b_{i+1}, t_{i+2}, t_{i+3}}`). Non-coplanar 4-vertex sets (`N011`) fail closed.

### 3.5 Defect Class M4 — Bounded Compound Premise Clauses

- **Root Cause**: `_kiem_vung_tien_de` and `_cau_tien_de_dong_hop_le` did not cover unlabelled `đáy` before `là` when owned by the declared solid's base, `trùng với` in `orthogonal_projection`, `các kích thước` before segment lengths, or `đáy ABC vuông tại A` without `là tam giác`.
- **Fix**:
  - Covered unlabelled `(?:mặt\s+)?đáy(?=\s+là\b)` via `_chu_cua_day` + `_vai_tro_doi_tuong_khop("đáy", verts, calls)`, added `trùng với` to `_C_CHIEU` / `construction_source_bound` and `kind == "chieu"` to `_cau_tien_de_dong_hop_le` (requiring a bound `midpoint`/`centroid` call when `"trung điểm"`/`"trọng tâm"` appears), added `(?:các\s+)?kích thước` to `_C_DOAN` / `_DANH_TU_TRUNG_TINH`, and added `|vuông(?:\s+cân)?\s+tại\s+{_L1}` to `_C_DAY`.

### 3.6 Defect Class M5 — Section-Area Question Reference Resolution & Goal Solid Validation

- **Root Cause**: Section-area questions phrased anaphorically (`"tính diện tích của nó"`) or by grounded section polygon name (`"tính diện tích tam giác MNP"`, `"tính diện tích tứ giác MNPQ"`) were rejected by Bridge/Planner/Source Gate, and Bridge did not validate `g.solid_id` on `area` `MathGoal` when `section_id` was present.
- **Fix**:
  - Validated `section_id` and `solid_id` fail-closed on `area` `MathGoal` in `typed_fact_next_bridge.py` (`INVALID_MATH_GOAL`, `UNKNOWN_SOLID_ID`, `SOURCE_OBJECT_MISMATCH`).
  - Added bounded support across `planner.py` (`_cau_hoi`, `_hoi_dien_tich_thiet_dien_phu`) and `registry.py` (`_HOI_DIEN_TICH_NO`, `_HOI_DIEN_TICH_TEN_TD`, `_CUM_TEN_THIET_DIEN`, `_CUM_HOI_THIET_DIEN_PHU`) for `"diện tích (của )?nó"` (single section, unique `thiết diện` antecedent, no competing polygon noun `N014`) and `"diện tích (của )?(tam giác|tứ giác|đa giác) <POLY>"` (requiring `<POLY>` to match the shape noun's vertex count and equal `{through_point, *stated_cut_points}` on the `DINH_CAT_CANH` certificate; `N008, N015, N016` fail closed).

### 3.7 Phase F (R2) — Explicit Deferral (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`)

- **Finding**: Stripping `notation` (`notation = None`) on non-coincident auxiliary `point3` objects (`H, H1..H4`) directly violates three locked regression contracts:
  1. `pedagogical-construction-sequencing` Contract **O4** (`backend/tests/geometry/construction_sequencing.py` + `test_pedagogical_sequencing.py`), which requires every `point3` with `producer == "construct_point.translate"` to appear in `formation.steps`, carry `notation = "H"` / `"H1"`, and have step `learner_text` `"Qua M dựng điểm H sao cho vectơ MH = vectơ BC."`.
  2. `scene3d-section-inspector-c0` Contract **R1** (`backend/tests/geometry/test_section_display_identity.py:77-93`), which locks `mp_td_*` `explanation` to `"Dựng (α): ...; dựng qua M và hai điểm dựng phụ H, H1."`.
  3. `typedfactnext-planner-bridge` (`backend/tests/geometry/test_typedfactnext_planner_bridge.py:487`), which requires `objs[d]["notation"]` for `d in mat["depends"]` (`M, H, H1`) to be strings on non-coincident points while forbidding `"(MHH1)"` on the plane/section.
- **Resolution (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`)**: Per Section 0 (*"if it can be implemented safely"*), Section 8 (*"If this correction requires a broad frontend/Scene3D contract redesign, STOP and request a separate Owner decision"*), Section 9 (*"No regression suite may be weakened"*), and Section 14.4 (*"R2 resolution or explicit deferral"*), non-coincident `point3.notation` hiding is recorded as **`R2_AUXILIARY_POINT_NOTATION_DEFERRED`** (`backend/app/ai/function_route.py` has 0 diff against baseline `129c1a95`). All existing Scene3D section/plane/quantity display identity guarantees (`mp_td_*` shows `(α)`, `td_*` shows `"Thiết diện bởi (α)"`, `kq_*` formulas never leak `H, H1..H4`, unmentioned auxiliaries are never marked `"given"`, and coincident translate points `H, H1` in `_an_dinh_thiet_dien_phu` have `notation = None`) remain 100% intact.

---

## 4. Registered 32-Case Development Corpus RED → GREEN Evaluation (Section 9)

- **Corpus**: [`new-development-corpus.json`](new-development-corpus.json) (`16` positive `D001..D016` + `16` negative/adversarial `N001..N016`, SHA-256 `6715740993e15b91a91f1713b6011d85a00a70f6cf261e10a7a885c1b8009887`)
- **Independent Exact Oracle**: [`oracle/new_dev_oracle.py`](oracle/new_dev_oracle.py) (exact `Fraction` arithmetic, independent of product modules)
- **Pytest Suite**: [`backend/tests/geometry/test_holdout_failure_repair.py`](../../../../../backend/tests/geometry/test_holdout_failure_repair.py) (`50/50 passed`)

| Metric | RED (`129c1a95` Baseline) | GREEN (`e7bcff31` Candidate) |
|---|---|---|
| **Positive Cases (`D001..D016`) Served** | `0 / 16` (`0.0%`) | **`16 / 16` (`100.0%`)** |
| **Exact Oracle Agreement on Served Positives** | `0 / 16` | **`16 / 16` (`100.0%`)** |
| **Positive False Refusals** | `16 / 16` | **`0 / 16` (`0.0%`)** |
| **Negative Cases (`N001..N016`) Refused** | `16 / 16` (`100.0%`) | **`16 / 16` (`100.0%`)** |
| **Negative Expected Refusal Code Match** | `12 / 16` (`75.0%`) | **`16 / 16` (`100.0%`)** |
| **Wrong-Served Total** | `0 / 32` | **`0 / 32` (`0.0%`)** |
| **Plane/Section/Quantity Aux Label Leaks** | `0` | **`0`** |

---

## 5. Post-Feedback 84-Case Comparison & Scorer Adjudication (`POST_FEEDBACK_DEVELOPMENT_REGRESSION`, Section 3.B & 3.C)

> [!IMPORTANT]
> The 84-case corpus from `hybrid-v2-independent-vietnamese-section-holdout` was opened and analyzed to diagnose `M1–M5`. Below it is reported strictly as **`POST_FEEDBACK_DEVELOPMENT_REGRESSION`** (`POST_FEEDBACK_REGRESSION_NOT_INDEPENDENT_HOLDOUT`, [`results/post-feedback-84-comparison.json`](results/post-feedback-84-comparison.json), [`results/h039-h040-adjudication-receipt.json`](results/h039-h040-adjudication-receipt.json)) and is **not** a new independent holdout score. **Independent Holdout Wave 2 is `NOT_EXECUTED`.**

| Metric | 1. Original Independent Holdout (`129c1a95`, Frozen) | 2. Post-Feedback Raw Frozen Evaluator (`evaluate_holdout.py` on `e7bcff31`) | 3. Post-Feedback Independently Adjudicated (`e7bcff31`, `POST_FEEDBACK_DEVELOPMENT_REGRESSION`) |
|---|---|---|---|
| **Classification** | `FROZEN_INDEPENDENT_HOLDOUT_BASELINE` | `POST_FEEDBACK_DEVELOPMENT_REGRESSION_RAW_SCORER` | `POST_FEEDBACK_DEVELOPMENT_REGRESSION_ADJUDICATED` |
| **Total Cases** | `84` (`42` SERVE, `42` REFUSE) | `84` (`42` SERVE, `42` REFUSE) | `84` (`42` SERVE, `42` REFUSE) |
| **Positives Correctly Served (`SERVED_CORRECT`)** | `9 / 42` (`21.4%`) | `38 / 42` (`90.5%`, see Note 1) | **`40 / 42` (`95.2%`)** |
| **Exact Oracle Agreement Among Served Positives** | `9 / 9` (`100.0%`) | `38 / 40` (see Note 1) | **`40 / 40` (`100.0%`)** |
| **Positive False Refusals (`FALSE_REFUSAL`)** | `33 / 42` (`78.6%`) | `2 / 42` (`4.8%`, `H037`, `H042`) | **`2 / 42` (`4.8%`, `H037`, `H042`)** |
| **Negatives Refused** | `42 / 42` (`100.0%`) | `42 / 42` (`100.0%`) | **`42 / 42` (`100.0%`)** |
| **Negative Refusal Reason Category Agreement** | `23 / 42` (`54.8%`) | `27 / 42` (`64.3%`) | **`27 / 42` (`64.3%`)** |
| **Wrong-Served on Refuse Cases** | `0 / 42` (`0.0%`) | `0 / 42` (`0.0%`) | **`0 / 42` (`0.0%`)** |
| **Wrong-Served Total** | `0 / 84` (`0.0%`) | `2 / 84` (`H039, H040` scorer bug, Note 1) | **`0 / 84` (`0.0%`)** |
| **Plane/Section/Quantity Aux Label Leaks** | `0 / 9` | N/A (Note 2) | **`0 / 40`** |

### Notes on `evaluate_holdout.py` Scorer Discrepancy Adjudication & Remaining 2 False Refusals

1. **Note 1 — Independent Exact-Arithmetic Adjudication of `H039` and `H040` ([`results/h039-h040-adjudication-receipt.json`](results/h039-h040-adjudication-receipt.json))**:
   - At baseline (`129c1a95`), `0/6` Category A (`P-A`) cases were served, so `_check_category_a` in `evaluate_holdout.py` (lines 97–101) was never exercised.
   - In `oracle_holdout.py` (lines 127–133), a section vertex lying exactly at a solid vertex (`f[v] == 0`) is written to `oracle/expected.json` as `{"vertex": "C"}` (`H039`) or `{"vertex": "A"}` (`H040`), whereas only strict interior edge cuts (`0 < t < 1`) are written as `{"edge": [u, v], "t": ...}`.
   - In `evaluate_holdout.py`, `_oracle_boundary(exp)` (lines 64–73) parses `{"vertex": ...}` into `verts` and `{"edge": ...}` into `edge_sets`, but `_check_category_a(sec, exp)` (lines 97–101) unpacks `_, _, o_sets = _oracle_boundary(exp)`—discarding `verts`—and checks `frozenset(v.get("edge")) in o_sets` for **every** entry in `route_d.sections[0].vertices`.
   - In Category A (`DINH_CAT_CANH`), the cutting-plane `through_point` (`C` in `H039`; `A` in `H040`) is a solid vertex represented in `route_d.sections[0].vertices` with `provenance == "THROUGH_POINT_REUSE"`, `stated == False`, and carrier lateral edge `v["edge"]` (`["C", "C'"]` in `H039`; `["S", "A"]` in `H040`), while in `scene3d.objects[td_sec1]` it is emitted with `vertex_sources[i].kind == "SOLID_VERTEX"` and `endpoint_entities[i].provenance_kind == "SOLID_VERTEX"`.
   - Independent exact `Fraction` verification in [`results/h039-h040-adjudication-receipt.json`](results/h039-h040-adjudication-receipt.json) confirms:
     - **`H039`**: `CEF` has 3 vertices: solid vertex `C` (`f(C) = 0`), `E` on `AA'` at `t = 32/169`, `F` on `BB'` at `t = 14/169`; `scene3d` polygon `[["176/169","7/169","14/169"], ["16/169","16/169","32/169"], ["0","1","0"]]` matches `(F, E, C)` with `0` error; `Adapter /4` (`hybrid-simulation-adapter/4`) and `DINH_CAT_CANH` pass with `identity_diagnostics = []`.
     - **`H040`**: `AEFK` has 4 vertices: solid vertex `A` (`f(A) = 0`), `E` on `SB` at `t = 1/9`, `F` on `SC` at `t = 1/17`, `K` on `SD` at `t = 1/9`; `scene3d` polygon `[["0","0","0"], ["5/9","4/9","8/9"], ["9/17","9/17","16/17"], ["4/9","5/9","8/9"]]` matches `(A, E, F, K)` with `0` error; `area_squared = "256/153"` matches both the independent `Fraction` calculation and `oracle/expected.json` (`"256/153"`).
2. **Note 2 (`evaluate_holdout.py::_aux_leaks`)**:
   - `evaluate_holdout.py` line 117 used an ASCII-only regex `(?<![A-Za-z0-9_'])H(?![A-Za-z0-9_'])` across all objects, which matched capital `'H'` in Vietnamese `"Hình chóp ..."` (`'ì'` is non-ASCII) and flagged `point3.notation = "H"` required by the locked `pedagogical-construction-sequencing` O4 contract (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`). Across all `40/40` served positive cases, `0` cases leak auxiliary labels into plane, section, or quantity display fields or mark unmentioned auxiliaries as `"given"`.
3. **Remaining 2 Positive False Refusals (`H037` and `H042`) — Out of Scope of Locked Modules**:
   - **`H037`**: Refused with `ENGINE_EXECUTION_FAILED` (`RadicalDomainError: căn thức 3142715144400 vượt trần 1000000000000`) due to the radical-domain cap (`10^12`) in `engine.py` (`ENGINE_VERSION = "geometry-function-engine/14"`, locked in this wave).
   - **`H042`**: Refused with `PREVIEW_VALIDATION_FAILED` in `adapter4_route.py` (`ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"`, locked in this wave) because `H042` states only `1` cut point (`DD'` at `Q`) out of `4` section vertices, mixing `stated_intersections` (Category A) with Category B (`plane-section-certificate/1`) section derivation.

---

## 6. Verification Gates, Candidate Freeze & Independent Review (Section 11)

- **T0 Impact Gate**: `IMPACT_GATE_PASS` (`node frontend/scripts/impact.mjs --base 129c1a952393808bfcdb6ecb48677c09b2ed6293 --dry`)
- **T1 Targeted Backend Suites**: `50/50` (`test_holdout_failure_repair.py`), `184/184` (`test_pedagogical_sequencing.py`, `test_typedfactnext_planner_bridge.py`, `test_section_display_identity.py`, `test_hybrid_preview_fixtures.py`), `482/482` (candidate/docs/readiness/integration/acceptance suites)
- **T2 Frontend Vitest Suite**: `83/83` test files, `1417/1417` tests passed
- **Candidate Freeze**: `e7bcff316ee6d443e753105a887e0689ea04848b` (product `e3678608f1f7110d7046c9c43c312c69d7614f55`, `118` files, `tree_hash = 84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f`, `freeze_evaluation_candidate.py --verify` `MATCH`)
- **Full T3 on Clean Detached Worktree (`D:/tmp/pg-t3-e7bcff31`)**: **`FULL_PRODUCT_GATE_PASS`** ([`full-t3/receipt.json`](full-t3/receipt.json))
  - Backend pytest: `12471 passed, 1 skipped, 2 deselected, 15 xfailed`
  - Frontend vitest: `83 passed (83) / 1417 passed (1417)`
  - Production typecheck + build: `PASS`
  - Thesis demo replay: `5/5 PASS`, `1/1 REDUCED_CHAIN PASS`
  - Demo crash surface: `6/6 PASS`, `0` unhandled exceptions
  - Post-T3 freeze check: **`MATCH`** (`exit_code = 0`)
- **Independent Read-Only Code Review**: **`INDEPENDENT_REVIEW_PASS`** ([`review.md`](review.md), subagent `3d7a72e1-46bb-48dc-a63a-ec28c61605e3`)

---

## 7. Remaining Risks & Open Items

1. **Independent Holdout Wave 2 (`NOT_EXECUTED`)**: Because the 84-case holdout corpus was opened to diagnose `M1–M5`, the `40/42` (`95.2%`) score is a `POST_FEEDBACK_DEVELOPMENT_REGRESSION` result, not an untouched blind holdout score. A fresh blind holdout is required before making curriculum generalization claims.
2. **Phase F (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`)**: Hiding `point3.notation` on non-coincident auxiliary points (`H, H1..H4`) requires an explicit Owner decision on revising the locked `pedagogical-construction-sequencing` O4 (`construction_sequencing.py`) and `scene3d-section-inspector-c0` R1 (`test_section_display_identity.py`) contracts.
3. **Locked Engine `/14` Radical Cap (`H037`) & Partial Stated Intersections (`H042`)**: Increasing `_TRAN_CAN` above `10^12` in `engine.py` or supporting partial `stated_intersections` on Category B sections in `adapter4_route.py` requires a future wave authorized to touch `engine.py` / `adapter4_route.py`.
4. **Live NL E2E & Browser E2E (`NOT_MEASURED`)**: Live natural-language extraction E2E and browser E2E for this repair wave are `NOT_MEASURED`.
