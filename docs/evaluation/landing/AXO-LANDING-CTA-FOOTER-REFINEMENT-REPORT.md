# AXO Landing — CTA 3D, Footer & Version Lifecycle Consolidation Report (Phase 1)

**Ngày hoàn thành:** 2026-11-15  
**Worktree thực tế:** `D:\Documents\projects\axo-geometry-library`  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Baseline SHA:** `ed308d1a8` (`docs(axo): add v1.4 visual direction report`)  
**Commit SHA Phase 1 (Code / Tests / `CODE_INDEX.md`):** `471baf39b9c5c321d7c78ac7c72ba6b6a643af7f` (`471baf39b`)  
**Commit SHA Báo cáo (Tài liệu này):** Đóng gói ở commit tài liệu ngay sau `471baf39b` (xem `git log -2` sau hoàn tất)  
**Tuyến xem thử cô lập:** `http://localhost:3001/gioi-thieu?preview=v1.4`  
**Tuyến Production mặc định:** `/` và `/gioi-thieu` (**V1.2.2** `"prod"` — giữ nguyên không thay đổi)  
**Tình trạng triển khai thực tế:** `NOT_DEPLOYED`  
**Owner Approval:** `PENDING_OWNER_REVIEW`

> [!IMPORTANT]
> - Báo cáo này tổng hợp **Pha 1** (triển khai nâng cấp CTA 3D, Footer, hồi phục nút capsule trên tuyến xem thử cô lập `?preview=v1.4`, kiểm toán toàn bộ inventory phiên bản Frontend và đề xuất hợp nhất).  
> - Mọi thành phần `Approved UI` (`Header`, `Logo chính thức`, `Auth`, `Hero`, `Storytelling V1.4`, `Interactive Demo`, `Workspace`) và tuyến production V1.2.2 (`/`, `/gioi-thieu`) được giữ nguyên hoàn toàn theo §11.  
> - **Không xóa** bản `prod` hay prototype `?prototype=a|b` trong lần chạy này; các thay đổi chưa commit của session khác (`OWNERSHIP_BLOCKED`) được giữ nguyên tuyệt đối.

---

## 1. Phạm vi Worktree, Branch, Baseline & Danh sách Tệp đã Sửa/Thêm (§16.1–§16.3, §16.18)

| Mục | Giá trị xác minh |
|---|---|
| **Worktree** | `D:\Documents\projects\axo-geometry-library` |
| **Branch** | `feat/axo-geometry-library-verification` |
| **Baseline Commit** | `ed308d1a8` (`docs(axo): add v1.4 visual direction report`) |
| **Code Commit SHA** | `471baf39b9c5c321d7c78ac7c72ba6b6a643af7f` (`feat(axo): upgrade v1.4 closing 3d scene and editorial footer`) |
| **Staging Guard** | Stage tường minh bằng `git add <file>`, tuyệt đối không `git add .` / `-A` |

### Danh sách 10 tệp thuộc phạm vi nhiệm vụ

