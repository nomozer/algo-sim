# AXO Landing V1.4 — Final Design Recovery & Interaction Refinement Report

**Ngày hoàn thành:** 2026-11-16  
**Worktree:** `D:\Documents\projects\axo-geometry-library`  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Baseline Commit SHA:** `e39d67548` (`docs(axo): add landing v1.4 product recovery report`) · Implementation base `a7d2437a9`  
**Implementation Commit SHA:** `eb7448533` (`eb7448533c124e84b6e07aebf7e8d56a854ef0a0`)  
**Tuyến xem trước cô lập:** `http://localhost:3001/gioi-thieu?preview=v1.4` (`presentation="v14"`)  
**Tuyến Production mặc định:** `/` và `/gioi-thieu` (**V1.2.2** `"prod"` — bảo toàn nguyên vẹn)  
**Tình trạng triển khai thực tế:** `NOT_DEPLOYED`  
**Trạng thái localhost:3001:** `PORT_3001_PRESERVED` (trạng thái nền `NOT_LISTENING`; khởi chạy duy nhất một lần theo cho phép tường minh của Chủ dự án và giữ chạy ngầm vĩnh viễn)  
**Owner Approval:** `PENDING_OWNER_REVIEW`

> [!IMPORTANT]
> - Báo cáo tách bạch rạch ròi giữa **xác minh kỹ thuật (`TECHNICAL_VERIFIED`)**, **bằng chứng quan sát trực tiếp qua REA MCP (`VERIFIED_BY_REA`)**, **suy luận thiết kế AXO (`CUSTOM_AXO_DESIGN`)** và **phê duyệt cảm quan / phát hành của Chủ dự án (`PENDING_OWNER_REVIEW`)**.
> - Không có tệp nào thuộc Workspace (`/app`), Production V1.2.2 (`/` và `/gioi-thieu`), Backend hoặc khu vực `OWNERSHIP_BLOCKED` của phiên song song bị sửa, khôi phục hay stage.

---

## A. Baseline

### 1. Trạng thái Worktree & Cổng 3001 Trước Khi Sửa
- **Nhánh & Worktree:** `feat/axo-geometry-library-verification` tại `D:\Documents\projects\axo-geometry-library`, xuất phát từ HEAD `e39d67548`.
- **Trạng thái cổng `localhost:3001` lúc mở phiên:** Không có tiến trình nào đang lắng nghe trên `3000/3001/3002/4173/5173` (`NOT_LISTENING` do phiên trước đã hủy background task). Sau khi hỏi trực tiếp và được Chủ dự án cho phép (`ask_question`), tiến trình `npx vite --port 3001 --strictPort` được khởi chạy từ `D:\Documents\projects\axo-geometry-library\frontend` (`TaskId: 3ef24255-0976-432d-b0af-48ebb7f2067e/task-83120`, PID `5220`) và giữ chạy xuyên suốt cũng như sau khi hoàn thành toàn bộ tác vụ.
- **Kiểm tra HTTP `200` trước khi sửa:** `/` (`200`), `/gioi-thieu` (`200`), `/gioi-thieu?preview=v1.4` (`200`), `/app` (`200`).

### 2. Bảng Phân Loại Lỗi Gốc Quan Sát Được Ở Bản Nền (`eb7448533` trước đó)

