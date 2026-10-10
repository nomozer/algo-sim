# Bản đồ triển khai planner và kiểm toán tái sử dụng / trùng lặp

Run `hybrid-compiler-selection`. Mã tại `91e2edf9` (candidate `e9d20aa2…`).

## 1. Tệp và ký hiệu

| tệp | dòng | ký hiệu | vai trò |
|---|---|---|---|
| `backend/app/simulation/geometry_functions/planner.py` (mới) | 358 | `TypedFact`, `KeHoach`, `doc_du_kien`, `lap_ke_hoach`, `PLANNER_VERSION`, `MAX_CALLS` | hợp đồng dữ kiện + planner tất định |
| `backend/app/ai/fact_extraction.py` (mới) | 102 | `SYSTEM_PROMPT`, `facts_response_schema`, `build_request`, `surface_fingerprint`, `parse_response`, `run_ai_fact_route` | adapter structured output; provider giả trong test |
| `backend/app/ai/function_route.py` (sửa) | +50 | `run_fact_route`, `_hinh_khong_duy_nhat` | planner → `run_function_route` → kiểm mục tiêu / phủ định → chẩn đoán |
| `backend/app/simulation/geometry_functions/engine.py` (sửa) | +27 | `KetQuaTuyen.details/planner/checker`, `_kiem_tren_hinh` | dữ liệu từ chối; checker một mệnh đề trên hình đã dựng |
| `backend/app/simulation/geometry_functions/registry.py` (sửa) | ±13 | `TuChoi.data`; từ khoá "lập phương", "chữ nhật" | dữ liệu kèm từ chối; nới cổng nguồn (khai ở `AB_OFFLINE_RESULTS.md` §6) |
| `backend/scripts/hybrid_ab_offline.py` (mới) | 214 | `facts_from_calls`, `phan_hang`, `chay` | bộ chạy A/B offline + bộ chấm sáu hạng |
| `backend/tests/geometry/test_hybrid_compiler_selection.py` (mới) | 107 test | | holdout, parity, luật planner, mã từ chối, adapter giả |
| `backend/tests/geometry/fixtures/hybrid_holdout_cases.json` (mới) | 14 ca | | tiền đăng ký `f6b1a551` |

## 2. Luồng `lap_ke_hoach`

1. `doc_du_kien`: Pydantic ⇒ `SCHEMA_INVALID`; ô bắt buộc theo `kind` ⇒ `FACT_INCOMPLETE`; id trùng ⇒ `SCHEMA_INVALID`.
2. Cờ toàn đề: `ambiguous` ⇒ `AMBIGUOUS_FACT`; `role = condition` ⇒ `CONDITIONAL_CLAUSE`.
3. Đọc khối (`_doc_khoi`): ký hiệu → đỉnh / đáy / đáy trên. Tứ diện "ABCD" thành chóp "D.ABC". Khối bị phủ định thì bỏ tính đều.
4. **Mở rộng định nghĩa:**

   | khối | lời gọi |
   |---|---|
   | chóp đều | `regular_pyramid` + `regular_polygon(đáy)` |
   | chóp thường | `pyramid` |
   | lăng trụ | `prism(right = đứng ∨ đều ∨ lập phương ∨ hộp)` |
   | lăng trụ đều / lập phương | thêm `regular_polygon(đáy)` |
   | hộp chữ nhật | thêm `rectangle(đáy)` |

5. **Từng dữ kiện** (`_anh_xa`). `prove` vào `goals`, `negated` vào `negated`; cả hai không vào `calls`.

   | dữ kiện | lời gọi |
   |---|---|
   | `polygon_shape` đều | `regular_polygon`; gộp với đáy đã khai đều và gắn cạnh |
   | `polygon_shape` hình chữ nhật | `rectangle` |
   | `polygon_shape` tam giác thường | chỉ đặt tên, không lời gọi |
   | `perpendicular` | theo kiểu toán hạng: (đường, mặt) `perpendicular_line_plane` · (đường, đường) `perpendicular_lines` · (mặt, mặt) chỉ khi một mặt là đáy của khối và mặt kia có đúng một đỉnh ngoài đáy: `face_perpendicular_base`; còn lại `UNSUPPORTED_CAPABILITY` |
   | `length` | `_do_dai`: `segment` `segment_length` · `height` `height` · `base_edge` gắn vào `regular_polygon` của đáy, đáy không đều thì `AMBIGUOUS_REFERENCE` · `lateral_edge` gán SA (chóp **đều**) hoặc AA′ (lăng trụ), chóp không đều thì `AMBIGUOUS_REFERENCE` · `edge` (lập phương, tứ diện đều) = cạnh đáy + cạnh bên |
   | `altitude` · `projection` · `point_def` · `equal_lengths` · `right_angle` | hàm cùng tên trong registry |
   | `question` | `_cau_hoi`: thể tích, diện tích, độ dài, khoảng cách điểm–mặt / đường–đường, góc đường–mặt / mặt–mặt; còn lại `UNSUPPORTED_CAPABILITY` |

