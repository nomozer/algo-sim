# VERCEL_FRONTEND_DEPLOYMENT_RUNBOOK.md — Hướng dẫn triển khai Frontend Axo trên Vercel

Tài liệu vận hành chính thức cho việc cấu hình, kiểm chứng và khắc phục sự cố khi triển khai frontend Axo trên Vercel với custom domain `https://hoclieu.tech`.

> [!IMPORTANT]
> Không lưu API key, `ADMIN_PASSWORD`, `DATABASE_URL`, JWT/session secrets, hoặc token Vercel trong tài liệu này hay trong `frontend/vercel.json`.

---

## 1. Phân tách ranh giới cấu hình

| Lớp cấu hình | Chủ sở hữu / Nơi lưu | Thành phần cụ thể |
|---|---|---|
| **Git-managed** (mã nguồn) | Kho Git (`frontend/vercel.json`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/components/AxoErrorExperience.tsx`) | Schema Vercel, lệnh build/output, SPA fallback rewrite loại trừ `/api` và `/assets`, security & cache headers, client router |
| **Vercel Project Settings** (Dashboard) | Vercel Project (`hoclieu.tech`) | Root Directory (`frontend`), Production Branch (`main`), Framework Preset (`Vite`), Node.js version, Preview/Production deployment settings |
| **Vercel Secrets & Env Vars** | Vercel Environment Variables (UI / CLI, ngoài Git) | Biến môi trường từng môi trường (Production / Preview / Development) nếu bổ sung về sau; **không** đặt secret backend (`GEMINI_API_KEY`, `APP_SESSION_SECRET`, `ADMIN_PASSWORD`, `DATABASE_URL`) vào biến `VITE_*` công khai |
| **DNS & Custom Domain** | Nhà cung cấp DNS + Vercel Domains | Bản ghi trỏ `hoclieu.tech` về edge Vercel (`A` / `CNAME`), chứng chỉ TLS/HTTPS và HSTS |

---

## 2. Thông số dự án Vercel & tương thích Node.js

| Thiết lập | Giá trị chuẩn (khớp kiến trúc thực tế) |
|---|---|
| **Vercel Root Directory** | `frontend` (dùng duy nhất `frontend/vercel.json`, không đặt file trùng ở root repo) |
| **Framework Preset** | Vite (`vite ^6.x`) |
| **Package Manager / Lockfile** | `npm` với `frontend/package-lock.json` (`npm ci` / `npm install`) |
| **Build Command** | `npm run build` (`tsc -b && vite build`) |
| **Output Directory** | `dist` |
| **Node.js Compatibility** | Node.js 20 LTS hoặc 22 LTS trên Vercel (đã kiểm build cục bộ trên Node v26.13.0 / npm 11.20.0; không phụ thuộc native addons khi build SPA tĩnh) |
| **Production Branch** | `main` |
| **Custom Domain hiện hành** | `https://hoclieu.tech` |

---

## 3. Chiến lược SPA Rewrite, Headers & Cache (`frontend/vercel.json`)

Cấu hình nằm tại [`frontend/vercel.json`](../../frontend/vercel.json) theo schema `https://openapi.vercel.sh/vercel.json`:

1. **SPA Rewrite có bảo vệ API và Static Assets:**
   - Rule `"source": "/((?!api(?:/|$)|assets(?:/|$)|.*\\.[a-zA-Z0-9]+$).*)"` → `"destination": "/index.html"`.
   - Phục vụ trực tiếp (HTTP `200 text/html`) và F5 reload mọi route SPA hợp lệ (`/`, `/about`, `/gioi-thieu`, `/login`, `/register`, `/forgot`, `/forgot-password`, `/reset`, `/app`, `/library`, `/history`, `/workspace`, `/admin`, `/account`, `/simulation/pyramid-circumscribed-sphere`, `/simulation/<slug>`) cũng như route lỗi ứng dụng (`/khong-ton-tai`) để `AxoErrorExperience` xử lý đúng hợp đồng.
   - Bảo toàn URL gốc và query parameters (ví dụ `?reset_token=...`), Browser Back/Forward hoạt động bình thường.
   - **Loại trừ rõ ràng** `/api`, `/api/*`, `/assets`, `/assets/*` và mọi đường dẫn có đuôi file (`.js`, `.mjs`, `.css`, `.png`, `.svg`, `.json`, ...). Request tới API hoặc asset không tồn tại **không bao giờ** bị rewrite nhầm thành `index.html` (`200 text/html`).
2. **Chính sách Cache:**
   - `/index.html`: `public, max-age=0, must-revalidate` để ngay sau redeploy, trình duyệt luôn lấy manifest chunk mới nhất, không giữ tham chiếu tới hash chunk đã bị xóa.
   - `/assets/([^/]+-[A-Za-z0-9_-]{8}\\.(js|mjs|css))`: `public, max-age=31536000, immutable` áp dụng chặt riêng cho các bundle JS/MJS/CSS có content hash 8 ký tự do Vite/Rollup sinh ra ở gốc `/assets/` (`index-*.js`, `vendor-three-*.js`, `geometry-samples-*.js`, `pdf-*.js`, `pdf.worker.min-*.mjs`, `index-*.css`). File không có hash 8 ký tự (như `/assets/foo-bar.js`) hoặc ảnh tĩnh dưới `/assets/landing/*` **không** bị gắn `immutable`.
   - Lưu ý xác minh: thông số Root Directory = `frontend` và Output Directory = `dist` trên `https://hoclieu.tech` hiện được **suy luận gián tiếp** từ phản hồi HTTP thực tế (`GET /` trả `dist/index.html`); xác minh trực tiếp trong Vercel Dashboard vẫn ở trạng thái `PENDING_EXTERNAL_CONFIGURATION`.
3. **Security Headers:**
   - `X-Content-Type-Options: nosniff`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: camera=(self), geolocation=(), microphone=(), payment=(), usb=()` — giữ quyền `camera=(self)` vì luồng chụp đề bài Camera-First cần truy cập camera cùng origin.
   - Không đặt `COOP`/`COEP` hay `CSP` cứng nhắc khi chưa đánh giá đủ tác động tới Three.js WebGL, worker `pdfjs-dist` và Google Fonts (`Inter`).

---

## 4. Chiến lược kết nối Backend (`/api/*`) & Biến môi trường

### Hiện trạng kiến trúc frontend
- Mọi lời gọi backend trong `frontend/src/` (`App.tsx`, `state/auth.ts`, `llm/client.ts`, `state/history.ts`, `state/construction-step-edits.ts`, `components/AuthGate.tsx`) sử dụng đường dẫn **relative `/api/...`** kèm `credentials: "include"`.
- Cục bộ ở development, [`frontend/vite.config.ts`](../../frontend/vite.config.ts) proxy `/api` tới `http://localhost:8000`. Proxy này **không** tự động tồn tại trên Vercel production.
- Backend FastAPI đặt cookie phiên `HttpOnly` với `SameSite=Lax` (`backend/app/accounts/router.py`). Do đó, khi có backend production host riêng (HTTPS):
  - **Phương án khuyến nghị khi gắn backend production:** thêm một rule rewrite có thứ tự **trước** catch-all SPA trong `frontend/vercel.json` để proxy cùng-origin `/api/:path*` → `https://<VERCEL_HOSTED_BACKEND_ORIGIN>/api/:path*` (giữ nguyên method, path, query, body và cookie `SameSite=Lax`), **hoặc** cấu hình `CORS` tường minh với origin `https://hoclieu.tech` + `allow_credentials=True` nếu chuyển sang URL tuyệt đối.
  - **Trạng thái hiện tại (`BACKEND_DEPLOYMENT_PENDING`):** chưa có origin backend production được cung cấp/triển khai, nên `frontend/vercel.json` **không** chứa URL backend giả định hay `localhost`. Request `/api/*` trên production trả HTTP `404` chuẩn (không bị biến thành HTML).

### Biến môi trường cần phân biệt
- **Frontend bundle (`VITE_*`):** công khai hoàn toàn trong JS build. Hiện ứng dụng không yêu cầu biến `VITE_*` bắt buộc khi chạy qua relative `/api`.
- **Backend secrets (tuyệt đối chỉ nằm ở backend host, không bao giờ đưa lên Vercel frontend):** `GEMINI_API_KEY`, `DATABASE_URL`, `APP_SESSION_SECRET`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`.

---

## 5. Quy trình triển khai Preview & Production

1. **Trước khi đẩy lên nhánh / Preview:**
   ```bash
   cd frontend
   npm run build
   npx vitest run src/vercel-config.test.ts src/code-index-sync.test.ts
   ```
2. **Vercel Preview Deployment:**
   - Tạo preview từ feature branch (hoặc chạy `npx vercel deploy` khi đã xác thực Vercel CLI trên máy có quyền).
   - Kiểm tra trực tiếp trên URL preview các deep link: `/about`, `/login`, `/register`, `/forgot-password`, `/simulation/pyramid-circumscribed-sphere`, `/khong-ton-tai`, và kiểm tra `/api/nonexistent` + `/assets/nonexistent.js` không trả `text/html`.
3. **Production Deployment (`main`):**
   - Sau khi Owner rà soát và merge vào `main`, push `main` để Vercel tự build từ Root Directory `frontend`.
   - **Không** dùng `vite` dev proxy ở production; mọi thao tác `vercel --prod` hoặc chỉnh DNS chỉ do Owner hoặc người có thẩm quyền thực hiện.

---

## 6. Điều tra lỗi 404 & Xử lý sự cố sau triển khai

### Cách phân biệt nhanh nguồn lỗi 404
| Triệu chứng khi gọi `curl -sS -i <url>` | Nguồn gốc lỗi | Hướng xử lý |
|---|---|---|
| `HTTP 404`, header `X-Vercel-Error: NOT_FOUND`, `Content-Type: text/plain` trên route như `/about`, `/simulation/pyramid-circumscribed-sphere` trong khi `/` trả `200 HTML` | **Vercel SPA Routing 404** (thiếu `rewrites` tại Vercel Root Directory, hoặc Root Directory bị đặt sai chỗ không đọc `frontend/vercel.json`) | Kiểm tra Root Directory = `frontend`, xác nhận `frontend/vercel.json` đã có mặt trong bản commit được deploy |
| `HTTP 200`, `Content-Type: text/html` trên route `/simulation/pyramid-circumscribed-sphere`, nhưng UI hiển thị trang **404 của Axo** | **Client-side Router 404** (slug không khớp `offline-catalog.ts` hoặc regex route sai) | Kiểm tra `CANONICAL_SAMPLE_SLUGS` trong `frontend/src/data/offline-catalog.ts` và `resolveLocationRoute` trong `frontend/src/components/AxoErrorExperience.tsx` |
| `HTTP 404`, `X-Vercel-Error: NOT_FOUND` hoặc `404 JSON` trên `/api/...` | **API 404 / Backend chưa gắn (`BACKEND_DEPLOYMENT_PENDING`)** | Đúng hành vi an toàn (API không bị nuốt thành HTML); khi backend sẵn sàng, gắn rewrite `/api/:path*` hoặc cấu hình backend endpoint |
| `HTTP 404` trên `/assets/index-*.js` trong khi `index.html` trả `200` | **Chunk cũ từ cache HTML** hoặc build fail | Xác nhận header `/index.html` có `max-age=0, must-revalidate` và kiểm tra Build Logs trên Vercel |

### Checklist kiểm tra Vercel Dashboard (dành cho Owner đối chiếu)
1. **Project Settings → General → Root Directory:** phải là `frontend`.
2. **Project Settings → General → Framework Preset:** `Vite`; **Build Command:** `npm run build` (hoặc default Vite override hợp lệ); **Output Directory:** `dist`.
3. **Project Settings → Environments / Git → Production Branch:** `main`.
4. **Project Settings → Domains:** `hoclieu.tech` đã xác thực SSL hợp lệ; nếu trước đây bật Deployment Protection chặn preview/domain, kiểm tra đúng phạm vi bảo vệ.
5. **Deployments → Build & Function Logs:** sau khi push `main`, mở deployment mới nhất và kiểm tra:
   - `curl.exe -sS -I https://hoclieu.tech/about` → phải là `HTTP/2 200` (`content-type: text/html`) và có `x-content-type-options: nosniff`.
   - `curl.exe -sS -I https://hoclieu.tech/simulation/pyramid-circumscribed-sphere` → `HTTP/2 200` (`text/html`), F5 trên trình duyệt mở thẳng mô phỏng 3D.
   - `curl.exe -sS -I https://hoclieu.tech/assets/nonexistent.js` → `HTTP/2 404` (không phải HTML).
   - `curl.exe -sS -I https://hoclieu.tech/api/nonexistent` → `404` (hoặc JSON từ backend khi backend đã gắn, không phải HTML).

---

## 7. Rollback Deployment khi có sự cố

1. **Rollback tức thời trên Vercel (không cần build lại):** mở Vercel Dashboard → Deployments → chọn bản deployment ổn định ngay trước đó → **Instant Rollback**.
2. **Rollback trong Git:** tạo commit tiến tới bằng `git revert <commit-sha>` trên `main` rồi push để Vercel build lại từ commit sạch (không dùng `git reset --hard` hay force-push trên `main`).
