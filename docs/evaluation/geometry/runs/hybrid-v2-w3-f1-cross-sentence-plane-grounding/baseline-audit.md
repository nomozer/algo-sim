# Baseline Audit — `HYBRID_V2_W3_F1_CROSS_SENTENCE_PLANE_GROUNDING`

## 1. Authoritative Baseline & Historical Holdout Wave 3 Verification

| Item | Verified Value | Status |
|---|---|---|
| Authoritative `main` / `origin/main` / remote | `e137623c4f674135a8d7884b78614c132eb78085` | `MATCH` |
| Baseline Product Commit | `73ca8d92e74059680ce53b99692af396df37a2f8` | `MATCH` |
| Baseline Full T3 Candidate | `b61f16995dfbe0110a639a2127d0fb5a9c3afde0` | `MATCH` |
| Baseline Product Freeze (`118` files) | `1170ca163529dd40b57f4058826db92a6433359546aa2ad718712f38a538c10d` | `MATCH` |
| Historical Holdout Wave 3 Branch | `research/hybrid-v2-independent-vietnamese-geometry-holdout-wave3` | Preserved untouched |
| Historical Holdout Wave 3 Worktree | `.superpowers/worktrees/independent-section-holdout-wave3` | Clean, untouched |
| Wave 3 Preregistration Commit | `f438a62a3485ce9b8d687cb91102c366e6848960` | Verified |
| Wave 3 Scorer Qualification Commit | `53cba0c8a63ae3cf7c1b058b8b09f07046449f06` | Verified |
| Wave 3 Pre-Execution Freeze Commit | `2332f7ad3d1a73733bbc720bcf36705c67bc2d6b` | Verified |
| Wave 3 Final HEAD | `0943f0ee6bd2a2b297827e39fa7c07054d716ea9` | Verified |
| Baseline Runtime Versions | Registry `geometry-functions/19`, Planner `geometry-fact-planner/17`, Engine `geometry-function-engine/14`, Adapter `hybrid-simulation-adapter/4`, Certificate `plane-section-certificate/1`, `CACHE_VERSION = 130`, `DEFAULT_MODE = LLM_ONLY`, `ALLOW_LIVE_AI = 0` | Verified |

---

## 2. Root-Cause Audit of `W3-F1` in `geometry-functions/19`

In Independent Vietnamese Geometry Holdout Wave 3 (`144` cases: `72` positive, `72` negative), all `24 / 24` positive cases in the `section_and_area` stratum (`18` Category B: `W3-B03, B06, B09, B12, B15, B18, B21, B24, B27, B30, B33, B36, B39, B42, B45, B48, B51, B54`; `6` Category A: `W3-A03, A06, A09, A12, A15, A18`) were refused at `_kiem_phu` (`mat_song_song_dung_nguon` in `backend/app/simulation/geometry_functions/registry.py`) with `SOURCE_OBJECT_MISMATCH`.

Tracing the complete execution path (`bridge_v2` -> `lap_ke_hoach` -> `kiem_nguon`) identifies **four interlocking mechanisms** in `W3-F1`:

### Mechanism 1 — Standalone Plane Definition Sentence Grammar in `registry.py`
When a cutting plane `(P)` / `(R)` is defined in its own premise sentence separate from the compound question sentence:
- In the 16 `perpendicular_line` and `parallel_plane` cases of `W3-F1`, the standalone definition sentence uses the closed Vietnamese coordination `"đồng thời"` (`"Mặt phẳng (P) đi qua H đồng thời vuông góc với cạnh SF"`, `"Mặt phẳng (R) đi qua M đồng thời song song với mặt phẳng (ABC)"`), whereas `_QUA_VUONG_DUONG` (line 4094) and `_QUA_SONG_SONG` (line 3496) only accepted `\s*,?\s*(?:và\s+)?`.
- In the 8 `parallel_two_lines` cases of `W3-F1`, the standalone definition sentence uses `"cả hai đường thẳng"` (`"Mặt phẳng (P) chứa N và song song với cả hai đường thẳng SK, KL"`), whereas `_QUA_HAI_DUONG` (line 4086) only accepted `(?:(?:hai|các)\s+(?:đường thẳng|cạnh)...)`.
- `_CUM_DUNG_MAT_PHU` (line 4119) and `_NOI_TIEN_DE` (line 2397) also lacked the closed sentence introducer `"thiết lập"` (`"Thiết lập mặt phẳng (P)..."`) and `"xét"` / `"kẻ"`.

