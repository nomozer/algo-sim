# AXO LANDING V1.8 — SPATIAL EDITORIAL 2.0 | VISUAL ARCHITECTURE, GEOMETRY & EXPERIENCE REDESIGN

> **Tuyến xem trước cô lập:** `/gioi-thieu?preview=v1.4` ([LandingPreviewV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingPreviewV14.tsx))
> **Nhánh làm việc:** `feat/axo-geometry-library-verification` · **Trạng thái nghiệm thu:** `OWNER_APPROVAL = PENDING_OWNER_REVIEW`

---

## 1. Baseline Git

- **Commit gốc trước khi triển khai V1.8 (`git rev-parse HEAD`):** `b84e19f5c018eb8a10d1f1f5003e16cfca187251` (`feat(landing): refine v1.7 storytelling stage, cube camera preset, and spatial editorial rhythm`)
- **Chuỗi 5 commit Landing gần nhất trước wave:**
  - `b84e19f5c` — `feat(landing): refine v1.7 storytelling stage, cube camera preset, and spatial editorial rhythm`
  - `762402943` — `feat(landing): refine v1.7 spatial storytelling, showcase stage, and coupled geometry`
  - `aaf180072` — `feat(landing): spatial visual system gallery, continuous light ground, and closing hexagon polish`
  - `b99311d3f` — `feat(landing): refine V1.6 header hover, spatial hero, scroll storytelling, and studio demo`
  - `b769a554f` — `feat(landing): AXO Landing V1.6 visual quality recovery on isolated preview`
- **Biên giới `OWNERSHIP_BLOCKED`:** Toàn bộ thay đổi dở trên working tree ngoài Landing (`backend/**`, `docs/EVIDENCE_INDEX.md`, `frontend/index.html`, `frontend/package*.json`, `frontend/public/**`, hệ Workspace/Classroom và các test không thuộc Landing) được giữ nguyên tuyệt đối, không restore, không stage và không commit.

---

## 2. Các nguồn tham khảo đã xác minh

1. **`DESIGN.md` & `frontend/src/styles/tokens.css` (OBSERVED trong kho mã):**
   - `tokens.css`: `--canvas: #ffffff`, `--canvas-soft: #f6f5f4`, `--ink: #31302e`, `--ink-secondary: #615d59`, `--primary: #0075de`, `--primary-active: #005bab`, `--accent-sky-tint: #dcebfa`, `--accent-orange: #dd5b00`, `--accent-orange-deep: #793400`.
   - `DESIGN.md`: định hướng Notion-calm sáng sạch, tối giản viền hộp trang trí `1px`, giữ font chữ nội dung tối thiểu `16px`, ưu tiên tương phản và khoảng thở biên tập.
2. **Website tham khảo `https://bundaumayo.top/` (OBSERVED qua trình duyệt & phân tích ảnh cấu trúc):**
   - **OBSERVED:** Header thoáng trên nền sáng, CTA định hướng rõ ràng; Hero bố cục 2 cột mạnh với điểm nhấn typography kết hợp cụm hình khối trực quan; các cụm minh họa vệ tinh phân tầng độ sâu rõ quanh vật thể trung tâm; section chuyển đổi nhịp bằng đóng khung nền/panel có chủ đích; **Closing CTA** đặt trong **Accent Panel bo tròn nền sáng xanh/nhạt** nổi bật tách biệt hoàn toàn với Hero, kèm **Footer phẳng** đặt sát bên dưới không đường kẻ ngang chia cắt.
   - **INFERRED:** Cự ly thị giác giữa khối Accent Panel Closing và Footer đóng vai trò khóa nhịp cuộn trang, tạo điểm kết rõ ràng mà không cần lặp lại bộ khung Hero.
   - **NOT_VERIFIED:** Tốc độ frame thực tế của các chuyển động cuộn trên phần cứng di động vật lý của trang tham khảo ngoài môi trường trình duyệt kiểm tra.
3. **REA MCP (`rea-cdp-browser`, CDP port `9248`) & `design-taste-frontend` (`lint.mjs`, `inspect.mjs`):**
   - Kiểm tra BEFORE trên `http://[::1]:3001/gioi-thieu?preview=v1.4` (`rea-before.json`, `before_localhost_3001.png`, Chrome `151.0.7922.34`).
   - Kiểm tra AFTER qua `lint.mjs` (6 file V1.4 `.tsx`), `inspect.mjs` trên build production tại `http://localhost:4182/gioi-thieu?preview=v1.4` (`taste_after_prod/report.json`), và REA MCP AFTER (`rea-after.json`, `after_localhost_4182.png`, Chrome `158.0.8127.36`).

---

## 3. Những vấn đề được tìm thấy (`BEFORE` Audit)

