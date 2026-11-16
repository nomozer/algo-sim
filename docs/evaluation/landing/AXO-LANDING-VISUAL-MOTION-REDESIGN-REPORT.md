# AXO LANDING — VISUAL & MOTION REDESIGN, V1.6 REFINEMENT REPORT

> **Scope:** Cô lập trên route preview `/gioi-thieu?preview=v1.4` (`LandingPreviewV14`, branch `feat/axo-geometry-library-verification`) · **Baseline HEAD:** `b769a554fee774d99e068ded748c288111bc4d13`
> **Production Routes (`/`, `/gioi-thieu`):** Bảo toàn nguyên trạng V1.2.2 (`"prod"`) · **Workspace (`/app`):** Không thay đổi
> **Owner Approval:** `OWNER_APPROVAL: PENDING_OWNER_REVIEW`

---

## 1. Baseline V1.6

- **Git baseline:** Commit `b769a554fee774d99e068ded748c288111bc4d13` (`feat(landing): AXO Landing V1.6 visual quality recovery on isolated preview`) trên nhánh `feat/axo-geometry-library-verification`.
- **Snapshot Baseline trước khi sửa (`before/before_baseline.json`):**
  - Header rest state (`1440×900`): `#landing-nav` bọc trong khung viền khép kín (`backgroundColor: rgba(247, 247, 244, 0.9)`, `border: 1px solid rgb(230, 230, 230)`, `borderRadius: 999px`). Mục active `"Giới thiệu"` dùng `font-weight: 600`; khi hover sang `"Trải nghiệm"`, `"Giới thiệu"` mất class `.is-active` và tụt về `font-weight: 500` trong khi `"Trải nghiệm"` chuyển lên `font-weight: 600`.
  - Hero: `h1FontSize = 52.56px` (`1440×900`), `26.52px` (`390×844`), `22px` (`320×568`). Hình chóp `S.ABCD` thiếu lưới đồng phẳng đáy và thiếu ký hiệu chứng minh góc nhị diện/đường vuông góc.
  - Storytelling: `storyTextCheck` ghi nhận `{ hasEdge4Claim: true, hasAllEqualClaim: true }` (`"a = 4"`, `"tất cả các cạnh bằng 4"`) — tự gán giả thiết số hóa không cần thiết ngay trên Landing.
  - Design Taste baseline trước đó (`landing_v1_6_audit/taste_after_prod/report.json`): tồn tại 3 cảnh báo/lỗi `few-pictures` (`FAIL`), `no-footage` (`WARN`), `outlined-box` (`WARN`).

---

## 2. Danh sách vấn đề đã xác nhận

1. **Header & Navigation (`LandingHeader`, `landing.css`):**
   - Khung `#landing-nav` có viền/nền hộp bao quanh toàn cụm tạo cảm giác nặng nề so với nền sáng tinh gọn.
   - Hover chéo làm mục trang hiện tại mất trạng thái đánh dấu (`.is-active` nhảy theo con trỏ) và thay đổi `font-weight` (`600 ↔ 500`), vi phạm tính ổn định thị giác.
   - Bấm `"Giới thiệu"` khi đang ở đầu trang hoặc cuộn từ dưới lên chưa bảo đảm căn sát `scrollY = 0`.
2. **Hero (`LandingHeroV14`, `landing.css`):**
   - Khối đáy `(ABCD)` chưa có lưới tọa độ đồng phẳng và ký hiệu góc vuông `AB ⊥ AD`; giao tuyến nhị diện với `K` trên `NP` thiếu hệ thống chứng minh `AK ⊥ NP`, `MK ⊥ NP`, `∠MKA` và vạch chân đường rọi `E′`, `F′`.
   - Khung dọc hẹp (`390×844`, `320×568`) cần nới khoảng thở cho đỉnh `S` và cỡ chữ `h1` mượt hơn (`30.42px` / `26.88px`).
   - Sau lần đo `inspect.mjs` đầu hậu chỉnh sửa, dòng 2 của `h1` chứa `<svg class="axo-v14-anno-svg axo-v14-anno-svg-circle">` (`top: -22%`) trùng stacking context `z-index: 2` với dòng 1 `"Hình học không gian,"` khiến `3/8` điểm kiểm tra bị hit-test (`covered-text` `FAIL` 38% ở `390×844`). Đã khắc phục bằng `.axo-v14-hero-title-line + .axo-v14-hero-title-line { z-index: 1; }`.
