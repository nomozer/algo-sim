# PLANNER_IMPLEMENTATION_REPORT — Thiết Kế & Triển Khai Mở Rộng Lập Kế Hoạch Tổ Hợp (`compositional-planner-capability-expansion`)

- **Run ID:** `compositional-planner-capability-expansion`
- **Product commits:**
  - `4f302b06a5cf582f8ed424abaae87aeeb3b0e6a2` (`feat(geometry): expand compositional planner discovery and bridge DAG verification`)
  - `7effb76b86522d091dca6af778afecec8aef247b` (`fix(geometry): guard ask_section_area trailing conjunction and promote R1-F01/F02 in staging verification`)
- **Candidate freeze commit:** `7bf744ec2c8da0c1100b462147e2bf96ef0c0ebf` (`measured_system`: `120` file, SHA-256 `d1c9fb815dbae8a4088d468b7e0c96a185c4e8a294a0c2e8a6880768ebd62a9e`, `CACHE_VERSION = "141"`, `semantic_environment_hash = "6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b"`)

---

## 1. Tổng Quan Kiến Trúc Thay Đổi (Không Phá Hợp Đồng Khóa)

Toàn bộ nâng cấp nằm gọn trong 4 mô-đun cốt lõi (`typed_fact_next_bridge.py`, `planner.py`, `registry.py`, `engine.py`) và giữ nguyên phiên bản hợp đồng (`typed-fact-next/2`, `geometry-fact-planner/26`, `geometry-functions/33`, `geometry-function-engine/24`, `output-policy/1`, `CACHE_VERSION = 141`), không sửa `typed_fact_next.py` và không tăng giới hạn `MAX_MEMORY_DECLARATIONS = 32` hay `MAX_EFFECT_DEPTH = 4`.

### 1.1 Bridge DAG Tổng Quát (`backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`)
1. **Giải phẳng DAG topo sâu tối đa 2 bậc (`_mo_ta_phang`):** Duyệt thứ tự phụ thuộc topo trên `described_points` bất kể loại trong `descriptor_contracts` và `POINT_DEFINITIONS`, bảo toàn cấu trúc `arg_items` và cho phép đầu mút `@id` trong mô tả đường thẳng.
2. **Đa mục tiêu và đường thẳng dẫn xuất (`_cau_hoi_mo_ta`, `_bridge`):** Sinh `goal_trees` cho cả 7 chế độ câu hỏi (`distance_point_line`, `distance_point_plane`, `distance_line_plane`, `length`, `angle_line_plane`, `angle_lines`, `area`), bao gồm đường thẳng dẫn xuất hai đầu mút `@id` (`PA3`, `C3-dist`), độ dài giữa 2 `@id` (`MG5`, `D2`/`R1-F02`), góc giữa 2 đường có `@id`, và diện tích tam giác nhiều `@id`.
3. **Thiết diện 3 điểm & `@orthocenter` (`_ten_mat_khai`, `_bridge`):** Khôi phục `_ten_mat_khai` cho `_la_mat_qua_ba_diem` trả `"".join(_refs(...))` khớp nhãn IR `mp_td_sec`, tự gắn quote mục tiêu `area` cho thiết diện 3 điểm chưa khai báo `construct_plane_section` (`SE3`), và sao chép `"point_tree"` trên mục tiêu `area(section_id)` để không mất cây `@id` bậc 2 khi dựng thiết diện.

### 1.2 Planner Đệ Quy & Tái Sử Dụng Trung Gian (`backend/app/simulation/geometry_functions/planner.py`)
1. **`TypedFact.goal_trees` với `SkipJsonSchema`:** Giữ nguyên byte-exact `TypedFact.model_json_schema()` SHA-256 và nằm trong `INTERNAL_FACT_FIELDS` (từ chối ngay nếu provider tự chèn trường nội bộ).
2. **`_EffectResolver` (`_nut_chung_chi`, `goal_trees`, `_chuoi_trees`):**
   - Hỗ trợ toán hạng `derived_line` (đầu mút mô tả `@id`) trong tìm kiếm lùi `AnswerDistance`, `AnswerDistanceLinePlane`, `AnswerAngleLines`, cùng tái sử dụng điểm trung gian đã dựng giữa các mục tiêu/nhánh con (`reused_intermediates >= 1` trên bài đa mục tiêu và thiết diện qua `@orthocenter` với `reused_intermediates = 3` ở `F3b_orthocenter_section`).
   - Hỗ trợ điểm mô tả/định nghĩa ở bậc lồng qua `_cau_hoi` và `_phan_giai_diem_mat_phu` (`plane_point_chain`), chỉ đọc mô tả và quy tắc từ `Registry` và `POINT_DEFINITIONS` — `0` chuỗi tên hàm/mô tả hardcode (được khóa bởi kiểm tra `NO_PLANNER_HARDCODING` trong `test_compositional_planner_expansion.py`).
3. **Tái sử dụng điểm chia đoạn trong cắt cạnh (`_dinh_cat_canh`):** Khi nguồn đã dựng điểm chia đoạn (`midpoint` / `divide_segment`) nằm đúng trên cạnh cắt thiết diện, planner tái sử dụng thay vì sinh trùng hoặc mâu thuẫn điểm phụ mới.

