# AXO Landing V1.4 — Product Storytelling, 3D Visual Quality & UX Recovery Report

**Ngày hoàn thành:** 2026-11-16  
**Worktree:** `D:\Documents\projects\axo-geometry-library`  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Baseline Commit SHA:** `2ddcd6f25` (`docs(axo): add landing design recovery and scroll storytelling report`) · Implementation base `d04a445a6`  
**Implementation Commit SHA:** `a7d2437a9` (`a7d2437a9204cc9d0ed981d590f99bdbcd6a0c19`)  
**Report Commit SHA:** Đóng gói ngay sau implementation commit  
**Tuyến xem trước cô lập:** `http://localhost:3001/gioi-thieu?preview=v1.4` (`presentation="v14"`)  
**Tuyến Production mặc định:** `/` và `/gioi-thieu` (**V1.2.2** `"prod"` — bảo toàn nguyên vẹn)  
**Tình trạng triển khai thực tế:** `NOT_DEPLOYED`  
**Owner Approval:** `PENDING_OWNER_REVIEW`

> [!IMPORTANT]
> - Báo cáo này tách bạch rõ giữa **xác minh kỹ thuật (`TECHNICAL_VERIFIED`)**, **chờ rà soát trực quan (`VISUAL_REVIEW_PENDING`)** và **quyết định nghiệm thu của Chủ dự án (`OWNER_APPROVAL_PENDING`)**. Không khẳng định thiết kế đã được Owner chốt.
> - Tuyến production `/` và `/gioi-thieu` (`"prod"`, V1.2.2) và không gian làm việc (`/app`, `/library`, `/workspace`) được bảo toàn nguyên vẹn.
> - Các tệp ngoài phạm vi Landing do phiên song song sở hữu (`OWNERSHIP_BLOCKED`) được giữ nguyên hoàn toàn trong working tree, không sửa, không khôi phục và không stage.

---

## 1. Executive Summary & Epistemic Classification

Đợt khôi phục chất lượng sản phẩm trên tuyến xem trước `?preview=v1.4` giải quyết triệt để các phản hồi nghiệm thu về tính sư phạm, chất lượng đồ họa 3D, trải nghiệm cuộn trang kể chuyện và vệ sinh giao diện:

| Phân loại | Trạng thái | Căn cứ xác minh trực tiếp |
|---|---|---|
| Chức năng, dữ liệu & test tự động (`tsc`, `vite build`, `vitest`) | `TECHNICAL_VERIFIED` | `tsc -b` + `vite build` exit `0` (`127 modules`, `5.42s`); `191/191` test files (`2248/2248` tests) PASS độc lập không có GPU/CPU contention |
| Không hiển thị sẵn đáp án toán học trên Landing V1.4 | `TECHNICAL_VERIFIED` | `landing-product-integrity.test.tsx` + quét DOM trực tiếp trên mọi section & cả 4 bước của Chóp / Lập phương đều trả `[]` |
| Tiêu đề Hero 2 dòng & 8-viewport responsive (`1920..320`) | `TECHNICAL_VERIFIED` | `verify-v14-product-after.mjs` + `inspect.mjs` xác nhận `2` dòng ở mọi viewport và `overflowPx = 0` |
| Storytelling sticky runway 4 chặng không chồng chữ | `TECHNICAL_VERIFIED` | `storyScrollChecks`: `runwayHeightPx = 2205`, `fwdMax = 1`, `revMax = 1` across `0%..100%` |
| Closing CTA 3D đa khối WebGL + dừng idle RAF về `0` | `TECHNICAL_VERIFIED` | `closingMetrics`: `spatial-multi-solid-3d`, `composition-settled`, `idleProbe500msFrames = 0` trên cả SwiftShader lẫn D3D11 |
| Cảm quan thẩm mỹ tổng thể & chi tiết thị giác | `VISUAL_REVIEW_PENDING` | Đã kiểm tra ảnh Before/After và video `.webm` thực tế, chờ Owner đánh giá cảm quan |
| Quyết định triển khai lên Production mặc định `/` | `OWNER_APPROVAL_PENDING` | Chờ Chủ dự án duyệt kết quả nghiệm thu (`PENDING_OWNER_REVIEW`) |

