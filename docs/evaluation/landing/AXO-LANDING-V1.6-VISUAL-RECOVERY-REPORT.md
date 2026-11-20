# AXO LANDING V1.6 — BÁO CÁO KHÔI PHỤC CHẤT LƯỢNG THỊ GIÁC & HỢP NHẤT THIẾT KẾ

- **Hướng thiết kế chính thức:** AXO Spatial Editorial — *Geometry in Motion*
- **Nhánh thực thi:** `feat/axo-geometry-library-verification` (Worktree `D:\Documents\projects\axo-geometry-library`, mốc nền `2732803e31e26fc91f4eeefb4c6dfcf9835f69ec`)
- **Tuyến xem trước cô lập:** `http://localhost:3001/gioi-thieu?preview=v1.4` (`LandingPrototypeMode = "v14"`)
- **Tuyến Production bảo toàn nguyên vẹn:** `/`, `/gioi-thieu` (`"prod"`, V1.2.2) và Workspace `/app`
- **Trạng thái phê duyệt chủ dự án:** `OWNER_APPROVAL: PENDING_OWNER_REVIEW`

---

## 1. Tóm tắt điều hành (Executive Summary)

Bản AXO Landing V1.6 khắc phục toàn diện các vấn đề thẩm mỹ, bố cục, đa dạng mô hình 3D và trải nghiệm di động còn tồn đọng ở V1.5 trên tuyến xem trước cô lập `/gioi-thieu?preview=v1.4` mà không làm thay đổi tuyến production V1.2.2, Workspace `/app`, Backend hoặc nhân hình học. Các cải tiến cốt lõi gồm:

1. **Khử lặp khối chóp `S.ABCD` trên toàn trang:** Hero giữ `S.ABCD` thiết diện ngũ giác `MENPF` (loại bỏ mảnh ngũ giác nhỏ lơ lửng góc trên trái và thay bằng hình chiếu đứng xuống mặt đáy `A–E′–N–P–F′` kèm hai dây rọi `EE′`, `FF′`), Storytelling trình diễn lăng trụ tam giác đều `ABC.A′B′C′`, và Closing CTA tái thiết kế hoàn toàn thành **lăng trụ lục giác đều (`R = 1.62, H = 2.88`) cắt bởi mặt phẳng nghiên cứu nghiêng `Π`** tạo lục giác thiết diện phẳng 6 đỉnh kèm trục đối xứng `OO′`, pháp tuyến và hai vòng ngoại tiếp đồng tâm (`0` nhãn chữ SGK, `0` khối chóp lặp).
2. **Hiển thị rõ ràng chú thích `"thiết diện thật"` trong Demo:** Sửa xung đột stacking context tại `.axo-sp-demo-section.is-v14 .axo-sp-section-title { position: relative; isolation: isolate; }` để khung mặt cắt xanh lam `.axo-v14-anno-svg-highlight` (`z-index: -1`) hiển thị sắc nét phía sau chữ trên mọi trình duyệt.
3. **Đưa Hero gọn lên trong fold & 2 dòng trên `320×568`:** Kéo khoảng trống đỉnh Hero từ `224px–233px` xuống `180px–182px` trên desktop và giới hạn `h1` về đúng `2` dòng ở mọi độ rộng từ `320px` đến `1920px`.
4. **Hợp nhất sân khấu Storytelling & Demo đa thiết bị:** Nâng kích thước SVG Storytelling (`scale = 64 * zoom`), bổ sung khung ngắn riêng cho `<= 480px && max-height: 620px` tránh cắt đáy chữ ở `320×568`, gom thanh 4 bước xuống dưới canvas 3D (`.axo-sp-demo-step-dock`), sửa cụm chọn mẫu mobile hết biến dạng oval (`border-radius: var(--rounded-lg)` + grid 1 cột), và hoàn thiện nút `#btn-landing-footer-top` dạng viên thuốc có phản hồi hover đồng bộ.

---

## 2. Preflight, Bảo toàn Port `3001` & Phạm vi Sở hữu

- **Bảo toàn tiến trình `localhost:3001`:** Vite dev server `PID 5220` (`task-83120`) lắng nghe trên `::1:3001` chạy liên tục suốt toàn bộ phiên làm việc, `0` lần kill, stop, restart hay thay đổi cấu hình Vite. Kiểm chứng bản build production `inspect.mjs` chạy riêng trên cổng tạm `4179` (`vite preview --port 4179 --strictPort`) và chỉ tắt đúng PID con `4179`.
- **Phạm vi chỉnh sửa (Ownership Guard):** Toàn bộ thay đổi chỉ nằm trong `frontend/src/components/landing/`, `frontend/src/components/__tests__/landing-*.test.tsx`, dòng `1983` của `docs/CODE_INDEX.md` và báo cáo này dưới `docs/evaluation/landing/`. Không chạm vào `backend/**`, `frontend/index.html`, `package*.json`, `public/**`, các component Workspace, `frontend/src/state/**`, `docs/EVIDENCE_INDEX.md` hay `docs/evaluation/geometry/runs/**`.
- **Tuân thủ quy tắc vòng đời:** Không tạo component hay file mang hậu tố `V15`/`V16`/`V17` (`landing-version-lifecycle.test.ts`). Không sử dụng màu hex literal hay CSS `var(--...)` trong TSX Three.js/SVG (`landing-design-system.test.tsx`).

