# FRESH_TRANSLATION_COMPOSITION_PROBE — mô hình có tự tìm ra `translate`?

> 4 đề mới, niêm phong trước khi gọi model, artifact chạy lại được từ lượt đầu.
> ⚠️ Đây là **lượt 2** — lượt 1 vỡ vì lỗi bộ đo, xem `LUOT_1_VO.md`.

Đóng băng `397f24f6`, cây sạch, `CACHE_VERSION 59`, prompt `1e9b8025`, thẻ
`4b0e0512`, seal `c4c074c5`. Nhiễm chéo SẠCH.
`PROBLEM_FAMILY_SPECIAL_CASES = 0` (quét AST mã sản phẩm).

## 0. Một đính chính phải đọc trước mọi con số

Chỉ thị §4 đòi ≥3/4 ca có `TRANSLATION_REQUIRED_BY_CURRENT_IR = YES`. **Không
ca nào đạt, và đó là sự thật.**

Wave trước tôi báo `PRE_EXTENSION_EXPRESSIBLE = NO`. Sai: audit hỏi câu **kiểu**
(*"phép sinh điểm nào nhận `vector3`?"* — đúng là KHÔNG) rồi tôi dùng nó trả
lời câu **ngữ nghĩa**. Tổ hợp có thật trong IR cũ:

    M = midpoint(P, S)
    Q = divide_segment(R, M, 2)      →  R + 2(M − R) = P + S − R

đúng bằng `translate(P, vector_from_points(R, S))`. Đã kiểm chạy.

⇒ `translate` là phép **dễ tìm và đúng nghĩa**, không phải một năng lực mới.
Đường vòng vẫn tồn tại nhưng nó dùng `divide_segment` với tỉ lệ `2` để đi RA
NGOÀI đoạn, trong khi hợp đồng của phép ấy khai `t=0 → A, t=1 → B`.

Nên probe này đo **"chọn gì khi cả hai đường đều mở"**, không đo *"có làm nổi
không"*. Mỗi ca ghi `TRANSLATION_USEFUL_BUT_NOT_REQUIRED` kèm chính đường vòng
viết ra ở trường `duong_vong`.

## 1. Kết quả

| | |
|---|---|
| ONE_SHOT_CORRECT | 2/4 |
| REPAIRED_CORRECT | 2/4 |
| **CORRECT_WITHIN_BUDGET** | **4/4** |
| SYSTEM_FAILURE | **0/4** |
| SYNTHESIS_FAILURE | 0/4 |
| **TRANSLATE_SELECTED_INITIAL** | **3/4** |
| TRANSLATE_SELECTED_AFTER_REPAIR | 3/4 |
| **ARITH_POINT_VECTOR_REAPPEARED** | **0** |
| VECTOR_TO_TRANSLATE_COMPOSITIONS | 1 |
| TRANSLATED_POINTS_USED_DOWNSTREAM | 5 |
| ARTIFACT_REPLAYABLE | **4/4** |
| CANONICAL_EXECUTABLE | 4/4 |

Provider **10/12** — 4 analyze + 4 tổng hợp đầu + 2 sửa.
Token: analyze 8.032 · tổng hợp đầu 18.346 · sửa 10.705 · **tổng 37.083**
(9.271 / ca đúng).

| đề | lớp | lượt ĐẦU | `translate` |
|---|---|---|---|
| `t1` hình bình hành | ONE_SHOT_CORRECT | đúng | `C` |
| `t2` lăng trụ | ONE_SHOT_CORRECT | đúng | *không dùng* |
| `t3` hộp, dây chuyền | REPAIRED_CORRECT | SCHEMA | `C, B', C', D'` |
| `t4` chuỗi sâu | REPAIRED_CORRECT | SCHEMA | `C` |

## 2. Tín hiệu mạnh nhất: khuôn cũ BIẾN MẤT

    ARITH_POINT_VECTOR_REAPPEARED = 0

`SYNTHESIS_STABILITY_K3` đếm khuôn `construct_point X = arith(+, var(P),
vector_from_points(A,B))` **10 lần** trên 18 quan sát, và nó giết 9/9 lượt
hỏng. Ở đây, trên bốn đề toàn đỉnh tịnh tiến, nó xuất hiện **không lần nào**.

Mô hình chuyển sang `translate` mà không cần một lời dặn theo dạng bài nào —
prompt chỉ có đúng một câu *"`translate` dời một điểm theo một vectơ"*, và
`PROBLEM_FAMILY_SPECIAL_CASES = 0`.

## 3. Cả hai lỗi lượt đầu là CÙNG MỘT thứ, và nó không phải lỗi ngữ nghĩa

