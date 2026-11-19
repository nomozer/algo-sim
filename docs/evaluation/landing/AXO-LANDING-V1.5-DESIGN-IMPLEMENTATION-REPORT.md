# AXO LANDING V1.5 — BÁO CÁO NGHIÊN CỨU, THIẾT KẾ, TRIỂN KHAI & KIỂM CHỨNG ĐỘC LẬP

- **Hướng sáng tạo:** AXO Spatial Editorial — *Geometry in Motion*
- **Nhánh Git thực thi:** `feat/axo-geometry-library-verification` (Worktree `D:\Documents\projects\axo-geometry-library`)
- **Môi trường xem trước cô lập:** `http://localhost:3001/gioi-thieu?preview=v1.4` (`LandingPrototypeMode = "v14"`)
- **Tuyến Production được giữ nguyên vẹn:** `/` và `/gioi-thieu` (`"prod"`, V1.2.2) và Workspace `/app`
- **Trạng thái phê duyệt chủ dự án:** `OWNER_APPROVAL: PENDING_OWNER_REVIEW`

---

## 1. Tóm tắt điều hành (Executive Summary)

AXO Landing V1.5 khôi phục và hợp nhất toàn bộ chất lượng thẩm mỹ, độ chính xác hình học 3D và trải nghiệm cuộn kể chuyện trên tuyến xem trước cô lập `/gioi-thieu?preview=v1.4` mà không làm xáo trộn tuyến production `/` / `/gioi-thieu`, Workspace `/app`, Backend hay nhân toán học. Trọng tâm thay đổi giải quyết bốn khiếm khuyết cốt lõi được phát hiện ở V1.4: (1) Hero 3D mở góc bất đối xứng tách bạch đường cao `SA` khỏi cạnh bên `SC` và nâng độ nổi khối thiết diện `MENPF`; (2) Storytelling đặt tiêu đề phía trên hành lang cuộn, loại bỏ thanh tiến độ trùng lặp, gợi mờ lăng trụ ở Chặng 1 qua `prismBuild` và khóa điểm `Q` chặt chẽ cho tới Chặng 3–4; (3) Interactive Demo đưa thanh 4 tab có nhãn xuống ngay dưới khung canvas 3D và bỏ khung hộp lồng ghép; (4) Closing CTA khôi phục cấu trúc **khối chóp `S.ABCD` thiết diện ngũ giác `MENPF` chiếu sáng studio sạch chữ cái** kèm 3 đối tượng hình học phụ trợ tiết chế và kịch bản hữu hạn `3600ms` tự dừng `0` idle RAF.

---

## 2. Preflight, Bảo toàn Port `3001` & Phạm vi Sở hữu (Ownership Guard)

- **Tiến trình `localhost:3001`:** Vite dev server `PID 5220` (`task-83120`) lắng nghe trên `::1:3001`, giữ nguyên hoạt động liên tục 100% trong suốt toàn phiên làm việc (0 lần kill, stop hoặc restart).
- **Cô lập phạm vi:** Mọi chỉnh sửa chỉ nằm trong `frontend/src/components/landing/`, bộ test `frontend/src/components/__tests__/landing-*`, dòng `1983` của `docs/CODE_INDEX.md` và báo cáo này dưới `docs/evaluation/landing/`. Không đụng `backend/**`, `frontend/index.html`, `package*.json`, `public/**`, Workspace components, `frontend/src/state/**`, hay `docs/EVIDENCE_INDEX.md`.
- **Tuân thủ vòng đời phiên bản:** Không tạo file `*V15*`/`*V16*` mới theo đúng ràng buộc của `landing-version-lifecycle.test.ts` và `landing-approved-ui-regression.test.tsx`.

---

## 3. Kiểm toán lịch sử V1.2 → V1.4 — Chấp nhận & Từ chối

