# AXO LANDING PAGE V1.2 — DESIGN SYSTEM, VISUAL STORYTELLING & PERFORMANCE ACCEPTANCE REPORT

> **Worktree:** `D:\Documents\projects\axo-geometry-library`  
> **Branch:** `feat/axo-geometry-library-verification`  
> **Preview URL:** `http://localhost:3001/gioi-thieu`  
> **Baseline Commit SHA (V1.1):** `dd5d92f67` (`feat(axo): refine spatial storytelling, demo, and 3d rendering lifecycle`)  
> **Documentation Commit Role:** `DOCUMENTATION_COMMIT_ROLE = SELF`

---

## 1. Tóm tắt & Trạng thái kiểm chứng (Verification Summary)

Báo cáo này ghi nhận kết quả triển khai **AXO Landing Page V1.2** theo định hướng nâng cấp có chọn lọc trên nền V1.1 (không xây lại từ đầu, không sửa Backend, không can thiệp Workspace hay tệp đang chỉnh dở của phiên song song). Mọi kết luận được gắn nhãn trung thực theo bốn trạng thái: `VERIFIED`, `INFERRED`, `NOT VERIFIED`, `BLOCKED`.

| Hạng mục chính | Trạng thái | Bằng chứng xác minh |
|---|---|---|
| Design System tokens (`tokens.css`) & 0 raw color hex | `VERIFIED` | `landing-design-system.test.tsx` (2/2 PASS), `contrastAudit` (`after-perf.json`) |
| Logo & Header auth-aware + Guest freedom + Focus trap | `VERIFIED` | `landing-header-navigation.test.tsx` (3/3 PASS), `after_01`, `after_12`, `after_13`, `after-perf.json` |
| Hero 3D đơn khối tinh giản & Shading giải tích | `VERIFIED` | `LandingHeroSculpture3D.tsx`, `after_03_hero_desktop.png`, `after_04_hero_mobile.png`, `hero-motion.webm` |
| Visual Storytelling Option A vs Option B benchmark | `VERIFIED` | `storytelling-comparison.json`, `storytelling-prism-option-b.webm`, `option_a_storytelling.png`, `option_b_storytelling.png` |
| Interactive Demo (bỏ prev/next & badge thừa, contextual reset) | `VERIFIED` | `landing-demo-integrity.test.tsx` (3/3 PASS), `after_08`, `after_09`, `after_15`, `interactive-demo.webm` |
| WebGL persistent lifecycle, label dedup & 2D collision repulsion | `VERIFIED` | `landing-webgl-lifecycle.test.tsx` (4/4 PASS), `after-perf.json` (`1 -> 2 -> 2` contexts, `0` overlaps) |
| Viewport matrix (`1920..320px`, gồm `1366×768`) & WCAG AA | `VERIFIED` | `after-perf.json` (7 viewport `0` overflow + `contrastAudit` 8/8 AA) + kiểm tra trực tiếp `1366×768` |
| TypeScript, Vite Build & Full Vitest (`172/172`, `2187/2187`) | `VERIFIED` | `npx tsc -b`, `npm run build` (`4.43s`), `npx vitest run --maxWorkers=2` (`93.14s`) |
| Kiểm tra riêng bằng REA MCP trong V1.2 | `NOT VERIFIED` | Tái sử dụng bằng chứng nghiên cứu tham chiếu V1.1 (§19); kiểm chứng V1.2 thực thi bằng Playwright Chromium + Vitest |

---

## 2. Danh sách tệp thay đổi & Commit cục bộ (§21–§22)

Tổng cộng **13 tệp code/test** thuộc phạm vi Landing V1.2 và **2 tệp tài liệu** được chỉnh sửa/tạo mới:

- **Source Landing (`7` tệp):**
  - `frontend/src/components/landing/landing.css`
  - `frontend/src/components/landing/LandingHeader.tsx`
  - `frontend/src/components/landing/landing-geometry-data.ts`
  - `frontend/src/components/landing/LandingStorytelling.tsx`
  - `frontend/src/components/landing/LandingInteractiveDemo.tsx`
  - `frontend/src/components/landing/LandingHeroSculpture3D.tsx`
  - `frontend/src/components/landing/LandingHeroScene3D.tsx`
- **Unit / Integration Tests (`6` tệp):**
  - `frontend/src/components/__tests__/landing-design-system.test.tsx` (mới)
  - `frontend/src/components/__tests__/landing-header-navigation.test.tsx` (mới)
  - `frontend/src/components/__tests__/landing-spatial-story.test.tsx` (cập nhật)
  - `frontend/src/components/__tests__/landing-storytelling-interaction.test.tsx` (mới)
  - `frontend/src/components/__tests__/landing-demo-integrity.test.tsx` (cập nhật)
  - `frontend/src/components/__tests__/landing-webgl-lifecycle.test.tsx` (mới)