```
statements.N.construct_point.expr.translate.vector
  Input should be a valid string
```

Mô hình viết vectơ **lồng thẳng** vào toán hạng:

```json
{"kind": "translate", "point": "B",
 "vector": {"kind": "vector_from_points", "from_point": "A", "to_point": "D"}}
```

5 lần (4 ở `t3`, 1 ở `t4`). Ý định dựng hình **đúng hoàn toàn** — chỉ hình
dạng wire sai, và một lượt sửa đã đủ cho cả hai ca.

⇒ Phép này **dễ tìm**; ràng buộc *"mọi trường là TÊN"* thì **không**. Ràng
buộc ấy là bất biến R0 (`test_R0_bieu_thuc_hinh_hoc_chi_nhan_TEN`): nhận cấu
trúc ở đó là mở đường cho toạ độ đi thẳng từ LLM vào. Nó có mặt trong thẻ
(`vector:tên`) và cả trong prompt (*"không nhận biểu thức lồng"*), và mô hình
vẫn lồng.

⚠️ Ghi làm **quan sát**, không hành động: wave này cấm sửa prompt/schema
(§25).

## 4. `t2` — ca không dùng `translate`, và vì sao nó không phải thất bại

`t2` (lăng trụ) đúng ngay lượt đầu **không** qua `translate`: trong hệ trục mô
hình tự chọn, `B'` có toạ độ hiển nhiên nên nó khai thẳng. Chương trình qua
mọi cổng và khớp oracle `3√14/7`.

Đây đúng là hệ quả của §0: khi tịnh tiến **không bắt buộc**, không có cơ sở
nào bắt mô hình phải dùng nó. Ghi là `TRANSLATE_NOT_SELECTED`, không phải
`SYNTHESIS_FAILURE`.

## 5. Tổ hợp — §15

`TRANSLATED_POINTS_USED_DOWNSTREAM = 5`: mọi điểm tịnh tiến đều được dùng
tiếp, không có ca nào dựng điểm rồi dừng. `t3` dựng bốn đỉnh bằng tịnh tiến
(gồm dây chuyền `C' = C + AA'`) rồi lấy trung điểm, dựng đường, và đo.

`VECTOR_TO_TRANSLATE_COMPOSITIONS = 1` thấp vì trong ba ca kia mô hình lồng
vectơ (nên không có biến vectơ trung gian để đếm) — con số này đo *cách viết*,
không đo *khả năng tổ hợp*.

## 6. Spot check trình duyệt

Hai ca ưu tiên §21 — dây chuyền (`t3`) và tịnh tiến → đo (`t4`). Chrome thật,
WebGL: **8/8, 0 lỗi console**. Cây thành phần hiện cả vectơ trung gian
(`vec_AD`) lẫn điểm chiếu (`H`), tức xuất xứ đi tới được mặt học sinh.

## 7. Phân loại (§22, ngưỡng chốt trước)

`ONE_SHOT_CORRECT = 2/4` (< 3/4) ⇒ **không** STRONG.
`CORRECT_WITHIN_BUDGET = 4/4 ≥ 2/4`, khám phá 3/4 nhưng one-shot chưa ổn

⇒ **TRANSLATION_COMPOSITION_EVIDENCE = MIXED.**

Không phải `WEAK_DISCOVERABILITY`: `translate` được chọn 3/4 ngay lượt đầu và
khuôn `arith` cũ biến mất hoàn toàn. Thứ chưa ổn là **hình dạng wire**, không
phải khả năng tìm thấy.

## 8. Kết luận khoa học được phép rút

> Trên bốn bài mới có cấu trúc affine khác nhau, LLM đã dùng primitive tịnh
> tiến tổng quát trong Semantic Program ở 3/4 lượt sinh đầu tiên, và ghép nó
> với các phép dựng/đo khác, mà không có mã nguồn riêng cho từng dạng bài.

**Không** kết luận đã giải quyết mọi bài affine. n = 4, k = 1.

## 9. Bằng chứng lịch sử không đổi

`CLEAN_BASELINE_V2` 6/6 và `SYNTHESIS_STABILITY_K3` 9/18 giữ nguyên. 9/18 vẫn
là kết quả độ ổn định **trước khi** `translate` tồn tại; không hồi tố.

## 10. Ghi chú ngân sách

Lượt 1 vỡ vì lỗi bộ đo sau 5 lượt (xem `LUOT_1_VO.md`), lượt 2 tiêu 10 lượt.
**Tổng thực chi 15**, trên trần 12 của §9. Quyết định chạy lại cả bốn thay vì
chỉ hai ca còn thiếu do người vận hành, đổi lấy một artifact đầy đủ và bốn ca
cùng một điều kiện.
