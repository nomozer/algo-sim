# AXO Landing — Design Recovery, Scroll Storytelling & Version Consolidation Report

**Ngày hoàn thành:** 2026-11-16  
**Worktree:** `D:\Documents\projects\axo-geometry-library`  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Baseline Commit SHA:** `919a06111` (`919a06111ba5ef7da47b604124e58f27d0f02686` — `docs(axo): add geometry regression and tab bar refinement report`)  
**Implementation Commit SHA:** `d04a445a6` (`d04a445a672f6ce813ef0d9815593fcafc1a576f`)  
**Report Commit SHA:** Đóng gói ngay sau implementation commit  
**Tuyến xem trước cô lập:** `http://localhost:3001/gioi-thieu?preview=v1.4` (`?preview=v1.4` / `?preview=v14`)  
**Tuyến Production mặc định:** `/` và `/gioi-thieu` (**V1.2.2** `"prod"` — bảo toàn nguyên vẹn)  
**Tình trạng triển khai thực tế:** `NOT_DEPLOYED`  
**Owner Approval:** `PENDING_OWNER_REVIEW`

> [!IMPORTANT]
> - Báo cáo này tách bạch rõ **tính ổn định kỹ thuật (`FUNCTIONALLY_STABLE`)** với **quyết định duyệt thiết kế của Chủ dự án (`PENDING_OWNER_REVIEW`)**. Không khẳng định thiết kế đã được Owner duyệt.
> - Tuyến production `/` và `/gioi-thieu` (`"prod"`, V1.2.2) và toàn bộ Workspace (`/app`, `/library`, `/workspace`) được bảo toàn nguyên vẹn.
> - Mọi tệp ngoài phạm vi Landing do phiên song song chỉnh sửa (`OWNERSHIP_BLOCKED`) được giữ nguyên tuyệt đối trong working tree.

---

## 1. Executive Summary

Đợt khôi phục chất lượng Axo Landing trên tuyến xem trước cô lập `?preview=v1.4` đã xử lý trực diện cả hai nhóm vấn đề kiến trúc và thẩm mỹ:

1. **Dọn dẹp vòng đời phiên bản (Version Consolidation):** Gỡ bỏ vĩnh viễn các bản prototype V1.3 bị từ chối (`frontend/src/components/landing/LandingPrototypeA.tsx`, `frontend/src/components/landing/LandingPrototypeB.tsx`, lớp CSS `.axo-v13-*`, truy vấn `?prototype=a|b` trong [`LandingView.tsx`](../../../frontend/src/components/LandingView.tsx)), đồng thời sửa lỗi React 18 `<StrictMode>` tại [`App.tsx`](../../../frontend/src/App.tsx) khiến URL `/gioi-thieu?preview=v1.4` bị ghi đè về `/` khi mount và làm mất trạng thái khi tải lại trang.
2. **Scroll-Driven Spatial Storytelling (0 WebGL):** Viết lại [`LandingStorytellingV14.tsx`](../../../frontend/src/components/landing/LandingStorytellingV14.tsx) từ giao diện 4 nút tab sang sân khấu dính (`position: sticky`) đồng bộ hai chiều theo cuộn trang tự nhiên (`computeStoryScrollProgress`, `interpolateStoryPose`), gác chặt kết quả `MN = 2 · PQ = 4 · MQ = NP = 2√2` và `S(MNPQ) = 3√7` chỉ mở ở Chặng 4, tối ưu bố cục mobile gắn gọn dưới Header `top: 68px` và loại bỏ thẻ text trùng lặp gây dịch chuyển bố cục (`CLS`).
3. **Hero & Demo Recovery:** Khôi phục Hero [`LandingHeroV14.tsx`](../../../frontend/src/components/landing/LandingHeroV14.tsx) theo hướng tinh giản: gỡ bỏ thẻ đáp án nổi `S(MENPF) = 6√6`, cắt tách rạch ròi nửa khối dưới đá vôi sáng ấm (`#faf7f2`, ánh sáng bù suy giảm Lambertian `1/π`) và nửa khung dây trên qua mặt phẳng `x + y + 2z = 6` tránh xuyên nét, tô thiết diện `MENPF` cam trong mờ `0.50`, kịch bản 4 nhịp `HERO_STORYBOARD_MS = 3600` tự dừng về `0` idle RAF. Tinh giản [`LandingInteractiveDemo.tsx`](../../../frontend/src/components/landing/LandingInteractiveDemo.tsx) riêng ở `presentation="v14"` (bỏ mục đóng mở đề bài gốc và chip thừa ở bước trung gian) mà không làm biến đổi chế độ `"default"` trên `/`.
4. **Final CTA & Footer Redesign (0 WebGL Analytical 3D):** Thay thế hình chóp WebGL trùng lặp (giảm `<canvas>` toàn trang `3 → 2`) bằng mô hình chiếu 3D giải tích **0 WebGL** của mặt cầu `(S)` tâm `I`, bán kính `R = 5` cắt mặt phẳng `(P): z = 3` tạo đường tròn `(H, r = 4)` và tam giác vuông `3-4-5` `IHA` tại [`LandingClosingScene3D.tsx`](../../../frontend/src/components/landing/LandingClosingScene3D.tsx). Gộp `200` phần tử `<line>` thành `6` `<path>` gom nhóm + 1 `frameState`, kéo FPS Closing mobile (`4x CPU`, `NOT_PHYSICAL_MOBILE`) từ `21.3 fps` lên **`41.1–55.1 fps`** (SwiftShader) và **`59.2 fps`** (Hardware GPU D3D11). Đơn giản hóa [`LandingClosingV14.tsx`](../../../frontend/src/components/landing/LandingClosingV14.tsx) trên mobile (chữ & CTA đặt trước 3D) và Footer (gỡ `.axo-v14-footer-trace-svg` và nút lặp `#btn-landing-footer-top`).

---

## 2. Unresolved Previous Requirements Audit

