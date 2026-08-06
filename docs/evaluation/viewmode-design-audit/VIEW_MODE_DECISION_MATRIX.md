# VIEW_MODE_DECISION_MATRIX

Lượt READ-ONLY. `main @ cc449d5` **+ patch cơ chế đang trong working tree, chưa
commit** (bounded_control_flow · insertion_sort · quy ước màu). Catalog canonical
**11 family / 22 target**, hash `4d7c8e65…` (`catalog_runtime_matrix.py`).

**Nguyên tắc chấm:** 2D là mặc định (`COVERAGE §2.4`). 3D chỉ hợp lệ khi **chiều
sâu mã hoá một biến hoặc quan hệ khái niệm**, không phải bố cục. "Đẹp hơn",
"hiện đại hơn", "có nhiều đối tượng", "là cây/đồ thị/mạng" đều **không** phải lý do.

## Kết quả

| Quyết định | Số target |
|---|---|
| `2D_ONLY` | **20** |
| `2D_PRIMARY_3D_OPTIONAL` | **1** |
| `3D_JUSTIFIED` | **0** |
| `DO_NOT_USE_3D` | **1** |

**Không đề xuất thêm 3D cho bất kỳ target nào.** Ngược lại, một target đang có 3D
được đề nghị **rút khỏi đường học** (giữ lại làm bằng chứng kiến trúc).

---

## Ma trận

| Target | Family | Cơ chế cốt lõi | Chế độ hiện tại | Đề xuất | Chiều sâu sẽ mã hoá gì | Rủi ro 3D | Bằng chứng quyết định |
|---|---|---|---|---|---|---|---|
| `algorithm.find_max` | single_pass_scan | quét một lượt, giữ cực trị | 2d | **2D_ONLY** | không gì — dãy là 1 chiều | dựng khối hộp cho dãy số làm che nhãn, thêm camera mà không thêm thông tin | vị trí + màu + ▲ đã mã hoá đủ vùng đã duyệt / hiện tại / cực trị (`find_max-desktop-2-mid`) |
| `algorithm.find_min` | single_pass_scan | như trên (đối xứng) | 2d | **2D_ONLY** | không gì | như trên | cùng renderer `ArrayView`, 9 hình SVG, 0 bảng |
| `algorithm.count_if` | single_pass_scan | duyệt + đếm theo điều kiện | 2d | **2D_ONLY** | không gì | như trên | xanh/xám/đang xét + chip `đếm` đủ trên mặt phẳng |
| `algorithm.sum_if` | single_pass_scan | duyệt + cộng dồn | 2d | **2D_ONLY** | không gì | như trên | như count_if |
| `algorithm.scan` | single_pass_scan | quét theo spec DSL | 2d | **2D_ONLY** | không gì | như trên | cùng `ArrayView` |
| `algorithm.linear_search` | single_pass_scan | so sánh tuần tự tới khi khớp | 2d | **2D_ONLY** | không gì | như trên | 1 chiều, không có quan hệ không gian thứ hai |
| `algorithm.binary_search` | interval_elimination | loại một nửa mỗi bước | 2d | **2D_ONLY** | không gì — "nửa bị loại" là một khoảng trên trục | chiều sâu sẽ **che** ranh giới trái/phải, thứ duy nhất cần đọc | vùng xám co lại theo bước, đọc được trong một cái nhìn (`binary_search-desktop-2-mid`) |
| `algorithm.bubble_sort` | comparison_sort | so sánh cặp kề + đổi chỗ | 2d | **2D_ONLY** | không gì | khối hộp làm mất so sánh chiều cao — thứ mang nghĩa của dãy số | cặp kề tô đậm + ▲▲ + đuôi xanh; kéo-thả what-if cần mặt phẳng |
| `algorithm.selection_sort` | comparison_sort | chọn cực trị rồi đổi chỗ | 2d | **2D_ONLY** | không gì | như trên | cùng `ArrayView` |
| `algorithm.insertion_sort` | comparison_sort | rút một quân, dịch phải, chèn | 2d | **2D_ONLY** | không gì — "ô trống" là một vị trí trên hàng | chiều sâu làm ô trống khó thấy, đúng thứ vừa được sửa để thấy | khay ĐANG GIỮ + ô trống nét đứt (patch working tree) |
| `algorithm.bounded_control_flow` | bounded_control_flow | kiểm tra → thân → cập nhật → quay lại | 2d | **2D_ONLY** | không gì — quỹ đạo biến là 1 chiều, chu trình là đồ thị phẳng | cạnh quay lại vẽ trong 3D sẽ bị che bởi chính trục giá trị | trục giá trị + biên + 4 pha + cạnh quay lại đọc được trên mặt phẳng (patch working tree) |
| `binary.decimal_to_binary` | positional_representation | trọng số vị trí → tổng | 2d | **2D_ONLY** | không gì | bit là hàng ngang có trọng số; dựng hộp làm mất quan hệ hàng | ô bit + `+8 +4 +1` + tổng; bấm bit đổi state thật (`interaction-remeasure.json`) |
| `binary.base_conversion` | positional_representation | chia liên tiếp, gom số dư, đọc ngược | 2d | **2D_ONLY** | không gì — bảng chia là quan hệ 2 chiều (hàng × cột) | 3D biến bảng thành thứ khó đọc, không thêm quan hệ | bảng chia mọc dần theo bước |
| `binary.character_encoding` | positional_representation | ký tự → code point → thập phân → nhị phân | 2d | **2D_ONLY** | không gì | như trên | hai bảng + tô hàng chia hiện tại (`character_encoding-narrow-2-mid`) |
| `database.relational_table_query` | relational_table_query | dòng dữ liệu qua 5 tầng pipeline | 2d | **2D_ONLY** | không gì — bảng đã là 2 chiều tự nhiên | chiều thứ ba không tương ứng với trục nào của dữ liệu | nhãn Giữ/Loại/Đang xét đổi theo bước; dải 5 chip |
| `generic.rule_scene` | structural_progressive_representation | quy tắc do AI mô tả tác động lên đối tượng | 2d | **2D_ONLY** | không gì | spec do LLM sinh — 3D sẽ khuếch đại mọi bố cục kém | family khai `result_authority = representation` |
| `logic.and_gate` | boolean_composition | AND của hai đầu vào | 2d | **2D_ONLY** | không gì — sơ đồ mạch là quy ước phẳng | sơ đồ mạch điện đọc theo quy ước 2D; 3D phá quy ước đó | công tắc → dây → cổng → đèn |
| `logic.boolean_dag` | boolean_composition | tín hiệu lan truyền qua DAG nhiều cổng | 2d | **2D_ONLY** | không gì — DAG xếp tầng theo độ sâu phụ thuộc, đã là trục ngang | cạnh chéo trong 3D chồng lên nhau, đúng thứ cần đọc | sơ đồ node-edge + dây đổi màu + `?`; bàn phím đổi state thật |
| `network.graph_traversal` | graph_traversal | frontier (hàng đợi/ngăn xếp) quyết định thứ tự | 2d | **2D_ONLY** | không gì có ích — đồ thị này không có toạ độ thật | **cạm bẫy điển hình**: "là đồ thị nên nên 3D". Nhưng thứ đang thiếu là **hàng đợi**, không phải chiều sâu | ở bước 3/7 narration nói "Lấy B ra khỏi hàng đợi" nhưng UI không có hàng đợi nào được vẽ; 3D không sửa được điều đó |
| `tree.traversal` | tree_traversal | ngăn xếp quyết định thứ tự duyệt | 2d | **2D_ONLY** | không gì có ích — cây nhị phân có bố cục phẳng chuẩn | như trên: thiếu **ngăn xếp**, không thiếu chiều sâu | cạnh A–B đã được tô cam; ngăn xếp vẫn là dòng chữ "Ngăn xếp: A, B" |
| `network.packet_routing` | graph_traversal | gói tin đi từng chặng theo tuyến | **2d/3d** | **DO_NOT_USE_3D** *(giữ code làm bằng chứng kiến trúc)* | **không gì** — module tự khai `meaningOfZ = "phân tách nút trên/ngoài tuyến (bố cục), không mang nghĩa khái niệm"` | nhãn nút bị thu nhỏ và mờ do phối cảnh; thêm thao tác camera; fixture công khai có 4 nút **đều trên tuyến** nên Z hoàn toàn phẳng | `packet_routing-desktop-6-mode3d`: 4 quả cầu cùng một độ sâu, thông tin **giống hệt** 2D nhưng nhãn khó đọc hơn. `threeD.role = architectural_poc` |
| `network.protocol_encapsulation` | layered_pdu_transform | mỗi tầng thêm/gỡ phần của mình; tháo gói là quá trình ngược | **2d/3d** | **2D_PRIMARY_3D_OPTIONAL** | **tầng giao thức** (trục sâu) × **chiều truyền gửi→nhận** (trục ngang) — hai biến khái niệm trực giao | nhãn tầng bị che một phần bởi mặt phẳng; phân đoạn PDU nhỏ ở góc camera mặc định | `encapsulation-desktop-6-mode3d`: 4 mặt phẳng xếp theo độ sâu = 4 tầng, có caption "Trục sâu = tầng giao thức · trục ngang = chiều truyền". `threeD.role = pedagogical`. Chuyển 2D↔3D giữ `cursor 2→2→2` |

