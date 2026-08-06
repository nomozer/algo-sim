# SIMULATION_QUALITY_MATRIX — bản ngắn

Lượt READ-ONLY tại `main @ cc449d5`. Catalog **11 family / 22 target**
(nguồn: `backend/scripts/catalog_runtime_matrix.py`, hash `4d7c8e65…`).
Chi tiết + bằng chứng ảnh: `simulation_mechanism_quality_audit.md`.

**A** = cơ chế nhân–quả nhìn thấy trên sân khấu ·
**B** = engine/timeline thật nhưng cơ chế chủ yếu qua code/bảng/chữ ·
**C** = chỉ mở dần nội dung · **D** = minh hoạ/không rõ.

| Target | A/B/C/D | Cơ chế ĐÃ nhìn thấy | Cơ chế còn ẨN | Hướng xử lý |
|---|---|---|---|---|
| `algorithm.find_max` | **A** | vùng đã duyệt xám · phần tử hiện tại · max hiện giữ · biểu thức so sánh · dự đoán | — | giữ nguyên |
| `algorithm.find_min` | **A** | như trên (đối xứng) | — | giữ nguyên |
| `algorithm.count_if` | **A** | phần tử thoả (xanh) vs loại (xám) · biến đếm · điều kiện đang xét | — | giữ nguyên |
| `algorithm.sum_if` | **A** | như count_if, tích luỹ tổng | — | giữ nguyên |
| `algorithm.binary_search` | **A** | nửa bị loại (xám) · vùng còn lại · phần tử giữa · quyết định loại nửa nào | — | giữ nguyên |
| `algorithm.linear_search` | **A−** | phần tử hiện tại · so sánh với khoá · vùng đã qua | không có "vùng còn lại" rõ như binary_search | chỉnh nhẹ |
| `algorithm.bubble_sort` | **A−** | cặp kề đang so sánh · đuôi đã ổn định (xanh) · what-if kéo thả | **hành động đổi chỗ** chỉ suy ra từ hai trạng thái, không được diễn ra | chỉnh nhẹ: diễn tả bước đổi chỗ |
| `algorithm.selection_sort` | **A−** | phần tử đang xét · nhỏ nhất đang giữ · vùng đã sắp | ranh giới "đã chọn xong" mờ hơn bubble | chỉnh nhẹ |
| `algorithm.scan` | **A−** | như find_max (cùng renderer) | không có ô dự đoán | chỉnh nhẹ |
| `algorithm.insertion_sort` | **B+** | cặp đang so · vùng đã sắp (xanh) | **giá trị đang cầm (4) KHÔNG có trên sân khấu**; ô trống hiện thành **số 7 lặp lại** | **thiết kế lại**: vẽ giá trị đang cầm + ô trống |
| `algorithm.bounded_control_flow` | **B−** | dòng mã giả hiện tại · điều kiện ĐÚNG/SAI · lượt lặp (chữ) | **toàn bộ vòng lặp**: quỹ đạo biến, biên dừng, cạnh quay lại, tích luỹ | **thiết kế lại sân khấu** |
| `binary.decimal_to_binary` | **A−** | trọng số vị trí · đóng góp từng bit · tổng | quy trình **đổi** 13 → 1101 (chia lấy dư) không có; sân khấu là mô hình trọng số | chỉnh nhẹ: nói rõ đang dạy trọng số |
| `binary.base_conversion` | **A−** | bảng chia · thương · số dư · dãy chữ số · đọc ngược | **không đánh dấu hàng đang tính** | chỉnh nhẹ: tô hàng hiện tại |
| `binary.character_encoding` | **A−** | ký tự → code point → thập phân → bảng chia (có tô hàng hiện tại) → đọc ngược | mũi tên/hình cho "đọc ngược" vẫn là chữ | chỉnh nhẹ |
| `database.relational_table_query` | **A−** | trạng thái từng dòng (Giữ/Loại/Đang xét) · chuỗi 5 tầng pipeline | tầng đang chạy không nổi bật trong dải chip | chỉnh nhẹ |
| `logic.and_gate` | **A−** | công tắc · dây · cổng AND · đèn ra · bảng chân trị | không chú giải màu | chỉnh nhẹ |
| `logic.boolean_dag` | **A−** | sơ đồ node-edge · lan truyền tín hiệu · cổng đang tính · `?` cho cổng chưa tới lượt · đầu vào bấm được | **không chú giải màu**; xanh lá mang HAI nghĩa | chỉnh nhẹ: thêm chú giải |
| `network.protocol_encapsulation` | **A−** | chồng tầng hai đầu · PDU thêm/gỡ từng phần · 2D↔3D cùng state | chiều truyền chỉ ngụ ý | giữ nguyên |
| `network.packet_routing` | **B+** | vị trí gói tin · dự đoán chặng kế tiếp | **đoạn đã đi vs còn lại không phân biệt**; không có hướng | chỉnh nhẹ |
| `tree.traversal` | **B+** | cây · nhãn trái/phải · node hiện tại · **cạnh đang đi được tô** | **ngăn xếp chỉ là dòng chữ** — đúng thứ quyết định thứ tự duyệt | **thiết kế lại**: vẽ ngăn xếp |
| `network.graph_traversal` | **B** | đồ thị · màu node đổi theo trạng thái | **hàng đợi chỉ là dòng chữ**; **không cạnh nào được tô** | **thiết kế lại**: vẽ hàng đợi + cạnh đang đi |
| `generic.rule_scene` | **C** | đối tượng + giá trị đổi khi bấm | không vẽ quan hệ nhân–quả (không dây, không cổng) | giữ nguyên — family này khai `representation` |

**Tổng: A 16 · B 5 · C 1 · D 0.**

Ba lỗi trình bày đáng ghi (không sửa trong lượt này):
`OBVIOUS_PRESENTATION_CORRECTNESS_RISK` — insertion_sort (số lặp + dữ liệu biến
mất) · tree.traversal (cạnh tô không khớp câu thuyết minh) · toàn catalog (một
màu, nhiều nghĩa, không chú giải).
