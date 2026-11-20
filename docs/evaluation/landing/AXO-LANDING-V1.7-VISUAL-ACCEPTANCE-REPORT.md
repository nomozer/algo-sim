# AXO LANDING V1.7 — BÁO CÁO NGHIỆM THU THỊ GIÁC & TINH CHỈNH TRẢI NGHIỆM

> **Tuyến kiểm thử:** `/gioi-thieu?preview=v1.4` ([LandingPreviewV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingPreviewV14.tsx)) · **Nhánh:** `feat/axo-geometry-library-verification`
> **Môi trường phát triển giữ nguyên trạng:** `http://[::1]:3001` (`PID 16060`, không dừng/khởi động lại trong toàn bộ phiên)
> **Trạng thái nghiệm thu:** `OWNER_APPROVAL: PENDING_OWNER_REVIEW`

---

## 1. Git `HEAD` trước khi sửa và trạng thái Commit

- **`HEAD` trước wave tinh chỉnh (verified via `git rev-parse HEAD`):** `762402943774a21b07212c772854de8d55d4cbfb`
- **Nhánh làm việc:** `feat/axo-geometry-library-verification`
- **Trạng thái tích hợp:** Không merge vào `main`, không push lên remote, không rewrite lịch sử (`rebase`/`amend`), không xóa nhánh hay mã legacy V1.2.2. Báo cáo này được lập và kiểm tra trước khi commit đóng gói `allowlist` trên nhánh hiện hành.

---

## 2. Danh sách đầy đủ các file đã chỉnh sửa & Biên giới `OWNERSHIP_BLOCKED`

Chỉ chạm **11 file thuộc phạm vi Landing V1.4 + kiểm thử + tài liệu chỉ mục/báo cáo**; toàn bộ các file `OWNERSHIP_BLOCKED` đang thay đổi dở trên working tree (`backend/**`, hệ `SimulationWorkspace.tsx`, classroom/live-session, `docs/EVIDENCE_INDEX.md`) được giữ nguyên hoàn toàn:

| STT | File | Vai trò trong đợt tinh chỉnh V1.7 Visual Acceptance |
| :---: | :--- | :--- |
| 1 | [LandingStorytellingV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingStorytellingV14.tsx) | Bỏ thẻ hộp xám; `prismBuild = 1` dựng đủ lăng trụ ngay Chặng 1 kèm hào quang tâm điểm gốc `M, N, P`; bỏ mũi tên vector `>>` thay bằng dải/gióng song song; nâng khung SVG lên `700×500` (`scale = 76`); thêm thẻ Chặng 4 `Hình thật thiết diện` / `Hình thang cân MNPQ`; thêm `.axo-v14-story-context-line` và lọc trùng chữ thanh tiến trình |
| 2 | [LandingInteractiveDemo.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingInteractiveDemo.tsx) | Hiển thị tên mô hình `.axo-v14-demo-model-name` ở cột biên tập mở bên phải trong chế độ `isV14` (giữ nguyên nhánh `"default"` V1.2.2) |
| 3 | [LandingHeroScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroScene3D.tsx) | Khóa hướng cử chỉ cảm ứng (`gestureMode: "idle" \| "pending" \| "orbit" \| "scroll"`) chỉ trong nhánh `presentation === "v14"` để vuốt dọc cuộn trang mượt mà không kích hoạt nhầm orbit |
| 4 | [landing-geometry-data.ts](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing-geometry-data.ts) | Thêm hàm tất định `computeShowcaseCameraPreset(points, sectionNormalThree, opts)` tính góc nhìn xiên theo pháp tuyến mặt cắt; áp dụng cho `LANDING_PYRAMID_SAMPLE` (`normalCosine = 0.8699`) và `LANDING_CUBE_SAMPLE` (`normalCosine = 0.9703`, diện tích lục giác `6.3×`); gọn hóa copy `v14Title` / `v14Guide` / `v14Focus` |
| 5 | [LandingHeroV14.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroV14.tsx) | Dịch vệ tinh trái `extractedPentagon` (`screenDx = -3.16`) và nới `applyHeroCameraFraming` (`scaleDist = 1.13`, `aspect < 1.2`) tách thoáng khỏi mép xanh mặt phẳng `(MNP)` |
| 6 | [LandingClosingScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingScene3D.tsx) | Đổi màu đáy thân sứ phần dưới sang trắng tinh `0xffffff` (`lowerMat.opacity = 0.94`) để nổi sắc khối rõ trên nền giấy ấm `--axo-sp-paper` `#F6F5F4` |
| 7 | [landing.css](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/landing.css) | Khôi phục nhịp nền luân phiên (`Hero #FFF → Story #F6F5F4 → Demo #FFF → Closing #F6F5F4 → Footer #F6F5F4` ngăn bằng hairline trong `.axo-v14-footer-shell`); sân khấu Storytelling không khung viền; khay Demo không viền trên `--axo-sp-paper`; chữ SVG `paint-order: stroke`; nút chạm di động `>= 44px` |
| 8 | [landing-scroll-storytelling.test.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-scroll-storytelling.test.tsx) | Kiểm chứng `prismBuild === 1`, thẻ `Hình thật thiết diện`, không tồn tại hàm mũi tên vector `buildParallelChevronD`, lớp `.axo-v14-story-context-line` |
| 9 | [landing-product-integrity.test.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/__tests__/landing-product-integrity.test.tsx) | Kiểm chứng hiển thị `.axo-v14-demo-model-name` và hàm `computeShowcaseCameraPreset` đạt `normalCosine >= 0.65` |
| 10 | [CODE_INDEX.md](file:///D:/Documents/projects/axo-geometry-library/docs/CODE_INDEX.md#L1983) | Cập nhật đồng bộ duy nhất dòng `1983` cho cụm Landing V1.4+ |
| 11 | `docs/evaluation/landing/AXO-LANDING-V1.7-VISUAL-ACCEPTANCE-REPORT.md` | Báo cáo nghiệm thu 14 mục này |

---

## 3. Vấn đề phát hiện khi kiểm tra thực tế & Nguyên nhân gốc

Đối chiếu trực tiếp ảnh chụp `BEFORE` (`landing_v1_7_acceptance/before/*.png` và `rea/before_localhost_3001.png`) chỉ ra **9 điểm nghẽn thiết kế và hình học**:

1. **Storytelling mang dáng dấp thẻ demo đóng hộp xám:** Toàn section `#cach-hoat-dong` nằm trên nền trắng `#FFFFFF`, trong khi bên phải đặt khung xám `.axo-v14-story-stage` đóng viền bo tròn trên `--axo-sp-paper` làm tách biệt như hộp nhúng thay vì sân khấu biên tập liền mạch.
2. **Lăng trụ Chặng 1 cụt vỡ thiếu mặt trên:** Ở Chặng 1 (`before_story_s1_1440x900.png`), `prismBuild < 1` khiến ba cột bên bị đứt đoạn và thiếu hoàn toàn tam giác đáy trên `A′B′C′`, gây cảm giác mô hình bị lỗi vẽ thay vì một lăng trụ đứng hoàn chỉnh.
3. **Mũi tên vector `>>` làm nhiễu ngôn ngữ hình học:** `buildParallelChevronD` vẽ ký hiệu `>>` dọc các đoạn `MN`, `PQ`, `BC` (`before_story_s4_1440x900.png`), dễ hiểu nhầm thành vector có hướng thay vì quan hệ song song `MN ∥ BC ⇒ PQ ∥ BC`.
4. **Thẻ hình thật thiết diện Chặng 4 quá nhỏ:** Góc `Hình thật (MNP)` trước đây nhỏ lọt thỏm góc trên phải, khó đọc trực quan bản chất hình thang cân phẳng `MNPQ`.
5. **Cột trái Storytelling lặp thông tin:** Văn bản nhãn bước và trạng thái lặp ý ở thanh điều hướng và khối chú thích, đồng thời thiếu dòng ngữ cảnh ngắn chỉ rõ tên khối `Lăng trụ tam giác đều ABC.A′B′C′`.
6. **Góc nhìn mặc định Lập phương trong Demo bị bẹt thành dải mỏng ~9° (`BEFORE` `cos θ = 0.157`):** Điểm đặt `v14CameraPos = [9.2, 6.0, -6.7]` gần như nhìn sượt cạnh mặt cắt `-x + y + z = 2` (pháp tuyến Three.js `(-1, 1, -1)`), làm lục giác đều `MNEPFQ` chỉ chiếm `14,096 px²` trên `1440×900` (`before_demo_cube_1440x900.png`).
7. **Demo thiếu tên mô hình rõ ở cột phải & xung đột vuốt dọc trên mobile:** Người dùng không nhìn thấy tên mô hình đang đọc ngay trong cột thông tin bên phải nếu không ngoái lại công tắc chọn ở đầu section; trên thiết bị cảm ứng, thao tác vuốt dọc cuộn trang chạm vào canvas 3D có thể bị bắt thành kéo xoay mô hình, và các nút bước chưa đạt chuẩn chạm `44px`.
8. **Hero vệ tinh trái đụng mép xanh mặt cắt:** Trong `before_localhost_3001.png` và `before_hero_1440x900.png`, vệ tinh `extractedPentagon` ở bên trái chạm chồng lên viền xanh của mặt phẳng `(MNP)`.
9. **Closing CTA & Footer chuyển nhịp nền phẳng:** Closing dùng nền trắng `#FFFFFF` khiến khối lăng trụ lục giác thân xám mờ nhẹ trên giấy trắng và không tạo độ ấm tương phản từ Demo (`#FFF`) sang Closing/Footer (`#F6F5F4`).

---

## 4. Thay đổi chi tiết ở Storytelling

- **Bố cục & Nhịp nền (`landing.css`, `LandingStorytellingV14.tsx`):** Chuyển toàn bộ `#cach-hoat-dong` sang nền giấy ấm `--axo-sp-paper` (`#F6F5F4`); gỡ bỏ nền hộp và đường viền của `.axo-v14-story-stage` để lăng trụ `ABC.A′B′C′` nổi không viền giữa vùng sân khấu sticky căn giữa màn hình desktop (`100vh`).
- **Tối giản cột trái:** Hợp nhất 1 thanh tiến trình 4 chặng (`.axo-v14-story-rail` + `.axo-v14-story-rail-fill`), thêm 1 dòng ngữ cảnh duy nhất `.axo-v14-story-context-line` (`Mô hình: Lăng trụ tam giác đều ABC.A′B′C′`), giữ độ mờ chuyển tiếp chapter tối thiểu `0.74` để người đọc luôn giữ mạch liền khối khi cuộn xuôi lẫn cuộn ngược.
- **Khôi phục hình học Chặng 1 → Chặng 4:**
  - `prismBuild = 1` ở mọi chặng để Chặng 1 hiển thị đủ đáy dưới `ABC`, ba cạnh bên và đáy trên `A′B′C′` sắc nét, kèm vòng hào quang đồng tâm `.axo-v14-svg-seed-halo` nhấn 3 trung điểm xuất phát `M, N, P`.
  - Gỡ bỏ `buildParallelChevronD` (`>>`), thay bằng dải song song mềm `.axo-v14-svg-parallel-band` + vạch gióng `.axo-v14-svg-parallel-guide`. Giữ khóa `Q` chỉ xuất hiện từ Chặng 3–4.
  - Mở rộng SVG `viewBox` lên `700×500` (`scale = 76`, dịch tâm ngang `cx = lerp(350, 240, insetReveal)` ở Chặng 4) và thêm thẻ **`Hình thật thiết diện` / `Hình thang cân MNPQ`** nổi bật ở vùng `x=458..684, y=24..234` (`insetScale = 35`), **0 đáp án số học**. Khoảng cách mép thẻ tới nhãn lăng trụ đo được đạt `11px` (`320px`) tới `34px` (`1440px–1920px`).
  - Áp dụng `paint-order: stroke fill` viền trắng nền cho chữ đỉnh/điểm SVG (`svgLabelsClipped = 0` trên cả 8 viewport).

---

## 5. Thay đổi chi tiết ở Interactive Demo

- **Khôi phục nhịp nền sáng & bố cục mở (`landing.css`, `LandingInteractiveDemo.tsx`):** Đưa `#trai-nghiem` lên nền trắng tinh `--axo-sp-bg` (`#FFFFFF`), đặt canvas WebGL vào sân khấu không viền `--axo-sp-paper` (`#F6F5F4`), loại bỏ hộp lồng hộp ở cột phải, bổ sung nhãn tên mô hình `.axo-v14-demo-model-name` (trên `"v14"`) đúng trật tự biên tập 5 phần: *Tên mô hình → Bước hiện tại → Tiêu đề ngắn → Hướng dẫn quan sát → CTA Mở trong Xưởng 3D*.
- **Thuật toán đặt góc nhìn tất định `computeShowcaseCameraPreset` (`landing-geometry-data.ts`):**
  - Tự động tính tâm `lookAt` từ AABB toàn bộ tập đỉnh khối (`domainCoordsToThreeVec`) và đặt `cameraPos` dọc tổ hợp chuẩn hóa của pháp tuyến mặt cắt (`sectionNormalThree`), hướng ngang chính diện và độ nâng camera mà không thay đổi bất kỳ tọa độ hình học gốc nào.
  - **Hình chóp `S.ABCD`:** `lookAt = [0, 0.35, 0]`, `cameraPos = [7.928, 6.729, -10.529]`, `normalCosine = 0.8699` (giữ ổn định qua đủ 4 bước).
  - **Hình lập phương `ABCD.A′B′C′D′`:** `lookAt = [0, 0, 0]`, `cameraPos = [-9.225, 5.414, -5.854]`, **`normalCosine = 0.9703`** (tăng từ `0.157` / góc sượt `9.0°` trước đây), giúp lục giác đều `MNEPFQ` hiển thị rộng chính diện với **diện tích chiếu tăng `6.3×` (`14,096 px² → 89,125 px²`)** và khoảng cách tối thiểu giữa 14 đỉnh `>= 79px`.
- **Cử chỉ chạm di động & kích thước nút (`LandingHeroScene3D.tsx`, `landing.css`):** Trong nhánh `presentation === "v14"`, bổ sung khóa hướng cử chỉ `gestureMode` (`"idle" | "pending" | "orbit" | "scroll"`): khi vuốt dọc (`totalDy > totalDx * 1.15`) trang cuộn tự nhiên không bị kẹt orbit (`resetAfterVerticalSwipe = "false"`), khi vuốt ngang/chéo khối 3D xoay mượt (`resetAfterHorizontalOrbit = "true"`). Trên mobile giữ đúng thứ tự *Heading → Bộ chọn mẫu → Khối 3D → Thanh bước → Hướng dẫn & CTA*, mọi nút chọn mẫu/bước đạt chiều cao `44px`.

---

## 6. Những khu vực đã giữ tốt / Tinh chỉnh bảo toàn

- **Header (`LandingHeader.tsx`):** Không bị hồi quy, pill mục đang xem, Guest 5 liên kết gọn sạch, trạng thái đăng nhập hiển thị đúng `"Vào ứng dụng"`.
- **Hero (`LandingHeroV14.tsx`):** Bảo toàn tiêu đề 2 dòng cân đối + nét khoanh cam `"hình dung"` + 2 CTA capsule + mô hình `S.ABCD` và đúng **3 vệ tinh liên kết** (`HERO_SATELLITE_COUNT = 3`); tinh chỉnh `extractedPentagon` (`screenDx = -3.16`) và `applyHeroCameraFraming` để vệ tinh trái tách thoáng viền `(MNP)`.
- **Closing CTA & Footer (`LandingClosingV14.tsx`, `LandingClosingScene3D.tsx`):** Giữ khối lăng trụ lục giác đều (`data-section-edges="6"`, `capLift: 0 → 0.22`) kết hợp nền ấm `--axo-sp-paper` `#F6F5F4` đồng bộ với Footer (ngăn bằng hairline trong bề rộng `.axo-v14-footer-shell`, `#btn-landing-footer-top` hoạt động cuộn về đầu trang); làm sáng mặt sứ trắng `0xffffff` giúp mặt khối rõ nét hơn trên nền giấy ấm.
- **Tuyến Production V1.2.2 & Workspace:** Kiểm chứng thực tế `/` (`rootProd.hasProdHero = true, hasV14Hero = false, overflowX = 0`), `/gioi-thieu` (`gioiThieuProd.hasProdHero = true, hasV14Hero = false, overflowX = 0`), và `/app` (`mounted = true, overflowX = 0`) đều nguyên vẹn.

---

## 7. Kết quả kiểm tra trực quan qua đủ 8 viewport

Toàn bộ ảnh chụp được ghi và mở xem bằng `read_file` tại thư mục artifact `C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\landing_v1_7_acceptance\` (`before/`, `after/`, `perf/after_acceptance_metrics.json`):

| Viewport | `overflowX` | `CLS` | Story Fwd / Rev | Nhãn SVG cắt (`storyLabelsClipped`) | Khoảng thoáng TrueShape (`px`) | Demo `S` đè hint | Chiều cao nút Sample / Step (`px`) | Hero / Closing Settled Idle RAF | Ảnh `AFTER` tiêu biểu |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `1920×1080` | `0` | `0` | `[0,1,2,3]` / `[2,1,0]` | `0` | `34` | `false` | `40` / `40` | `0` / `0` | `after_hero_1920x1080.png` |
| `1440×900` | `0` | `0` | `[0,1,2,3]` / `[2,1,0]` | `0` | `34` | `false` | `40` / `40` | `0` / `0` | `after_hero_1440x900.png`, `after_story_s1..s4_1440x900.png`, `after_demo_pyramid_1440x900.png`, `after_demo_cube_1440x900.png`, `after_closing_1440x900.png`, `after_footer_1440x900.png` |
| `1366×768` | `0` | `0` | `[0,1,2,3]` / `[2,1,0]` | `0` | `32` | `false` | `40` / `40` | `0` / `0` | `after_hero_1366x768.png` |
| `1024×768` | `0` | `0` | `[0,1,2,3]` / `[2,1,0]` | `0` | `26` | `false` | `40` / `40` | `0` / `0` | `after_hero_1024x768.png`, `after_demo_pyramid_1024x768.png`, `after_demo_cube_1024x768.png` |
| `768×1024` | `0` | `0` | `[0,1,2,3]` / `[2,1,0]` | `0` | `19` | `false` | `40` / `44` | `0` / `0` | `after_hero_768x1024.png`, `after_story_s1..s4_768x1024.png`, `after_demo_pyramid_768x1024.png`, `after_demo_cube_768x1024.png`, `after_closing_768x1024.png` |
| `390×844` | `0` | `0` | `[0,1,2,3]` / `[2,1,0]` | `0` | `16` | `false` | `44` / `44` | `0` / `0` | `after_hero_390x844.png`, `after_story_s1..s4_390x844.png`, `after_demo_pyramid_390x844.png`, `after_demo_cube_390x844.png`, `after_closing_390x844.png`, `after_footer_390x844.png` |
| `360×800` | `0` | `0` | `[0,1,2,3]` / `[2,1,0]` | `0` | `15` | `false` | `44` / `44` | `0` / `0` | `after_hero_360x800.png`, `after_demo_pyramid_360x800.png`, `after_demo_cube_360x800.png` |
| `320×568` | `0` | `0` | `[0,1,2,3]` / `[2,1,0]` | `0` | `11` | `false` | `44` / `44` | `0` / `0` | `after_hero_320x568.png`, `after_story_s1..s4_320x568.png`, `after_demo_pyramid_320x568.png`, `after_demo_cube_320x568.png`, `after_closing_320x568.png`, `after_footer_320x568.png` |

- **Kiểm tra bổ sung:** `leakedAnswers = []` trên **8 / 8** viewport (0 đáp án bài giải bị lộ); `sectionBgs` xác nhận chính xác `#FFFFFF → #F6F5F4 → #FFFFFF → #F6F5F4 → #F6F5F4` trên **8 / 8** viewport; `ArrowLeft` chuyển bước bằng bàn phím (`stepAfterKey = "true"`), kéo xoay hiện nút Đặt lại góc nhìn (`resetVisibleAfterDrag = true`), bấm `#btn-landing-demo-reset` ẩn nút (`resetHiddenAfterClick = true`), bấm `#btn-landing-footer-top` cuộn về đầu trang đạt yêu cầu.
- **`design-taste-frontend` Quality Gates:**
  - `lint.mjs` trên cả 8 tệp TSX V1.4: **PASS (`0 FAIL, 0 WARN`)**.
  - `inspect.mjs` trên bản production preview (`vite preview --port 4181`, `1440×900`, `768×1024`, `390×844`): **`0` `horizontalOverflow`, `0` `lowContrast`, `0` `smallText`, `0` `consoleErrors`, `0` `outlinedBoxes` trên desktop/tablet** (`1` ở `390px`, `1` `hairline` nội bộ `div.axo-v14-footer-shell`); chỉ báo `[few-pictures]` (`FAIL`) và `[no-footage]` (`WARN`) do `inspect.mjs` chỉ đếm thẻ `<img>`/`<video>` truyền thống mà không tính WebGL `<canvas>`/`<svg>`.

---

## 8. Kết quả kiểm tra bằng REA MCP (Trước / Sau trên Live `localhost:3001` & Tham chiếu ngoài)

- **BEFORE trên `http://[::1]:3001/gioi-thieu?preview=v1.4` (`rea/rea-before.json`):**
  - `list_browser_targets`: `ev_c904887b105d82eca889dc3bae53e09f5a8950472ca9d60ee8fd1854f66079b4`
  - `inspect_web_page`: `ev_2dbedb713870da3689f56cc41c59259a4650e47293e7c4db53633d7fdebca31a` (`domTotalNodes: 451`, `resourcesCount: 20`, `consoleErrors: 0`)
  - `capture_web_screenshot`: `ev_45143cbd82b2a58ac0ac683fc47f1017515d48b69349a28383802e271a587543` (`1422×748`, `75,591` B, `sha256: 6363546e8f13d756c019289843c47814a9521de4b03ca3cb6812b4414dced067`, `rea/before_localhost_3001.png`)
- **AFTER trên `http://[::1]:3001/gioi-thieu?preview=v1.4` (`rea/rea-after.json`):**
  - `list_browser_targets`: `ev_ffdb1c38ab5e317f6e9f29f977f30b196a7ca3ff1def00cd7794a546127a40ed`
  - `inspect_web_page`: `ev_514a5b3a1d8edea83833759a788f5520af87ef597a800ac75f132c403d2d61ce` (`domTotalNodes: 462`, `resourcesCount: 20`, `consoleErrors: 0`)
  - `capture_web_screenshot`: `ev_f01399bbd58051e17a0d556b1450f54a5d36e8b73e453ab352846d5783438a07` (`1440×900`, `77,372` B, `sha256: a120cc40b3e965f617dbcc82027c16183f3eae4b2cbfd18f10d1be2127bd3724`, `rea/after_localhost_3001.png`) — ảnh chụp REA trực tiếp xác nhận vệ tinh trái `extractedPentagon` tách thoáng khỏi đường viền xanh `(MNP)` và dải Storytelling `#F6F5F4` chuyển nhịp rõ ngay dưới Hero.
- **Tham chiếu thiết kế & chuyển động bên ngoài (kế thừa từ báo cáo trước kèm trạng thái trung thực):**
  - `https://pudding.cool/`: `VERIFIED_BY_REA` (`inspect: ev_8714031fee7b398ad902423a90e59407ebe48815b93ccb55c02e46e063c33c3f`, `shot: ev_e635a4cdcca4ce3cbc6d033c3a1a662c6e373e1cb21dcf2f9899142de7356ba8`).
  - `https://bundaumayo.top/`: `VERIFIED_BY_REA` (`inspect: ev_5b6eb948463ed30f5be2f5542635f66108fbcb2d101c815a179ceb7d0bf24975`, `shot: ev_5f45bbd14e9e47d4ff6945b64a17f3794b65791a799296c9aa73c9a9ae4cd730`).
  - `https://www.lusion.co/`: `VERIFIED_BY_REA` (`inspect: ev_d24f6a38ad425e13c6a53d89a18acbd0deabd11f745ea624494ac702024f8a37`, `shot: ev_1f28362dcf9cbe7d01b7728c2aaf437f732aa49e41ac75a88390c54c6bcb0ced`).
  - `https://rive.app/`: `VERIFIED_BY_REA` (`shot: ev_d8b185318f6b048b5fb7077dcc4a2c569b53b550a52fc8e2209862c33eac2af4`).
  - `https://www.figma.com/`: `VERIFIED_BY_REA` (`inspect: ev_e8740f5632074b6947f1429a0529aeab38cea167a2a59df59e78517d026c1cb1`).
  - `https://tympanus.net/codrops/hub/`: `NOT_VERIFIED` (chặn chống bot Cloudflare HTTP `403`, dừng kiểm tra theo đúng quy tắc an toàn).

---

## 9. Video ghi lại Storytelling đủ 4 chặng & Cuộn ngược

| Trạng thái | File Video `.webm` | Dung lượng | Keyframes trích xuất | Xác nhận trực quan |
| :--- | :--- | :---: | :--- | :--- |
| BEFORE | `videos/before/01_before_storytelling_4stages_1440x900.webm` | `587,620` B | — | Lộ hộp xám, Chặng 1 vỡ cột thiếu đáy trên, `>>` vector, hình thật nhỏ |
| AFTER | `videos/after/01_after_storytelling_4stages_fwd_rev_1440x900.webm` | `548,330` B | `keyframes/kf_after_story_s4.png` (`80,413` B), `keyframes/kf_after_story_rev_s1.png` (`61,155` B) | Đủ 4 chặng xuôi `[0,1,2,3]` và cuộn ngược `[2,1,0]`: Chặng 1 đủ lăng trụ + halo `M,N,P`; Chặng 4 hiện thẻ `Hình thật thiết diện` nổi bật; cuộn ngược về Chặng 1 sạch không sót nét |

---

## 10. Video ghi lại Interactive Demo cho đủ cả 2 mô hình

| Trạng thái | File Video `.webm` | Dung lượng | Keyframes trích xuất | Xác nhận trực quan |
| :--- | :--- | :---: | :--- | :--- |
| BEFORE | `videos/before/02_before_demo_pyramid_and_cube_1440x900.webm` | `1,214,706` B | — | Lập phương góc mặc định bị sượt ~9°, hộp bọc cột phải dày |
| AFTER (Desktop) | `videos/after/02_after_demo_pyramid_and_cube_1440x900.webm` | `1,131,408` B | `keyframes/kf_after_demo_pyr_orbit.png` (`112,594` B), `keyframes/kf_after_demo_cube_default.png` (`134,055` B) | Hình chóp `S.ABCD` kéo xoay/đặt lại góc nhìn mượt + tên mô hình rõ; chuyển sang Lập phương hiện ngay lục giác đều `MNEPFQ` cân đối chính diện |
| AFTER (Mobile) | `videos/after/03_after_mobile_story_and_demo_390x844.webm` | `624,503` B | — | Kiểm chứng trình tự cuộn Storytelling và Demo trên khung `390×844` kèm vuốt dọc không khóa scroll |

---

## 11. Các phần thất bại, bị bỏ qua hoặc chưa kiểm chứng được

- **Vitest đầy đủ sau mọi sửa đổi:** `npx vitest run --testTimeout=20000` đạt **`191 / 191` file (`2,250 / 2,250` tests PASSED, `0` fail, `0` skip)** (`132.63s`); `npx tsc -b` exit `0`; `npx vite build` exit `0` (`127` modules).
- **Trạng thái `reducedMotionCheck.closingBeat` trong `verify-v17-acceptance-after.mjs`:** Giá trị trong `after_acceptance_metrics.json` ghi `null` vì dòng `319` của script kiểm tra nhầm thuộc tính `data-cta-beat` thay vì `data-closing-beat` trong DOM thực tế. Bù lại, kịch bản `capture-closing-settled.mjs` đã xác minh trực tiếp `data-closing-beat === "exploration-settled"` và `closingSettledIdleRaf === 0` trên cả 8 viewport, đồng thời `landing-cta-motion.test.tsx` kiểm tra trạng thái lắng đọng của `LandingClosingScene3D` dưới `prefers-reduced-motion`.
- **Chưa kiểm chứng trên phần cứng thật (`NOT_PHYSICAL_MOBILE`):** Toàn bộ kiểm chứng mobile (`320×568`, `360×800`, `390×844`, `768×1024`) và WebGL trong phiên này chạy trên **Chromium + SwiftShader ANGLE** với giả lập cảm ứng (`hasTouch: true`); trải nghiệm vuốt tay thật và GPU phần cứng trên điện thoại thật chưa được đo trực tiếp.
- **Tham chiếu `tympanus.net/codrops/hub/` (`NOT_VERIFIED`):** Bị chặn bởi thử thách chống bot HTTP `403`, không thể lấy bằng chứng trực tiếp.
- **`inspect.mjs` `[few-pictures]` / `[no-footage]`:** Công cụ tự động chấm `FAIL` cho `[few-pictures]` trên trang kỹ thuật 3D vì không tính `<canvas>` WebGL hay `<svg>` là ảnh bitmap `<img>`.

---

## 12. Trạng thái chạy thực tế trên cổng `3001`

- **Tiến trình `localhost:3001` (`PID 16060`, `::1:3001`):** Được bảo toàn liên tục trong suốt toàn bộ phiên (chưa từng kill, restart hay thay đổi tiến trình).
- **Kết quả kiểm tra live:** Tải thành công `http://[::1]:3001/gioi-thieu?preview=v1.4` qua Playwright và REA MCP (`0` lỗi console, `2/2` canvas WebGL khởi tạo bình thường, fallback SVG `?no_webgl=1` hiển thị `0` canvas, `WEBGL_lose_context` mất/khôi phục context thành công `restoredHostActive: true`). Các tuyến `/`, `/gioi-thieu` và `/app` trả trạng thái khỏe và không bị ảnh hưởng.

---

## 13. Việc còn lại (nếu có) ở Hero, Closing CTA hoặc Footer

- **Đã xử lý xong các điểm chốt ưu tiên ở Wave này:** tách khoảng hở vệ tinh trái Hero khỏi viền `(MNP)`, khôi phục nền `--axo-sp-paper` `#F6F5F4` cho Closing CTA & Footer kèm mặt sứ trắng `0xffffff` giúp khối lục giác nổi rõ hơn.
- **Tùy chọn mở rộng cho vòng Owner review sau (không chặn nghiệm thu V1.7 hiện tại):** cân nhắc thay viền mảnh của nút phụ `.axo-v14-btn-secondary` trên mobile (`390px`) thành nền đặc `--axo-sp-surface` nếu muốn triệt tiêu cảnh báo `[outlined-box] (1)` của `inspect.mjs`, và kiểm thử bổ sung trực tiếp trên điện thoại vật lý (iOS Safari / Android Chrome) khi Owner duyệt xong giao diện.

---

## 14. Danh sách file phiên bản cũ (V1.2.2) sẽ xem xét dọn sau khi có phê duyệt của Owner

**Không xóa bất kỳ tệp nào dưới đây ở lượt này** (tất cả vẫn phục vụ tuyến production `/` và `/gioi-thieu`):

- [LandingHeroSculpture3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroSculpture3D.tsx)
- [LandingClosingSculpture.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingClosingSculpture.tsx)
- [LandingStorytelling.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingStorytelling.tsx)
- [LandingExplainerAnimation.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingExplainerAnimation.tsx)
- [LandingIllustrationAccents.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingIllustrationAccents.tsx)
- Nhánh `presentation === "default"` trong [LandingHeader.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeader.tsx), [LandingInteractiveDemo.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingInteractiveDemo.tsx), [LandingHeroScene3D.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/landing/LandingHeroScene3D.tsx), và [LandingView.tsx](file:///D:/Documents/projects/axo-geometry-library/frontend/src/components/LandingView.tsx)

```text
OWNER_APPROVAL: PENDING_OWNER_REVIEW
PRODUCTION_DEPLOYMENT: BLOCKED
VERSION_CLEANUP: DEFERRED_UNTIL_APPROVAL
```
