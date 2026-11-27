# FINAL_ACCEPTANCE_REPORT — AXO Final Responsive Hero, Sidebar Brand Wordmark & Vercel Deployment Closure

- **Trạng thái bàn giao:**
  - `AXO_FINAL_HERO_SIDEBAR_REFINEMENT_READY_FOR_OWNER_REVIEW`
  - `VERCEL_CONFIG_READY`
  - `VERCEL_LOCAL_VALIDATION_PASS`
  - `VERCEL_PREVIEW_VALIDATION_PENDING`
  - `VERCEL_PRODUCTION_DEPLOYMENT_PENDING`
  - `BACKEND_DEPLOYMENT_PENDING`
- **Ngày hoàn thiện báo cáo tổng hợp:** `2026-11-27`
- **Thư mục run:** [`docs/evaluation/geometry/runs/axo-hero-footer-redesign-vercel-hardening/`](.)
- **Số liệu đo hiển thị chi tiết (JSON):** [`visual-metrics.json`](visual-metrics.json) · [`after-visual-metrics.json`](after-visual-metrics.json)

---

## 1. Git State và Baseline

| Hạng mục | Giá trị xác minh thực tế |
|---|---|
| **Repository chính** | `D:\Documents\projects\algo-sim` (`MERGE_HEAD = False`, không conflict, nguyên vẹn) |
| **Branch tích hợp đích** | `main` (`08b40cc3cff9c2a66adec60dfa0b5b3808f82a62`) |
| **`origin/main`** | `08b40cc3cff9c2a66adec60dfa0b5b3808f82a62` (khớp `main`) |
| **Worktree triển khai** | `D:\Documents\projects\algo-sim\.superpowers\worktrees\axo-landing-page-design` |
| **Branch làm việc** | `feat/axo-hero-footer-redesign` (`HEAD = 08b40cc3cff9c2a66adec60dfa0b5b3808f82a62`, chưa commit/merge/push) |
| **Cổng nghiệm thu** | Frontend duy nhất `http://localhost:3000/about` (Landing) và `http://localhost:3000/app` (Workspace) |

---

## 2. Các Hạn Chế Responsive & Thương Hiệu Trước Đợt Tinh Chỉnh Cuối

So với mốc Chiến dịch 3 ([`screenshots/before-final-refinement/`](screenshots/before-final-refinement/)):

1. **Tỷ lệ chữ / hình học và khoảng trống ngang Hero trên desktop:** Chia lưới gần 50/50 (`1.02fr / 0.98fr`) với khoảng trống trắng xung quanh SVG (`viewBox="0 0 480 420"`) khiến kích thước mực vẽ thực tế trên `1440px` mới đạt `309.6 × 302.0px`, khoảng cách ngang tới khối chữ rộng và điều khiển tách xa dưới hình.
2. **Tablet dọc (`768×1024`, `1024×1366`) thiếu liên kết dọc:** Cột chữ căn trái trong khi hình học căn giữa một dải rộng; chiều cao `960px` cũng chưa tách bạch tablet ngang (`1024×768`) và tablet dọc (`1024×1366`).
3. **Sidebar mở rộng vẫn dùng `[Icon] Axo` (`17px, 650`):** `font-weight: 650` không có trong bộ Inter `400/500/600/700` được nạp từ Google Fonts (`index.html`), và icon nhỏ cạnh chữ làm đầu Sidebar nặng thị giác hơn phong cách tối giản của Workspace.

---

## 3. Chiến Lược Responsive Cuối (Desktop → Laptop → Tablet → Mobile)

- **Desktop rộng (`2560×1440`, `1920×1080`):** Giữ container `1240px` (`--axo-v14-container-max`) đồng bộ Header/Section; không kéo giãn tràn viewport; heading giữ trần `50px` (`3.125rem`).
- **Laptop (`1440×900`, `1366×768`, `1280×720`, `1024×768`):** Giữ bố cục 2 cột `Chữ trái — Hình học phải`, thu gọn `column-gap` và co scale hình học mềm ở `<= 1160px` để heading luôn giữ `2` dòng và không bị cắt theo chiều cao thấp (`720px`/`768px`).
- **Tablet (`1024×1366`, `820×1180`, `768×1024`):** Xếp dọc căn giữa toàn khối (heading, lead, CTA pair, SVG showcase `380px`, controls) tạo một trục thị giác thống nhất.
- **Mobile (`430×932`, `390×844`, `375×812`, `360×800`, `320×700`):** Khôi phục nhịp đọc căn trái tự nhiên trên mobile hẹp (Heading → Lead → CTA → Showcase `300px`, co `248px` ở `<= 359px` kèm CTA xếp dọc 44px), không thu nhỏ nút dưới ngưỡng chạm.