### Mechanism 2 — Cross-Sentence Plane Reference Resolution When `derived_section.quote` Points to the Question Sentence
When `derived_sections[0].quote` (or `c.quotes` of `section` / `ask_section_area`) points to the **question sentence** (e.g., `"Hãy xác định thiết diện tạo bởi mặt phẳng (P) với hình chóp S.ABCD và tính diện tích thiết diện đó."`) while `(P)` is defined in an earlier sentence of `problem_text` (`de`), `mat_song_song_dung_nguon` previously scanned only `doan` (`c.quotes`) for `cac_mau` (`_QUA_SONG_SONG`, `_QUA_VUONG_DUONG`, `_QUA_HAI_DUONG`) and returned `False` (`SOURCE_OBJECT_MISMATCH`), and `_kiem_vung_tien_de` left the earlier plane-definition sentence in `de[:first_request]` uncovered (`SOURCE_PREMISE_UNREAD`).

### Mechanism 3 — Intermediate Premise Sentences Between Plane Definition and Question (`_kiem_du_kien_cau_hoi`)
In `_kiem_du_kien_cau_hoi` (line 2222 of `registry.py`):
```python
request_contexts |= {_bien_cau(de, vt[0]) for c in calls if c.fn in ("section", "intersection_line") for q in c.quotes
                     if (vt := _vi_tri(de, q)) is not None}
```
When a derived-plane `section` call (`c.id in phu`) carries two quotes `[q_def, q_req]` (the definition sentence and the question sentence) and one or more premise sentences appear **between** `q_def` and `q_req` (for example, when premises are reordered or intermediate point/length sentences sit between the plane definition sentence and the final question sentence), adding `q_def`'s sentence to `request_contexts` pulls `first_request` backward to `q_def`. Line 2227 (`questions |= {_bien_cau(de, p) ... if first_request <= p < len(de)}`) then sweeps all intermediate premise sentences into the question-context loop, causing a false refusal (`QUESTION_CONTEXT_UNSUPPORTED`).

### Mechanism 4 — Consistent `plane_name` Enforcement Across All Three Plane Relations
In `typed_fact_next_bridge.py` (`_mat_fact`, lines 135–140), `plane_name` was previously forwarded to the planner fact only for `parallel_two_lines`, and dropped for `parallel` and `perpendicular`. To prevent cross-plane tampering (e.g., source defines and asks for `(Q)` while payload claims `plane_name = "P"`), `plane_name` (`ten_khai`) must be propagated and checked uniformly across all three plane relations (`MAT_SONG_SONG`, `MAT_VUONG_DUONG`, `MAT_HAI_DUONG`).

---

## 3. Exact Audit of the 24 Historical `W3-F1` Cases in Wave 3

In `kiem_nguon` (`registry.py`), `_kiem_phu` (`_kiem_mat_song_song` / `_kiem_mat_vuong_duong`) executes at line 1988 **before** `_kiem_nguon_dong` (line 2004) and **before** the per-call premise loop (line 2007). Because all 24 `section_and_area` positive cases in Wave 3 failed at line 1988 (`_kiem_phu` -> `SOURCE_OBJECT_MISMATCH`), Wave 3's `report.md` classified all 24 under `W3-F1`.

Auditing the full premise lists of all 24 historical `W3-F1` cases reveals that they partition into:

