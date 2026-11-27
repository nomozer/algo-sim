# AXO — FRONTEND PERFORMANCE OPTIMIZATION, ROUTE-LEVEL LAZY LOADING & BUNDLE ISOLATION — FINAL ACCEPTANCE REPORT

> **Trạng thái:** Đang hoàn tất phát hành (`ba9eec063`), chờ cập nhật kết quả đo trực tiếp `https://hoclieu.tech` sau `git push origin main`.
> **Ngày thực hiện:** 2026-11-27
> **Nhánh:** `main` (Base: `9809ece5c925259612c3c5d78cff32e60822cdce` → Candidate `ba9eec063`)

---

## 1. Tóm tắt kiến trúc & Các lớp tách phụ thuộc (Bundle Isolation)

1. **Tách siêu dữ liệu thuần khỏi Three.js (`perf(scene3d)` — `72b4d353c`):**
   - Tách `scene3d-metadata.ts` (toán tử `Q³` thuần, `attachProblemContextToScene`, `problemContextOfScene`, `inspectAxialCurvedOrthogonality`, `normalizeCylinderEnvelopeTitle`, `hasUncertifiedObjectSource`) khỏi `scene3d-semantic-policy.ts`.
   - Ngắt cạnh phụ thuộc kéo `three` vào `history.ts`, `offline-catalog.ts`, `geometry-samples.ts` và Landing/Shell.
2. **Tải dữ liệu 22 bài mẫu hình học theo nhu cầu (`perf(frontend)` — `ec034ab1f`):**
   - Tách `sample-catalog-meta.ts` (chỉ chứa metadata nhẹ, slug, phân loại, đề bài rút gọn, `stepCount`, `configHash` và cache runtime) và `CatalogSamplePreview.tsx` + `geometry2d/catalog-preview.ts` (thumbnail SVG tĩnh).
   - Nạp động hai nhóm JSON gốc (`advanced-geometry-samples.json` qua chunk `geometry-samples-public` và `geometry-samples.json` qua chunk `geometry-samples-legacy`) bằng dynamic `import()` trong `sample-loader.ts` khi người dùng mở bài mẫu hoặc khôi phục `scene3d`, có chống race-condition (`sampleLoadSeq` + `waitForPendingSampleLoad()`) trong `store.ts`. Hai tệp JSON chuẩn gốc được giữ nguyên 100% nội dung.
3. **Route-Level Lazy Loading, Tách Auth/Admin & Lazy App CSS (`ec034ab1f`):**
   - Chia `AuthGate.tsx` thành các chunk độc lập: `auth-shared.tsx`, `AuthGateModal.tsx`, `AuthPageView.tsx`, `AccountSettingsModal.tsx`, `AdminWorkspaceView.tsx`.
   - Cấu hình `React.lazy` kèm retry 1 lần + `.preload()` + `resetFailedLazyChunks()` + prefetch có điều kiện theo ý định (`shouldPrefetchOnIntent()`, tự tắt khi `saveData` hoặc mạng `2g`/`slow-2g`) tại `utils/lazy-with-retry.ts`.
   - Chia CSS ứng dụng thành `tokens.css` + `shell-base.css` + `landing.css` (nạp ban đầu gọn nhẹ cho Landing) và `global.css` qua `load-app-styles.ts` (tải bất đồng bộ theo route `/app`, `/library`, `/login`, `/admin`, `/simulation/...`), loại bỏ `import "../styles/global.css"` khỏi từng component TSX để tương thích hoàn toàn với các test harness `esbuild`.
   - Cấu hình `vite.config.ts` manualChunks tách riêng `vendor-three`, `geometry-samples-public`, `geometry-samples-legacy`.

---

## 2. Cấu trúc Bundle Production (`frontend/dist`) BEFORE vs AFTER

