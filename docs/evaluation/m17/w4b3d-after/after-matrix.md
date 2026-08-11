# W4B-3A — MA TRẬN AFTER (toàn danh mục)

**Sinh từ nguồn** bởi `frontend/scripts/after-matrix-w4b3a.mjs` — registry
(`capability-descriptors.json`) + module frontend đang chạy + `measure-1920.json`.
Đừng sửa tay: chạy lại script.

Luật phân loại khai ở đầu script. Ba phép suy BỊ CẤM: `predict` ⇒ thao tác
trực tiếp · `timeline` ⇒ mô hình tương tác · có trong catalog ⇒ có phủ chương trình.

Tổng: **23 target · 12 family**. Đo được trong trình duyệt **23/23** (**0** target chưa có bài mẫu offline ⇒ chỉ đọc được năng lực KHAI BÁO).

Thao tác trực tiếp: **13 đo được** (+0 chỉ khai báo). Cam kết thuật toán: **9 đo được** (+0 chỉ khai báo). Khai `predict`: **11**.

> Hai cột đếm riêng có chủ đích. Cộng "đo được" với "chỉ khai báo" thành một
> con số là tự cho mình điểm cao hơn bằng chứng đang có.

| Target | Family | Hiện diện | Bài mẫu | Loại trải nghiệm | Vòng đời | Chủ sở hữu tất định | Thao tác trực tiếp | Cam kết thuật toán | Thử thách | Dòng thời gian | Chính sách biểu diễn | 2D/3D | Dải @1920 | Bằng chứng trình duyệt | Giới hạn đã khai |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| algorithm.binary_search | interval_elimination | PUBLIC_SAMPLE | có | INTERACTIVE_MODEL | progressive | algorithm.binary_search | CÓ | CÓ (4/13 bước) | có | có (13 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| algorithm.bounded_control_flow | bounded_control_flow | PUBLIC_SAMPLE | có | TRACE_PLAYBACK | progressive | algorithm.bounded_control_flow | không | không | không | có (12 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | hàm/thủ tục và đệ quy — ngoài phạm vi luồng điều khiển hữu hạn; danh sách/mảng, chuỗi, số thực, nhập xuất — chưa có trong ngữ pháp v1 |
| algorithm.bubble_sort | comparison_sort | PUBLIC_SAMPLE | có | INTERACTIVE_MODEL | progressive | algorithm.bubble_sort | CÓ | CÓ (21/40 bước) | có | có (40 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| algorithm.count_if | single_pass_scan | PUBLIC_SAMPLE | có | COMMITMENT_TRACE | progressive | algorithm.count_if | không | CÓ (10/17 bước) | có | có (17 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| algorithm.find_max | single_pass_scan | PUBLIC_SAMPLE | có | INTERACTIVE_MODEL | progressive | algorithm.find_max | CÓ | CÓ (7/10 bước) | có | có (10 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| algorithm.find_min | single_pass_scan | PUBLIC_SAMPLE | có | INTERACTIVE_MODEL | progressive | algorithm.find_min | CÓ | CÓ (6/10 bước) | có | có (10 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| algorithm.insertion_sort | comparison_sort | PUBLIC_SAMPLE | có | INTERACTIVE_MODEL | progressive | algorithm.insertion_sort | CÓ | CÓ (12/33 bước) | có | có (33 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| algorithm.linear_search | single_pass_scan | PUBLIC_SAMPLE | có | INTERACTIVE_MODEL | progressive | algorithm.linear_search | CÓ | CÓ (6/8 bước) | có | có (8 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| algorithm.scan | single_pass_scan | PUBLIC_AI_ONLY | có | TRACE_PLAYBACK | progressive | algorithm.scan | không | không | không | có (4 bước) | 2D_ONLY | 2d | 1 | ĐO 4 bề rộng | một lượt quét nhiều biến tích luỹ (vd tìm cả max lẫn min) — single_pass_scan.multi_accumulator, BACKLOG |
| algorithm.selection_sort | comparison_sort | PUBLIC_SAMPLE | có | INTERACTIVE_MODEL | progressive | algorithm.selection_sort | CÓ | CÓ (10/24 bước) | có | có (24 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| algorithm.sum_if | single_pass_scan | PUBLIC_SAMPLE | có | COMMITMENT_TRACE | progressive | algorithm.sum_if | không | CÓ (9/16 bước) | có | có (16 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| binary.base_conversion | positional_representation | PUBLIC_SAMPLE | có | TRACE_PLAYBACK | progressive | binary.base_conversion | không | không | không | có (5 bước) | 2D_ONLY | 2d | 0 | ĐO 4 bề rộng | — |
| binary.character_encoding | positional_representation | PUBLIC_SAMPLE | có | TRACE_PLAYBACK | progressive | binary.character_encoding | không | không | không | có (21 bước) | 2D_ONLY | 2d | 1 | ĐO 4 bề rộng | emoji và ký tự ngoài BMP (mã > 65535) — ngoài phạm vi v1; dãy byte UTF-8/UTF-16, Base64, nén, mã hoá bảo mật — ngoài phạm vi |
| binary.decimal_to_binary | positional_representation | PUBLIC_SAMPLE | có | INTERACTIVE_STAGE | exploratory | binary.decimal_to_binary | CÓ (sân khấu, luôn mở) | không | không | không | 2D_ONLY | 2d | 1 | ĐO 4 bề rộng | — |
| database.relational_table_query | relational_table_query | PUBLIC_SAMPLE | có | TRACE_PLAYBACK | progressive | database.relational_table_query | không | không | không | có (19 bước) | 2D_ONLY | 2d | 1 | ĐO 4 bề rộng | JOIN nhiều bảng · truy vấn lồng · thêm/sửa/xoá dữ liệu · SQL tự do · GROUP BY nhiều nhóm · kết nối CSDL thật — ngoài phạm vi v1; phần tích luỹ (đếm/tổng/cực trị) TRÙNG cơ chế với single_pass_scan; cái mới ở đây là KHUNG QUAN HỆ (lược đồ, kiểu cột, vị từ trên bản ghi, phép chiếu, sắp xếp ổn định) |
| generic.rule_scene | boolean_composition · structural_progressive_representation | PUBLIC_SAMPLE | có | INTERACTIVE_STAGE | hybrid | generic.rule_scene | CÓ (sân khấu, luôn mở) | không | không | không | 2D_ONLY | 2d | 0 | ĐO 4 bề rộng | — |
| logic.and_gate | boolean_composition | PUBLIC_SAMPLE | có | INTERACTIVE_STAGE | exploratory | logic.and_gate | CÓ (sân khấu, luôn mở) | không | không | không | 2D_ONLY | 2d | 1 | ĐO 4 bề rộng | — |
| logic.boolean_dag | boolean_composition | PUBLIC_SAMPLE | có | INTERACTIVE_STAGE | hybrid | logic.boolean_dag | CÓ (sân khấu, luôn mở) | không | không | có (3 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | — |
| network.graph_traversal | graph_traversal | PUBLIC_SAMPLE | có | TRACE_PLAYBACK | progressive | network.graph_traversal | không | không | không | có (7 bước) | 2D_ONLY | 2d | 1 | ĐO 4 bề rộng | đường đi ngắn nhất có trọng số (Dijkstra) — future family |
| network.packet_routing | graph_traversal | PUBLIC_SAMPLE | có | INTERACTIVE_MODEL | progressive | network.packet_routing | CÓ | không | có | có (4 bước) | 2D_ONLY | 2d | 1 | ĐO 4 bề rộng | đường đi ngắn nhất có trọng số (Dijkstra); dựng topo từng bước |
| network.protocol_encapsulation | layered_pdu_transform | PUBLIC_SAMPLE | có | TRACE_PLAYBACK | progressive | network.protocol_encapsulation | không | không | có | có (9 bước) | 2D+3D (phù hợp sư phạm) | 2d/3d | 1 | ĐO 4 bề rộng | bắt tay TCP ba bước; phân mảnh; retransmission; congestion; DNS |
| tree.traversal | tree_traversal | PUBLIC_SAMPLE | có | TRACE_PLAYBACK | progressive | tree.traversal | không | không | không | có (22 bước) | 2D_ONLY | 2d | 2 | ĐO 4 bề rộng | BST/AVL/heap/cây biểu thức/cây n-nhánh — ngoài phạm vi duyệt cây nhị phân |
| web.style_model | web_presentation | PUBLIC_SAMPLE | có | BOUNDED_ARTIFACT | exploratory | web.style_model | CÓ (sân khấu, luôn mở) | không | không | không | 2D_ONLY | 2d | 1 | ĐO 4 bề rộng | — |

## Tổng hợp (đếm SAU khi có bảng từng target)

```json
{
  "targets": 23,
  "families": 12,
  "visibility": {
    "PUBLIC_SAMPLE": 22,
    "PUBLIC_AI_ONLY": 1,
    "INTERNAL_FIXTURE": 0
  },
  "experience": {
    "INTERACTIVE_MODEL": 8,
    "TRACE_PLAYBACK": 8,
    "COMMITMENT_TRACE": 2,
    "INTERACTIVE_STAGE": 4,
    "BOUNDED_ARTIFACT": 1
  },
  "direct_manipulation_measured": 13,
  "direct_manipulation_gated": 8,
  "direct_manipulation_always_on_stage": 5,
  "direct_manipulation_declared_only": 0,
  "algorithm_commitment_measured": 9,
  "algorithm_commitment_declared_only": 0,
  "challenge_predict": 11,
  "measured_in_browser": 23,
  "not_measurable_no_sample": 0,
  "trigger_band_remaining": "0 (xem measure-*.json: không target nào còn experimentTrigger)"
}
```