| Phân loại | Khu vực & Tệp | Nguyên nhân gốc quan sát từ ảnh Before & code |
|---|---|---|
| `LAYOUT_ERROR` / `RESPONSIVE_ERROR` | **Hero** ([`LandingHeroV14.tsx`](../../../frontend/src/components/landing/LandingHeroV14.tsx), [`AnnotatedHeading.tsx`](../../../frontend/src/components/landing/AnnotatedHeading.tsx), [`landing.css`](../../../frontend/src/components/landing/landing.css)) | `.axo-sp-main` đã cộng `72px` header, nhưng `.axo-v14-hero` tiếp tục đệm `padding-top: clamp(78px, 8.2vh, 108px)` gây khoảng trống thừa phía trên; `.axo-v14-hero-title-line` ép `white-space: nowrap` ở cả màn nhỏ làm co chữ mobile `1.52rem`; vòng tròn `"hình dung"` hơi sát dấu chữ quốc ngữ và gãy nhẹ ở đỉnh phải; đường SVG tầng `z-index` bị `inspect.mjs` bắt lỗi `[covered-text]` trên dòng 1. |
| `MOTION_ERROR` / `GEOMETRY_ERROR` / `CONTENT_ERROR` | **Storytelling** ([`LandingStorytellingV14.tsx`](../../../frontend/src/components/landing/LandingStorytellingV14.tsx), [`landing.css`](../../../frontend/src/components/landing/landing.css)) | (1) `computeChapterEnvelope` để khoảng trống `vis: 0` quanh `p = 0.25, 0.50, 0.75` khiến cột chữ biến mất hoàn toàn khi cuộn qua ranh giới chặng; (2) Chặng 1 đặt `extrude: 0.22` làm bẹp khối lăng trụ so với Chặng 2–4 và `zoom: 1.12 -> 1.25` khiến đáy `A, M` + góc mặt phẳng cắt bị **cắt cụt mép dưới SVG** (`viewBox="0 0 600 430"`); (3) Việc cấm luôn giả thiết gốc `a = 4` đã đánh đồng giả thiết với đáp án toán học (`3√7`, `2√2`). |
| `LAYOUT_ERROR` / `UX_ERROR` | **Interactive Demo** ([`LandingInteractiveDemo.tsx`](../../../frontend/src/components/landing/LandingInteractiveDemo.tsx), [`landing-geometry-data.ts`](../../../frontend/src/components/landing/landing-geometry-data.ts), [`landing.css`](../../../frontend/src/components/landing/landing.css)) | Thẻ `.axo-v14-demo-focus-note` lồng viền trắng bên trong bảng điều khiển tạo cảm giác hộp-trong-hộp và để khoảng hở dọc lớn phía trên nút `"Mở trong Xưởng 3D"`. |
| `GEOMETRY_ERROR` / `ARCHITECTURE_ERROR` | **Closing CTA** ([`LandingClosingScene3D.tsx`](../../../frontend/src/components/landing/LandingClosingScene3D.tsx)) | Dựng một scene Three.js thứ 3 độc lập (khoảng ~1.045 dòng) với hai khối rời rạc (Lăng trụ lục giác + Hình nón) không gắn với dữ liệu hình học kiểm chứng của Axo và tạo thêm `WebGLRenderer` tùy biến không cần thiết. |
| `UX_ERROR` | **Footer & Hover** ([`LandingClosingV14.tsx`](../../../frontend/src/components/landing/LandingClosingV14.tsx), [`landing.css`](../../../frontend/src/components/landing/landing.css)) | Thiếu điều khiển `#btn-landing-footer-top` (`"Về đầu trang"`) và nút chính `.axo-v14-btn-primary:hover` chưa đồng bộ bóng đổ nâng nhẹ hướng xanh chuẩn bản Production. |

---

## B. Design Research (`VERIFIED_BY_REA` + Đối Chiếu Tham Chiếu)

Thực hiện kiểm chứng trực tiếp bằng công cụ REA Chrome DevTools Protocol (`rea`: `list_browser_targets`, `inspect_web_page`, `capture_web_screenshot`) trên Chromium CDP `127.0.0.1:9233` (trước khi sửa) và `127.0.0.1:9234` (sau khi sửa), sau đó đóng riêng phiên Chromium kiểm tra mà không chạm cổng `3001`:

