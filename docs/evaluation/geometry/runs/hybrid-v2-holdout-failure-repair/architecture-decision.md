# Architecture Decision Record — Hybrid V2 Holdout Failure Repair (`M1–M5` and `R2`)

## 1. Decision Summary

- **Decision**: Proceed with bounded implementation of **M1–M5** (Contract/Bridge/Planner/Source Gate correctness and Vietnamese section language-coverage repairs). Explicitly **defer R2** (non-coincident auxiliary `point3.notation` hiding) in accordance with Section 0 (`"if it can be implemented safely"`), Section 8 (`"If this correction requires a broad frontend/Scene3D contract redesign, STOP and request a separate Owner decision"`), Section 9 (`"No regression suite may be weakened"`), and Section 14.4 (`"R2 resolution or explicit deferral"`).
- **Version Updates**:
  - `REGISTRY_VERSION`: `geometry-functions/17` → `geometry-functions/18`
  - `PLANNER_VERSION`: `geometry-fact-planner/16` → `geometry-fact-planner/17`
  - Unchanged: `ENGINE_VERSION = "geometry-function-engine/14"`, `ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"`, `PLANE_SECTION_CERTIFICATE_VERSION = "plane-section-certificate/1"`, `CACHE_VERSION = "130"`, `DEFAULT_MODE = "LLM_ONLY"`.

---

## 2. Phase A — M1 (`plane_name` Contract Alignment & `MAT_HAI_DUONG` Source Gate Parity)

### 2.1 Plane Identifier vs. Vertex Label Separation (`planner.py`)

- **Problem**: `typed-fact-next/2` (`typed_fact_next.py:67`) validates `plane_name` with `^(?:[A-Z][0-9]*'?|[α-ω]'?)$`, whereas `planner.py:105` validated `TypedFact.plane_name` with `Label` (`^[A-Z][0-9]*'?$`), rejecting Greek plane names (`α`, `β`).
- **Design**:
  - Keep `Label` (`^[A-Z][0-9]*'?$`) strictly for geometric points/vertices (`point`, `points`, `points_a`, `points_b`, `apex`, `foot`, `cut_points`, `cut_edges`, `boundary_edges`).
  - Introduce `PlaneName` for `TypedFact.plane_name` accepting `^(?:[A-Z][0-9]*'?|[α-ω]'?)$` at runtime while using `pydantic.WithJsonSchema({"pattern": r"^[A-Z][0-9]*'?$", "type": "string"})` so the provider-facing `TypedFact.model_json_schema()` SHA-256 (`aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`) remains byte-identical (no public schema migration required).
  - Preserve exact `plane_name` identity across Bridge → Planner → Registry (`ten_mat_phu`) → Engine (`plane_label`) → Scene3D (`_vai_mat_cat`).

### 2.2 `MAT_HAI_DUONG` & `_kiem_nguon_dong` Source Gate Parity (`registry.py`)

- Expand `_QUA_HAI_DUONG` to accept:
  - Greek or Latin plane symbol `(?P<ten>{_P1}|[α-ω])`
  - Optional `mặt phẳng|mp` prefix and optional `là mặt phẳng` before `_QUA_CHUA`
  - Line-pair phrasings `(?:(?:hai|các)\s+(?:đường thẳng|cạnh)(?:\s+bên)?\s+)?(?P<a>{_P1})\s*(?P<b>{_P1})(?![\w'])\s*(?:,\s*(?:và\s+)?|\s+và\s+)\s*(?P<c>{_P1})\s*(?P<d>{_P1})(?![\w'])`.
- Unify `_mat_hai_duong_dung_nguon` with `mat_song_song_dung_nguon(..., hai_duong=lines, ten_khai=d["plane_name"])` while preserving the strict requirement that `({plane_name})` is not defined or referenced outside the bound plane definition and section ask/construct phrases.
- In `_kiem_nguon_dong`, split sentences on `;` (matching `_kiem_vung_tien_de`) while still rejecting modification tokens (`song|đổi|thay|gấp|nhân đôi|nhân ba`), and add closed verification branches for `right_angle`, `orthogonal_projection`, `altitude`, `height`, `divide_segment`, and chained `segment_length` (`AB = AC = 5`).

---

## 3. Phase B — M2 (Deterministic Single-Solid Binding for Omitted `solid`)

