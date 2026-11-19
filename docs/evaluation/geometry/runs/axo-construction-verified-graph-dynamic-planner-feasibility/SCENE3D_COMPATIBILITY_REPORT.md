# SCENE3D COMPATIBILITY REPORT (`construction-scene3d-bridge/1` — Phase H)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Gate E6 Verdict:** **`PASS_ARTIFACT_ONLY`** (Frontend `frontend/` nằm dưới quyền sở hữu riêng `axo-geometry-library` -> `BLOCKED_OWNERSHIP`; không sửa frontend).
- **Bridge Module:** [scene3d_bridge.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/experimental/construction_planner/scene3d_bridge.py)
- **Production Validator Reused:** [construction_continuity.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/construction_continuity.py), [certificates.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/geometry_functions/certificates.py)

---

## 1. Đối chiếu hợp đồng Scene3D hiện tại

Kiểm toán trực tiếp [scene3d.py](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/app/simulation/semantic_program/scene3d.py) và [Scene3DExplorer.tsx](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx) xác nhận:
- `Scene3D` gồm `objects`, `events`, `formation.steps`, `chart_metric`, `length_unit`.
- Mọi thực thể hình học giữ tọa độ hữu tỉ chuẩn hóa dạng chuỗi (`["0", "0", "1"]`), trường `origin`, `producer`, `depends`, `computational_depends`, `visible_prerequisites`, cùng `perpendicular_witness` do `certify_line_plane_perpendicularity` cấp cho đoạn đường cao dựng thêm.
- `validate_construction_continuity` cưỡng chế 7 bất biến cộng dồn trên chuỗi `formation.steps` và toàn bộ tập `objects`/`events`.

---

## 2. Chứng cứ End-to-End đã xác minh (`Gold Typed Facts -> Scene3D`)

Trên bài toán **C01** (*Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA ⟂ (ABC), SA = a. Tính khoảng cách từ A đến (SBC)*):

| Phương án | Số nút ProofGraph | Số bước Presentation | Số đối tượng Scene3D | Kết quả & Trạng thái | L4 Continuity Issues | SHA-256 Digest (16 ký tự đầu) |
| --- | --- | --- | --- | --- | --- | --- |
| **Plan #1 (Direct Projection)** | `8` | `3` | `10` (`H_A`, `seg_A_H`, `ln_A_H` + `perpendicular_witness PROVEN`) | `a√21/7` (`GOAL_VERIFIED`) | **`0` (`L4 PASS`)** | `pg: 7f2fb5846705dc69` · `scene: 0a99196d8dd87dde` |
| **Plan #2 (Synthetic 2-Step)** | `15` | `8` | `17` (`M_A`, `seg_A_M`, `pl_SAM_A`, `ln_S_M_A`, `K_alt_A`, `seg_A_K`…) | `a√21/7` (`GOAL_VERIFIED`) | **`0` (`L4 PASS`)** | `pg: 1d575a7eb4e0a361` · `scene: d8a6478eecb78dc4` |

Chuỗi bước trình bày của **Plan #2**:
1. `pstep_0 (INIT_GIVEN)`: Khởi tạo đỉnh, khối `S.ABC`, mặt phẳng `(SBC)`, đường `BC`, `SA`.
2. `pstep_1 (CONSTRUCT_AUXILIARY)`: Hạ `M_A` vuông góc lên `BC` (`op.project_point_to_line`, tạo `M_A`, `seg_A_M`, `ln_A_M`).
3. `pstep_2 (CONSTRUCT_AUXILIARY)`: Nối `SM_A` (`ln_S_M_A`).
4. `pstep_3 (CONSTRUCT_AUXILIARY)`: Xác định mặt phẳng `(SAM_A)` (`pl_SAM_A`).
5. `pstep_4 (CONSTRUCT_AUXILIARY)`: Hạ `K_alt_A` vuông góc lên `SM_A` (`K_alt_A`, `seg_A_K`, `ln_A_K`).
6. `pstep_5 (ESTABLISH_RELATION)`: Chứng minh `BC ⟂ (SAM_A)` theo định lý hai đường cắt nhau.
7. `pstep_6 (ESTABLISH_RELATION)`: Chứng minh `AK_alt_A ⟂ (SBC)` theo định lý hai đường cắt nhau `SM_A` và `BC`.
8. `pstep_7 (MEASURE_GOAL)`: Xác định độ dài chứng nhân `a√21/7`.

Trên toàn bộ **`33/33`** ca dương của benchmark 40 ca, `compile_proof_graph_to_scene3d` tạo `Scene3D` hợp lệ với **`0` lỗi `validate_construction_continuity`**.

---

## 3. Handoff tích hợp Frontend (`BLOCKED_OWNERSHIP`)
Để nâng cấp từ `PASS_ARTIFACT_ONLY` lên `PASS` UI đầy đủ trong một chiến dịch frontend có quyền trên `axo-geometry-library`:
1. Cho phép `Scene3DExplorer.tsx` nhận danh sách phương án thay thế `plans[]` kèm nhãn tóm tắt (`Plan #1: Trực tiếp` vs `Plan #2: Định lý ba đường vuông góc / hình chiếu tuần tự`) để học sinh chuyển đổi.
2. Hiển thị badge riêng biệt cho `AUXILIARY_CONSTRUCTION` (`origin="derived"`, `display_group: ["auxiliary"]`) và lớp highlight `ESTABLISH_RELATION` dựa trên `explanation_evidence.attached_verifications`.
3. Dùng `validate_construction_continuity` làm bước kiểm tra tĩnh đầu vào trên API adapter trước khi giao cho UI.
