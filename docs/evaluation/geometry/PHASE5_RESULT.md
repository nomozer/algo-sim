# PHASE 5 — GEOMETRY DEV EVALUATION · kết quả

> **TẬP DEV, KHÔNG phải benchmark.** Được nhìn, hệ được sửa theo nó. Số ở đây
> **không bao giờ** là số held-out của luận văn — held-out phải do custodian
> chọn bằng seed của GVHD.

| | |
|---|---|
| Commit | `5c93e22` · cây sạch · `freeze --verify` PASS |
| `CACHE_VERSION` | 38 |
| Model | `gemini-2.5-flash` |
| Chạy | **10/10 case**, `hoan_tat = true`, không đứt ngân sách |
| Prompt | `geometry_program_generator.md`, **không sửa trong và sau khi chạy** |

---

## 1. Kết quả — đếm thô, không phần trăm

Mẫu số 10 < 20 nên `RELIABILITY_EVALUATION_PLAN §3.3` cấm viết tỉ lệ phần trăm.

| Chỉ số | Kết quả | Nghĩa |
|---|---|---|
| **G1** cú pháp | **6/10** | IR qua schema Pydantic |
| **G2** ngữ nghĩa | **6/10** | qua `validate_semantic_program` |
| **A** chạy trọn | **0/10** | interpreter chạy hết, 0 vi phạm biên |
| **O** oracle | **0/0** | ← **không phải 0/10, đọc §4** |
| `obligation_match` | **3/6** | khai đúng LOẠI nghĩa vụ đề hỏi |
| `replay_R` · `assurance_B` · `renderer_V` | **chưa đo** | không case nào tới được các tầng ấy |

---

## 2. Từng case

| case | G1 | G2 | A | tầng | mã lỗi |
|---|:-:|:-:|:-:|:-:|---|
| geo_01 | ✅ | ✅ | ❌ | 6 | `input_not_grounded` |
| geo_02 | ✅ | ✅ | ❌ | 6 | `input_not_grounded` |
| geo_03 | ✅ | ✅ | ❌ | 6 | `input_not_grounded` |
| geo_04 | ✅ | ✅ | ❌ | 6 | `input_not_grounded` |
| geo_05 | ✅ | ✅ | ❌ | 6 | `input_not_grounded` |
| geo_06 | ✅ | ✅ | ❌ | 6 | `requested_operation_uncovered` |
| geo_07 | ❌ | ❌ | ❌ | 2 | `semantic_program_invalid` |
| geo_08 | ❌ | ❌ | ❌ | 2 | `semantic_program_invalid` |
| geo_09 | ❌ | ❌ | ❌ | 2 | `semantic_program_invalid` |
| geo_10 | ❌ | ❌ | ❌ | 2 | `semantic_program_invalid` |

**Phân bố: tầng 6 = 6 · tầng 2 = 4.** Tầng 3 (execution) và 4 (toán sai): **0 —
vì không case nào tới được đó.**

---

## 3. Ba chế độ hỏng, và chúng nói lên điều khác nhau

### ① `input_not_grounded` — 5/10. **Hợp đồng MÂU THUẪN với prompt.**

Đề hình học **không cho toạ độ**. Prompt **bảo mô hình tự đặt hệ toạ độ** — đó
là yêu cầu đúng, và là nửa khó của bài toán sinh ở miền này.

Nhưng `grounding_gate` đòi mọi `initial_value` không phải hạt khởi tạo phải có
`source_fact_id` trỏ về một mục dữ liệu **trong đề**. Toạ độ `A(0,0,0)` do mô
hình chọn **không có trong đề**, nên bị từ chối.

> Prompt bảo *"hãy chọn hệ toạ độ"*; cổng trả lời *"anh lấy dữ liệu này ở đâu ra?"*
> Không có đường nào để mô hình thoả cả hai.

