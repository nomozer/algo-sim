# Scene3D Integration & Multi-Plan Switching Report (`AXO CONSTRUCTION /2`)

## 1. Sửa lỗi bảo toàn khối khi cắt gọn chứng minh (Bắt trước holdout trên `E04`)

- Ở `/1`, `prune_to_goal_closure` cắt bớt các đỉnh/mặt của khối đa diện nếu không tham gia trực tiếp vào bao đóng mục tiêu (`E04`: chỉ giữ `A, B, B', C'` của khối lập phương `ABCD.A'B'C'D'`). Khi biên dịch sang `Scene3D`, các đỉnh còn lại (`A', C, D, D'`) và `solid_main` bị thiếu, làm vi phạm bất biến *"đối tượng giả thiết không biến mất khi chuyển phương án"*.
- `/2` đã sửa `compile_proof_graph_to_scene3d` (`scene3d_bridge.py` trước khi đóng băng holdout): luôn nạp đầy đủ `frame.points` và `frame.polyhedron` (`solid_main`) ở bước khởi tạo `pstep_0` bất kể tập con chứng minh nào được dùng.

## 2. Kết quả kiểm chứng 7 bất biến chuyển phương án Scene3D ([presentation_validator.py](../../../backend/experimental/construction_planner/presentation_validator.py))

Kiểm tra qua `validate_multiplan_switching` trên toàn bộ **`5/5` ca Group E (`E01`–`E05`)**:
1. Mọi phương án có `answers` đồng nhất (`len(answers) == 1`).
2. Tập thực thể giả thiết lõi (`frame.points` + `solid_main`) giữ nguyên không biến mất khi chuyển phương án (`5/5 PASS`).
3. `chart_metric` đồng nhất qua mọi phương án.
4. Không có tham chiếu treo giữa các bước `formation.steps` (`visible_ids`, `highlighted_ids` đều nằm trong `scene_ids` của đúng phương án đó).
5. `source_proof_graph_id` tách biệt cho từng phương án (không ghi đè chéo dữ liệu).
6. Mỗi phương án đạt `validate_presentation_step_graph` (`6` bất biến sư phạm/chứng cứ).
7. Mỗi phương án đều vượt `L0`–`L4` `verify_full_proof_and_scene(..., strict_node_replay=True)` bao gồm kiểm tra `certificates.verify_perpendicular_witness`.

## 3. Handoff Frontend (`Gate F8 = PASS_ARTIFACT_ONLY`)

- Worktree `frontend/` nằm dưới `axo-geometry-library` (`BLOCKED_OWNERSHIP`), `0` dòng bị sửa đổi.
- Xuất patch [frontend_scene3d_multiplan_switcher.patch](handoff/frontend_scene3d_multiplan_switcher.patch) (`1,819 B`) bổ sung prop `alternativePlans` và state `activePlanRank` tự cô lập trong `Scene3DExplorer.tsx`.
- **`git apply --check` PASS (`exit code 0`)**.
