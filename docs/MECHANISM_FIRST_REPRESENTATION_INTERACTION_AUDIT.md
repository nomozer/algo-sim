# W4B-2R — BIỂU DIỄN THEO CƠ CHẾ + TƯƠNG TÁC: AUDIT TOÀN DANH MỤC

`THESIS_SCOPE = T2/T3/T4`. Baseline `6f37845`. Tài liệu **audit** — số sống ở
`docs/CURRENT_STATE.md`, bằng chứng ở
`docs/MECHANISM_FIRST_REPRESENTATION_INTERACTION_EVIDENCE.md`.

## 1. Luật mới: chính sách biểu diễn

**2D và 3D là LỰA CHỌN BIỂU DIỄN, không phải tầng đúng đắn.** Một target chỉ
được bày cả hai khi mỗi bên chở một nghĩa khác nhau bảo vệ được. Trạng thái bị
cấm là `2D_AND_3D_BY_DEFAULT` — có 3D chỉ vì sản phẩm đã có renderer 3D.

Chủ sở hữu: `simulations/renderer.ts` — `representationPolicyOf()` (phân loại)
và `representationPolicyProblems()` (phán quyết hợp lệ).

**Không thêm trường `representationPolicy` vào 22 module.** Chính sách đã nằm
sẵn trong hai thứ module VỐN khai: `supportedVisualModes` (được cấp mode nào) và
`threeD.role` (chiều sâu nghĩa là gì). Thêm trường thứ ba là dựng nguồn sự thật
thứ hai phải giữ đồng bộ bằng tay — `ARCHITECTURE_MAP §8` #1. Ở đây chỉ **đặt
tên** cho tổ hợp đã có.

Điều kiện của `2d_and_3d_justified` là **lời khai `threeD.role === "pedagogical"`**,
không phải sự tồn tại của renderer.

## 2. Kết quả: 21 / 0 / 1

| chính sách | số | target |
|---|---|---|
| `2D_ONLY` | **21** | tất cả trừ dòng dưới |
| `3D_ONLY` | **0** | *(không có — và đây là kết quả HỢP LỆ, §24)* |
| `2D_AND_3D_JUSTIFIED` | **1** | `network.protocol_encapsulation` |

**Đúng một target đổi chính sách: `network.packet_routing` (2D+3D → 2D_ONLY).**

Bằng chứng kết tội đến từ **chính module đó**: nó khai
`threeD.role = "architectural_poc"` với
`meaningOfZ = "phân tách nút trên/ngoài tuyến (bố cục), không mang nghĩa khái niệm"`.
Tức sản phẩm đã tự thừa nhận trục Z ở đây không chở ngữ nghĩa nào. Cơ chế của
bài là **topology + đường đi + khả năng tới được**, cả ba đọc trọn trên mặt
phẳng. Giữ toggle vì "đã có renderer 3D" đúng là định nghĩa của `BY_DEFAULT`.

Không mất gì về kiến trúc: `protocol_encapsulation` (Z = **tầng giao thức**) vẫn
làm chứng cho bất biến #16/#18 — 2D và 3D dùng chung một state.

## 3. Ma trận 22 target

`OO` = OBSERVE_ONLY · `DM` = DIRECT_MANIPULATION · `PO` = PREDICTION_OPTIONAL ·
`WI` = WHAT_IF_INPUT · `WS` = WHAT_IF_STRUCTURE · `EC` = ENGINE_CONTRACT_MISSING.

