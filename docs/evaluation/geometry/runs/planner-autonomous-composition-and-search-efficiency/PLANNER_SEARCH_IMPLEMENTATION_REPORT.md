# PLANNER_SEARCH_IMPLEMENTATION_REPORT — Thiết Kế, Tối Ưu Tìm Kiếm & Phân Tích `MG9` (`planner-autonomous-composition-and-search-efficiency`)

- **Run ID:** `planner-autonomous-composition-and-search-efficiency`
- **Product commit:** `8d12e93c4` (`feat(planner): generalize autonomous effect composition, cross-role reuse, and precondition pruning`)
- **Evaluator commit:** `3fa23e481` · **Frozen Candidate:** `009c06df1` (`120` file, `tree_hash = a9e6a372da73497b...`, `CACHE_VERSION = "142"`, `cay_lam_viec_sach = true`, `SEALED = DA_NIEM_PHONG`)

---

## 1. Cải Tiến Tìm Kiếm Tự Động & Tái Sử Dụng (`B1`–`B5`)

Mọi thay đổi giữ nguyên kiến trúc `Hybrid /4` tất định và `0` hardcode bài toán/nhãn/hàm trong `_EffectResolver`:

### 1.1 Mở Rộng Tự Khám Phá Cho `ask_distance_lines` & `intersect_line_line`
- **`registry.py`:**
  - Bổ sung `AnswerDistanceLines` vào `PlanningTerm.kind`, gắn `PlanningContract` cho `ask_distance_lines` (giữ `goal=None`, `provider_offered=True` nên không phá khóa bề mặt trích xuất).
  - Nới mẫu câu `intersect_line_line.planning.phrase` (`(?:hai\s+` -> `(?:(?:hai\s+)?`) để câu mô tả tự nhiên không có từ `"hai"` vẫn lập kế hoạch qua tìm kiếm hiệu ứng được.
- **`typed_fact_next_bridge.py` (`_cau_hoi_mo_ta`):** Khi `goal_type == "distance"` và `keys == {"line1", "line2"}`, tự động hạ cây mục tiêu `mode="distance_lines"` bảo toàn đầu mút mô tả/dẫn xuất ở cả hai đường thẳng.
- **`planner.py` & `engine.py`:** Bổ sung `mode == "distance_lines"` trong `goal_trees`, kiểm tra đầu mút `ask_distance_lines` ở `kiem_mat_cat`, và đánh giá khoảng cách chéo/song song chính xác trên thước đo Gram qua `_kc2_khoang_cach_hai_duong`, `_kc2_duong_hai_duong`, `kc2_dich["distance_lines"]`, `_KIEM_DICH`.

### 1.2 Tái Sử Dụng Anh Em Trong Mục Tiêu & Hậu Kiểm Memo (`B3`, `B4`)
- **`planner.py::_EffectResolver`:**
  - Thêm sổ theo dõi trạng thái đang chờ `_pending` + `_pending_sig()` và bộ thu gom `_collect_pending` (dùng biến cục bộ `eff_ops` để bảo toàn duy nhất biểu thức gốc trong `_emit` theo `test_mutant_is_killed`).
  - Các nhánh anh em giải ở chi phí biên `0` khi trung gian hợp lệ đã nằm trong `_pending` hoặc `self.plan.calls`; `_emit` gộp trùng lời gọi không mới (`fresh`). Nhờ đó trên đoạn thẳng & góc đường thẳng Euler (`T1`, `E1`), số bước phụ giảm từ `10 -> 8`, `reused_intermediates = 2`, loại bỏ hoàn toàn điểm trùng tọa độ `H4`.
  - Tách khóa memo trong `_resolve`: các điểm `"desc"` (`("desc", ...)`) dùng khóa `key` độc lập `_pending_sig()` để giữ `search_depth = 3` trên cây phân rã điểm (bảo toàn `test_family_a2`, `test_family_c2`, `test_section_vii`), trong khi các hiệu ứng locus (`PerpLine`, `PerpDir`, `Foot`) vẫn kèm `_pending_sig()`.