| Hạng mục lịch sử | Quyết định của Owner / Bài học | Xử lý trong V1.5 |
| --- | --- | --- |
| Tách Production V1.2.2 khỏi Preview `?preview=v1.4` | Chấp nhận | Giữ nguyên ranh giới `LandingPrototypeMode = "prod" \| "v14"` |
| Bỏ hiển thị đáp án số học (`6√6`, `32`, `3√7`, `12√3`) trên Landing | Chấp nhận | Giữ `0` đáp án số học; chỉ giữ giả thiết gốc `a = 4` ở Storytelling |
| Dọn toàn bộ prototype V1.3 (`PrototypeA/B`, `.axo-v13-*`) | Chấp nhận | Kiểm toán xác nhận `0` selector/component V1.3 sót lại |
| Chuyển Closing CTA từ khối chóp `471baf39b` sang khối lập phương gắn nhãn `MNEPFQ` | **Bị từ chối** | Loại bỏ khối lập phương gắn nhãn; khôi phục khối chóp studio 3D kèm 3 đối tượng phụ trợ |
| Vòng lặp RAF vô hạn `9600ms` trong Closing cũ | **Bị từ chối** | Chuyển sang storyboard hữu hạn `CLOSING_STORYBOARD_MS = 3600` (`0` RAF khi idle/offscreen) |
| Điểm `Q` lộ sớm ở Chặng 2 & rãnh rail trùng lặp trong Storytelling | Hồi quy V1.4 | Khóa `Q` chặt vào `activeStageIndex >= 2` và loại bỏ `.axo-v14-story-rail` |
| Bảng phải Interactive Demo trông như hộp trong hộp (`[1][2][3][4]` + khối text dài) | Hồi quy V1.4 | Chuyển thành tab có nhãn ngay dưới canvas 3D và dẫn hướng mở không viền |

---

## 4. Nghiên cứu trực tiếp qua REA MCP (CDP `127.0.0.1:9236`)

Toàn bộ nguồn tham chiếu được mở bằng Chromium thực với SwiftShader WebGL và quan sát thụ động qua `rea:list_browser_targets`, `rea:inspect_web_page` và `rea:capture_web_screenshot`:

