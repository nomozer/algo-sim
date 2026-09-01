# REPLAYABLE_STABILITY_SEED — hạt giống cho phép đo độ ổn định k=3

> Chụp đầu vào tổng hợp **đủ để chạy lại**, cộng đúng một quan sát tổng hợp
> ban đầu cho mỗi ca. 12 lượt provider, **không sửa**, chạy một lần.

Đóng băng `f774a332`, cây sạch, `CACHE_VERSION 58`, prompt `b8bb766b`, thẻ
`d409584f`, miền `hinh_hoc`. Đề khớp manifest `CLEAN_BASELINE_V2` **6/6** theo
byte.

## 0. Đây KHÔNG phải một lượt đánh giá khái quát hoá

Sáu đề này mô hình **đã thấy** ở `CLEAN_BASELINE_V2`. Gọi lượt này là "chạy
lại V2" hay "đánh giá khái quát hoá" là nói sai.

Tên đúng: **repeat 1 của một phép đo độ ổn định.** Điểm lịch sử
`CLEAN_BASELINE_V2 = 6/6` **không đổi**, và `4/6` dưới đây **không được đem so
với nó** — hai lượt hỏi hai câu khác nhau, và lượt này còn khác một điều kiện
quyết định: **không có lượt sửa**.

## 1. Mục tiêu của wave: INPUT_EQUIVALENCE

| | |
|---|---|
| REQUEST_CONTRACT_RAW_CAPTURED | **6/6** |
| REQUEST_CONTRACT_ROUNDTRIP | **6/6** |
| MODEL_INPUT_PAYLOAD_CAPTURED | **6/6** |
| MODEL_INPUT_HASH_REPLAY | **6/6** |
| **INPUT_EQUIVALENCE** | **PASS** |
| ARTIFACT_REPLAYABLE | **YES** |

Kiểm **hai chiều**, cả hai chạy từ đĩa với 0 lượt provider:

    tự chứa   payload lưu trong artifact băm ra đúng hash đã ghi
    dựng lại  ghép từ MẢNH (đề + hợp đồng + thẻ) ra đúng hash ấy

Chiều một chứng minh artifact đứng vững **khi mã đã refactor**; chiều hai
chứng minh **mã hiện tại thật sự tái tạo được**. Chỉ một chiều thì hoặc ta tin
một bản sao, hoặc ta tin một công thức có thể đã đổi.

`test_probe_artifact_replayable.py` chạy lại phép kiểm ấy trong suite — nó
**không** đọc cờ `input_equivalence` mà artifact tự ghi, vì tin cờ ấy là tin
bị cáo.

## 2. Ngân sách

| | |
|---|---|
| ANALYZE_CALLS | 6 |
| INITIAL_SYNTHESIS_CALLS | 6 |
| REPAIR_CALLS | **0** |
| TOTAL_PROVIDER_CALLS | **12/12** |
| ANALYZE_TOKENS | 11.711 |
| SYNTHESIS_TOKENS | 34.356 |
| TOTAL_TOKENS | 46.067 |

Trần cưỡng chế ở **biên gọi**: lượt tổng hợp thứ hai của bất kỳ ca nào bị chặn
*trước khi gửi*, nên nó tiêu 0 token.

## 3. Repeat 1 — quan sát, không phải kết luận

`REPEAT_1_CORRECT = 4/6`

| đề | repeat 1 | `construct_point` chọn | program hash |
|---|---|---|---|
| `v2_01` tứ diện | ĐÚNG | `M, N, I` | `67fc2a56` |
| `v2_02` lăng trụ | **HỎNG · SCHEMA** | — | — |
| `v2_03` lập phương | ĐÚNG | `M, I` | `957f3be3` |
| `v2_04` thiết diện | ĐÚNG | `M, N, P, O, I, Q` | `3b080ca6` |
| `v2_05` góc hai đường | **HỎNG · SCHEMA** | — | — |
| `v2_06` giao rồi chiếu | ĐÚNG | `I, H` | `83a63d18` |

Hai ca hỏng **cùng một lỗi**:

    statements.0.construct_point.expr
      Input tag 'arith' found using 'kind' does not match any of the expected
      tags: intersect_line_plane, intersect_line_line, midpoint,
      project_onto, divide_segment

Mô hình đặt một biểu thức **số học** vào `construct_point`, nơi hợp đồng chỉ
nhận năm phép dựng ra điểm.

⚠️ Đây là một **quan sát**, không phải một chẩn đoán, và wave này không hành
động theo nó (§17). Ghi thêm để lượt sau đọc đúng bối cảnh: cùng lớp lỗi đã
được ghi ở `CACHE_VERSION 46` — *"`construct_point C = arith(B + D)` xuất hiện
ở HAI vòng đo độc lập"* — nên nay là lần thứ ba. Nó cũng chính là lỗi mà
`AMBIGUOUS_FIRST_BINDING` đã bắt ở `cb_04` của V1, chỉ khác chỗ lần này schema
bắt trước.

`v2_04` đáng chú ý theo hướng khác: mô hình dựng **sáu** điểm (`M, N, P, O, I,
Q`) trong khi lời giải chuẩn tắc dùng ba. Chương trình vẫn qua toàn bộ cổng và
khớp oracle — bằng chứng cho việc mô hình **tổ hợp** chứ không chép một khuôn.

## 4. Điều wave này KHÔNG kết luận (§15)

- Không nói hệ tốt hơn hay kém hơn `CLEAN_BASELINE_V2`.
- Không nói `4/6` là độ chính xác của bất cứ thứ gì. Nó là **một** quan sát
  cho mỗi ca, và một quan sát không đo được độ ổn định — đó là toàn bộ lý do
  wave k=3 tồn tại.
- Không đổi `probe.json` của V2.

## 5. Sẵn sàng cho k=3

`INPUT_EQUIVALENCE = PASS` và `ARTIFACT_REPLAYABLE = YES`

⇒ `READY_FOR_SYNTHESIS_STABILITY_K3 = YES`

Lượt kế tiếp dùng hạt giống này làm **R1**, và cần đúng:

    0 analyze · 6 tổng hợp R2 · 6 tổng hợp R3 · 0 sửa · trần 12 lượt

R2/R3 phải khẳng định `MODEL_INPUT_HASH == model_input_hash` của R1 trước khi
gửi — artifact đã mang sẵn hash ấy cho cả sáu ca.