3. **Storytelling (`LandingStorytellingV14`, `landing.css`):**
   - Còn text `"a = 4"` / `"tất cả các cạnh bằng 4"` gây hiểu nhầm thành khẳng định số học cứng; cần phân tách vai trò nhận thức (`Giả thiết`, `Đối tượng đã dựng`, `Quan hệ quan sát được`, `Kết quả xác lập`) và `establishedState`.
   - Chiều cao lăng trụ đứng và vùng phẳng `STORY_PLANE_QUAD` cần kéo giãn tỷ lệ (`PRISM_HEIGHT_SCALE = 1.16`), nới biên độ xoay theo cuộn (`-0.36 → 0.15`), hiển thị thanh 4 bước `.axo-v14-story-rail`, ký hiệu song song `>>` và cạnh bằng nhau `||`.
   - `inspect.mjs` báo `small-text` (`WARN`, 3 khối `< 13px`) ở `.axo-v14-story-rail-label` và `.axo-v14-story-epistemic-badge` (`0.75rem = 12px`); đã nâng lên `0.8125rem` (`13px`).
4. **Demo tương tác (`LandingInteractiveDemo` + `.axo-sp-demo-section.is-v14`):**
   - Card bao ngoài lồng nhiều lớp viền/nền xám làm phân tán sự chú ý khỏi sân khấu 3D; cụm nút bước dựng và gợi ý xoay chưa theo phong cách studio nhẹ.
   - Trên mobile (`390×844`), `.axo-sp-sample-pill` (`0.78rem`) và `.axo-v14-demo-orbit-hint` (`0.75rem`) dưới `13px`; đã nâng lên `0.8125rem` (`13px`) kèm `padding: 7px 9px` giữ 2 mẫu nằm cùng 1 hàng xuống tới `360×800`.
5. **Closing & Footer (`LandingClosingScene3D`, `LandingClosingV14`, `landing.css`):**
   - Lăng trụ lục giác phần kết thiếu độ tách ánh sáng key/rim giữa các mặt và thiếu ngàm vuông góc tại pháp tuyến tâm `normalStem ⊥ Π` cùng ngàm rọi đáy tại đỉnh `[0, 2, 4]`; vòng tròn phụ trên đỉnh tách khối gây cảm giác rời rạc.
   - `scrollToLandingSection("landing-hero")` chưa dùng `window.scrollTo({ top: 0, behavior })` khi đang ở trang hiện tại; link footer cần gạch chân mượt `scaleX` từ trái sang phải.

---

## 3. Tài liệu REA và các hành vi đã thực sự kiểm chứng

- **Pre-edit REA MCP & CDP Interactive Probe (`rea/rea-redesign-before.json`):**
  - `list_browser_targets`: `ev_998de3391678d8b009e8922565c506e3b4ac439323304671a4fe8be6a662ef47`
  - Tham chiếu tương tác trước đó (`bundaumayo.top`): `ev_1a2266dabb24fa4d9c33c7731b837d2f0255f25885dd040c9ca546a51b7a6bd8`
  - `https://ciechanow.ski/` (`INTERACTIVE_VERIFIED`, cuộn tới `scrollY = 720`, ghi nhận `canvasCount = 120`, `svgCount = 0`): `inspect_web_page` `ev_f317e14d015d55899cc0c6c8fb9e6b135c250720725fe0a4cc0f8ac1348007bf`, `capture_web_screenshot` `ev_4a5c3d3aea695cc37d5e812797a36fc2251aeb59c9d372ad8718a2d36037f7cd`.
  - `https://www.notion.com/` (`INTERACTIVE_VERIFIED`, header không viền hộp ngoài, hover giữ cố định `weight = 400/500` không nhảy layout, `scrollY = 720`, `svgCount = 27`, `footerHeight = 396`): `inspect_web_page` `ev_78240584c87be58673d70a252c01917bf143e35d4c4e813cd0073bde4fad646d`, `capture_web_screenshot` `ev_158a4a7a97257ff3fa0f0001b1a69b76a811f751d721745a99ef93ba7cfa8311`.
  - Baseline `http://localhost:3001/gioi-thieu?preview=v1.4` (`INTERACTIVE_VERIFIED`, ghi nhận `"Giới thiệu"` tụt `600 -> 500` khi hover): `inspect_web_page` `ev_01a12b9b473a5f40e802e71dc0496541cfd425e9846abe0caf4a7d969be06e0b`, `capture_web_screenshot` `ev_f176743ea608df3d2c754703c9aeac7a7f92bff18050be7b70716fa925dad96f`.
  - Nguồn tham khảo `codrops` trong ledger cũ (`landing_v1_6_audit/rea/rea-v16-ledger.json`): giữ trạng thái `NOT_VERIFIED` do trả `HTTP 403`.
