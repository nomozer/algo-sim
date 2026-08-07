# W4B-1A.1 — TRUSTED MEASUREMENT + VIEWPORT OWNERSHIP

Hai việc, theo đúng thứ tự đó: **làm cho dụng cụ đo đáng tin trước**, rồi mới
dùng nó để chấm một thay đổi bố cục. Lượt trước (W4B-1A) làm ngược lại — đo bằng
một dụng cụ có hai khiếm khuyết chưa biết, và kết luận "SẠCH" cho một bố cục
đang bỏ không tới 46% màn hình.

## Danh tính lượt đo

| | |
|---|---|
| Git SHA nền | `63d9896` (sau W4B-1A + tài liệu critique) |
| Chrome | 150.0.7871.187, `--headless=new`, DPR 1, zoom **100%** |
| App | Vite dev `http://localhost:3003` |
| Node / npm / Python | v24.13.0 / 11.6.2 / 3.12.10 |
| Nguồn phát hiện | `docs/evaluation/m17/design-critique/` — Assessment A của lượt Impeccable |

---

## 1. Dụng cụ đo — hai khiếm khuyết và cách chữa

### 1.1. Phiên CDP không cô lập (§3A)

**Trước.** `const CDP_PORT = 9337` — hằng số. `connect()` chỉ hỏi "có trang nào
trên cổng 9337 không". Hai lượt chạy song song, hoặc một lượt trước đó ném lỗi và
bỏ lại Chrome mồ côi, thì lượt sau **bám vào trình duyệt của lượt khác** và trả
về hình học của trang khác.

**Đã xảy ra thật**, không phải rủi ro lý thuyết: hai agent của lượt critique chạy
script này đồng thời và sinh ra một artifact gắn nhãn `network.graph_traversal`
nhưng mô tả một trang `find_max`.

**Sau.** `--remote-debugging-port=0` để Chrome tự chọn cổng rảnh, rồi đọc cổng
thật từ `DevToolsActivePort` trong **chính profile của lượt này**. Không còn hằng
số nào để đụng nhau, và không cần dò cổng rảnh (dò vẫn còn khe hở race). PID +
cổng + profile được ghi vào `session` của artifact.

### 1.2. Dấu vân tay chỉ kiểm hình dạng, không kiểm danh tính (§3B)

**Trước.** Dấu vân tay hỏi `.app-layout` · `.panel-center` · `.panel-controls` ·
`.sim-stage` có mặt không. Một Chrome bị bám nhầm **vẫn là workspace hợp lệ** —
chỉ là của mô phỏng khác. Guard không thể phát hiện.

**Sau.** Hỏi thẳng engine store: `useAppStore.getState().active.moduleId`, so với
`simulation_id` mà lượt chạy đang yêu cầu. Lệch → ghi
`WRONG_SIMULATION_OR_FIXTURE.json` (kèm expected/actual/PID/cổng) và **thoát 2**.

### 1.3. Đường dọn dẹp đảm bảo (§3D)

**Trước.** `chrome.kill()` chỉ nằm trên hai đường thoát bình thường. Một
assertion đỏ hay một exception giữa chừng đều bỏ lại tiến trình Chrome sống — và
với cổng cố định, lượt sau bám vào đúng nó.

**Sau.** Mọi lối ra đi qua `shutdown()`: thành công · thoát mã != 0 · throw ·
unhandled rejection · SIGINT/SIGTERM. Handler `exit` giữ đồng bộ.

---

## 2. Bốn chứng minh (§3C, §3D)

| # | Phép thử | Kết quả | Mã thoát |
|---|---|---|---:|
| 1 | Lượt chạy bình thường sau khi sửa | `PASS` | 0 |
| 2 | **Tiêm lỗi** `--self-test-throw` ngay sau khi Chrome khởi động | `uncaughtException` được bắt, `shutdown()` chạy | **3** |
| 2b | Kiểm PID của lượt tiêm lỗi sau khi thoát | **PID 23584 đã được dọn** — không còn tiến trình mồ côi | — |
| 3 | **Song song A**: `algorithm.find_max` | pid **9204** · cổng **59755** · artifact chỉ chứa `algorithm.find_max` | 0 |
| 4 | **Song song B**: `network.graph_traversal` (chạy CÙNG LÚC với A) | pid **14752** · cổng **61157** · artifact chỉ chứa `network.graph_traversal` | 0 |

Khác PID, khác cổng, không bám chéo, mỗi artifact đúng target của nó. Đây chính
là kịch bản trước đây chắc chắn hỏng.

Cờ `--self-test-throw` là **cổng tiêm lỗi tái lập được**, nằm luôn trong script —
không phải sửa tạm file rồi hoàn tác như lượt W4B-1A.

---

## 3. Shell đòi bề rộng viewport (§4)

### 3.1. Đo cơ chế TRƯỚC khi sửa

Assessment A nêu giả thuyết: auto margin trên trục ngang triệt tiêu
`align-self: stretch`. Tôi chưa đo, nên đo trước (`width-before/`):

| | 1366×768 | 1920×1080 |
|---|---:|---:|
| `#root` (khung cha) | 1356 | 1910 |
| `.app-layout` | **1039** | **1039** |
| `margin-left/right` computed | **158.5px** | **435.5px** |
| `max-width` khai báo | 1720px | 1720px |
| `align-self` | auto | auto |

Margin đúng bằng `(1356−1039)/2` và `(1910−1039)/2` — toàn bộ chỗ dư bị auto
margin nuốt. `.app-layout` giữ **cùng một bề rộng 1039px ở hai màn hình khác
hẳn nhau**, và `max-width: 1720px` **không bao giờ được chạm tới**. Giả thuyết
được xác nhận bằng số, không phải bằng suy luận.