---

## 2. Git Worktree Scope & Ownership Isolation Audit

- Toàn bộ thay đổi được giữ gọn trong `frontend/src/components/landing/`, `frontend/src/components/__tests__/landing-*.test.*` và `docs/CODE_INDEX.md` (chỉ cập nhật dòng `1983`).
- Mọi tệp `OWNERSHIP_BLOCKED` thuộc `backend/*`, `frontend/index.html`, `frontend/package*.json`, `frontend/public/*`, các view Workspace (`SimulationWorkspace`, `Scene3DExplorer`, `HomeView`, `TopNav`, v.v.), `frontend/src/state/*` và các bộ test Workspace không liên quan đều được giữ nguyên trạng, không bị chạm hay stage nhầm.
- Staging tuân thủ allowlist tường minh (`git add <file>`), không dùng `git add .` hoặc `git add -A`.

---

## 3. Zero Pre-Displayed Answers Audit & Verification Proof

Toàn bộ giá trị kết quả tính toán sẵn bị phản ánh trên Landing V1.4 đã được loại bỏ khỏi tầng trình diễn bằng cấu trúc dữ liệu (không che bằng CSS `display: none`), đồng thời bảo toàn nguyên vẹn `LANDING_PYRAMID_SAMPLE.verifiedMetrics`, `LANDING_CUBE_SAMPLE.verifiedMetrics`, `equationText`, `answerBadge` cho `"prod"` và Workspace:

| Khu vực V1.4 | Trước khi sửa (Before) | Sau khi sửa (After) | Kết quả kiểm DOM thực tế |
|---|---|---|---|
| **Hero (`#landing-hero`)** | Không lộ đáp án số | Giữ sạch hoàn toàn, chỉ hiển thị nhãn hình học (`S, M, N, P, E, F`) | `leakedAnswers.hero = []` |
| **Storytelling (`#cach-hoat-dong`)** | Chặng 1 ghi `"cạnh a = 4"`, Chặng 4 ghi `"MN = 2 · PQ = 4 · MQ = NP = 2√2"` và `S(MNPQ) = 3√7` | Chuyển toàn bộ mô tả & `relationNote` sang quan hệ song song / đối xứng thuần túy; xóa `verifiedResult` & `.axo-v14-story-verified` | `stage_1..4 = []` |
| **Interactive Demo — Chóp (Bước 1–4)** | Bước 4 hiển thị 2 chip `S(MENPF) = 6√6` và `V(S.ABCD) = 32` | Thay bằng khối gợi ý quan sát trực quan `v14Focus` trên cả 4 bước `1..4` | `pyramid.step_1..4 = []` |
| **Interactive Demo — Lập phương (Bước 1–4)** | Bước 3–4 hiển thị `"2√2"`, `"12√3"` cùng chip `S(MNEPFQ) = 12√3`, `MN = 2√2` | Thay bằng chuỗi `v14StepLabel / v14Title / v14Guide / v14Focus` không chứa số liệu tính sẵn | `cube.step_1..4 = []` |
| **Closing CTA & Footer** | Mặt cầu SVG mang nhãn mô hình tĩnh + chú thích dài | WebGL 3D đa khối không nhãn/số/công thức + CTA gọn | `closing = []`, `footer = []` |

---

## 4. Hero Typography, Circle Annotation & 3D Pyramid Recovery