---

## 4. Breakpoint Thực Tế & Kết Quả Quét Liên Tục (`320–2560px`)

| Breakpoint (`landing.css`) | Phạm vi áp dụng & Lý do | Kết quả đo `resizeSweep` (`23` độ rộng) |
|---|---|---|
| **Mặc định (`> 1160px`)** | `1280–2560px`: lưới `0.92fr / 1.08fr`, `column-gap: clamp(24px, 3.2vw, 44px)`, showcase `424px` | `overflowX = 0`, `ctaOverlap = false`, `clipped = false`, `H1 = 47.2–50px` (`2` dòng) |
| `@media (max-width: 1160px)` | Laptop/tablet ngang `921–1160px` (`1024×768`): lưới `0.94fr / 1.06fr`, `clamp(340px, 38vw, 404px)` | `1024px`: `heroH = 542.2px`, `H1 = 36.99px`, ink `323.8×315.9px` |
| `@media (max-width: 920px), (max-width: 1080px) and (orientation: portrait)` | Tablet dọc (`1024×1366`, `820×1180`, `768×1024`): xếp dọc căn giữa trục giữa, max showcase `380px` | `768–1024p`: `heroH = 703.2–715.5px`, ink `316.2×308.5px` |
| `@media (max-width: 680px)` | Mobile (`360–680px`): căn trái đọc thuận mắt, 2 CTA một hàng `min-height: 44px`, showcase `300px` | `360–430`: `heroH = 566.6–587.4px`, ink `249.6×243.5px` |
| `@media (max-width: 359px)` | Mobile cực hẹp (`320×700`, `359px`): xếp dọc 2 CTA, phụ tối giản 44px, showcase `248px` | `320px`: `heroH = 562.5px`, ink `206.4×201.3px`, `overflowX = 0` |

*Toàn bộ 23 độ rộng trong dải quét liên tục `[320, 359, 360, 375, 390, 430, 600, 640, 680, 681, 768, 820, 920, 921, 960, 1024, 1080, 1160, 1280, 1366, 1440, 1920, 2560]` đạt `overflowX = 0`, `ctaOverlap = false`, `clipped = false`.*

---

## 5. Bố Cục Hero Trước / Sau

- **Hero Left (`LandingHeroV14.tsx`):** Bảo toàn tuyệt đối nội dung bất biến (`H1` 2 dòng *"Hình học không gian, / dễ hình dung hơn."*, đoạn mô tả, 2 CTA), `factsCount = 0`.
- **Siết chặt SVG `viewBox` đồng nhất trên cả 3 cảnh:** `viewBox="0 0 480 420"` → **`viewBox="54 42 372 336"`** (`aspect-ratio: 372 / 336`), giữ nguyên **100%** tọa độ đỉnh, đường sinh, nét đứt và nhãn `α, β, Δ` (khoảng an toàn rìa tối thiểu `>= 16px` trong khung `54..426 × 42..378`), đồng thời tinh chỉnh nét vẽ tương ứng độ phóng `1.14x` (`1.6px` nét chính, `1.25px` nét khuất).

---

## 6. Kích Thước Hình Học Thực Tế & Optical Alignment

Đo bằng SVG `getBBox()` ánh xạ qua `getScreenCTM()` (`after-visual-metrics.json`):