- **Post-edit REA MCP Verification (`rea/rea-redesign-after.json` tại `http://127.0.0.1:9239`, hover `#nav-landing-trai-nghiem` trên `http://localhost:3001/gioi-thieu?preview=v1.4`):**
  - `list_browser_targets`: `ev_2ddfe835e33215122f705102e1e9ff590ff611fb95bed44e0428fc0f39a2dd27`
  - `inspect_web_page`: `ev_45f5a09750bfb46c0413e7f068ec196344c638913bdc10a3c134e17e6db54c71` (`console_errors: 0`, `failed_requests: 0`)
  - `capture_web_screenshot`: `ev_c26444d4580d044de6288e6cd4fc1c5f26d5f1eb0f8d2a001b6508f7ba1a8e04` (`rea/after_localhost_3001.png`, `95656` bytes, SHA256 `c2295cbd7bcf0e9ebb9848cd630a9fc80d9e9ebe2844e82693aa0000636eec45`) — ảnh chụp xác nhận mục active `"Giới thiệu"` giữ màu nhấn kèm gạch đáy nhỏ gọn trong khi pill hover nằm êm dưới `"Trải nghiệm"`.

---

## 4. Lý do chọn hướng thiết kế

Tiếp tục nhất quán định hướng **Spatial Editorial: Geometry in Motion** kết hợp **Epistemic Honesty**:

1. **Làm sạch khung điều hướng và hộp bao:** Gỡ viền bao nav và viền card ngoài của Demo giúp mắt đi thẳng vào typography và hình khối 3D thay vì phân tách thành các hộp giao diện lồng nhau kiểu dashboard.
2. **Tương phản nhận thức rõ ràng trong hình học không gian:** Trên Hero và Closing 3D, mọi nét phụ trợ (lưới đáy, đường vuông góc `AK ⊥ NP`, `MK ⊥ NP`, góc nhị diện `∠MKA`, dây rọi `EE′`/`FF′`, pháp tuyến `normalStem ⊥ Π` và ngàm rọi đỉnh đáy) đều phục vụ giải thích quan hệ không gian chứ không phải trang trí rời khối.
3. **Không bịa giả thiết số học trên Landing:** Thay vì ghi `"a = 4"` làm người xem hiểu nhầm mọi chóp/lăng trụ đều cố định độ dài, Storytelling nêu minh bạch vai trò nhận thức (`Giả thiết`, `Đối tượng đã dựng`, `Quan hệ quan sát được`, `Kết quả xác lập`) đúng tinh thần bài toán tổng quát của Axo.
4. **Hiệu năng và tính ổn định DOM:** Giữ nguyên kiến trúc 1 `WebGLRenderer` mỗi canvas mount, 0 RAF chạy ngầm sau khi kịch bản dừng (`rafTicksDuringIdle1s: 0`), không đổi `font-weight` khi hover nav (`maxWidthShiftPx: 0`), mọi chữ đọc có cỡ tối thiểu `13px` (`0.8125rem`).