| Nguồn | Trạng thái | DOM / Canvas / SVG | `evidence_id` (Inspection) | Ghi chú học hỏi |
| --- | --- | --- | --- | --- |
| `https://bundaumayo.top/` | `VERIFIED_VIA_REA_MCP` | 1856 / 0 / 19 | `ev_39e63319670f821ea847f74c25a723f05c0b373c672bbb4c6f6499cdb580a2ab` | Nét vòng tròn vẽ tay bao chữ tự nhiên và phân tầng cụm 3D chính–phụ thoáng |
| `https://www.notion.com/` | `VERIFIED_VIA_REA_MCP` | 1150 / 0 / 27 | `ev_44ca0f72d13e3314fbf4aaab9501b5594745fbe413828ddae636ced1a3624954` | Typography editorial tương phản cao, 1 điểm nhấn tiêu điểm, sản phẩm nằm giữa |
| `https://www.figma.com/` | `VERIFIED_VIA_REA_MCP` | 1922 / 0 / 66 | `ev_672e915f906ecd71f0d0c9f9e865bbd01356069481adc675808515d7b8a8da3e` | Nhịp section luân phiên sáng/trung tính không lạm dụng khung viền |
| `https://rive.app/` | `VERIFIED_VIA_REA_MCP` | 4080 / 31 / 42 | `ev_2d1b7b704cfc509e5a3a605fff9a114746177219b06de106da9be2ddc1cc7112` | Thanh chọn chuyển trạng thái gọn gàng gắn trực tiếp với sân khấu tương tác |
| `https://pudding.cool/` | `VERIFIED_VIA_REA_MCP` | 1554 / 0 / 7 | `ev_d7e1e75f191e4e36454bb972b8509af388e3b7e7545fb48d4e93c7220bef3496` | Scrollytelling giữ chặt nhịp văn xuôi song hành với đồ họa thay đổi theo cuộn |
| `https://lusion.co/` | `VERIFIED_VIA_REA_MCP` | 3054 / 3 / 41 | `ev_1813f1df73be034db48c5fc855556356567594b6acb87b91bf4f61dd36c9e73a` | Kỷ luật chuyển động mượt mà với trọng tâm vật thể 3D duy nhất trong tầm mắt |
| `https://ciechanow.ski/` | `VERIFIED_VIA_REA_MCP` | 6495 / 120 / 0 | `ev_01239e20bef0fa3fd7194f4ae2bcf5bee0ebe34f37da477396ef7328e558b690` | Giải thích hình học không gian/cơ học từng bước tách lớp rõ ràng, không chữ thừa |
| `https://mathigon.org/` | `VERIFIED_VIA_REA_MCP` | 1850 / 0 / 42 | `ev_4608b85ca9c7348cfc1634a7818a58d3e7c87f3440ac7be1fa157f817f56df68` | Hình khối đa diện màu chuẩn trực quan, không biến trang giới thiệu thành bài giải |
| `https://spline.design/` | `VERIFIED_VIA_REA_MCP` | 2072 / 4 / 148 | `ev_5d81fb2e9e4d952da086a4b010908005121f9d0c13028a4a8589077759c60f4f` | Chú thích hình học gắn ngay trong tiêu đề lớn + tương phản bề mặt sạch |
| `https://tympanus.net/codrops/` | `NOT_VERIFIED` | N/A | N/A | Bị cổng Cloudflare (`Just a moment...`) chặn; tuân thủ chính sách không vượt anti-bot |
| `http://localhost:3001/gioi-thieu?preview=v1.4` (Before) | `VERIFIED_VIA_REA_MCP` | 492 / 1 / 11 | `ev_f316b1e0834578869f59da7956096f5d2b05d1bcc7fc1ef4c09bfba747c89971` | Screenshot SHA-256 `b02327cd...5461` (`70752` bytes) |
| `http://localhost:3001/gioi-thieu?preview=v1.4` (After V1.5) | `VERIFIED_VIA_REA_MCP` | 412 / 2 / 11 | `ev_ff1877904c5f7a28c3150225db6bd6181b9b60d48ac45585fed82aee49297e70` | Screenshot SHA-256 `3f497d51...e3f8` (`87309` bytes, `ev_71a0dac7...c06a`) |

---

## 5. Tổng hợp Meta Astryx & `design-taste-frontend` / `ui-ux-pro-max`

- **Meta Astryx:** Tách rạch ròi token chuyển động/nổi khối dùng lại toàn cục (`--axo-v14-ease-out`, `--axo-v14-t-fast`, `--axo-v14-t-med`), đồng bộ hóa phân cấp thị giác sáng–tối không tạo hộp viền thừa, tách trạng thái `:disabled` tường minh và kiểm chứng tự động kết hợp đọc ảnh thật.
- **`ui-ux-pro-max` & `design-taste-frontend` (`draw.mjs` hướng `split-stage`):** Đưa page về thang cỡ chữ tinh gọn (`14 / 16 / 18 / 20 / 22 / 40 / 51 px`, xóa bỏ cảnh báo `[size-count]` 11 cỡ chữ ở bản Before), đạt tỷ lệ phông `Inter 100%`, không nhảy dòng cô lập và không hộp 1px lồng trong Demo.

---

## 6. Định hướng sáng tạo: AXO Spatial Editorial — Geometry in Motion

Một ngôn ngữ trình bày thống nhất xuyên suốt cả trang: nền `#ffffff` (`--canvas`) xen kẽ `#f6f5f4` (`--axo-sp-paper`), nhấn hình học xanh lam `--primary` (`#0075de`) cho trục/mặt phẳng cắt và cam đất `--accent-orange` (`#dd5b00`) cho đa giác thiết diện — kết nối từ nét vẽ vòng tròn/gạch chân/mặt cắt trong tiêu đề tới các khối 3D studio.

---

## 7. Hệ thống Token, Trạng thái & Thang chữ (Pha B — `landing.css`)