Đối chiếu `landing_v1_8/before/*.png`, `landing_v1_8/perf/before_metrics.json` và `landing_v1_8/rea/before_localhost_3001.png`:

| Khu vực | Vấn đề thực tế ở `BEFORE` | Giữ lại | Khôi phục | Thiết kế lại |
|---|---|---|---|---|
| **Header** | Ổn định ở V1.7; giữ trạng thái pill mục đang xem, không nhảy width khi hover | Toàn bộ cấu trúc `LandingHeader.tsx` & scroll-spy `rAF` | — | — |
| **Hero** | 1) Chóp trên tách rời `detachedUpperCap` dùng sai 6 đỉnh `{S, M, E, N, P, F}` (bỏ sót đỉnh `C` dù mặt phẳng `x + y + 2z = 6` đi qua `M, N, P`, phía chứa `S` và `C` phải có **7 đỉnh**); 2) Cạnh `S.ABCD` vẽ 1 nét liền xuyên sai qua mặt phẳng `(MNP)`; 3) Góc nhìn `[10.8, 5.9, -7.2]` khiến vệ tinh 2 & 3 bám gần biên phải và ở `1920×1080` tiêu đề Story hé nhẹ ở đáy fold; 4) Vòng cam `"hình dung"` chạm sát dấu thanh/đáy chữ `g` | Bố cục 2 cột `S.ABCD` + 3 vệ tinh, typography 2 dòng, 2 CTA capsule, 0 đáp án | Cự ly vệ tinh thoáng & `min-height` khóa fold `1920×1080` | Toán học `detachedUpperCap` 7 đỉnh `{S, C, M, E, N, P, F}`, thuật toán cắt nửa không gian `splitEdgeAtPlane`, vòng `circle` SVG nới khoảng dấu |
| **Storytelling** | 1) Đường dẫn cuộn `224svh` kéo dải cuộn dài hơn cần thiết; 2) Toàn sân khấu hòa phẳng trên `--axo-sp-paper` thiếu đĩa sân khấu sáng sạch; 3) Biên mặt phẳng `STORY_PLANE_QUAD = 0.34` quá rộng/đậm và đoạn `MQ`/`PQ` mặt khuất vẽ đặc như mặt trước; 4) Mobile `<=480px` summary chỉ `14px` (`0.875rem`) | Mạch 4 chặng tất định, `prismBuild = 1`, khóa `Q` chặt ở Chặng 3–4, thẻ `Hình thật thiết diện` | Độ sáng & phân tầng nền sạch trên nền giấy ấm | Rút runway xuống `192svh`/`182svh`, đĩa sân khấu sứ trắng `--canvas` bo `24px`, viền trái công thức bỏ đóng khung, cắt gọt mặt phẳng `0.24` & nét đứt `6 4` cho cạnh khuất, chữ `>= 16px` |
| **Interactive Demo** | 1) Cạnh chóp/lập phương dựng thành 1 nét liền duy nhất xuyên qua mặt phẳng cắt khi xoay 360°; 2) Nút chọn mẫu/bước còn viền box `1px`; 3) Khung highlight `"thiết diện thật."` sát dấu chấm và dấu nặng; 4) Mô tả bước dưới `16px` | 2 mẫu `S.ABCD` & `ABCD.A′B′C′D′`, `computeShowcaseCameraPreset`, khóa cử chỉ chạm `gestureMode`, nút xoay/reset | Bố cục editorial mở 5 thành phần | Tách từng cạnh tại `(secNormal, secOffset)` thành `posSolidLine`/`negSolidLine` tự đổi `renderOrder` theo hướng camera trong `SpatialSceneCanvas`; bỏ viền pill `1px`; mở rộng `highlight` `polygon` |
| **Closing** | 1) Đặt trên nền `--axo-sp-paper` phẳng không viền/panel nên giống biến thể lặp lại của Hero; 2) Cạnh lăng trụ lục giác và mặt phẳng cắt xung đột `renderOrder` gây xuyên nét; 3) Chưa có vệ tinh/mảnh thiết diện tách rời cân đối; 4) Khoảng hở tới Footer tới `96px` trên desktop (`before_metrics.json`) | Lăng trụ lục giác đều `R=1.62, H=2.88` + nắp nâng `0→0.22` + kịch bản tự dừng 0 RAF | Cân bằng thị giác với Hero mà không lặp lại khuôn | Panel Accent bo `32px` (`24px` mobile) nền `--axo-sp-closing-panel` từ `tokens.css`, sửa `renderOrder` (`lower=4, plane=5, secFill=6, upper=8`), bổ sung **Companion 3** lục giác trích rời `extractedHexGroup` |
| **Footer** | 1) Ngăn bằng `footerBorderTop = 1px` hairline cắt ngang container; 2) Cách panel Closing tới `96px` trên desktop / `40px` trên mobile | Bộ liên kết 4 mục + nút `#btn-landing-footer-top` | Bố cục 2 cột phẳng tối giản | Gỡ bỏ hoàn toàn `border-top: 0px`, kéo nhịp panel-đến-footer khít xuống `28px` desktop (`25px` `1024`, `20px` `768`, `18px` mobile) |

