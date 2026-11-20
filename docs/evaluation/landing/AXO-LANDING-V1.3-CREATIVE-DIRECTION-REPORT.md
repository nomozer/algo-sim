# AXO Landing Page V1.3 — Creative Direction, Motion Research & Prototype Evaluation Report

**Ngày hoàn thành:** 2026-11-15  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Mốc nền Pha A:** [`AXO-LANDING-V1.2.2-UX-REPORT.md`](./AXO-LANDING-V1.2.2-UX-REPORT.md) (`2cde6e6a4`)  
**Prototype Disposition:** `NOT_APPROVED_FOR_INTEGRATION` (cả Prototype A `?prototype=a` và Prototype B `?prototype=b` được thay thế định hướng bởi bản Preview V1.4 thống nhất `?preview=v1.4`; giữ nguyên mã nguồn để đối chiếu QA, không gộp vào production)  
**Owner Approval:** `NOT_APPROVED_FOR_INTEGRATION` (V1.3 đã bị vượt cấp sang V1.4)

> [!IMPORTANT]
> Cả hai prototype V1.3 (`?prototype=a` và `?prototype=b`) đang được đánh dấu **`NOT_APPROVED_FOR_INTEGRATION`** và vẫn chạy ở chế độ **cô lập hoàn toàn qua query parameter** để đối chiếu trực tiếp với bản Preview V1.4. Trang mặc định `/` và `/gioi-thieu` (không có query parameter) giữ nguyên bản **V1.2.2** không thay đổi.

---

## 1. Executive Summary (`PENDING_OWNER_REVIEW`)

Pha B (**AXO Landing V1.3**) chuyển trọng tâm trang giới thiệu `/gioi-thieu` từ dạng trình diễn thẻ kỹ thuật rời rạc sang **kể chuyện hình học không gian liên tục trên một sân khấu duy nhất (single morphing stage)**, kết hợp nghiên cứu thực nghiệm bằng **REA MCP** trên các website tham chiếu và thiết kế hai phương án prototype có khả năng vận hành độc lập:

- **Prototype A (`?prototype=a` — Vector Interactive Storytelling):** Tập trung vào độ sắc nét vector thuần SVG cho Hero (`HeroConceptASvg`, concept *Geometric Transformation*) và phần "Cách Axo hoạt động" (`ContinuousVectorStoryCanvas`), không khởi tạo thêm ngữ cảnh WebGL nào cho Hero/Story (toàn trang chỉ giữ `1` WebGL context ở phần Demo Tương tác bên dưới).
- **Prototype B (`?prototype=b` — 3D Spatial Transformation):** Tập trung vào chiều sâu không gian thực trên Three.js cho Hero (`HeroConceptB3D`, concept *Spatial Construction*) và phần "Cách Axo hoạt động" (`Continuous3DStoryStage`), áp dụng cơ chế nhường slot `#v13-demo-slot` bằng `IntersectionObserver` (`rootMargin: "260px 0px"`) để **không bao giờ vượt quá 2 WebGL context hoạt động đồng thời**, kèm SVG fallback xác định (`HeroConceptBFallbackSvg` và `Story3DFallbackSvg`) ngay từ lúc SSR/trước hydration hoặc khi mất ngữ cảnh đồ họa.

**Bảo chứng cô lập (Production Isolation Guarantee):**
- `readLandingPrototypeMode()` trong `frontend/src/components/LandingView.tsx` trả về `"prod"` cho mọi URL không mang `?prototype=a` hoặc `?prototype=b`.
- Không sửa đổi bất kỳ hành vi mặc định nào của `/`, `/gioi-thieu`, Auth, Draft Restoration, hoặc các module Workspace từ Pha A.

---

## 2. Reference Website Motion Research (REA MCP Audit)

Nghiên cứu được thực hiện bằng REA MCP (`list_browser_targets`, `inspect_web_page`, `analyze_web_bundle` — gói tổng hợp tại `landing_v1_3_audit/rea/rea-motion-summary.json`, `capturedAt: "2026-11-15T13:08:56.912Z"`):

