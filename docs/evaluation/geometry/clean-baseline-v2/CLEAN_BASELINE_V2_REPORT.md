# CLEAN_BASELINE_V2 — baseline tổng hợp sau bản sửa ràng buộc lần đầu

> 6 đề mới, niêm phong trước khi gọi model, đường sản phẩm đầy đủ. Chạy một
> lần. Không sửa code hay prompt giữa các đề.

Niêm phong `c1e0f672`, cây sạch, `CACHE_VERSION 58`, miền `hinh_hoc` →
`geometry_program_generator`, prompt `b8bb766b` (4.705 B), thẻ `d409584f`
(2.996 B), seal `adbb0ca9`. Tiền kiểm PASS, nhiễm chéo SẠCH.

## 1. Kết quả

| | |
|---|---|
| ONE_SHOT_CORRECT | **5/6** |
| REPAIRED_CORRECT | 1/6 |
| **CORRECT_WITHIN_BUDGET** | **6/6** |
| SYSTEM_FAILURE | **0/6** |
| SYNTHESIS / SCHEMA / GROUNDING / HONESTY | 0 / 0 / 0 / 0 |
| FIRST_BINDING_RUNTIME_FAILURES | **0/6** |
| NEW_CODE_REQUIRED_DURING_PROBE | **0** |
| ENVELOPE_TRANSPORT | PASS |
| SYSTEM_PATTERN_REPEATED | NO |

Provider: **13 lượt** — 6 analyze + 6 tổng hợp đầu + 1 sửa.
Token: analyze 11.540 · tổng hợp đầu 40.794 · sửa 6.121 · **tổng 58.455**.
9.742 token / ca đúng · 2,17 lượt provider / ca đúng · sửa chiếm 10,5%.

## 2. Con số quan trọng nhất không phải 6/6

    CONSTRUCT_POINT_SELECTED   12
    SAFE_ASSIGN_NORMALIZED      0

Mô hình dùng dạng chuẩn tắc **12/12 lần**. Bộ chuẩn hoá không phải ra tay lần
nào.

Ở `CLEAN_BASELINE_V1` con số ngược lại: **0** lần `construct_point`, và mọi
điểm phụ đều qua `assign` — lối chết ở runtime, 4/6 ca mất trắng.

Điều đổi giữa hai lượt **không phải mô hình**. Thẻ văn phạm dẫn từ
`_TOAN_HANG_LENH`, bảng *cố ý* không chứa `construct_point`, nên thẻ **giấu
mất câu lệnh ấy**. Mô hình không chọn nhầm giữa hai lối — nó dùng lối duy nhất
được bày ra. Nay thẻ dẫn từ `_KIEU_DUNG` và mô hình chọn đúng ngay lần đầu,
không cần một lời dặn nào trong prompt.

⇒ 4/6 ca của V1 mất vì **một cái tên vắng mặt trong một danh sách**.

## 3. So với V1 — chỉ so cái so được (§20)

Hai bộ đề khác nhau, nên **không** nói "V2 tốt hơn V1" dựa trên x/6. So được
là các chỉ số CẤU TRÚC:

| | V1 | V2 |
|---|---|---|
| FIRST_BINDING_RUNTIME_FAILURES | 4/6 | **0/6** |
| SYSTEM_FAILURE | 4/6 | **0/6** |
| CONSTRUCT_POINT_SELECTED | 0 | 12 |

Điểm tổng hợp của V2 (6/6) là **baseline riêng**, không phải một phép cải
thiện đo được so với V1.

## 4. Ca duy nhất cần sửa

`v2_03` (lập phương, khoảng cách từ trung điểm đường chéo không gian tới `BM`,
đáp số `√30/5`) — một lượt sửa, rồi đúng. Đây là ca có kết quả vô tỉ duy nhất
đi kèm hai trung điểm ở hai vị trí khác loại (một trên cạnh, một trên đường
chéo không gian).

Sửa tiêu 6.121 token, 10,5% tổng — đúng khuôn §11 muốn: prompt sửa gửi mảnh
hợp đồng liên quan, không gửi lại cả thẻ.

## 5. Độ phức tạp thật sự của bộ đề

| đề | hình | vật dẫn xuất | độ sâu | nghĩa vụ | đáp số |
|---|---|---|---|---|---|
| `v2_01` | tứ diện | 6 | 5 | 1 | `4/3` |
| `v2_02` | lăng trụ | 3 | 4 | 1 | `18/17` |
| `v2_03` | lập phương | 3 | 4 | 1 | `√30/5` |
| `v2_04` | chóp + thiết diện | 6 | 5 | 2 | `4/3` |
| `v2_05` | chóp đáy chữ nhật | 3 | 4 | 1 | `3/10` |
| `v2_06` | chóp, giao rồi chiếu | 7 | 6 | 2 | `√22`, `64/3` |

Bốn phép dựng khác nhau xuất hiện: `midpoint`, `intersect_line_line`,
`project_onto`, `construct_section`. Hai đáp số vô tỉ. Hai đề hai nghĩa vụ.

`CANONICAL_EXECUTABLE = 6/6`, đo **trước** lượt live bằng cách chạy lời giải
chuẩn tắc do người viết qua toàn bộ chuỗi cổng — kể cả hậu điều kiện và cổng
vận chuyển. Lời giải ấy không vào prompt và không tính là thành công.

## 6. Spot check trình duyệt

Hai ca ưu tiên theo §19 — thiết diện/độ sâu cao (`v2_04`) và căn thức/nhiều
năng lực (`v2_06`). Chrome thật, WebGL: **8/8, 0 lỗi console**.

| ca | xưởng 3D | cây thành phần | tua bước |
|---|---|---|---|
| `v2_04` thiết diện + thể tích | canvas 1 | 43 mục | 2 nút, cảnh còn nguyên |
| `v2_06` giao rồi chiếu, `√22` | canvas 1 | 25 mục | 2 nút, cảnh còn nguyên |

## 7. Giới hạn — ba điều phải khai

**① n = 6.** Đây là probe nhỏ. Nó **không** tuyên bố gì về độ chính xác trên
toàn bộ hình học THPT, và 6/6 với n = 6 có khoảng dao động rộng. Lượt fresh
probe trước đã cho thấy phương sai thật: hai ca lật giữa hai lượt trên **cùng**
đề, cùng hash.

**② Bộ đề tránh hai giới hạn đã khai**, có chủ đích và ghi từ trước:
`SECTION_VERTEX_INTERSECTION_GAP` (mặt cắt không đi qua đỉnh nào) và
`CONTROL_FLOW_DEFINITE_ASSIGNMENT` PARTIAL (không đề nào buộc ràng buộc lần
đầu trong nhánh). Một bộ đề chạm vào chúng sẽ cho điểm thấp hơn, và điểm ấy sẽ
nói về hai giới hạn đã biết chứ không nói về năng lực tổng hợp.

**③ Không có k > 1.** Không đo độ ổn định. Mỗi đề chạy đúng một lượt.

## 8. Phân loại (§21)

`SYSTEM_FAILURE = 0` và `CORRECT_WITHIN_BUDGET = 6/6 ≥ 4/6`

⇒ **CLEAN_BASELINE_V2 = STRONG.**

Ngưỡng này đặt **trước** khi thấy kết quả (§21 của chỉ thị), không đặt sau.
