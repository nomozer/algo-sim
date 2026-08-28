# NHẬT KÝ THU THẬP ĐỀ HELD-OUT — nguồn nào lấy được, nguồn nào không

> Lượt thu thập 2026-08-27. **0 API call của hệ** (chỉ đọc web).
>
> Ghi lại để lượt sau **không dò lại từ đầu**: sản lượng thật của từng loại
> nguồn, và một hạn chế của cách thu thập mà không lệnh nào phát hiện hộ.

---

## 0. Kết quả một câu

**0 bài `accepted`.** Năm lượt thu, **bốn rào khác nhau**, và mỗi lượt lộ ra
một rào mới — chúng che nhau:

| # | Rào | Lượt | Bản chất |
|---|---|:-:|---|
| 1 | **Định dạng** — đề nằm trong PDF/ảnh | 1 | thu thập |
| 2 | **Miền số của kernel** — dữ kiện/đáp án vô tỉ vs `Fraction` | 2 | **năng lực** |
| 3 | **Nguyên văn** — kênh tự động rơi ký hiệu toán, IM LẶNG | 3–4 | **tính toàn vẹn dữ liệu** |
| 4 | **LỆCH KIỂU NHIỆM VỤ** — 92% đề là trắc nghiệm 4 phương án | 5 | **thiết kế phép đo** |
| 5 | **`2a` KHÔNG PHÂN BIỆT được với `a√2`** khi trích PDF | 7 | **nhận nhầm bài** |

Rào **5 nặng nhất**, và nó khác hẳn bốn rào kia về **hướng hỏng**: bốn rào đầu
làm **mất bài** (an toàn — bỏ sót), rào 5 làm **nhận nhầm bài** (nguy hiểm — một
đề ngoài phủ trông như trong phủ, lọt vào tập niêm phong, rồi cái trượt của nó
vào luận văn thành *"mô hình không làm được"*). Xem **§1f**.

Rào **4** thì cần **quyết định của người**, không phải thêm công thu thập: nguồn
dễ lấy nhất (đề thi THPT sau 2025) là nguồn ít khớp nhất với kiểu nhiệm vụ.

Rào 3 đã được **giải một nửa**: HTML thô giữ nguyên văn (LaTeX còn nguyên), nên
người chỉ còn phải **đọc soát**, không phải **gõ lại**.

---

## 1b. ⛔ RÀO LỚN NHẤT — miền số của kernel (phát hiện lượt 2)

Kernel dựng trên `Fraction` **có chủ đích** (`exact.py`: so bằng đúng, không
epsilon, nên vuông góc/song song/đồng phẳng là phép so **chính xác**). Hệ quả
với việc **chọn đề** thì chưa ai viết ra, và nó loại rất nhiều:

### Ba lớp đề KHÔNG đủ tư cách vào tầng A

| Lớp | Ví dụ | Vì sao |
|---|---|---|
| **Tỉ số dữ kiện vô tỉ** | *đáy cạnh `a`, `SA = a√3`* | không hệ trục nào làm **cả hai** hữu tỉ. Chọn `a=1` ⇒ `SA=√3`; chọn `a=√3` ⇒ đáy vô tỉ |
| **Đáp án `distance` vô tỉ** | `d = a√3/3`, `d = 3√6` | `geometry_exec._do` **NÉM** `GEOMETRY_IRRATIONAL_RESULT`. Không làm tròn, **không** trả bình phương |
| (hệ quả) phần lớn đề khoảng cách trong đề thi thật | | đáp án đề thi hầu như luôn có căn |

**KHÔNG áp cho `angle` và `volume`:** `angle` trả `cos²`/`sin²` — luôn hữu tỉ
khi toạ độ hữu tỉ; `volume` của khối đa diện hữu tỉ luôn hữu tỉ. Nên **A09,
A10, A14 vẫn dễ tìm đề**; **A11, A12 mới là hai ô khó**.

### Kiểm chứng bằng chính kernel, không suy đoán

```python
d2 = distance_sq_point_plane(P, Plane3.through(M, E, D))   # = 54
_can_huu_ti(Fraction(54))                                  # → None ⇒ NÉM
```

Khoá bởi `test_distance_VO_TI_thi_engine_NEM_chu_khong_tra_binh_phuong`.

### Và một bẫy đơn vị nữa, im lặng hơn

`angle_cos_sq` trả **cos²** cho cặp đường–đường và mặt–mặt, nhưng **sin²** cho
cặp **đường–mặt** (`sin_sq_line_plane`) — cùng một tên trường. Ô **A10** (góc
đường–mặt) khai nhầm `cos²` thì chấm sai mà không cổng nào báo. Đã ghi vào
`pool.json.__don_vi_oracle__` và khoá bằng test.

### Quyết định cần người — KHÔNG tự quyết

`BANG_O` hiện **không có ô nào** nhận lớp *"đáp án vô tỉ"*: B01–B06 là chéo
nhau · đường∥mặt · nhị diện · Oxyz · mặt cong · vectơ. Ba đường đi, và cả ba
đều đổi tính chất của lượt đo:

| | Đường | Cái giá |
|---|---|---|
| **1** | **Chỉ nhận đề `distance` hữu tỉ** vào A11/A12 | tập bớt đại diện: đề thi thật hầu như luôn ra căn. Phải khai giới hạn ấy khi báo số |
| **2** | **Mở một ô tầng B** cho lớp vô tỉ, chấm bằng *từ chối trung thực* | đúng tinh thần tầng B (**hệ có nói thẳng là không biểu diễn chính xác được không?**), nhưng **N đổi từ 20** ⇒ ngân sách và `HOLDOUT_K_FINAL` phải chốt lại |
| **3** | Cho `measure` trả bình phương cho `distance` | **SỬA HỆ** ⇒ ngoài phạm vi mọi pha 7A/7B, và phá `measured_system_hash` |

Đường **3 bị loại ngay** — pha này cấm sửa hệ. Chọn giữa **1** và **2** là việc
của người duyệt, và phải xong **trước** khi soạn tiếp pool, nếu không sẽ soạn
40 bài rồi mới biết phần lớn phải loại.

---

## 1c. ⛔ RÀO THỨ BA — trích PDF cũng KHÔNG cho nguyên văn (lượt 3)

Lượt 2 kết luận *"đường nhanh hơn: chép từ PDF, vì chép từ PDF là chép nguyên
văn thật"*. **Kết luận ấy SAI khi việc chép là tự động**, và đây là bằng chứng.

Tải thật `chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-le-minh-tam.pdf`
(toanmath, 10,8 MB, **217 trang**), trích bằng **hai** thư viện độc lập
(`pymupdf`, `pypdf`). Đếm ký hiệu trên **toàn** văn bản trích được:

| Ký hiệu | Số lần xuất hiện |
|---|--:|
| `=` | **1303** |
| `⊥` **vuông góc** | **0** |
| `√` căn | **0** |
| `∈` thuộc | **0** |
| `∥` song song | **0** |
| `°` độ | 3 |

