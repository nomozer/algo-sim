# PHỦ CHƯƠNG TRÌNH — Hình học không gian THPT

> Bảng này trả lời câu hội đồng sẽ hỏi: **"hệ làm được bao nhiêu phần của chương
> trình phổ thông?"** — bằng con số, không bằng cảm giác.
>
> Mọi ô **ĐƯỢC / KHÔNG** dưới đây đo bằng cách **chạy thật** phép đo/vị ngữ
> tương ứng, không suy từ tên hàm. Nhật ký đo ở §5.

Nguồn chương trình: GDPT 2018 môn Toán — xem §6.

---

## 1. Kết quả gọn

| | |
|---|---|
| Chủ đề khảo sát | **18** |
| **ĐƯỢC** diễn đạt trọn | **9** |
| **MỘT PHẦN** | **3** |
| **KHÔNG** diễn đạt được | **6** |

⚠️ Đây là phủ **HỢP ĐỒNG** (IR biểu đạt nổi hay không), **KHÔNG** phải phủ
**NĂNG LỰC** (AI có sinh đúng hay không). Một chủ đề "ĐƯỢC" vẫn có thể trượt vì
mô hình viết sai — đó là câu hỏi của Phase 5, không phải của bảng này.

---

## 2. Toán 11 — Đường thẳng & mặt phẳng trong không gian

| # | Chủ đề | Nghĩa vụ / cơ chế | |
|---|---|---|:-:|
| 1 | Đại cương: điểm · đường · mặt, **giao tuyến hai mặt** | `point_on_line` + `intersect_plane_plane` | ✅ |
| 2 | Hai đường thẳng **song song** | `parallel` → `P.parallel_lines` | ✅ |
| 3 | Đường thẳng **∥ mặt phẳng** | `parallel` → `P.parallel_line_plane` | ✅ |
| 4 | Hai mặt phẳng **song song** | `parallel` → `P.parallel_planes` | ✅ |
| 5 | **Phép chiếu song song**, hình biểu diễn | — | ❌ |
| 6 | **Vectơ** trong không gian | kiểu `vector3` có; **phép toán vectơ không có** | ⚠️ |

**#5 — vì sao KHÔNG.** IR chỉ có `project_onto`, và nó là **chiếu vuông góc**
(`K.project_point_onto_plane`). Chiếu song song theo một phương cho trước là
phép khác, kernel không có. Đây là chủ đề *dựng hình biểu diễn* — cốt lõi của
việc **vẽ hình không gian trên giấy**, và hệ không nói về nó được.

**#6 — vì sao MỘT PHẦN.** `vector3` là một kiểu bộ nhớ, nhưng IR **không có**
phép cộng vectơ, nhân vô hướng, hay tích vô hướng ở tầng biểu thức. Đề *"phân
tích $\vec{SM}$ theo $\vec{SA}, \vec{SB}, \vec{SC}$"* không viết ra được.

---

## 3. Toán 11 — Quan hệ vuông góc

| # | Chủ đề | Nghĩa vụ / cơ chế | |
|---|---|---|:-:|
| 7 | Hai đường thẳng **vuông góc** | `perpendicular` → `P.perpendicular_lines` | ✅ |
| 8 | Đường thẳng **⊥ mặt phẳng** | `perpendicular` → `P.line_perpendicular_plane` | ✅ |
| 9 | Hai mặt phẳng **vuông góc** | `perpendicular` → `P.perpendicular_planes` | ✅ |
| 10 | **Góc** giữa đường–đường · đường–mặt · mặt–mặt | `angle`, đo bằng `cos²`/`sin²` | ✅ |
| 11 | **Góc nhị diện** | chỉ có góc hai mặt phẳng | ⚠️ |
| 12 | **Khoảng cách** — điểm↔mặt, điểm↔đường | `distance` | ✅ |
| 13 | **Khoảng cách** — đường↔mặt ∥, mặt↔mặt ∥, **hai đường chéo nhau** | — | ❌ |
| 14 | **Hình chiếu vuông góc** của điểm | `project_onto` | ✅ |