- **Tài liệu & Chỉ mục (`2` tệp):**
  - `docs/CODE_INDEX.md` (cập nhật mục `components/LandingView.tsx` với danh sách thành phần và test V1.2)
  - `docs/evaluation/landing/AXO-LANDING-V1.2-REPORT.md` (tài liệu này)

**Các commit cục bộ trên `feat/axo-geometry-library-verification` (không push, không merge `main`):**

1. `6712a7a50` — `style(axo): align landing components with design system` (`landing.css`, `LandingHeader.tsx`, `landing-design-system.test.tsx`, `landing-header-navigation.test.tsx`)
2. `ef5dd3d37` — `feat(axo): refine landing visual storytelling` (`landing-geometry-data.ts`, `LandingStorytelling.tsx`, `landing-spatial-story.test.tsx`, `landing-storytelling-interaction.test.tsx`)
3. `42502b9c6` — `refactor(axo): simplify interactive geometry showcase` (`LandingInteractiveDemo.tsx`, `landing-demo-integrity.test.tsx`)
4. `fb5650d0f` — `perf(axo): optimize landing animation lifecycle` (`LandingHeroSculpture3D.tsx`, `LandingHeroScene3D.tsx`, `landing-webgl-lifecycle.test.tsx`)
5. *(Commit tài liệu này — xem mục 19)* — `docs(axo): record landing v1.2 evaluation report and code index` (`DOCUMENTATION_COMMIT_ROLE = SELF`)

---

## 3. Kiểm toán Design System (Design System Audit)

- **Nguồn thẩm quyền xác minh (`VERIFIED`):** Tìm kiếm trong toàn workspace xác nhận không tồn tại file `DESIGN.md` độc lập; nguồn token chuẩn duy nhất của sản phẩm là `frontend/src/styles/tokens.css` kết hợp nguyên tắc định hướng tại `docs/DESIGN_BRIEF.md`.
- **Sai lệch ở V1.1:** `landing.css` từng dùng mã màu đen tùy tiện `rgb(17, 17, 16)` cho CTA chính và rải rác các giá trị màu literal trong CSS thay vì ràng buộc biến token chuẩn của hệ thống.
- **Khắc phục ở V1.2:** Chuẩn hóa toàn bộ khai báo màu trong `frontend/src/components/landing/landing.css` về biến trong `tokens.css` (`0` color hex literal trong khai báo màu, được khóa cứng bằng `landing-design-system.test.tsx`).

---

## 4. Chuẩn hóa Token & Thành phần (Normalized Tokens & Components)

Tách bạch rành mạch giữa **Lớp 1 — UI Chrome & Điều hướng** và **Lớp 2 — Ngữ nghĩa Hình học không gian**:

| Lớp | Token chuẩn (`tokens.css`) | Giá trị | Vai trò áp dụng trong Landing V1.2 |
|---|---|---|---|
| UI Primary | `--primary` | `#0075de` | Nút CTA chính (`#btn-landing-header-start`, `#btn-landing-hero-start`, `#btn-landing-open-showcase-3d`, `#btn-landing-final-start`), tab bước đang chọn (`01..04`) |
| UI Primary Hover/Text | `--primary-active`, `--on-primary` | `#005bab`, `#ffffff` | Chữ/nhãn `.axo-sp-eyebrow`, `.axo-sp-point-tag.is-seed`, trạng thái hover nút chính |
| UI Surface & Ink | `--canvas`, `--canvas-soft`, `--surface`, `--ink`, `--ink-secondary`, `--ink-muted` | `#ffffff`, `#f6f5f4`, `#ffffff`, `#000000`, `#31302e`, `#615d59` | Nền trang, thẻ bo góc, chữ tiêu đề, chữ dẫn (`13.18:1` trên nền trắng), chữ phụ |
| Math Highlight (H2) | `--accent-orange` | `#dd5b00` | Mặt cắt thiết diện, đường giao tuyến chính trong Hero/Storytelling/Interactive Demo |
| Math Text Contrast | `--accent-orange-deep` | `#793400` | Chữ nhãn trên chip metric `.axo-sp-story-metric-pill.is-highlight` / `.axo-sp-demo-metric-val` (`8.06:1`) và `.axo-sp-point-tag.is-intersection` (`9.11:1`) |
| Math Plane Tint | `--accent-sky-tint` | `#dcebfa` | Mặt phẳng cắt `(MNP)` và chip ngữ cảnh giả thiết toán học |

---

## 5. Before / After Logo & Header (`VERIFIED`)

