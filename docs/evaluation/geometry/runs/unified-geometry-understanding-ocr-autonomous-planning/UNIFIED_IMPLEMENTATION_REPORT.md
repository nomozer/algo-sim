# UNIFIED_IMPLEMENTATION_REPORT — Thiết Kế & Triển Khai Hợp Nhất (`unified-geometry-understanding-ocr-autonomous-planning`)

- **Run ID:** `unified-geometry-understanding-ocr-autonomous-planning`
- **Product commits:** `65a393212b68710ba1712f2aff431191127b78aa` (Stream A/B/C & cache `143`), `fff0e63bde0e5be9f6897a1909750b8995fdd310` (Source Gate regex group fix + local parser compound/unit bounds)
- **Evaluated Frozen Candidate:** `dbf61030357c477dc80c90adb3efc1a7342e4f1f` (`measured_system`: `120` file, SHA-256 `9aa3eaa3b5bddab90d3d45f437a8e08ad7517db674755cef3fc88fd9be25e3bf`, `cay_lam_viec_sach = true`, `CACHE_VERSION = "143"`, `ROUTE_D_CACHE_POLICY = "143:route-d"`)

---

## 1. Stream A — Hiểu Đề Hình Học Tiếng Việt Tổ Hợp & Ràng Buộc Mặt Phẳng (`A4`)

### 1.1 Bảo toàn schema trích xuất & mở rộng `A4` (`contains_points` với `@id`)
- **`backend/app/simulation/geometry_functions/typed_fact_next.py`:**
  - Mở rộng `PlaneConstraintSpec` cho phép tham chiếu điểm mô tả `@id` (`is_described_ref`) **chỉ khi `kind == "contains_points"`** và đăng ký vào `described_ref_uses`.
  - Mọi `@id` xuất hiện trong `parallel_to_line` hoặc `perpendicular_to_plane` tiếp tục bị từ chối fail-closed với `INVALID_QUALIFIED_REF`.
  - Giữ nguyên default `plane_name: NonEmptyText = "α"` trên `_PlaneSectionBase`, đảm bảo **`typed_fact_next_surface_fingerprint()` = `33197a45e0620d94...` không đổi 1 bit**.
- **`backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`:**
  - Khi hạ `contains_points`, phân giải các điểm `@id` qua `_mo_ta_cua` vào `"point_items"` để chuyển cây mô tả đệ quy tới Planner (`MAT_RANG_BUOC`); giữ nguyên `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` cho các ràng buộc hướng.
  - Gắn `f["plane_name"]` dựa trên `"plane_name" in sec.model_fields_set` để phân biệt mặt cắt không đặt tên nội dòng (`ten_khai = None`) với mặt đặt tên tường minh (`ten_khai = "P"` hoặc `"α"`).
  - Mở rộng `_v2_plane_def_quotes` cho trích dẫn mặt ràng buộc chứa điểm mô tả.
- **`backend/app/simulation/geometry_functions/planner.py` & `engine.py`:**
  - `planner.py::_mat_rang_buoc` nhận các phần tử `dict` trong `point_items`, giải cây hiệu ứng đệ quy qua `_EffectResolver`, thu gom trung gian và phát `d["point_chains"]`.
  - `engine.py::_bien_dich_mat_cat` xử lý sạch trường hợp mặt cắt 3 điểm `@id` `MAT_RANG_BUOC` có `constructs == []` mà không bỏ sót ràng buộc đồng phẳng.

