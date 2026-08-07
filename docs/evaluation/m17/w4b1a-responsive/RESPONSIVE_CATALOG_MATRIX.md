# RESPONSIVE_CATALOG_MATRIX — W4B-1A

Số trong ô = **px nội dung bị giấu sau thanh cuộn nội bộ của `.panel-center`**
(lớn nhất qua ba checkpoint initial · mid · final). `0` = không giấu gì.
Sinh tự động từ `catalog-*/responsive-diagnosis.json` — không nhập tay.

| # | Target | 1366×768 trước | 1366×768 sau | 1536×864 trước | 1536×864 sau | Narrow (1024×768 · 768×900) | Cao (1920×1080 · 1366×1024 · 1440×900) | Còn lại |
|---:|---|---:|---:|---:|---:|:--:|:--:|---|
| 1 | `algorithm.binary_search` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 2 | `algorithm.bounded_control_flow` | 25 | **0** | 0 | **0** | PASS | PASS | — |
| 3 | `algorithm.bubble_sort` | 31 | **0** | 0 | **0** | PASS | PASS | — |
| 4 | `algorithm.count_if` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 5 | `algorithm.find_max` | 71 | **0** | 0 | **0** | PASS | PASS | — |
| 6 | `algorithm.find_min` | 71 | **0** | 0 | **0** | PASS | PASS | — |
| 7 | `algorithm.insertion_sort` | 89 | **0** | 0 | **0** | PASS | PASS | — |
| 8 | `algorithm.linear_search` | 74 | **0** | 0 | **0** | PASS | PASS | — |
| 9 | `algorithm.scan` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 10 | `algorithm.selection_sort` | 31 | **0** | 0 | **0** | PASS | PASS | — |
| 11 | `algorithm.sum_if` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 12 | `binary.base_conversion` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 13 | `binary.character_encoding` | 159 | **0** | 63 | **0** | PASS | PASS | — |
| 14 | `binary.decimal_to_binary` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 15 | `database.relational_table_query` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 16 | `generic.rule_scene` | 39 | **0** | 0 | **0** | PASS | PASS | — |
| 17 | `logic.and_gate` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 18 | `logic.boolean_dag` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 19 | `network.graph_traversal` | 60 | **0** | 0 | **0** | PASS | PASS | — |
| 20 | `network.packet_routing` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 21 | `network.protocol_encapsulation` | 0 | **0** | 0 | **0** | PASS | PASS | — |
| 22 | `tree.traversal` | 71 | **0** | 0 | **0** | PASS | PASS | — |

**Tổng kết.** 22/22 target đo được. Trước bản vá: **11 target** giấu nội dung ở ít nhất một trong hai viewport nghiệm thu (FAIL, 19 vi phạm). Sau bản vá: **0 target** (PASS). Đã sửa 11 target.

| Bộ đo | Viewport | Verdict | Vi phạm |
|---|---|---|---:|
| catalog-before | 1366×768 · 1536×864 | `FAIL` | 19 |
| catalog-after | 1366×768 · 1536×864 | `PASS` | 0 |
| narrow-after | 1024×768 · 768×900 | `PASS` | 0 |
| tall-after | 1920×1080 · 1366×1024 · 1440×900 | `PASS` | 0 |

