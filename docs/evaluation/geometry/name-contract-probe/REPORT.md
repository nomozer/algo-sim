# NAME_ONLY_CONTRACT_LIVE_PROBE — `tên<T>` có đổi được cách mô hình VIẾT?

> 4 đề mới, 8/8 lượt provider, **0 lượt sửa**. Artifact chạy lại được 4/4.
> Đóng băng `bc8b06c`, cây sạch, `CACHE_VERSION 60`.

## 1. Câu trả lời cho câu hỏi A: có, và tuyệt đối

    TOTAL_NAME_SLOTS_EMITTED   42
    RAW_NAME_SLOTS             42
    WRAPPED_VAR_SLOTS           0
    NESTED_DERIVED_EXPR_SLOTS   0
    RAW_LITERAL_SLOTS           0
    WRONG_TYPE_SLOTS            0
    RAW_NAME_COMPLIANCE_RATE  1.0

**Bộ chuẩn hoá không phải làm gì cả**: 0 lần gỡ bọc, 0 lần nâng, 0 temp, 0 ca
được cứu. Trên 42 ô toán hạng thuộc bảy họ primitive khác nhau, mô hình viết
đúng một định danh trần ở **mọi ô**.

Đối chiếu bối cảnh lịch sử — **không** phải một phép so điểm: trên artifact đã
commit trước wave hợp đồng, 23 ô bị viết sai hình dạng (7 lồng + 16 bọc `var`).
n = 4 và k = 1, nên đây là *một quan sát sạch*, không phải một tuyên bố nhân quả.

`n3` cố ý **không cần** `translate`, và nó cũng 9/9 ô đúng — nên tính tuân thủ
không phải hiệu ứng của việc mô hình vừa nhìn thấy một phép mới trong thẻ.

## 2. Câu hỏi B: hệ chạy 2/4, và **không lỗi nào là lỗi ô TÊN**

| đề | kết cục | ô TÊN | hỏng ở đâu |
|---|---|---|---|
| `n1` hình thoi | ONE_SHOT_CORRECT | 10/10 | — |
| `n2` lăng trụ xiên | ONE_SHOT_CORRECT | 12/12 | — |
| `n3` mặt qua điểm dẫn xuất | FAIL_SCHEMA | 9/9 | `divide_segment.ratio` |
| `n4` giao đường–mặt | FAIL_GROUNDING | 11/11 | `analyze` không phát fact toạ độ |

Đây đúng là thứ việc tách hai metric sinh ra để lộ. Cả bốn chương trình
`RAW_CONTRACT_COMPLIANT`, hai trong số đó vẫn hỏng — vì hai luật **khác**.

### 2a. `n3` — literal bọc quanh một VÔ HƯỚNG, không phải một ô TÊN

```json
{"kind": "divide_segment", "a": "S", "b": "D",
 "ratio": {"kind": "literal", "value": 2}}
```

`ratio` là **chuỗi phân số**, không phải ô TÊN, nên `GeometryName` không phủ
nó. Cùng lớp với `canonical_const_int` (đã vá cho `for_range.step` từ
2026-08-24): mô hình bọc `literal` quanh một vô hướng ở đúng chỗ hợp đồng đòi
giá trị trần. Ghi làm **quan sát**, §22 cấm sửa trong lúc chạy.

### 2b. `n4` — lỗi nằm ở THƯỢNG NGUỒN, không ở lượt tổng hợp

`analyze` phát ĐÚNG BA dữ kiện, toàn quan hệ (`abcd_is_square`,
`m_is_midpoint_sc`, `k_is_intersection_bm_sad`) — **không dữ kiện nào cho năm
toạ độ đề cho**, dù đề viết chúng tường minh. Mô hình tổng hợp trích dẫn đúng
cả hai fact quan hệ nó có, rồi với năm điểm không có fact nào để trích, nó viết
chính chữ trong đề (`source_fact_id: "A(0; 0; 0)"`). Grounding từ chối, đúng.

Và nó **không hệ thống** — đó mới là điều đáng ghi:

| đề | số fact | có fact toạ độ? |
|---|---|---|
| `n1` | 4 | ✔ `m_coords`, `n_coords`, `p_coords` |
| `n2` | 7 | ✔ `coord_A`…`coord_A_prime` |
| `n3` | 3 | ✘ |
| `n4` | 3 | ✘ |

