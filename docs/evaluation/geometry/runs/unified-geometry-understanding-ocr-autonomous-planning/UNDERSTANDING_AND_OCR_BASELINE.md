# UNDERSTANDING_AND_OCR_BASELINE — Khảo Sát Nền Hiểu Đề, OCR & Tự Động Tổ Hợp (`unified-geometry-understanding-ocr-autonomous-planning`)

- **Run ID:** `unified-geometry-understanding-ocr-autonomous-planning`
- **Baseline anchor (`start_head`):** `5c1713997540de91d2b6c10fcdbd0d8724aced1c` (`planner-autonomous-composition-and-search-efficiency`, frozen candidate `009c06df1`, `CACHE_VERSION = "142"`, `measured_system = a9e6a372da73497b...`, `120` files)
- **Kiến trúc chuẩn hóa:** `Hybrid /4` tất định (`Local Geometry Parser /2` | `Gemini -> TypedFactNext /2` -> `Source Gate` -> `FactGraph` -> `Planner /26` -> `Registry /33` -> `Exact Kernel /24` -> `Adapter /4` -> `Scene3D`), `ALLOW_LIVE_AI = 0`, **`0` lượt gọi AI live**.

---

## 1. Giới Hạn Hiểu Đề Tiếng Việt & Khớp Nguồn Tại Baseline (`5c1713997`) — Stream A

Kiểm toán tại `5c1713997` cho thấy `Planner /26`, `Registry /33` và `Exact Kernel /24` đã giải được nhiều cấu trúc tổ hợp trên Gold `TypedFactNext /2` (`21/21` `NC-*` Gold, `61/62` `reasoning_matrix`, `13/13` `r1-probe`), nhưng **tầng đọc ngôn ngữ tự nhiên cục bộ + cầu nối ràng buộc mặt cắt (`A4`)** còn nhiều đứt gãy thực chất:

1. **Độ phủ ngôn ngữ tự nhiên trên 21 ca `NC-*` chỉ đạt `4 / 21` (`19.0%`):**
   - `parse_point_or_described` chưa hỗ trợ đệ quy đồng nhất qua `line`, `orthogonal_projection_line`, `intersect_line_plane`, `intersect_line_line` và trung điểm đoạn nối hai điểm mô tả (ví dụ `"giao điểm của đường thẳng nối S với trung điểm của BC và đường thẳng nối B với trung điểm của SC"`, `"hình chiếu vuông góc của trực tâm của tam giác SBD lên đường thẳng nối S với trung điểm của BC"`).
   - Quy tắc `7i` (`m_dist_from`, `m_dist_between`) và `7j` (`m_ang`) dựa vào regex một lượt cứng nhắc cho từng mẫu câu thay vì tách toán tử cấp đỉnh (`_iter_top_splits`) kết hợp `parse_line_or_described` / `parse_plane_or_base` / `parse_point_or_described`. Do đó **`17 / 21`** câu `NC-*` (gồm cả `NC-D2_E1` chứa góc hai đầu mút `@id`) dừng ở `LOCAL_PARSE_PARTIAL -> LIVE_AI_DISABLED`.
   - Ngoài ra `_CUM_HOI` và `_DOI_TUONG_DT_GOC_NGUON` trong `registry.py` thiếu mẫu `"đường thẳng nối X với Y"` khi đi cùng `ask_distance_lines` / `ask_angle_line_plane`.

2. **Nút thắt `A4` — `PlaneConstraintSpec` chứa điểm mô tả (`@id`):**
   - Trong `typed_fact_next.py`, `PlaneConstraintSpec` chặn hoàn toàn `is_described_ref` kể cả trên `kind == "contains_points"` (trả `INVALID_QUALIFIED_REF`).
   - Do đó mọi mặt phẳng cho bởi ràng buộc hỗn hợp đi qua điểm mô tả (như `"Mặt phẳng (P) đi qua A, M và song song với BD"` khi `M` là điểm mô tả ẩn danh, hoặc `"Mặt phẳng (P) đi qua A, B và trung điểm của SC"`) đều bị từ chối ở schema hoặc cầu nối thay vì giữ nguyên ranh giới từ chối chỉ cho ràng buộc hướng (`parallel_to_line`, `perpendicular_to_plane`).

3. **Các lỗ hổng đọc đề phát triển thực tế (`DEV37`, `COMP112`, tách câu, trắc nghiệm):**
   - `DEV37:diagram_benign`: `(tham khảo hình vẽ)` không đi qua `_THAM_KHAO_HINH` trong `registry.py` khiến `_kiem_don_vi_hoi` hoặc parser tưởng ngoặc chứa đơn vị/ràng buộc lạ.
   - `DEV37:sec_do_P_cat`: cụm `"thiết diện do (P) cắt hình chóp"` chưa được `_CAT_BOI_TEN`, `_td_mat_truoc_khoi`, `_cum_goi_khoi`, `mat_cat_dung_nguon` và luật parser `7c-0b`/`7e` nhận diện.
   - `COMP112:dp_unnamed_through_point`: `_PlaneSectionBase.plane_name` mặc định `"α"` khiến `_mat_fact` luôn gán `f["plane_name"] = "α"` ngay cả khi đề viết `"mặt phẳng đi qua trung điểm của SA và song song với mặt đáy"` (không đặt tên mặt phẳng), dẫn tới `SOURCE_OBJECT_MISMATCH`.
   - `7c-0`: mẫu thiết diện 3 điểm chỉ khớp ngoặc `(MNK)`, bỏ sót `"mặt phẳng qua M, N, K"`.
   - Tách câu thiếu dấu chấm trước từ mở câu hỏi viết hoa (ví dụ `"SA = a Tính thể tích..."`) và khối đáp án trắc nghiệm đảo thứ tự (`A. ... B. ... D. ... C. ...`) chưa được xử lý an toàn.

