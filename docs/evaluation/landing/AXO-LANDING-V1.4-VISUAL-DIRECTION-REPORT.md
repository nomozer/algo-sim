# AXO Landing Page V1.4 — Unified Visual Design, Typography & Motion System Report

**Ngày hoàn thành:** 2026-11-15  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Mốc nền V1.2.2 / V1.3:** [`AXO-LANDING-V1.2.2-UX-REPORT.md`](./AXO-LANDING-V1.2.2-UX-REPORT.md) · [`AXO-LANDING-V1.3-CREATIVE-DIRECTION-REPORT.md`](./AXO-LANDING-V1.3-CREATIVE-DIRECTION-REPORT.md) (`aebcb1810`)  
**Tuyến xem thử V1.4 cô lập:** `http://localhost:3001/gioi-thieu?preview=v1.4` (alias: `?preview=v14`, `?prototype=v1.4`, `?prototype=v14`)  
**Tuyến Production mặc định:** `/` và `/gioi-thieu` (giữ nguyên **V1.2.2** `"prod"` — không thay đổi)  
**Owner Approval:** `PENDING_OWNER_REVIEW`

> [!IMPORTANT]
> Bản **AXO Landing V1.4** vận hành ở chế độ **preview cô lập qua query parameter (`?preview=v1.4`)**, tuyệt đối không hiển thị thanh banner reviewer, nhãn `PENDING_OWNER_REVIEW` hay bộ chuyển prototype bên trong giao diện xem thử. Trang mặc định `/` và `/gioi-thieu` giữ nguyên V1.2.2 trong trạng thái `PENDING_OWNER_REVIEW`.

---

## 1. Executive Summary (`PENDING_OWNER_REVIEW`)

AXO Landing V1.4 hợp nhất toàn bộ trang giới thiệu công khai `/gioi-thieu?preview=v1.4` thành một hệ thống thị giác, typography và chuyển động thống nhất mang bản sắc hình học không gian:

1. **Nghiên cứu thực chứng trực tiếp bằng REA MCP:** Kiểm tra 6 website tham chiếu (`bundaumayo.top`, `notion.com`, `figma.com`, `rive.app`, `lusion.co`, `pudding.cool`) + CSS stylesheet từ `bundaumayo.top` (`VERIFIED_BY_REA`), đồng thời đánh dấu trung thực `tympanus.net/codrops/` là `REA_NOT_VERIFIED` do gặp phản hồi `HTTP 403 / Cloudflare`.
2. **Expressive Geometry Typography (`AnnotatedHeading.tsx`):** Chuẩn hóa 3 biến thể nét vẽ hình học thuần SVG (`circle` quanh `"hình dung"`, `underline` kèm witness ticks quanh `"từng lớp không gian"`, `highlight` mặt cắt nghiêng quanh `"thiết diện thật"` và `"S(MNPQ) = 3√7"`), khắc phục triệt để lỗi Blink/Chromium khi kết hợp `pathLength="1"` với `vector-effect="non-scaling-stroke"` dưới `preserveAspectRatio="none"` bằng `stroke-dasharray: none` ở trạng thái hoạt động kết hợp animation `clip-path` wipe mượt (`axo-v14-anno-wipe`).
3. **Hero Spatial System (`LandingHeroV14.tsx` + `LandingHeroScene3D.tsx` `presentation="v14"`):** Khối chóp `S.ABCD` cắt bởi mặt phẳng `(MNP)` tạo thiết diện ngũ giác `MENPF` với mặt cắt cam nổi bật, nét `SA ⊥ (ABCD)`, chiều cao khung khóa cứng theo `clamp(380px, 40vw, 500px)` để triệt tiêu CLS (`CLS = 0` trên mọi lượt đo benchmark), nhịp xuất hiện `ANIMATION_DURATION_MS = 1420` ms rồi tự dừng về `0` idle RAF, đi kèm thẻ chiếu trực giao 2D thật (`computeTrueShapeSection2D`) với `S(MENPF) = 6√6`.
4. **Continuous Spatial Storytelling (`LandingStorytellingV14.tsx`):** `0` WebGL context; dựng phép chiếu phối cảnh 3D SVG + RAF tween (`projectPrismPoint3D`) trên lăng trụ tam giác đều `ABC.A′B′C′` cạnh `a = 4` (`LANDING_PRISM_STORY_SPEC`) qua 4 chặng (`STORY_STAGES_V14`), giữ chặt kỷ luật sư phạm không lộ `S(MNPQ) = 3√7` và `MN = 2 · PQ = 4 · MQ = NP = 2√2` cho đến Chặng 4, cùng bố cục mobile riêng `"visual" / "rail" / "readout"` (`minStepHeight = 49px` trên tablet portrait & mobile).
5. **Interactive Demo Workbench & Closing Cohesion (`LandingInteractiveDemo.tsx` `presentation="v14"` + `LandingClosingV14.tsx` + `LandingPreviewV14.tsx`):** Đồng bộ ánh sáng studio (`presentation="v14"`), bỏ eyebrow kỹ thuật thừa, nối motif chóp `S.ABCD → MENPF` sang phần kết trang và footer tinh gọn, giữ ngân sách **tối đa 2 WebGL context đồng thời** (`1` ở Hero + `1` ở Demo).