### 1.3 Tái Sử Dụng Xuyên Luật & Kiểm Chứng Nguồn (`B3`, `B4`)
- **`registry.py`:** Mở rộng `chain_quotes` trong `_kiem_result_binding` qua `MAT_VUONG_DUONG`, `MAT_RANG_BUOC`, `DINH_CAT_CANH`; bổ sung `POINT_DEFINITIONS` vào `producer(ref)`; cho phép `x in built_so_far` ở `_check_got`; cập nhật `allowed_foot_quotes` ở `distance(point, line)` (giữ nguyên tương thích `T3`); và mở rộng `_kiem_dinh_cat` (`reuse_through_point`) chấp nhận chân dựng từ `orthogonal_projection_line`, `intersect_line_plane`, `intersect_line_line`.
- **`planner.py`:** Mở rộng `_dinh_cat_canh` (`tren_canh_id`), `_tren_duong` (đầu mút đường dẫn xuất), và `_tren_mat` (điểm mặt phẳng từ `orthogonal_projection` / `intersect_line_plane`) để cắt tỉa và tái sử dụng xuyên mặt cắt (`T4`, `T5`, `DCC`).

### 1.4 Cắt Tỉa Tiên Điều Kiện Trước Bộ Đếm Ngân Sách (`B5`)
- **`planner.py::_EffectResolver._resolve`:** Đảo kiểm tra `self._unmet(contract, env)` **trước** khi tăng `self.candidates += 1`, chỉ tính vào ngân sách tìm kiếm những ứng viên thực sự qua vòng tiên điều kiện và cấu trúc hình học hợp lệ. Nhờ đó giảm mạnh lãng phí ngân sách tìm kiếm mà không nới lỏng bất kỳ cận an toàn nào (`MAX_EFFECT_CANDIDATES = 48`, `MAX_EFFECT_DEPTH = 4`).

---

## 2. Phân Tích Gốc Rễ `MG9` (7 Câu Hỏi Bắt Buộc)

Kiểm tra trực tiếp qua `TB.bridge_v2`, `planner.lap_ke_hoach` và toàn tuyến `run_hybrid_offline` trên `MG9` (bảo toàn trần `MAX_EFFECT_CANDIDATES = 48`, `MAX_MEMORY_DECLARATIONS = 32`):

1. **Planner có lập được kế hoạch cho `MG9` không?** **Có** (`PLAN_SUCCEEDED`). Trước tối ưu hóa, `MG9` thất bại tại Planner với `PLAN_TOO_LARGE` (`54 > 48`) chỉ vì `21` ứng viên bị từ chối tiên điều kiện (`precondition: the point lies on the line`) bị cộng vào `candidates`.
2. **Thông số tìm kiếm thực tế của `MG9` sau B5:**
   - `classification = "REGISTERED_DECOMPOSITION"`
   - `candidate_evaluations = 33` (`<= MAX_EFFECT_CANDIDATES = 48`, giảm từ `54`)
   - `pruned_nodes = 21` (`rejection_reasons = ['precondition: the point lies on the line']`)
   - `explored_states = 72`, `search_depth = 4`, `plan_cost = 13`, `calls = 20` (`13` bước phụ `q1_aux..q3_aux3`)
3. **Toàn tuyến Hybrid `/4` từ chối ở tầng nào?** Ở **tầng kiểm định bộ nhớ IR / Kernel (`route_ir_budget`)**, **không** còn ở tầng Planner.
4. **Mã từ chối chính xác:** `reason_code = "IR_MEMORY_BUDGET_EXCEEDED"` (`status = "REFUSED"`).
5. **Trần `MAX_MEMORY_DECLARATIONS = 32` có bị thay đổi không?** **Không** (`MAX_MEMORY_DECLARATIONS == 32` và `MAX_EFFECT_CANDIDATES == 48` được khóa cứng trong `test_planner_autonomous_composition.py`).
6. **Chênh lệch trước / sau ở `MG9`:** Ứng viên tính ngân sách giảm **`54 -> 33`** (`-38.9%`), nút cắt tỉa hợp lệ **`0 -> 21`**, đưa chẩn đoán từ lỗi sai tầng search (`PLAN_TOO_LARGE`) về ranh giới hợp đồng thực chất (`IR_MEMORY_BUDGET_EXCEEDED`).
7. **Tại sao `MG9` vẫn vượt ngưỡng bộ nhớ IR và quyết định kỹ thuật:** Sau `gop_doi_tuong_trung`, IR biên dịch của `MG9` cần **`34` `memory_declarations`** (`5` đỉnh + `1` khối + `13` điểm + `10` đường thẳng + `2` vectơ + `3` đầu ra float — thậm chí nếu chia sẻ tối đa vẫn cần tối thiểu `33 > 32`). Vì `34 > MAX_MEMORY_DECLARATIONS (32)`, giữ `MG9` fail-closed `IR_MEMORY_BUDGET_EXCEEDED` là quyết định đúng đắn và trung thực theo hợp đồng.
