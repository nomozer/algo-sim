# W4B-2R — BẰNG CHỨNG: BIỂU DIỄN THEO CƠ CHẾ + VÒNG ĐỜI QUAN SÁT

`THESIS_SCOPE = T2/T3/T4`. Baseline `6f37845`. Audit đi kèm:
`docs/MECHANISM_FIRST_REPRESENTATION_INTERACTION_AUDIT.md` (ma trận 22 dòng).

## 1. Đã đổi gì

| commit | việc |
|---|---|
| `eebc22a` | chính sách biểu diễn có chủ sở hữu khai báo · `packet_routing` → 2D_ONLY · hai guard toàn danh mục |

**Đúng MỘT target đổi chính sách.** Không có wave nào vá 22 renderer bằng tay.

## 2. Chính sách biểu diễn: 21 / 0 / 1

| | số | |
|---|---|---|
| `2D_ONLY` | **21** | |
| `3D_ONLY` | **0** | kết quả HỢP LỆ (§24) — không ép target nào vào ô này |
| `2D_AND_3D_JUSTIFIED` | **1** | `network.protocol_encapsulation` (Z = tầng giao thức) |

Chủ sở hữu: `renderer.ts::representationPolicyOf` +
`representationPolicyProblems`. **Dẫn xuất từ hai thứ module vốn khai**
(`supportedVisualModes` + `threeD.role`) — không thêm trường thứ ba phải đồng bộ
tay. Điều kiện của "cả hai" là **`threeD.role === "pedagogical"`**, không phải
sự tồn tại của renderer.

`network.packet_routing` bị hạ về 2D_ONLY bằng **lời khai của chính nó**:
`architectural_poc` + `meaningOfZ = "bố cục, không mang nghĩa khái niệm"`.
`ui3d.tsx` và `render3d.test.tsx` đã gỡ khỏi kho mã.

## 3. Bằng chứng trình duyệt — Chrome thật, CDP

`frontend/scripts/capture-w4b2r-representation.mjs` ·
artifact `docs/evaluation/m17/w4b2r-representation/`

**39/39 PASS × 3 viewport** (`1920×1080` · `1366×768` · `768×900`), một tiến
trình Vite MỚI, `--strictPort`, cùng một ảnh chụp mã nguồn.

Bảy bài làm chứng chọn theo **cơ chế** (§31), không theo ảnh người dùng gửi:

| bài | cơ chế | chính sách | toggle | READY/PAUSED | chạy trọn không trả lời |
|---|---|---|---|---|---|
| `algorithm.binary_search` | thu hẹp khoảng | 2d_only | **không** | ✓ | ✓ |
| `algorithm.insertion_sort` | giữ/dời/chèn | 2d_only | **không** | ✓ | ✓ (33 bước) |
| `logic.and_gate` | tín hiệu qua cổng | 2d_only | **không** | ✓ | cảnh khám phá (1 khung) |
| `binary.decimal_to_binary` | trọng số vị trí | 2d_only | **không** | ✓ | cảnh khám phá |
| `generic.rule_scene` | cảnh do DSL mô tả | 2d_only | **không** | ✓ | cảnh khám phá |
| `network.packet_routing` | topology + đường đi | **2d_only ⬅ ĐỔI** | **không** | ✓ | ✓ (4 bước) |
| `network.protocol_encapsulation` | **tầng giao thức** | **2d_and_3d_justified** | **CÓ** `[2D][3D]` | ✓ | ✓ (9 bước) |

Ảnh `network_packet_routing-1-ready.png` cho thấy tiêu đề phụ nay đọc
*"Định tuyến gói tin · từng bước · **2D**"* (trước: `2D / 3D`) và góc phải
**không còn toggle**.

Sidecar đọc `representationPolicyOf`, renderer owner, timeline, capability
**thẳng từ store + `renderer.ts`** — không suy từ DOM.

## 4. Vòng đời Quan sát: ĐÃ ĐÚNG, nay được KHOÁ toàn danh mục

Wave này **không sửa** ba luật dưới đây — nó đo rồi khoá chúng:

| luật | bằng chứng |
|---|---|
| `LEARNER_INITIATES_FIRST_RUN` | `playing` chỉ nhận `true` qua `setPlaying` (nút Play); mọi nhánh nạp đặt `false`. 7/7 bài làm chứng READY/PAUSED trong Chrome |
| `CANONICAL_RUN_CAN_COMPLETE_WITHOUT_PREDICTION` | chạy trọn timeline của MỌI envelope offline bằng `nextStep`; `prediction` vẫn `null` |
| `OBSERVE_REQUIRES_NO_ANSWER` | `nextStep` không đọc `prediction`; `submitPrediction` không đụng cursor |

Trước W4B-2R chúng đúng nhưng chỉ được kiểm gián tiếp ở vài target.

## 5. Tiêm lỗi — 7/8 ĐỎ, khôi phục XANH

| §45 | lỗi tiêm | kết quả |
|---|---|---|
| A | mọi target thành BOTH | **ĐỎ** (4 test) |
| B | thêm toggle 3D cho target 2D_ONLY | **ĐỎ** (4 test) |
| C | Play dừng chờ học sinh trả lời | **ĐỎ** |
| D | ẩn trạng thái Quan sát khi đóng công cụ | **ĐỎ** |
| E | rẽ nhánh chính sách theo chuỗi tiêu đề | **ĐỎ** |
| F | target 3D mất biện minh sư phạm (`poc` mà vẫn bày cả hai) | **ĐỎ** (2 test) |
| G | mở Thí nghiệm trước vòng đời | **KHÔNG ÁP DỤNG** — xem §6 |
| H | what-if chỉ đổi pixel, không đổi engine state | **ĐỎ** (5 test) |