- **Design**:
  - In `typed_fact_next_bridge.py` (`_map_premise` for `height` and `altitude`) and `planner.py` (`khoi_cua`):
    - When `solid` is explicitly provided, validate it against declared solids as before.
    - When `solid` is omitted (`None`):
      - If `len(solids) == 1`, bind deterministically to the unique root solid (for `altitude`, also require that `apex` is the pyramid apex or a prism top vertex and `foot != apex`).
      - If `len(solids) == 0`, raise `TuChoi("UNKNOWN_SOLID", ...)`.
      - If `len(solids) > 1`, raise `TuChoi("AMBIGUOUS_REFERENCE", ...)` — never guess or pick the first solid.
  - Downstream in `registry.py` (`_so_theo_vai_tro` / `_lien_ket_cau` / `_cua_khop`), the bound solid is still verified against any explicit `"của hình <loại> <nhãn>"` in the source sentence, refusing contradictory solid-kind or solid-label attributions.
  - Allow plural quantifiers `(?:(?:các|mọi|mỗi)\s+)?` before role nouns in `_C_VAI`, `_C_DAY`, and `_C_NOI` (`"có các cạnh đáy bằng 4"`).

---

## 4. Phase C — M3 (Bounded Source Gate Section Wording Expansion)

- **`_DAN_THIET_DIEN` & `_CUM_DUNG_THIET_DIEN_PHU`**:
  - Accept `"khi (bị )?cắt bởi"`, `"thiết diện tạo bởi <khối> và mặt phẳng (β)"`, and named section polygons `"thiết diện <POLY> (của <khối>) ..."`.
  - When a section phrase names a polygon `<POLY>` (e.g. `"Xác định thiết diện AMNP"`), verify in `_kiem_mat_song_song` that `set(<POLY>)` equals the grounded section vertices `{through_point, *stated_cut_points}` and `len(<POLY>) >= 3`; otherwise refuse with `SOURCE_OBJECT_MISMATCH`.
- **4-Vertex Coplanar Solid Reference Planes in `mat_song_song_dung_nguon`**:
  - When the source names a 4-vertex plane `tap` (such as a lateral face `(BCC'B')` or diagonal plane `(ACC'A')`, `(BDD'B')`, `(BCD'A')`) and the contract provides a 3-point subset `q` (`len(q) == 3 and frozenset(q) < tap`), accept `tap` if and only if `tap` is a verified coplanar 4-vertex plane of the declared solid (base, top, lateral face `{b_i, b_j, t_j, t_i}`, or opposite-edge plane `{b_i, b_{i+1}, t_{i+2}, t_{i+3}}`). Arbitrary 4-point subsets that are not coplanar faces/diagonal planes of the solid are rejected.
- **Inline Section Prefix Matching**:
  - When matching inline section definitions (`noi_gop`), check both `qn[:m.start()]` and the full source prefix `s[_cau_chua(s, goc + m.start()):goc + m.start()]` so quotes starting at `mặt phẳng (α)...` still bind inline section headers in the same sentence.
- **Line Role Nouns Before Perpendicular Line**:
  - Expand `_QUA_VUONG_DUONG` and `_DIEM_TRUOC_VUONG_DUONG` from `(?:đường thẳng\s+)?` to `(?:(?:đường thẳng|đường chéo|cạnh bên|cạnh đáy|cạnh|đoạn thẳng|đoạn)\s+)?`.
- **`"Tính theo a ..."` Pre-Object Parameter Annotation**:
  - Allow `theo\s+[a-z]` in `_GIUA_HOP_LE` and validate it in `_kiem_don_vi_hoi` (requiring `sym == "a"`, `_co_tham_so_a(calls) == True`, and `chieu in ("length", "area", "volume")`).

---

## 5. Phase D — M4 (Bounded Compound Premise Coverage)

- **Unlabelled `"đáy"` Before `"là"`**:
  - In `_kiem_vung_tien_de`, cover `(?:mặt\s+)?đáy(?=\s+là\b)` when `_chu_cua_day(de, pos)` resolves to a declared solid's base and `_vai_tro_doi_tuong_khop("đáy", verts, calls)` holds.
- **`"trùng với"` in `orthogonal_projection`**:
  - Accept `(?:là|trùng\s+với)` in `construction_source_bound`, `_CUM_DINH_NGHIA_DIEM`, and `_C_CHIEU`.
- **`"các kích thước"` Before Segment Labels**:
  - Add `(?:các\s+)?kích thước` to `_DANH_TU_TRUNG_TINH` and `_C_DOAN`.
- **`_C_DAY` & `_cau_tien_de_dong_hop_le` Right/Isosceles-Right Triangle Base Clauses**:
  - Support `đáy (là) tam giác ABC vuông (cân) tại A` and `đáy ABC vuông tại A` in `_C_DAY`, and verify both `right_angle` and equal ray lengths when `"vuông cân"` appears in `_cau_tien_de_dong_hop_le`.

---

