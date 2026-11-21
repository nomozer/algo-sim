# CONSTRUCTION OWNER HANDOFF (`AXO CONSTRUCTION /1`)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Scope Rule Respected:** `0` file trong `backend/app/**` và `0` file trong `frontend/**` bị sửa trong chiến dịch này. Mọi thay đổi đề xuất dưới đây cần được chủ sở hữu tương ứng tiếp nhận trong chiến dịch riêng.

---

## 1. Handoff cho Chủ sở hữu `Registry /33`, `Planner /26` & `SemanticProgram` (`backend/app/simulation/**`)

| Hạng mục | Bằng chứng đo đạc trong `/1` | Đề xuất thay đổi có kiểm soát |
| --- | --- | --- |
| **1. Tách truy vấn metric khỏi phép dựng chứng nhân** | Trong `Adapter /4`, `ask_distance_point_plane` trả `a√2/2` nhưng `scene3d.objects` chứa `0` điểm phụ (`has_auxiliary_foot_point = false`); Baseline A đạt `0/33` ca có witness trong `Scene3D` | Bắt buộc hoặc mở chế độ dựng witness cho `ask_distance_point_plane`, `ask_distance_line_plane`, `ask_distance_lines`, `ask_angle_plane_plane`, `ask_volume`, tái sử dụng hợp đồng đã chứng minh tại `construction_operators.py` |
| **2. Bổ sung `PlanningContract` còn thiếu trong `Registry /33`** | Kiểm toán trực tiếp thấy `49/64` hàm không có `PlanningContract`, gồm `divide_segment`, `point_reflection`, `ask_angle_plane_plane`, `ask_volume`, `ask_section_area` | Gắn `PlanningContract` đầy đủ hoặc tích hợp lớp `construction-operator/1` vào tầng lập kế hoạch |
| **3. Khắc phục từ chối `UNDERDETERMINED_POINT` trên `segment_ratio`** | `B01`, `B06` bị Baseline A từ chối `UNDERDETERMINED_POINT`, còn Candidate B tổ hợp thành công `op.divide_segment_ratio` đạt `a√21/2` và `a√10/10` | Nối sự kiện `segment_ratio` sang constructor `divide_segment` trong `planner.py` |
| **4. Chặn đường cong suy biến trùng điểm ở metric query** | `D02` (đoạn `AA` trùng điểm) được Baseline A trả `SERVED 0a` thay vì từ chối suy biến | Kiểm tra `distinct_points` sớm ở tầng `planner.py` / `registry.py` cho `ask_length` khi 2 đầu mút trùng nhãn |
| **5. Nâng trần bộ nhớ IR (`MAX_MEMORY_DECLARATIONS = 32`)** | `B09` (chuỗi 19 bước dựng trên lập phương) thất bại `IR_MEMORY_BUDGET_EXCEEDED` trên `Baseline A` tại [validator.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/semantic_program/validator.py#L143), trong khi Dynamic Planner giải trong `26.2 ms` | Mở rộng có kiểm soát hoặc dùng graph-scoped IR allocation cho chuỗi dài trên `SemanticProgramSpec` |
| **6. Hỗ trợ đa phương án thay thế & tách đồ thị chứng minh** | `_EffectResolver._resolve` thu gọn greedy về 1 nhánh (`min(choices)`); chưa tách `ConstructionProofGraph` vs `PresentationStepGraph` | Giữ danh sách phương án đạt chứng chỉ và xuất đồ thị 2 tầng cho Adapter `/4` |

---

## 2. Handoff cho Chủ sở hữu Frontend (`frontend/` — worktree `axo-geometry-library`)

- **`Scene3DExplorer.tsx`:** Thêm bộ chuyển phương án (`Plan #1`, `Plan #2`, …), phân biệt trực quan `AUXILIARY_CONSTRUCTION` với `GIVEN_OBJECT`, và hiển thị bước suy luận `ESTABLISH_RELATION` từ `explanation_evidence` đã chứng minh ở backend (`SCENE3D_COMPATIBILITY_REPORT.md` §3).
