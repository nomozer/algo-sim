# W4B-1A — RESPONSIVE HEIGHT DIAGNOSIS + CATALOG-WIDE LAYOUT FIX

Kết quả một lượt: triệu chứng *"workspace chỉ dùng được khi thu nhỏ browser"* là
**lỗi trục CHIỀU CAO**, không phải chiều rộng. Sửa ở một shared owner
(`.app-layout`), nghiệm thu trên 22/22 target × 8 viewport ở zoom 100%.

## Danh tính lượt đo

| | |
|---|---|
| Git SHA (lúc đo) | `cba61a2` + bản vá working tree |
| Baseline W4B-0 | `267aca5` · `cba61a2` — cả hai có trong history |
| Chrome | 150.0.7871.187, `--headless=new` |
| devicePixelRatio | 1 (`deviceScaleFactor: 1`, `mobile: false`) |
| Zoom | **100%** ở mọi phép đo |
| App | Vite dev `http://localhost:3001` (cổng 3000 đang bị tiến trình khác chiếm) |
| Node / npm / Python | v24.13.0 / 11.6.2 / 3.12.10 |
| Baseline suite trước khi sửa | pytest **1129 passed, 2 skipped** · vitest **924 passed / 58 file** · catalog matrix **22 target PASS** · `git diff --check` sạch |

## 1. Chẩn đoán — probe trực giao (§4)

Giả thuyết tĩnh trước khi đo: `.app-layout` cao đúng một màn
(`height: calc(100vh - 57px)`) với `.panel-center { overflow-y: auto }`, trong
khi **cả ba breakpoint của repo đều theo chiều rộng** (1100 · 900 · 860) — không
có một media query nào theo chiều cao.

Probe giữ nguyên target/fixture/checkpoint/browser/zoom, chỉ đổi viewport. Số đo
là px nội dung bị giấu sau thanh cuộn nội bộ của `.panel-center`
(`network.graph_traversal`, bước giữa):

| Viewport | Rộng | Cao | Bị giấu | Trang cuộn được |
|---|---:|---:|---:|---|
| 1920×1080 | dư | dư | **0px** | không cần |
| 1366×1024 | **hẹp** | dư | **0px** | không cần |
| 1920×768 | dư | **thấp** | **170px** | **KHÔNG** |
| 1366×768 | **hẹp** | **thấp** | **170px** | **KHÔNG** |

Hai hàng giữa là phép thử quyết định: đổi chiều rộng không đổi kết quả, đổi
chiều cao thì đổi. `page_scrollable_y = false` ở **cả bốn** — trang chưa bao giờ
cuộn, nội dung chỉ biến mất vào một thanh cuộn nội bộ không có tín hiệu ở mức
trang. Thu nhỏ browser cho nhiều CSS px chiều cao hơn ⇒ vừa. Đúng cách người
dùng đã tự xoay xở.

**Verdict: `HEIGHT_DOMINANT`.**

Ghi chú trung thực: ở `algorithm.find_max` (ảnh người dùng cung cấp), bước đầu
**không** tái hiện — nội dung đủ thấp để vừa. Chỉ từ bước có thuyết minh trở đi
mới lộ (11px), và target nội dung cao hơn mới cho thấy độ lớn thật (170px). Vì
vậy phép đo chỉ ở checkpoint `initial` sẽ kết luận nhầm `NOT_REPRODUCED`.

Artifact: `probe-before/` · `probe-before-traversal/` · `probe-after-traversal/`.

## 2. Bản vá — một shared owner (§9)

`frontend/src/styles/global.css`, thêm **một** media query theo chiều cao:

```css
@media (min-width: 1101px) and (max-height: 900px) {
  .app-layout, .app-layout.right-closed { height: auto; min-height: calc(100vh - 57px); }
  .panel-center, .panel-right { overflow-y: visible; }   /* trả quyền cuộn cho TRANG */
  .panel-controls { position: sticky; bottom: 0; z-index: 50; box-shadow: var(--shadow-elevated); }
  .panel-center { padding-bottom: 140px; }               /* bù chỗ cho thanh ghim đáy */
}
```