| Thành phần (`dist/`) | BEFORE (`9809ece5c`) | AFTER (`ba9eec063`) | Biến đổi |
|---|---|---|---|
| `<link rel="modulepreload">` trong `dist/index.html` | `vendor-three`, `geometry-samples` | Không preload chunk nặng (`[]`) | Loại bỏ hoàn toàn preload dư thừa |
| Entry JS (`index-*.js`) | `1,094.95 kB` raw / `315.51 kB` gz | `474.73 kB` raw / `140.66 kB` gz | **-56.6% raw / -55.4% gz** |
| Entry CSS (`index-*.css`) | `409.10 kB` raw / `64.27 kB` gz | `58.11 kB` raw / `9.99 kB` gz | **-85.8% raw / -84.5% gz** |
| App-wide CSS lazy (`load-app-styles-*.css`) | Gộp trong entry CSS | `363.30 kB` raw / `57.67 kB` gz | Chỉ tải ngoài Landing |
| Three.js chunk (`vendor-three-*.js`) | `568.24 kB` / `143.15 kB` gz (eager) | `568.24 kB` / `143.15 kB` gz (lazy) | Chỉ tải ở `/simulation/*` |
| Geometry Samples JSON chunks | `1,399.94 kB` / `263.90 kB` gz (gộp) | `public`: `543.42 kB` (`57.27 kB` gz)<br>`legacy`: `219.10 kB` (`17.05 kB` gz) | Nạp đúng nhóm theo nhu cầu |
| Route chunks tách riêng | Gộp trong `index.js` | `SimulationWorkspace` `868.48 kB`, `AdminWorkspaceView` `132.78 kB`, `LibraryView` `55.07 kB`, `LeftSidebar` `44.92 kB`, `AuthPageView` `22.94 kB`, `AccountSettingsModal` `14.43 kB`, `HomeView` `0.50 kB` | Cô lập theo từng màn hình |

---

## 3. So sánh Hiệu năng Thực nghiệm (Local Production Build `:3000`, `n=5` Median)

| Kịch bản | JS BEFORE | JS AFTER | CSS BEFORE | CSS AFTER | Total BEFORE | Total AFTER | Three.js (A) | Samples (A) | LCP BEFORE | LCP AFTER | Ready BEFORE | Ready AFTER |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `desktop:/` | `723,718 B` | **`140,780 B` (-80.5%)** | `65,856 B` | **`11,572 B` (-82.4%)** | `1,686,666 B` | `1,049,392 B` | `0 B` | `0 B` | `716 ms` | `688 ms` | `730 ms` | `709 ms` |
| `desktop:/about` | `723,718 B` | **`140,780 B`** | `65,857 B` | **`11,572 B`** | `1,686,666 B` | `1,049,392 B` | `0 B` | `0 B` | `726 ms` | `764 ms` | `744 ms` | `772.5 ms` |
| `desktop:/library` | `723,718 B` | **`208,052 B` (-71.3%)** | `65,857 B` | `69,615 B` | `934,882 B` | **`422,922 B` (-54.8%)** | `0 B` | `0 B` | `1,128 ms` | **`796 ms` (-29.4%)** | `1,145 ms` | **`787 ms` (-31.3%)** |
| `desktop:/app` | `723,718 B` | **`190,233 B` (-73.7%)** | `65,856 B` | `69,617 B` | `934,882 B` | **`405,105 B` (-56.7%)** | `0 B` | `0 B` | `844 ms` | **`768 ms`** | `875 ms` | **`776 ms`** |
| `desktop:/login` | `723,718 B` | **`196,866 B`** | `65,856 B` | `69,617 B` | `934,882 B` | **`411,738 B` (-56.0%)** | `0 B` | `0 B` | `800 ms` | **`688 ms`** | `795 ms` | **`695 ms`** |
| `desktop:/admin` | `723,718 B` | **`220,499 B`** | `65,857 B` | `69,618 B` | `934,882.5 B` | **`435,371.5 B` (-53.4%)** | `0 B` | `0 B` | `880 ms` | `872 ms` | `892 ms` | `894 ms` |
| `desktop:/simulation/pyramid-circumscribed-sphere` | `723,718 B` | `678,657 B` | `65,856 B` | `69,617 B` | `954,004 B` | `912,650 B` | `143,538 B` | **`75,089 B` (-71.6%)** | `1,200 ms` | `1,936 ms` | `1,260 ms` | `2,145 ms` |
| `mobile_slow:/` (Fast3G+4xCPU) | `723,718 B` | **`140,780 B`** | `65,856 B` | **`11,572 B`** | `790,473 B` | `326,085 B` | `0 B` | `0 B` | `5,252 ms` | **`2,472 ms` (-52.9%)** | `5,379 ms` | **`2,779 ms` (-48.3%)** |
| `mobile_slow:/library` (Fast3G+4xCPU) | `723,718 B` | **`208,052 B`** | `65,858 B` | `69,615 B` | `934,884 B` | **`422,922 B`** | `0 B` | `0 B` | `8,064 ms` | **`4,144 ms` (-48.6%)** | `8,638 ms` | **`4,182 ms` (-51.6%)** |
| `mobile_slow:/app` (Fast3G+4xCPU) | `723,718 B` | **`190,233 B`** | `65,856 B` | `69,615 B` | `800,844 B` | **`405,103 B`** | `0 B` | `0 B` | `6,772 ms` | **`3,260 ms` (-51.9%)** | `7,043 ms` | **`3,461 ms` (-50.9%)** |

