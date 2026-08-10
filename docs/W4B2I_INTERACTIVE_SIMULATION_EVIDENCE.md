# W4B-2I — BẰNG CHỨNG: THAO TÁC TRÊN SÂN KHẤU + THÍ NGHIỆM CẤU TRÚC

`THESIS_SCOPE = T3`. Baseline `fc0634a` → HEAD wave này. Audit đi kèm:
`docs/W4B2I_INTERACTION_MODEL_AUDIT.md` (đọc §1 trước — nó đính chính tiền đề).

## 1. Đã làm gì

| commit | việc |
|---|---|
| `96c3075` | audit: ma trận direct-9 + what-if-22, bảng sở hữu, lý do BỎ `BASELINE_OBSERVED` |
| `8ddf93a` | `bubble_sort` + `selection_sort` vào cổng Thí nghiệm — khép 7/9 → **9/9** |
| `ebed0b3` | họ tìm kiếm: hành động gắn vào **chính các cột**, có bàn phím |
| `fce4f39` | `network.packet_routing`: what-if cấu trúc + trạng thái **không tới được** |

**KHÔNG làm** (có chủ đích, xem audit §1b): cổng `BASELINE_OBSERVED`.

## 2. Vì sao không có `BASELINE_OBSERVED`

Bản yêu cầu mô tả sản phẩm là "dừng ở bước quyết định, bắt trả lời rồi mới chạy
tiếp". Đọc mã thì **tiền đề đó sai**: `nextStep` không đọc `prediction`
(`store.ts:333`), tự chạy là `setInterval` không cổng (`SimulationControls.tsx:38`),
`PredictionBar` trả `null` khi `busy` và mặc định thu gọn, `submitPrediction` chỉ
ghi `store.prediction`. **Năm** bất biến §54 đã đúng và đã có test khoá từ trước.

Dựng thêm một cổng "xem hết mới được thao tác" sẽ **lấy đi** quyền (nay học sinh
mở Thí nghiệm được ngay bước 1), và là **wave thứ sáu** trên cùng một capability
(W4B-2B → 2C → 2D → 2V → 2V/C2) — `RULES.md §3c` gọi đó là DEEP_HARDENING. User
đã duyệt bỏ.

## 3. Bằng chứng trình duyệt — Chrome thật, CDP

`frontend/scripts/capture-w4b2i-interaction.mjs` ·
artifact: `docs/evaluation/m17/w4b2i-scene-interaction/`

**20/20 PASS** ở cả ba viewport: `1920×1080` · `1366×768` · `768×900`.

### A. `binary_search` — hành động về đúng chỗ nó tác động

| ảnh | chứng minh |
|---|---|
| `A1-observe-baseline` | Quan sát: **0** vùng bấm, **0** hàng nút, `svg role="img"` |
| `A2-experiment-open-scene-regions` | mở Thí nghiệm ⇒ **3 vùng bấm trên chính các cột**: `Tìm tiếp ở nửa TRÁI` (cột 1–4) · `Chính là phần tử giữa` (cột 5) · `Tìm tiếp ở nửa PHẢI` (cột 6–10). Hàng nút rời **biến mất** |
| `A3-keyboard-focus` | focus bàn phím vào vùng đầu tiên; `3/3` vùng có `tabindex="0"` |
| `A4-after-scene-action` | bấm sai ⇒ engine chấm `incorrect`, `JSON.stringify(active.state)` **không đổi một ký tự** |

`svg` đổi `role` `img` → `group` khi có vùng bấm — nếu không, mọi vùng sẽ **tàng
hình** với trình đọc màn hình, đúng cái bẫy mà một hàng nút không có.

### B. `packet_routing` — sửa mô hình, engine tính lại

| ảnh | chứng minh |
|---|---|
| `B1-network-baseline` | tuyến gốc `client→router→isp→server` do BFS dựng |
| `B2-network-tool-open` | mở Thí nghiệm ⇒ 3 liên kết thành vùng bấm (Quan sát: 0) |
| `B3-network-disconnected-unreachable` | ngắt `router—isp` ⇒ `route = []`, liên kết vẽ nét đứt, **không vẽ chấm gói tin**, thuyết minh: *"…không còn liên kết nào dẫn tới Máy chủ (server) — gói tin không đi được."* |
| `B4-network-second-cut` | ngắt chặng đầu ⇒ lại không tới được |
| `B5-network-reset-to-baseline` | **Về mạng ban đầu** ⇒ tuyến gốc trở lại nguyên vẹn |

Nối lại chặng vừa ngắt ⇒ tuyến gốc quay về, và ở mọi cấu hình `route` luôn khớp
đúng `bfsRoute` trên topology hiện tại — renderer không tính một mét đường nào.

### 3b. Runner này ĐÃ TỪNG ĐỎ (không phải guard chưa được chứng minh)

Lượt chạy đầu ra **14/20**: năm phép kiểm của phần A báo FAIL vì runner dừng ở
bước 0. Nguyên nhân là **lỗi của runner**, không phải sản phẩm — nút "Thí nghiệm"
hiện ở mọi bước chưa phải bước cuối, nên dừng theo nó thì đứng ở bước không có
điểm quyết định. Mốc đúng là `.search-observe`. Ghi lại vì đây đúng loại
"runner hết hạn tố cáo sản phẩm" mà `ARCHITECTURE_MAP §8` #14 cảnh báo.

## 4. Tiêm lỗi — 8 lỗi, 8 lần ĐỎ, khôi phục XANH