| Viewport | Cột `gridCols` | Thực tế Ink W×H | Mức tăng vs C3 | `copyCenterY` | `inkCenterY` | `showcaseCenterY` | `horizontalInkGap` | Fold Vis |
|---|---|---|---|---:|---:|---:|---:|---:|
| `2560×1440` | `550.2 / 645.8px` | `352.9 × 344.2px` | **`+14.0%`** | `386.5px` | `366.5px` | `386.5px` | `214.6px` | **`100%`** |
| `1920×1080` | `550.2 / 645.8px` | `352.9 × 344.2px` | **`+14.0%`** | `377.9px` | `357.9px` | `377.9px` | `214.6px` | **`100%`** |
| `1440×900` | `550.2 / 645.8px` | `352.9 × 344.2px` | **`+14.0%`** | `363.6px` | `343.6px` | `363.6px` | `214.6px` | **`100%`** |
| `1366×768` | `550.3 / 646.0px` | `352.8 × 344.2px` | **`+13.9%`** | `360.4px` | `340.4px` | `360.4px` | `214.6px` | **`100%`** |
| `1280×720` | `525.8 / 617.3px` | `352.9 × 344.2px` | — | `354.3px` | `334.3px` | `354.3px` | `172.9px` | **`100%`** |
| `1024×768` | `430.3 / 485.2px` | `323.8 × 315.9px` | — | `335.4px` | `315.5px` | `335.4px` | `107.3px` | **`100%`** |
| `1024×1366` | Stacked `942.1px` | `316.2 × 308.5px` | — | `221.1px` | `539.9px` | `559.8px` | Stacked | **`100%`** |
| `820×1180` | Stacked `754.4px` | `316.2 × 308.4px` | — | `212.4px` | `526.5px` | `546.5px` | Stacked | **`100%`** |
| `768×1024` | Stacked `706.6px` | `316.2 × 308.5px` | — | `211.0px` | `523.6px` | `543.6px` | Stacked | **`100%`** |
| `430×932` | Stacked `390px` | `249.6 × 243.5px` | — | `185.8px` | `441.2px` | `462.1px` | Stacked | **`100%`** |
| `390×844` | Stacked `350px` | `249.6 × 243.5px` | — | `182.9px` | `435.4px` | `456.4px` | Stacked | **`100%`** |
| `375×812` | Stacked `335px` | `249.6 × 243.5px` | — | `181.8px` | `433.2px` | `454.2px` | Stacked | **`100%`** |
| `360×800` | Stacked `320px` | `249.6 × 243.5px` | — | `192.2px` | `454.0px` | `474.9px` | Stacked | **`100%`** |
| `320×700` | Stacked `280px` | `206.4 × 201.3px` | — | `204.3px` | `454.6px` | `475.5px` | Stacked | **`100%`** |

*3 cảnh tại `1440×900` duy trì `heroH = 601.1875px` (`heroHeightShiftMax = 0px`): Dodecahedron `352.9×344.2px`, Cylinder `346.7×346.5px`, Dihedral `385.3×334.0px` — trọng lượng thị giác đồng đều, không cảnh nào bị cắt hay tràn khung.*

---

## 7. Khoảng Cách Hình Học & Scene Controls

- Cắt khoảng trống thừa bên dưới sân khấu và kéo controls lên bằng `margin-top: -4px` (`-2px` trên mobile) nhưng giữ nguyên vùng chạm `min-width: 44px; min-height: 44px` trên cả `#hero-scene-dot-0..2` lẫn `#hero-scene-toggle`.
- Khoảng cách đo thật tại `1440×900`:
  - Từ đáy mực vẽ (`ink.bottom = 515.7px`) tới rìa trên vùng bấm 44×44 (`controlsRect.top`): **`15.4px`** (không chồng lấn hit area).
  - Từ đáy mực vẽ tới cạnh trên dot pill nhìn thấy: **`30.4px`** (mobile: `24.3–26.7px`; tablet: `28.4px`), gọn và gắn kết rõ rệt.

---

## 8. Kết Quả Hai Chu kỳ Autoplay & Vòng Đời (`Phase 5.4`)

- **Kiểm chứng trên Chromium thật (`capture-campaign4.mjs`, `1440×900`):**
  - Chuỗi 7 trạng thái thu được trong [`hero-autoplay-2cycles.webm`](screenshots/after/hero-autoplay-2cycles.webm) (`2,138,227 B`):
    1. `dodecahedron` (`0 ms`, `heroH = 601.1875px`)
    2. `cylinder-section` (`5,531 ms`, `601.1875px`)
    3. `dihedral-planes` (`11,381 ms`, `601.1875px`)
    4. `dodecahedron` (`17,353 ms`, `601.1875px`)
    5. `cylinder-section` (`23,617 ms`, `601.1875px`)
    6. `dihedral-planes` (`29,576 ms`, `601.1875px`)
    7. `dodecahedron` (`35,577 ms`, `601.1875px`)
  - **`twoCycleMatched = true`**, **`twoCycleHeroShiftMax = 0px`**, không blank frame, không nhấp nháy.
- **Vòng đời & Accessibility:** `hoverLifecycleOk = true`, `togglePersistenceOk = true` (Pause chủ động giữ nguyên qua hover leave / blur / scroll offscreen rồi quay lại), `offscreenObserverOk = true`, `visibilityOk = true`, `keyboardOk = true`, `reducedMotionOk = true`, chuyển route `/about → /library → /about` sạch sẽ.
- **Unit test:** `landing-hero-visual-lifecycle.test.tsx` xác nhận helper `nextHeroSceneIndex` quay đủ 2 vòng `0→1→2→0→1→2→0` và `HERO_SCENE_DWELL_MS === 6000`.

---

## 9. Sidebar Wordmark Trước / Sau (`LeftSidebar.tsx` + `global.css`)

