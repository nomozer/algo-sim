# Baseline Audit & Evidence Reconciliation (`HYBRID_V2_HOLDOUT_FAILURE_REPAIR`)

## 1. Preflight Verification

- **Authoritative Baseline SHA**: `129c1a952393808bfcdb6ecb48677c09b2ed6293` (`local main == origin/main`)
- **Product Freeze Verification at Baseline**:
  - `freeze_evaluation_candidate.py --verify`: `MATCH`
  - Frozen file count: `118`
  - Frozen tree hash: `ae6360b1d20beb96b87bad4f335b74b3a61e7483d06214aa2192f17fe6f1c70a`
- **Baseline Versions**:
  - `REGISTRY_VERSION`: `geometry-functions/17`
  - `PLANNER_VERSION`: `geometry-fact-planner/16`
  - `ENGINE_VERSION`: `geometry-function-engine/14`
  - `ADAPTER_V4_VERSION`: `hybrid-simulation-adapter/4`
  - `PLANE_SECTION_CERTIFICATE_VERSION`: `plane-section-certificate/1`
  - `CACHE_VERSION`: `130`
  - `DEFAULT_MODE`: `LLM_ONLY` (Hybrid opt-in only)
- **Isolated Worktree**:
  - Path: `.superpowers/worktrees/holdout-failure-repair`
  - Branch: `research/hybrid-v2-holdout-failure-repair`
  - Preserved Holdout Worktree (untouched): `.superpowers/worktrees/independent-section-holdout` on branch `research/hybrid-v2-independent-vietnamese-section-holdout` (`f7f177a626c33bb13aa40d3a904c82266ed8a276`)

---

## 2. Section 1 — Authoritative Evidence Reconciliation

Per Section 1 of the Owner GO, the frozen holdout files in `.superpowers/worktrees/independent-section-holdout/docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout/` were audited against the earlier prose summary:
1. `inputs/holdout.json` & `holdout-manifest.json` (`sha256: 2ac510be64e4dd135ab69a67d62dfbc5dc34495c4850df4d432e89bc7f699ac2`)
2. `results/scored-run-1/summary.json` & `results/scored-run-1/track-a.json`
3. `results/analysis.json` & `review.md`

### 2.1 Authoritative Case Lists vs. Earlier Prose Summary

All three machine-generated artifacts (`results/scored-run-1/summary.json`, `results/scored-run-1/track-a.json`, `results/analysis.json`) and `review.md` are **100% consistent with each other**. The discrepancy was solely in the conversational prose summary, which transposed 4 pairs of adjacent case IDs (`H008↔H009`, `H014↔H016`, `H025/H027↔H028/H030`, `H039↔H040`):

| Category | Authoritative Frozen Evidence (`track-a.json`, `summary.json`, `analysis.json`, `review.md`) | Earlier Prose Summary | Exact Reconciliation |
|---|---|---|---|
| **Served Correct (`9/42`)** | `H001`, `H003`, `H009`, `H014`, `H020`, `H021`, `H025`, `H027`, `H031` | Listed `H008, H016, H028, H030, H039` in place of `H009, H014, H025, H027` | `H009, H014, H025, H027, H031` are the true served cases alongside `H001, H003, H020, H021`. |
| **M1: `SCHEMA_INVALID` (`plane_name`, 12 positive + 2 negative)** | Positives: `H005, H006, H011, H012, H017, H018, H023, H024, H029, H030, H035, H036`; Negatives: `H054, H062` | Omitted `H030` because it misclassified `H030` as served | All 12 positive `through_point_parallel_two_lines` (`P2`) cases failed at `planner.py:105` (`TypedFact.plane_name` rejecting `α`/`β`). |
| **M2: `UNKNOWN_SOLID` (omitted `solid`, 3 positive + 2 negative)** | Positives: `H008, H010, H040`; Negatives: `H048, H051` | Listed `H009, H010, H039` | `H008, H010, H040` are the 3 regular-pyramid positive cases with omitted `solid` on `height`. |
| **M3: `SOURCE_OBJECT_MISMATCH` (section wording, 14 positive)** | `H004, H007, H013, H016, H019, H022, H026, H028, H032, H033, H034, H037, H039, H042` | Listed `H014, H025, H027, H040` instead of `H016, H028, H039` | All 14 positive cases failed at the Registry Source Gate (`_kiem_mat_song_song` / `mat_song_song_dung_nguon`). |
| **M4: `SOURCE_PREMISE_UNREAD` (compound premise, 1 primary positive)** | `H002` (plus secondary premise-coverage blockers on `H015, H019, H022, H024, H028`) | `H002` | `H002` failed at `_kiem_vung_tien_de` on `"Cho hình chóp S.ABC có đáy là tam giác ABC vuông tại A với AB = 6, AC = 8."` |
| **M5: `UNSUPPORTED_CAPABILITY` (area wording, 3 primary positive)** | `H015, H038, H041` (plus secondary blocker on `H040` after M2) | `H015, H038, H041` | `H015, H041` ask `"tính diện tích của nó"`; `H038` (and `H040`) ask `"Tính diện tích tam giác MNP"` / `"Tính diện tích tứ giác AEFK"`. |