---

## 2. V1.3 Prototype Disposition (`NOT_APPROVED_FOR_INTEGRATION`)

- Hai prototype thử nghiệm V1.3 (`?prototype=a` trong `LandingPrototypeA.tsx` và `?prototype=b` trong `LandingPrototypeB.tsx`) đã được cập nhật trạng thái **`NOT_APPROVED_FOR_INTEGRATION`** trong [`AXO-LANDING-V1.3-CREATIVE-DIRECTION-REPORT.md`](./AXO-LANDING-V1.3-CREATIVE-DIRECTION-REPORT.md).
- Mã nguồn hai route thử nghiệm V1.3 vẫn được giữ nguyên có chủ đích phía sau `readLandingPrototypeMode()` để phục vụ so sánh định lượng A/B/Prod/V1.4 trong cùng điều kiện đo.

---

## 3. REA MCP Live Research & Evidence Ledger

Bằng chứng kiểm chứng trực tiếp được ghi trong [`rea-v14-evidence-ledger.json`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea-v14-evidence-ledger.json):

| Site | URL | Trạng thái | REA Evidence ID | Scenario / DOM / Screenshot SHA-256 | Ảnh inspect |
|---|---|---|---|---|---|
| **bundaumayo** | `https://bundaumayo.top/` | `VERIFIED_BY_REA` | `ev_8f0f77d4f7e1691be920caa6b535aad6260faad60d6010abef5fbbb2cd87957e` | `9a736d0f...` / `f70dcc3f...` (`66,688 B`) / `9021be38...` (`434,817 B`) | [`rea_01_bundaumayo.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea_01_bundaumayo.png) |
| **bundaumayo_css** | `https://bundaumayo.top/assets/css/clay.css?v=11-1792852154` | `VERIFIED_BY_REA` | `ev_8c525df40b6a22b34eac02906e13cb36697e55fb46e3423c296b45862ef9cd7f` | `a777dfa4...` / — / — | — |
| **notion** | `https://www.notion.com/` | `VERIFIED_BY_REA` | `ev_4a877a80d540c074c71959aecd875bb70f0f0343104149be4f866ae8ba8c1177` | `91768e10...` / `7db24efc...` (`194,680 B`) / `9bb5a508...` (`160,464 B`) | [`rea_02_notion.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea_02_notion.png) |
| **figma** | `https://www.figma.com/` | `VERIFIED_BY_REA` | `ev_86e3bf30ace417056c5c681089dff15018e865aa09e6e714800d24060e24e152` | `6defdd40...` / `fe3ee223...` (`1,894,605 B`) / `5f21937e...` (`286,239 B`) | [`rea_03_figma.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea_03_figma.png) |
| **rive** | `https://rive.app/` | `VERIFIED_BY_REA` | `ev_e5dc2f4a552a0bb51780bb1ba5430dd093576d7bcaa99c463d54ae498af73f7d` | `e0ce9d1b...` / `93297791...` (`697,590 B`) / `6dab4364...` (`624,906 B`) | [`rea_04_rive.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea_04_rive.png) |
| **lusion** | `https://lusion.co/` | `VERIFIED_BY_REA` | `ev_e9fd0d4e726a559ceff7cfc557d173192db9f0a544285667469ae7aee36fa2b8` | `6dedc154...` / `141cdb51...` (`112,432 B`) / `46eef0c4...` (`111,759 B`) | [`rea_05_lusion.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea_05_lusion.png) |
| **pudding** | `https://pudding.cool/` | `VERIFIED_BY_REA` | `ev_cf00211b5590ce7ad5b8255e105efbc60027698bd0835504e608d5a1afab6213` | `918abd61...` / `7a14e2d8...` (`147,979 B`) / `bb6cbe2f...` (`173,595 B`) | [`rea_06_pudding.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/rea/rea_06_pudding.png) |
| **codrops** | `https://tympanus.net/codrops/` | `REA_NOT_VERIFIED` | `null` | HTTP 403 / Cloudflare anti-bot challenge (`'Just a moment...'`), tuân thủ nguyên tắc không vượt anti-bot. | `null` |

**Bài học kiến trúc áp dụng trực tiếp vào V1.4:**
- Bố cục editorial trắng rộng kiểu Notion (`#ffffff` / `#f7f6f4` + tương phản mạnh + nhấn thị giác đặt trực tiếp vào cụm từ lõi).
- Không ghép minh họa rời rạc kiểu card; dùng chú thích SVG gắn trực tiếp lên ngữ nghĩa văn bản và 1 sân khấu đồng bộ cho mỗi phần.
- State-driven animation tự ngủ (`idleRAF = 0`) lấy cảm hứng từ Rive thay vì vòng lặp 60fps vô tận khi người dùng dừng cuộn.
- WebGL có ngân sách nghiêm ngặt (`<= 2` active) học từ Lusion, giữ Storytelling bằng SVG nhẹ để đảm bảo resize mượt trên mobile.

---

## 4. Design System & Token Compliance

- Toàn bộ kiểu V1.4 cô lập dưới tiền tố `.axo-v14-*` và modifier `.is-v14` trong `frontend/src/components/landing/landing.css`, dùng trực tiếp token từ `frontend/src/styles/tokens.css` (`--ink`, `--canvas`, `--hairline`, `--rounded-md`, `--axo-sp-accent`, `--axo-sp-amber`, `--axo-sp-amber-deep`, `--axo-sp-paper`, `--axo-sp-ease`).
- Kiểm tra tự động bằng `design-taste-frontend/scripts/lint.mjs`, `src/styles/tokens.test.ts` (`15/15`), `src/styles/class-coverage.test.ts` (`4/4`) và `src/components/ui-hygiene.test.ts` (`18/18`): **0 `#hex` hardcode, 0 `var(--...)` inline trong TSX, 0 eyebrow/badge kỹ thuật `01..04`, 0 banner reviewer trên giao diện xem thử**.

---

## 5. Architecture & Component Summary

### 5.1. Expressive Typography (`AnnotatedHeading.tsx`)
- `AnnotatedPhrase` hỗ trợ 3 biến thể (`circle`, `underline`, `highlight`), bọc `<span className="axo-v14-anno-text">` + `<svg aria-hidden="true" focusable="false" preserveAspectRatio="none">` có `pathLength={1}` và `vector-effect="non-scaling-stroke"`.
- **Phát hiện & sửa lỗi trên Chromium trong vòng visual QA:** Khi `.axo-v14-anno.is-active .axo-v14-anno-path` giữ `stroke-dasharray: 1` với `pathLength="1"` và `vector-effect="non-scaling-stroke"`, Blink cắt nét gạch chân `"từng lớp không gian"` tại `~270px` (~62–70% bề rộng trên desktop 1440/1920px, ~91% trên mobile 390px) và gây hở mép trên của oval `"hình dung"` tại 320px/390px. Đã khắc phục bằng cách chuyển trạng thái `.is-active .axo-v14-anno-path` về `stroke-dasharray: none; stroke-dashoffset: 0;` và dùng `@keyframes axo-v14-anno-wipe` (`clip-path: inset(...)` + `opacity`) trên phần tử SVG, đồng thời mở rộng nhẹ padding quanh `"hình dung"` (`0 0.18em`) và hạ vị trí gạch chân (`bottom: -0.28em`) để không chạm chân chữ `p`/`g`.

### 5.2. Hero & True-Shape Projection (`LandingHeroV14.tsx`, `LandingHeroScene3D.tsx`)
- Hiển thị ngay SVG fallback xác định trước khi Three.js khởi tạo; kích thước `.axo-v14-hero-visual` được khóa khớp `.axo-v14-hero-canvas-host` (`height: clamp(380px, 40vw, 500px)` trên desktop, `360px` tại `<= 1024px`) để triệt tiêu dịch chuyển dọc khi gắn WebGL (**CLS = 0.000**).
- `LandingHeroScene3D` nhận prop `presentation?: "default" | "v14"` để dùng ánh sáng định hướng theo pháp tuyến mặt và đĩa tiếp xúc đồng tâm phẳng.
- `computeTrueShapeSection2D` tính phép chiếu trực giao chuẩn độ dài cạnh của ngũ giác `MENPF` với `S(MENPF) = 6√6`. Trên mobile `<= 680px`, `.axo-v14-hero-trueshape` chuyển thành thanh ngang full-width ngay dưới khối 3D thay vì nổi lệch phải.

### 5.3. Continuous Spatial Storytelling (`LandingStorytellingV14.tsx`)
- Dùng `STORY_STAGES_V14` (`4` chặng: `Từ đề bài` → `Dựng không gian` → `Xác lập quan hệ` → `Kết quả`) trên `LANDING_PRISM_STORY_SPEC` (`ABC.A′B′C′`, `M ∈ AB`, `N ∈ AC`, `P ∈ CC′`, `(MNP): √3x + y − √3z = 2√3`).
- Kỷ luật sư phạm được Playwright xác nhận: Chặng 1 (`stage 0`) ẩn hoàn toàn `S(MNPQ) = 3√7` và `MQ = NP = 2√2`; Chặng 4 (`stage 3`) hiển thị đầy đủ `MN = 2 · PQ = 4 · MQ = NP = 2√2` và pill `S(MNPQ) = 3√7`.
- Bố cục mobile `<= 920px` đảo sang grid `"visual" / "rail" / "readout"`, hàng nút chặng 4 cột chiều cao đo được `49px` (đạt chuẩn chạm `>= 48px`), hỗ trợ vuốt ngang, phím mũi tên và dừng chuyển động ngay dưới `prefers-reduced-motion`.

### 5.4. Interactive Demo Workbench, Closing & Isolation
- `LandingInteractiveDemo` nhận `presentation="v14"`, gắn `data-ui="product-workbench"` và `.is-v14`, nhấn `"thiết diện thật"` bằng `AnnotatedPhrase variant="highlight"`, ẩn dòng eyebrow kỹ thuật thừa.
- `LandingClosingV14` giữ CTA `#btn-landing-final-start` và `#btn-landing-hero-library` cạnh SVG chuyển tiếp wireframe sang khối đặc `S.ABCD → MENPF`; `LandingFooterV14` giữ `#btn-landing-footer-library`.
- `LandingPreviewV14` ghép trọn vẹn Header + Hero + Storytelling + Demo + Closing + Footer, nối vào `LandingView.tsx` qua `readLandingPrototypeMode()` (`"v14"` khi `?preview=v1.4` / `?preview=v14` / `?prototype=v1.4` / `?prototype=v14`).

---

## 6. Quantitative Benchmark & 8-Viewport Verification (`v14-comparison-benchmark.json`)

Dữ liệu thu trực tiếp từ [`v14-comparison-benchmark.json`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/perf/v14-comparison-benchmark.json) (`capturedAt: "2026-11-15T14:48:55.141Z"`, chạy lại sau chỉnh sửa visual QA và xác nhận `CLS = 0`):

> [!NOTE]
> Các lượt đo `mobile_390x844_4x_cpu` sử dụng giả lập CPU throttling 4× trên Chromium Desktop (`deviceNote: "NOT_PHYSICAL_MOBILE"`), không phải phần cứng điện thoại vật lý.

### 6.1. Backend 1: `ANGLE/SwiftShader` (`Vulkan 1.3.0 SwiftShader Device`)

| Profile | Biến thể | Active FPS | Avg / P95 Frame (ms) | Resize FPS | Long Tasks (cnt / max ms) | LCP (ms) | CLS | WebGL (max / life / lost) | Idle RAF | Errors | Heap Δ (MB) |
|---|---|---:|---|---:|---|---:|---:|---|---:|---:|---:|
| `desktop_1920x1080` | `prod` | `57.1` | `17.51 / 16.8` | `121.9` | `4 / 114` | `1008` | `0` | `2 / 2 / 0` | `0` | `0` | `+2.9` |
| `desktop_1920x1080` | `proto_a` | `59` | `16.95 / 16.8` | `118.2` | `3 / 95` | `636` | `0` | `1 / 1 / 0` | `0` | `0` | `+2.76` |
| `desktop_1920x1080` | `proto_b` | `58.7` | `17.03 / 16.7` | `99.4` | `4 / 90` | `388` | `0` | `2 / 6 / 0` | `0` | `0` | `+2.1` |
| `desktop_1920x1080` | **`preview_v14`** | **`60`** | **`16.67 / 16.8`** | **`118.2`** | **`2 / 120`** | **`472`** | **`0`** | **`2 / 3 / 0`** | **`0`** | **`0`** | `+2.71` |
| `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | `prod` | `55.8` | `17.91 / 16.8` | `96.3` | `5 / 277` | `1304` | `0` | `2 / 2 / 0` | `0` | `0` | `+0.36` |
| `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | `proto_a` | `48.4` | `20.65 / 33.3` | `104.6` | `5 / 345` | `1220` | `0` | `1 / 1 / 0` | `0` | `0` | `-0.12` |
| `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | `proto_b` | `50.9` | `19.66 / 16.8` | `104.6` | `8 / 293` | `1080` | `0` | `2 / 6 / 0` | `0` | `0` | `+0.39` |
| `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | **`preview_v14`** | **`44.8`** | `22.32 / 33.4` | **`102.1`** | `7 / 274` | `1216` | **`0`** | **`2 / 3 / 0`** | **`0`** | **`0`** | `-1.19` |

### 6.2. Backend 2: `Hardware GPU (ANGLE D3D11)` (`Intel(R) UHD Graphics (0x00009A68)`)

| Profile | Biến thể | Active FPS | Avg / P95 Frame (ms) | Resize FPS | Long Tasks (cnt / max ms) | LCP (ms) | CLS | WebGL (max / life / lost) | Idle RAF | Errors | Heap Δ (MB) |
|---|---|---:|---|---:|---|---:|---:|---|---:|---:|---:|
| `desktop_1920x1080` | `prod` | `56` | `17.86 / 16.8` | `122` | `2 / 392` | `696` | `0` | `2 / 2 / 0` | `0` | `0` | `-0.13` |
| `desktop_1920x1080` | `proto_a` | `59.3` | `16.85 / 16.8` | `121.9` | `1 / 60` | `432` | `0` | `1 / 1 / 0` | `0` | `0` | `+0.54` |
| `desktop_1920x1080` | `proto_b` | `59` | `16.95 / 16.8` | `121.9` | `3 / 86` | `396` | `0` | `2 / 6 / 0` | `0` | `0` | `+4.17` |
| `desktop_1920x1080` | **`preview_v14`** | **`60`** | **`16.67 / 16.7`** | **`121.9`** | **`2 / 129`** | **`508`** | **`0`** | **`2 / 3 / 0`** | **`0`** | **`0`** | `+4.44` |
| `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | `prod` | `56.9` | `17.57 / 16.7` | `95.7` | `5 / 289` | `1300` | `0` | `2 / 2 / 0` | `0` | `0` | `+0.35` |
| `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | `proto_a` | `53.2` | `18.81 / 16.8` | `104.6` | `7 / 269` | `1184` | `0` | `1 / 1 / 0` | `0` | `0` | `+2.97` |
| `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | `proto_b` | `51.2` | `19.53 / 16.8` | `107.7` | `7 / 274` | `1072` | `0` | `2 / 6 / 0` | `0` | `0` | `-0.1` |
| `mobile_390x844_4x_cpu` (`NOT_PHYSICAL_MOBILE`) | **`preview_v14`** | **`54.7`** | `18.29 / 33.3` | **`105.4`** | `6 / 304` | `1228` | **`0`** | **`2 / 3 / 0`** | **`0`** | **`0`** | `+1.78` |

### 6.3. Ma trận 8 Viewport & Kiểm tra Hành vi Playwright

| Viewport (`w × h`) | `prod` (`overflowX / h1Px / ctas`) | `preview_v14` (`overflowX / h1Px / ratio / ctas`) | Mobile Story Layout (`figAboveRail / railAboveRead / minH / inBounds`) |
|---|---|---|---|
| `desktop-1920` (`1920×1080`) | `false / 69.6 / [48,48]` | `false / 60 / 1.2 / [46,46]` | `false / true / 48 / true` |
| `desktop-1440` (`1440×900`) | `false / 69.6 / [48,48]` | `false / 60 / 1.2 / [46,46]` | `false / true / 48 / true` |
| `laptop-1366` (`1366×768`) | `false / 66.934 / [48,48]` | `false / 59.421 / 1.2 / [46,46]` | `false / true / 48 / true` |
| `tablet-landscape-1024` (`1024×768`) | `false / 50.176 / [48,48]` | `false / 44.544 / 1.2 / [46,46]` | `false / true / 48 / true` |
| `tablet-portrait-768` (`768×1024`) | `false / 40.8 / [48,48]` | `false / 37.6 / 1.2 / [46,46]` | `true / true / 49 / true` |
| `mobile-390` (`390×844`) | `false / 40.8 / [48,48]` | `false / 33.54 / 1.24 / [46,46]` | `true / true / 49 / true` |
| `mobile-360` (`360×800`) | `false / 40.8 / [48,48]` | `false / 32 / 1.24 / [46,46]` | `true / true / 49 / true` |
| `mobile-320` (`320×568`) | `false / 40.8 / [48,48]` | `false / 32 / 1.24 / [46,46]` | `true / true / 49 / true` |

- **Epistemic & Guest Parity (`epistemicCheck`):** `stage0Hides3Sqrt7 = true`, `stage0Hides2Sqrt2 = true`, `stage3Shows3Sqrt7 = true`, `stage3Shows2Sqrt2 = true`, `zeroReviewBanner = true`, `guestHeroBtn = "Bắt đầu dựng hình"`, `guestFinalBtn = "Bắt đầu dựng hình"`.
- **Auth Parity (`authParityCheck`):** `authHeroBtn = "Vào ứng dụng"`, `authFinalBtn = "Vào ứng dụng"`, `headerHasAccount = true`.
- **Reduced Motion (`reducedMotionCheck`):** `settledIdleRafCount = 0`.

---

## 7. Visual QA & Motion Artifact Inventory (Inspected)

Toàn bộ 16 ảnh chụp PNG dưới đây đã được kiểm tra trực tiếp bằng `read_file` sau lần sửa visual cuối cùng (với các ảnh V1.4), kết hợp 4 video chuyển động `.webm` ghi trên Chromium:

- **V1.2.2 Baseline Reference:**
  - [`prod_v122_desktop_hero.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/prod_v122_desktop_hero.png)
  - [`prod_v122_mobile_story.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/prod_v122_mobile_story.png)
- **V1.4 Desktop & Laptop (1920, 1440, 1366):**
  - [`v14_desktop_1920_hero.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_desktop_1920_hero.png)
  - [`v14_desktop_1440_hero.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_desktop_1440_hero.png)
  - [`v14_laptop_1366_hero.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_laptop_1366_hero.png)
  - [`v14_desktop_story_stage0.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_desktop_story_stage0.png)
  - [`v14_desktop_story_stage3.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_desktop_story_stage3.png)
  - [`v14_desktop_demo.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_desktop_demo.png)
  - [`v14_desktop_closing.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_desktop_closing.png)
- **V1.4 Tablet & Mobile (768, 390, 320):**
  - [`v14_tablet_768_hero.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_tablet_768_hero.png)
  - [`v14_tablet_768_story.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_tablet_768_story.png)
  - [`v14_mobile_390_hero.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_mobile_390_hero.png)
  - [`v14_mobile_390_story_stage3.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_mobile_390_story_stage3.png)
  - [`v14_mobile_390_demo.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_mobile_390_demo.png)
  - [`v14_mobile_320_hero.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_mobile_320_hero.png)
  - [`v14_mobile_320_story.png`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/screenshots/v14_mobile_320_story.png)
- **Video Chuyển Động WebM:**
  - [`v14_hero_entrance_and_typography.webm`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/video/v14_hero_entrance_and_typography.webm)
  - [`v14_story_continuous_stages.webm`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/video/v14_story_continuous_stages.webm)
  - [`v14_demo_orbit_and_sample_switch.webm`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/video/v14_demo_orbit_and_sample_switch.webm)
  - [`v14_mobile_390_flow.webm`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_v1_4_audit/video/v14_mobile_390_flow.webm)

---

## 8. Verification Results & Commit Groups

### 8.1. Automated Checks After Final Code/CSS Edit (`b717cebd1`)
- `design-taste-frontend/scripts/lint.mjs` trên 5 file TSX V1.4 mới (`AnnotatedHeading.tsx`, `LandingHeroV14.tsx`, `LandingStorytellingV14.tsx`, `LandingClosingV14.tsx`, `LandingPreviewV14.tsx`): **`0 FAIL, 0 WARN`**.
- `npm run build` (`tsc -b && vite build`): thoát mã **`0`** (`127 modules transformed`, `dist` build thành công trong `5.66s`).
- `npx vitest run` cho toàn bộ 18 file test Landing + CSS transitions/scrollbar: **`18/18` file pass (`66/66` test pass)**.
- `npx vitest run src/styles/tokens.test.ts`: **`1/1` file pass (`15/15` test pass)**.
- `npx vitest run src/code-index-sync.test.ts src/styles/class-coverage.test.ts`: **`2/2` file pass (`7/7` test pass)**.
- `npx vitest run src/components/ui-hygiene.test.ts`: **`1/1` file pass (`18/18` test pass)**.
- Chạy độc lập `src/simulations/domains/geometry/axo-cross-family-scene3d-acceptance.test.tsx`: **`1/1` file pass (`10/10` test pass)**; `src/components/geometry2d/geometry2d-illustration-system.test.tsx`: **`1/1` file pass (`7/7` test pass)**.
- *Ghi nhận trung thực về full sweep hậu sửa CSS:* Ở lượt chạy full `npx vitest run --maxWorkers=1` sau khi chỉnh `AnnotatedHeading.tsx` và `landing.css`, `179/182` file (`2222/2225` test) pass và có `3` test quét toàn bộ catalog hình học (`geometry2d-illustration-system.test.tsx:157`, `axo-cross-family-scene3d-acceptance.test.tsx:383`, `axo-pedagogical-presentation-hardening.test.tsx:425`) chạm timeout mặc định `5000ms` do tải CPU/JIT khi chạy liên tiếp; `axo-cross-family-scene3d-acceptance.test.tsx` (`10/10`) và `geometry2d-illustration-system.test.tsx` (`7/7`) đều pass khi chạy lại tách khỏi contention, còn `axo-pedagogical-presentation-hardening.test.tsx` đã pass (`8/8`, `3762ms`) ở lượt trước đó (`task-80648`, cũng sau lần sửa code/CSS cuối cùng). Không nới lỏng timeout hay assertion của bất kỳ bài test nào.

### 8.2. Git Commits on Branch `feat/axo-geometry-library-verification`
1. `eeb12c9c6` — `feat(axo): add expressive geometry typography`
2. `f97f00b1f` — `feat(axo): redesign landing hero visual system`
3. `e34faf7d4` — `feat(axo): refine spatial storytelling preview`
4. `b717cebd1` — `style(axo): unify demo and final cta presentation`
5. Commit báo cáo V1.4 (`docs(axo): add v1.4 visual direction report`) bổ sung riêng [`AXO-LANDING-V1.4-VISUAL-DIRECTION-REPORT.md`](./AXO-LANDING-V1.4-VISUAL-DIRECTION-REPORT.md) và [`AXO-LANDING-V1.3-CREATIVE-DIRECTION-REPORT.md`](./AXO-LANDING-V1.3-CREATIVE-DIRECTION-REPORT.md).

---

## 9. Known Limitations & Owner Review Gate

- **Chưa gộp vào production:** Mặc định `/` và `/gioi-thieu` vẫn chạy V1.2.2 (`"prod"`) chờ quyết định trực tiếp của Chủ dự án (`Owner Approval: PENDING_OWNER_REVIEW`).
- **Mobile thực tế:** Đo đạc mobile trong báo cáo sử dụng `mobile_390x844_4x_cpu` giả lập (`NOT_PHYSICAL_MOBILE`), cần thử lướt/vuốt thêm trên thiết bị iOS/Android thật trước khi cutover production.
- **Tỷ lệ khung chữ 320px:** Trên màn hình siêu hẹp `320×568`, Hero giữ `overflowX = false` và full CTA rõ nét; thanh `.axo-v14-hero-trueshape` và hình 3D xếp dưới fold dọc chuẩn của màn hình 568px.