| Website | URL | Trạng thái | REA Evidence ID | Script / Resource | Tín hiệu DOM & Asset quan sát |
|---|---|---|---|---:|---|
| **Figma** | `https://www.figma.com/` | `VERIFIED_BY_REA` | `ev_408712af95c24d3e2940d582ba2729a441a5e4db6564e85ffc8bf6338242a540` | `142` scripts / `35` resources | `svgMentions: 66`, `canvasOrWebglMentions: 0`, `videoMentions: 0`; từ khóa asset: `d3 (110)`, `motion (2)`, `rive (1)` |
| **Rive** | `https://rive.app/use-cases/websites` | `VERIFIED_BY_REA` | `ev_aa627f05de3fd100da35911a3a3fcb17a378eb9fd666e871cfd3cc9a81337e37` | `7` scripts | `svgMentions: 10`, `canvasOrWebglMentions: 0`, `videoMentions: 6`; từ khóa asset: `rive (210)`, `lottie (3)`, `d3 (3)` |
| **The Pudding** | `https://pudding.cool/` | `VERIFIED_BY_REA` | `ev_3bbfe02aa0889a379d957240e8adf65a7780a6e5fa30af1d62c274bb46e09552` | `22` scripts / `82` resources | `svgMentions: 7`, `canvasOrWebglMentions: 0`, `videoMentions: 0`; từ khóa asset: `d3 (30)` |
| **Lusion** | `https://lusion.co/` | `VERIFIED_BY_REA` | `ev_c35f1001d5e7e288fd5cbdde57d48fc9eccc768512d7f9468201504c615d4828` | `2` scripts / `10` resources | `svgMentions: 44`, `canvasOrWebglMentions: 4`, `videoMentions: 1`; từ khóa asset: `svg (7)`, `d3 (5)`, `motion (1)` |
| **Codrops** | `https://tympanus.net/codrops/` | `REA_NOT_VERIFIED` | — | — | Bị chặn bởi `HTTP 403 / Cloudflare anti-bot challenge ('Just a moment...')` ghi nhận từ `list_browser_targets`; tuân thủ quy tắc an toàn tuyệt đối không vượt CAPTCHA/anti-bot. |

---

## 3. REA MCP Findings & Runtime Lessons Applied to Axo

Từ 4 website đã xác minh bằng REA (`VERIFIED_BY_REA`), nhóm thiết kế rút ra 4 bài học kiến trúc trực tiếp áp dụng vào V1.3:

1. **Vector SVG + Video nhẹ thắng thế cho kể chuyện editorial & UI kỹ thuật (`Figma`, `The Pudding`):** Cả `figma.com` (`66` SVG, `0` WebGL canvas) lẫn `pudding.cool` (`7` SVG, `30` D3 hit) chứng minh minh họa vector sạch + chuyển trạng thái rõ ràng truyền tải cấu trúc rất nhanh mà không tốn ngân sách GPU. Đây là nền tảng cho **Prototype A (`?prototype=a`)**.
2. **State machine tương tác thay cho loop chạy vô hạn (`Rive`):** `rive.app/use-cases/websites` sử dụng cấu trúc trạng thái đóng gói (`rive: 210`, `lottie: 3`, kết hợp `video: 6`), tránh render nặng liên tục khi người dùng đã dừng đọc. Ở Axo V1.3, vòng `requestAnimationFrame` trong Hero và Storytelling tự động ngủ (`settledIdleRafCount === 0`) ngay khi hoàn tất chuyển tiếp hoặc khi ra khỏi viewport (`IntersectionObserver`) / ẩn tab (`visibilitychange`).
3. **WebGL có kiểm soát chặt chẽ về ngân sách cảnh & fallback SVG (`Lusion`):** `lusion.co` chỉ dùng `2` script và `4` tín hiệu Canvas/WebGL kết hợp `44` phần tử SVG để giữ tải nhẹ và rõ khung hình. Với **Prototype B (`?prototype=b`)**, Axo áp dụng cơ chế cấp phát có giới hạn tối đa `2` ngữ cảnh WebGL đồng thời (`HeroConceptB3D` / `Continuous3DStoryStage` / `#v13-demo-slot`) và dự phòng SVG tức thì.
4. **Ranh giới minh bạch nguồn kiểm chứng (`Codrops`):** Bất kỳ nguồn nào gặp cổng chống bot (`HTTP 403 / Cloudflare`) đều được gắn nhãn `REA_NOT_VERIFIED` và loại khỏi bằng chứng hành vi thực nghiệm.

---

## 4. Creative Direction & Visual Principles

