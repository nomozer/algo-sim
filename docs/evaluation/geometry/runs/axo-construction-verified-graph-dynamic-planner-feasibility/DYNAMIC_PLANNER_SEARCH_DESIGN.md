# DYNAMIC PLANNER SEARCH DESIGN (`dynamic-construction-planner/1`)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Module Implementation:**
  - [construction_state.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/construction_state.py)
  - [construction_search.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/construction_search.py)
  - [construction_operators.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/construction_operators.py)

---

## 1. Thiết kế tìm kiếm có giới hạn (Phase D, §§8–10)

### 1.1 Khởi tạo trạng thái ban đầu (`build_initial_frame`)
1. Chỉ nạp phần **tiền đề thuần túy** (loại bỏ mọi truy vấn mục tiêu trước khi gọi `engine.dung_tu_loi_goi`) để thu được tọa độ khởi tạo `points: dict[str, Vec3]` và tensor Gram đối xứng xác định dương (`chart_metric: Metric`) đã kiểm định Sylvester.
2. Các phép dựng tường minh khai báo trong đề (`midpoint`, `divide_segment_ratio`, `triangle_centroid`, `point_reflection`, `intersect_line_plane`, `plane_through_point_parallel_plane`, …) không bị tính trước ở tầng khởi tạo mà đưa vào hàng đợi `PendingConstruction` để Dynamic Planner tự mở khóa theo thứ tự phụ thuộc.
3. Hàm `DynamicConstructionPlanner.plan(frame, goal_spec, budget)` **không nhận bất kỳ tham số oracle hay đáp số nào**.

### 1.2 Không gian trạng thái & Chống trùng hoán vị
Mỗi `PlannerSearchState` bất biến lưu: `objects` (kèm `origin` và `canonical_geom_key`), `nodes` (DAG chứng minh tích lũy), `relations` (tập quan hệ đã chứng minh), `key_to_ids`, `pending`, `cost`, `depth`, `aux_count`, `lineage`, `last_node_by_object`, và `relation_node_ids`.

- **`canonical_state_signature`**: Băm SHA-256 trên tập khóa hình học chuẩn hóa (`canonical_geom_key`), tập quan hệ đã chứng minh và tập `pending` còn lại. Hai chuỗi hoán vị các phép dựng độc lập sinh cùng tập hình và quan hệ được gộp tại frontier để tránh bùng nổ tổ hợp $k!$, nhưng hai phương án tạo **các đối tượng phụ hoặc quan hệ chứng minh khác nhau** (như `proj_plane` trực tiếp vs `proj_line -> plane_SAM -> deduce_perp -> proj_line -> deduce_perp`) giữ chữ ký khác nhau và cùng tồn tại.

### 1.3 Thuật toán tìm kiếm & Heuristic cấu trúc
- Dùng **Best-First Dependency-Aware Search** trên hàng đợi ưu tiên `(cost + h(state, goal), depth, seq, state_sig)`:
  1. Khớp các `PendingConstruction` đã đủ đầu vào (mở khóa tuần tự theo thứ tự khai báo khi độc lập).
  2. Khởi tạo các thực thể đích của `GoalSpec` (`plane3`, `line3`, cạnh đa giác) nếu chưa tồn tại.
  3. Sinh ứng viên tổng hợp đối tượng phụ & định lý suy diễn theo loại mục tiêu (`project_point_to_plane`, chuỗi hai bước `project_point_to_line` + `plane_through_three_points` + `deduce_line_perp_plane_two_lines`, `common_perpendicular_skew_lines` vs `plane_through_line_parallel_line` + `project_point_to_plane`, `line_parallel_through_point`, `intersect_planes` + `construct_dihedral_linear_angle`, `deduce_parallel_line_plane_transfer`).
- Mỗi phép chuyển trạng thái chạy kiểm chứng `L0`–`L2` **ngay tại bước đó** (`execute_operator`); nhánh vi phạm tiền điều kiện hoặc suy biến bị loại và ghi nhận ngay vào `pruned_states` / `rejection_reasons`.

### 1.4 Ngân sách tài nguyên (`SearchBudget`) & Trạng thái kết thúc (§9)
Mọi ràng buộc mặc định được kiểm tại mỗi vòng lặp `while frontier`:
- `max_depth = 8` (hiệu dụng `cfg.max_depth + len(frame.pending_constructions)` cho chuỗi giả thiết dài hợp lệ như `B09` dài 19 bước).
- `max_expanded_states = 250`, `max_graph_nodes = 96`, `max_candidate_operators = 600`, `max_wall_clock_ms = 2000.0`, `max_memory_mb = 128.0`, `max_plans = 3`.
- Tập trạng thái kết thúc chuẩn: `GOAL_VERIFIED`, `NO_PLAN_FOUND_WITHIN_BUDGET`, `UNSUPPORTED_OPERATOR`, `MISSING_PRECONDITION`, `CONTRADICTORY_CONSTRAINTS`, `SEARCH_TIMEOUT`, `SEARCH_RESOURCE_LIMIT`, `VERIFICATION_FAILED`.

### 1.5 Thu thập đa phương án & Xếp hạng tất định (§15)
Khi tìm thấy một phương án đạt `GOAL_VERIFIED`, thuật toán cắt tỉa nút thừa (`prune_to_goal_closure`), khử trùng theo chữ ký bản chất (`(sorted_ops_used, sorted_non_quantity_canonical_keys)`), rồi tiếp tục mở frontier trong ngân sách đến tối đa `max_plans` phương án khác biệt thực chất. Xếp hạng tất định theo bộ:
`(cost_tich_luy, so_doi_tuong_phu, do_sau_do_thi, so_buoc_trinh_bay, substantive_sig)`.