| Thuộc tính đo (`before-perf.json` -> `after-perf.json`) | Before (V1.1) | After (V1.2) | Chênh lệch / Ghi chú |
|---|---|---|---|
| Desktop (`1920×1080`) Header Height | `72px` | `72px` | Giữ ổn định |
| Desktop Logo SVG (`#btn-landing-logo .axo-logo-svg`) | `24 × 24 px` | `29 × 29 px` | `+20.8%` kích thước cạnh |
| Desktop Wordmark (`font-size`) | `17px` | `20px` | `+17.6%`, nổi bật cân đối trên thanh 72px |
| Mobile (`390×844`) Header Height | `68px` | `68px` | Giữ ổn định |
| Mobile Logo SVG (`#btn-landing-logo .axo-logo-svg`) | `24 × 24 px` | `26 × 26 px` | `+8.3%`, `overflowX: false` |
| Mobile Wordmark (`font-size`) | `17px` | `18px` | `+5.9%` |
| Auth-aware Desktop Header (đã đăng nhập) | Không hiển thị tài khoản | `hasAccountWidget: true` (`Nguyễn Nhật Minh`), `#btn-landing-header-start` = `"Vào ứng dụng"` | Không chặn khách (`Guest` giữ `"Bắt đầu"` + `"Thư viện"`) |
| Auth-aware Mobile Drawer + Focus Trap | Không có thẻ tài khoản / trap | `#landing-mobile-account` (`Nguyễn Nhật Minh · Học sinh`), `mobileFocusTrapAllInside: true` | `Tab`/`Shift+Tab` xoay vòng khép kín trong drawer |

- Đồng bộ thanh trượt nav pill bằng `offsetLeft` / `offsetWidth` + `document.fonts.ready` và scroll-spy điều tiết qua `requestAnimationFrame` (`LandingHeader.tsx`).

---

## 6. Before / After CTA (`VERIFIED`)

- **Nút chính (`#btn-landing-header-start`, `#btn-landing-hero-start`, `#btn-landing-open-showcase-3d`, `#btn-landing-final-start`):** Chuyển từ `rgb(17, 17, 16)` (`#111110`) trên chữ trắng sang `rgb(0, 117, 222)` (`--primary: #0075de`) trên chữ `rgb(255, 255, 255)` (`4.57:1`, `passesAA: true`).
- **Nút phụ Hero:** Giữ nền trắng `rgb(255, 255, 255)` và chữ `rgb(0, 0, 0)` (`--ink`), tương phản cao với nút chính.
- **Điều hướng tự do cho Khách:** `enterAxoWorkspace()` và `openLibraryFromLanding()` đưa thẳng khách vào `/app` hoặc `/library` mà không dựng cổng bắt buộc đăng nhập (`landing-header-navigation.test.tsx`).

---

## 7. Before / After Hero Sculpture (`VERIFIED`)

- **Vấn đề V1.1:** Khối cầu/bát diện bay lơ lửng hai bên gây phân tán thị giác; dùng `MeshStandardMaterial` với 4 nguồn sáng + tone mapping tốn GPU/CPU; thiếu khóa StrictMode RAF và DPR cap trên màn hình dày điểm ảnh.
- **Nâng cấp V1.2 (`LandingHeroSculpture3D.tsx`):**
  - Loại bỏ `sphereCompanionGroup` và `octMesh`, giữ **một khối đa diện vát cạnh đơn khối** sạch sẽ trên nền trắng thoáng.
  - Phần nắp trên trong mờ (`opacity: 0.24`) làm lộ rõ mặt cắt thiết diện màu cam `#dd5b00` và mặt phẳng cắt viền xanh `#0075de`.
  - Thay `MeshStandardMaterial` / `ACESFilmicToneMapping` bằng **analytical face-normal vertex-color studio shading** trên `THREE.MeshBasicMaterial({ vertexColors: true })`.
  - Giảm thời gian dựng vào `entranceDurationMs = 650ms`, khóa `DPR` ở `1.25` (mobile) / `1.5` (desktop), tạm dừng RAF trong `120ms` khi đang cuộn trang, thêm cờ bảo vệ `requestAnimationFrame` dưới React StrictMode và chỉ bật `webglReady` khi canvas thật sự hiển thị.

---

## 8. Storyboard & Kết quả so sánh Animation vs Video (§6–§8)

### Mô hình toán học Storytelling

Cả hai phương án đều bám chuẩn một bài toán chuẩn xác từ `LANDING_PRISM_STORY_SPEC`:
**Lăng trụ tam giác đều `ABC.A′B′C′`** cạnh đáy `4`, chiều cao `4`, mặt phẳng cắt `(MNP)` (`M` trung điểm `AB`, `N` trung điểm `AC`, `P` trung điểm `CC′`) tạo giao tuyến `PQ // BC` cắt `BB′` tại trung điểm `Q`:
- **01 · Đề bài:** Dựng lăng trụ `ABC.A′B′C′`, ghim trung điểm `M ∈ AB`, `N ∈ AC`, `P ∈ CC′`.
- **02 · Phân tích:** Đường trung bình `MN // BC`; giao tuyến qua `P` song song `BC` nằm trong `(BCC′B′)`.
- **03 · Dựng hình:** Kẻ tia qua `P` song song `BC` cắt `BB′` tại `Q`; nối khép kín tứ giác `M–N–P–Q`.
- **04 · Khám phá:** Thiết diện **hình thang cân `MNPQ`** với hai đáy `MN = 2`, `PQ = 4`, hai cạnh bên `MQ = NP = 2√2`, diện tích chính xác `S(MNPQ) = 3√7`.

