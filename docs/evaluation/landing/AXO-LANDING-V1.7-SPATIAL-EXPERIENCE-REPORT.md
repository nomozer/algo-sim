# AXO LANDING V1.7 — SPATIAL EXPERIENCE REDESIGN & QUALITY REPORT

> **Scope:** Cô lập trên tuyến xem trước `/gioi-thieu?preview=v1.4` (`LandingPreviewV14.tsx`, nhánh `feat/axo-geometry-library-verification`) · **Baseline `HEAD`:** `aaf180072a32c4efbbb07684d4c51dfce7b57705`
> **Production Routes (`/`, `/gioi-thieu`):** Giữ nguyên V1.2.2 (`"prod"`) · **Workspace (`/app`) & `backend/**`:** Bảo toàn nguyên trạng
> **Persistent Dev Server:** `http://[::1]:3001` (`PID 16060`, lắng nghe cổng `3001`, không tắt/restart trong toàn bộ phiên)
> **Owner Approval:** `OWNER_APPROVAL = PENDING_OWNER_REVIEW`

---

## 1. Phạm vi thay đổi & Bảo toàn Allowlist

Chỉ chỉnh sửa **8 tệp mã nguồn & kiểm thử thuộc danh sách V1.4 + 2 tệp tài liệu**, tuyệt đối không chạm các tệp `OWNERSHIP_BLOCKED` (`backend/**`, `frontend/src/components/SimulationWorkspace.tsx`, `docs/EVIDENCE_INDEX.md`, hệ classroom/live-session):