- **Trước ([`before-sidebar-expanded-1440.png`](screenshots/before-final-refinement/before-sidebar-expanded-1440.png)):** `#sb-brand-home` chứa `<span class="sb-brand-logo"><IconAxoLogo size={22} /></span>` + `<span class="sb-brand-name">Axo</span>`.
- **Sau ([`after-sidebar-expanded-1440.png`](screenshots/after/after-sidebar-expanded-1440.png)):** Gỡ bỏ hoàn toàn `<IconAxoLogo>` và `.sb-brand-logo` trong Sidebar mở rộng, giữ nguyên `<button id="sb-brand-home" class="sb-brand" aria-label="Axo — Về màn hình nhập đề toán">` chỉ còn `<span class="sb-brand-name">Axo</span>`.
- **Trạng thái thu gọn & mobile drawer:** Giữ nguyên `#btn-sidebar-open-trigger` (`IconSidebarCollapsedTrigger`) ở Sidebar thu gọn ([`after-sidebar-collapsed-1440.png`](screenshots/after/after-sidebar-collapsed-1440.png)) và nút Search + Close trên mobile drawer ([`after-sidebar-mobile-390.png`](screenshots/after/after-sidebar-mobile-390.png), không chồng lấn).

---

## 10. Thông Số Typography Thực Tế Của Wordmark

| Thuộc tính | Trước (`before-sidebar-metrics`) | Sau (`after-visual-metrics`) | Ghi chú |
|---|---|---|---|
| `font-family` | `Inter, ...` | `Inter, ...` | Dùng font Inter sẵn có trong `index.html`, **0** font remote mới |
| `font-size` | `17px` | **`24px`** | Khớp dải 23–25px, cân tỷ lệ header Sidebar |
| `font-weight` | `650` *(không nằm trong `400;500;600;700`)* | **`600`** *(Inter SemiBold tải thật)* | Không dùng gradient/glow/shadow |
| `letter-spacing` | `-0.34px` (`-0.02em`) | **`-0.96px`** (`-0.04em`) | Khít gọn đặc trưng Axo wordmark |
| `line-height` | `18.7px` (`1.1`) | **`24px`** (`1`) | Giữ `#sb-header` cao đúng `48px` như trước |
| Căn lề trái vs icon menu đầu | `brandRect.left = 10px` | `wordmarkLeftX = 22px` = `sbNavFirstIconLeftX = 22px` | **`wordmarkToNavIconDeltaX = 0px`** |

---

## 11. Bằng Chứng Giữ Nguyên Logo Ở Mọi Vị Trí Khác (Brand Scope Lock)

- **SSR Vitest (`sidebar-brand-wordmark.test.tsx`):** Xác nhận `LandingHeader.tsx`, `LandingFooter.tsx`, `TopNav.tsx`, `AuthGate.tsx` (Login + Admin sidebar `IconAxoSidebarLogo` + `Axo Quản trị`) và `icons.tsx` (`IconAxoLogo`, `IconAxoSidebarLogo`) hoàn toàn nguyên vẹn; `branding.test.tsx` xác nhận `favicon.svg` & tab title `Axo` giữ nguyên.
- **Trình duyệt thật:** Landing Header (`headerLogoSvgs >= 1`), Landing Footer (`footerLogoSvgs = 3`), `/login` (`loginLogoSvgs = 2`) và `/admin` (`hasSvg: true, title: "Axo", sub: "Quản trị"`) đều bảo toàn biểu trưng đầy đủ.

---

## 12. Sidebar Functional & Auth Regression

- Guest (`/app`): Click `#nav-item-library` → `/library`, `#sb-brand-home` → `/app`, `#nav-item-new-problem` ok, badge thư viện `11`, mở/đóng hộp tìm kiếm `#axo-search-modal`, nút lọc `.sb-filter-trigger-btn`, thu gọn `#btn-sidebar-collapse` & mở lại `#btn-sidebar-open-trigger`, hover/focus nút tìm kiếm & thu gọn ([`after-sidebar-controls-focus-1440.png`](screenshots/after/after-sidebar-controls-focus-1440.png)), mobile drawer `overflowX = 0`.
- Authenticated Student (`Pass B`): [`after-sidebar-auth-1440.png`](screenshots/after/after-sidebar-auth-1440.png) hiển thị wordmark `Axo` (`24px`, `600`, `sbHeaderHeight = 48px`) cùng hồ sơ `"Nguyễn Minh Anh / Học sinh"`.

---

## 13. Performance & Asset Measurements (`dist/` trên Cổng `3000`)

