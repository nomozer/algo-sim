# Review độc lập — LOCAL, 2026-10-14

Người review: một subagent riêng (cùng họ mô hình, ngữ cảnh mới), chỉ đọc, phạm vi `09b29d48..38c304ce`. **Phán quyết:
NONBLOCKING**, nhưng nêu một hồi quy trình bày thật (C1) và các chỗ bằng chứng/công bố chưa đủ. Độc lập người đánh giá:
một phần (khác phiên, không phải người).

| # | phát hiện | xử lý |
|---|---|---|
| C1 | Phép dời đẩy chân đường cao (`project_onto(S, mặt ⊆ đáy)`) ra sau khối ⇒ mất bước `CONSTRUCT_HEIGHT` "Dựng chiều cao SH" với chóp có hình chiếu đỉnh; corpus không có ca nào như vậy, O3 không đòi chiều cao | **tái hiện** (trước: base → height → lateral; sau: không height); RED `1cd29fe8` → sửa `a5a0797c`: điểm mà CHÍNH `formation._chan_ung_vien` nhận làm chân được giữ trước khối; thêm so sánh "vai trò dựng không mất" với nền `5bd28d73` cho cả 36 ca |
| C2 | Phép tách tô-pô đúng; nhiều khối ⇒ O2 thoả rỗng vì tập cho phép là hợp | ghi giới hạn (không có ca nhiều khối trong Hybrid) |
| C3 | `PrismTopologySpec` mặc định `lateral_structure="right"` cả với lăng trụ xiên; chỉ nhận ′, không nhận ’; docstring cũ | sửa `a5a0797c` (+ test lăng trụ xiên, ’); không ảnh hưởng đáp số |
| C4 | Nhánh tịnh tiến giả định thứ tự `depends` = [điểm, vectơ]; viết sau bộ lọc snake_case của scene3d | sửa: kiểm kiểu `point3`, `vector3`; ký hiệu/vai đều từ `display_names` (không có id máy) |
| K1 | O3 không đòi "bước riêng" | sửa `1cd29fe8`: từng vai trò ở một bước riêng, đúng thứ tự |
| K2 | O4 là kiểm chuỗi con; không kiểm chiều vectơ | sửa: đòi "vectơ {gốc}{điểm mới}"; ký hiệu một chữ vẫn là kiểm yếu — ghi giới hạn; O5/O6 gần như tất yếu (bố cục chạy trước `bien_dich`) — công bố |
| E1 | Tập kiểm thứ tự bị dùng để lái một sửa (B02 → `c217aade`) | công bố ở `report.md`: held-out đúng nghĩa = lượt đầu tại `b0a853a0` (27/28 served PASS); kết quả sau sửa không gọi là held-out; "28 served + 2 refused", không phải "30/30" |
| E2 | Lời khai chạy lại 45/32/30 được commit trước bằng chứng; heldout 32 bị dùng | chạy lại ở product cuối, commit cùng tài liệu; khai heldout 32 là phép kiểm BẤT BIẾN (một lần dùng), không phải held-out mới |
| E3 | Receipt đo thiếu commit/candidate; candidate trung gian bị ghi đè | script ghi `git_head`, `git_dirty_paths`, `candidate_tree_hash`; divergence ghi `intermediate_candidates`; commit `0dd7f4cc` đã sửa test RED tiền đăng ký (nó kiểm nhầm `RequestContract` nên không thể xanh) — công bố ở đây |

Xác nhận của review: phép tách tô-pô không bao giờ đọc tên trước khi định nghĩa; `_bien_dich_mat_cat`, phép đo,
`kiem_mat_cat` không bị ảnh hưởng; khai prism chỉ từ ký hiệu nguồn, không thể khớp sai; lời kể đúng nghĩa tịnh tiến
(H = M + (C − B)); freeze/divergence/cache đúng luật; `main.py`/`pipeline.py` không nhập module Hybrid.
