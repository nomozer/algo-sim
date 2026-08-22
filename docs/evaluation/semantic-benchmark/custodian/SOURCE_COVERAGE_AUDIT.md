# SOURCE COVERAGE AUDIT — năm SGK, 708 trang

Kết luận ngắn: **corpus bài toán thuật toán trong SGK Tin học THPT tập trung
gần như trọn vẹn ở hai chương** — Tin học 10 Chủ đề 5 và Tin học 11 (KHMT) Chủ
đề 6. Ba cuốn còn lại đóng góp **5/189 record**.

Đó không phải thiếu sót của việc trích. Đó là hình dạng thật của chương trình:
ba cuốn kia dạy hệ điều hành, mạng, đạo đức số, cơ sở dữ liệu, chỉnh sửa ảnh,
AI/học máy và HTML/CSS — những nội dung không đặt ra bài toán có **kết quả xác
định tính được từ dữ liệu cho sẵn**.

## Cách đọc nguồn

Cả năm cuốn là **bản quét, không có lớp chữ**: `pdftotext` trả 60 ký tự cho 60
trang, đúng bằng số dấu ngắt trang.

| | Đường đọc | Trang |
|---|---|---|
| V1 (TH10 CĐ5, TH11-KHMT CĐ6) | PyMuPDF dựng ảnh → đọc bằng thị giác | 135 |
| V2 (ba cuốn còn lại) | `backend/scripts/ocr_sgk_ingest.py` → Cloud Vision, **cache trên đĩa** | 483 |

Repo **không có** RAG/index/cache nào để tái dùng trước đó: `data/knowledge/`
chỉ chứa PDF nguồn, còn `app/ingestion/input.py` là lớp chuẩn hoá input của
**sản phẩm** (text/docx/ảnh), không đọc PDF. Cache OCR nay nằm ở
`data/knowledge/ocr-cache/` và mọi lượt chạy sau đọc lại từ đó.

Credential Cloud Vision nạp từ `.secrets/` qua `GOOGLE_APPLICATION_CREDENTIALS`;
giá trị secret **không** vào log lẫn artifact.

## Rubric eligibility áp dụng

Một bài **eligible** khi: input/state **hữu hạn và rời rạc** · có **kết quả hoặc
biến đổi xác định** · có **thủ tục thực thi có biên** · kết quả **kiểm tra độc
lập được**.

Vận hành thành quy tắc trích: **nhận** câu đòi một kết quả xác định tính được từ
dữ liệu hoặc thủ tục đã cho; **loại** câu thuần định nghĩa · nêu ý kiến · kể tên
· thao tác giao diện · "lệnh này có lỗi không" · in ra chuỗi cho sẵn · yêu cầu
*viết một câu lệnh/truy vấn* mà không có dữ liệu cụ thể và đáp án là mã chứ
không phải một giá trị.

Rubric nói về **bản chất bài toán**, không hỏi hệ có làm được không.

## Bảng theo chủ đề

### `tin-hoc-11-ict.pdf` — 155 trang, **3 record**

| Chủ đề | Trang | Eligible? | Record | Bằng chứng |
|---|---|---|---|---|
| CĐ1. Máy tính và xã hội tri thức | 5–31 | không | 0 | Bài 1–5: hệ điều hành, phần mềm nguồn mở. Bài 4 có bảng cộng hai bit nhưng câu hỏi là *"z và t là kết quả của phép toán lôgic nào"* — nhận diện phép toán, đáp án in ngay trong đoạn (tr.25) |
| CĐ2. Tổ chức lưu trữ, tìm kiếm, trao đổi thông tin | 32–43 | không | 0 | khái niệm lưu trữ, tìm kiếm trên Internet |
| CĐ3. Đạo đức, pháp luật, văn hoá số | 44–48 | không | 0 | thảo luận |
| CĐ4. Giới thiệu các hệ CSDL | 49–78 | không | 0 | bài tập là *viết câu truy vấn / thiết kế bảng* — không cho dữ liệu cụ thể, đáp án là mã (tr.57, 72) |
| CĐ5. Hướng nghiệp với tin học | 79–95 | không | 0 | nghề nghiệp |
| CĐ6. Thực hành tạo và khai thác CSDL | 96–118 | không | 0 | thao tác trên phần mềm; LT tr.115 là sao lưu/phục hồi |
| **CĐ7. Phần mềm chỉnh sửa ảnh và làm video** | 119–153 | **có** | **3** | tr.121 LT1 (kích thước ảnh theo 4 độ phân giải), tr.121 LT2 (độ phân giải cao/thấp hơn), tr.136 LT2 (số khung hình Blend) |