- Bổ sung `--axo-v14-ease-out`, `--axo-v14-t-fast`, `--axo-v14-t-med`, `--axo-v14-shadow-cta-hover`, `--axo-v14-shadow-stage` dưới `#view-landing.axo-sp-root`.
- Chuẩn hóa `.axo-v14-btn:disabled` (nền `--hairline`, chữ `--ink-muted`, xóa bỏ chỉ phụ thuộc opacity), `.axo-v14-btn-secondary` (nền điền mềm không viền 1px) và `.axo-v14-root .axo-sp-mobile-toggle`.
- Dọn toàn bộ hex literal (0 vi phạm trong `landing-design-system.test.tsx`).

---

## 8. Hero Typography & Điêu khắc 3D + 3 Đối tượng phụ trợ (Pha C.1–C.2)

- `AnnotatedHeading.tsx`: tinh chỉnh vòng tròn `circle` (`viewBox="0 0 368 168"`) thoáng dấu chữ tiếng Việt; bọc `"hình dung hơn."` trong `.axo-v14-hero-phrase-keep` (`white-space: nowrap`) để chữ `"hơn."` không bị rớt dòng cô lập ở `360px`–`390px`.
- `LandingHeroV14.tsx`: chuyển góc camera bất đối xứng `(11.6, 6.3, -7.8)` tách hẳn đường cao `SA` khỏi `SC`, nâng `lowerMat` `opacity: 0.78`, `HERO_SECTION_FILL_OPACITY = 0.5`, đồng bộ ánh sáng studio 3 điểm và bổ sung 3 đối tượng phụ trợ tiết chế (đoạn kéo dài `NP`, cung phương vị đáy, hình thật ngũ giác `MENPF` đẳng cự góc cao + 2 tia chiếu mờ) kèm hoàn chỉnh đường cạnh bên fallback SVG `?no_webgl=1`.

---

## 9. Khôi phục Closing CTA Khối chóp 3D Studio + 3 Phụ trợ (Pha C.3)

- `LandingClosingScene3D.tsx`: khôi phục khối chóp `S.ABCD` + mặt phẳng `(MNP)` + ngũ giác thiết diện `MENPF` (`lowerFrustumFaceCount = 5`, `upperCapFaceCount = 5`, dư phẳng `< 1e-6`, dư trung điểm `< 1e-6`), **0 thẻ chữ cái SGK trên mô hình**.
- Bổ sung 3 đối tượng phụ trợ tiết chế (`companionCount = 3`): hình thật `MENPF` nhỏ phía trên + tia chiếu, bát diện khung dây nhỏ, cung phương vị + vạch `NP` đáy.
- Chạy kịch bản 4 nhịp hữu hạn `CLOSING_STORYBOARD_MS = 3600` (`pyramid-solid` → `cutting-plane` → `intersection-trace` → `pentagon-settled`), `CLOSING_SECTION_FILL_OPACITY = 0.56`, tạm dừng khi cuộn khỏi vùng nhìn hoặc tab ẩn, tự dừng `0` RAF sau khi ổn định, dọn sạch GPU khi unmount và hỗ trợ fallback SVG `?no_webgl=1` + `prefers-reduced-motion`.
- `LandingClosingV14.tsx` + `LandingHeroV14.tsx`: kiểm tra `window.matchMedia("(prefers-reduced-motion: reduce)")` trước khi `scrollIntoView`.

---

## 10. Kể chuyện cuộn trang (Pha D — `LandingStorytellingV14.tsx`)

