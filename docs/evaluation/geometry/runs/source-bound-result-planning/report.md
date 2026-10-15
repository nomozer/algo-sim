# Source-Bound Result Binding + Bounded Effect-Driven Point–Line Distance Planning (LOCAL, 2026-10-15)

**Kết luận: `RESULT_BINDING_INTEGRATION_REVIEW_READY`.**
Nhánh `research/source-bound-result-planning` (rẽ từ `19140e2f` / `main` `2a3c0787`). Không merge, không push, không gọi Gemini thật (`MODEL_REQUEST_COUNT = 0`), `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid vẫn tắt trên sản phẩm.

## 1. Đối chiếu Preregistration (`next-slice-preregistration.md`)

Toàn bộ hạng mục trong tài liệu tiền đăng ký [`docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/next-slice-preregistration.md`](../goal-directed-planner-generalization-audit/next-slice-preregistration.md) (`sha256 = 14303fa0d80f5a55e5f0fd87f7cc6d15f23fdf80e118668c02007019ed297db7`) đạt `COMPLETED`:

| Hạng mục | Thực thi | Phân loại |
|---|---|---|
| **§4.1 Fact Transport (`TypedFact.line_ref`)** | `planner.py`: `line_ref: str \| None` cho `question(distance)` và `projection`; kiểm toàn vẹn tham chiếu/vai trò/phủ định/3 nhãn phân biệt mỗi mặt trong `doc_du_kien` (`UNKNOWN_DERIVED_REFERENCE`, `DERIVED_REFERENCE_TYPE_MISMATCH`, `GOAL_CLAUSE_NOT_PREMISE`, `CONDITIONAL_CLAUSE`, `NEGATED_CLAUSE`, `FACT_INCOMPLETE`). | `COMPLETED` |
| **§4.2 Call Schema (`ProjectionLineArgs.line_ref`)** | `registry.py`: `line` xor `line_ref`; Route A bị chặn bởi `_kiem_result_binding` (`RESULT_BINDING_UNVERIFIED`); bề mặt Route A (`7ea511a6…`), bề mặt Route B (`485d3834…`) và khai báo hàm (`5ceb0f99…`) chốt trong [`provider-surfaces.json`](provider-surfaces.json) và [`reconciliation.json`](reconciliation.json). | `COMPLETED` |
| **§4.3 Registry Effect Metadata (`PlanningTerm`, `PlanningContract`)** | `registry.py`: khai báo nội bộ trên `intersection_line` (`Line`), `orthogonal_projection_line` (`Foot`), `ask_length` (`AnswerDistance`); không xuất ra `function_declarations()`. | `COMPLETED` |
| **§4.4 Bounded Effect Resolver (`_EffectResolver`)** | `planner.py`: phân giải ngược có trần (`MAX_EFFECT_DEPTH = 3`, `MAX_EFFECT_NEEDS = 32`, `MAX_EFFECT_CANDIDATES = 8`, `MAX_RESULT_LINES = 4`, `MAX_RESULT_FEET = 8`, `MAX_CALLS = 64`), phát hiện chu trình (`DEPENDENCY_CYCLE`), tái sử dụng hình chiếu đã khai với chi phí `0`, gộp các producer `intersection_line` tương đương (`aliases`, kể cả producer không được tham chiếu), ghi nhớ (`memo`) qua nhiều câu hỏi lặp. | `COMPLETED` |
| **§4.5 Source Grounding (`_kiem_result_binding`, `_kiem_nguon_dong`)** | `registry.py`: kiểm chứng chỉ `result-line-reference`, `result-line-alias`, `effect_binding` đối chiếu trên toàn bộ câu bao chứa (`_bien_cau`) trong đề, kiểm `_hoi_dung_cum` cho câu hỏi `line_ref` và chân chiếu đường có tên, kiểm đủ 3 nhãn phân biệt mỗi mặt phẳng trước khi chuẩn hoá tập hợp (`frozenset`), gọi `_kiem_nguon_dong` cho toàn bộ tiền đề. | `COMPLETED` |
| **§4.6 Engine, IR & Scene3D (`engine.py`, `function_route.py`)** | `engine.py`: `_Dung.lines` lưu `Line3` đã kiểm thuộc cả hai mặt phẳng qua `K.intersect_plane_plane`, phát lệnh IR `intersect_plane_plane` đúng một lần trước consumer đầu tiên (`_emit_intersection`), tự kiểm tương đương `Line3` với bộ nhớ thực thi của Kernel. `function_route.py`: gắn vai trò `Điểm dựng phụ` (`AUXILIARY`) cho chân phụ mới, nâng bước `resolve_line` đã xác thực thành `CREATE` / `GEOMETRY_CONSTRUCTION`, giữ nguyên cơ chế ẩn `perpendicular_witness` khi khoảng cách bằng `0`. | `COMPLETED` |

## 2. Kết quả Kiểm chứng RED → GREEN, Đối soát Corpus & Review Độc lập

- **RED baseline (`de5ea1a7`, [`red.json`](red.json)):** 18/18 ca trong `next-slice-corpus.json` (`sha256 = 6587fabf084029bf7aa787df291b27bbf83fde95212ca9a8f1bd4c4ce9cbda84`) từ chối `SCHEMA_INVALID` trước khi mở `line_ref`.
- **GREEN trên tập khóa (`test_result_binding_planning.py` — 72 passed; đối soát đầy đủ tại [`reconciliation.json`](reconciliation.json)):**
  - **6/6 ca dương gốc (`SERVED`, `EXACT_MATCH`):**
    1. `derived-line-pyramid` ($d^2 = 10/11$, $d = \sqrt{110}/11$)
    2. `derived-line-cuboid` ($d^2 = 5$, $d = \sqrt{5}$)
    3. `derived-line-prism` ($d^2 = 3$, $d = \sqrt{3}$)
    4. `different-direction-decomposition` ($d^2 = 10$, $d = \sqrt{10}$)
    5. `zero-distance` ($d^2 = 0$, $d = 0$, không sinh `perpendicular_witness` suy biến)
    6. `shared-line-foot-two-goals` ($d^2 = 10/11$, $d = \sqrt{110}/11$, dùng chung giao tuyến và chân chiếu qua hai câu hỏi)
  - **12/12 ca âm gốc (`REFUSED`, fail-closed, `EXACT_MATCH`):**
    1. `unknown-reference` (`UNKNOWN_DERIVED_REFERENCE`)
    2. `wrong-reference-type` (`DERIVED_REFERENCE_TYPE_MISMATCH`)
    3. `producer-source-mismatch` (`SOURCE_OBJECT_MISMATCH`)
    4. `conditional-producer` (`CONDITIONAL_CLAUSE`)
    5. `proof-producer` (`GOAL_CLAUSE_NOT_PREMISE`)
    6. `negated-producer` (`NEGATED_CLAUSE`)
    7. `parallel-planes` (`PARALLEL_NO_INTERSECTION`)
    8. `coincident-planes` (`CONTAINED_INFINITE_INTERSECTION`)
    9. `long-quote-nonnumeric` (`SOURCE_PREMISE_UNREAD`)
    10. `and-song-unread-premise` (`SOURCE_PREMISE_UNREAD`)
    11. `unverified-goal-value` (`NOT_ASKED_IN_SOURCE`)
    12. `cycle` (`DEPENDENCY_CYCLE`)
  - **Oracle độc lập & đối chứng (72 tests trong `test_result_binding_planning.py`):** kiểm hiệp thuộc bằng tích có hướng/vô hướng affine và cực tiểu bậc hai Gram (`test_independent_incidence_gram_and_causal_oracle`); 6 biến thể metamorphic (`registry-order`, `facts-order`, `plane-order`, `plane-orientation`, `rename`, `collision`); co giãn kích thước nguồn và đổi bản đồ affine + Gram (`test_metric_translation_and_chart_scaling_of_real_planned_ir`); 6 trần ngân sách (`PLAN_TOO_LARGE`); gỡ effect khỏi `REGISTRY` (`UNSUPPORTED_CAPABILITY`); chu trình effect (`DEPENDENCY_CYCLE`); chặn Route A (`RESULT_BINDING_UNVERIFIED`); 8 biến thể đối kháng nguồn + đoạn giao tuyến hữu hạn + mặt 4 ký tự trùng đỉnh `(SAAC)`; 6 biến thể câu bao chứa cắt cụt quote / từ bổ nghĩa (`test_enclosing_sentence_outside_truncated_quote_or_modifier_is_refused`); khử trùng lặp `intersection_line` không tham chiếu (`test_unreferenced_intersection_line_deduplication_and_coexistence`); từ chối mặt phẳng 3 điểm thẳng hàng (`test_collinear_three_point_plane_in_intersection_line_is_refused`).
- **Review độc lập ([`review.md`](review.md)):**
  - Rà soát độc lập 11 chiều trên commit `b8112f35` phát hiện `[CRITICAL-1]` (câu bao chứa ngoài quote bị cắt cụt / từ bổ nghĩa ở `_kiem_result_binding` và `_kiem_phu`), `[IMPORTANT-1]` (hai tiền đề `intersection_line` tương đương không được tham chiếu phát sinh 2 lệnh trùng), `[IMPORTANT-2]` (lệch mô tả văn bản trong bản nháp `report.md` so với `next-slice-corpus.json` và `provider-surfaces.json`), và `[NONBLOCKING-1]` (thêm test tường minh cho mặt 3 điểm thẳng hàng).
  - Đã sửa triệt để theo chu trình RED → GREEN tại commit sản phẩm `10dd6d6e` (candidate `47e54b3dc9d261e86d4c1415cf904fd5e20ff884dc67fad2e316ea360cddc1fc`, 110 file) và được reviewer độc lập xác nhận lại `PASS` (0 lỗi mở).
- **Bất biến hồi quy & T3 tách rời (`verification/`):**
  - `two-line-plane-section`: development 45 (`12 SERVED / 33 REFUSED`) và heldout 32 (`11 SERVED / 21 REFUSED`) giữ nguyên kết quả.
  - `hybrid_compiler_benchmark`: 30 ca lịch sử giữ nguyên kết quả (`19/9/0/2` ở cả hai nhánh `facts` và `pipeline`).
  - Cổng T3 có thẩm quyền trong worktree tách rời sạch (`verification/t3-pass.json`, `verification/t3-authoritative.log`): toàn bộ pytest backend, Vitest frontend (`68 files, 1055 passed`), `npm run build`, `replay_demo_cases.py`, và `audit_demo_crash_surface.py` đều `PASS`.
- **Kiểm chứng trình duyệt (`visual/`):**
  - Xuất 18 kết quả thực tế (`visual/corpus-results.json`, bất biến byte `1ceed3f0…` sau commit `10dd6d6e`) và 4 cảnh trình duyệt (`visual/scenes.json`, bất biến byte `177665cc…`).
  - Playwright trên cả **SwiftShader** (`visual/swiftshader/receipt.json`) và **Intel UHD D3D11 GPU** (`visual/gpu/receipt.json`) đạt `PASS_CORE_CAUSAL_RENDERING` (`scenes: 4, errors: 0`): giao tuyến `gt_g` luôn sinh trước chân `H` (`lineBorn < footBorn`), chọn đối tượng `H` hoạt động, tua lùi không rò `H`, ẩn `gt_g` làm thay đổi số điểm ảnh thực (`ownPixels`: 323–578 px), ca từ chối `parallel-planes` hiển thị mã lỗi và không vẽ canvas. Giữ 14 ảnh chính cho người duyệt, băm SHA-256 của 88 ảnh bước trung gian lưu tại [`visual/image-policy.json`](visual/image-policy.json).

## 3. Giới hạn & Cổng còn mở

- Tập `next-slice-corpus.json` là tập phát triển dẫn xuất từ chẩn đoán (`NOT_HELD_OUT`); chưa có tập held-out độc lập riêng cho lát cắt `line_ref` và chưa đo Gemini thật (`MODEL_REQUEST_COUNT = 0`).
- Mặc định sản phẩm giữ nguyên `LLM_ONLY` (`CACHE_VERSION = 125`), Hybrid vẫn `NO-GO` trên sản phẩm; việc tích hợp nhánh `research/source-bound-result-planning` vào `main` chờ quyết định của người dùng.
