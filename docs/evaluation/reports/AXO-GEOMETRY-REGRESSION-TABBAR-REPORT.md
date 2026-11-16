# AXO — Geometry Renderer Regression & Workspace Tab Bar Refinement Report

> **Worktree:** `D:/Documents/projects/axo-geometry-library`  
> **Branch:** `feat/axo-geometry-library-verification`  
> **Baseline `HEAD`:** `1bfc2bc36` (`1bfc2bc361c2a887e5d826996e365154cb09c41d`)  
> **Live Dev Server Tested:** `http://localhost:3001/app` (offline backend `:8000` mode)  
> **Owner Approval:** `PENDING_OWNER_REVIEW`

---

## A. Git Baseline & Audited History

Các commit liên quan đến renderer, camera, bước dựng, quan hệ hình học và thanh công cụ trên nhánh hiện tại được kiểm tra đối chiếu:

| Commit | Ngày | Tiêu đề | Vai trò trong truy vết |
| --- | --- | --- | --- |
| `a6d9bebf6` | 2026-11-09 | `fix(scene3d): fix root-cause camera framing, sphere/line/plane bounds, and label readability` | Chuẩn hóa khung camera độc lập và biên hiển thị gốc |
| `3085b182e` | 2026-11-14 | `fix(axo): simplify geometry plane visualization policy` | Thiết kế có chủ đích hiển thị tối giản `(MNP)` ở bước trung gian |
| `c7a6077fd` | 2026-11-14 | `fix(axo): improve geometry scene rendering consistency` | Đồng bộ nhất quán dựng hình trên các họ hình học |
| `af81b3db5` | 2026-11-14 | `fix(axo): verify plane geometry and refine object interactions` | Chốt quy tắc `COPLANAR_INTERSECTION_GUIDE` & retire `(MNP)` ở bước 12/12 |
| `d49763413` | 2026-11-14 | `fix(axo): strengthen geometry step integrity and visualization` | Gây hồi quy tuyến cắt thẳng `compactPlaneAnchorPoints` vào `boundedPlanePolygon` |
| `dfc063840` | 2026-11-14 | `fix(axo): refine geometry interaction and step visualization` | Tinh chỉnh tương tác và hiển thị từng bước |
| `b5810dcc3` | 2026-11-14 | `fix(axo): integrate verified backend geometry contracts` | Tích hợp hợp đồng dữ kiện hình học xác minh |
| `8b0c270ad` | 2026-11-14 | `fix(axo): refine geometry relationships and camera locate` | Tinh chỉnh thẻ quan hệ và định vị đối tượng |
| `aecd3daa5` | 2026-11-14 | `fix(axo): improve geometric relationship presentation` | Nâng cấp trình bày quan hệ hình học |
| `c46353c78` | 2026-11-15 | `fix(axo): restore geometry toolbar functionality` | Khôi phục thanh công cụ (`Tùy chỉnh hình`, Eye X-Ray, Reset View) |

---

## B. Pha A — Geometry Renderer Regression & Step Consistency

### 1. Bảng phân định Hồi quy vs. Khiếm khuyết Thiết kế vs. Thiết kế Có chủ đích (§3.2)

| Hiện tượng quan sát | Phân loại | Nguồn gốc xác minh | Kết luận xử lý |
| --- | --- | --- | --- |
| `chop-thiet-dien-ba-diem`: Bước `9–11/12` vẽ `△MNP` chế độ `MINIMAL_GEOMETRY` kèm `COPLANAR_INTERSECTION_GUIDE` (`coplanar_guide:E:N`, `E:M`, `F:P`, `F:M`), rồi ẩn `(MNP)` khi đóng thiết diện `MENPF` (`thiet_dien#5cf`) tại bước `12/12` | **Intentional Design Decision** (không phải regression) | `3085b182e` + `af81b3db5`, được khóa bởi `v9413-geometry-rendering-integrity.test.tsx`, `plane-and-section-presentation-policy.test.tsx`, `step-continuity-and-scene-invariants.test.tsx` | **Giữ nguyên** 100%, không sửa policy thiết diện 3 điểm |
| `chop-mat-cau-ngoai-tiep` (Bước `11/17`): 3 mặt phẳng trung trực `(α)` `mp_tt_AB`, `(β)` `mp_tt_AD`, `(γ)` `mp_tt_SA` phình quá khổ tràn viền canvas (`maxD = 11.22`, tỷ lệ `1.62x` đường kính chóp `6.93`, `z ∈ [-1.95, 5.95]`) | **Compound Defect:** (1) Khiếm khuyết thiết kế + (2) Hồi quy từ `d49763413` | (1) `scene3d-semantic-policy.ts` kiểm `curved_solid` toàn cục không loại trừ mặt cầu ngoại tiếp downstream `cau_ngoai_tiep`, ép mặt phẳng trung trực lấy patch `2.30 × R`; (2) `d49763413` (`scene3d-view.tsx`) đưa thẳng `compactPlaneAnchorPoints` vào `boundedPlanePolygon`, bỏ qua xén đáy `z >= zMin` | **Đã sửa tận gốc** trong `scene3d-semantic-policy.ts` mà không chạm bất biến toán học hay camera |