Cả Prototype A và B tuân thủ hệ thiết kế Axo Light Mode hiện hành (`frontend/src/components/landing/landing.css`, phạm vi `.axo-v13-*`, 0 token CSS ngoại lai, 0 `#hex` hardcode sai quy chuẩn trong phần khai báo quy tắc tĩnh):

- **Không gian trắng rộng kiểu editorial:** Bề mặt `#ffffff` / `#f7f6f4`, đường viền mỏng `#e5e3de`, điểm nhấn Axo Blue `#0075de` (mặt phẳng cắt & mối quan hệ song song `MN // PQ`) và Semantic Orange `#dd5b00` (thiết diện cắt `MNPQ` và các đỉnh giao điểm).
- **Kể chuyện trên một sân khấu duy nhất:** Thay thế chuỗi card rời bằng một khối minh họa biến đổi liên tục đồng bộ với 4 chặng câu chuyện (`Bước 1` → `Bước 4`), giữ người học tập trung vào **cùng một đối tượng hình học** đang tiến hóa qua từng suy luận.
- **Nhận thức sư phạm rõ ràng (Epistemic Discipline):** Không tiết lộ độ dài và diện tích đáp án ở các bước giả thiết ban đầu; các kết quả chỉ xuất hiện ở `Bước 4 — Kết quả trực quan`.

---

## 5. Hero Redesign Concepts (Concept A vs Concept B)

| Tiêu chí | Concept A — `Geometric Transformation` (`LandingPrototypeA`) | Concept B — `Spatial Construction` (`LandingPrototypeB`) |
|---|---|---|
| **Component** | `HeroConceptASvg` | `HeroConceptB3D` + fallback `HeroConceptBFallbackSvg` |
| **Công nghệ dựng hình** | 100% Pure SVG 2.5D với phép chiếu perspective tự tính | Three.js `WebGLRenderer` (`fov = 36`, camera từ `LANDING_PYRAMID_SAMPLE.defaultCamera * 0.92`, `defaultLookAt`) + `HeroConceptBFallbackSvg` khi SSR/chưa sẵn sàng |
| **Chuyển động chủ đạo** | Biến đổi nhịp `900ms` (sweep mặt phẳng `#0075de` và hiện rõ thiết diện `#dd5b00` trên khối chóp đáy thang) + phản hồi nghiêng theo con trỏ chuột (tắt dưới `prefers-reduced-motion`) | Khối chóp cắt 3D thực (`LANDING_PYRAMID_SAMPLE.planeQuad`) tự cân bằng tư thế và xoay nhẹ theo tương tác con trỏ, ngủ RAF ngay khi đạt trạng thái nghỉ |
| **WebGL context sử dụng tại Hero** | `0` | `1` (hoặc `0` tạm thời nếu người dùng cuộn xuống vùng `#v13-demo-slot`) |

---

## 6. Prototype A Architecture (`?prototype=a`)

- **Tệp nguồn:** `frontend/src/components/landing/LandingPrototypeA.tsx`
- **Thanh xem thử có điều khiển (`#landing-v13-review-banner`):** Hiển thị nhãn trạng thái `PENDING_OWNER_REVIEW` và bộ 3 nút chuyển đổi tức thời qua `switchLandingPrototype()` (`Bản V1.2.2 hiện hành`, `Prototype A: Vector Motion`, `Prototype B: 3D Spatial`), đồng bộ sự kiện `popstate` và `axolanding:protochange`.
- **Sân khấu Storytelling `ContinuousVectorStoryCanvas`:** Chiếu hình học 3D của lăng trụ đứng `ABC.A′B′C′` lên mặt phẳng SVG `viewBox="0 0 600 430"` với tâm `cy = 216`, hệ số phóng đại `55 * vis.zoom`, ràng buộc tọa độ nhãn trong vùng an toàn `[24..576] × [24..406]` để không cắt chữ ở bất kỳ chặng nào.
- **Ngân sách tài nguyên đồ họa:** Hero và Storytelling hoàn toàn không tạo `<canvas>` WebGL. Chỉ phần Demo tương tác `LandingInteractiveDemo` bên dưới mới dùng `1` WebGL context (`WebGL active = 1 / lifetime = 1`).

---

## 7. Prototype B Architecture (`?prototype=b` & WebGL Slot Leasing `<= 2`)

