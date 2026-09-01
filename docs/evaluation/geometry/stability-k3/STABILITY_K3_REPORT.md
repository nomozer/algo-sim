# SYNTHESIS_STABILITY_K3 — cùng một đầu vào, ba lần sinh

> 6 ca × 3 lượt = 18 quan sát. R1 đọc từ hạt giống, R2/R3 gọi mới.
> 12 lượt provider, **0 analyze, 0 sửa**. Chạy một lần.

Đóng băng `550bb00c`, `CACHE_VERSION 58`, prompt `b8bb766b`, thẻ `d409584f` —
khớp hạt giống ba giá trị. `INPUT_HASH_PRE_SEND` **PASS 12/12**: mỗi payload
được băm và đối chiếu với hash của R1 **trước khi gửi**.

## 1. Kết quả

| | |
|---|---|
| INITIAL_CORRECT_TOTAL | **9/18** |
| ONE_SHOT_SYNTHESIS_RELIABILITY | 9/18 |
| CASE_STABLE_3_OF_3 | 2/6 |
| **CASE_AT_LEAST_2_OF_3** | **3/6** |
| CASE_UNSTABLE_1_OF_3 | 1/6 |
| CASE_FAILED_0_OF_3 | 2/6 |
| **SYSTEM_FAILURE_TOTAL** | **0/18** |
| FIRST_BINDING_RUNTIME_FAILURES | 0/18 |

| đề | | R1 R2 R3 | nhãn | chương trình khác nhau |
|---|---|---|---|---|
| `v2_01` tứ diện | 3/3 | ✓ ✓ ✓ | STABLE | **3** |
| `v2_02` lăng trụ | 0/3 | ✗ ✗ ✗ | CONSISTENT_FAILURE | 0 |
| `v2_03` lập phương | 2/3 | ✓ ✗ ✓ | MOSTLY_STABLE | 2 |
| `v2_04` thiết diện | 1/3 | ✓ ✗ ✗ | UNSTABLE | 1 |
| `v2_05` góc hai đường | 0/3 | ✗ ✗ ✗ | CONSISTENT_FAILURE | 0 |
| `v2_06` giao rồi chiếu | 3/3 | ✓ ✓ ✓ | STABLE | **3** |

`CASE_AT_LEAST_2_OF_3 = 3/6` và `SYSTEM_FAILURE_TOTAL = 0`

⇒ **SYNTHESIS_STABILITY = MIXED** (ngưỡng chốt trước lượt đo, không đổi sau).

## 2. Phát hiện chính: một KHOẢNG TRỐNG IR, không phải mô hình kém

**9/9 lượt hỏng đều là `SCHEMA`.** Không một lỗi grounding, trung thực, runtime
hay checker nào. Và khuôn hỏng lặp lại **10 lần** với **cùng một hình dạng**:

```json
"construct_point": {
  "target_var": "B_prime",
  "expr": {"kind": "arith", "op": "+",
           "left":  {"kind": "var", "name": "B"},
           "right": {"kind": "vector_from_points",
                     "from_point": "A", "to_point": "A_prime"}}}
```

Đọc ra tiếng Việt: **"tịnh tiến điểm B theo vectơ AA'"**.

Đó là cách tự nhiên nhất — và với hình hộp/lăng trụ, gần như là cách DUY NHẤT
— để dựng các đỉnh dẫn xuất:

    C  = B + vectơ AD        (hoàn thành hình bình hành đáy)
    B' = B + vectơ AA'       (tịnh tiến theo cạnh bên)
    C' = C + vectơ AA'
    D' = D + vectơ AA'

`PointExpr` có đúng năm phép: `intersect_line_plane`, `intersect_line_line`,
`midpoint`, `project_onto`, `divide_segment`. **Không phép nào là tịnh tiến.**

### Điều này đã được ghi trong kho, và bị bỏ quên

`grounding_gate` Wave 5 đã khai:

> Bất biến *"mọi đỉnh dẫn xuất phải do primitive dựng"* đã bị **bác bỏ**: IR
> không có tịnh tiến/hoàn thành hình bình hành, nên nó sẽ buộc `unsupported`
> gần hết bài hình lập phương.

