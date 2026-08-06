# M17 — Pedagogical alignment audit (bản rút gọn)

**READ-ONLY.** Không sửa production/dataset/EvalItem/CURRENT_STATE, không chạy
LLM, không chạy Chrome, **0 ảnh mới**, không commit. Baseline `887ec10`, tree sạch.

## 1. Kết luận điều hành

1. **Bốn năng lực đại diện phủ đủ bốn kiểu tương tác** — và tiền đề đó đã được
   **xác minh bằng code**, không phải giả định: `predict` + `whatif_swap`
   (bubble_sort), `toggle` (boolean_dag), chỉ timeline (character_encoding),
   `predict` + 2D/3D (protocol_encapsulation).
2. **Không có target nào cần sửa trước pilot.** Không ca nào có learner task bất
   khả thi hay UI dựng sai cơ chế.
3. **Điểm yếu thật không nằm ở tương tác mà ở NEO CHƯƠNG TRÌNH.** Ba family mới
   nhất — `tree_traversal`, `relational_table_query`, `bounded_control_flow` —
   **không có case nào khai `learning_objective`**. Đây là lỗ **siêu dữ liệu**, vá
   được bằng cách thêm eval case qua `check_admission`, **không** cần family mới.
4. Quyết định phạm vi: **`FREEZE_AT_11_FAMILIES`** (lý do đầy đủ ở
   `family_scope_decision.md`).
5. **Không có bằng chứng nào về tác động học tập.** `learner impact =
   NOT_EVALUATED` — và checkpoint này không thể thay đổi điều đó.

## 2. Phương pháp và giới hạn

Nguồn bằng chứng **chỉ** trong repo: catalog + descriptors, `coverage.py`,
`authenticity.py`, hợp đồng module FE, eval dataset, artifact đánh giá đã có.

Giới hạn quyết định nhất, do **chính repo tự khai**:

> `docs/COVERAGE.md`: taxonomy ở **mức TÊN BÀI**, *không phải* mức **yêu cầu cần
> đạt**; và *"**VẪN CHƯA CÓ:** cấu trúc mục tiêu → nhiệm vụ → chấm điểm"*.

`curriculum_anchor` trong catalog chỉ là con trỏ bài (`'T11CS B21–22'`). Nguồn mục
tiêu **có neo** duy nhất là `EvalItem.learning_objective`, được cổng
`check_admission` gác và khoá bằng test: **95/113 case** khai đủ
`learning_objective` + `pedagogical_rationale`.

Vì vậy audit đầy đủ objective/task/assessment/rubric **chỉ** thực hiện cho hai
target có neo. Hai target còn lại ghi `CURRICULUM_ANCHOR_INCOMPLETE` — **không tự
sáng tác mục tiêu**, đúng §3.

**Cảnh báo đọc số:** một family hiện `GROUNDED` **không** đồng nghĩa mọi target
trong đó có neo. `boolean_composition` GROUNDED nhờ `logic.and_gate` +
`generic.rule_scene`, còn `logic.boolean_dag` có **0**; `positional_representation`
GROUNDED nhờ `base_conversion`/`decimal_to_binary`, còn `binary.character_encoding`
có **0**.

## 3. Light scan — 11 family

| Family | Target đại diện | Neo chương trình | Vai trò luận văn |
|---|---|---|---|
| `comparison_sort` | `algorithm.bubble_sort` | GROUNDED (8) | **CORE_EVIDENCE** |
| `layered_pdu_transform` | `network.protocol_encapsulation` | GROUNDED (6) | **CORE_EVIDENCE** |
| `boolean_composition` | `logic.boolean_dag` | GROUNDED (18) *ở family*, **0 ở target** | **CORE_EVIDENCE** |
| `positional_representation` | `binary.character_encoding` | GROUNDED (8) *ở family*, **0 ở target** | **CORE_EVIDENCE** |
| `single_pass_scan` | `algorithm.count_if` | GROUNDED (16) | SUPPORTING_EVIDENCE |
| `interval_elimination` | `algorithm.binary_search` | GROUNDED (6) | SUPPORTING_EVIDENCE |
| `graph_traversal` | `network.graph_traversal` | GROUNDED (5) | SUPPORTING_EVIDENCE |
| `structural_progressive_representation` | `generic.rule_scene` | GROUNDED (16) | **REPRESENTATION_ONLY** |
| `tree_traversal` | `tree.traversal` | **INCOMPLETE (0)** | NEEDS_REVIEW |
| `relational_table_query` | `database.relational_table_query` | **INCOMPLETE (0)** | NEEDS_REVIEW |
| `bounded_control_flow` | `algorithm.bounded_control_flow` | **INCOMPLETE (0)** | NEEDS_REVIEW |

