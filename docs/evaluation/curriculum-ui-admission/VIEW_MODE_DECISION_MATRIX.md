# VIEW_MODE_DECISION_MATRIX — target nào nên 2D, target nào đáng 3D

## 0. Tiêu chí quyết định (áp cho cả 22)

Một target **đáng 3D** khi và chỉ khi cơ chế cần dạy có **chiều thứ ba mang nghĩa**.
Nếu chiều thứ ba chỉ để đẹp, nó **lấy mất** độ chính xác đọc vị trí mà 2D đang có.

| Mã | Câu hỏi | Nếu "không" |
|---|---|---|
| C1 | Cơ chế có đại lượng nào **không xếp được** lên một trục? | 2D đủ |
| C2 | Có **quan hệ bao chứa / phân tầng** cần nhìn thấy đồng thời? | 2D đủ |
| C3 | Có **chuyển động trong không gian** là bản thân nội dung? | 2D đủ |
| C4 | 3D có làm **mất** khả năng so sánh chính xác hai giá trị? | nếu "có" → 2D |

Ràng buộc kiến trúc: **bất biến #16** — 2D và 3D dùng chung module/config/state/
timeline; **bất biến #18** — `threeD.role` chỉ nhận `architectural_poc` hoặc
`pedagogical`. Đổi chế độ **không** được làm gián đoạn timeline.

## 1. Bảng quyết định

| Target | C1 | C2 | C3 | C4 | Quyết định | Lý do một câu |
|---|:-:|:-:|:-:|:-:|---|---|
| `algorithm.scan` | – | – | – | ✓ | **2D** | Dãy số là một trục; 3D phá khả năng so sánh chiều cao cột |
| `algorithm.find_max` | – | – | – | ✓ | **2D** | như trên |
| `algorithm.find_min` | – | – | – | ✓ | **2D** | như trên |
| `algorithm.count_if` | – | – | – | ✓ | **2D** | như trên |
| `algorithm.sum_if` | – | – | – | ✓ | **2D** | như trên |
| `algorithm.linear_search` | – | – | – | ✓ | **2D** | như trên |
| `algorithm.binary_search` | – | – | – | ✓ | **2D** | Nghĩa nằm ở **thu hẹp đoạn**, thuần một trục |
| `algorithm.bubble_sort` | – | – | – | ✓ | **2D** | So sánh chiều cao là toàn bộ nội dung |
| `algorithm.selection_sort` | – | – | – | ✓ | **2D** | như trên |
| `algorithm.insertion_sort` | – | – | – | ✓ | **2D** | "Chỗ trống" + "phần tử đang giữ" là quan hệ trong một hàng |
| `algorithm.bounded_control_flow` | – | – | – | – | **2D** | Vòng lặp là chu kỳ, đã vẽ bằng trục + chặng |
| `binary.decimal_to_binary` | – | – | – | ✓ | **2D** | Chuỗi bit theo vị trí, một trục |
| `binary.base_conversion` | – | – | – | ✓ | **2D** | Bảng đối chiếu — 3D vô nghĩa |
| `binary.character_encoding` | – | – | – | ✓ | **2D** | Bảng mã — 3D vô nghĩa |
| `logic.and_gate` | – | – | – | – | **2D** | Mạch phẳng theo quy ước sơ đồ mạch |
| `logic.boolean_dag` | – | – | – | – | **2D** | Sơ đồ mạch là quy ước **phẳng** trong SGK; 3D làm sai quy ước |
| `database.relational_table_query` | – | – | – | ✓ | **2D** | Bảng quan hệ |
| `generic.rule_scene` | – | – | – | – | **2D** | Khung fallback, không có hình học riêng |
| `tree.traversal` | – | ✓ | – | ✓ | **2D** | Cây có phân cấp nhưng vẽ phẳng là quy ước chuẩn |
| `network.graph_traversal` | – | – | – | ✓ | **2D** | Đồ thị phẳng đọc chính xác hơn |
| **`network.protocol_encapsulation`** | – | **✓** | – | – | **3D — `pedagogical`** | **Đóng gói = bao chứa lồng nhau**; 3D cho thấy header bọc payload theo tầng |
| **`network.packet_routing`** | – | – | **✓** | – | **3D — `architectural_poc`** | Gói tin **di chuyển qua nút mạng** — chuyển động là nội dung |

## 2. Kết quả

| Chế độ | Số target | Danh sách |
|---|---:|---|
| **2D duy nhất** | **20** | tất cả trừ hai dòng cuối |
| **3D `pedagogical`** | **1** | `network.protocol_encapsulation` |
| **3D `architectural_poc`** | **1** | `network.packet_routing` |

Trạng thái hiện tại đã khớp: đo trong Chrome, **đúng 2 target có nút chuyển 2D/3D**
(`mode_buttons = "2D,3D"`), 20 target còn lại không có. **Không đề xuất thêm 3D
cho target nào.**

## 3. Điều đã kiểm chứng, và điều chưa

**Đã kiểm trong Chrome thật** (đợt trước, giữ nguyên kết luận): chuyển 2D → 3D → 2D
trên `packet_routing` và `protocol_encapsulation` **không** làm nhảy cursor
(`state_continuous = true`) — bất biến #16 đứng vững.

**Chưa kiểm chứng:** liệu 3D có **giúp học sinh hiểu đóng gói tốt hơn 2D** hay không.
Không có dữ liệu học sinh. Bảng trên là lập luận **thiết kế**, không phải bằng chứng
**sư phạm** — không được trích dẫn như bằng chứng hiệu quả học tập.