| Hạng mục tồn đọng trước đó | Nguyên nhân gốc rễ đã xác minh | Biện pháp xử lý đã thực thi | Trạng thái |
|---|---|---|---|
| Prototype V1.3 (`LandingPrototypeA/B`, `?prototype=a\|b`, `.axo-v13-*`) vẫn nằm trong mã nguồn | Chưa có bản hợp nhất chính thức sau khi V1.3 bị từ chối | Xóa `LandingPrototypeA.tsx`, `LandingPrototypeB.tsx`, `.axo-v13-*`, thu hẹp `LandingPrototypeMode = "prod" \| "v14"` | `FUNCTIONALLY_STABLE` |
| Reload trang `/gioi-thieu?preview=v1.4` rơi về `/` (`"prod"`) | `App.tsx` Effect 2 dưới React 18 `<StrictMode>` chạy với `view === "home"` trước khi re-render và gọi `pushState(..., "", "/")` | Kiểm tra `effectiveView = useAppStore.getState().view` và trả sớm khi ở đường dẫn landing trong `App.tsx` | `VERIFIED` |
| Storytelling V1.4 vẫn dùng nút tab cố định thay vì chuyển cảnh theo cuộn | Triển khai cũ dựa vào click tab 1–4; lặp lại text ghi chú bên trong từng `<li>` gây CLS mobile `0.0807` | Thay bằng sân khấu sticky đồng bộ `scrollY` hai chiều; loại bỏ text lặp trong `<li>`; hiệu chỉnh anchor mobile `0.68` | `PENDING_OWNER_REVIEW` |
| Giai đoạn 3 Storytelling giữ độ mờ cam đậm `0.52` | Luật CSS `.axo-v14-svg-section-poly { fill-opacity: 0.52; }` ghi đè thuộc tính SVG `fillOpacity` động | Gỡ `fill-opacity` mặc định khỏi `.axo-v14-svg-cutting-plane` / `.axo-v14-svg-section-poly`, khoanh riêng vào `.axo-v14-hero-fallback-svg` | `VERIFIED` |
| Hero nổi thẻ `S(MENPF) = 6√6`, cạnh xuyên mặt phẳng, khối dưới hơi tối | Chưa tách đoạn theo nửa không gian `x+y+2z=6`; ánh sáng đặt lệch sau camera (`-Z`) & PBR `1/π` chưa bù | Gỡ `.axo-v14-hero-trueshape`, tách nửa trên/dưới qua mặt phẳng cắt, ánh sáng trước phải `(14, 15, -9)` + `ambientLight = 2.1` | `PENDING_OWNER_REVIEW` |
| Final CTA dựng WebGL thứ 3 lặp lại chóp `S.ABCD`; Footer thừa SVG skyline & nút top | Thiết kế V1.4 trước dùng cùng khối chóp và thêm `.axo-v14-footer-trace-svg` | Chuyển Final CTA sang 0-WebGL mặt cầu ∩ mặt phẳng `(P): z=3`; bỏ SVG trang trí & nút về đầu trang trong Footer | `PENDING_OWNER_REVIEW` |
| Độ tương phản tag nhấn xanh & lệch lề tablet `768px` (`design-taste-frontend`) | `--axo-sp-accent` (`#0075de`) trên nền `#f6f5f4` ~`4.2:1`; `.axo-v14-hero-copy` / `.axo-v14-closing-copy` bị giới hạn `max-width` trên layout 1 cột | Chuyển `.axo-v14-demo-step-tag` & `.axo-v14-svg-label-seed` sang `var(--axo-sp-accent-active)`; đặt `max-width: 100%` dưới `1024px` / `920px` | `VERIFIED` |

---

## 3. Version & Prototype Consolidation Audit

Toàn bộ các tệp thuộc vòng đời Landing được kiểm toán và phân loại rõ:

| Tệp / Biểu tượng | Phân loại vòng đời | Vai trò hiện hành |
|---|---|---|
| [`LandingView.tsx`](../../../frontend/src/components/LandingView.tsx) (nhánh `"prod"`), [`LandingHeroSculpture3D.tsx`](../../../frontend/src/components/landing/LandingHeroSculpture3D.tsx), [`LandingStorytelling.tsx`](../../../frontend/src/components/landing/LandingStorytelling.tsx), [`LandingExplainerAnimation.tsx`](../../../frontend/src/components/landing/LandingExplainerAnimation.tsx), [`LandingClosingSculpture.tsx`](../../../frontend/src/components/landing/LandingClosingSculpture.tsx), [`LandingIllustrationAccents.tsx`](../../../frontend/src/components/landing/LandingIllustrationAccents.tsx) | `PRODUCTION_ACTIVE` | Tuyến mặc định `/` và `/gioi-thieu` (V1.2.2 `"prod"`) giữ nguyên cho người dùng công khai |
| [`LandingPreviewV14.tsx`](../../../frontend/src/components/landing/LandingPreviewV14.tsx), [`LandingHeroV14.tsx`](../../../frontend/src/components/landing/LandingHeroV14.tsx), [`LandingStorytellingV14.tsx`](../../../frontend/src/components/landing/LandingStorytellingV14.tsx), [`LandingClosingV14.tsx`](../../../frontend/src/components/landing/LandingClosingV14.tsx), [`LandingClosingScene3D.tsx`](../../../frontend/src/components/landing/LandingClosingScene3D.tsx), [`AnnotatedHeading.tsx`](../../../frontend/src/components/landing/AnnotatedHeading.tsx) | `CANDIDATE_UNDER_REVIEW` | Tuyến xem trước cô lập `?preview=v1.4` chờ Chủ dự án nghiệm thu giao diện |
| [`LandingHeader.tsx`](../../../frontend/src/components/landing/LandingHeader.tsx), [`LandingInteractiveDemo.tsx`](../../../frontend/src/components/landing/LandingInteractiveDemo.tsx), [`LandingHeroScene3D.tsx`](../../../frontend/src/components/landing/LandingHeroScene3D.tsx), [`landing-geometry-data.ts`](../../../frontend/src/components/landing/landing-geometry-data.ts), [`landing.css`](../../../frontend/src/components/landing/landing.css) | `SHARED_ACTIVE` | Dùng chung an toàn giữa `"prod"` (`presentation="default"`) và `"v14"` (`presentation="v14"`) |
| `frontend/src/components/landing/LandingPrototypeA.tsx`, `frontend/src/components/landing/LandingPrototypeB.tsx`, `.axo-v13-*`, `?prototype=a\|b` | `DEPRECATED_REMOVED` | Đã xóa sau khi kiểm chứng không còn consumer; giữ đường khôi phục qua Git commit baseline `919a06111` |
| [`docs/evaluation/landing/`](./) các báo cáo V1.2 → V1.4 trước đó | `ARCHIVED_REFERENCE` | Tài liệu đối chiếu lịch sử thiết kế và quyết định nghiệm thu qua từng vòng |
| `backend/*`, `docs/EVIDENCE_INDEX.md`, `docs/CODE_INDEX.md` dòng `4605–4646`, `docs/evaluation/geometry/runs/axo-*`, `frontend/index.html`, `frontend/package*.json`, các thay đổi Workspace/Scene3D không thuộc Landing | `OWNERSHIP_BLOCKED` | Tuyệt đối không sửa, không khôi phục, không stage |