### Đo đạc thực nghiệm Option A vs Option B (`storytelling-comparison.json`)

> **Ghi nhận trung thực về điều kiện đo:** Benchmark thực hiện bằng Playwright Chromium (`ANGLE/SwiftShader`, `1920×1080` CPU `1x` và `390×844` CPU `4x`) sau khi cách ly tải Hero WebGL ban đầu (`storytelling-comparison.json`). Video đối chứng Option B tạo tất định ở độ phân giải `960×600 @ 30fps` (`18s`, VP8 `.webm` `410,749 bytes` + `poster.png` `125,189 bytes`).

| Tiêu chí so sánh | Option A: Vector SVG + CSS Motion Graphics | Option B: WebM Video `960×600@30fps` + Range Seek | Lợi thế |
|---|---|---|---|
| **1. Payload & tài nguyên mạng** | **`6.84 KB`** DOM/SVG inline (`0` file video/poster) | `523.38 KB` (`410.75 KB` WebM + `125.19 KB` PNG poster) | **Option A (-98.7% dung lượng)** |
| **2. Số WebGL / Canvas** | **`0` WebGL / `0` Canvas** | `0` WebGL / `0` Canvas | Ngang nhau |
| **3. CLS khi chuyển 4 chặng** | **`0`** (`frameHeightDeltaPx: 0`) | `0` | Ngang nhau |
| **4. Độ trễ chuyển chặng TB (`avgSwitchMs`)** | Desktop `642.60 ms` (`[270.9, 786.6, 446, 1066.9]`) / Mobile 4x `267.57 ms` (`[186.7, 132.8, 287.6, 463.2]`) | **Desktop `74.38 ms` / Mobile 4x `65.78 ms`** | Option B nhanh seek hơn trong SW-GL harness (lưu ý: `avgFps` benchmark SwiftShader Option A `9.7`/`28.6` vs Option B `37.4`/`141.3`) |
| **5. Main-thread Long Tasks lúc chuyển chặng** | Desktop `1` (`497 ms`) / Mobile 4x `4` (`803 ms`) | **Desktop `0` (`0 ms`) / Mobile 4x `0` (`0 ms`)** | Option B |
| **6. Idle RAF (1500ms đứng yên)** | **Desktop `0` / Mobile 4x `1`** | Desktop `4` / Mobile 4x `4` | **Option A ít RAF nền hơn** |
| **7. Độ sắc nét Retina / Zoom & Theme tokens** | **Sắc nét vector vô hạn ở mọi DPI**, chữ DOM sắc nét, ăn trực tiếp CSS `tokens.css` | Raster `960×600` bị mềm khi phóng >`960px` / Retina; chữ trong frame không chọn/không theo theme | **Option A vượt trội rõ rệt** |
| **8. Accessibility, Reduced Motion & Bảo trì** | Nút ARIA sống + phím mũi tên + `prefers-reduced-motion` tức thì; **single source of truth** từ `LANDING_PRISM_STORY_SPEC` | Phải render lại `.webm` + poster nhị phân mỗi lần chỉnh chữ/nhãn hoặc đổi màu | **Option A vượt trội rõ rệt** |

---

## 9. Quyết định lựa chọn phương án Storytelling (`VERIFIED`)

- **Phương án được chọn cho bản chính thức: Option A — Interactive Vector SVG + CSS Motion Graphics (`LandingStorytelling.tsx`).**
- **Lý do kỹ thuật dựa trên bằng chứng đo:**
  1. Payload nhẹ hơn ~76× (`6.84 KB` vs `523.38 KB`), `0` WebGL context và giữ toàn bộ nhãn đỉnh (`A, B, C, A′, B′, C′, M, N, P, Q`) sắc nét tuyệt đối ở mọi mức zoom & DPR.
  2. Khử segment stroke gap (bỏ `pathLength={100}`, dùng `stroke-dasharray: 420`), mở góc chiếu `37°` và thu gọn `planeQuad` `0.8x` giúp hình nằm gọn hoàn toàn trong khung.
  3. Rút gọn chiều cao đường chạy sticky từ `2862px` (`runwayToStickyRatio: 2.65`, khoảng trống đáy `383.9px`) xuống **`1641.59px` (`runwayToStickyRatio: 1.52`, khoảng trống đáy `188.3px`)**.
  4. Cố định đồng thời 4 pill chỉ số (`min-height: 34px`, trạng thái `.is-muted` khi chưa tới chặng 4) và `manualLockUntilRef` chống nhấp nháy khi chuyển chặng → **`frameHeightDeltaPx = 0px` (`CLS = 0` trong `storyStages`)**.
  5. File video `storytelling-prism-option-b.webm` giữ tại thư mục artifact audit bên ngoài git tree, không commit nhị phân dư thừa vào repo.

