# Hợp đồng Typed Facts (nhánh B, thực nghiệm)

Phiên bản `geometry-fact-planner/1`. Nguồn sự thật là mã: `backend/app/simulation/geometry_functions/planner.py::TypedFact`
(Pydantic, `extra="forbid"`). Lược đồ provider được sinh từ chính model đó (`app/ai/fact_extraction.py::facts_response_schema`).
Tài liệu này mô tả hợp đồng, **không** phải contract sản phẩm đang hiệu lực. B không phải mặc định và chưa nối vào route nào.

## 1. Nguyên tắc

1. Mô hình **chỉ trích**: không chọn phép dựng, không tính, không viết toạ độ hay mã. Không có ô toạ độ nào trong lược đồ.
2. Mỗi mệnh đề của đề là một dữ kiện. Mỗi dữ kiện có `quotes` chép **nguyên văn** từ đề. Planner chuyển quote sang lời gọi,
   rồi cổng nguồn 5 tầng của registry kiểm như với nhánh A.
3. Vai trò mệnh đề là dữ liệu, không phải hành vi của mô hình. Mô hình gắn nhãn; planner quyết định.
4. Không chắc thì `ambiguous = true`. Planner từ chối, không đoán.
5. Lược đồ phẳng: một đối tượng, các ô dùng tuỳ `kind`. Lý do: structured output của provider diễn đạt kém `oneOf`.

## 2. Ô chung

| ô | kiểu | bắt buộc | nghĩa |
|---|---|---|---|
| `id` | chuỗi ≥ 1 ký tự, duy nhất | có | định danh, đi vào trace và id lời gọi |
| `kind` | 11 giá trị, §3 | có | loại dữ kiện |
| `role` | `premise` · `prove` · `condition` · `question` | có | đề cho · điều phải chứng minh · trong "nếu … thì" · đề hỏi |
| `negated` | bool, mặc định false | không | mệnh đề bị phủ định trong đề |
| `ambiguous` | bool, mặc định false | không | mô hình không chắc cách hiểu |
| `quotes` | danh sách chuỗi, ≥ 1 | có | đoạn nguyên văn làm căn cứ |

## 3. Loại dữ kiện và ô bắt buộc

Ô bắt buộc thiếu ⇒ `FACT_INCOMPLETE` (`planner._CAN`).

| `kind` | ô bắt buộc | ô tuỳ chọn | ví dụ |
|---|---|---|---|
| `solid` | `solid`, `solid_type` (`pyramid` · `prism` · `tetrahedron` · `cube` · `cuboid`) | `regular`, `right` | "hình chóp tứ giác đều S.ABCD" |
| `polygon_shape` | `points`, `shape` (`equilateral_triangle` · `square` · `regular_hexagon` · `regular_polygon` · `rectangle` · `triangle`) | `value` (cạnh) | "đáy ABC là tam giác đều cạnh 2" |
| `right_angle` | `at`, `points` | | "vuông tại B" |
| `length` | `value`, `measure` (`segment` · `base_edge` · `lateral_edge` · `height` · `edge`) | `points` (khi `segment`), `solid` (khi khác `segment`) | "cạnh bên bằng a√2" |
| `equal_lengths` | `points_a`, `points_b` | | "SA = SB" |
| `perpendicular` | `points_a`, `points_b` (1 điểm / 2 = đường / ≥ 3 = mặt) | | "SA vuông góc với (ABC)" |
| `altitude` | `points`, `solid` | | "SH là đường cao của hình chóp" |
| `projection` | `point`, `points`, `at` | | "hình chiếu của S lên (ABC) là H" |
| `point_def` | `point`, `point_kind` (`midpoint` · `centroid`), `points` | | "M là trung điểm BC" |
| `question` | `quantity` (`volume` · `area` · `length` · `distance` · `angle`) | `solid`, `points`, `points_a`, `points_b` | "Tính khoảng cách giữa AM và B′C" |
| `unsupported` | `reason` | | mệnh đề không có loại phù hợp |

Giá trị (`value`) theo `ExactNumber` của registry: chép từ đề (số nguyên, thập phân, phân số, căn, có hoặc không có ký hiệu
`a`). `registry.doc_so` đọc thành số chính xác, không qua float (`1,5` thành 3/2).

## 4. Planner xử lý vai trò thế nào

| trường hợp | hành vi |
|---|---|
| có `ambiguous` | toàn bộ đề `AMBIGUOUS_FACT` |
| có `role = condition` | toàn bộ đề `CONDITIONAL_CLAUSE` |
| `role = prove` | **không** dựng; giữ làm mục tiêu, kiểm sau khi dựng: `HOLDS` / `FAILS` ⇒ `PROOF_GOAL_FALSE` / `UNVERIFIABLE` (vẫn phục vụ) |
| `negated = true` | **không** dựng; kiểm sau khi dựng: phải `FAILS`; `HOLDS` ⇒ `INCONSISTENT_FACTS`; `UNVERIFIABLE` ⇒ `NEGATED_CLAUSE` |
| `solid` có `negated` | khối vẫn có, tính ĐỀU bị bỏ ("không phải chóp đều") |
| `role = question` | sinh lời gọi `ask_*`; câu hỏi không bao giờ gộp |

## 5. Phản hồi provider

Một lượt gọi mỗi đề. `responseMimeType = application/json`, `responseSchema = facts_response_schema()`, không có `tools`.
Bộ đọc phản hồi (`parse_response`) trả mã:

`PROVIDER_RESPONSE_INVALID` · `PROVIDER_BLOCKED` · `NO_CANDIDATE` · `RESPONSE_TRUNCATED` (`finishReason = MAX_TOKENS`; danh
sách dữ kiện cụt **không** đi tiếp) · `PROVIDER_REFUSED` · `JSON_INVALID` · `LIVE_AI_DISABLED` · `PROVIDER_ERROR`.

Không mã nào lùi về `LLM_ONLY` (test `test_khong_lui_ve_llm_only`).

## 6. Đổi hợp đồng

Đổi `TypedFact` hoặc `SYSTEM_PROMPT` làm đổi `fact_extraction.surface_fingerprint()` (hiện `83dcfa7a…`). Mọi lượt đo bằng
mô hình phải ghi dấu vân tay này. B không thuộc "bề mặt mô hình" có băm của `LLM_ONLY`, nên không bump `CACHE_VERSION`.
