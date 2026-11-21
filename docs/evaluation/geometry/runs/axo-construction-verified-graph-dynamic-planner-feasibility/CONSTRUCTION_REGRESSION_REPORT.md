# CONSTRUCTION REGRESSION & SAFETY REPORT (`AXO CONSTRUCTION /1`)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Verified Base HEAD:** `498f354608c45ce98ba4f75a0222afbe56139ce2` (`feat/local-first-geometry-understanding`)
- **Product Freeze Baseline:** `6310113f2202bc3a4919406b26fad08cb09b38c9` / `9a9352d586caa360f82052ba1b76fe9b4227f26c` (`123` files, `measured_system_sha256 = 113a6a7cf6bbc15a…`, `CACHE_VERSION = 145`, `6233c43c395c9b49…`)
- **Test Module:** [test_verified_construction_graph_and_planner.py](../../../../../../backend/tests/geometry/test_verified_construction_graph_and_planner.py)

---

## 1. Bất biến phạm vi & toàn vẹn bản đóng băng

| Bất biến kiểm tra | Kết quả thực tế | Lệnh xác minh |
| --- | --- | --- |
| Mã sản phẩm đóng băng (`backend/app/**`) | **`0` thay đổi (`123` file khớp hoàn toàn)** | `freeze_evaluation_candidate.py --verify` $\rightarrow$ `113a6a7cf6bbc15a…` |
| Khóa định danh môi trường & cache | **`CACHE_VERSION 145` khớp hoàn toàn** | `lock_cache_identity.py --verify` $\rightarrow$ `6233c43c395c9b49…` |
| Quyền sở hữu Frontend (`frontend/**`) | **`0` thay đổi (`BLOCKED_OWNERSHIP`)** | `git status --short` / `git diff --name-only` |
| Mặc định định tuyến & AI ngoài | `HYBRID_ROUTE_MODE = "live"` giữ nguyên, `ALLOW_LIVE_AI = 0`, `external_ai_calls = 0` | Thiết lập biến môi trường thực thi |
| Chiến dịch đóng băng `/5`–`/8`, `sealed_H1`, `locked_W2_W3`, GGUF | **`0` chỉnh sửa / `0` mở khóa** | Kiểm tra working tree & git diff |

---

## 2. Kết quả bộ kiểm thử 17 hạng mục (§19) & Hồi quy mục tiêu

Thực thi `pytest -c backend/pytest.ini backend/tests/geometry/test_verified_construction_graph_and_planner.py -v` đạt **`16 passed in 3.14s` (`0 failed`)**, bao phủ toàn bộ 17 yêu cầu §19:

| Hạng mục §19 | Hàm kiểm thử | Trạng thái |
| --- | --- | --- |
| 1. Schema 16 trường & phân biệt `GIVEN_OBJECT` / `DERIVED_OBJECT` / `AUXILIARY_CONSTRUCTION` | `test_1_graph_schema_and_provenance` | `PASSED` |
| 2. Định danh chính tắc `canonical_geom_key` bất biến nhãn & phát hiện trùng nút dựng | `test_2_canonical_vs_label_identity_and_duplicates` | `PASSED` |
| 3. Thứ tự topo DAG, truy vết phụ thuộc & cắt tỉa nút thừa theo goal closure | `test_3_dag_validation_unused_pruning_and_trace` | `PASSED` |
| 4. Kiểm tra kiểu toán hạng `L0` trên `construction-operator/1` | `test_4_operator_type_validation_L0` | `PASSED` |
| 5. Từ chối thiếu tiền điều kiện `L1` (`MISSING_PRECONDITION`) | `test_5_missing_precondition_L1` | `PASSED` |
| 6. Phát hiện chu trình phụ thuộc (`CYCLIC_DEPENDENCY`) | `test_6_cyclic_dependency_detection` | `PASSED` |
| 7. Từ chối dữ kiện/độ dài/hình học mâu thuẫn (`CONTRADICTORY_CONSTRAINTS`, `NON_POSITIVE_DIMENSION`) | `test_7_contradictory_constraints` | `PASSED` |
| 8. Từ chối toàn bộ 8 dạng suy biến & vuông góc bất khả thi | `test_8_degenerate_geometry_operators` | `PASSED` |
| 9–10. Dừng an toàn theo ngân sách `max_wall_clock_ms`, `max_expanded_states`, `max_depth`, `max_graph_nodes` | `test_9_10_search_timeout_and_resource_budgets` | `PASSED` |
| 11. Tổ hợp động Case B mới chưa có recipe sẵn | `test_11_dynamic_composition_case_b` | `PASSED` |
| 12. Cưỡng chế chứng nhân hình học trước khi tính goal & hệ lăng trụ xiên Gram SPD | `test_12_exact_witness_required_and_oblique_gram` | `PASSED` |
| 13. Cô lập hoàn toàn đáp án oracle (không truyền đáp án vào planner/frame) | `test_13_oracle_independence` | `PASSED` |
| 14. Chuyển đổi sang `Scene3D`, tuần tự JSON LF-SHA256 & `0` lỗi continuity `L4` | `test_14_scene3d_serialization_and_continuity` | `PASSED` |
| 15. Tính tái lập tất định (`digest` đồ thị và lời giải bit-identical) | `test_15_deterministic_reproducibility` | `PASSED` |
| 16. Thu thập đa phương án thay thế (`>= 2` phương án thực chất trên `C01`) & xếp hạng | `test_16_alternative_plans_and_ranking` | `PASSED` |
| 17. Tương đương Baseline A & ranh giới bảo mật 5 lớp của Model 2 (`model2-action-interface/1`) | `test_17_parity_and_model2_security_boundaries` | `PASSED` |

Chạy gộp với hai bộ test hồi quy `/8` (`test_slm_math_evaluator_v2.py` + `test_scoped_local_routing_policy.py`) đạt **`76 passed in 4.24s`**.

---

## 3. Toàn bộ bộ kiểm thử backend (`pytest -c backend/pytest.ini backend/tests -q`)

- **Kết quả quan sát trực tiếp:** **`15,046 passed, 7 skipped, 3 deselected, 12 xfailed, 1 warning in 777.24s (0:12:57)`** (`exit_code = 0`).
- **Tỷ lệ thất bại:** **`0 failed`** — không làm vỡ bất kỳ hợp đồng Hybrid `/4`, `Source Gate`, `Planner /26`, `Registry /33`, `Exact Kernel /24`, `LocalParser /2`, hay các bộ kiểm thử đánh giá từ `/5`–`/8`.
