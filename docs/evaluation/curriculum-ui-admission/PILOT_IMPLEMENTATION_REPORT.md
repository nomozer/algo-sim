# PILOT_IMPLEMENTATION_REPORT — `logic.boolean_dag`

**Trạng thái: đã cài, đã đo, CHƯA commit, CHƯA push.**
Cơ sở mã trước pilot: `main` @ **`722acea`**.

## 1. Phạm vi thay đổi

**2 file sản phẩm** (giới hạn cho phép: 8) + 1 file test.

| File | Loại | Dòng |
|---|---|---|
| `frontend/src/simulations/domains/logic/dag-module.tsx` | sản phẩm | +51 / −9 |
| `frontend/src/styles/global.css` | sản phẩm | +8 / −0 |
| `frontend/src/simulations/domains/logic/dag.test.tsx` | test | +68 / −1 |

**Không** đụng: backend, engine, state, timeline, schema, DSL manifest, catalog,
store, `SimulationWorkspace`, `SimulationControls`. **Không** thêm family / target /
module. `git diff --check` sạch.

## 2. Ba thay đổi, mỗi cái vá một khuyết điểm đã đo

### PILOT-1 — sơ đồ mạch trở thành phần lớn nhất

*Khuyết điểm:* sơ đồ chiếm **11 %** thẻ, bảng chân lý **24 %** — bảng tra to gấp
hơn hai lần cơ chế chính, trái với NT-1 rút từ benchmark.

*Việc đã làm:* phóng to node (`NODE_W` 76→96, `NODE_H` 38→46, `COL_GAP` 54→72,
`ROW_GAP` 16→22) **và** — phần quyết định — nới `maxWidth` của SVG từ `w`
(đúng bề rộng viewBox, 432 px) lên `max(w, 720)`.

*Bài học đáng ghi:* **phóng to node một mình KHÔNG có tác dụng.** Lượt đo đầu sau
khi chỉ đổi kích thước node cho kết quả sơ đồ **16 %** — vẫn nhỏ hơn bảng (22 %).
Nguyên nhân thật là `maxWidth: w` khoá SVG ở đúng bề rộng viewBox trong một thẻ
rộng ~900 px, nên viewBox to ra thì hình chỉ **thu nhỏ lại bên trong khung cũ**.
Nếu tôi dừng ở bước đó và báo cáo "đã phóng to sân khấu", đó sẽ là một tuyên bố sai.

### PILOT-2 — gỡ quá tải màu ở cổng đầu ra

*Khuyết điểm:* cổng đầu ra mang **viền xanh lá**, mà xanh lá đồng thời là "tín hiệu
= 1" trên dây và trên chữ số. Ảnh before bắt được ca cổng OR có viền xanh lá **trong
khi giá trị của nó còn là `?`**.

*Việc đã làm:* vai trò "đầu ra" nay nói bằng **chữ "ĐẦU RA"** + **khung ngoài nét
đứt** màu `--ink-muted`. Bỏ hoàn toàn `stroke="var(--accent-green)"` khỏi node.
Dây và chữ số **vẫn** xanh khi mang tín hiệu 1 — xanh lá từ đây chỉ còn **một nghĩa**.

### PILOT-3 — thêm chú giải tín hiệu

*Khuyết điểm:* `legend = false`; 19/22 target dùng màu mà không giải thích màu.