**Lệnh Git khôi phục tệp V1.3 nếu cần đối chiếu lịch sử:**
```powershell
git checkout 919a06111 -- frontend/src/components/landing/LandingPrototypeA.tsx frontend/src/components/landing/LandingPrototypeB.tsx
```

---

## 4. Reference Website Motion & Storytelling Research (`VERIFIED_BY_REA`)

Các trang tham chiếu được thu thập thực nghiệm bằng **REA MCP** (`capture_browser_scenario` / công cụ quan sát web) trước khi thiết kế chuyển động:

| Trang tham chiếu | URL | Trạng thái | REA Evidence ID | `screenshot_sha256` | Bài học áp dụng cho Axo |
|---|---|---|---|---|---|
| **The Pudding** | `https://pudding.cool/` | `VERIFIED_BY_REA` | `ev_746e5c5db388b220472cd8c725c897610803b903a728ec90c17b3cc6c8f91d74` | `da1eb3908bb4f9b3260cc6798b4e90edc0efe25b8ee35224092cd83105b2afef` | Khoảng thở bài viết biên tập, nhịp phân đoạn thị giác rõ giữa khối văn bản và đồ họa |
| **The Pudding — Pi Scrollytelling** | `https://pudding.cool/2026/11/pi/` | `VERIFIED_BY_REA` | `ev_978001f011cc715aecfc072364283f78e8446ddd068e6dfff9d077ebc5e893d6` | `26ad4f431831bde1a1274694719dfdef67db851313d5d9f78885b015de7ccc16` | Sân khấu sticky cố định một bên để các đoạn văn cuộn qua điều khiển tiến độ `p ∈ [0, 1]` |
| **Rive** | `https://rive.app/` | `VERIFIED_BY_REA` | `ev_1df5680b7ded55d09475d351a5223502bbf71945a05dff6f999d57f9c2b71337` | `284ceb2d55baa731b7216870e7e78b8d572e137d08a85091d3c779f8a18aee70` | Phân lớp điểm nhấn tương tác vừa đủ, phản hồi pointer mượt nhưng tiết chế |
| **Figma** | `https://www.figma.com/` | `VERIFIED_BY_REA` | `ev_00bfec5d265fe2c546c16e84857f88f1d344dbe13c9a5539e39a236a54446b38` | `2e3504cf3685170f0592b288e0a3f1aaa92819a4dc895df8a1d5b01068356c5b` | Typography lớn sắc nét, hệ nút gọn đồng bộ và tránh các hộp thẻ đóng khung nặng |
| **Lusion** | `https://lusion.co/` | `VERIFIED_BY_REA` | `ev_da305007bad000f66628b2d8e858d8275bbe095c45c8a400ab0c9dc555b0e3fa` | `0e4d36e4dfef720ba435ab01aa1883c65e6ba737289a61c23befd359a7a84eb7` | Kiểu chuyển động 3D gắn chặt với chiều sâu không gian và giữ 0 rò rỉ frame khi nghỉ |

---

## 5. Scroll-Driven Storytelling Architecture

[`LandingStorytellingV14.tsx`](../../../frontend/src/components/landing/LandingStorytellingV14.tsx) thay thế hoàn toàn mô hình `role="tablist"` / nút `btn-landing-story-step-*` bằng một sân khấu dựng hình SVG chiếu 3D **0 WebGL** (`#landing-storytelling-scene`) gắn sticky song hành cùng danh sách `<ol className="axo-v14-story-chapters">`:

- **Đồng bộ hai chiều không chiếm quyền cuộn:** Không `wheel` hijacking; chỉ lắng nghe `{ passive: true }` cho `scroll` / `resize` + `requestAnimationFrame` khử nhiễu ngưỡng `0.002`.
- **Hàm ánh xạ tiến độ chuẩn hóa:** `computeStoryScrollProgress(firstCenterY, lastCenterY, viewportHeight, isCompactStack)` sử dụng ngưỡng neo `0.48 * vh` trên desktop và `0.68 * vh` trên bố cục xếp chồng compact (`<= 920px`).
- **Nội suy liên tục `interpolateStoryPose(p, reducedMotion)`:** Điều khiển mượt `yaw`, `pitch`, `zoom`, `extrude`, `planeSweep`, `parallelCue`, `traceProgress`, và `sectionFill` qua các mốc `[0, 0.34, 0.64, 0.94]`.
- **Sàng lọc thông tin theo từng chặng:** Ở Chặng 1–3, thanh readout chỉ hiển thị giả thiết / quan hệ (`M ∈ AB · N ∈ AC · P ∈ CC′`, `MN ∥ BC ⇒ PQ ∥ BC · Q ∈ BB′`). Chỉ khi `pose.activeStageIndex === 3` mới mở khóa dòng kết luận `Hình thang cân MNPQ: MN = 2 · PQ = 4 · MQ = NP = 2√2` và `S(MNPQ) = 3√7`.

**Kiểm chứng 11 kịch bản cuộn trang thực tế (`after-verification.json`):**

