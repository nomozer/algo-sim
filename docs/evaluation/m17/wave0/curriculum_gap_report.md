# Báo cáo Curriculum Gap — M17-Lite Wave 0

Sinh tự động (xem authenticity report). Trạng thái coverage lấy từ
`app/simulation/coverage.py` (M14 §O) + phán quyết audit W0.

## Đơn vị kiến thức chưa được hỗ trợ (CAPABILITY_GAP)

- **CSDL: bảng, bản ghi, truy vấn** (`database_table_query`, T11 CĐ4): chưa có table/grid — gap trung thực, ứng viên post-M8
- **Hệ điều hành: tiến trình (máy trạng thái)** (`os_process_fsm`, T11 B1–2): chưa có FSM
- **Đường đi ngắn nhất CÓ TRỌNG SỐ (Dijkstra)** (`dijkstra_weighted_shortest_path`, không có anchor SGK): COVERAGE §7b — ngoài phạm vi công khai; capability_gap là câu trả lời đúng dài hạn

## Đơn vị kiến thức PARTIAL

- **Lặp / rẽ nhánh / biến** (`loops_branch_variable`): chỉ trong các thuật toán cố định, không phải code tự do
- **HTML/CSS (quan hệ markup ↔ hiển thị)** (`html_css`): structural + reveal; thiếu practice tự dựng
- **Mã hoá văn bản/âm thanh/ảnh** (`text_media_encoding`): một phần; cần table/grid
- **Mảng 1D/2D (chỉ số ↔ giá trị)** (`arrays_1d_2d`): 1D ngầm trong trace; 2D chưa có
- **Học sinh tự dựng/thao tác, engine kiểm được** (`practice_activity`): substrate (PredictionCapability), chưa phải một mode đầy đủ

## Cơ chế intentional-gap (audit W0 xác nhận chặn trung thực)

- `comparison_sort.other_unspecified`: HONEST_GAP (case `aud-nm-sort-unspecified`)
- `comparison_sort.partition_recursive`: HONEST_GAP (case `aud-nm-quick-sort`)
- `comparison_sort.select_extreme_repeated`: HONEST_GAP (case `aud-nm-selection-sort`)
- `positional_representation.non_binary_base`: HONEST_GAP (case `aud-nm-hex-base`)

## Gap sẽ đóng trong M17-Lite (theo proposal đã duyệt)

- `positional_representation.non_binary_base` → Wave 1 (base conversion 2/8/10/16).
- `comparison_sort.select_extreme_repeated` → Wave 1 (Selection Sort).
- Duyệt cây (`tree_traversal`) → Wave 2 (family mới; regression W0 đang gap trung thực).
- CSDL bảng/truy vấn (`database_table_query`) → Wave 2 (`relational_table_query`).

## Gap giữ nguyên làm future work (KHÔNG trong M17-Lite)

- `comparison_sort.partition_recursive` (Quick Sort) — contract chưa biểu diễn partition.
- `dijkstra_weighted_shortest_path` — future family weighted_shortest_path.
- `os_process_fsm` — chưa có FSM.
- bounded_control_flow, dom_css_resolution — theo scope đã chốt.