---

## 10. Before / After Interactive Demo (`VERIFIED`)

| Khía cạnh (`before-perf.json` -> `after-perf.json`) | Before (V1.1) | After (V1.2) |
|---|---|---|
| Nút lặp `#btn-landing-demo-prev` / `#btn-landing-demo-next` | Có (`hasPrevNext: true`) | Đã xóa (`hasPrevNext: false`); giữ `01..04` tabs + phím mũi tên `ArrowLeft`/`ArrowRight`/`ArrowUp`/`ArrowDown` |
| Huy hiệu đè đỉnh canvas (`topBadgeLeft`) | `"Bước 4/4"` | Đã xóa (`topBadgeLeft: null`) |
| Chỉ số toán học (`verifiedMetrics`) | Hòa trong mô tả text | Tách thành các chip chỉ số độc lập (Chóp: `S = 6√6`, `V = 32`; Lập phương: `S = 12√3`, `MN = 2√2`) |
| Đặt lại góc nhìn (`#btn-landing-demo-reset`) | Chưa có chế độ ngữ cảnh theo orbit | Ẩn mặc định (`data-visible="false"`), tự hiện khi xoay (`data-visible="true"`), bấm để reset **chỉ camera** và giữ nguyên bước đang học (`preservedStep3Active: true`) |

---

## 11. Kiểm tra Geometry Labels & Formula (`VERIFIED`)

- **Khử trùng lặp danh tính đỉnh (`extractPointsFromSample`):** Tập đỉnh đầu vào được khử trùng lặp ID; React key trên `.axo-sp-point-tag` dùng `${sample.id}:${pt.id}` nên không rò rỉ node giữa lần đổi Hình chóp ↔ Hình lập phương (`landing-webgl-lifecycle.test.tsx`).
- **Tách nhãn 2D chống chồng chéo (`separateLabelPositions`):** Đẩy giãn 2 lượt trên tọa độ chiếu 2D và kẹp an toàn trong khung canvas. Kết quả kiểm định DOM trên `after-perf.json` (`overlapAudit`):
  - **Storytelling SVG:** `10` nhãn — `overlaps: []` (`0` cặp chồng lấn).
  - **Interactive Demo — Hình chóp `S.ABCD`:** `11` nhãn — `overlaps: []`.
  - **Interactive Demo — Lập phương `ABCD.A′B′C′D′`:** `14` nhãn — `overlaps: []`.
- **Bất biến công thức & mặt phẳng (`landing-spatial-story.test.tsx` & `landing-demo-integrity.test.tsx`):**
  - Hình chóp `S.ABCD`: `M, N, P` đúng trung điểm; 5 điểm thiết diện `MENPF` thỏa mãn `x + y + 2z = 6`.
  - Lập phương `ABCD.A′B′C′D′`: lục giác `MNEPFQ` đồng phẳng trên `-x + y + z = 2`, 6 cạnh bằng nhau (`2√2`), `S = 12√3`.
  - Lăng trụ `ABC.A′B′C′`: `M, N, P, Q` đồng phẳng, `MN = 2`, `PQ = 4`, `MQ = NP = 2√2`, `S(MNPQ) = 3√7`.

---

## 12. Performance Before / After & Điều kiện đo (`VERIFIED`)

- **Điều kiện đo (`before-perf.json`, `after-perf.json`):** Playwright Chromium headless với `--use-gl=angle --use-angle=swiftshader`, `dpr: 1`. Mỗi pha chạy **3 phiên trình duyệt sạch độc lập**: ổn định `1.8s`, đo Idle Hero RAF `1.5s`, quét cuộn deterministic 65 bước toàn trang và cuộn lại, đo Idle Story RAF `1.5s`, chuyển mẫu Interactive Demo 4 lần (`Chóp ↔ Lập phương`), đo Idle Demo RAF `1.5s`. Desktop đo ở `1920×1080` (`1x` CPU); Mobile đo ở `390×844` (`4x` CPU throttling).

### Bảng tổng hợp 3 Run & Trung vị — Desktop (`1920×1080`, 1× CPU, SwiftShader)

