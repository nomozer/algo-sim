# Ngữ nghĩa mục tiêu mô phỏng (P2 · Gate H1)

Số liệu: lượt 2 (candidate `a0f979392`, trình duyệt thật, `local-only-scoped`). Chi tiết từng ca:
`SIMULATION_ONLY_INPUT_EVALUATION.json`. Khoảng tin cậy Wilson 95%.

## Ba chế độ

| Chế độ | Hợp đồng sản phẩm hiện hành | Đo được (lượt 2) |
|---|---|---|
| **A — SIMULATE_ONLY** | Native: `simulation_goals=[construct_object]`, không cần `ask_*`. Không có mục tiêu số nào được bịa (0/14 ca phục vụ có `answers`). | 14/28 = 0.50 [0.33, 0.67] |
| **B — SIMULATE_AND_QUERY** | "Mô phỏng/vẽ/dựng … **và tính** …" được hiểu (luật 7b + mục tiêu toán). "… **và biểu diễn** khoảng cách/góc" **không** được hiểu là câu hỏi ⇒ Source Gate chặn (`NOT_ASKED_IN_SOURCE`, `AMBIGUOUS_VALUE_QUOTE`). Khi hỏi bằng "Tính khoảng cách …", sản phẩm đã tự dựng và chỉ ra đoạn biểu diễn (vd `AH ⊥ (SBD)`). | 5/10 = 0.50 [0.24, 0.76] |
| **C — QUERY_WITH_SCENE** | Mục tiêu toán ⇒ dựng cảnh + đáp số chính xác; cảnh được chấm riêng với đáp số. | 21/26 = 0.81 [0.62, 0.91]; đáp số 26/26 đúng |

Không có ca nào "đúng đáp số nhưng cảnh sai": mọi cảnh có đáp số đều qua oracle hình học (0/252 quan hệ vi phạm).

## Hình chưa xác định duy nhất

| Lớp | Hành vi sản phẩm | Ca |
|---|---|---|
| `UNIQUE_GEOMETRY` | Phục vụ khi đọc được. | 40 cảnh phục vụ |
| `ILLUSTRATIVE_GEOMETRY` (đề chỉ mô phỏng, thiếu kích thước) | **Không có cơ chế minh hoạ** cho chỉ-mô-phỏng. N01 (parser tất định): từ chối `AMBIGUOUS_FACT` kèm bản ghi làm rõ `MISSING_DATA` ("nói rõ các số đo cần thiết"), nhưng UI hiện "Axo chưa hỗ trợ phép dựng này" thay vì câu hỏi làm rõ. N13 (`AMBIGUOUS_FACT`), N18 (`SOURCE_OBJECT_MISMATCH`) bị chặn trên đường SLM. Cả ba an toàn. | N01, N13, N18 |
| Minh hoạ có chứng chỉ | Engine **có** `SIMILARITY_SCALE_ILLUSTRATIVE` / `HEIGHT_INVARIANT_ILLUSTRATIVE` / `TARGET_INVARIANT_ILLUSTRATIVE`, nhưng chỉ khi có một đại lượng được hỏi đã chứng minh bất biến; cảnh khi đó mang `scene_configuration` công khai là minh hoạ và kích thước minh hoạ không vào giả thiết. | không có ca nào trong bộ kích hoạt; C20 (góc AB'–BC' trong lập phương không cho cạnh) bị từ chối `MISSING_DIMENSION` dù góc xác định tới đồng dạng |
| `INSUFFICIENT_FOR_REQUESTED_MEASUREMENT` | Từ chối toàn bộ (`MISSING_DIMENSION`), không phục vụ riêng phần hình. | N02, N14 |
| `CONTRADICTORY_GEOMETRY` | Từ chối `INCONSISTENT_FACTS` / `NON_POSITIVE_LENGTH`, UI "Dữ kiện đề bài chưa nhất quán". | N03, N04, N05 |

Kết luận Mode A: **hệ mô phỏng được mà không cần câu hỏi tính toán**; giới hạn không nằm ở hợp đồng (TypedFactNext, planner) mà
ở **độ phủ câu lệnh mô phỏng của parser tất định** và việc SLM không tạo được mục tiêu `construct_object` qua Source Gate
(`SIMULATION_CONTRACT_AUDIT.md`, phát hiện 1). Không có mục tiêu số nào được tự thêm để lách; Source Gate không bị nới.
