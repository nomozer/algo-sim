# PHASE 5.5 — GEOMETRY GENERATION RE-EVALUATION

> **TẬP DEV, KHÔNG phải benchmark.** Được nhìn, hệ đã được sửa theo nó.

| | |
|---|---|
| Commit đo | `5f42363` · **cây sạch toàn kho và hệ được đo** |
| `measured_system_hash` | `dccf1934e4db27b0` · 141 file |
| `CACHE_VERSION` | 40 |
| Model | `gemini-2.5-flash` |
| Chạy | **10/10**, `hoan_tat = true`, không đứt ngân sách |
| Artifact | `dev-results-55/` — **không đè** baseline lượt 5.0 |

---

## 1. Metrics

| | 5.0 | **5.5** | |
|---|:---:|:---:|---|
| **G1** cú pháp | 9/10 | **9/10** | = |
| **G2** ngữ nghĩa | 9/10 | **9/10** | = |
| **A** chạy trọn | 1/10 | **1/10** | = |
| **O** oracle | 1/1 PASS | **1/1 PASS** | = |
| `obligation_match` | 10/10 | **9/10** | ▼1 |

**Điểm tổng đứng yên.** Nhưng lượt này **không phải một lượt đo lặp lại** — nó là
lượt đầu tiên có `RequestContract` trong artifact, và điều đó thay đổi hẳn thứ
kết luận được.

## 2. Từng case

| case | G1 | G2 | A | 5.0 | → | 5.5 |
|---|:-:|:-:|:-:|---|:-:|---|
| geo_01 | ✅ | ✅ | ❌ | `coverage_uncovered` | = | `coverage_uncovered` |
| geo_02 | ✅ | ✅ | ❌ | `coverage_uncovered` | → | `input_not_grounded` |
| geo_03 | ❌ | ❌ | ❌ | `input_not_grounded` | → | `semantic_program_invalid` |
| **geo_04** | ✅ | ✅ | **✅** | **OK** | = | **OK · oracle PASS** |
| geo_05–09 | ✅ | ✅ | ❌ | `input_not_grounded` | = | `input_not_grounded` |
| geo_10 | ✅ | ✅ | ❌ | `semantic_program_invalid` | → | `input_not_grounded` |

**Phân bố: tầng 6 = 8 · tầng 2 = 1 · đi trọn đường = 1** — trùng khít 5.0.

---

## 3. Failure taxonomy

| Nhóm | 5.0 | 5.5 |
|---|---:|---:|
| grounding | 6 | **7** |
| coverage C₁a | 2 | **1** |
| schema | 1 | **1** |
| dependency · execution · oracle | 0 | **0** |

---

## 4. STEP 6 — C₁a: câu trả lời, đọc được chứ không suy

Đây là lý do Wave 3 tồn tại, và nó trả lời trong một dòng:

```
CONTRACT   witness = 'm'      ← chữ THƯỜNG
CHƯƠNG TRÌNH khai   = 'M'      ← chữ HOA
details: witness 'm' chưa khai báo (chương trình khai: [A B C D M S abcd …])
```

**Không phải mô hình lệch danh xưng. Là HAI HỢP ĐỒNG CỦA TA đánh nhau.**

`analyze_contract.py` mô tả `witness`: *"Tên biến kiểu **snake_case**"*. Đó là
quy ước Tin học, và nó **đúng** ở đó. `analyze` tuân thủ: hạ `M` → `m`. Còn hình
học gọi tên điểm bằng **chữ hoa** — `A`, `B`, `M`, `S` — và lượt viết chương
trình cũng tuân thủ đúng quy ước của miền nó.

Hai lượt đều làm đúng luật được giao. Luật thì mâu thuẫn nhau, và **không tầng
nào hoà giải**.

Đo cơ học trên toàn bộ 10 bài: **đúng 1 ca** khớp mẫu "witness chỉ khác hoa
thường" — `geo_01`. Nên đây là **một nguyên nhân xác định**, không phải một lớp
lỗi rộng.