| Chỉ số | Before Run 1 / 2 / 3 (**Median**) | After Run 1 / 2 / 3 (**Median**) | Biến thiên (Median) |
|---|---|---|---|
| WebGL Contexts (Initial / Scroll / 4× Switch) | `3 / 4 / 8` (cả 3 run) | **`1 / 2 / 2` (cả 3 run)** | **-66.7% initial · -75.0% sau đổi mẫu** |
| WebGL Context Lost | `0 / 0 / 0` (**0**) | `0 / 0 / 0` (**0**) | `0` |
| Idle RAF 1500ms (Hero / Story / Demo) | `0 / 9..12 / 0` (Story med **9**) | **`0 / 0 / 0` (cả 3 run)** | **Triệt tiêu hoàn toàn idle RAF thừa** |
| Avg FPS (trong lúc cuộn + chuyển mẫu SW-GL) | `7.3 / 7.1 / 7.1` (**7.1**) | `13.1 / 11.8 / 12.4` (**12.4**) | **+74.6%** |
| P95 Frame Time (ms) | `569.2 / 395.9 / 333.2` (**395.9**) | `187.5 / 194.4 / 194.5` (**194.4**) | **-50.9%** |
| Max Frame Time (ms) | `645.7 / 770.8 / 791.5` (**770.8**) | `868.1 / 923.5 / 916.6` (**916.6**) | +145.8 ms (xem ghi chú lazy Demo mount ở mục 16) |
| Long Tasks (số lượng / tổng ms) | `19, 24, 24` (**24**) / **5319 ms** | `17, 16, 16` (**16**) / **2507 ms** | **-33.3% số lượng · -52.9% tổng thời gian** |
| LCP (ms) | `2152 / 1924 / 1900` (**1924 ms**) | `1196 / 1084 / 1060` (**1084 ms**) | **-43.7%** |
| CLS | `0.1835 / 0.1835 / 0.1835` (**0.18**) | `0.1411 / 0.1411 / 0.1411` (**0.14**) | **-22.2%** |
| JS Heap Delta (MB) | `5.43 / 5.29 / 1.05` (**5.29 MB**) | `6.10 / 5.86 / 5.70` (**5.86 MB**) | Mức ổn định tương đương (`~38.13 MB` sau tương tác) |

### Bảng tổng hợp 3 Run & Trung vị — Mobile (`390×844`, 4× CPU Throttle, SwiftShader)

| Chỉ số | Before Run 1 / 2 / 3 (**Median**) | After Run 1 / 2 / 3 (**Median**) | Biến thiên (Median) |
|---|---|---|---|
| WebGL Contexts (Initial / Scroll / 4× Switch) | `2 / 4 / 8` (cả 3 run) | **`1 / 2 / 2` (cả 3 run)** | **-50% initial · -75.0% sau đổi mẫu** |
| WebGL Context Lost | `0 / 0 / 0` (**0**) | `0 / 0 / 0` (**0**) | `0` |
| Idle RAF 1500ms (Hero / Story / Demo) | `0 / 27 / 0` (Story med **27**) | **`0 / 0 / 0` (cả 3 run)** | **Triệt tiêu hoàn toàn 27 idle RAF Story** |
| Avg FPS | `35.9 / 34.1 / 36.2` (**35.9**) | `39.6 / 41.9 / 39.5` (**39.6**) | **+10.3%** |
| P95 Frame Time (ms) | `69.5 / 76.4 / 62.4` (**69.5**) | `69.5 / 62.5 / 76.3` (**69.5**) | Giữ ổn định |
| Max Long Task (ms) | `1303 / 1294 / 1349` (**1303**) | `817 / 835 / 803` (**817**) | **-37.3%** |
| Long Tasks (số lượng / tổng ms) | `11, 14, 11` (**11**) / **4281 ms** | `9, 11, 10` (**10**) / **2884 ms** | **-32.6% tổng thời gian block UI** |
| LCP (ms) | `3532 / 3512 / 3708` (**3532 ms**) | `2388 / 2436 / 2328` (**2388 ms**) | **-32.4%** |
| CLS | `0.0823 / 0.0839 / 0.0839` (**0.08**) | `0.1559 / 0.1744 / 0.1510` (**0.16**) | +0.08 (xem mục 16) |
| JS Heap Delta (MB) | `2.95 / 3.72 / 3.10` (**3.10 MB**) | `0.96 / -2.09 / 3.67` (**0.96 MB**) | **-69.0%** |

---

## 13. Ma trận Responsive Viewport (§16 — `VERIFIED`)

Toàn bộ **8 mức kích thước** (7 mức trong `after-perf.json` + kiểm tra bổ sung trực tiếp `1366×768`) đều không phát sinh thanh cuộn ngang (`overflowX: false`) và bảo toàn header, logo, CTA, Hero, Storytelling, Demo, Final CTA, Footer:

| Viewport | `scrollWidth / innerWidth` | `overflowX` | Header Height | Anchor / Ghi chú kiểm chứng |
|---|---|---|---|---|
| `1920 × 1080` (`desktop_1920`) | `1920 / 1920` | `false` | `72px` | `after-perf.json` |
| `1440 × 900` (`laptop_1440`) | `1440 / 1440` | `false` | `72px` | `after-perf.json` |
| `1366 × 768` (`laptop_1366`) | `1366 / 1366` | `false` | `72px` | Anchor `#cach-hoat-dong` heading `top=167px`, `#trai-nghiem` heading `top=187px` (cách đáy header `72px` lần lượt `95px` & `115px`; `scrollMarginTop: 88px`) |
| `1024 × 768` (`tablet_landscape_1024`) | `1024 / 1024` | `false` | `72px` | `after-perf.json` |
| `768 × 1024` (`tablet_portrait_768`) | `768 / 768` | `false` | `68px` | `after-perf.json` |
| `390 × 844` (`mobile_390`) | `390 / 390` | `false` | `68px` | `after-perf.json`, Mobile drawer + auth card PASS |
| `360 × 800` (`mobile_360`) | `360 / 360` | `false` | `68px` | `after-perf.json` |
| `320 × 568` (`mobile_320`) | `320 / 320` | `false` | `68px` | `after-perf.json` |

---

## 14. Kết quả Accessibility (§17 — `VERIFIED`)

| Bộ kiểm định WCAG AA (`after-perf.json -> contrastAudit`) | Màu chữ | Màu nền thực đo | Tỷ lệ tương phản | Đạt AA (`>= 4.5:1`) |
|---|---|---|---|---|
| `#btn-landing-header-start` | `rgb(255, 255, 255)` | `rgb(0, 117, 222)` | **`4.57 : 1`** | `PASS` |
| `#btn-landing-hero-start` | `rgb(255, 255, 255)` | `rgb(0, 117, 222)` | **`4.57 : 1`** | `PASS` |
| `.axo-sp-eyebrow` | `rgb(0, 91, 171)` | `rgb(255, 255, 255)` | **`6.81 : 1`** | `PASS` |
| `.axo-sp-hero-lead` | `rgb(49, 48, 46)` | `rgb(255, 255, 255)` | **`13.18 : 1`** | `PASS` |
| `.axo-sp-story-metric-pill.is-highlight` | `rgb(121, 52, 0)` | `rgb(252, 239, 230)` | **`8.06 : 1`** | `PASS` |
| `.axo-sp-point-tag.is-seed` | `rgb(0, 91, 171)` | `rgb(255, 255, 255)` | **`6.81 : 1`** | `PASS` |
| `.axo-sp-point-tag.is-intersection` | `rgb(121, 52, 0)` | `rgb(255, 255, 255)` | **`9.11 : 1`** | `PASS` |
| `.axo-sp-demo-metric-val` | `rgb(121, 52, 0)` | `rgb(252, 239, 230)` | **`8.06 : 1`** | `PASS` |

- **Bàn phím & Drawer modal:** `mobileFocusTrapAllInside: true` khi nhấn `Tab` / `Shift+Tab` liên tiếp trong `#landing-mobile-drawer`; đóng bằng `Escape`; phím mũi tên chuyển bước ở Storytelling & Interactive Demo và xoay camera ở canvas 3D.
- **Reduced Motion:** CSS `@media (prefers-reduced-motion: reduce)` trong `landing.css` và tắt animation tự động trong `LandingHeroSculpture3D.tsx`.

---

## 15. TypeScript, Build, Vitest & Bằng chứng Browser/Video (`VERIFIED`)

- **TypeScript (`npx tsc -b`):** Exit `0` (0 lỗi).
- **Production Build (`npm run build`):** Exit `0` — 118 modules built trong `4.43s` (`dist/assets/index-BN3telHR.css 384.35 kB`, `dist/assets/vendor-three-C9WMaCbY.js 593.92 kB`, `dist/assets/index-D6wCkv9v.js 1,064.77 kB`, `dist/assets/geometry-samples-CG-Uw38U.js 1,359.68 kB`).
- **Full Vitest (`npx vitest run --maxWorkers=2`):** Exit `0` — **`Test Files 172 passed (172)`**, **`Tests 2187 passed (2187)`**, thời gian **`93.14s`** (không chỉnh tăng timeout tùy tiện).
- **Chạy độc lập hai suite hình học nặng từ báo cáo V1.1 (cùng `--maxWorkers=2`):**
  - `src/simulations/domains/geometry/axo-pedagogical-presentation-hardening.test.tsx`: `8 passed` (`4339ms`).
  - `src/simulations/domains/geometry/axo-cross-family-scene3d-acceptance.test.tsx`: `10 passed` (`4984ms`).
  - Tổng hợp: `2 passed (2)`, `18 passed (18)`, Duration **`7.05s`** (`0` timeout).
- **Bằng chứng Ảnh chụp & Video chuyển động ngoài repo (tại `C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_2_audit/`):**
  - Ảnh `before/` (`before_01..before_11.png`) và `after/` (`after_01..after_15.png`, đã mở kiểm tra trực quan 11 ảnh key gồm `after_01`, `after_03`, `after_04`, `after_07`, `after_08`, `after_09`, `after_10`, `after_11`, `after_12`, `after_13`, `after_15`).
  - Video `.webm` kiểm chứng chuyển động (`video/`):
    - `hero-motion.webm` (`597,785 bytes`)
    - `storytelling-scroll.webm` (`720,551 bytes`)
    - `interactive-demo.webm` (`1,061,153 bytes`)
    - `mobile-experience.webm` (`457,037 bytes`)
  - Dữ liệu JSON & đối chứng Option B: `perf/before-perf.json`, `perf/after-perf.json`, `storytelling_comparison/storytelling-comparison.json`, `storytelling_comparison/option_b/storytelling-prism-option-b.webm` (`410,749 bytes`).
