# text-to-geometry-functions — báo cáo (vertical slice kiến trúc text → function calls → dựng tất định)

Trạng thái: **`NEW_TEXT_TO_GEOMETRY_FUNCTIONS_VERTICAL_SLICE_AWAITING_REVIEW`**. Nhánh `feat/text-to-geometry-functions`
(rẽ từ `main` = `28ac1d61`). **0 lượt gọi model.** Đầu ra AI được đóng vai bằng fixture gán nhãn trước ⇒ kết quả dưới đây
là `foundation_only`: chứng minh engine và hợp đồng, **không** nói gì về năng lực của Gemini.

## 1. Kết luận

Đường mới chạy thật đầu–cuối: lời gọi hàm có kiểu + nguồn → cổng nguồn → engine giải phụ thuộc, tự chọn khung affine +
metric Gram, kiểm lại mọi dữ kiện → IR **sẵn có** → interpreter/kernel **sẵn có** → Scene3D **sẵn có** có `chart_metric`.
27/27 fixture khớp kết cục đăng ký trước: 10 phục vụ với đáp số chính xác đúng nhãn tính tay, 17 từ chối đúng mã. Hai tổ
hợp không có họ/khuôn nào trong kho (đáy lục giác đều + chân tại đỉnh; đáy vuông + chân tại trung điểm cạnh) dựng được bằng
cùng 16 hàm, không thêm mã theo họ. Không sửa kernel, interpreter, Scene3D, lược đồ IR, prompt, thẻ văn phạm, routing hay
`run_pipeline`; `LLM_ONLY` giữ nguyên làm mặc định sản phẩm.

## 2. Kiểm toán (chi tiết: `ARCHITECTURE_IMPLEMENTATION_MAP.md`)

Trước run: nhân hình học, `Metric` khung affine, primitive dựng câu lệnh IR, interpreter, Scene3D — **IMPLEMENTED**;
compiler họ-bài (9 họ thể tích, opt-in, không nối vào sản phẩm) và FactGraph — **PARTIAL**; **registry hàm cho AI, hợp đồng
lời gọi có nguồn, bố cục từ dữ kiện có kiểu — MISSING**. Việc chọn phép dựng nằm trong mã eligibility theo họ, metric
đa giác đều suy từ văn bản theo khuôn T8/T11/T12 của tuyến `LLM_ONLY`.

## 3. Đã viết / tái sử dụng

| | tệp | vai |
|---|---|---|
| MỚI | `backend/app/simulation/geometry_functions/registry.py` | 16 hàm (`FunctionSpec`, Pydantic `extra="forbid"`), `doc_ke_hoach`, `kiem_nguon`, `function_declarations` |
| MỚI | `backend/app/simulation/geometry_functions/engine.py` | `dung_tu_loi_goi`, `_Dung` (khối, bố cục, phụ thuộc, h², kiểm), IR, thực thi |
| MỚI | `backend/app/ai/function_route.py` | `run_function_route` — điểm vào; bày Scene3D (tầng được phép nhập `scene3d`) |
| SỬA | `backend/tests/geometry/test_structured_geometry_relations.py::test_Y_duong_mac_dinh_VAN_khong_tham_chieu_compiler` | loại trừ đích danh gói nghiên cứu (nó tái sử dụng `geometry_compiler.primitives`) và SIẾT thêm: `pipeline.py`/`main.py` không được tham chiếu `geometry_functions`/`function_route` |
| MỚI | `backend/scripts/run_text_to_functions_fixtures.py` | điểm vào CLI, ghi `offline/results.json` + cảnh |
| MỚI | `backend/tests/geometry/test_text_to_geometry_functions.py` + `fixtures/text_to_functions_cases.json` | 64 test, 27 ca |
| MỚI | `scene_world_metric_check.ts` (run này) | kiểm `veKhongGian` tổng quát: mọi cặp điểm |
| TÁI SỬ DỤNG, không sửa | `geometry_compiler/primitives.py`, `geometry/metric.py`, `semantic_program/{validator,formation,interpreter,simulation_state,scene3d}.py`, frontend `scene3d-chart.ts` | |
| SỬA | `docs/CODE_INDEX.md` (một hàng) | |

## 4. Kết quả từng ca (`offline/results.json`, `diagnostics/fixture_run.log`)