`#root { display: flex; flex-direction: column }` ⇒ trục ngang là trục **phụ**;
`margin: 0 auto` ở đó là auto margin trên trục phụ ⇒ stretch bị tắt ⇒ lưới co về
fit-content. Nói cách khác: **bề rộng của mô phỏng đang do độ dài câu thuyết minh
dài nhất quyết định.**

### 3.2. Bản vá

```css
.app-layout {
  width: 100%;          /* bề rộng XÁC ĐỊNH ⇒ không co theo nội dung nữa */
  max-width: 1720px;    /* nay mới có tác dụng */
  margin-inline: auto;  /* chỉ còn việc căn giữa phần dư khi màn > 1720px */
}
```

`box-sizing: border-box` đặt ở `*` nên padding nằm trong 100% — không sinh tràn
ngang (đã kiểm bằng phép đo, không suy đoán).

### 3.3. Kết quả (`width-after/`)

| viewport | trước | sau | mong đợi theo hợp đồng CSS |
|---|---:|---:|---|
| 1366×768 | 1039 (lề 158.5) | **1356** (lề 0) | `min(1356, 1720)` = 1356 ✓ |
| 1920×1080 | 1039 (lề 435.5) | **1720** (lề 95) | `min(1910, 1720)` = 1720 ✓ |

Được thêm **+317px** ở laptop và **+681px** ở màn rộng. 190px còn lại ở 1920 là
`max-width` của hệ thiết kế, không phải khoảng chết.

### 3.4. Nghiệm thu toàn danh mục (`catalog-after/`)

26 mẫu · **22/22 target** × 3 viewport × 3 checkpoint = 234 phép đo, **PASS**,
thoát 0. Dấu hiệu quyết định:

| viewport | `.app-layout` — số bề rộng khác nhau | bề rộng | khung `.sim-stage` |
|---|---:|---:|---:|
| 1366×768 | **1** (trước: 23) | 1356 | 942 |
| 1536×864 | **1** (trước: 26) | 1526 | 1112 |
| 1920×1080 | **1** | 1720 | 1306 |

Trước bản vá, bề rộng lưới nhận **23 giá trị khác nhau ở cùng một viewport** —
bằng chứng trực tiếp rằng nó do nội dung quyết định. Sau bản vá còn **đúng một
giá trị**, bằng `min(khung cha, max-width)`. Khung sân khấu cũng đồng nhất theo,
và rộng hơn hẳn (trước: 570–942px tuỳ target).

---

## 4. Điều kiện chấm mới: `LAYOUT_NOT_USING_VIEWPORT` (§5)

Guard W4B-1A có năm điều kiện, tất cả đều hỏi *"có tràn / có bị giấu / có bị
che không"*. **Không điều kiện nào hỏi "app có DÙNG màn hình không"** — nên một
shell bỏ trống 46% bề rộng vẫn PASS sạch. Đó là lý do lượt trước tuyên bố SẠCH
trên một bố cục hỏng.

Bề rộng mong đợi **dẫn xuất từ hợp đồng CSS đo được**, không phải một tỉ lệ cố
định áp cho mọi breakpoint:

```
expected = min(khung_cha.width, parseFloat(app_layout.css_max_width))
FAIL nếu app_layout.width < expected - 4px
```

Màn hẹp hơn `max-width` → phải dùng gần trọn khung cha. Màn rộng hơn → phải đạt
đúng `max-width` đã khai.

**Chứng minh guard đỏ được** (`proof/5-viewport-guard-red/`) — hoàn nguyên CSS về
bản cũ rồi chạy lại:

```
✗ FAIL — 2 vi phạm
  network.graph_traversal  1366x768/mid   LAYOUT_NOT_USING_VIEWPORT
    .app-layout 1039px < mong đợi 1356px (khung cha 1356px · max-width 1720px) ⇒ lề chết 317px
  network.graph_traversal  1920x1080/mid  LAYOUT_NOT_USING_VIEWPORT
    .app-layout 1039px < mong đợi 1720px (khung cha 1910px · max-width 1720px) ⇒ lề chết 871px
exit 1
```

871px trùng khớp con số 46% mà Assessment A báo cáo độc lập.

---

## 5. Giới hạn — lượt này KHÔNG kết luận điều gì

- `LEARNER_IMPACT_NOT_EVALUATED` và `CURRICULUM_SUPPORT_PARTIAL` **giữ nguyên**.
  Sân khấu rộng hơn là **browser usability**, không phải bằng chứng học tập.
- Lượt này **chưa** đụng tới kích thước nội tại của renderer. Khung đã rộng ra,
  nhưng mọi SVG vẫn tự khoá `maxWidth` bằng đúng bề rộng `viewBox` của nó, nên
  phần lớn chỗ vừa giành được **chưa được sân khấu dùng**. Đó là việc riêng, và
  **không được sửa bằng cách phóng viewBox** — cách đó đã thử và đã hỏng
  (`dag-module.tsx:273-305`, có test khoá `maxWidth ≤ viewBox`).
- Một trình duyệt, một DPR, `--hide-scrollbars`. Chưa đo ở chế độ có thanh cuộn
  chiếm chỗ thật.
- Bằng chứng W4B-1A đã commit **không** bị nhiễm theo cơ chế 1.1 (các lượt chạy
  tuần tự, đều thoát bình thường) — nhưng guard lúc đó **không thể chứng minh**
  điều đó. Từ lượt này trở đi thì chứng minh được.