| Kịch bản | `progress` | `stage` | `hasButtonTabs` | Điểm `Q` | `sectionFillOpacity` | `3√7` | Trạng thái |
|---|---|---|---|---|---|---|---|
| Initial load (`Hero`) | `0.000` | `0` | `false` | `false` | `0.000` | `false` | `VERIFIED` |
| Forward Stage 1 | `0.000` | `0` | `false` | `false` | `0.000` | `false` | `VERIFIED` |
| Forward Stage 2 | `0.334` | `1` | `false` | `false` | `0.000` | `false` | `VERIFIED` |
| Forward Stage 3 | `0.667` | `2` | `false` | `true` | `0.048` (mờ đúng thiết kế) | `false` | `VERIFIED` |
| Forward Stage 4 | `1.000` | `3` | `false` | `true` | `0.480` | `true` | `VERIFIED` |
| Mid-transition 1 / 2 / 3 | `0.167 / 0.500 / 0.834` | `0 / 1 / 3` | `false` | `F / T / T` | tăng đơn điệu | `F / F / T` | `VERIFIED` |
| Reverse Scroll `4 -> 3 -> 2 -> 1` | `1 -> 0.667 -> 0.334 -> 0` | `3 -> 2 -> 1 -> 0` | `false` | đồng nhất xuôi | khớp ngược chiều | `T -> F -> F -> F` | `VERIFIED` |
| Fast jump (`End -> Start`) | `1.000 -> 0.000` | `3 -> 0` | `false` | `true -> false` | `0.48 -> 0` | `true -> false` | `VERIFIED` |
| Resize giữa chặng 3 (`1920 -> 1366`) | `0.662` | `2` | `false` | `true` | `0.045` | `false` | `VERIFIED` |
| Reload tại Chặng 3 (`?preview=v1.4`) | `0.667` | `2` | `false` | `true` | `0.048` | `false` | `VERIFIED` |
| Keyboard `PageDown` từ Chặng 1 | `0.769` | `3` | `false` | `true` | `0.212` | `true` | `VERIFIED` |

---

## 6. Hero & 3D Visual Recovery

[`LandingHeroV14.tsx`](../../../frontend/src/components/landing/LandingHeroV14.tsx) được phục hồi nhằm nâng cấp trình diễn không gian trong 1 ngữ cảnh WebGL duy nhất (`#landing-hero-sculpture`):

- **Gỡ thẻ đáp án nổi:** Loại bỏ hoàn toàn `.axo-v14-hero-trueshape` và nhãn kết quả `S(MENPF) = 6√6` khỏi vùng Hero để hình khối giữ vai trò điêu khắc biên tập sạch.
- **Tách ranh giới nửa không gian trên mặt phẳng `x + y + 2z = 6`:** Phần khối dưới giữ mặt đá vôi sáng ấm (`color: 0xfaf7f2`, `emissive: 0x38342e`, `emissiveIntensity: 0.28`) cùng cạnh trụ đậm; phần chóp trên chuyển sang nét mảnh tinh tế; giao tuyến ngũ giác `MENPF` tách lớp rõ với tô cam `HERO_SECTION_FILL_OPACITY = 0.5` để không bị cạnh sau xuyên cắt.
- **Chiếu sáng theo hướng nhìn camera:** Đặt nguồn sáng phù hợp với góc máy `[13.5, 7.6, -7.5]`: `ambientLight = 2.1` (`0xfffdf9`), `keyLight = 2.15` tại `(14, 15, -9)`, và `fillLight = 1.05` tại `(-6, 10, -12)`.
- **Chu kỳ dựng hữu hạn 4 nhịp:** `HERO_STORYBOARD_MS = 3600` (`solid-emergence` -> `seed-anchors` -> `plane-intersection` -> `section-settled`) tự dừng hoàn toàn về `0` idle RAF khi hoàn tất (`preIdleRaf: 0`, `postIdleRaf: 0` trên Desktop và `postIdleRaf: 0` sau settle trên Mobile).
- **Nhãn đỉnh chống trùng:** `6` callout đỉnh (`S, M, E, N, P, F`) qua bộ tách va chạm 2 lượt `separateLabelPositions`, cùng đường SVG fallback tĩnh khi tắt WebGL (`HeroFallbackSvg`).

---

## 7. Interactive Demo Simplification

[`LandingInteractiveDemo.tsx`](../../../frontend/src/components/landing/LandingInteractiveDemo.tsx) bổ sung prop `presentation?: "default" | "v14"`:

- Khi `presentation === "v14"` (tuyến `?preview=v1.4`): ẩn hộp đóng mở `.axo-sp-demo-problem-disclosure` (“Xem đề bài gốc”) và ẩn chip phụ `.is-stage-note` ở các bước 01–03, giữ lại bảng điều khiển súc tích gồm chuyển mẫu (`Hình chóp S.ABCD` / `Lập phương ABCD.A'B'C'D'`), thanh chọn bước `01–04`, kết quả xác thực bước cuối (`S(MENPF) = 6√6`, `V(S.ABCD) = 32` / `S(MNEPFQ) = 12√3`, `MN = 2√2`), và CTA `#btn-landing-open-showcase-3d` (“Mở trong Xưởng 3D”).
- Khi `presentation === "default"` (tuyến production `/` và `/gioi-thieu`): giữ nguyên toàn bộ cấu trúc V1.2.2 không thay đổi hành vi.

---

## 8. Final CTA & Footer Redesign

