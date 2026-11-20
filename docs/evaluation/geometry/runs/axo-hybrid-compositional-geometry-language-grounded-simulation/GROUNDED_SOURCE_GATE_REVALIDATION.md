# GROUNDED_SOURCE_GATE_REVALIDATION (`/12` P5)

- **Module:** `backend/app/simulation/geometry_functions/registry.py`
- **Registry Contract:** `REGISTRY_VERSION = "geometry-functions/33"` (unchanged)
- **Dependency Guard:** **0 imports from `app.ai`** (verified statically via AST check in `test_v12_compositional_source_gate.py`)

---

## 1. Root Causes Resolved from `/11` Source Gate Rejections

1. **Nested declaration openers + attribute continuations (`_la_khoi_mo_dau_kem_gt`):**
   - Extended post-`_C_KHOI` premise continuations in both `_la_mo_khoi_mo_phong` and `_kiem_vung_tien_de` to admit closed introducers `"đáy"`, `"cạnh"`, `"các cạnh"`, `"mọi cạnh"`, `"mỗi cạnh"`, `"tất cả các cạnh"`, `"chiều cao"`, `"đường cao"`, `"trong đó"`, `"sao cho"`, `"mà"` (fixing `Q08`, `Q10`, `Q12`) alongside `_khop_ky_hieu_khoi` matching both dotted (`S.ABCD`, `ABC.A'B'C'`) and undotted tetrahedron notation (`OABC`, `ABCD`), while still rejecting ungrounded bare object lists (`"Cho mình xem hình chóp S.ABCD và đường thẳng SC"`).
2. **Inline premise + trailing request splitting (`_TACH_MUC_TIEU_NOI_CAU`, `_span_req`, `_prem_cut` in `_kiem_du_kien_cau_hoi`):**
   - Sentences beginning with a valid solid declaration and ending with a single inline goal separator (`"; tính..."`, `", sau đó tính..."`, `" và tính..."`, `", rồi tìm..."`) with zero ask markers in `[cs, cut)` now keep `[cs, cut)` in the premise region checked by `_kiem_vung_tien_de` and route `[req_a, ce)` to `_kiem_du_kien_cau_hoi` (fixing `Q04`, `Q05`, `Q06`, `Q08`, `Q09`, `Q10`, `Q12`, `Q13`, `Q14`), without exempting any trailing modifier or changed condition inside `[req_a, ce)`.
3. **Closed quantifier, ratio point, and polygon premise patterns (`S13`, `S28`, `S11`, `EXAM_EXCL`):**
   - `_phan_tich_cau` orders `("tyso", _TY_SO)` before `("diem", _C_DIEM)`; `_TY_SO` admits optional `gọi|lấy|chọn` + `điểm` prefix (`S28`); `_C_VAI`/`_C_NOI`/`_lien_ket_cau` propagate `tatca` for `"tất cả các cạnh [đều] bằng ..."` (`S13`); `_C_DAGIAC` and `_lien_ket_cau` accept `"có ABCD là hình vuông cạnh 4"` without misclassifying a solid's own base as a subject shift (`S28`); `_VAT_MO_PHONG` (`"hình 3D của"`) and `_DUOI_MO_PHONG` handle 3D show requests (`S11`).
   - Added exclamation/question sentence endings `[.!?;]` to `_C_DCAO`, `_C_DIEM`, `_C_CHIEU`, `_C_MAT`, `_C_MPDN`, `_C_HET`, `_NOI_TIEN_DE`, and `_phan_tich_cau`; updated `_GIAN_DAN` for `"Câu 2 (2 điểm)."` and `_GHI_CHU_TRINH_BAY` for `"Chỉ cần vẽ hình, không cần tính gì thêm!"`; added `regular_tetrahedron` to `rb_khop`.
4. **Solid height ask binder (`Q05`):**
   - Added `"chiều cao"`, `"đường cao"` keywords to `ask_distance_point_plane` and `_chieu_cao_khoi_khop` in `_CUM_HOI["ask_distance_point_plane"]` bound strictly to `_GOI_NGUON.get()`'s declared apex and base (or prism base/top) matching the solid phrase; added `đồng thời`, `bạn hãy` to `_DAN_CAU_HOI`.
5. **Independent diacritic-free Source Gate wrapper (`_kiem_nguon`):**
   - Verifies raw verbatim quotes (`_vi_tri(de, q)`) BEFORE any projection (so fabricated accented quotes on ASCII inputs are rejected immediately with `QUOTE_NOT_IN_SOURCE`).
   - Independently checks geometry structure and blocks out-of-domain/polysemy decoys (`canh quat`, `so duong`, `ket qua dung`, informatics/physics/calculus terms) via `_du_dieu_kien_bu_dau_nguon` before applying span-tracked 1-1 phrase/token projection (`_bu_dau_nguon`, `_anh_xa_quote_nguon`) inside `registry.py` with zero `app.ai` imports.

---

## 2. Verification Summary

- Diagnostic suite (`scratch/diag_gate.py`): `16/16` (`S11, S13, S28, S34, Q04, Q05, Q06, Q08, Q09, Q10, Q12, Q13, Q14, EXAM_EXCL, MUON_XEM, ASCII_OK`) -> `OK`.
- Pytest command:
  `pytest backend/tests/geometry/test_v12_compositional_source_gate.py backend/tests/geometry/test_v12_compositional_clause_analysis.py backend/tests/geometry/test_v12_diacritic_free_domain_gate.py backend/tests/geometry/test_source_gate_clause_role.py backend/tests/geometry/test_hybrid_ask_operand_binding.py backend/tests/geometry/test_hybrid_safety_readiness.py backend/tests/geometry/test_hybrid_offline.py backend/tests/geometry/test_hybrid4_mathematical_reliability.py`
- Result: **369 passed in 28.27s** (0 failures, 0 skipped), including all 7 adversarial counterexample pairs in `test_v12_compositional_source_gate.py`.
