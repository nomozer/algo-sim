# HIGH_RISK_VERIFICATION — đối chiếu 4 khối HIGH với nguồn

**Ngày**: 2026-08-29 · **Chế độ**: `MÁY-TỪ-NGUỒN` (`machine_verifier`) ·
**Không người nào ký cho từng bài.**

`MEASURED_OUTPUT_USED_FOR_SOURCE_VERIFICATION = false` — không bước nào dưới
đây dùng `run_pipeline`, LLM phân tích, hay bất kỳ đầu ra nào của hệ đang được
đo. Nguồn được đọc bằng: ảnh trang PDF dựng tại chỗ (`pymupdf`, 170 dpi) và
HTML gốc tải thẳng. Đáp án được kiểm lại bằng **suy dẫn toạ độ độc lập**, và
suy dẫn ấy chỉ dùng để *phát hiện lệch* — giá trị ghi vào `ĐÁP ÁN` vẫn là
**đáp án in trong nguồn**.

## Vì sao bốn khối này là HIGH

`PROTOCOL_AMENDMENT_PRESEAL` xếp rủi ro theo *chỗ máy có thể đọc sai mà vẫn ra
một đề đọc như thật*. Bốn khối này mỗi khối có một chỗ như vậy, nêu sẵn ở
trường `CẦN KIỂM GÌ` của gói.

---

## A09#0 — cos vô tỉ, oracle hữu tỉ

- **Nguồn**: Chuyên đề QHVG Toán 11 (KNTTVCS, 704tr), B22.1 PHẦN TỰ LUẬN,
  Câu 13 — đề tr PDF 3, lời giải tr PDF 13 ("Page 10").
- **Đọc bằng**: ảnh trang 3 và trang 13.

| Trục | Kết quả |
|---|---|
| `PRIMARY_MATCH` | **PASS** — nguồn: *"Cho hình lập phương ABCD.A′B′C′D′, gọi I là trung điểm của cạnh AB. Tính côsin của góc giữa hai đường thẳng A′D và B′I được kết quả là"*. Bản chép bỏ đuôi *"được kết quả là"* (dạng điền khuyết) và đóng câu bằng dấu chấm; không mất dữ kiện nào. |
| `MATH_SYMBOLS_MATCH` | **PASS** — `A′D`, `B′I`, `I` trung điểm `AB` khớp; không ký hiệu nào rơi. |
| `SOURCE_SOLUTION_MATCH` | **PASS** — nguồn in nguyên văn `cos(A′D, B′I) = √10/5`. |
| `VERDICT` | **CONFIRMED** |

**Suy dẫn độc lập** (cạnh 1): `A′D = (0,1,−1)`, `B′I = (−1/2,0,−1)` ⇒
`cos = 1/(√2 · √5/2) = 2/√10 = √10/5` ✓. `cos² = 4/10 = 2/5` = `ĐÁP ÁN`.

Đây là ứng viên đắt nhất của cả tập: **đáp án nguồn VÔ TỈ mà đơn vị checker
vẫn HỮU TỈ**. Nó là bằng chứng vì sao ô A09 nhận `cos²` chứ không nhận `cos`.

---

## A11#0 — công thức trong bản tóm tắt bị nghi sai

- **Nguồn**: VietJack — *Khoảng cách lớp 11 (Lý thuyết Toán 11 KNTT)*, Ví dụ 2.
- **Đọc bằng**: HTML gốc (`curl`), phần lời giải nằm trong ảnh nên chỉ câu kết
  luận là chữ.

| Trục | Kết quả |
|---|---|
| `PRIMARY_MATCH` | **PASS** — nguồn: *"Cho hình chóp S.ABC có mặt phẳng (SAB) vuông góc với mặt đáy, tam giác SAB vuông tại S, AB = a, SA = 3a/5. Tính khoảng cách từ điểm S đến mặt phẳng (ABC)."* Khớp từng chữ. |
| `MATH_SYMBOLS_MATCH` | **PASS** — `SA = 3a/5` là **phân số**, không phải căn thức bị nuốt. |
| `SOURCE_SOLUTION_MATCH` | **PASS** — nguồn kết: *"Vậy khoảng cách từ điểm S đến mặt phẳng (ABC) bằng 12a/25"*. |
| `VERDICT` | **CONFIRMED** |

**Suy dẫn độc lập**: `SB = √(a² − 9a²/25) = 4a/5`; đường cao từ `S` xuống `AB`
bằng `SA·SB/AB = 12a/25`. Vì `(SAB) ⊥ (ABC)` nên chân đường cao ấy chính là
hình chiếu của `S` lên `(ABC)` ⇒ `d = 12a/25` ✓.

