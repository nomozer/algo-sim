# AXO LANDING — SPATIAL VISUAL SYSTEM & EXPERIENCE REFINEMENT REPORT

> **Scope:** Cô lập trên route preview `/gioi-thieu?preview=v1.4` (`LandingPreviewV14`, branch `feat/axo-geometry-library-verification`) · **Baseline HEAD:** `b99311d3f`
> **Production Routes (`/`, `/gioi-thieu`):** Bảo toàn nguyên trạng V1.2.2 (`"prod"`) · **Workspace (`/app`):** Không thay đổi
> **Server Live Preservation:** `http://localhost:3001` (`PID 5220`, `task-83120`, lắng nghe trên `::1:3001`) được giữ nguyên hoàn toàn trong suốt phiên
> **Owner Approval:** `OWNER_APPROVAL: PENDING_OWNER_REVIEW`

---

## 1. Kiểm toán nguyên nhân gốc & Hiện trạng Baseline (`before/before_metrics.json`)

Kiểm tra trực quan và đo đạc trên `1440×900` trước chỉnh sửa cho thấy 4 nhóm vấn đề cốt lõi:

1. **Đường cắt màu nền Hero → Storytelling & cụt màn hình đầu (`first-fold truncation`):**
   - Trước đây `.axo-v14-hero` dùng nền `#FFFFFF` (`rgb(255, 255, 255)`), trong khi `.axo-v14-story` chuyển đột ngột sang nền `#F6F5F4` (`rgb(246, 245, 244)`).
   - Ở `1440×900`, `hero.bottom = 657px` (`hero.height = 585px`, `heroShell.height = 520px`), khiến `~243px` phía dưới màn hình đầu bị hở một dải màu xám `#F6F5F4` cắt ngang giữa Hero và Storytelling.
2. **Hero còn rườm rà chi tiết SGK & cảm giác cô lập một khối đơn lẻ:**
   - Khối `S.ABCD` kèm thiết diện `MENPF` bị nặng bởi lưới `4×4` trên mặt đáy `(ABCD)`, điểm phụ `K` + cung góc nhị diện `∠MKA`, và các nét rọi đứng `E′`/`F′` chồng chéo xung quanh.
   - Bóng tiếp xúc cũ dùng các đĩa phẳng lặp thay cho bóng studio radial mềm.
3. **Viền hộp lồng nhau giữa Storytelling & Demo:**
   - `.axo-v14-story-epistemic-box`, `.axo-sp-scene-shell.is-v14`, `.axo-v14-demo-orbit-hint`, `.axo-sp-ghost-chip`, `.axo-sp-step-tab` dùng viền `1px` bao quanh nhiều lớp; mặt bên sáng/tối trên hình lăng trụ SVG Storytelling có độ tương phản phẳng (`0.52`).
4. **Closing CTA hòa sắc yếu trên nền `#F6F5F4` & ngàm rọi đáy gượng gạo:**
   - Khối lăng trụ lục giác đều (`0xf8f6f2`, `opacity = 0.72`) dễ bị chìm trên nền `#F6F5F4`, đồng thời bộ `plumbGuides`/`footRings` dạng ngàm góc kỹ thuật ở đáy tạo cảm giác khô cứng.

---

## 2. Nghiên cứu tham chiếu thực tế qua REA MCP & CDP Tương tác

Thực hiện khảo sát đối chứng bằng cả **REA MCP** (`inspect_web_page` + `capture_web_screenshot`) và probe DOM/hover/scroll qua CDP `9242` (`rea/cdp-interactive-probe.json`):

