# BÁO CÁO ỨNG VIÊN HELD-OUT — quét nguồn web

> Sinh từ `harvest_holdout_candidates.py` + sàng theo luật nhận bài.
> **0 API call. KHÔNG ghi `pool.json`** — đây là danh sách để người duyệt.

```
FOUND_CANDIDATES:      22
ACCEPTABLE_CANDIDATES: 0
READY_FOR_INGEST:      NO
```

---

## 1. Nguồn đã quét

| Nguồn | URL quét | Có khối đề | SẠCH | Loại vì đề là ẢNH |
|---|--:|--:|--:|--:|
| mathvn — 2026 | — | 208 | 125 | 45 |
| mathvn — SGK 2024-26 | — | 9 | 4 | 0 |
| mathvn — 2024-2025 | — | 7 | 0 | 1 |
| **toanmath.com** | 34 sitemap | **0** | **0** | — |
| vted · hoc247 · diendantoanhoc | — | **0** | **0** | chặn fetch |
| loigiaihay · vietjack | — | **0** | **0** | ảnh / chặn |

**toanmath**: kiểm trực tiếp một trang chuyên đề — `Đề bài` **không có**,
`math-box` **không có**, chỉ **2 link `.pdf`** và **16 `<img>`**. Đây là
site phân phối **PDF**, không phải site đăng đề dạng văn bản.

**PDF chuyên đề**: đã tải thật và trích bằng hai thư viện độc lập — rơi
ký hiệu toán (`⊥` **0 lần** / 217 trang). Không đọc được nguyên văn ⇒
toàn bộ ứng viên từ PDF bị loại theo **luật 4 điều kiện 1**.

---

## 2. Ứng viên hình học không gian