- Đặt `.axo-v14-story-header` phía trên `.axo-v14-story-runway`, bỏ thanh `.axo-v14-story-rail` trùng lặp bên cạnh khung chữ, tăng `STORY_SVG_H = 520` (`cy = 236`, `scale = 51`) và tối ưu `.axo-v14-story-sticky` (`min-height: 0; top: 76px`) để không bao giờ bị cắt đáy SVG/readout.
- Thêm `prismBuild` (`0.18` ở Chặng 1 → `1` từ Chặng 2–4) làm nổi bật tam giác đáy `ABC` và điểm gốc ở Chặng 1 trong khi giữ `extrude = 1` & `zoom = 1` ở cả 4 chặng; tạo bóng mặt bên SVG bằng lớp CSS `.axo-v14-svg-prism-face-lit` / `-shade` (`0` hex / `0` `var(--` trong TSX).
- Khóa điểm `Q` nghiêm ngặt: chỉ hiện khi `activeStageIndex >= 2 && (parallelCue > 0.25 || traceProgress > 0.56)`.

**Bảng kiểm chứng 13 điểm cuộn xuôi & ngược trên `LandingStorytellingV14` (`1440×900`):**

| Target Frac | Stage Index | Progress Thực tế | Chương đang hiện | Hiển thị `Q` | Thanh tiến độ UI |
| --- | --- | --- | --- | --- | --- |
| `0.00` (xuôi) | `0` | `0.000` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |
| `0.12` (xuôi) | `0` | `0.071` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |
| `0.25` (xuôi) | `0` | `0.201` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |
| `0.38` (xuôi) | `1` | `0.331` | `1` | `false` | Chặng 2 / 4 · Dựng không gian |
| `0.50` (xuôi) | `1` | `0.451` | `1` | `false` | Chặng 2 / 4 · Dựng không gian |
| `0.65` (xuôi) | `2` | `0.601` | `1` | `true` | Chặng 3 / 4 · Xác lập quan hệ |
| `0.75` (xuôi) | `2` | `0.701` | `1` | `true` | Chặng 3 / 4 · Xác lập quan hệ |
| `0.88` (xuôi) | `3` | `0.831` | `1` | `true` | Chặng 4 / 4 · Kết quả |
| `1.00` (xuôi) | `3` | `0.951` | `1` | `true` | Chặng 4 / 4 · Kết quả |
| `0.65` (ngược) | `2` | `0.601` | `1` | `true` | Chặng 3 / 4 · Xác lập quan hệ |
| `0.38` (ngược) | `1` | `0.331` | `1` | `false` | Chặng 2 / 4 · Dựng không gian |
| `0.12` (ngược) | `0` | `0.071` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |
| `0.00` (ngược) | `0` | `0.000` | `1` | `false` | Chặng 1 / 4 · Từ đề bài |

---

## 11. Tinh giản Khu Trải nghiệm 3D (`LandingInteractiveDemo.tsx`, Pha E)

- Giữ nguyên 100% `presentation === "default"` cho Production.
- Trong `presentation === "v14"`: chuyển 4 tab có nhãn `v14ShortTab` (`1. Khối chóp`..`4. Thiết diện` / `1. Lập phương`..`4. Lục giác đều`) xuống ngay bên dưới khung 3D, đặt gợi ý xoay & nút `#btn-landing-demo-reset` gọn ở toolbar trên canvas, gỡ bỏ hộp nền trắng lồng ở cột phải và dọn stack `Dữ kiện gốc` / `Kéo để xoay...`, thay nút chính sang viên thuốc kích thước tự nhiên kèm SVG mũi tên chuẩn (`ui-hygiene.test.ts` clean).

---

## 12. Chân trang & Kiểm toán CSS dư thừa (Pha F)

- `.axo-v14-footer`: chuẩn hóa phân cấp chữ `0.875rem` trên nền `--canvas` nối nhịp mềm sau `--axo-sp-paper`.
- Đã quét toàn bộ 108 selector `.axo-v14-*` trong `landing.css`: `0` selector chết không sử dụng (9 chuỗi biến động tương ứng template `axo-v14-anno-${variant}` của `AnnotatedHeading.tsx`).

---

## 13. Chính xác toán học & Trung thực sản phẩm

