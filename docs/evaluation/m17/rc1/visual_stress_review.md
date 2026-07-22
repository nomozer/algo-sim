# M17-RC1 §E — Audit thị giác toàn danh mục

Chụp trên **Chrome thật** qua CDP (không SSR, không framework E2E), hai
viewport, kèm assertion chạy trong trình duyệt. Phán quyết REAL/PARTIAL/
BROKEN do **người xem ảnh** chấm — assertion xanh KHÔNG tự thành REAL.

- Renderer: **6** (đã review 6) · fixture **25**
- Ảnh: **134** (desktop 67 · hẹp 67)
- REAL **0** · PARTIAL **6** · BROKEN **0** · GAP **0**
- Lỗi: tìm **3** · sửa **2** · còn chặn **1**

| Renderer | Family | Target | canonical/boundary/stress | Ảnh | Trạng thái |
|---|---|---|---|---|---|
| `algorithm` | comparison_sort, interval_elimination, single_pass_scan | 3/10 | 1/1/2 | 26 | **PARTIAL_VISUAL** |
| `binary` | positional_representation | 2/2 | 1/0/1 | 8 | **PARTIAL_VISUAL** |
| `generic` | boolean_composition, structural_progressive_representation | 1/1 | 1/0/1 | 12 | **PARTIAL_VISUAL** |
| `logic` | boolean_composition | 2/2 | 1/0/1 | 8 | **PARTIAL_VISUAL** |
| `network` | graph_traversal, layered_pdu_transform | 3/3 | 4/2/2 | 48 | **PARTIAL_VISUAL** |
| `tree` | tree_traversal | 1/1 | 2/2/1 | 32 | **PARTIAL_VISUAL** |

## Nhận xét người review

### `algorithm` — PARTIAL_VISUAL
- Tiêu chí chưa đạt: RESPONSIVE_PASS
- Cột mảng, con trỏ bước, mã giả và tường thuật đồng bộ; số âm/thập phân và nhãn tên tiếng Việt hiển thị đúng; binary search thu hẹp khoảng rõ. HẠ ĐIỂM vì VIS-003.

### `binary` — PARTIAL_VISUAL
- Tiêu chí chưa đạt: RESPONSIVE_PASS
- Hàng trọng số/bit và bảng chia-lấy-dư rõ. HẠ ĐIỂM vì VIS-003.

### `generic` — PARTIAL_VISUAL
- Tiêu chí chưa đạt: LAYOUT_PASS, RESPONSIVE_PASS
- Sau hai bản sửa: nhãn dài so le nên không còn dồn thành khối chữ không đọc được; badge kỹ thuật GENERIC đã thay bằng 'MÔ PHỎNG THEO MÔ TẢ'. VẪN CHẬT khi nhiều nhãn rất dài nằm cùng hàng ngang — đọc được nhưng sát nhau; không sửa thêm được nếu không đụng `state.pos` (§10 cấm sửa engine state). Engine authenticity GIỮ NGUYÊN PARTIAL — audit thị giác KHÔNG nâng hạng; tiêu đề không giả nhận diện thuật toán, phụ đề nói rõ 'Mô phỏng tổng quát (AI tự dựng)'.

### `logic` — PARTIAL_VISUAL
- Tiêu chí chưa đạt: RESPONSIVE_PASS
- Cổng, dây nối và bảng chân trị rõ; and_gate là module khám phá (không timeline) nên chỉ có ảnh initial — đúng hợp đồng. HẠ ĐIỂM vì VIS-003.

### `network` — PARTIAL_VISUAL
- Tiêu chí chưa đạt: RESPONSIVE_PASS
- Sau bản sửa nhãn: mọi cạnh hiện rõ (không tái phát phantom token), nhãn dài xuống dưới nút nên không còn bị nút cắt ngang, hàng đợi/ngăn xếp đúng biến thể, thứ tự thăm hiện dần, đích không tới được không bị dựng đường giả. HẠ ĐIỂM vì lỗi layout DÙNG CHUNG ở viewport hẹp (xem VIS-003), không phải lỗi của renderer này.

### `tree` — PARTIAL_VISUAL
- Tiêu chí chưa đạt: RESPONSIVE_PASS
- Regression bản sửa nhãn dài VR1 GIỮ NGUYÊN: cạnh trái/phải rõ, nhãn 11 nút tiếng Việt không chồng nút, canvas co giãn, ngăn xếp/hàng đợi đúng biến thể, thứ tự duyệt hiện dần. Cây một nút và cây lệch sâu đều đúng. HẠ ĐIỂM vì VIS-003 (layout hẹp dùng chung).