| ca | nhóm | kết cục | đáp số / mã |
|---|---|---|---|
| PYR1 · PYR1_P2 · PYR1_P3 | chóp + 2 diễn đạt khác (xáo thứ tự, `⊥`, "mặt phẳng đáy", cạnh từ `AB = 4`) | SERVED ×3 | 4√3 ×3; độ dài² mọi cặp đỉnh trùng nhau |
| PRISM1 | lăng trụ đứng đáy tam giác vuông | SERVED | 30 |
| PRISM2 | lăng trụ lục giác đều | SERVED | 18√3 |
| COMP1 | chóp + trung điểm + khối thứ hai + khoảng cách điểm–mặt | SERVED | V(M.ABC)=4 · d(A,(SBC))=12/5 |
| COMP2 | **tổ hợp mới**: đáy lục giác đều, SA ⊥ đáy tại đỉnh | SERVED | 6√3 · SD=5 |
| COMP3 | **tổ hợp mới**: đáy vuông, chân tại trung điểm H của AB | SERVED | 4 · SC=√14 · cos²(SC,(ABCD))=5/14 |
| REG1 · REG2 | chóp tam giác đều / lục giác đều, cạnh bên | SERVED | 3√39 · 12 |
| MISS1 | thiếu quan hệ xác định đỉnh | REFUSED | UNDERDETERMINED_POINT |
| MISS2 | lăng trụ thiếu chiều cao | REFUSED | MISSING_DIMENSION |
| CONTRA1 · CONTRA2 · CONTRA3 | cạnh bên ≠ chiều cao; SB mâu thuẫn; vi phạm bất đẳng thức tam giác | REFUSED | INCONSISTENT_FACTS ×3 |
| OOS1 · OOS2 · OOS3 | khối nón; ngũ giác đều; lăng trụ xiên | REFUSED | OUT_OF_SCOPE · UNSUPPORTED_REGULAR_POLYGON · UNDERDETERMINED_POINT |
| NEG1 · NEG2 | "không phải là hình chóp lục giác đều": AI khai chóp đều / AI khai chóp thường | REFUSED | NEGATED_CLAUSE · UNSUPPORTED_BASE_SHAPE |
| G1–G7 | đầu ra AI cố ý sai | REFUSED | UNGROUNDED_VALUE · QUOTE_NOT_IN_SOURCE · PREDICATE_NOT_IN_QUOTE · UNKNOWN_LABEL · SCHEMA_INVALID ×2 (hàm `place_point` có toạ độ; ô `apex_xyz`) · AMBIGUOUS_VALUE_QUOTE |

Kiểm thêm (test): chân `SA ⊥ (ABC)` là A chứ không phải tâm (SB² = 25 so với 9 + 16/3 của chóp đều cùng kích thước); thứ
tự dựng theo phụ thuộc (H sau A, B; S sau H; M sau S); xáo thứ tự lời gọi 5 lần × 4 ca ⇒ đáp số, trace, chương trình IR
trùng từng byte; Euler + `chart_metric` + điểm kernel = bố cục cho cả 10 cảnh; registry đóng, khai báo hàm không có ô toạ
độ; không import `app.ai`, chạy cả 27 ca với `call_gemini`/`run_pipeline` bị thay bằng hàm ném lỗi ⇒ không lần gọi nào.

**Oracle độc lập.** Đáp số và độ dài² kỳ vọng tính tay bằng công thức sách trước khi có engine (fixture); test đọc Scene3D
+ `chart_metric`, không đọc toạ độ nội bộ engine. Renderer: `veKhongGian` của frontend ⇒ RENDER_METRIC_OK 10/10 cảnh,
183 cặp điểm, sai số tương đối ≤ 5·10⁻¹⁰ (frontend làm tròn khi ghi chuỗi); tiêm lỗi (bỏ metric khi vẽ) ⇒ MISMATCH, mã
thoát 1 (`diagnostics/renderer_metric_check.log`). Kiểm đột biến 6/6 bị bắt: chân đặt vào tâm, bỏ bước kiểm, bỏ vị từ,
sai dấu khung lục giác, phụ thuộc thứ tự lời gọi, bỏ cổng nguồn (`diagnostics/mutation_check.log`).

## 5. Test và cổng

- `tests/geometry/test_text_to_geometry_functions.py`: 64 passed (đỏ trước khi có module — TDD).
- Full backend suite lần 1 (mã chưa tách tầng): 7780 passed, **14 failed**. Ba lỗi THẬT của bản đầu: engine dưới
  `app/simulation` nhập `scene3d` và `simulation_state` (đảo hướng phụ thuộc — `test_scene3d`/`test_simulation_state`
  ::`test_KHONG_module_nao_o_TANG_DUOI_…`), và nhắc `geometry_compiler` (`test_Y…`). Sửa ở gốc: bày cảnh dời lên
  `app/ai/function_route.py`; `test_Y` đổi như bảng §3. Mười lỗi còn lại là candidate lệch (đúng luật, xem dưới), một là
  `test_holdout_readiness` chỉ đỏ khi cây bẩn.
- Full backend suite sau sửa + đóng băng lại, cây sạch tại `c71cae4c`: **7795 passed, 0 failed**, 1 skipped, 2 deselected.
- Cổng tài liệu (`test_docs_information_architecture.py`, `test_docs_test_telemetry.py`) xanh sau đóng băng; node harness
  `compiler-scene-replay-lib.node-test.mjs` (đọc manifest Tier-A vừa ghim) 88/88; `lock_cache_identity --verify` khớp
  (`CACHE_VERSION` 125, môi trường b1714b56… không đổi).