---

## 5. Những gì giữ, thay đổi và loại bỏ (Kiểm kê PHA 11)

| Module / Tập tin | Trạng thái PHA 11 | Vai trò & Thay đổi |
| :--- | :--- | :--- |
| `frontend/src/components/landing/LandingView.tsx` | `KEEP` | Bản production V1.2.2 tại `/` và `/gioi-thieu`, giữ nguyên 100% |
| `frontend/src/components/landing/LandingStorytelling.tsx` | `KEEP` | Thành phần storytelling của production V1.2.2 |
| `frontend/src/components/landing/LandingHeroSculpture3D.tsx` | `KEEP` | Điêu khắc Hero của production V1.2.2 |
| `frontend/src/components/landing/LandingClosingSculpture.tsx` | `KEEP` | Điêu khắc Closing của production V1.2.2 |
| `frontend/src/components/landing/LandingExplainerAnimation.tsx` | `KEEP` | Thành phần minh họa của production V1.2.2 |
| `frontend/src/components/landing/LandingIllustrationAccents.tsx` | `KEEP` | Thành phần điểm nhấn của production V1.2.2 |
| `frontend/src/components/landing/AnnotatedHeading.tsx` | `KEEP` | Giữ nguyên component chú thích typography biểu cảm V1.6 (`circle`/`underline`/`highlight`) |
| `frontend/src/components/landing/LandingHeroScene3D.tsx` | `KEEP` | Khung `SpatialSceneCanvas` dùng chung + lifecycle WebGL đơn nhất mỗi mount |
| `frontend/src/components/landing/landing-geometry-data.ts` | `KEEP` | Dữ liệu tọa độ mẫu `chop-thiet-dien-ba-diem`, `lap-phuong-thiet-dien-bat-ky`, `LANDING_PRISM_STORY_SPEC` |
| `frontend/src/components/landing/LandingInteractiveDemo.tsx` | `KEEP` + CSS `REDESIGN` | JSX giữ nguyên hợp đồng `presentation="v14"`; lớp `.axo-sp-demo-*.is-v14` trong `landing.css` bỏ viền hộp ngoài, gộp floating badge & capsule step dock |
| `frontend/src/components/landing/LandingPreviewV14.tsx` | `REDESIGN` | Truyền `<LandingHeader presentation="v14" />` cho preview V1.6 |
| `frontend/src/components/landing/LandingHeader.tsx` | `REDESIGN` + `RESTORE` hover | Hỗ trợ `presentation="v14"` (`is-v14`, `data-nav-hover-state`), giữ `.is-current-section` khi di chuột chéo, cuộn về `top: 0` cho `landing-hero` |
| `frontend/src/components/landing/LandingHeroV14.tsx` | `REDESIGN` | Bổ sung lưới `(ABCD)` `4×4`, `AB ⊥ AD`, minh chứng `K = (N+P)/2` (`AK ⊥ NP`, `MK ⊥ NP`, `∠MKA`), `E′`/`F′` và căn chỉnh `lookY + 0.28`, apex `S` (`py - 20`, `padTop = 14`), đồng bộ `<HeroFallbackSvg />` |
| `frontend/src/components/landing/LandingStorytellingV14.tsx` | `REDESIGN` | Gỡ bỏ `"a = 4"` / `"tất cả các cạnh bằng 4"`; thêm `epistemicRole`, `establishedState`, `.axo-v14-story-rail`, `PRISM_HEIGHT_SCALE = 1.16`, `STORY_PLANE_QUAD`, yaw `-0.36 → 0.15`, `k = [0.06, 0.32, 0.58, 0.84]`, dấu `>>` và `||` |
| `frontend/src/components/landing/LandingClosingScene3D.tsx` | `REDESIGN` | Tăng tương phản shading key/rim (`0.72 + key * 0.28 + rim * 0.12`), ngàm pháp tuyến tâm `normalStem ⊥ Π`, thay vòng tròn đỉnh rời `1.08 * R` bằng ngàm rọi đáy tại đỉnh `[0, 2, 4]`, đồng bộ `<ClosingFallbackSvg />` |
| `frontend/src/components/landing/LandingClosingV14.tsx` | `REDESIGN` | `scrollToLandingSection("landing-hero")` gọi `window.scrollTo({ top: 0, behavior })` khi `window.scrollY > 0` |
| `frontend/src/components/landing/landing.css` | `REDESIGN` | CSS `.axo-sp-header.is-v14` / `.axo-sp-nav.is-v14`, stacking `.axo-v14-hero-title-line`, mobile typography/spacing (`30.42px` tại `390px`, `26.88px` tại `320px`), `story-rail` & badge `>= 0.8125rem` (`13px`), `.axo-sp-demo-*.is-v14` studio, underline `scaleX` footer |
| Các phần tử bị loại bỏ khỏi Preview V1.6 | `OBSOLETE` (trong preview) | Viền hộp bao `#landing-nav`, thay đổi `font-weight: 600 ↔ 500` khi hover, text `"a = 4"` / `"tất cả các cạnh bằng 4"`, vòng đỉnh rời `1.08 * R` trên lăng trụ Closing, khung card xám bao ngoài Demo |
| Các module Landing V1.2.2 | `DELETE_AFTER_APPROVAL` | Chỉ xem xét hợp nhất/dọn trong nhiệm vụ riêng **sau khi Owner phê duyệt**; không xóa ở nhiệm vụ này |
| File song song trong worktree (`backend/**`, `docs/EVIDENCE_INDEX.md`, `docs/evaluation/geometry/runs/axo-*`, `SimulationWorkspace.tsx`, `TopNav.tsx`, `HomeView.tsx`, `LeftSidebar*`, `attachment-fidelity*`, `v9*`) | `OWNERSHIP_BLOCKED` | Không đụng chạm, không stage, không sửa |