Ngoài ra, kiểm tra `before_metrics.json` phát hiện lỗi phân cấp cỡ chữ trên màn hình nhỏ `360×800` và `320×568`:
- `320×568` (`BEFORE`): `heroH1Px = 26.88px` **nhỏ hơn** `storyH2Px / demoH2Px / closingH2Px = 29.6px`!
- `360×800` (`BEFORE`): `heroH1Px = 28.08px` **nhỏ hơn** `storyH2Px = 29.6px`!

---

## 4. Lý do chọn phương án thiết kế (`AXO Spatial Editorial 2.0`)

1. **Từ “giấy xám phẳng + nhiều đường viền” sang “phân lớp bề mặt không viền `tokens.css`”:**
   Thay vì dùng viền `1px` để chia ô pill/button/footer, V1.8 phân cấp bằng sắc độ nền trực tiếp từ `--canvas` (`#ffffff`), `--canvas-soft` (`#f6f5f4`), `--accent-sky-tint` (`#dcebfa`) qua `color-mix` (`--axo-sp-closing-panel`), giữ toàn bộ CSS/TSX **0 màu `#hex` literal**.
2. **Đóng vai “phần kết có điểm nhấn” học hỏi cấu trúc `bundaumayo.top`:**
   Trên nền giấy ấm `--axo-sp-paper`, `.axo-v14-closing-shell` đóng thành một Accent Panel bo góc `32px` mang sắc sứ xanh nhạt riêng biệt, kết hợp lăng trụ lục giác + Companion 3, nối xuống Footer phẳng không đường kẻ chỉ `28px` bên dưới.
3. **Toán học đúng trước khi tinh chỉnh đồ họa (`Correct Geometry → Strong Composition`):**
   Không che giấu lỗi hình học bằng shader; mọi cạnh cắt qua mặt phẳng đều tách đoạn thực sự tại giao điểm với mặt phẳng, mọi đa diện tách rời đều tuân thủ đúng bất đẳng thức nửa không gian.

---

## 5. Danh sách thành phần giữ lại

- [LandingHeader.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeader.tsx): header nổi, thanh chọn `#landing-nav` chống nhảy width (`font-weight: 500`, `::after`), `<TopNavAccount />`, ngăn kéo di động 5 mục kèm `Escape` & focus trap.
- [LandingInteractiveDemo.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingInteractiveDemo.tsx): cấu trúc chọn mẫu 2 bài toán, cột editorial 5 phần, thanh dock 4 bước.
- [LandingClosingV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingV14.tsx): cấu trúc Closing CTA + Footer 4 liên kết + `#btn-landing-footer-top`.
- [landing-geometry-data.ts](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing-geometry-data.ts): dữ liệu tọa độ chuẩn hóa `LANDING_SHOWCASE_SAMPLES`, `LANDING_PRISM_STORY_SPEC`, `computeShowcaseCameraPreset`.
- [LandingPreviewV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingPreviewV14.tsx), toàn bộ trang `/` và `/gioi-thieu` (V1.2.2 `"prod"`) và `/app` (Workspace).

---

## 6. Danh sách thành phần đã khôi phục

- **Nhịp nền sáng-ấm luân phiên V1.7 kết hợp độ tương phản mới:** giữ đúng nhịp `Hero (#FFFFFF) → Story (#F6F5F4) → Demo (#FFFFFF) → Closing (#F6F5F4 với Panel sứ xanh) → Footer (#F6F5F4)` đã được chứng minh sạch trên cả desktop lẫn mobile.
- **Kịch bản Storytelling & Gesture Lock:** giữ `prismBuild = 1` ở Chặng 1, khóa điểm `Q` ở Chặng 3–4, `maxVisibleChapters = 1` và `gestureMode` phân tách vuốt dọc/xoay 3D trên thiết bị cảm ứng.
- **0 đáp án số học & 0 RAF khi dừng:** bảo toàn triệt để trạng thái `heroIdleRaf = 0`, `closingIdleRaf = 0`, `leakedAnswers = []`.

---

## 7. Danh sách thành phần thiết kế lại