1. **9 Pure `W3-F1` Cases (`6` Category B + `3` Category A):**
   - Category B (`6` cases): `W3-B03`, `W3-B15`, `W3-B21`, `W3-B33`, `W3-B39`, `W3-B45`
   - Category A (`3` cases): `W3-A03`, `W3-A09`, `W3-A15`
   - All premises in these 9 cases use Registry `/19`-supported premise wording. Repairing `W3-F1` alone transitions all **9 / 9** directly from `FALSE_REFUSAL (SOURCE_OBJECT_MISMATCH)` to `SERVED_CORRECT` with `100%` exact `Fraction` oracle agreement.

2. **15 Compound-Defect Cases (`W3-F1` + Secondary Out-of-Scope Premise Defect in `W3-F2`, `W3-F3`, or `W3-F4`):**
   - **`W3-F1 + W3-F2` (`7` cases: `W3-B06, W3-B12, W3-B24, W3-B30, W3-B42, W3-A06, W3-A12`):** Once `W3-F1` plane grounding passes at line 1988, these 7 cases reach line 2051 and are refused with `PREDICATE_NOT_IN_QUOTE` on `p6` (`divide_segment` using `"thỏa mãn"` or `"Trên đoạn ... chọn điểm ... với"`, which is `W3-F2`).
   - **`W3-F1 + W3-F3` (`6` cases: `W3-B09, W3-B18, W3-B27, W3-B36, W3-B54, W3-A18`):** Once `W3-F1` plane grounding passes at line 1988, these 6 `parallel_two_lines` cases reach line 2004 (`_kiem_nguon_dong`) and are refused with `SOURCE_PREMISE_UNREAD` on their solid/projection/ratio premise sentence (which is `W3-F3`, and also `W3-F2`/`W3-F4` in `B18, B36, B54, A18`).
   - **`W3-F1 + W3-F4` (`2` cases: `W3-B48, W3-B51`):** Once `W3-F1` plane grounding passes at line 1988, these 2 `cube` cases reach line 2089 and are refused with `UNGROUNDED_VALUE` on `p2` (`base_is_square` stating `"với đáy ... là hình vuông cạnh bằng ..."`, which is `W3-F4`, plus `W3-F2` on `p4` in `W3-B48`).

Per Owner GO §4, §6, §8, and §15 (`"Wave này chỉ sửa W3-F1. Không mở rộng sang F2–F5... Nếu không đạt mục tiêu, báo cáo đúng kết quả thực tế và root cause"`):
- We do **not** expand scope to `W3-F2..W3-F5`.
- In `inputs/development.json`, we include both:
  - **Slice A (`historical_w3_f1_verbatim`, 24 cases):** the 24 verbatim Wave 3 `W3-F1` cases (`24/24` fail with `SOURCE_OBJECT_MISMATCH` on baseline; after `W3-F1` repair, `24/24` pass `_kiem_phu` plane grounding, `9/24` are `SERVED_CORRECT` end-to-end, and `15/24` expose their secondary `W3-F2/F3/F4` refusal codes).
  - **Slice B (`w3_f1_isolated_24`, 24 cases):** the same 24 `W3-F1` geometric problems with only the secondary `W3-F2/F3/F4` non-plane premise wording normalized to Registry `/19`-supported wording (`24/24` fail with `SOURCE_OBJECT_MISMATCH` on baseline; **`24/24` (`18/18` Category B, `6/6` Category A) are `SERVED_CORRECT` end-to-end with `100%` exact `Fraction` oracle match after `W3-F1` repair**).
  - **Slice C (`authored_cross_sentence_positive`, 24 cases):** 24 newly authored cross-sentence positive cases covering all required variations from Owner GO §6 (`24/24` `SERVED_CORRECT` with exact `Fraction` oracle match after `W3-F1` repair).
  - **Slice D (`mandatory_negative_tamper`, 20 cases):** all 20 mandatory adversarial/tamper vectors from Owner GO §7 (`20/20` fail-closed with exact expected refusal reason agreement).