| Nguồn quan sát | Evidence ID / Thao tác REA | SHA-256 JSON / Ảnh PNG | Quan sát thực tế & Bài học áp dụng |
|---|---|---|---|
| `https://bundaumayo.top/` (Hero + Footer) | `inspect_web_page` `ev_7f8bb614...186bb` · `capture_web_screenshot` `ev_c6a43195...77b73` (Hero) & `ev_3719a352...044c6` (Footer) | PNG Hero `985d1923...c35b45c` · PNG Footer `23adc805...3b1b58d` (`VERIFIED_BY_REA`) | **Học trực tiếp:** Vòng khoanh nét tay quanh tiếng Việt có dấu mở thoáng theo chiều dọc tránh cắt dấu; Footer sạch không kẻ nhiều đường ngang, đặt `Trở về đầu trang` dạng liên kết chữ kèm mũi tên hướng lên gọn gàng ở đáy phải. **Tránh sao chép:** Không bê nền xanh mint hay nút viền đen dày kiểu sticker minh họa (`CUSTOM_AXO_DESIGN`). |
| `https://www.notion.com/` | `inspect_web_page` `ev_bd63e0bc...63fe8` · `capture_web_screenshot` `ev_cccde029...4b5f5` | PNG `407e2c7f...cb2128` (`VERIFIED_BY_REA`) | **Học trực tiếp:** Tiêu đề không chân đầm chắc (`tight tracking`), tương phản trắng sạch trên nút chính `#0075de`, nút phụ nền dịu và minh họa sản phẩm trung tâm làm điểm neo thị giác. |
| `AXO V1.4 Before` (`localhost:3001/gioi-thieu?preview=v1.4`) | `inspect_web_page` `ev_42b209af...10b40` · `capture_web_screenshot` `ev_380daef4...0828b` | PNG `061bb8e6...ebf5108` (`VERIFIED_BY_REA`) | Ghi nhận khoảng đệm đỉnh Hero lớn, chữ `"Theo dõi bài toán qua..."` ló sớm ở mép dưới fold 900px và đỉnh vòng cam phía trên chữ `"hình dung"` hơi gấp. |
| `AXO V1.4 After` (`localhost:3001/gioi-thieu?preview=v1.4`) | `inspect_web_page` `ev_142aa65b...27d2` · `capture_web_screenshot` `ev_7c776e63...36e4d` | PNG `b02327cd...5461` (`VERIFIED_BY_REA`) | Xác nhận trên DOM & ảnh live: Hero cân đối gọn ngay trong viewport đầu, nét khoanh thoáng dấu chữ tiếng Việt, khối chóp `S.ABCD` đồng khối rõ nét (`20` resources, `0` lỗi tải trang). |

---

## C. Implementation

Toàn bộ thay đổi đã được rà soát và đóng gói trong commit **`eb7448533`** (`951` dòng thêm, `1329` dòng bỏ — giảm `378` dòng ròng nhờ hợp nhất renderer 3D dùng chung):

1. **Hero ([`AnnotatedHeading.tsx`](../../../frontend/src/components/landing/AnnotatedHeading.tsx), [`LandingHeroV14.tsx`](../../../frontend/src/components/landing/LandingHeroV14.tsx), [`landing.css`](../../../frontend/src/components/landing/landing.css)):**
   - Mở rộng `VARIANT_GEOMETRY.circle` (`viewBox="0 0 360 160"`), hạ độ dày nét còn `2.05px` (`stroke-opacity: 0.92`) và đặt `.axo-v14-hero-title` có `isolation: isolate` với `.axo-v14-anno-text { z-index: 2 }` / `.axo-v14-anno-svg { z-index: -1 }` để nét vẽ luôn nằm sau chữ quốc ngữ và không kích hoạt `[covered-text]`.
   - Khôi phục khoảng trắng rõ ràng giữa hai dòng `<span className="axo-v14-hero-title-line">` trên mobile dưới `440px` (`white-space: normal`, cỡ chữ `clamp(1.92rem, 7.6vw, 2.3rem)`), giữ 2 dòng chuẩn xác từ `>= 440px` (`51.1px` trên `1440px`).
   - Loại bỏ khoảng đệm trần trùng lặp (`padding-top: clamp(24px, 3.8vh, 44px)` trên desktop, `20px` trên mobile) và kéo camera khối chóp `S.ABCD` về `[9.7, 5.9, -10.1]` giữ nguyên `capLift = 0` và `HERO_SECTION_FILL_OPACITY = 0.28`.