**Nghi vấn đã nêu trong `CẦN KIỂM GÌ` — chưa đóng được, và không cần đóng**:
bản tóm tắt lý thuyết được cho là in công thức `SA·AB/SB` (đúng phải là
`SA·SB/AB`). Công thức ấy nằm **trong ảnh**, không đọc được bằng chữ. Không
quan trọng: thứ chảy vào `ĐÁP ÁN` là **con số nguồn tự in** (`12a/25`), và con
số ấy khớp suy dẫn độc lập. Một công thức in sai ở đoạn lý thuyết không làm
sai đáp án của ví dụ.

`C` là điểm **tự do** (đề không ràng buộc) — đã kiểm: `d` không phụ thuộc `C`.

---

## A04#1 — ba tỉ số, và cái mẫu số dễ đọc nhầm

- **Nguồn**: DeThi.edu.vn — *Bài tập tự luận Toán 11: Đường thẳng và mặt phẳng
  song song (có lời giải)*, **Bài 32 ý a)**.
- **Đọc bằng**: HTML trang (trang nhúng nguyên văn tài liệu dưới dạng chữ).

| Trục | Kết quả |
|---|---|
| `PRIMARY_MATCH` | **PASS** — nguồn: *"32. Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. Trên các cạnh SA, SB, AD lần lượt lấy các điểm M, N, P sao cho SM/SA = SN/SB = PD/AD. a) Chứng minh MN P (ABCD)."* |
| `MATH_SYMBOLS_MATCH` | **PASS** — mẫu số thứ ba là **`PD/AD`**, KHÔNG phải `AP/AD` (đúng chỗ `CẦN KIỂM GÌ` cảnh báo). Ký tự `P` đứng giữa hai đối tượng là `∥` bị hỏng phông: cả tài liệu dùng `P` cho `∥` (`OO' P DF`, `MN P CDEF`, `IM P CD`…). |
| `SOURCE_SOLUTION_MATCH` | **N/A — kết luận nằm trong chính đề bài.** Bài ra dạng *chứng minh*, nên nguồn tự khẳng định `MN ∥ (ABCD)`; đó là đáp án của nguồn. Bản xem công khai cắt trước phần lời giải của mục LUYỆN TẬP, nên **không** có lời giải từng bước để đối chiếu. |
| `VERDICT` | **CONFIRMED** |

**Suy dẫn độc lập**: `SM/SA = SN/SB` ⇒ `MN ∥ AB` (Ta-lét trong `△SAB`);
`AB ⊂ (ABCD)`, `MN ⊄ (ABCD)` ⇒ `MN ∥ (ABCD)` ✓. Tỉ số chung là **tham số tự
do** — kết luận đúng với mọi giá trị, cùng lớp đã chốt.

---

## A04#2 — `G1, G2` và lại chữ `P`

- **Nguồn**: cùng tài liệu, **Bài 31 ý a)**.

| Trục | Kết quả |
|---|---|
| `PRIMARY_MATCH` | **PASS** — nguồn: *"31.Cho hình chóp S.ABCD. Gọi M,N lần lượt là trung điểm của AB và BC; G1, G2 tương ứng là trọng tâm các tam giác SAB, SBC. a) Chứng minh AC P (SMN)."* |
| `MATH_SYMBOLS_MATCH` | **PASS** — tên `G1, G2` xác nhận; `AC P (SMN)` = `AC ∥ (SMN)`. |
| `SOURCE_SOLUTION_MATCH` | **N/A — kết luận nằm trong chính đề bài** (như A04#1). |
| `VERDICT` | **CONFIRMED** |

**Suy dẫn độc lập**: `MN` là đường trung bình `△ABC` ⇒ `MN ∥ AC`;
`AC ⊄ (SMN)` ⇒ `AC ∥ (SMN)` ✓.

`G1, G2` chỉ xuất hiện ở ý b)/c) — bản chép giữ chúng vì chúng thuộc **phần
cho** của đề gốc, và bỏ đi là sửa đề.

---

## Tổng kết

| Khối | PRIMARY | SYMBOLS | SOURCE_SOLUTION | VERDICT |
|---|---|---|---|---|
| A09#0 | PASS | PASS | PASS (`√10/5`) | **CONFIRMED** |
| A11#0 | PASS | PASS | PASS (`12a/25`) | **CONFIRMED** |
| A04#1 | PASS | PASS | N/A (kết luận trong đề) | **CONFIRMED** |
| A04#2 | PASS | PASS | N/A (kết luận trong đề) | **CONFIRMED** |

**4/4 CONFIRMED bằng máy, đối chiếu với đúng nguồn đã trích dẫn.**

Câu được phép viết trong báo cáo: *"4 bản ghi HIGH_RISK đã được đối chiếu lại
với tài liệu nguồn; 37 bản ghi còn lại dựa vào xuất xứ nguồn công khai có
trích dẫn, kiểm nhất quán bằng máy, và đóng băng trước niêm phong."*

Câu **KHÔNG** được phép viết: *"41/41 do người kiểm"*, *"all cases human
verified"*, *"42/42 human verified"*.