| # | target | họ / cơ chế | biểu diễn | vì sao | Observe cần trả lời? | tương tác | engine tính lại |
|---|---|---|---|---|---|---|---|
| 1 | `algorithm.find_max` | quét dãy — cực trị + bất biến vùng đã duyệt | 2D_ONLY | dãy là 1 chiều; Z không thêm gì | **không** | PO · DM(kề) · WI | có (nhánh) |
| 2 | `algorithm.find_min` | như trên | 2D_ONLY | như trên | **không** | PO · DM(kề) · WI | có |
| 3 | `algorithm.count_if` | quét dãy — vị từ + biến đếm | 2D_ONLY | như trên | **không** | PO · DM(kề) · WI | có |
| 4 | `algorithm.sum_if` | quét dãy — vị từ + tích luỹ | 2D_ONLY | như trên | **không** | PO · DM(kề) · WI | có · ⚠️ tích luỹ chưa chiếu lên sân khấu |
| 5 | `algorithm.linear_search` | tìm tuần tự — chi phí so sánh | 2D_ONLY | vị trí + chi phí là 1 chiều | **không** | PO · **DM(sân khấu)** · WI | có |
| 6 | `algorithm.binary_search` | thu hẹp khoảng đã sắp | 2D_ONLY | khoảng/mid/nửa bị loại đọc rõ trên trục ngang | **không** | PO · **DM(sân khấu)** · WI | có |
| 7 | `algorithm.bubble_sort` | đổi chỗ cặp kề | 2D_ONLY | so sánh cặp kề là quan hệ 1 chiều | **không** | PO · DM(kề) · WI | có |
| 8 | `algorithm.selection_sort` | chọn cực trị vùng chưa sắp | 2D_ONLY | như trên | **không** | PO · DM(kề) · WI | có |
| 9 | `algorithm.insertion_sort` | giữ + dời + chèn | 2D_ONLY | ô trống/quân đang giữ đã có ngữ pháp riêng 2D | **không** | PO · DM(kề) · WI | có |
| 10 | `algorithm.scan` | duyệt tổng quát theo mô tả | 2D_ONLY | dãy 1 chiều | **không** | OO | — (`apply` = identity) |
| 11 | `algorithm.bounded_control_flow` | vòng lặp có chặn — biến + điều kiện | 2D_ONLY | luồng điều khiển đọc bằng mã giả + biến | **không** | OO · EC | — |
| 12 | `binary.decimal_to_binary` | trọng số vị trí nhị phân | 2D_ONLY | hàng bit là 1 chiều | **không** | WI (bật/tắt bit) | có |
| 13 | `binary.base_conversion` | chia lấy dư | 2D_ONLY | chuỗi phép chia là danh sách | **không** | OO · EC | — |
| 14 | `binary.character_encoding` | ký tự → code point → nhị phân | 2D_ONLY | chuỗi ánh xạ tuyến tính | **không** | OO · EC | — |
| 15 | `logic.and_gate` | cổng logic — tín hiệu vào/ra | 2D_ONLY | sơ đồ cổng là ngữ pháp 2D chuẩn của môn | **không** | **WI (bật/tắt đầu vào)** | có |
| 16 | `logic.boolean_dag` | mạch nhiều cổng — lan truyền tín hiệu | 2D_ONLY | DAG phẳng đọc tốt; Z làm rối dây | **không** | **WI (bật/tắt đầu vào)** | có |
| 17 | `tree.traversal` | quan hệ cấu trúc + frontier | 2D_ONLY | cây vẽ phẳng là quy ước SGK; Z không thêm quan hệ | **không** | OO · EC | — |
| 18 | `network.graph_traversal` | BFS/DFS — frontier hàng đợi/ngăn xếp | 2D_ONLY | đồ thị phẳng + frontier là bảng | **không** | OO · EC | — |
| 19 | `network.packet_routing` | topology + đường đi + khả năng tới được | **2D_ONLY** ⬅ **ĐỔI** | module tự khai Z = bố cục, không nghĩa | **không** | PO · **WS** (nối/ngắt/về gốc) | **có** (`recompute` BFS) |
| 20 | `network.protocol_encapsulation` | đóng/mở gói qua **tầng** giao thức | **2D_AND_3D_JUSTIFIED** | **Z = tầng giao thức** — nghĩa khái niệm thật | **không** | PO | — |
| 21 | `database.relational_table_query` | lọc theo vị từ trên bảng | 2D_ONLY | bảng vốn là lưới 2 chiều | **không** | OO · EC | — |
| 22 | `generic.rule_scene` | cảnh do DSL mô tả (luật tất định) | 2D_ONLY | DSL khai toạ độ miền 2D (0–100) | **không** | DM · **WS** (patch spec) | có |