- **Tiêu đề 2 dòng cân đối ([`LandingHeroV14.tsx`](../../../frontend/src/components/landing/LandingHeroV14.tsx) & [`landing.css`](../../../frontend/src/components/landing/landing.css)):** Tổ chức `<h1 id="axo-v14-hero-heading">` bằng hai `<span className="axo-v14-hero-title-line">` (`display: block; white-space: nowrap`) kết hợp tỷ lệ chữ đáp ứng (`clamp(2.05rem, 3.35vw, 3.1rem)` trên desktop, `clamp(1.52rem, 6.8vw, 2.15rem)` dưới `680px`), chấm dứt hoàn toàn hiện tượng rớt từ mồ côi `"gian,"` sang dòng giữa (`3 -> 2` dòng trên `1440px` và `1920px`).
- **Vòng khoanh SVG (`"hình dung"` — [`AnnotatedHeading.tsx`](../../../frontend/src/components/landing/AnnotatedHeading.tsx)):** Nới `viewBox="0 0 344 148"`, `pathD` thoát khỏi dấu thanh tiếng Việt và chữ kế cận (`padding: 0 0.24em` trên `.axo-v14-anno-circle`, khung SVG `height: 146%`).
- **Khối chóp `S.ABCD` 3D thống nhất (`HeroSpatialStage`):**
  - Hợp nhất phần chóp trên và phần cụt dưới (`capLift = 0`), giữ độ mờ mặt có kiểm soát (`lowerMat = 0.30`, `upperMat = 0.14`, `HERO_SECTION_FILL_OPACITY = 0.28`, mặt phẳng xanh `0.14`, biên cắt `margin = 0.26` via `computeBoundedPlaneQuad`).
  - Đặt camera nghiêng 3D chuẩn mực `[10.4, 6.3, -10.8]` (`fov = 33`, `lookAt = [lookX, lookY + 0.18, lookZ]`).
  - Tính toán động **cạnh thấy (nét liền `#191918`) vs cạnh khuất (nét đứt `#615d59`, đường cao `SA` xanh `#0075de`)** theo hướng pháp tuyến ngoài của 5 mặt chóp tới camera trên đủ 8 cạnh (`AB, BC, CD, DA, SA, SB, SC, SD`).
  - Đổi hướng đẩy nhãn điểm `S, M, N, P, E, F` theo phương xuyên tâm ra ngoài tâm hình chóp, loại bỏ chạm chữ `E` vào cạnh `ME` trên desktop lẫn `390px` mobile.
  - Kịch bản 4 nhịp hữu hạn `HERO_STORYBOARD_MS = 3800` tự dừng về `0` idle RAF; đổi định danh `shadowOuter*`/`shadowInner*` thành `haloOuter*`/`haloInner*` để tuân thủ rule vệ sinh CSS/lint.

---

## 5. Scroll-Driven Storytelling Architecture

- **Hành lang cuộn 1 khung nhìn ([`LandingStorytellingV14.tsx`](../../../frontend/src/components/landing/LandingStorytellingV14.tsx)):** Thay thế danh sách `<li>` xếp cao `2053px` (chữ cũ mờ `0.44` và nhiều khoảng trắng chết) bằng `.axo-v14-story-runway` (`245svh` desktop / `210svh` mobile) bọc một khung `.axo-v14-story-sticky` duy nhất giữ cố định cả tiêu đề vùng, sân khấu SVG `PrismEditorialStage` lẫn ô nội dung từng chặng.
- **Dissolve không chồng chữ (`computeChapterEnvelope`):** Phân hoạch tiến độ `[0, 1]` thành 4 khoảng rời nhau hoàn toàn qua khoảng đệm chết `0.004` quanh `0.25, 0.50, 0.75` kết hợp `visibility: hidden` cho chặng không hoạt động, đảm bảo tại mọi mốc cuộn xuôi lẫn ngược có tối đa **1** chặng hiển thị (`fwdMax = 1`, `revMax = 1` qua 21 điểm kiểm tra).
- **Làm nổi bật mạch suy luận Chặng 3 (`parallelCue`):** Khi làm rõ quan hệ `MN ∥ BC ⇒ PQ ∥ BC` và tìm `Q ∈ BB′`, các cạnh trên không tham gia (`A′B′, A′C′, B′C′, AA′`) giảm độ đậm (`*(1 - 0.42 * pose.parallelCue)`), đồng thời dịch tâm lăng trụ xuống `cy = 236` để đỉnh `C′` thoáng trên cả desktop lẫn `390px` mobile.
- **Giảm chuyển động (`prefers-reduced-motion: reduce`):** Gỡ sticky runway, xếp 4 chặng thành cột tĩnh dễ đọc với `opacity: 1`.

---

## 6. Interactive Demo Streamlining & Cube Plane Framing