**`⊥` xuất hiện ĐÚNG 0 LẦN trong một tài liệu 217 trang về QUAN HỆ VUÔNG GÓC.**
Font toán trong PDF không có ánh xạ Unicode, nên trình trích **bỏ im lặng** đúng
những ký hiệu mang hình học.

Hậu quả cụ thể, cùng một câu (Bài 40, trang 20):

```
NGUỒN (đọc bằng mắt)   …AB = a, AD = a√3, SA ⊥ (ABCD) và SA = a…
TRÍCH TỰ ĐỘNG          … 3  ,,AB a AD a SA ABCD và  SA a .…
```

Mất `=`, mất `⊥`, mất `√`. Bản trích **vẫn đọc như một đề bài** — đó là chỗ nguy
hiểm. Đưa nó vào pool là niêm phong một **bài toán khác**.

## 1d. ✅ KÊNH THỨ BA — HTML thô GIỮ được nguyên văn (lượt 4)

Hai kênh trước hỏng vì có **một bước diễn giải lại** (tóm tắt · ánh xạ glyph).
`curl` thì không: nó trả **byte gốc**, và trên site dùng MathJax, toán nằm sẵn
trong HTML dưới dạng **LaTeX**. Hiện trường:

```html
<h3>Đề bài</h3>
<div class="math-box">
  <p>Cho hình lập phương \(ABCD.MNPQ\) có cạnh bằng \(6\). Gọi \(E\) là
     trung điểm của đoạn thẳng \(AB\).</p>
</div>
```

`\(...\)` giữ **đủ** thông tin: `\perp`, `\sqrt{3}`, `\frac` đều còn nguyên.
Không bước nào diễn giải ⇒ không bước nào làm mất.

Đóng gói thành `scripts/harvest_holdout_candidates.py`, **ba cổng trung thực**:
① có khối *Đề bài* tách được (không có ⇒ đang **đoán** đâu là đề) · ② **không**
`<img>` trong khối · ③ có dấu vết LaTeX.

### Nhưng sản lượng thì cạn — đo được, hai lượt quét

**Lượt A — lọc theo từ khoá hình học** (60 url):

```
3883 url (sitemap mathvn) → 60 ứng viên → 11 có khối đề → 2 SẠCH → 0 dùng được
```

**Lượt B — quét RỘNG toàn bộ bài 2026** (344 url, không lọc từ khoá), để kiểm
xem khuôn `math-box` có ở những bài mà slug không mang từ khoá không:

```
81/344 trang đầu → 0 trang có khối đề tách được
```

Không phải bộ lọc từ khoá quá hẹp — **khuôn `math-box` bản thân nó hiếm**, chỉ
có ở một nhúm bài. Tỉ lệ gộp hai lượt: **2 sạch / 141 trang ≈ 1,4%**, và **0%**
lọt qua ranh giới năng lực.

**Bốn nguồn khác đã thử, không nguồn nào dùng được:**

| Nguồn | Kết quả |
|---|---|
| `toanhocbactrungnam.vn` | sitemap 200, nhưng trang đề **0 LaTeX · 5 ảnh** |
| `vted.vn` · `diendantoanhoc.org` · `hoc247.net` | chặn fetch tự động / trả trang rỗng |
| `loigiaihay.com` | 189 ảnh, đề không có dạng văn bản |
| `vietjack.com` | trả 1120 byte — chặn |

Hai bài sạch: bài lập phương (**đã loại**, đáp án `3√6` vô tỉ) và một bài
**chứng minh công thức tổng quát** cho tứ diện đẳng diện — tham số ký hiệu
`a, b, c`, không phải bài cụ thể, nên cũng ngoài ranh giới.

**Cổng ② là chỗ mất nhiều nhất (9/11).** Phần lớn nội dung toán trên web tiếng
Việt là **ảnh chụp**, và `curl` cũng không đọc được ảnh.

Ba site khác đã thử (`vted.vn`, `hoc247.net`, `diendantoanhoc.org`) đều **chặn
fetch tự động** hoặc trả trang rỗng.

### ⇒ Kênh ĐÚNG, nguồn CẠN

| Kênh | Nguyên văn? | Hỏng kiểu gì |
|---|:-:|---|
| Công cụ đọc web | ❌ | đi qua một mô hình tóm tắt |
| Trích PDF tự động | ❌ | rơi ký hiệu toán, **im lặng** |
| **HTML thô + parse** | ✅ | không hỏng — nhưng **0 bài dùng được** trên nguồn đã quét |
| **Người mở nguồn đọc** | ✅ | — |

Nên `problem_text_verified` **chỉ** người hạ được, và `kiem_pool` **từ chối**
niêm phong khi nó chưa `true`. Bài chưa xác minh mang
`status: rejected_unverified` và **không được vào holdout**.

Bộ thu vẫn đáng giữ: chạy nó trên **site khác** là việc rẻ (một lệnh), và mỗi
bài SẠCH nó tìm ra là một bài người chỉ phải **đọc soát** thay vì **gõ lại**.

---

## 1e. ⛔ RÀO THỨ TƯ — LỆCH KIỂU NHIỆM VỤ (lượt 5, và đây là rào nặng nhất)

⚠️ **Sửa một con số tôi báo sai ở lượt 4.** Tôi đọc log lúc sweep đang chạy và
báo *"81 trang → 0 khối đề"*. Sai: log chưa flush. Sweep chạy xong cho
**344 url → 208 có khối đề → 125 SẠCH**. Kênh HTML thô **hiệu quả hơn nhiều**
so với con số tôi đưa ra.

### Sàng 125 ứng viên sạch

```
125 ứng viên SẠCH
  → 26  câu hình học không gian (tách theo mốc "Câu N" / "Bài N")
  →  8  trong ranh giới năng lực
        (loại: 6 dữ kiện vô tỉ · 4 Oxyz cho sẵn toạ độ · 5 mặt cong)
  →  1  không phải trắc nghiệm
  →  0  dùng được   (bài duy nhất ấy chính là bài A11 đã loại vì vô tỉ)
```

### Con số quyết định: **92% là TRẮC NGHIỆM**

```
26 câu hình học không gian tách được
  24 trắc nghiệm 4 phương án   (92%)
   2 tự luận
```

Trong 8 câu **trong ranh giới**: **7 trắc nghiệm**, 1 tự luận (đã loại vì vô tỉ).

### Vì sao trắc nghiệm là rào, không phải chi tiết

Hệ nhận đề rồi **dựng cảnh và kiểm nghĩa vụ**. Nó **không "chọn phương án"**.
Một câu như:

> *Cho tứ diện \(ABCD\) có \(M, N\) lần lượt là trung điểm của \(AB, AC\). Mặt
> phẳng nào sau đây song song với đường thẳng \(MN\)? A. \((ACD)\). B.
> \((ABD)\). C. \((ABC)\). D. \((BCD)\).*

có hình học **hoàn toàn trong ranh giới** (dữ kiện hữu tỉ, quan hệ `parallel`),
nhưng **câu hỏi** thì không phải *"chứng minh MN ∥ (BCD)"* — nó là *"chọn một
trong bốn"*. Đưa nguyên văn vào hệ thì không có nghĩa vụ nào để khai.

**Ba đường, và không đường nào tôi được tự chọn:**