| lỗi tiêm | kết quả |
|---|---|
| ánh xạ vùng đảo trái↔phải (bug "tên-sang-tên") | ĐỎ |
| hàng nút rời quay lại **song song** với vùng bấm | ĐỎ *(chỉ sau khi tách `commitmentSurfaceKind` — xem dưới)* |
| gỡ `tabIndex` (thao tác trực tiếp thành chỉ-chuột) | ĐỎ ×2 |
| giữ `role="img"` khi đã có vùng bấm | ĐỎ |
| what-if ghi đè thẳng `baseline` | ĐỎ ×2 |
| bỏ kiểm tra tham chiếu nút (sửa topology bypass validation) | ĐỎ |
| renderer tự gọi `bfsRoute` | ĐỎ ×3 |
| trạng thái không-tới-được lặng lẽ rơi về tuyến giả | ĐỎ ×4 |

**Lần tiêm quan trọng nhất là lần ĐI LỌT.** Viết thẳng `actionsHidden={false}`
trong `ui.tsx` — tức khôi phục đúng hồi quy wave này sinh ra để chặn — mà **cả
suite vẫn XANH**: `labOpen` là state cục bộ nên `renderToString` chỉ đi qua trạng
thái ĐÓNG, nơi cả hai bề mặt đều vắng (`ARCHITECTURE_MAP §8` #13). Luật được tách
thành hàm thuần `commitmentSurfaceKind` rồi tiêm lại ⇒ ĐỎ. Nếu chỉ chạy suite mà
không tiêm lỗi, wave này đã ship một bất biến không có thật.

## 5. Một lỗi do CHÍNH ảnh chụp bắt được

`B3` lượt đầu cho thấy dải *"Không còn đường nào từ client tới server"* nằm ngay
trên khe thuyết minh vốn đã nói cùng điều đó — **hai kênh cho một câu**, đúng loại
trùng lặp W4B-2V đã gỡ ở họ tìm kiếm. Đã bỏ dải; chủ sở hữu duy nhất của câu đó
là `narrate()` (SHELL-N), còn trạng thái không-tới-được đọc được trên sân khấu
bằng **liên kết nét đứt + vắng chấm gói tin** (hai kênh thị giác). Có test khoá.

## 6. Ma trận sau wave

**Tương tác trực tiếp — 9 target.** `DIRECT_SCENE_READY` đã hiện thực: **2**
(`linear_search`, `binary_search`). `SCENE_ADJACENT`: **7** — họ scan và sort cần
**thêm chỉ số vào model trước** (chỉ họ tìm kiếm đã mang `currentIndex` +
`activeRange`), là việc thật, không giấu. Cả **9/9** nay ở sau cổng Thí nghiệm.

**What-if — 22 target.** `WHAT_IF_INPUT_READY` 12 · `WHAT_IF_STRUCTURE_READY`
**2** (`generic.rule_scene` + **`network.packet_routing` mới**) ·
`WHAT_IF_BLOCKED` **8** (giảm từ 9).

## 7. Cổng

`vitest 1089/71` · `pytest 1135 passed, 2 skipped` · `tsc -b` + build sạch ·
browser **20/20 × 3 viewport** · `git diff --check` sạch.

## 8. Giới hạn — nói thẳng

- Họ **scan/sort chưa scene-bound**. `count_if`/`sum_if` phân loại trung thực là
  SCENE_ADJACENT: hành động là một **vị từ**, không phải một vị trí; ép bấm-vào-ô
  sẽ làm UI khó hiểu hơn để đổi lấy một ô xanh trong ma trận.
- `sum_if` còn rào riêng: biến tích luỹ chưa chiếu lên sân khấu ⇒ "cộng vào tổng"
  chưa có hệ quả thị giác. **REPRESENTATION_BLOCKED**, không sửa trong wave này.
- Mạng **chỉ** nối/ngắt/về-ban-đầu. Thêm/xoá nút kéo theo đặt kiểu nút, đặt lại
  nguồn/đích, bố cục 2D+3D — đó là trình soạn đồ thị (§27), cố ý để ngoài.
- 8 target vẫn `WHAT_IF_BLOCKED` (`apply` = identity).
- **Chưa đo trên người học.** `LEARNER_IMPACT_NOT_EVALUATED`,
  `CURRICULUM_SUPPORT_PARTIAL` giữ nguyên.

## 9. Tuyên bố được phép

*"Sau khi xem diễn biến tất định, học sinh thao tác trực tiếp lên chính vùng mà
hành động tác động, và sửa được mô hình trong giới hạn có kiểm định để engine
tính lại hệ quả."* Không tuyên bố gì về kết quả học tập.

## 10. Verdict

```
W4B2I_INTERACTIVE_SIMULATION_PARTIAL
— EXPERIMENT_GATE_ROLLOUT_COMPLETE 9/9
— DIRECT_SCENE_INTERACTION_VERIFIED 2/9 (họ tìm kiếm; 7 còn lại SCENE_ADJACENT,
  lý do kỹ thuật nêu ở §6 — thiếu chỉ số trong model, KHÔNG phải thiếu thời gian)
— BOUNDED_WHAT_IF_STRUCTURE_VERIFIED (network pilot)
— ENGINE_RECOMPUTE_OWNS_NEW_STATE
— BASELINE_REMAINS_RESTORABLE
— UNREACHABLE_STATE_NOW_REPRESENTABLE (đổi engine CÓ KHAI BÁO, user duyệt)
— BASELINE_OBSERVED_REJECTED (tiền đề sai + RULES §3c)
```

Không dùng COMPLETE: 7/9 target vẫn là SCENE_ADJACENT chứ không phải
DIRECT_SCENE_READY.
