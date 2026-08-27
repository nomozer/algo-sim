# NHẬT KÝ THU THẬP ĐỀ HELD-OUT — nguồn nào lấy được, nguồn nào không

> Lượt thu thập 2026-08-27. **0 API call của hệ** (chỉ đọc web).
>
> Ghi lại để lượt sau **không dò lại từ đầu**: sản lượng thật của từng loại
> nguồn, và một hạn chế của cách thu thập mà không lệnh nào phát hiện hộ.

---

## 0. Kết quả một câu

**1 bài lấy được, 39 bài còn thiếu.** Không phải vì thiếu nguồn — đề thi công
khai của Việt Nam có rất nhiều — mà vì **định dạng**: thứ có đề đầy đủ thì nằm
trong PDF hoặc ảnh, thứ đọc được dạng văn bản thì mỗi trang một bài.

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

## 3. Bài đã thu — 1/40

### `hp_a11_001` · ô **A11** · họ `measurement` · `quantity`

| | |
|---|---|
| Nguồn | **Đề thi chính thức TN THPT 2026**, mã đề 0103, Câu 6 Phần III (thi 11/06/2026) |
| url | https://www.mathvn.com/2026/06/tinh-khoang-cach-tu-iem-en-mat-phang.html |
| Đáp án nguồn | **7,35** (đề yêu cầu làm tròn hàng phần trăm) |
| Đơn vị oracle | `d² = 54` |

**`phep_chuyen`, và vì sao bài này cần nó:** đáp án nguồn là số **đã làm tròn**,
không dùng thẳng làm oracle được. Tính lại độc lập: `A(0,0,0) B(6,0,0) D(0,6,0)
M(0,0,6) P(6,6,6)`, `E(3,0,0)`; mặt `(MED)`: `x/3 + y/6 + z/6 = 1` ⇒
`2x + y + z − 6 = 0`; `d(P) = |12+6+6−6|/√6 = 18/√6 = 3√6 ≈ 7,348…` → làm tròn
**7,35**, khớp đáp án nguồn. `3√6` vô tỉ ⇒ checker so `d² = 54`.

Phép tính này **đã được làm lại độc lập và khớp nguồn tới hàng phần trăm** — đó
là lý do tin được. Nhưng nó vẫn là *tôi tính*, và `phep_chuyen` phải hiện ra để
người khác kiểm lại; giấu nó đi thì *"oracle độc lập"* chỉ còn là lời khai.

⚠️ Bài này **vẫn mang `can_kiem_tay: true`** — phần chưa xác nhận là **văn bản
đề**, không phải phép tính.

---

## 4. Việc còn lại — 19 ô trống

```
A01 A02 A03 A04 A05 A06 A07 A08 A09 A10 A12 A13 A14 B01 B02 B03 B04 B05 B06
```

Thứ tự đề nghị, theo độ sẵn có của nguồn:

1. **A14 (thể tích) · A11–A12 (khoảng cách) · A09–A10 (góc)** — đề thi năm nào
   cũng có, và đáp án là một số nên `phep_chuyen` gọn.
2. **A03–A08 (song song · vuông góc)** — nhiều trong chuyên đề Toán 11. Đáp án
   là **true/false** nên không cần `phep_chuyen`, nhưng phải chọn đề hỏi *chứng
   minh một quan hệ cụ thể*, đừng lấy đề trắc nghiệm bốn phương án.
3. **A01 · A02 · A13** — giao tuyến, điểm thuộc mặt, thiết diện. Khó tìm dạng
   *"dựng rồi chỉ ra"*; phần lớn đề thi hỏi trắc nghiệm.
4. **B01–B06** — sáu ô **ngoài phủ**, chấm bằng *từ chối trung thực*. Dễ tìm
   nhất (chỉ cần đề đúng loại, **không** cần đáp án ở đơn vị checker) nhưng
   **B03 — góc nhị diện có miền** là ô quan trọng nhất cả tập: nó kiểm hệ có
   lặng lẽ trả lời câu nhị diện bằng góc mặt–mặt hay không.

⚠️ **Không ép bài vào ô sai bản chất.** Ô thiếu bài ⇒ dừng, không rút bù — rút
bù là lặng lẽ đổi tập đo thành tập dễ hơn.

---

## 5. Bài bị loại — chưa có

Chưa loại bài nào: mới có một bài đạt và nó vào thẳng ô A11. Khi loại, ghi vào
đây kèm **lý do**, đừng loại im lặng — loại im lặng là một dạng chọn tập.
