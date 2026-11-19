# AXO V1.2.1 — Auth Flow, Creative Animation & Landing Page Refinement Report

**Ngày hoàn thành:** 2026-11-15  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Worktree Frontend/Repo:** `D:\Documents\projects\axo-geometry-library`  
**Mốc nền V1.2 trước đó:** [`AXO-LANDING-V1.2-REPORT.md`](./AXO-LANDING-V1.2-REPORT.md) (`3281b934b`)  
**Owner Approval:** `PENDING_OWNER_REVIEW`

---

## 1. Tóm tắt điều hành & Cô lập phạm vi (`VERIFIED`)

Phiên **AXO V1.2.1** tiếp nối trực tiếp bản AXO Landing Page V1.2 tại `/gioi-thieu` (`/`) nhằm giải quyết triệt để năm nhóm vấn đề đã được chỉ ra sau nghiệm thu V1.2: đồng bộ trạng thái đăng nhập hai chiều giữa Landing Page và Workspace, loại bỏ nút kêu gọi hành động trùng trong giao diện di động, tái thiết kế minh họa không gian Hero theo hướng cô đọng (Concept A), thay minh họa kỹ thuật khô cứng ở mục *Cách Axo hoạt động* bằng mạch animation vector SVG 4 chặng có câu chuyện liền mạch, và tinh giản bảng tương tác mẫu 3D kèm đo đạc hiệu năng/responsive đầy đủ.

**Cô lập phạm vi Git (`Scope Isolation`):** Toàn bộ mã nguồn được commit chọn lọc (`git add <file>` từng tệp) trên đúng phạm vi Landing & Auth sync (`frontend/src/App.tsx`, `frontend/src/components/LandingView.tsx`, `frontend/src/components/landing/*`, `frontend/src/components/__tests__/landing-*.tsx`, `docs/CODE_INDEX.md` dòng `1983` và báo cáo này). Mọi thay đổi chưa commit của phiên song song trong working tree (`backend/**`, `frontend/package*.json`, `frontend/index.html`, `AuthGate.tsx`, `AxoErrorExperience.tsx`, `HomeView.tsx`, `SimulationWorkspace.tsx`, `TopNav.tsx`, `Scene3DExplorer.tsx`, `scene3d-tool-menu.tsx`, `frontend/src/state/*`, `docs/EVIDENCE_INDEX.md`, và các dòng `4605–4646` của `docs/CODE_INDEX.md`) đều được **bảo toàn nguyên vẹn**, không sửa, không stage, không khôi phục và không commit; không push remote và không merge vào `main`.

---

## 2. Sổ cái Commit V1.2.1 (`VERIFIED`)

| Thứ tự | Commit SHA | Thông điệp commit | Tệp thay đổi (theo `git log --stat`) |
|---|---|---|---|
| 1 | `9e2340c72` | `fix(axo): synchronize landing and workspace auth navigation` | `frontend/src/App.tsx`, `frontend/src/components/__tests__/landing-auth-sync.test.tsx`, `frontend/src/components/landing/landing-geometry-data.ts` |
| 2 | `5f66a2910` | `fix(axo): remove redundant mobile navigation actions` | `frontend/src/components/__tests__/landing-header-navigation.test.tsx`, `frontend/src/components/landing/LandingHeader.tsx`, `frontend/src/components/landing/landing.css` |
| 3 | `61f3f78f6` | `feat(axo): redesign hero spatial illustration` | `frontend/src/components/__tests__/landing-webgl-lifecycle.test.tsx`, `frontend/src/components/landing/LandingHeroSculpture3D.tsx`, `frontend/src/components/landing/landing.css` |
| 4 | `2533d1442` | `feat(axo): add animated product explainer storytelling` | `frontend/src/components/LandingView.tsx`, `frontend/src/components/__tests__/landing-storytelling-interaction.test.tsx`, `frontend/src/components/landing/LandingExplainerAnimation.tsx`, `frontend/src/components/landing/LandingIllustrationAccents.tsx`, `frontend/src/components/landing/LandingStorytelling.tsx`, `frontend/src/components/landing/landing.css` |
| 5 | `85f47feee` | `refactor(axo): simplify interactive demo and exact math presentation` | `frontend/src/components/__tests__/landing-demo-integrity.test.tsx`, `frontend/src/components/landing/LandingHeroScene3D.tsx`, `frontend/src/components/landing/LandingInteractiveDemo.tsx` |
| 6 | `9f7ff3286` | `style(axo): add CSS rules for explainer stage and mobile drawer button` | `frontend/src/components/landing/landing.css` |
| 7 | `d75681930` | `fix(axo): restore mobile menu focus on Escape close` | `frontend/src/components/landing/LandingHeader.tsx` |
| 8 | `59300b9b4` | `fix(axo): prevent storytelling mobile overflow and scene4 badge overlap` | `frontend/src/components/landing/LandingExplainerAnimation.tsx`, `frontend/src/components/landing/landing.css` |
| 9 | *(commit này)* | `docs(axo): add v1.2.1 verification report` | `docs/CODE_INDEX.md` (dòng `1983`), `docs/evaluation/landing/AXO-LANDING-V1.2.1-REPORT.md` |