- **REA MCP:** `NOT VERIFIED` trong V1.2 (dùng lại phân tích tham chiếu Notion / Alex Greenshpun / Bún đậu Mayonnaise từ V1.1 theo §19; kiểm chứng thực thi hiện tại dùng Playwright Chromium + Vitest).

---

## 16. Các điểm còn tồn tại & Lưu ý trung thực (Residual Items)

1. **Mobile cold-load CLS (`0.16` trên `390×844`, `after-perf.json`) & `maxFrameMs` (`916.6 ms` desktop SwiftShader):**
   - Trong `storyStages` của Storytelling, `CLS = 0` (`frameHeightDeltaPx = 0`), và benchmark riêng Option A ghi nhận `cls: 0`. Giá trị CLS cấp trang (`0.14` desktop / `0.16` mobile) đến từ lần dựng khung initial layout / lazy hydrate WebGL dưới 4× CPU SwiftShader khi quét toàn trang liên tục.
   - Đỉnh `maxFrameMs` (`~916 ms` desktop / `~652 ms` mobile) rơi vào thời điểm `InteractiveDemo` khởi tạo lần đầu `WebGLRenderer` dưới phần mềm `ANGLE/SwiftShader` không có GPU phần cứng (`rootMargin: "320px 0px"`), nhưng đã tách khỏi initial Hero paint nên LCP giảm `43.7%` desktop / `32.4%` mobile.
2. **Audit docs tồn đọng ngoài phạm vi (`NOT_OUR_REGRESSION`):** `backend/scripts/audit_docs_information_architecture.py` báo 4 đường dẫn cũ ở `docs/CODE_INDEX.md` các dòng `4605, 4619, 4634, 4646` (`LiveClassDock.tsx`, `LiveClassStrip.tsx`, `MonitorView.tsx`, `state/classroom-sync.ts`) thuộc thay đổi xóa Classroom đang chưa commit của phiên song song. Phần Landing có `0` đường dẫn hỏng.

---

## 17. Backend Handoff

`None` — Phiên Landing V1.2 không sửa bất kỳ file nào thuộc Backend, Geometry Engine hoặc hợp đồng API.

---

## 18. Thay đổi chưa commit của phiên song song được bảo toàn

Toàn bộ các thay đổi chưa commit của phiên khác trên worktree `D:\Documents\projects\axo-geometry-library` được giữ nguyên 100%, không stage, không restore, không ghi đè:
- `backend/app/accounts/**`, `backend/app/main.py`, `backend/app/persistence/classroom_models.py`, `backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py`, `backend/scripts/seed_demo_accounts.py`, `backend/tests/**`
- `docs/EVIDENCE_INDEX.md`, `docs/evaluation/geometry/runs/axo-*`
- `frontend/index.html`, `frontend/package*.json`, `frontend/public/favicon*`, `frontend/public/prototypes/`, `frontend/scripts/attachment-resize.node-test.mjs`
- `frontend/src/components/{AssignDialog,AssignmentsView,AuthGate,AxoErrorExperience,ClassesView,HomeView,LiveClassDock,LiveClassStrip,MonitorRoute,MonitorView,ObserveView,PracticeReporter,ScreenCaptureDialog,SimulationWorkspace,TopNav}.tsx` và các test Workspace/Attachment/Classroom tương ứng
- `frontend/src/simulations/domains/geometry/{Scene3DExplorer.tsx,scene3d-focus-mode.test.tsx,scene3d-tool-menu.tsx}`, `frontend/src/state/**`, `frontend/src/styles/{scrollbar-ownership.test.ts,transition-semantics.test.ts}`

---

## 19. Commit SHAs & Trạng thái phê duyệt

- **Code Commits trên `feat/axo-geometry-library-verification`:**
  - `6712a7a50` — `style(axo): align landing components with design system`
  - `ef5dd3d37` — `feat(axo): refine landing visual storytelling`
  - `42502b9c6` — `refactor(axo): simplify interactive geometry showcase`
  - `fb5650d0f` — `perf(axo): optimize landing animation lifecycle`
- **Docs Commit:** được tạo ngay sau báo cáo này (`docs/CODE_INDEX.md` + `docs/evaluation/landing/AXO-LANDING-V1.2-REPORT.md`, gắn `DOCUMENTATION_COMMIT_ROLE = SELF`).

**Owner Approval:** `PENDING_OWNER_REVIEW`