22 dòng, không trùng, không thiếu — guard dẫn xuất từ registry
(`representation-policy-w4b2r.test.ts`), **không** chép tay danh sách.

## 4. Ba luật vòng đời: ĐÃ ĐÚNG TỪ TRƯỚC, nay có guard

Đo, không đoán:

| luật | trạng thái | bằng chứng |
|---|---|---|
| `LEARNER_INITIATES_FIRST_RUN` | **đã đúng** | `playing` chỉ nhận `true` qua `setPlaying` (nút Play); mọi nhánh nạp đặt `playing: false` |
| `CANONICAL_RUN_CAN_COMPLETE_WITHOUT_PREDICTION` | **đã đúng** | chạy trọn timeline của MỌI envelope offline bằng `nextStep`, `prediction` vẫn `null` |
| `OBSERVE_REQUIRES_NO_ANSWER` | **đã đúng** | `nextStep` không đọc `prediction`; `submitPrediction` không đụng cursor |

Wave này **không sửa** ba luật đó — nó **khoá** chúng trên toàn danh mục
(`observe-lifecycle-w4b2r.test.ts`). Trước đây chúng đúng nhưng chỉ được kiểm
gián tiếp ở vài target.

### 4b. Vì sao KHÔNG dựng `BASELINE_OBSERVED` (§16/§39)

Giữ nguyên quyết định W4B-2I (user đã duyệt), và lý do vẫn đứng vững:

- Cổng Thí nghiệm hiện **do học sinh tự mở**, khả dụng **từ bước 1** — tức đã là
  *tập cha* của điều §16 muốn ("khả dụng sau baseline"). Thứ duy nhất chưa có là
  **ràng buộc**, không phải khả năng.
- Ràng buộc đó **lấy đi quyền**: bắt xem hết mới được thao tác.
- §14 (READY/PAUSED, không tự chạy) đã tạo đúng khoảng lặng để học sinh nhìn
  trạng thái đầu, mà không cần khoá gì.
- Bề mặt cam kết đã qua W4B-2B → 2C → 2D → 2V → 2V/C2 → 2I. Thêm khoá là wave
  thứ bảy trên cùng một capability — `RULES.md §3c` DEEP_HARDENING.

Hệ quả: **fault §45-G không áp dụng** (chính sách cố ý không đòi baseline).

## 5. Phát hiện chưa xử lý ở wave này

- **§11/§26 vai trò miền chở bằng CHỮ.** `packet_routing` vẽ client/router/isp/
  server bằng **bốn hình tròn giống hệt**, chỉ khác màu viền + nhãn chữ. Đây là
  *pattern*, không phải lỗi một bài — cần đo cả `graph_traversal`, `tree`,
  `database` trước khi sửa, và sửa ở **chủ sở hữu hình dạng dùng chung**, không
  vá riêng network. **Hoãn có chủ đích**: wave này đã đổi chính sách biểu diễn
  của chính target đó; gộp thêm một đợt vẽ lại là hai thay đổi lớn chồng nhau
  trên cùng một file, khó quy trách khi hồi quy.
- **7 target `ENGINE_CONTRACT_MISSING`** (`apply` = identity): `algorithm.scan`,
  `bounded_control_flow`, `base_conversion`, `character_encoding`,
  `tree.traversal`, `graph_traversal`, `relational_table_query`. **Không bịa
  tương tác trong UI cho chúng** (§20).
- `sum_if`: biến tích luỹ chưa chiếu lên sân khấu (REPRESENTATION_BLOCKED, đã
  ghi từ W4B-2I).

## 6. Tuyên bố được phép

*"AlgoSim chọn biểu diễn 2D hay 3D theo CƠ CHẾ đang mô phỏng; biểu diễn trình
bày state của engine tất định và không quyết định sự thật thuật toán."*

**Bị cấm** (đổi từ wave này): *"AlgoSim cung cấp cả 2D lẫn 3D cho mọi mô phỏng."*
Giữ nguyên `LEARNER_IMPACT_NOT_EVALUATED`, `CURRICULUM_SUPPORT_PARTIAL`.