| Nguồn tham chiếu | Trạng thái xác minh | Kết quả quan sát thực tế & Bằng chứng REA | Bài học thiết kế áp dụng |
| :--- | :--- | :--- | :--- |
| `https://bundaumayo.top/` | `VERIFIED_BY_REA` | HTTP `200` · `dom: 705`, `svg: 19`, `widthShift: 0`, `overflow390: 0` · `inspect_ev: ev_5b6eb948463ed30f5be2f5542635f66108fbcb2d101c815a179ceb7d0bf24975`, `shot_ev: ev_5f45bbd14e9e47d4ff6945b64a17f3794b65791a799296c9aa73c9a9ae4cd730` (`420,328` B, `sha256: 34b13bbb4b359cf4fd3facb0ce66536186b41074c05ea5336758e93f18299296`) | Nền sáng mở rộng thoáng, phân cấp khoảng trống không phụ thuộc hộp viền |
| `https://www.lusion.co/` | `VERIFIED_BY_REA` | HTTP `200` · `canvas: 3`, `svg: 41`, `dom: 1314`, `widthShift: 0`, `overflow390: 0` · `inspect_ev: ev_d24f6a38ad425e13c6a53d89a18acbd0deabd11f745ea624494ac702024f8a37`, `shot_ev: ev_1f28362dcf9cbe7d01b7728c2aaf437f732aa49e41ac75a88390c54c6bcb0ced` (`721,550` B, `sha256: 1c9f679c69441ebc6999e95361818344ac8bdee7d7bb1c92300a2391b488aeb2`) | Vệ tinh tiền/hậu cảnh phân tầng chiều sâu camera và parallax bất đối xứng |
| `https://rive.app/` | `VERIFIED_BY_REA` | HTTP `200` · `canvas: 32`, `svg: 40`, `dom: 2593`, hover contrast `rgba(255,255,255,0.85)->rgb(255,255,255)`, `widthShift: 0`, `overflow390: 0` · `shot_ev: ev_d8b185318f6b048b5fb7077dcc4a2c569b53b550a52fc8e2209862c33eac2af4` (`83,541` B, `sha256: 4ff0e59ec0f08a650326d1ec702c54d8c1e8bcd62adab02cd55fb272ea5ed5de`) | Tương tác mượt giữ cố định chiều rộng, không giật layout khi di chuột |
| `https://www.figma.com/` | `VERIFIED_BY_REA` | HTTP `200` · `svg: 69`, `dom: 1686`, `widthShift: 0`, `overflow390: 0` · `inspect_ev: ev_e8740f5632074b6947f1429a0529aeab38cea167a2a59df59e78517d026c1cb1` | Ngôn ngữ bề mặt giấy/nền trắng sạch nhường trọng tâm cho vật thể trực quan |
| `https://tympanus.net/codrops/hub/` | `NOT_VERIFIED` | HTTP `403`, title `"Just a moment..."` (Cloudflare anti-bot challenge; không thực hiện vượt/giải challenge) | Không trích dẫn đặc tả từ nguồn bị chặn |

**Chụp REA MCP hậu chỉnh sửa trên bản chạy trực tiếp `http://[::1]:3001/gioi-thieu?preview=v1.4` (`rea/rea-after.json`):**
- `list_browser_targets` `evidence_id`: `ev_2317959cb49b58988916479da0e788010e12b66121fc5fc80764e8a3b91c7b99`
- `inspect_web_page` `evidence_id`: `ev_93845cc5c52dceb9480074aa8070238a2368d122142ee109ffa57f97218323b4` (`456` nút DOM, `113` scripts)
- `capture_web_screenshot` `evidence_id`: `ev_79d298e988c1870e44448d2de31ee8304910aa866147db691342856451a7b7b8` (`74,961` B, `1440×900`, `sha256: 96bc4d78ae36c79ca208834cb79bc0f57f76b312f8368e063696a74c36b3b6f2`, lưu tại `rea/after_localhost_3001.png` và đã kiểm tra trực tiếp).

---

## 3. Lựa chọn phương án thiết kế & Tái thiết kế hệ thống thị giác

### Concept A (Được chọn): **Spatial Geometry Gallery** kết hợp biên đạo trung tâm tất định 4 nhịp
- **Lý do chọn Concept A thay Concept B (khối đơn lập cô độc):** Thư viện không gian cho phép vừa giữ vai trò chính xác định tính của khối chóp `S.ABCD` + mặt cắt `(MNP)` + thiết diện ngũ giác `MENPF` (`HERO_SECTION_FILL_OPACITY = 0.5`), vừa mở chiều sâu trường ảnh studio với 3 vệ tinh đa diện chuẩn toán học phân bố bất đối xứng theo tam giác không thẳng hàng quanh tâm.
- **Triển khai trong [LandingHeroV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroV14.tsx):**
  - Loại bỏ lưới `4×4`, điểm `K`, cung nhị diện và bộ ngàm rọi `projFoot*` / `plumbLine*`; chỉ giữ 6 điểm neo thiết yếu (`S, M, N, P, E, F`), ký hiệu vuông góc `SA ⊥ (ABCD)` tại `A`, vết đáy `NP`, cung phương vị và bóng tiếp xúc radial mềm (`createHeroShadowTexture()`).
  - Thêm `buildHeroSpatialGallerySpecs()` (`HERO_SATELLITE_COUNT = 3`) định vị 3 vệ tinh trong hệ cơ sở camera `(basisRight, basisUp, basisForward)` với 3 độ sâu tách biệt:
    1. **Vệ tinh hậu cảnh trên-phải (`octahedron`):** Bát diện đều cạnh bằng nhau (`r = 0.44`) kèm mặt cắt vuông ngang đường xích đạo (`screenDx: 2.36, screenDy: 1.88, screenDz: 1.35`).
    2. **Vệ tinh tiền cảnh trái (`extractedPentagon`):** Ngũ giác thiết diện trích đẳng cự chuẩn tỉ lệ `computeTrueShapeSection2D()` kèm bóng dưới khay (`screenDx: -2.92, screenDy: 0.58, screenDz: -0.65`).
    3. **Vệ tinh trung cảnh phải (`slicedCube`):** Khối lập phương khung dây cắt bởi mặt `x + y + z = 0` thành lục giác đều (`screenDx: 3.24, screenDy: -0.36, screenDz: -0.28`).
  - Hiệu chỉnh `applyHeroCameraFraming()` (`scaleDist = aspect < 1.2 ? 1.12 + (1.2 - aspect) * 0.62 : 1.1`, co `curAspectSpread` khi `aspect < 1.08`) sau phát hiện trực quan ở lượt kiểm định đầu tiên để triệt tiêu hoàn toàn chạm mép giữa vệ tinh và cạnh `SB` / `SD` trên cả desktop và mobile `320px`. Bỏ qua `pointerType === "touch"` ở `handlePointerMove`. Đồng bộ `<HeroFallbackSvg />`.

