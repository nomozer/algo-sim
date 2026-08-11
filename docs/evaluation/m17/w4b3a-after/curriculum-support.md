# W4B-3A — BẢNG HỖ TRỢ THEO CHƯƠNG TRÌNH

**Sinh từ nguồn** bởi `backend/scripts/curriculum_support_report.py` đọc
`app/simulation/coverage.py`. Đừng sửa tay: sửa registry rồi chạy lại.

> **Đọc đúng hai cột.** `Phủ` trả lời *mục này đã ship tới đâu*; `Kiểu hỗ trợ`
> trả lời *học sinh thật sự làm được gì*. Một mục chỉ bấm-Tiến-để-xem và một
> mục học sinh đổi được mô hình đều hiện `SUPPORTED` ở cột thứ nhất — đó là lý
> do có cột thứ hai.

> **Ranh giới không được xoá:** *chương trình có chủ đề này* ≠ *AlgoSim có một
> cơ chế mô phỏng có nghĩa sư phạm cho nó*. Không đơn vị nào được nâng hạng chỉ
> vì có target trùng tên (COVERAGE §O5).

**25 đơn vị kiến thức** · trong phạm vi: **18** · tuyên bố hiện hành: **`CURRICULUM_SUPPORT_PARTIAL`**

## Đếm theo kiểu hỗ trợ

| Kiểu | Nghĩa | Số đơn vị |
|---|---|---|
| `SUPPORTED_INTERACTIVE` | Học sinh ĐỔI được mô hình, engine tính lại | 8 |
| `SUPPORTED_TRACE` | Đi từng bước tất định (có thể có cam kết được chấm) | 2 |
| `SUPPORTED_BOUNDED_ARTIFACT` | Sửa thuộc tính trong miền ĐÓNG của một sản phẩm | 1 |
| `SUPPORTED_EXPLANATION` | Chỉ trình bày/giải thích | 0 |
| `PARTIAL` | Có phần — giới hạn khai tường minh | 5 |
| `UNSUPPORTED` | Chưa/cố ý không hỗ trợ | 2 |
| `NOT_SIMULATION_SUITABLE` | Không nên mô phỏng (mô phỏng ở đây là trang trí) | 7 |

Còn dang dở trong phạm vi (7): `arrays_1d_2d`, `database_table_query`, `dijkstra_weighted_shortest_path`, `loops_branch_variable`, `os_process_fsm`, `practice_activity`, `text_media_encoding`

## Từng đơn vị

