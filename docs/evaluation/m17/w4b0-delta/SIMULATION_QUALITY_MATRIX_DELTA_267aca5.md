# SIMULATION_QUALITY_MATRIX — DELTA tại `267aca5`

**Không thay thế ma trận gốc.** `simulation-mechanism-audit/SIMULATION_QUALITY_MATRIX.md`
chấm tại `cc449d5` và giữ nguyên giá trị lịch sử. Tài liệu này chỉ ghi **những
dòng đã trôi** sau 27 commit, kèm bằng chứng quan sát được tại HEAD.

| | |
|---|---|
| Baseline ma trận gốc | `cc449d5` (2026-08-04) = `origin/main` |
| HEAD lượt này | `267aca5` |
| Khoảng cách | **27 commit** |
| Phương pháp | Chrome thật qua CDP, 1440×1000, đứng giữa timeline (nơi cơ chế đang diễn ra) |
| Fixture | lấy từ `frontend/scripts/visual-stress-audit.mjs` và file test production |
| Production AI call | **0** (xem `DECISION_GATE.md §C`) |

**Không tin commit message.** Mỗi dòng dưới đây có một phép đo trong trình duyệt;
`candidate fix` chỉ là *giả thuyết* về commit nào đã chạm tới, còn verdict đến từ
phép đo.

## 1. Bảng delta

| Target | Kết luận cũ (`cc449d5`) | Bằng chứng tại HEAD | Trạng thái | Lý do |
|---|---|---|---|---|
| `algorithm.insertion_sort` | **B+** — *"giá trị đang cầm (4) KHÔNG có trên sân khấu; ô trống hiện thành số 7 lặp lại"* → **thiết kế lại** | `.hold-tray` có mặt; **1 ô trống** vẽ bằng khung nét đứt + chữ "trống" | **RESOLVED** | `bb992eb` vẽ quân bài đang giữ và ô trống; renderer đọc `snapshot.ids` thay vì chỉ `array` |
| `algorithm.bounded_control_flow` | **B−** — *"toàn bộ vòng lặp: quỹ đạo biến, biên dừng, cạnh quay lại, tích luỹ đều ẩn"* → **thiết kế lại sân khấu** | 1 SVG trên sân khấu; văn bản có đủ *lượt · vòng · lặp* | **RESOLVED** | `04b68e1` dựng biểu diễn vòng lặp |
| `tree.traversal` | **B+** — *"ngăn xếp chỉ là dòng chữ"* → **thiết kế lại: vẽ ngăn xếp** | `.frontier.frontier-stack`, 2 ô, chữ *"NGĂN XẾP (LIFO) · VỪA LẤY RA B · ĐỈNH A · LIFO — đẩy vào và lấy ra đều ở đỉnh"* | **RESOLVED** | `722acea` + `1372a8d` (frontier view dùng chung) |
| `network.graph_traversal` | **B** — *"hàng đợi chỉ là dòng chữ; **không cạnh nào được tô**"* → **thiết kế lại: vẽ hàng đợi + cạnh đang đi** | `.frontier.frontier-queue`, **4 ô** — nhưng **0/5 cạnh** được nhấn (stroke-width < 2.5) | **IMPROVED_PARTIAL** | `33956bd` vá vế *hàng đợi*; vế *cạnh đang đi* **chưa** |
| `logic.boolean_dag` | **A−** — *"không chú giải màu; xanh lá mang HAI nghĩa"* | `.stage-legend` có 4 mục: *tín hiệu 1 · tín hiệu 0 · viền đậm = cổng đang tính · ? chưa tới lượt* | **RESOLVED** | `e3bf406` chú giải dùng chung suy từ trace |
| `logic.and_gate` | **A−** — *"không chú giải màu"* | **không có** `.stage-legend` | **STILL_PRESENT** | chú giải dùng chung chưa áp cho module này |
| `binary.base_conversion` | **A−** — *"không đánh dấu hàng đang tính"* | 3 hàng bảng, **0 hàng** mang lớp `is-current`/`is-active` | **STILL_PRESENT** | không commit nào chạm |
| `database.relational_table_query` | **A−** — *"tầng đang chạy không nổi bật trong dải chip"* | 4 chip tầng, **0 chip** được nhấn | **STILL_PRESENT** | không commit nào chạm |
| `network.packet_routing` | **B+** — *"đoạn đã đi vs còn lại không phân biệt; không có hướng"* | 6 cạnh, **0 lớp phân biệt**, **0 mũi tên**, **không chú giải** | **STILL_PRESENT** | không commit nào chạm |