---

## 6. So sánh Before/After theo từng khu vực

| Khu vực | Before (Baseline V1.6) | After (V1.6 Refinement) |
| :--- | :--- | :--- |
| **Header** | `#landing-nav` có nền `rgba(247, 247, 244, 0.9)` + viền `1px solid rgb(230, 230, 230)`; hover sang `"Trải nghiệm"` làm `"Giới thiệu"` mất `.is-active` và nhảy `font-weight: 600 → 500`. | Thanh nav mở trực tiếp trên nền header (`is-v14`), `font-weight: 500` cố định (`maxWidthShiftPx = 0`). Khi hover mục khác (`data-nav-hover-state="other"`), `"Giới thiệu"` giữ `.is-current-section` cùng vạch đáy `::after` (`bottom: 1px`), pill `paper` trượt mượt dưới mục đang hover và trở về êm khi rời chuột. |
| **Hero** | Đáy chóp `(ABCD)` thưa nét phụ trợ, chưa có lưới & chứng minh góc nhị diện tại `NP`; `h1` `52.56px` / `26.52px` / `22px`; đường vòng `circle` của dòng 2 đè hit-test dòng 1 trên `390px` (`covered-text` 38%). | Có lưới đồng phẳng `(ABCD)` `4×4`, ký hiệu vuông `AB ⊥ AD`, trung điểm `K` với `AK ⊥ NP`, `MK ⊥ NP`, cung góc nhị diện `∠MKA`, vạch chân `E′`/`F′`; tỷ lệ `h1` cân đối (`47.81px` `@1440`, `30.42px` `@390`, `26.88px` `@320`), thoáng đỉnh `S` và `covered-text = 0`. |
| **Storytelling** | Tự gán `"a = 4"` và `"tất cả các cạnh bằng 4"`; rail/badge cỡ `12px` (`small-text` `WARN`). | Phân vai nhận thức minh bạch (`Giả thiết`, `Đối tượng đã dựng`, `Quan hệ quan sát được`, `Kết quả xác lập`), `0` đáp án/giả thiết số học bịa thêm (`forbidden: 0`), thanh tiến trình 4 chặng & badge `13px` (`0.8125rem`) không bị cắt chữ, `PRISM_HEIGHT_SCALE = 1.16`, xoay cuộn `-0.36 → 0.15`, dấu song song `>>` và bằng nhau `||`. |
| **Demo** | Khối Demo lồng trong box xám ngoài; nút mẫu đen đặc nặng; nhãn mobile `12.48px` / `12px`. | Bố cục studio mở không viền hộp ngoài (`.axo-sp-demo-workbench.is-v14`), thanh `4` bước dạng viên thuốc đồng bộ accent, huy hiệu `Kéo để xoay 3D` nổi gọn (`13px`), nút chọn mẫu 1 hàng xuống tới `360×800` (`pillsSameRow: true`), xếp dọc sạch ở `320×568` (`@media (max-width: 350px)`). |
| **Closing** | Lăng trụ lục giác thiếu độ sâu key/rim, còn vòng tròn phụ trên đỉnh tách khối. | Shading key/rim rõ các mặt, ngàm vuông góc tại pháp tuyến tâm `normalStem ⊥ Π`, 3 ngàm rọi đáy tại đỉnh `[0, 2, 4]`, đồng bộ SVG fallback `?no_webgl=1`. |
| **Footer** | Link chân trang đổi màu tĩnh; nút về đầu trang chỉ `scrollIntoView`. | Link footer có vạch gạch chân `scaleX` trượt trái sang phải khi hover/focus; `#btn-landing-footer-top` cuộn chính xác về `backToTopScrollY: 0` trên cả `1440×900` và `390×844`. |