## 6. Phase E — M5 (Bounded Section-Area Question Reference Resolution)

- **Bridge (`typed_fact_next_bridge.py`)**:
  - For `math_goals` with `goal_type == "area"` and `target = {"section_id": sec_id}`:
    1. Direct `"thiết diện"` mention in `g.quote` (existing path).
    2. Anaphoric `"diện tích của nó"` in `g.quote`: allowed only when `len(v.derived_sections) == 1` and the section is defined or constructed in the same or immediately preceding sentence without an intervening competing polygon noun.
    3. Named polygon `"diện tích (của )?(tam giác|tứ giác|đa giác) <POLY>"` in `g.quote`: allowed only when `<POLY>` matches the vertex count of its shape noun and `set(<POLY>)` equals the grounded section polygon `{through_point, *stated_cut_points}` of `sec`.
- **Source Gate (`registry.py`)**:
  - In `mat_song_song_dung_nguon`:
    - Recognize `"diện tích (của )?nó"` in the same sentence after a bound section construction phrase (`_DAN_THIET_DIEN`) when no competing polygon noun intervenes.
    - Recognize `"diện tích (của )?(tam giác|tứ giác|đa giác) <POLY>"` when `<POLY>` equals `{through_point, *stated_cut_points}` (with shape-noun vertex count agreement) and a `DINH_CAT_CANH` certificate on that plane is present.
  - Include these spans in `_CUM_HOI_THIET_DIEN_PHU` / `buoc` so question-context coverage (`_kiem_du_kien_cau_hoi`) accounts for them cleanly.

---

## 7. Phase F — R2 (Scene3D Auxiliary-Point Label Hygiene — Explicit Deferral)

- **Audit of Locked Scene3D Contracts**:
  1. **Locked Contract O4 (`pedagogical-construction-sequencing`)**: `backend/tests/geometry/construction_sequencing.py` (enforced by `backend/tests/geometry/test_pedagogical_sequencing.py`) requires every `point3` object with `producer == "construct_point.translate"` (i.e. `H, H1` in `MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`) to appear in `formation.steps`, carry `notation == <point_id>` (`"H"`, `"H1"`), and have a formation event `learner_text` containing `"vectơ"` and `f"vectơ {names[1]}{names[0]}"` (`"Qua M dựng điểm H sao cho vectơ MH = vectơ BC."`).
  2. **Locked Contract R1 (`scene3d-section-inspector-c0`)**: `backend/tests/geometry/test_section_display_identity.py` (`test_R1_plane_explanation_states_the_source_definition_then_the_real_construction`) requires the cutting plane's `explanation` to state `"Dựng (α): mặt phẳng qua M và song song với (ABCD); dựng qua M và hai điểm dựng phụ H, H1."` and locks `ev["learner_text"] == before["learner_text"]`.
  3. **Locked Contract B (`scene3d-plane-section-display-identity`) & `test_typedfactnext_planner_bridge.py:487`**: `test_typedfactnext_planner_bridge.py:487` requires `objs[d]["notation"]` for `d in mat["depends"]` (`M, H, H1`) to be strings on non-coincident auxiliary points while forbidding `"(MHH1)"` or `"qua M, H, H1"` on any plane/section field; `test_B_a_section_with_unnamed_vertices_is_not_named_through_a_coincident_construction_point` clears `objs["H"]["notation"] = None` specifically when `H` or `H1` coincides in 3D coordinates (`xyz`) with an unnamed section vertex (`I, I1`).
- **Decision (Explicit Deferral of Non-Coincident `point3.notation` Hiding)**:
  - Stripping `notation` (`notation = None`) on non-coincident `H, H1..H4` auxiliary `point3` objects directly contradicts the locked `pedagogical-construction-sequencing` O4 contract, `scene3d-section-inspector-c0` R1 contract, and `test_typedfactnext_planner_bridge.py:487`.
  - Per Section 8 (*"If this correction requires a broad frontend/Scene3D contract redesign, STOP and request a separate Owner decision"*) and Section 9 (*"No regression suite may be weakened"*), non-coincident `point3.notation` hiding is **explicitly deferred** (`backend/app/ai/function_route.py` remains byte-identical to baseline `129c1a952393808bfcdb6ecb48677c09b2ed6293`), preserving 100% of existing Scene3D section/plane/quantity display identity guarantees (`mp_td_*` shows `(α)`, `td_*` shows `"Thiết diện bởi (α)"` with `notation = None`, `kq_*` formulas never leak `H, H1..H4`, unmentioned auxiliary points never carry `"given"` in `display_group`, and source-mentioned `H` in `D012` preserves `notation = "H"`).
