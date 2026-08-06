# DESIGN_CLARITY_MATRIX

Thang 0–3 × 6 tiêu chí, tối đa **18**.
`15–18` READY_FOR_PILOT · `11–14` MINOR_REFINEMENT · `7–10` MECHANISM_REDESIGN ·
`0–6` NOT_YET_A_SIMULATION.

**Engine đúng KHÔNG nâng điểm.** Mọi target dưới đây đều có engine đúng và
timeline đúng (back/tự chạy/dừng/scrub/reset đã thao tác thật, 22/22 đạt) — điều
đó không xuất hiện trong bất kỳ ô điểm nào.

| Target | Mechanism | Cause-effect | Interaction | Hierarchy | State language | Responsive | Tổng /18 | Verdict |
|---|---|---|---|---|---|---|---|---|
| `algorithm.bubble_sort` | 3 | 3 | 3 | 2 | 1 | 3 | **15** | READY_FOR_PILOT |
| `algorithm.insertion_sort` | 3 | 3 | 2 | 2 | 2 | 3 | **15** | READY_FOR_PILOT |
| `binary.decimal_to_binary` | 3 | 3 | 3 | 2 | 1 | 3 | **15** | READY_FOR_PILOT |
| `logic.and_gate` | 3 | 3 | 3 | 2 | 1 | 3 | **15** | READY_FOR_PILOT |
| `logic.boolean_dag` | 3 | 3 | 3 | 2 | 1 | 3 | **15** | READY_FOR_PILOT |
| `algorithm.find_max` | 3 | 3 | 2 | 2 | 1 | 3 | **14** | MINOR_REFINEMENT |
| `algorithm.find_min` | 3 | 3 | 2 | 2 | 1 | 3 | **14** | MINOR_REFINEMENT |
| `algorithm.count_if` | 3 | 3 | 2 | 2 | 1 | 3 | **14** | MINOR_REFINEMENT |
| `algorithm.sum_if` | 3 | 3 | 2 | 2 | 1 | 3 | **14** | MINOR_REFINEMENT |
| `algorithm.binary_search` | 3 | 3 | 2 | 2 | 1 | 3 | **14** | MINOR_REFINEMENT |
| `algorithm.bounded_control_flow` | 3 | 3 | 1 | 2 | 2 | 3 | **14** | MINOR_REFINEMENT |
| `network.protocol_encapsulation` | 3 | 3 | 2 | 2 | 1 | 3 | **14** | MINOR_REFINEMENT |
| `algorithm.linear_search` | 2 | 3 | 2 | 2 | 1 | 3 | **13** | MINOR_REFINEMENT |
| `algorithm.scan` | 3 | 3 | 1 | 2 | 1 | 3 | **13** | MINOR_REFINEMENT |
| `algorithm.selection_sort` | 2 | 3 | 2 | 2 | 1 | 3 | **13** | MINOR_REFINEMENT |
| `binary.character_encoding` | 3 | 3 | 1 | 2 | 1 | 3 | **13** | MINOR_REFINEMENT |
| `database.relational_table_query` | 3 | 3 | 1 | 2 | 1 | 3 | **13** | MINOR_REFINEMENT |
| `network.packet_routing` | 2 | 2 | 2 | 2 | 1 | 3 | **12** | MINOR_REFINEMENT |
| `binary.base_conversion` | 2 | 2 | 1 | 2 | 1 | 3 | **11** | MINOR_REFINEMENT |
| `tree.traversal` | 2 | 2 | 1 | 2 | 1 | 3 | **11** | MINOR_REFINEMENT |
| `generic.rule_scene` | 1 | 1 | 2 | 2 | 1 | 3 | **10** | MECHANISM_REDESIGN |
| `network.graph_traversal` | 1 | 1 | 1 | 2 | 1 | 3 | **9** | MECHANISM_REDESIGN |

**Phân bố:** READY_FOR_PILOT **5** · MINOR_REFINEMENT **15** ·
MECHANISM_REDESIGN **2** · NOT_YET_A_SIMULATION **0**.

---

## Vì sao gần như cả catalog kẹt ở "state language = 1"

Đây là **điểm thấp nhất và đồng loạt nhất** của toàn hệ. Đo được:
`legend = true` ở đúng **1/22** target ở bước giữa (`bounded_control_flow`, và
`insertion_sort` khi đang giữ quân bài) — cả hai đều là patch vừa làm. 20 target
còn lại **không có chú giải nào**, trong khi cùng một màu mang nghĩa khác nhau:

| Màu | `count_if` | `bubble_sort` | `tree.traversal` | `boolean_dag` |
|---|---|---|---|---|
| xanh lá | đã đếm vào | đã ổn định | đã thăm | tín hiệu = 1 **và** viền cổng đầu ra |
| xám | đã loại | chưa xét | chưa thăm | tín hiệu = 0 **và** chưa biết |

Một học sinh học `count_if` rồi chuyển sang `boolean_dag` sẽ mang theo nghĩa sai.
Đây là lý do **không** target nào đạt 3 ở tiêu chí này, kể cả các target 15 điểm.

## Vì sao "hierarchy = 2" ở toàn bộ 22 target

Không target nào đạt 3, vì cùng một lý do đo được: **panel Quan sát chiếm cố định
21% chiều ngang ở desktop** cho mọi target, kể cả target mà nội dung quan sát chỉ
có 3 dòng chữ (`base_conversion`, `graph_traversal`). Và ở **9/11 target thuộc
domain algorithm**, thẻ "XÁC ĐỊNH BÀI TOÁN" trong Quan sát **lặp lại nguyên tiêu
đề** đã có ngay phía trên sân khấu (`dup_title_in_observer = true`).

Trường hợp riêng đáng ghi: `bounded_control_flow` sau patch có sân khấu chiếm
**40%** thẻ trong khi khối "MÃ GIẢ" chiếm **37%** — gần ngang nhau. Mã giả đúng ra
phải là phần đối chiếu; đây là hệ quả phụ của chính patch vừa làm và nên chỉnh ở
đợt sau.

## Ghi chú đo lường (không phải phát hiện)

`stage_share_of_card` **thấp giả** ở `binary.*` và `database.*` vì phần lớn nội
dung cơ chế của chúng nằm **ngoài** `.sim-stage` (bảng chia, bảng kết quả).
`character_encoding` đo được 26% nhưng thực tế sân khấu chiếm gần hết thẻ — xem
`binary-character_encoding-narrow-2-mid.png`. Không dùng con số này để trừ điểm.