1. **[LandingHeroV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroV14.tsx):** góc camera `[11.8, 6.0, -5.2]` (`scaleDist` `1.18/1.16`), toán học `detachedUpperCap` 7 đỉnh `{S, C, M, E, N, P, F}`, thuật toán `splitEdgeAtPlane` + `secEdgeBindings`, 9 nhãn chu vi `projectAnchors`, cập nhật `<HeroFallbackSvg />` đồng bộ.
2. **[LandingStorytellingV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingStorytellingV14.tsx) + [landing.css](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing.css):** sân khấu đĩa sứ trắng `--canvas` bo `24px`, runway gọn `192svh`/`182svh`, mặt phẳng cắt `0.24`, nét đứt `6 4` cạnh khuất.
3. **[LandingHeroScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroScene3D.tsx):** chia đôi cạnh tại `(secNormal, secOffset)` thành `posSolidLine` / `negSolidLine` với `renderOrder` động `8` vs `3` theo nửa phía camera khi xoay 360°, làm dịu viền thiết diện mặt khuất (`hostFront`) trong nhánh `presentation === "v14"`.
4. **[LandingClosingScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingScene3D.tsx) + [landing.css](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing.css):** Accent Panel bo `32px` `--axo-sp-closing-panel`, lăng trụ lục giác `baseScale = 0.9`, phân lớp `renderOrder`, thêm Companion 3 `extractedHexGroup` từ `computeClosingExtractedHexagon2D()` + `<ClosingFallbackSvg />`, tháo bỏ `border-top` của Footer.
5. **[AnnotatedHeading.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/AnnotatedHeading.tsx) + [landing.css](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing.css):** mở rộng cung vòng cam `"hình dung"` và khung xanh `"thiết diện thật."` thoáng dấu tiếng Việt; sửa toàn bộ thang chữ 6 bậc (`h1 > h2` tại mọi bề rộng `320px–1920px`, nội dung `>= 16px`).

---

## 8. Các thay đổi hình học và bằng chứng kiểm chứng

1. **Sửa lỗi toán học chóp trên tách rời (`LandingHeroV14.tsx`, `landing-hero-visual-lifecycle.test.tsx`):**
   - Mặt phẳng `(MNP)` của bài `S.ABCD` có phương trình nửa không gian $x + y + 2z - 6 \ge 0$ về phía đỉnh $S$. Kiểm tra trực tiếp các đỉnh gốc: $S$ và $C$ đều thuộc nửa không gian chứa $S$, cùng 5 giao điểm ngũ giác $M, E, N, P, F$ nằm trên mặt phẳng ($= 0$).
   - V1.8 cập nhật `capIds = ["S", "C", "M", "E", "N", "P", "F"]`, `capFaceLoops` dựng từ `upperFaces`, và 6 cạnh cắt thực `[S,M], [S,E], [S,C], [S,F], [C,N], [C,P]`.
   - **Kiểm chứng:** `npx vitest run src/components/__tests__/landing-hero-visual-lifecycle.test.tsx` kiểm tra tọa độ cả 7 đỉnh thỏa mãn $x + y + 2z - 6 \ge -10^{-6}$ và đủ cạnh đồng dạng → **`4/4` PASSED**.
2. **Che khuất theo nửa không gian chống xuyên nét (`LandingHeroV14.tsx`, `LandingHeroScene3D.tsx`):**
   - Hero: `splitEdgeAtPlane` chia cạnh tại mặt cắt thành `lowerSolid` (`renderOrder = 4`) và `upperSolid` (`renderOrder = 8`), `secEdgeBindings` đối chiếu hướng pháp tuyến mặt kề để vẽ nét liền/đứt chính xác.
   - Interactive Demo (`presentation === "v14"`): `splitSegmentAtPlane` tạo `posSolidLine` và `negSolidLine`; mỗi frame kiểm tra `camOnPosSide = rig.secNormal.dot(camera.position) >= rig.secOffset` để đặt nửa phía camera lên `renderOrder = 8` và nửa sau xuống `renderOrder = 3`, kết hợp `faceFrontFlags` cho viền thiết diện (`renderOrder = 7` / `6`).
3. **Storytelling mặt cắt & cạnh khuất (`LandingStorytellingV14.tsx`):**
   - Thu gọn `STORY_PLANE_QUAD` về lề `0.24`, giảm `fillOpacity = 0.13`, `strokeOpacity = 0.54`, và dùng `traceHostFaceIdx` phân biệt cạnh trên mặt nhìn thấy (nét liền `0.96`) với cạnh mặt khuất (nét đứt `6 4`).
4. **Closing CTA & Companion 3 (`LandingClosingScene3D.tsx`):**
   - Căn camera `baseScale = 0.9`, `lookVec = [0.24, 0.04, 0]`, phân tầng `lower = 4`, `plane = 5`, `secFill = 6`, `secBorder = 7|6`, `upper = 8`, `dots = 9`, và gắn `extractedHexGroup` (`computeClosingExtractedHexagon2D()`) ở góc phải trên hướng về camera, đồng bộ với `<ClosingFallbackSvg />`.

---

## 9. Các thay đổi typography, màu sắc và bố cục

