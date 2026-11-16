# PLANNER_DISCOVERY_BASELINE — Khảo Sát Năng Lực Tự Khám Phá & Hiệu Năng Tìm Kiếm (`planner-autonomous-composition-and-search-efficiency`)

- **Run ID:** `planner-autonomous-composition-and-search-efficiency`
- **Baseline anchor (`start_head`):** `39b2f3691` (kế thừa từ `compositional-planner-capability-expansion`, candidate `7bf744ec2`, `CACHE_VERSION = "141"`)
- **Kiến trúc khảo sát:** `Hybrid /4` tất định (`Local Geometry Parser /2` / `Gemini -> TypedFactNext /2` -> `bridge_v2` -> `Source Gate` -> `Planner /26` -> `Registry /33` -> `Exact Kernel /24` -> `Adapter /4`), `ALLOW_LIVE_AI = 0`, **`0` lượt gọi AI live**.

---

## 1. Kiểm Toán `_EffectResolver`, `Registry /33`, `Bridge /2` & `Exact Kernel /24` Tại Baseline

Tại `39b2f3691`, `Planner /26` đã vượt qua mốc `61 / 62` trên `reasoning_matrix` nhưng kiểm toán Phase A phát hiện **5 giới hạn cấu trúc thực chất**:

1. **Đánh giá ứng viên trước kiểm tra tiên điều kiện (`MG9` false budget fail):**
   - Trong `planner.py::_EffectResolver._resolve`, bộ đếm ngân sách `self.candidates += 1` đứng **trước** `self._unmet(contract, env)` và kiểm tra ràng buộc cấu trúc (`off_line` / lies-on-plane).
   - Trên `MG9` (`test_hybrid_reasoning_generalization.py::test_g6_three_defined_points_fail_closed_on_the_search_budget`), nhánh tìm kiếm phải thử qua `21` ứng viên không thỏa `precondition` (`the point lies on the line`), khiến bộ đếm cộng lên `54 > MAX_EFFECT_CANDIDATES (48)` và từ chối sớm với `PLAN_TOO_LARGE` **trước** khi chạm giới hạn thực sự của IR/Kernel.

2. **Thiếu `PlanningContract` & đánh giá chính xác cho `ask_distance_lines` với đường thẳng dẫn xuất:**
   - Hàm `ask_distance_lines` trong `Registry /33` có `planning = None`, `TypedFactNextBridge /2` (`_cau_hoi_mo_ta`) chưa hạ mục tiêu `distance` với `keys == {"line1", "line2"}` sang chế độ `distance_lines`, và `engine.py` (`kc2_dich`, `_KIEM_DICH`, `kiem_mat_cat`) chưa hỗ trợ kiểm tra đầu mút và đo khoảng cách chính xác giữa hai đường thẳng dẫn xuất (1 hoặc 2 đường qua `@id`).
   - Song song đó, mẫu quy hoạch của `intersect_line_line` bắt buộc cụm `"hai "` (`(?:hai\s+...`), từ chối các mô tả tự nhiên như `"giao điểm của đường thẳng nối ... và đường thẳng nối ..."`.

3. **Trùng lặp điểm phụ giữa các nhánh anh em trong cùng mục tiêu (`T1` Euler segment & `E1` Euler line angle):**
   - Khi một mục tiêu cần cả `@orthocenter(SBD)` lẫn `@circumcenter(SBD)` trên cùng tam giác không đều `SBD` (`SA = 3`, cạnh đáy `2`), nhánh thứ nhất phát sinh đường vuông góc `PerpLine` nhưng `_EffectResolver` chưa đồng bộ hóa bảng trung gian đang chờ `_pending` giữa các nhánh anh em trước lúc `_emit`.
   - Hệ quả: hệ phát sinh **10** lời gọi phụ (tạo dư một điểm `H4` trùng tọa độ với `H` trên `Scene3D`), thay vì tái sử dụng hai đường vuông góc đã có (`8` lời gọi phụ).

4. **Thiếu chia sẻ trích dẫn xuyên luật & kiểm tra tái sử dụng ở Source Gate (`registry.py`):**
   - `_kiem_result_binding` chưa hợp nhất danh sách `chain_quotes` xuyên qua nhiều luật phụ (`MAT_VUONG_DUONG`, `MAT_RANG_BUOC`, `DINH_CAT_CANH`), và `_check_got` chưa chấp nhận điểm đã dựng sẵn (`x in built_so_far`) khi tái sử dụng lời gọi.
   - `_kiem_dinh_cat` (`reuse_through_point`) chưa chấp nhận điểm đi qua dựng từ `orthogonal_projection_line`, `intersect_line_plane`, hay `intersect_line_line`; `_dinh_cat_canh` (`tren_canh_id`), `_tren_duong`, `_tren_mat` trong `planner.py` cũng chưa đọc đầu mút của đường dẫn xuất hoặc mặt phẳng qua `orthogonal_projection`/`intersect_line_plane`.
   - Ngữ pháp trong `_rang_buoc_nguon` cho `MAT_RANG_BUOC` yêu cầu đủ 2 điểm chứa trong mặt phẳng kết hợp vuông góc (vd. `"Mặt phẳng (P) đi qua A, C và vuông góc với (SBD)"`) và mệnh đề thiết diện tường minh (`"Xác định thiết diện ... và tính diện tích thiết diện đó"`) khi kết hợp với mục tiêu `@orthogonal_projection`.

5. **Memo hóa `_resolve` cần tách biệt khóa cho điểm mô tả `"desc"` vs locus (`PerpLine` / `PerpDir` / `Foot`):**
   - Thử nghiệm `memo_key = (kind, operands, self._pending_sig())` áp chung cho mọi loại làm tăng `search_depth` từ `3` lên `4` trên các nhánh điểm mô tả trùng lặp (`test_family_a2`, `test_family_c2`, `test_section_vii`) do bỏ lỡ `memo` hit trên nút `Point(("desc", ...))`.

---

## 2. Giới Hạn Cần Bảo Toàn Suốt Chiến Dịch

1. Không chuyển sang AI-guided Planner; LLM không được chọn hàm hay sinh chương trình theo từng đề.
2. Giữ nguyên `MAX_EFFECT_DEPTH = 4`, `MAX_EFFECT_NEEDS = 96`, `MAX_EFFECT_CANDIDATES = 48`, `MAX_MEMORY_DECLARATIONS = 32` (không nới trần ngân sách để "qua" `MG9` bằng cách giảm an toàn).
3. Giữ nguyên khóa AST `NO_PLANNER_HARDCODING`, tính duy nhất của chuỗi nguồn kiểm tra đột biến trong `test_hybrid_goal_decomposition.py::test_mutant_is_killed`, 4 fingerprint bề mặt trích xuất (`function_calling`, `fact_extraction("flat"|"v3")`, `typed_fact_next`), và `output-policy/1` Mode A ẩn đáp số.
