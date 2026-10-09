# geometry-grounding-safety — kế hoạch và tiền đăng ký

Việc: sửa hai lỗi tính đúng đã xác nhận, không họ hình mới. Cloud, nhánh `fix/geometry-grounding-safety` từ `origin/main`
= `e6c3cf68` (khớp, cây sạch). `LLM_ONLY` mặc định, compiler opt-in, 0 lượt gọi model, frontend không đổi.

## 1. Tái hiện (trước mọi sửa)

- **`ISSUE-ARCH-C0-SHAPE-TEXT-NOT-CHECKED-AGAINST-COORDINATES`** — `diagnostics/probe_c0_shape_text_vs_coordinates.py`
  của run general-polygon-base chạy lại tại `e6c3cf68`: đề nhất quán và đề "hình thang vuông tại C và D" (toạ độ vuông tại A,
  B) đều `served`, `V = 6`, `PROVEN_SAFE` C0. **Nguyên nhân (mã):** `assumption_gate.kiem_gia_dinh`, nhánh C0 — khi mọi literal
  trên lát cắt là `SOURCE_DATUM` thì trả `PROVEN_SAFE` ngay; các `RangBuoc` server đọc từ cùng đề (`_doc_de` → `rb`) chỉ
  được dùng cho C1 (khuôn) và cho quan hệ của mô hình (`_trang_thai_quan_he`), không bao giờ được kiểm trên toạ độ.
- **`ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION`** — `compiler._danh_gia_eligibility_rectangular_pyramid` và
  `_danh_gia_eligibility_cuboid_prism`: `base_shape` trống + MỘT góc vuông ở đáy ⇒ coi là hình chữ nhật (`SUPPORTED`);
  chỉ cổng giả định của route chặn (test LOCAL `test_mot_goc_vuong_khong_phuc_vu_hinh_chu_nhat_tu_gia_dinh`).

## 2. Sửa (đăng ký trước)

1. **C0:** trước khi cấp `PROVEN_SAFE` C0, mọi ràng buộc hình dạng server đọc được mà MỌI thực thể của nó có giá trị
   điểm trong chương trình được kiểm CHÍNH XÁC trên chính các giá trị ấy: `line_perp_line`, `line_perp_plane`,
   `right_triangle`, `base_rectangle`, `base_square` (kèm cạnh), `base_parallelogram`, `base_rhombus`,
   `base_equilateral` (kèm cạnh). Một ràng buộc sai ⇒ `UNDETERMINED`, mã mới `SOURCE_SHAPE_CONTRADICTS_COORDINATES`
   (nguyên nhân `SOURCE`, không gửi đi sửa, lời riêng). Ràng buộc có thực thể không có trong chương trình, hoặc kind
   ngoài danh sách ⇒ bỏ qua (thiếu mô tả KHÔNG phải mâu thuẫn). Độ dài/toạ độ đã có cổng riêng (bất biến nguồn) — không
   đổi. Thứ tự ưu tiên nguồn không đổi; chỉ thêm một phép kiểm trước khi chứng nhận C0.
2. **Compiler:** đáy tứ giác KHÔNG khai `base_shape`/`solid_subkind` là hình chữ nhật chỉ khi đề cho ≥ 3 góc vuông (mỗi
   góc giữa hai cạnh đáy kề); một góc vuông ⇒ `UNSUPPORTED_STRUCTURED_RELATION_MISSING`, mã `BASE_RECTANGLE_NOT_PROVEN`
   (lùi về LLM). Hai góc vuông kề vẫn đi họ G05. Đáy khai hình chữ nhật/vuông, khối khai hộp/lập phương: không đổi.

Cổng giả định không bị tắt hay nới.

## 3. Tiêu chí

`labels.json`: 11 ca C0 (LLM_ONLY, toạ độ) + 7 ca compiler; `oracle.py` kiểm lại quan hệ trên toạ độ và thể tích bằng tích
vô hướng/công thức gõ tay. Không Scene3D, không đáp số khi mâu thuẫn. Hồi quy G04, G05, các ca C0 hiện có (corpus/fixture),
toàn bộ pytest so baseline sạch `e6c3cf68`. `CACHE_VERSION` quyết bằng bằng chứng: lỗi C0 làm một số envelope từng PHỤC VỤ
thành từ chối ⇒ dự kiến bump nếu có hàng phục vụ đổi (kiểm fixture + corpus).