- Mọi phép cắt mặt phẳng `S.ABCD` (`x + y + 2z = 6`), `ABC.A′B′C′` (`MNPQ` hình thang cân), `ABCD.A′B′C′D′` (`MNEPFQ` lục giác đều) đều giữ sai số phẳng `< 1e-6` và qua toàn bộ test hình học.
- `landing-product-integrity.test.tsx` xác nhận `0` chuỗi đáp án số học bị lộ trước trên toàn trang V1.5 preview.

---

## 14. Ma trận đa khung hình (Responsive Matrix — 9 Viewports)

| Viewport | `scrollWidth - innerWidth` (`overflowX`) | `scrollHeight` | `h1` (`fontSize`) | Hero Beat | Lỗi JS Runtime |
| --- | --- | --- | --- | --- | --- |
| `1920×1080` | `0` | `5229` | `51.2px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |
| `1440×900` | `0` | `4807` | `51.12px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |
| `1280×800` | `0` | `4538` | `45.44px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |
| `1024×768` | `0` | `4293` | `36.352px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |
| `820×1180` | `0` | `5372` | `34.4px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |
| `768×1024` | `0` | `5031` | `34.4px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |
| `430×932` | `0` | `4908` | `32.68px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |
| `390×844` | `0` | `4814` | `30.72px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |
| `360×800` | `0` | `4791` | `30.72px` | `section-settled` | `0` (`1` HTTP 500 `/api/auth/me` do backend offline) |

---

## 15. Hiệu năng, Ngân sách WebGL & Khả năng truy cập

- **Ngân sách WebGL trên production bundle (`vite preview` port `4179`):** `webglContextCreations = 3`, `canvasDomCount = 3` (1 Hero + 1 Interactive Demo + 1 Closing CTA); trên dev server `StrictMode` tạm tạo `5` lần trước khi cleanup về `3` `<canvas>` trong DOM. `#cach-hoat-dong` dùng `0` WebGL canvas.
- **Vòng lặp nghỉ:** `rafTicksDuringIdle1s = 0` sau khi Hero và Closing CTA kết thúc kịch bản dựng hình.
- **`prefers-reduced-motion: reduce` + `?no_webgl=1`:** Hero SVG fallback (`heroFallbackSvg = true`) và Closing SVG fallback (`closingFallbackSvg = true`, `data-cta-visual="svg-fallback"`, `data-closing-beat="pentagon-settled"`) hiển thị đầy đủ hình chóp và thiết diện không cần WebGL.

---

## 16. Kết quả các cổng kiểm tra tự động (Quality Gates)

| Cổng kiểm tra | Phạm vi | Kết quả |
| --- | --- | --- |
| `design-taste-frontend` `lint.mjs` | 7 file TSX V1.5 | **`0 FAIL, 0 WARN`** |
| `design-taste-frontend` `inspect.mjs` (Dev `3001`) | `1440 / 768 / 390` | **`0 FAIL, 3 WARN`** (`[dev-server]`, `[outlined-box] @390`, `[edge-text] @390`) |
| `design-taste-frontend` `inspect.mjs` (Built `dist/` `4179`) | `1440 / 768 / 390` | **`0 FAIL, 2 WARN`** (`[outlined-box] @390` 1px glass pill header / `[edge-text] @390` `16px` lề mobile); **xóa sạch `[size-count]` WARN** |
| `tsc -b && vite build` | Toàn bộ Frontend TS + bundle | **PASS** (0 lỗi TypeScript / Vite build `6.12s`) |
| `npx vitest run` (chạy đầy đủ sau sửa cuối) | Toàn bộ Workspace + Landing + Semantics | **`191 / 191` file test PASS · `2248 / 2248` test case PASS** (`0` fail, `0` skip) |
| `verify-v15-complete.mjs` (Playwright) | 9 viewports, 13 scroll stops, 5 video, Telemetry | **PASS** (`overflowX = 0`, `0` idle RAF, `qVisible` đúng Stage 3–4) |

---

## 17. Danh mục bằng chứng trực quan & Video

