# Presentation Step Validation Report (`AXO CONSTRUCTION /2`)

## 1. Sáu bất biến trình bày & bảo toàn chứng cứ (§18)

Module `presentation_validator.py` (`presentation-step-validator/1`) kiểm tra tự động mọi `PresentationStepGraph` so với `ConstructionProofGraph` nguồn:

1. **Không giới thiệu đối tượng chưa kiểm chứng hoặc vắng mặt khỏi `ProofGraph`:** Mọi `oid` trong `step.object_ids` phải thuộc một nút `VERIFIED` trong `ProofGraph`.
2. **Mọi tham chiếu nút đều tồn tại và đã được kiểm chứng:** `step.construction_graph_refs` không được rỗng và mọi `ref` đều phải có `verification_status == "VERIFIED"`.
3. **Không đảo thứ tự phụ thuộc:** Mọi `req` trong `step.prerequisite_steps` phải đã xuất hiện ở bước có `step_index` nhỏ hơn.
4. **Tách biệt bước đo mục tiêu với bước dựng hình:** Bước `MEASURE_GOAL` bắt buộc liên kết tới nút `node_type == "GOAL"` trong `ProofGraph`.
5. **Giải thích gắn với chứng cứ nút:** Mọi bước sau `INIT_GIVEN` bắt buộc chứa `node_verification` trong `explanation_evidence`.
6. **Chặn rò rỉ token nội bộ ra văn bản học sinh (`learner_text`):** `_friendly_obj_name` và `_friendly_learner_text` trong `construction_graph.py` chuẩn hóa tên hiển thị tự nhiên, và validator từ chối nếu `learner_text` chứa bất kỳ token nội bộ nào trong `("VERIFIED", "UNVERIFIED", "node_id", "schema_version", "n_step_", "n_goal_", "op.")`.

## 2. Kết quả thực nghiệm

- Toàn bộ **`33/33`** ca dương Benchmark `/1` và **`42/42`** ca dương phục vụ trên Holdout `/2` đều đạt **`validate_presentation_step_graph()["valid"] == True`** với `issue_count == 0`.
- Kịch bản tấn công `M12_presentation_leak_and_phantom_object` (tiêm `PHANTOM_POINT_Z` và chuỗi nội bộ `"Thực thi op.project_point_to_plane VERIFIED tại n_step_1"`) bị chặn ngay với `PRESENTATION_INVARIANT_FAILED` (`issue_count = 4`), cũng như được khóa hồi quy ở Category 10 của `test_axo_construction_v2_integrity_and_integration.py`.