- **3 lượt lặp `c2-waterfall.mjs` trên `1440×900`:**
  - LCP: `[380, 372, 460]` ms (Route Matrix median `472 ms`) · CLS: **`0.0009`** (`[0.0009, 0.0009, 0.001]`).
  - Tổng initial requests: **`14`**, Encoded local: **`4,205,258 B`** (`dist/assets/index-CMUo9evk.js` gzip `315.51 kB`, `index-CIkMycCD.css` gzip `64.27 kB`), PNGs trên disk: `7` file (`730,859 B`, giảm `-70.6%` vs Pre-C1, **0** request ảnh Hero PNG).
  - `phase10DistFullPage`: cả 3 bước *Cách hoạt động* `stepOpacity = "1"`, `imgComplete = true`, `imgNatW = 1840`.

---

## 14. Vercel Preservation & Deployment Status

- Bảo toàn nguyên vẹn [`frontend/vercel.json`](../../../../../frontend/vercel.json), `vercel-config.test.ts` (4/4), canonical `/about` (`/gioi-thieu`, `?preview=`), `/forgot-password`, API exclusions (`/api/*` trả `404` JSON/plain non-HTML), asset exclusion (`/assets/nonexistent.js` trả `404` non-HTML), immutable cache 8-char hash (`/assets/geometry-samples-DJZVi0c4.js`), và [`VERCEL_FRONTEND_DEPLOYMENT_RUNBOOK.md`](../../../../architecture/VERCEL_FRONTEND_DEPLOYMENT_RUNBOOK.md).
- Trạng thái triển khai thực tế: `VERCEL_CONFIG_READY`, `VERCEL_LOCAL_VALIDATION_PASS`, **`VERCEL_PREVIEW_VALIDATION_PENDING`**, **`VERCEL_PRODUCTION_DEPLOYMENT_PENDING`**, **`BACKEND_DEPLOYMENT_PENDING`**.

---

## 15. Console Error Classification (`Pass A`) & Backend `/api/analyze` Contract (`Pass B`)

- **Phân loại Console Error trên Pass A (`dist/` không kèm backend, `17` routes):**
  - `expectedOfflineApiUnavailable`: **`77`** (toàn bộ là gọi `/api/auth/me`, `/api/health`, `/api/auth/recovery-status` trả `404` từ harness cục bộ chưa nối backend).
  - `jsRuntimeErrors`: **`0`** · `networkAssetErrors`: **`0`** · `routingOrUnexpectedHttpErrors`: **`0`** · **`unexpectedConsoleErrorsCount`: `0`** (`zeroUnexpectedConsoleErrors: true`, `zeroPageErrors: true`).
- **Kiểm chứng `/api/analyze` trên Pass B (FastAPI `:8000`, `ALLOW_LIVE_AI=0`, `HYBRID_ROUTE_MODE=staging-replay`, DB SQLite tạm cô lập):**
  - Schema không hợp lệ (`{ input: "..." }`): **`422` JSON** (`analyzeInvalidSchema422`, *không* tính là giải bài toán).
  - Đầu vào hợp lệ ngoài miền (`type: "text"` phi hình học) & đầu vào hình học trong chế độ offline không corpus: trả **`503 STAGING_CORPUS_UNAVAILABLE` JSON** fail-closed (tuyệt đối không rò HTML, không gọi external AI).
  - Kèm `accept-landing-cutover-and-admin.mjs`: **`16/16` PASS**, `0` unexpected console/page/5xx errors.

---

## 16. Build / Vitest / Playwright / Freeze Receipts (Sau Chỉnh Sửa Cuối)

| Kiểm tra | Kết quả | Chi tiết |
|---|---|---|
| `npm run build` (`tsc -b && vite build`) | **PASS** | `0` lỗi TS, `123` modules trong `9.51s` |
| **Full Vitest (timeout mặc định)** | **`191 / 191` files · `2,309 / 2,309` tests PASS** | `166.46s` (`WALL_SEC = 183.53s`), `0` failed, `0` skipped, không tăng `--testTimeout` |
| `capture-campaign4.mjs` (dev `:3000`) | **`8 / 8` nhóm PASS** | `14` viewports, `23` resize sweep widths, `2` chu kỳ autoplay + WebM, full lifecycle + Sidebar |
| `design-taste-frontend` `inspect.mjs` (`dist/` `:3000`) | **`0 FAIL`** (`1 WARN [no-footage]`) | H1 `2` dòng (`1440: 50px`, `768: 40px`, `390: 30.6px`), `Inter 100%`, `overflow: 0` |
| `verify-route-matrix.mjs` (`Pass A` `dist/`) | **`17 / 17` routes PASS** | F5 + Back/Forward + `/simulation/pyramid-circumscribed-sphere` PASS |
| `verify-backend-integration.mjs` (`Pass B`) | **PASS (`allOk: true`)** | Health, 404 JSON, Guest 401, Teacher RBAC 403 (`HttpOnly, SameSite=Lax`), `/api/analyze` |
| `accept-landing-cutover-and-admin.mjs` (`Pass B`) | **`16 / 16` PASS** | Responsive 7 viewports, interactions, auth/admin RBAC, `0` console/page/5xx errors |
| `capture-sidebar-auth-and-admin.mjs` (`Pass B`) | **PASS** | Student `/app` wordmark + Admin `Axo Quản trị` logo giữ nguyên |