---

## 2. Điểm Nghẽn Độ Tin Cậy OCR Hình Học Tại Baseline — Stream B

Kiểm toán hạ tầng OCR local (`local_ocr.py`, `local_ocr_worker.py`, `ocr_reconcile.py`, `local_ocr_route.py`, `unified_input.py`) tại `5c1713997` xác định **6 điểm nghẽn chính**:

1. **Đẩy nhầm cache ảnh gốc khi đọc lại crop:** `local_ocr.py` dùng chung một LRU `_CACHE` (`max=16`); chỉ một lần gọi `reread_local_ocr_regions` cho ~16+ vùng nghi ngờ đủ đẩy toàn bộ bản ghi OCR toàn trang khỏi cache.
2. **Nhiễu lề từ ký tự hàng xóm trong crop đọc lại (`_reread`):** Cắt vùng nghi ngờ chỉ mở lề thô mà không loại thành phần liên thông (connected component) chạm viền trái/phải nhưng không giao hộp lõi, làm nhiễu chuỗi nhận dạng `tesseract_eng_line` và `rapidocr_latin_rec`.
3. **Thiếu chuẩn đo hình học nét chữ (`_analyze_crop_glyph_topology`):** Khi `rapidocr` đọc được Unicode (`a²`, `a³`, `a√3`, `⊥`, `∥`) còn `tesseract_eng_line` hoặc `rapidocr_latin_rec` làm phẳng thành ASCII (`a2`, `a3`, `av3`, `L`), bộ đối chiếu không có đặc trưng điểm ảnh độc lập để chứng thực:
   - Mũ nhỏ lệch trên-phải (`has_superscript_cc`) phân biệt `a²` với `a2` hay dấu phẩy đi kèm (`a²,`, `4cm²,`);
   - Hai nét chéo tách rời không thanh ngang (`has_radical_stroke`) phân biệt `√` với `4` / `V`;
   - Ngã ba chữ T ngược (`has_perp_t_junction`) phân biệt `⊥` với `L`;
   - Hai vạch thẳng song song (`has_parallel_bars`) phân biệt `∥`;
   - Kiểm tra độ nét/tương phản (`blurry`) để chặn tuyệt đối tự động nhận khi ảnh mờ.
4. **Lượng tử hóa dòng dễ gãy (`round(cy / band)`):** Trong `ocr_reconcile.py`, gán dòng theo lưới cứng `round(cy / band)` dễ tách đôi các từ lệch nhẹ trên cùng một dòng cơ sở hoặc gộp nhầm chỉ số mũ/phân số ở dải phương án trắc nghiệm.
5. **Chặn nhầm góc tù hợp lệ & dính chữ:** `_SHARED_CORRUPTION_RE` chặn cả góc hình học hợp lệ `100°..179°`; các từ dính ngoặc hoặc dấu phẩy không phải thập phân (`phẳng(ABCD)`, `a,BC`) chưa được tách trước khi bỏ phiếu (trong khi `S,ABCD` và `S.A8CD` vẫn phải giữ nguyên cờ lỗi); chấm giữa kiểu `ABCD·A'B'C'D'` chưa được chuẩn hóa về `ABCD.A'B'C'D'`.
6. **Xếp hạng bỏ phiếu ưu tiên nhầm ASCII hỏng hoặc `'` đơn lẻ:** Ký tự nháy `'`/`′` làm tăng điểm ưu tiên một dòng đơn lẻ trước tổ hợp 2 họ, và `av3` hai phiếu đôi khi thắng `a√3` Unicode hợp lệ. Đồng thời `unified_input.py` và `local_ocr_route.py` chưa xuất tường minh trường quyết định ba trạng thái `ocr_decision` (`LOCAL_OCR_ACCEPT`, `LOCAL_OCR_REVIEW_REQUIRED`, `LOCAL_OCR_REJECT_UNREADABLE`).

---

## 3. Khóa An Toàn Phải Bảo Toàn Xuyên Suốt Chiến Dịch

1. Không đưa LLM vào chọn hàm hay sinh mã giải theo từng đề; `Planner /26`, `Registry /33`, `Exact Kernel /24` vẫn hoàn toàn tất định.
2. Giữ nguyên 4 fingerprint bề mặt trích xuất (`function_calling`, `fact_extraction("flat"|"v3")`, `typed_fact_next_surface_fingerprint`) và `NO_PLANNER_HARDCODING`.
3. Giữ nguyên trần ngân sách tìm kiếm/IR (`MAX_EFFECT_DEPTH = 4`, `MAX_EFFECT_CANDIDATES = 48`, `MAX_MEMORY_DECLARATIONS = 32`), `output-policy/1` Chế độ A (`0` rò đáp số ở mục tiêu dựng hình/lượng giác), và chính sách `0` tự động nhận sai (`false auto-accepts == 0`) trên OCR.