Đây là **lỗi kiến trúc**, không phải lỗi của mô hình. Ở miền Tin học, toạ độ là
**dữ liệu đề cho**; ở hình học, hệ toạ độ là **lựa chọn mô hình hoá**. Cổng
grounding chưa biết phân biệt hai thứ.

Cùng họ với căng thẳng đã ghi nhận ở miền cũ (bảng cặp ngoặc là **hằng số thuật
toán**, không có fact để ghim) — nhưng ở hình học nó không phải ca lẻ: **nó
chặn mọi bài**.

### ② Bịa `kind`/`type` ngoài taxonomy đóng — 4/10

| Bịa ra | Số ca | Loại |
|---|---:|---|
| `type: volume` | 2 | **dùng tên NGHĨA VỤ làm MemoryType** |
| `type: angle` · `type: perpendicular` · `distance` | 3 | như trên |
| `kind: construct_plane` · `construct_solid` | 2 | câu lệnh dựng chưa có |

Hai nhóm, hai nguyên nhân khác nhau:

- **Lẫn hai taxonomy.** Mô hình khai `{"name":"V","type":"volume"}` — lấy tên
  *nghĩa vụ* làm *kiểu bộ nhớ*. Thẻ văn phạm liệt kê cả hai họ tên, và bảng
  *"đề hỏi gì → nghĩa vụ nào"* trong prompt dùng đúng những tên ấy. Nhìn từ phía
  mô hình, đó là một nhầm lẫn **hợp lý**.
- **Thiếu phép dựng.** `construct_plane` / `construct_solid` không tồn tại — IR
  chỉ có `construct_point`/`line`/`section`. Mô hình cần dựng một mặt phẳng
  (vd `(SBC)` từ ba điểm) và không có từ nào để nói.

### ③ `requested_operation_uncovered` — 1/10 (geo_06), cổng C₁a

Chương trình hợp lệ nhưng không có đường tạo ra thứ nghĩa vụ đòi.

---

## 4. Vì sao `O = 0/0`, không phải `0/10`

**Không một chương trình nào chạy tới interpreter.** Oracle không có gì để chấm.

Ghi `0/10` sẽ đọc thành *"mô hình tính sai toán 10 lần"* — hoàn toàn sai. Sự
thật là **phép đo chưa chạm được tới thứ nó định đo**.

> Lượt này **không thu được một dữ liệu nào** về năng lực suy luận hình học của
> mô hình. Nó đo được **hợp đồng của chúng ta**, không đo được **mô hình**.

---

## 5. `obligation_match` — 3/6, và chỗ lệch có ý nghĩa

| case | đề mong | mô hình khai | khớp |
|---|---|---|:-:|
| geo_01 | `point_on_plane` | `point_on_plane` | ✅ |
| geo_02 | `point_on_line` | **`derived_sequence`** | ❌ |
| geo_03 | `coplanar` | **`structural_traversal`** | ❌ |
| geo_04 | `point_on_plane` | **`predicate_verdict`** | ❌ |
| geo_05 | `perpendicular` | `perpendicular` | ✅ |
| geo_06 | `parallel` | `parallel` | ✅ |

Ba nghĩa vụ bị khai nhầm — `derived_sequence`, `structural_traversal`,
`predicate_verdict` — **đều là nghĩa vụ của miền TIN HỌC**.

Nguyên nhân xác định được: runner chỉ ép skill ở `stage_semantic_program`;
`stage_semantic_analyze` **vẫn dùng `semantic_analyze.md`** của miền Tin học, và
enum của nó nay chứa **cả 19 nghĩa vụ**. Mô hình chọn nghĩa vụ Tin học cho bài
hình học vì prompt phân tích không hề nhắc tới hình học.

Đây là **lỗ trong thiết kế lượt đo**, không phải lỗ của mô hình.

---

## 6. Trả lời ba câu

### ① AI đã sinh Geometry Program chưa?