Bốn đề cùng nêu toạ độ theo một kiểu; `analyze` trích ở hai đề và bỏ ở hai đề.
⇒ Đây là **bất ổn của `analyze`**, không phải một lỗ hợp đồng, và nó là nguyên
nhân gần của thất bại duy nhất ở tầng grounding.

## 3. ⚠️ Một khiếm khuyết của CHÍNH BỘ ĐỀ, phải khai

Chẩn đoán offline (**0 lượt gọi**): gỡ bọc `literal` của `n3` bằng tay thì
chương trình qua schema **và khớp oracle** — nhưng

    F = (0, 12, −6)     đúng phải là (0, 4, 2)

Mô hình đọc *"SF = 2FD"* thành tỉ lệ `2` thay vì `2/3`, tức `F` nằm ngoài đoạn
`SD`. **Oracle của `n3` vẫn không phân biệt được**: khoảng cách từ `B` tới mặt
`(A, E, F)` bằng 4 với cả hai `F`, vì cả hai nằm trên đường `SD` và cấu hình
này tình cờ cho cùng thành phần pháp tuyến theo `Ox`.

Tôi đã thay oracle của `n3` **một lần** trước khi seal vì đúng lý do ấy, và bản
thay vẫn chưa đủ. Nó không làm sai con số nào đã báo — `n3` hỏng ở schema nên
chưa bao giờ được tính đúng — nhưng nếu mô hình viết `"2"` thành chuỗi thì
`n3` đã được ghi ONE_SHOT_CORRECT với một hình dựng sai. Khai ra vì một bộ đo
chỉ đáng tin đúng bằng chỗ yếu nhất của nó.

## 4. R0 và hai chốt canh

    RAW_GEOMETRY_LITERAL_ATTEMPTS        0
    SYMBOLIC_COORDINATE_STATIC_REJECTION N_A  (không ca nào phát)
    FIRST_BINDING_RUNTIME_FAILURES       0/4
    STATIC_FAILURE 0/4 · RUNTIME_FAILURE 0/4 · SYSTEM_FAILURE 0/4

Không lần nào mô hình thử đưa toạ độ thô vào một ô TÊN, nên cửa R0 lo nhất vẫn
chưa ai gõ. Toạ độ ký hiệu cũng không xuất hiện — chốt §14 **chưa được thử
lửa** ở lượt này, và nói nó "PASS" là nói quá.

## 5. Phân loại theo ngưỡng CHỐT TRƯỚC (§18)

    MODEL_NAME_DISCOVERABILITY = STRONG
      RAW_CONTRACT_COMPLIANT 4/4 ≥ 3/4 ✔ · raw literal 0 ✔ · không lặp lại
      một khuôn sai hình dạng nào ✔

    SYSTEM_ERGONOMICS = MIXED
      CORRECT_WITHIN_INITIAL 2/4 (không đạt 4/4 của STRONG);
      2–3/4 đúng và không lỗi hệ lặp lại ⇒ MIXED.

Ngưỡng viết trước khi chạy, áp nguyên văn.

## 6. Token

    ANALYZE 10.154 · SYNTHESIS 18.714 · TỔNG 28.868
    TOKENS_PER_CORRECT_INITIAL_IR = 14.434

Cao vì mẫu số là 2. Không so với wave trước: khác bộ đề, khác điều kiện (kia có
lượt sửa, đây không).

## 7. Kết luận được phép rút

> Sau khi hợp đồng IR khai kiểu ô toán hạng ngay tại chỗ dùng (`tên<point3>`),
> mô hình phát đúng định danh trần ở **42/42** ô thuộc bảy họ primitive trên
> bốn đề mới, không lần nào cần tới lớp chuẩn hoá tiện dụng.

**Không** kết luận rằng lớp chuẩn hoá là thừa: nó được dựng từ 23 lần quan sát
được trong lịch sử, và một lượt n = 4 không bác bỏ chúng. Nó nay là **lưới an
toàn không dùng tới**, và đó là trạng thái đúng của một lưới an toàn.

## 8. Còn mở sau lượt này

- **`analyze` bỏ sót dữ kiện toạ độ ở 2/4 đề** — nguyên nhân gần của thất bại
  grounding duy nhất. Bất ổn, không phải thiếu năng lực.
- **`literal` bọc quanh vô hướng ở `divide_segment.ratio`** — cùng lớp đã vá
  cho `for_range.step`, chưa vá cho miền hình học.
- **Oracle của `n3` không phân biệt được `F` sai** — nợ của bộ đề, xem §3.