---

## 3. Phân tích nguyên nhân gốc & Thay đổi đã triển khai (`VERIFIED`)

### 3.1. Đồng bộ xác thực & điều hướng hai chiều Landing ↔ Workspace (`9e2340c72`)
- **Nguyên nhân gốc ở V1.2:** Phiên đăng nhập giữa `/gioi-thieu` và `/app` thiếu cơ chế đối soát tập trung theo sự kiện focus/visibility và thiếu đồng bộ đa tab; luồng quay lại `/gioi-thieu` hoặc khi session hết hạn trả `HTTP 401` có thể giữ trạng thái hiển thị cũ hoặc làm mất bản nháp `#home-problem-input`.
- **Giải pháp (`App.tsx`, `landing-geometry-data.ts`):**
  - Bổ sung `reconcileAuthSession(force)` với ngưỡng điều tiết `AUTH_RECONCILE_THROTTLE_MS = 1200` khi cửa sổ focus/trở lại hiển thị, xử lý dọn phiên ngay khi server trả `HTTP 401`.
  - Đồng bộ trạng thái đăng nhập xuyên tab qua `AXO_AUTH_SYNC_STORAGE_KEY` (`localStorage` event) và `AXO_AUTH_SYNC_CHANNEL` (`BroadcastChannel`).
  - Bảo đảm điều hướng 1 chạm không vòng lặp chuyển hướng cho cả khách lẫn người dùng đã đăng nhập (`Student` / `Teacher` → `/app`, `Admin` → `/admin`) và giữ nguyên nội dung nháp `problemText` trên Composer khi quay lại Landing rồi vào lại ứng dụng.
- **Kiểm chứng:** `landing-auth-sync.test.tsx` và Gates 1–5 trong Playwright (`gate1_guest_header`, `gate2_student_auth_flow`, `gate3_teacher_admin_roles`, `gate4_cross_tab_and_401_cleanup`, `gate5_draft_preservation`).

### 3.2. Header Mobile & Ngăn kéo điều hướng — Khử trùng lặp CTA & Focus Management (`5f66a2910`, `9f7ff3286`, `d75681930`)
- **Nguyên nhân gốc ở V1.2:** Trên mobile, header và drawer dễ tạo cảm giác trùng CTA; việc nhấn chuột vs nhấn bàn phím mở drawer hoặc đóng bằng `Escape` chưa tách bạch rõ nơi đặt focus.
- **Giải pháp (`LandingHeader.tsx`, `landing.css`):**
  - Khi drawer đóng trên mobile (`<= 920px`), thanh header giữ `#btn-landing-header-start` gọn (`"Bắt đầu"` cho khách / `"Vào ứng dụng"` cho tài khoản đã đăng nhập) và ẩn cụm nav/login/pill tài khoản desktop; khi `#landing-mobile-drawer` mở (`!mobileOpen && ...`), `#btn-landing-header-start` được tháo khỏi header để bên trong drawer chỉ hiển thị duy nhất **1 CTA chính** (`#btn-landing-drawer-primary`), tránh lặp nút trên màn hình đang mở.
  - Khách trong drawer có link đăng nhập phụ `#btn-landing-drawer-login` (`Đăng nhập tài khoản`); người dùng đã đăng nhập hiển thị thẻ tài khoản `#landing-mobile-account` (`Nguyễn Nhật Minh · Học sinh`) và nút `"Vào ứng dụng"`, không còn nút đăng nhập thừa.
  - Phân biệt pointer vs keyboard khi mở drawer: click chuột focus container `#landing-mobile-drawer` (không làm sáng vòng focus ở link đầu tiên), còn nhấn `Enter` từ nút menu đưa focus vào phần tử tương tác bên trong kèm focus trap `Tab`/`Shift+Tab`. Bổ sung `restoreFocusOnCloseRef` (`d75681930`) để bấm `Escape` khôi phục focus chính xác về `#btn-landing-mobile-menu`.