### 1.3 Source Gate Đệ Quy, `output-policy/1` & Tối Ưu Cold-Start (`backend/app/simulation/geometry_functions/registry.py`)
1. **Xác thực cây mô tả & đường thẳng đệ quy (`_pt_expr_alts`, `_line_core_alts`, `_xac_thuc_nut`, `_cum_mo_ta_long(..., rename_inner=False)`):**
   - Phân tách hai mẫu `"nối ..."` và `"(đi) qua ..."` trong `_line_core_alts` để không bao giờ trùng tên nhóm regex khi đường thẳng có hai đầu mút `@id`.
   - Thêm tham số `rename_inner=False` khi nối mẫu lồng từ `_xac_thuc_nut` nhằm tránh tiền tố kép `in_in_ops` làm trượt chứng chỉ phủ định (`test_family_d1`).
   - Chứng thực đủ 7 chế độ trong `_kiem_result_binding::chain` + chuỗi điểm trên mặt phụ `plane_point_chain` (cả bậc 2 và `@orthocenter`).
2. **Bảo toàn `fe_fp("v3")` và `GOAL_VERIFIER_TARGET`:** Giữ `ask_distance_line_plane.planning` ở trạng thái `provider_offered=False` và `goal=None` (cùng khóa kiểm tra `ans[0].verifier != 'distance_line_plane'` trong `_kiem_result_binding`), đồng thời không đưa `"distance_line_plane"` vào `GOAL_VERIFIER_TARGET`, giữ nguyên toàn bộ `typed_fact_next_surface_fingerprint()`, `function_calling.surface_fingerprint()`, và `fact_extraction.surface_fingerprint("flat" | "v3")`.
3. **Sửa tương tác thiết diện 3 điểm & ghép mệnh đề hỏi (`_CAT_BOI_TEN`, `_mat_ten_diem`, `ask_section_area`, `_kiem_don_vi_hoi`):**
   - Hỗ trợ tên khối có dấu chấm (`S.ABCD`, `ABCD.A'B'C'D'`) trong `_CAT_BOI_TEN`.
   - Thêm lookahead không rỗng `(?=\s+(?:{_TU_KHOI}|{_P1}+\.{_P1}+|{_P1}{{4}})(?![\w']))` sau `(?:của|và|cắt)` ở `ask_section_area` để không ăn mất từ nối `" và"` trước câu hỏi thứ hai trong các đề đa mục tiêu (`cr.cube_section_plus_inscribed_sphere`).
   - Truyền `ask_id=ask.id` vào `_kiem_don_vi_hoi` để bảo toàn Mode A `output-policy/1` (như `ROUND_HALF_UP`) trên cụm câu hỏi `effect-chain` đa mô tả.
4. **Tối ưu thời gian biên dịch regex cold-start (`_GuardedPattern`, `_mau_hoi_dong`, `_DESC_DIEM_PHU_ANON`):** Dùng phân phối hợp nhất regex `nested_desc` (`18 -> 2` mẫu) kết hợp `_GuardedPattern` (guard bằng tiền tố tất yếu rút trực tiếp từ hợp đồng và neo cú pháp của `anon_extra`) và memo hóa `_mau_hoi_dong(base_desc, goals)`, đưa lần phân tích lạnh đầu tiên (`test_local_geometry_parser.py`) từ `4869.6 ms` xuống đạt ngưỡng `< 500.0 ms` (`r1` đạt `PASS`, các lần tiếp theo `11.9–20.8 ms`) mà không thay đổi ngôn ngữ chấp nhận.

### 1.4 Exact Kernel (`backend/app/simulation/geometry_functions/engine.py`)
1. **`_kiem_nut_mo_ta` / `kiem_mo_ta`:** Thẩm định đệ quy mọi nút mô tả trong `operand_trees` (tính đồng nhất hình học `Fraction`, kiểm tra `orthocenter` / `circumcenter` / `centroid` / `orthogonal_projection*` / `intersect*`), không cô lập hàm di sản `AnswerDistance`.
2. **`_kc2_khoang_cach_duong_mat` & `kc2_dich`:** Tính chính xác bình phương khoảng cách giữa đường thẳng dẫn xuất (qua 2 điểm mô tả) và mặt phẳng qua tích có hướng và thước đo Gram chính xác; cập nhật `formation_budget` / `muc_tieu` tương thích đa cây mô tả.

---

## 2. Xác Minh Hồi Quy Trọng Điểm Cho Staging (`export_hybrid_product_integration_corpus.py`)

Do `R1-F01` (`D1`, `'√6/2'`) và `R1-F02` (`D2`, `'√2'`) nay được phục vụ chính xác end-to-end với `Scene3D` đầy đủ qua `/api/analyze`, cấu hình `SIXTEEN_CLASSES` trong `backend/scripts/export_hybrid_product_integration_corpus.py` được cập nhật tiến tới:
- Đưa `R1-F01` và `R1-F02` vào lớp `09_described_points` (`SERVED`, kiểm tra oracle `'√6/2'` và `'√2'`, `Scene3D` liên tục, không rò machine ID).
- Thay `R1-F01` trong lớp `16_unsupported_goals` bằng `R1-F03` (`"điểm đối xứng với A qua C"`, vốn đã có sẵn trong `product-integration-staging-corpus.json` và tiếp tục từ chối fail-closed `capability_gap`).
- Toàn bộ các tệp corpus/replay đóng băng lịch sử (`r1-live-pilot-corpus.json`, `r1-live-pilot-gold-replay-final.jsonl`, `product-integration-staging-corpus.json`, `product-integration-16-classes-verification.json`) được **giữ nguyên từng byte**.
