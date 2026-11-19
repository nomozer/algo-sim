# Model 2 Deterministic Baseline Specification (`AXO CONSTRUCTION /2`)

## 1. Mục tiêu & Nguyên tắc Baseline (§19)

Trước khi xem xét bất kỳ mô hình học máy/SLM nào cho vai trò trình bày/hướng dẫn tương tác (`Needle 3` / `Model 2` — bị cấm triển khai trong `/2`), hệ thống phải có một bộ chọn hành động **tất định 100%, không AI** (`DeterministicModel2BaselineSelector`) đóng vai trò mốc đối chuẩn tối thiểu (*baseline floor*) và chứng minh ranh giới hành động hợp lệ (`validate_model2_action`).

## 2. Thiết kế `DeterministicModel2BaselineSelector` (`model2_interface.py`)

- **`DeterministicPresentationState`:** ghi nhận `active_plan_index`, `completed_step_ids`, `highlighted_object_ids`, `shown_explanations` dạng immutable `dataclass(frozen=True)`.
- **Quy tắc chọn hành động (`select_next_action`):**
  1. Nếu người học yêu cầu đổi phương án hợp lệ (`0 <= request_switch_plan < available_plans_count` và khác phương án hiện tại) ⇒ trả hành động `"switch_plan"`.
  2. Nếu người học yêu cầu phát lại bước đã hoàn thành (`request_replay_step_id in observation.completed_step_ids`) ⇒ trả `"replay_step"` kèm đúng `visual_emphasis` và `learner_text` đã kiểm chứng.
  3. Nếu `observation.allowed_actions` rỗng ⇒ trả `{"kind": "complete"}`.
  4. Ngược lại, chọn theo thứ tự topo ưu tiên tất định: `INIT_GIVEN (0) -> CONSTRUCT_DERIVED (1) -> CONSTRUCT_AUXILIARY (2) -> ESTABLISH_RELATION (3) -> MEASURE_GOAL (4)`, kiểm lại bắt buộc qua `validate_model2_action(...)` trước khi phát `"reveal_step"`.
- **Walkthrough đầu-cuối (`run_deterministic_walkthrough`):** duyệt sạch từ `pstep_0` tới bước đo mục tiêu cuối cùng mà **không bao giờ**:
  - mở bước khi chưa xong `prerequisite_steps` (`MODEL2_DEPENDENCY_VIOLATION`),
  - tự bịa hành động ngoài `observation.allowed_actions` (`MODEL2_ACTION_NOT_ALLOWED`),
  - thực hiện thao tác dựng không có `ProofGraph` hậu thuẫn.

## 3. Tiêu chí vượt mốc bắt buộc cho bất kỳ Needle 3 / Model 2 tương lai

Mọi mô hình AI tương tác sau này nếu muốn thay thế `DeterministicModel2BaselineSelector` bắt buộc phải:
1. Đạt **100%** tỷ lệ tuân thủ `validate_model2_action` (0 lỗi phụ thuộc, 0 đối tượng ma, 0 rò rỉ token nội bộ).
2. Chứng minh vượt trội định lượng rõ ràng so với walkthrough topo tất định trên tác vụ sư phạm thực tế (ví dụ: thích ứng câu hỏi ngược dòng của học sinh hoặc giải thích đa phương án có đối chứng), thay vì chỉ tái phát lại chuỗi bước có sẵn.