### `tin-hoc-12-cs.pdf` — 168 trang, **1 record**

| Chủ đề | Trang | Eligible? | Record | Bằng chứng |
|---|---|---|---|---|
| CĐ1. Máy tính và xã hội tri thức | 7–15 | không | 0 | AI, thảo luận |
| CĐ2. Mạng máy tính và Internet | 16–35 | không | 0 | thiết bị mạng, giao thức — câu hỏi định tính |
| CĐ3. Đạo đức, pháp luật, văn hoá số | 36–40 | không | 0 | thảo luận |
| **CĐ4. Giải quyết vấn đề với sự trợ giúp của máy tính** | 41–120 | **có (1 bài)** | **1** | Bài 7–18 là HTML/CSS. Duy nhất tr.66 LT1 có phép tính xác định (tỉ lệ ảnh 720×450 với `width="600"`) |
| CĐ5. Hướng nghiệp với tin học | 121–130 | không | 0 | nghề nghiệp |
| CĐ6. Mạng máy tính và Internet (thực hành) | 131–133 | không | 0 | thao tác thiết bị |
| CĐ7. Giải quyết vấn đề với sự trợ giúp của máy tính | 134–165 | không | 0 | Bài 25–30: học máy, khoa học dữ liệu, mô phỏng. LT tr.148 hỏi *ước tính* bậc độ lớn, không phải kết quả xác định |

### `tin-hoc-12-ict.pdf` — 160 trang, **1 record**

| Chủ đề | Trang | Eligible? | Record | Bằng chứng |
|---|---|---|---|---|
| CĐ1–CĐ6 | 7–133 | không | 0 | trùng nội dung với `tin-hoc-12-cs` ở CĐ1–3, CĐ5; CĐ4 là HTML/CSS |
| **CĐ4 (tr.66)** | 66 | **có (1 bài)** | **1** | LT1 cùng dạng bài với 12-CS nhưng `width="690"` — hai giá trị khác nhau nên là hai record riêng |
| CĐ7. Ứng dụng tin học | 134–156 | không | 0 | Bài 23–28: xây dựng trang web |

### Đã có từ V1 (giữ nguyên)

| SGK | Chủ đề | Trang | Record |
|---|---|---|---|
| `tin-hoc-10.pdf` | CĐ5. Giải quyết vấn đề với sự trợ giúp của máy tính | 86–155 | **109** |
| `tin-hoc-11-cs.pdf` | CĐ6. Kĩ thuật lập trình | 81–145 | **75** |

## Cách khảo sát ba cuốn V2

Từ cache OCR, quét **toàn bộ** khối bài tập (`LUYỆN TẬP`, `VẬN DỤNG`, `THỰC
HÀNH`, `Nhiệm vụ n`, `Câu hỏi n`, `Hoạt động n`) rồi lọc hai vòng độc lập:

1. động từ tính toán + tối thiểu 3 chữ số trong khối → 7 + 2 + 2 ứng viên;
2. động từ chuyển đổi/thuật toán (`hãy chuyển`, `đổi sang`, `mã hoá`, `hãy sắp`,
   `hãy đếm`, `hãy tìm`, `xác định giá trị`, …) → 18 + 19 + 13 ứng viên.

Mọi ứng viên đều được đọc nguyên văn. Vòng 2 không thêm record nào — toàn bộ là
"hãy tìm hiểu", "hãy nêu", "vì sao". Công cụ: `scan_cache.py`.

## Ý nghĩa cho luận văn

Phạm vi phủ chương trình phải được ghi **đúng theo source universe thực tế**:
benchmark đo lớp bài thuật toán của **Tin học 10 CĐ5 và Tin học 11 KHMT CĐ6**,
cộng vài bài tính toán rời rạc ở ba cuốn còn lại. **Không** được diễn giải thành
"toàn bộ chương trình Tin học THPT".