---

## 17. Historical Freeze Integrity

- `python backend/scripts/freeze_evaluation_candidate.py --verify-historical`: **`PASS`** (commit `4978ac01f`, `127` files, `7bd85b6e2c8719e4…`, `git_head_provenance=True`).
- `pytest -q backend/tests/semantic_program/test_evaluation_candidate.py`: **`40 passed in 79.78s` (`0:01:19`)**.
- `python backend/scripts/audit_docs_information_architecture.py`: **`PASS`** (`0` broken links, `0` secret leaks).

---

## 18. Danh Sách Đầy Đủ File Sửa / Thêm / Xóa (`git status --short`)

- **Modified (17):** `docs/CODE_INDEX.md`, `docs/OPERATIONS.md`, `docs/architecture/README.md`, `frontend/scripts/accept-landing-cutover-and-admin.mjs`, `frontend/src/App.tsx`, `frontend/src/components/AxoErrorExperience.tsx`, `frontend/src/components/LeftSidebar.tsx`, `frontend/src/components/__tests__/header-sidebar-icon-alignment.test.tsx`, `frontend/src/components/__tests__/landing-footer-layout.test.tsx`, `frontend/src/components/__tests__/landing-hero-visual-lifecycle.test.tsx`, `frontend/src/components/__tests__/landing-minimal-restructure.test.tsx`, `frontend/src/components/landing/LandingFooter.tsx`, `frontend/src/components/landing/LandingHeroV14.tsx`, `frontend/src/components/landing/LandingHowItWorks.tsx`, `frontend/src/components/landing/landing.css`, `frontend/src/components/sidebar-scrollbar-refinement.test.tsx`, `frontend/src/styles/global.css`.
- **Deleted (4 PNG AI lỗi thời):** `frontend/public/assets/landing/hero-studio/hero-float-orbit.png`, `frontend/public/assets/landing/hero-studio/hero-float-plane.png`, `frontend/public/assets/landing/hero-studio/hero-studio-diorama.png`, `frontend/public/assets/landing/studio-scenes/closing-scene.png`.
- **Untracked / Added (5 nhóm):** `frontend/vercel.json`, `frontend/src/vercel-config.test.ts`, `frontend/src/components/__tests__/sidebar-brand-wordmark.test.tsx`, `docs/architecture/VERCEL_FRONTEND_DEPLOYMENT_RUNBOOK.md`, `docs/evaluation/geometry/runs/axo-hero-footer-redesign-vercel-hardening/`.

---

## 19. Kế Hoạch Staging Ba Nhóm Commit (Không Trùng File)

*Thứ tự khuyến nghị: Commit 1 (hạ tầng route độc lập) → Commit 2 (Landing Hero/Footer/bằng chứng & xóa asset cũ) → Commit 3 (Sidebar wordmark).* Mỗi file chỉ xuất hiện trong **đúng một** commit, mọi commit giữ repo build được hoàn toàn:

1. **`fix(deploy): finalize Vercel SPA routing and deployment configuration`**
   - `frontend/vercel.json`
   - `frontend/src/vercel-config.test.ts`
   - `frontend/src/App.tsx`
   - `frontend/src/components/AxoErrorExperience.tsx`
   - `docs/architecture/VERCEL_FRONTEND_DEPLOYMENT_RUNBOOK.md`
   - `docs/architecture/README.md`
   - `docs/OPERATIONS.md`
2. **`feat(landing): finalize responsive automatic geometric hero and landing visuals`**
   - `frontend/src/components/landing/LandingHeroV14.tsx`
   - `frontend/src/components/landing/LandingHowItWorks.tsx`
   - `frontend/src/components/landing/LandingFooter.tsx`
   - `frontend/src/components/landing/landing.css`
   - `frontend/src/components/__tests__/landing-hero-visual-lifecycle.test.tsx`
   - `frontend/src/components/__tests__/landing-minimal-restructure.test.tsx`
   - `frontend/src/components/__tests__/landing-footer-layout.test.tsx`
   - `frontend/scripts/accept-landing-cutover-and-admin.mjs`
   - `frontend/public/assets/landing/hero-studio/hero-float-orbit.png` *(delete)*
   - `frontend/public/assets/landing/hero-studio/hero-float-plane.png` *(delete)*
   - `frontend/public/assets/landing/hero-studio/hero-studio-diorama.png` *(delete)*
   - `frontend/public/assets/landing/studio-scenes/closing-scene.png` *(delete)*
   - `docs/CODE_INDEX.md`
   - `docs/evaluation/geometry/runs/axo-hero-footer-redesign-vercel-hardening/`
