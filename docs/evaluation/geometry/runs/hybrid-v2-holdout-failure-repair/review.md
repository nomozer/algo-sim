# Independent Read-Only Code & Architecture Review Report — `HYBRID_V2_HOLDOUT_FAILURE_REPAIR`

- **Reviewer Subagent**: `3d7a72e1-46bb-48dc-a63a-ec28c61605e3` (`Independent Holdout Repair Reviewer`, `research` read-only)
- **Reviewed Candidate Commit**: `e7bcff316ee6d443e753105a887e0689ea04848b` (product commit `e3678608f1f7110d7046c9c43c312c69d7614f55`)
- **Authoritative Baseline Commit**: `129c1a952393808bfcdb6ecb48677c09b2ed6293` (`main = origin/main`)
- **Measured Product Tree Hash**: `84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f` (`so_file = 118`)
- **Final Verdict**: **`INDEPENDENT_REVIEW_PASS`** (`0 BLOCKER, 0 MAJOR, 0 MINOR, 2 NIT resolved`)

---

## 1. Product Scope & Version Discipline — **PASS**

- **Modified Product Files (`backend/app/` & `frontend/src/`)**:
  - `git diff --name-only 129c1a952393808bfcdb6ecb48677c09b2ed6293..e7bcff31 -- backend/app/ frontend/src/` confirms **only 3 product files** are modified under `backend/app/`:
    1. `backend/app/simulation/geometry_functions/planner.py` (`+75 / -5`)
    2. `backend/app/simulation/geometry_functions/registry.py` (`+286 / -50`)
    3. `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py` (`+20 / -6`)
  - **0 files** are modified under `frontend/src/` and `backend/app/ai/function_route.py` is byte-identical to baseline `129c1a952393808bfcdb6ecb48677c09b2ed6293`.
- **Version Constants & Mode Invariants**:
  - `REGISTRY_VERSION == "geometry-functions/18"` (`registry.py:54`)
  - `PLANNER_VERSION == "geometry-fact-planner/17"` (`planner.py:48`)
  - `ENGINE_VERSION == "geometry-function-engine/14"` (`engine.py`)
  - `ADAPTER_V4_VERSION == "hybrid-simulation-adapter/4"` (`adapter4_route.py`)
  - `PLANE_SECTION_CERTIFICATE_VERSION == "plane-section-certificate/1"` (`engine.py`)
  - `CACHE_VERSION == "130"` (`main.py`)
  - `DEFAULT_MODE == "LLM_ONLY"` (`pipeline.py`) and `main_module.semantic_route_mode() == "off"`

---

## 2. M1 — Plane Identifier Contract Alignment & `MAT_HAI_DUONG` / `_kiem_nguon_dong` Parity — **PASS**

- **`PlaneName` vs `Label` Separation (`planner.py:49–53`, `planner.py:112`, `registry.py:75`)**:
  - `Label` in `registry.py:75` remains strictly `^[A-Z][0-9]*'?$` for geometric point/vertex references (`point`, `points`, `points_a`, `points_b`, `at`, `cut_points`, `cut_edges`, `boundary_edges`).
  - `PlaneName` in `planner.py:49–53` validates `^(?:[A-Z][0-9]*'?|[α-ω]'?)$` at runtime for `TypedFact.plane_name`, accepting both Latin (`P`, `R`, `Q'`) and Greek (`α`, `β`, `α'`) plane identifiers while rejecting Greek symbols on point/vertex fields (`N003`).
  - `TypedFact.model_json_schema()` SHA-256 is verified byte-identical to the locked fingerprint:
    `aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`.
- **`MAT_HAI_DUONG` & `_kiem_nguon_dong` Source Gate Parity (`registry.py:3646–3875`, `4082–4133`, `4606–4653`)**:
  - `_QUA_HAI_DUONG` (`registry.py:4082–4086`) accepts Latin/Greek plane symbols `(?P<ten>{_P1}|[α-ω]'?)`, optional `mặt phẳng|mp` / `là mặt phẳng` prefixes, `_QUA_CHUA` + `_DUOI_DIEM_QUA`, and line-pair phrasings `(?:(?:hai|các)\s+(?:đường thẳng|cạnh)(?:\s+bên)?\s+)?` with comma or `và` separator.
  - `_kiem_mat_song_song` (`registry.py:3869–3872`) routes `MAT_HAI_DUONG` (`two = d.get("rule") == MAT_HAI_DUONG`) through `mat_song_song_dung_nguon(..., hai_duong=lines, ten_khai=d.get("plane_name"))`, giving `MAT_HAI_DUONG` full parity with `MAT_SONG_SONG` and `MAT_VUONG_DUONG` while preserving the strict `defs_span + refs_span` guard (`registry.py:3726–3734`) that rejects unparsed occurrences of `(ten_khai)` (`N001`, `N002`).
  - `_kiem_nguon_dong` (`registry.py:4606–4625`, `4653`) validates full compound sentences via `_cau_tien_de_dong_hop_le(sent_s, sent_start, de, calls, allow_single=True)` (provided no forbidden transform tokens appear) and accepts `cạnh|đoạn thẳng` in `midpoint` atomic forms.