### 3.3. Thiết kế lại Hero Spatial Illustration — Benchmark Concept A vs Concept B (`61f3f78f6`)
- **Đo đạc đối chứng (`hero-prototypes-benchmark.json`, `ANGLE / SwiftShader`):**

| Phương án thử nghiệm | Viewport | FPS | P95 Frame (ms) | Canvas | WebGL Created / Lost | CLS |
|---|---|---|---|---|---|---|
| **Concept A (`transformation`)** | `1920×1080` | **28.7** | **41.7** | 1 | **1 / 0** | `0` |
| **Concept A (`transformation`)** | `390×844` | **62.4** | **20.9** | 1 | **1 / 0** | `0` |
| Concept B (`sculpture`) | `1920×1080` | 27.6 | 48.6 | 1 | 2 / 0 | `0` |
| Concept B (`sculpture`) | `390×844` | 59.2 | 20.9 | 1 | 2 / 0 | `0` |

- **Quyết định & Triển khai (`LandingHeroSculpture3D.tsx`, `landing.css`):** Chọn **Concept A** (đơn khối đa diện cắt chéo sạch khung nền trắng, bỏ tag đỉnh `.axo-sp-point-tag` ở Hero để triệt tiêu rung/trễ DOM, chỉ dùng `1` WebGL context với analytical studio shading và đạt tốc độ/độ ổn định cao hơn trên cả Desktop lẫn Mobile).

### 3.4. Hoạt họa kể chuyện sản phẩm 4 chặng & Vá lỗi visual di động (`2533d1442`, `59300b9b4`)
- **Thiết kế (`LandingExplainerAnimation.tsx`, `LandingIllustrationAccents.tsx`, `LandingStorytelling.tsx`, `landing.css`):**
  - Chuyển sang sân khấu kể chuyện 4 chặng đồng bộ nguyên lý **"Một thời điểm, một ý chính"** bằng **100% Vector SVG + CSS** (`0` `<canvas>`, `0` `<video>`, không dùng `pathLength` theo luật `landing-storytelling-interaction.test.tsx`), minh họa lăng trụ tam giác đều `ABC.A′B′C′` bị cắt bởi `(MNP)` tạo hình thang cân `MNPQ`: Chặng 1 (*Đề bài xuất hiện*) → Chặng 2 (*Hình thành không gian*) → Chặng 3 (*Khám phá quan hệ `MN // BC` & giao điểm `Q`*) → Chặng 4 (*Kết quả trực quan `S(MNPQ) = 3√7`*).
  - Bổ sung thanh điều khiển 4 phân đoạn + nút `#btn-landing-story-autoplay` (`Tạm dừng`/`Tự chạy`), đồng thời tôn trọng `@media (prefers-reduced-motion: reduce)` (`sticky` chuyển về `static`, thời lượng transition `<= 0.01ms` / `1e-05s`).
- **2 lỗi visual được phát hiện & khắc phục triệt để trong nghiệm thu ảnh (`59300b9b4`):**
  1. **Tràn phải ở mục `#cach-hoat-dong` trên mobile `390×844` (`after_08_storytelling_mobile.png`):** Grid `@media (max-width: 920px)` dùng `grid-template-columns: 1fr` (mặc định `minmax(auto, 1fr)`) và `.axo-sp-story-rail`, `.axo-sp-story-pills`, `.axo-sp-story-visual-col` thiếu `min-width: 0; max-width: 100%;` khiến dải pill cuộn ngang đẩy cột rộng hơn viewport. Đã chuyển sang `minmax(0, 1fr)` và đặt `min-width: 0; max-width: 100%;` trên toàn bộ container liên quan; kết quả kiểm tra `storyRightOverflow: 0` trên toàn bộ `8/8` viewport.
  2. **Huy hiệu kết quả Chặng 4 chồng lên đỉnh `A` (`after_07_scene04.png`):** Huy hiệu gốc ở `x="26" y="294" width="206"` chạm tọa độ chiếu 2D của đỉnh `A` (`205.6, 315.1`). Đã dời sang vùng trống góc trên bên phải (`x="382" y="16" width="202" height="58"`), hoàn toàn tách khỏi nhãn `C′` (`344.5, 46.6`), cạnh `C′–B′` và đỉnh `B′`.