6. Ghi chiều cao theo khối (dùng cho chẩn đoán). Quá 64 lời gọi ⇒ `PLAN_TOO_LARGE`. Gộp lời gọi y hệt, gộp quote cho đa giác
   và khối, không gộp câu hỏi.

Mỗi lời gọi phát ra ghi một dòng trace `{fact, rule, fn, call}`. `run_fact_route` đặt trace vào `KetQuaTuyen.planner`.

## 3. Sau khi dựng (`run_fact_route`)

`run_function_route` với đúng `{"calls": k.calls}`. Thứ tự sau đó:

1. Không phục vụ và mã `UNDERDETERMINED_POINT`: thử `_hinh_khong_duy_nhat`. Mẫu duy nhất là đỉnh chóp chưa xác định + có chiều
   cao + chỉ hỏi thể tích, cho ra `FIGURE_NOT_UNIQUE`. Ngoài mẫu đó giữ nguyên mã.
2. Phục vụ: checker (`engine._kiem_tren_hinh` → `_Dung._dung_khong`) kiểm từng mục tiêu và từng mệnh đề phủ định. Đây là
   **cùng** hàm engine dùng để kiểm lại mọi dữ kiện sau khi dựng. Câu hỏi / `unsupported` / điểm không có trên hình cho
   `UNVERIFIABLE`.
3. Mục tiêu `FAILS` ⇒ `PROOF_GOAL_FALSE`. Phủ định `HOLDS` ⇒ `INCONSISTENT_FACTS`. Phủ định `UNVERIFIABLE` ⇒ `NEGATED_CLAUSE`.

## 4. Kiểm toán tái sử dụng

**Dùng nguyên, không sửa:** kernel (`geometry/`), metric, `semantic_program/ir_builders.py`, interpreter, validator,
`formation`, phần dựng Scene3D + `chart_metric` trong `function_route.py`, `_openapi`, `MAX_OUTPUT_TOKENS`, `TEMPERATURE`,
`LiveAIDisabled`, `live_transport` của `function_calling.py`.

**Dùng nguyên, có mở rộng nhỏ:**

- registry: `doc_ke_hoach`, `kiem_nguon` 5 tầng; thêm `TuChoi.data` và ba từ khoá;
- engine: `_Dung`, `_dung_khong`; thêm checker và trường kết quả.

Lời gọi của B đi qua **cùng** cổng nguồn và **cùng** bước kiểm lại dữ kiện như A.

**Không dùng:** `geometry_compiler/` (FactGraph, `contract_adapter`, `SUPPORTED_FAMILY*`). FactGraph đọc `RequestContract` của
`LLM_ONLY` (không có quote theo dữ kiện, không có vai trò mệnh đề) và sinh `SemanticProgramSpec` theo họ bài. B sinh lời gọi
registry, không có họ bài. Guard `test_Y` mở rộng thêm `app.ai.fact_extraction`: đường mặc định không với tới B theo bao đóng
import.

## 5. Trùng lặp còn lại (có khai)

| chỗ trùng | mức | vì sao giữ | khi nào gộp |
|---|---|---|---|
| bộ đọc vỏ phản hồi Gemini (`usageMetadata`, `promptFeedback`, `finishReason`, `MAX_TOKENS`) ở `fact_extraction.parse_response` và `function_calling.parse_response`, cùng lớp `_TuChoiAI` | ~15 dòng | phần nội dung khác hẳn (JSON văn bản vs `functionCall` song song); B còn là thực nghiệm | nếu B được giữ sau A/B thật: tách `_doc_vo_phan_hoi` dùng chung |
| hai biểu diễn "dữ kiện": `TypedFact` (B) và `GeometryFactGraph` (compiler cũ) | khái niệm | khác đầu vào, khác đầu ra, khác chủ (§4) | khi bỏ `LLM_ONLY`, compiler cũ hết người đọc |
| tri thức định nghĩa (chóp đều ⇒ đáy đều, lập phương ⇒ …) ở planner, ở mô tả hàm cho mô hình A, và ở khuôn họ bài T11/T12 của compiler | khái niệm | mỗi nơi phục vụ một tuyến | cùng thời điểm trên |
| `live_transport` ghi usage với nhãn `"function_calling"` cho mọi payload | nhỏ | B chưa chạy live | runner A/B thật phải gắn nhãn theo nhánh (`REAL_MODEL_AB_PROTOCOL.md` §5) |

Không có toán học mới trong planner. Mọi phép tính hình nằm ở engine/kernel như trước.