### 2. Giải pháp kỹ thuật & Số đo trước/sau

Thay đổi tại `frontend/src/simulations/domains/geometry/scene3d-semantic-policy.ts` (Commit `72870daaf`):
- Bổ sung `getRelatedCurvedSolidsForPlane` và `isCurvedSolidRelatedPlane` với fast-path khi cảnh không có `curved_solid`, duyệt bao đóng phụ thuộc (`depends`, `computational_depends`, `visible_prerequisites`) để **loại trừ** các `curved_solid` downstream phụ thuộc vào chính mặt phẳng đang xét (như `cau_ngoai_tiep` sinh từ giao của `mp_tt_AB`, `mp_tt_AD`, `mp_tt_SA`), đồng thời khi cảnh có đa diện (`hasPolyhedronSolid`) chỉ liên kết `curved_solid` qua conic cut (`circle3` / `ellipse3` / `curved_section` / `section`) hoặc phụ thuộc trực tiếp của mặt phẳng (`conicLinkedIds.has(c.id) || directPlaneDeps.has(c.id)`).
- Áp dụng bộ lọc này cho `compactPlaneAnchorPoints`, `resolveStudiedPlaneVisualStyle`, `resolveAdaptivePlaneVisualization`, `computeBoundedStudiedPlanePolygon` và `computeCompactTrapezoidPlanePolygon` (loại `curved_solid` không liên quan khỏi `allFinite`, kết hợp hệ số thu gọn cụm đa mặt `coexistingCount >= 3 ? 0.78`).

**Kết quả đo đạc trên `chop-mat-cau-ngoai-tiep` tại Bước `11/17` (`pyrDiam = 6.93`):**

| Mặt phẳng trung trực | Trước sửa (Baseline `1bfc2bc36`) | Sau sửa (`72870daaf`) | Tỷ lệ / `pyrDiam` | Miền cao `z` (sau) | Mode & Lý do |
| --- | --- | --- | --- | --- | --- |
| `(α)` `mp_tt_AB` | `11.22` (`1.62x`, `z ∈ [-1.95, 5.95]`) | **`5.48`** | **`0.79x`** | `[0, 2.33]` | `COMPACT_PLANE_PATCH` (`coexisting_or_point_normal_patch`) |
| `(β)` `mp_tt_AD` | Bị phóng theo patch cầu `2.30R` | **`5.67`** | **`0.82x`** | `[0, 2.48]` | `COMPACT_PLANE_PATCH` (`coexisting_or_point_normal_patch`) |
| `(γ)` `mp_tt_SA` | Bị phóng theo patch cầu `2.30R` | **`4.24`** | **`0.61x`** | `[2, 2]` | `COMPACT_PLANE_PATCH` (`coexisting_or_point_normal_patch`) |

### 3. Bất biến toán học, camera, các bước dựng & 10 họ hình học