3. **`refactor(ui): simplify sidebar brand with Axo wordmark`**
   - `frontend/src/components/LeftSidebar.tsx`
   - `frontend/src/styles/global.css`
   - `frontend/src/components/__tests__/sidebar-brand-wordmark.test.tsx`
   - `frontend/src/components/__tests__/header-sidebar-icon-alignment.test.tsx`
   - `frontend/src/components/sidebar-scrollbar-refinement.test.tsx`

---

## 20. Ma Trận Acceptance Gates (A–O)

| Gate | Nội dung | Trạng thái | Bằng chứng |
|---|---|---|---|
| **A** | Git ownership | `PASS` | Giữ nguyên changeset trên `feat/axo-hero-footer-redesign`; `main`, worktree khác sạch |
| **B** | Desktop Hero | `PASS` | Bố cục `0.92fr/1.08fr`, ink `352.9×344.2px` (`+14%`), `2560/1920/1440/1366/1280/1024` cân đối |
| **C** | Tablet Hero | `PASS` | Breakpoint tách portrait tablet (`1024×1366`, `820×1180`, `768×1024`) căn giữa đồng trục |
| **D** | Mobile Hero | `PASS` | `430/390/375/360/320` căn trái rõ ràng, `0` overflow, CTA `>= 44px`, `100%` SVG trên fold |
| **E** | Geometry integrity | `PASS` | Giữ nguyên 3 SVG trực giao; `viewBox="54 42 372 336"`, `0` cắt cạnh/nhãn |
| **F** | Autoplay (2 chu kỳ) | `PASS` | Đủ 2 vòng `Dodecahedron → Cylinder → Dihedral → ... → Dodecahedron` (`0px` shift, WebM `2.14 MB`) |
| **G** | Sidebar wordmark | `PASS` | Chỉ text `Axo` (`Inter 600, 24px, -0.04em`), thẳng hàng icon menu (`deltaX = 0`), `sb-top 48px` |
| **H** | Sidebar functionality | `PASS` | Bài toán mới, Thư viện (`11`), Search modal, Lọc, Thu gọn/Mở rộng, Mobile drawer, Student Auth `PASS` |
| **I** | Brand consistency | `PASS` | Landing Header/Footer, TopNav, Login, Admin `Axo Quản trị`, favicons nguyên vẹn |
| **J** | Accessibility | `PASS` | Keyboard, `:focus-visible`, touch, hover/offscreen/visibility pause, `reducedMotion` `PASS` |
| **K** | Vercel preservation | `PENDING_EXTERNAL_CONFIGURATION` | Local `dist/` (`17/17` routes, cache `8`-char hash) `PASS`; chờ Dashboard, Preview & Production |
| **L** | Performance | `PASS` | LCP `dist/` `380–472ms`, `CLS 0.0009`, `7` PNGs (`730,859 B`), `0` asset thừa |
| **M** | Regression | `PASS` | `npm run build`, `191/191` Vitest (`2,309` tests), `16/16` E2E, `40` pytests & freeze `PASS` |
| **N** | Git readiness | `PASS` | Changeset sạch `3` nhóm commit không trùng file, `0` secret/scratch |
| **O** | Owner review | `PENDING_OWNER_REVIEW` | Chờ nghiệm thu tại `http://localhost:3000/about` & `http://localhost:3000/app` |

---

## 21. Trạng Thái Git Cuối

- Repo chính `D:\Documents\projects\algo-sim`: không sửa đổi; giữ nguyên `docs/evaluation/geometry/runs/post-merge-cleanup-closure/`.
- Worktree `.superpowers/worktrees\axo-landing-page-design` (nhánh `feat/axo-hero-footer-redesign`): không tự commit/merge/push, không chứa scratch/DB tạm, sẵn sàng để Owner nghiệm thu.

---

## Phụ Lục — Thư Mục Bằng Chứng Ảnh & Video Trực Quan