### 3.5. Tinh giản Interactive Demo & Độ ổn định nhãn 3D (`85f47feee`)
- **Cải tiến (`LandingInteractiveDemo.tsx`, `LandingHeroScene3D.tsx`):**
  - Loại bỏ `bottomCaption` (`.axo-sp-scene-pill` đè góc dưới trái canvas), tự động ẩn gợi ý xoay `.axo-sp-scene-hint` ngay khi người dùng xoay/tương tác (`hasCameraMoved`), giữ nút `#btn-landing-demo-reset` xuất hiện đúng ngữ cảnh (`data-visible="true"` sau khi đổi góc nhìn).
  - Hiển thị các đại lượng toán học chính xác tách biệt trên chip: Hình chóp `S.ABCD` (`S(MENPF) = 6√6`, `V(S.ABCD) = 32`) và Lập phương `ABCD.A′B′C′D′` (`S(MNEPFQ) = 12√3`, `MN = 2√2`, nút `#btn-landing-open-showcase-3d` mở vào `/simulation/cube-hexagonal-plane-section`).
  - Ở `LandingHeroScene3D.tsx`, bổ sung fallback `<text>` cho nhãn SVG khi `!webglReady` và gỡ bỏ `left`/`top` `%` inline trên `.axo-sp-point-tag` để chỉ cập nhật vị trí qua transform mượt không gây Layout Shift.

---

## 4. Benchmark hiệu năng Before / After (`VERIFIED`)

> **Điều kiện đo (`before-perf.json`, `after-perf.json`, commit cuối `59300b9b4`):** Chạy 3 phiên độc lập cho mỗi cấu hình trong Playwright Chromium headless (`dpr: 1`), gồm Hero WebGL ban đầu (`1.8s`), nghỉ `1.5s`, cuộn 65 bước deterministic, nghỉ `1.5s` ở Storytelling, chuyển mẫu Demo 4 lần, và nghỉ `1.5s`. Thực hiện trên cả **`ANGLE/SwiftShader`** lẫn **`Hardware GPU`** (`ANGLE (Intel, Intel(R) UHD Graphics (0x00009A68) Direct3D11 vs_5_0 ps_5_0, D3D11)`).

### 4.1. `ANGLE/SwiftShader` — Desktop (`1920×1080`, `1×` CPU, 3-run median)

| Chỉ số | Before V1.2.1 Run 1 / 2 / 3 (**Median**) | After `59300b9b4` Run 1 / 2 / 3 (**Median**) | Biến thiên (Median) |
|---|---|---|---|
| **CLS** | `0.1411 / 0.1411 / 0.1411` (**0.1411**) | `0.0105 / 0.0085 / 0.0085` (**0.0085**) | **-94.0%** (`< 0.1` đạt chuẩn) |
| WebGL Contexts (Initial / Scroll / Switch) | `1 / 2 / 2` | `1 / 2 / 2` (`webglLost: 0`) | Giữ ổn định tối ưu |
| Idle RAF 1500ms (Hero / Story / Demo) | `0 / 0 / 0` | `0 / 0 / 0` | `0` idle RAF rò rỉ |
| Avg FPS (SW-GL trong lúc cuộn & đổi mẫu) | `10.4 / 11.2 / 11.2` (**11.2**) | `8.7 / 10.4 / 11.6` (**10.4**) | Tương đương dưới giới hạn SW-GL |
| P95 Frame Time (ms) | `243.1 / 208.5 / 194.4` (**208.5**) | `243 / 229.2 / 208.3` (**229.2**) | ~229 ms SW-GL |
| Max Frame Time (ms) | `1013.9 / 965.2 / 992.7` (**992.7**) | `798.5 / 937.5 / 694.4` (**798.5**) | **-19.6%** |
| Long Tasks (số lượng / tổng ms) | `17, 18, 18` (**18**) / **2737 ms** | `16, 7, 7` (**7**) / **1888 ms** | **-61.1% số lượng · -31.0% tổng ms** |
| Max Long Task (ms) | `1008 / 959 / 990` (**990**) | `794 / 930 / 690` (**794**) | **-19.8%** |
| LCP (ms) | `1216 / 1244 / 1064` (**1216**) | `2484 / 1140 / 736` (**1140**) | **-6.3%** |
| JS Heap Delta / After (MB) | `5.89` / `38.15` | `0.34` / `31.63` | **-94.2% Heap Delta** |

