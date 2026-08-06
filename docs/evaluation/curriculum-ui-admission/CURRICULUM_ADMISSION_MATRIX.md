# CURRICULUM_ADMISSION_MATRIX — 22 target so với chương trình Tin học THPT

Nguồn và mức tin cậy: [CURRICULUM_SOURCE_LOG.md](CURRICULUM_SOURCE_LOG.md).
Catalog **đóng băng ở 11 family / 22 target** — bảng này **không đề xuất thêm hay
bớt target**, chỉ xếp loại để biết **ưu tiên công sức vào đâu**.

## 0. Bốn nhãn

| Nhãn | Nghĩa | Hệ quả |
|---|---|---|
| **CỐT LÕI** | Nội dung phần chung, mọi học sinh THPT đều học | Ưu tiên cao nhất |
| **ĐỊNH HƯỚNG** | Thuộc một định hướng (KHMT hoặc ICT), không phải mọi học sinh | Ưu tiên vừa |
| **CHUYÊN ĐỀ** | Chỉ có ở chuyên đề học tập lớp 12 KHMT | Ưu tiên thấp về mặt phủ chương trình |
| **CÔNG CỤ** | Không phải một nội dung trong chương trình; là hạ tầng của hệ thống | Không xếp hạng theo chương trình |

## 1. Bảng chính

| # | Target | Nội dung chương trình tương ứng | Lớp / định hướng | Nhãn | Nguồn | Ghi chú |
|---|---|---|---|---|---|---|
| 1 | `algorithm.bounded_control_flow` | cấu trúc lặp `for`/`while`, số lần lặp | 10, phần chung | **CỐT LÕI** | S1 | Nội dung lập trình nền, mọi học sinh |
| 2 | `algorithm.scan` | duyệt tuần tự một dãy | 10, phần chung | **CỐT LÕI** | S1 | Khung của mọi bài lặp trên dãy |
| 3 | `algorithm.find_max` | tìm giá trị lớn nhất trong dãy | 10, phần chung | **CỐT LÕI** | S1 | Bài tập lặp kinh điển lớp 10 |
| 4 | `algorithm.find_min` | tìm giá trị nhỏ nhất | 10, phần chung | **CỐT LÕI** | S1 | như trên |
| 5 | `algorithm.count_if` | đếm phần tử thoả điều kiện | 10, phần chung | **CỐT LÕI** | S1 | lặp + rẽ nhánh |
| 6 | `algorithm.sum_if` | tính tổng có điều kiện | 10, phần chung | **CỐT LÕI** | S1 | lặp + rẽ nhánh + biến tích luỹ |
| 7 | `algorithm.linear_search` | tìm kiếm tuần tự | 11 KHMT | **ĐỊNH HƯỚNG** | S4 | KNTT Bài 19 |
| 8 | `algorithm.binary_search` | tìm kiếm nhị phân | 11 KHMT | **ĐỊNH HƯỚNG** | S4 | KNTT Bài 19 |
| 9 | `algorithm.bubble_sort` | sắp xếp nổi bọt | 11 KHMT | **ĐỊNH HƯỚNG** | S5 | KNTT Bài 21 |
| 10 | `algorithm.selection_sort` | sắp xếp chọn | 11 KHMT | **ĐỊNH HƯỚNG** | S5 | KNTT Bài 21 |
| 11 | `algorithm.insertion_sort` | sắp xếp chèn | 11 KHMT | **ĐỊNH HƯỚNG** | S5 | KNTT Bài 21 |
| 12 | `binary.decimal_to_binary` | đổi thập phân → nhị phân | 10, phần chung | **CỐT LÕI** | S2 | KNTT Bài 3 |
| 13 | `binary.base_conversion` | chuyển đổi giữa các hệ đếm | 10, phần chung | **CỐT LÕI** | S2 | mở rộng của #12 |
| 14 | `binary.character_encoding` | mã ASCII / Unicode | 10, phần chung | **CỐT LÕI** | S2 | KNTT Bài 3 |
| 15 | `logic.and_gate` | cổng logic, bảng chân lý | 11, **phần chung cả hai định hướng** | **CỐT LÕI** | S3 | KNTT Bài 4 / Cánh diều Bài 1 |
| 16 | `logic.boolean_dag` | mạch logic nhiều cổng nối tiếp | 11, **phần chung** | **CỐT LÕI** | S3 | mở rộng trực tiếp của #15 |
| 17 | `database.relational_table_query` | CSDL quan hệ, truy vấn SQL | 11 (ICT là chính) | **ĐỊNH HƯỚNG** | S6 | KNTT Bài 14 |
| 18 | `network.protocol_encapsulation` | phân tầng TCP/IP, đóng gói dữ liệu | 12, phần chung | **CỐT LÕI** | S7 | KNTT Bài 4 |
| 19 | `network.packet_routing` | định tuyến gói tin trong mạng | 12, phần chung | **CỐT LÕI** | S7 | mức "hiểu ý tưởng", không phải giải thuật định tuyến |
| 20 | `network.graph_traversal` | duyệt đồ thị BFS/DFS | **chuyên đề 12 KHMT** | **CHUYÊN ĐỀ** | S8 | không phải nội dung đại trà |
| 21 | `tree.traversal` | cây và phép duyệt cây | **chuyên đề 12 KHMT** | **CHUYÊN ĐỀ** | S8 | không phải nội dung đại trà |
| 22 | `generic.rule_scene` | — (khung diễn hoạt theo luật, dùng cho đề không rơi vào domain nào) | — | **CÔNG CỤ** | — | hạ tầng fallback, không xếp theo chương trình |

## 2. Tổng hợp

| Nhãn | Số target | Danh sách |
|---|---|---|
| **CỐT LÕI** | **13** | 1–6 (6) · 12–16 (5) · 18–19 (2) |
| **ĐỊNH HƯỚNG** | **6** | 7–11 (5) · 17 (1) |
| **CHUYÊN ĐỀ** | **2** | 20, 21 |
| **CÔNG CỤ** | **1** | 22 |
| | **22** | khớp catalog đóng băng |

## 3. Ba kết luận rút ra được

1. **Không target nào nằm ngoài chương trình.** 21/22 ánh xạ được vào một nội dung
   cụ thể; cái còn lại (`generic.rule_scene`) là hạ tầng, không phải nội dung dạy.

2. **Trọng tâm hiện tại lệch về nhóm ĐỊNH HƯỚNG và CHUYÊN ĐỀ so với công sức bỏ ra.**
   Các đợt trước đã đầu tư nặng vào `insertion_sort`, `selection_sort` (ĐỊNH HƯỚNG)
   và `graph_traversal`, `tree.traversal` (CHUYÊN ĐỀ — chỉ học sinh chuyên đề KHMT
   mới học). Trong khi đó `logic.*` và `binary.*` — nhóm **mọi học sinh đều học** —
   chưa nhận được đợt cải tiến trực quan nào.

3. **Vì vậy ưu tiên BFS bị hạ xuống.** Yêu cầu của bạn nói rõ: *"Ưu tiên BFS chỉ khi
   audit chương trình xác nhận BFS hoặc queue có vai trò phù hợp."* Audit xác nhận
   BFS/queue **có** trong chương trình, nhưng **chỉ ở chuyên đề học tập lớp 12 KHMT**
   — tức nhóm học sinh hẹp nhất trong ba nhóm. Điều kiện "vai trò phù hợp" để được
   **ưu tiên** không đạt. BFS không được chọn làm pilot.