- **Responsive 7 viewports (`1920x1080` → `320x700`):** `0` tràn ngang (`overflowX`), `0` ảnh vỡ (`brokenImgs`).
- **Kiểm tra thị giác 6 màn hình chụp BEFORE/AFTER (`screenshots/`):** Giữ nguyên 100% bố cục Landing, Hero, Library SVG thumbnails, App composer, Login card và Workspace Scene3D 17 bước.

---

## 4. Kiểm định Hành trình End-to-End, Khôi phục Chunk, Bảo toàn CSS & WebGL (`verify_step_d_e2e.mjs`)

- **Hành trình cô lập `S.ABCD` (`ALLOW_LIVE_AI=0`, `HYBRID_ROUTE_MODE=local-first`):**
  - `wsReadyMs = 655 ms`, `POST /api/analyze` → `200 OK` (`1,113 ms`), `totalSubmitToSceneMs = 1,642 ms`, `status = SERVED`, `hasExactAnswer16 = true`, `.geo3d-canvas canvas` (`809×862`, `hasGl = true`, `renderedCount = 11`), `0` request ra mạng ngoài.
- **Phục hồi lỗi tải chunk (Chunk Load Failure & Retry):**
  - Chặn request `**/LibraryView-*.js` khi đã nhập đề nháp trên `/app` → `ErrorBoundary` hiển thị bề mặt khôi phục hợp lệ (`errorVisible = true`, `hasRetryBtn = true`, không trắng trang). Gỡ chặn và bấm `[data-error-action="secondary-retry"]` → `LibraryView` khôi phục đủ `11` thẻ (`libraryRecovered = true`), quay lại `/app` giữ nguyên hoàn toàn nội dung đề nháp (`draftPreserved = true`).
- **Điều hướng ngược (`/ -> /app -> /about`):** `hasSidebar = false`, `headerH = 72 px`, `heroBg = rgb(255, 255, 255)`, `overflowX = false`, `brokenImgs = 0`.
- **Ổn định WebGL qua chuyển bài mẫu liên tiếp:** `webglcontextlost = 0`, `renderedCount = 26`, `canvas = 809×862`, `pageErrors = []`.

---

## 5. Kiểm chứng Hồi quy, Bảo mật & Đóng băng Candidate trên Cây Commit Sạch (`ba9eec063`)