**#11 — vì sao MỘT PHẦN.** Góc nhị diện có **miền** (nửa mặt phẳng) và có thể
tù; `cos_sq_between_planes` trả **bình phương cosin của góc giữa hai mặt phẳng**,
luôn thuộc $[0°, 90°]$. Đề hỏi *"góc nhị diện $[A, SB, C]$ bằng $120°$"* thì hệ
trả lời được góc mặt-mặt là $60°$ — **đúng theo định nghĩa của nó**, sai theo
câu hỏi.

**#13 — lỗ LỚN NHẤT, và nó nằm ở HỢP ĐỒNG chứ không ở kernel.**

```
kernel  CÓ  distance_sq_skew_lines · distance_sq_parallel_lines
measure CHƯA nối       →  đo được: điểm–mặt · điểm–đường
                          KHÔNG   : đường–đường · đường–mặt · mặt–mặt
```

*Khoảng cách giữa hai đường thẳng chéo nhau* là dạng bài **tần suất cao** ở đề
tốt nghiệp. Kernel tính được **chính xác** rồi; chỉ thiếu một nhánh `isinstance`
trong `geometry_exec._do`. Đây là món rẻ nhất trong toàn bảng.

⚠️ Cùng chỗ ấy còn một ràng buộc **không** vá bằng code được: `distance` trả
`GEOMETRY_IRRATIONAL_RESULT` khi kết quả vô tỉ (ví dụ điểm–điểm $(0,0,3)$ tới
$(1,1,1)$ ra $\sqrt{6}$). Đó là **quyết định thiết kế đúng** — thà báo còn hơn
làm tròn — nhưng nó loại mọi đề mà khoảng cách không hữu tỉ. Muốn phủ nhóm ấy
phải cho `measure` trả **bình phương** khoảng cách, và sửa cả cách đề khai đáp án.

---

## 4. Toán 12

| # | Chủ đề | Nghĩa vụ / cơ chế | |
|---|---|---|:-:|
| 15 | **Thể tích** khối đa diện (chóp, lăng trụ) | `volume` — `construct_solid` + `measure.volume` | ✅ |
| 16 | **Thiết diện** · bốn điểm **đồng phẳng** | `coplanar` — `construct_section` đi theo MẶT, sinh từng cạnh | ✅ |
| 16b | **Điểm thuộc mặt phẳng / đường thẳng** | `point_on_plane` · `point_on_line` | ✅ |
| 17 | Hệ toạ độ **Oxyz**: đề cho sẵn toạ độ | fact số + `point3` | ✅ |
| 18 | **Phương trình** mặt phẳng / đường thẳng / mặt cầu | — | ❌ |
| 19 | **Mặt cầu · mặt nón · mặt trụ** (khối tròn xoay) | — | ❌ |
| 20 | **Quỹ tích** điểm | — | ❌ |

**#18 — vì sao KHÔNG.** Hệ có `Plane3` là một **đối tượng**, không có *"phương
trình mặt phẳng"* là một **kết quả cần tìm**. Đề *"viết phương trình mặt phẳng
(P) đi qua A và vuông góc d"* hỏi một **biểu thức đại số**; taxonomy 8 nghĩa vụ
không có kind nào nhận nó.

**#19, #20 — prompt TỰ KHAI, và đó là hành vi đúng.**

> *"Đề cần mặt cầu, mặt nón, mặt trụ, hoặc quỹ tích — **nói thẳng là không diễn
> đạt được**. Đừng thay bằng một khối đa diện gần giống. Một mô phỏng sai hình
> còn tệ hơn không có mô phỏng: học sinh sẽ tin nó."*