- **Hệ phân cấp tiêu đề (`h1 > h2` across `320px–1920px`):**
  - `1920×1080`: `h1 = 52.8px`, `h2 = 39.2px`
  - `1440×900`: `h1 = 49.68px`, `h2 = 39.2px` (BEFORE: `47.808px` / `40px`)
  - `1366×768`: `h1 = 47.127px`, `h2 = 37.565px`
  - `1024×768`: `h1 = 36px`, `h2 = 28.16px`
  - `768×1024`: `h1 = 36px`, `h2 = 24px`
  - `390×844`: `h1 = 30.42px`, `h2 = 24px` (BEFORE: `30.42px` / `29.6px`)
  - `360×800`: `h1 = 28.08px`, `h2 = 24px` (khắc phục lỗi BEFORE `28.08px < 29.6px`)
  - `320×568`: `h1 = 28px`, `h2 = 24px` (khắc phục lỗi BEFORE `26.88px < 29.6px`)
- **Cỡ chữ nội dung `>= 16px` & thoáng dấu tiếng Việt:**
  - `.axo-v14-story-lead`, `.axo-v14-closing-lead`, `.axo-v14-story-chapter-summary`, `.axo-sp-demo-workbench.is-v14 .axo-sp-demo-step-desc` đều đạt tối thiểu `1rem` (`16px`) ở cả desktop lẫn `<= 480px`. `inspect.mjs` xác nhận `body.size = 16.1px` (`1440`), `16px` (`768`), `16px` (`390`), `smallText = 0`.
  - `.axo-v14-hero-title` đặt `line-height: 1.26` (`1.28` mobile); `AnnotatedHeading.tsx` điều chỉnh `circle` và `highlight` `polygon` để tránh cắt dấu nặng/mũ ở `"hình dung"` và `"thiết diện thật."`.
- **Màu sắc & Không viền thừa:**
  - `0` mã màu `#hex` literal trong `landing.css` và các file `.tsx` V1.4; `0` `var(--` trong `.tsx`.
  - `.axo-v14-closing-shell` sử dụng `--axo-sp-closing-panel` từ `color-mix(...)` trên `--accent-sky-tint` và `--canvas` → render ra `color(srgb 0.931373 0.960784 0.990196)`, bo `32px` desktop / `24px` mobile.
  - Gỡ viền `1px` của `.axo-sp-sample-pill`, `.axo-sp-demo-step-dock` và `border-top` của `.axo-v14-footer-shell` (`0px`).
  - Nâng `min-height` `.axo-v14-hero-shell` lên `clamp(520px, calc(100svh - 144px), 940px)` giữ fold `1920×1080` và `1440×900` sạch bóng tiêu đề Story ở đáy màn hình; thu hẹp khoảng hở Closing-Footer từ `96px → 28px` (desktop) và `40px → 18px` (mobile).

---

## 10. Kết quả responsive (8 viewports)

Số liệu trích nguyên văn từ `landing_v1_8/perf/after_metrics.json`:

| Viewport | `overflowX` | `CLS` | `heroH1Px` / `storyH2Px` | Gap Closing→Footer (`px`) | Story Fwd / Rev / `maxVisible` | SVG cắt (`Story` / `Hero`) | Demo `S` đè hint | MinBtn Sample/Step (`px`) | Settled Idle RAF (`Hero`/`Closing`) | `pageErrors` |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1920×1080` | `0` | `0` | `52.8 / 39.2` | `28` | `0,1,2,3 (Q:F,F,T,T)` / `2,1,0` / `1` | `0 / 0` | `false` | `40 / 40` | `0 / 0` | `[]` |
| `1440×900` | `0` | `0` | `49.68 / 39.2` | `28` | `0,1,2,3 (Q:F,F,T,T)` / `2,1,0` / `1` | `0 / 0` | `false` | `40 / 40` | `0 / 0` | `[]` |
| `1366×768` | `0` | `0` | `47.127 / 37.565` | `28` | `0,1,2,3 (Q:F,F,T,T)` / `2,1,0` / `1` | `0 / 0` | `false` | `40 / 40` | `0 / 0` | `[]` |
| `1024×768` | `0` | `0` | `36 / 28.16` | `25` | `0,1,2,3 (Q:F,F,T,T)` / `2,1,0` / `1` | `0 / 0` | `false` | `40 / 40` | `0 / 0` | `[]` |
| `768×1024` | `0` | `0` | `36 / 24` | `20` | `0,1,2,3 (Q:F,F,T,T)` / `2,1,0` / `1` | `0 / 0` | `false` | `40 / 44` | `0 / 0` | `[]` |
| `390×844` | `0` | `0` | `30.42 / 24` | `18` | `0,1,2,3 (Q:F,F,T,T)` / `2,1,0` / `1` | `0 / 0` | `false` | `44 / 44` | `0 / 0` | `[]` |
| `360×800` | `0` | `0` | `28.08 / 24` | `18` | `0,1,2,3 (Q:F,F,T,T)` / `2,1,0` / `1` | `0 / 0` | `false` | `44 / 44` | `0 / 0` | `[]` |
| `320×568` | `0` | `0` | `28 / 24` | `18` | `0,1,2,3 (Q:F,F,T,T)` / `2,1,0` / `1` | `0 / 0` | `false` | `44 / 44` | `0 / 0` | `[]` |

- Khoảng thoáng giữa thẻ `Hình thật thiết diện` và nhãn đỉnh lăng trụ đạt `30px` (`1920–1366`), `23px` (`1024`), `19px` (`768`), `15px` (`390`), `13px` (`360`), `11px` (`320`).
- `leakedAnswers = []` trên tất cả 8 viewport.

---

## 11. Kết quả kiểm thử chức năng, hiệu năng & chống hồi quy

- **Tương tác Header & Mobile Drawer (`after_metrics.json`):**
  - `1440×900` hover sang mục điều hướng thứ 2: `maxHoverWidthShiftPx = 0`, `hoverStateOnSecondLink = "other"`.
  - `390×844` Mobile Drawer: mở `aria-expanded = "true"`, bấm `Escape` đóng (`"false"`) và trả focus về `focusedIdAfterEscape = "btn-landing-mobile-menu"`.
- **Tương tác Demo 3D (`after_metrics.json`):**
  - Phím mũi tên `ArrowLeft` chuyển tab bước (`stepAfterKey = "true"`), kéo xoay 3D hiện nút đặt lại (`resetVisibleAfterDrag = true`), bấm `#btn-landing-demo-reset` ẩn nút (`resetHiddenAfterClick = true`), bấm `#btn-landing-footer-top` cuộn về đầu trang (`scrollAfterTopBtn <= 41px`).
- **Fallback `?no_webgl=1` & `prefers-reduced-motion` (`after_metrics.json`):**
  - `?no_webgl=1`: `canvases = 0`, `heroSvg = true`, `closingSvg = true` (đồng bộ 7 đỉnh Hero & Companion 3 Closing).
  - `prefers-reduced-motion`: `heroBeat = "section-settled"`, `visibleStoryChapters = 4`, `closingBeat = "exploration-settled"`.
- **Bảo toàn Production & Workspace (`after_metrics.json`):**
  - `/` (`rootProd`): `hasProdHero = true`, `hasV14Hero = false`, `overflowX = 0`.
  - `/gioi-thieu` (`gioiThieuProd`): `hasProdHero = true`, `hasV14Hero = false`, `overflowX = 0`.
  - `/app` (`workspaceCheck`): `mounted = true`, `overflowX = 0`.
- **Kiểm định kỹ thuật & Visual QA:**
  - `npx tsc -b`: exit `0`.
  - `npx vite build`: exit `0` (`built in 4.96s`).
  - `design-taste-frontend/scripts/lint.mjs` trên 6 file V1.4 `.tsx`: **`RESULT: 0 FAIL, 0 WARN`**.
  - `design-taste-frontend/scripts/inspect.mjs` tại `http://localhost:4182/gioi-thieu?preview=v1.4` (`1440, 768, 390` + `--film`): `0 FAIL` ở `[body-size]`, `[outlined-box]`, `[hairline]`, `[low-contrast]`, `[off-centre]`, `[edge-text]`, `[still-page]` (`29` phần tử chuyển động ở `1440`); chỉ báo `few-pictures` & `no-footage` do toàn trang dùng WebGL 3D & SVG động thay vì ảnh stock/video.
  - **Bộ test Vitest đầy đủ (`npx vitest run --testTimeout=20000`, sau mọi chỉnh sửa code/CSS/`CODE_INDEX.md`):** **`191 passed (191)` files · `2250 passed (2250)` tests** (`133.59s`), bao gồm `src/code-index-sync.test.ts` và toàn bộ suite Landing + Workspace/3D Scene.
  - **Kiểm tra kiến trúc tài liệu (`python backend/scripts/audit_docs_information_architecture.py --json`):** `OWNERSHIP.valid = true`, `LINKS.valid = true` (`684` liên kết, `0` gãy), `DOCS_LAYOUT.valid = true`, `STATUS_LEDGER.valid = true`, `EVIDENCE_INDEX.valid = true`, `OPEN_ISSUES.valid = true`, `CANONICAL_NEXT_ACTION.valid = true`, `STABLE_MUTABLE.valid = true`, `SECRET_SCAN.valid = true` (`0` leak); `CODE_INDEX.stale_paths` chỉ giữ đúng 4 đường dẫn lớp học `OWNERSHIP_BLOCKED` tồn tại từ trước (`LiveClassDock.tsx`, `LiveClassStrip.tsx`, `MonitorView.tsx`, `classroom-sync.ts`).