---

## 3. Baseline Trước Chỉnh Sửa (Before — V1.5) & Nguyên nhân gốc

Kiểm tra baseline trước chỉnh sửa (`before_baseline.json` và `taste_before/report.json`) trên 9 viewport chỉ ra 6 khiếm khuyết chính:

1. **Khối chóp `S.ABCD` lặp lại 3 lần (Hero, Demo mặc định và Closing CTA):** Thiếu đa dạng đa diện trên một trang giới thiệu hệ thống mô phỏng hình học không gian.
2. **Hero có chi tiết ngũ giác nhỏ lơ lửng góc trên trái & khoảng trống đỉnh lớn:** Khoảng cách đỉnh `h1Top` tới `233px` (`1920×1080`), `226px` (`1440×900`), `224px` (`1366×768`); ở `320×568`, `h1` gãy thành `3` dòng (`h1Height = 114px`) đẩy khối 3D khỏi màn hình đầu; cụm vòng chữ `hình dung` còn sát chữ `g`.
3. **Chú thích `"thiết diện thật"` ẩn sau nền trang:** `#landing-demo-heading` có `isolation: auto`, khiến `.axo-v14-anno-svg` (`z-index: -1`) lọt xuống dưới nền `--canvas` của `#view-landing`.
4. **Cảnh báo `design-taste-frontend` Before:** `taste_before/report.json` ghi nhận cảnh báo `[edge-text]` tại `390px` (`16px` lề ngang ở đoạn mô tả Storytelling) và `[outlined-box]` tại `390px`.
5. **Bố cục mobile Storytelling & Demo:** Trên `320×568` đoạn chữ cuối Chặng bị hụt sát đáy khung dính; `.axo-sp-demo-samples` có `border-radius: 999px` bị kéo thành hình oval lớn khi xếp dọc hai mẫu trên mobile `320px–430px`.
6. **Footer & Closing CTA:** Closing CTA lặp khối chóp, cần thay thế hoàn toàn bằng đa diện khác họ; nút `#btn-landing-footer-top` chưa có nền viên thuốc và hiệu ứng nhấc `-1px` đồng bộ với header/CTA.

---

## 4. Tổng hợp Nghiên cứu REA MCP & Meta Astryx

Toàn bộ nguồn tham chiếu bên ngoài được duyệt qua headless Chromium (`CDP 127.0.0.1:9236`) và ghi nhận thụ động qua `rea:list_browser_targets`, `rea:inspect_web_page` và `rea:capture_web_screenshot`:

| Nguồn tham chiếu | Trạng thái | DOM Nodes / Scripts | Inspection `evidence_id` | Screenshot `evidence_id` | Học hỏi thiết kế áp dụng vào V1.6 |
| --- | --- | --- | --- | --- | --- |
| `https://bundaumayo.top/` | `VERIFIED_VIA_REA_MCP` | 1856 / 15 | `ev_793de4bb5941c66395861fd919eebe5c6ab4aa853eb77a2c632508ed0903a553` | `ev_5d63fcd72dbb5328595c5f7331070a2aa0ecba33b490feeb1b3e9773476aa364` | Nét bút vẽ tay phóng khoáng thoáng dấu chữ; cụm 3D gọn không gắn mảnh trang trí rời |
| `https://www.notion.com/` | `VERIFIED_VIA_REA_MCP` | 1150 / 57 | `ev_9b3b4183891772c62125be3bf2fdc480ec1ca468108f9a6c5f40f50faa5fd4fe` | `ev_5e0b4e0f5be0f29c3efcaa1b9d7943fd7c0be6b67783ac872882c40161c7de08` | Nhịp editorial sạch, tương phản trắng–kem và tách lớp sân khấu sản phẩm |
| `https://www.figma.com/` | `VERIFIED_VIA_REA_MCP` | 1944 / 144 | `ev_18a86991b1d10fd5696b4e11d86d688144416b18b1daabae5b45ea0204d62a52` | `ev_1b2d50c0a2f05dc4d962e281f5a8cb53f002f81036b7e7f0e245e25f5406257c` | Phân vùng nền màu liền mạch thay cho các hộp viền chia cắt |
| `https://rive.app/` | `VERIFIED_VIA_REA_MCP` | 4081 / 4 | `ev_e76049ab3cd7fecb952430f432e0000f6056d613d603764580179f2b10cbbdd3` | `ev_4506da31b5bfe9a441f89b947f469972461eaf5ae4a22381c55fd60f3694a870` | Bộ chuyển trạng thái gắn sát khung tương tác |
| `https://pudding.cool/` | `VERIFIED_VIA_REA_MCP` | 1554 / 22 | `ev_ae36fa930f20d3f6b21ce88d5585163b2727903b3ca187c689d1261550261e49` | `ev_e7c6637b6ce19b20c7b7a3bac0daf8ab2a9aecaaf2e4f3863266b1abbd02bef7` | Khớp chặt văn bản từng bước cuộn với đồ họa chính |
| `https://lusion.co/` | `VERIFIED_VIA_REA_MCP` | 3054 / 2 | `ev_a69f7a9c3311a54f5802c4fc164dc38ba302f886ef736d283d38327ac7541ec5` | `ev_68f4b59de4ef56020991c5a09bbed0ee9d1a48fab41c3df76a5603b6e40c729d` | Tập trung một tiêu điểm điêu khắc 3D mỗi chặng nhìn |
| `https://ciechanow.ski/` | `VERIFIED_VIA_REA_MCP` | 6495 / 3 | `ev_08070a84accdee549b12043da45d3d1d86553085c04f6ea18e540c54344fdcbb` | `ev_6558ada88d8dbb3c128f5665405b19900c031e367368cef7936b262facf9253b` | Chiếu hình khối kết hợp vết hình chiếu trực giao để tự giải thích bản chất không gian |
| `https://mathigon.org/` | `VERIFIED_VIA_REA_MCP` | 1850 / 7 | `ev_3ebb6bbbd3525535717243f5186397a4f75f6599f0a0ff4b73c79c1f6bb6ff1e` | `ev_ee25ea6497c7b3410faa3439f20394f1df04333522e11624c0e1a3bd96d95ca7` | Sắc độ đa diện tách khối rõ nhưng không đưa đáp số đại số vào landing |
| `https://spline.design/` | `VERIFIED_VIA_REA_MCP` | 2027 / 33 | `ev_ae26f6ae34a35ae55a667bf86ee2b8e20a06161c1833e0f172edc232eb79711b` | `ev_560642d732fc593400d5f08de551f5032f5da7b4c4da47f886517f41d6ce4773` | Cân bằng giữa sân khấu 3D thoáng và CTA không rối mắt |
| `https://github.com/meta/astryx` | `VERIFIED_VIA_REA_MCP` | 3773 / 0 | `ev_fedb1bf4aa1bdcffef881bec238632beae8e65453de5f26a72b28b29dbf592f5` | `ev_3bd2434fe9cef42c13aaded741c9071cc9a0deec5e146414413c90ed2bb25f4e` | Chuẩn token khoảng đệm, trạng thái `:hover`/`:active`/`:focus-visible`/`:disabled` |
| `https://threejs.org/` | `VERIFIED_VIA_REA_MCP` | 1320 / 2 | `ev_7a7b1d8cccb95db3ee607b2971cd782d3a2ee93aa07bbb49728bffdf0ba4113e` | `ev_4b43fb19d4d0f1b4b8a334ab3ede0d9ad38dfe61fb603d9d87302d8a2d505d49` | Quản lý tài nguyên `BufferGeometry`/`Material` và render theo nhu cầu |
| `https://tympanus.net/codrops/` | `NOT_VERIFIED` | N/A | N/A | N/A | Chặn bởi tường HTTP 403 / Cloudflare (`Just a moment...`), tuân thủ nguyên tắc không vượt anti-bot |
| `http://localhost:3001/gioi-thieu?preview=v1.4` (After V1.6) | `VERIFIED_VIA_REA_MCP` | 413 / 113 excluded | `ev_f8b93407008c157ecd61ac5d987c9e794b5def95b5f6767ccfeea2bfe09f5596` | `ev_79db4ad70fe94f339ae00ae736969c31306ae474d4bef2e588d0d9fb1b04dbb9` | List targets `ev_f39d7476...1b7b`; `after_localhost_3001.png` (`92,285` bytes); `consoleErrors = 0` |

**Áp dụng từ Meta Astryx & `design-taste-frontend`:** Toàn bộ V1.6 giữ bảng màu thương hiệu Axo (`#ffffff`, `#f6f5f4`, `#0075de`, `#dd5b00`), không dùng bo tròn card ghép chồng, mở rộng lề ngang mobile thành `20px` để xóa sạch `[edge-text]`, chuẩn hóa nút CTA thứ cấp sang nền điền mềm không viền 1px thừa và phân tách rõ trạng thái hover trên cả 8 nhóm tương tác.