### Tái cân bằng bề mặt nền, Storytelling, Demo & Closing CTA
- **Thống nhất nhịp nền ([landing.css](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing.css)):**
  - `.axo-v14-hero`, `.axo-v14-story`, `.axo-sp-demo-section.is-v14` dùng chung nền trắng `--axo-sp-bg` (`rgb(255, 255, 255)`), triệt tiêu đường cắt ngang ở fold đầu.
  - `.axo-v14-hero-shell` dùng `min-height: clamp(500px, calc(100svh - 156px), 700px)`; `.axo-v14-hero-visual` dùng `height: clamp(430px, 45vw, 550px)` và `touch-action: pan-y`.
  - `.axo-v14-story-stage` và `.axo-sp-demo-workbench.is-v14` dùng khay lõm `--axo-sp-paper` (`rgb(246, 245, 244)`), bỏ viền `1px` ở `.axo-v14-story-epistemic-box`, `.axo-v14-demo-orbit-hint`, `.axo-sp-ghost-chip`, `.axo-sp-step-tab`, và đặt khung cảnh trắng sạch `--canvas` (`border: 0`) cho `.axo-sp-scene-shell.is-v14`.
- **Storytelling ([LandingStorytellingV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingStorytellingV14.tsx)):** Nâng tương phản mặt bên sáng/tối (`fillOpacity` `0.82` / `0.44` theo `toneClass`) kết hợp `--axo-sp-accent-tint` trên nền khay `--axo-sp-paper`.
- **Closing CTA ([LandingClosingScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingScene3D.tsx)):**
  - Nội suy sắc độ mặt lăng trụ lục giác từ xám xanh mát `(0.84, 0.88, 0.94)` tới sứ trắng ấm `(1.0, 0.996, 0.988)` trên chất liệu `0xffffff` (`lowerMat.opacity = 0.92`, `upperMat.opacity = 0.24`), nổi bật tách nền `#F6F5F4`.
  - Thay đĩa tròn AO và ngàm chân `plumbGuides`/`footRings` bằng bóng tiếp xúc radial `createClosingShadowTexture()` và **Companion 3 = Bản trích lát cắt lục giác xiên** `computeClosingExtractedHexagon2D()` ở hậu cảnh trên-phải (`dx=2.08, dy=1.12, dz=1.1`), đồng bộ trong `<ClosingFallbackSvg />`.

---

## 4. Định lượng Trước / Sau (`1440×900`) & Kiểm chứng đa thiết bị

### So sánh Trước / Sau trên `1440×900`
| Chỉ số đo (`1440×900`) | Trước (`before_metrics.json`) | Sau (`after_metrics.json`) | Ghi chú |
| :--- | :--- | :--- | :--- |
| `hero.bottom` / `hero.height` | `657px` / `585px` | `842px` / `770px` | Lấp đầy hợp lý khung nhìn đầu, hết hở nền xám |
| `heroShell.height` / `heroVisual.height` | `520px` / `520px` | `700px` / `550px` | Cân đối cụm chữ CTA trái và gallery 3D phải |
| `hero.bg` → `story.bg` → `demoSection.bg` | `#FFFFFF` → `#F6F5F4` → `#FFFFFF` | `#FFFFFF` → `#FFFFFF` → `#FFFFFF` | Nền trắng liên tục qua 3 phần |
| `storyStage.bg` / `demoWorkbench.bg` | `#FFFFFF` / `transparent` | `#F6F5F4` / `#F6F5F4` | Khay sân khấu lõm thống nhất |
| `closing.bg` → `footer.bg` | `#F6F5F4` → `#FFFFFF` | `#F6F5F4` → `#FFFFFF` | Chuyển nhịp sạch cho vùng kết và chân trang |
| `overflowX` / `CLS` / `idleRaf1s` | `—` / `—` / `—` | `0` / `0` / `0` | Tổng chiều cao trang `4981px` |

