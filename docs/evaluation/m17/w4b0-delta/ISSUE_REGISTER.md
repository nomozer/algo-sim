# ISSUE_REGISTER — W4B-0 tại `267aca5`

Mỗi mục ghi bằng chứng baseline, bằng chứng tại HEAD, nơi sửa và bằng chứng
nghiệm thu cần có. Mức ảnh hưởng theo thang của lượt: **P0** sai kiến thức hoặc
giả vờ đúng · **P1** renderer lệch engine hoặc kết quả tất định sai · **P2** cơ
chế học không nhìn thấy / xử lý kém · **P3** wording, nhãn, UX nhỏ.

**Không có P0 hay P1 nào trong lượt này.**

## STALE_AUDIT_CLAIM

| ID | Kết luận cũ | Bằng chứng HEAD | Mức | Xử lý |
|---|---|---|---|---|
| `SA-1` | `insertion_sort` cần **thiết kế lại** (dữ liệu biến mất, số lặp) | `.hold-tray` + 1 ô trống | — | **Đóng.** Ghi RESOLVED ở ma trận delta |
| `SA-2` | `bounded_control_flow` cần **thiết kế lại sân khấu** | 1 SVG + từ khoá vòng lặp | — | **Đóng.** RESOLVED |
| `SA-3` | `tree.traversal` cần **vẽ ngăn xếp** | `.frontier-stack`, 2 ô, giải thích LIFO | — | **Đóng.** RESOLVED |
| `SA-4` | `boolean_dag` không có chú giải màu | `.stage-legend` 4 mục | — | **Đóng.** RESOLVED |
| `SA-5` | **`pedagogical_alignment_audit`: "ba family mới nhất không có case nào khai `learning_objective`"** | **0/100 eval item thiếu `learning_objective` tại HEAD** | — | **Đóng — kết luận đã hết đúng.** Xem `CM-1` cho vấn đề THẬT còn lại |

> `SA-5` là lý do lượt này tồn tại. Ở lượt trước tôi đã trích kết luận cũ này và
> đề xuất "đóng lỗ `learning_objective`" như việc tiếp theo. **Đề xuất đó sai** —
> lỗ ấy đã đóng từ trước. Vấn đề thật có hình dạng khác (xem `CM-1`).

## MECHANISM_VISIBILITY

| ID | Target | Vấn đề | Bằng chứng | Mức | Nơi sửa |
|---|---|---|---|---|---|
| `MV-1` | `network.graph_traversal` | cạnh đang đi **không được tô** — hàng đợi đã vẽ nhưng đường đi vẫn không nhìn thấy | `0/5` cạnh có `stroke-width ≥ 2.5` | **P2** | `domains/network/traverse-module.tsx` |
| `MV-2` | `network.packet_routing` | đoạn đã đi vs còn lại không phân biệt; không hướng; không chú giải | `0` lớp cạnh · `0` mũi tên · `0` mục chú giải | **P2** | `domains/network/index.ts` |
| `MV-3` | `binary.base_conversion` | không đánh dấu hàng đang tính trong bảng chia | `0/3` hàng có lớp active | **P3** | `domains/binary/convert-module.tsx` |
| `MV-4` | `database.relational_table_query` | tầng pipeline đang chạy không nổi bật | `0/4` chip active | **P3** | `domains/database/table-module.tsx` |
| `MV-5` | `logic.and_gate` | không có chú giải màu — `StageLegend` dùng chung chưa áp | `.stage-legend` vắng mặt | **P3** | `domains/logic/index.ts` |

`MV-1` và `MV-2` cùng một bệnh: **cạnh của đồ thị/mạng không mang trạng thái**.
Sửa chung một primitive rẻ hơn sửa hai chỗ.

## CURRICULUM_METADATA

| ID | Vấn đề | Bằng chứng tại HEAD | Mức | Nơi sửa |
|---|---|---|---|---|
| `CM-1` | **Ba target không có eval item nào**: `algorithm.selection_sort`, `binary.base_conversion`, `network.graph_traversal` | catalog 22 target · dataset khai 19 | **P2** | `backend/app/evaluation/datasets/*.py` |
| `CM-2` | Bốn target chỉ có **1** eval item: `binary.character_encoding`, `database.relational_table_query`, `logic.boolean_dag`, `tree.traversal` | đếm theo `expect_simulation_id` | **P3** | như trên |
| `CM-3` | 16/100 item không khai `expect_simulation_id` | có thể hợp lệ (ca từ chối / ngoài catalog) — **chưa xác minh** | **P3** | cần đọc từng ca trước khi kết luận |

`CM-1` là hình dạng thật của thứ audit cũ gọi là "lỗ neo chương trình". Không
phải *thiếu trường metadata* mà là *thiếu ca đánh giá*. `selection_sort` là target
được thêm sau lượt audit đó nên chưa từng có ca; hai target còn lại thì có sẵn
nhưng chưa được phủ.

## EVIDENCE_GAP

| ID | Vấn đề | Mức | Ghi chú |
|---|---|---|---|
| `EG-1` | `algorithm.scan` — kết luận cũ *"không có ô dự đoán"* **chưa xác minh tại HEAD** | **P2** | `algorithm.scan` chạy qua `makeScanModule` (engine M12) chứ không phải `makeAlgorithmModule`, nên `ScanActionZone` của cụm quét dãy **không** tự áp cho nó. Cần một phép đo riêng |
| `EG-2` | `tree.traversal` — rủi ro cũ *"cạnh tô không khớp câu thuyết minh"* **không tái hiện được** trong lượt này | **P3** | phép đo lượt này nhắm ngăn xếp; chưa đối chiếu cạnh ↔ thuyết minh |
| `EG-3` | Delta chỉ đo ở **1440×1000**, một checkpoint | **P3** | viewport hẹp dựa vào bằng chứng của các lượt trước |
| `EG-4` | `mechanism-fix/` và `frontier-fix/` **không khai baseline SHA** | **P3** | manifest ghi "không xác định" thay vì suy đoán |

## LAYOUT · ACCESSIBILITY · ENGINE_CORRECTNESS · RENDERER_STATE_MISMATCH

**Không có mục nào.** Chín ca đo trong lượt này không phát hiện lệch giữa
renderer và state canonical, không tràn ngang, không control bị che. Lỗi ghim
đáy của shell đã được vá và có guard ở lượt W3B (`.panel-center` bù padding,
smoke 5 target × 2 viewport, 130/130).