- **Before / After Hero Desktop, Laptop, Tablet & Mobile:**
  - `1440×900`: [`before-c1`](screenshots/before/before-hero-desktop-1440.png) → [`before-showcase`](screenshots/before-showcase/after-hero-desktop-1440.png) → [`before-final`](screenshots/before-final-refinement/after-hero-desktop-1440.png) → [`after-hero-desktop-1440.png`](screenshots/after/after-hero-desktop-1440.png)
  - `2560×1440`: [`after-hero-desktop-2560.png`](screenshots/after/after-hero-desktop-2560.png) · `1920×1080`: [`after-hero-desktop-1920.png`](screenshots/after/after-hero-desktop-1920.png)
  - Laptop `1366×768` / `1280×720` / `1024×768`: [`after-hero-laptop-1366.png`](screenshots/after/after-hero-laptop-1366.png) · [`after-hero-laptop-1280.png`](screenshots/after/after-hero-laptop-1280.png) · [`after-hero-laptop-1024.png`](screenshots/after/after-hero-laptop-1024.png)
  - Tablet `1024×1366` / `820×1180` / `768×1024`: [`after-hero-tablet-1024p.png`](screenshots/after/after-hero-tablet-1024p.png) · [`after-hero-tablet-820.png`](screenshots/after/after-hero-tablet-820.png) · [`after-hero-tablet-768.png`](screenshots/after/after-hero-tablet-768.png)
  - Mobile `430` / `390` / `375` / `360` / `320`: [`after-hero-mobile-430.png`](screenshots/after/after-hero-mobile-430.png) · [`after-hero-mobile-390.png`](screenshots/after/after-hero-mobile-390.png) · [`after-hero-mobile-375.png`](screenshots/after/after-hero-mobile-375.png) · [`after-hero-mobile-360.png`](screenshots/after/after-hero-mobile-360.png) · [`after-hero-mobile-320.png`](screenshots/after/after-hero-mobile-320.png)
- **Ba Scene Hero & Video Hai Chu Kỳ Autoplay:**
  - `1440`: [`scene-1-dodecahedron`](screenshots/after/after-hero-scene-1-dodecahedron-1440.png) · [`scene-2-cylinder`](screenshots/after/after-hero-scene-2-cylinder-1440.png) · [`scene-3-dihedral`](screenshots/after/after-hero-scene-3-dihedral-1440.png) · [`hover-focus`](screenshots/after/after-hero-hover-focus-1440.png)
  - `1920` & `1366`: [`cylinder-1920`](screenshots/after/after-hero-scene-2-cylinder-1920.png) · [`dihedral-1920`](screenshots/after/after-hero-scene-3-dihedral-1920.png) · [`cylinder-1366`](screenshots/after/after-hero-scene-2-cylinder-1366.png) · [`dihedral-1366`](screenshots/after/after-hero-scene-3-dihedral-1366.png)
  - Video WebM 2 chu kỳ hoàn chỉnh (`7` trạng thái): [`hero-autoplay-2cycles.webm`](screenshots/after/hero-autoplay-2cycles.webm)
- **Sidebar Wordmark Before / After & Auth (`http://localhost:3000/app`):**
  - Expanded `1440`: [`before-sidebar-expanded-1440.png`](screenshots/before-final-refinement/before-sidebar-expanded-1440.png) → [`after-sidebar-expanded-1440.png`](screenshots/after/after-sidebar-expanded-1440.png)
  - Collapsed `1440`: [`before-sidebar-collapsed-1440.png`](screenshots/before-final-refinement/before-sidebar-collapsed-1440.png) → [`after-sidebar-collapsed-1440.png`](screenshots/after/after-sidebar-collapsed-1440.png)
  - Mobile drawer `390`: [`before-sidebar-mobile-390.png`](screenshots/before-final-refinement/before-sidebar-mobile-390.png) → [`after-sidebar-mobile-390.png`](screenshots/after/after-sidebar-mobile-390.png)
  - Controls hover/focus & Student Auth: [`after-sidebar-controls-focus-1440.png`](screenshots/after/after-sidebar-controls-focus-1440.png) · [`after-sidebar-auth-1440.png`](screenshots/after/after-sidebar-auth-1440.png)
- **Full-page Landing, Sections & Deep-link:**
  - [`after-full-page-1440.png`](screenshots/after/after-full-page-1440.png) · [`after-how-it-works-1440.png`](screenshots/after/after-how-it-works-1440.png) · [`after-closing-cta-1440.png`](screenshots/after/after-closing-cta-1440.png) · [`after-footer-desktop-1440.png`](screenshots/after/after-footer-desktop-1440.png) · [`after-footer-mobile-390.png`](screenshots/after/after-footer-mobile-390.png) · [`after-deep-link-pyramid-sphere-1440.png`](screenshots/after/after-deep-link-pyramid-sphere-1440.png)
