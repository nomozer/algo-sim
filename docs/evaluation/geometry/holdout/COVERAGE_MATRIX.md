# MA TRẬN ĐỘ PHỦ — POOL HELD-OUT HÌNH HỌC

> Sinh bằng `scripts/holdout_coverage_matrix.py`. **0 API call.**
> Không thêm bài, không chọn bài — chỉ đếm và chỉ ra chỗ trống.

**Pool: 1 bài · phủ 1/20 ô · ⛔ CHƯA RÚT ĐƯỢC**

---

## 1. Theo Ô (trục thiết kế tập đo)

| Ô | Họ | Đáp án | Nghĩa vụ kiểm | Bài | |
|---|---|---|---|--:|---|
| **A01** | intersection | construction | `point_on_line` | 0 | ⛔ trống · Giao tuyến hai mặt phẳng — điểm thuộc giao tuyến |
| **A02** | point_construction | verdict | `point_on_plane` | 0 | ⛔ trống · Điểm thuộc mặt phẳng |
| **A03** | line_relation | verdict | `parallel` | 0 | ⛔ trống · Hai đường thẳng song song |
| **A04** | line_relation | verdict | `parallel` | 0 | ⛔ trống · Đường thẳng song song mặt phẳng |
| **A05** | plane_construction | verdict | `parallel` | 0 | ⛔ trống · Hai mặt phẳng song song |
| **A06** | line_relation | verdict | `perpendicular` | 0 | ⛔ trống · Hai đường thẳng vuông góc |
| **A07** | line_relation | verdict | `perpendicular` | 0 | ⛔ trống · Đường thẳng vuông góc mặt phẳng |
| **A08** | plane_construction | verdict | `perpendicular` | 0 | ⛔ trống · Hai mặt phẳng vuông góc |
| **A09** | measurement | quantity | `angle` | 0 | ⛔ trống · Góc giữa hai đường thẳng |
| **A10** | measurement | quantity | `angle` | 0 | ⛔ trống · Góc giữa đường thẳng và mặt phẳng |
| **A11** | measurement | quantity | `distance` | 1 | ✅ · Khoảng cách từ điểm đến mặt phẳng |
| **A12** | measurement | quantity | `distance` | 0 | ⛔ trống · Khoảng cách từ điểm đến đường thẳng |
| **A13** | plane_construction | verdict | `coplanar` | 0 | ⛔ trống · Thiết diện / bốn điểm đồng phẳng |
| **A14** | solid_geometry | quantity | `volume` | 0 | ⛔ trống · Thể tích khối chóp hoặc lăng trụ |
| **B01** | measurement | refusal | `—` | 0 | ⛔ trống · Khoảng cách giữa hai đường thẳng chéo nhau |
| **B02** | measurement | refusal | `—` | 0 | ⛔ trống · Khoảng cách đường ∥ mặt, hoặc mặt ∥ mặt |
| **B03** | measurement | refusal | `—` | 0 | ⛔ trống · Góc nhị diện có miền (có thể tù) |
| **B04** | — (không họ nào khớp) | refusal | `—` | 0 | ⛔ trống · Oxyz: viết phương trình mặt phẳng / đường / mặt cầu |
| **B05** | solid_geometry | refusal | `—` | 0 | ⛔ trống · Mặt cầu · mặt nón · mặt trụ |
| **B06** | line_relation | refusal | `—` | 0 | ⛔ trống · Phép toán vectơ, hoặc phép chiếu song song |

---

## 2. Theo HỌ (trục nội dung)

| Họ | Ô tầng A | Ô tầng B | Bài | Ô còn trống |
|---|---|---|--:|---|
| **point_construction**<br>*dựng điểm · điểm thuộc vật* | A02 | — | 0 | A02 |
| **line_relation**<br>*quan hệ đường–đường, đường–mặt* | A03, A04, A06, A07 | B06 | 0 | A03, A04, A06, A07, B06 |
| **plane_construction**<br>*dựng mặt · quan hệ mặt–mặt · thiết diện* | A05, A08, A13 | — | 0 | A05, A08, A13 |
| **intersection**<br>*giao tuyến · giao điểm* | A01 | — | 0 | A01 |
| **solid_geometry**<br>*khối đa diện* | A14 | B05 | 0 | A14, B05 |
| **measurement**<br>*khoảng cách · góc · thể tích* | A09, A10, A11, A12 | B01, B02, B03 | 1 | A09, A10, A12, B01, B02, B03 |
| **proof_verification**<br>*chứng minh thuần, tách khỏi một quan hệ cụ thể* | **—** | — | 0 | — |

---

## 3. Theo HÌNH DẠNG ĐÁP ÁN

Ba hình dạng chấm bằng ba kiểu oracle khác nhau; lệch phân bố ở đây
làm lệch cả ý nghĩa của chỉ số ② `oracle`.

| Hình dạng | Bài | Chấm bằng |
|---|--:|---|
| construction | 0 | vật dựng được + quan hệ định nghĩa nó |
| verdict | 0 | true/false |
| quantity | 1 | phân số · cos² |
| refusal | 0 | **thang khác**: từ chối trung thực / bịa hình |

---

## 4. Hai chỗ hai trục KHÔNG khít — phát hiện thiết kế

Có trước khi pool có bài nào, nên không phải hệ quả của việc
chọn đề. Cả hai đều **giữ nguyên có chủ đích**, không ép cho đủ bảng.

**① Họ không có ô tầng A nào: `proof_verification`**

Trong `BANG_O`, việc *chứng minh* không có ô của riêng nó mà nằm lồng
trong sáu ô quan hệ A03–A08 — đề *"chứng minh AB ⊥ (SCD)"* rơi vào
A06/A07/A08. Ép một ánh xạ cho đủ bảy họ thì bảng trông đầy trong khi
tập đo không đổi một chút nào.

Hệ quả phải khai khi báo cáo 7B: **không tách được** *"hệ chứng minh
được quan hệ"* khỏi *"hệ nhận ra quan hệ"*. Muốn tách thì phải mở ô
mới trong `BANG_O` — việc TRƯỚC khi niêm phong, không phải sau.

**② Ô không thuộc họ nào: `B04`**

Viết phương trình mặt phẳng trong Oxyz là bài **biểu diễn đại số**,
không phải một trong bảy họ hình học. Nó vẫn là một ô tầng B hợp lệ —
ô tầng B chấm bằng *từ chối trung thực*, không cần thuộc họ nào.

