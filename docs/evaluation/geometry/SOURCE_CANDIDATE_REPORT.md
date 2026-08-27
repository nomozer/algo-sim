# BÁO CÁO NGUỒN ỨNG VIÊN — tài liệu để NGƯỜI chép đề

> Tìm **nguồn**, không trích đề. Mọi link đã **tải thật và xác minh**:
> HTTP 200 · 4 byte đầu là `%PDF` · số trang đọc bằng PyMuPDF.
> **0 API call. Không ghi `pool.json`. Không tạo đề.**

```
FOUND_SOURCES:          8
LIKELY_BATCH_SIZE:      35   (ước lượng thận trọng, xem §3)
READY_FOR_MANUAL_COPY:  YES
```

---

## 1. Cách đo — vì sao tin được số ở đây

Với mỗi nguồn: tải PDF thật → mở bằng PyMuPDF → quét **từng trang**, đếm
trang có mốc bài **tự luận** (`Bài N. Cho hình chóp…`) và trang có **bốn
phương án** `A. B. C. D.`. Tải xong **xoá file** — không giữ 78 MB tài liệu
có bản quyền trong kho.

⚠️ Đây là đếm **TRANG**, không phải đếm **BÀI**, và mốc nhận dạng là chuỗi
ký tự nên có sai số. Nó đủ để **xếp hạng nguồn**, không đủ để hứa số bài.

⚠️ Số trang tự luận **chưa** trừ rào ranh giới năng lực. Đề Việt Nam dùng
`a√3`, `a√2` rất nhiều, và lớp ấy **ngoài phủ** — xem `CAPABILITY_BOUNDARY §2.2`.
Nên số bài dùng được sẽ **thấp hơn đáng kể** số trang tự luận.

---

## 2. Nguồn — xếp theo lượng nội dung tự luận

### 1. Chuyên đề quan hệ vuông góc trong không gian — Toán 11 KNTTVCS  · ⭐ **KHUYẾN NGHỊ**

```
source_name             : Chuyên đề quan hệ vuông góc trong không gian — Toán 11 KNTTVCS
url                     : https://toanmath.com/2023/08/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-knttvcs.html
file                    : https://toanmath.com/toanmath-pdf/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-knttvcs.pdf
chapter                 : các ô A06 A07 A08 A10 A11 A12
estimated_slots         : A06 A07 A08 A10 A11 A12
sample_problem_location : trang 2, 3, 5, 6
requires_human_copy     : true
```

- **704 trang** · 19.4 MB
- **203 trang tự luận** · 403 trang trắc nghiệm

### 2. Quan hệ vuông góc trong không gian — Toán 11 (Lê Minh Tâm)  · ⭐ **KHUYẾN NGHỊ**

```
source_name             : Quan hệ vuông góc trong không gian — Toán 11 (Lê Minh Tâm)
url                     : https://toanmath.com/2024/02/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-le-minh-tam.html
file                    : https://toanmath.com/toanmath-pdf/chuyen-de-quan-he-vuong-goc-trong-khong-gian-toan-11-le-minh-tam.pdf
chapter                 : các ô A06 A07 A08 A10 A11 A12
estimated_slots         : A06 A07 A08 A10 A11 A12
sample_problem_location : trang 5, 6, 17, 18
requires_human_copy     : true
```

- **217 trang** · 10.3 MB
- **117 trang tự luận** · 0 trang trắc nghiệm

- ✅ **KHÔNG có trang trắc nghiệm nào** — né trọn rào *lệch kiểu nhiệm vụ*.

### 3. Tài liệu chuyên đề khối đa diện và thể tích khối đa diện  · ⭐ **KHUYẾN NGHỊ**

```
source_name             : Tài liệu chuyên đề khối đa diện và thể tích khối đa diện
url                     : https://toanmath.com/2023/07/tai-lieu-chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.html
file                    : https://toanmath.com/toanmath-pdf/tai-lieu-chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.pdf
chapter                 : các ô A14
estimated_slots         : A14
sample_problem_location : trang 45, 46, 47, 48
requires_human_copy     : true
```