- **Cảnh 3D Giải tích 0 WebGL ([`LandingClosingScene3D.tsx`](../../../frontend/src/components/landing/LandingClosingScene3D.tsx)):** Loại bỏ hoàn toàn ngữ cảnh WebGL thứ 3 lặp lại hình chóp `S.ABCD`. Thay bằng mô hình **Mặt cầu ∩ Mặt phẳng**: mặt cầu `(S)` tâm `I(0, 0, 0)` bán kính `R = 5` bị cắt bởi mặt phẳng `(P): z = 3`, sinh đường tròn giao tuyến tâm `H(0, 0, 3)` bán kính chính xác `r = 4` và tam giác vuông `IHA` (`IH = 3`, `HA = 4`, `IA = 5`), đi kèm chu kỳ 4 pha tuần hoàn `C^0` (`CLOSING_CYCLE_DURATION_MS = 9600`).
- **Tối ưu hiệu năng SVG (`6 <path>` thay `200 <line>`):** Toàn bộ cung xích đạo (`64` đoạn), cung kinh tuyến (`64` đoạn) và đường tròn giao tuyến (`72` đoạn) được nối liên tục thành `6` chuỗi SVG `<path d="..." />` (`equatorBackPath`, `equatorFrontPath`, `meridianBackPath`, `meridianFrontPath`, `circleBackPath`, `circleFrontPath`), gom `motionState` + `tilt` vào 1 object `frameState`, giúp cắt mạnh số node cập nhật mỗi frame. Tự tạm dừng khi ra khỏi viewport (`IntersectionObserver`) hoặc ẩn tab (`visibilitychange`), và cố định ở trạng thái hoàn chỉnh dưới `prefers-reduced-motion: reduce`.
- **Thứ tự Mobile & Footer tinh giản ([`LandingClosingV14.tsx`](../../../frontend/src/components/landing/LandingClosingV14.tsx)):** Trên mobile (`<= 920px`), cột chữ & CTA xuất hiện trước hình minh họa (`responsiveCtaCopyFirst: true`); Footer bỏ họa tiết `.axo-v14-footer-trace-svg` và nút lặp `#btn-landing-footer-top`, giữ đúng 4 liên kết định vị (`Giới thiệu`, `Cách hoạt động`, `Trải nghiệm`, `Thư viện bài mẫu`).

---

## 9. Hover, Active, Focus & Touch System

Tất cả điều khiển tương tác trên [`landing.css`](../../../frontend/src/components/landing/landing.css) giữ chuẩn hình dạng viên nang `border-radius: var(--rounded-full)` (`9999px` trên nút CTA chính/phụ, `999px` trên nút Header), tương phản WCAG AA (`--axo-sp-accent-active: #005bab` trên nền nhạt), khóa hiệu ứng hover bằng `@media (hover: hover) and (pointer: fine)` và có trạng thái `:focus-visible` rõ nét.

**Kết quả telemetry kiểm tra `mouse.move -> rest -> hover -> mouseleave` trên 10 phần tử (`after-verification.json`):**

| # | Phần tử | Selector | Hoàn nguyên hoàn toàn (`revertedCleanly`) |
|---|---|---|---|
| 1 | Header Start CTA | `#btn-landing-header-start` | `true` |
| 2 | Header Library Link | `#btn-landing-header-library` | `true` |
| 3 | Top Nav Storytelling | `#nav-landing-cach-hoat-dong` | `true` |
| 4 | Hero Primary CTA | `#btn-landing-hero-start` | `true` |
| 5 | Hero Secondary CTA | `#btn-landing-hero-story` | `true` |
| 6 | Demo Sample Switch | `#btn-landing-sample-chop-thiet-dien-ba-diem` | `true` |
| 7 | Demo Step Tab 1 | `#btn-landing-demo-step-1` | `true` |
| 8 | Closing Primary CTA | `#btn-landing-final-start` | `true` |
| 9 | Closing Secondary CTA | `#btn-landing-hero-library` | `true` |
| 10 | Footer Library Link | `#btn-landing-footer-library` | `true` |

---

## 10. Geometry & Mathematical Verification

Các bất biến tọa độ được kiểm chứng trực tiếp bằng Vitest qua từng khối đại diện:

1. **Hero — Hình chóp `S.ABCD` (`LANDING_PYRAMID_SAMPLE`):**
   - Đỉnh gốc: `A(0, 0, 0)`, `B(4, 0, 0)`, `C(4, 4, 0)`, `D(0, 4, 0)`, `S(0, 0, 6)`, tâm đáy `O(2, 2, 0)`.
   - Ba điểm hạt nhân mặt cắt: `M(0, 0, 3) ∈ SA`, `N(4, 2, 0) ∈ BC`, `P(2, 4, 0) ∈ CD`; phương trình mặt phẳng cắt `x + y + 2z = 6`; hai giao điểm trên cạnh bên: `E(3, 0, 1.5) ∈ SB`, `F(0, 3, 1.5) ∈ SD`.
   - Phép chiếu trực giao `computeTrueShapeSection2D()` biến ngũ giác `M-E-N-P-F` về 2D với sai lệch bảo toàn tỷ lệ độ dài cạnh `maxDeviation < 1e-4`.
2. **Storytelling — Lăng trụ tam giác đều `ABC.A′B′C′` (`LANDING_PRISM_STORY_SPEC`):**
   - Đỉnh: `A(0, 0, 0)`, `B(4, 0, 0)`, `C(2, 2√3, 0)`, `A′(0, 0, 4)`, `B′(4, 0, 4)`, `C′(2, 2√3, 4)`; trung điểm `M(2, 0, 0) ∈ AB`, `N(1, √3, 0) ∈ AC`, `P(2, 2√3, 2) ∈ CC′`; giao tuyến song song `MN ∥ BC` cắt `BB′` tại `Q(4, 0, 2)`.
   - Hình thang cân `MNPQ`: `MN = 2`, `PQ = 4`, `MQ = NP = 2√2`, diện tích `S(MNPQ) = 3√7`.
3. **Interactive Demo — Khối lập phương `ABCD.A′B′C′D′` (`LANDING_CUBE_SAMPLE`):**
   - Thiết diện lục giác đều `MNEPFQ`, `MN = 2√2`, `S(MNEPFQ) = 12√3` xác minh qua chuyển tab `demoCheck.demoText === true`.
4. **Final CTA — Mặt cầu `(S)` cắt mặt phẳng `(P)` (`buildClosingSpatialRigData()`):**
   - `(S)` tâm `I(0, 0, 0)`, `R = 5`; mặt phẳng `(P): z = 3` (`d = |IH| = 3`), tâm đường tròn giao tuyến `H(0, 0, 3)`, bán kính `r = 4`; bốn điểm chuẩn trên `(C)`: `A(4, 0, 3)`, `B(0, 4, 3)`, `C(-4, 0, 3)`, `D(0, -4, 3)`.
   - Sai số phương trình mặt cầu `|x² + y² + z² - 25| < 1e-6`, tích vô hướng `|IH · HA| < 1e-6`, định lý Pythagoras `||IH|² + |HA|² - |IA|²| < 1e-6` (`landing-cta-geometry.test.tsx`).