2. **Scroll-Driven Storytelling ([`LandingStorytellingV14.tsx`](../../../frontend/src/components/landing/LandingStorytellingV14.tsx), [`landing.css`](../../../frontend/src/components/landing/landing.css)):**
   - **Tỷ lệ nhất quán & hết cắt hình:** Giữ cố định `extrude = 1` và `zoom = 1` trên toàn bộ 4 chặng lăng trụ `ABC.A′B′C′`, mở rộng khung chiếu SVG thành `640×490` (`cx = 320, cy = 242, scale = 55`) kèm khử trùng nhãn 2 lượt `separateLabelPositions` và vạch đánh dấu trung điểm trên `AB, AC, CC′`.
   - **Giả thiết gốc vs Đáp án ([`landing-product-integrity.test.tsx`](../../../frontend/src/components/__tests__/landing-product-integrity.test.tsx)):** Khôi phục giả thiết gốc của đề (`cạnh a = 4 · Trung điểm M ∈ AB, N ∈ AC, P ∈ CC′`) tại Lead & Chặng 1, đồng thời giữ `0` đáp án tính sẵn (`3√7`, `2√2`, `MN = 2`, `PQ = 4`, `S(MNPQ)`).
   - **Chuyển chặng mượt 2 chiều không blank frame:** Thay khoảng chết `vis: 0` bằng phân hoạch kín `[0, 0.25) | [0.25, 0.5) | [0.5, 0.75) | [0.75, 1]` kết hợp hiệu ứng trượt dọc có giảm chấn RAF (`0.34`, tự nhảy tức thì khi cuộn vượt `0.2`, tự dừng `rafId = 0` khi đứng yên) và rãnh trạng thái 4 chặng `.axo-v14-story-rail` (chấm tròn hình học + nhãn gọn `Đề bài · Dựng hình · Quan hệ · Kết quả` trên mobile).

3. **Interactive Demo ([`LandingInteractiveDemo.tsx`](../../../frontend/src/components/landing/LandingInteractiveDemo.tsx), [`landing-geometry-data.ts`](../../../frontend/src/components/landing/landing-geometry-data.ts), [`landing.css`](../../../frontend/src/components/landing/landing.css)):**
   - Xóa viền hộp lồng trong `.axo-v14-demo-focus-note`, bỏ viền 1px bao ngoài trên `.axo-sp-demo-workbench.is-v14` & `.axo-sp-scene-shell.is-v14` (thay bằng tương phản bề mặt `#f6f5f4` / `#ffffff`), bổ sung trường `v14Premise` (`Dữ kiện gốc`) và gợi ý xoay ngay trong bố cục `align-items: center` cân đối, bảo toàn bước đang chọn khi bấm `#btn-landing-demo-reset`.

4. **Closing CTA, Footer & Hover ([`LandingHeroScene3D.tsx`](../../../frontend/src/components/landing/LandingHeroScene3D.tsx), [`LandingClosingScene3D.tsx`](../../../frontend/src/components/landing/LandingClosingScene3D.tsx), [`LandingClosingV14.tsx`](../../../frontend/src/components/landing/LandingClosingV14.tsx), [`landing.css`](../../../frontend/src/components/landing/landing.css)):**
   - Mở rộng `SpatialSceneCanvas` thêm `frameless`, `pointTagFilter`, chặn `?no_webgl=1` và phông chữ không chân cho SVG fallback V1.4.
   - Viết lại `LandingClosingScene3D.tsx` tái sử dụng trực tiếp `SpatialSceneCanvas` + dữ liệu hình lập phương `LANDING_CUBE_SAMPLE` (`spatial-cube-hexagon-3d`: 4 nhịp `cube-solid -> cutting-plane -> intersection-trace -> hexagon-settled` qua `MNEPFQ` trên nền `#f6f5f4` trong suốt, `0` WebGL renderer tùy biến lặp lại).
   - Khôi phục `#btn-landing-footer-top` (`"Về đầu trang"` kèm mũi tên SVG hướng lên trong `LandingFooterV14`) và khôi phục `.axo-v14-btn-primary:hover` đúng cảm giác bản chuẩn (`transform: translateY(-1px); box-shadow: 0 8px 20px -10px rgba(0, 117, 222, 0.55);`).