---

## 5. Typography Biểu cảm & Đối chiếu Dấu chữ Tiếng Việt (`AnnotatedHeading.tsx`)

- **Vòng tròn `circle` (`viewBox="0 0 368 184"`):** Mở rộng chiều cao hộp SVG và kéo vòng cung dưới thoáng dưới chữ `g` trong cụm **`hình dung`**, khoảng thở trên thoáng dấu huyền `ì`.
- **Khung cắt `highlight` (`viewBox="0 0 320 120"`):** Bổ sung khung tứ giác mặt cắt xiên kèm các vạch góc giao điểm (`secondaryD`), gắn cùng `IntersectionObserver` kích hoạt vẽ nét một lần phía client (`SSR` mặc định `is-active`).
- **Sửa lỗi stacking context:** Thêm `position: relative; isolation: isolate;` vào `.axo-sp-demo-section.is-v14 .axo-sp-section-title`, đưa `h2Isolation` từ `"auto"` về `"isolate"` trên mọi viewport so với Before, giúp **`thiết diện thật`** hiển thị đầy đủ viền cắt xanh lam `rgb(0, 117, 222)`.
- **Cỡ chữ hero trên `320×568`:** Thu min-clamp của `@media (max-width: 390px)` về `clamp(1.375rem, 6.8vw, 1.82rem)` (`22px` tại `320px`), đưa tiêu đề chính về đúng `2` dòng ở cả 9 viewport thay vì `3` dòng trên `320×568`.

---

## 6. Hero V1.6 — Không gian Thoáng & Hình chiếu Đứng (`LandingHeroV14.tsx`)

- **Bỏ hình nhỏ lơ lửng gây rối:** Gỡ bỏ hoàn toàn cụm `trueShapeGroup`, `projRayM`, `projRayF` ở góc trên trái mà Owner phản hồi là rời rạc.
- **Độ sâu khối 3D + hình chiếu đáy thực:** Áp dụng `buildFacesBufferGeometry(..., baseColorHex)` tô bóng định hướng theo pháp tuyến tam giác, tăng độ rực cam đất thiết diện `MENPF` (`0xed6d14`, `HERO_SECTION_FILL_OPACITY = 0.5`), bổ sung hai đường chéo đáy `AC`, `BD` và dựng đúng hình chiếu vuông góc đứng xuống mặt đáy **`A–E′–N–P–F′`** (`E′ ∈ AB`, `F′ ∈ AD`) nối hai dây rọi `EE′`, `FF′`.
- **Khung camera & Fallback SVG đồng bộ:** `applyHeroCameraFraming(w, h)` tự nới khoảng cách camera trên tỉ lệ khung hẹp và `<HeroFallbackSvg />` dùng hệ tọa độ barycentric affine khớp hình chiếu thật (`0` nhãn thừa, `0` đáp số toán).

---

## 7. Storytelling Cuộn Liên Tục 4 Chặng (`LandingStorytellingV14.tsx`)

- **Nâng tỷ lệ lăng trụ & độ rõ điểm:** Tăng khung SVG từ `cy = 236, scale = 51` lên **`STORY_SVG_W = 640`, `STORY_SVG_H = 470`, `scale = 64 * pose.zoom`, `cy = 226`**, đặt bề mặt sân khấu `.axo-v14-story-stage` nền sáng tách khỏi hành lang `--axo-sp-paper`. Siết `computeChapterEnvelope` (`w = 0.038`, `opacity >= 0.38`) giữ luôn duy nhất `visibleChapters = 1` ở mọi mốc cuộn.
- **Responsive di động (`320×568` & `390×844`):** Thêm quy tắc `@media (max-width: 480px) and (max-height: 620px)` giảm chiều cao SVG xuống `136px` và lề nội dung chương xuống gọn hơn để Chặng 4 không bị cắt chữ dưới đáy màn hình nhỏ.

**Bảng kiểm chứng 13 điểm cuộn xuôi & ngược trên `LandingStorytellingV14` (`1440×900`, run cuối):**