- **443 trang** · 14.1 MB
- **97 trang tự luận** · 289 trang trắc nghiệm

### 4. Chuyên đề quan hệ song song trong không gian — Toán 11 KNTTVCS  · ⭐ **KHUYẾN NGHỊ**

```
source_name             : Chuyên đề quan hệ song song trong không gian — Toán 11 KNTTVCS
url                     : https://toanmath.com/2023/07/chuyen-de-quan-he-song-song-trong-khong-gian-toan-11-knttvcs.html
file                    : https://toanmath.com/toanmath-pdf/chuyen-de-quan-he-song-song-trong-khong-gian-toan-11-knttvcs.pdf
chapter                 : các ô A01 A03 A04 A05 A13
estimated_slots         : A01 A03 A04 A05 A13
sample_problem_location : trang 3, 14, 15, 21
requires_human_copy     : true
```

- **389 trang** · 7.4 MB
- **35 trang tự luận** · 303 trang trắc nghiệm

### 5. Chuyên đề Toán 11 — chương quan hệ song song trong không gian  · ⭐ **KHUYẾN NGHỊ**

```
source_name             : Chuyên đề Toán 11 — chương quan hệ song song trong không gian
url                     : https://toanmath.com/2025/07/chuyen-de-toan-11-chuong-quan-he-song-song-trong-khong-gian.html
file                    : https://toanmath.com/toanmath-pdf/chuyen-de-toan-11-chuong-quan-he-song-song-trong-khong-gian.pdf
chapter                 : các ô A01 A03 A04 A05 A13
estimated_slots         : A01 A03 A04 A05 A13
sample_problem_location : trang 16, 17, 18, 19
requires_human_copy     : true
```

- **75 trang** · 2.7 MB
- **32 trang tự luận** · 0 trang trắc nghiệm

- ✅ **KHÔNG có trang trắc nghiệm nào** — né trọn rào *lệch kiểu nhiệm vụ*.

### 6. Bài tập quan hệ song song trong không gian (Võ Công Trường)  · ⚠️ yếu

```
source_name             : Bài tập quan hệ song song trong không gian (Võ Công Trường)
url                     : https://toanmath.com/2023/08/bai-tap-quan-he-song-song-trong-khong-gian-vo-cong-truong.html
file                    : https://toanmath.com/toanmath-pdf/bai-tap-quan-he-song-song-trong-khong-gian-vo-cong-truong.pdf
chapter                 : các ô A01 A03 A04 A05 A13
estimated_slots         : A01 A03 A04 A05 A13
sample_problem_location : trang 66, 71, 72
requires_human_copy     : true
```

- **73 trang** · 6.8 MB
- **3 trang tự luận** · 4 trang trắc nghiệm

- ⛔ Gần như toàn trắc nghiệm. **Không nên dùng** cho held-out.

### 7. Thể tích khối đa diện — 500 bài tập chọn lọc (Lê Minh Tâm)  · ⚠️ yếu

```
source_name             : Thể tích khối đa diện — 500 bài tập chọn lọc (Lê Minh Tâm)
url                     : https://toanmath.com/2023/08/500-bai-tap-chon-loc-the-tich-khoi-da-dien-le-minh-tam.html
file                    : https://toanmath.com/toanmath-pdf/500-bai-tap-chon-loc-the-tich-khoi-da-dien-le-minh-tam.pdf
chapter                 : các ô A14
estimated_slots         : A14
sample_problem_location : trang 264, 286
requires_human_copy     : true
```

- **326 trang** · 15.1 MB
- **2 trang tự luận** · 319 trang trắc nghiệm

- ⛔ Gần như toàn trắc nghiệm. **Không nên dùng** cho held-out.

### 8. Phân dạng bài tập Toán 11 — quan hệ vuông góc trong không gian  · ⚠️ yếu