### 1.2 Nguồn ngữ pháp Source Gate (`registry.py`) & Độ sâu đệ quy
- **`backend/app/simulation/geometry_functions/registry.py`:**
  - Bổ sung `constraint_point_chains` vào `_kiem_result_binding` (hợp nhất `chain_quotes` và xác thực từng chuỗi điểm của `MAT_RANG_BUOC` qua `_xac_thuc_nut`) và viết `_khop_rang_buoc_mo_ta` + cập nhật `_kiem_mat_rang_buoc` để đối chiếu nguyên văn cả điểm đặt tên lẫn điểm `@id` trên đề.
  - Bổ sung mẫu `"đường thẳng nối X với Y"` vào `_doan_cum`, `_doan_nhan`, `_CUM_HOI` (`ask_length`, `ask_distance_lines`, `ask_distance_line_plane`, `ask_angle_line_plane`, `ask_angle_lines`, `ask_length_ratio`) và `_DOI_TUONG_DT_GOC_NGUON`.
  - Mở rộng nhận diện cụm thiết diện `"do (P) cắt ..."` qua `_CAT_BOI_TEN`, `_td_mat_truoc_khoi_pats` / `_td_mat_truoc_khoi` (tách 2 pattern không dùng trùng tên nhóm `(?P<ten>)` trong `mat_song_song_dung_nguon`), `_cum_goi_khoi`, `mat_cat_dung_nguon` và `_doc_phep_dung_cau_hoi` (`m["ten"] or m["ten2"]`, `m["khoi"] or m["khoi2"]`).
  - Cho phép chú thích `((hình )?minh họa|(hình vẽ)|tham khảo hình vẽ)` đi qua `_THAM_KHAO_HINH` và bỏ qua ngoặc tham khảo hình trong `_kiem_don_vi_hoi` (`DEV37:diagram_benign`).

### 1.3 Parser Tiếng Việt đệ quy có giới hạn (`local_geometry_parser.py` & `adaptive_input_router.py`)
- **`strip_mc_options_block` & `split_into_Sentences`:** Cắt khối đáp án trắc nghiệm đảo thứ tự (ví dụ `A. ... B. ... D. ... C. ...`) khi đủ ≥ 2 nhãn A–D và không chứa động từ mệnh đề đề toán; tách câu thông minh khi thiếu dấu chấm trước cụm mở đầu câu hỏi viết hoa (`Khoảng cách`, `Thể tích`, `Diện tích`, `Số đo`, `Góc`, `Tính`, `Tìm`, `Xác định`).
- **Bộ phân tích tổ hợp đệ quy (`depth <= 3` trong parser, `<= 2` ở Kernel):**
  - `parse_plane_or_base`, `parse_line_or_described` (`nối X với Y`, đệ quy qua `@id`), `parse_point_or_described` (thử tách phải-sang-trái với `_snapshot()` / `_restore()` cho `hình chiếu ... lên/trên ...`, `trung điểm đoạn nối X với Y`, `giao điểm đường và (mặt)`, `giao điểm hai đường thẳng`).
  - Quy tắc `6d-0`/`6d` gộp thành một bộ phân tích mặt phẳng ràng buộc hỗ trợ `contains_points` với `@id` (cả dạng 3 điểm lẫn dạng kèm `song song với ...` / `vuông góc với ...`); quy tắc `7c-0` đọc `"qua M, N, K"`; quy tắc `7c-0b`/`7e` đọc `"do (P) cắt"`; quy tắc `7c-0c` dựng mặt cắt không tên nội dòng (`"mặt phẳng đi qua trung điểm của SA và song song với mặt đáy"`, phục vụ `COMP112:dp_unnamed_through_point`).
  - Quy tắc `7h` (`m_len_join`), `7i` (`m_dist_from`, `m_dist_between`) và `7j` (`m_ang`) dùng `_iter_top_splits` với biên `_NEXT_GOAL_LOOKAHEAD` và `_TRAILING_GOAL_META_RE` (`theo đơn vị độ`, `theo x`, ...), nâng độ phủ NL `NC-*` từ **`4 / 21` -> `21 / 21`** và bảo toàn các câu ghép nhiều mục tiêu.

---

## 2. Stream B — OCR Hình Học Tin Cậy & Đối Chiếu Hai Họ (`layout-aware-ocr-reconcile/2`)

1. **Tách đôi cache OCR (`backend/app/ingestion/local_ocr.py`):**
   - Tách `_RAW_OCR_CACHE` (`max = 32`) và `_REREAD_CACHE` (`max = 64`), cập nhật `clear_local_ocr_cache()` xóa cả hai, chấm dứt việc đọc lại nhiều crop nghi ngờ đẩy mất kết quả OCR toàn trang khỏi cache.