| Bước cuộn | Target Progress | Stage Index | Progress Thực tế | Chương đang hiển thị (`opacity >= 0.38`) | Điểm `Q` (`qVisible`) | Bộ đếm giai đoạn UI |
| --- | --- | --- | --- | --- | --- | --- |
| 1 (xuôi) | `0.00` | `0` | `0.000` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |
| 2 (xuôi) | `0.12` | `0` | `0.067` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |
| 3 (xuôi) | `0.25` | `0` | `0.197` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |
| 4 (xuôi) | `0.38` | `1` | `0.327` | `1` | `false` | Chặng 2 / 4 · Dựng không gian |
| 5 (xuôi) | `0.50` | `1` | `0.447` | `1` | `false` | Chặng 2 / 4 · Dựng không gian |
| 6 (xuôi) | `0.65` | `2` | `0.597` | `1` | `true` | Chặng 3 / 4 · Xác lập quan hệ |
| 7 (xuôi) | `0.75` | `2` | `0.697` | `1` | `true` | Chặng 3 / 4 · Xác lập quan hệ |
| 8 (xuôi) | `0.88` | `3` | `0.827` | `1` | `true` | Chặng 4 / 4 · Kết quả |
| 9 (xuôi) | `1.00` | `3` | `0.948` | `1` | `true` | Chặng 4 / 4 · Kết quả |
| 10 (ngược) | `0.65` | `2` | `0.597` | `1` | `true` | Chặng 3 / 4 · Xác lập quan hệ |
| 11 (ngược) | `0.38` | `1` | `0.327` | `1` | `false` | Chặng 2 / 4 · Dựng không gian |
| 12 (ngược) | `0.12` | `0` | `0.067` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |
| 13 (ngược) | `0.00` | `0` | `0.000` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |

---

## 8. Khu Trải Nghiệm 3D Tương Tác (`LandingInteractiveDemo.tsx`, `LandingHeroScene3D.tsx`)

- Giữ nguyên hoàn toàn `presentation === "default"` phục vụ production V1.2.2.
- Trên `presentation === "v14"`: hợp nhất cụm canvas 3D và 4 nút bước dựng `.axo-sp-demo-step-dock` trong một vùng sân khấu chung `.axo-sp-demo-canvas-wrap` nền `--axo-sp-paper`, giữ nhãn `"Kéo để xoay 3D"` / `"Góc nhìn tùy chỉnh"` một dòng, và bổ sung `v14AspectScale` trong `LandingHeroScene3D.tsx` (`renderFrame`) tránh cắt góc đa diện khi xoay trên màn hình hẹp.
- Sửa lỗi cụm chọn mẫu mobile `.axo-sp-demo-samples` bị oval: chuyển từ `border-radius: 999px` sang `display: grid; grid-template-columns: minmax(0, 1fr); border-radius: var(--rounded-lg);` tại `@media (max-width: 680px)`.

---

## 9. Thiết Kế Lại Closing CTA Thành Lăng Trụ Lục Giác Đều Khám Phá 3D (`LandingClosingScene3D.tsx`)

- **Xóa lặp khối chóp `S.ABCD`:** Closing CTA (`spatial-polyhedra-exploration-3d`) dựng **Lăng trụ lục giác đều (`CLOSING_PRISM_RADIUS = 1.62`, `H = 2.88`) cắt bởi mặt phẳng nghiên cứu nghiêng `Π`** (`n = normalize([0.32, 0.91, -0.26])`, `offset = 0.12`), sinh thiết diện lục giác phẳng chính xác 6 đỉnh (`data-section-edges="6"`, `planarResiduals < 1e-6`, `baseRadiusResiduals < 1e-6`, `7` mặt phần dưới và `7` mặt phần trên).
- **Hệ phụ trợ gắn kết, `0` vật thể rời góc:** Gồm đúng 3 lớp phụ trợ trực tiếp gắn trên hệ trục khối lăng trụ (`companionCount = 3`): (1) trục đối xứng `OO′` kèm góc vuông đáy và pháp tuyến mặt cắt, (2) vòng tròn ngoại tiếp đáy + đường gióng đứng, (3) cung phương vị đáy + vòng ngoại tiếp mặt trên. Loại bỏ hoàn toàn bát diện nhỏ lơ lửng góc trên phải.
- **Vòng đời kịch bản & tài nguyên:** Kịch bản 4 nhịp hữu hạn `CLOSING_STORYBOARD_MS = 3600` (`prism-solid` → `cutting-plane` → `intersection-trace` → `exploration-settled`), tự dừng `0` RAF khi ổn định/ẩn tab/ra khỏi viewport, dọn toàn bộ geometry/material khi unmount và đồng bộ fallback SVG `<ClosingFallbackSvg />` (`?no_webgl=1` & `prefers-reduced-motion`).

---

## 10. Footer, Đồng bộ Hover & Điều hướng Bàn phím / Drawer

**Bảng kiểm chứng Parity Hover trên 8 nhóm nút tương tác (`1440×900`):**