### 4.2. `ANGLE/SwiftShader` — Mobile (`390×844`, `4×` CPU Throttle, 3-run median)

| Chỉ số | Before V1.2.1 Run 1 / 2 / 3 (**Median**) | After `59300b9b4` Run 1 / 2 / 3 (**Median**) | Biến thiên (Median) |
|---|---|---|---|
| **CLS** | `0.151 / 0.1744 / 0.151` (**0.151**) | `0.0218 / 0.0195 / 0.0218` (**0.0218**) | **-85.6%** (`< 0.1` đạt chuẩn) |
| WebGL Contexts (Initial / Scroll / Switch) | `1 / 2 / 2` | `1 / 2 / 2` (`webglLost: 0`) | Giữ ổn định tối ưu |
| Idle RAF 1500ms (Hero / Story / Demo) | `0 / 0 / 0` | `0 / 0 / 0` | `0` idle RAF rò rỉ |
| Avg FPS | `39.9 / 42.4 / 39.5` (**39.9**) | `44 / 47.9 / 50.9` (**47.9**) | **+20.1%** |
| P95 Frame Time (ms) | `76.4 / 55.6 / 69.4` (**69.4**) | `62.5 / 55.5 / 55.5` (**55.5**) | **-20.0%** |
| Max Frame Time (ms) | `631.8 / 583.5 / 638.8` (**631.8**) | `409.7 / 472.2 / 423.6` (**423.6**) | **-33.0%** |
| Long Tasks (số lượng / tổng ms) | `10, 9, 10` (**10**) / **2975 ms** | `11, 10, 9` (**10**) / **1831 ms** | **-38.5% tổng thời gian** |
| Max Long Task (ms) | `1239 / 894 / 884` (**894**) | `405 / 468 / 414` (**414**) | **-53.7%** |
| LCP (ms) | `3036 / 2392 / 2404` (**2404**) | `1348 / 1412 / 1440` (**1412**) | **-41.3%** |
| JS Heap Delta / After (MB) | `2.78` / `38.17` | `2.32` / `32.73` | Giảm `-5.44 MB` heap cuối |

### 4.3. `Hardware GPU` (`Intel(R) UHD Graphics D3D11`) — Desktop & Mobile

| Cấu hình | Run 1 / 2 / 3 | Avg FPS (Median) | P95 / Max Frame (ms) | Long Tasks (count / total ms) | CLS | LCP (ms) |
|---|---|---|---|---|---|---|
| Before Desktop (`before-perf.json`, 1-run probe) | Run 1 | `131.9` | `7.1 / 76.2` | `4 / 492` | `0` | `912` |
| **After Desktop (`1920×1080`, `1×` CPU, 3-run median)** | `132.4 / 140.6 / 139.3` | **`139.3`** | **`7.1 / 76.3`** | **`3 / 227`** | **`0.0125`** | **`412`** (`892 / 412 / 396`) |
| Before Mobile Hardware GPU | — | `NOT MEASURED` | `NOT MEASURED` | `NOT MEASURED` | `NOT MEASURED` | `NOT MEASURED` |
| **After Mobile (`390×844`, `4×` CPU, 3-run median)** | `128.5 / 127.8 / 128.9` | **`128.5`** | **`7.2 / 131.9`** | **`9 / 1148`** | **`0.0195`** | **`1296`** (`1192 / 1296 / 1420`) |

---

## 5. Ma trận kiểm chứng toàn diện (`VERIFIED`)

### 5.1. Kiểm thử đơn vị, hợp đồng & build sản xuất
- **Full Vitest (`npx vitest run --maxWorkers=2`, chạy sau mọi chỉnh sửa cuối cùng):** **`173 passed (173)` test files, `2195 passed (2195)` tests** (`Duration: 102.01s`, 0 fail, 0 skip), bao gồm toàn bộ các suite Landing (`landing-auth-sync.test.tsx`, `landing-header-navigation.test.tsx`, `landing-webgl-lifecycle.test.tsx`, `landing-storytelling-interaction.test.tsx`, `landing-demo-integrity.test.tsx`, `landing-design-system.test.tsx`, `landing-spatial-story.test.tsx`), `src/styles/class-coverage.test.ts` (`4` tests) và `src/code-index-sync.test.ts` (`3` tests).
- **TypeScript & Production Bundle (`npx tsc -b && npm run build` ở commit `59300b9b4`):** Thoát mã `0`, `120 modules transformed`, `built in 4.79s`.

