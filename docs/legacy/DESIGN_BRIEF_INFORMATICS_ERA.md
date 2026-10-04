# DESIGN_BRIEF.md — phần đã tách, chép nguyên văn

> Tách khỏi [`DESIGN_BRIEF.md`](../DESIGN_BRIEF.md) ở run `cuboid-final-review` (2026-10-05): mô tả sản phẩm, bố cục workspace, hợp đồng hiển thị theo miền và việc thiết kế của giai đoạn Tin học; các ràng buộc §3, ngôn ngữ thị giác, giọng văn và quy trình kiểm ở lại.
> Nguồn: `docs/DESIGN_BRIEF.md` tại commit `4048ff83d14ad2a1fcd940d127590ca777dbc7cf` (blob `8710530dc5d10139311e799b215da3e2de06d15d`). Mỗi khối dưới đây là **nguyên văn** (byte-identical)
> các dòng ghi trong chú thích của nó, theo thứ tự của bản gốc. Đây là lịch sử: không sửa, không thêm.
> Đường dẫn tương đối trong các khối viết cho thư mục `docs/`, nên từ `legacy/` chúng trỏ lệch một cấp
> (`README.md`). Kiểm lại: `docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --verify`.

<!-- khối 1/5 · dòng 18–24 của bản gốc · §1: informatics topic and the browser-engine sentence · sha256 4776e47363e4299d07437750329e0209b1d1116ef84816ae60714869768b4bfd -->
**Tên đề tài:** *Hệ thống mô phỏng tương tác kết hợp LLM phân tích bài toán
bằng ngôn ngữ tự nhiên, hỗ trợ dạy học môn Tin học THPT.*

Học sinh **dán một đề bài bằng tiếng Việt**. LLM (Gemini) **chỉ đọc hiểu đề và
điền một bản đặc tả đã kiểm định**. Sau đó **một engine tất định chạy trên
trình duyệt** sinh ra toàn bộ diễn biến, hoạt cảnh và kết quả.

<!-- hết khối 1 -->

<!-- khối 2/5 · dòng 28–33 của bản gốc · §1: informatics learners and catalogue scale · sha256 96d74c44f1ba9862689cddf1126bb0617ec7cc6c088745abd2e5e37ffe638664 -->
**Người học:** học sinh THPT Việt Nam (lớp 10–12), môn Tin học, chương trình
GDPT 2018. Không phải lập trình viên. **Mọi chữ trên màn hình là tiếng Việt.**

**Quy mô hiện tại:** 9 họ năng lực · 19 mô phỏng · 6 miền hiển thị
(`algorithm`, `binary`, `logic`, `network`, `tree`, `generic`).

<!-- hết khối 2 -->

<!-- khối 3/5 · dòng 71–82 của bản gốc · §2: workspace layout of the informatics stage · sha256 d987a931313ddbbae96bee304fa12ba17a6c0e0594c8878b2cf63772a2d99a31 -->
### Bố cục Workspace (2 cột)

| Vùng | Nội dung |
|---|---|
| **Sân khấu** (trái, lớn) | Hình ảnh mô phỏng: dãy cột, cây, đồ thị, mạch, bit… |
| **Panel trạng thái** (dưới sân khấu) | Ngăn xếp/hàng đợi/biến — **sự thật engine**, cập nhật từng bước |
| **Thuyết minh** (dưới panel) | Một câu nói **hành động & nguyên nhân** của bước hiện tại |
| **Quan sát** (phải) | Siêu dữ liệu: biến thể, gốc, tiến độ, "Hỏi AI về bước này" |
| **Dòng thời gian** (đáy, full width) | ⏮ ◀ ▶ Tự chạy ⏭ · Đặt lại · "Bước 12 / 22" · tốc độ · thanh trượt |

---

<!-- hết khối 3 -->

<!-- khối 4/5 · dòng 131–153 của bản gốc · §4: display contracts of the removed domains · sha256 660bd3d891df895489cd35b74aee146875011085312791667ca08e4e1efa20c8 -->
## 4. Hợp đồng hiển thị theo từng miền

Mỗi mô phỏng phải thể hiện được **cơ chế ẩn** của nó — không chỉ vẽ đúng dữ liệu.

| Miền | Phải nhìn thấy | Panel |
|---|---|---|
| **algorithm** (tìm/đếm/tổng/sắp xếp) | dãy cột, ô đang xét, vùng đã sắp, biến chạy, dòng mã giả đang thực hiện | biến + mã giả |
| **tree** (duyệt cây) | gốc rõ, quan hệ **trái/phải** có nhãn, nút hiện tại/đã thăm/chưa thăm khác nhau, đường active | **ngăn xếp** (DFS) hoặc **hàng đợi** (theo mức) |
| **network** (định tuyến, duyệt đồ thị) | đỉnh–cạnh, gói tin/nút đang xét, đường đi dựng dần | hàng đợi / ngăn xếp |
| **network** (đóng gói TCP/IP) | chồng tầng hai đầu gửi–nhận, PDU dày thêm/mỏng đi qua từng tầng | delta từng bước |
| **binary** (bit, đổi cơ số) | ô bit + hàng trọng số, hoặc bảng chia-lấy-dư / trọng số vị trí | tiến trình chuyển đổi |
| **logic** (cổng, mạch) | cổng và dây, đầu vào bật/tắt, đầu ra sáng/tắt | **bảng chân trị** |
| **generic** (cảnh tự dựng) | đúng các đối tượng đề khai (nút, cạnh, công tắc, đèn, ô giá trị) | — |

**Phép thử vàng:** *người xem phải phân biệt được bốn biến thể duyệt cây mà
KHÔNG cần đọc tiêu đề.* Nếu chỉ khác nhau ở chữ trên đầu thì thiết kế chưa đạt.

**Về 3D:** 3D **không phải một miền riêng**, chỉ là renderer thứ hai đọc **cùng
trạng thái**. Chỉ dùng 3D khi **trục sâu mang ý nghĩa thật** (ví dụ: Z = tầng
giao thức). 3D xoay cho đẹp = bị cấm.

---

<!-- hết khối 4 -->

<!-- khối 5/5 · dòng 211–225 của bản gốc · §8: design backlog of the informatics product · sha256 c87792116e30e5b6e949f1cbf53fe103c5102c44523637c98e697979218ab731 -->
## 8. Chỗ đang cần thiết kế

| Việc | Trạng thái |
|---|---|
| Cây 1 nút để lại khoảng trắng lớn dưới khung | thẩm mỹ, chưa xử lý |
| Nhãn cạnh 9px khi cây dày hơn 8 nút | cần đo lại nếu nới giới hạn |
| Miền **bảng/CSDL** (`relational_table_query`) | **chưa mở** — sẽ cần ngôn ngữ thị giác cho lưới dữ liệu, vị từ lọc, tổng hợp |
| Chế độ luyện tập / tự kiểm | ngoài phạm vi hiện tại, cần duyệt riêng |

**Đang bị đóng băng phạm vi** (đừng thiết kế nếu chưa được duyệt): miền chuyên
biệt mới, trình soạn thảo mã, undo/redo, phóng to/kéo thả khung nhìn, trình sửa
kiểu, sửa topology.

---

<!-- hết khối 5 -->