- **Tệp nguồn:** `frontend/src/components/landing/LandingPrototypeB.tsx`
- **Sân khấu Hero `HeroConceptB3D`:** Khởi tạo `webglReady = false` để SSR và lần sơn đầu luôn hiển thị `HeroConceptBFallbackSvg` sạch sẽ; sau mount mới cấp phát `WebGLRenderer` nếu được cấp slot.
- **Sân khấu Storytelling `Continuous3DStoryStage`:** Dựng trực tiếp khối lăng trụ, mặt phẳng cắt `LANDING_PRISM_STORY_SPEC.planeQuad`, thiết diện `MNPQ` và các điểm neo `P, Q` gắn trực tiếp vào `prismPivot` (bảo đảm điểm `P ∈ CC′` di chuyển khớp tuyệt đối theo tiến trình dựng `extrude` ở Bước 1), khung nhìn đặt theo `radius = 12.6 / curZoom`, `lookAt(0, -0.08, -0.38)`, kết hợp lớp nhãn SVG phủ `axo-v13-3d-labels-overlay` kẹp an toàn `[24..576] × [24..406]`.
- **Cơ chế cấp phát giới hạn `<= 2` WebGL Context qua `#v13-demo-slot`:**
  - `Continuous3DStoryStage` giữ `1` slot cố định trong suốt phiên xem (khi không bị mất ngữ cảnh).
  - `#v13-demo-slot` sử dụng `IntersectionObserver({ rootMargin: "260px 0px" })` theo dõi `demoNearViewport`: khi vùng Demo tiến gần viewport, Hero nhường quyền WebGL (`webglAllowed = !demoNearViewport`) để Demo khởi tạo; khi cuộn lên lại vùng Hero, Demo hủy mount sạch sẽ và Hero nhận lại slot.
  - Kết quả đo thực tế trên Playwright: `maxSimultaneousConnectedWebgl === 2`, `lifetimeWebglCreated === 6` (khi cuộn qua lại giữa Hero và Demo), `webglContextLostCount === 0`.

---

## 8. Mathematical & Pedagogical Continuity

Cả hai prototype sử dụng chung nguồn dữ liệu hình học `LANDING_PRISM_STORY_SPEC` trong `frontend/src/components/landing/landing-geometry-data.ts`, bảo đảm đúng toán học và phân tầng sư phạm:

1. **Kiểm chứng toán học tọa độ (`landing-storytelling-geometry.test.tsx`):**
   - `MN = 2`, `PQ = 4`, `MQ = NP = 2√2`
   - `MN ∥ PQ` (tích có hướng của hai véc-tơ chỉ phương bằng `0`)
   - Hình thang cân `MNPQ` có chiều cao $\sqrt{7}$ và diện tích chính xác $S(MNPQ) = 3\sqrt{7}$.
2. **Phân tách 4 chặng liên tục (`V13_STORY_SCENES`):**
   - **Bước 1 — Đề bài xuất hiện:** Chỉ hiển thị giả thiết `Giả thiết: Lăng trụ đều ABC.A′B′C′ (a = 4)` và `Trung điểm M ∈ AB · N ∈ AC · P ∈ CC′`. Không lộ `MN = 2`, `MQ = NP = 2√2`, hay `S(MNPQ) = 3√7`.
   - **Bước 2 — Hình thành không gian:** Thể hiện `AA′, BB′, CC′ ⊥ (ABC)` và tách nét khuất theo độ sâu quan sát.
   - **Bước 3 — Khám phá quan hệ:** Làm nổi bật quan hệ song song `MN ∥ PQ`, tìm giao điểm thứ tư `Q ∈ BB′` trên mặt phẳng `(MNP)`.
   - **Bước 4 — Kết quả trực quan:** Mở khóa đầy đủ chip kết quả (`emphasis === "result"`) gồm `MN = 2`, `PQ = 4`, `MQ = NP = 2√2`, `S(MNPQ) = 3√7`.

---

## 9. Mobile Storytelling Strategy (`NOT_PHYSICAL_MOBILE`)

- Bố cục mobile (breakpoint `<= 920px` và `<= 560px` trong `landing.css`) ưu tiên **sân khấu minh họa lên trước**, theo sau là thanh điều khiển `Bước 1–4`, nút `Tạm dừng / Tiếp tục` và thẻ giải thích ngắn gọn (illustration-first), tránh cảnh chữ dày đè lên hình.
- Các nút chọn chặng và điều khiển đều đạt vùng chạm thuận tiện, nhóm chip thông số tự xuống dòng sạch trên màn hình hẹp (`320px–390px`).
- **Lưu ý trung thực môi trường đo:** Tất cả số liệu mobile trong Báo cáo mục 11 được thu trên Chrome Headless giả lập viewport `390 × 844` kèm tiết lưu CPU `4×` (`NOT_PHYSICAL_MOBILE`), không thay thế hoàn toàn cảm nhận chạm trên thiết bị iOS/Android vật lý.

