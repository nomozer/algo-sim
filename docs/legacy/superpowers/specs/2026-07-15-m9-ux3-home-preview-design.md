# M9-UX3 — Home gọn + preview đúng cơ chế

Ngày: 2026-07-15 · Nhánh: `m9-ux3-home-preview` · Trạng thái: đã duyệt thiết kế

## 1. Vì sao

Hai vấn đề, một do người dùng nêu, một phát hiện khi đọc code:

1. **Trang chủ nhìn nặng và lệch.** `textarea` 5 dòng rỗng + nút `btn-primary` đặc kín
   chiều ngang nuốt trọn màn hình đầu; hero căn giữa nhưng tiêu đề mục căn trái; card
   gợi ý cao thấp so le vì tiêu đề dài ngắn khác nhau.
2. **Tranh preview vẽ SAI cơ chế ở 2 chỗ** (nghiêm trọng hơn "xấu"):
   - `algorithm.linear_search` dùng kind `search-range` — tranh vẽ con trỏ **trái/giữa/phải**.
     Tìm kiếm tuần tự **không có mid, không có trái/phải**. Đây là cơ chế của binary
     search đang treo trên card tìm kiếm tuần tự.
   - `algorithm.insertion_sort` dùng kind `sort-swap` — mũi tên **đổi chỗ**. Chèn thì
     **nhấc ra rồi dời vào**; chính `decision.ts` (M9-S1) hỏi hai câu khác nhau:
     *"đổi chỗ?"* (nổi bọt) vs *"dời?"* (chèn).

   Cả hai va thẳng vào nguyên tắc sư phạm #6 (`COVERAGE.md §2.6`): *mọi thứ trực quan
   phải chạm cơ chế ẩn thật*. Tranh minh hoạ dạy sai cơ chế trước cả khi học sinh bấm vào.

   Ngoài ra 4 bài `find_max`/`find_min`/`sum_if`/`count_if` dùng chung một tranh — trùng
   nhưng không sai. Vẫn nên tách, vì `sum_if` ↔ `count_if` (cộng dồn ↔ đếm) đúng là chỗ
   học sinh hay lẫn.

3. **Rò rỉ fixture nội bộ.** `InputPanel.tsx` gọi `offlineCatalog()` (16 mẫu, kể cả
   `internal_fixture`) chứ không phải `publicCatalog()` (12 mẫu). Luật phạm vi M9-UX2
   ("danh mục công khai khoanh trong Tin học THPT") mới chỉ được áp ở Home; mở panel trái
   trong workspace ra, học sinh vẫn thấy mẫu tam giác + 3 bản "(tổng quát)", kèm chuỗi
   kĩ thuật `algorithm.find_max` làm phụ đề. Test M9-UX2 chỉ kiểm Home nên lọt.

## 2. Phạm vi

**Frontend-only.** Không đụng engine, store, pipeline, backend, DSL manifest, catalog
backend. Không thêm domain / DSL primitive / edit mode / capability → **không va scope
freeze `CURRENT_STATE.md` §5b**. Kế thừa trực tiếp dòng M9-UX1 → M9-UX2.

**0 lượt gọi AI** (chính sách CLAUDE.md: UI/CSS-only → không cần live AI).

## 3. Thiết kế

### 3.1 `SamplePreview.tsx` — 7 kind → 13 kind

Kiến trúc **không đổi**: vẫn SVG tĩnh thuần trình bày, dữ liệu minh hoạ cố định, tra bằng
`simulation_id` qua `KIND_BY_SIM_ID`, không chạy engine, không fetch, id lạ → fallback
`generic` (không bao giờ ném). Chỉ thay đổi **độ phân giải của bảng tra**.

| simulation_id | kind | cơ chế tranh vẽ |
|---|---|---|
| `algorithm.find_max` | `algorithm-bars` *(giữ)* | cột **cao nhất** tô xanh |
| `algorithm.find_min` | `bars-min` *(mới)* | cột **thấp nhất** tô tím |
| `algorithm.sum_if` | `sum-threshold` *(mới)* | ngưỡng nét đứt + ô **tổng Σ đang cộng dồn** |
| `algorithm.count_if` | `count-threshold` *(mới)* | cùng ngưỡng, huy hiệu là **bộ đếm** |
| `algorithm.linear_search` | `linear-scan` *(**sửa lỗi**)* | quét trái→phải, ô đã xem xám, kính lúp ở ô đang xét — **bỏ hẳn trái/giữa/phải** |
| `algorithm.binary_search` | `search-range` *(giữ)* | trái/giữa/phải + vùng đã loại |
| `algorithm.bubble_sort` | `sort-swap` *(giữ)* | hai mũi tên vòng ngược = **đổi chỗ** |
| `algorithm.insertion_sort` | `insertion-lift` *(**sửa lỗi**)* | một cột **nhấc khỏi hàng**, mũi nêm chỉ chỗ **dời vào** |
| `binary.decimal_to_binary` | `binary-bits` *(giữ)* | |
| `network.packet_routing` | `network-path` *(giữ)* | |
| `logic.and_gate` | `logic-gate` *(giữ)* | |
| *(metadata `preview`)* | `web-structure` *(giữ)* | |
| *(id lạ)* | `generic` *(giữ)* | fallback |