---

## Vì sao KHÔNG có target nào được xếp `3D_JUSTIFIED`

Tiêu chí `3D_JUSTIFIED` đòi: *bỏ chiều sâu thì học sinh **mất** một thông tin cơ
chế quan trọng*. Áp vào target duy nhất có chiều sâu mang nghĩa
(`protocol_encapsulation`): chế độ 2D **đã** mã hoá tầng bằng vị trí dọc và
gửi/nhận bằng hai cột — nên bỏ 3D đi, học sinh **không mất** thông tin cơ chế
nào; 3D chỉ làm ẩn dụ "chồng tầng" trở thành nghĩa đen. Đó đúng là định nghĩa của
`2D_PRIMARY_3D_OPTIONAL`.

Kết luận này trùng với chính tuyên bố của repo (`threeD.role = pedagogical` cho
encapsulation, `architectural_poc` cho packet_routing) — audit chỉ xác nhận bằng
quan sát, không phát minh luật mới.

## Khuyến nghị cho `network.packet_routing`

Không xoá renderer 3D: nó là **bằng chứng kiến trúc** cho luận điểm "2D và 3D dùng
chung engine/state/timeline" (bất biến #16), và lượt đo này xác nhận điều đó
(`cursor 2→2→2`, `three_canvas = true`). Nhưng **không nên trình bày 3D như một
chế độ học** cho target này: với fixture công khai, Z không tách gì cả và nhãn khó
đọc hơn 2D. Đề nghị: giữ nguyên code, ghi rõ trong tài liệu rằng đây là PoC kiến
trúc, và cân nhắc ẩn nút 3D khỏi đường học sinh ở một đợt sau — **không làm trong
đợt này**.