---

## 10. Reduced Motion & Fallback Strategy

- **CSS Accessibility:** `landing.css` bổ sung khối `@media (prefers-reduced-motion: reduce)` tắt transition/animation trên `.axo-v13-step-item`, `.axo-v13-play-btn`, `.axo-v13-switch-btn`, v.v.
- **Runtime Reduced Motion (kiểm chứng bằng Playwright):** Dưới `reducedMotion: "reduce"`, cả Prototype A và Prototype B tự động dừng chuỗi tự động chuyển chặng (`playBtnText === "Tiếp tục"`), đưa mô hình về trạng thái tĩnh chuẩn xác ngay lập tức với `settledIdleRafCount === 0`.
- **Fallback xác định ở Prototype B:** Nếu môi trường chưa có WebGL (SSR, thiết bị chặn WebGL, hoặc `webglcontextlost`), `HeroConceptBFallbackSvg` và `Story3DFallbackSvg` lập tức đảm bảo nội dung hình học rõ nét, không xuất hiện khung canvas trống.

---

## 11. Performance Benchmark Comparison (Dual-Backend Playwright)

Nguồn đo chính thức: `landing_v1_3_audit/perf/v13-prototypes-benchmark.json` (`capturedAt: "2026-11-15T13:34:34.977Z"`). Toàn bộ **12/12 lần chạy** (2 backend × 2 viewport profile × 3 biến thể) đạt `settledIdleRafCount = 0`, `webglContextLostCount = 0`, `consoleErrorCount = 0`, `pageErrorCount = 0`.

### 11.1. Backend 1: `ANGLE / SwiftShader` (`Google, Vulkan 1.3.0 SwiftShader Device`)

| Profile | Biến thể | Motion FPS | P95 Frame (ms) | Resize FPS / P95 | Long Tasks (count / max ms) | LCP (ms) | CLS | WebGL (active / max / lifetime) | JS Heap Δ (MB) |
|---|---|---:|---:|---|---:|---:|---:|---|---:|
| `desktop_1920x1080` (`1×`) | `prod` (V1.2.2) | `57.2` | `16.7` | `118.2 / 16.7ms` | `3 / 563ms` | `1312` | `0` | `2 / 2 / 2` | `+3.53` (`37.29 → 40.82`) |
| `desktop_1920x1080` (`1×`) | `proto_a` (`?prototype=a`) | `58.4` | `16.7` | `121.9 / 16.7ms` | `1 / 97ms` | `544` | `0` | `1 / 1 / 1` | `+0.87` (`37.65 → 38.52`) |
| `desktop_1920x1080` (`1×`) | `proto_b` (`?prototype=b`) | `58.7` | `16.7` | `106.5 / 33.3ms` | `4 / 82ms` | `388` | `0` | `2 / 2 / 6` | `+1.14` (`38.08 → 39.22`) |
| `mobile_390x844` (`4× CPU`, `NOT_PHYSICAL_MOBILE`) | `prod` (V1.2.2) | `60.0` | `16.8` | `108.3 / 16.8ms` | `5 / 285ms` | `1336` | `0.0191` | `2 / 2 / 2` | `-2.81` (`39.61 → 36.8`) |
| `mobile_390x844` (`4× CPU`, `NOT_PHYSICAL_MOBILE`) | `proto_a` (`?prototype=a`) | `51.8` | `33.3` | `114.6 / 16.8ms` | `5 / 268ms` | `1212` | `0` | `1 / 1 / 1` | `+0.68` (`38.38 → 39.06`) |
| `mobile_390x844` (`4× CPU`, `NOT_PHYSICAL_MOBILE`) | `proto_b` (`?prototype=b`) | `52.4` | `16.8` | `54.7 / 16.8ms` | `6 / 280ms` | `1116` | `0` | `2 / 2 / 6` | `+0.89` (`39.05 → 39.94`) |