**Một phần: 6/10 sinh ra chương trình HỢP LỆ** (qua cả cú pháp lẫn thẩm định
ngữ nghĩa). Nhưng **0/10 chạy được**, nên chưa có chương trình nào **dùng được**.

### ② AI có sinh chương trình đúng toán không?

**KHÔNG TRẢ LỜI ĐƯỢC.** Điều kiện để kết luận là `executable ∧ oracle PASS ∧
obligation_match` — vế đầu đã **0/10**, nên hai vế sau không có mẫu.

Và **không được dùng** *"6/10 qua thẩm định"* để suy ra bất cứ điều gì về tính
đúng toán học: qua thẩm định nghĩa là **hình dạng hợp lệ**, không nghĩa là
**tính đúng**.

### ③ Điểm yếu nằm ở đâu?

Xếp theo số ca chặn, và **không cái nào là "mathematical reasoning"**:

| # | Điểm yếu | Ca | Thuộc về |
|---|---|---:|---|
| 1 | **Hợp đồng grounding mâu thuẫn với miền** | 5 | **kiến trúc của ta** |
| 2 | Taxonomy thiếu phép dựng (`construct_plane`) | 2 | **hợp đồng của ta** |
| 3 | Prompt để mô hình lẫn hai taxonomy | 3 | **prompt của ta** |
| 4 | `analyze` vẫn là prompt Tin học | 3 lệch | **thiết kế lượt đo của ta** |
| 5 | Suy luận hình học sai | **0** | — *chưa có dữ liệu* |

**Bốn trên bốn nguyên nhân đều thuộc về hệ, không thuộc về mô hình.**

---

## 7. KẾT LUẬN: **C — Chưa chứng minh được**

Không phải B. B (*"có khả năng nhưng chưa đủ bằng chứng"*) đòi ít nhất một
mảnh bằng chứng dương về năng lực sinh **đúng**. Lượt này có **0**.

Điều đã chứng minh được, và chỉ điều này:

> Hệ **đo được**, và phép đo **chỉ ra đúng chỗ hỏng**. Sáu trong mười chương
> trình có hình dạng hợp lệ; không cái nào chạy được; và mọi nguyên nhân chặn
> đều nằm trong hợp đồng của chúng ta, không nằm ở mô hình.

Điều **chưa** được phép nói: *"AI sinh được mô phỏng hình học"* · *"AI hiểu
hình học"* · bất cứ tuyên bố nào về tính đúng toán học.

---

## 8. Điều KHÔNG được làm sau báo cáo này

Kết quả xấu là **dữ liệu**, không phải lỗi cần vá gấp. Cấm: sửa prompt để tăng
tỉ lệ · thêm luật ép pass · nới grounding cho dễ thở · bỏ case fail · đổi
dataset · gọi lượt này là benchmark.

Bốn nguyên nhân ở §6 là **phát hiện của lượt đo**, và sửa chúng là một **wave
riêng có phạm vi khai trước** — không phải một chuỗi vá phản xạ. Đặc biệt
nguyên nhân ①: nới `grounding_gate` là đụng một cổng an toàn, phải có thiết kế
riêng và phải trả lời được *"làm sao phân biệt **lựa chọn mô hình hoá** với
**dữ liệu bịa**"*.

---

## 9. Thiếu sót của chính lượt đo này — khai để lần sau đừng lặp

- **Không ghi số lượt API.** Runner không gọi `usage_report()`, nên artifact
  không có `token`/`calls`. Ước lượng từ call graph: **20–34 lượt logic**
  (10 × analyze 1 + semantic_analyze 1 + semantic_program 1). Không xác nhận
  được, và đó là lỗi của runner.
- **`analyze` không được ép sang prompt hình học** — biết trước, chấp nhận
  trước, nhưng hệ quả (§5) lớn hơn dự kiến.
- **`renderer_V` không đo được** vì chưa có renderer; `replay_R` và
  `assurance_B` không đo được vì `A = 0`.
