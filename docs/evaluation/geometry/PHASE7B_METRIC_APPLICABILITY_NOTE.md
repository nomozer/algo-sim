# PHASE 7B — PHẠM VI ÁP DỤNG CỦA BỘ CHẤM · GHI CHÚ TRÌNH BÀY

> Kết quả **một** lượt dry-run trên artifact đã lưu. **0 API call · không
> benchmark · không sửa hệ · không sửa `PHASE7_METRIC_CONTRACT`.**
>
> ⚠️ File này **không** phải hợp đồng chỉ số. Hợp đồng đã đóng băng ở
> `PHASE7_METRIC_CONTRACT §6` và không đổi. Đây là **ghi chú cách đọc** — nó
> tồn tại vì một con số `x/k'` đọc sai thì sai ở luận văn, không sai ở code.

```
METRIC_APPLICABILITY_READY:  YES
SCORER_ERRORS:               0
```

---

## 1. Đã chấm cái gì

```
210 bản ghi thô  →  81 LƯỢT CHẠY phân biệt
```

⚠️ **Con số thô đếm trùng.** `tong_hop.json` và `phan_tich_phu_thuoc.json` chép
lại chính những lượt nằm ở artifact từng-lượt. Gộp theo `(nguồn, case_id, lần)`
mới ra đơn vị thật. Báo `210` là thổi phồng cỡ mẫu **gấp 2,6 lần** — và đó là
kiểu sai không ai bắt được từ bảng kết quả.

| Nguồn | Lượt |
|---|--:|
| `phase7a-pilot` · `phase7a-pilot-sau-71` | 15 · 15 |
| `stability-6.7` · `stability-6.7.2` | 15 · 15 |
| `dev-results-55` · `dev-results-w4` | 10 · 10 |
| `demo` | 1 |

---

## 2. Từng chỉ số — `N_total` · `applicable` · `N/A`

| | Chỉ số | `N_total` | applicable | N/A | Kết quả trong phần applicable |
|---|---|--:|--:|--:|---|
| ① | `served` | 81 | 60 | 21 | `49/60` servable |
| ② | `oracle` | 81 | 50 | 31 | `50/50` |
| ③a | `construction_match` | 59 | **32** | **27** | `28/32` |
| ③b | `verification_match` | 59 | 59 | 0 | `51/59` |
| ⑤ | `stability` | 15 đề | 5 đề | 10 đề | — |

**Mỗi chỉ số có `N` RIÊNG.** Không có một mẫu số chung cho cả bảng, và ép
chúng về một mẫu số là bịa ra dữ liệu không tồn tại.

---

## 3. Vì sao N/A — từng cái một, đều đúng ngữ nghĩa nhiệm vụ

### ③a `construction_match` — N/A khi **đề không đòi dựng vật nào**

Tra thẳng kỳ vọng, không suy:

| Đề | vật phải dựng | ③a |
|---|--:|---|
| `1-trung-diem` | 1 | áp dụng |
| `3-pmn-giao-tuyen` | 6 | áp dụng |
| `2-the-tich` | **0** | **N/A** |
| `4-khoang-cach` | **0** | **N/A** |
| `5-goc` | **0** | **N/A** |

Ba đề N/A đều là bài **đo lường**: *"tính thể tích"*, *"tính khoảng cách"*,
*"tính góc"* — chúng hỏi một **con số**, không ra lệnh dựng một vật có tên. Không
có vật nào để đối chiếu thì `None` là câu trả lời **đúng**, không phải thất bại.

> **Không sửa chỉ số để ép mọi bài có ③a.** Ép thì mỗi bài đo lường sẽ nhận một
> điểm dựng bịa ra từ hư không, và ③a hết đo được thứ nó sinh ra để đo.

⚠️ **Hệ quả phải lường trước cho lượt held-out.** `BANG_O` có **5/14 ô tầng A**
là ô đo lường — `A09` `A10` `A11` `A12` `A14` — và đó cũng đúng là những ô dễ
kiếm đề nhất. Nếu tập thu được nghiêng về chúng, `k'` của ③a sẽ nhỏ. Số nhỏ vẫn
báo được; cái không được làm là đọc nó như tỉ lệ.

### ② `oracle` — N/A khi lượt chạy **chưa tới chỗ có kết quả**

```
21 lượt  ·  không có ban_ghi đầy đủ (dừng trước khi thực thi)
10 lượt  ·  "không có final_memory"
```

### ⑤ `stability` — N/A khi đề **chưa chạy đủ `k = 3` lượt**

5 đề pilot có đủ 3 lượt; 10 đề DEV (`geo_01`…`geo_10`) mỗi đề **một** lượt.
Đúng định nghĩa: `stability` đo phương sai **giữa các lượt**, một lượt thì không
có phương sai nào để đo.

---

## 4. Một lượt cho thấy vì sao ① không được báo một mình

```
3-pmn-giao-tuyen · lần 1
    oracle_dat = True        ← kernel tính ĐÚNG
    servable   = False       ← nhưng KHÔNG phục vụ được
    stage      = learner_surface
    envelope   = unsupported
```

Hệ ra đúng đáp số mà vẫn không dựng nổi bề mặt cho học sinh. Đây là lý do
`PHASE7_METRIC_CONTRACT §C` đã dặn *"① không báo một mình — luôn kèm ③"*; lượt
này là ca cụ thể của luật ấy. Nó cũng là lý do `N_applicable` **lệch nhau giữa
các chỉ số**: ② áp dụng được cho một lượt mà ① đánh dấu không phục vụ được.

---

## 5. QUY TẮC TRÌNH BÀY — dùng cho báo cáo Phase 7B

Mỗi chỉ số báo **bốn** con số, không rút gọn:

```
<tên chỉ số>:
    x / k'          ← k' = số lượt chỉ số ấy THỰC SỰ áp dụng được
    N_total
    N_applicable
    N_not_applicable
```

Ví dụ đúng khuôn, lấy thẳng từ dry-run này:

```
construction_match:
    28/32
    N_total            59
    N_applicable       32
    N_not_applicable   27   (đề đo lường, không có vật phải dựng)
```

**Ba điều cấm:**

- ❌ Nội suy `N/A` thành pass **hoặc** fail. `None ≠ False` — đây là luật đã có
  trong hợp đồng, ghi lại ở đây vì nó là chỗ dễ trượt nhất khi lên bảng.
- ❌ Dùng một mẫu số chung cho cả bảng. Mỗi chỉ số một `N`.
- ❌ Suy tỉ lệ khi `k'` nhỏ. Tầng A có 14 bài; `x/k'` đọc là **đếm thô**.

---

## 6. Ranh giới sử dụng chính những con số trong file này

Số ở đây đến từ **artifact DEV** — bốn wave đã sửa hệ theo đúng những đề ấy.
Chúng dùng được để:

- xác nhận bộ chấm **chạy** (0 lỗi trên 59 lượt chấm được);
- biết chỉ số nào áp dụng tự nhiên cho nhóm nhiệm vụ nào;
- chốt cách đọc kết quả trước khi có kết quả.

**Không** dùng được để: công bố độ tin cậy · sửa chỉ số · sửa hệ · chọn bài
held-out có lợi · loại bài mà hệ hay trượt · đổi ranh giới năng lực.

⚠️ Riêng `② oracle 50/50` và `③b 51/59` là số **trên tập đã ôn**. Đặt chúng cạnh
số held-out mà không nói rõ điều đó là so hai thứ khác nhau.