- **Tách riêng trình diễn V1.4 ([`LandingInteractiveDemo.tsx`](../../../frontend/src/components/landing/LandingInteractiveDemo.tsx)):** Khi `presentation === "v14"`:
  - Xóa hoàn toàn khối chip đáp án `.axo-sp-demo-metrics` khỏi cả 4 bước của Chóp và Lập phương, thay bằng thẻ câu dẫn quan sát `.axo-v14-demo-focus-note`.
  - Gỡ tiêu đề lặp lại phía trên canvas (chỉ giữ nút ngữ cảnh `#btn-landing-demo-reset` khi người dùng đã xoay góc nhìn).
  - Gỡ dòng gợi ý đáy canvas (`bottomHint={undefined}`), đổi nút bước thành `1..4` (`tabular-nums`) và dùng nút capsule `.axo-v14-btn .axo-v14-btn-primary` cho `"Mở trong Xưởng 3D"`.
- **Cân khung mặt cắt Hình lập phương ([`landing-geometry-data.ts`](../../../frontend/src/components/landing/landing-geometry-data.ts) & [`LandingHeroScene3D.tsx`](../../../frontend/src/components/landing/LandingHeroScene3D.tsx)):** Thu gọn lề mặt cắt lục giác đều `0.36 -> 0.26`, tinh chỉnh `v14CameraPos` / `v14LookAt` riêng cho V1.4 và hạ độ mờ mặt/cắt (`baseFaceMat = 0.30`, `sideFaceMat = 0.20`, `planeFillMat = 0.14`, `secFillMat = 0.28`) để góc nhọn mặt phẳng cắt không còn chạm mép trên khung 3D.

---

## 7. Closing CTA Redesign (WebGL Multi-Solid Composition)

- **Thay thế hoàn toàn Mặt cầu SVG cũ bị từ chối:** Viết lại [`LandingClosingScene3D.tsx`](../../../frontend/src/components/landing/LandingClosingScene3D.tsx) bằng một cảnh WebGL Three.js 3D độc lập (`data-cta-visual="spatial-multi-solid-3d"`) gồm hai khối hình học tách bạch trong không gian:
  1. **Lăng trụ lục giác đều đứng (`Lăng trụ lục giác đều`)** có mặt đứng/cạnh thấy-khuất tính động theo pháp tuyến, bị một mặt phẳng xanh cắt xiên theo phương trình chuẩn tạo thiết diện lục giác cam trong mờ (`CLOSING_SECTION_FILL_OPACITY = 0.28`, sai số đồng phẳng `< 1e-6` trên cả 6 đỉnh).
  2. **Hình nón tròn xoay (`Hình nón`)** đặt lệch sang phải (`solidCenterGap = 3.666 > 1.42 + 1.20`), thể hiện sinh đường biên động theo góc nhìn camera, đường tròn đáy nửa liền nửa đứt, đường cao đứt khúc `O–S`, bán kính đáy kèm góc vuông tại `O` và vòng tròn thiết diện ngang song song đáy.
- **Không chữ, không đáp án, tối ưu vòng đời GPU:** Tuyệt đối `0` nhãn đỉnh hay số liệu trên cảnh kết; kịch bản 4 nhịp `CLOSING_STORYBOARD_MS = 3400` tự dừng về `0` idle RAF, tạm dừng bằng `IntersectionObserver` + `visibilitychange`, hỗ trợ pointer tilt + `webglcontextlost`/`restored`, dọn toàn bộ geometry/material/renderer qua `.dispose()`, và giữ `<ClosingFallbackSvg />` đồng bộ khi `?no_webgl=1` hoặc SSR.
- **Đồng bộ copy & CTA ([`LandingClosingV14.tsx`](../../../frontend/src/components/landing/LandingClosingV14.tsx)):** Chuẩn hóa tiêu đề `"Đưa bài toán của bạn vào không gian 3D."` và lead ngắn `"Nhập đề bài tiếng Việt hoặc khám phá các mô hình có sẵn trong thư viện."`.

---

## 8. Restored Owner-Approved UI Decisions & Design System Compliance