---

## 11. Accessibility & Reduced Motion Audit

- **`prefers-reduced-motion: reduce` (kiểm chứng runtime Playwright):**
  - Hero dựng tức thì về nhịp cuối (`reducedHeroBeat.beat === "section-settled"`, `rafPending === 0`).
  - Final CTA cố định ở trạng thái hoàn chỉnh (`reducedHeroBeat.ctaPhase === "complete-settled"`).
  - Storytelling chuyển sang gán bước rời rạc mượt theo vị trí cuộn mà không nội suy rung khung hình (`reducedStoryStage`: `data-story-stage="3"`, `data-reduced-motion="true"`, `has3Sqrt7 === true`).
- **Hỗ trợ bàn phím & Screen Reader:**
  - `PageDown` trên desktop cuộn qua các chặng Storytelling tự nhiên (`afterKeyboardPageDown.stage === 3`, `hasButtonTabs === false`).
  - Menu mobile `#btn-landing-mobile-menu` hỗ trợ focus trap `Tab` / `Shift+Tab` và nhấn `Escape` trả focus về nút mở menu.
  - Sân khấu Final CTA mang thuộc tính `role="img"` + `aria-label` tiếng Việt chuẩn mực, SVG ẩn `aria-hidden="true"` `focusable="false"`, không có nút/bảng lồng bên trong.
- **Kết quả `design-taste-frontend` (`inspect.mjs`):** `0` lỗi tương phản màu WCAG AA (`contrast` fail = `0`), `0` tràn ngang (`horizontalOverflow = 0`), `768px` cân giữa; còn 6 cảnh báo/fail quy tắc tổng quát của công cụ biên tập ảnh (`headline-lines`, `mono` trên ký hiệu đỉnh hình học `A/B/C/D`, `shadow` trên chip mẫu đang chọn dùng chung Design System, `hairline` ranh giới các chặng cuộn, `few-pictures` vì trang chủ hình học dùng canvas WebGL + vector thay ảnh chụp stock) đều là đặc thù chủ đích của sản phẩm hình học không gian Axo.

---

## 12. Before/After Performance & WebGL Lifecycle Benchmarks