| | Đường | Cái giá |
|---|---|---|
| **①** | **Nhận nguyên văn đề trắc nghiệm** | hệ không có nghĩa vụ để khai ⇒ ô chắc chắn trượt, và trượt vì **lệch kiểu nhiệm vụ** chứ không vì mô hình kém |
| **②** | **Viết lại thành đề dựng/chứng minh** | ⛔ **CẤM** — *"không tự biến đổi đề"*. Viết lại là tôi soạn đề, và tập held-out mất đúng thứ làm nó có giá trị |
| **③** | **Đổi nguồn sang đề TỰ LUẬN** | SGK · chuyên đề tự luận · đề HSG. Chúng tồn tại, nhưng nằm trong **PDF/ảnh** (rào §1c) ⇒ quay lại cần người chép |

### Vì sao rào này xuất hiện bây giờ mới thấy

Đề thi tốt nghiệp THPT môn Toán **sau 2025** gần như thuần trắc nghiệm
(trắc nghiệm nhiều phương án · đúng–sai · trả lời ngắn). Nguồn **dễ lấy nhất**
lại là nguồn **ít khớp nhất** với kiểu nhiệm vụ của hệ. Bài `hp_a11_001` che
mất điều này ở lượt 3: nó *là* tự luận (trả lời ngắn), nên tôi không thấy rằng
nó là **ngoại lệ**, không phải mẫu số chung.

### Lượt C — quét riêng nhánh SGK, để tìm đề TỰ LUẬN

Giả thuyết: bài tập SGK là **tự luận** (*"Chứng minh rằng…"*, *"Hãy dựng…"*),
nên nhánh SGK sẽ né được rào trắc nghiệm. Quét 269 url `giai-bai-tap` /
`sgk-toan` / `bai-tap-N` / `chung-minh` (2024–2026):

```
269 url → 9 có khối đề → 4 SẠCH
```

**Giả thuyết SAI, và lý do đáng ghi:** trang giải SGK **không chép lại đề bài**
— chúng viết thẳng lời giải, vì người đọc đã có sách trước mặt. Đúng thứ đã
thấy ở lượt 2 khi đọc `bai-tap-416-417-418`: có lời giải, không có đề.

### Tổng ba lượt quét, trên trục TỰ LUẬN

| Lượt | URL quét | SẠCH | Câu HHKG | **Tự luận + trong ranh giới** |
|---|--:|--:|--:|--:|
| A — lọc từ khoá | 60 | 2 | 2 | **0** |
| B — toàn bộ 2026 | 344 | 125 | 26 | **0** |
| C — nhánh SGK | 269 | 4 | ~0 | **0** |
| D — toàn bộ 2024–2025 | 481 | **0** | 0 | **0** |
| **Tổng** | **1154** | **131** | **26** | **0** |

⚠️ **Lượt D cho 0 SẠCH trên 481 url** — 7 trang có khối đề, cả 7 rớt vì không
có dấu vết LaTeX. Đây là bằng chứng cho một điều đã đoán ở lượt B: khuôn
`math-box`/`Đề bài` là **của riêng loạt bài 2026**; bài cũ hơn đăng toán bằng
**ảnh**. Quét rộng thêm về quá khứ **không** tăng sản lượng.

Sàng theo đúng luật nhận bài của Phase 7B.1 (chỉ tự luận · có mệnh lệnh dựng
hoặc tính · không vô tỉ · không Oxyz cho sẵn · không mặt cong · không cần hình
vẽ kèm): **1 câu** lọt tới vòng cuối, và nó chính là bài A11 đã loại vì vô tỉ.

⇒ **Kênh tự động đã cạn kiệt.** Không phải thiếu công quét — 673 url là đủ để
thấy quy luật: nguồn web tiếng Việt cho **lời giải**, không cho **đề tự luận
dạng văn bản**.

### Ứng viên tốt nhất tìm được — và nó kẹt ở đúng rào này

`hp_a14_cand_002` (Sở GD&ĐT Hà Tĩnh, đề thi thử TN THPT 2026 lần 2):

> *Cho hình chóp \(S.ABCD\) có đáy \(ABCD\) là hình vuông cạnh bằng \(2\), cạnh
> bên \(SA\) vuông góc với mặt phẳng đáy và \(SA=3\). Thể tích của khối chóp
> \(S.ABCD\) bằng A. \(12\). B. \(6\). C. \(8\). D. \(4\).*

Dữ kiện **hữu tỉ hoàn toàn** (2 và 3), `V = (1/3)·4·3 = 4` là **phân số chính
xác** — thoả mọi điều kiện của `CAPABILITY_BOUNDARY`. Nó kẹt **chỉ** vì bốn
phương án. Đã đưa vào `cases` với `status: needs_manual_review` để quyết định
①/②/③ có một ví dụ cụ thể trước mắt.

---

## 1f. ⛔ RÀO THỨ NĂM — trích PDF LÀM MẤT PHÂN BIỆT `2a` với `a√2`

Lượt 3 kết luận *"trích PDF rơi ký hiệu toán"*. Đúng, nhưng **chưa đủ nặng**.
Đo lại trên hai nguồn được chỉ định, và một trong hai giữ ký hiệu khá tốt:

| Nguồn | `=` | `⊥` | `√` | `∈` | `°` |
|---|--:|--:|--:|--:|--:|
| Quan hệ vuông góc — Lê Minh Tâm (217tr) | 1 | **0** | **0** | 0 | 3 |
| **Khối đa diện & thể tích (443tr)** | **6797** | **520** | **0** | 33 | 419 |

Tài liệu thứ hai giữ được `⊥` **520 lần**, `=` **6797 lần** — tưởng là dùng
được. Nhưng `√` vẫn **0**, và đó **không** phải "mất một ký hiệu trang trí".

### Đối chiếu ảnh trang gốc với bản trích — trang 46

| Bài | **Bản gốc** (dựng ảnh từ PDF rồi đọc) | **Bản trích tự động** |
|---|---|---|
| Câu 3 | `AC = a√3` · `SB = a√5` | `3 AC a =` · `5 SB a =` |
| Câu 4 | `SA = 2√3a` | `2 3 SA a =` |
| **Câu 5** | **`AC = 2a`** | **`2 AC a =`** |
| Câu 7 | `AB = 3a` · `AD = 2a` · `SB = 5a` | `3 AB a =` · `2 AD a =` · `5 SB a =` |

> **`AC = a√3` và `AC = 2a` trích ra thành CÙNG MỘT DẠNG `<số> AC a =`.**
> Dấu căn biến mất, và con số vốn nằm **dưới** dấu căn bị dồn ra **trước** tên
> đối tượng — chỗ mà một hệ số nhân cũng nằm.

### Vì sao đây là rào nặng nhất trong năm rào

Bốn rào trước làm **mất bài**. Rào này làm **nhận nhầm bài**:

`a√3` là dữ kiện **ngoài ranh giới năng lực** (`CAPABILITY_BOUNDARY §2.2`);
`2a` thì **trong**. Bản trích khiến cả hai trông như nhau, và cái trông giống
hơn là cái **hữu tỉ**. Nên bộ lọc năng lực sẽ **nhận** một bài ngoài phủ, nó
vào tập đã niêm phong, hệ trượt nó, và cái trượt ấy vào luận văn thành *"mô
hình không tính được thể tích"*.

