# RENDERER_FIT_MATRIX — W4B-2A

## 0a. Bốn hàng còn lại — phân loại từ MÃ NGUỒN, không từ tỉ lệ

Giả thuyết vào lượt này là ba trong bốn hàng đều `TRUE_ADAPTIVE_FIT_FAILURE`.
Đọc chủ sở hữu bố cục thì **không hàng nào giống ca `graph_traversal`**.

`graph_traversal` có `const W = 420` — một hằng số **bất kể đồ thị có mấy nút**.
Đó là lối tắt cài đặt, và sửa nó là đúng. Bốn hàng còn lại thì ngược lại: bề
rộng của chúng **đã dẫn xuất từ nội dung**.

| Hàng | Chủ sở hữu bề rộng | Bề rộng tính từ | Phân loại |
|---|---|---|---|
| `logic.boolean_dag` | `layoutDag` | `(maxDepth+1)·NODE_W + maxDepth·COL_GAP` — **topology** | **B** |
| `tree.traversal` | `layoutSize` | `max(360, số_nút · SLOT_W)`, `SLOT_W = 86` — **bề rộng nhãn** | **B** |
| `network.packet_routing` / 2d | `layout2d` | `X0·2 + (cols−1)·COL` — **độ dài tuyến** | **B** |
| `generic.rule_scene` | `layoutPositions` | toạ độ do **spec DSL** sinh | **B** |

Bằng chứng cho từng cái:

- **`tree.traversal`** — `SLOT_W = 86` không phải số tuỳ tiện: comment tại chỗ
  ghi đây là bản sửa hồi quy **M17-VR1**, khung cố định 460×300 chỉ đủ nhãn 1–2
  ký tự nên tên tiếng Việt dài ("Trăng Khuyết", "Sương Mai") tràn khỏi nút và
  chồng nhau. Mỗi nút nay được cấp **một làn đủ rộng cho nhãn ~12 ký tự**. Nới
  làn rộng hơn nữa **không thêm chỗ cho nhãn** — chỉ tăng quãng mắt phải đi giữa
  hai nút anh em.
- **`logic.boolean_dag`** — bề rộng là `số tầng × bề rộng cổng + khe`. Nới khe
  giữa các tầng làm **dây tín hiệu dài ra**, không làm đường lan truyền dễ đọc
  hơn; cổng đã đủ rộng cho nhãn.
- **`packet_routing` 2D** — `COL = 150` cho mỗi chặng. Nới ra chỉ kéo dài liên
  kết giữa hai thiết bị.
- **`generic.rule_scene`** — toạ độ đến **từ spec do LLM soạn và validator
  duyệt**. Đổi tỉ lệ toạ độ là **đổi nghĩa cảnh**, đúng thứ §6 cảnh báo. Không
  đụng.

### Vì sao dừng ở đây thay vì chọn một owner

`§11` yêu cầu: xếp hạng mơ hồ thì **DỪNG và báo**. Sau khi đọc mã, số hàng thuộc
`TRUE_ADAPTIVE_FIT_FAILURE` là **0** — không có ứng viên nào để xếp hạng.

Tỉ lệ 0.46–0.51 của chúng **không** cùng bản chất với 0.32 của `graph_traversal`.
Cùng một con số thấp đến từ hai nguyên nhân khác hẳn: một bên là hằng số bỏ quên,
một bên là hệ toạ độ ngữ nghĩa đã cấp đủ chỗ cho thứ cần đọc. Sửa nhóm sau bằng
cách nới bố cục sẽ là **tối ưu cho một tỉ lệ**, đúng thứ `§5` của lượt trước cấm.

### Soát thị giác ca biên (A0) — nhãn B giữ nguyên, nhưng lộ ra một vấn đề KHÁC

Ảnh 1920×1080 cho thấy thứ mà hình học không nói được.

**Renderer thì đọc tốt.** `tree.traversal` 7 nút: nút rõ, cạnh có nhãn
*trái/phải*, nút hiện tại cam, đã thăm xanh, ngăn xếp LIFO ngay dưới sân khấu.
`logic.boolean_dag`: cổng có nhãn, dây tín hiệu xanh khi mang giá trị 1, cổng
đang tính viền đậm, đầu ra nét đứt = *chưa tới lượt*. Không cái nào cần rộng
hơn — nới ra chỉ kéo dài dây và tăng quãng mắt. **Nhãn `B` được xác nhận.**

**Nhưng cả hai đều để lại một dải trống lớn DƯỚI thẻ**: ~230px với cây, ~350px
với DAG, cộng panel bên phải gần như rỗng (2–3 dòng chữ trong một cột cao). Ở
1920×1080, nhánh `max-height: 900px` của W4B-1A **không** áp dụng, nên bố cục là
một-màn cố định `height: calc(100vh − 57px)` với `.panel-center` cuộn trong —
nội dung ngắn thì phần còn lại của cột là khoảng trống.

Đó **không phải** lỗi renderer. Đó là **`C — STAGE_OR_CONTAINER_DENSITY_ISSUE`**,
và nó **dùng chung**: mọi target có nội dung ngắn đều dính, không riêng bốn hàng
này. Đúng triệu chứng §4 mô tả — "sân khấu dư thừa làm thứ bậc thị giác yếu đi".

**Hệ quả cho cổng A0**: theo `§13`, còn một hàng `C` chưa xử lý thì Phase A0
**chưa** đóng, và `§15` không cho Phase B bắt đầu. Việc cần làm là chỉnh **mật độ
container**, không nới renderer — và vì nó dùng chung nên phải sửa ở một chỗ, đo
lại, chứ không vá từng target.

### Điều lượt này CHƯA kết luận