Kernel dựng trên `Fraction` và đa diện; mặt cong không nằm trong mô hình. Đây
**không** phải thiếu sót cài đặt mà là **ranh giới của phương pháp** — và khai
nó ra là trung thực, không phải là yếu.

---

## 5. Nhật ký đo

Chạy trên `8b4025e`, không suy từ tên hàm.

```
distance   ĐƯỢC  điểm–mặt = 3   ·  điểm–đường = 3
           KHÔNG điểm–điểm (GEOMETRY_IRRATIONAL_RESULT — √6)
           KHÔNG đường–đường chéo · đường–mặt · mặt–mặt (GEOMETRY_OPERAND_TYPE)
angle      ĐƯỢC  đường–đường · mặt–mặt · đường–mặt
kernel có  distance_sq_skew_lines · distance_sq_parallel_lines  ← chưa nối
predicate  collinear · coplanar · line_in_plane · line_perpendicular_plane
           parallel_line_plane · parallel_lines · parallel_planes
IR dựng    point · line · plane · solid · section   (5, không có extrude/base)
```

---

## 6. Bốn việc, xếp theo phủ thêm được bao nhiêu / tốn bao nhiêu

| | Việc | Phủ thêm | Công |
|---|---|---|---|
| 1 | Nối `distance` cho **đường–đường · đường–mặt · mặt–mặt** | **#13** — dạng tần suất cao | vài nhánh `isinstance`, kernel đã có |
| 2 | `measure` trả **bình phương** khoảng cách khi vô tỉ | mở phần lớn đề khoảng cách | đụng cách khai đáp án |
| 3 | Phép toán **vectơ** ở tầng biểu thức | **#6** trọn vẹn | thêm biểu thức, không đụng kernel |
| 4 | Góc **nhị diện** có miền | **#11** | cần khái niệm mới ở kernel |

**KHÔNG nên làm**: mặt cầu/nón/trụ (#19) — đổi cả nền toán từ đa diện hữu tỉ
sang mặt cong, tức viết lại kernel. Ngoài phạm vi khoá luận.

---

## 7. Điều bảng này KHÔNG nói

Nó nói **hợp đồng biểu đạt được gì**, không nói **AI sinh đúng bao nhiêu**. Hai
số ấy độc lập, và số thứ hai chỉ có ở lượt đo Phase 5 (`A = 4/10` trên tập DEV
đã bị nhìn).

Nó cũng **không** đo tần suất: chưa ai đếm mỗi chủ đề chiếm bao nhiêu phần trăm
đề thi thật. Bảng nói *"phủ 9/18 chủ đề"*, **không** được đọc thành *"làm được
50% đề thi"*.

---

## Nguồn

- [Chuyên đề Quan hệ vuông góc trong không gian — Toán 11 KNTT (VietJack)](https://www.vietjack.com/toan-lop-11/quan-he-vuong-goc-trong-khong-gian-kntt.jsp)
- [Tài liệu ôn thi tốt nghiệp THPT môn Toán theo GDPT 2018 (TOANMATH)](https://toanmath.com/2025/04/tai-lieu-on-thi-tot-nghiep-thpt-mon-toan-theo-chuong-trinh-gdpt-2018.html)
- [Lý thuyết chương Mặt nón · mặt trụ · mặt cầu — Toán 12 (VietJack)](https://vietjack.com/toan-lop-12/tong-hop-ly-thuyet-chuong-mat-non-mat-tru-mat-cau.jsp)
- [Chuyên đề hình học không gian ôn thi tốt nghiệp THPT 2025 (Thư Viện Học Liệu)](https://thuvienhoclieu.com/chuyen-de-hinh-hoc-khong-gian-on-thi-tot-nghiep-thpt-giai-chi-tiet/)
- [Lời giải chi tiết đề thi Toán tốt nghiệp THPT 2025 chính thức (MathVN)](https://www.mathvn.com/2025/07/loi-giai-chi-tiet-e-thi-toan-tot-nghiep.html)