`generic.rule_scene` giữ **REPRESENTATION_ONLY** — `result_authority =
representation`, **không** tính là mô phỏng cơ chế tính toán. Đây là phân vai
đúng, không phải lỗi.

Ba family `NEEDS_REVIEW` đều là wave M17 mới nhất (W2A/W2B/W2C): năng lực đã
ship và có test, nhưng **chưa ai viết mục tiêu học tập cho chúng**.

## 4. Deep audit — bốn target

### 4.1 `algorithm.bubble_sort` — audit ĐẦY ĐỦ

| Trục | Nội dung |
|---|---|
| **Objective** (có neo) | *"Giải thích một lượt duyệt của sắp xếp nổi bọt làm gì và vì sao thuật toán dừng."* · *"Nhận ra cơ chế đổi-chỗ-cặp-kề qua MÔ TẢ, không qua tên gọi."* (`cap-bubble`, `cap-bubble-paraphrase`, `m16-bubble-*`; T11CS.CD6, L2) |
| **Cơ chế** | quyết định so sánh → đổi chỗ ở từng cặp **kề nhau**; đuôi đã sắp lớn dần |
| **Observable state** | `config`, `trace`, `cursor`; sự kiện `compare`/`swap`/`mark`/`done`; renderer bắt buộc có `array_columns`, `narration_per_step`, `pseudocode_line` |
| **Causal transition** | Có — mỗi bước là `compare` rồi `swap` (hoặc không), nhìn được state trước/sau |
| **Learner task** | "Trước bước kế tiếp, dự đoán cặp được so sánh và có đổi chỗ không; sau đó giải thích thay đổi của dãy." |
| **Interaction fit** | **SUFFICIENT** — `predict` + `whatif_swap` + timeline đủ cho task |
| **Feedback tất định** | `predict.check` chấm bằng **trace thật**, không gọi LLM (`types.ts` cấm cứng); `whatif_swap` sinh nhánh hệ quả |
| **Alignment** | **READY_WITH_LIMITATION** (cần phiếu học tập dẫn dắt phần "giải thích") |

**Assessment (BẢN NHÁP — chưa kiểm định, chưa qua giáo viên):**
- *Trước:* "Với dãy `[5, 1, 4]`, lượt duyệt đầu tiên so sánh những cặp nào?"
- *Trong:* "Dự đoán 3 bước liên tiếp; ghi lại bước em đoán sai và vì sao."
- *Sau/chuyển giao:* "Vì sao sau lượt thứ nhất, phần tử lớn nhất chắc chắn ở cuối dãy?"
- *Rubric ngắn:* 2đ nêu đúng **cặp kề**; 2đ nêu điều kiện **đổi chỗ**; 1đ nêu **đuôi đã sắp** lớn dần.

### 4.2 `network.protocol_encapsulation` — audit ĐẦY ĐỦ