---

## 7. Video tương tác tương ứng

Toàn bộ 7 video `.webm` đã được ghi trực tiếp từ Playwright sau bản sửa CSS cuối cùng (thư mục `landing_v1_6_redesign/videos/` thuộc Artifact Directory):

1. `01_header_hover_all_items.webm` (`645,413` bytes): Kiểm chứng hover tuần tự từ `"Giới thiệu"` → `"Cách hoạt động"` → `"Trải nghiệm"` → rời chuột; pill di chuyển mượt, `"Giới thiệu"` giữ trạng thái hiện tại + vạch đáy, không giật rộng chữ.
2. `02_hero_load_and_motion.webm` (`691,839` bytes): Kiểm chứng Hero load, diễn tiến dựng mặt cắt `MENPF`, dây rọi và dừng sạch ở `section-settled` với `rafTicksDuringIdle1s = 0`.
3. `03_storytelling_scroll_forward_4_stages.webm` (`825,371` bytes): Kiểm chứng cuộn xuôi mượt qua đủ 4 chặng (`01 · Đề bài` → `02 · Dựng hình` → `03 · Quan hệ` → `04 · Kết quả`), chỉ 1 chương hiện tại rõ nét và mô hình lăng trụ xoay liên tục theo scroll.
4. `04_storytelling_scroll_reverse.webm` (`818,065` bytes): Kiểm chứng cuộn ngược từ Chặng 4 về Chặng 1, chuyển trạng thái đối xứng không nhấp nháy hay mất đường.
5. `05_demo_switch_models_orbit_steps.webm` (`798,979` bytes): Kiểm chứng chuyển giữa `"Hình chóp S.ABCD"` và `"Lập phương ABCD.A′B′C′D′"`, xoay 3D và bấm đổi bước `1..4`.
6. `06_closing_animation_and_footer.webm` (`1,310,311` bytes): Kiểm chứng nhịp dựng lăng trụ lục giác `Closing`, hover link Footer và bấm `"Về đầu trang"` cuộn thẳng lên `top: 0`.
7. `07_mobile_navigation_and_scroll.webm` (`414,378` bytes): Kiểm chứng giao diện di động `390×844`, ngăn kéo menu, thanh mẫu Demo và cuộn mượt không `overflowX`.

---

## 8. Kết quả kiểm thử kỹ thuật

