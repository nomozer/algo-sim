# NAMED_GEOMETRY_OPERAND_ERGONOMICS — ô toán hạng TÊN, dễ dùng mà không nới R0

> 0 lượt gọi model. Không sửa một artifact lịch sử nào, không đổi một điểm số
> lịch sử nào.

## 1. Erratum — phân loại lại `translate`

    PRE_EXTENSION_SEMANTIC_EXPRESSIBLE = YES
    TRANSLATE_CLASSIFICATION           = CANONICAL_ERGONOMIC_PRIMITIVE

`P + vectơ(R,S)` **biểu diễn được** bằng IR cũ ở một số cấu hình:

    M = midpoint(P, S)
    Q = divide_segment(R, M, 2)      →  R + 2(M − R) = P + S − R

Nên `translate` **không** là một năng lực tổng quát mới. Lý do thêm nó vẫn
đứng, và nay được gọi đúng tên: nó giảm ma sát tổng hợp và cho một biểu diễn
affine trực tiếp, có kiểu, dễ khám phá. `SYNTHESIS_STABILITY_K3` 9/18 và
`TRANSLATION_COMPOSITION_EVIDENCE = MIXED` giữ nguyên.

## 2. Ô toán hạng TÊN — dẫn xuất, không chép tay

    NAME_ONLY_OPERAND_AUTHORITY = ir_static_check._CHU_KY
                                · ir_static_check._TOAN_HANG_LENH
                                · ir_static_check._KIEU_DO ← measure_contract
    NAME_ONLY_OPERAND_SLOTS     = 30   (16 biểu thức · 7 câu lệnh · 7 measure)

`hoisting.O_TEN` dẫn từ hai bảng đầu; `measure` tra thẳng `_KIEU_DO` vì kiểu
toán hạng của nó phụ thuộc `quantity`. Ba người đọc cùng một bảng: bộ nâng, thẻ
văn phạm, và guard chống trôi.

## 3. Điều audit tìm thấy, và nó KHÔNG phải điều chỉ thị dự đoán

`scripts/audit_named_operand_ergonomics.py` quét mọi chương trình thô đã commit
trong `docs/evaluation/geometry/**`:

| | |
|---|---|
| HISTORICAL_NESTED_EXPR_ATTEMPTS | **23** |
| ↳ nâng được (biểu thức dựng lồng) | 7 |
| ↳ **gỡ bọc `var`** | **16** |
| STILL_REJECTED | **0** |
| toạ độ thô trong một ô TÊN | **0 lần, chưa từng** |

Lớp ma sát **đông nhất không phải biểu thức lồng**. Nó là `{"kind":"var","name":
"Q"}` bọc quanh một cái tên — `through_a`, `of`, `wrt`, `through[]`. Đó đúng
lớp lỗi mà `canonical_container_name` đã vá cho miền Tin học từ 2026-08-23
(*"hai cách viết CÙNG MỘT tham chiếu"*); ô hình học là `str` trần nên chưa ai vá.

⇒ Hai cơ chế, cố ý tách:

- **`hoisting.nang_bieu_thuc_long`** — biểu thức DỰNG lồng ⇒ một ràng buộc có
  tên đứng trước. Sinh temp.
- **`contract.canonical_geometry_name`** — `var` bọc quanh tên ⇒ chính cái tên.
  1:1, **không** sinh temp, không thực thể mới.

Gộp hai thứ vào một con số là báo cáo sai chuyện đang xảy ra; bản đầu của bộ
audit đã sai đúng thế và bị sửa trước khi ghi số.

## 4. Ranh giới an toàn — bốn câu hỏi, và cái vẫn phải chết

`SAFE_HOISTING_AUDIT = PASS`: 23/23 lần quan sát được thoả cả bốn.

Nâng khi **và chỉ khi**: ① `kind` có trong `_CHU_KY` · ② kiểu trả về ∈ kiểu ô
nhận · ③ không mang `model_assumption` · ④ độ sâu ≤ 4.

Vẫn chết, đúng như trước: `translate(A, [1,2,3])` · `translate(A, {"x":…})` ·
kiểu trả về sai · `kind` lạ · biểu thức lồng chở `model_assumption`. Cái cuối là
cửa sau đáng sợ nhất và nó đóng: một giả định mô hình tự đặt phải được khai ở
một điểm gốc, nơi `grounding_gate` hỏi nó.

Lời từ chối nay **CÓ DẠY** thay vì `Input should be a valid string` — câu đã
giết 2/4 lượt tổng hợp đầu của probe trước mà không nói phải làm gì.

## 5. R0 sau chuẩn hoá — mệnh đề cả wave đứng lên

    R0_CANONICAL_INVARIANT = PASS

Bất biến áp lên chương trình **đã chuẩn hoá**, không lên bản thô: lớp tiện dụng
được phép nhận một hình dạng khác, nhưng thứ đi tiếp vào hệ phải là dạng chuẩn
tắc — **mọi ô toán hạng hình học là một chuỗi TÊN**. Khoá bởi
`test_R0_moi_toan_hang_hinh_hoc_van_la_TEN_sau_chuan_hoa`.