- Bảo toàn thiết kế đã được Owner chấp nhận: nền phân lớp phẳng `#ffffff` (`--canvas`) xen `#f6f5f4` (`--axo-sp-paper`), nút CTA dạng capsule (`var(--rounded-full)`), nút chính xanh `#0075de` (`--axo-sp-accent`) và nút phụ viền hairline trung tính.
- Toàn bộ giao diện V1.4 đạt `100% Inter` (chuyển cả nhãn đỉnh trong Demo `.is-v14` từ monospace sang `var(--font-family)`), xóa bóng đổ tĩnh trên workbench `.is-v14` và trên tab chọn mẫu `.axo-sp-sample-pill.is-active`, bỏ các vạch chia `1px` thừa ở Footer và thanh trạng thái Storytelling để phân tách hoàn toàn bằng mảng màu và khoảng thở.
- Nâng độ tương phản chữ dẫn (`--ink-secondary`, `#31302e`) với kích thước body tính toán `18.2px / 1.62` trên desktop.

---

## 9. Hover, Active, Focus & Reduced-Motion System

- Desktop hover nâng nhẹ `-1px` (`matrix(1, 0, 0, 1, 0, -1)`), trở về chính xác `none` khi rời chuột (`resetClean: true`); chặn nâng dưới `@media (hover: none)` cho màn hình cảm ứng.
- Thêm trạng thái `.axo-v14-btn:disabled` (`opacity: 0.52; cursor: not-allowed; transform: none;`), bảo toàn `:focus-visible` `2px solid var(--axo-sp-accent)`.
- Kiểm chứng trực tiếp với `emulateMedia({ reducedMotion: "reduce" })` cùng `?no_webgl=1`: tắt WebGL (`0` `<canvas>`), hiển thị `<HeroFallbackSvg />` & `<ClosingFallbackSvg />`, toàn bộ 4 chặng Storytelling hiện tĩnh (`opacity: 1`).

---

## 10. Frontend Version Lifecycle & Dead Code Consolidation Audit

- **Đã gỡ bỏ khỏi codebase và CSS:** `verifiedResult`, `.axo-v14-story-verified`, `.axo-v14-story-chapter-eyebrow`, `.axo-v14-closing-stage`, `.axo-v14-closing-svg`, toàn bộ nhóm `.axo-v14-svg-sphere-*`, logic mặt cầu 3-4-5 cũ và hàm tách rời chóp Hero (`capLift > 0`).
- **Tài sản sống còn hiệu lực:**
  - Tuyến Production V1.2.2 (`/` & `/gioi-thieu`): `LandingHeader`, `LandingHeroSculpture3D`, `LandingStorytelling`, `LandingExplainerAnimation`, `LandingInteractiveDemo (default)`, `LandingClosingSculpture` — **giữ nguyên 100%**.
  - Tuyến Preview V1.4 (`?preview=v1.4`): `LandingPreviewV14`, `LandingHeroV14`, `LandingStorytellingV14`, `LandingInteractiveDemo (v14)`, `LandingClosingV14`, `LandingClosingScene3D`, `AnnotatedHeading`.

---

## 11. Reference Inspiration & Live REA Evidence Ledger