### Kết quả kiểm thử kỹ thuật (sau edit cuối)
| Bộ kiểm thử / Công cụ | Phạm vi | Kết quả thực tế |
| :--- | :--- | :--- |
| `npx tsc -b` | Toàn bộ `frontend/` | **PASS** — exit `0` |
| `npx vite build` | Toàn bộ `frontend/` | **PASS** — exit `0`, 127 modules, `✓ built in 5.32s` |
| `npx vitest run --testTimeout=20000` | Toàn bộ unit/integration/Chromium test | **PASS** — `191 / 191` files passed, `2250 / 2250` tests passed (`128.93s`) |
| `lint.mjs` (`design-taste-frontend`) | 8 file `.tsx` V1.4 (`LandingPreviewV14`, `LandingHeader`, `AnnotatedHeading`, `LandingHeroV14`, `LandingStorytellingV14`, `LandingInteractiveDemo`, `LandingClosingV14`, `LandingClosingScene3D`) | **PASS** — `0 FAIL, 0 WARN` trên cả 8/8 file (Lưu ý: `LandingView.tsx` dòng `138` của V1.2.2 giữ nguyên `.axo-sp-eyebrow` production không chỉnh sửa) |
| `inspect.mjs` — **Prod Preview** (`http://127.0.0.1:4179`, `vite preview`) | `--widths 1440,768,390 --film` | **Exit 1:** `1440×900`, `768×1024`, `390×844` render đủ chữ (`401`/`376`/`376` từ), `overflow = 0`, sạch `no-title`/`hero-void`/`covered-text`/`small-text`/`outlined-box`. Còn `few-pictures` (`FAIL` — chỉ đếm `<img>`, không tính WebGL Canvas/SVG) và `no-footage` (`WARN` — không dùng `<video>`). *Ghi chú:* bản chạy thử `inspect.mjs` trên dev server `::1:3001` gặp hiện tượng tải module rời bị nghẽn thoáng qua ở 1 tab (`words = 0`), nên bản production preview `4179` mới phản ánh đúng bundle thật. |
| Ma trận Playwright 8 Viewport (`verify-spatial-system.mjs`) | `1920×1080`, `1440×900`, `1366×768`, `1024×768`, `768×1024`, `390×844`, `360×800`, `320×568` | **PASS** — exit `0`, `0` lỗi trên 8/8 viewport: `overflowX = 0`, `CLS = 0`, `idleRaf = 0`, `pageErrors = 0`, `heroBeat = "section-settled"`, `scrollTop` sau `#btn-landing-footer-top` `< 10` |
| Tương tác, Trạng thái & Route không hồi quy | Story scroll xuôi `[0,1,2,3]` & ngược `[2,1,0]`, Demo 2 mẫu + orbit chuột/phím + reset, Auth (`"Vào ứng dụng"`), Drawer mobile (`Escape` trả focus), `?no_webgl=1` SVG fallback, `reducedMotion`, `/`, `/gioi-thieu`, `/app` | **PASS** — toàn bộ đạt, `/` và `/gioi-thieu` giữ V1.2.2 (`hasV14Hero: false`), `/app` `overflowX = 0`, `errs: []` |
| 6 Video `.webm` & Keyframes | `landing_spatial_system/videos/01..06*.webm` + `keyframes/` | **PASS** — đủ 6 video (`636,177 B` – `1,532,788 B`), đã mở xem ảnh chụp `1440/1366/768/390/320`, `?no_webgl=1` và keyframes qua `read_file` |
| `npx vitest run code-index-sync` | Đồng bộ `docs/CODE_INDEX.md` (dòng `1983`) | **PASS** — `1 / 1` file, `3 / 3` tests passed (`264ms`) |
| `python backend/scripts/audit_docs_information_architecture.py --json` | Cấu trúc `docs/`, liên kết và chỉ mục | `LINKS.valid = true` (`684` liên kết, `0` gãy), `DOCS_LAYOUT.valid = true` (`29` root docs, `167` catalog, `0` unclassified), `SECRET_SCAN.valid = true`; `STATUS = FAIL` **chỉ** do `CODE_INDEX.stale_path_count = 4` có sẵn ngoài phạm vi (`4605, 4619, 4634, 4646`) |