Temp mang kiểu suy TĨNH (`vector3`, không bao giờ `unknown`), sinh ở **đúng
khối** của câu lệnh dùng nó, và **không** được đẩy ra scope ngoài — nên
`CONTROL_FLOW_DEFINITE_ASSIGNMENT` giữ nguyên trạng PARTIAL, không mở thêm.

Xuất xứ đi qua temp không đứt: `Q = translate(A, vector_from_points(B,D))` cho
bao đóng nguồn `{A, B, D}`. Temp **vẫn nằm trong đồ thị tất định** và tự khai
`synthetic` để tầng trình bày gộp lại (`display_group: internal`) — xoá nó khỏi
cảnh là nói dối về xuất xứ, còn để `_tam_1` lên màn hình học sinh là một định
danh kỹ thuật lọt bề mặt.

## 6. Chạy lại lịch sử (§18/§19)

    HISTORICAL_NESTED_EXPR_ATTEMPTS = 23
    NORMALIZED_SAFELY               = 23
    STILL_REJECTED                  = 0
    EXECUTABLE_AFTER_NORMALIZATION  = 2/5 chương trình

Hai chương trình hỏng của translation probe **chạy trọn chuỗi cổng** — schema,
tĩnh, grounding + trung thực, thực thi, transport — và **khớp oracle**:

| đề | temp | oracle | khớp |
|---|---|---|---|
| `t3_hop_tinh_tien_day_chuyen` | 4 × `vector3` | `3√89/5` | ✔ |
| `t4_mat_xich_trong_chuoi_sau` | 1 × `vector3` | `2√2` | ✔ |

Ba chương trình còn lại dừng, và **cả ba là lỗi ngữ nghĩa THẬT của mô hình**:
`angle_cos` trên `line3` (×2, bắt ở thẩm định tĩnh) và một toạ độ ký hiệu (×1).
Không ca nào bị chuẩn hoá che đi.

## 7. Một lỗ mà chính lượt chạy lại lộ ra — và tôi đã bịt

⚠️ **Ngoài chữ của chỉ thị.** `declare_point.at` là `list[Any]` và
`initial_value` là `Any`, nên một toạ độ KÝ HIỆU đi thẳng tới kernel:

    {"name":"A","type":"point3","at":[{"kind":"var","name":"a"}, 0, 0]}

Mô hình đang nói *"cạnh đáy là a"* — đúng thói quen SGK. Kernel ném `ZERO_VECTOR`
ở **runtime**, nơi vòng sửa không với tới. Lỗ này **vốn đã có**; ở artifact
`dihedral-probe-ergonomics` nó bị một lỗi schema khác che, và bịt phép nâng làm
nó lộ ra.

Không bịt thì bản vá này đổi một ca chết-có-lời-sửa thành một ca chết câm. Nên
câu ③ của thẩm định tĩnh (*"số hữu tỉ chính xác"*) nay áp cho toạ độ, không chỉ
cho `ratio` — `ir_static_check._kiem_toa_do`, dùng đúng `_la_huu_ti` và
`IR_NOT_EXACT_RATIONAL` đã có. Không thêm năng lực nào.

## 8. Ngân sách token tránh được (§22 — chỉ log thật)

    REPAIRS_AVOIDABLE_BY_HOISTING = 2   (t3, t4)
    TOKENS_AVOIDABLE_BY_HOISTING  = 10.705   (6.363 + 4.342)

Cả hai lượt sửa ấy tồn tại **chỉ vì hình dạng wire**: chương trình lượt đầu
đúng nghĩa và đúng đáp số, đã kiểm ở §6. Không ngoại suy sang đề khác.

⚠️ `TRANSLATION_COMPOSITION_EVIDENCE` và `ONE_SHOT_CORRECT = 2/4` của probe
**giữ nguyên**. Nói *"cùng bốn đầu ra thô ấy nay phân loại 4/4 one-shot"* là một
mệnh đề về **hệ hôm nay**, không phải một điểm số được sửa lại.

## 9. Cái wave này KHÔNG làm

    NEW_GEOMETRY_CAPABILITY = NO
    HISTORICAL_SCORES_CHANGED = NO
    LLM_CALLS = 0

Không primitive mới, không kiểu mới, không câu lệnh mới. Tuyên bố phạm vi bài
toán **không** tăng vì wave này: nó là `IR_ERGONOMICS / CANONICALIZATION`.

## 10. Còn mở

- **`construct_plane.through` bọc CẢ DANH SÁCH** — `{"kind":"literal","value":
  ["A","B","C"]}` thay vì ba tên. `list[GeometryName]` gỡ bọc từng **phần tử**,
  không gỡ được lớp bọc ngoài. Đã quan sát trong lịch sử; chưa xử.
- **Toạ độ ký hiệu** nay bị từ chối TĨNH có lời chỉ đường, nhưng mô hình vẫn
  chưa có cách nói *"cạnh a"* — đó là một câu hỏi thiết kế, không phải một lỗ.
- `CONTROL_FLOW_DEFINITE_ASSIGNMENT` vẫn PARTIAL, cố ý không đụng.