Nhãn **B** ở trên dựa trên **mã nguồn + hình học đã đo**, chưa dựa trên soát thị
giác từng ca biên: cây 3 nút trong sân khấu 1306px, hay DAG 2 tầng, có thể vẫn
đọc ra như một hòn đảo nhỏ. Nếu có ca như vậy thì nó thuộc **C —
`STAGE_OR_CONTAINER_DENSITY_ISSUE`** (vấn đề mật độ sân khấu, xử lý ở container)
chứ không phải nới bố cục renderer. Đó là phép đo còn thiếu, đã ghi ở đây thay
vì để trống.

---

## 0. Ba phép đo đặc biệt — độ phủ đạt 22/22

Ba ca này trước đây **không đo được** bằng phép "phần tử vẽ lớn nhất": bảng
không phải SVG, và hai target 3D mặc định mở ở chế độ 2D.

| Target / chế độ | Thẻ đo | Sân khấu | Hình vẽ | Tỉ lệ | Lớp |
|---|---|---|---|---:|---|
| `database.relational_table_query` / 2d | `table` | 1306×273 | **1306×273** | **1.00** | hợp đồng BẢNG |
| `network.packet_routing` / **3d** | `canvas` | 1306×340 | **1306×340** | **1.00** | `CANVAS_FILL` ✓ |
| `network.protocol_encapsulation` / **3d** | `canvas` | 1306×340 | **1306×340** | **1.00** | `CANVAS_FILL` ✓ |

**Bảng chưa bao giờ thiếu hụt.** Nó khai `width: 100%` trong `.sim-stage` nên
vốn bám khung theo CSS — con số 12×12 ở baseline là phép đo bắt nhầm một icon,
**lỗi của dụng cụ đo, không phải của renderer**. Hợp đồng của nó là riêng: không
so tỉ lệ với renderer SVG như thể hai thứ cùng nghĩa.

**Hai canvas 3D bám trọn sân khấu**, thoả `CANVAS_FILL`. Lưu ý ranh giới: canvas
đầy khung **không** đồng nghĩa với "3D tốt cho học tập" — kích thước vật thể bên
trong canvas là câu hỏi khác, và `threeD.role` của `packet_routing` vẫn là
`architectural_poc`, không đổi trong milestone này.

Độ phủ nay tách làm hai phát biểu:

- **Độ phủ nạp danh mục**: 22/22 target nạp được qua runner.
- **Độ phủ đo vừa-khung**: **22/22 target** đã có ít nhất một phép đo hợp lệ.
- **Số hàng target × chế độ**: 24 (hai target mạng có thêm hàng 3D).

Không được rút gọn thành *"22/22 renderer đều adaptive"* — mỗi hàng giữ lớp
riêng: `ADAPTIVE_LAYOUT` · `CANVAS_FILL` · `FIXED_SEMANTIC_SIZE`.

---

# Baseline ban đầu

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
cột, bố cục đã **chạm trần ngữ nghĩa** ngay ở 1306px, nên 316px thêm vào thành
lề căn giữa có chủ đích. Đây là `SEMANTIC_MAX_REACHED` theo §11. Bằng chứng tính
thích ứng nằm ở test đơn vị (620px → 900px thì bố cục lớn theo) cộng với chênh
lệch trước–sau ở trên.

## 2c. HIỆU CHỈNH MẬT ĐỘ — trần 96px là VƯỢT MỨC

Soát trình duyệt cho thấy trần đầu tiên làm cột quá lớn và bố cục mất cân đối.
Một renderer hỏng được theo **hai** hướng, và "chiếm nhiều sân khấu nhất" **không
phải** là tiêu chí thành công.

Bốn ứng viên, đo trong Chrome @1920×1080 (sân khấu 1306px):

| Trần cột | 7 cột (`bubble_sort`) | 8 cột (`find_max`) | Nhận xét |
|---:|---:|---:|---|
| 96 | 864 | 984 | **vượt mức** — cặp đang so sánh cách nhau quá xa |
| **76** | **684** | **779** | **CHỌN** |
| 68 | 612 | 697 | còn dè dặt |
| 60 | 540 | 615 | gần như quay lại bản hằng số cũ (504) |

Chọn **76** vì nó giữ khoảng cách tâm-đến-tâm hai cột kề nhau **dưới 100px** —
mắt bắt được cả cặp trong một lần nhìn, mà vẫn hơn hẳn bản cũ. Cơ chế của bài là
*so sánh hai cột kề nhau*, nên khoảng cách đó là ràng buộc sư phạm, không phải
sở thích.

### Bảng cuối — 10 target `ArrayView` @1920×1080

| Target | Hằng số cũ | Trần 96 | **Trần 76 (chọn)** |
|---|---:|---:|---:|
| `algorithm.binary_search` | 714 | 1224 | **969** |
| `algorithm.count_if` | 714 | 1224 | **969** |
| `algorithm.sum_if` | 644 | 1104 | **874** |
| `algorithm.find_max` | 574 | 984 | **779** |
| `algorithm.linear_search` | 574 | 984 | **779** |
| `algorithm.bubble_sort` | **504** | 864 | **684** |
| `algorithm.find_min` | 504 | 864 | **684** |
| `algorithm.insertion_sort` | 434 | 744 | **589** |
| `algorithm.scan` | 364 | 624 | **494** |
| `algorithm.selection_sort` | 364 | 624 | **494** |

Chín target ngoài họ `ArrayView` đo lại ở cả ba mốc đều **+0px**.

**Không gian dư còn lại là có chủ đích** — dành cho con trỏ, quan hệ giữa cặp
đang xét, ranh giới vùng đã sắp, quỹ đạo dời chỗ, và công cụ thao tác của học
sinh ở milestone sau. Hợp đồng sizing chừa chỗ cho chúng thay vì tiêu vào bề
rộng cột.

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