| Kết quả sàng | Số |
|---|--:|
| trắc nghiệm 4 phương án | 19 |
| [đã phán trong pool: needs_manual_review] KHÔNG vướng ranh giới năng lực — dữ kiện HỮU TỈ hoàn toàn (đáy vuông cạnh 2, SA = 3), V = (1/3)·4·3 = 4 là phân số chính | 1 |
| [đã phán trong pool: rejected_capability_boundary] distance output irrational and unsupported by kernel — d(P,(MED)) = 3√6; d² = 54 và √54 không hữu tỉ, nên `geometry_exec | 1 |
| [đã phán trong pool: rejected_capability_boundary] CHỨNG MINH CÔNG THỨC TỔNG QUÁT, không phải bài cụ thể. Dữ kiện là tham số ký hiệu a, b, c và yêu cầu là chứng minh một đ | 1 |

**Tổng ứng viên: 22 · nhận được: 0**

---

## 3. Danh sách đầy đủ

| id | ô | đáp án | trạng thái | đề (rút gọn) |
|---|---|---|---|---|
| `cand_001` | A14 | trong đề | ⛔ trắc nghiệm 4 phương án | Một khối chóp có đường cao $h = 2a$ và diện tích đáy $B = a^2$ . Thể tích của khối chóp bằng A. \( \frac{2a^3}… |
| `cand_002` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 2. Cho tứ diện \(ABCD\). Gọi \(M, N\) lần lượt là trung điểm của \(AB, CD\) và \(G\) là trung điểm của \(M… |
| `cand_003` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 3. Cho hình chóp \(SABC\), có đáy \(ABC\) là tam giác vuông tại \(A\) và \(SA=SB=SC\). Gọi \(H\) là trung … |
| `cand_004` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Cho hình lập phương \(ABCD.A'B'C'D'\). Tìm mệnh đề sai? A. \( (\overrightarrow{AD}; \overrightarrow{A'B'}) = 9… |
| `cand_005` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Cho hình lập phương \( ABCD.A'B'C'D' \). Phát biểu nào sau đây là đúng? A. \( (ABCD) \perp (A'B'C'D') \). B. \… |
| `cand_006` | A14 | trong đề | ⛔ trắc nghiệm 4 phương án | Cho hình chóp $S.ABCD$ có đáy là hình vuông cạnh bằng $a,$ $SA \bot (ABCD), SA = a\sqrt3$. Thể tích khối chóp … |
| `cand_007` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 1. Xác định mặt phẳng song song với đường trung bình trong tứ diện Cho tứ diện \(ABCD\) có \(M, N\) lần lư… |
| `cand_008` | A14 | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 2. Thể tích khối chóp đều Cho hình chóp đều \(S.ABCD\) có cạnh đáy bằng \(a\sqrt{2}\), cạnh bên bằng \(2a\… |
| `cand_009` | A07 | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 3. Hình chóp và vuông góc với mặt phẳng Cho hình chóp \(S.ABCD\) có đáy là hình bình hành tâm \(O\), \(SA … |
| `cand_010` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 2 (Vectơ trong tứ diện): Cho tứ diện \(ABCD\). Gọi \(M, P\) là trung điểm của \(AB\) và \(CD\). Đặt \[ \ov… |
| `cand_011` | A04 | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 1 (Đường thẳng song song với mặt phẳng): Cho hình chóp \(S.ABCD\) có đáy \(ABCD\) là hình bình hành. Gọi \… |
| `cand_012` | A14 | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 2 (Thể tích khối lăng trụ): Cho khối lăng trụ có diện tích đáy \(S=20\) và chiều cao \(h=9\). Thể tích của… |
| `cand_013` | A07 | trong đề | ⛔ trắc nghiệm 4 phương án | Cho hình chóp \(S.ABCD\) có đáy \(ABCD\) là hình chữ nhật, đường thẳng \(SA\) vuông góc với mặt phẳng \((ABCD)… |
| `cand_014` | A11 | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 2. Khoảng cách từ điểm đến mặt phẳng trong hình chóp Cho hình chóp \(S.ABC\) có \(SA\) vuông góc với mặt p… |
| `cand_015` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 5 (Trọng tâm tứ diện): Cho tứ diện \(ABCD\) có trọng tâm \(G\) và \(M\) là một điểm bất kì. Phát biểu nào … |
| `cand_016` | A14 | trong đề | ⛔ [đã phán trong pool: needs_manual_review] KHÔNG vướng ranh giới năng lực — dữ kiện HỮU TỈ hoàn toàn (đáy vuông cạnh 2, SA = 3), V = (1/3)·4·3 = 4 là phân số chính | Cho hình chóp \(S.ABCD\) có đáy \(ABCD\) là hình vuông cạnh bằng \(2\), cạnh bên \(SA\) vuông góc với mặt phẳn… |
| `cand_017` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 4 (Vectơ trong hình hộp): Cho hình hộp \(ABCD.A'B'C'D'\) (tham khảo hình vẽ). Khẳng định nào sau đây đúng?… |
| `cand_018` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 2 (Quan hệ vuông góc trong hình chóp): Cho hình chóp \(S.ABCD\) có đáy \(ABCD\) là hình chữ nhật tâm \(I\)… |
| `cand_019` | A14 | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 3 (Thể tích khối chóp): Cho hình chóp \(S.ABCD\) có đáy \(ABCD\) là hình vuông, tam giác \(SAC\) vuông cân… |
| `cand_020` | — | trong đề | ⛔ trắc nghiệm 4 phương án | Câu 4 (Vectơ trong hình hộp chữ nhật): Cho hình hộp chữ nhật \(ABCD.A'B'C'D'\) có \(AB=2,\;BC=4,\;CC'=5\). Độ … |
| `cand_021` | A11 | trong đề | ⛔ [đã phán trong pool: rejected_capability_boundary] distance output irrational and unsupported by kernel — d(P,(MED)) = 3√6; d² = 54 và √54 không hữu tỉ, nên `geometry_exec | Câu 6 – Phần III – Mã đề 0103 – Đề thi chính thức tốt nghiệp THPT 2026, Bộ GD&ĐT) Cho hình lập phương \(ABCD.M… |
| `cand_022` | A14 | trong đề | ⛔ [đã phán trong pool: rejected_capability_boundary] CHỨNG MINH CÔNG THỨC TỔNG QUÁT, không phải bài cụ thể. Dữ kiện là tham số ký hiệu a, b, c và yêu cầu là chứng minh một đ | Cho tứ diện $ABCD$ có các cặp cạnh đối diện đôi một bằng nhau: $AB = CD = a$, $AC = BD = b$, $AD = BC = c$ (gọ… |

Nguồn từng ứng viên (url đầy đủ):

- `cand_001` — https://www.mathvn.com/2026/03/e-khao-sat-chat-luong-toan-12-lan-1-nam.html
- `cand_002` — https://www.mathvn.com/2026/03/e-thi-thu-mon-toan-thpt-2026-cum-truong.html
- `cand_003` — https://www.mathvn.com/2026/03/e-thi-thu-mon-toan-thpt-2026-cum-truong.html
- `cand_004` — https://www.mathvn.com/2026/03/e-thi-thu-tot-nghiep-thpt-2026-mon-toan_31.html
- `cand_005` — https://www.mathvn.com/2026/04/de-thi-thu-toan-nam-2026-co-dap-an-so-gd-cao-bang.html
- `cand_006` — https://www.mathvn.com/2026/04/e-mon-toan-thi-thu-2026-so-gd-ong-nai.html
- `cand_007` — https://www.mathvn.com/2026/04/so-hai-phong-e-mon-toan-khao-sat-ky-thi.html
- `cand_008` — https://www.mathvn.com/2026/04/so-son-la-e-mon-toan-thi-thu-tot-nghiep.html
- `cand_009` — https://www.mathvn.com/2026/04/so-son-la-e-mon-toan-thi-thu-tot-nghiep.html
- `cand_010` — https://www.mathvn.com/2026/05/cum-08-so-ca-mau-e-toan-thi-thu-tot.html
- `cand_011` — https://www.mathvn.com/2026/05/cum-truong-chuyen-phu-tho-e-kscl-lop-12.html
- `cand_012` — https://www.mathvn.com/2026/05/cum-truong-chuyen-phu-tho-e-kscl-lop-12.html
- `cand_013` — https://www.mathvn.com/2026/05/so-bac-ninh-2-e-thi-thu-tot-nghiep-thpt.html
- `cand_014` — https://www.mathvn.com/2026/05/so-gd-t-tuyen-quang-e-thi-thu-tot.html
- `cand_015` — https://www.mathvn.com/2026/05/so-gia-lai-e-thi-thu-tot-nghiep-mon.html
- `cand_016` — https://www.mathvn.com/2026/05/so-ha-tinh-l2-e-thi-thu-toan-co-loi.html
- `cand_017` — https://www.mathvn.com/2026/05/so-son-la-l3-e-thi-thu-tot-nghiep-thpt.html
- `cand_018` — https://www.mathvn.com/2026/05/so-vinh-long-e-thi-thu-tot-nghiep-mon.html
- `cand_019` — https://www.mathvn.com/2026/06/lien-truong-chuyen-nang-e-thi-thu-mon.html
- `cand_020` — https://www.mathvn.com/2026/06/lien-truong-chuyen-nang-e-thi-thu-mon.html
- `cand_021` — https://www.mathvn.com/2026/06/tinh-khoang-cach-tu-iem-en-mat-phang.html
- `cand_022` — https://www.mathvn.com/2026/08/cong-thuc-tinh-tich-tu-dien-co-cac-cap.html

---

## 4. Kết luận

**0/22 ứng viên nhận được.**

Không ghi `pool.json`. Ứng viên bị loại **không** phải lỗi hệ thống và
**không** phải lỗi mô hình — chúng là đề không hợp kiểu nhiệm vụ hoặc
nằm ngoài miền số của kernel, cả hai đã đóng băng ở `CAPABILITY_BOUNDARY`.