| Thành phần | Selector | Trạng thái trước hover | Trạng thái khi hover | Thay đổi (`changed`) |
| --- | --- | --- | --- | --- |
| Header CTA | `#btn-landing-header-start` | `bg: rgb(0, 117, 222)`, `r: 999px` | `bg: rgb(0, 91, 171)`, `translateY(-1px)` | `true` |
| Hero Primary CTA | `#btn-landing-hero-start` | `bg: rgb(0, 117, 222)`, `r: 9999px` | `bg: rgb(0, 91, 171)`, `translateY(-1px)` | `true` |
| Hero Secondary CTA | `#btn-landing-hero-story` | `bg: rgb(246, 245, 244)`, `r: 9999px` | `bg: rgb(255, 255, 255)`, `translateY(-1px)` | `true` |
| Sample Pill Cube | `#btn-landing-sample-lap-phuong-thiet-dien-bat-ky` | `bg: rgb(246, 245, 244)`, `color: rgb(49, 48, 46)` | `bg: rgb(230, 230, 230)`, `color: rgb(0, 0, 0)` | `true` |
| Demo CTA | `#btn-landing-open-showcase-3d` | `bg: rgb(0, 117, 222)`, `r: 9999px` | `bg: rgb(0, 91, 171)`, `translateY(-1px)` | `true` |
| Closing Primary CTA | `#btn-landing-final-start` | `bg: rgb(0, 117, 222)`, `r: 9999px` | `bg: rgb(0, 91, 171)`, `translateY(-1px)` | `true` |
| Closing Secondary CTA | `#btn-landing-hero-library` | `bg: rgb(255, 255, 255)`, `r: 9999px` | `bg: rgb(255, 255, 255)`, `translateY(-1px)` | `true` |
| Footer Back-to-Top | `#btn-landing-footer-top` | `bg: rgb(246, 245, 244)`, `r: 9999px` | `bg: rgb(230, 230, 230)`, `color: rgb(0, 91, 171)`, `translateY(-1px)` | `true` |

- **Điều hướng bàn phím & Mobile Drawer:** Bấm `#btn-landing-footer-top` cuộn trang về vùng đỉnh (`scrollY = 244`); trên mobile, mở drawer (`drawerOpen = true`), bấm `Escape` đóng drawer (`drawerClosedOnEscape = true`) và khôi phục tiêu điểm bàn phím chính xác về `#btn-landing-mobile-menu` (`focusRestoredId = "btn-landing-mobile-menu"`).

---

## 11. Ma trận So sánh Before / After Trên 9 Viewport