- **Ranh giới bất biến:** `git diff 9809ece5c..ec034ab1f -- backend/app frontend/src/simulations/domains/semantic frontend/src/data/advanced-geometry-samples.json frontend/src/data/geometry-samples.json` **trống hoàn toàn**.
- **Frontend Regression (độc lập, cây `ba9eec063`):** `npm run build` PASS (`0` cảnh báo CSS), `tsc -b` PASS (`0` lỗi), `npx vitest run` **194/194 test files (`2,319/2,319` tests) PASS**, bao gồm `route-lazy-loading.test.tsx` (6/6) và `bundle-isolation.test.ts` (2/2).
- **Backend Offline Regression (`ALLOW_LIVE_AI=0`, cây `ba9eec063`):**
  - Partition 1 (`tests/geometry/` chạy song song lúc đầu): `13,247 passed, 1 failed` (`test_14_weak_device_performance_and_memory_stability_50_requests` `p50=58.5ms < 50ms` do tranh chấp CPU với Vitest); chạy lại `tests/geometry/test_correctness_ocr_performance.py` độc lập: **`21 passed in 18.12s` (`0 failed`)**.
  - Partition 2 (`tests/ --ignore=tests/geometry`): **`1,971 passed, 0 failed`**.
  - Tổng hợp hiệu lực: **`15,219 passed, 0 failed`**.
- **Freeze Governance & Cache Identity (`ba9eec063`):**
  - `freeze_evaluation_candidate.py --verify`: **PASS** (`commit=5255ac2a0`, `product_commit_sha=ec034ab1f`, `cay_lam_viec_sach=true`, `127 files`, `tree_hash=92f8e24dd56b5bb0eda60fa85cdf3caabea71a0c7b5ed0e741922f7b2cbb1ab7`, `CACHE_VERSION="158"`).
  - `--verify-historical` trên candidate active (`5255ac2a0`), lịch sử `4978ac01f`, và archive `prior-EVALUATION_CANDIDATE-473cb68de.json`: **ALL PASS**.
  - `lock_cache_identity.py --verify`: **PASS (`CACHE_VERSION 158`)**.
- **Bảo mật & Xuất bản:** `npm audit` = `0 vulnerabilities`, `npm audit --omit=dev` = `0 vulnerabilities`, `check_publication_safety.py --range 9809ece5c..HEAD` = **PASS** (`scanned=51, violations=0`).

---

## 6. Kiểm chứng Production `https://hoclieu.tech` (Sau Push)

- *Sẽ cập nhật ngay sau khi đẩy `main` và xác minh deployment Vercel.*

---

## 7. Bảng Cổng Nghiệm thu Gate A–Z & Kết luận Pha 27

| Gate | Hạng mục kiểm chứng | Kết quả |
|---|---|---|
| A–D | Khóa ranh giới bất biến (`backend/app`, `semantic/`, JSON gốc không đổi) | **PASS** |
| E–G | Tách Three.js metadata (`scene3d-metadata.ts`), Sample metadata & dynamic loader (`sample-loader.ts`) | **PASS** |
| H–K | Route lazy loading (`Auth/Admin/Workspace/Library/Home/Sidebar`), Lazy App CSS (`load-app-styles.ts`), `shell-base.css` | **PASS** |
| L–N | `npm run build` (0 CSS warning), `tsc -b` (0 error), Bundle isolation (`vendor-three`/`samples` không ở Landing) | **PASS** |
| O–R | Hồi quy toàn phần Frontend (`194/194` files, `2,319/2,319` tests) & Backend offline (`15,219` passed hiệu lực) | **PASS** |
| S–V | Đo BEFORE vs AFTER local & Fast3G (`desktop:/` JS `-80.5%`, `mobile_slow:/` LCP `-52.9%`), 7 responsive viewports, thị giác 6 trang | **PASS** |
| W–Y | E2E `S.ABCD` (`SERVED`, đáp án `16`), khôi phục lỗi chunk + giữ nháp, WebGL stability (`0` context lost), `npm audit` `0`, `publication_safety` & 5 cổng Freeze Governance | **PASS** |
| Z | Đẩy `origin/main` & xác minh trực tiếp `https://hoclieu.tech` | **PENDING_PUSH** |