- [LandingStorytellingV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingStorytellingV14.tsx) — tinh giản khung lặp, thêm thanh tiến trình liên tục `.axo-v14-story-rail-fill`, mở rộng khung SVG lên `680×500` (`scale = 72`), dựng cột tăng trưởng theo thông số (`isGrowingPillar`) kèm đường gióng nét đứt và hình trích đẳng cự `Hình thật (MNP)` tại Chặng 4.
- [LandingHeroScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroScene3D.tsx) — **chỉ** tinh chỉnh nhánh `presentation === "v14"` (nhánh `"default"` của V1.2.2 giữ nguyên): bóng tiếp xúc radial `createDemoContactTexture()`, đậm sắc mặt cắt thiết diện (`secFillMat.opacity = curSecFill * 0.44`), bù nâng khung `v14AspectScale` ở viewport hẹp (`320×568`).
- [landing-geometry-data.ts](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing-geometry-data.ts) — bổ sung/cập nhật góc máy gần hơn (~14%) `v14CameraPos` và chuẩn hóa `v14LookAt` qua đủ 4 bước của mẫu hình chóp `S.ABCD` và hình lập phương `ABCD.A′B′C′D′`.
- [LandingHeroV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroV14.tsx) — thay các vệ tinh rời trước đó bằng **3 vệ tinh liên kết trực tiếp với khối chóp `S.ABCD`** (`orthographicPlan`, `extractedPentagon`, `detachedUpperCap`) xoay mặt phẳng hướng trực diện camera và mở tuần tự `0.38 → 0.80`; đổi tên `createHeroContactTexture()` sạch từ `"shadow"`; đồng bộ `<HeroFallbackSvg />`.
- [LandingClosingScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingScene3D.tsx) — gỡ bỏ mảnh nổi thừa sát mép phải, đưa hình chiếu trực giao thiết diện xuống mặt đáy đồng trục, thêm hiệu ứng tách nhấc phần chóp trên `upperCapGroup` dọc pháp tuyến mặt cắt (`capLift: 0 → 0.22`), đổi tên `createClosingContactTexture()`, đồng bộ `<ClosingFallbackSvg />`.
- [landing.css](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing.css) — thống nhất sân khấu Demo trắng (`--canvas`) trên nền band `--axo-sp-paper` không hộp lồng hộp, thanh `.axo-v14-story-rail-fill`, hình trích `Hình thật (MNP)`, Closing nền trắng `--axo-sp-bg` chuyển xuống Footer `--axo-sp-paper` có `#btn-landing-footer-top`, tinh chỉnh `@media (max-width: 350px)`.
- [landing-hero-visual-lifecycle.test.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-hero-visual-lifecycle.test.tsx) & [landing-cta-motion.test.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-cta-motion.test.tsx) — cập nhật kiểm định toán học cho 3 vệ tinh liên kết `S.ABCD` và nhịp tách `capLift` (`0 → > 0.15`).
- [CODE_INDEX.md](file:///D:/Documents/projects/axo-geometry-library/docs/CODE_INDEX.md#L1983) (chỉ cập nhật dòng `1983`) và báo cáo này.

---

## 2. Nghiên cứu tham chiếu thực tế qua REA MCP & Hậu kiểm Live `localhost:3001`

### Tham chiếu bên ngoài (External Design & Motion Research)

| Nguồn | Trạng thái | Bằng chứng REA / Quan sát thực tế | Ứng dụng vào V1.7 |
| :--- | :--- | :--- | :--- |
| `https://pudding.cool/` | `VERIFIED_BY_REA` | HTTP `200` · `1440×900` · `domTotalNodes: 1554`, `resourcesCount: 74` · `list_targets: ev_65049e5db6814964de1df409f40cb870bbeeaf863ddc86fecad0150e349f572a`, `inspect_web_page: ev_8714031fee7b398ad902423a90e59407ebe48815b93ccb55c02e46e063c33c3f`, `capture_web_screenshot: ev_e635a4cdcca4ce3cbc6d033c3a1a662c6e373e1cb21dcf2f9899142de7356ba8` (`152,038` B, `sha256: 2b4901f9f51caa25a46ce7ef5b1d8f9162f1e851eabe1537da83fc280ca37bdf`, lưu tại `landing_v1_7/rea/rea_pudding.png`) | Nhịp chương scrollytelling sticky sạch chữ, không lặp meta thừa, một điểm nhấn thị giác duy nhất mỗi chặng |
| `https://bundaumayo.top/` | `VERIFIED_BY_REA` (phiên trước) | `dom: 705`, `widthShift: 0`, `overflow390: 0` · `inspect_ev: ev_5b6eb948463ed30f5be2f5542635f66108fbcb2d101c815a179ceb7d0bf24975`, `shot_ev: ev_5f45bbd14e9e47d4ff6945b64a17f3794b65791a799296c9aa73c9a9ae4cd730` (`420,328` B, `sha256: 34b13bbb4b359cf4fd3facb0ce66536186b41074c05ea5336758e93f18299296`) | Giãn khoảng thở nền sáng, tách band bằng sắc độ trắng / giấy đá thay cho viền hộp |
| `https://www.lusion.co/` | `VERIFIED_BY_REA` (phiên trước) | `dom: 1314`, `canvas: 3`, `svg: 41`, `widthShift: 0` · `inspect_ev: ev_d24f6a38ad425e13c6a53d89a18acbd0deabd11f745ea624494ac702024f8a37`, `shot_ev: ev_1f28362dcf9cbe7d01b7728c2aaf437f732aa49e41ac75a88390c54c6bcb0ced` (`721,550` B, `sha256: 1c9f679c69441ebc6999e95361818344ac8bdee7d7bb1c92300a2391b488aeb2`) | Vệ tinh 3D phân tầng chiều sâu hỗ trợ vật thể chính chứ không trang trí rời rạc |
| `https://rive.app/` | `VERIFIED_BY_REA` (phiên trước) | `dom: 2593`, `canvas: 32`, `widthShift: 0` · `shot_ev: ev_d8b185318f6b048b5fb7077dcc4a2c569b53b550a52fc8e2209862c33eac2af4` (`83,541` B, `sha256: 4ff0e59ec0f08a650326d1ec702c54d8c1e8bcd62adab02cd55fb272ea5ed5de`) | Chuyển động thanh chọn mượt không xô chữ khi di chuột |
| `https://www.figma.com/` | `VERIFIED_BY_REA` (phiên trước) | `dom: 1686`, `svg: 69`, `overflow390: 0` · `inspect_ev: ev_e8740f5632074b6947f1429a0529aeab38cea167a2a59df59e78517d026c1cb1` | Ngôn ngữ thẻ phẳng, sân khấu sản phẩm duy nhất tránh hộp lồng hộp |
| `https://tympanus.net/codrops/hub/` | `NOT_VERIFIED` | Cloudflare challenge (`HTTP 403`) — dừng kiểm tra đúng quy tắc anti-bot | Không trích dẫn đặc tả kỹ thuật từ nguồn này |

### Chụp kiểm chứng hậu chỉnh sửa trên live `http://[::1]:3001/gioi-thieu?preview=v1.4` (`landing_v1_7/rea/rea-after.json`)

- `list_browser_targets`: `ev_ad9d33b9b5b541bfad850b21bfd8ec7595814fa44d4cf0677091e084dad64ccd`
- `inspect_web_page`: `ev_555aa7b164b7de625e02726a3f140655dee3f0cd959c07e8855267ad97bad781` (`domTotalNodes: 451`, `resourcesCount: 20`, `consoleErrors: 0`)
- `capture_web_screenshot`: `ev_84ea6788ab0d1d48e9c2ec6de6a80956188661345e041c221bf4da42a745a130` (`1422×748`, `75,591` B, `sha256: 6363546e8f13d756c019289843c47814a9521de4b03ca3cb6812b4414dced067`, lưu tại `landing_v1_7/rea/after_localhost_3001.png`, đã mở kiểm tra trực tiếp).

---

## 3. Quyết định thiết kế & Cải tiến theo từng phần

1. **Hero (`LandingHeroV14.tsx`):**
   - Bảo toàn bố cục 2 dòng tiêu đề cân bằng + nét khoanh `"hình dung"`, 2 nút capsule, nền trắng tinh gọn và trình tự hữu hạn `3800ms` tự dừng (`0` RAF tĩnh).
   - Thay bát diện/lập phương ngẫu nhiên thành **3 vệ tinh liên kết trực tiếp với `S.ABCD`** (`orthographicPlan` hình chiếu bằng trực giao ngũ giác, `extractedPentagon` bản trích mặt cắt đẳng cự, `detachedUpperCap` phần chóp trên sau mặt cắt) xoay mặt phẳng hướng trực diện camera (`faceCameraQuat`) và xuất hiện lần lượt (`0.38 → 0.80`).
2. **Storytelling (`LandingStorytellingV14.tsx`):**
   - Loại bỏ dòng meta và khối readout trùng lặp; hợp nhất tiến trình cuộn thành 1 thanh `.axo-v14-story-rail` với thanh lấp đầy liên tục `.axo-v14-story-rail-fill` tương thích cuộn xuôi lẫn cuộn ngược.
   - Mở rộng sân khấu SVG lên `680×500` (`scale = 72`), bổ sung tăng trưởng trụ đứng + đường gióng nét đứt (`isGrowingPillar`), khóa giao điểm `Q` chặt chẽ chỉ xuất hiện từ Chặng 3 (`MN ∥ BC ⇒ PQ ∥ BC`), và bổ sung hình trích `Hình thật (MNP)` đẳng cự hình thang cân ở Chặng 4 không có số liệu/đáp án bài giải.
3. **Interactive Demo (`LandingInteractiveDemo.tsx`, `LandingHeroScene3D.tsx`, `landing-geometry-data.ts`):**
   - Gom `#landing-product-showcase` thành 1 sân khấu trắng `--canvas` đặt trên nền band `--axo-sp-paper`, phân cách cột điều khiển bên phải bằng 1 rãnh hairline duy nhất (triệt tiêu hộp lồng hộp).
   - Đưa góc máy `v14CameraPos` gần ~14%, thêm bóng tiếp xúc radial `createDemoContactTexture()`, nâng độ rõ thiết diện cam đất (`0.44`), hỗ trợ cả Hình chóp `S.ABCD` & Lập phương `ABCD.A′B′C′D′` cùng kéo/phím xoay 3D, đặt lại góc nhìn và khắc phục hoàn toàn va chạm nhãn `S` với huy hiệu `"Kéo để xoay 3D"` tại `320×568`.
4. **Closing CTA & Footer (`LandingClosingScene3D.tsx`, `LandingClosingV14.tsx`, `landing.css`):**
   - Gỡ mảnh nổi lệch sát mép phải, đưa hình chiếu trực giao mặt cắt lục giác xuống mặt đáy đồng trục, và thêm tách nhấc phần chóp trên dọc pháp tuyến (`capLift: 0 → 0.22`) trên lăng trụ lục giác đều (`data-section-edges="6"`).
   - Chuyển Closing CTA về nền trắng `--axo-sp-bg` và Footer về `--axo-sp-paper` kèm nút `#btn-landing-footer-top` nền `--canvas` cuộn về đầu trang.

---

## 4. Định lượng Trước / Sau & Kiểm chứng hình học

### So sánh Trước (`perf/before_metrics.json`) vs Sau (`perf/after_metrics.json`)

| Chỉ số | Trước (Baseline V1.6) | Sau (V1.7 Run 2) | Thay đổi / Trạng thái |
| :--- | :--- | :--- | :--- |
| Demo Canvas `1440×900` (`demoBox`) | `758 × 521` (`394,918 px²`) | `857 × 589` (`504,773 px²`) | **`+27.8%`** diện tích hiển thị 3D |
| Demo Canvas `768×1024` / `390×844` / `320×568` | `694×477` / `322×290` / `252×290` | `726×499` / `348×310` / `278×310` | **`+9.4%` / `+15.5%` / `+17.9%`** |
| Story SVG ViewBox & Scale | `640 × 470`, `scale = 64` | `680 × 500`, `scale = 72` | Khung vẽ lớn hơn, thoáng nhãn hơn |
| Nền Closing → Footer (`1440×900`) | `#F6F5F4` → `#FFFFFF` | `#FFFFFF` → `#F6F5F4` | Tách nhịp sáng/xám chuẩn xác |
| Ma trận 8 Viewport `overflowX` | `0` trên 4 viewport đo | **`0`** trên cả **8 / 8** viewport | `1920×1080` tới `320×568` không tràn ngang |
| Story Forward / Reverse (`1920..320`) | `—` | **`[0,1,2,3]` / `[2,1,0]`** trên **8 / 8** viewport | Khớp cuộn xuôi & cuộn ngược cả `320×568` |
| `heroIdleRaf` / `closingIdleRaf` / `CLS` | `0` / `—` / `0.0001..0.0004` | **`0` / `0` / `0`** trên **8 / 8** viewport | Không rò rỉ vòng lặp đồ họa |

*Ghi chú minh bạch mốc đo:* `after_metrics.json` và 6 video `.webm` được chạy ở Run 2 ngay trước chỉnh sửa 2 dòng cuối cùng cho khoảng hở chữ `S` ở `320×568`; ngay sau chỉnh sửa cuối cùng này, toàn bộ `npx tsc -b`, `npx vite build`, `lint.mjs`, chụp lại `after_demo_pyramid_320x568.png` / `after_demo_cube_320x568.png`, `inspect.mjs` (dev `3001` & prod `4179`), REA live capture `localhost:3001` và bộ test đầy đủ **`191 files / 2,250 tests` Vitest** đều đã chạy lại và đạt 100%.

### Kiểm chứng hình học

- **Hero `S.ABCD` & 3 vệ tinh:** Sai số mặt phẳng và tọa độ 3 vệ tinh liên kết (`orthographicPlan`, `extractedPentagon`, `detachedUpperCap`) đạt `< 1e-6` trong `landing-hero-visual-lifecycle.test.tsx`.
- **Storytelling `ABC.A′B′C′`:** Các điểm gốc `M, N, P` nằm đúng cạnh, `Q ∈ BB′` chỉ xuất hiện khi `stage >= 2` (`MN ∥ BC ⇒ PQ ∥ BC`), thiết diện Chặng 4 là hình thang cân phẳng kèm hình trích đẳng cự `Hình thật (MNP)`.
- **Closing Hexagonal Prism:** Lục giác thiết diện 6 đỉnh (`data-section-edges="6"`), hình chiếu trực giao đồng trục trên mặt đáy, phần chóp trên `upperCapGroup` tịnh tiến dọc pháp tuyến `capLift` (`0` ở nhịp 1–2, `> 0.15` khi lắng đọng & chế độ giảm chuyển động) trong `landing-cta-motion.test.tsx`.

---

## 5. Kết quả Build, Test, Quality Gates & Hồi quy

| Hạng mục kiểm định | Phạm vi / Lệnh | Kết quả quan sát sau chỉnh sửa cuối |
| :--- | :--- | :--- |
| TypeScript check | `npx tsc -b` | **PASS** — exit `0` |
| Production bundle | `npx vite build` | **PASS** — exit `0` (`127 modules`, `5.88s`) |
| Taste-skill lint | `lint.mjs` trên 8 tệp `.tsx` V1.4 | **PASS** — `0 FAIL, 0 WARN` |
| Vitest đầy đủ | `npx vitest run --testTimeout=20000` | **PASS** — **`191 / 191` files passed, `2,250 / 2,250` tests passed** (`188.33s`) |
| `inspect.mjs` (Dev `3001`) | `http://[::1]:3001/gioi-thieu?preview=v1.4` (`1440, 768, 390`) | `overflow: 0`, `lowContrast: 0`, `smallText: 0`, `outlinedBoxes: 0`, `consoleErrors: 0`. Exit `1` chỉ do `[few-pictures]` (chỉ đếm `<img>`, không tính WebGL `<canvas>`/`<svg>`) + `[no-footage]`, `[hairline]` (1 border footer), `[dev-server]` |
| `inspect.mjs` (Prod `4179`) | `vite preview --port 4179` (`1440, 768, 390`) | **0** `overflow` / `lowContrast` / `smallText` / `outlinedBoxes` / `brokenImages` / `consoleErrors` trên cả 3 viewport; cảnh báo `dev-server` biến mất; còn `[few-pictures]` (`FAIL`) và `[hairline]`, `[no-footage]` (`WARN`) |
| Fallback & Trạng thái đặc biệt | `?no_webgl=1`, `reducedMotion`, `WEBGL_lose_context` | **PASS** — `0` canvas khi `?no_webgl=1` (`heroSvg: true`, `closingSvg: true`); `reducedMotion` nhảy thẳng trạng thái hoàn thiện; khôi phục context mất/phục hồi `restoredHostActive: true` |
| Cô lập Production & Workspace | `/`, `/gioi-thieu`, `/app` | **PASS** — `rootProd` & `gioiThieuProd` giữ V1.2.2 (`hasV14Hero: false`, `overflowX: 0`); `/app` `mounted: true`, `overflowX: 0`, `errors: []` |
| Đồng bộ chỉ mục & Docs IA | `code-index-sync.test.ts` & `audit_docs_information_architecture.py --json` | `code-index-sync` **PASS (`3/3`, `47ms`)**; `LINKS.valid = true` (`684` liên kết, `0` gãy), `DOCS_LAYOUT.valid = true` (`0` unclassified), `SECRET_SCAN.valid = true`; chỉ còn `4` đường dẫn stale có sẵn `OWNERSHIP_BLOCKED` (`4605, 4619, 4634, 4646`) |

---

## 6. Kiểm kê Artifact Trực quan (Đã mở xem qua `read_file`)

Tất cả artifact nằm tại thư mục conversation artifact `landing_v1_7/` (ngoài git tree):
- **Baseline Before (`before/`):** **36** ảnh `.png` (`before_hero_*`, `before_story_s1..s4_*`, `before_demo_pyramid_*`, `before_demo_cube_*`, `before_closing_*`, `before_footer_*` trên `1440×900`, `768×1024`, `390×844`, `320×568`).
- **After Capture (`after/`):** **49** ảnh `.png` qua 8 viewport (`1920×1080`, `1440×900`, `1366×768`, `1024×768`, `768×1024`, `390×844`, `360×800`, `320×568` + `after_fallback_nowebgl_1440x900.png`), bao gồm `after_demo_pyramid_320x568.png` và `after_demo_cube_320x568.png` chụp lại sau tinh chỉnh cuối xác nhận chữ `S` tách thoáng huy hiệu `"Kéo để xoay 3D"`.
- **6 Video `.webm` bắt buộc (`videos/`):**
  1. `01_hero_motion_and_hover_1440x900.webm` (`971,879` B) + `keyframes/kf1_hero_hover.png` (`79,841` B)
  2. `02_storytelling_forward_4stages_1440x900.webm` (`1,235,311` B) + `kf2_story_fwd_s1.png` / `kf2_story_fwd_s4.png`
  3. `03_storytelling_reverse_4stages_1440x900.webm` (`989,336` B) + `kf3_story_rev_s1.png`
  4. `04_interactive_demo_both_samples_1440x900.webm` (`2,197,759` B) + `kf4_demo_pyramid_orbit.png` / `kf4_demo_cube_orbit.png`
  5. `05_closing_cta_and_footer_1440x900.webm` (`1,404,179` B) + `kf5_closing_settled.png`
  6. `06_mobile_full_scroll_390x844.webm` (`1,426,295` B) + `kf6_mobile_drawer.png`
- **REA (`rea/`):** `rea_pudding.png` (`152,038` B), `after_localhost_3001.png` (`75,591` B), `rea-research.json`, `rea-after.json`.
- **Inspect Filmstrips (`taste_after_dev/`, `taste_after_prod/`):** `desktop-fold.jpg`, `mobile-fold.jpg`, `desktop-film-01.jpg`, `report.json`.

---

## 7. Danh sách tệp V1.2.2 đề xuất dọn sau khi Owner duyệt nâng cấp (KHÔNG xóa lúc này)

Các tệp sau hiện vẫn phục vụ tuyến production V1.2.2 (`/` và `/gioi-thieu`), phải **giữ nguyên** cho tới khi Chủ dự án phê duyệt chuyển đổi chính thức:
- `frontend/src/components/landing/LandingHeroSculpture3D.tsx`
- `frontend/src/components/landing/LandingClosingSculpture.tsx`
- `frontend/src/components/landing/LandingStorytelling.tsx`
- `frontend/src/components/landing/LandingExplainerAnimation.tsx`
- `frontend/src/components/landing/LandingIllustrationAccents.tsx`
- Nhánh `presentation === "default"` trong `LandingHeader.tsx`, `LandingInteractiveDemo.tsx`, `LandingHeroScene3D.tsx`.

---

## 8. Phân loại nhận thức & Trạng thái nghiệm thu

- **VERIFIED:** Toàn bộ sửa đổi mã nguồn trên nhánh cô lập `?preview=v1.4`; `npx tsc -b`; `npx vite build`; `lint.mjs` (`0 FAIL, 0 WARN`); `191/191` files (`2,250/2,250` tests) Vitest; `inspect.mjs` trên dev `3001` & prod `4179`; 8-viewport Playwright matrix + 6 `.webm` videos; REA MCP capture trước (`pudding.cool`) & hậu chỉnh sửa (`localhost:3001`); ảnh chụp sau tinh chỉnh cuối `320×568`; không hồi quy `/`, `/gioi-thieu`, `/app`; giữ sống server `localhost:3001` (`PID 16060`).
- **INFERRED:** Trải nghiệm vuốt/cuộn cảm ứng mượt trên thiết bị di động thật được suy luận từ hành vi sticky + `touch-action: pan-y` giả lập trên Chromium `320px–390px`.
- **NOT_VERIFIED:**
  - `https://tympanus.net/codrops/hub/` (`HTTP 403` Cloudflare anti-bot challenge).
  - Thiết bị di động vật lý (`NOT_PHYSICAL_MOBILE`: toàn bộ kiểm thử mobile `320×568`, `360×800`, `390×844`, `768×1024` chạy trên Chromium SwiftShader).
- **FAILED:** Không có hạng mục kiểm thử sản phẩm nào thất bại (`inspect.mjs` chỉ báo `[few-pictures]` do không tính `<canvas>` WebGL / `<svg>` là `<img>`).
- **PENDING_OWNER_REVIEW:** Quyết định phê duyệt thẩm mỹ & cho phép cutover V1.4+ thay V1.2.2 của Chủ dự án.

`OWNER_APPROVAL = PENDING_OWNER_REVIEW`