Đường vòng lúc ấy: cho mô hình **KHAI** các đỉnh ấy bằng toạ độ kèm
`model_assumption`. Ở đây mô hình đang làm điều **đúng hơn** — nó cố **DỰNG**
chúng thay vì khai — và IR không cho.

⇒ Mô hình không sai. Nó đang tôn trọng R0 chặt hơn thứ IR cho phép diễn đạt.

### Phân bố theo lượt

    R1 = 3 · R2 = 8 · R3 = 2      (13 câu lệnh, trên 10 chương trình)

Ba đề dính: `v2_02` (lăng trụ, cả 3 lượt), `v2_03` (lập phương, R2),
`v2_04`/`v2_05` (chóp, R2). Đúng những hình có **đỉnh tịnh tiến**.

`v2_01` (tứ diện, mọi đỉnh nằm trên trục) và `v2_06` (chóp, đỉnh dẫn xuất là
giao điểm và hình chiếu) **không** cần tịnh tiến — và cả hai đều 3/3 STABLE.
Tương quan này là toàn bộ bằng chứng: **ổn định hay không phụ thuộc bài có cần
một phép IR thiếu hay không**, chứ không phụ thuộc độ khó của bài.

### Hai lỗi còn lại, khác khuôn

- `v2_04` R3 — `memory_declarations[9].type` không thuộc `MemoryType`.
- `v2_05` R3 — đặt `construct_line` (một CÂU LỆNH) vào chỗ `assign.expr` cần
  một biểu thức.

Hai ca lẻ, không đủ thành khuôn.

## 3. Bằng chứng TỔ HỢP, không phải chép khuôn

    TOTAL_DISTINCT_NORMALIZED_PROGRAMS   9
    ALTERNATIVE_VALID_COMPOSITIONS       3/6

`v2_01` và `v2_06` mỗi ca đúng **3/3 với 3 chương trình KHÁC NHAU**. Cùng đề,
cùng byte đầu vào, ba lời giải khác cấu trúc, cả ba qua checker.

Đó là kết quả **tốt** theo §13: khác hash không phải bất ổn. Điều cần ổn định
là **tính đúng ngữ nghĩa**, không phải danh tính văn bản của chương trình.
Đây là bằng chứng trực tiếp cho luận điểm của đề tài — AI **tổ hợp** từ
primitive, không phát lại một module cố định.

## 4. Ràng buộc lần đầu vẫn vững

    CONSTRUCT_POINT_SELECTED         52
    SAFE_ASSIGN_NORMALIZED           23
    FIRST_BINDING_RUNTIME_FAILURES   **0/18**

Bản sửa `IR_FIRST_BINDING_CONTRACT` giữ nguyên qua 18 quan sát: không một
chương trình nào chết ở runtime vì tiền điều kiện khai báo.

## 5. Điều wave này KHÔNG kết luận

- **Không** phải độ chính xác trên hình học THPT. Sáu đề này là **tập đo độ
  ổn định**, mô hình đã thấy chúng; gọi chúng là held-out là nói sai.
- `9/18` là **khả năng lặp lại trên cùng một đầu vào**, không phải accuracy.
- **Không** so với `CLEAN_BASELINE_V2 = 6/6`: lượt ấy CÓ vòng sửa, lượt này
  không. Hai điều kiện khác nhau.
- n = 6, k = 3. Khoảng dao động rộng.

## 6. Quyết định (§22)

`SYNTHESIS_STABILITY = MIXED` ⇒ phân tích khuôn hỏng, và chỉ tiếp tục nếu có
một khuôn lặp lại **mang tính giao diện rõ**.

Có, và nó rõ đến mức đo được: **10/13 câu lệnh hỏng là một phép dựng duy nhất
mà IR không có tên để gọi.** Đây là lỗ hổng giao diện, không phải lỗ hổng năng
lực mô hình.

⇒ `READY_TO_SELECT_NEXT_GENERAL_CAPABILITY = YES`, và năng lực cần chọn đã
được phép đo chỉ đích danh — không phải chọn theo linh cảm.

⚠️ Wave này **không sửa** (§20, §21). Không thêm primitive, không đổi prompt,
không chạy lại.