⚠️ Giả thuyết Wave 3 nêu — *"lệch danh xưng giữa hai lượt LLM"* — **sai về bản
chất**. Không phải model đặt tên khác nhau; là **schema của ta ép một quy ước
sai miền**.

## 5. Grounding — nguyên nhân THẬT, và nó không phải cái Wave 3 vá

`trích dẫn hỏng = 0` ở **cả bảy ca**. Vấn đề id namespace mà Wave 3 nhắm tới
**đã tự biến mất** — mô hình nay trích dẫn đúng id có trong hợp đồng:

```
geo_09  CONTRACT facts: abcd_hinh_vuong · canh_day · chieu_cao_sa · sa_vuong_goc_day
        IR trích dẫn  : abcd_hinh_vuong · canh_day · chieu_cao_sa       ← khớp hết
```

Chết ở chỗ khác:

```
B: giá trị [0, 0] không có trong mục 'canh_day' (cạnh đáy)
C: giá trị [1, 1, 0] không có trong mục 'abcd_hinh_vuong' (ABCD là hình vuông)
```

Mô hình khai `B = (1,0,0)`, ghim về `canh_day` (values = `1`). P2 phẳng hoá toạ
độ thành các nguyên tử `1, 0, 0` rồi đòi **từng cái** có trong mục được ghim.
`1` có; `0` không.

**Nhưng `0` ở đây không phải dữ liệu lấy từ đề.** Nó là **số không cấu trúc của
hệ trục** — "không dịch theo y, không dịch theo z". Bắt nó truy về một mục dữ
liệu là hỏi sai câu.

Và `C = (1,1,0)` ghim về `abcd_hinh_vuong` — một fact **quan hệ**, `values` rỗng.
Mô hình đang nói *"vị trí C suy ra từ việc ABCD là hình vuông"*. Đó là lập luận
**đúng**, và phép kiểm theo giá trị không có cách nào diễn đạt nó.

Hai ca còn lại (`geo_02`, `geo_06`) là dạng khác và cổng chặn **đúng**: biến
`bool` tên `point_on_plane`/`parallel` khai sẵn `initial_value` — mô hình khai
thẳng đáp án.

### Vì sao dự đoán offline của Wave 3 trật

Tôi đã đo `grounding 0/6 → 3/6` và **khai rõ là đo với hợp đồng rỗng, ca xấu
nhất**. Hướng sai hoá ra ngược lại: hợp đồng rỗng ⇒ trích dẫn **không giải
được** ⇒ rơi vào nhánh giả thiết mà Wave 3 vừa mở ⇒ qua. Hợp đồng **thật** ⇒
trích dẫn **giải được** ⇒ đi đường nghiêm ngặt ⇒ chết ở so giá trị.

Nói thẳng: **bản vá Wave 3 TASK 2 gần như không tác dụng ở lượt này**, vì vấn đề
nó nhắm tới đã tự hết. Cái có tác dụng là TASK 1 (§4) và TASK 5.

## 6. Hai ca đổi mã lỗi — cả hai đều là **tiến lên một tầng**

`geo_10` `schema → grounding`: lỗi bọc thừa `literal` quanh `through`/`vertices`
**không lặp lại**. Wave 3 quyết định không vá nó vì *"một lần là giai thoại"* —
quyết định ấy nay có bằng chứng.

`geo_03` `grounding → schema`: lỗi **mới**, khác hẳn —
`field.field = 'vertices'` (chỉ nhận `left`/`right`/`val`/`data`). Mô hình cố
đọc trường của một `solid` bằng phép truy cập trường của cây nhị phân.

`geo_02` `coverage → grounding` + là ca `obligation_match` lệch duy nhất: khai
`point_on_plane` cho đề hỏi `point_on_line` (dựng giao tuyến hai mặt phẳng).

---

## 7. Cost report — số THẬT

