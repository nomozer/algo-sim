# MODEL 2 INTERFACE READINESS (`model2-action-interface/1` — Phase I)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Prototype Module:** [model2_interface.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/model2_interface.py)
- **Needle 3 / Model 2 Implementation Status:** **NOT IMPLEMENTED / ZERO RUNTIME DEPENDENCY** (tuân thủ nghiêm ngặt quy tắc không triển khai, fine-tune hay nạp Needle 3 trong `/1`).

---

## 1. Lược đồ quan sát cho Model 2 (`Model2Observation`)

Từ cặp `(ConstructionProofGraph, PresentationStepGraph)` đã xác minh toàn phần `L0`–`L4` và danh sách `completed_step_ids` hiện tại của phiên trình bày, `build_model2_observation(...)` cung cấp góc nhìn chỉ đọc:

- `requested_goal`: Đặc tả mục tiêu đang yêu cầu.
- `completed_step_ids`: Các bước trình bày đã hoàn tất.
- `available_verified_steps` & `allowed_actions`: Tập bước hợp lệ tiếp theo có **mọi `prerequisite_steps` đều nằm trong `completed_step_ids`**.
- `step_dependencies`: Bản đồ phụ thuộc đầy đủ trên toàn `PresentationStepGraph`.
- `object_references`: Danh sách ID đối tượng đã được xác minh trong đồ thị.
- `valid_transition_constraints`: Quy tắc bất biến chuyển trạng thái.

---

## 2. Ranh giới bảo mật 5 lớp (`validate_model2_action`)

Mọi hành động do Model 2 (tương lai) đề xuất bắt buộc đi qua cổng fail-closed `validate_model2_action(observation, presentation_graph, proposed_payload)`:

| Ràng buộc bảo mật (§17) | Cơ chế chặn trong `model2_interface.py` | Kết quả kiểm chứng trên `C01` |
| --- | --- | --- |
| 1. Không tự tạo giả thiết nguồn (`add_premise`) | Từ chối ngay bất kỳ trường đột biến nào trong `forbidden_fields` | `MODEL2_SECURITY_BOUNDARY_VIOLATION` |
| 2. Không tự tuyên bố quan hệ đúng | Chỉ chọn từ `allowed_actions` chiếu từ `ConstructionProofGraph VERIFIED` | Bị từ chối nếu không thuộc đồ thị |
| 3. Không bỏ qua phụ thuộc | Kiểm tra `step_id` phải có mọi tiền đề trong `completed_step_ids` | Thử nhảy cóc `reveal::pstep_6` tại bước 0 $\Rightarrow$ `MODEL2_DEPENDENCY_VIOLATION` |
| 4. Không gọi operator thiếu điều kiện | Model 2 không gọi trực tiếp operator; mọi bước đã qua `L0`–`L2` ở Planner | Chặn ở kiến trúc tách pha |
| 5. Không đổi kết quả Exact Kernel (`override_answer`, `mutate_coordinates`) | `forbidden_fields` chặn `override_answer`, `mutate_coordinates` | `MODEL2_SECURITY_BOUNDARY_VIOLATION` |

Đề xuất hợp lệ (`reveal::pstep_1` khi `pstep_0` đã xong) trả `Model2ActionDecision(accepted=True, reason_code="ACCEPTED")`.