### 11.2. Backend 2: `Hardware GPU D3D11` (`Intel(R) UHD Graphics (0x00009A68) Direct3D11 vs_5_0 ps_5_0`)

| Profile | Biến thể | Motion FPS | P95 Frame (ms) | Resize FPS / P95 | Long Tasks (count / max ms) | LCP (ms) | CLS | WebGL (active / max / lifetime) | JS Heap Δ (MB) |
|---|---|---:|---:|---|---:|---:|---:|---|---:|
| `desktop_1920x1080` (`1×`) | `prod` (V1.2.2) | `57.1` | `16.8` | `122.1 / 16.7ms` | `3 / 407ms` | `752` | `0` | `2 / 2 / 2` | `-0.04` (`38.68 → 38.64`) |
| `desktop_1920x1080` (`1×`) | `proto_a` (`?prototype=a`) | `57.5` | `16.7` | `122.0 / 16.7ms` | `3 / 134ms` | `592` | `0` | `1 / 1 / 1` | `+1.93` (`36.31 → 38.24`) |
| `desktop_1920x1080` (`1×`) | `proto_b` (`?prototype=b`) | `58.7` | `16.7` | `114.2 / 16.8ms` | `4 / 97ms` | `500` | `0` | `2 / 2 / 6` | `+0.75` (`37.86 → 38.61`) |
| `mobile_390x844` (`4× CPU`, `NOT_PHYSICAL_MOBILE`) | `prod` (V1.2.2) | `54.2` | `16.8` | `98.3 / 16.8ms` | `5 / 644ms` | `1916` | `0` | `2 / 2 / 2` | `-1.19` (`39.38 → 38.19`) |
| `mobile_390x844` (`4× CPU`, `NOT_PHYSICAL_MOBILE`) | `proto_a` (`?prototype=a`) | `48.6` | `33.4` | `114.6 / 16.8ms` | `6 / 388ms` | `1676` | `0` | `1 / 1 / 1` | `+2.04` (`35.47 → 37.51`) |
| `mobile_390x844` (`4× CPU`, `NOT_PHYSICAL_MOBILE`) | `proto_b` (`?prototype=b`) | `49.7` | `33.3` | `46.7 / 33.4ms` | `9 / 292ms` | `1144` | `0` | `2 / 2 / 6` | `+0.54` (`38.72 → 39.26`) |

**Nhận xét định lượng chính:**
- Cả hai prototype V1.3 đều rút ngắn **LCP** và giảm hẳn độ dài **max Long Task** so với V1.2.2 (ví dụ trên Desktop SwiftShader: `proto_a` max long task `97ms`, `proto_b` `82ms` so với `prod` `563ms`; trên Desktop Hardware GPU: LCP `592ms` / `500ms` so với `prod` `752ms`).
- **Prototype A** cho tốc độ khung hình khi resize rất ổn định trên mobile tiết lưu CPU (`114.6 fps` / `16.8ms`) và chỉ dùng `1` ngữ cảnh WebGL toàn trang.
- **Prototype B** đạt tốc độ khung hình chuyển động nhỉnh hơn nhẹ (`58.7 fps` Desktop, `52.4 / 49.7 fps` Mobile `4× CPU`) nhờ render 3D GPU, nhưng chi phí `resize` trên mobile (`54.7 / 46.7 fps`) và số lần khởi tạo lại ngữ cảnh (`lifetime = 6` khi cuộn Hero ↔ Demo) cao hơn.

---

## 12. Visual Quality Comparison (Post-Fix Inspection)

Qua hai lượt chụp ảnh và video `.webm` thực tế trên Chromium (bộ ảnh cuối lưu tại `landing_v1_3_audit/screenshots/` và `landing_v1_3_audit/video/`):

- **Các lỗi thị giác đã phát hiện và sửa triệt để ở vòng QA trực quan:**
  1. Căn khung hình & tỷ lệ chiếu `ContinuousVectorStoryCanvas` (Prototype A): tăng hệ số phóng đại `55 * vis.zoom`, đặt tâm `cy = 216`, kẹp vùng nhãn `[24..576] × [24..406]` giúp lăng trụ và chữ ký hiệu `A, B, C, M, N, P, Q` rõ nét, không chạm biên.
  2. Căn camera & mặt phẳng `HeroConceptB3D` + `Continuous3DStoryStage` (Prototype B): chỉnh `LANDING_PYRAMID_SAMPLE.defaultCamera * 0.92` (`fov = 36`) cho Hero; chỉnh `radius = 12.6 / curZoom` và `lookAt(0, -0.08, -0.38)` cho Story; dùng chính xác polygon `planeQuad`; neo điểm `P` và `Q` trực tiếp vào `prismPivot` để `P` không bị tách rời khi lăng trụ trồi lên ở Bước 1.
  3. Sửa dòng mô tả `.axo-sp-section-lead` bị cắt cụt ở cả hai prototype để hiển thị đầy đủ bài toán lăng trụ đều `ABC.A′B′C′ (a = 4)`.