- `freeze_evaluation_candidate --verify`: lệch sau khi thêm `backend/app/simulation/geometry_functions/` (đúng luật) ⇒
  đóng băng lại ở commit riêng `c71cae4c`, trong worktree detached sạch tại `86f683e0` (= product commit): candidate
  `93077b51…` → `8f12f4ab…`, 102 → 106 tệp, taxonomy / primitive set / lược đồ không đổi; lớp lệch mới
  `inputs/candidate_divergence.json` (đính chính lớp `regular-prisms`), log tích luỹ nối thêm, `test_C2b` trỏ lớp mới,
  manifest Tier-A ghim `86f683e0` / `8f12f4ab` (`diagnostics/freeze_86f683e0.log`).
- T3 / frontend: không chạy — không đổi `frontend/`; script `.ts` của run chạy bằng esbuild + node như các run trước.

## 6. Kiến trúc mới còn phụ thuộc `LLM_ONLY` ở đâu

Không ở đường thực thi: engine chỉ dùng IR/interpreter/Scene3D chung. Phụ thuộc còn lại là **đầu vào**: chưa có bộ sinh lời
gọi hàm thật (đang là fixture). Sản phẩm (`run_pipeline`, `/api/analyze`) vẫn đi `LLM_ONLY`; đường mới chỉ gọi được qua
`app/ai/function_route.run_function_route` / CLI. Interpreter dùng chung còn lỗi P2 của pilot (`Radical × int`) — đường mới không phát `arith`.

## 7. Có cần mở rộng primitive không

Có, theo đề thật chứ không theo danh sách: (1) độ dài ký hiệu `a` (phổ biến nhất trong đề Việt Nam — đáp số theo a³);
(2) "mặt bên … vuông góc với đáy" và "hình chiếu của S lên đáy là …" (chân dựng bằng quan hệ, không bằng tên điểm);
(3) góc giữa hai mặt, khoảng cách hai đường chéo nhau; (4) đáy hình thoi/hình thang (cần dữ kiện góc). Mỗi hàm mới phải
kèm luật bố cục hoặc kiểm, và giữ khung hữu tỉ (đa giác đều 5 cạnh vẫn từ chối).

## 8. Văn liệu (`LITERATURE_GAP_MATRIX.md`, tác tử nghiên cứu nền, 26 công trình)

Ý "thư viện phép dựng + hợp thành" **không mới** (Gulwani et al., PLDI 2011); gần nhất hiện nay là GeoBuildBench (2026,
preprint: văn bản → DSL kiến thiết 2D, LLM viết cả chương trình, kiểm bằng dung sai — tương ứng tuyến `LLM_ONLY` cũ).
Trong tập đã đọc, không công trình nào **báo cáo** đồng thời đề hình không gian, thư viện hàm 3D có kiểu mà mô hình chỉ
*chọn*, và kiểm chính xác — khoảng trống **trong tập đọc**, không phải bằng chứng tính mới. Neo tham số vào span đề: `NR`
trong các công trình hình học đã mở. Token theo loại IR: `NR` toàn bộ. 7 công trình đọc toàn văn, 19 chỉ tóm tắt; câu trích
phải đối chiếu bản gốc trước khi vào khoá luận.

Hướng có căn cứ đáng theo: **H1** chọn hàm theo mệnh đề vs viết cả chương trình (pilot G05: 0/10 dương ở `LLM_ONLY`, lỗi
là toạ độ √3 + nhãn xuất xứ — đúng hai thứ đường mới gỡ khỏi mô hình); **H2** neo nguồn bắt buộc (G1–G4 cho thấy cổng
bắt được bốn lối bịa, cần đo tần suất trên mô hình thật); **H3** token (thinking chiếm 74 % chi phí pilot). Compact DSL và
FactGraph **không** được đề xuất triển khai ở bước này: registry lời gọi hàm đã là biểu diễn trung gian, chưa có phép đo cho
thấy cần thêm tầng.

## 9. Bước nhỏ tiếp theo để nối Gemini thật

Một adapter `function_declarations()` → `tools.functionDeclarations` + `toolConfig.functionCallingConfig = {mode: ANY,
allowedFunctionNames}` + prompt ngắn "đọc từng mệnh đề, chọn hàm, chép quote", gom `functionCall` thành `{"calls": [...]}` rồi
gọi `run_function_route`. Đo trước 0 lượt (fixture tái lập đầu ra function calling), rồi một pilot nhỏ có ngân sách theo
`EXPERIMENT_PROTOCOL.md` Q1 — **cần quyết định của người dùng**, đặt `maxOutputTokens`.

## 10. Giới hạn

`foundation_only`; fixture do chính tác giả engine viết (độc lập một phần: nhãn tính tay trước khi có engine); từ khoá vị
từ là điều kiện cần, không hiểu ngữ nghĩa; một mặt đáy; 16 hàm. Skills đã dùng: `superpowers:verification-before-completion`,
`superpowers:test-driven-development`, `mattpocock-skills:research` (tác tử nền cho văn liệu).