---

## 3. Root-Cause Audit Across M1–M5 and R2

### 3.1 Phase A — M1 (`plane_name` Contract Mismatch & `MAT_HAI_DUONG` Source Gate Parity)

1. **Contract-to-Planner `plane_name` Mismatch**:
   - `typed_fact_next.py:67` defines `_PLANE_SYM_RE = re.compile(r"^(?:[A-Z][0-9]*'?|[α-ω]'?)$")`.
   - `typed_fact_next_bridge.py:293` forwards `plane_name=s.plane_name` on `through_point_parallel_two_lines` facts.
   - `planner.py:105` defines `plane_name: Label | None = None`, where `Label` requires `^[A-Z][0-9]*'?$`. Any Greek plane symbol (`α`, `β`) raises `SCHEMA_INVALID` at `planner.py:165`.
   - **Constraint**: `TypedFact.model_json_schema()` is pinned by SHA-256 (`aa9d93eeac9f1659af8e5acd42af1904b7aaed674a8ab0f56f0c7dd8b2ad4ee8`) in 4 test suites. Using `PlaneName = Annotated[str, BeforeValidator(_nhan_mat), Field(pattern=r"^(?:[A-Z][0-9]*'?|[α-ω]'?)$"), WithJsonSchema({"pattern": r"^[A-Z][0-9]*'?$", "type": "string"})]` accepts Greek plane symbols at runtime without altering the locked JSON schema hash.
2. **Secondary `MAT_HAI_DUONG` Parity Blockers in `registry.py`**:
   - `_QUA_HAI_DUONG` (`registry.py:3930`) only accepted Latin `(?P<ten>{_P1})`, required explicit `mặt phẳng|mp` before `({ten})`, and did not accept `(?:hai|các)\s+(?:đường thẳng|cạnh)(?:\s+bên)?` or comma-separated line pairs (`AB, SC`).
   - `_mat_hai_duong_dung_nguon` (`registry.py:3979–4037`) was a restrictive duplicate of `mat_song_song_dung_nguon` that rejected inline section definitions (`cắt bởi mặt phẳng (α) đi qua M, song song với AD và SB`), `"khi cắt bởi (α)"`, and `"tính diện tích của thiết diện"` / `"thiết diện đó"`.
   - `_kiem_nguon_dong` (`registry.py:4399–4494`) rejected semicolons (`;`) inside sentences and lacked closed branches for `right_angle`, `orthogonal_projection`, `altitude`, `height`, `divide_segment`, and single-clause premise segments after `;`.

### 3.2 Phase B — M2 (Optional `solid` Binding on `height` and `altitude`)

1. **Bridge & Planner Single-Solid Resolution**:
   - `typed_fact_next.py:143–153` allows `solid: str | None = None` on `height` and `altitude` premises.
   - `typed_fact_next_bridge.py:229,240` forwards `solid= _solid_symbol(p.args.get("solid"), solids)`, which returns `None` when omitted.
   - `planner.py:384` (`khoi_cua`) immediately raises `UNKNOWN_SOLID` when `f.solid` is `None`.
   - **Fix**: When `solid` is omitted (`None`), bind deterministically to the unique declared root solid if and only if `len(solids) == 1` (and for `altitude`, verify `apex` belongs to that solid and `foot != apex`). If `len(solids) == 0`, raise `UNKNOWN_SOLID`; if `len(solids) > 1`, raise `AMBIGUOUS_REFERENCE`.
2. **Secondary Role-Value Grammar Blocker (`H010`)**:
   - In `H010` (`"Cho hình chóp tứ giác đều S.ABCD có các cạnh đáy bằng 4, chiều cao của hình chóp bằng 3."`), `_C_VAI` (`registry.py:933`) did not allow plural quantifiers `(?:(?:các|mọi|mỗi)\s+)?` before `cạnh đáy`, causing `_phan_tich_cau` to fail on the sentence and leave `"chiều cao của hình chóp bằng 3"` unbound (`UNGROUNDED_VALUE`).

### 3.3 Phase C — M3 (Source Gate Section Wording & Coplanar 4-Vertex Reference Planes)

1. `_DAN_THIET_DIEN` (`registry.py:3471`):
   - Rejected `"khi (bị )?cắt bởi"`, `"thiết diện tạo bởi <khối> và mặt phẳng (β)"`, and named section polygons `"Xác định thiết diện AMNP (của <khối> ...)"`.
2. `mat_song_song_dung_nguon` (`registry.py:3593–3615`):
   - Only allowed a 3-point `parallel_plane` (`q`) to match a 4-point source plane (`tap`) when `tap == frozenset(day)` (the base). Lateral faces and diagonal planes of a prism (`(BCC'B')`, `(ABB'A')`, `(ACC'A')`, `(BDD'B')`, `(BCD'A')`) were rejected because `typed-fact-next/2` restricts `parallel_plane` to 3 points (`_plane3`) while Vietnamese problems write 4-vertex face/diagonal plane notations.
   - Checked inline section prefixes only inside `qn[:m.start()]` instead of also checking `s[:goc + m.start()]` in the source sentence when `q` starts at `mặt phẳng (α)...`.