Ba quyết định và lý do:

- **Không** tái dùng nhánh `≤1100px`. Nhánh đó biến Quan sát thành drawer — đúng
  cho màn hẹp, nhưng ở 1366–1920 chiều rộng vẫn dư, biến nó thành drawer là hạ
  cấp không có lý do. Ở đây chỉ đổi **quyền sở hữu cuộn**, giữ nguyên hai cột.
- `position: sticky` + `padding-bottom` là **tái dùng nguyên cơ chế FIX-1 và
  đính chính W3B** đã được đo ở nhánh màn hẹp (thanh ghim đáy từng phủ lên vùng
  hành động của `insertion_sort @1024×768`), không phải phát minh mới.
- Ngưỡng **900px** suy từ hình học đo được: `.panel-center` khả dụng =
  `viewportH − 195`; nội dung cao nhất đo được 743px ⇒ cần `viewportH ≥ 938`.
  900 phủ trọn 768 · 864 · 900; từ 1024 trở lên bố cục một-màn vẫn đủ chỗ (đo
  được: 0px bị giấu ở 1366×1024 và 1920×1080).

## 3. Nghiệm thu — 22/22 target × 8 viewport (§10–§12)

Chi tiết từng target: [RESPONSIVE_CATALOG_MATRIX.md](RESPONSIVE_CATALOG_MATRIX.md).

| Bộ đo | Viewport | Verdict | Vi phạm |
|---|---|---|---:|
| `catalog-before` | 1366×768 · 1536×864 | **FAIL** | **19** |
| `catalog-after` | 1366×768 · 1536×864 | **PASS** | 0 |
| `narrow-after` | 1024×768 · 768×900 | **PASS** | 0 |
| `tall-after` | 1920×1080 · 1366×1024 · 1440×900 | **PASS** | 0 |

**11/22 target** giấu nội dung ở ít nhất một viewport nghiệm thu trước bản vá
(nhiều nhất: `binary.character_encoding` 159px, `algorithm.insertion_sort` 89px,
`algorithm.linear_search` 74px). Sau bản vá: **0**. Không target nào cần patch
riêng — `TARGET_SPECIFIC_LAYOUT` = rỗng.

Điều kiện chấm (máy chấm, không chấm bằng mắt): `HORIZONTAL_OVERFLOW` ·
`CONTENT_HIDDEN_IN_PANEL` · `CONTROL_OCCLUDED` (elementFromPoint tại tâm control
trả về phần tử khác) · `CONTROL_OFFSCREEN` · `TEXT_CLIPPED`.

## 4. Guard đã được chứng minh ĐỎ ĐƯỢC (§5, §6)