- **Toán học (`chop-mat-cau-ngoai-tiep` Bước `11/17`):** Giữ nguyên `point`, `normal`, vuông góc từng cặp (`M_AB ⊥ AB`, `M_AD ⊥ AD`, `M ⊥ SA`, sai số `< 1e-6`), điểm đồng quy tâm `I(2, 2, 2)` và `O(2, 2, 0)` thuộc mặt phẳng, đoạn giao tuyến `truc_day` đúng miền `[0, 2]`.
- **Camera framing độc lập:** Đường kính chóp (`duongKinhCanh`) và tâm xoay (`tinhTamXoayOnDinh`) khi có/không có 3 mặt phẳng phụ trùng khớp đến `6` chữ số thập phân; trong `chop-thiet-dien-ba-diem`, camera bất biến qua toàn bộ chuỗi scrub `9 → 10 → 11 → 12 → 11 → 10 → 9 → 12` tại `position = [11.8566827176046, 7.585095987623152, 12.042453782197228]`, `target = [1.75, 1.75, 2.25]`.
- **Kiểm tra live 10 họ & tương tác trên `chop-thiet-dien-ba-diem` (Bước `12/12`):**
  - `Tùy chỉnh hình` (`button[aria-label="Tùy chỉnh hình"]`): mở đủ `2` thanh trượt độ đục — **Độ đục vỏ khối** (`12% → 36%` xác nhận qua `window.__geo3d_shell_opacity_pct`) và **Độ đậm mặt phẳng cắt** (`8% → 24%` xác nhận qua `window.__geo3d_plane_opacity_pct`).
  - **Eye X-Ray (`#btn-xray`):** bật/tắt sạch (`true` / `false`).
  - **Camera orbit / zoom / reset (`#btn-reset-pos`):** kéo xoay delta `6.60`, lăn chuột zoom delta `1.17`, reset về đúng vị trí ban đầu (`resetError = 0`).
  - **Chọn thực thể trên canvas:** click vào `chop::edge:C-S` hiển thị `.context-object-card` (`Cạnh CS | Cạnh khối | Cạnh của khối đa diện nối hai đỉnh C và S. | Thuộc S.ABCD | Xem quan hệ | Định vị`).
  - **Các họ hình học đã chụp ảnh `after/` kiểm tra trực quan:** `lap-phuong-thiet-dien-bat-ky` (26 đối tượng), `lang-tru-tam-giac-thiet-dien` (20), `mat-cau-cat-mat-phang` (13), `mat-phang-tiep-xuc-mat-cau` (12), `hinh-non-cat-song-song-day` (20), `oxyz-giao-diem-duong-mat` (14), `goc-nhi-dien-hai-mat-phang` (15), `chop-mat-cau-ngoai-tiep` (`8..12, 17`), `chop-thiet-dien-ba-diem` (`9..12` + X-Ray).

---

## C. Pha B — Workspace Tab Bar Refinement

### 1. Thay đổi triển khai (`edc87fe45`)

- **`frontend/src/components/WorkspaceTabBar.tsx`:**
  - Chuyển bố cục sang dải cuộn ngang `.ws-tabbar-strip` (`role="tablist"`), nút `+` (`#btn-header-change-prob`) đặt ngay sau dải tab.
  - Bổ sung tự động cuộn tab đang chọn vào vùng nhìn thấy (`ensureTabVisibleInStrip`) theo tọa độ tương đối `getBoundingClientRect()` (khắc phục sai lệch `offsetLeft` do `.ws-tabbar-strip` không có `offsetParent`), kết hợp `ResizeObserver` + `window.resize` theo `requestAnimationFrame` để giữ tab đang chọn luôn hiển thị sau khi đổi kích thước khung nhìn qua các breakpoint.
  - Bổ sung hỗ trợ cuộn ngang bằng con lăn chuột (`onWheel`), điều hướng bàn phím đầy đủ (`ArrowLeft`, `ArrowRight`, `Home`, `End`, `Enter`, `Space`, `Escape`), portal tooltip `[role="tooltip"].ws-tab-floating-tooltip` căn giữa & kẹp trong viewport khi hover chuột hoặc focus bàn phím (tắt khi chạm nút đóng `×`), và loại bỏ hoàn toàn `useLayoutEffect` để đạt `0` cảnh báo SSR.
- **`frontend/src/styles/global.css`:**
  - `.ws-tabbar-strip` (`position: relative; overflow-x: auto; overflow-y: hidden; scrollbar-width: none; scroll-behavior: smooth` kèm `@media (prefers-reduced-motion: reduce)`).
  - `.ws-tab-item` (`flex: 0 0 auto; min-width: 148px; max-width: 244px; font-weight: 500` bất biến giữa nghỉ / hover / active -> dịch chuyển `0px`).
  - Light Mode active hierarchy tuân thủ `DESIGN.md` Level 0: nền tint `rgba(15, 23, 42, 0.067)`, viền hairline `rgba(15, 23, 42, 0.16)`, vạch nhấn đáy `1.5px` tinh tế, không tự chế `box-shadow`.
  - `.ws-tab-item:focus-visible { outline-offset: -2px; }` tránh bị cắt mép trên/dưới trong strip `28px`.
  - `.ws-tab-floating-tooltip` dùng `box-shadow: var(--shadow-elevated)` và `color: var(--on-primary, #ffffff)` trên nền `--ink` đạt chuẩn WCAG AA (`src/styles/tokens.test.ts`).
  - Responsive mobile `@media (max-width: 480px)`: `min-width: 112px; max-width: min(192px, 42vw)`, giữ icon, tiêu đề có nghĩa và nút `×` hoàn toàn không va chạm ngay cả ở `320px`.