| Trục | Nội dung |
|---|---|
| **Objective** (có neo) | *"Mô tả được PDU ở từng tầng và giải thích tháo gói là quá trình NGƯỢC của đóng gói."* · *"Phân biệt cơ chế ĐÓNG GÓI theo tầng với việc gói tin ĐI QUA thiết bị trung gian."* (`cur-t12-encap*`, `m16-encap-*`; T12.CD2, L2–L3) |
| **Cơ chế** | PDU biến đổi qua 4 tầng; tính **đối xứng** đóng gói ↔ tháo gói |
| **Observable state** | `payloadLabel`, `layers`, `steps`, `cursor`; sự kiện `add`/`remove`/`transmit`/`deliver` |
| **Causal transition** | Có — mỗi bước thêm/gỡ đúng phần của một tầng, theo thứ tự cố định |
| **Learner task** | "Dự đoán tầng kế tiếp và thành phần được thêm/gỡ; rồi đối chiếu cùng trạng thái đó ở 2D và 3D." |
| **Interaction fit** | **SUFFICIENT** — `predict` + timeline; 2D/3D dùng **chung** state (bất biến #16) |
| **Feedback tất định** | `predict.check` chấm theo `steps` của engine |
| **Alignment** | **READY_WITH_LIMITATION** (3D là bằng chứng **bổ sung**, không phải chính) |

**Assessment (BẢN NHÁP — chưa kiểm định):**
- *Trước:* "Kể tên 4 tầng theo thứ tự dữ liệu đi xuống ở máy gửi."
- *Trong:* "Ở mỗi bước, dự đoán tầng kế tiếp và phần thông tin được thêm."
- *Sau/chuyển giao:* "Vì sao máy nhận phải gỡ theo thứ tự **ngược lại**?"
- *Rubric ngắn:* 2đ đúng thứ tự tầng; 2đ nêu **mỗi tầng thêm phần của mình**; 1đ giải thích **đối xứng** gửi–nhận.

⚠️ Một objective có neo bắt đầu bằng **"Hiểu dữ liệu được THÊM DẦN…"** — động từ
`hiểu` nằm trong danh sách **mơ hồ bị cấm** của chính khung đánh giá. Đây là việc
sửa câu chữ trong dataset, **không** sửa trong checkpoint read-only này.

### 4.3 `logic.boolean_dag` — `CURRICULUM_ANCHOR_INCOMPLETE`

**Không viết objective/assessment/rubric** (0 case có neo cho target này).
Các trục còn lại vẫn đánh giá được:

- **Cơ chế:** lan truyền phụ thuộc Boolean qua DAG nhiều cổng.
- **Observable state:** `values`, `evalOrder`, `nodeOutputs`, `steps`, `truthTable`,
  `cursor` — renderer bắt buộc `gate_table_with_engine_outputs` + `truth_table_panel`.
- **Causal transition:** Có — `toggle` một đầu vào → engine tính lại downstream;
  `evalOrder` phơi **thứ tự đánh giá**, tách bạch với **giá trị** node.
- **Interaction fit:** **SUFFICIENT** — `toggle` là thao tác chạm đúng cơ chế ẩn.
- **Feedback tất định:** state đổi + bảng chân trị do engine sinh.
- **Alignment:** **INSUFFICIENT_EVIDENCE** — thiếu neo mục tiêu, **không** thiếu năng lực.

### 4.4 `binary.character_encoding` — `CURRICULUM_ANCHOR_INCOMPLETE`

**Không viết objective/assessment/rubric** (0 case có neo cho target này).

- **Cơ chế:** ký tự → mã → thập phân → **chia lấy dư** → dãy số dư → nhị phân.
- **Observable state:** `spec`, `trace`, `cursor`, `rows`; renderer bắt buộc
  `code_point_after_mapping_only` và `binary_after_conversion_only` — tức **cấm**
  công bố dãy bit trước khi cơ chế chạy.
- **Causal transition:** Có, và đã chứng minh bằng E2E C1: `65 : 2 = 32 dư 1`,
  DOM bước đầu chưa có `1000001`.
- **Interaction fit:** **SUFFICIENT_WITH_SCAFFOLD** — timeline đủ cho nhiệm vụ
  *quan sát và giải thích*; phần "giải thích vì sao đọc ngược số dư" cần phiếu học
  tập, **không** cần thêm prediction.
- **Feedback tất định:** thuyết minh theo từng bước trace. Lưu ý: đây là **narration
  theo trace**, **không** phải phản hồi cho hành động của học sinh — vì target
  không có learner action nào.
- **Alignment:** **READY_WITH_LIMITATION** cho ca **ASCII**; ca Unicode chưa dùng
  được ở đường live (`W3-LIVE PARTIAL — CLOSED`).

## 5. Interaction-fit — tổng hợp

| Target | Mức | Fit |
|---|---|---|
| `algorithm.bubble_sort` | PREDICTION_OR_WHAT_IF | **SUFFICIENT** |
| `network.protocol_encapsulation` | PREDICTION + 2D/3D | **SUFFICIENT** |
| `logic.boolean_dag` | MECHANISM_ACTION | **SUFFICIENT** |
| `binary.character_encoding` | TIMELINE_CONTROL | **SUFFICIENT_WITH_SCAFFOLD** |

**Không đề xuất nâng interaction cho bất kỳ target nào.** Với W3, mục tiêu là
*quan sát và giải thích một cơ chế tất định*; thêm prediction sẽ là nâng cấp theo
**hình thức**, không theo mục tiêu — đúng thứ §13 cấm. Phiếu học tập rẻ hơn và đủ.

## 6. Rủi ro hiểu nhầm

| Target | Rủi ro | UI hiện xử lý ra sao |
|---|---|---|
| `bubble_sort` | tưởng "nổi bọt" là phần tử **nhảy** thẳng về cuối | `array_columns` + narration từng cặp **sửa** được |
| `bubble_sort` | tưởng thuật toán dừng khi dãy "trông đã sắp" | sự kiện `done` phơi điều kiện dừng thật |
| `boolean_dag` | lẫn **giá trị** node với **thứ tự đánh giá** | `evalOrder` tách riêng khỏi `nodeOutputs` — **sửa** được |
| `character_encoding` | nhầm ký tự `'7'` với số `7` | đã vá ở W3-VR (bọc nháy) — **sửa** được |
| `character_encoding` | tưởng dãy bit tự xuất hiện, không qua phép chia | hợp đồng `binary_after_conversion_only` **chặn** |
| `character_encoding` | nhầm Unicode code point với **byte UTF-8** | **CHƯA xử lý** — UI không nói rõ ranh giới này |
| `protocol_encapsulation` | đọc trục **Z** là khoảng cách vật lý | `threeD.role = pedagogical` (Z = tầng) nhưng UI **chưa chú thích** rõ cho học sinh |

Hai rủi ro **chưa xử lý** (UTF-8, trục Z) là ứng viên tốt cho phiếu học tập, không
nhất thiết phải sửa UI.

## 7. Claim audit — bảy tuyên bố

| # | Tuyên bố | Trạng thái | Căn cứ |
|---|---|---|---|
| 1 | Hệ thống **hỗ trợ dạy học** Tin học THPT | **SUPPORTED_WITH_LIMITATION** | có neo bài SGK + mục tiêu có cổng, nhưng **chưa có người học** |
| 2 | Người học **quan sát cơ chế từng bước** | **SUPPORTED** | authenticity contract + REAL_SIMULATION + E2E C1 (DOM/trace) |
| 3 | Người học **tương tác** với mô phỏng | **SUPPORTED_WITH_LIMITATION** | đúng với 3/4 target; `character_encoding` **không có** learner action |
| 4 | 2D/3D biểu diễn **cùng state** | **SUPPORTED** | bất biến #16 + #18, khoá bằng test |
| 5 | Mô phỏng **giúp học sinh hiểu tốt hơn** | **NOT_VERIFIED** | không có dữ liệu người học |
| 6 | LLM **chuyển đề tự nhiên thành mô phỏng** | **SUPPORTED_WITH_LIMITATION** | W3-LIVE **PARTIAL — CLOSED**; định tuyến 6/6 nhưng Unicode chưa qua |
| 7 | **Bao phủ chương trình** Tin học THPT | **OVERCLAIM — cấm dùng** | COVERAGE.md chỉ cho phép "phủ **đại diện**, mức tên bài" |

Câu chữ đề nghị cho luận văn (chưa sửa tài liệu canonical): thay "bao phủ chương
trình" bằng **"phủ đại diện, có neo nguồn, ở mức tên bài của SGK"**; thay "giúp
học sinh hiểu tốt hơn" bằng **"phơi bày cơ chế ẩn theo từng bước tất định"**.

## 8. Pilot readiness (một đoạn)

Sản phẩm **đã đủ điều kiện để THIẾT KẾ** pilot, chưa đủ để chạy. Bước hợp lý kế
tiếp là nhờ **1–2 giáo viên Tin học** rà bốn năng lực đại diện về độ chính xác,
độ khớp mục tiêu và nguy cơ gây hiểu nhầm; nếu đạt thì thử với một nhóm nhỏ theo
khung *pre-task → dùng mô phỏng → post/transfer → phiếu hỏi ngắn*. Chưa thu dữ
liệu nào, chưa chọn cỡ mẫu, chưa chọn kiểm định thống kê, và **chưa được phép
tuyên bố tác động học tập**. Việc liên hệ giáo viên và thu dữ liệu người học nằm
ngoài mọi checkpoint kỹ thuật.

## 9. Việc hoãn lại

1. **Thêm eval case có `learning_objective` cho 3 family `NEEDS_REVIEW`**
   (`tree_traversal`, `relational_table_query`, `bounded_control_flow`) và cho 2
   target `CURRICULUM_ANCHOR_INCOMPLETE` (`logic.boolean_dag`,
   `binary.character_encoding`) — qua `check_admission`, **không** cần family mới.
2. Sửa câu chữ objective dùng động từ mơ hồ ("Hiểu…", "Thấy…") trong dataset.
3. Chú thích học sinh cho trục Z (3D = tầng giao thức, không phải khoảng cách) và
   ranh giới code point ↔ byte UTF-8.
4. `U+1EBF` ở đường live vẫn chưa đo được (W3-LIVE đã đóng ở PARTIAL).
5. Part B: `BLOCKED_NO_DOCX`.