| Viewport | `overflowX` | `scrollHeight` (Before → After) | `h1Top` (Before → After) | `h1` `fontSize` / Số dòng (After) | `#landing-demo-heading` `isolation` | Closing (`visual` / `edges`) | Lỗi JS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1920×1080` | `0` | `5229` → `5008` | `233` → `182` | `53.6px` / `2` dòng | `"auto"` → `"isolate"` | `spatial-polyhedra-exploration-3d` / `6` | `0` |
| `1440×900` | `0` | `4807` → `4609` | `226` → `180` | `52.56px` / `2` dòng | `"auto"` → `"isolate"` | `spatial-polyhedra-exploration-3d` / `6` | `0` |
| `1366×768` | `0` | `4492` → `4309` | `224` → `181` | `49.859px` / `2` dòng | `"auto"` → `"isolate"` | `spatial-polyhedra-exploration-3d` / `6` | `0` |
| `1024×768` | `0` | `4293` → `4183` | `100` → `92` | `37.376px` / `2` dòng | N/A (`deep: false`) | N/A | `0` |
| `768×1024` | `0` | `5031` → `4816` | `96` → `88` | `34.4px` / `2` dòng | `"isolate"` | `spatial-polyhedra-exploration-3d` / `6` | `0` |
| `430×932` | `0` | `4908` → `4650` | `88` → `84` | `30.53px` / `2` dòng | `"isolate"` | `spatial-polyhedra-exploration-3d` / `6` | `0` |
| `390×844` | `0` | `4814` → `4530` | `88` → `84` | `26.52px` / `2` dòng | `"auto"` → `"isolate"` | `spatial-polyhedra-exploration-3d` / `6` | `0` |
| `360×800` | `0` | `4791` → `4473` | `88` → `84` | `24.48px` / `2` dòng | N/A (`deep: false`) | N/A | `0` |
| `320×568` | `0` | `4615` → `4287` | `88` → `84` | `22px` / `2` dòng (Before: `114px`, 3 dòng) | `"auto"` → `"isolate"` | `spatial-polyhedra-exploration-3d` / `6` | `0` |

---

## 12. Chính sách Chất lượng Kỹ thuật, Hiệu năng WebGL & Cổng Tự động

| Hạng mục kiểm định | Kết quả thực đo |
| --- | --- |
| `npx tsc -b` | PASS (`0` lỗi TypeScript) |
| `npx vite build` | PASS (build production xong trong `6.06s`) |
| `design-taste-frontend` `lint.mjs` (7 file TSX V1.6) | **`0 FAIL, 0 WARN`** (nhờ loại hex, inline gradient, box-shadow tĩnh; `LandingHeroScene3D.tsx` giữ comment `shadow` và phông `JetBrains Mono` chỉ dùng cho nhánh SVG V1.2.2 `presentation="default"`) |
| `npx vitest run --testTimeout=20000` | **`191 / 191` file PASS · `2248 / 2248` test PASS** (`0` fail, `0` skip) |
| `npx vitest run code-index-sync` | **PASS** (`1 / 1` file, `3 / 3` tests) |
| `audit_docs_information_architecture.py` | Exit `1` (`CODE_INDEX` 4 stale paths do các file classroom `OWNERSHIP_BLOCKED` chưa commit của phiên song song tại dòng `4605, 4619, 4634, 4646`: `LiveClassDock.tsx`, `LiveClassStrip.tsx`, `MonitorView.tsx`, `classroom-sync.ts`); **`docs/CODE_INDEX.md:1983`, `LINKS = 0` broken, `OWNERSHIP = True`, `STATUS_LEDGER = True`, `EVIDENCE_INDEX = True`, `Docs root closed list = True (29/167, unclassified [])`** |
| `design-taste-frontend` `inspect.mjs` (Dev `3001`) | `few-pictures` FAIL (đặc thù ứng dụng WebGL/SVG hình học không dùng ảnh stock), `no-footage` / `dev-server` / `outlined-box@390` WARN; **`edge-text@390` đã biến mất hoàn toàn** (`edgeText: []`, `gaps: []`, `slivers: []`, `consoleErrors: []`) |
| `design-taste-frontend` `inspect.mjs` (Prod build `4179`) | `few-pictures` FAIL (như trên), `no-footage` / `outlined-box@390` WARN; **`dev-server` và `edge-text@390` đều sạch (`0` lỗi console, `voidShare: 0`, `horizontalOverflow: 0`)** |
| Ngân sách WebGL & Idle RAF | `canvasDomCount = 3`, `webglContextCreations = 5` (chế độ dev StrictMode mount đôi trước khi cleanup về 3 canvas), `rafTicksDuringIdle1s = 0` |
| Fallback `?no_webgl=1` & `prefers-reduced-motion` | `heroFallbackSvg = true`, `closingFallbackSvg = true`, `closingVisual = "svg-fallback"`, `closingBeat = "exploration-settled"`, `demoHighlightOpacity = "1"` |
| Non-regression routes (`/`, `/gioi-thieu`, `/app`) | Cả 3 tuyến trả HTTP `200`, `isV14 = false`, `overflowX = 0`, `errors = []` |

---

## 13. Bảng KEEP / RESTORE / REDESIGN / REMOVE AFTER APPROVAL & Kiểm toán Vòng đời File

| File dưới `frontend/src/components/landing/` | Phân loại V1.6 | Vai trò hiện tại & Hành động sau khi Owner duyệt |
| --- | --- | --- |
| `LandingHeader.tsx` | `KEEP` | Thanh điều hướng kính nổi & mobile drawer chung cho Production + Preview |
| `LandingHeroSculpture3D.tsx` | `KEEP` | Điêu khắc Hero của Production V1.2.2 (tuyệt đối giữ nguyên trước khi cutover) |
| `LandingClosingSculpture.tsx` | `KEEP` | Điêu khắc Closing của Production V1.2.2 (giữ nguyên) |
| `LandingStorytelling.tsx` | `KEEP` | Storytelling 4 chặng bản Production V1.2.2 (giữ nguyên) |
| `LandingExplainerAnimation.tsx` | `KEEP` | Explainer pipeline bản Production V1.2.2 (giữ nguyên) |
| `LandingIllustrationAccents.tsx` | `KEEP` | Họa tiết phụ bản Production V1.2.2 (giữ nguyên) |
| `landing-geometry-data.ts` | `KEEP` | Nguồn tọa độ hình chóp, lập phương & lăng trụ chuẩn hóa (`computeBoundedPlaneQuad`) |
| `LandingPreviewV14.tsx` | `KEEP` | Cổng gắn bản xem trước cô lập `?preview=v1.4` |
| `LandingClosingV14.tsx` | `KEEP` | Cấu trúc Closing Copy + Footer `LandingFooterV14` bản xem trước |
| `AnnotatedHeading.tsx` | `RESTORE` + `REDESIGN` | Khôi phục hiệu ứng vẽ nét SVG + mở rộng `circle` `368×184` thoáng dấu tiếng Việt & góc cắt `highlight` `320×120` |
| `LandingHeroV14.tsx` | `RESTORE` + `REDESIGN` | Khôi phục bố cục Hero thoáng, bỏ ngũ giác lơ lửng góc trên, thêm hình chiếu đáy `A–E′–N–P–F′` & framing theo tỷ lệ màn hình |
| `LandingStorytellingV14.tsx` | `REDESIGN` | Nâng kích thước SVG `640×470` (`scale = 64`), siết khung chuyển cảnh 1 chương rõ nét và thêm tầng responsive `<= 480px × 620px` |
| `LandingInteractiveDemo.tsx` | `RESTORE` + `REDESIGN` | Giữ bản V1.2.2; V1.4 gộp thanh bước dựng `.axo-sp-demo-step-dock` trong sân khấu canvas chung |
| `LandingHeroScene3D.tsx` | `RESTORE` | Bổ sung `v14AspectScale` cho khung demo hẹp trong khi giữ `default` không đổi |
| `LandingClosingScene3D.tsx` | `REDESIGN` | Thay thế khối chóp trùng lặp bằng Lăng trụ lục giác đều cắt mặt phẳng nghiên cứu `Π` (6 đỉnh thiết diện, `0` vật thể rời) |
| `landing.css` | `RESTORE` + `REDESIGN` | Sửa `isolation: isolate` cho `#landing-demo-heading`, co chữ Hero `320×568`, bỏ oval switcher mobile, nâng cấp pill `#btn-landing-footer-top` |
| Nhóm component V1.2.2 cũ (`LandingHeroSculpture3D.tsx`, `LandingStorytelling.tsx`, `LandingExplainerAnimation.tsx`, `LandingClosingSculpture.tsx`, `LandingIllustrationAccents.tsx`, chế độ `?preview=v1.4`) | `REMOVE AFTER APPROVAL` | Chỉ được hợp nhất / dọn bỏ sau khi Owner **chính thức phê duyệt V1.6 thay thế V1.2.2**; phiên V1.6 giữ nguyên 100% không xóa trước thời điểm phê duyệt |

