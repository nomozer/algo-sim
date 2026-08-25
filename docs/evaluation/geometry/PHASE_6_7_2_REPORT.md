# PHASE 6.7.2 — AI DỰNG HÌNH hay KHAI KẾT QUẢ? (2026-08-26)

> Câu hỏi duy nhất của pha này, và nó **khác hẳn** mọi pha trước: không hỏi *"có
> qua cổng không"* mà hỏi *"chương trình AI sinh ra có thật sự DỰNG các vật từ
> nhau, hay chỉ KHAI SẴN chúng rồi gọi đó là mô phỏng?"*
>
> Một chương trình khai sẵn mọi toạ độ vẫn qua được mọi cổng và ra đúng đáp số.
> Nó chỉ không còn là một **quá trình dựng hình** — và khi ấy toàn bộ giá trị sư
> phạm của đề tài biến mất.
>
> 15 lượt live trên `8a3adb8` (`CACHE 45`, sau Phase 6.7.1) + phân tích lại 15
> lượt của Phase 6.7. **Tổng 30 chương trình.**

---

## 1. Hai tỉ lệ được hỏi

| | Phase 6.7 (`5e42fa0`) | Phase 6.7.2 (`8a3adb8`) | **Gộp** |
|---|:-:|:-:|:-:|
| **Literal substitution** | 0/124 | 0/107 | **0/231 = 0.0%** |
| **Dependency construction** | 113/124 = 91.1% | 96/107 = 89.7% | **209/231 = 90.5%** |
| Witness **dẫn xuất** | 14/14 | 13/13 | **27/27 = 100%** |
| Độ sâu chuỗi | 1 – 4 | 1 – 4 | **1 – 4** |
| Chương trình có ≥1 literal thay thế | **0/15** | **0/15** | **0/30** |

### Cách hai tỉ lệ được định nghĩa

Mẫu số là **phần đáng lẽ phải dựng**, không phải tổng khai báo. Chia cho tổng
thì một chương trình khai nhiều điểm gốc tự động "tệ" đi — mà điểm gốc là **dữ
kiện**, không phải kết quả.

```
literal_hop_le     điểm gốc khai toạ độ + model_assumption
                   KHÔNG tính là lỗi: đề hình học không cho toạ độ,
                   prompt BẢO mô hình tự đặt hệ trục

literal_thay_the   ← thứ pha này đi tìm
                   · witness của một nghĩa vụ khai bằng `initial_value`
                     → khai thẳng ĐÁP ÁN
                   · line3/plane3/solid/polygon3 khai `initial_value`
                     → khai sẵn HÌNH thay vì dựng

dung_phu_thuoc     vật sinh ra từ một phép dựng đọc TÊN vật khác
```

### Phần dư 9.5% **không phải** "khai kết quả"

11/124 và 11/107 vật không được dựng. Đọc từng cái: **toàn bộ** là biến chết đặt
tên theo nghĩa vụ —

```
point_on_line        bool   initial_value = null   không ai ghi vào
volume               float  initial_value = null   không ai ghi vào
obligation_Q_on_AD   bool   initial_value = null   không ai ghi vào
```

`initial_value = null` ⇒ **không phải** khai đáp án. Mô hình đang coi danh sách
nghĩa vụ như thứ nó phải "khai một chỗ chứa", rồi bỏ trống. Vô hại về đúng-sai
(không ai đọc chúng), nhưng nó giải thích một lượt trượt ở Phase 6.7: bài 1
lần 4 khai **đúng một** biến `point_on_line_M_SA` và không dựng gì cả — cùng
hành vi, đẩy tới cực đoan.

### Độ sâu chuỗi: 2 → **4**

