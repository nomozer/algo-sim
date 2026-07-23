# M17-RC1 §E — Audit thị giác toàn danh mục

Chụp trên **Chrome thật** qua CDP (không SSR, không framework E2E), hai
viewport, kèm assertion chạy trong trình duyệt. Phán quyết REAL/PARTIAL/
BROKEN do **người xem ảnh** chấm — assertion xanh KHÔNG tự thành REAL.

- Renderer: **6** (đã review 6) · fixture **25**
- Ảnh: **134** (desktop 67 · hẹp 67)
- REAL **5** · PARTIAL **1** · BROKEN **0** · GAP **0**
- Lỗi: tìm **4** · sửa **2** · còn chặn **0**

| Renderer | Family | Target | canonical/boundary/stress | Ảnh | Trạng thái |
|---|---|---|---|---|---|
| `algorithm` | comparison_sort, interval_elimination, single_pass_scan | 3/10 | 1/1/2 | 26 | **REAL_VISUAL** |
| `binary` | positional_representation | 2/2 | 1/0/1 | 8 | **REAL_VISUAL** |
| `generic` | boolean_composition, structural_progressive_representation | 1/1 | 1/0/1 | 12 | **PARTIAL_VISUAL** |
| `logic` | boolean_composition | 2/2 | 1/0/1 | 8 | **REAL_VISUAL** |
| `network` | graph_traversal, layered_pdu_transform | 3/3 | 4/2/2 | 48 | **REAL_VISUAL** |
| `tree` | tree_traversal | 1/1 | 2/2/1 | 32 | **REAL_VISUAL** |

## Nhận xét người review

### `algorithm` — REAL_VISUAL
- Tiêu chí chưa đạt: không
- Cột mảng, con trỏ bước, mã giả và tường thuật đồng bộ engine; số âm và thập phân hiển thị đúng; nhãn tên tiếng Việt không tràn; binary search thu hẹp khoảng rõ; kết quả chỉ hiện ở bước cuối.

### `binary` — REAL_VISUAL
- Tiêu chí chưa đạt: không
- Hàng trọng số và ô bit rõ; bảng chia-lấy-dư của đổi cơ số tổng quát đọc được ở cả hai viewport; giá trị lớn (2026₁₀ → hex) không tràn.

### `generic` — PARTIAL_VISUAL
- Tiêu chí chưa đạt: LAYOUT_PASS
- Sau VIS-002 + bản so le BA hàng: ba nhãn dài trên cùng một đường ngang đã tách rời và đọc được; badge kỹ thuật GENERIC thay bằng 'MÔ PHỎNG THEO MÔ TẢ'. GIỮ PARTIAL vì §8: với nhãn CỰC dài và NHIỀU đối tượng hơn số hàng so le, bố cục vẫn có thể chật — không sửa thêm được nếu không đụng `state.pos` (§1 cấm sửa engine state). Hạn chế này KHÔNG che nút/trạng thái và KHÔNG làm sai cơ chế. Engine authenticity GIỮ NGUYÊN PARTIAL — audit thị giác không nâng hạng; tiêu đề không giả nhận diện thuật toán, phụ đề ghi rõ 'Mô phỏng tổng quát (AI tự dựng)'.

### `logic` — REAL_VISUAL
- Tiêu chí chưa đạt: không
- Cổng, dây nối và bảng chân trị rõ; mạch ba cổng lồng nhau đọc được. and_gate là module KHÁM PHÁ (không timeline) nên chỉ có ảnh initial — đúng hợp đồng, không phải thiếu ảnh.

### `network` — REAL_VISUAL
- Tiêu chí chưa đạt: không
- Mọi cạnh hiện rõ ở CẢ hai viewport (không tái phát phantom token — kiểm computed stroke thật trong Chrome). Sau VIS-001: nhãn tiếng Việt dài nằm DƯỚI nút, không còn bị nút cắt ngang. BFS dùng hàng đợi, DFS dùng ngăn xếp, cùng topology cho thấy khác biệt rõ; đồ thị có chu trình không lặp vô hạn; đích không tới được KHÔNG bị dựng đường giả; đồ thị có hướng và đồ thị dày vẫn đọc được; kết quả hiện dần.

### `tree` — REAL_VISUAL
- Tiêu chí chưa đạt: không
- Regression bản sửa nhãn dài VR1 GIỮ NGUYÊN: cạnh trái/phải rõ, nhãn 11 nút tiếng Việt không chồng nút, canvas co giãn, ngăn xếp/hàng đợi đúng biến thể, thứ tự duyệt hiện dần, đường đang đi nổi bật. Cây một nút và cây lệch sâu đều đúng. Viewport hẹp đầy đủ, không cắt.