---

## 5. Sơ đồ phụ thuộc & Vòng đời Query Param (§14)

- **Chuỗi module Preview V1.4:**
  - `LandingView.tsx` kiểm tra `readLandingPrototypeMode()` (`?preview=v1.4` → `LandingPreviewV14.tsx`; mặc định `"prod"` → nhánh V1.2.2 giữ nguyên).
  - `LandingPreviewV14.tsx` ghép tuần tự 5 lớp: `LandingHeader (presentation="v14")` → `LandingHeroV14` → `LandingStorytellingV14` → `LandingInteractiveDemo (presentation="v14")` → `LandingClosingV14 (LandingClosingScene3D + LandingFooterV14)`.
  - Dữ liệu hình học dùng chung một nguồn chân lý `landing-geometry-data.ts` (`LANDING_PYRAMID_SAMPLE`, `LANDING_CUBE_SAMPLE`, `LANDING_PRISM_STORY_SPEC`, `computeBoundedPlaneQuad`).
- **Vòng đời Query Params:**
  - `?preview=v1.4`: Kích hoạt cây preview Spatial Visual System cô lập; chuyển route về `/` hoặc `/gioi-thieu` trở về V1.2.2.
  - `?no_webgl=1`: Ép Hero & Closing chuyển tức thì sang `<HeroFallbackSvg />` và `<ClosingFallbackSvg />` với `data-cta-visual="svg-fallback"` mà không khởi tạo `WebGLRenderer`.
  - `?story_progress=<0..1>`: Ghim tiến trình Storytelling phục vụ kiểm chứng từng chặng xác định.
  - Không thay đổi bất kỳ route hay trạng thái nào của `/app` hoặc `backend/**`.

---

## 6. Tổng kết Trạng thái & Phê duyệt (§15 `A–G`)

- **A. IMPLEMENTED:** Hoàn thiện Concept A Spatial Geometry Gallery trong [LandingHeroV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroV14.tsx), tương phản lăng trụ SVG [LandingStorytellingV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingStorytellingV14.tsx), sứ trắng + lát cắt lục giác Companion 3 trong [LandingClosingScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingScene3D.tsx), thống nhất nền trắng/giấy đá và xóa viền lồng trong [landing.css](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing.css), bổ sung unit tests trong [landing-hero-visual-lifecycle.test.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-hero-visual-lifecycle.test.tsx) và [landing-cta-geometry.test.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-cta-geometry.test.tsx).
- **B. VERIFIED:** `npx tsc -b`, `npx vite build`, `191/191` file (`2250/2250` test cases) Vitest, `lint.mjs` (`0 FAIL, 0 WARN` trên 8 file TSX V1.4), `inspect.mjs` trên bundle production `4179`, Playwright 8 viewport + 6 video `.webm` + kiểm tra trực tiếp hình ảnh + REA MCP post-edit capture `ev_79d298e988c1870e44448d2de31ee8304910aa866147db691342856451a7b7b8`.
- **C. NOT_VERIFIED:**
  - `https://tympanus.net/codrops/hub/` (`HTTP 403` Cloudflare challenge).
  - Thiết bị di động vật lý (`NOT_PHYSICAL_MOBILE`): mọi bài kiểm tra `768×1024`, `390×844`, `360×800`, `320×568` đều chạy trên Chromium giả lập WebGL qua SwiftShader (`--use-angle=swiftshader`).
- **D. KNOWN_ISSUES:**
  - `inspect.mjs` tiếp tục báo `few-pictures` (`FAIL`) và `no-footage` (`WARN`) vì đánh giá `<img>`/`<video>` thay cho WebGL `<canvas>` / `<svg>` dựng hình thực.
  - `python backend/scripts/audit_docs_information_architecture.py --json` có sẵn 4 đường dẫn stale `OWNERSHIP_BLOCKED` trong `docs/CODE_INDEX.md` (các dòng `4605, 4619, 4634, 4646` thuộc tính năng classroom ngoài phạm vi Landing — giữ nguyên không sửa).
- **E. PRODUCTION_UNCHANGED:** `YES` (`/` và `/gioi-thieu` giữ V1.2.2 `"prod"`, `/app` không đổi).
- **F. PORT_3001_PRESERVED:** `YES` (`PID 5220` lắng nghe trên `::1:3001`, không kill hay restart).
- **G. OWNER_APPROVAL:** `OWNER_APPROVAL: PENDING_OWNER_REVIEW`
