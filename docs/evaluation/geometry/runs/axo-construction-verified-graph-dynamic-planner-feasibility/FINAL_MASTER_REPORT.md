# AXO CONSTRUCTION /1 — VERIFIED CONSTRUCTION GRAPH & DYNAMIC PLANNER FEASIBILITY (FINAL MASTER REPORT)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Branch:** `feat/local-first-geometry-understanding`
- **Base Commit Audited:** `498f354608c45ce98ba4f75a0222afbe56139ce2`
- **Frozen Product Baseline:** `6310113f2202bc3a4919406b26fad08cb09b38c9` (`9a9352d586caa360f82052ba1b76fe9b4227f26c`, `123` files, `measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `CACHE_VERSION = 145`)
- **Classification:** `OFFLINE_CONSTRUCTION_GRAPH_AND_DYNAMIC_PLANNER_PROTOTYPE` (`RESEARCH_PROTOTYPE_NON_PRODUCTION`)
- **Environment Constraints Respected:** `ALLOW_LIVE_AI = 0`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`, `0` fine-tuning, `0` Needle 3 implementation, `0` changes to `backend/app/**` & `frontend/**`, `HYBRID_ROUTE_MODE = "live"` default preserved, not merged, not pushed.
- **Overall Feasibility Verdict:** **`FEASIBLE_IN_ISOLATED_PROTOTYPE_NEEDS_INTEGRATION_WAVE`** (`Gate E6 = PASS_ARTIFACT_ONLY`)

---

## 1. Trả lời thẳng các câu hỏi cốt lõi (§34)

1. **Kiến trúc hiện tại thực sự động tới đâu và còn thiếu gì?**
   - Hệ thống hiện tại (`Planner /26`, `Registry /33`, `Exact Kernel /24`, `Scene3D`) **không hoàn toàn tĩnh** vì đã có `_EffectResolver` (độ sâu tối đa 4 trên `15/64` hàm có `PlanningContract`) và `7` quy tắc `AUXILIARY_RULES`.
   - Tuy nhiên, nó **chưa phải Dynamic Construction Planner**: `49/64` hàm thiếu `PlanningContract`, nhiều `ask_*` tính ra đáp số bằng công thức đại số **nhưng không dựng chứng nhân hình học phụ trong `Scene3D`** (`0/33` ca dương trong đối chiếu có auxiliary witness ở `Scene3D`), không giữ hay xếp hạng đa phương án (`_EffectResolver` luôn lấy `min`), bị giới hạn `MAX_MEMORY_DECLARATIONS = 32` trong IR (`B09` thất bại), không kiểm tra trùng điểm ở metric query `ask_length` (`D02` trả nhầm `0a`), và chưa tách `ConstructionProofGraph` khỏi `PresentationStepGraph`. Chi tiết tại [EXISTING_CONSTRUCTION_ARCHITECTURE_AUDIT.md](EXISTING_CONSTRUCTION_ARCHITECTURE_AUDIT.md).

2. **Verified Construction Graph biểu diễn được gì hơn kiến trúc cũ?**
   - Lược đồ 2 tầng (`verified-construction-graph/1` + `presentation-step-graph/1`) dùng nút 16 trường lưu đầy đủ xuất xứ (`GIVEN_OBJECT`, `DERIVED_OBJECT`, `AUXILIARY_CONSTRUCTION` với `source_fact_refs = []`), định danh hình học chính tắc bất biến nhãn (`canonical_geom_key`), chứng cứ kiểm định `L0`–`L4` theo từng nút, và bản chiếu tách riêng các nút kiểm định nội bộ thành `explanation_evidence`. Chi tiết tại [VERIFIED_CONSTRUCTION_GRAPH_DESIGN.md](VERIFIED_CONSTRUCTION_GRAPH_DESIGN.md).

3. **Dynamic Construction Planner tìm được phương án mới nào mà kiến trúc cũ không có?**
   - Thực nghiệm `40` ca Gold Typed Facts (`Groups A–E`, `seed = 0`) chứng minh **`28` ca `CASE_B_DYNAMIC_COMPOSITION`** được tổ hợp động từ `23` toán tử nguyên tử (`construction-operator/1`) mà không dùng công thức giải sẵn theo đề hay đáp án oracle: gồm hạ vuông góc 2 bước qua chân đáy (`C01`), đoạn vuông góc chung vs mặt phẳng song song cho 2 đường chéo nhau (`C02`, `C03`), dựng tia/mặt vuông góc cho góc nhị diện (`C04`, `E05`), chia đoạn theo tỉ số (`B01`, `B06` vốn bị Baseline A từ chối `UNDERDETERMINED_POINT`), phản xạ/trọng tâm đa bước, thiết diện song song, và chuỗi 19 bước (`B09`, mà Baseline A lỗi `IR_MEMORY_BUDGET_EXCEEDED`). Chi tiết tại [DYNAMIC_COMPOSITION_EVALUATION.json](DYNAMIC_COMPOSITION_EVALUATION.json) và [DYNAMIC_PLANNER_SEARCH_DESIGN.md](DYNAMIC_PLANNER_SEARCH_DESIGN.md).

4. **Các phương án có chứng minh được chính xác bằng Exact Kernel không?**
   - **Có (`33/33` ca dương `PASS L0–L4` + khớp oracle qua `axo-math-evaluator/2`; `7/7` ca âm/suy biến từ chối an toàn).** Mọi quan hệ hình học đều được chứng minh trực tiếp trong không gian phân số chính xác `Fraction` + tensor Gram `Metric` đã qua kiểm định Sylvester SPD tại [construction_verifier.py](../../../../../../backend/experimental/construction_planner/construction_verifier.py), và mọi truy vấn metric đều bị khóa sau cổng kiểm tra sự tồn tại của chứng nhân dựng hình tương ứng (`evaluate_goal_if_witnessed`).

5. **Tác động hiệu năng thế nào?**
   - Trong ngân sách `max_depth = 8` (mở rộng theo số bước tiền đề hợp lệ), `max_expanded_states = 250`, `max_wall_clock_ms = 2000.0`, `max_memory_mb = 128.0`, `max_plans = 3`, thực nghiệm đạt **`0.0` tỷ lệ timeout**, `avg_search_ms = 26.096 ms` (`max = 155.941 ms`), `avg_graph_construction_ms = 9.348 ms`, `avg_exact_verification_ms = 0.431 ms`, `avg_serialization_ms = 1.08 ms`, `avg_expanded_states = 7.7` (`max = 41`), `avg_graph_node_count = 7.875`, `avg_final_plan_length = 2.125`, và đỉnh bộ nhớ chỉ **`335.87 KiB`** (`avg_baseline_a_ms = 105.534 ms`). Chi tiết tại [CONSTRUCTION_PERFORMANCE.json](CONSTRUCTION_PERFORMANCE.json).

6. **Đã sẵn sàng làm nền cho Needle 3 / Model 2 chọn phương án chưa?**
   - **Sẵn sàng ở cấp giao diện chỉ đọc (`model2-action-interface/1` — zero Needle 3 runtime dependency):** cung cấp `Model2Observation` (`available_verified_steps`, `allowed_actions`, `step_dependencies`) và bộ lọc fail-closed 5 lớp `validate_model2_action` chặn mọi cố gắng thêm giả thiết, nhảy cóc phụ thuộc, sửa tọa độ hoặc ghi đè đáp số. Chi tiết tại [MODEL2_INTERFACE_READINESS.md](MODEL2_INTERFACE_READINESS.md).

7. **Đánh đổi, rủi ro và điều kiện để triển khai tiếp?**
   - Các khối tròn xoay / tiếp xúc phương trình bậc cao (`D06`, `Case C`) nằm ngoài miền hữu tỉ $\mathbb{Q}^3$ + căn bậc hai đơn và cần tầng đại số mới trước khi mở rộng operator.
   - `Scene3D` JSON đa phương án đã đạt `0` lỗi continuity (`33/33`, `L4`), nhưng UI chuyển đổi `Plan #1 / Plan #2` trên `frontend/` bị chặn bởi `BLOCKED_OWNERSHIP` (`axo-geometry-library`) nên Gate `E6 = PASS_ARTIFACT_ONLY`.
   - Việc tích hợp vào đường production `Hybrid /4` phải qua chiến dịch riêng được chủ sở hữu `backend/app/simulation/**` và `frontend/` phê duyệt theo [CONSTRUCTION_OWNER_HANDOFF.md](CONSTRUCTION_OWNER_HANDOFF.md).

---

## 2. Bảng tổng hợp kết quả định lượng

| Hạng mục đo kiểm | Kết quả quan sát thực tế | Nguồn chứng cứ |
| --- | --- | --- |
| **40 ca Gold (`Groups A–E`, seed=0)** | **Candidate B: `40/40`** (`33/33` L0–L4 + oracle, `7/7` neg/unsupported refused, **`5/5` đa phương án**); **Baseline A: `32/40`** (`26/33` served, `6/7` neg, **`0/33` aux witness trong Scene3D**, `D02` lỗi `0a`, `B09` lỗi `>32 decl`) | [GOLD_CONSTRUCTION_BENCHMARK_RESULTS.json](GOLD_CONSTRUCTION_BENCHMARK_RESULTS.json) |
| **Kiểm toán tính mới (`Novelty Audit`)** | `CASE_B_DYNAMIC_COMPOSITION = 28`, `CASE_A_PREDEFINED_OR_PARITY = 5`, `CASE_C_UNSUPPORTED_OR_NEGATIVE = 1`, `NEGATIVE_REFUSAL_CASE = 6` | [DYNAMIC_COMPOSITION_EVALUATION.json](DYNAMIC_COMPOSITION_EVALUATION.json) |
| **Thư viện toán tử (`construction-operator/1`)** | `23` toán tử dựng & định lý suy diễn, tích hợp kiểm chứng `L0`–`L2` theo từng bước | [CONSTRUCTION_OPERATOR_INVENTORY.json](CONSTRUCTION_OPERATOR_INVENTORY.json) |
| **Kiểm thử §19 (17 hạng mục)** | **`16 passed in 3.14s`** (`76 passed in 4.24s` khi gộp suite evaluator & routing `/8`) | [test_verified_construction_graph_and_planner.py](../../../../../../backend/tests/geometry/test_verified_construction_graph_and_planner.py) |
| **Toàn bộ backend `pytest`** | **`15,046 passed, 7 skipped, 3 deselected, 12 xfailed, 1 warning in 777.24s`** (`0 failed`) | [CONSTRUCTION_REGRESSION_REPORT.md](CONSTRUCTION_REGRESSION_REPORT.md) |
| **Toàn vẹn đóng băng & Khóa Cache** | `123` file sản phẩm (`113a6a7cf6bbc15a…`), `CACHE_VERSION 145` (`6233c43c395c9b49…`), `0` diff `backend/app/**` & `frontend/**` | [CONSTRUCTION_FEASIBILITY_DECISION.md](CONSTRUCTION_FEASIBILITY_DECISION.md) |

---

## 3. Ranh giới kiến trúc mục tiêu sau chiến dịch `/1`

```text
Gold Typed Facts / Extracted Premises
        ↓
[Premise-Only Exact Frame] (engine.dung_tu_loi_goi -> Vec3 + SPD Gram Metric)
        ↓
[Dynamic Construction Planner] (bounded best-first + canonical_state_signature dedup)
   ├── 23 Verified Atomic & Deductive Operators (L0-L2 inline)
   └── Multi-Plan Goal Witness Check (L3: evaluate_goal_if_witnessed)
        ↓
[ConstructionProofGraph (verified-construction-graph/1)]
   ├── Projection ──→ [PresentationStepGraph (presentation-step-graph/1)]
   ├── Bridge ──────→ [Scene3D + continuity L4 (0 issues)]
   └── Read-only ───→ [Model 2 Interface (model2-action-interface/1)]
```

Chiến dịch `AXO CONSTRUCTION /1` kết luận **Khả thi trong nguyên mẫu cô lập (`FEASIBLE_IN_ISOLATED_PROTOTYPE_NEEDS_INTEGRATION_WAVE`)**, sẵn sàng chuyển giao danh sách nâng cấp có kiểm soát tới chủ sở hữu `backend/app/simulation/**` và `frontend/`.