*Việc đã làm:* thêm `.stage-legend.dag-legend` với 4 mục. Mỗi mục có **dấu hiệu
ngoài màu** (chữ số **1**/**0**, chữ **?**, viền nét đứt) để học sinh không phân
biệt được màu vẫn đọc được. CSS mới: `.stage-legend .dot.is-unknown` dùng viền
nét đứt nền trong suốt — **khác hình**, không chỉ khác màu.

## 3. Before / after — cùng cursor, cùng viewport

Đo bằng **cùng một harness**: BEFORE chạy trên **worktree tách rời tại `722acea`**
(dev server cổng 3100), AFTER chạy trên working tree có pilot (cổng 3000). Kịch bản
giống hệt: mid = `floor(steps*0.45)` lần **bấm thật** "Tiến một bước", final = nút
"Đến cuối". **12/12 pha khớp cursor** — không có chuyện lấy hai trạng thái khác nhau
để chứng minh giao diện đẹp hơn.

Số đầy đủ: [browser-acceptance.json](browser-acceptance.json) (mục `deltas`).

| Chỉ số | desktop | laptop | narrow |
|---|---|---|---|
| **Sơ đồ / thẻ** | 11 % → **36 %** | 10 % → **34 %** | 13 % → **38 %** |
| **Bảng chi tiết / thẻ** | 24 % → **18 %** | 25 % → **18 %** | 24 % → **18 %** |
| **Sơ đồ có lớn hơn bảng?** | không → **có (2,0×)** | không → **có (1,9×)** | không → **có (2,1×)** |
| Mục chú giải | 0 → **4** | 0 → **4** | 0 → **4** |
| `<rect>` viền xanh lá | 1 → **0** | 1 → **0** | 1 → **0** |
| Nhãn "ĐẦU RA" | không → **có** | không → **có** | không → **có** |
| Chữ trong thẻ (pha mid) | 326 → **411** | 326 → **411** | 326 → **411** |
| Tràn ngang | không → không | không → không | không → không |
| Nút điều khiển trong khung | 6/6 → 6/6 | 6/6 → 6/6 | 6/6 → 6/6 |

**Đánh đổi phải nói rõ: lượng chữ TĂNG 326 → 411 ký tự (+26 %).** Pilot **thêm**
chữ, trong khi một trong ba câu hỏi của đợt này là "UI có quá nhiều chữ không".
Tôi cho rằng đánh đổi này đáng: 85 ký tự thêm vào là **chú giải giải mã màu**, gắn
ngay dưới sân khấu, chứ không phải văn xuôi giải thích thuật toán. Nhưng đây là
**lập luận thiết kế**, không phải kết quả đo — bạn có quyền bác.

Ảnh: [screenshots/before/](screenshots/before/) và [screenshots/after/](screenshots/after/)
— **12 file mỗi bên, trùng tên từng cặp**.

## 4. UI acceptance trên ba viewport

| Kiểm tra | desktop 1440×1000 | laptop 1024×768 | narrow 768×900 |
|---|---|---|---|
| Không tràn ngang | ✅ | ✅ | ✅ |
| 6/6 nút điều khiển trong khung nhìn | ✅ | ✅ | ✅ |
| Ngăn "Quan sát" mở ra **không che** nút điều khiển | — | ✅ *(hit test 6/6)* | ✅ *(hit test 6/6)* |
| Đúng **một** khe tường thuật | ✅ | ✅ | ✅ |
| Space trên node đầu vào **không** kích hoạt tự chạy | ✅ | — | — |

**Hai chỉ số suýt bị báo cáo sai — đã truy ra là ARTIFACT ĐO:**

1. **"Drawer che nút điều khiển"**: chồng lấn bounding-box giữa `panel-right`
   (cột cao 360×711) và thanh control (876×40) là **11 684 px²** ở laptop,
   **22 011 px²** ở narrow. Nghe như lỗi. Nhưng `document.elementFromPoint` tại
   tâm **từng nút** trả về đúng nút đó — **6/6 chạm được**. Chồng hình chữ nhật
   ≠ che. Chỉ số hợp lệ là hit test.

2. **"Space kích hoạt autoplay"**: cursor nhảy 4 → 0 sau khi bấm Space. Nghe như
   guard phím tắt bị hỏng. Truy ra: đổi đầu vào thì **timeline dựng lại từ đầu** —
   đúng thiết kế. Kiểm chứng bằng cách chờ thêm 1,4 s: cursor **vẫn 0**,
   `playing = false`. Không phải autoplay. Đã tách thành hai trường riêng
   `timeline_rebuilt` và `autoplay_started` trong file acceptance.

## 5. Hồi quy

| Cổng | Trước pilot | Sau pilot |
|---|---|---|
| `vitest run` | 810 pass / 52 file | **813 pass / 52 file** (+3 test khoá pilot) |
| `npm run build` (`tsc -b`) | ✓ | **✓** |
| `pytest -q` | 1129 pass / 2 skip | **1129 pass / 2 skip** (không đụng backend) |
| catalog runtime matrix | 22 PASS | **22 PASS** |
| `git diff --check` | sạch | **sạch** |

Ba test mới khoá đúng ba nguyên nhân, không khoá hệ quả:
- *"cổng đầu ra KHÔNG dùng màu tín hiệu để đánh dấu vai trò"* — khẳng định không
  `<rect>` nào mang `--accent-green`, **và** dây tín hiệu 1 **vẫn** xanh (nếu chỉ
  cấm xanh lá thì test sẽ xanh cả khi tôi lỡ xoá mất nghĩa đúng).
- *"sơ đồ được phép giãn rộng hơn bề rộng viewBox"* — khoá `max-width > viewBox
  width`, tức khoá **nguyên nhân thật**, không khoá kích thước node (số node có thể
  đổi vì lý do khác mà không phải hồi quy).
- *"chú giải tín hiệu có mặt và mỗi mục có dấu hiệu NGOÀI màu"*.

## 6. Điều pilot này KHÔNG chứng minh

- **Không** có bằng chứng học sinh hiểu mạch logic tốt hơn. Chưa có bất kỳ kiểm
  chứng nào với người học. Toàn bộ mục 3 là **số đo giao diện**.
- **Không** đo được ảnh hưởng tới thời gian hoàn thành hay tỉ lệ trả lời đúng.
- **Không** kiểm tra với người dùng khiếm thị màu thật; lập luận "có dấu hiệu ngoài
  màu" là **suy luận thiết kế**, không phải kết quả kiểm thử khả dụng.
- Chỉ áp cho **một** target. 18/22 target còn thiếu chú giải **vẫn thiếu**.
