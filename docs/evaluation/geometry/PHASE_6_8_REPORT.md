# PHASE 6.8 — FINAL PRE-PHASE7 HARDENING (2026-08-26)

> Không mở benchmark. Không frontend. Không mở rộng miền. Không thêm tính năng.
>
> **Trạng thái đóng băng**: `7e73291` · `CACHE_VERSION 46` ·
> `cay_lam_viec_sach: True` · `pytest 2856 passed, 0 đỏ` · `vitest 1598 passed` ·
> `runtime_doctor --doi-mode serve` **PASS** · smoke **3/3**.

---

## 1. Chốt hợp đồng chỉ số Phase 7

`PHASE7_METRIC_CONTRACT.md` — chốt **trước** khi tiêu call đầu tiên, vì đổi định
nghĩa một chỉ số sau khi đã thấy số là chọn thước theo điểm.

| | Chỉ số | Câu hỏi nó trả lời |
|---|---|---|
| ① | `served` | Hệ có phát ra một mô phỏng không? |
| ② | `oracle` | Mô phỏng ấy có **đúng** không? |
| ③ | `obligation_match` | Hệ có **tự biết** mình đúng không? |
| ④ | `construction_validity` | Nó **dựng hình** hay **khai kết quả**? |
| ⑤ | `stability` | Lặp lại có ra cùng kết quả không? |

**Không gộp** — và đó không phải nguyên tắc suông: chúng **đã đi ngược chiều
nhau** trong dữ liệu thật. Bài thiết diện ở Phase 6.7.2 đạt `served 5/5` với
`obligation_match 0/5`; bốn trong năm lượt ấy dựng đúng hình mà **không kiểm gì
cả**.

Bốn luật khác được ghi vào hợp đồng, mỗi luật đến từ một chỗ đã sai một lần:

- `oracle` có **ba** trạng thái (`True`/`False`/`None`). Gộp `None` vào `False`
  là ghi một lượt *không đo được* thành một lượt *sai*.
- `obligation_match` đòi **bằng đúng**, và **kỳ vọng phải đến từ nguồn ngoài** —
  ở Phase 6.7.2 kỳ vọng tôi tự đặt bị **5/5 lượt bác bỏ nhất quán**, và đọc lại
  đề thì mô hình có lý.
- `construction_validity` lấy mẫu số là **phần đáng lẽ phải dựng**, không phải
  tổng khai báo: điểm gốc là **dữ kiện**, không phải kết quả.
- `stability` báo `x/k` kèm **phân bố**, không phải pass/fail — `so_nghia_vu` của
  bài thiết diện dao động `0·1·2·3·4` trên cùng một đề, và chính phân bố ấy mới
  là phát hiện.

---

## 2. `ConstructPointStmt` — hai loại điểm, và ranh giới thuộc về R0

```
ĐIỂM DỮ KIỆN    memory_declarations + initial_value
                kèm source_fact_id (đề cho) hoặc model_assumption (tự chọn
                hệ trục).  Grounding gác kênh này.

ĐIỂM DẪN XUẤT   construct_point.  Toạ độ do KERNEL tính.
```

### Bằng chứng

`expr: ValueExpr` cho phép cả `arith`, `literal`, `index`, `peek`… —
`eval_geometry_expr` từ chối chúng, nhưng ở **lúc chạy**. **Hợp đồng nói hợp lệ,
engine nói không, và mô hình tin hợp đồng:**

```json
{"kind":"construct_point","target_var":"C",
 "expr":{"kind":"arith","op":"+","left":{"var":"B"},"right":{"var":"D"}}}
```

Vi phạm R0 (LLM tự tính toạ độ) và còn **sai công thức** — đỉnh thứ tư là
`B + D − A`, chỉ đúng khi `A` ở gốc.

| Vòng đo | Lượt | Câu lệnh |
|---|---|---|
| Phase 6.7 | `2-the-tich-lan5` | `construct_point C = arith(B + D)` |
| Phase 6.7.2 | `2-the-tich-lan2` | `construct_point C = arith(B + D)` |

Hai vòng **độc lập**, hai bản mã, **cùng một câu lệnh** — thoả điều kiện *"chỉ
sửa nếu có bằng chứng lặp lại"*.

### Sửa: thu hẹp kiểu, không thêm luật

`ConstructPointStmt.expr: ValueExpr → PointExpr` — **năm** phép dựng sinh ra một
điểm:

```
intersect_line_plane · intersect_line_line · midpoint
project_onto · divide_segment
```

`intersect_plane_plane` **vắng mặt có chủ đích** (trả `Line3`, không phải điểm).
`var` cũng vắng: sao chép một điểm đã có không phải một phép **dựng**.