---

## 3. M2 — Single-Solid Resolution & Plural Quantifiers — **PASS**

- **Single-Solid Resolution (`typed_fact_next_bridge.py:229–249`, `planner.py:208`, `392–398`)**:
  - In `typed_fact_next_bridge.py:229–249`, `height` and `altitude` premises resolve `sol = next(iter(solids.values()))` if and only if `sid is None` (`a.get("solid")` and `prem.solid_id` are both `None`) and `len(solids) == 1`. Explicit unknown solid IDs remain unmapped and fail closed.
  - In `planner.py:208`, `_CAN["altitude"]` requires `("points",)`, and `khoi_cua` (`planner.py:392–398`) resolves omitted `s` on `altitude` and `length(measure="height")` to `next(iter(k.solids.values()))` when `len(k.solids) == 1`, raises `AMBIGUOUS_REFERENCE` when `len(k.solids) > 1` (`N004`), and raises `UNKNOWN_SOLID` when `len(k.solids) == 0` or when an explicit `s` is unknown (`N006`).
  - `_cua_khop` (`registry.py`) continues to enforce source-quote solid-kind/label ownership on SG-3 role-value clauses, refusing `UNGROUNDED_VALUE` when a quote claims a conflicting solid kind (`N005`).
- **Plural Quantifiers in SG-3 (`registry.py:933–938`, `964–965`)**:
  - `_C_DAY`, `_C_VAI`, and `_C_NOI` accept optional `(?:(?:các|mọi|mỗi)\s+)?` (and `độ dài (các|mọi|mỗi)`), allowing sentences like `"có các cạnh đáy bằng 4, chiều cao của hình chóp bằng 3"` (`D004`) to parse and bind cleanly.

---

## 4. M3 — Bounded Source Gate Section Wording & 4-Vertex Coplanar Solid Planes — **PASS**

- **Section Wording & Prepositions (`registry.py:2678–2682`, `2973`, `3412–3414`, `3490–3502`, `3568–3574`)**:
  - `_CAT_BOI`, `_DAN_THIET_DIEN`, `_CUM_HOI["ask_section_area"]`, and `_CUM_DUNG_THIET_DIEN` accept `(?:khi\s+(?:bị\s+)?|bị\s+)?(?:cắt bởi|tạo bởi)` and `thiết diện (?:của|(?:được )?tạo bởi) <khối> (?:với|và) <mặt>`.
  - `_QUA_CHUA` and `_DUOI_DIEM_QUA` accept role prefixes (`đỉnh`, `trung điểm`, `trọng tâm`) with role-call verification (`registry.py:3699–3703`) and trailing `của (cạnh|đoạn thẳng|tam giác) <NHAN>`.
  - `_QUA_VUONG_DUONG` and `_DIEM_TRUOC_VUONG_DUONG` (`registry.py:4091–4099`) accept `(?:đường thẳng|đường chéo|cạnh bên|cạnh đáy|đoạn thẳng|đoạn|cạnh)`.
  - `_GIUA_HOP_LE` (`registry.py:3124`), `_CHAN_TAN_NGU` (`registry.py:1786`), and `_kiem_don_vi_hoi` (`registry.py:3257–3260`) accept `"Tính theo a ..."` between the request verb and target phrase if and only if `sym.lower() == "a"`, `chieu in ("length", "area", "volume")`, and `_co_tham_so_a(calls)` is true (`D010`).
- **4-Vertex Coplanar Solid Planes (`_mat_coplanar_khoi`, `registry.py:3617–3639`, `3687–3691`)**:
  - `_mat_coplanar_khoi` enumerates strictly the mathematically coplanar 4-vertex planes of the declared solid (4-gon pyramid base, 4-gon prism base/top, opposite-edge diagonal planes, lateral faces, and vertical diagonal planes spanned by parallel lateral edges). Non-coplanar 4-vertex sets such as `(ABCC')` are excluded and fail closed (`N011`).

---

## 5. M4 — Bounded Compound Premise Clauses — **PASS**