Nguồn đối chiếu: [`before-benchmark.json`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_design_recovery/before/before-benchmark.json) so với [`after-verification.json`](file:///C:/Users/Bunny/.gemini/antigravity/brain/3ef24255-0976-432d-b0af-48ebb7f2067e/landing_design_recovery/after/after-verification.json) trên máy phục vụ cục bộ Vite dev (`http://localhost:3001/gioi-thieu?preview=v1.4`). Mọi cấu hình giả lập di động `390x844` kèm `4x CPU` throttling được gắn nhãn trung thực **`NOT_PHYSICAL_MOBILE`**.

| Cấu hình đo | Nhãn giả lập | `<canvas>` DOM (Before → After) | WebGL Active / Lost (Before → After) | Closing FPS / P95 After | CLS (Before → After) | Offscreen Settled RAF | Ghi chú |
|---|---|---|---|---|---|---|---|
| `swiftshader_desktop_1920x1080` | `SwiftShader` (`1x CPU`) | `3 → 2` | `6/0 → 3/0` | `60.0 fps` / `16.7 ms` | `0 → 0` | `0` | Closing 0 WebGL, Story `60 fps` |
| `swiftshader_mobile_390x844_4x_cpu` | `NOT_PHYSICAL_MOBILE` (`4x CPU`) | `3 → 2` | `6/0 → 3/0` | `41.1 fps` / `50.0 ms` (chạy trước đạt `55.1 fps`) | `0 → 0.0134` | `0` | Hero `60 fps`, Story `60 fps`, Demo `60 fps` |
| `hardware_gpu_desktop_1920x1080` | `Hardware GPU D3D11` (`1x CPU`) | `3 → 2` | `6/0 → 3/0` | `60.0 fps` / `16.8 ms` | `0 → 0` | `0` | Toàn bộ 4 phân đoạn giữ `60 fps` |
| `hardware_gpu_mobile_390x844_4x_cpu` | `NOT_PHYSICAL_MOBILE` (`4x CPU`) | `3 → 2` | `6/0 → 3/0` | `59.2 fps` / `16.7 ms` | `0.0134` | `0` | `LCP 1976 ms`, cải thiện từ `21.3 fps` bản chưa gộp `<path>` |

- **Ghi chú kỹ thuật:** `Hero` và `Demo` đóng góp `2` phần tử `<canvas>` trên DOM (`rawCalls: 3` là tổng lượt khởi tạo `getContext` tính cả probe phát hiện WebGL khả dụng; `lost = 0`); `LandingClosingScene3D` dùng **`0` WebGL context** (`ctaCanvases: 0`). Kết thúc kiểm tra: `consoleErrors: 0`, `pageErrors: 0`.

---

## 13. Responsive Audit Across 8 Viewports

Tất cả 8 kích thước màn hình từ `1920px` đến `320px` vượt qua kiểm tra `scrollWidth <= innerWidth`, CTA đầu tiên nằm dưới Header cố định và lọt trọn màn hình đầu tiên, cùng thứ tự cột CTA cuối trang hợp lệ (`ctaOrderCopyFirst: true`):

| Viewport | `overflowX` | Header (`px`) | CTA đầu lọt màn hình đầu | Thứ tự CTA cuối hợp lệ |
|---|---|---|---|---|
| `1920x1080` | `false` | `72` | `true` | `true` |
| `1440x900` | `false` | `72` | `true` | `true` |
| `1366x768` | `false` | `72` | `true` | `true` |
| `1024x768` | `false` | `72` | `true` | `true` |
| `768x1024` | `false` | `68` | `true` | `true` |
| `390x844` | `false` | `68` | `true` | `true` |
| `360x800` | `false` | `68` | `true` | `true` |
| `320x568` | `false` | `68` | `true` | `true` |

---

## 14. Regression Audit on Production Landing & Workspace

- **Production Landing (`/`) & Workspace (`/app`):** Kiểm tra trực tiếp bằng Playwright xác nhận `/` tiếp tục nạp bản V1.2.2 `"prod"` (`prodCheck: { hasProdRoot: true, overflowX: false }`), và `/app` dựng màn hình làm việc chuẩn (`appCheck: { renderedApp: true, overflowX: false }`).
- **Biên dịch TypeScript & Build Production:**
  ```powershell
  npx tsc -b; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; npm run build
  ```
  Kết quả: **exit 0** (`5.17s`, `127 modules transformed`).
- **Toàn bộ Bộ Test Vitest Frontend:**
  ```powershell
  npx vitest run --testTimeout=15000 --maxWorkers=2
  ```
  Kết quả: **`190/190` test files passed**, **`2248/2248` tests passed** (`113.80s`), bao gồm toàn bộ các guard CSS tokens, `class-coverage.test.ts`, `transition-semantics.test.ts`, `code-index-sync.test.ts`, `ui-hygiene.test.ts`, `phase-b-views.test.tsx`, `13` file `landing-*.test.*`, và toàn bộ bộ test Workspace / Scene3D / Continuity hiện hành.

---

## 15. Visual Evidence Pack

Tất cả ảnh Before/After, video quay động và báo cáo REA MCP lưu tại thư mục artifact phiên làm việc:

- **Before Baselines:** `landing_design_recovery/before/` (`before-benchmark.json`, `desktop_hero.png`, `desktop_story.png`, `desktop_demo.png`, `desktop_closing_cta.png`, `desktop_footer.png`, `mobile_hero.png`, `mobile_story.png`, `mobile_demo.png`, `mobile_closing_cta.png`, `mobile_footer.png`) + REA `ev_510e42eca93ac3f2d8fa9a0930ae4f3cc834e5a64f761f004be9cdd80723911e` (`prod`), `ev_26fd577801989632409e73636ae4f25442a476ee8aed60f3ed4d60935831dbb1` (`?preview=v1.4` trước sửa).
- **After Refreshed Screenshots & Videos:** `landing_design_recovery/after/` (`desktop_hero_settled.png`, `desktop_story_stage_1..4.png`, `desktop_story_mid_1..3.png`, `desktop_demo_pyramid.png`, `desktop_demo_cube.png`, `desktop_closing_cta.png`, `desktop_footer.png`, `mobile_hero_390.png`, `mobile_menu_open.png`, `mobile_story_390.png`, `mobile_closing_cta_390.png`, `mobile_footer_390.png`, `hover_primary_cta.png`, `hover_secondary_cta.png`, cùng 6 video `.webm` trong `videos/`: `hero_motion_cycle.webm`, `storytelling_scroll_1_to_4.webm`, `storytelling_reverse_4_to_1.webm`, `cta_motion_cycle.webm`, `hover_mouse_leave.webm`, `mobile_scrolling_390x844.webm`).
- **Visual Audit & Final Post-Polish REA Capture:**
  - `landing_design_recovery/taste_inspect/tablet-fold.jpg`, `desktop-fold.jpg`, `mobile-fold.jpg`, `report.json`.
  - Final REA MCP capture (`http://localhost:3001/gioi-thieu?preview=v1.4` sau chỉnh sửa cuối): `evidence_id = ev_ae6f8205abfef39456cf2d1410b4657ed8074322b020d89850449f40474402d9`, `screenshot_sha256 = d069a311864e188d1e2fc9b7d1f488992657314e5174ab063ec05692d4462ed7`.

---

## 16. Files Changed / Removed

Tất cả `24` tệp thuộc phạm vi nhiệm vụ (23 tệp code/test/index + báo cáo này):

| # | Tệp | Hành động | Tóm tắt thay đổi |
|---|---|---|---|
| 1 | [`frontend/src/App.tsx`](../../../frontend/src/App.tsx) | Sửa | Tránh `<StrictMode>` re-mount ghi đè `/gioi-thieu?preview=v1.4` về `/` qua `effectiveView` |
| 2 | [`frontend/src/components/LandingView.tsx`](../../../frontend/src/components/LandingView.tsx) | Sửa | Bỏ import/nhánh `?prototype=a\|b`, giữ `"prod"` mặc định + `"v14"` cô lập |
| 3 | [`frontend/src/components/landing/LandingHeroV14.tsx`](../../../frontend/src/components/landing/LandingHeroV14.tsx) | Sửa | Bỏ card `6√6`, tách cạnh qua `x+y+2z=6`, `HERO_SECTION_FILL_OPACITY = 0.5`, sáng đá vôi `1/π`, 4 nhịp 3.6s -> 0 RAF |
| 4 | [`frontend/src/components/landing/LandingStorytellingV14.tsx`](../../../frontend/src/components/landing/LandingStorytellingV14.tsx) | Sửa | Sân khấu sticky cuộn liên tục 4 chặng (0 WebGL), gác `3√7` đúng Chặng 4, tối ưu mobile không lặp text |
| 5 | [`frontend/src/components/landing/LandingInteractiveDemo.tsx`](../../../frontend/src/components/landing/LandingInteractiveDemo.tsx) | Sửa | Tinh giản `presentation="v14"` bỏ disclosure và chip phụ, bảo toàn `"default"` |
| 6 | [`frontend/src/components/landing/LandingClosingScene3D.tsx`](../../../frontend/src/components/landing/LandingClosingScene3D.tsx) | Sửa | Chuyển sang 0-WebGL Mặt cầu `R=5` ∩ Mặt phẳng `z=3`, gộp `6` SVG `<path>` + 1 `frameState` |
| 7 | [`frontend/src/components/landing/LandingClosingV14.tsx`](../../../frontend/src/components/landing/LandingClosingV14.tsx) | Sửa | Gỡ `.axo-v14-footer-trace-svg` và nút lặp `#btn-landing-footer-top` |
| 8 | [`frontend/src/components/landing/landing.css`](../../../frontend/src/components/landing/landing.css) | Sửa | Gỡ `.axo-v13-*`, chuẩn sticky & SVG fill, `--axo-sp-accent-active`, căn đều tablet `<= 1024px`, mobile CTA trước |
| 9 | `frontend/src/components/landing/LandingPrototypeA.tsx` | Xóa | Gỡ prototype V1.3 bị từ chối |
| 10 | `frontend/src/components/landing/LandingPrototypeB.tsx` | Xóa | Gỡ prototype V1.3 bị từ chối |
| 11–22 | 12 tệp test `frontend/src/components/__tests__/landing-*.test.*` | Tạo/Sửa | Cập nhật assertions & bổ sung `landing-version-lifecycle.test.ts`, `landing-scroll-storytelling.test.tsx` |
| 23 | [`docs/CODE_INDEX.md`](../../CODE_INDEX.md) | Sửa | Đồng bộ dòng 1983 mô tả Landing + các tệp test mới |
| 24 | [`docs/evaluation/landing/AXO-LANDING-DESIGN-RECOVERY-REPORT.md`](./AXO-LANDING-DESIGN-RECOVERY-REPORT.md) | Tạo mới | Báo cáo tổng hợp 18 mục và ma trận ký duyệt Owner |

---

## 17. Known Limitations

1. **Tuyến Production chưa thay đổi mặc định:** Phiên bản mới chỉ chạy trên `?preview=v1.4` và chỉ thay thế `/` khi Chủ dự án nghiệm thu và yêu cầu cutover.
2. **Đo kiểm Mobile 4x CPU là mô phỏng:** Kết quả `390x844` ở `4x CPU` throttle được thu trên Chromium desktop (`NOT_PHYSICAL_MOBILE`); trên máy thật (iOS Safari / Android Chrome) cần kiểm tra thêm nếu triển khai staging.
3. **Các rule chung của `inspect.mjs`:** Bộ `design-taste-frontend` đánh fail các quy chuẩn blog ảnh (`few-pictures`, `no-footage`, `hairline`, `mono`, `headline-lines`, `shadow` nút pill mẫu); các phần tử này xuất phát từ bản chất minh họa toán học tương tác và token hệ thống đã quy chuẩn.
4. **Môi trường phát triển local:** Thử nghiệm chạy trên Vite dev server (`localhost:3001`, không kèm backend `/api/auth/me` nên Proxy console ghi 500 thụ động khi kiểm auth guest); production build tĩnh `vite build` đã kiểm chứng thành công tách biệt (`5.17s`).

---

## 18. Owner Visual Sign-Off Matrix

| # | Tiêu chí kiểm chứng | Trạng thái kỹ thuật | Quyết định Owner | Ghi chú bằng chứng |
|---|---|---|---|---|
| 1 | Xóa bỏ prototype V1.3 bị từ chối (`A/B`, `.axo-v13-*`) | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `landing-version-lifecycle.test.ts` (2/2), `git status` |
| 2 | Bảo toàn tuyến Production `/` & `/gioi-thieu` (V1.2.2 `"prod"`) | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `prodCheck.hasProdRoot === true`, `phase-b-views.test.tsx` |
| 3 | Tải lại `/gioi-thieu?preview=v1.4` giữ nguyên URL & trạng thái | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `afterReloadState` (`stage: 2`, `hasButtonTabs: false`) |
| 4 | Storytelling chuyển cảnh theo cuộn tự nhiên (không nút tab) | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `11` kịch bản `storyCheckpoints` + `storytelling_*.webm` |
| 5 | Gác kết quả `S(MNPQ) = 3√7` & `2√2` chỉ tại Chặng 4 | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | Chặng 1–3 `has3Sqrt7: false`; Chặng 4 `true` |
| 6 | Tỷ lệ đậm dần của thiết diện ở Chặng 3 -> Chặng 4 | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `sectionFillOpacity`: `0.048` ở Chặng 3 -> `0.480` ở Chặng 4 |
| 7 | Hero gỡ bỏ thẻ đáp án nổi `S(MENPF) = 6√6` | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `heroCheck.hasTrueShapeCard: false`, `desktop_hero_settled.png` |
| 8 | Hero tách ranh giới nét & ánh sáng nửa chóp dưới/trên | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `desktop_hero_settled.png` (`AMBIENT 2.1`, `LOWER #faf7f2`) |
| 9 | Kịch bản Hero 4 nhịp 3.6s dừng về `0` idle RAF | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `hero_motion_cycle.webm`, `preIdleRaf: 0`, `postIdleRaf: 0` |
| 10 | Interactive Demo tinh giản ở `?preview=v1.4` | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `demoCheck.hasProblemDisclosure: false`, `desktop_demo_pyramid.png` |
| 11 | Final CTA 0-WebGL (Mặt cầu ∩ Mặt phẳng `(P): z=3`) | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `ctaCanvases: 0`, `ctaVisual: analytical-3d-svg`, `desktop_closing_cta.png` |
| 12 | Tối ưu hiệu năng SVG CTA (`6 <path>`, Mobile FPS cải thiện) | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | SwiftShader `21.3 -> 41.1–55.1 fps`; Hardware GPU `59.2 fps` (`NOT_PHYSICAL_MOBILE`) |
| 13 | Mobile CTA đặt cột chữ & nút trước hình 3D | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `responsiveCtaCopyFirst: true`, `mobile_closing_cta_390.png` |
| 14 | Footer tối giản bỏ SVG horizon & nút top lặp | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `footerTraceSvg: false`, `footerTopBtn: false`, `desktop_footer.png` |
| 15 | Hệ thống nút capsule `9999px` & hover hoàn nguyên 10/10 | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `hoverAllReverted: true`, `hover_mouse_leave.webm` |
| 16 | Hỗ trợ accessibility, bàn phím & `prefers-reduced-motion` | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `reducedMotionCheck` PASS, focus trap Drawer |
| 17 | Tương thích đa màn hình `1920px` đến `320px` & Tablet `768px` | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `8/8` viewports `overflowX: false`, `tablet-fold.jpg` cân đối |
| 18 | Bộ kiểm thử tổng thể (`tsc`, `vite build`, `190/190` Vitest) | `FUNCTIONALLY_STABLE` | `PENDING_OWNER_REVIEW` | `190/190` files (`2248/2248` tests) PASS, `tsc` + `build` exit 0 |

---

**Owner Approval:** `PENDING_OWNER_REVIEW`