| Đơn vị | Nhãn | Neo chương trình | Phủ | Kiểu hỗ trợ | Bằng chứng |
|---|---|---|---|---|---|
| `access_control` | Kiểm soát truy cập (quy tắc logic) | T10 B9 · T11 B15 | SUPPORTED | **SUPPORTED_INTERACTIVE** | tái dụng bề mặt boolean (gạt điều kiện) — cùng đường tương tác với logic_data |
| `binary_search` | Tìm kiếm nhị phân | T11CS B19 | SUPPORTED | **SUPPORTED_INTERACTIVE** | INTERACTIVE_MODEL đo được: Khám phá cho phá tiền đề dãy đã sắp, Thử thách cho chọn nửa (4/13 bước) |
| `binary_system` | Hệ đếm & đổi cơ số (trọng số vị trí) | T10 B4 | SUPPORTED | **SUPPORTED_INTERACTIVE** | decimal_to_binary INTERACTIVE_STAGE (bật/tắt bit, engine tính lại); base_conversion chỉ khai báo, chưa đo |
| `info_system_dataflow` | Hệ thống thông tin / luồng dữ liệu có hướng | T11 B10 · T12CS B29 | SUPPORTED | **SUPPORTED_INTERACTIVE** | generic.rule_scene INTERACTIVE_STAGE (hybrid — gạt công tắc, chuỗi rule tính lại) |
| `logic_data` | Dữ liệu lôgic / bảng chân trị | T10 B5 | SUPPORTED | **SUPPORTED_INTERACTIVE** | and_gate INTERACTIVE_STAGE (gạt đầu vào → bảng chân trị tất định); boolean_dag chưa có bài mẫu offline |
| `packet_routing` | Định tuyến gói tin (BFS số chặng) | T10 CĐ2 · T12 CĐ2 | SUPPORTED | **SUPPORTED_INTERACTIVE** | INTERACTIVE_MODEL đo được: ngắt/nối liên kết → BFS định tuyến lại; kèm predict chặng kế tiếp |
| `single_pass_scan` | Quét dãy một lượt (tìm/đếm/tổng/tìm-đầu-tiên) | T10 CĐ5 · T11CS B17 | SUPPORTED | **SUPPORTED_INTERACTIVE** | find_max/find_min/linear_search INTERACTIVE_MODEL; sum_if/count_if chỉ COMMITMENT_TRACE — kéo ở hai bài đó là trang trí nên CỐ Ý không bày (COVERAGE §2.6) |
| `sorting` | Sắp xếp so sánh | T11CS B21–22 | SUPPORTED | **SUPPORTED_INTERACTIVE** | bubble/insertion ĐO ĐƯỢC là INTERACTIVE_MODEL (kéo đổi chỗ → apply → engine chạy lại nhánh); selection chỉ KHAI BÁO (chưa có bài mẫu offline) |
| `graph_traversal` | Duyệt đồ thị / tìm đường không trọng số (BFS/DFS) | T11CS B17 · T12 CĐ2 | SUPPORTED | **SUPPORTED_TRACE** | có timeline BFS/DFS nhưng CHƯA có bài mẫu offline ⇒ chưa đo được trong trình duyệt; không khai thao tác tự do |
| `network_layering` | Giao thức / phân tầng mạng (đóng-mở gói) | T12 B4 · 12CS B22–24 | SUPPORTED | **SUPPORTED_TRACE** | protocol_encapsulation TRACE_PLAYBACK: đóng/mở gói từng tầng, parity 2D↔3D đã đo trong trình duyệt; KHÔNG có thao tác tự do lên PDU |
| `html_css` | HTML/CSS (quan hệ markup ↔ hiển thị) | T12 CĐ4 | PARTIAL | **SUPPORTED_BOUNDED_ARTIFACT** | web.style_model: sửa thuộc tính trong MIỀN ĐÓNG (hợp đồng FE≡BE có sync-lock); KHÔNG có đường viết CSS tự do |
| `arrays_1d_2d` | Mảng 1D/2D (chỉ số ↔ giá trị) | T11CS B17 | PARTIAL | **PARTIAL** | 1D ngầm trong trace của mọi bài dãy; 2D chưa có target nào |
| `database_table_query` | CSDL: bảng, bản ghi, truy vấn | T11 CĐ4 | PARTIAL | **PARTIAL** | relational_table_query có timeline nhưng chưa có bài mẫu offline; pipeline nhiều tầng bằng NL vẫn PARTIAL |
| `loops_branch_variable` | Lặp / rẽ nhánh / biến | T10 B17–21 | PARTIAL | **PARTIAL** | bounded_control_flow có timeline nhưng CHƯA có bài mẫu offline ⇒ chưa có bằng chứng trình duyệt; không predict, không explore |
| `practice_activity` | Học sinh tự dựng/thao tác, engine kiểm được | cross | PARTIAL | **PARTIAL** | substrate đã có (predict.check + explore/apply) nhưng chưa phải một mode học tập đầy đủ |
| `text_media_encoding` | Mã hoá văn bản/âm thanh/ảnh | T10 B3, B6 | PARTIAL | **PARTIAL** | character_encoding có timeline nhưng chưa có bài mẫu offline; ảnh/âm thanh và dãy byte UTF-8 ngoài phạm vi |
| `dijkstra_weighted_shortest_path` | Đường đi ngắn nhất CÓ TRỌNG SỐ (Dijkstra) | không có anchor SGK | CAPABILITY_GAP | **UNSUPPORTED** | COVERAGE §7b — capability_gap là câu trả lời đúng, không phải thiếu sót cần vá |
| `os_process_fsm` | Hệ điều hành: tiến trình (máy trạng thái) | T11 B1–2 | CAPABILITY_GAP | **UNSUPPORTED** | chưa có engine FSM nào sở hữu cơ chế này |
| `ai_ml_datascience_overview` | Tổng quan AI / Học máy / KHDL | T12 CĐ1 · 12CS CĐ7 | OUT_OF_SCOPE | **NOT_SIMULATION_SUITABLE** | 'mạng nơ-ron 3D xoay' là mô phỏng trang trí kinh điển |
| `career_orientation` | Hướng nghiệp | mọi khối | OUT_OF_SCOPE | **NOT_SIMULATION_SUITABLE** | không có cơ chế ẩn động |
| `cloud_email_social` | Lưu trữ đám mây, email, mạng xã hội | T11 B6–8 | OUT_OF_SCOPE | **NOT_SIMULATION_SUITABLE** | thao tác công cụ, không phải cơ chế |
| `digital_ethics_law_culture` | Đạo đức/pháp luật/văn hoá số, bản quyền | CĐ3 (mọi khối) | OUT_OF_SCOPE | **NOT_SIMULATION_SUITABLE** | không có cơ chế ẩn động để thao tác |
| `hardware_network_lookup` | Bên trong máy tính / thiết bị mạng | T11 B4 · T12 B3 | OUT_OF_SCOPE | **NOT_SIMULATION_SUITABLE** | sự kiện tra cứu |
| `info_concepts_devices` | Thông tin & xử lí thông tin; thiết bị số | T10 B1–2, B7 | OUT_OF_SCOPE | **NOT_SIMULATION_SUITABLE** | khái niệm — hình tĩnh có chú thích tốt hơn |
| `software_skills` | Kĩ năng phần mềm (đồ hoạ/ảnh/video) | T10 CĐ4 · T11-ICT CĐ7 | OUT_OF_SCOPE | **NOT_SIMULATION_SUITABLE** | chính phần mềm đó mới là 'mô phỏng' |