**Bất biến mới cần khoá bằng test**: trong domain `algorithm`, **không hai
`simulation_id` nào dùng chung một kind**. Đây là thứ ngăn tái phát lỗi "tranh của bài
khác treo trên card này".

### 3.2 `ProblemInput.tsx` — prop `variant?: "hero" | "compact"`

Component này **dùng chung ở hai nơi** với hai ràng buộc bề rộng khác hẳn:

- `HomeView` — cột rộng, là hành động chính.
- `InputPanel` — cột trái workspace **264px**; pill có icon hai đầu sẽ vỡ ở bề rộng này.

Nên tách **lớp vỏ**, giữ **lõi**:

- `variant="hero"` (Home, mặc định ở Home): một pill — `textarea` 1 dòng tự cao dần
  (`rows=1`, auto-grow tới ~6 dòng), kẹp tệp là icon **trong** ô bên trái, nút gửi là
  icon tròn **trong** ô bên phải. Không còn nút xanh đặc kín chiều ngang.
- `variant="compact"` (InputPanel, mặc định): **giữ nguyên hình dạng hiện tại**.

Toàn bộ logic (`onAnalyze`, `fileToPayload`, health check, `file-chip`, error banner) dùng
chung — chỉ khác JSX bao ngoài. Không nhân đôi hành vi.

### 3.3 `HomeView.tsx` — bố cục B

- **Card hàng ngang**: thumb 52×38 bên trái, chữ bên phải → **card cao bằng nhau**, hết
  cảnh tiêu đề dài đẩy một card cao hơn hàng xóm.
- Lưới **2 cột** (thay vì 4) → tiêu đề không xuống 3 dòng.
- Domain có **chấm màu** lấy từ `DOMAIN_COLOR` — hằng số **đã tồn tại** trong
  `offline-catalog.ts` mà Home chưa hề dùng (InputPanel thì có dùng).
- Cột nội dung `.app-single` 1040px → **920px**, khớp với `.home-section` vốn đã là 920.
- **"Xem tất cả" gom nhóm theo domain** (Thuật toán · Nhị phân · Mạng · Lôgic · Tổng quát)
  với tiêu đề nhóm, thay vì đổ 12 card phẳng.

### 3.4 `InputPanel.tsx` — vá rò rỉ fixture

- `offlineCatalog()` → `publicCatalog()`.
- Bỏ `simId` (`algorithm.find_max`) làm phụ đề — thay bằng nhãn domain tiếng Việt.

Fixture nội bộ **không mất**: `offlineCatalog()` vẫn còn nguyên cho test/dev/regression,
và lịch sử mở lại bằng envelope nên không phụ thuộc danh mục (bất biến #17).

## 4. Test

Sửa `frontend/src/data/catalog.test.tsx`:

- Thay khối `(12)(13)(14)` — hiện đang **khoá cái sai** (`expect(previewKindOf(
  "algorithm.linear_search")).toBe("search-range")`) — thành khẳng định 8 bài → 8 kind
  riêng biệt.
- **Test mới**: không hai `simulation_id` domain algorithm nào dùng chung kind.
- **Test mới**: `InputPanel` chỉ hiện mẫu public — không có "tam giác", không có
  "(tổng quát)", không lộ chuỗi `algorithm.` ra UI.
- Giữ nguyên các test đã có: fallback `generic` không ném; mọi kind render ra `<svg>`;
  Home SSR không quảng bá fixture; lịch sử vẫn reopen được fixture đã rời danh mục.

Nghiệm thu: `npm run build` (tsc + vite) · `npm test` · mở browser thật kiểm bố cục,
card cao bằng nhau, 8 tranh khác nhau, panel trái không còn tam giác.

## 5. Rủi ro

- `.app-single` 1040 → 920 cũng ảnh hưởng `HistoryView` (dùng chung lớp). Chấp nhận —
  lịch sử là danh sách hàng, hẹp lại còn dễ đọc hơn.
- Pill auto-grow cần `useRef` + chỉnh `style.height` theo `scrollHeight`. Đây là DOM
  thuần, không state — không đụng store.