- **Thư mục Artifact:** `C:\Users\Bunny\.gemini\antigravity\brain\3ef24255-0976-432d-b0af-48ebb7f2067e\landing_v1_5_audit\`
- **Before / After Screenshots:** `before/*.png`, `after/hero_after_1440.png`, `after/hero_after_390.png`, `after/hero_mobile_360.png`, `after/story_stage1..4_after_1440.png`, `after/demo_pyramid_after_1440.png`, `after/demo_cube_after_1440.png`, `after/closing_after_1440.png`, `after/closing_after_390.png`, `after/footer_after_1440.png`, `after/nowebgl_after_1440.png`, `after/nowebgl_closing_1440.png`, cùng `taste_after_prod/*.jpg`.
- **REA MCP Captures:** `rea/*.png`, `rea/rea-v15-ledger.json`, `rea/after_localhost_3001.png`, `rea/rea-v15-after.json`.
- **5 Video kiểm chứng thực tế (`landing_v1_5_audit/videos/`):**
  1. `hero_v15_desktop.webm` (`756,591` bytes)
  2. `story_scroll_v15_desktop.webm` (`750,156` bytes)
  3. `demo_interaction_v15_desktop.webm` (`824,830` bytes)
  4. `closing_cta_v15_desktop.webm` (`675,470` bytes)
  5. `mobile_scroll_v15_390.webm` (`559,242` bytes)

---

## 18. Chứng minh không hồi quy (Non-Regression Proof)

Kiểm chứng Playwright trực tiếp trên `http://localhost:3001`:
- `/` → HTTP `200`, `isV14 = false`, `overflowX = 0`, `errors = []`
- `/gioi-thieu` → HTTP `200`, `isV14 = false`, `overflowX = 0`, `errors = []`
- `/app` → HTTP `200`, `isV14 = false`, `overflowX = 0`, `errors = []`

---

## 19. Danh sách tệp thay đổi (Allowlist)

- `frontend/src/components/landing/AnnotatedHeading.tsx`
- `frontend/src/components/landing/LandingHeroV14.tsx`
- `frontend/src/components/landing/LandingStorytellingV14.tsx`
- `frontend/src/components/landing/LandingInteractiveDemo.tsx`
- `frontend/src/components/landing/LandingClosingV14.tsx`
- `frontend/src/components/landing/LandingClosingScene3D.tsx`
- `frontend/src/components/landing/landing-geometry-data.ts`
- `frontend/src/components/landing/landing.css`
- `frontend/src/components/__tests__/landing-hero-visual-lifecycle.test.tsx`
- `frontend/src/components/__tests__/landing-cta-geometry.test.tsx`
- `frontend/src/components/__tests__/landing-cta-motion.test.tsx`
- `frontend/src/components/__tests__/landing-product-integrity.test.tsx`
- `frontend/src/components/__tests__/landing-scroll-storytelling.test.tsx`
- `frontend/src/components/__tests__/landing-webgl-lifecycle.test.tsx`
- `docs/CODE_INDEX.md` (chỉ dòng 1983)
- `docs/evaluation/landing/AXO-LANDING-V1.5-DESIGN-IMPLEMENTATION-REPORT.md`

---

## 20. Giới hạn còn lại & Cổng phê duyệt

- Khi kiểm thử độc lập frontend trên `3001` khi backend FastAPI chưa bật, mọi route đều phát `GET /api/auth/me` trả về HTTP `500` từ proxy Vite (không ảnh hưởng render Landing hay Workspace UI).
- `https://tympanus.net/codrops/` không thể xác minh qua REA MCP do tường anti-bot Cloudflare (`NOT_VERIFIED`).
- Trên `@390px`, `inspect.mjs` giữ lại 2 `WARN` mức nhẹ (`1px` đường viền thanh header kính nổi dùng chung `.axo-sp-nav` và khoảng lề `16px` ở mô tả Storytelling).
- Bản xem trước `/gioi-thieu?preview=v1.4` **chưa đưa lên production** và chờ đánh giá trực quan của chủ dự án:

`OWNER_APPROVAL: PENDING_OWNER_REVIEW`