### 5.2. 13/13 Playwright Verification Gates (`e2e-gates-v121.json` — `allPassed: true`)

| Gate ID | Hạng mục kiểm định | Trạng thái | Ghi nhận thực đo |
|---|---|---|---|
| `gate1_guest_header` | Header khách ở `/gioi-thieu` | `PASS` | `1` nút `#btn-landing-header-login`, CTA `"Bắt đầu"`, `0` account pill |
| `gate2_student_auth_flow` | Đăng nhập Student 1-click & persist reload | `PASS` | `wsPath: "/app"`, `#sb-user-account-btn` = `Nguyễn Nhật Minh Học sinh`, `/gioi-thieu` giữ `"Vào ứng dụng"` sau reload |
| `gate3_teacher_admin_roles` | Đồng bộ vai trò Teacher (`/app`) & Admin (`/admin`) | `PASS` | Cả 2 role định tuyến đúng và đồng bộ tên ở header Landing |
| `gate4_cross_tab_and_401_cleanup` | Đồng bộ đa tab & dọn phiên khi `HTTP 401` | `PASS` | Tab Landing và tab Workspace tự quay về trạng thái Guest sau 401 |
| `gate5_draft_preservation` | Bảo toàn nháp đề bài qua chuyển trang | `PASS` | Giữ nguyên chuỗi `Cho hình chóp S.ABCD...` trên `#home-problem-input` |
| `gate6_mobile_drawer_dedup` | Khử trùng lặp CTA trên header/drawer mobile | `PASS` | Drawer mở `openHeaderStartCount: 0`, `primaryCtas: 1`; Auth drawer có `#landing-mobile-account` & `hasDupLoginBtn: false` |
| `gate7_focus_ring_pointer_vs_keyboard` | Tách biệt pointer/keyboard & Escape focus return | `PASS` | Pointer focus `landing-mobile-drawer`; `Escape` trả về `btn-landing-mobile-menu`; `Enter` + `Tab` giữ focus trong drawer |
| `gate8_hero_redesign` | Concept A Hero sạch tag đỉnh | `PASS` | `pointTags: 0`, `heroCanvas: 1` |
| `gate9_explainer_4_scenes` | Explainer SVG 4 chặng không canvas/video | `PASS` | Cả 4 chặng: `canvases: 0`, `videos: 0`, `activeCards: 1`, `singleLineMetricRow: true` |
| `gate10_interactive_demo` | Orbit, auto-hide hint, metric chips, Mở 3D | `PASS` | Hint `1 → 0`, reset `false → true`, caption pills `0`, metric chips khớp `6√6`/`32`/`12√3`/`2√2`, mở `/simulation/cube-hexagonal-plane-section` |
| `gate11_reduced_motion` | Hỗ trợ `prefers-reduced-motion: reduce` | `PASS` | `reducedMotionMatches: true`, `stickyPosition: "static"`, `planeTransitionDuration: "1e-05s"` (`<= 0.01s`) |
| `gate12_viewport_matrix_8` | Ma trận 8 viewport (`1920×1080`..`320×568`) | `PASS` | `8/8` đạt `overflowPx: 0` và `storyRightOverflow: 0` |
| `gate13_wcag_aa_and_zero_console_errors` | Tương phản WCAG AA & zero runtime errors | `PASS` | `8/8` selector đạt AA (`4.57:1`–`21:1`), `pageErrors: []`, `consoleErrors: []` |

### 5.3. Ma trận Responsive 8 Viewport & Tương phản WCAG AA
- **8 Viewport (`overflowPx = 0`, `storyRightOverflow = 0` ở tất cả độ phân giải):** `1920×1080`, `1440×900`, `1366×768`, `1024×768`, `768×1024`, `390×844`, `360×800`, `320×568`.
- **WCAG AA (`1440×900`):** `.axo-sp-hero-title` (`21:1`), `.axo-sp-hero-lead` (`13.18:1`), `#btn-landing-header-login` (`13.18:1`), `#btn-landing-header-start` (`4.57:1`), `#btn-landing-hero-start` (`4.57:1`), `.axo-sp-story-metric-pill.is-highlight` (`8.08:1`), `.axo-sp-demo-metric-val` (`8.08:1`), `#btn-landing-open-showcase-3d` (`4.57:1`).
- **REA MCP Runtime Check:** `NOT VERIFIED` (chưa kích hoạt phiên REA MCP cho V1.2.1; toàn bộ kiểm chứng DOM, WebGL, Console/PageError, Video flow và ảnh PNG đều được thực hiện trực tiếp qua Playwright Chromium `ANGLE/SwiftShader`, `Hardware GPU` và kiểm tra thị giác từng file PNG bằng công cụ đọc ảnh).