Đó **đúng là** lớp sai lệch mà Phase 7A.1 đã phải đi sửa một lần, và lần này
nó vào từ cửa dữ liệu chứ không từ cửa bộ đo.

⇒ **Không có ngoại lệ cho tài liệu "giữ ký hiệu tốt".** `√` là ký hiệu quyết
định tư cách; mất nó là mất đúng thứ cần nhất.

### Điều này KHÔNG nói

Nó **không** nói tài liệu vô dụng — vật liệu có thật và đủ. Trang 46 của
*Khối đa diện & thể tích* có **Câu 7** với `AB = 3a`, `AD = 2a`, `SB = 5a`:
dữ kiện **hữu tỉ hoàn toàn**, một ứng viên **A14 tốt**. Chỉ là muốn biết điều
đó thì phải **nhìn trang gốc**, và người nhìn phải là người ký `NGƯỜI CHÉP`.

---

## 1. Hạn chế của cách thu thập này — quan trọng hơn con số

Công cụ đọc web trả nội dung **đã đi qua một mô hình tóm tắt**. Nghĩa là
`problem_text` thu được là bản **chép LẠI**, không phải bản **chép NGUYÊN VĂN**
— trong khi `HOLDOUT_PROTOCOL` đòi nguyên văn, và một chữ sai trong đề hình học
làm bài toán thành **bài khác** (đổi "trung điểm" thành "điểm", đổi "(SBC)"
thành "(SBD)" là đổi hẳn đáp án).

Không lệnh nào bắt được lỗi ấy: đề vẫn đọc trôi chảy, vẫn giải được, vẫn ra một
số. Nó chỉ lộ ra khi có người **mở url đối chiếu từng chữ**.

Nên mỗi bài thu bằng cách này mang `can_kiem_tay: true`, và `kiem_pool` **từ
chối niêm phong** khi còn cờ ấy:

```
POOL KHÔNG HỢP LỆ — 1 lỗi:
  · hp_a11_001: can_kiem_tay còn true — chưa ai đối chiếu problem_text với
    nguồn. Niêm phong một đề chép sai là niêm phong một bài toán KHÁC.
```

Trả nợ = mở url, đọc, sửa nếu lệch, **rồi mới** xoá cờ. Xoá cờ mà không đối
chiếu là biến một cổng thành một ô trống.

---

## 2. Sản lượng theo loại nguồn — đo được, không phỏng đoán