### 2. So sánh trước/sau & Ma trận 8 Viewport (Live Playwright `1440×900` → `320×568`)

- **Trước sửa (`tabbar_before_metrics.json`, `1440×900`, 10 bài + Thư viện):** tab bị nén xuống `46.4px–111.8px`, tiêu đề cắt còn `"Thi..."`, `"Kh..."`, `"Mặt..."`; trên mobile `390×844` chiều rộng chữ bằng `0px` và nút `×` đè thẳng lên icon.
- **Sau sửa — Mở tăng dần (`1440×900`):**
  - `1` tab bài toán (+ Thư viện = 2 tabs): `stripClientW = 421`, `stripScrollW = 421`, width = `244px`.
  - `2` tabs (+ Thư viện = 3 tabs): `stripClientW = 669`, `stripScrollW = 669`, width = `244px`, phân biệt rõ icon `cube` vs `pyramid`.
  - `5` tabs (+ Thư viện = 6 tabs): `stripClientW = 1046`, `stripScrollW = 1413`, width = `244px`.
  - `10` tabs (+ Thư viện = 11 tabs): `stripClientW = 1046`, `stripScrollW = 2653`, width = `244px`.

**Ma trận 8 kích thước màn hình khi mở 10 bài toán (`11` tabs):**

| Viewport | `docOverflowX` | `stripClientW` | `stripScrollW` | `activeVisibleInStrip` | Tab Sample Min–Max W | Icon/Close Overlap |
| --- | --- | --- | --- | --- | --- | --- |
| `1920×1080` | `0` | `1526` | `2653` | `true` | `244px – 244px` | `false` |
| `1440×900` | `0` | `1046` | `2653` | `true` | `244px – 244px` | `false` |
| `1366×768` | `0` | `972` | `2653` | `true` | `244px – 244px` | `false` |
| `1024×768` | `0` | `867` | `2653` | `true` | `244px – 244px` | `false` |
| `768×1024` | `0` | `611` | `2651` | `true` | `244px – 244px` | `false` |
| `390×844` | `0` | `239` | `1839` | `true` | `163.8px – 163.8px` | `false` |
| `360×800` | `0` | `209` | `1713` | `true` | `151.2px – 151.2px` | `false` |
| `320×568` | `0` | `169` | `1545` | `true` | `134.4px – 134.4px` | `false` |

### 3. Tương tác, Tooltip, Đóng tab & Điều hướng

- **Hover shift:** `widthDelta = 0`, `heightDelta = 0`.
- **Tooltip portal:** Hover (`left: 494, top: 39, right: 808.9, bottom: 67.2, clipped: false`) và Keyboard Focus (`left: 648, top: 39, right: 984.5, bottom: 67.2, clipped: false`).
- **Keyboard & Wheel:** `Home → tab-library`, `ArrowRight → tab-sample-chop-thiet-dien-ba-diem → tab-sample-lap-phuong-thiet-dien-bat-ky`, `Escape → 0 tooltip`, `End + Space → tab-sample-hinh-non-cat-song-song-day`, cuộn con lăn `scrollLeft: 1607 → 1449`.
- **Chuyển đổi Library ↔ Workspace:** Giữ nguyên `11` tabs và độ rộng Sidebar `271px`.
- **Đóng tab không hộp thoại xác nhận:** `dialogsTriggered = 0`; đóng tab đang chọn chuyển đúng sang tab lân cận (`10 → 9`), đóng hết toàn bộ tab mẫu trả về `tab-library` với `11` thẻ Thư viện (`remainingNonLibTabs = 0`).

### 4. Đường dẫn bằng chứng trực quan (`before/` và `after/`)

Thư mục artifact phiên làm việc: `C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/geo_tabbar_regression/`
- **Pha A (`before/` & `after/`):** `chop_mat_cau_step_08_of_17.png` .. `_12_of_17.png`, `_17_of_17.png`; `chop_thiet_dien_step_09_of_12.png` .. `_12_of_12.png`, `chop_thiet_dien_step_12_xray.png`; 7 ảnh họ hình học `family_*.png`; dữ liệu đo `pha_a_diagnostics.json`.
- **Pha B (`before/` & `after/`):** `tabbar_desktop_1tab.png`, `tabbar_desktop_2tabs.png`, `tabbar_desktop_5tabs.png`, `tabbar_desktop_10tabs.png`, `workspace_desktop_10tabs.png`, `tabbar_hover_tooltip.png`, `tabbar_focus_tooltip.png`, `tabbar_mobile_390_10tabs.png`, `tabbar_mobile_320_10tabs.png`; dữ liệu trước `before/tabbar_before_metrics.json` và sau `after/after_full_verification.json`.

