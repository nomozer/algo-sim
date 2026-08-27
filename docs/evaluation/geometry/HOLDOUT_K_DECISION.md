# QUYẾT ĐỊNH `k` CHO LƯỢT HELD-OUT — hồ sơ lựa chọn, CHƯA triển khai

> Phải chốt **TRƯỚC khi xin seed**. Chốt sau khi thấy số là chọn thước theo
> điểm, và ở đây nó tệ hơn bình thường: `k` quyết định *chỉ số nào báo cáo
> được*, nên đổi `k` muộn là đổi cả danh sách chỉ số.
>
> Văn bản này **không** thực thi gì. Nó trình bày lựa chọn, chi phí, và cái mất
> của từng phương án.

---

## 0. Mâu thuẫn cần hoà giải

| Nguồn | Nói gì |
|---|---|
| `HOLDOUT_PROTOCOL §2` · §5⑤ | **"Chạy MỘT LƯỢT.** Trượt thì ghi nhận là trượt." |
| `PHASE7_METRIC_CONTRACT §2⑤` | **"Mỗi đề chạy `k ≥ 3` lượt độc lập."** Báo `x/k`, **không** pass/fail |
| `PHASE7_METRIC_CONTRACT §4` | Cấm *"báo pass/fail cho một đề chạy `k` lượt"* |

### Hai câu ấy KHÔNG thật sự chống nhau — và đây là chỗ dễ đọc nhầm

*"Chạy một lượt"* ở §2 sinh ra từ §6 (*"không sửa hợp đồng theo từng bài"*): nó
cấm **lặp có sửa** — chạy, thấy trượt, sửa hệ, chạy lại trên cùng tập. Cái đó
biến held-out thành DEV.

`k` lượt **trong cùng một phiên đã niêm phong**, không sửa gì giữa chừng, không
chọn lượt đẹp, **không** vi phạm điều ấy. Nó là *một lượt đo* gồm `k` phép lấy
mẫu — đúng nghĩa §2 quan tâm.

⇒ Mâu thuẫn thật chỉ còn là **ngân sách**.

---

## 1. Chi phí — dẫn từ call graph, không ước lượng

Trần mỗi bài đã duyệt: **6 logic · 8 HTTP** (analyze ≤2 · semantic_analyze 1 ·
semantic_program ≤3, cộng đệm transient). N = 20 ô.

| Phương án | Lượt chạy | Logic | HTTP | So với trần đã duyệt |
|---|--:|--:|--:|---|
| **A** — `k=1` toàn bộ | 20 | 120 | 160 | **= 1,0×** (đúng trần) |
| **B** — `k=3` toàn bộ | 60 | 360 | 480 | **3,0×** |
| **C** — `k=3` tầng A · `k=1` tầng B | 48 | 288 | 384 | **2,4×** |

---

## 2. Option A — `k = 1`

**Được:** đúng chữ của giao thức gốc · rẻ nhất · không cần duyệt ngân sách mới.

**Mất — và mất nhiều hơn vẻ ngoài:**

- **⑤ `stability` không báo cáo được.** Nó là chỉ số **đã đóng băng**
  (`§6`), nên bỏ nó không phải là "báo cáo gọn hơn" mà là **một thay đổi hợp
  đồng chỉ số**, phải khai ở `§7` kèm lý do. Đóng băng ở 7A.2 rồi phá ở 7B là
  đúng thứ việc đóng băng sinh ra để ngăn.
- **Mọi chỉ số còn lại thành pass/fail.** `§4` cấm báo pass/fail cho một đề
  chạy `k` lượt — ở `k=1` thì không còn `x/k` nào để báo, và mỗi ô thành một
  điểm nhị phân. Với N=14 tầng A, một bài đổi chiều là **±7 điểm phần trăm**.
- **Bằng chứng nói con số ấy không bền.** Hai lần đo được trên chính kho này:

  ```
  Phase 6.6   cùng mã, cùng ba đề, hai lượt liên tiếp:  0/3  rồi  3/3
  Phase 7A    5-goc: lượt 1 và 3 qua, lượt 2 trượt — `analyze` không tất định
              khi khai vai trò `geometric_perpendicular`
  ```

  Lượt 2 ấy, nếu là lượt **duy nhất**, sẽ vào luận văn thành *"mô hình không
  làm được"*. Nó không đúng.