```
source_name             : Phân dạng bài tập Toán 11 — quan hệ vuông góc trong không gian
url                     : https://toanmath.com/2024/01/phan-dang-bai-tap-toan-11-quan-he-vuong-goc-trong-khong-gian.html
file                    : https://toanmath.com/toanmath-pdf/phan-dang-bai-tap-toan-11-quan-he-vuong-goc-trong-khong-gian.pdf
chapter                 : các ô A06 A07 A08 A10
estimated_slots         : A06 A07 A08 A10
sample_problem_location : KHÔNG tìm thấy trang tự luận nào
requires_human_copy     : true
```

- **62 trang** · 1.7 MB
- **0 trang tự luận** · 60 trang trắc nghiệm

- ⛔ Gần như toàn trắc nghiệm. **Không nên dùng** cho held-out.

---

## 3. Ước lượng số bài lấy được

| Nguồn | Trang tự luận | Ước lượng bài dùng được |
|---|--:|--:|
| Chuyên đề quan hệ vuông góc trong không gian — Toán  | 203 | 10 |
| Quan hệ vuông góc trong không gian — Toán 11 (Lê Min | 117 | 10 |
| Tài liệu chuyên đề khối đa diện và thể tích khối đa  | 97 | 9 |
| Chuyên đề quan hệ song song trong không gian — Toán  | 35 | 3 |
| Chuyên đề Toán 11 — chương quan hệ song song trong k | 32 | 3 |
| **Tổng** | **484** | **35** |

Ước lượng cố ý **thận trọng**: chia 10 rồi kẹp vào `[3, 10]`, đúng khoảng
mà nhiệm vụ đặt ra cho mỗi nguồn. Con số thật phụ thuộc tỉ lệ đề có dữ kiện
vô tỉ — chỉ biết được khi người mở tài liệu ra đọc.

---

## 4. Thứ tự nên mở

| # | Nguồn | Vì sao trước |
|---|---|---|
| 1 | **Quan hệ vuông góc — Lê Minh Tâm (217tr)** | 117 trang tự luận, **0 trang trắc nghiệm**. Đã kiểm tay trang 20: *Bài 40, Bài 41* là đề tự luận thật |
| 2 | **Chuyên đề Toán 11 — quan hệ song song (75tr)** | 32 trang tự luận, **0 trắc nghiệm**, file nhỏ 2.7 MB — mở nhanh |
| 3 | **Khối đa diện & thể tích (443tr)** | nguồn **A14** tốt nhất: 97 trang tự luận, mẫu ngay trang 45–48 |
| 4 | Quan hệ vuông góc — KNTTVCS (704tr) | 203 trang tự luận nhưng lẫn 403 trang trắc nghiệm |
| 5 | Quan hệ song song — KNTTVCS (389tr) | 35 trang tự luận |

⚠️ **Không có nguồn nào cho ô B01–B06** (ngoài phủ: chéo nhau · nhị diện ·
Oxyz · mặt cong · vectơ). Sáu ô ấy cần tìm riêng, và chúng **dễ hơn** — chỉ
cần đúng loại, không cần đáp án.

⚠️ **Chưa tìm được SGK PDF chính thức.** Bộ GD-ĐT không phát hành bản PDF
công khai ổn định; các bản lưu hành trên mạng không tra ngược được về nguồn
chính thức, nên không đạt điều kiện `nguon.url` của giao thức.

---

## 5. Việc tiếp theo

1. Mở nguồn **#1** ở trang mẫu, chọn 3 bài **A14/A09/A10** có dữ kiện **hữu tỉ**.
2. Gõ vào [`batch_001.txt`](holdout/batch_001.txt) kèm dòng `NGƯỜI CHÉP:`.
3. `python scripts/ingest_holdout_batch.py …` (soi) rồi `--ghi`.

**`requires_human_copy: true` cho MỌI nguồn** — trích PDF tự động rơi ký hiệu
toán (đo được: `⊥` **0 lần** trong chính nguồn #1, 217 trang về quan hệ vuông
góc). Không có ngoại lệ.