- **Unlabelled `"đáy"` Before `"là"` (`registry.py:2565–2567`)**:
  - In `_kiem_vung_tien_de`, `(?:mặt\s+)?đáy(?=\s+là)` is marked as a verified object reference only when `_chu_cua_day` resolves the owning solid's base vertices `verts <= dung` and `_vai_tro_doi_tuong_khop("đáy", verts, calls)` holds.
- **`"trùng với"` in `orthogonal_projection` (`registry.py:953–955`, `1938`, `3400–3408`, `4380–4381`, `4550–4563`)**:
  - Accepted across `_C_CHIEU`, `_moc_menh_de`, `_CUM_DINH_NGHIA_DIEM`, `construction_source_bound`, and `_cau_tien_de_dong_hop_le(kind="chieu")` (which additionally requires a bound `midpoint` or `centroid` call when `"trung điểm"` or `"trọng tâm"` appears in the projection clause, e.g. `D012`).
- **`"các kích thước"` Before Segment Labels (`registry.py:956`, `2407`)**:
  - Added to `_C_DOAN` and `_DANH_TU_TRUNG_TINH` only when immediately followed by explicit segment labels (`AB = 6, AD = 4, AA' = 2`, `D008`).
- **Right / Isosceles-Right Base Triangles (`registry.py:933`, `4469–4483`)**:
  - `_C_DAY` and `_cau_tien_de_dong_hop_le` validate `right_angle` at the stated vertex (`N012` refuses mismatched right-angle vertex) and additionally require equal leg lengths (`equal_length` call or equal local segment values) when `"cân"` is present.

---

## 6. M5 — Section-Area Question Reference Resolution & Goal Solid Validation — **PASS**

- **Goal Solid Validation in Bridge (`typed_fact_next_bridge.py:326–335`)**:
  - For `goal_type == "area"` with `"section_id" in g.target`, the bridge fails closed with `INVALID_MATH_GOAL` if `section_id` is not in `p.derived_sections`, `UNKNOWN_SOLID_ID` if `g_solid` is not in `solids`, and `SOURCE_OBJECT_MISMATCH` if `g_solid != sec.target_solid_id`.
- **Anaphoric `"tính diện tích của nó"` (`planner.py:961–979`, `registry.py:3579–3583`, `3802–3812`)**:
  - Accepted only when there is a single derived section (`len(k.derived_planes) <= 1`), a unique preceding `thiết diện` mention (`len(tds) == 1`), and **no** competing polygon/face noun (`_DANH_TU_CANH_TRANH_TD`) between that `thiết diện` mention and `diện tích (của )?nó` (`D013`, `D014` pass; `N014` fails closed).
- **Grounded Named Section Polygon `"tính diện tích (tam giác|tứ giác|đa giác) <POLY>"` (`planner.py:980–1000`, `registry.py:3584–3591`, `3750–3791`)**:
  - Verified in both `_hoi_dien_tich_thiet_dien_phu` (`planner.py`) and `mat_song_song_dung_nguon` (`registry.py`): requires distinct vertex labels in `<POLY>`, vertex count agreement with the shape noun (`tam giác` = 3, `tứ giác` = 4), and exact set equality `set(pts) == {through_point, *stated_cut_points}` against the `DINH_CAT_CANH` cut certificate (`N008`, `N015`, `N016` fail closed with `SOURCE_OBJECT_MISMATCH`).

---

## 7. R2 Deferral & No Hardcoding / Fail-Closed Discipline — **PASS**

- **Zero Hardcoding**:
  - Verified 0 occurrences of holdout IDs (`H001..H084`), development corpus IDs (`D001..D016`, `N001..N016`), or case-specific numeric constants/answers in `backend/app/` or `frontend/src/`.
- **R2 Deferral & Regression Preservation**:
  - Deferring R2 (`e3678608`) leaves `backend/app/ai/function_route.py`, `backend/tests/geometry/test_pedagogical_sequencing.py`, `backend/tests/geometry/test_section_display_identity.py`, and `backend/tests/geometry/test_typedfactnext_planner_bridge.py` with **0 diff** against baseline `129c1a952393808bfcdb6ecb48677c09b2ed6293`.
  - Independent execution of the targeted regression bundle passes cleanly: **`316 passed, 5 xfailed`**.

---

## 8. NIT Resolution

- Both documentation NITs noted by the reviewer (`architecture-decision.md` §1/§7 R2 deferral note and regenerating `results/green-evaluation.json` + `results/post-feedback-84-comparison.json` at candidate `e7bcff31`) have been resolved in the final documentation commit without touching any product file.

---

## Final Verdict

**`INDEPENDENT_REVIEW_PASS`**