5. **Version Lifecycle & Docs Index:** Không tạo `V15`/`V16`; cập nhật duy nhất dòng `1983` trong [`docs/CODE_INDEX.md`](../../../docs/CODE_INDEX.md).

---

## D. Visual Evidence (Before vs After & Motion Videos)

Thư mục bằng chứng của lượt hoàn thiện nằm tại:  
`C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\landing_v14_final\`

### 1. Ma trận đối chiếu ảnh Trước / Sau (`14` trạng thái + phụ bản)

| Trạng thái kiểm chứng | Ảnh Before | Ảnh After | Xác nhận trực quan |
|---|---|---|---|
| Hero Desktop (`1440×900`) | `before/hero_before_1440.png` | `after/01_hero_desktop_1440.png` | Vòng khoanh thoáng dấu chữ tiếng Việt, đệm đỉnh gọn, `h1` 2 dòng `51.1px`, `S.ABCD` liền khối `CLS = 0`. |
| Hero Mobile (`390×844` & `320×568`) | `before/hero_before_390.png` | `after/02_hero_mobile_390.png`, `after/02b_hero_mobile_320.png` | Tách dòng `"không gian, / dễ hình dung hơn."` tự nhiên, đủ khoảng trắng, `overflowPx = 0`. |
| Storytelling Chặng 1 (`p=0.08`) | `before/story_stage1_before_1440.png` | `after/03_story_stage1_1440.png` | Hết bẹp khối (`extrude = 1`), khôi phục `a = 4`, vạch trung điểm `M, N, P`, `clippedSvgCount = 0`. |
| Storytelling Chặng 2 & Transition (`p=0.25`, `0.38`) | `before/story_deadband_before_1440.png` | `after/04b_story_transition_1to2_1440.png`, `after/04_story_stage2_1440.png` | Xóa hoàn toàn khoảng trống mù `vis: 0`; luôn hiển thị đúng `1` chặng, không cắt mép đáy mặt phẳng `(MNP)`. |
| Storytelling Chặng 3 (`p=0.50`, `0.65`) | — | `after/05b_story_transition_2to3_1440.png`, `after/05_story_stage3_1440.png` | Tia song song `MN ∥ BC ⇒ PQ ∥ BC` nổi rõ, điểm `Q ∈ BB′` xuất hiện đúng nhịp. |
| Storytelling Chặng 4 (`p=0.75`, `0.90`) | `before/story_stage4_before_1440.png` | `after/06b_story_transition_3to4_1440.png`, `after/06_story_stage4_1440.png` | Hình thang cân `MNPQ` và 4 góc mặt phẳng `(MNP)` lọt trọn trong SVG (`clippedSvgCount = 0`). |
| Storytelling Mobile (`390×844`) | `before/story_before_390.png` | `after/07b_story_stage1_mobile_390.png`, `after/07_story_mobile_390.png` | Khung hình `196px` không cắt góc dưới, rãnh 4 nhãn gọn phía trên card, chữ và hình không che nhau. |
| Demo Chóp `S.ABCD` & Bước 2 (`1440×900`) | `before/demo_before_1440.png` | `after/08_demo_pyramid_1440.png`, `after/08b_demo_pyramid_step2_1440.png` | Bỏ viền hộp lồng, `Dữ kiện gốc` + `Gợi ý quan sát` cân với CTA, không lộ đáp án số. |
| Demo Lập phương & Mobile (`390×844`) | — | `after/09_demo_cube_1440.png`, `after/09b_demo_mobile_390.png` | Khung lập phương & thiết diện lục giác đều nằm gọn, `0` chip đáp án. |
| Closing CTA Desktop & Mobile | `before/closing_before_1440.png` | `after/10_closing_cta_desktop_1440.png`, `after/11_closing_cta_mobile_390.png` | Khối lập phương `ABCD.A′B′C′D′` cắt bởi `(MNP)` thành lục giác đều `MNEPFQ` nổi trực tiếp trên nền `#f6f5f4`. |
| Footer Desktop & Mobile + Hover | `before/footer_before_1440.png`, `before/footer_before_390.png` | `after/12_footer_desktop_1440.png`, `after/12c_footer_top_hover_1440.png`, `after/12b_footer_mobile_390.png` | Có nút `#btn-landing-footer-top` `"Về đầu trang"` kèm mũi tên SVG + hover gạch chân xanh. |
| Mobile Drawer Guest & Authenticated | — | `after/13_mobile_drawer_guest_390.png`, `after/13b_mobile_drawer_auth_390.png` | Guest đúng 5 điều khiển; Authenticated hiện đúng vai trò `"Học sinh"`, nút `"Đăng xuất"` & CTA `"Vào ứng dụng"`. |
| Non-Regression & `?no_webgl=1` | — | `after/14_prod_v122_nonregression_1440.png`, `after/14b_workspace_app_1440.png`, `after/14c_fallback_nowebgl_1440.png` | Production `/` (V1.2.2) & Workspace `/app` nguyên vẹn; `?no_webgl=1` dùng fallback SVG sạch (`canvasCount = 0`). |

