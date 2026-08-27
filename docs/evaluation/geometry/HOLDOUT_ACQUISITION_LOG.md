# NHẬT KÝ THU THẬP ĐỀ HELD-OUT — nguồn nào lấy được, nguồn nào không

> Lượt thu thập 2026-08-27. **0 API call của hệ** (chỉ đọc web).
>
> Ghi lại để lượt sau **không dò lại từ đầu**: sản lượng thật của từng loại
> nguồn, và một hạn chế của cách thu thập mà không lệnh nào phát hiện hộ.

---

## 0. Kết quả một câu

**0 bài hợp lệ. 1 bài đã thu rồi bị LOẠI.** Hai rào, và rào thứ hai quan trọng
hơn nhiều:

1. **Định dạng** — đề đầy đủ nằm trong PDF hoặc ảnh; thứ đọc được dạng văn bản
   thì mỗi trang một bài (lượt 1).
2. **Miền số của kernel** — phần lớn đề thi hình học Việt Nam có **dữ kiện hoặc
   đáp án vô tỉ** (`a√3`, `a√2/2`), mà kernel dựng trên `Fraction` (lượt 2, §1b).

Rào thứ hai không phải chuyện thu thập chậm — nó **thu hẹp tập đề đủ tư cách**,
và phải xử lý trước khi soạn tiếp 40 bài rồi mới phát hiện phần lớn phải loại.

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

### Nhưng sản lượng thì cạn — đo được

```
3883 url (sitemap mathvn)
  → 60  ứng viên (lọc từ khoá hình học không gian)
  → 11  có khối đề tách được
  →  2  SẠCH (qua cả ba cổng)
  →  0  trong ranh giới năng lực
```

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

## 5. Bài bị loại — 1

| Bài | Ô dự kiến | Lý do |
|---|---|---|
| `hp_a11_001` | A11 | **đáp án vô tỉ** (`3√6`) ⇒ `GEOMETRY_IRRATIONAL_RESULT` — §3 |

Nguồn máy đọc được: `pool.json.__bai_bi_loai__`, khoá bởi
`test_bai_bi_loai_deu_co_LY_DO`. **Loại im lặng là một dạng chọn tập** — mỗi
lần loại phải ghi lý do và giữ url, để người sau kiểm được rằng bài bị loại vì
*nằm ngoài phủ*, không phải vì *hệ làm sai nó*.

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
