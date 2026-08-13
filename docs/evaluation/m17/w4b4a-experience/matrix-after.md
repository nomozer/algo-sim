# W4B-4D — Ma trận trải nghiệm TOÀN danh mục (SAU khi triển khai)

Sinh từ `probe.json` (đo bằng HÀNH VI qua `module.apply`, 2026-08-12T16:23:31.636Z).
Nguồn số duy nhất là phép đo; file này chỉ trình bày lại. Câu hỏi nghiệm thu:
*"Bỏ hết Play/Next/đúng-sai đi, học sinh còn thao tác được lên mô hình và
quan sát hệ quả tất định không?"*

**20/23 target thao tác được trực tiếp** · 3 giữ trace
có lý do cơ chế khai trong `KEEP_TRACE` (guard hai chiều: thiếu lý do là đỏ,
lý do lỗi thời khi target đã tương tác cũng đỏ).

| Target | Mode | Thao tác đổi state | Cửa Khám phá | Cam kết | Trải nghiệm |
|---|---|---|---|---|---|
| `algorithm.binary_search` | progressive | 1/1 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `algorithm.bounded_control_flow` | progressive | 0/1 | — | — | TRACE (quyết định có lý do cơ chế) |
| `algorithm.bubble_sort` | progressive | 1/1 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `algorithm.count_if` | progressive | 2/4 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `algorithm.find_max` | progressive | 1/1 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `algorithm.find_min` | progressive | 1/1 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `algorithm.insertion_sort` | progressive | 1/1 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `algorithm.linear_search` | progressive | 1/1 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `algorithm.scan` | progressive | 0/1 | — | — | TRACE (quyết định có lý do cơ chế) |
| `algorithm.selection_sort` | progressive | 1/1 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `algorithm.sum_if` | progressive | 4/4 | ✔ | ✔ | thao tác trực tiếp + cam kết |
| `binary.base_conversion` | hybrid | 2/5 | luôn mở | — | thao tác trực tiếp |
| `binary.character_encoding` | hybrid | 1/5 | luôn mở | — | thao tác trực tiếp |
| `binary.decimal_to_binary` | exploratory | 5/9 | luôn mở | — | thao tác trực tiếp |
| `database.relational_table_query` | hybrid | 2/2 | luôn mở | — | thao tác trực tiếp |
| `generic.rule_scene` | hybrid | 2/2 | luôn mở | — | thao tác trực tiếp |
| `logic.and_gate` | exploratory | 2/2 | luôn mở | — | thao tác trực tiếp |
| `logic.boolean_dag` | hybrid | 3/3 | luôn mở | — | thao tác trực tiếp |
| `network.graph_traversal` | hybrid | 1/4 | luôn mở | — | thao tác trực tiếp |
| `network.packet_routing` | progressive | 1/4 | ✔ | — | thao tác trực tiếp |
| `network.protocol_encapsulation` | progressive | 0/4 | — | — | TRACE (quyết định có lý do cơ chế) |
| `tree.traversal` | hybrid | 2/2 | luôn mở | — | thao tác trực tiếp |
| `web.style_model` | exploratory | 2/2 | luôn mở | — | thao tác trực tiếp |

Chứng cứ trình duyệt: `../w4b4c-experience/acceptance.json` — 6 target đổi
tham số ở 4 bề rộng, kết quả tính lại KHÔNG cần Play, nhãn lệch-đề im lúc mở
và lên tiếng sau khi đổi. Tiêm lỗi: `../w4b4d-composition/fault-log.md`.