- **9 ảnh chụp hậu kiểm đã xác nhận trực quan:** `prod_isolation_desktop.png`, `proto_a_desktop_hero.png`, `proto_a_desktop_story_stage0.png`, `proto_a_desktop_story_stage3.png`, `proto_a_mobile_story.png`, `proto_b_desktop_hero.png`, `proto_b_desktop_story_stage0.png`, `proto_b_desktop_story_stage3.png`, `proto_b_mobile_story.png`.
- **2 video minh họa chuyển động liên tục:** `proto_a_motion.webm` và `proto_b_motion.webm`.

---

## 13. Trade-off Matrix & Reasoned Recommendation (No Unilateral Winner)

Quyết định chọn hướng nào cho bản chính thức thuộc thẩm quyền của Chủ dự án (`PENDING_OWNER_REVIEW`). Bảng dưới tổng hợp trung thực các đánh đổi giữa hai phương án:

| Tiêu chí | Prototype A (`?prototype=a` — Vector Motion) | Prototype B (`?prototype=b` — 3D Spatial) |
|---|---|---|
| **Chiều sâu 3D không gian thực** | Hình chiếu 2.5D trên SVG; sắc nét ở mọi DPI nhưng góc xoay bị giới hạn quanh tư thế thiết kế sẵn. | Khối Three.js thực có thể xoay không gian liên tục; mang lại cảm giác "3D geometry engine" rõ rệt nhất. |
| **Độ ổn định thiết bị yếu / Mobile & Resize** | Xuất sắc: `0` WebGL ở Hero/Story, `114.6 fps` khi resize trên mobile `4× CPU`, không bao giờ gặp rủi ro `webglcontextlost` ở đầu trang. | Tốt nhờ cơ chế nhường slot `<= 2` và fallback SVG, nhưng resize mobile (`46.7–54.7 fps`) và lifecycle WebGL (`lifetime = 6`) nặng hơn Prototype A. |
| **Độ sắc nét nhãn đỉnh toán học** | Đỉnh và chữ `A, B, C, M, N, P, Q` hòa chung một cây vector SVG, không lệch nét. | Dùng lớp SVG phủ đồng bộ tọa độ chiếu 3D; đẹp khi tĩnh nhưng nhạy cảm hơn với thay đổi khung camera. |
| **Rủi ro bảo trì dài hạn** | Thấp — thuần React + phép chiếu toán học nhẹ, không cần quản lý tài nguyên GPU ở 2 khối đầu trang. | Trung bình — cần duy trì quy luật dispose Three.js và slot lease `<= 2` giữa Hero và Demo. |

**Đề xuất cân bằng để Chủ dự án cân nhắc:**
- **Chọn Prototype A (`?prototype=a`)** nếu ưu tiên tuyệt đối tốc độ tải đầu trang, độ sắc nét kiểu Notion/Figma, nhẹ pin trên mobile và zero-risk về WebGL ở phần trên màn hình (vẫn giữ 3D WebGL ở Demo Tương tác bên dưới).
- **Chọn Prototype B (`?prototype=b`)** nếu ưu tiên ấn tượng thị giác 3D ngay từ Hero và muốn người học cảm nhận không gian xoay Three.js xuyên suốt phần Storytelling.
- **Hướng kết hợp khả thi (nếu Chủ dự án yêu cầu ở vòng tiếp theo):** Dùng **Hero Concept A (SVG)** hoặc **Hero Concept B** kết hợp có chọn lọc với phần Storytelling tương ứng — cả hai khối hiện được tách sạch để có thể phối ghép dễ dàng sau khi có quyết định.

---

## 14. Prototype Access Instructions & Evidence Artifacts

Server phát triển cục bộ đang chạy tại `http://localhost:3001`:

