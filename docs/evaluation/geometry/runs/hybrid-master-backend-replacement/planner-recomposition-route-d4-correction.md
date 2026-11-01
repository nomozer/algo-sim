# Đính chính: tái tổ hợp của Planner `/23` trên tuyến `/4` (Continuation 12, §IV + §IX)

> **CORRECTS:** `planner-recomposition-audit.md`, câu "Delivered on Route D `/4`… Generalized Planner Recomposition" trong
> `HYBRID_MASTER_EPIC_CURRENT_STATE.md` (Eleventh continuation) và mục "Newly certified and generalized on Hybrid `/4`"
> của `owner-go-request.md` (update eleventh continuation). Các bản gốc giữ nguyên; lớp này thay phần tuyên bố về `/4`.
> **Loại bằng chứng:** `IMPLEMENTER_AUTHORED_DEVELOPMENT_DIAGNOSTIC`, offline, 0 provider call. Biên nhận:
> `route-d4-representation-probe.json` (sinh bởi `tools/route_d4_representation_probe.py`). Product không đổi
> (candidate `800ab355`, `184c64ff…`).

## 1. Điều gì sai trong tuyên bố cũ

Ma trận 24 ca (`planner-recomposition-matrix.json`) chạy **mọi ca qua `TypedFact` phẳng** (`run_fact_route`, tuyến B):
câu hỏi ở đó mang `point_kind` nên một điểm mô tả không đặt tên ("hình chiếu vuông góc của A lên SB") đi được vào
planner. 9 ca `DISCOVERED_FUNCTION_COMPOSITION` là thật **trên tuyến B** (khoá bởi `test_planner_recomposition_oracle.py`).

Tuyến mà `/api/analyze` opt-in, S-2 và live paired đo là **`/4`**: `TypedFactNextPayloadV2` → `typed_fact_next_bridge`
→ cùng planner. Bridge chỉ nhận toán hạng mục tiêu là **nhãn đã đặt tên** (`_distance_question`, `_angle_question`,
`_operand`), và `through_point` của mặt phẳng phụ cũng là nhãn. Không có dạng nào cho điểm mô tả.

| Ca probe | Dạng (analogue C11) | Kết quả `/4` |
|---|---|---|
| U1 | đoạn nối C với hình chiếu của A lên SB (C1a) | `REFUSED INVALID_MATH_GOAL` |
| U2 | khoảng cách từ trung điểm của SC đến (ABCD) | `REFUSED INVALID_MATH_GOAL` |
| U3 | đoạn nối trung điểm SA với trung điểm BC (D2) | `REFUSED INVALID_MATH_GOAL` |
| U4 | (P) qua hình chiếu của A lên SD, ∥ (SBC) (C5) | `REFUSED INVALID_QUALIFIED_REF` |
| N1 | đối chứng có tên: d(A, SC) | `SERVED 2√6/3` (tính tay khớp), `REGISTERED_DECOMPOSITION` |
| N2 | đối chứng có tên: qua K = hình chiếu của A lên SD | `SERVED 3√2/2` (tính tay khớp), `REGISTERED_DECOMPOSITION` |

Trên 52 ca SERVED gold của `student_language_probe.py` chạy qua `/4`: 50 `SOURCE_EXPLICIT_SEQUENCE`,
2 `REGISTERED_DECOMPOSITION`, **0 `DISCOVERED_FUNCTION_COMPOSITION`**.

**Tuyên bố đúng:** planner `/23` tự tái tổ hợp hàm qua needs/effects trên tuyến B. Trên `/4`, lớp bài có điểm mô tả không
đặt tên là `REPRESENTATION_BLOCKED` (hợp đồng mục tiêu), fail-closed, 0 wrong-served. Trên `/4` chỉ phục vụ được chuỗi có
tên (`SOURCE_EXPLICIT_SEQUENCE`) và hai quy tắc phân rã đã đăng ký (điểm–đường, mặt phẳng phụ qua điểm có tên).

## 2. D1/D2 theo checklist §IX

| Câu hỏi | D1 (mô tả lồng 2 tầng) | D2 (hai đầu mút không tên) |
|---|---|---|
| Registry có đủ producer? | Có (`midpoint`, `orthogonal_projection`, `ask_length`) | Có (`midpoint` ×2, `ask_length`) |
| Có kế hoạch hợp lệ? | Có, oracle độc lập: 3 bước, √2 | Có, oracle: 3 bước, √6 |
| `TypedFactNext` biểu diễn được goal? | **Không** — và cả dạng một tầng cũng không (U1–U4) | **Không** (U3) |
| Bridge làm mất thông tin? | Bridge từ chối có mã, không mất im lặng | như D1 |
| Planner nhận được nếu biểu diễn đủ? | Một tầng: có (tuyến B). Lồng: không — câu hỏi phẳng mang một `point_kind` | Không — mỗi câu hỏi phẳng mang một điểm mô tả |

Phân loại trên `/4`: D1, D2 **và** 9 ca C của C11 đều `REPRESENTATION_BLOCKED`, không phải `REACHABLE_BUT_SEARCH_MISSED`.
Không có lỗi tìm kiếm nào được chứng minh trên `/4`.

## 3. Bằng chứng về giá trị sử dụng (để quyết định có mở hợp đồng không)

Quét toàn bộ đề hình không gian trong các corpus đánh giá của kho (mẫu: câu không mở đầu bằng "Gọi/Lấy/Cho" có
"từ/nối/đến/giữa/và/qua/của + trung điểm/trọng tâm/hình chiếu/giao điểm + của/cạnh/đoạn/nhãn"):

- `independent-nlu-extraction-evaluation` (60 đề, tác giả là subagent không truy cập kho — **không phải người**): **2/60**
  ("Tính khoảng cách từ trung điểm của cạnh SC đến mặt phẳng (ABCD)", "Tính khoảng cách từ O đến trọng tâm của tam giác ABC").
- Wave 2 (90) và Wave 3 (130), curator độc lập, thiên về thiết diện: **0**.
- Các corpus phát triển còn lại: 0.

Giới hạn: regex là bộ lọc, không phải bộ đếm đã kiểm tay trên toàn bộ; mẫu số nhỏ; không có corpus sách giáo khoa thật.
Không suy ra tỷ lệ trong dân số đề thật.

## 4. Hệ quả và quyết định (không tự triển khai)

Tiêu chí 2 của live paired chỉ chịu được thua khoảng 2/45 ca serve. Nếu tác giả độc lập viết vài đề dạng này, Hybrid sẽ
từ chối (`INVALID_MATH_GOAL`) trong khi LLM_ONLY có thể phục vụ — một nguồn `HYBRID_CUTOVER_NO_GO` có thể biết trước.

Mở hợp đồng là đổi **bề mặt mô hình của arm Hybrid** (bridge + lời dặn trong `TransportExtractor`; `MathGoalSpec.target`
vốn là `dict` mở nên lược đồ JSON có thể không đổi), nên kéo theo candidate mới, Full T3, review độc lập, approval mới.
Bằng chứng giá trị hiện có (2/60, tác giả agent) chưa đủ để tự làm. Đưa thành quyết định Owner **R-1** trong
`owner-go-request.md`. D1 (lồng) cần thêm biểu diễn lồng ở cả câu hỏi phẳng — không đề xuất ở mốc này.