2. **Đọc lại vùng cắt sạch lề & đo hình học nét chữ (`backend/app/ingestion/local_ocr_worker.py`):**
   - Trong `_reread`: cắt vùng nghi ngờ với lề bất đối xứng chặt (`pad_x = 3`, `pad_y = 6..7`), `_strip_edge_bleed` xóa các thành phần liên thông (CC) của chữ lân cận chạm biên trái/phải mà không giao vùng lõi, thêm viền trắng `16 px` và phóng `3x` nội suy Lanczos.
   - Trả thêm `tesseract_eng_line_conf`, tùy chọn `tesseract_vie_line` và bản đồ **`glyph_topology`** thuần hình học điểm ảnh qua `_analyze_crop_glyph_topology`:
     - `blurry` (contrast & sharp stroke fraction),
     - `has_superscript_cc` + `superscript_digit_hint` (lọc thành phần chữ cơ sở `h >= max(6, 0.45 * max_cc_h)` để dấu phẩy thấp như trong `a²,`, `4cm²,` không che đường cơ sở chữ `a`/`m`),
     - `has_radical_stroke` (phát hiện hai nét xiên tách rời không có thanh ngang như chữ `4` để phân biệt `√` với `V`/`4`),
     - `has_perp_t_junction` (ngã ba chữ T ngược đáy ngang đối xứng với thân dọc giữa, phân biệt `⊥` với `L`),
     - `has_parallel_bars` (hai cột thẳng song song `∥`).
3. **Nâng cấp đối chiếu `layout-aware-ocr-reconcile/2` (`ocr_reconcile.py`, `local_ocr_route.py`, `unified_input.py`):**
   - Bumped `OCR_RECONCILE_VERSION = "layout-aware-ocr-reconcile/2"`.
   - Mở rộng `_SHARED_CORRUPTION_RE` cho phép góc hình học hợp lệ `100°..179°` trong khi vẫn chặn `>= 180°` (`600°`) và token lỗi `S,ABCD` / `S.A8CD`.
   - Thay `round(cy / band)` bằng gom dòng theo độ chồng lấn dọc `_yoverlap >= 0.35` (`_assign_row_clusters`); nới dung sai phân số xếp chồng dải lựa chọn (`0.65 * med_h`).
   - Chuẩn hóa dấu chấm giữa ký hiệu lăng trụ (`ABCD·A'B'C'D'` -> `ABCD.A'B'C'D'`); bổ sung `_split_glued_words` tách từ dính ngoặc / dấu phẩy không thập phân (`phẳng(ABCD)`, `a,BC`) nhưng vẫn khóa nguyên `S,ABCD` / `S.A8CD`.
   - Sửa xếp hạng bỏ phiếu để ký tự nháy `'`/`′` không thổi phồng hạng đơn-engine thắng 2-engine, và biểu thức Unicode toán học hợp lệ xếp trên ASCII thoái hóa hai phiếu (`av3`).
   - Bổ sung `_verify_base_plus_glyph_topology` (`CROSS_FAMILY_BASE_PLUS_GLYPH_TOPOLOGY`): chỉ tự động nhận (`LOCAL_OCR_ACCEPT`) các ký hiệu `²`, `³`, `√`, `⊥`, `∥` khi ảnh rõ (`not blurry`), `conf >= 82`, họ thứ 2 khớp phần gốc và `glyph_topology` xác thực đúng nét chữ (**`0` false auto-accepts**). Xuất trường tường minh `ocr_decision` (`LOCAL_OCR_ACCEPT`, `LOCAL_OCR_REVIEW_REQUIRED`, `LOCAL_OCR_REJECT_UNREADABLE`).

---

## 3. Stream C — Tính Toàn Vẹn Cache (`CACHE_VERSION = "143"`) & Bảo Toàn Bất Biến

- Nâng `CACHE_VERSION = "143"`, `ROUTE_D_CACHE_POLICY = "143:route-d"` trong `backend/app/main.py`, cập nhật `backend/cache_identity.lock.json` (`semantic_environment_hash = 6233c43c395c9b49...`) và 21 file test khóa phiên bản (bao gồm kiểm chứng thực tế `POST /api/analyze` loại bỏ bản ghi `142:route-d` cũ).
- Giữ nguyên toàn bộ `NO_PLANNER_HARDCODING`, trần bộ nhớ IR `MAX_MEMORY_DECLARATIONS = 32`, `Scene3D` continuity (`0` lỗi), `output-policy/1` Mode A (`0` rò đáp số), và 4 fingerprint bề mặt trích xuất.
