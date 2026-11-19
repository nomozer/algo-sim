# Proof Integrity Audit (`AXO CONSTRUCTION /2`)

## 1. Các lỗ hổng đã phát hiện ở `construction-exact-verifier/1`

Qua kiểm toán mã nguồn và kiểm thử tấn công bằng đột biến (*mutation audit* — `audit_proof_integrity_and_invariance_v2.py`), verifier `/1` có 4 điểm yếu thực sự khiến nhiều đồ thị giả mạo vẫn vượt qua khi `strict_node_replay=False`:

1. **Không tái thực thi toán tử đại số ở `L2`:** `/1` chỉ kiểm tra `node.verification_status == "VERIFIED"` và `bool(node.verification_evidence)` thay vì gọi lại `execute_operator(op_id, inputs_exact, params, chart_metric)` để đối chiếu tọa độ đầu ra và bằng chứng từng bit JSON.
2. **Không tái đánh giá độc lập `L3` trên bao đóng phụ thuộc ngược:** `/1` chỉ kiểm cờ `witness_verified` có sẵn trên nút `GOAL`, do đó không phát hiện nút `GOAL` bị làm giả đáp số hoặc bỏ qua bước dựng hỗ trợ.
3. **Mất khóa chứng nhân `seg_C_A` trên `A07_angle_sc_base_square`:** Trong `/1`, `_resolve_angle_line_plane` không đưa `proj_seg_k` vào `witness_keys`, khiến `prune_to_goal_closure` cắt nhầm đoạn hình chiếu `seg_C_A`. Đã sửa triệt để trong `construction_operators.py` (`witness_keys` giữ đủ `proj_seg_k` và `proj_ln_k`).
4. **Lỗi gọi `certificates.verify_perpendicular_witness` ở `L4` (bắt được trước holdout qua `M11`):** Hàm sản phẩm `certificates.verify_perpendicular_witness(witness, canh, chart_metric, segment_obj=o)` trả về tuple `(ok: bool, code: str)` và kỳ vọng cả `scene3d`, KHÔNG ném `CertificateError`. Mã ban đầu truyền `pts_scene` và bỏ qua giá trị trả về khiến chứng nhân Scene3D bị sửa giả không bị phát hiện. Đã sửa trực tiếp trong `construction_verifier.py` trước khi khóa `CANDIDATE_V2_FREEZE_SHA256 = 26c9b505...`.

## 2. Kết quả kiểm thử 12 kịch bản đột biến ([PROOF_MUTATION_TEST_RESULTS.json](PROOF_MUTATION_TEST_RESULTS.json))

Tất cả **12/12** kịch bản tấn công (10 lớp đột biến chứng minh §7 + 1 đột biến `Scene3D.perpendicular_witness` + 1 rò rỉ/đối tượng ma ở `PresentationStepGraph`) đều bị chặn **100%** bởi `construction-exact-verifier/2` + `presentation-step-validator/1`, trong đó **11/12 ca đã lọt qua verifier `/1`**:

