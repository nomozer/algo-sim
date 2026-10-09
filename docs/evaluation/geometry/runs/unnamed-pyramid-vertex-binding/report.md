# unnamed-pyramid-vertex-binding — báo cáo

Nhánh `fix/unnamed-pyramid-vertex-binding` từ `a7c56942`. Cloud, 0 lượt gọi model, `LLM_ONLY` mặc định, compiler opt-in,
frontend không đổi. Hai pha: nghiên cứu phương án (b) (`9f9e66d`, `07afbd4` ⇒ `ARCHITECTURE_DECISION_REQUIRED`), rồi
**triển khai phương án A** theo quyết định cuối cùng của người dùng. Kết luận:
**`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`**.

## 1. Ba điều phân biệt

1. **Giảm thiểu an toàn đã làm:** mọi chóp đều không tên mà §24 không gắn được (đề gọi tên điểm thiếu toạ độ) nay nằm
   trong vùng từ chối U3 và bị cổng chặn (amendment §25). Không còn đáp số nào được phục vụ cho các đề ấy.
2. **Chưa hỗ trợ (giới hạn năng lực, không phải kết luận toán học):** 5 trong 21 đề do CHÍNH ĐỀ xác định đáp số (S5 √17,
   S7 16, R2_S9 16/3, P9 9/2, P11 3 — `labels.json`, `oracle.py`) bị từ chối theo chính sách A. Không có đề nào trong 21
   được tuyên bố là vô nghiệm.
3. **Hoãn:** phương án B (mô hình tham số chóp đều trong cổng, tiêu chí nghiệm thu sẵn có = `labels.json` + `oracle.py`)
   là nâng cấp năng lực tuỳ chọn.

## 2. Sửa (chỉ lớp vùng từ chối / lý do cổng)

- `shape_constraint.neu_khoi_da_dien`: mọi khẳng định chóp đều không tên `()` thuộc vùng U3.
- `assumption_gate._nhan_khuon`: khẳng định ấy không gắn được ⇒ `TEMPLATE_NOT_MATCHED unnamed regular pyramid: its
  vertices are not fixed by the text` ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN` (mã hiện hành; không phải
  `SOURCE_SHAPE_CONTRADICTS_COORDINATES`). Không parser mới, không kernel, không solver, không `solid_topology`.

## 3. Kết quả (`results/transitions.json`, nhãn chính sách `policy_a_labels.json`)

| nhóm | số | trước (`a7c56942`) → sau |
|---|---|---|
| served → refused | 12 | 9 đúng theo quy ước (5 do đề xác định — giới hạn năng lực; 4 mơ hồ thật — R2_L1, W5_A, R2_S10, R2_S8 — từ chối đúng) + 3 đáp số sai/không căn cứ (N5 SA = 3, R2_N9 16, W5_C 16/3 — sửa lỗi an toàn); tất cả `assumption` / `ASSUMPTION_INVARIANCE_UNPROVEN` |
| refused → refused | 9 | giữ đúng chặng và lý do cũ (source_invariant 5, grounding 3, construction_binding 1) |

21/21 từ chối, khớp nhãn chính sách. Biến thể khác: 3 thay đổi, đều là cùng văn bản với hàng đăng ký (`unnamed` của N5,
S5, P11 — câu hỏi vốn không có ký hiệu khối). 26 hàng gắn được của §24, ký hiệu chuẩn, hai lối viết của run bộ đọc, khối
gọi tên ở câu hỏi: không đổi. Nhãn C0 của ba run trước (29 + 27 + 11 hàng): không đổi.

**Kiểm chứng:** oracle toán học 21/21 (giữ nguyên); `test_unnamed_pyramid_vertex_binding.py` + test của run trước (cập
nhật có chủ đích: hàng `unchanged` nay bị từ chối; hàng C0 không gắn vẫn qua C0) 97/97; bộ đọc + C0 §21–§24 + C1 T7/T8 +
G04 + G05 + cổng giả định trong toàn bộ pytest; không Scene3D qua `run_pipeline`; demo 5/5, bề mặt sập 6/6. Toàn bộ
pytest (worktree sạch, cùng máy): `5669292` 7487 passed / 136 failed / 4 errors; `a7c56942` 7467 / 131 / 4 — 131 + 4 có
sẵn trùng hệt; 5 đỏ mới = danh tính candidate (LOCAL đóng băng) — `results/pytest_compare.json`. 49/49 fixture Tier-A
trùng byte.

## 4. Cache · candidate

Bề mặt mô hình KHÔNG đổi. **`CACHE_VERSION` 122 → 123** (`cache/decision.json`): 12 đề phục vụ ở 122 nay bị từ chối.
Khoá danh tính sinh lại bằng script; ghim test cập nhật. Mã sản phẩm đổi ⇒ LOCAL đóng băng lại candidate (không sửa hash
tay). T3 trình duyệt và mô hình thật: không chạy trên Cloud.