| Bộ kiểm thử / Công cụ | Phạm vi & Cách chạy | Kết quả thực tế (sau edit cuối) |
| :--- | :--- | :--- |
| TypeScript (`npx tsc -b`) | Toàn bộ `frontend/` | **PASS** — exit `0`, `0` lỗi kiểu |
| Production Build (`npx vite build`) | Toàn bộ `frontend/` | **PASS** — exit `0`, 127 modules, `dist/index.html` + `assets/index-Bz2xWNnn.css` (`423.76 kB`) trong `7.79s` |
| Vitest (`npx vitest run --testTimeout=20000`) | Toàn bộ unit/integration/browser suite `frontend/` | **PASS** — `191 / 191` files passed, `2249 / 2249` tests passed (`129.46s`, `0` failed, `0` skipped) |
| Playwright Matrix (9 viewport) | `1920×1080`, `1440×900`, `1366×768`, `1024×768`, `768×1024`, `430×932`, `390×844`, `360×800`, `320×568` + `?no_webgl=1` + `reducedMotion` | **PASS** — `overflowX = 0`, `forbidden = 0`, `errorCount = 0` trên đủ 9/9 viewport; `pillsSameRow = true` từ `1920px` xuống `360px` (`false` có chủ đích ở `320px`); `rafTicksDuringIdle1s = 0`; `backToTopScrollY = 0` (`1440×900`, `390×844`) |
| Kiểm tra hồi quy route (`/`, `/gioi-thieu`, `/app`) | Playwright runtime check | **PASS** — `/` và `/gioi-thieu` giữ V1.2.2 (`hasV14Root: false`, `hasLandingStoryScene: true`); `/app` giữ nguyên Workspace (`hasAppWorkspace: true`); `0` lỗi console/pageerror |
| Design Taste Lint (`lint.mjs`) | 8 file `.tsx` Landing | **PASS** — `0 FAIL, 0 WARN` |
| Design Taste Inspect (`inspect.mjs`) — **Prod Preview** (`http://127.0.0.1:4179`) | `1440`, `768`, `390` trên `vite preview` | Exit `1` — **đã sạch hoàn toàn** `covered-text`, `small-text`, `outlined-box`; chỉ còn 2 mục cấu trúc do trang dùng 3D/SVG thuần: `few-pictures` (`FAIL`) và `no-footage` (`WARN`) |
| Design Taste Inspect (`inspect.mjs`) — **Dev Server** (`http://localhost:3001`) | `1440`, `768`, `390` | Exit `1` — `few-pictures` (`FAIL`), `no-footage` (`WARN`), `dev-server` (`WARN`); `0` lỗi layout/overflow/contrast |
| Docs Sync (`npx vitest run code-index-sync`) | Kiểm đồng bộ `docs/CODE_INDEX.md` (dòng 1983) và mã nguồn Landing | **PASS** — `1 / 1` file, `3 / 3` tests passed (`45ms`) |
| Docs Architecture Audit (`python backend/scripts/audit_docs_information_architecture.py --json`) | Kiểm tra cấu trúc `docs/`, liên kết và chỉ mục | `LINKS.valid = true` (`684` links, `0` broken), `DOCS_LAYOUT.valid = true` (`29` root docs, `167` catalog, `0` unclassified), `SECRET_SCAN.valid = true` (`0` leaks), `STABLE_MUTABLE.valid = true`; `STATUS = FAIL` **duy nhất** do `CODE_INDEX.stale_path_count = 4` ở các dòng `4605, 4619, 4634, 4646` (4 file classroom `OWNERSHIP_BLOCKED` có sẵn trước phiên, không thuộc Landing) |

---

## 9. Những lỗi chưa khắc phục