3. `_QUA_VUONG_DUONG` / `_DIEM_TRUOC_VUONG_DUONG` (`registry.py:3940–3944`):
   - Only accepted `(?:đường thẳng\s+)?` before the perpendicular line label, rejecting `đường chéo`, `cạnh bên`, `cạnh đáy`, `đoạn thẳng`, `cạnh`.
4. `"Tính theo a diện tích..."` (`registry.py:3100, 3224`):
   - `_GIUA_HOP_LE` and `_kiem_don_vi_hoi` only accepted `theo a` after the asked object phrase, not between the request verb (`Tính`) and the asked object phrase (`diện tích...`).

### 3.4 Phase D — M4 (Compound Premise Coverage)

1. Unlabelled `"đáy"` before `"là"` (`H002`, `H015`, `H019`, `H022`, `H024`, `H041`):
   - In `"Cho hình chóp S.ABC có đáy là tam giác ABC vuông tại A"`, the `right_angle` quote is `"tam giác ABC vuông tại A"`, leaving `"đáy"` outside the quote. `_TEN_DOI_TUONG` required a label immediately after `"đáy"`.
   - Fix: In `_kiem_vung_tien_de`, cover bare `(?:mặt\s+)?đáy(?=\s+là\b)` when `_chu_cua_day(de, pos)` resolves to a declared solid's base and `_vai_tro_doi_tuong_khop("đáy", verts, calls)` holds.
2. `"trùng với"` in `orthogonal_projection` (`H019`, `H022`, `H024`):
   - `construction_source_bound`, `_CUM_DINH_NGHIA_DIEM`, and `_C_CHIEU` only matched `là`, not `trùng với` (`"hình chiếu vuông góc của A' lên mặt phẳng (ABC) trùng với trung điểm H của cạnh AB"`).
3. `"các kích thước"` before segment lengths (`H028`):
   - Add `(?:các\s+)?kích thước` to `_DANH_TU_TRUNG_TINH` and `_C_DOAN` so `"có các kích thước AB = 6, AD = 4, AA' = 2"` is covered only when directly naming segment labels.

### 3.5 Phase E — M5 (Section-Area Question Binding)

1. Bridge & Planner (`typed_fact_next_bridge.py:362`, `planner.py`):
   - `typed_fact_next_bridge.py:362` rejects `measurement(area, target={"section_id": ...})` when `"thiết diện"` is not a literal substring of `g.quote` (`"tính diện tích của nó"`, `"Tính diện tích tam giác MNP"`, `"Tính diện tích tứ giác AEFK"`).
2. Bounded Resolution Design:
   - **Anaphoric (`"diện tích của nó"`)**: Accepted when and only when `g.quote` matches `diện tích\s+của\s+nó`, there is a unique derived section in the problem, and the same sentence (or immediately preceding sentence) defines/requests that section without any competing area-bearing noun phrase (`tam giác`, `tứ giác`, `hình vuông`, `hình chữ nhật`, `đáy`, `mặt bên`) between the section mention and `"diện tích của nó"`.
   - **Named Section Polygon (`"diện tích (tam giác|tứ giác|đa giác) <POLY>"`)**: Accepted when `<POLY>` has 3 or 4 vertices matching its shape noun (`tam giác` = 3, `tứ giác` = 4) and `set(<POLY>)` equals the grounded section vertex set `{through_point, *stated_cut_points}` (or the named section polygon in `Xác định thiết diện <POLY>`).

### 3.6 Phase F — R2 (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`)

- In `function_route.py:398–405`, `aux_ids` only checked `d.get("label")` (single-point rules), omitting `d.get("labels")` and `d.get("feet")` from `MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`, and `DINH_CAT_CANH`.
- In `_vai_mat_cat` (`function_route.py:132–223`), internal plane-construction auxiliary points (`H, H1..H4`) keep `notation = "H"` / `"H1"` on non-coincident `point3` objects and appear in `translate_point` / `orthogonal_projection_line` event/step narrations as required by the locked `pedagogical-construction-sequencing` O4 (`construction_sequencing.py`) and `scene3d-section-inspector-c0` R1 (`test_section_display_identity.py`) contracts.
- **Disposition (`R2_AUXILIARY_POINT_NOTATION_DEFERRED`)**:
  - Per Section 0 (*"if it can be implemented safely"*), Section 8 (*"If this correction requires a broad frontend/Scene3D contract redesign, STOP and request a separate Owner decision"*), and Section 9 (*"No regression suite may be weakened"*), hiding `point3.notation` on non-coincident auxiliary points is recorded as **`R2_AUXILIARY_POINT_NOTATION_DEFERRED`** (`backend/app/ai/function_route.py` remains byte-identical to baseline `129c1a952393808bfcdb6ecb48677c09b2ed6293`), preserving all existing O4, R1, and coincident-point (`_an_dinh_thiet_dien_phu`) contracts.