**Chỗ bị chặn quan trọng ngang việc bị chặn.** Trước: lỗi nổ ở `execution`, tức
**sau** vòng sửa — `thu_that_bai` của **cả hai** lượt đều **rỗng**, không một lần
thử lại nào. Nay nổ ở biên **parse**, nơi lỗi đi ngược cho mô hình sửa trong ≤3
lượt, và thông điệp Pydantic liệt kê đúng năm tag hợp lệ.

### Đóng theo bằng chứng, không theo suy đoán

| Nguồn | `construct_point` dùng gì |
|---|---|
| 30 chương trình đã sinh | `midpoint` ×22 · `arith` ×2 · **không gì khác** |
| toàn bộ test trong kho | `midpoint` · `project_onto` · `intersect_line_line` · `divide_segment` · `intersect_line_plane` |

Một test đọc lại **mọi** chương trình đã sinh ở hai vòng đo và khẳng định chỉ
đúng hai lượt `arith` hỏng — chúng **vốn đã hỏng**, chỉ hỏng muộn hơn.

### Thẻ văn phạm phải nói ra

Hợp đồng hẹp mà thẻ vẫn gọi là *"biểu thức"* thì mô hình vẫn hiểu chỗ ấy nhận
bất kỳ biểu thức nào — đúng cái hiểu đã đẻ ra `arith(B+D)`. Nay:

```
construct_point: target_var:tên expr:phép dựng ĐIỂM label?:tên
assign:          target_var:tên expr:biểu thức          ← KHÔNG đổi
```

Nhãn **dẫn xuất** bằng cách so **tập tag**, không so tên. `assign` giữ nguyên vì
nó thật sự nhận mọi biểu thức.

⚠️ `_tag` phải nhận **hai** hình dạng: alias gốc là
`Annotated[Union, Discriminator]`, nhưng Pydantic **bóc lớp ngoài** ở
`model_fields[...].annotation`. Bản đầu chỉ xử một dạng và **im lặng trả rỗng**
ở đúng chỗ nó được gọi — thẻ vẫn in "biểu thức" mà không báo gì.

### Bốn điều kiện của pha này

| | |
|---|:-:|
| không sửa kernel | ✅ |
| không sửa renderer | ✅ (frontend 0 dòng ngoài schema sinh lại) |
| không thêm DSL ngoài hình học | ✅ `PointExpr` **không thêm** một `kind` nào vào `ValueExpr` — nó **chọn ra** một tập con |
| chỉ sửa contract/validator nếu có bằng chứng | ✅ lặp lại ở hai vòng đo độc lập |

Khác biệt giữa *"siết hợp đồng"* và *"mở rộng DSL"* có test riêng:
`tag(PointExpr) ⊆ tag(ValueExpr)`.

---

## 3. Smoke — **3/3**

```
1 · trung điểm    ✅  25s ·  7 đối tượng ·  4 bước   A B D C S SA M
2 · thể tích      ✅  25s ·  8 đối tượng ·  4 bước   … ABCD S.ABCD V_S_ABCD
                       V = 12  ✓ kiểm tay 1/3·3²·4
3 · thiết diện    ✅ 152s · 14 đối tượng · 10 bước
                       A B C D S M N P PMN ABCD_plane d AD_line Q S_ABCD_solid
```

Cả ba đều đủ loại đối tượng đề đòi và đều **có diễn tiến** (>1 bước phát lại).

---

## 4. Lỗi còn lại thuộc **model** hay **contract**?

Tổng hợp 30 lượt đo + 3 smoke, phân loại theo bốn nhóm đóng:

| Nhóm | Trạng thái |
|---|---|
| **routing** | **0** lỗi trong 30 lượt. Đóng. |
| **validator** | 2 lỗi ở Phase 6.7 → **đã sửa và chứng minh** ở 6.7.1 (chạy lại chính IR, không sửa chương trình). **0** lỗi ở 6.7.2. Đóng. |
| **contract** | 1 lỗi (`arith` trong `construct_point`) → **đã sửa ở pha này**, có bằng chứng lặp lại. |
| **model generation** | **CÒN — và là nhóm duy nhất còn lại.** |

### Nhóm model còn lại là những gì

Từ 6 lượt trượt ở Phase 6.7 (sau khi trừ 2 lỗi validator và 1 lỗi contract):

- khai **đúng một** biến đặt tên theo nghĩa vụ (`point_on_line_M_SA`), không dựng gì
- bỏ sót `model_assumption` cho **đúng một** điểm trong năm
- tự thêm một nghĩa vụ đề **không hỏi**, sai kiểu container
- lượt đọc đề khai **rỗng** nghĩa vụ trên một đề rõ ràng có mệnh đề kiểm được

