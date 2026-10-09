# c0-whole-solid-reader — báo cáo

Nhánh `fix/c0-whole-solid-reader` từ `a1350da3` (= `origin/main`, khớp, cây sạch). Cloud, 0 lượt gọi model, `LLM_ONLY`
mặc định, compiler opt-in, frontend không đổi. Tiền đăng ký `3660523` (plan, 27 nhãn C0 với `claims` viết tay, luật tương
đương C1, oracle, probe baseline C0 + C1) trước mọi sửa sản phẩm. Kết luận:
**`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`** — `ISSUE-ARCH-C0-WHOLE-SOLID-CLAIMS-NOT-READ` thu hẹp,
CHƯA RESOLVED (chóp đều không tên).

## 1. Phân tích (`a1350da3`)

| Lối viết | Vì sao bộ đọc bỏ qua | Gắn khối | Xử lý |
|---|---|---|---|
| (1) `hình chóp tứ/tam giác đều có đỉnh S và đáy ABCD` | `_KHOI_CHOP` chỉ nhận ký hiệu `X.Y` | đề gọi tên đỉnh + đáy ⇒ duy nhất | **sửa** |
| (3) `hình chóp đều S.ABCD` | `_KHOI_CHOP` đòi `tứ/tam giác` trước `đều` | ký hiệu ⇒ duy nhất; số đỉnh đáy quyết định loại | **sửa** |
| (2) `hình chóp tứ giác đều` không tên | không có tên đỉnh/đáy | không có căn cứ duy nhất trong đề | **không sửa** (§4) |
| phủ định `không phải (là) hình chóp tứ giác đều S.ABCD` | (lỗi có sẵn) đọc thành tiền đề | — | **sửa**: không phát |

Bên tiêu thụ cùng các kind (`formation`, phát hiện T7/T8, `do_luong_cua`, `construction_binding`, `display_names`,
`neu_khoi_da_dien`, §22) ⇒ tiêu chí: lối viết mới phát ĐÚNG tập ràng buộc của ký hiệu chuẩn (trừ span).

## 2. Sửa — chỉ bộ đọc (`shape_constraint.py`)

`_KHOI_CHOP` nhận `chóp đều X.Y`; `_KHOI_CHOP_DINH_DAY` cho `chóp tứ/tam giác đều có đỉnh (là) X (và|,) (mặt) đáy (là) Y`
(cùng nhóm `dinh`/`day`); `_cac_chop` dùng chung cho `doc_rang_buoc` và `_khoi_cua_du_kien`; khẳng định chóp đều không
phát ngay sau "không phải (là)". Không đổi cổng giả định, route, vùng U3, compiler, khuôn C1, không logic hình học trong
bộ đọc, không tên đỉnh cố định. Hợp đồng từ vựng: amendment §23.

## 3. Kết quả

**C0 (27 nhãn, oracle độc lập 27/27; probe `diagnostics/probe_a1350da3.log` → `probe_candidate.log`):**

| chuyển | số | hàng |
|---|---|---|
| served → refused | 10 | P1_C ×5 (vuông, đổi tên + phân số, tam giác, câu hỏi gọi tên khối, dạng `là … ,`), P3_C ×3 (vuông, tam giác, khối sau toạ độ), M_C ×2 (hai khối) — đều `SOURCE_SHAPE_CONTRADICTS_COORDINATES` |
| refused → served | 1 | N_K_negation_canonical_notation (phủ định không còn là tiền đề; V = 4 đúng oracle) |
| served → served | 16 | 13 nhất quán (V đúng oracle, C0) + mục tiêu/câu hỏi/phủ định + 2 hàng P2 không tên (mâu thuẫn VẪN phục vụ — giới hạn, §4) |
| refused → refused | 0 | |

**C1 (`results/transitions.json`; mỗi lối viết, 47 hàng của hai corpus chóp đều):** ký hiệu chuẩn không đổi (26 phục vụ,
21 từ chối). Viết lại theo (1) hoặc (3) so với `main`: refused → served 24 (giá trị = nhãn ký hiệu chuẩn), served →
refused 1 (`N5_apex_over_vertex`: `main` phục vụ đáp số SAI 3 — nay từ chối như ký hiệu chuẩn), refused → refused 20,
served → served 2. Trên candidate: kết cục (1)/(3) == kết cục chuẩn 94/94, bộ đọc trùng ký hiệu chuẩn. Biến thể không tên
không đổi.

**Kiểm chứng:** `tests/geometry/test_c0_whole_solid_reader.py` 129/129 (red-before trên mã `a1350da3`: 108 đỏ / 21 xanh);
cùng các bộ C0 §21/§22, G04, G05, chóp đều C1, cổng giả định: 737/737; demo 5/5, bề mặt sập 6/6. Toàn bộ pytest (worktree
sạch, cùng máy): `7d55153` 7390 passed / 136 failed / 4 errors; `a1350da3` 7266 / 131 / 4 — 131 + 4 có sẵn trùng hệt; 5 đỏ
mới = danh tính candidate (LOCAL đóng băng lại) — `results/pytest_compare.json`. Compiler không đọc bộ đọc này trực
tiếp; chương trình compiler qua cùng cổng route (trong bộ pytest).

## 4. Chưa xử lý — chóp đều không tên

Dữ kiện không gọi tên đỉnh/đáy ⇒ không gắn (không đoán). Đề nằm ngoài vùng từ chối của route (`neu_khoi_da_dien`, U3)
⇒ cổng chỉ ghi trạng thái. Đo trên hai corpus (`diagnostics/unnamed_gap_a1350da3.json`, không ký hiệu cả ở câu hỏi): 37
đề được phục vụ — 22 đúng nhãn, 4 khác giá trị, 11 lẽ ra phải từ chối. Nới vùng sẽ từ chối cả 22 đề đúng vì C1 chưa có
phép gắn chóp không tên ⇒ cần mở rộng C1 (gắn theo bảng mặt như lăng trụ đứng không tên) + nhãn + quyết định cache riêng:
`ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`. Ngoài ra không đọc: `hình chóp có đỉnh S và đáy ABCD` không
"đều" (không mở rộng C1 chóp thường), `chóp đều` đáy ≠ 3/4 đỉnh.

## 5. Cache · candidate

Bề mặt mô hình KHÔNG đổi. **`CACHE_VERSION` 120 → 121** (`cache/decision.json`): đề phục vụ ở 120 nay bị từ chối (C0 10
hàng; C1 đáp số sai). 49/49 fixture Tier-A trùng byte. Khoá danh tính sinh lại bằng script. Mã sản phẩm đổi ⇒ LOCAL đóng
băng lại candidate (không sửa hash tay). T3 trình duyệt và mô hình thật: không chạy trên Cloud.
