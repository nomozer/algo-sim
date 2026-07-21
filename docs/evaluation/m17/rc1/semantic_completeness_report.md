# M17-RC1 §D — Semantic Completeness

**Bất biến:** `status=ok` ⟹ `dropped_requirements` rỗng. Đề hỏi nhiều thao
tác mà family chỉ dựng được một → TỪ CHỐI TRUNG THỰC, không âm thầm chọn một.

Probe **sinh từ registry chính sách** — thêm family/cơ chế thì probe tự có.

- Family có chính sách: **9/9**
- Probe: **16** · khớp kỳ vọng **16** · lệch **0**
- Chặn đúng (multi-operation): **5** · chặn oan (single-operation): **0**
- ok mà còn dropped_requirements: **0** (phải là 0)
- Kết luận: **PASS**

## Chính sách theo family

| Family | Cardinality | max | #cơ chế | Ghi chú |
|---|---|---|---|---|
| `tree_traversal` | single | 1 | 4 | Một lần duyệt = một thứ tự. Đề hỏi nhiều thứ tự → tách từng lần. |
| `comparison_sort` | single | 1 | 5 | Một lần mô phỏng chạy một thuật toán sắp xếp. |
| `graph_traversal` | single | 1 | 3 | BFS và DFS là hai lần duyệt khác nhau — chưa có chế độ so sánh. |
| `positional_representation` | single | 1 | 2 | Một lần đổi = một cặp cơ số nguồn→đích. |
| `interval_elimination` | single | 1 | 1 | — |
| `single_pass_scan` | single | 1 | 5 | Một lượt quét cho một mục tiêu (max/min/đếm/tổng/tìm). |
| `boolean_composition` | multiple | 8 | 3 | Một mạch CHỨA nhiều cổng — nhiều cơ chế trong một cảnh là bình thường. |
| `layered_pdu_transform` | pipeline | 2 | 1 | Đóng gói → truyền → tháo gói là MỘT quy trình nối tiếp, không phải xung đột. |
| `structural_progressive_representation` | multiple | 8 | 2 | Một cảnh generic có thể vừa hé lộ vừa di chuyển. |

## Probe

| Probe | Kỳ vọng | Thực tế | Pha chặn | error_code | dropped |
|---|---|---|---|---|---|
| `tree_traversal::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `tree_traversal::all-mechanisms` | BLOCKED | ✓ BLOCKED | requested_combination | `multiple_operations_not_supported` | 4 |
| `comparison_sort::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `comparison_sort::all-mechanisms` | BLOCKED | ✓ BLOCKED | requested_combination | `multiple_operations_not_supported` | 5 |
| `graph_traversal::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `graph_traversal::all-mechanisms` | BLOCKED | ✓ BLOCKED | requested_combination | `multiple_operations_not_supported` | 3 |
| `positional_representation::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `positional_representation::all-mechanisms` | BLOCKED | ✓ BLOCKED | requested_combination | `multiple_operations_not_supported` | 2 |
| `interval_elimination::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `single_pass_scan::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `single_pass_scan::all-mechanisms` | BLOCKED | ✓ BLOCKED | requested_combination | `multiple_operations_not_supported` | 5 |
| `boolean_composition::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `boolean_composition::all-mechanisms` | PASS | ✓ PASS | — | `—` | 0 |
| `layered_pdu_transform::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `structural_progressive_representation::single-operation` | PASS | ✓ PASS | — | `—` | 0 |
| `structural_progressive_representation::all-mechanisms` | PASS | ✓ PASS | — | `—` | 0 |
