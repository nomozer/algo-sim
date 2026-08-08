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

**Không một renderer nào phản ứng.**

⚠️ **Đọc con số này theo LỚP renderer, không kết luận cả 19 đều hỏng.** Phản ứng
0px chỉ là **khiếm khuyết** với lớp `ADAPTIVE_LAYOUT` khi chưa chạm trần ngữ
nghĩa. Với `FIXED_SEMANTIC_SIZE` thì 0px có thể là **chủ đích** — ở đó phải xét
riêng phần sân khấu bỏ trống, không xét bề rộng hình vẽ.

Cái chung cho mọi lớp: mọi SVG đang khoá `maxWidth` bằng đúng bề rộng `viewBox`
nội tại, và bề rộng nội tại đó **không hề là hàm của khung chứa** — nên không
renderer nào có cơ hội phản ứng, kể cả những cái đáng lẽ phải phản ứng.

Nó cũng xác nhận điều §9 lo: **đóng Quan sát hiện chỉ tạo thêm white space**.

## 2b. SAU khi sửa `ArrayView` (AFTER)

| Target | Hình vẽ TRƯỚC | SAU | Chênh |
|---|---:|---:|---:|
| `algorithm.binary_search` | 714 | **1224** | +510 |
| `algorithm.count_if` | 714 | **1224** | +510 |
| `algorithm.sum_if` | 644 | **1104** | +460 |
| `algorithm.find_max` | 574 | **984** | +410 |
| `algorithm.linear_search` | 574 | **984** | +410 |
| `algorithm.bubble_sort` | **504** | **864** | **+360** |
| `algorithm.find_min` | 504 | **864** | +360 |
| `algorithm.insertion_sort` | 434 | **744** | +310 |
| `algorithm.scan` | 364 | **624** | +260 |
| `algorithm.selection_sort` | 364 | **624** | +260 |

**10/10 target `ArrayView` cải thiện.** Chín target ngoài họ `ArrayView` đo lại
đều **+0px** — không có blast radius ngoài ý muốn.

`bubble_sort` — đúng mẫu ảnh người dùng gửi — từ **504px → 864px** trong sân
khấu 1306px.

**Đóng Quan sát vẫn +0px sau bản vá, và đó là PASS chứ không phải FAIL:** với 7
cột, bố cục đã **chạm trần ngữ nghĩa** (`colW = 96`) ngay ở 1306px, nên 316px
thêm vào thành lề căn giữa có chủ đích. Đây là `SEMANTIC_MAX_REACHED` theo §11.
Bằng chứng tính thích ứng nằm ở test đơn vị (620px → 900px thì bố cục lớn theo)
cộng với chênh lệch trước–sau ở trên.

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