| | 5.0 | **5.5** |
|---|---:|---:|
| lượt logic | 28/60 | **30**/60 |
| HTTP request | 30/80 | **30**/80 |
| retry · 429 | 2 · 0 | **0 · 0** |
| tổng token | 143 098 | **196 851** |
| USD (chặn trên) | 0.2171 | **0.3379** |

```
prompt      71 311        thoughts    101 788   ← 52% tổng token
candidates  23 752        cached        8 943
```

**Độ trễ: 572.211s tổng · chậm nhất một lượt 50.559s.**

Lượt 5.0 in ra `0s` vì `tong_ket` thiếu một tham số. **TASK 6 đã sửa, và đây là
xác nhận trên đường chạy thật** — không phải chỉ trong test.

`thoughts_tokens` tăng 57 871 → 101 788 (+76%) trong khi số lượt chỉ 28 → 30.
Mô hình **nghĩ nhiều hơn hẳn** cho cùng bộ đề.

---

## 8. STEP 5 — so sánh, và điều KHÔNG được kết luận

**Không nói "AI đã tốt hơn".** G1/G2/A/O đứng yên, `obligation_match` **giảm** 1.

Nhưng cũng **không nói "không tiến bộ"**. Thứ tiến bộ là **năng lực đo**:

| | 5.0 | 5.5 |
|---|---|---|
| nguyên nhân C₁a | suy từ dấu vết | **đọc được: `m` vs `M`** |
| id namespace | giả thuyết hàng đầu | **đo được: 0 ca** |
| nguyên nhân grounding | "không truy được về đề bài" ×6 | **so giá trị trên toạ độ** |
| độ trễ | `0s` (sai) | **572.211s** |

### Phân định lỗi hợp đồng vs lỗi model

| Nguyên nhân | Ca | Của ai |
|---|---:|---|
| P2 so GIÁ TRỊ trên toạ độ | 5 | **hợp đồng của ta** |
| `witness` snake_case vs điểm chữ hoa | 1 | **hợp đồng của ta** |
| khai `bool` đáp án sẵn | 2 | **model** — cổng chặn đúng |
| `field.field='vertices'` | 1 | **model** |
| khai sai nghĩa vụ (`geo_02`) | 1 | **model** |

**6/9 thất bại thuộc hợp đồng, 3/9 thuộc model.** Lần đầu tỉ lệ này đo được thay
vì ước.

---

## 9. STEP 7 — kết luận khoa học

**Được phép nói:**

> Hệ đã đo được khả năng sinh **Geometry Program** của LLM trong semantic
> simulation framework, và **định vị được nguyên nhân thất bại tới từng dòng
> hợp đồng**.

Cụ thể: 9/10 chương trình hợp lệ · 1/10 chạy trọn · 1/1 đúng toán khi tới oracle
· 9/10 khai đúng nghĩa vụ.

**KHÔNG được nói:** *"AI sinh mô phỏng 3D"*. `B` (servable) chưa đo được —
tập nguyên thuỷ thị giác không có nguyên thuỷ 3D nào. Renderer chưa có. Tương
tác 3D chưa có.

**Cũng không được nói** `1/1` là độ tin cậy toán học: một mẫu không phải một tỉ lệ.

---

## 10. Chờ quyết định — dữ liệu cho từng phương án

**A. Sửa C₁a** — dữ liệu **đã chứng minh**, nhưng chẩn đoán khác giả thuyết:
không cần bộ khớp ngữ nghĩa; cần hoà giải quy ước đặt tên giữa hai miền. Đi kèm
là **lỗ lớn hơn ở §5**: P2 so giá trị trên toạ độ, chặn 5 ca. Cả hai đều là hợp
đồng của ta, cả hai đều xác định được.

**B. Renderer 3D** — mở khoá `B`, trục duy nhất chưa từng đo được.

**C. Interactive geometry editor** — phụ thuộc B.

**D. Mở rộng benchmark** — ⚠️ **chưa nên**: 6/9 thất bại hiện tại thuộc hợp đồng,
nên thêm bài chỉ nhân bản cùng một lỗi và làm số khó đọc hơn.

**DỪNG.** Không sửa tiếp.