| Nguồn tham chiếu / Mục tiêu | Phương thức quan sát | REA `evidence_id` | Ghi nhận & Trạng thái |
|---|---|---|---|
| `https://bundaumayo.top/` | REA MCP Live Capture | `ev_c4e556653832a8ee5b913b4767bb672c13c202144481d92bceece53a61c6a7df` | `VERIFIED_BY_REA` (`screenshot_sha256: 9021be38c81aa4cfb2e102bffe343e0abd363ab982d3a039939245fa10e004fa`, 19 SVG tags, nhịp kể chuyện tinh gọn) |
| `https://tympanus.net/codrops/` | REA MCP Live Capture | `ev_4488f53a8ca5a2492984f9035ca275c12075ad12985d2fa7eafca6bba506d147` | **BLOCKED (`cloudflare_blocked: True`, `"Just a moment..."`)** — dừng thu thập đúng quy tắc (`NOT VERIFIED`) |
| Reference baselines tái sử dụng | Prior session REA captures | `ev_00bfec5d265fe2c546c16e84857f88f1d344dbe13c9a5539e39a236a54446b38` (figma), `ev_1df5680b7ded55d09475d351a5223502bbf71945a05dff6f999d57f9c2b71337` (rive), `ev_746e5c5db388b220472cd8c90c17b3cc6c8f91d74` (`pudding.cool`), `ev_978001f011cc715aecfc072364283f78e8446ddd068e6dfff9d077ebc5e893d6` (`pudding.cool/2026/11/pi/`), `ev_da305007bad000f66628b2d8e858d8275bbe095c45c8a400ab0c9dc555b0e3fa` (lusion) | `VERIFIED_BY_REA` (baseline từ phiên trước trong cùng mạch thiết kế V1.4) |
| **Post-Change Live V1.4 (`http://localhost:3001/gioi-thieu?preview=v1.4`)** | REA `list_browser_targets` | `ev_cc203c460ef2b1f2dd86f5cdb57b2a23071d20f645ccca35cd5c02575fd97872` | `VERIFIED_BY_REA` (CDP target `HeadlessChrome/151.0.7922.34`) |
| **Post-Change Live V1.4 Screenshot** | REA `capture_web_screenshot` | `ev_0bc8ac70333a61b73cae1be24c1c1ff015ca3f5e38dec217a5d415b33b137222` | `VERIFIED_BY_REA` (`screenshot_sha256: 3a89a83573fe72d8c6d117436ac30c8a2e6de5a324df6dc1c18a0c355c8d040a`) |
| **Post-Change Live V1.4 DOM & Page** | REA `inspect_web_page` | `ev_61a2e3bc900395f2384c218b6bd460118ed1fe48db9439f711a86940d859c456` | `VERIFIED_BY_REA` (DOM, accessibility, scripts, console, resources) |

---

## 12. `design-taste-frontend` Lint & Live Render Inspection Results

- **Source Lint (`lint.mjs` trên 5 file TSX V1.4):** `RESULT: 0 FAIL, 0 WARN` (`AnnotatedHeading.tsx`, `LandingHeroV14.tsx`, `LandingStorytellingV14.tsx`, `LandingClosingScene3D.tsx`, `LandingClosingV14.tsx`). (`LandingInteractiveDemo.tsx` dòng `64` giữ điều kiện `{!isV14 && <p className="axo-sp-eyebrow">` chỉ render cho bản `"prod"` V1.2.2.)
- **Live Render Inspection (`inspect.mjs --allow few-pictures,no-footage --wait=1800`):** `RESULT: 0 FAIL, 3 WARN` (`size-count`, `dev-server`, `outlined-box`). Các lỗi từ lượt đo trước (`mono`, `shadow`, `button-fx`, `hairline`, `covered-text`, `grey-body`) đều đã về **`0 FAIL`**. (Cờ `--allow few-pictures,no-footage` được khai báo minh bạch vì Axo là công cụ mô phỏng toán học 3D WebGL thời gian thực, không sử dụng ảnh stock hoặc video trang trí ngoài mục đích sản phẩm.)

---

## 13. Mathematical & Geometric Invariants Proof

- **Hero Chóp `S.ABCD` (`landing-hero-visual-lifecycle.test.tsx`):** `computeTrueShapeSection2D` bảo toàn đẳng cự 5 cạnh ngũ giác `MENPF` với `maxDeviation < 1e-4`; khối thống nhất (`capLift = 0`), mặt phẳng cắt giới hạn gọn (`margin = 0.26`).
- **Storytelling Lăng trụ `ABC.A′B′C′` (`landing-storytelling-geometry.test.tsx`):** Hệ tọa độ miền giữ nguyên hoàn toàn bất biến (`MN = 2`, `PQ = 4`, `MQ = NP = 2√2`, `MN ∥ PQ`, `S(MNPQ) = 3√7`), tách bạch tuyệt đối khỏi phần chữ bề mặt Landing.
- **Closing Multi-Solid (`landing-cta-geometry.test.tsx`):**
  - Toàn bộ 6 đỉnh thiết diện lục giác đều nằm trên mặt phẳng cắt với `prismPlanarResiduals < 1e-6`, mọi cao độ giao điểm nằm chặt trong `(y_bottom, y_top)`.
  - Bán kính vòng cắt ngang hình nón thỏa chính xác định lý Thales `R * (1 - t)`.
  - Khoảng cách giữa 2 tâm đáy `solidCenterGap > 1.42 + 1.20` đảm bảo 0 chồng lấn hình khối.