1. **`inspect.mjs` — `few-pictures` (`FAIL`) và `no-footage` (`WARN`):** Bộ lọc tự động của `inspect.mjs` chỉ đếm ảnh chụp `<img>`/raster hoặc thẻ `<video>`, không tính `<canvas>` WebGL Three.js tương tác hay `<svg>` hình học chính xác là "picture", và Landing dùng dựng hình thời gian thực thay cho `<video>`. Đây là hạn chế cố hữu giữa rule ảnh/video tổng quát của tool với đặc thù WebGL 3D giáo dục toán học; không nhúng ảnh stock giả để né rule.
2. **`inspect.mjs` trên dev server (`dev-server` `WARN`):** Xuất hiện đúng bản chất khi trỏ `localhost:3001` dev; không còn xuất hiện trên bản dựng production `vite preview` (`127.0.0.1:4179`).
3. **Nguồn REA `codrops`:** Trả `HTTP 403` (`NOT_VERIFIED` từ phiên audit trước).
4. **Hạng mục `OWNERSHIP_BLOCKED` trong `CODE_INDEX.md` / worktree:** `audit_docs_information_architecture.py --json` trả `STATUS = FAIL` duy nhất tại `CODE_INDEX` với 4 stale paths có sẵn (`docs/CODE_INDEX.md:4605 -> LiveClassDock.tsx`, `4619 -> LiveClassStrip.tsx`, `4634 -> MonitorView.tsx`, `4646 -> state/classroom-sync.ts`) cùng các file classroom đang dở trong worktree ngoài phạm vi Landing; các mục này được giữ nguyên không sửa.

---

## 10. Rủi ro và giới hạn kiểm thử

- Kiểm thử WebGL trong CI/Playwright local chạy qua SwiftShader (`--use-angle=swiftshader`), chưa đo trực tiếp FPS trên nhiều GPU di động vật lý (iOS Safari/Android thực).
- Bản V1.6 Refinement chỉ bật tại `?preview=v1.4`; luồng đăng nhập OAuth thực tế hoặc chuyển giao chính thức lên `/` / `/gioi-thieu` chưa thực hiện vì còn `PENDING_OWNER_REVIEW`.
- Khả năng đọc và nhịp cuộn thực tế của Storytelling vẫn cần Owner trực tiếp duyệt qua video và trình duyệt.

---

## 11. Danh sách file thay đổi (Allowlist 13 file)

1. `frontend/src/components/landing/LandingPreviewV14.tsx`
2. `frontend/src/components/landing/LandingHeader.tsx`
3. `frontend/src/components/landing/LandingHeroV14.tsx`
4. `frontend/src/components/landing/LandingStorytellingV14.tsx`
5. `frontend/src/components/landing/LandingClosingScene3D.tsx`
6. `frontend/src/components/landing/LandingClosingV14.tsx`
7. `frontend/src/components/landing/landing.css`
8. `frontend/src/components/__tests__/landing-header-navigation.test.tsx`
9. `frontend/src/components/__tests__/landing-scroll-storytelling.test.tsx`
10. `frontend/src/components/__tests__/landing-storytelling-continuity.test.tsx`
11. `frontend/src/components/__tests__/landing-storytelling-geometry.test.tsx`
12. `docs/CODE_INDEX.md` (chỉ dòng 1983)
13. `docs/evaluation/landing/AXO-LANDING-VISUAL-MOTION-REDESIGN-REPORT.md`

---

## 12. Git diff và commit

- **Nhánh:** `feat/axo-geometry-library-verification` (rẽ trên nền baseline `b769a554fee774d99e068ded748c288111bc4d13`).
- **Tóm tắt diff trên 11 file code & test Landing trước bước cập nhật docs:** `11 files changed, 944 insertions(+), 184 deletions(-)`.
- **Chính sách tích hợp:** Chỉ stage đúng 13 file allowlist bằng `git add <file>`, không đụng file `OWNERSHIP_BLOCKED`, tạo 1 commit cục bộ trên `feat/axo-geometry-library-verification` (`feat(landing): refine V1.6 header hover, spatial hero, scroll storytelling, and studio demo`), **không merge vào `main` và không push**.

---

## 13. Trạng thái server 3001

- Vite dev server tại `http://localhost:3001` (`PID 5220`, `task-83120`) được bảo toàn nguyên vẹn trong suốt phiên, không bị tắt hay khởi động lại. Kiểm tra HTTP `200` sau commit được xác minh trước khi kết thúc.

---

## 14. Trạng thái phê duyệt

- Production `/`, `/gioi-thieu` vẫn giữ V1.2.2; `/app` không bị ảnh hưởng.
- `OWNER_APPROVAL: PENDING_OWNER_REVIEW`