---

## 12. So sánh ảnh Before / After & Video kiểm chứng

Toàn bộ artifact lưu tại thư mục artifact phiên làm việc `C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\landing_v1_8\`:

| Hạng mục | `BEFORE` | `AFTER` | Điểm cải thiện đã xác minh |
|---|---|---|---|
| **Hero Desktop (`1920×1080` / `1440×900`)** | [before_hero_1920x1080.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_hero_1920x1080.png) · [before_hero_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_hero_1440x900.png) | [after_hero_1920x1080.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_hero_1920x1080.png) · [after_hero_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_hero_1440x900.png) · [desktop-fold.jpg](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/taste_after_prod/desktop-fold.jpg) | Sửa chóp trên 7 đỉnh `{S,C,M,E,N,P,F}`, cắt cạnh `splitEdgeAtPlane` hết xuyên mặt phẳng, hết lấp ló tiêu đề Story ở đáy fold `1920×1080` & `1440×900` |
| **Hero Mobile (`390×844` / `320×568`)** | [before_hero_390x844.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_hero_390x844.png) · [before_hero_320x568.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_hero_320x568.png) | [after_hero_390x844.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_hero_390x844.png) · [after_hero_320x568.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_hero_320x568.png) · [mobile-fold.jpg](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/taste_after_prod/mobile-fold.jpg) | `h1` (`28px`) > `h2` (`24px`), vòng cam thoáng dấu, không cắt hình/nhãn |
| **Storytelling Chặng 1 & Chặng 4** | [before_story_s1_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_story_s1_1440x900.png) · [before_story_s4_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_story_s4_1440x900.png) | [after_story_s1_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_story_s1_1440x900.png) · [after_story_s4_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_story_s4_1440x900.png) | Đĩa sân khấu `--canvas` `24px`, lăng trụ Chặng 1 sạch điểm `M,N,P` (chưa lộ `Q`), nét đứt khuất rõ ở Chặng 4 |
| **Demo Chóp & Lập phương (`1440×900`)** | [before_demo_pyramid_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_demo_pyramid_1440x900.png) · [before_demo_cube_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_demo_cube_1440x900.png) | [after_demo_pyramid_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_demo_pyramid_1440x900.png) · [after_demo_cube_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_demo_cube_1440x900.png) | Phân mặt trước/sau theo camera 360°, bỏ viền pill, khung xanh `"thiết diện thật."` thoáng |
| **Closing CTA & Footer (`1440×900` / `390×844`)** | [before_closing_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_closing_1440x900.png) · [before_footer_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/before/before_footer_1440x900.png) | [after_closing_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_closing_1440x900.png) · [after_footer_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_footer_1440x900.png) · [after_closing_390x844.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_closing_390x844.png) | Accent Panel `--axo-sp-closing-panel` bo `32px`, Companion 3 lục giác tách rời, khoảng hở tới Footer giảm `96px → 28px`, gỡ `border-top` |
| **Fallback `?no_webgl=1` & REA MCP** | [before_localhost_3001.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/rea/before_localhost_3001.png) | [after_fallback_hero_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_fallback_hero_1440x900.png) · [after_fallback_closing_1440x900.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/after/after_fallback_closing_1440x900.png) · [after_localhost_4182.png](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/rea/after_localhost_4182.png) | SVG fallback đồng bộ 7 đỉnh Hero & Companion 3; REA MCP xác nhận `465` DOM nodes |
| **Video chuyển động `AFTER`** | — | [01_after_hero_story_desktop.webm](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/videos/after/01_after_hero_story_desktop.webm) · [02_after_demo_closing_footer_desktop.webm](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/videos/after/02_after_demo_closing_footer_desktop.webm) · [03_after_mobile_flow_390x844.webm](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_8/videos/after/03_after_mobile_flow_390x844.webm) | Đã ghi cả cuộn xuôi/ngược Story, đổi mẫu + bước Demo, Closing 3D + Footer + mobile `390×844` (`881KB`, `1.58MB`, `895KB`) |

---

## 13. Những lỗi chưa xử lý hoặc chưa xác minh (`NOT_PHYSICAL_MOBILE` & Giới hạn)

1. **`NOT_PHYSICAL_MOBILE`:** Toàn bộ kiểm chứng cảm ứng (`390×844`, `360×800`, `320×568`) và render 3D chạy trên **Chromium + SwiftShader ANGLE giả lập viewport/touch**; tốc độ WebGL và độ nhạy cảm ứng trên iPhone/Android phần cứng thật là **`NOT_VERIFIED`**.
2. **`consoleErrors` `/api/auth/me` khi backend tắt:** Khi chạy preview frontend độc lập không bật backend `:8000`, trình duyệt ghi nhận request `/api/auth/me` trả về HTTP `500` ở console (hiện tượng có sẵn của môi trường offline, `pageErrors = []` ở mọi viewport).
3. **`inspect.mjs` (`few-pictures`, `no-footage`):** Quy tắc chung cho site biên tập vẫn báo thiếu ảnh raster (`0` ảnh chụp) và `<video>` do Axo chủ ý thay bằng live Three.js WebGL & interactive SVG.
4. **Điểm cuối REA AFTER (`4182` thay cho `3001`):** Sau khi bộ chụp `AFTER` chính thức trên `localhost:3001` hoàn tất (`14:35:09`), tiến trình `3001` ngoài phạm vi đã dừng ngoài ý muốn trước bước REA AFTER (`14:48:17`); theo quy tắc không tự chiếm/restart `:3001`, lượt REA MCP AFTER chạy trên `vite preview --port 4182` từ cùng mã nguồn đã build và được dọn sạch tiến trình tạm ngay sau khi chụp.

---

## 14. Git diff và cấu trúc Commit đóng gói

Chỉ **9 file thuộc allowlist V1.8** được đưa vào commit trên nhánh `feat/axo-geometry-library-verification` (lưu ý `CODE_INDEX.md` cũng chỉ chỉnh sửa đúng dòng `1983`):

- `frontend/src/components/landing/AnnotatedHeading.tsx` (`+4/-4`)
- `frontend/src/components/landing/landing.css` (`+143/-143` trong tổng `286` biến động định kiểu, 0 màu hex)
- `frontend/src/components/landing/LandingHeroV14.tsx` (`505` dòng thêm/sửa hợp nhất 7 đỉnh & cắt nửa không gian)
- `frontend/src/components/landing/LandingStorytellingV14.tsx` (`+16/-5`)
- `frontend/src/components/landing/LandingHeroScene3D.tsx` (`177` dòng thêm/sửa tách cạnh nửa không gian động 360°)
- `frontend/src/components/landing/LandingClosingScene3D.tsx` (`173` dòng thêm/sửa `renderOrder` + Companion 3)
- `frontend/src/components/__tests__/landing-hero-visual-lifecycle.test.tsx` (`18` dòng cập nhật kiểm chứng 7 đỉnh)
- `docs/CODE_INDEX.md` (chỉ dòng `1983`)
- `docs/evaluation/landing/AXO-LANDING-V18-VISUAL-ARCHITECTURE-REPORT.md`

Tổng diff mã/test trước commit: `7 files changed, 781 insertions(+), 407 deletions(-)`. Không merge `main`, không push remote, không động vào các file `OWNERSHIP_BLOCKED`.

---

## 15. Xác nhận trạng thái server 3001

- Trong toàn bộ quá trình chỉnh sửa mã, build, và chạy đầy đủ bộ chụp/đo 8 viewport + 3 video (`after_metrics.json`, kết thúc lúc `14:35:09`), tiến trình Vite dev server ngoài `http://localhost:3001` (`PID 11148`) phản hồi **HTTP `200`** trên cả 4 tuyến (`/`, `/gioi-thieu`, `/gioi-thieu?preview=v1.4`, `/app`) và **không bao giờ bị kill hoặc restart bởi tác vụ**.
- Sau `14:48:17`, khi kiểm tra cho bước REA AFTER, hệ thống ghi nhận `PID 11148` đã tự thoát từ bên ngoài (`HTTP 000` trên `[::1]:3001`, `localhost:3001`, `127.0.0.1:3001`). Tuân thủ tuyệt đối §1.2, phiên không chiếm cổng `3001` và không tự ý khởi động lại server trên cổng `3001`; các tác vụ kiểm thử tạm trên cổng `4182` và `9248` đã được dọn sạch hoàn toàn.

---

## 16. Các vấn đề cần Owner nghiệm thu

1. Xác nhận bản thiết kế **AXO Spatial Editorial 2.0** tại `/gioi-thieu?preview=v1.4` (bật lại `npm run dev -- --port 3001` nếu phiên dev ngoài đã đóng): Hero `S.ABCD` + 3 vệ tinh với chóp 7 đỉnh & cắt nửa không gian, Storytelling đĩa sứ trắng 4 chặng, Interactive Demo cắt cạnh 360° cho Chóp & Lập phương, và Closing Accent Panel xanh sứ bo `32px` nối Footer phẳng.
2. Cho ý kiến liệu đã đạt yêu cầu để mở khóa hợp nhất V1.4 thay thế tuyến production `/` và `/gioi-thieu` trong đợt tiếp theo hay cần tinh chỉnh thêm.

**`OWNER_APPROVAL = PENDING_OWNER_REVIEW`**