---

## 14. 8-Viewport Responsive Matrix

| Viewport | `h1` số dòng (`h1EstimatedLines`) | Chiều cao `h1` (`px`) | Độ rộng SVG khoanh tròn (`px`) | Tràn ngang (`overflowPx`) | Trạng thái |
|---|---|---|---|---|---|
| `desktop-1920` (`1920×1080`) | `2` | `123` | `294` | `0` | `PASS` |
| `desktop-1440` (`1440×900`) | `2` | `120` | `286` | `0` | `PASS` |
| `laptop-1366` (`1366×768`) | `2` | `113` | `271` | `0` | `PASS` |
| `tablet-landscape-1024` (`1024×768`) | `2` | `85` | `203` | `0` | `PASS` |
| `tablet-portrait-768` (`768×1024`) | `2` | `81` | `194` | `0` | `PASS` |
| `mobile-390` (`390×844`) | `2` | `67` | `157` | `0` | `PASS` |
| `mobile-360` (`360×800`) | `2` | `62` | `145` | `0` | `PASS` |
| `mobile-320` (`320×568`) | `2` | `61` | `144` | `0` | `PASS` |

---

## 15. Accessibility, Keyboard & Fallback Verification

- **No-WebGL + Reduced Motion (`?preview=v1.4&no_webgl=1` & `prefers-reduced-motion: reduce`):** `heroFallbackSvg: true`, `closingFallbackSvg: true`, `storyChaptersAllReadable: true` (toàn bộ 4 chặng đạt `opacity: 1`), `zeroCanvas: true`.
- **Keyboard & Focus:** `tablist` Bước `1..4` và Chọn mẫu hỗ trợ phím mũi tên & `:focus-visible`, cấu trúc heading ngữ nghĩa đầy đủ (`h1 -> h2 -> h3`).

---

## 16. Dual-Backend Performance & GPU Budget

So sánh trực tiếp trước/sau trên `verify-v14-product-after.mjs` vs `before-audit.json` (tất cả lỗi 401 là mock HTTP `/api/auth/me` cho trạng thái Guest; **`nonAuthConsoleErrors = []`**, **`pageErrors = []`**):

| Hồ sơ kiểm thử | Thời gian tải (`loadMs`) | Idle RAF sau dừng (`idleProbe500msFrames`) | WebGL contexts đang sống | FPS cuộn trung bình | Max Frame (`ms`) | Khung > 50ms |
|---|---|---|---|---|---|---|
| **Before:** SwiftShader Desktop `1440×900` | `2109 ms` | — | `1` (chỉ Hero) | `58.1 fps` | `50.1 ms` | `1` |
| **After:** SwiftShader Desktop `1440×900` | `2225 ms` | **`0`** | `2`–`3` (Hero + Demo + Closing) | `57.3 fps` | `116.6 ms` | `1` |
| **Before:** Hardware GPU D3D11 `1440×900` | `2100 ms` | — | `1` | `54.8 fps` | `83.3 ms` | `2` |
| **After:** Hardware GPU D3D11 `1440×900` | `2294 ms` | **`0`** | `2`–`3` | `55.4 fps` | `116.7 ms` | `2` |
| **Before:** SwiftShader `390×844` `4x CPU` (`NOT_PHYSICAL_MOBILE`) | `3426 ms` | — | `1` | `54.0 fps` | `116.7 ms` | `2` |
| **After:** SwiftShader `390×844` `4x CPU` (`NOT_PHYSICAL_MOBILE`) | `3931 ms` | **`0`** | `2`–`3` | `55.2 fps` | `133.4 ms` | `1` |

---

## 17. Production V1.2.2 & Workspace Non-Regression Proof

- **Production `/` & `/gioi-thieu`:** `prodV122Ok: true` (`prod_v122_nonregression_1440.png` xác nhận giữ nguyên bản V1.2.2, không chứa `.axo-v14-root`, vẫn giữ `axo-sp-closing-sculpture`).
- **Axo Workspace (`/app`):** Nhấn `#btn-landing-open-showcase-3d` từ mẫu Hình lập phương trên V1.4 mở chuẩn xác Workspace tới bước 12/12 (`workspaceOpenedOk: true`, `workspace_app_nonregression_1440.png`), bảo toàn đầy đủ bài toán, cây bước dựng và mô hình 3D.