Bốn thứ ấy **không chung một nguyên nhân kỹ thuật**. Chúng chung một tính chất:
mỗi lần mô hình đi chệch một luật **khác nhau**, và luật nào cũng đã có sẵn
trong prompt hoặc trong thẻ văn phạm.

Đó là chữ ký của **độ ổn định sinh**, không phải của một lỗ hệ còn sót. Và nó là
**thứ Phase 7 cần ĐO**, không phải thứ cần triệt tiêu trước Phase 7.

### Một quan trắc chưa đóng, không phải lỗi

`construction_validity` đo được **0% literal substitution** trên 231 vật và
**100% witness dẫn xuất** — tức khi mô hình sinh được chương trình thì chương
trình ấy **thật sự dựng hình**. Nhưng `obligation_match` cho thấy hệ **tự kiểm
rất ít**: có lượt `served` với `so_nghia_vu = 0`, và khi ấy `servable = true`
nghĩa là *"chạy trọn và mọi thứ lên được hình"*, **không** phải *"đáp án đã được
đối chiếu"*.

Đó là chỗ luận điểm mỏng nhất của đề tài. Nó **không** phải một bug — nó là một
**giới hạn cần đo và cần khai**, và hợp đồng chỉ số đã buộc mọi báo cáo Phase 7
phải nêu nó ra.

---

## 5. Đủ điều kiện mở Phase 7 chưa?

# ✅ ĐỦ — mở được Phase 7A pilot

| | Điều kiện | |
|---|---|:-:|
| 1 | môi trường: doctor PASS, cây sạch, cache 0, candidate đóng băng | ✅ |
| 2 | `pytest 2856` · `vitest 1598`, **0 đỏ** | ✅ |
| 3 | smoke **3/3**, cả ba đủ đối tượng và có diễn tiến | ✅ |
| 4 | **routing**: 0 lỗi / 30 lượt | ✅ |
| 5 | **validator**: 0 lỗi / 15 lượt sau bản vá 6.7.1 | ✅ |
| 6 | **contract**: lỗi cuối đã sửa, có bằng chứng lặp lại | ✅ |
| 7 | AI **dựng phụ thuộc**, không khai kết quả (0/231, 27/27) | ✅ |
| 8 | hợp đồng chỉ số đã chốt **trước** khi đo | ✅ |
| 9 | kỳ vọng nghĩa vụ đến từ **nguồn ngoài** | ⚠️ **chưa có** |

**⑨ là điều kiện duy nhất chưa thoả, và nó không sửa được bằng code.** Kỳ vọng
nghĩa vụ cho mỗi đề held-out phải đến từ đáp án nguồn ngoài — nếu tôi tự đặt,
mọi chỗ tôi đọc đề khác mô hình sẽ được ghi thành *"mô hình sai"*, và Phase 6.7.2
đã cho thấy chuyện ấy xảy ra thật (5/5 lượt bác bỏ kỳ vọng của tôi, một cách có
lý).

`HOLDOUT_PROTOCOL §2` đã có sẵn cơ chế cho đúng vấn đề ấy — nhưng nó vẫn đang
**chặn cứng ở seed của GVHD**, và pool chưa có.

### Khuyến nghị cho Phase 7A pilot

Pilot **không** cần ⑨, vì pilot không tuyên bố con số của luận văn:

1. Chạy trên **tập DEV** (`dev/cases.json`, 10 bài) với `k = 3`, ngân sách dẫn từ
   call graph: `6 logic × 10 × 3 = 180 logic / 240 HTTP`.
2. Báo cáo đủ **năm** chỉ số, không gộp, theo `PHASE7_METRIC_CONTRACT.md`.
3. Mục tiêu của pilot là **kiểm bộ đo**, không phải lấy điểm: xem năm chỉ số có
   phân biệt được các trường hợp không, và taxonomy bốn nhóm có phủ hết lỗi
   không.
4. Số của tập DEV **không bao giờ** là số của luận văn — nó đã bị nhìn và hệ đã
   được sửa theo nó qua tám wave.

Con số held-out chỉ có sau khi ⑨ được giải quyết, và cửa ấy nằm ở phía người
hướng dẫn, không ở phía code.

---

## Chi phí

3 lượt smoke ≈ **20 lượt LLM**. Phần còn lại của pha này chạy **0 API call** —
bằng chứng cho việc thu hẹp `PointExpr` lấy từ 30 chương trình đã lưu.
