# Compositional Geometry Language Analysis Design (AXO HYBRID /12 P3)

## 1. Kiến trúc tầng phân tích mệnh đề (`compositional_clause_analysis.py`)

Module [`compositional_clause_analysis.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/simulation-intent-slm-recovery/backend/app/ai/compositional_clause_analysis.py) (`COMPOSITIONAL_CLAUSE_ANALYZER_VERSION = "compositional-clause-analyzer/1"`) chuyển chuỗi đầu vào thô sang cấu trúc mệnh đề có provenance đầy đủ trước khi đi vào Local Parser và Model 1 (`Qwen3-0.6B-AxoV9`):

`Original Input -> Span-Preserving Normalization -> Controlled 1-1 Diacritic Projection (guarded) -> Compositional Clause Segmentation -> 8 Clause Roles -> Intent / Entity Binding -> Local Parser /3 or SLM /6 -> Independent Source Gate`

## 2. Chuẩn hoá bảo toàn Span (`SpanMappedText`)

- Ánh xạ từng ký tự từ `normalized_text` về chỉ mục `[char_orig_start[i], char_orig_end[i])` trong `original_text` khi xử lý Unicode NFC/NFD, `CRLF -> LF`, khoảng trắng kép, ký hiệu `ΔABC -> tam giác ABC`, `º -> °`, ký hiệu `′ -> '`.
- Phương thức `orig_quote(norm_start, norm_end)` **luôn cắt nguyên văn từ `original_text`** — tuyệt đối không dùng văn bản đã chiếu dấu hoặc văn bản chuẩn hoá làm trích dẫn giả.
- Chiếu không dấu có kiểm soát (`_project_diacritic_free`) chỉ kích hoạt khi có ngữ cảnh hình học không gian rõ ràng (danh từ khối + nhãn/quan hệ) và bị chặn chủ động trước decoy CNTT/vật lý (`mang hinh chu nhat`, `con lac lo xo`, `do thi`, `cay khung`).

## 3. Phân loại 8 vai trò mệnh đề & Phân rã câu lồng

1. `CONTEXT_HEADER`: nhãn câu/bài thi (`"Câu 2 (2 điểm)."`, `"Bài 4:"`).
2. `NEGATED_REQUEST`: phân biệt rạch ròi 3 phạm vi con (`negated_command`: `"Không vẽ..."`, `negated_premise`: `"SA không vuông góc..."`, và `meta_no_calc`: `"Chỉ cần vẽ hình, không cần tính toán:"` / `"Không cần tính gì thêm."`) để meta vô hại không bao giờ bị ép thành `contra` (`S22`) hoặc `missing` (`S09`).
3. `CONDITIONAL_PREMISE`: giữ nguyên mệnh đề điều kiện (`"Nếu ... thì ..."`, `"Giả sử ..."`) không thăng cấp thành giả thiết khẳng định; miễn trừ cụm giao tiếp `"muốn xem"` (`S35`).
4. `SIMULATION_REQUEST`: tách lead-in mô phỏng đứng trước khai báo khối lồng (`"Vẽ/Mô phỏng/Dựng/Biểu diễn/Hiển thị/Em muốn xem ... [chỉ khối]"`).
5. `OBJECT_DECLARATION` & `GEOMETRIC_CONSTRAINT`: phần khai báo đối tượng và giả thiết hình học được gán biên span nguyên bản tách rời khỏi động từ mô phỏng ở đầu và mục tiêu số ở cuối.
6. `MEASUREMENT_REQUEST`: mục tiêu số ở cuối câu tách qua `, rồi / và / sau đó / đồng thời / ; + tính|tìm|xác định`, bảo toàn nguyên cụm cho multi-goal (`và tính thể tích và khoảng cách...`).
7. `VISUALIZATION_REQUEST`: tách yêu cầu hiển thị đối tượng định danh (`"biểu diễn đường cao KE"`) khỏi cụm mơ hồ `"biểu diễn khoảng cách / góc"` không có động từ `"tính"` (`AMBIGUOUS_DISTANCE_OR_ANGLE_VISUALIZATION` theo quyết định `A3`).

## 4. Kết quả kiểm thử P3 (dev/historical `/11`, `V12` holdout chưa chạm)

- `test_v12_compositional_clause_analysis.py`: **5/5 PASSED**.
- Kiểm định trên 114 ca `/11` (`CLAUSE_SEGMENTATION_EVALUATION.json`, `SOURCE_SPAN_PROVENANCE_AUDIT.json`):
  - `exact_orig_span_mismatch_count = 0` trên toàn bộ mệnh đề được tách.
  - `simulate_only_intent_detected = 39/39`.
  - `simulate_and_query_intent_detected = 15/16` (`Q16` `"Biểu diễn ... và khoảng cách ..."` thiếu động từ `"tính"` nên không tự suy diễn thành `MEASUREMENT_REQUEST` theo `A3`).
  - `diacritic_projected_valid = 3` (`S37`, `S38`, `C24`).
