# RENDERER_FIT_MATRIX — W4B-2A baseline

Đo trên Chrome thật, zoom 100%, 1920×1080, checkpoint có hình vẽ lớn nhất.
`visual` = phần tử vẽ **có diện tích lớn nhất** trong `.sim-stage` (svg hoặc
canvas) — không phải khung sân khấu.

## 1. Tỉ lệ hình vẽ / sân khấu (Observation MỞ)

| Target | Sân khấu | Hình vẽ | Chiếm | Bỏ trống ngang |
|---|---|---|---:|---:|
| `database.relational_table_query` | 1306×273 | 12×12 | **1%** | 1294 |
| `binary.decimal_to_binary` | 1306×182 | 276×150 | **21%** | 1030 |
| `algorithm.scan` | 1306×268 | 364×268 | **28%** | 942 |
| `algorithm.selection_sort` | 1306×286 | 364×268 | **28%** | 942 |
| `network.graph_traversal` | 1306×474 | 420×260 | **32%** | 886 |
| `algorithm.insertion_sort` | 1306×344 | 434×268 | **33%** | 872 |
| `logic.and_gate` | 1306×240 | 460×240 | 35% | 846 |
| `algorithm.bubble_sort` | 1306×286 | 504×268 | **39%** | 802 |
| `algorithm.find_min` | 1306×286 | 504×268 | 39% | 802 |
| `algorithm.bounded_control_flow` | 1306×290 | 560×96 | 43% | 746 |
| `algorithm.find_max` | 1306×286 | 574×268 | 44% | 732 |
| `algorithm.linear_search` | 1306×286 | 574×268 | 44% | 732 |
| `generic.rule_scene` | 1306×269 | 600×269 | 46% | 706 |
| `tree.traversal` | 1306×470 | 602×274 | 46% | 704 |
| `network.packet_routing` | 1306×180 | 610×140 | 47% | 696 |
| `algorithm.sum_if` | 1306×286 | 644×268 | 49% | 662 |
| `logic.boolean_dag` | 1306×309 | 662×246 | 51% | 644 |
| `algorithm.binary_search` | 1306×286 | 714×268 | 55% | 592 |
| `algorithm.count_if` | 1306×286 | 714×268 | 55% | 592 |

Không renderer nào vượt **55%** bề rộng sân khấu.

## 2. Phép thử quyết định — đóng panel Quan sát

Đóng Quan sát cấp thêm **+316px** bề rộng sân khấu. Câu hỏi: hình vẽ có lớn theo
không, hay chỉ đẻ thêm khoảng trắng?

| | |
|---|---|
| Target đo được | **19** |
| Sân khấu rộng thêm | **+316px, cả 19** |
| Hình vẽ rộng thêm | **+0px, cả 19** |
| Phản ứng theo bề rộng | **0 / 19** |

**Không một renderer nào phản ứng.** Đây là bằng chứng trực tiếp cho hợp đồng
`ADAPTIVE_LAYOUT` bị vi phạm toàn danh mục: mọi SVG khoá `maxWidth` bằng đúng bề
rộng `viewBox` nội tại, nên toàn bộ 316px vừa cấp thành khoảng trắng.

Nó cũng xác nhận điều §9 lo: **đóng Quan sát hiện chỉ tạo thêm white space**,
không làm mô phỏng lớn hơn một pixel nào.

## 3. Phân loại (từ số đo, chưa phải kết luận cuối)

| Lớp | Target | Căn cứ |
|---|---|---|
| `ADAPTIVE_LAYOUT` — cần sửa | 9 target họ algorithm (ArrayView) · `tree.traversal` · `logic.boolean_dag` · `network.graph_traversal` · `network.packet_routing` · `generic.rule_scene` | bố cục tính được lại từ bounds; hiện khoá cứng |
| `FIXED_SEMANTIC_SIZE` — ứng viên | `logic.and_gate` · `binary.decimal_to_binary` · `algorithm.bounded_control_flow` | phóng to không tăng giá trị nhận thức; nên xử lý **mật độ sân khấu**, không phóng hình |
| `CANVAS_FILL` | `network.packet_routing` (3D) · `network.protocol_encapsulation` (3D) | **chưa đo** — fixture danh mục mặc định `visual_mode: 2d` |

## 4. Giới hạn của chính phép đo này

- **`database.relational_table_query` đo ra 12×12** vì bảng dữ liệu là **HTML,
  không phải SVG/canvas**. Phép đo "phần tử vẽ lớn nhất" **không áp dụng** cho
  renderer dạng bảng — cần một phép đo riêng, không được kết luận nó chiếm 1%.
- **Hai target 3D chưa được đo ở chế độ 3D.** Cần một lượt bật `visual_mode`
  trước khi phân lớp `CANVAS_FILL`.
- Chiều cao chưa phân tích — cột `stage_h` thay đổi theo target (180…474px), nên
  tỉ lệ chiều cao cần đọc cùng lớp renderer, không so phẳng.
- Đây là **baseline TRƯỚC** mọi thay đổi. Chưa có AFTER.