---

## 18. Before vs After Visual Evidence & Video Artifacts Index

Thư mục artifact hội thoại: `landing_v14_recovery/` (`before/`, `after/`, `after/videos/`, `taste_draw/`, `taste_after/`):

- **Before (`landing_v14_recovery/before/`):** `before-audit.json`, `hero_desktop_1440.png`, `hero_mobile_390.png`, `story_stage1_1440.png`, `story_stage4_1440.png`, `demo_pyramid_1440.png`, `demo_cube_step4_1440.png`, `closing_cta_1440.png`, `footer_1440.png`.
- **After (`landing_v14_recovery/after/`):** `after-verification.json`, `hero_desktop_1440.png`, `hero_mobile_390.png`, `story_stage1_1440.png`, `story_stage2_1440.png`, `story_stage3_1440.png`, `story_stage4_1440.png`, `story_mobile_stage4_390.png`, `demo_pyramid_step1_1440.png`, `demo_pyramid_step4_1440.png`, `demo_cube_step1_1440.png`, `demo_cube_step4_1440.png`, `demo_mobile_cube_step4_390.png`, `closing_cta_1440.png`, `closing_cta_mobile_390.png`, `footer_1440.png`, `footer_mobile_390.png`, `fallback_nowebgl_1440.png`, `prod_v122_nonregression_1440.png`, `workspace_app_nonregression_1440.png`.
- **Video `.webm` (`landing_v14_recovery/after/videos/`):**
  - `hero_entrance_settle.webm` (`559,207 bytes`)
  - `storytelling_forward_1_to_4.webm` (`657,304 bytes`)
  - `storytelling_reverse_4_to_1.webm` (`480,713 bytes`)
  - `closing_cta_3d_settle.webm` (`483,532 bytes`)
  - `mobile_scroll_390x844.webm` (`686,173 bytes`)

---

## 19. Automated Quality Gates Summary

- **`npx tsc -b` & `npm run build`:** Exit `0` (`127 modules transformed`, `✓ built in 5.42s`).
- **`npx vitest run --testTimeout=15000 --maxWorkers=2`:** **`Test Files 191 passed (191)` · `Tests 2248 passed (2248)` · `0 failed` · `0 skipped`** (`132.86s`, gồm đầy đủ `tokens.test.ts`, `class-coverage.test.ts`, `ui-hygiene.test.ts`, `code-index-sync.test.ts`, `landing-product-integrity.test.tsx` và toàn bộ 23 tệp test landing + toàn bộ Workspace/Geometry).
- **`backend/scripts/audit_docs_information_architecture.py`:** `Internal links broken: 0`, `Docs root closed list: True (29 root docs, 167 catalogued, unclassified [])`, `EVIDENCE_INDEX valid: True`, `OPEN_ISSUES valid: True`, `Secret leaks: 0`, `Test reconciliation balanced: True`. (`CODE_INDEX stale paths: 4` nằm riêng tại các dòng `4605`, `4619`, `4634`, `4646` thuộc phạm vi xóa tệp classroom chưa commit của phiên song song — `0` stale path trong phạm vi Landing.)

---

## 20. Remaining Limitations, Promotion Checklist & Owner Sign-Off

1. **Giới hạn hiện tại:** Đánh giá di động `390×844` sử dụng giả lập CPU `4x` trong Chromium (`NOT_PHYSICAL_MOBILE`), chưa đo trực tiếp trên phần cứng điện thoại vật lý; môi trường triển khai production thực tế chưa kích hoạt (`NOT_DEPLOYED`).
2. **Điều kiện đưa V1.4 lên Production `/`:** Chỉ thực hiện chuyển tuyến mặc định khi Chủ dự án xem trực tiếp bản `?preview=v1.4`, xác nhận ưng ý Hero, Storytelling 4 chặng, Interactive Demo và Closing 3D đa khối.
3. **Trạng thái ký duyệt:**

**Owner Approval: `PENDING_OWNER_REVIEW`**