**Dấu vân tay trang.** Mọi phép đo workspace khẳng định `.app-layout` ·
`.panel-center` · `.panel-controls` · `.sim-stage` đều có mặt; sai thì ghi
`WRONG_PAGE_OR_FIXTURE.json` và **thoát mã 2**, không ghi PASS. (Tiền lệ:
`audit-layout.mjs` từng báo "TẤT CẢ SẠCH" vì đo nhầm trang — `ARCHITECTURE_MAP §8` #14.)

**Tiêm lỗi giả** — `guard-proof/`:

| Bước | Trạng thái CSS | Kết quả | Mã thoát |
|---|---|---|---:|
| 1 | nguyên bản (đã vá) | `PASS` | 0 |
| 2 | tiêm `.app-layout { min-width: 3000px }` + lớp phủ `.panel-controls::after` | `FAIL` — 3 loại: `HORIZONTAL_OVERFLOW` (3000 > 1366) · `CONTROL_OCCLUDED` (6 nút trúng lớp phủ) · `CONTROL_OFFSCREEN` | **1** |
| 3 | gỡ lỗi tiêm | `PASS` | 0 |

Khôi phục đã kiểm bằng `git diff --stat`: `global.css` chỉ còn **+59 dòng** của
bản vá, không còn dấu vết khối tiêm.

## 5. Runner — reuse/extend, không sinh runner thứ tư (§2, §13)

| Trách nhiệm | Quyết định | Ghi chú |
|---|---|---|
| Chẩn đoán responsive (trục rộng **và cao**), before/after | **EXTEND_EXISTING** `scripts/diagnose-responsive.mjs` | thêm: viewport tham số hoá · checkpoint timeline · trục chiều cao · hit-test · fingerprint · acceptance + mã thoát · chế độ quét danh mục |
| Bộ fixture cho nhiều renderer | **EXTRACT_SHARED** → `scripts/fixtures.mjs` | chuyển nguyên văn từ `visual-stress-audit.mjs`; script đó nay `import`, dữ liệu không đổi một dòng |
| Sweep fixture × viewport × checkpoint | **REUSE_EXISTING** `visual-stress-audit.mjs` | chỉ đổi nguồn fixture |
| Hạ tầng CDP | **REUSE_EXISTING** `audit-layout.mjs` | không đụng |

**Không tạo runner mới.**

Nguồn fixture cho phép quét 22/22: `offlineCatalog()` của app phủ 13 target (17
mẫu) — đây là dữ liệu học sinh thật sự mở được, nên dùng làm nguồn chính. Bộ
stress phủ thêm 5. **4 target còn lại** (`algorithm.scan`,
`algorithm.selection_sort`, `algorithm.bounded_control_flow`,
`binary.character_encoding`) trước nay **chưa từng có mẫu mở được trong trình
duyệt** — chỉ có unit test — nên chưa từng nằm trong bất kỳ bản soát bố cục nào.
Đã thêm fixture cho chúng vào `fixtures.mjs`, config lấy nguyên văn shape từ
test đang xanh của chính module (không đoán).

## 6. Giới hạn — lượt này KHÔNG kết luận điều gì

- **`LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên.** Không có dữ liệu người học nào.
  "Dùng được ở zoom 100%" là **browser usability**, đo bằng hình học DOM — nó
  không nói gì về việc học sinh hiểu cơ chế tốt hơn.
- **`CURRICULUM_SUPPORT_PARTIAL` giữ nguyên.** Lượt này không đụng độ phủ
  chương trình; ba target không có eval case vẫn không có (việc của W4B-1B).
- Bằng chứng là **hình học DOM + hit-test trong Chrome thật**, không phải đánh
  giá thẩm mỹ. Ảnh chụp minh hoạ, không phải căn cứ chấm.
- Chrome **headless** với `--hide-scrollbars`. Thanh cuộn thật của trình duyệt
  có thể chiếm thêm ~15px chiều rộng ở chế độ hiện đầu — không đổi kết luận trục
  cao, nhưng biên chiều rộng chưa đo ở chế độ có thanh cuộn.
- Chỉ đo **một** DPR (=1) và **một** trình duyệt. Chưa đo Firefox/Safari.
- Ngưỡng 900px suy từ nội dung cao nhất **hiện có** (743px). Target tương lai cao
  hơn ~830px sẽ vượt cả bố cục 1024 — guard sẽ bắt được, nhưng ngưỡng lúc đó phải
  xét lại.
- Fixture của 4 target mới là **fixture soát bố cục**, không phải mẫu công khai
  cho học sinh (`visibility` không đổi, danh mục công khai không đổi).

## 7. Tái lập

```bash
cd frontend && npm run dev            # cửa sổ khác

# probe trục trực giao
node scripts/diagnose-responsive.mjs --port 3000 --fixture network.graph_traversal \
  --routes workspace --checkpoints initial,mid,final \
  --viewports 1920x1080,1920x768,1366x1024,1366x768 --out <thư-mục>

# nghiệm thu toàn danh mục (thoát != 0 khi có vi phạm)
node scripts/diagnose-responsive.mjs --port 3000 --fixture all \
  --routes workspace --checkpoints initial,mid,final \
  --viewports 1366x768,1536x864 --out <thư-mục>
```