### 2. Bảng `6` Video Motion Đã Ghi (`after/videos/*.webm`)

| Tệp video | Dung lượng (bytes) | Luồng kiểm tra |
|---|---|---|
| `01_hero_to_storytelling.webm` | `801,502` | Hoàn tất Hero storyboard và cuộn mượt từ Hero xuống Chặng 1 Storytelling |
| `02_storytelling_forward_1_to_4.webm` | `789,670` | Cuộn xuôi liên tục qua `16` bước từ Chặng 1 -> Chặng 4 trên `1440×900` |
| `03_storytelling_reverse_4_to_1.webm` | `762,357` | Cuộn ngược từ Chặng 4 -> Chặng 1 kiểm tra tính thuận nghịch của hình khối & chữ |
| `04_storytelling_to_demo.webm` | `524,524` | Cuộn từ Chặng 4 xuống Interactive Demo và chuyển mẫu Chóp -> Lập phương |
| `05_closing_cta_4beat.webm` | `682,408` | Chu trình 4 nhịp của khối lập phương -> lục giác đều `MNEPFQ` tại Closing CTA |
| `06_mobile_scroll_390x844.webm` | `830,220` | Toàn tuyến trên viewport `390×844` từ Hero đến Footer (`overflowPx = 0`) |

---

## E. Technical Evidence