---

## 3. Option B — `k = 3` toàn bộ ⟵ **KHUYẾN NGHỊ**

**Được:**

- Giữ **trọn bộ chỉ số đã đóng băng**, không phải sửa hợp đồng ở `§7`.
- Đo được thứ mà tập DEV đã chứng minh là có thật: **phương sai giữa các lượt**.
  `§2⑤` đòi báo **phân bố**, không chỉ tỉ lệ — `so_nghia_vu` của bài thiết diện
  từng dao động `0 · 1 · 2 · 3 · 4` trên **cùng một đề**, và chính phân bố ấy là
  phát hiện, không phải trung bình.
- Phân biệt được hai câu rất khác nhau mà `k=1` gộp làm một: *"hệ không làm
  được bài này"* và *"hệ làm được bài này 2 lần trên 3"*. Với một luận văn về
  **độ tin cậy** của đường sinh, câu thứ hai mới là câu đang hỏi.
- Tầng B cũng cần `k`: bằng chứng 7A cho thấy **chính hành vi từ chối cũng
  không tất định**. `k=1` ở đó là tung đồng xu, và ô B03 — ô khó nhất — sẽ
  không phân biệt được *"hệ nói thẳng"* với *"hệ vừa may"*.

**Mất:** **3,0× trần đã duyệt** → cần một quyết định ngân sách tường minh
**trước** khi rút seed.

---

## 4. Option C — `k=3` tầng A, `k=1` tầng B (phương án lui)

Rẻ hơn B **20%** (288/384). Lý lẽ: tầng B chấm **nhị phân** (từ chối trung thực
/ bịa hình) và **không** nuôi A · O · ③, nên `k` ở đó rẻ tiền hơn về mặt thông
tin.

**Nhưng** phải khai thẳng cái mất: sáu ô B trở thành **một lần lấy mẫu duy
nhất**, và bằng chứng 7A nói hành vi từ chối *không* tất định. Báo cáo khi ấy
buộc phải viết *"tầng B: 1 lượt/ô, chưa đo được độ ổn định của từ chối"* — chứ
không được im.

Dùng C **chỉ khi** ngân sách B bị từ chối. Không dùng C như lựa chọn mặc định:
nó tiết kiệm 96 HTTP để đánh đổi lấy đúng câu hỏi mà tầng B sinh ra để trả lời.

---

## 5. Khuyến nghị

> **Option B — `k = 3` cho cả 20 ô. 360 logic / 480 HTTP.**
>
> Lui về **C** nếu ngân sách không duyệt. **Không** lui về A: `k=1` buộc phải
> phá một chỉ số vừa đóng băng, và làm thế ở đúng lượt đo chính thức thì con số
> thu được yếu hơn nhiều so với phần tiết kiệm được.

**Ba việc đi kèm nếu chọn B**, phải làm **trước** khi rút seed:

1. Sửa `HOLDOUT_PROTOCOL §2`/`§5⑤` thành *"chạy MỘT PHIÊN, `k` lượt mỗi ô,
   không sửa hệ giữa chừng"* — làm rõ chữ *"một lượt"*, và ghi rằng đây là làm
   rõ chứ không phải nới lỏng.
2. Cập nhật ngân sách ở `§5` từ `120/160` lên `360/480` kèm phép nhân dẫn ra nó.
3. Ghi lần đổi vào `PHASE7_METRIC_CONTRACT §7` — kể cả khi nó **không** đổi
   định nghĩa chỉ số nào, vì nó đổi **điều kiện đo** của ⑤.

Cả ba đều là sửa **tài liệu giao thức**, không sửa hệ, và đều phải xong **trước**
seed — sau seed thì mọi thay đổi đều nằm sau con dấu.

---

## 6. Điều văn bản này KHÔNG làm

- **Không** chọn thay. `k` đổi ngân sách thật, nên quyết định thuộc về người
  trả ngân sách.
- **Không** chạy gì. 0 API call.
- **Không** sửa `HOLDOUT_PROTOCOL` hay hợp đồng chỉ số. Ba việc ở §5 là việc
  **sau khi có quyết định**, cố ý chưa làm.
