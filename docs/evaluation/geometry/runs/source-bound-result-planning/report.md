# Source-Bound Result Binding + Bounded Effect-Driven Point–Line Distance Planning (LOCAL, 2026-10-15)

**Kết luận: `LOCAL_RESEARCH_SLICE_VERIFIED_NO_PUSH`.**
Nhánh `research/source-bound-result-planning` (rẽ từ `19140e2f` / `main` `2a3c0787`). Không merge, không push, không gọi Gemini thật (`MODEL_REQUEST_COUNT = 0`), `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid vẫn tắt trên sản phẩm.

## 1. Đối chiếu Preregistration (`next-slice-preregistration.md`)

Toàn bộ hạng mục trong tài liệu tiền đăng ký [`docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/next-slice-preregistration.md`](../goal-directed-planner-generalization-audit/next-slice-preregistration.md) đạt `COMPLETED`:

| Hạng mục | Thực thi | Phân loại |
|---|---|---|
| **§4.1 Fact Transport (`TypedFact.line_ref`)** | `planner.py`: `line_ref: str \| None` cho `question(distance)` và `projection`; kiểm toàn vẹn tham chiếu/vai trò/phủ định/3 nhãn phân biệt mỗi mặt trong `doc_du_kien` (`UNKNOWN_DERIVED_REFERENCE`, `DERIVED_REFERENCE_TYPE_MISMATCH`, `GOAL_CLAUSE_NOT_PREMISE`, `CONDITIONAL_CLAUSE`, `NEGATED_CLAUSE`, `FACT_INCOMPLETE`). | `COMPLETED` |
| **§4.2 Call Schema (`ProjectionLineArgs.line_ref`)** | `registry.py`: `line` xor `line_ref`; Route A bị chặn bởi `_kiem_result_binding` (`RESULT_BINDING_UNVERIFIED`); bề mặt Route A (`912b22ef…`) giữ nguyên, khai báo hàm (`be38f55f…`) và bề mặt Route B (`442d1a0b…`) chốt trong [`provider-surfaces.json`](provider-surfaces.json). | `COMPLETED` |
| **§4.3 Registry Effect Metadata (`PlanningTerm`, `PlanningContract`)** | `registry.py`: khai báo nội bộ trên `intersection_line` (`Line`), `orthogonal_projection_line` (`Foot`), `ask_length` (`AnswerDistance`); không xuất ra `function_declarations()`. | `COMPLETED` |
| **§4.4 Bounded Effect Resolver (`_EffectResolver`)** | `planner.py`: phân giải ngược có trần (`MAX_EFFECT_DEPTH = 3`, `MAX_EFFECT_NEEDS = 32`, `MAX_EFFECT_CANDIDATES = 8`, `MAX_RESULT_LINES = 4`, `MAX_RESULT_FEET = 8`, `MAX_CALLS = 64`), phát hiện chu trình (`DEPENDENCY_CYCLE`), tái sử dụng hình chiếu đã khai với chi phí `0`, gộp các producer `intersection_line` tương đương (`aliases`), ghi nhớ (`memo`) qua nhiều câu hỏi lặp. | `COMPLETED` |
| **§4.5 Source Grounding (`_kiem_result_binding`, `_kiem_nguon_dong`)** | `registry.py`: kiểm chứng chỉ `result-line-reference`, `result-line-alias`, `effect_binding` đối chiếu span nguyên tử trong đề, kiểm đủ 3 nhãn phân biệt mỗi mặt phẳng trước khi chuẩn hoá tập hợp (`frozenset`), gọi `_kiem_nguon_dong` cho toàn bộ tiền đề. | `COMPLETED` |
| **§4.6 Engine, IR & Scene3D (`engine.py`, `function_route.py`)** | `engine.py`: `_Dung.lines` lưu `Line3` đã kiểm thuộc cả hai mặt phẳng qua `K.intersect_plane_plane`, phát lệnh IR `intersect_plane_plane` đúng một lần trước consumer đầu tiên (`_emit_intersection`), tự kiểm tương đương `Line3` với bộ nhớ thực thi của Kernel. `function_route.py`: gắn vai trò `Điểm dựng phụ` (`AUXILIARY`) cho chân phụ mới, nâng bước `resolve_line` đã xác thực thành `CREATE` / `GEOMETRY_CONSTRUCTION`, giữ nguyên cơ chế ẩn `perpendicular_witness` khi khoảng cách bằng `0`. | `COMPLETED` |

## 2. Kết quả Kiểm chứng RED → GREEN & Đối chứng

- **RED baseline (`de5ea1a7`, [`red.json`](red.json)):** 18/18 ca trong `next-slice-corpus.json` từ chối `SCHEMA_INVALID` trước khi mở `line_ref`.
- **GREEN trên tập khóa (`test_result_binding_planning.py` — 64 passed):**
  - **6/6 ca dương (`SERVED`):** `derived-line-pyramid` ($d^2 = 10/11$), `derived-line-cuboid` ($d^2 = 1$), `derived-line-prism` ($d^2 = 3$), `derived-line-regular-pyramid` ($d^2 = 1/2$), `derived-line-zero-distance` ($d^2 = 0$, không sinh `perpendicular_witness` suy biến), `derived-line-reused-foot` ($d^2 = 10/11$, tái sử dụng chân `J` với `new_constructions = 0`).
  - **12/12 ca âm (`REFUSED`, fail-closed):** `parallel-planes` (`PARALLEL_PLANES`), `coincident-planes` (`COINCIDENT_PLANES`), `unknown-line-ref` (`UNKNOWN_DERIVED_REFERENCE`), `wrong-producer-type` (`DERIVED_REFERENCE_TYPE_MISMATCH`), `prove-role-producer` (`GOAL_CLAUSE_NOT_PREMISE`), `conditional-producer` (`CONDITIONAL_CLAUSE`), `negated-producer` (`NEGATED_CLAUSE`), `incomplete-plane` (`FACT_INCOMPLETE`), `contradictory-length` (`INCONSISTENT_FACTS`), `unread-premise-tail` (`SOURCE_PREMISE_UNREAD`), `cyclic-point-def` (`DEPENDENCY_CYCLE`), `wrong-goal-planes` (`SOURCE_OBJECT_MISMATCH`).
  - **Oracle độc lập & đối chứng:** kiểm hiệp thuộc bằng tích có hướng/vô hướng affine và cực tiểu bậc hai Gram (`test_independent_incidence_gram_and_causal_oracle`); 6 biến thể metamorphic (`registry-order`, `facts-order`, `plane-order`, `plane-orientation`, `rename`, `collision`); co giãn kích thước nguồn và đổi bản đồ affine + Gram (`test_metric_translation_and_chart_scaling_of_real_planned_ir`); 6 trần ngân sách (`PLAN_TOO_LARGE`); gỡ effect khỏi `REGISTRY` (`UNSUPPORTED_CAPABILITY`); chu trình effect (`DEPENDENCY_CYCLE`); chặn Route A (`RESULT_BINDING_UNVERIFIED`); 8 biến thể đối kháng nguồn + đoạn giao tuyến hữu hạn + mặt 4 ký tự trùng đỉnh `(SAAC)`.
- **Bất biến hồi quy (`verification/`):**
  - `two-line-plane-section`: development 45 (`12 SERVED / 33 REFUSED`) và heldout 32 (`11 SERVED / 21 REFUSED`) giữ nguyên kết quả.
  - `hybrid_compiler_benchmark`: 30 ca lịch sử giữ nguyên kết quả (`19/9/0/2` ở cả hai nhánh `facts` và `pipeline`).
  - Cụm kiểm thử hình học liên quan (`872 passed, 5 xfailed`), kiểm thử tài liệu/danh tính/candidate (`123 passed`), toàn bộ Vitest frontend (`68 files, 1055 passed`) và `vite build` đều PASS.
- **Kiểm chứng trình duyệt (`visual/`):**
  - Xuất 18 kết quả thực tế (`visual/corpus-results.json`) và 4 cảnh trình duyệt (`visual/scenes.json`: `derived-line-pyramid`, `derived-line-cuboid`, `derived-line-prism`, `parallel-planes`).
  - Playwright trên cả **SwiftShader** (`visual/swiftshader/receipt.json`) và **Intel UHD D3D11 GPU** (`visual/gpu/receipt.json`) đạt `PASS_CORE_CAUSAL_RENDERING` (`scenes: 4, errors: 0`): giao tuyến `gt_g` luôn sinh trước chân `H` (`lineBorn < footBorn`), chọn đối tượng `H` hoạt động, tua lùi không rò `H`, ẩn `gt_g` làm thay đổi số điểm ảnh thực (`ownPixels`: 323–578 px), ca từ chối `parallel-planes` hiển thị mã lỗi và không vẽ canvas. Giữ 14 ảnh chính cho người duyệt, băm SHA-256 của 88 ảnh bước trung gian lưu tại [`visual/image-policy.json`](visual/image-policy.json).

## 3. Giới hạn & Cổng còn mở

- Tập `next-slice-corpus.json` là tập phát triển dẫn xuất từ chẩn đoán (`NOT_HELD_OUT`); chưa có tập held-out độc lập riêng cho lát cắt `line_ref` và chưa đo Gemini thật (`MODEL_REQUEST_COUNT = 0`).
- Chưa chạy lại cổng T3 toàn kho trong worktree tách rời cho commit `b8112f35` (đã chạy đầy đủ cụm regression hình học 872 test, cụm docs/identity/candidate 123 test, toàn bộ 1055 test Vitest frontend, `vite build`, và Playwright SwiftShader + D3D11). Không tuyên bố `FULL_PRODUCT_GATE_PASS` cho T3 trước khi chạy cổng tách rời.