| # | Tệp | Hành động | Vai trò |
|---|---|---|---|
| 1 | [`frontend/src/components/landing/LandingClosingScene3D.tsx`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingScene3D.tsx) | Tạo mới | Cảnh 3D Three.js chính thức cho Final CTA (`S.ABCD` + `(MNP)` + `MENPF`), 4 pha dựng liên tục, SVG fallback toán học & dọn GPU |
| 2 | [`frontend/src/components/landing/LandingClosingV14.tsx`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingV14.tsx) | Sửa | Thay `ClosingConstructionMotif` bằng `<LandingClosingScene3D />`; thiết kế lại `LandingFooterV14` với `<IconAxoLogo />`, đường chân trời hình học SVG, `scrollToLandingSection` và `#btn-landing-footer-top` |
| 3 | [`frontend/src/components/landing/landing.css`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing.css) | Sửa | Khôi phục nút capsule `border-radius: var(--rounded-full)` trên `.axo-v14-btn`, nền `var(--canvas)` cho `.axo-v14-btn-secondary`, bổ sung layout/responsive `.axo-v14-closing*` (gồm `scroll-margin-top: 72px` & đệm mobile clearances) và `.axo-v14-footer*` dùng tách tone nền; gỡ CSS thừa đã xác minh hết người gọi (`.axo-v14-closing-motif`, `.axo-v14-footer-mark`, `.axo-v14-svg-wireframe-hint`) |
| 4 | [`frontend/src/components/__tests__/landing-cta-geometry.test.tsx`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-cta-geometry.test.tsx) | Tạo mới | Kiểm chứng mặt phẳng `x + y + 2z = 6`, trung điểm `M, N, P`, cắt đa diện nửa không gian, diện tích 2D fallback không suy biến |
| 5 | [`frontend/src/components/__tests__/landing-cta-motion.test.tsx`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-cta-motion.test.tsx) | Tạo mới | Kiểm chứng chuỗi 4 pha dựng, điều kiện biên khép kín `C^0` tại `CLOSING_CYCLE_DURATION_MS`, `prefers-reduced-motion` và `?closing_phase=mid\|settled` |
| 6 | [`frontend/src/components/__tests__/landing-footer-layout.test.tsx`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-footer-layout.test.tsx) | Tạo mới | Kiểm chứng `<IconAxoLogo />` nét đen, đúng 4 liên kết, zero `<canvas>` trong Footer, zero thông tin liên hệ/CTA trùng, nút về đầu trang `#btn-landing-footer-top` |
| 7 | [`frontend/src/components/__tests__/landing-approved-ui-regression.test.tsx`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-approved-ui-regression.test.tsx) | Tạo mới | Guard bảo vệ capsule `.axo-v14-btn`, hover, zero `#hex` literal, giữ nguyên Hero/Demo/Production, phát hiện hậu tố số lặp và trạng thái phê duyệt báo cáo |
| 8 | [`frontend/src/components/__tests__/landing-webgl-lifecycle.test.tsx`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-webgl-lifecycle.test.tsx) | Sửa | Bổ sung test `IntersectionObserver`, `ResizeObserver`, `visibilitychange`, `webglcontextlost`/`restored`, `renderer.dispose()`, `item.dispose()`, `?no_webgl=1` trên `LandingClosingScene3D` |
| 9 | [`docs/CODE_INDEX.md`](file:///D:/Documents/projects/axo-geometry-library/docs/CODE_INDEX.md) | Sửa | Đăng ký `LandingClosingScene3D.tsx`, cập nhật mô tả `LandingClosingV14.tsx` và 4 tệp test CTA/Footer mới dưới mục `components/LandingView.tsx` |
| 10 | [`docs/evaluation/landing/AXO-LANDING-CTA-FOOTER-REFINEMENT-REPORT.md`](file:///D:/Documents/projects/axo-geometry-library/docs/evaluation/landing/AXO-LANDING-CTA-FOOTER-REFINEMENT-REPORT.md) | Tạo mới | Báo cáo nghiệm thu 23 mục Pha 1, Version Inventory toàn frontend và kế hoạch hợp nhất Pha 2 |

---

## 2. Kết quả Nghiên cứu Thực nghiệm REA MCP (§16.4)

Sổ cái bằng chứng tại [`rea-cta-footer-evidence-ledger.json`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/rea/rea-cta-footer-evidence-ledger.json):

| Site | URL | Trạng thái | REA Evidence ID | Hash / Chi tiết quan sát | Ảnh inspect |
|---|---|---|---|---|---|
| **bundaumayo Footer** | `https://bundaumayo.top/#lien-he` | `VERIFIED_BY_REA` | `ev_8aece4a25d2150720d1bbc803cdf43e63871c30b4740b1b2bcf86c1df1dc400b` | `scenario_sha256: 15a30f8b...`, `dom_sha256: 5e9b956e...` (`66,850 B`), `screenshot_sha256: be9123fc...` (`370,673 B`) | [`rea_bundaumayo_footer.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/rea/rea_bundaumayo_footer.png) |
| **bundaumayo Hero / CSS** | `https://bundaumayo.top/`, `clay.css?v=11-1792852154` | `VERIFIED_BY_REA` | `ev_8f0f77d4...` / `ev_8c525df4...` | Nhịp phân tách vùng kết và Footer thoáng rộng, tách bằng bề mặt/nét nhẹ, không nhồi thẻ | [`rea_01_bundaumayo.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea_01_bundaumayo.png) |
| **lusion / rive / figma / notion** | `lusion.co`, `rive.app`, `figma.com`, `notion.com` | `VERIFIED_BY_REA` | `ev_e9fd...` / `ev_e5dc...` / `ev_86e3...` / `ev_4a87...` | Tỷ trọng whitespace editorial, chuyển động có điểm dừng khi rời vùng nhìn, tương tác nhẹ | [`rea_05_lusion.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea_05_lusion.png) |
| **codrops** | `https://tympanus.net/codrops/` | **`NOT VERIFIED`** | `null` | Gặp phản hồi `HTTP 403 / Cloudflare anti-bot challenge ('Just a moment...')`; tuân thủ luật an toàn không vượt anti-bot | `null` |

**Bài học kiến trúc áp dụng (không sao chép linh vật, màu hoặc nội dung thương hiệu ngoài Axo):**
- Tổ chức khối kết trang gọn gàng theo 2 lớp rõ rệt: phần CTA 3D làm điểm nhấn chuyển đổi cuối, tách sang nền trắng của Footer bằng biến đổi bề mặt (`#f6f5f4` → `#ffffff`) thay cho viền đóng khung nặng nề.
- Hàng đầu Footer phân bổ cặp Brand (trái) — Essential Links (phải), nối sang thanh dưới cùng gồm bản quyền gọn + nút trở về đầu trang qua một dải nhịp điệu vector mảnh mang bản sắc hình học Axo.

---

## 3. Áp dụng Skill Thiết kế (`design-taste-frontend`) (§16.5)

1. **`lint.mjs` (`LandingClosingScene3D.tsx`, `LandingClosingV14.tsx`):** Thoát mã `0`, **`RESULT: 0 FAIL, 0 WARN`**.
2. **`inspect.mjs` trên `http://localhost:3001/gioi-thieu?preview=v1.4`:**
   - **Điểm đã xử lý dứt điểm trong phạm vi CTA & Footer:** Xóa `border-top: 1px solid var(--hairline)` trên `#landing-footer.axo-v14-footer` (tách bằng tone bề mặt `#f6f5f4` → `#ffffff`), giúp Footer biến mất hoàn toàn khỏi danh sách `[hairline]` của `inspect.mjs`.
   - **Các `7 FAIL, 9 WARN` còn lại trên trang toàn cục (ngoài phạm vi hoặc có lý do bảo vệ minh bạch):**
     - `[headline-lines]`, `[mono]`, `[shadow]`, `[button-fx]`, `[hairline]` (`div.axo-v14-story-readout`, `details.axo-v14-story-proof`): phát sinh tại **Hero (`Approved UI`)**, **Storytelling V1.4 (`Approved UI`)** và tab **Interactive Demo (`Approved UI`)** — bị cấm sửa theo §11 *Approved UI Preservation*.
     - `[few-pictures]` / `[no-footage]` / `[body-size]` (`14.1px`): Axo sử dụng mô hình WebGL 3D toán học và vector SVG hình học chuyên ngành thay cho ảnh stock trang trí; kích thước chữ thừa kế token hiện hành.

---

## 4. Quyết định Creative Direction (§16.6)

- **Bản sắc CTA 3D (`#landing-final-cta`):** Loại bỏ hình SVG phẳng `ClosingConstructionMotif` dễ tạo cảm giác “công thức tĩnh”, thay bằng sân khấu Three.js WebGL không khung card, cân đối hai cột (`max-width: 1200px`, desktop grid `1fr : 1.08fr`, mobile `<= 920px` đưa hình 3D lên trên sao cho vẫn có đủ khoảng hở đầu đỉnh `S` dưới thanh Header dính).
- **Chiều sâu khối không gian & kỷ luật hình học:** Khối chóp `S.ABCD` tách rõ phần đáy cụt dưới mặt cắt (`lowerMesh` opacity `0.90`) và chóp trên mờ (`upperMesh` opacity `0.20`, `renderOrder: 3`) với `MeshStandardMaterial` + `flatShading: true` dưới cặp sáng chính `(11, 15, -5)` + fill mát `(-10, 4, 10)`, giữ cạnh khuất nét đứt (`DA, AB, SA`), mặt phẳng cắt `(MNP)` xanh dương mờ (`0x62aef0`, `renderOrder: 4`), thiết diện ngũ giác `MENPF` cam đất rõ khối (`0xe6620a`, `renderOrder: 5`), điểm ẩn `A` hạ sắc mờ (`0.34`) để không lẫn thành đốm tối nổi giữa mặt cắt. Tuyệt đối **không** thêm card thông số, bảng diện tích hay nút điều khiển camera vào CTA.
- **Khôi phục Capsule CTA (`9999px`):** Đặt lại `border-radius: var(--rounded-full)` cho `.axo-v14-btn` (Hero và Closing CTA) và `background-color: var(--canvas)` (`rgb(255, 255, 255)`) cho `.axo-v14-btn-secondary`, bảo toàn hiệu ứng hover `translateY(-1px)` và `focus-visible`.
- **Footer Nhận diện Axo (`#landing-footer`):** Khôi phục `<IconAxoLogo />` nét đen đồng bộ Header (loại bỏ nền xanh dương `.axo-v14-footer-mark`), giữ đúng 4 liên kết cốt lõi (`Giới thiệu`, `Cách hoạt động`, `Trải nghiệm`, `Thư viện bài mẫu`), bổ sung dải `.axo-v14-footer-trace-svg` (`preserveAspectRatio="xMidYMid meet"`) tạo đường chân trời điểm-nối nhẹ (không lặp mô hình 3D lớn thứ hai) và nút capsule `#btn-landing-footer-top` (`44px` hit target).

---

## 5. Dữ liệu Hình học, Bất biến Toán học & Thiết kế Animation (§16.7–§16.9)

### Nguồn dữ liệu hình học (§16.7)
- `LandingClosingScene3D.tsx` tiêu thụ trực tiếp `LANDING_PYRAMID_SAMPLE` từ [`landing-geometry-data.ts`](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing-geometry-data.ts) (`points`, `solidEdges`, `planeQuad`, `sectionLoop`, `defaultCamera`, `defaultLookAt`), quy đổi tọa độ toán học qua `worldToMathCoords`.

### Bất biến hình học đã kiểm chứng (§16.8)
Kiểm chứng tự động trong `landing-cta-geometry.test.tsx` và `landing-webgl-lifecycle.test.tsx`:
1. Thứ tự 5 đỉnh thiết diện khớp chính xác `["M", "E", "N", "P", "F"]`.
2. Cả 5 đỉnh `M, E, N, P, F` thỏa mãn phương trình mặt phẳng cắt `(MNP): x + y + 2z = 6` với sai số dư `< 1e-6`.
3. `M`, `N`, `P` khớp chính xác công thức trung điểm của `SA`, `BC`, `CD`.
4. Thuật toán `clipPolygonHalfSpace` tách khối chóp qua `(MNP)` thành hai nhóm đa giác không suy biến (`lowerFrustumFaces.length >= 4`, `upperCapFaces.length >= 3`).
5. Phép chiếu dự phòng 2D `projectClosingFallbackSvg(480, 380)` cho diện tích Shoelace ngũ giác `> 800` và toàn bộ đỉnh (`>= 11` điểm) nằm gọn trong lề an toàn `(20, width - 20)` và `(20, height - 20)`.

### Thiết kế Animation (§16.9)
Hàm thuần túy `evaluateClosingMotionState(elapsedMs, reducedMotion, previewOverride)` với chu kỳ `CLOSING_CYCLE_DURATION_MS = 9600` ms:
1. **Pha A — `"base-pyramid"` (`u < 0.20`):** Định hình chóp đáy `S.ABCD`, nét khuất `SA/AB/AD` và 3 điểm gốc `M, N, P`.
2. **Pha B — `"plane-emergence"` (`0.20 <= u < 0.42`):** Mặt phẳng `(MNP)` tịnh tiến dọc pháp tuyến về đúng mặt cắt.
3. **Pha C — `"section-intersection"` (`0.42 <= u < 0.74`):** Dò vẽ tuần tự 5 cạnh thiết diện `MENPF` (`traceProgress`), bật giao điểm `E, F` trên `SB, SD` và phủ dần mặt cam `sectionFillOpacity`.
4. **Pha D — `"complete-settled"` (`0.74 <= u < 0.92`, kèm `dissolveOut` ở `0.88..0.98`):** Hoàn thiện toàn cảnh và khép chu kỳ liên tục `C^0` tại biên `u = 0 / 1`.
- **Reduced Motion & QA:** Dưới `prefers-reduced-motion: reduce`, trả trực tiếp trạng thái tĩnh `"complete-settled"` (`0` idle RAF). Hỗ trợ query test `?closing_phase=mid|settled`.

---

## 6. Kết quả Performance Before vs After & WebGL Lifecycle (§16.10–§16.11)

Nguồn đo trực tiếp cùng kịch bản trên `http://localhost:3001/gioi-thieu?preview=v1.4`:  
- **Before:** [`before-cta-footer-benchmark.json`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/perf/before-cta-footer-benchmark.json) (`2026-11-15T15:59:07.910Z`)  
- **After:** [`after-cta-footer-benchmark.json`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/perf/after-cta-footer-benchmark.json) (`2026-11-15T16:33:54.775Z`)

> [!NOTE]
> Mọi hồ sơ `mobile_390x844_4x_cpu` chạy trong Playwright desktop kèm `Emulation.setCPUThrottlingRate({ rate: 4 })` (`deviceNote: "NOT_PHYSICAL_MOBILE"`), không phải phần cứng di động vật lý.

### 6.1. Bảng So sánh DOM & Thẩm mỹ Đo lường (1440×900)

| Chỉ số DOM | Before (`svg-only`) | After (`webgl-canvas`) | Ghi chú |
|---|---:|---:|---|
| `ctaVisualType` | `svg-only` | **`webgl-canvas`** (`data-closing-visual="webgl"`) | Chuyển sang Three.js WebGL thực |
| `ctaBtnBorderRadius` (CTA cuối) | `8px` | **`9999px`** | Khôi phục chuẩn pill/capsule |
| `heroBtnBorderRadius` (Hero) | `8px` | **`9999px`** | Đồng bộ hệ nút toàn trang |
| `ctaSecBtnBg` (nút phụ) | — | **`rgb(255, 255, 255)`** (`var(--canvas)`) | Nền sáng rõ trên vùng `#f6f5f4` |
| `footerLogoMarkBg` / `Color` | `rgb(220, 235, 250)` / `rgb(0, 117, 222)` | **`rgba(0, 0, 0, 0)` / `rgb(0, 0, 0)`** (`hasOldBlueMark: false`) | Khôi phục `<IconAxoLogo />` nét đen chính thức |
| `footerHeight` | `103.625 px` | **`282.94 px`** | Đủ Brand + Links + Horizon trace + Copy + Back-to-top |

### 6.2. Bảng So sánh Hiệu năng Before / After Trên 2 Backend

| Backend & Profile | Giai đoạn | Active FPS | Avg / P95 Frame (ms) | Resize FPS (P95) | Long Tasks (cnt / max ms) | LCP (ms) | CLS | WebGL (Top / CTA / Max / Life / Lost) | Offscreen Idle RAF | Demo State Saved | Errors |
|---|---|---:|---|---:|---|---:|---:|---|---:|---|---|
| **SwiftShader** `desktop_1920x1080` | Before | `60` | `16.67 / 16.7` | `60` (`16.8`) | `4 / 143` | `888` | `0` | `1 / 2 / 2 / 3 / 0` | `0` | — | `0` |
| **SwiftShader** `desktop_1920x1080` | **After** | `36.8` | `27.16 / 66.7` | `50.3` (`16.8`) | `5 / 240` | `632` | **`0`** | `1 / 3 / 3 / 4 / 0` | **`0`** | **`true`** | **`0`** |
| **SwiftShader** `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | Before | `60` | `16.67 / 16.7` | `54.7` (`33.3`) | `6 / 424` | `1520` | `0` | `1 / 2 / 2 / 3 / 0` | `0` | — | `0` |
| **SwiftShader** `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | **After** | `38.9` | `25.72 / 50` | `45.4` (`66.6`) | `14 / 442` | `2096` | **`0`** | `1 / 3 / 3 / 4 / 0` | **`0`** | **`true`** | **`0`** |
| **Hardware GPU (D3D11)** `desktop_1920x1080` | Before | `60` | `16.67 / 16.8` | `56.1` (`16.8`) | `5 / 193` | `588` | `0` | `1 / 2 / 2 / 3 / 0` | `0` | — | `0` |
| **Hardware GPU (D3D11)** `desktop_1920x1080` | **After** | **`60`** | **`16.67 / 16.8`** | `33.8` (`250`) | `6 / 271` | `812` | **`0`** | `1 / 3 / 3 / 4 / 0` | **`0`** | **`true`** | **`0`** |
| **Hardware GPU (D3D11)** `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | Before | `60` | `16.67 / 16.8` | `56.4` (`16.7`) | `6 / 276` | `1384` | `0` | `1 / 2 / 2 / 3 / 0` | `0` | — | `0` |
| **Hardware GPU (D3D11)** `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | **After** | **`60`** | **`16.67 / 16.8`** | `51.4` (`33.3`) | `7 / 279` | `1364` | **`0`** | `1 / 3 / 3 / 4 / 0` | **`0`** | **`true`** | **`0`** |

### 6.3. Phân tích WebGL Lifecycle (§16.11)
- **Tài nguyên WebGL có giới hạn (+1 context tại CTA):** Do Hero (`LandingHeroV14`, 1 context) và Demo (`LandingInteractiveDemo`, 1 context) thuộc `Approved UI` §11 giữ renderer bền vững, `LandingClosingScene3D` khởi tạo lười thêm đúng `1` renderer khi vào viewport (`webglActiveAtTop = 1`, `webglActiveAtCta = 3`, `webglMaxConcurrent = 3`, `webglLifetimeCreated = 4`), không rò rỉ vô hạn khi cuộn qua lại (`offViewportIdleRafDelta = 0`, `webglContextLost = 0`).
- **Bảo toàn trạng thái Demo:** Khi chọn mẫu `lap-phuong-thiet-dien-bat-ky` trong `#trai-nghiem` rồi cuộn xuống CTA/Footer và cuộn ngược lên, tab mẫu đang chọn vẫn giữ nguyên (`demoActiveAfterScroll = true`).
- **Xử lý sự cố & Dọn bộ nhớ:** Quản lý qua `IntersectionObserver`, `ResizeObserver`, `visibilitychange`, `webglcontextlost`/`webglcontextrestored`, giải phóng bằng `renderer.dispose()` + `item.dispose()` mọi geometry/material; fallback SVG đầy đủ hình `(MNP)` + `MENPF` khi `?no_webgl=1` (`FALLBACK_ATTR = "svg-fallback"`).

---

## 7. Kết quả Responsive (8 Viewport), Điều khiển Chuột/Phím/Cảm ứng & Kho Ảnh/Video (§16.12–§16.13)

### 7.1. Ma trận 8 Viewport Playwright (`after-cta-footer-benchmark.json`)

| Viewport (`W × H`) | Thiết bị / Input | `overflowX` | `stage (W×H)` | `stageInVP` | `btnOverlap` | `footerInVP` | `topBtnHeight` | Title TV | `focus` + `About Top` (`scrollAfterTop`) | `errors` |
|---|---|---|---|---|---:|---|---:|---|---|---|
| `desktop_1920x1080` | Mouse + Keyboard | `false` | `598×430` | `true` | `false` | `true` | `44` | `true` | `true` (`8px`) | `0` |
| `desktop_1440x900` | Mouse + Keyboard | `false` | `598×430` | `true` | `false` | `true` | `44` | `true` | `true` (`16px`) | `0` |
| `laptop_1366x768` | Mouse + Keyboard | `false` | `598×430` | `true` | `false` | `true` | `44` | `true` | `true` (`23px`) | `0` |
| `tablet_landscape_1024x768` | Mouse + Keyboard | `false` | `468×348` | `true` | `false` | `true` | `44` | `true` | `true` (`15px`) | `0` |
| `tablet_portrait_768x1024` | Touch (`tap()`) | `false` | `736×310` | `true` | `false` | `true` | `44` | `true` | `true` (`58px`) | `0` |
| `mobile_390x844` | Touch (`tap()`) | `false` | `358×270` | `true` | `false` | `true` | `44` | `true` | `true` (`69px`) | `0` |
| `mobile_360x800` | Touch (`tap()`) | `false` | `328×270` | `true` | `false` | `true` | `44` | `true` | `true` (`89px`) | `0` |
| `mobile_320x568` | Touch (`tap()`) | `false` | `288×270` | `true` | `false` | `true` | `44` | `true` | `true` (`111px`) | `0` |

### 7.2. Kho Ảnh Before / After (Đã inspect trực tiếp bằng `read_file`) & Video WebM (§16.13)

- **Before (`5` ảnh):**
  - [`before/cta_desktop_1440.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/before/cta_desktop_1440.png) · [`before/cta_button_hover.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/before/cta_button_hover.png) · [`before/footer_desktop_1440.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/before/footer_desktop_1440.png)
  - [`before/cta_mobile_390.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/before/cta_mobile_390.png) · [`before/footer_mobile_390.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/before/footer_mobile_390.png)
- **After (`11` ảnh cập nhật cuối):**
  - Desktop CTA & Hover: [`after/cta_desktop_1440.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/cta_desktop_1440.png) · [`after/cta_button_hover.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/cta_button_hover.png)
  - Trạng thái chuyển động & dự phòng: [`after/cta_animation_mid.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/cta_animation_mid.png) · [`after/cta_animation_settled.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/cta_animation_settled.png) · [`after/cta_reduced_motion.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/cta_reduced_motion.png) · [`after/cta_webgl_fallback.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/cta_webgl_fallback.png)
  - Footer & Mobile: [`after/footer_desktop_1440.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/footer_desktop_1440.png) · [`after/cta_mobile_390.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/cta_mobile_390.png) · [`after/footer_mobile_390.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/footer_mobile_390.png) · [`after/cta_mobile_320.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/cta_mobile_320.png) · [`after/footer_mobile_320.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/after/footer_mobile_320.png)
- **Video chuyển động thực:** [`cta_3d_construction_and_footer.webm`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_cta_footer_audit/video/cta_3d_construction_and_footer.webm) (`1,208,516 bytes`)

---

## 8. Kết quả Cổng Chất lượng, Hồi quy & Giới hạn Xác minh (§16.14–§16.17)

### 8.1. TypeScript, Build, Vitest & Playwright (§16.14–§16.15)
- **`design-taste-frontend/scripts/lint.mjs`** (sau sửa cuối, `task-81259`): thoát `0`, `RESULT: 0 FAIL, 0 WARN`.
- **`npx tsc -b && npm run build`** (sau sửa cuối, `task-81259`): thoát `0`, `✓ 128 modules transformed`, `✓ built in 7.22s`.
- **Vitest bộ mục tiêu Landing / Hygiene / Tokens / CodeIndex** (sau sửa cuối, `task-81259`): **`Test Files 27 passed (27)`**, **`Tests 140 passed (140)`** (`Duration 12.20s`).
- **Vitest toàn bộ repo (`npx vitest run --maxWorkers=2`)** (`task-81145`, ngay trước tinh chỉnh 3 dòng CSS/framing cuối ở Step 1): `Test Files 184 passed | 2 failed (186)` (`Tests 2235 passed | 2 failed (2237)`), trong đó đúng `2` test quét toàn bộ catalog hình học (`axo-cross-family-scene3d-acceptance.test.tsx:383`, `step-continuity-and-scene-invariants.test.tsx:255`) chạm timeout mặc định `5000ms` khi chạy 2 worker tranh chấp CPU. Chạy tách tải hai tệp đó (`npx vitest run --maxWorkers=1`, `task-81183`) đạt **`Test Files 2 passed (2)`**, **`Tests 18 passed (18)`** (`Duration 10.03s`, không sửa assertion hay tăng timeout).
- **Playwright QA (`qa_cta_footer_after.mjs`, `task-81265`)** (sau sửa cuối): `8/8` viewport pass, `PROD_SMOKE` pass (`/` V1.2.2 bình thường: `hasHeader: true, hasHero: true, hasFooter: true, overflowX: false, errors: []`), `VIDEO_BYTES=1208516`, `0` errors.
- **Kiểm tra hậu báo cáo:** chạy lại `rules-hygiene.test.ts`, `code-index-sync.test.ts`, `landing-approved-ui-regression.test.tsx` ngay trước commit tài liệu.

### 8.2. Những giới hạn chưa xác minh trung thực (§16.16)
1. Thiết bị di động đo qua giả lập 4× CPU trên Chromium desktop (`NOT_PHYSICAL_MOBILE`), chưa kiểm chứng trên iOS Safari / Android Chrome phần cứng thật.
2. Nguồn tham khảo `https://tympanus.net/codrops/` trả HTTP `403` Cloudflare (`NOT VERIFIED`).
3. Sau tinh chỉnh 3 dòng CSS (`scroll-margin-top`, bỏ `border-top` Footer, padding mobile) và `lookY + 0.40` cuối cùng, đã chạy lại đầy đủ 27/27 file Vitest mục tiêu (140/140 test) + `tsc -b` + `vite build` + Playwright QA, không lặp lại full `186`-file sweep vì các file không thuộc Landing không bị chạm.
4. `PRODUCTION_DEPLOYMENT_VERIFIED = NO`; chưa triển khai bản V1.4 lên route mặc định `/`.

### 8.3. Các tệp chưa commit ngoài phạm vi nhiệm vụ (`OWNERSHIP_BLOCKED`, §16.17)
Working tree đang chứa thay đổi từ các phiên song song khác (giữ nguyên 100% không stage/sửa/hoàn tác):
- **`backend/` (16 entries):** sửa `accounts/*`, `main.py`, `persistence/classroom_models.py`, `scripts/seed_demo_accounts.py`, các `tests/test_*`; xóa `classroom_router.py`, `session_router.py`, `test_classroom_api.py`, `test_live_session_api.py`; untracked migration `backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py`.
- **`docs/`:** sửa `docs/EVIDENCE_INDEX.md`; untracked nhiều thư mục run trong `docs/evaluation/geometry/runs/` (`axo-attachment-fidelity/`, `axo-attachment-refinement/`, `axo-attachment-scroll/`, `axo-attachment-ux/`, `axo-ui-consistency/`).
- **`frontend/`:** sửa `index.html`, `package.json`, `package-lock.json`, `public/favicon.svg`, `AuthGate.tsx`, `AxoErrorExperience.tsx`, `HomeView.tsx`, `SimulationWorkspace.tsx`, `TopNav.tsx`, `Scene3DExplorer.tsx`, `scene3d-tool-menu.tsx`, `auth.ts`, `history.ts`, `learner-recovery-snapshot.ts`, `store.ts` và nhóm test liên quan; xóa các thành phần/test Classroom/Assign/Monitor/Observe/LiveClass/PracticeReporter; untracked `public/favicon-*.png`, `public/prototypes/*`, `scripts/attachment-resize.node-test.mjs`, `ScreenCaptureDialog.tsx`, `LeftSidebar.v9_2.test.tsx`, `attachment-fidelity.test.tsx`, `v92-*`, `v942-*`, `v943-*`, `v944-*`, `v945-*`, `state/__tests__/workspace-tab-close.test.tsx`.

---

## 9. Toàn bộ Version Inventory của Frontend & Dependency Map (§16.19–§16.21)

### 9.1. Kiểm kê Toàn Frontend (`403` tracked files + untracked trong `frontend/`) (§16.19)

| Phân hệ / Nhóm tệp | Tệp tiêu biểu / Thực thể (`V*`, `Preview`, `Prototype`, `Demo`) | Nơi tham chiếu chính | Trạng thái vận hành thực tế |
|---|---|---|---|
| **Router điều phối Landing** | `src/components/LandingView.tsx` (`LandingPrototypeMode = "prod" \| "a" \| "b" \| "v14"`) | `App.tsx:16, 686` | `LIVE_PRODUCTION_ROUTER` |
| **Production V1.2.2 (`prod`)** | `LandingHeader.tsx`, `LandingHeroSculpture3D.tsx`, `LandingStorytelling.tsx`, `LandingExplainerAnimation.tsx`, `LandingClosingSculpture.tsx`, `LandingIllustrationAccents.tsx` | `LandingView.tsx:3–11, 137–182` | `LIVE_PRODUCTION_DEFAULT` (`/` & `/gioi-thieu`) |
| **Shared Active Landing Modules** | `landing-geometry-data.ts`, `LandingInteractiveDemo.tsx`, **`LandingHeroScene3D.tsx` (`SpatialSceneCanvas`)**, `landing.css` | **`LandingInteractiveDemo.tsx:8` (`SpatialSceneCanvas`)**; `LandingView.tsx`; `LandingPrototypeA/B`; `LandingPreviewV14` | **`SHARED_LIVE_ACROSS_ALL_MODES`** |
| **V1.4 Preview (`?preview=v1.4`)** | `LandingPreviewV14.tsx`, `LandingHeroV14.tsx`, `LandingStorytellingV14.tsx`, `AnnotatedHeading.tsx`, `LandingClosingV14.tsx` (`LandingClosingV14`, `LandingFooterV14`), `LandingClosingScene3D.tsx` | `LandingView.tsx:8, 82`; `LandingPreviewV14.tsx:1–15`; `LandingClosingV14.tsx:4, 49` | `ISOLATED_PREVIEW_CANDIDATE` (`PENDING_OWNER_REVIEW`) |
| **V1.3 Experimental (`?prototype=a\|b`)** | `LandingPrototypeA.tsx`, `LandingPrototypeB.tsx` | `LandingView.tsx:9–10, 86–90`; `LandingPrototypeB.tsx:12` mượn helpers từ `LandingPrototypeA.tsx` | `NOT_APPROVED_FOR_INTEGRATION` (chờ xóa ở Pha 2) |
| **Landing & Styles Tests (`21` + `4` style)** | `landing-*.test.tsx` (`18` file), `phase-b-views.test.tsx`, `sidebar-toggle-icon.test.tsx`, `ui-hygiene.test.ts`, `tokens.test.ts`, `class-coverage.test.ts`, `scrollbar-ownership.test.ts`, `transition-semantics.test.ts` | Bộ test Vite/Vitest Landing & CSS tokens | `ACTIVE_TESTS` |
| **Workspace / Geometry 3D Core** | `SimulationWorkspace.tsx`, `HomeView.tsx`, `LibraryView.tsx`, `Scene3DExplorer.tsx`, `simulations/domains/geometry/*` (`scene3d-*.ts/tsx`, fixtures) | `App.tsx`, các bài test `simulations/domains/geometry/*` | `ACTIVE_PRODUCT_CORE` (hiện một số file có edit ngoài phạm vi từ phiên khác) |
| **File `V*` / Prototype ngoài phạm vi** | `public/prototypes/axo-left-sidebar-prototype.html`, `axo-multi-problem-workspace.html`, `LeftSidebar.v9_2.test.tsx`, `v92-*`, `v942-*`, `v943-*`, `v944-*`, `v945-*`, `v9413-*` | Các nhiệm vụ Workspace / Sidebar / Capture trước hoặc song song | `OWNERSHIP_BLOCKED` / ngoài phạm vi Landing |

### 9.2. Phân loại Hành động & Đề xuất Vòng đời (`KEEP / RENAME_AFTER_APPROVAL / DELETE_AFTER_APPROVAL / UNKNOWN / OWNERSHIP_BLOCKED`) (§16.20)

| File / Nhóm file | Phân loại | Lý do & Bằng chứng tham chiếu |
|---|---|---|
| `LandingView.tsx`, `LandingHeader.tsx`, `LandingInteractiveDemo.tsx`, `landing-geometry-data.ts`, `landing.css`, `LandingClosingScene3D.tsx` | **`KEEP`** | Thành phần cốt lõi / tên canonical chức năng không dính hậu tố số (tách riêng phần dọn nhánh flag trong `LandingView.tsx` ở Pha 2) |
| **`LandingHeroScene3D.tsx` (`SpatialSceneCanvas`)** | **`RENAME_AFTER_APPROVAL`** (hiện `KEEP` bắt buộc) | **Không phải code chết:** được `LandingInteractiveDemo.tsx:8` import và sử dụng trên cả 4 route (`prod`, `a`, `b`, `v14`). Đề xuất đổi tên rõ vai trò (`LandingInteractiveSceneCanvas.tsx`) sau khi chốt Pha 2 |
| `LandingPreviewV14.tsx`, `LandingHeroV14.tsx`, `LandingStorytellingV14.tsx`, `LandingClosingV14.tsx`, `AnnotatedHeading.tsx` | **`RENAME_AFTER_APPROVAL`** | Đang gánh thiết kế ứng viên V1.4 `PENDING_OWNER_REVIEW`; giữ trong Pha 1, hợp nhất & bỏ hậu tố `V14` ở Pha 2 sau phê duyệt |
| `LandingPrototypeA.tsx`, `LandingPrototypeB.tsx` | **`DELETE_AFTER_APPROVAL`** | Đã bị gắn `NOT_APPROVED_FOR_INTEGRATION`; chỉ giữ sau `readLandingPrototypeMode()` để đối chiếu, xóa hoàn toàn ở Pha 2 kèm rà `landing-motion-accessibility.test.tsx` & `LandingPrototypeB.tsx:12` |
| `LandingHeroSculpture3D.tsx`, `LandingStorytelling.tsx`, `LandingExplainerAnimation.tsx`, `LandingClosingSculpture.tsx`, `LandingIllustrationAccents.tsx` | **`DELETE_AFTER_APPROVAL`** | Hiện **đang phục vụ route `prod` `/` và `/gioi-thieu`** (`LandingView.tsx:3–11`). Cấm xóa ở Pha 1; chỉ thay thế/xóa sau khi chủ dự án duyệt chuyển `prod` sang thiết kế V1.4 ở Pha 2 |
| 4 test mới (`landing-cta-geometry`, `landing-cta-motion`, `landing-footer-layout`, `landing-approved-ui-regression`) + `landing-webgl-lifecycle.test.tsx` | **`KEEP`** | Test theo tên chức năng, bảo vệ hình học, animation, WebGL, capsule và guard hợp nhất |
| Toàn bộ file dirty/untracked của Classroom, Attachment, LeftSidebar V9.2–V9.4.x (`backend/*`, `docs/EVIDENCE_INDEX.md`, `docs/evaluation/geometry/runs/*`, `frontend/public/prototypes/*`, `ScreenCaptureDialog.tsx`, `workspace-tab-close.test.tsx`...) | **`OWNERSHIP_BLOCKED`** | Thay đổi đang mở của phiên khác ngoài phạm vi nhiệm vụ; giữ nguyên tuyệt đối |
| Tên/biến thể `v9*` trong các test Workspace/Geometry cũ chưa rà hết runtime | **`UNKNOWN`** | Ngoài phạm vi Landing CTA/Footer; chỉ đánh giá dọn nếu có lệnh kiểm toán Workspace riêng |

### 9.3. Bảng Mapping Phiên bản Cũ → Component Canonical Mục tiêu (Pha 2 Sau Phê duyệt) (§16.21)

| Phiên bản / Thành phần cũ | Component Canonical mục tiêu | Dependency & Test cần di trú khi gộp Pha 2 |
|---|---|---|
| `LandingHeroSculpture3D.tsx` (`prod`) + `LandingPrototypeA/B` Hero + `LandingHeroV14.tsx` | `frontend/src/components/landing/LandingHero.tsx` | Cập nhật `LandingView.tsx`, `landing-hero-visual-lifecycle.test.tsx`, `phase-b-views.test.tsx` |
| `LandingStorytelling.tsx` + `LandingExplainerAnimation.tsx` (`prod`) + `LandingPrototypeA/B` Story + `LandingStorytellingV14.tsx` | `frontend/src/components/landing/LandingStorytelling.tsx` | Cập nhật `LandingView.tsx`, `landing-storytelling-*.test.tsx`, `landing-demo-integrity.test.tsx` |
| `LandingHeroScene3D.tsx` (`SpatialSceneCanvas`) | `frontend/src/components/landing/LandingInteractiveSceneCanvas.tsx` (hoặc giữ `SpatialSceneCanvas`) | Cập nhật import ở `LandingInteractiveDemo.tsx:8`, `landing-webgl-lifecycle.test.tsx` |
| `LandingClosingSculpture.tsx` (`prod`) + `LandingClosingV14.tsx` (`LandingClosingV14`) | `frontend/src/components/landing/LandingClosing.tsx` + `LandingClosingScene3D.tsx` | Cập nhật `LandingView.tsx`, `landing-cta-*.test.tsx`, giữ nguyên `#btn-landing-final-start` & `#btn-landing-hero-library` |
| `LandingClosingV14.tsx` (`LandingFooterV14`) | `frontend/src/components/landing/LandingFooter.tsx` | Cập nhật `LandingView.tsx`, `landing-footer-layout.test.tsx` |
| `LandingPreviewV14.tsx` + `LandingView.tsx` (`?preview=v1.4` / `?prototype=a\|b`) | `frontend/src/components/LandingView.tsx` | Gỡ `readLandingPrototypeMode()` & `switchLandingPrototype()`, bỏ các class CSS chỉ dùng cho `.axo-v13-*`, cập nhật `landing-approved-ui-regression.test.tsx` để bắt mọi route/prototype chết |
| `LandingPrototypeA.tsx`, `LandingPrototypeB.tsx`, `LandingIllustrationAccents.tsx` | *Xóa sau phê duyệt Pha 2* | Gỡ tham chiếu trong `LandingView.tsx`, `landing-motion-accessibility.test.tsx`, `docs/CODE_INDEX.md` |

---

## 10. Tình trạng Phê duyệt & Kế hoạch Phát hành / Rollback Dự kiến (§16.22–§16.23)

### 10.1. Bảng Tình trạng Nghiệm thu (§16.22)

| Cổng trạng thái | Trạng thái hiện tại | Bằng chứng |
|---|---|---|
| **`TECHNICALLY_VERIFIED`** | **ĐẠT (cục bộ trên nhánh preview)** | `lint.mjs` 0 fail, `tsc -b` + `vite build` pass, `27/27` Vitest mục tiêu pass (`140/140`), `184/186` full `--maxWorkers=2` + `2/2` (`18/18`) `--maxWorkers=1`, Playwright 8 viewport + 11 ảnh + video WebM pass |
| **`OWNER_DESIGN_APPROVED`** | **CHƯA** (`PENDING_OWNER_REVIEW`) | Chủ dự án chưa duyệt bộ ảnh/video & thiết kế CTA 3D + Footer |
| **`READY_FOR_RELEASE`** | **CHƯA** | Chỉ mở sau khi hoàn tất Pha 2 (hợp nhất canonical + xóa bản cũ đã được duyệt) |
| **`DEPLOYED`** | **CHƯA (`NOT_DEPLOYED`)** | Không có lệnh deploy/push/merge trong lần chạy hiện tại |

### 10.2. Kế hoạch Phát hành Pha 2 & Rollback (§16.23)

1. **Khi chủ dự án phê duyệt thiết kế (bằng lệnh riêng cho Pha 2):**
   - Hợp nhất các tệp V1.4 sang tên canonical trong bảng §9.3 (`LandingHero.tsx`, `LandingStorytelling.tsx`, `LandingClosing.tsx`, `LandingFooter.tsx`, không tạo hậu tố `V15`/`V2`).
   - Đưa giao diện đã chốt lên `/` và `/gioi-thieu`, xóa `LandingPrototypeA/B`, các file V1.2.2 bị thay thế và nhánh query `?prototype=*` / `?preview=*` kèm cập nhật `docs/CODE_INDEX.md`.
   - Chạy đầy đủ `tsc -b`, `npm run build`, full `npx vitest run --maxWorkers=2` và Playwright E2E trực tiếp trên `/` & `/gioi-thieu`.
   - Chỉ merge vào `main` / deploy khi có lệnh xác nhận rõ ràng của chủ dự án.
2. **Rollback dự kiến:**
   - Do Pha 1 chỉ tác động cô lập vào `?preview=v1.4` và không chạm `/` hay `/gioi-thieu`, rollback tức thì chỉ cần `git revert 471baf39b` (cùng commit báo cáo tương ứng) trên nhánh làm việc mà không ảnh hưởng production V1.2.2.

---

**Trạng thái thực tế:** `NOT_DEPLOYED`  
**Owner Approval:** `PENDING_OWNER_REVIEW`