---

## D. Cổng Chất lượng & Giới hạn Kiểm chứng Trung thực

Tất cả các lệnh bên dưới được chạy **sau lần chỉnh sửa mã/CSS cuối cùng**:

| Cổng kiểm tra | Lệnh thực thi | Kết quả đo được |
| --- | --- | --- |
| TypeScript Build Check | `npx tsc -b` | Exit `0` |
| Production Bundle | `npm run build` | `✓ 129 modules transformed`, `✓ built in 5.53s`, Exit `0` |
| Focused Vitest Suites (Pha A + B) | `npx vitest run --maxWorkers=1` (13 files trọng tâm) | **13/13 files, 109/109 tests passed** (`34.70s`) |
| Full Frontend Vitest Suite | `npx vitest run --maxWorkers=2` | **188/188 files passed, 2243/2243 tests passed** (`115.04s`, 0 failed, 0 skipped) |
| Live Chromium E2E (`localhost:3001/app`) | `node .../verify_after_live.mjs` | Exit `0`, `0` `pageErrors`, `0` `otherConsoleErrors`, `0` `dialogs` |

**Giới hạn trung thực:**
1. Khi chạy E2E trên `http://localhost:3001/app`, backend API `:8000` không bật nên có `8` log console 500 từ proxy Vite tới `/api/*` (`apiProxy500Count: 8`); ngoài ra `otherConsoleErrors = 0` và `pageErrors = 0`.
2. Kiểm tra kiến trúc tài liệu `python backend/scripts/audit_docs_information_architecture.py` sau khi tạo báo cáo ghi nhận `Docs root closed list: True (29 root docs, 167 catalogued, unclassified [])`, `Internal links broken: 0`, `Ownership domains valid: True`, `EVIDENCE_INDEX valid: True`, `Secret leaks: 0`, và ghi nhận `4` đường dẫn cũ trong `CODE_INDEX stale paths` xuất phát từ các tệp classroom do phiên song song xóa (không thuộc phạm vi tác vụ này nên giữ nguyên).

---

## E. Quyền sở hữu Git & Trạng thái Commit

### 1. Các tệp thuộc phạm vi nhiệm vụ này (Đã commit sạch bằng allowlist)

| Commit SHA | Nhóm | Tệp | Trạng thái |
| --- | --- | --- | --- |
| `72870daaf` | Pha A (Renderer) | `frontend/src/simulations/domains/geometry/scene3d-semantic-policy.ts` | Committed |
| `72870daaf` | Pha A (Tests) | `frontend/src/simulations/domains/geometry/plane-extent-and-step-regression.test.tsx` | Committed (New) |
| `edc87fe45` | Pha B (Tab Bar) | `frontend/src/components/WorkspaceTabBar.tsx` | Committed |
| `edc87fe45` | Pha B (Styles) | `frontend/src/styles/global.css` | Committed |
| `edc87fe45` | Pha B (Tests) | `frontend/src/components/__tests__/workspace-tabbar-refinement.test.tsx` | Committed (New) |
| `SELF` | Documentation | `docs/evaluation/reports/AXO-GEOMETRY-REGRESSION-TABBAR-REPORT.md` | Commit báo cáo hiện tại |

### 2. Thay đổi chưa commit của phiên làm việc song song (Được giữ nguyên 100% — Không đụng/stage/reset)

Các thay đổi đang có sẵn trong working tree từ phiên song song tiếp tục được bảo toàn nguyên trạng:
- `backend/*` (chủ yếu chỉnh sửa/xóa `accounts/classroom_router.py`, `session_router.py`, `classroom_models.py`, migration `f8a2c41d9e05_remove_classroom_and_live_session_tables.py` và test backend tương ứng).
- `docs/EVIDENCE_INDEX.md` và các run `docs/evaluation/geometry/runs/axo-attachment-*`, `axo-ui-consistency/`.
- `frontend/index.html`, `frontend/package.json`, `frontend/package-lock.json`, `frontend/public/*`, `frontend/scripts/attachment-resize.node-test.mjs`, các file `frontend/src/components/*` / `state/*` / `styles/*.test.ts` thuộc luồng attachment / home / classroom cleanup và landing prototype.

---

**Owner Approval: PENDING_OWNER_REVIEW**