Phase 5G đo trên IR của lượt W4 và kết luận chuỗi phụ thuộc **tối đa 2 tầng**,
nguyên nhân là **hợp đồng** chứ không phải mô hình (không có phép nói *"dựng đáy
trước, rồi nâng lên thành khối"*).

Nay đo được **4** ở mọi lượt bài 3, và 3 ở một lượt bài 2. `construct_polygon`
của Phase 6.6 mở đúng mắt xích ấy: `điểm → đa giác → khối/mặt → giao tuyến →
giao điểm`.

---

## 2. Trả lời thẳng câu hỏi của pha

> **AI có thực sự sinh phép dựng phụ thuộc hay đang khai báo kết quả?**

**Sinh phép dựng phụ thuộc.** Trên 30 chương trình, **0 trường hợp** khai kết
quả, **100% witness** được dẫn xuất từ một phép dựng hoặc một phép đo, và chuỗi
phụ thuộc dài tới 4 tầng.

Điều đó **không** ngẫu nhiên mà có: cổng `structural_coverage` từ chối đúng hành
vi ấy (*"witness không dẫn xuất từ … — chương trình khai đáp án chứ không tính
nó"*), và grounding chặn `initial_value` không truy được về đề. Con số 0% là
**kết quả của cơ chế**, không phải may mắn — và đó chính là điều luận điểm R0
cần chứng minh.

⚠️ **Giới hạn phải đọc kèm**: 0% đo trên các chương trình **được sinh ra**. Nó
**không** nói gì về những lượt chết trước khi sinh nổi IR.

---

## 3. Phân loại lỗi — 1 lượt trượt / 15

| Nhóm | Số | |
|---|:-:|---|
| 1 · model generation | 0 | |
| 2 · **contract** | **1** | `construct_point C = arith(B + D)` |
| 3 · validator | 0 | |
| 4 · routing | 0 | mọi lượt đều tới được route sinh |

### Lượt duy nhất — và nó **LẶP LẠI**

```
2-the-tich lần 2   GEOMETRY_OPERAND_TYPE: biểu thức hình học lạ: arith
{"kind":"construct_point","target_var":"C",
 "expr":{"kind":"arith","op":"+","left":{"var":"B"},"right":{"var":"D"}}}
```

Mô hình tự cộng hai điểm để tính toạ độ đỉnh thứ tư. Kernel từ chối — **đúng**,
vì R0 nói toạ độ do kernel sinh, không do LLM tính. (Và công thức ấy còn sai:
đỉnh thứ tư là `B + D − A`, chỉ đúng khi `A` ở gốc.)

**Xếp nhóm CONTRACT, không phải model**, và lý do phải nói rõ:

`ConstructPointStmt.expr: ValueExpr` — union ấy **CÓ CHỨA** `arith`. Hợp đồng
**cho phép** đúng thứ engine cấm. Mô hình viết một câu lệnh mà kiểu khai báo nói
là hợp lệ.

Hệ quả nặng hơn: lỗi nổ ở **`execution`**, tức **SAU** vòng sửa. Lỗi validator
được gửi ngược cho mô hình sửa (≤3 lượt); lỗi runtime thì không. Nên chương
trình kiểu này **không bao giờ có cơ hội được sửa**, dù thông báo đã nói đúng
chỗ sai — `thu_that_bai` của lượt này là `[]`: không một lần thử lại nào.

**Bằng chứng lặp lại** (điều kiện pha này đặt ra để được sửa):

| | Lượt | Cùng câu lệnh |
|---|---|---|
| Phase 6.7 | `2-the-tich-lan5` | `construct_point C = arith(B + D)` |
| Phase 6.7.2 | `2-the-tich-lan2` | `construct_point C = arith(B + D)` |

Hai vòng đo **độc lập**, hai bản mã khác nhau, **cùng một câu lệnh**. Không phải
nhiễu.

**Pha này chỉ báo cáo, không sửa** — đúng phạm vi đã đặt.

---

## 4. Số phụ: `served` tăng mạnh, `obligation_match` thì không

| | Phase 6.7 | Phase 6.7.2 |
|---|:-:|:-:|
| served | 9/15 | **14/15** |
| oracle | 9/15 | **14/15** |
| obligation_match | 11/15 | **10/15** |

Bản vá validator của Phase 6.7.1 ăn đúng chỗ nó nhắm: bài thể tích 2/5 → **4/5**,
bài trung điểm 3/5 → **5/5**. Phase 6.7 **chiếu** 11/15; **đo được 14/15**.

### ⚠️ Nhưng bài 3 `obligation_match` = **0/5**, và một phần là lỗi của TÔI

Nghĩa vụ mà lượt đọc đề khai ra ở bài 3, 5 lượt:

```
lần 1   point_on_line(AD, Q) · point_on_line(d, Q)
lần 2   point_on_line(AD, Q)
lần 3   —  (không nghĩa vụ nào)
lần 4   —  (không nghĩa vụ nào)
lần 5   point_on_line(AD, Q)
```

Kỳ vọng tôi đặt trong bộ đo là `{point_on_line, point_on_plane}`. **5/5 lượt
không đồng ý với tôi, và theo một hướng nhất quán.**

Đọc lại đề thì mô hình có lý: *"Hãy dựng mặt phẳng (PMN)"* là một **mệnh lệnh
dựng**, không phải một **mệnh đề cần chứng minh**. `point_on_plane` cần một
witness, mà đề không hỏi điểm nào thuộc `(PMN)`. Nên `obligation_match = 0/5` ở
bài 3 phần lớn là **kỳ vọng của tôi sai**, không phải mô hình bất ổn.

Phần **thật sự** bất ổn là hai lượt khai **rỗng** (lần 3, lần 4): đề rõ ràng đòi
*"xác định giao điểm Q"*, và đó là một mệnh đề kiểm được. Nên con số đúng cho
bài 3 là **3/5 lượt khai một bộ nghĩa vụ hợp lý**, không phải 0/5.

Cả bốn lượt `nv ∈ {0, 1}` vẫn `served` và vẫn qua oracle độc lập — tức **hệ dựng
đúng hình nhưng tự kiểm rất ít**. Kết luận này giữ nguyên từ Phase 6.7 và không
được xoá bởi con số 14/15.

---

## 5. Điều kiện đủ để mở Phase 7

| | Điều kiện | |
|---|---|:-:|
| 1 | môi trường: `runtime_doctor --doi-mode serve` PASS, cây sạch, cache 0 | ✅ |
| 2 | `pytest` xanh (2839) | ✅ |
| 3 | **AI dựng phụ thuộc, không khai kết quả** — 0/231 literal, 27/27 witness dẫn xuất | ✅ |
| 4 | không lỗi **routing** trong 15 lượt | ✅ |
| 5 | không lỗi **validator** trong 15 lượt (nhóm C của 6.7 đã đóng) | ✅ |
| 6 | **chỉ số của Phase 7 là một CẶP** `(served, obligation_match)` | ⚠️ chưa chốt |
| 7 | benchmark chạy **k lượt mỗi đề**, không một lượt | ⚠️ chưa chốt |
| 8 | kỳ vọng nghĩa vụ mỗi đề phải do **người khác** đặt, không do tôi | ⚠️ **mới lộ ra** |

**① – ⑤ đã đủ.** Ba câu hỏi mà Phase 6.6 và 6.7 để lại đều đã có câu trả lời
bằng số, và không câu nào còn là lỗ của hệ.

**⑥ ⑦** đã kết luận ở Phase 6.7, chỉ chờ chốt.

**⑧ là điều kiện MỚI, và nó lộ ra từ chính lượt đo này.** `obligation_match =
0/5` của bài 3 phần lớn vì **tôi** đặt kỳ vọng sai, không vì mô hình. Nếu Phase 7
để tôi tự đặt kỳ vọng nghĩa vụ cho từng đề held-out, mọi chỗ tôi đọc đề khác mô
hình sẽ ghi thành "mô hình sai". Đó là cùng một lớp lỗi với việc tôi tự soạn
held-out — và `HOLDOUT_PROTOCOL §2` đã có sẵn cơ chế: **đáp án và yêu cầu đến từ
nguồn ngoài**.

---

## 6. Khuyến nghị

**Mở được Phase 7, với ba điều chốt trước khi tiêu call đầu tiên:**

1. Chỉ số là **cặp** `(served, obligation_match)`, không gộp, không báo `served`
   một mình.
2. Mỗi đề chạy **k ≥ 3 lượt**; báo cáo là `x/k`, không phải pass/fail.
3. Kỳ vọng nghĩa vụ lấy từ **đáp án nguồn ngoài**, không do tôi suy từ đề.

**Một việc nên làm, không bắt buộc**: thu hẹp `ConstructPointStmt.expr` xuống
đúng tập biểu thức hình học. Nó biến lỗi `arith` từ **runtime** (không sửa được)
thành **validator** (mô hình được sửa trong ≤3 lượt), và bằng chứng lặp lại đã
đủ theo điều kiện pha này đặt ra. Nhưng nó là một thay đổi hợp đồng, nên thuộc
quyết định của người hướng dẫn chứ không thuộc pha đo.

---

## Chi phí

15 lượt × ~6 lượt LLM ≈ **90 lượt**, `gemini-2.5-flash`. Phân tích phụ thuộc
chạy **0 API call** trên artifact đã lưu — gồm cả 15 lượt của Phase 6.7, nên
đường cơ sở không tốn thêm gì.

Artifact: `stability-6.7.2/` (15 file + `phan_tich_phu_thuoc.json`).
Đường cơ sở: `stability-6.7/phan_tich_phu_thuoc.json`.