| Loại nguồn | Ví dụ | Đọc được? | Sản lượng |
|---|---|---|---|
| **Bài blog về MỘT câu thi chính thức** | [mathvn.com — Câu 6 mã đề 0103, TN THPT 2026](https://www.mathvn.com/2026/06/tinh-khoang-cach-tu-iem-en-mat-phang.html) | ✅ đề + đáp án + lời giải, dạng văn bản | **1 bài/trang** |
| **Chuyên đề tổng hợp** | [toanmath.com — quan hệ vuông góc](https://toanmath.com/2025/08/de-kiem-tra-theo-bai-hoc-chu-de-quan-he-vuong-goc-trong-khong-gian.html) | ❌ **chỉ link tải PDF** (tài liệu 305 trang) | 0 |
| **Lời giải cả đề thi chính thức** | [mathvn.com — lời giải chi tiết TN THPT 2026](https://www.mathvn.com/2026/06/loi-giai-chi-tiet-e-thi-chinh-thuc-tot.html) | ❌ lời giải nằm trong **14 ảnh** | 0 |
| **Trang tổng hợp bài tập** | [vietjack.me — 50 bài khoảng cách](https://vietjack.me/cac-bai-toan-ve-khoang-cach-trong-khong-gian-va-cach-giai-toan-lop-12-44875.html) | ❌ lỗi chứng chỉ TLS | 0 |

**Kết luận vận hành:** loại nguồn **duy nhất** thu được bằng công cụ đọc web là
*bài viết riêng cho từng câu*. Muốn 40 bài thì cần ~40 trang như thế — và chúng
tồn tại, nhưng phải tìm từng câu một.

**Đường nhanh hơn nhiều, cần người:** tải PDF chuyên đề (toanmath có tài liệu
217–704 trang, kèm đáp án và lời giải chi tiết) rồi chép đề vào pool. Một tài
liệu đủ cho hàng chục ô, và **chép từ PDF là chép nguyên văn thật** — không qua
mô hình tóm tắt, nên `can_kiem_tay` hạ được ngay lúc chép.

---

## 3. Bài đã thu — và bị LOẠI

### ❌ `hp_a11_001` — thu ở lượt 1, loại ở lượt 2

| | |
|---|---|
| Nguồn | **Đề thi chính thức TN THPT 2026**, mã đề 0103, Câu 6 Phần III (thi 11/06/2026) |
| url | https://www.mathvn.com/2026/06/tinh-khoang-cach-tu-iem-en-mat-phang.html |
| Đáp án nguồn | **7,35** (đề yêu cầu làm tròn hàng phần trăm) |
| Ô dự kiến | A11 |
| **Lý do loại** | **đáp án VÔ TỈ** — hệ không phục vụ được |

Tính lại độc lập: `A(0,0,0) B(6,0,0) D(0,6,0) M(0,0,6) P(6,6,6)`, `E(3,0,0)`;
mặt `(MED)`: `x/3 + y/6 + z/6 = 1` ⇒ `2x + y + z − 6 = 0`;
`d(P) = |12+6+6−6|/√6 = 18/√6 = 3√6 ≈ 7,348…` → làm tròn **7,35**, **khớp đáp án
nguồn**. Nhưng `d² = 54` và `√54` không hữu tỉ ⇒ `_do` ném
`GEOMETRY_IRRATIONAL_RESULT`.

**Bản trước của pool khai `oracle_result: {distance: "54"}` — SAI QUY ƯỚC.**
`_do` trả **khoảng cách thật** cho `distance`, không trả bình phương. Lỗi ấy
chép theo `pool.template.json`, và khuôn ấy cũng dạy sai (`d² = 1/3`); cả hai
đã sửa cùng lượt này.

> **Đây là lý do bài phải bị loại chứ không phải sửa đơn vị:** đổi
> `oracle_result` sang `"54"` hay `"3√6"` đều vô nghĩa — hệ **không trả ra giá
> trị nào cả**, nó ném lỗi. Giữ bài trong A11 là dựng một ô **chắc chắn trượt**
> rồi ghi cái trượt ấy vào luận văn thành *"mô hình không làm được khoảng
> cách"*. Đúng loại sai lệch mà Phase 7A.1 đã phải đi sửa một lần.

Bài này dùng lại được **nếu** chọn đường ② ở §1b (mở một ô tầng B cho lớp vô
tỉ) — khi đó nó thành một ca *"từ chối trung thực"* khá tốt, vì hệ **nên** nói
thẳng là không biểu diễn chính xác được thay vì làm tròn.

---

## 4. Việc còn lại — cả 20 ô trống

Thứ tự đề nghị, **xếp lại theo rào §1b** (không còn theo độ sẵn có của nguồn):

1. **A14 (thể tích) · A09–A10 (góc)** — **dễ nhất**, và lý do là toán học chứ
   không phải may mắn: `volume` và `cos²/sin²` **luôn hữu tỉ** khi toạ độ hữu
   tỉ, nên không vướng rào vô tỉ. Chỉ cần tránh đề có **dữ kiện** vô tỉ
   (`SA = a√3`). ⚠️ A10 phải khai **sin²**, không phải cos².
2. **A03–A08 (song song · vuông góc)** — đáp án **true/false**, không cần
   `phep_chuyen`, không vướng vô tỉ. Chọn đề hỏi *chứng minh một quan hệ cụ
   thể*, đừng lấy trắc nghiệm bốn phương án. Vẫn phải tránh dữ kiện vô tỉ.
3. **A01 · A02 · A13** — giao tuyến, điểm thuộc mặt, thiết diện. Khó tìm dạng
   *"dựng rồi chỉ ra"*; phần lớn đề thi hỏi trắc nghiệm.
4. **A11 · A12 (khoảng cách)** — **KHÓ NHẤT, và có thể không lấp được**. Cần đề
   mà khoảng cách ra **hữu tỉ**, trong khi đề thi thật hầu như luôn ra căn.
   Chờ quyết định ①/② ở §1b trước khi mất công tìm.
5. **B01–B06** — sáu ô ngoài phủ, chấm bằng *từ chối trung thực*. Không cần đáp
   án ở đơn vị checker nên dễ nhất về mặt dữ liệu. **B03 — góc nhị diện có
   miền** là ô quan trọng nhất cả tập: nó kiểm hệ có lặng lẽ trả lời câu nhị
   diện bằng góc mặt–mặt hay không.

⚠️ **Không ép bài vào ô sai bản chất.** Ô thiếu bài ⇒ dừng, không rút bù — rút
bù là lặng lẽ đổi tập đo thành tập dễ hơn.

⚠️ **Đừng soạn A11/A12 trước khi có quyết định §1b.** Soạn 40 bài rồi mới phát
hiện phần lớn phải loại là mất công hai lần, và tệ hơn: người soạn sẽ bị cám dỗ
"chữa" đơn vị oracle cho vừa — đúng cái vừa xảy ra ở lượt này.

---

## 5. Bài bị loại — 2

| Bài | Ô dự kiến | Lý do |
|---|---|---|
| `hp_a11_001` | A11 | **đáp án vô tỉ** (`3√6`) ⇒ `GEOMETRY_IRRATIONAL_RESULT` — §3 |
| `hp_a14_cand_001` | A14 | **chứng minh CÔNG THỨC TỔNG QUÁT**, tham số ký hiệu `a, b, c` — không có tầng đại số ký hiệu (`CAPABILITY_BOUNDARY §2.5`) |

⚠️ Bài thứ hai đáng chú ý: nó **thu được nguyên văn** qua HTML thô (LaTeX còn
nguyên `\frac`, `\sqrt`), tức **kênh làm đúng việc của kênh**. Nó rớt ở cổng
**sau** — ranh giới năng lực. Hai cổng khác nhau, và việc chúng chặn ở hai chỗ
khác nhau là bằng chứng cả hai đang hoạt động.

Nguồn máy đọc được: `pool.json.__bai_bi_loai__`, khoá bởi
`test_bai_bi_loai_deu_co_LY_DO`. **Loại im lặng là một dạng chọn tập** — mỗi
lần loại phải ghi lý do và giữ url, để người sau kiểm được rằng bài bị loại vì
*nằm ngoài phủ*, không phải vì *hệ làm sai nó*.

---

## 5b. BÀN GIAO — dán đề vào, tôi làm phần còn lại

Sau 673 url, kênh tự động **cạn**. Nhưng phần người phải làm **nhỏ hơn nhiều**
so với lượt 3 tưởng: không phải *"gõ lại 40 đề rồi điền JSON"*, mà chỉ là **dán
đề tự luận dạng văn bản**. Mọi việc còn lại là máy làm được, và đã có cổng kiểm.

### Người làm

Chép đề từ **SGK Toán 11/12** hoặc **PDF chuyên đề tự luận** đang có, dán theo
khuôn dưới. Chép từ sách/PDF **bằng mắt** chính là bước xác minh nguyên văn mà
giao thức đòi — nên `problem_text_verified` hạ được ngay.

```
[A14] Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc
      với mặt phẳng đáy và SA = 3. Tính thể tích khối chóp S.ABCD.
      NGUỒN: SGK Toán 11 tập 1 KNTT, bài 7.x trang NN
      ĐÁP ÁN: 4
```

Ba dòng mỗi bài: **ô** · **đề nguyên văn** · **nguồn + đáp án**. Không cần JSON,
không cần biết `capability_tag` hay `answer_shape`.

⚠️ File lô phải mở đầu bằng **`NGƯỜI CHÉP: <tên> · <ngày> · <chép từ đâu>`**.
Không có dòng ấy thì `ingest_holdout_batch.py` **từ chối cả lô** — vì hành vi
chép của người **chính là** bước xác minh nguyên văn, và không ai khác cấp được
chứng nhận ấy.

### Máy làm phần còn lại — đã có đường nạp (Phase 7B.2)

```bash
python scripts/ingest_holdout_batch.py lo1.txt          # soi, không ghi
python scripts/ingest_holdout_batch.py lo1.txt --ghi    # ghi vào pool.json
```

Nó xếp ô · gán `capability_tag`/`answer_shape` từ `NANG_LUC` · dựng
`oracle_result` · chạy `check_capability_boundary`, và **cảnh báo** đúng năm lớp
đề không hợp luật (trắc nghiệm · căn thức · tham chiếu hình vẽ · mặt cong ·
Oxyz cho sẵn) mà **không tự loại** — phán quyết cuối là của người.

Chạy thử đầu-cuối với lô mẫu 2 bài (A14 + A09): cả hai qua cổng, đúng thẻ, đúng
`oracle_result`. Đường nạp **sẵn sàng**; chỉ còn thiếu đề thật.

### Ưu tiên, theo tỉ lệ loại thấp nhất

| Thứ tự | Ô | Vì sao dễ |
|---|---|---|
| 1 | **A14** thể tích | `volume` **luôn hữu tỉ** — không vướng rào vô tỉ |
| 2 | **A09 · A10** góc | `cos²`/`sin²` **luôn hữu tỉ**. ⚠️ A10 khai **sin²** |
| 3 | **A01–A08 · A13** quan hệ | đáp án **true/false**, không cần `phep_chuyen` |
| 4 | **A11 · A12** khoảng cách | **khó nhất** — cần `d` hữu tỉ; chờ quyết định ①/② |
| 5 | **B01–B06** ngoài phủ | không cần đáp án, chỉ cần đúng loại |

⚠️ Với **mọi** ô: tránh đề có **tỉ số dữ kiện vô tỉ** (`đáy cạnh a, SA = a√3`) —
lớp này phổ biến trong đề thi và nằm ngoài ranh giới **kể cả ở A14**.

---

## 6. Lượt sau nên làm gì

1. **Chốt ①/② ở §1b** — người duyệt. Đường găng, không phải việc thu thập.
2. **Người chép đề.** Không kênh tự động nào cho nguyên văn (§1c). Cách rẻ nhất
   đã biết: mở PDF chuyên đề bằng trình đọc, **nhìn** và gõ lại đề, giữ đủ
   `=`, `⊥`, `√`, `∈`, `∥`. Mỗi bài vài phút; 40 bài là việc một buổi.
3. Bắt đầu từ **A14 · A09 · A10** — ba ô **không vướng rào vô tỉ**
   (`volume` và `cos²/sin²` luôn hữu tỉ), nên tỉ lệ loại thấp nhất.
4. Sau **mỗi lô**: `seal_geometry_holdout.py --seed 0 --chi-kiem-pool` +
   `holdout_coverage_matrix.py --md …`. `check_capability_boundary()` chạy sẵn
   trong `kiem_pool` và bắt: thẻ lệch ô · `answer_shape` ngoài tập đóng · oracle
   dạng căn thức · oracle thập phân · thiếu `domain_condition` · chưa đối chiếu
   nguyên văn.

> Bản đã tải nằm ở scratchpad của phiên, **không** commit: nó là tài liệu có
> bản quyền và không phải bằng chứng của lượt đo. Tải lại bằng url ở §2.

---

## 7. Rà nguồn cho **A11 · A12** (2026-08-28) — và vì sao khe hở là CẤU TRÚC

Lượt này chỉ rà đúng hai ô còn `SOURCE_GAP`. Ghi lại **cái đã loại**, để lượt
sau không tìm lại chính chúng.

### 7a. Đã kiểm, đã loại

| Nguồn | Cỡ | Loại vì |
|---|--:|---|
| *Chuyên đề khoảng cách từ điểm đến mặt phẳng* — Trần Mạnh Tường ([toanmath](https://toanmath.com/2020/08/chuyen-de-khoang-cach-tu-diem-den-mat-phang-tran-manh-tuong.html)) | 15 tr | **15 câu trắc nghiệm** — 7B chỉ nhận tự luận |
| *Bài toán khoảng cách trong không gian* ([toanmath](https://toanmath.com/2022/07/bai-toan-khoang-cach-trong-khong-gian.html)) | 63 tr | **trắc nghiệm tự luyện** |
| Slaught & Lennes, *Solid Geometry with Problems and Applications* ([Gutenberg 29807](https://www.gutenberg.org/files/29807/29807-pdf.pdf)) | 242 tr | tải về, **quét toàn văn**: chỉ **9 trang** nhắc *"distance from … plane/line"*, và không trang nào là bài A11/A12 — chúng là **quỹ tích**, **hình nón**, **hình cầu**, **chóp cụt**. Mặt cong ⇒ ngoài ranh giới |

Kho sàng của các wave trước (`trong_ranh_gioi.json` 8 mục, `screened.json` 26
mục) cũng **không có mục A11/A12 nào**, và hầu hết là trắc nghiệm.

### 7b. Vì sao — đây KHÔNG phải thất bại tìm kiếm

Trong cấu hình chuẩn của SGK (`SA ⊥ (ABCD)`, `AB ⊥ BC`), khoảng cách A11 rơi vào
đúng một công thức:

```
BC ⊥ AB và BC ⊥ SA  ⇒  BC ⊥ (SAB)  ⇒  (SBC) ⊥ (SAB), giao tuyến SB
d(A,(SBC)) = d(A, SB) = SA·AB / √(SA² + AB²)
```

⇒ **hữu tỉ ⟺ `(SA, AB)` là một cặp cạnh góc vuông Pythagore.** Và A12 (điểm →
đường) rơi vào **cùng** công thức ấy.

Cặp Pythagore đầu tiên: `3–4` (→ `12/5`) · `6–8` (→ `24/5`) · `5–12` (→ `60/13`)
· `8–15` (→ `120/17`) · `9–12` (→ `36/5`).

Nhưng SGK gần như luôn đặt `SA = a`, `SA = a√2`, `SA = a√3`, đáy hình vuông cạnh
`a` — mọi lựa chọn ấy cho `d` **vô tỉ**. Ví dụ điển hình gặp trong lượt rà:
`ABCD` vuông cạnh `a`, `SA = a√3` ⇒ `d = a√3/2`.

> **Khe hở A11/A12 là tính chất của TỔNG THỂ ĐỀ, không phải của lượt tìm.**
> Lớp bài hữu tỉ tồn tại và mô tả được bằng một câu, nhưng nó **hiếm trong tài
> liệu phổ thông** vì tác giả chọn số cho đẹp hình, không chọn cho đẹp `d`.

### 7c. Còn lại một đầu mối chưa kiểm

Prasolov & Sharygin, *Problems in Plane and Solid Geometry, v.2 — Solid
Geometry*: **560 bài kèm lời giải đầy đủ**, hình học **tổng hợp** (không toạ
độ). Chưa tải được ở lượt này. Đây là chỗ đáng thử tiếp theo, và nếu dùng thì
rơi vào **MODE A/B** của §5 (tiếng Anh ⇒ hoặc người dịch trước khi seal, hoặc
đánh dấu `external_challenge` và **không** gộp vào chỉ số chính).

⚠️ Tài liệu A-Level / IB **không** lấp được A11/A12: chương trình ấy dạy khoảng
cách 3D bằng **vectơ và toạ độ cho sẵn**, mà đó đúng là thứ ô **B04** loại khỏi
tầng A (*"Oxyz cho sẵn toạ độ ⇒ mô hình không phải tự đặt hệ trục"*). Tìm ở đó
sẽ ra bài cho B04, không ra bài cho A11.

### 7d. Rà Sharygin / Prasolov (2026-08-28, lượt hai) — `SOURCE_GAP_CONFIRMED`

Tải **toàn văn** Sharygin, *Problems in Solid Geometry* (MIR 1986, 340 bài,
[archive.org](https://archive.org/details/sharyginproblemsinsolidgeometry)) —
bản `djvu.txt` là **text thật**, không phải ảnh công thức, nên quét được máy.

```
338 khối đề tách được  ·  34 đề có chữ "distance"  ·  0 đề dùng được cho A11/A12
```

Từng bài, theo bộ lọc A–D:

| # | Đề | Loại vì |
|---|---|---|
| 7 · 22 · 49 · 192 | khoảng cách giữa **hai đường CHÉO NHAU** | **thuộc ô B01**, không phải A11/A12 |
| 51 | *"distance from the vertex to the centre of gravity"* | điểm → **điểm**, không phải điểm → mặt/đường |
| 80 | hộp `2a·a·a` nhưng có **tứ diện đều** MNPQ | `REJECT_IRRATIONAL` (√3) · và hỏi khoảng cách hai trung điểm |
| 105 | P cách N là `2`, cách cạnh MN là `1` | `REJECT_IRRATIONAL` — cạnh thứ ba `√3` |
| 158 · 212 · 236 | hỏi **thể tích** / **diện tích bóng** / chứng minh | không phải bài khoảng cách |

Prasolov & Sharygin v.2 (560 bài) **không tải được**: archive.org chỉ có v.1
(*Plane Geometry*), mccme.ru không còn bản tiếng Anh của tập rắn.

#### Vì sao cả ba GENRE đều trượt — mỗi genre trượt một kiểu

| Genre | Có bài khoảng cách không | Rơi vào đâu |
|---|---|---|
| Sách chuyên đề VN (15tr · 63tr) | **có, đúng loại** | ⛔ **trắc nghiệm** — 7B chỉ nhận tự luận |
| Sách olympiad (Sharygin, Prasolov) | có | ⛔ *"distance"* ở đây gần như luôn là **hai đường chéo nhau** ⇒ **ô B01**, ngoài phủ tầng A |
| A-Level / IB | có | ⇒ dạy bằng **vectơ + toạ độ cho sẵn** ⇒ **ô B04** |
| Sách tổng hợp cổ điển (Slaught & Lennes) | rất ít | ⛔ quỹ tích · nón · cầu · chóp cụt |

> **A11/A12 nằm ở giao của ba điều kiện hẹp**: thể loại **bài tập luyện của
> trường** (không phải olympiad) · dạng **tự luận** (không phải trắc nghiệm) ·
> và số liệu **Pythagore** (không phải `a`, `a√2`, `a√3`). Ba cái ấy hiếm khi
> gặp nhau, và đó là toàn bộ lý do hai ô này trống.

**Chỗ đáng thử tiếp**: phần **tự luận** của đề thi VN — câu cuối đề thi học kỳ,
đề HSG tỉnh, đề ôn thi tốt nghiệp phần tự luận — vì phần trắc nghiệm là chỗ
7B loại, còn phần tự luận thì cùng một tài liệu vẫn có. Lọc bằng chữ ký
Pythagore đã in sẵn trong khối A11/A12 của gói chép tay.

### 7e. Lượt tìm CUỐI cho A11/A12 — nguồn TỰ LUẬN tiếng Việt (2026-08-28)

Rà đúng thể loại còn lại: bài tự luận tiếng Việt kèm lời giải.

| Nguồn | Kết quả |
|---|---|
| VietJack — *Khoảng cách lớp 11* (KNTT), **Ví dụ 2** | ✅ **A11 PASS** — xem dưới |
| VietJack — *Khoảng cách từ một điểm tới một đường thẳng* | ⛔ mọi bài ra **căn**: `2a√6/3` · `a√3/2` · `√22` `√55` `√33` `√66` |
| SGK Toán 11 KNTT — Bài 26, bài 7.22–7.27 | ⛔ toàn `a` ký hiệu + tam giác **đều** / lập phương ⇒ `√6/3·a`, `√3/2·a` |
| SGK Toán 12 CTST — *"thiết lập hệ trục Oxyz như Hình 19"* | ⛔ `REJECT_OXYZ` — và `AB=2a, SA=3a` ⇒ `d` có `√13` |
| edusmart.vn — chuyên đề dạng 2 | ⛔ `REJECT_MISSING_SOURCE` — trang không có nội dung bài |

#### ✅ A11 — ứng viên DUY NHẤT có đáp án hữu tỉ

```
Nguồn   : VietJack · Khoảng cách lớp 11 (Lý thuyết Toán 11 Kết nối tri thức)
Vị trí  : Ví dụ 2
Dữ kiện : (SAB) ⊥ đáy · △SAB vuông tại S · AB = a · SA = 3a/5
Đáp án  : d(S,(ABC)) = 12a/25        ⇒ gán a = 1 ⇒ ĐÁP ÁN 12/25
```

Kiểm hữu tỉ, bốn bước:

| | Kiểm | Kết quả |
|---|---|---|
| **A** | đặt được vào toạ độ hữu tỉ? | `SB = √(a² − 9a²/25) = 4a/5` — bộ ba **3-4-5 thu nhỏ `a/5`**. `A(0,0,0)` `B(a,0,0)` `S(9a/25, 0, 12a/25)` ✅ |
| **B** | pháp tuyến hữu tỉ? | mặt đáy `z = 0`, pháp tuyến `(0,0,1)` ✅ |
| **C** | chuẩn vectơ hữu tỉ? | `‖(0,0,1)‖ = 1` ✅ |
| **D** | `d` cuối hữu tỉ? | `12a/25` ✅ |

⚠️ **Hai rủi ro người xác minh phải tự kiểm khi mở nguồn** — ghi ra vì cả hai đều
im lặng:

1. Đề đặt tên `C` nhưng **không ràng buộc vị trí `C`**. `d(S,(ABC))` không phụ
   thuộc `C`, nhưng hệ vẫn phải đặt `C` ở đâu đó để dựng cảnh. Có thể thành một
   phép thử **khó hơn** (mô hình phải nhận ra `C` tự do), cũng có thể vấp cổng
   `input-sufficiency`. Không giấu.
2. Bản tóm tắt ghi công thức là `SA·AB/SB`; **đúng** phải là `SA·SB/AB`. Đáp án
   `12a/25` thì đúng. ⇒ **đọc lời giải gốc**, đừng tin bản tóm tắt — kể cả bản
   này.

Đây là **trang dạy học**, không phải SGK gốc. Truy xuất được và có lời giải nên
đủ điều kiện 2–3, nhưng nếu tra được đúng bài trong SGK thì tốt hơn.

#### ⛔ A12 — `SOURCE_GAP_CONFIRMED`

Không tìm được bài nào. Lý do có cấu trúc, và **khác** lý do của A11:

```
A11 (điểm→mặt) : d = SA·SB/AB          — MỘT lần Pythagore là đủ
A12 (điểm→đường): d = √(SA² + h²)      — cần Pythagore LẦN HAI khớp tiếp
```

`d(A, BC)` trong không gian gần như luôn ra `√(tổng bình phương)`, nên muốn hữu
tỉ thì phải có **hai** trùng hợp Pythagore lồng nhau. Ví dụ đo được ở lượt này:
`SA=3a, SB=a, SC=2a` đôi một vuông góc ⇒ `BC = a√5` ngay từ bước đầu.

⇒ **Ngừng thu thập nguồn cho A12.** Ba lựa chọn thiết kế đánh giá đã nêu trong
báo cáo lượt này; quyết định thuộc người dùng.

### 7f. Chốt A11, và vì sao A12 bị chặn bởi GIAO THỨC chứ không bởi nguồn

#### A11 — `A11_VALID`, sau khi giải quyết nghi vấn "điểm C tự do"

Nghi vấn nêu ở §7e: đề đặt tên `C` nhưng không ràng buộc vị trí. Đã tra thẳng
mã, không suy đoán:

| Kiểm | Kết quả |
|---|---|
| `construct_plane` dựng được kiểu nào? | **chỉ qua BA ĐIỂM đã có tên** — không có dạng *"mặt qua đường thẳng, vuông góc mặt khác"* |
| Cổng `input_requirements` có mục hình học? | **KHÔNG** — bảng ấy chỉ phục vụ miền Tin học cũ |
| `request_contract` có đòi mọi điểm bị ràng buộc? | **KHÔNG** |
| Ca DEV đặt điểm tự do chưa? | **có, mọi ca** — `free_objects: ['A','B','C','D','S']` |

⇒ Đặt `C` tự do là **quyền dựng hình mà hệ vốn đã dùng**, không phải bịa dữ
kiện. Và `d` **bất biến** theo `C`: `(SAB) ⊥ (ABC)` giao tuyến `AB`, nên
`d(S,(ABC)) = d(S,AB)` — chỉ phụ thuộc `A`, `B`, `S`.

Kiểm nốt tính nhất quán của phép đặt: `A(0,0,0)` · `B(a,0,0)` · `C` bất kỳ
trong `z=0` · `S(9a/25, 0, 12a/25)` ⇒ `(SAB)` là `y=0`, `(ABC)` là `z=0`, hai
mặt **vuông góc** ✅. Ràng buộc của đề thoả, và phép đặt là duy nhất sai khác
một phép dời hình.

**Đa dạng cấu trúc**: khác DEV trên **ba** trục — đáy **tam giác** (DEV toàn
hình vuông) · **mặt bên** ⊥ đáy (DEV toàn **cạnh bên** ⊥ đáy) · mặt đáy suy từ
một **quan hệ vuông góc** chứ không từ một đa giác có tên.

#### A12 — `A12_BLOCKED_BY_PROTOCOL`

Câu hỏi: giao thức có cho dùng bài **do người độc lập/GVHD biên soạn** không?

- **Nguyên tắc thì cho.** `HOLDOUT_PROTOCOL §1` nói điểm mạnh *"không nằm ở chỗ
  tôi chưa nhìn — mà ở chỗ **tôi không viết được ra chúng, và không sửa được
  đáp án**"*. Bài do GVHD soạn thoả đúng tính chất ấy.
- **Chữ thì không.** `§3①` viết: *"SOẠN POOL ≥40 bài, phủ ĐỦ 20/20 ô, **trích
  từ nguồn công khai**"*. Bài GVHD soạn **không phải nguồn công khai**.

⇒ Không tự nới. Muốn dùng đường này thì phải **sửa `§3①` TRƯỚC khi seal** và
khai là sai lệch tiền đăng ký — đúng lệ đã làm với `obligation_match`. Quyết
định thuộc người dùng; tôi không soạn `A12_HUMAN_AUTHORING_REQUEST` khi giao
thức hiện hành chưa cho.

### 7g. ⛔ TRÍCH TEXT TỪ PDF NUỐT SẠCH DẤU CĂN — hỏng theo hướng NHẬN NHẦM

Đo trên *Chuyên đề QHVG trong không gian Toán 11* (KNTTVCS, 704 trang), phần
KHOẢNG CÁCH tự luận + lời giải (tr 294–334):

```
ký tự '⊥' trong text trích : 204
ký tự '∆'                  :  58
ký tự '√'                  :   0     ← MẤT SẠCH
```

Đối chiếu **ảnh trang** với **text trích**, cùng một trang:

| Bài | Ảnh trang (SỰ THẬT) | Text trích | Máy sẽ kết luận |
|---|---|---|---|
| Câu 6 | `BC = a√2` | `BC = a 2` | `2a` — **hữu tỉ** ❌ |
| Câu 10 | `a√6` | `6 a` | `6a` — **hữu tỉ** ❌ |
| Câu 12 · 13 | `SA = a√3` | `3 SA a =` | `3a` — **hữu tỉ** ❌ |
| Câu 2 (đáp án) | `a√3/2` | `3 . 2 a` | `3a/2` — **hữu tỉ** ❌ |

> **Lọc tính hữu tỉ bằng text trích PDF là SAI, và sai theo đúng hướng nguy
> hiểm nhất: NHẬN NHẦM.** Mọi bài vô tỉ đều hiện ra như bài hữu tỉ. Bốn ca độc
> lập ở trên đủ để đóng cửa hướng này.
>
> Cách duy nhất đã chứng minh dùng được: **dựng ảnh trang rồi đọc**. Đó cũng là
> cách đã dùng cho hai ứng viên A14 ở tr 80–83.

Ghi chú: `⊥` sống sót còn `√` thì không — nên một quét *"đề có nhắc vuông góc
không"* vẫn tin được, còn quét *"đáp án có căn không"* thì không.

### 7h. BẢN ĐỒ NGUỒN — mục TỰ LUẬN có lời giải, tra bằng mục lục PDF

Tài liệu 704 trang có **mục lục máy đọc được**, tách rõ `TULUAN` khỏi `TN` và
`DE` khỏi `HDG`. Đây là siêu dữ liệu **cấu trúc**, không phải công thức, nên
tin được (khác §7g).

| Mục | Đề (tr) | Lời giải (tr) | Ô |
|---|--:|--:|---|
| B22.1 HAI ĐƯỜNG THẲNG VUÔNG GÓC | 1–3 | 4–15 | **A06** |
| B23.1 ĐƯỜNG THẲNG ⊥ MẶT PHẲNG | 44–48 | 49–64 | **A07** |
| B24.1 PHÉP CHIẾU ⊥ · GÓC ĐT–MP | 103–108 | 109–140 | **A10** · **B06** |
| B25.1 HAI MẶT PHẲNG VUÔNG GÓC | 190–201 | 202–249 | **A08** |
| B26.1 KHOẢNG CÁCH | 294–301 | 302–334 | **A11** · B01 · B02 |
| B27.1 THỂ TÍCH P1 · P2 | 435–457 · 509–511 | 458–508 · 512–539 | **A14** |

⇒ **10 ô** có nguồn tự luận kèm lời giải trong MỘT tài liệu. Còn thiếu nguồn:
A01–A05 · A09 · A13 (đều thuộc chương **quan hệ song song**, không nằm trong
tài liệu chương 7 này) · B03 · B04 · B05.

⚠️ **A12 KHÔNG có trong bản đồ này.** Quét toàn bộ phần tự luận của cả 7 mục:
**0 bài** hỏi khoảng cách từ điểm đến một **đường thẳng**. Chương trình chương 7
hiểu *"khoảng cách"* là điểm→**mặt phẳng** và **hai đường chéo nhau**, không
phải điểm→đường. Khớp với kết luận §7f.

#### ✅ A11 — ứng viên THỨ HAI, đã đọc ảnh trang

```
Nguồn   : Chuyên đề QHVG Toán 11 (KNTTVCS, 704tr) · B26.1 KHOẢNG CÁCH
          PHẦN TỰ LUẬN · Câu 7 · trang PDF 298 ("Page 57")
Dữ kiện : SA ⊥ (ABC) · △ABC vuông tại B · BC = 2a
Đáp án  : d(C,(SAB)) = CB = 2a   ⇒ gán a = 1 ⇒ ĐÁP ÁN 2
```

`BC ⊥ AB` (vuông tại B) và `BC ⊥ SA` ⇒ `BC ⊥ (SAB)` ⇒ khoảng cách chính là
`CB`. **Không phép tính nào sinh căn** — an toàn hơn ứng viên VietJack. `AB` và
`SA` không được cho, và đáp án không phụ thuộc chúng.