| Mã đột biến | Lớp tấn công | `/1` (`strict=False`) | `/2` (`strict=True`) | Tầng chặn `/2` & mã lỗi |
| --- | --- | --- | --- | --- |
| `M01_delete_supporting_node` | Xóa nút chiếu & nối tắt `dependency_ids` về `GIVEN` | `PASSED (BYPASS!)` | **`REJECTED`** | `L2` (`MISSING_PRECONDITION`) |
| `M02_mutate_input_object_ids` | Tráo điểm đầu vào `A -> B` trên `project_point_to_plane` | `PASSED (BYPASS!)` | **`REJECTED`** | `L2` (`DEGENERATE_POINT_ALREADY_INCIDENT`) |
| `M03_reverse_projection_arguments` | Đảo vị trí `point` và `plane` | `PASSED (BYPASS!)` | **`REJECTED`** | `L2` (`UNVERIFIED_CONSTRUCTION`, 0 crash) |
| `M04_perturb_foot_coordinates` | Dịch tọa độ chân `H_A` thêm `(+1/5,0,0)` & cập nhật giả cả `canonical_geom_key` | `PASSED (BYPASS!)` | **`REJECTED`** | `L2` (`UNVERIFIED_CONSTRUCTION`) |
| `M05_replace_perp_with_parallel_evidence` | Đổi chứng chỉ vuông góc thành `"parallel"` giả | `PASSED (BYPASS!)` | **`REJECTED`** | `L2` (`UNVERIFIED_CONSTRUCTION`) |
| `M06_tamper_chart_metric` | Sửa `chart_metric` đồ thị thành `2*I` | `PASSED (BYPASS!)` | **`REJECTED`** | `L1` (`METRIC_MISMATCH`) |
| `M07_tamper_goal_cos_sq_on_verified_node` | Sửa đáp số `GOAL` `cos²=3/7 -> 99/100` trên `E05` | `PASSED (BYPASS!)` | **`REJECTED`** | `L3` (`UNVERIFIED_CONSTRUCTION`) |
| `M08_inject_future_cycle_dependency` | Cho nút trước phụ thuộc nút `GOAL` (tạo chu trình) | `REJECTED` | **`REJECTED`** | `L0` (`CYCLIC_DEPENDENCY`) |
| `M09_forged_evidence_with_verified_flag` | Ghi `{'forged_certificate': True}` kèm cờ `VERIFIED` | `PASSED (BYPASS!)` | **`REJECTED`** | `L2` (`UNVERIFIED_CONSTRUCTION`) |
| `M10_corrupt_intermediate_preserve_final_answer` | Làm hỏng tọa độ điểm `K` trung gian, giữ nguyên đáp số cuối | `PASSED (BYPASS!)` | **`REJECTED`** | `L2` (`UNVERIFIED_CONSTRUCTION`) |
| `M11_scene3d_perpendicular_witness_tamper` | Sửa `from`/`foot`/`plane_directions` trong `Scene3D.perpendicular_witness` | `PASSED (BYPASS!)` | **`REJECTED`** | `L4` (`SCENE3D_CONTINUITY_FAILED`) |
| `M12_presentation_leak_and_phantom_object` | Chèn đối tượng ma & token `op.`/`VERIFIED`/`n_step_` vào `learner_text` | `PASSED (BYPASS!)` | **`REJECTED`** | `Presentation Validator` (`PRESENTATION_INVARIANT_FAILED`) |

## 3. Kiểm chứng 9 bất biến hình học ([GEOMETRY_INVARIANCE_RESULTS.json](GEOMETRY_INVARIANCE_RESULTS.json))

Cả **9/9** phép biến đổi hình học trên nhiều họ khối đa diện khác nhau đều giữ nguyên đáp số chính xác, đạt `L0`–`L4 PASS`, **và giữ đẳng cấu cấu trúc DAG chứng minh (`graph_structural_isomorphism_signature` trùng khớp 100%)**:
1. Đổi tên đỉnh (`A,B,C,S -> P,Q,R,T` trên `C01`): `a√21/7` = `a√21/7`
2. Hoán vị thứ tự tiền đề độc lập (`B01`): `a√21/2` = `a√21/2`
3. Tịnh tiến vector hữu tỉ `(7/3, -11/5, 4)` (`C01`): `a√21/7` = `a√21/7`
4. Phép quay trực giao hữu tỉ `SO(3, Q)` ma trận 3-4-5 (`C04`): `a√3/3` = `a√3/3`
5. Biến đổi hệ cơ sở tổng quát `GL(3, Q)` kèm hiệp biến tensor metric $G' = A^{-T} G A^{-1}$ trên lăng trụ xiên không chéo: `a` = `a` (`chart_metric` biến đổi từ `((1,1/2,0),(1/2,1,0),(0,0,1))` sang `((1,0,0),(0,3/16,-1/24),(0,-1/24,49/108))`, chữ ký DAG khớp 100%)
6. Phép đối xứng gương `diag(-1, 1, 1)` (`C01`): `a√21/7` = `a√21/7`
7. Phóng đại thuần nhất hệ số `3` (`C01`): `3√21a/7 == 3a√21/7`
8. Biểu diễn đường thẳng tương đương (`point + dir`, `-dir` trên `C04`): `a√3/3` = `a√3/3`
9. Biểu diễn mặt phẳng tương đương (nhân pháp tuyến với `-3/2` trên `C01`): `a√21/7` = `a√21/7`
