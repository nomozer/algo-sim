# Controlled Backend Integration Report (`AXO CONSTRUCTION /2`)

## 1. Trạng thái quyền sở hữu & Ranh giới

- **`INTEGRATION_STATUS = BLOCKED_OWNERSHIP` · `Gate F7 = BLOCKED_OWNERSHIP`**.
- Toàn bộ thư mục sản phẩm `backend/app/**` (gồm `adapter4_route.py`, `main.py`, `planner.py`, `registry.py`, `engine.py`, `scene3d.py`) giữ **`0` chỉnh sửa**. Mọi tích hợp được hiện thực đầy đủ ở tầng cầu nối cô lập (`verified_input_bridge.py`, `integration_adapter.py`) và đóng gói thành patch hợp lệ sẵn sàng bàn giao cho owner.

## 2. Kết quả kiểm chứng Cầu nối & Adapter cô lập

1. **Cầu nối tôn trọng Source Gate (`verified_input_bridge.py`):**
   - Gọi `bridge_v2` (nếu `typed-fact-next/2`) -> `planner.lap_ke_hoach` -> `registry.kiem_nguon` **trước** khi tạo `InitialGeometryFrame`.
   - Kiểm chứng trên `B01`: quote đúng được chấp nhận (`accepted=True`, `source_gate_status="VERIFIED"`); quote bịa không có trong đề (`"trích dẫn giả không tồn tại trong đề"`) bị **từ chối ngay** (`accepted=False`, `source_gate_status="REFUSED"`, `frame=None`) — **`0` bypass Source Gate**.
2. **Kiểm chứng 4 chế độ của `AXO_DYNAMIC_CONSTRUCTION_MODE` (`integration_adapter.py`, kiểm trên `C01`):**
   - `"off"` (mặc định): trả 100% từ `LEGACY_PRODUCT_PIPELINE` (`status="SERVED"`), không chạy Dynamic Planner.
   - `"shadow"`: trả kết quả `LEGACY_PRODUCT_PIPELINE` cho người dùng (`user_impact="NONE"`) đồng thời phát `shadow_receipt` có `dynamic_l0_l4_verified=True`, `dynamic_plans_count >= 2`, `answers_match=True`.
   - `"experimental"`: trả `DYNAMIC_CONSTRUCTION_PLANNER_V2` (`status="SERVED"`) kèm `multiplan_bundle` (`>= 2` phương án tự chứa đã kiểm `validate_multiplan_switching`).
   - `force_experimental_failure=True` (mô phỏng timeout/lỗi động): tự động chuyển an toàn sang `SAFE_VERIFIED_LEGACY_FALLBACK` (`fallback_used=True`, đáp số `"a√21/7"` bảo toàn) vì đường legacy đã xác minh Kernel + Source Gate; nếu cả hai đều không chứng minh được -> `FAIL_CLOSED_REFUSED`.
3. **Bản vá bàn giao Backend ([backend_adapter4_dynamic_construction_flag.patch](handoff/backend_adapter4_dynamic_construction_flag.patch)):**
   - Kích thước `1,183 B`, móc vào `backend/app/ai/adapter4_route.py::run_typed_fact_next_v2_route` sau `FR.chay_sau_cau_noi(b)`.
   - Kiểm tra **`git apply --check` PASS (exit code 0)**.
4. **Tính tương thích với toán tử `Registry /33`:**
   - Trong `23` toán tử của `construction-operator/1`: `16` toán tử dựa trên nền `EXISTS_IN_REGISTRY_33` / tương đương trực tiếp Kernel (`exact.py`, `metric.py`, `measure.py`, `section.py`); `7` toán tử là đặc tả mới hoặc định lý suy diễn cần mở hợp đồng ở `Registry /33` khi tích hợp sản phẩm (`plane_through_point_parallel_plane`, `plane_through_point_perp_line`, `common_perpendicular_skew_lines`, `polyhedron_plane_section`, `construct_dihedral_linear_angle`, cùng 3 toán tử suy diễn quan hệ & `plane_through_line_parallel_line`).
   - Cũng cần gỡ giới hạn cố định `MAX_MEMORY_DECLARATIONS = 32` trong `Planner /26` nếu muốn xử lý chuỗi > 18 bước như `B09` trên đường legacy.