---

## 6. Ghi chú bàn giao Backend (`Backend Handoff Note — READ-ONLY`)

Trong quá trình kiểm tra chỉ đọc kho mẫu [`advanced-geometry-samples.json`](../../../frontend/src/data/advanced-geometry-samples.json) đối với bài toán **`lap-phuong-thiet-dien-bat-ky`** (*Thiết diện lục giác đều của hình lập phương `ABCD.A′B′C′D′`*):
- Dữ liệu `envelope.scene3d.objects` khai báo `thiet_dien` (`type: "section"`) với `ordered_vertex_ids: ["M", "N", "E", "P", "F", "Q"]`, `ordered_boundary_edges: ["MN", "NE", "EP", "PF", "FQ", "QM"]`, giá trị đo `S_td.value = "12√3"` và `config.frames[23]` là `"Xác định khoảng cách giữa M và N bằng 2√2."`.
- Tuy nhiên, mảng tọa độ `thiet_dien.polygon` hiện lưu theo thứ tự `[["2","4","0"], ["0","2","0"], ["0","0","2"], ["2","0","4"], ["4","2","4"], ["4","4","2"]]` (tức `[N, M, Q, F, P, E]`, bắt đầu tại `C-D` rồi đi ngược chiều), tương ứng với thứ tự trong `endpoint_entities` (`edge:C-D`, `edge:A-D`, `edge:A-A_prime`, `edge:A_prime-B_prime`, `edge:B_prime-C_prime`, `edge:C-C_prime`), lệch vị trí so với `ordered_vertex_ids` (`["M", "N", "E", "P", "F", "Q"]`).
- **Xử lý ở Frontend V1.2.1:** Không chỉnh sửa Backend hay file JSON tĩnh theo quy tắc cô lập phạm vi; Frontend giữ cấu hình đọc riêng cho mẫu giới thiệu trong [`landing-geometry-data.ts`](../../../frontend/src/components/landing/landing-geometry-data.ts) (`LANDING_CUBE_SAMPLE`) và chuyển tiếp thông tin sai lệch thứ tự mảng `thiet_dien.polygon` / `endpoint_entities` vs `ordered_vertex_ids` này để đội Backend chuẩn hóa đồng bộ về sau.

---

## 7. Danh mục Artifact Kiểm chứng (`C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\landing_v1_2_1_audit`)

- **`perf/`:** `before-perf.json`, `hero-prototypes-benchmark.json`, `after-perf.json`, `e2e-gates-v121.json`
- **`prototypes/`:** `prototype_a_desktop_1920.png`, `prototype_a_mobile_390.png`, `prototype_b_desktop_1920.png`, `prototype_b_mobile_390.png`
- **`before/` (17 ảnh gốc V1.2):** `before_01_header_guest_desktop.png` .. `before_11_mobile_360x800.png`
- **`after/` (17 ảnh sau sửa, gồm bản chụp lại trên `59300b9b4`):** `after_01_header_guest_desktop.png`, `after_02_header_auth_desktop.png`, `after_03_mobile_drawer_guest.png`, `after_04_mobile_drawer_auth.png`, `after_05_workspace_after_login.png`, `after_06a_hero_desktop.png`, `after_06b_hero_mobile.png`, `after_07_scene01.png`..`after_07_scene04.png`, `after_08_storytelling_desktop.png`, `after_08_storytelling_mobile.png`, `after_09_interactive_demo_desktop.png`, `after_09_interactive_demo_mobile.png`, `after_10_closing_cta_footer.png`, `after_11_mobile_360x800.png`
- **`video/` (6 bản quay Playwright E2E):** `v121_01_auth_sync_flow.webm`, `v121_02_mobile_drawer_navigation.webm`, `v121_03_hero_spatial_illustration.webm`, `v121_04_product_explainer_animation.webm`, `v121_05_interactive_demo_orbit_and_open.webm`, `v121_06_reduced_motion.webm`

---

**Owner Approval:** `PENDING_OWNER_REVIEW`