- **Bản chính thức V1.2.2 (không bị ảnh hưởng):** `http://localhost:3001/` và `http://localhost:3001/gioi-thieu`
- **Prototype A (Vector Interactive Storytelling):** `http://localhost:3001/gioi-thieu?prototype=a`
- **Prototype B (3D Spatial Transformation):** `http://localhost:3001/gioi-thieu?prototype=b`

**Thư mục artifact kiểm chứng (ngoài git tree):**
- REA Summary: `landing_v1_3_audit/rea/rea-motion-summary.json`
- Dual-backend Benchmark JSON: `landing_v1_3_audit/perf/v13-prototypes-benchmark.json`
- Screenshots (9 tệp PNG): `landing_v1_3_audit/screenshots/`
- Videos (2 tệp WebM): `landing_v1_3_audit/video/proto_a_motion.webm`, `landing_v1_3_audit/video/proto_b_motion.webm`

---

## 15. Automated Verification Gates (`VERIFIED`)

- `design-taste-frontend/scripts/lint.mjs` trên `LandingPrototypeA.tsx` & `LandingPrototypeB.tsx`: `0 FAIL, 0 WARN`.
- `npx tsc -b`: thoát mã `0`.
- `npm run build` (`vite build`): thoát mã `0` (`122 modules transformed`).
- `npx vitest run --maxWorkers=2 code-index-sync class-coverage landing-`: **14/14 file test pass, 52/52 test pass** (gồm 2 suite V1.3 mới `landing-motion-accessibility.test.tsx`, `landing-storytelling-geometry.test.tsx`, `code-index-sync.test.ts`, `class-coverage.test.ts` và các suite Landing sẵn có).
- `Playwright 8-viewport matrix` (`3 routes × 8 viewports = 24/24` phép kiểm tra): `overflowX: false` trên mọi kích thước từ `1920×1080` xuống `320×568`; `h1LineRatio`: `1.03` (`prod`), `1.25` (`proto_a`, `proto_b`).
- `Playwright Switch & Isolation`: chuyển đổi `proto_a → proto_b → prod` giữ đúng URL query, hiển thị banner đúng ngữ cảnh và xóa sạch banner khi quay lại `/gioi-thieu`.
- `python backend/scripts/audit_docs_information_architecture.py --json`: trả `STATUS: "FAIL"` (mã thoát `1`) **chỉ do 4 đường dẫn cũ sẵn có** thuộc phần xóa lớp học của phiên song song tại `docs/CODE_INDEX.md` dòng `4605, 4619, 4634, 4646` (`LiveClassDock.tsx`, `LiveClassStrip.tsx`, `MonitorView.tsx`, `classroom-sync.ts` — không chỉnh sửa để bảo toàn phạm vi); toàn bộ các cổng kiểm định còn lại (`OWNERSHIP.valid: true`, `DOCS_LAYOUT.valid: true` [`root_doc_count: 29`, `catalog_count: 167`, `unclassified: []`], `LINKS.valid: true` [`684` liên kết, `0` lỗi], `SECRET_SCAN.valid: true`, `STATUS_LEDGER.valid: true`, `EVIDENCE_INDEX.valid: true`, `OPEN_ISSUES.valid: true`, `CANONICAL_NEXT_ACTION.valid: true`, `STABLE_MUTABLE.valid: true`) đều đạt.

---

## 16. Integration Gate Status

- **Trạng thái hiện tại:** `Owner Approval: PENDING_OWNER_REVIEW`.
- **Chính sách tích hợp:** Không gộp Prototype A hay Prototype B vào route mặc định (`/`, `/gioi-thieu`) khi chưa có quyết định lựa chọn trực tiếp từ Chủ dự án.
- **Danh sách đúng 8 tệp thuộc commit Pha B (`feat(axo): add v1.3 landing motion prototypes for owner review`):**
  1. `frontend/src/components/LandingView.tsx`
  2. `frontend/src/components/landing/LandingPrototypeA.tsx`
  3. `frontend/src/components/landing/LandingPrototypeB.tsx`
  4. `frontend/src/components/landing/landing.css`
  5. `frontend/src/components/__tests__/landing-motion-accessibility.test.tsx`
  6. `frontend/src/components/__tests__/landing-storytelling-geometry.test.tsx`
  7. `docs/CODE_INDEX.md`
  8. `docs/evaluation/landing/AXO-LANDING-V1.3-CREATIVE-DIRECTION-REPORT.md`