---

## 14. Danh mục Bằng chứng Trực quan & 6 Video `.webm`

- **Thư mục Artifact:** `C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\landing_v1_6_audit\`
- **Ảnh Before / After:** Đầy đủ ảnh trong `before/` (`before_baseline.json`) và `after/` (`hero_*`, `story_*`, `demo_pyramid_*`, `demo_cube_*`, `closing_*`, `footer_*`, `nowebgl_hero_1440.png`, `nowebgl_closing_1440.png`), cùng ảnh kiểm định bản production build trong `taste_after_prod/`.
- **REA MCP Audit:** `rea/rea-v16-ledger.json` (11 site live + 1 blocked `403`), `rea/rea-v16-after.json` (`ev_f39d7476...`, `ev_f8b93407...`, `ev_79db4ad7...`) và `rea/after_localhost_3001.png` (`92,285` bytes).
- **6 Video thực tế ghi nhận trên `localhost:3001` (`landing_v1_6_audit/videos/`):**
  1. `01_hero_animation_and_cta_hover.webm` (`747,560` bytes)
  2. `02_storytelling_forward_4_stages.webm` (`751,302` bytes)
  3. `03_storytelling_reverse_scroll.webm` (`798,418` bytes)
  4. `04_interactive_demo_both_models.webm` (`1,286,923` bytes)
  5. `05_closing_cta_and_footer.webm` (`797,602` bytes)
  6. `06_mobile_navigation_and_scroll.webm` (`1,026,895` bytes)

---

## 15. Giới hạn còn lại & Trạng thái Phê duyệt

- Trên môi trường kiểm thử chỉ chạy frontend (`localhost:3001` / `4179`) chưa bật FastAPI backend, request `/api/auth/me` nhận HTTP `500` từ proxy Vite (không ảnh hưởng render Landing hay điều hướng `/app`).
- `https://tympanus.net/codrops/` không thể xác minh trực tiếp qua REA MCP do trả HTTP `403` Cloudflare challenge (`NOT_VERIFIED`).
- `design-taste-frontend` `inspect.mjs` vẫn báo `few-pictures` (`FAIL` do trang dùng WebGL/SVG 3D thay ảnh chụp) và `outlined-box@390` (`1` pill nút phụ có viền `1px` trên nền kem); toàn bộ cảnh báo chữ sát lề `[edge-text]` và `[dev-server]` trên production preview `4179` đã được giải quyết dứt điểm.
- `audit_docs_information_architecture.py` vẫn báo exit `1` cho tới khi phiên làm việc sở hữu cụm classroom (`OWNERSHIP_BLOCKED`) dọn 4 tham chiếu `CODE_INDEX.md` dòng `4605, 4619, 4634, 4646`; toàn bộ liên kết và danh mục phía Landing/V1.6 đều sạch `0` lỗi.
- Tuyến `/`, `/gioi-thieu` giữ nguyên V1.2.2; toàn bộ cải tiến V1.6 nằm tại `/gioi-thieu?preview=v1.4` chờ chủ dự án kiểm tra thực tế và phê duyệt:

`OWNER_APPROVAL: PENDING_OWNER_REVIEW`