**Tổng: RESOLVED 4 · IMPROVED_PARTIAL 1 · STILL_PRESENT 4.**

## 2. Ba `OBVIOUS_PRESENTATION_CORRECTNESS_RISK` của ma trận gốc

Ma trận gốc nêu ba rủi ro trình bày, tách riêng khỏi bảng chấm:

| Rủi ro gốc | Trạng thái tại HEAD | Bằng chứng |
|---|---|---|
| `insertion_sort` — số lặp + dữ liệu biến mất | **RESOLVED** | quân bài đang giữ nằm ngoài dãy trong `.hold-tray`; ô nó để lại vẽ thành ô trống |
| `tree.traversal` — cạnh tô không khớp câu thuyết minh | **NOT_REPRODUCIBLE trong lượt này** | phép đo của lượt này nhắm ngăn xếp, không đối chiếu cạnh↔thuyết minh; **không kết luận** |
| toàn catalog — một màu nhiều nghĩa, không chú giải | **IMPROVED_PARTIAL** | `StageLegend` dùng chung đã có (`e3bf406`) và nghĩa theo từng bài đã sửa (`bec90a9`), nhưng `and_gate` vẫn không có chú giải |

## 3. Các dòng KHÔNG đo trong lượt này

Bốn cụm dưới đây đã có bằng chứng nghiệm thu riêng, mới hơn ma trận gốc; lượt này
**trích lại** thay vì đo lần nữa:

| Dòng cũ | Bằng chứng thay thế |
|---|---|
| `bubble_sort` **A−** *"hành động đổi chỗ chỉ suy ra từ hai trạng thái, không được diễn ra"* | `37fc481` — direct action "Đổi chỗ hai phần tử này"; nghiệm thu Chrome 477/477 (3 target × 3 viewport × 17 trạng thái) |
| `selection_sort` **A−** *"ranh giới đã chọn xong mờ hơn bubble"* | vùng hành động nêu *"Phần chưa sắp vị trí 1–6"* — đo trong cùng lượt nghiệm thu |
| `linear_search` **A−** *"không có vùng còn lại rõ như binary_search"* | `3c766cf`/`516ed67` — `SearchActionZone` mang chi phí: đã so sánh · còn lại · xấu nhất |
| `scan` **A−** *"không có ô dự đoán"* | **CHƯA XÁC MINH** — `algorithm.scan` đi qua `makeScanModule` (engine M12) chứ không phải `makeAlgorithmModule`, nên vùng hành động của cụm quét dãy **không** tự động áp cho nó. Xem `ISSUE_REGISTER.md` |

Các dòng còn lại của ma trận gốc (`find_max`, `find_min`, `count_if`, `sum_if`,
`binary_search`, `decimal_to_binary`, `character_encoding`,
`protocol_encapsulation`, `generic.rule_scene`) **không có commit nào chạm vào cơ
chế trình bày** trong 27 commit, nên kết luận cũ được giữ nguyên mà không đo lại.
Riêng bốn bài quét dãy có đổi **chú giải** (`bec90a9`) — đổi theo hướng đúng
nghĩa hơn, đã khoá bằng test.

## 4. Giới hạn của phép đo lượt này

1. **Chỉ 1440×1000, chỉ một checkpoint** (giữa timeline). Ma trận gốc chụp
   initial/mechanism-active/final. Ảnh AFTER ở đây ghép với ảnh
   `-2-mechanism-active` của bộ gốc.
2. **Probe của `insertion_sort` báo "giá trị lặp = 3, 4, 2" — đó là nhiễu của
   phép đo, không phải phát hiện.** Probe gom mọi `<text>` số trong SVG, nên nhãn
   chỉ số dưới mỗi cột (0…5) trùng với giá trị phần tử. Không dùng số này để kết
   luận gì.
3. **`RESOLVED` ở đây nghĩa là "dấu hiệu quan sát được đã có mặt"**, không phải
   "cơ chế đã dạy đúng". Cái sau cần giáo viên và học sinh — xem §I của
   `DECISION_GATE.md`.
4. `network.graph_traversal` được chấm theo **cả hai vế** của kết luận cũ. Vá một
   vế rồi tuyên bố RESOLVED là overclaim; đó là lý do nó ở `IMPROVED_PARTIAL`.