### 5b. Một test XANH VÌ LÝ DO SAI, bắt được trong wave này

`m8-acceptance.test.tsx` **vẫn xanh** sau khi 3D của `packet_routing` bị gỡ.
Nguyên nhân: `setVisualMode("3d")` chỉ ghi một cờ trình bày vào store, còn
`effectiveVisualMode` mới là chỗ rơi về `"2d"` lúc render — nên nó "nghiệm thu
luồng 2D→3D→2D" trên một bài **không có 3D**. Cùng họ với anti-pattern #8.

Đã sửa: bài làm chứng nay **dẫn xuất từ chính sách** (`target duy nhất có
2d_and_3d_justified`) thay vì viết cứng, nên gỡ 3D khỏi nó sẽ đỏ ngay ở bước
chọn bài chứ không âm thầm nghiệm thu một toggle không tồn tại.

## 6. Vì sao KHÔNG dựng `BASELINE_OBSERVED` (§16/§39)

Giữ quyết định W4B-2I (user đã duyệt), lý do vẫn đứng vững:

- Cổng Thí nghiệm **do học sinh tự mở** và khả dụng **từ bước 1** — đã là *tập
  cha* của điều §16 muốn. Thứ chưa có là **ràng buộc**, không phải khả năng.
- Ràng buộc đó **lấy đi quyền**: bắt xem hết mới được thao tác.
- §14 (READY/PAUSED, không tự chạy) — nay đã đo được ở cả 7 bài — tạo đúng
  khoảng lặng để học sinh nhìn trạng thái đầu, mà không khoá gì.
- Bề mặt cam kết đã qua **sáu** wave (W4B-2B→2C→2D→2V→2V/C2→2I). Thêm khoá là
  wave thứ bảy trên cùng một capability — `RULES.md §3c` DEEP_HARDENING.

## 7. Cổng

`vitest 1089/72` · `pytest 1135 passed, 2 skipped` · `tsc -b` + build sạch ·
browser **39/39 × 3 viewport** · `git diff --check` sạch.

> Vitest giảm 1099 → 1089 vì `render3d.test.tsx` (16 test của renderer đã nghỉ)
> bị gỡ, và wave này thêm 16 test mới. Không test nào bị *tắt*.

## 8. Giới hạn — nói thẳng

- **§11/§26 vai trò miền chở bằng CHỮ: CHƯA SỬA.** Ảnh
  `network_packet_routing-1-ready.png` của chính wave này cho thấy
  client/router/isp/server là **bốn hình tròn giống hệt**, chỉ khác màu viền +
  nhãn. Đây là *pattern*, cần đo cả `graph_traversal`/`tree`/`database` rồi sửa
  ở **chủ sở hữu hình dạng dùng chung**. Hoãn có chủ đích: wave này vừa đổi
  chính sách biểu diễn của đúng target đó, gộp thêm một đợt vẽ lại là hai thay
  đổi lớn chồng nhau trên cùng một file, khó quy trách khi hồi quy.
- **7 target `ENGINE_CONTRACT_MISSING`** (`apply` = identity): `algorithm.scan`,
  `bounded_control_flow`, `base_conversion`, `character_encoding`,
  `tree.traversal`, `graph_traversal`, `relational_table_query`. **Không bịa
  tương tác trong UI cho chúng** (§20).
- `tree.traversal` và `algorithm.scan` **không có mẫu offline** ⇒ không vào được
  bộ ảnh trình duyệt. Chính sách của chúng vẫn được guard toàn danh mục phủ
  (guard chạy trên registry, không cần fixture).
- `sum_if`: biến tích luỹ chưa chiếu lên sân khấu (từ W4B-2I).
- **Chưa đo trên người học** — `LEARNER_IMPACT_NOT_EVALUATED`,
  `CURRICULUM_SUPPORT_PARTIAL`.

## 9. Tuyên bố

Được nói: *"AlgoSim chọn biểu diễn 2D hay 3D theo CƠ CHẾ đang mô phỏng; biểu
diễn trình bày state của engine tất định và không quyết định sự thật thuật toán."*

**Bị cấm từ wave này**: *"AlgoSim cung cấp cả 2D lẫn 3D cho mọi mô phỏng."*

## 10. Verdict

```
W4B2R_MECHANISM_FIRST_REPRESENTATION_PARTIAL
— WHOLE_CATALOG_POLICY_FROZEN            22/22 phân loại, guard dẫn xuất từ registry
— NO_2D_3D_BY_DEFAULT                    21 / 0 / 1
— REPRESENTATION_SELECTED_BY_MECHANISM   packet_routing hạ 2D_ONLY bằng lời khai của chính nó
— SHARED_LIFECYCLE_COMPLETE              3 luật Quan sát khoá toàn danh mục
— LEARNER_STARTED_BASELINE_VERIFIED      7/7 bài làm chứng READY/PAUSED trong Chrome
— CANONICAL_OBSERVE_HAS_NO_REQUIRED_QUIZ_GATE
— CONTEXT_REUSE_PRESERVED · RENDERER_TRUTH_OWNERSHIP_UNCHANGED
— DEFERRED: DOMAIN_ROLE_CARRIED_BY_TEXT  (§11/§26 — đo rồi, chưa sửa, lý do ở §8)
— DEFERRED: ENGINE_CONTRACT_MISSING × 7
```

Không dùng COMPLETE: `DOMAIN_ROLE_CARRIED_BY_TEXT` đã **đo được** nhưng chưa sửa,
và 7 target vẫn thiếu hợp đồng tương tác tất định.