| Cổng kiểm tra | Lệnh thực thi | Kết quả xác thực |
|---|---|---|
| **Taste Static Lint (`design-taste-frontend`)** | `node ...\scripts\lint.mjs src/components/landing/{AnnotatedHeading,LandingHeroV14,LandingStorytellingV14,LandingInteractiveDemo,LandingClosingScene3D,LandingClosingV14,LandingPreviewV14}.tsx` | **`RESULT: 0 FAIL, 0 WARN`** (`7 files`) |
| **Taste DOM Inspector (`inspect.mjs`)** | `node ...\scripts\inspect.mjs http://localhost:3001/gioi-thieu?preview=v1.4 --out ...\taste_after --allow few-pictures,no-footage` | **`RESULT: 0 FAIL, 3 WARN`** (`[size-count]`, `[dev-server]`, `[outlined-box]` ở Header mobile toggle; `0` lỗi `[covered-text]`, `0` lỗi `[numbering]`, `Inter 100%`) |
| **TypeScript & Production Bundle** | `npx tsc -b && npm run build` | **Exit `0`** (`127 modules`, `5.42s`) |
| **Toàn bộ Vitest Suite (chạy độc lập)** | `npx vitest run --testTimeout=15000 --maxWorkers=2` | **`191/191` test files PASS (`2248/2248` tests)**, gồm toàn bộ các bài toán học & SVG (`landing-scroll-storytelling`, `landing-storytelling-geometry`, `landing-cta-geometry`, `landing-cta-motion`, `landing-footer-layout`, `landing-product-integrity`, `landing-webgl-lifecycle`, `ui-hygiene`, `class-coverage`) |
| **Playwright 8-Viewport & Interactions** | `node ...\scratch\verify-v14-final.mjs` | **`0px` overflow trên cả 8 viewport (`1920..320`), `CLS = 0`, `pageErrors = 0`, `forbiddenTextHits = []`, `forbiddenAriaHits = []`, `clippedSvgCount = 0`**, `stepPreservedOnReset = true`, `scrollAfterFooterTop = 24px`, `workspaceLoadedUrl = .../simulation/cube-hexagonal-plane-section`, `backToLandingUrl = .../gioi-thieu?preview=v1.4`, `focusRestoredAfterEscapeId = btn-landing-mobile-menu`, `prodRootIsNotV14 = true`, `appLoadedClean = true` |
| **Hiệu năng đo trên Chromium (Playwright)** | Đo frame rate & JS Heap | Desktop `1440×900`: `approxFpsIdleOrActive = 61`, `heapUsedMB = 57.51`; Mobile `390×844` CPU throttle `4x` (**`NOT_PHYSICAL_MOBILE`**): `approxFps = 61` |
| **WebGL Lifecycle & `prefers-reduced-motion`** | `?no_webgl=1` + `reducedMotion: "reduce"` | `canvasCount = 0`, `heroSvgFallback = true`, `demoSvgFallback = true`, `closingSvgFallback = true`, `storyReducedMotion = "true"` |

---

## F. Open Issues & Limitations

1. **Thiết bị di động vật lý (`NOT_PHYSICAL_MOBILE`):** Hiệu năng mobile `390×844` mới được kiểm tra bằng Playwright CPU throttle `4x` trên Windows headless Chrome (`SwiftShader`), chưa đo trực tiếp trên điện thoại iOS/Android thật với GPU phần cứng.
2. **Backend API tắt khi chạy Vite độc lập (`consoleErrorCount = 8`):** Khi kiểm tra độc lập dev server `localhost:3001` không bật FastAPI port `8000`, yêu cầu khởi tạo `/api/auth/me` trả proxy `500` ở mỗi context mới (đây là hành vi dự kiến khi thiếu backend và không phát sinh `pageError`).
3. **Bản mặc định Production:** Theo quy định an toàn phát hành, `/` và `/gioi-thieu` vẫn giữ **V1.2.2 (`"prod"`)**; bản V1.4 chỉ kích hoạt tại `?preview=v1.4` trong khi chờ Owner duyệt.

---

## G. Server Preservation (`localhost:3001`)

- **Trạng thái nền trước khi làm:** `NOT_LISTENING` (xác minh bằng `Get-NetTCPConnection -LocalPort 3001`).
- **Quyết định của Chủ dự án:** Đã hỏi qua `ask_question` và nhận phê duyệt khởi chạy `npx vite --port 3001 --strictPort` từ `D:\Documents\projects\axo-geometry-library\frontend` và giữ chạy ngầm xuyên suốt + sau khi hoàn tất.
- **Định danh tiến trình bảo toàn:** TaskId `3ef24255-0976-432d-b0af-48ebb7f2067e/task-83120`, Windows PID `5220`, không hề bị tắt, kill hay khởi động lại trong toàn bộ phiên làm việc (`PORT_3001_PRESERVED`).
- **Kiểm tra đáp ứng 4 tuyến:** `/`, `/gioi-thieu`, `/gioi-thieu?preview=v1.4` và `/app` đều phản hồi HTTP `200`.

---

## H. Approval

Owner Approval: `PENDING_OWNER_REVIEW`
