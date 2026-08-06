# UI_COMPLEXITY_MATRIX — giao diện có quá nhiều chữ / panel không?

Đo trong **Chrome thật** (CDP), **22/22 target mở được, 0 lỗi runtime**, viewport
desktop 1440×1000, đo ở **pha giữa timeline** (mid = 45 % số bước, đạt bằng bấm
thật). Số thô: [raw-observations.json](raw-observations.json).

Cột nghĩa là: `stage%` = diện tích `.sim-stage` trên diện tích thẻ làm việc ·
`shapes` = số hình trong SVG sân khấu · `stage_txt` / `body_txt` = ký tự chữ trong
sân khấu / trong toàn thẻ · `narr` = số câu tường thuật · `legend` = có chú giải ·
`pseudo` = số dòng mã giả đang tô sáng · `predict` = có thanh dự đoán.

## 1. Bảng 22 target

| Target | stage% | shapes | stage_txt | body_txt | narr | legend | pseudo | predict | Nhãn CT |
|---|---:|---:|---:|---:|---:|:---:|---:|:---:|---|
| `tree.traversal` | **67** | 13 | 207 | 573 | 1 | ✓ | 0 | – | CHUYÊN ĐỀ |
| `network.graph_traversal` | **65** | 10 | 166 | 540 | 0 | ✓ | 0 | – | CHUYÊN ĐỀ |
| `algorithm.scan` | 53 | 7 | 19 | 413 | 1 | – | 1 | – | CỐT LÕI |
| `generic.rule_scene` | 51 | 7 | 16 | 362 | 0 | – | 0 | – | CÔNG CỤ |
| `logic.and_gate` | 51 | 9 | 24 | 380 | 1 | – | 0 | – | CỐT LÕI |
| `algorithm.selection_sort` | 50 | 7 | 41 | 924 | 1 | – | 1 | – | ĐỊNH HƯỚNG |
| `database.relational_table_query` | 50 | 5 | 150 | 567 | 1 | – | 0 | – | ĐỊNH HƯỚNG |
| `algorithm.bubble_sort` | 46 | 9 | 41 | 963 | 1 | – | 1 | – | ĐỊNH HƯỚNG |
| `algorithm.insertion_sort` | 46 | 7 | 23 | 899 | 1 | – | 1 | – | ĐỊNH HƯỚNG |
| `binary.base_conversion` | 44 | 0 | 97 | 487 | 0 | – | 0 | – | CỐT LÕI |
| `binary.decimal_to_binary` | 44 | 4 | 26 | 374 | 1 | – | 0 | – | CỐT LÕI |
| `algorithm.binary_search` | 43 | 11 | 48 | 1054 | 1 | – | 1 | – | ĐỊNH HƯỚNG |
| `algorithm.bounded_control_flow` | 40 | 10 | 129 | 451 | 1 | ✓ | 1 | – | CỐT LÕI |
| `network.protocol_encapsulation` | 39 | 0 | 186 | 755 | 1 | – | 0 | ✓ | CỐT LÕI |
| `algorithm.count_if` | 36 | 11 | 57 | 906 | 1 | – | 1 | ✓ | CỐT LÕI |
| `algorithm.sum_if` | 36 | 10 | 47 | 936 | 1 | – | 1 | ✓ | CỐT LÕI |
| `algorithm.linear_search` | 34 | 9 | 47 | 1006 | 1 | – | 1 | ✓ | ĐỊNH HƯỚNG |
| `algorithm.find_max` | 32 | 10 | 74 | 1033 | 1 | – | 1 | ✓ | CỐT LÕI |
| `algorithm.find_min` | 32 | 9 | 73 | 1038 | 1 | – | 1 | ✓ | CỐT LÕI |
| **`logic.boolean_dag`** | **32** | 11 | 113 | 606 | 1 | **–** | 0 | – | **CỐT LÕI** |
| `network.packet_routing` | 28 | 8 | 53 | 566 | 1 | – | 0 | ✓ | CỐT LÕI |
| `binary.character_encoding` | 26 | 0 | 65 | 627 | 1 | – | 0 | – | CỐT LÕI |

## 2. Trả lời thẳng câu hỏi "UI có quá nhiều chữ / panel không?"

**Không phải quá nhiều panel. Số panel là hằng số và đã được kiểm soát.**

- **Bề rộng ngăn quan sát đúng 21 % ở cả 22 target** — không target nào phình ra.
- **`narration_count` ≤ 1 ở tất cả 22 target** — một khe tường thuật duy nhất, đúng
  hợp đồng đã chốt ở đợt trước.
- **`dup_narration_in_observer = false` ở 22/22**; `dup_title_in_observer = true`
  ở 9 target thuộc nhóm `algorithm.*` — tiêu đề bài lặp lại trong ngăn quan sát.
  Đây là trùng lặp **duy nhất** đo được, và nó nhỏ.
- **`overflow_x = false` ở 22/22**, ba viewport. Không target nào tràn ngang.

**Vấn đề thật không nằm ở lượng chữ, mà ở TỈ LỆ giữa sân khấu và phần còn lại.**

Nhóm `algorithm.*` có `body_txt` cao nhất (899–1054 ký tự) nhưng phần lớn là **mã
giả + bảng biến** — thứ có chức năng rõ ràng. Ngược lại, ba target dưới cùng bảng
(`packet_routing` 28 %, `character_encoding` 26 %, `boolean_dag` 32 %) có sân khấu
**nhỏ hơn một nửa** so với `tree.traversal` (67 %), trong khi cả ba đều thuộc nhóm
**CỐT LÕI**.

**Nhưng `stage_share_of_card` KHÔNG dùng được cho `binary.*` và `database.*`.**
Ba target đó (`base_conversion`, `character_encoding`, `relational_table_query`) có
`svg_in_stage = false`, `tables_in_stage = 1` — "sân khấu" của chúng **là một bảng**,
nên đo diện tích SVG là vô nghĩa và đo diện tích `.sim-stage` cũng không nói được
bảng đó có dễ đọc hay không. Tôi **không** dùng chỉ số này để xếp hạng ba target đó,
và **không** chọn pilot dựa trên nó.

## 3. Chỉ có 3/22 target có chú giải

`legend = ✓` chỉ ở `tree.traversal`, `network.graph_traversal`,
`algorithm.bounded_control_flow` — cả ba đều là kết quả của các đợt sửa gần đây.
**19/22 target còn lại dùng màu mà không giải thích màu.** Với hệ đã thống nhất
ngôn ngữ màu (xanh dương = đang xét, xanh lá = đã chốt, xám = chưa xét, cam = đang
giữ/biên), việc không nói ra quy ước khiến quy ước đó chỉ tồn tại trong đầu người
viết code. Đây là khoảng trống hệ thống lớn nhất mà lượt đo này tìm ra.
