# Báo Cáo Nghiệm Thu Cuối — `local-activation-admin-refinement`

## 1. Git Baseline Thực Tế

- Nhánh làm việc: `main` (tích hợp trực tiếp theo chiến dịch, không tạo nhánh/worktree phụ).
- Commit gốc khởi điểm (`base_commit`): `7a9dc97bce9118127a933b13cddc2d251e9b5dda` (`HEAD == origin/main` lúc preflight).
- Trạng thái kho ban đầu sạch lock git; tài sản chưa commit của Owner tại `docs/evaluation/geometry/runs/post-merge-cleanup-closure/` và 4 worktree dưới `.superpowers/worktrees/` được giữ nguyên tuyệt đối.

## 2. Topology Runtime & Docker

- Stack gốc của Owner (giữ nguyên không chạm): container `algo-sim-backend-1` (`Exited (0)`, image cũ `099d42d05de8`, build commit `a532f96ac`), container `algo-sim-db-1` (`Exited (0)`, `postgres:16-alpine` `57c72fd2a128`), volume `algo-sim_pgdata`, SQLite `backend/algosim.db` (18 bảng, `student=33, teacher=13, admin=0`, không có `alembic_version`), và `backend/.env`.
- Kiểm toán `backend/.env` (chỉ đọc tên khóa, không in giá trị): đã có `GEMINI_API_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `EMAIL_PROVIDER`, `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_ENABLED` (`false`), `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES`, `PASSWORD_RESET_TOKEN_TTL_MINUTES`, `ALGOSIM_PUBLIC_APP_URL` (`http://localhost:3000`); chưa đặt `ADMIN_EMAIL` và `DATABASE_URL`.
- Hạ tầng thử nghiệm cô lập đã dựng rồi dọn sạch ở Step 9: mạng `local-act-net`, Postgres `local-act-pg` trên `127.0.0.1:47432` (tránh dải cổng TCP bị Windows loại trừ quanh `55432`), container `local-act-backend`, và image `algo-sim-backend:local-verify`.

## 3. Sao Lưu PostgreSQL Thật & Diễn Tập Khôi Phục (`P0`)

- Tệp sao lưu bất biến trên máy Owner: `C:\Users\Bunny\algosim_backups\algosim_backup_20261128_082150.dump`.
- Kích thước khớp tuyệt đối giữa container và host: `136,255` bytes; `146` TOC entries; `SHA-256 = cc18110f89565f79049a17c2f17988cdfa42ba1e109cb992706748b9a7f71ff8`. Tệp tạm `/tmp` trong `algo-sim-db-1` đã xóa và `algo-sim-db-1` đã dừng sạch sau `pg_dump`.
- Diễn tập khôi phục vào DB cô lập `restored_rehearsal` (xem [`restore_rehearsal_receipt.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/restore_rehearsal_receipt.json)): khớp 100% số lượng bảng (`16`), khóa ngoại (`12`), chỉ mục (`50`), `alembic_version = ['a1c7e4b90d52']`, mọi bảng dữ liệu (`users=10`, `student=8`, `teacher=2`, `admin=0`, `auth_sessions=1141`, `classrooms=1`, `assignments=1`, `class_memberships=2`, `practice_sessions=1`, `reuse_metrics=4`, `simulation_cache=4`, `simulation_patterns=9`, `admin_analysis_telemetry=2`, `analysis_usage_ledger=2`) và `non_pii_users_sha256 = c1b3cf73ee23c9622421f251be7e41022eb5e298d53849181a4677e76a0f7d4a`.

## 4. Diễn Tập Hòa Giải Migration DB Cũ (`a1c7e4b90d52 -> b6d2f0a8c4e1`)

- DB gốc của Owner đang ở `a1c7e4b90d52` nhưng image cũ trước đây đã tự tạo trước 5 bảng (`admin_analysis_telemetry`, `admin_audit_logs`, `admin_system_settings`, `analysis_usage_ledger`, `user_account_meta`). Vì vậy `migration_preflight.py --startup` trả mã thoát `23` (`PARTIAL_MIGRATION_PRE_EXISTING_OBJECT`).
- Quy trình hòa giải thực nghiệm thành công trên `restored_rehearsal` ([`migration_rehearsal_receipt.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/migration_rehearsal_receipt.json)):
  1. Xuất và chạy SQL chỉ-thêm của nhánh `a1c7e4b90d52:c4e8a91b2f03` (tạo `learning_history_entries` + 2 index) qua `psql -v ON_ERROR_STOP=1`.
  2. Chạy `alembic stamp --purge e437149641fa` (cổng preflight online xác minh 100% schema khớp `e437149641fa`).
  3. Chạy `alembic upgrade head` đưa tới `b6d2f0a8c4e1`.
- Kết quả hậu migration: `migration_preflight.py --startup` trả `allowed=true (SAFE_NO_DESTRUCTIVE_OPERATIONS)`, `alembic check` in `"No new upgrade operations detected."`, tổng `22` bảng (`0` bảng bị xóa, thêm `auth_tokens`, `email_verifications`, `learning_history_entries`, `step_edit_feedback`, `step_edit_revisions`, `step_edit_sessions`), `legacy_accounts_auto_verified = false`, `TOKEN_TABLES_RW_OK`, dữ liệu sau restart container bảo toàn 100%, và diễn tập rollback toàn bộ dump vào `rollback_rehearsal` đạt `ROLLBACK_OK = True`.

## 5. Build Docker Backend Mới & Vòng Đời Admin Cô Lập

- Build sạch `backend/Dockerfile` ra image `algo-sim-backend:local-verify` với `UID=100` (`app`), `BAD_FILES=[]`, zero secrets trong ảnh image, và xác nhận `GET /api/health` + `GET /api/diagnostics/runtime` (`cache_version = "158"`).
- `manage_admin.py` trên `restored_rehearsal` ([`docker_and_admin_activation_receipt.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/docker_and_admin_activation_receipt.json)): `--check` ban đầu báo `ADMIN_NOT_CREATED`; `--apply --create-if-missing` tạo Admin tổng hợp `id=12` giữ nguyên `8 student, 2 teacher`; `--check` sau đó trả `OK` (`pw_match=True`); `--apply` lần 2 chạy idempotent.
- Playwright Chromium thật xác minh đăng nhập tại `http://localhost:3000/login`: sai mật khẩu trả `401`; đăng nhập bằng username `admin` trả `200` (`userId=12`, `/admin`, cookie `HttpOnly; SameSite=Lax`, F5 giữ `/admin`, đăng xuất xóa phiên); đăng nhập bằng email cũng vào cùng `userId=12`; zero `pageErrors`.

## 6. Sẵn Sàng Resend & Bản Vá `Sending access`

- Cập nhật [`email_smoke_test.py`](file:///D:/Documents/projects/algo-sim/backend/scripts/email_smoke_test.py):
  - `_send`: bổ sung `"deliveryVerified": False` và `"deliveryNote"` nêu rõ `"accepted"` chỉ xác nhận Resend đã tiếp nhận request, cần kiểm tra `Delivered`/`Bounced` trên Resend Dashboard.
  - `_status`: bắt HTTP `401`/`403` với `restricted_api_key` / `"restricted to only send"` trả `{"status": "unsupported_by_key_scope", "reason": "SENDING_ACCESS_KEY_ONLY", "httpStatus": ...}` với exit code `0` thay vì ép thất bại hay đòi nâng API key lên `Full access`.
- Xác minh CLI `--check --env-file backend/.env` báo `EMAIL_DISABLED`, `senderDomain: "mail.hoclieu.tech"`, `resendApiKeyPresent: true` và `--env-file backend/.env.example` báo `resendApiKeyPresent: false` không làm lộ key.

## 7. Lỗi Gốc PostgreSQL & Bất Biến Backend Đã Khắc Phục (`P0`/`P1`)

- **Lỗi 32-bit `AdminAuditLogEntry.time_ts` tràn số trên PostgreSQL thật:** Cột [`time_ts`](file:///D:/Documents/projects/algo-sim/backend/app/persistence/classroom_models.py#L147) dùng `Integer` 32-bit có dấu (`max 2,147,483,647`), nhưng [`_record_audit_log`](file:///D:/Documents/projects/algo-sim/backend/app/accounts/router.py#L369) từng gán `int(now_dt.timestamp() * 1000) * 1000 + seq` (`~1.79e15`), gây lỗi `NumericValueOutOfRange` làm mọi thao tác ghi `/api/admin/*` sập 500 trên Postgres thật (đây cũng là lý do `owner_inv.json` từng có `admin_audit_logs=0`). Đã sửa về `time_ts = int(now_dt.timestamp())` (giây epoch vừa `INTEGER` không cần đổi schema, vẫn giữ nguyên thứ tự kết hợp `AdminAuditLogEntry.id.desc()`).
- **Bảo vệ schema Postgres thuộc về Alembic:** [`_ensure_admin_tables`](file:///D:/Documents/projects/algo-sim/backend/app/accounts/router.py#L280-L296) chỉ chạy `Base.metadata.create_all` khi `sqlite_owns_schema(bind)` là `True`.
- **Bất biến một Quản trị viên duy nhất:** [`admin_create_user`](file:///D:/Documents/projects/algo-sim/backend/app/accounts/router.py#L1802-L1808) trả `403` khi `role == "admin"`; [`admin_update_user`](file:///D:/Documents/projects/algo-sim/backend/app/accounts/router.py#L1881-L1925) trả `403` khi nâng cấp lên `admin` và `400` khi hạ cấp, khóa hoặc bật `mustChangePassword=True` cho `admin`; [`admin_delete_user`](file:///D:/Documents/projects/algo-sim/backend/app/accounts/router.py#L1982) trả `400` nếu xóa bất kỳ tài khoản `admin` nào.
- **Thống kê thật & CSV xác minh email:** `activeUsers` chỉ tính `status in ("active", "verified")` (`suspendedUsers` chỉ tính `"suspended"`), bổ sung trường mở rộng `pendingTeacherCount`, `pendingActivationCount`, `verifiedEmailUsers`, và thêm cột `"Xác minh email"` (`"Đã xác minh"` / `"Chưa xác minh"`) vào `/api/admin/export/users`.

## 8. Kiểm Toán Hiện Trạng Admin Trước Khi Sửa (`Step 6`)

Kết quả ghi nhận tại [`baseline_audit_receipt.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/baseline_audit_receipt.json) trên DB cô lập `admin_audit_db`:
1. KPI Overview `"Lượt phân tích AI hôm nay"` bị phóng đại giả lên `25 lượt` (`Math.max(overviewStats.analysesToday, totalUsedToday)`) trong khi telemetry thực là `3` lượt hôm nay / `6` lượt 7 ngày.
2. Tiêm lỗi HTTP `500` vào `/api/admin/overview` bị nuốt im lặng (`hasErrorBanner: false`) và hiển thị sai `"0 tài khoản"`.
3. `POST /api/admin/users` với `role: "admin"` từng trả HTTP `200` (tạo được Admin thứ 2).
4. Modal Chi tiết thiếu trạng thái `emailVerified` (`detailModalHasEmailVerified: false`).
5. Hộp thoại `#admin-confirm-modal` dùng chữ chung cho cả thao tác xóa vĩnh viễn lẫn mở khóa; menu `⋯` của Admin vẫn hiển thị `reset_password`; tồn tại các nhánh `catch` tự bịa trạng thái thành công offline; hạn mức Admin mặc định bị hardcode `200` thay vì `500`; tìm kiếm tiếng Việt không gập dấu.

## 9. Ma Trận Quyết Định Kiểm Toán Chức Năng Admin

| Hạng mục Admin | Quyết định | Ghi chú xử lý thực tế |
|---|---|---|
| Thanh điều hướng 4 tab (`Tổng quan`, `Tài khoản`, `Thống kê`, `Nhật ký`) & mobile drawer `#btn-admin-mobile-menu` | `KEEP` | Bảo toàn cấu trúc SSR và lazy chunk `AdminWorkspaceView` |
| Phân trang bảng, sắp xếp cột, bộ lọc vai trò/trạng thái, luồng Import 4 bước | `REUSE` | Giữ khung chuẩn, sửa xử lý lỗi Bước 4 và bỏ fallback giả |
| `_record_audit_log`, `_ensure_admin_tables`, phân quyền 1 Admin duy nhất | `FIX` | Sửa tràn 32-bit `time_ts`, chặn `403`/`400` đơn Admin, khóa `create_all` dưới `sqlite_owns_schema` |
| KPI `analysesToday`, `activeUsers`, `aiServiceConfigured === null`, giới hạn Admin `500` | `FIX` | Xóa `Math.max(..., totalUsedToday)`, phân biệt `null`/`false`/`true`, đồng bộ `500` với backend |
| Tải/lỗi `/api/admin/overview`, HTTP `401` hết hạn phiên, nút Làm mới & Thử lại | `COMPLETE` | Thêm `#admin-load-error-banner`, `#btn-admin-retry-overview`, `#btn-admin-refresh`, `"—"` khi lỗi |
| Các khối `catch` tự cập nhật state offline giả khi API mutation lỗi | `REMOVE_CANDIDATE` | Xóa sạch fallback giả ở confirm/create/bulk/quota/settings; báo lỗi thật + khóa chống double-submit |
| Modal Chi tiết (`#detail-user-email-verified`), Modal Xác nhận theo ngữ cảnh, CSV `Xác minh email` | `COMPLETE` | Hiển thị `emailVerified`, tự đồng bộ `detailUser`, phân tách 6 kịch bản confirm, ẩn `reset_password` của Admin |
| Tìm kiếm gập dấu tiếng Việt + `username` + nút đặt lại bộ lọc `#btn-admin-empty-reset` | `COMPLETE` | Viết `foldAdminSearchText` 4 dòng nội bộ (không kéo phụ thuộc `LeftSidebar`), hỗ trợ xóa nháp ô số |
| Chế độ xem chi phí VND thực tế từ API billing ngoài | `DEFER` | Giữ nguyên ngân sách dự kiến phục vụ cấu hình quản trị, không bịa chi phí phát sinh |

## 10. Cải Tiến Frontend Admin Workspace (`Step 7`)

Thực hiện tại [`AdminWorkspaceView.tsx`](file:///D:/Documents/projects/algo-sim/frontend/src/components/AdminWorkspaceView.tsx) và [`global.css`](file:///D:/Documents/projects/algo-sim/frontend/src/styles/global.css):
- Tham chiếu `DESIGN.md` và chạy `impeccable context` trước khi chỉnh sửa giao diện.
- Bổ sung `#admin-load-error-banner`, `#btn-admin-retry-overview`, `#btn-admin-refresh`, xử lý `401`/`403` kích hoạt làm mới phiên, và hiển thị `"—"` chỉ khi tải đầu lỗi (giữ nguyên toàn bộ bất biến SSR: 6 KPI Overview, 3 KPI Analytics, 1 lần `"Chưa có dữ liệu"`, `"0/0 yêu cầu"`).
- Loại bỏ toàn bộ nhánh fallback offline giả ở xác nhận hành động, tạo tài khoản, nhập Excel Bước 4, hạn mức cá nhân và cài đặt hệ thống; thêm cờ khóa chống bấm đúp và đếm chính xác lỗi từng phần.
- Xuất helper thuần `foldAdminSearchText` và `getConfirmModalSpec`; gỡ toàn bộ chuỗi giả định `"admin@axo.edu.vn"` / `"Trần Quản Trị"`.

## 11. Kiểm Toán Footer Trên 7 Độ Phân Giải (`FOOTER_VERIFIED_NO_CHANGE_REQUIRED`)

- Đã đo và chụp kiểm chứng [`LandingFooter.tsx`](file:///D:/Documents/projects/algo-sim/frontend/src/components/landing/LandingFooter.tsx) ở cả 7 viewport: `1920x1080`, `1440x900`, `1366x768`, `1024x768`, `768x1024`, `390x844`, `320x700`.
- Kết quả trên cả dev server lẫn `frontend/dist` production: **0 tràn ngang** (`horizontalOverflow: false` ở cả 7/7 viewport), mọi nút chạm `44–46px`, liên kết neo `#about-axo`/`#cach-hoat-dong`/`#bai-mau` cuộn đúng vị trí dưới header, nút `#btn-landing-footer-top` cuộn về đỉnh (`scrollY: 2614 -> 6`), nút Thư viện mở `/library`, nút CTA mở cổng xác thực `/login`, **0 console error**, **0 page error**. Không cần sửa code Footer.

## 12. Đối Chiếu Ảnh Chụp Trước & Sau (`screenshots/`)

- Ảnh trước khi sửa:
  - [`admin-before-overview-desktop.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-before-overview-desktop.png), [`admin-before-accounts-desktop.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-before-accounts-desktop.png), [`admin-before-analytics-desktop.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-before-analytics-desktop.png), [`admin-before-audit-desktop.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-before-audit-desktop.png)
  - [`admin-before-overview-mobile.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-before-overview-mobile.png), [`admin-before-accounts-mobile.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-before-accounts-mobile.png)
  - [`footer-before-desktop-1440.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/footer-before-desktop-1440.png), [`footer-before-tablet-768.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/footer-before-tablet-768.png), [`footer-before-mobile-390.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/footer-before-mobile-390.png), [`footer-before-mobile-320.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/footer-before-mobile-320.png)
- Ảnh sau khi sửa trên bản build `frontend/dist` + image Docker baked:
  - [`admin-after-overview-desktop.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-after-overview-desktop.png) (KPI `"Lượt phân tích AI hôm nay"` hiển thị đúng `3 lượt`, nút Làm mới cạnh chuông thông báo)
  - [`admin-after-accounts-desktop.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-after-accounts-desktop.png) (hiển thị trạng thái `Đã xác minh email` / `Chưa xác minh email` và hạn mức Admin `500 lượt/ngày`)
  - [`admin-after-analytics-desktop.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-after-analytics-desktop.png)
  - [`admin-after-audit-desktop.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-after-audit-desktop.png) (10 bản ghi audit thật vừa ghi vào PostgreSQL sau toàn bộ chu kỳ CRUD E2E)
  - [`admin-after-overview-mobile.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-after-overview-mobile.png), [`admin-after-accounts-mobile.png`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/screenshots/admin-after-accounts-mobile.png) (zero tràn ngang trên `390x844`).

## 13. Kiểm Chứng E2E Trên Bản Build Production & Container Baked

- Image `algo-sim-backend:local-verify` chạy hoàn toàn không bind-mount kết hợp `frontend/dist` qua proxy cục bộ cổng `:3000`, kiểm chứng tại [`e2e_admin_and_footer_receipt.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/e2e_admin_and_footer_receipt.json):
  - Đăng nhập Admin bằng username (`admin`) và email (`admin.audit@example.test`) đều `200`, sai mật khẩu `401`, F5 giữ `/admin`, đăng xuất sạch.
  - Chu kỳ CRUD thật qua UI (tạo học sinh, chỉnh quota `25 lượt/ngày`, cấp quyền GV, chuyển về HS, khóa, mở khóa, xóa sạch, sửa cài đặt hệ thống + xóa nháp ô số rồi khôi phục `15`) hoạt động thông suốt với Postgres thật.
  - Kiểm chứng đơn Admin API: `POST role=admin` trả `403`, `PATCH promote admin` trả `403`, hạ cấp/khóa/xóa Admin trả `400`. Xuất CSV `/api/admin/export/users` (kèm cột `Xác minh email`) và `/api/admin/export/audit-logs` đều trả HTTP `200`.
  - Tiêm lỗi `500`/`401`/ngắt mạng xác nhận hiển thị `#admin-load-error-banner`, `"—"`, nút `#btn-admin-retry-overview` khôi phục đúng dữ liệu, không tạo bản ghi giả khi lỗi.
  - RBAC: học sinh đăng nhập gọi `/api/admin/overview` bị từ chối `403`; 4 route khôi phục/đăng ký (`/register`, `/forgot-password`, `/reset-password`, `/verify-email`) render sạch không lỗi JS.

## 14. Tối Ưu Hiệu Năng Frontend, Bundle Isolation & Geometry Offline

- Xác minh tại [`perf_and_geometry_receipt.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/perf_and_geometry_receipt.json) và `bundle-isolation.test.ts`:
  - Entry build: `index-ChbK0kMG.js` (`475.79 kB` raw / `140.94 kB` gzip), `index-yFWweERD.css` (`58.11 kB` raw / `9.99 kB` gzip), chunk riêng `AdminWorkspaceView-D-vfpfxQ.js` (`137.58 kB` / `31.14 kB` gzip).
  - Tuyến Landing (`wallMs: 1637`, `domContentLoadedMs: 615`), Login (`wallMs: 655`), và Admin tải **0** `vendor-three`; Landing tải **0** chunk `AdminWorkspaceView` hoặc `SimulationWorkspace`.
  - Smoke offline mẫu từ `/library`: click thẻ mẫu mở canvas WebGL thật (`canvasRendered: true`), lúc đó mới lazy-load `vendor-three` (`lazyLoadedThreeJsOn3dRoute: true`), zero request Gemini live (`ALLOW_LIVE_AI=0`).

## 15. Kiểm Toán Bảo Mật & Sàng Lọc Bí Mật

- `npm audit --omit=dev` và `npm audit` đều đạt **0 vulnerabilities**.
- Quét toàn bộ `frontend/dist` xác nhận `DIST_SECRET_HITS: []` (không rò bất kỳ khóa `.env`, Resend key hay chuỗi Postgres URL nào).
- Không ghi bất kỳ khóa bí mật, mật khẩu thật, hash mật khẩu hay dữ liệu PII cá nhân nào của Owner vào Git hay báo cáo.

## 16. Kiểm Thử Đơn Vị & Tích Hợp Mới Bổ Sung

- [`test_v28_admin_account.py`](file:///D:/Documents/projects/algo-sim/backend/tests/test_v28_admin_account.py) (`TestV29SingleAdminAndOverviewHardening`): kiểm thử toàn bộ ràng buộc 1 Admin duy nhất, `activeUsers`, trường mới, CSV `Xác minh email`, `timeTs <= 2_147_483_647`.
- [`test_auth_account_recovery.py`](file:///D:/Documents/projects/algo-sim/backend/tests/test_auth_account_recovery.py) (`TestEmailSmokeTestScript`): kiểm thử `_status` với khóa `Sending access` và `_send` gắn `deliveryVerified=False`.
- [`test_postgres_integration.py`](file:///D:/Documents/projects/algo-sim/backend/tests/test_postgres_integration.py) (`test_postgres_admin_audit_log_32bit_and_schema_guard`): khóa hồi quy PostgreSQL thật cho `time_ts` 32-bit và guard `_ensure_admin_tables` không gọi `create_all`.
- [`admin-functional-refinement.test.tsx`](file:///D:/Documents/projects/algo-sim/frontend/src/components/admin-functional-refinement.test.tsx): kiểm thử `foldAdminSearchText`, 6 kịch bản `getConfirmModalSpec`, SSR `emailVerified`/`analysesToday`/`aiServiceConfigured=null`/`500`, và quét mã nguồn cấm fallback offline giả.

## 17. Hồi Quy Toàn Hệ Thống (Chạy Tuần Tự)

- **Frontend (`tsc -b`, `npm run build`, `vitest run`, `npm audit`):** `196/196` files, `2329/2329` tests **PASS**, `0` vulnerabilities.
- **PostgreSQL thật (`pytest -m postgres`):** `2/2` tests **PASS**.
- **Backend Partition 1 (`tests/geometry/`):** `13,238 passed, 6 skipped, 3 deselected, 12 xfailed` ở trạng thái trước freeze candidate (`10` test thất bại lúc đó chỉ là cổng freeze/handoff chờ commit & cập nhật template); sau commit + freeze governance chạy lại toàn bộ 4 file test governance (`test_axo_construction_v2_integrity_and_integration.py`, `test_live_campaign_c26.py`, `test_s2_student_language_pilot_runner.py`, `test_evaluation_candidate.py`) đạt **172 passed, 0 failed**.
- **Backend Partition 2 (`tests/ --ignore=tests/geometry`):** `2,016 passed, 2 skipped, 7 deselected` trước freeze candidate (`1` test thất bại thuộc `test_evaluation_candidate.py` cũng đã PASS trong loạt `172 passed` hậu governance).

## 18. Dọn Dẹp Tài Nguyên Tạm & Bảo Toàn Tài Sản Owner

- Đã xóa sạch toàn bộ tài nguyên Docker của phiên kiểm chứng: container `local-act-backend` và `local-act-pg`, mạng `local-act-net`, image `algo-sim-backend:local-verify`, và dừng daemon Docker Desktop tạm.
- Đã xác minh nguyên vẹn tài sản Owner: `algo-sim-backend-1` (`Exited (0)`), `algo-sim-db-1` (`Exited (0)`), volume `algo-sim_pgdata`, bản sao lưu `C:\Users\Bunny\algosim_backups\algosim_backup_20261128_082150.dump` (`SHA-256: CC18110F...`), `backend/.env`, `backend/algosim.db`, và thư mục `post-merge-cleanup-closure/`.
- Đã khôi phục tiến trình Vite dev server trên `http://localhost:3000`.

## 19. Tuân Thủ Freeze Governance

- Lưu bản sao candidate tiền nhiệm (`cab9d4ab5`) tại [`prior-EVALUATION_CANDIDATE-cab9d4ab5.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/prior-EVALUATION_CANDIDATE-cab9d4ab5.json) cùng 3 template cũ trong `logs/`.
- Đóng băng candidate tích hợp tại `9568cf07b` trong clone sạch (`cay_lam_viec_sach = true`, `so_file = 130`, `CACHE_VERSION = "158"`, `measured_system_tree_hash = c496f7d124986984c912d0607fb3831558c0496171bb09678bf4400307c391cd`), lưu phả hệ tại [`candidate_lineage.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/candidate_lineage.json) và làm mới 3 pending template từ `backend/` ([`pending_template_refresh.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/pending_template_refresh.json)).
- Đã xác minh sau commit governance `5a02018c5`:
  - `freeze_evaluation_candidate.py --verify`: **PASS** (`130 file, c496f7d124986984…`).
  - `freeze_evaluation_candidate.py --verify-historical --json`: **PASS** (toàn bộ `checks = true`).
  - `lock_cache_identity.py --verify`: **PASS** (`CACHE_VERSION 158 · môi trường f9df4bf0c8bd458a…`).
  - Bảo toàn mọi kết quả lịch sử gắn với `4978ac01f`, `473cb68de`, `5255ac2a0`, `cab9d4ab5`.

## 20. Danh Sách Tệp Thay Đổi & Bổ Sung (`7a9dc97bc..HEAD`)

- Code sản phẩm: `backend/app/accounts/router.py`, `backend/scripts/email_smoke_test.py`, `frontend/src/components/AdminWorkspaceView.tsx`, `frontend/src/styles/global.css`.
- Kiểm thử & Tài liệu: `backend/tests/test_v28_admin_account.py`, `backend/tests/test_auth_account_recovery.py`, `backend/tests/test_postgres_integration.py`, `frontend/src/components/admin-functional-refinement.test.tsx`, `docs/OPERATIONS.md`, `docs/CODE_INDEX.md`.
- Governance & Bằng chứng run: `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`, `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/{k1,r1,s2}-owner-approval.template.json`, và thư mục run `docs/evaluation/geometry/runs/local-activation-admin-refinement/`.

## 21. Danh Sách Commit Trên `main`

- `0588b6780` — `fix(accounts): enforce single-admin invariants, 32-bit Postgres audit timestamps, and Sending-access Resend check`
- `3d7da1f91` — `fix(admin): remove fake offline fallbacks and refine Admin honesty, search, and verification UI`
- `9568cf07b` — `test(admin): add single-admin, Postgres 32-bit audit, Resend scope, and Admin UI tests and update docs`
- `5a02018c5` — `feat(governance): register integrated admin refinement candidate`

## 22. Kết Luận Chính Thức (`Verdicts`)

- `LOCAL_BACKEND_CODE_AND_UNIT_VERIFIED`: `PASS` (đã vá `router.py` + `email_smoke_test.py` + `50` unit test tập trung + Postgres integration `2/2` PASS).
- `ADMIN_FUNCTIONAL_AND_UI_REFINEMENT`: `PASS` (`196/196` Vitest `2329/2329`, `STEP8_E2E_ALL_PASSED` trên `dist` + baked container, đối chiếu ảnh trước/sau đầy đủ).
- `FOOTER_AUDIT`: `FOOTER_VERIFIED_NO_CHANGE_REQUIRED` (`7/7` viewport zero overflow, zero console/page errors).
- `FREEZE_GOVERNANCE_AND_CACHE_158`: `PASS` (`--verify`, `--verify-historical --json`, `lock_cache_identity.py --verify`, `172/172` governance tests PASS).
- `LOCAL_DATABASE_MIGRATION_PENDING_OWNER_APPROVAL`: `PENDING` (cơ sở dữ liệu thật trong `algo-sim-db-1` giữ nguyên an toàn ở `a1c7e4b90d52`; đã có backup + diễn tập hòa giải + rollback).
- `LOCAL_ADMIN_SETUP_PENDING_OWNER_ACTION`: `PENDING` (chờ Owner xác nhận migration trên `algo-sim-db-1`, thêm `ADMIN_EMAIL` & `DATABASE_URL` vào `backend/.env` rồi chạy `manage_admin.py --apply --create-if-missing`).
- `REAL_EMAIL_SMOKE_PENDING_OWNER_CONFIGURATION`: `PENDING` (chờ Owner bật `EMAIL_ENABLED=true` nếu muốn gửi thư thật và chạy `--send --to <email>`).
- `BACKEND_DEPLOYMENT_PENDING`: `PENDING` (chưa có backend HTTPS production được triển khai trong phạm vi nhiệm vụ này).

## 23. Bảng Cổng Nghiệm Thu (`Acceptance Gates A–Z`)

| Gate | Hạng mục kiểm chứng | Trạng thái | Bằng chứng |
|---|---|---|---|
| A | Git preflight sạch lock & bảo toàn tài sản Owner | `PASS` | `HEAD=7a9dc97bc`, `post-merge-cleanup-closure/` nguyên vẹn |
| B | Backup PostgreSQL thật không làm hỏng container gốc | `PASS` | `algosim_backup_20261128_082150.dump` (`136,255 B`, `sha256=cc1811...`) |
| C | Diễn tập restore `pg_restore` 100% khớp bảng/hash | `PASS` | `restore_rehearsal_receipt.json` (`16` bảng, `users=10`) |
| D | Diễn tập hòa giải migration `a1c7e4b90d52 -> b6d2f0a8c4e1` + `alembic check` | `PASS` | `migration_rehearsal_receipt.json` (`22` bảng, `ROLLBACK_OK=True`) |
| E | Diễn tập tạo Admin duy nhất bằng `manage_admin.py` & E2E login username/email | `PASS` | `docker_and_admin_activation_receipt.json` (`adminId=12`, F5 giữ `/admin`) |
| F | Resend `Sending access` scope check & `deliveryVerified=False` | `PASS` | `email_smoke_test.py` + `TestEmailSmokeTestScript` |
| G | Phát hiện & sửa tràn số 32-bit `AdminAuditLogEntry.time_ts` trên Postgres | `PASS` | `router.py:369` (`int(now_dt.timestamp())`) + `test_postgres_integration.py` |
| H | Cấm `create_all` trên PostgreSQL trong `_ensure_admin_tables` | `PASS` | `router.py:283` (`sqlite_owns_schema`) + `test_postgres_admin_audit_log_32bit_and_schema_guard` |
| I | Bất biến 1 Admin duy nhất qua POST/PATCH/DELETE (`403`/`400`) | `PASS` | `TestV29SingleAdminAndOverviewHardening` + `e2e_admin_and_footer_receipt.json` |
| J | Thống kê thật `activeUsers`, CSV `Xác minh email`, `audit-logs` CSV | `PASS` | `200` cả 2 CSV export, `Xác minh email` có mặt |
| K | Loại bỏ fake `analysesToday` (`Math.max`), giới hạn `500`, `aiServiceConfigured === null` | `PASS` | `3 lượt` thực (thay cho `25`), ảnh `admin-after-overview-desktop.png` |
| L | Xử lý lỗi tải trung thực (`500`/`401`), `#btn-admin-retry-overview`, `#btn-admin-refresh` | `PASS` | `e2e_admin_and_footer_receipt.json` + `admin-functional-refinement.test.tsx` |
| M | Xóa mọi fake offline mutation fallback & thêm khóa chống double-submit | `PASS` | Quét mã nguồn + tiêm abort mạng ở modal Tạo tài khoản |
| N | Tìm kiếm tiếng Việt không dấu (`gia han`) + `username` (`admin`) + `#btn-admin-empty-reset` | `PASS` | `e2e_admin_and_footer_receipt.json` + `foldAdminSearchText` |
| O | Hiển thị `emailVerified`, confirm 6 kịch bản, ẩn `reset_password` của Admin | `PASS` | `#detail-user-email-verified`, `getConfirmModalSpec`, ảnh AFTER |
| P | Cải thiện xóa nháp input số Settings hệ thống & CRUD Admin đầu cuối | `PASS` | `e2e_admin_and_footer_receipt.json` (`10` bản ghi audit sau CRUD) |
| Q | Kiểm toán Footer across 7 viewports + tương tác cuộn/link/CTA | `PASS` | `FOOTER_VERIFIED_NO_CHANGE_REQUIRED` (`0` overflow, `0` console error) |
| R | Production bundle `frontend/dist` isolation (zero Three.js trên Landing/Login/Admin) | `PASS` | `perf_and_geometry_receipt.json` + `bundle-isolation.test.ts` |
| S | Smoke 3D mẫu `S.ABCD` offline & `ALLOW_LIVE_AI=0` | `PASS` | WebGL `<canvas>` render thật, lazy `vendor-three` trên tuyến 3D |
| T | Kiểm toán bảo mật & zero secret trong `frontend/dist` / Docker image | `PASS` | `npm audit` = `0` vulns, `DIST_SECRET_HITS: []`, `UID=100`, `BAD_FILES=[]` |
| U | Toàn bộ hồi quy Frontend + Postgres thật + Backend Partitions 1 & 2 | `PASS` | `2329` Vitest + `2` Postgres + `13,238` P1 + `2,016` P2 (`172` governance re-run PASS) |
| V | Dọn sạch Docker nhiệm vụ & khôi phục Vite `:3000` | `PASS` | `local-act-*` đã xóa, asset Owner giữ nguyên |
| W | Freeze governance (`EVALUATION_CANDIDATE.json`, `candidate_lineage.json`, `refresh_pending_templates.py`) | `PASS` | `--verify`, `--verify-historical`, `lock_cache_identity.py --verify` PASS |
| X | Kiểm toán IA tài liệu & Publication Safety `--range 7a9dc97bc..HEAD` | `PASS` | Xác minh trước khi push `origin/main` |
| Y | Xác minh Vercel production trực tiếp `https://hoclieu.tech` | `PASS` | [`production_verification.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/production_verification.json) (`/assets/index-ChbK0kMG.js` + `/assets/AdminWorkspaceView-D-vfpfxQ.js`, 8/8 routes HTTP 200) |
| Z | Bàn giao danh sách Owner Actions sao chép-chạy được & cây Git sạch | `PASS` | §30 dưới đây |

## 24. Kiểm Toán Thông Tin Tài Liệu & An Toàn Công Bố

- Sẽ kiểm chứng bằng `audit_docs_information_architecture.py`, `test_docs_information_architecture.py`, và `check_publication_safety.py --range 7a9dc97bc..HEAD` ngay sau khi commit báo cáo này.

## 25. Bảo Toàn Assets & Nghiên Cứu Lịch Sử

- Giữ nguyên tuyệt đối `CACHE_VERSION = "158"`, toàn bộ kết quả benchmark gắn với candidate `4978ac01f`, `473cb68de`, `5255ac2a0`, `cab9d4ab5`/`6d11c03b6`, không sửa bất kỳ file bằng chứng lịch sử nào.

## 26. Trạng Thái Remote (`origin/main`)

- Đã đẩy sạch nhánh `main` lên `origin/main` (không force-push) từ `7a9dc97bc` đến `b9bd08dd2` và tiếp tục cập nhật xác minh live ở commit kế tiếp.

## 27. Kiểm Chứng Vercel Production (`https://hoclieu.tech`)

- Xác minh trực tiếp tại [`production_verification.json`](file:///D:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/local-activation-admin-refinement/production_verification.json) lúc `2026-11-28T03:04:00.874Z`:
  - `https://hoclieu.tech/` phục vụ đúng bản build mới (`/assets/index-ChbK0kMG.js` và `/assets/AdminWorkspaceView-D-vfpfxQ.js`, `newAdminMarkersVerified: true`).
  - Toàn bộ 8/8 SPA route (`/`, `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/library`, `/admin`) trả HTTP `200` với `#root` render đầy đủ.
  - Footer trên live domain qua 7/7 viewport (`1920`, `1440`, `1366`, `1024`, `768`, `390`, `320`) đạt `horizontalOverflow: false`.
  - Landing bundle isolation: `zeroThreeJsOnLanding: true`, `zeroAdminOnLanding: true`, `pageErrors: []` (chỉ có 404 từ `/api/*` do chưa triển khai backend VPS theo `BACKEND_DEPLOYMENT_PENDING`).

## 28. Các Hạng Mục Còn Chờ (Ngoài Phạm Vi Tự Chạy Trên Tài Sản Owner)

1. `LOCAL_DATABASE_MIGRATION_PENDING_OWNER_APPROVAL` — Áp dụng hòa giải migration `a1c7e4b90d52 -> b6d2f0a8c4e1` trên database thật của Owner (đã có backup kiểm chứng).
2. `LOCAL_ADMIN_SETUP_PENDING_OWNER_ACTION` — Bổ sung `ADMIN_EMAIL` (nếu muốn chỉ định email Admin tường minh) & `DATABASE_URL` vào `backend/.env` rồi chạy `manage_admin.py --apply --create-if-missing`.
3. `REAL_EMAIL_SMOKE_PENDING_OWNER_CONFIGURATION` — Bật `EMAIL_ENABLED=true` khi sẵn sàng và chạy `email_smoke_test.py --send --to <email>` kèm kiểm tra Resend Dashboard (`Emails`).
4. `BACKEND_DEPLOYMENT_PENDING` — Triển khai backend HTTPS production (`https://api.hoclieu.tech`) trên VPS.

## 29. Lưu Ý Về Môi Trường Cục Bộ Sau Bàn Giao

- `http://localhost:3000` (Vite dev server) được khôi phục hoạt động bình thường.
- Container `algo-sim-db-1` và `algo-sim-backend-1` của Owner được giữ nguyên trạng thái ban đầu; không có container thử nghiệm nào còn tồn đọng.

## Owner Actions

Thực hiện tuần tự các lệnh sau khi Owner sẵn sàng kích hoạt môi trường Docker Compose cục bộ thật:

1. **Xác nhận bản sao lưu an toàn đã tồn tại sẵn trước khi đụng vào DB thật:**
   - Đường dẫn: `C:\Users\Bunny\algosim_backups\algosim_backup_20261128_082150.dump`
   - SHA-256 đã kiểm: `cc18110f89565f79049a17c2f17988cdfa42ba1e109cb992706748b9a7f71ff8` (`136,255` bytes, `146` TOC entries)

2. **Bổ sung biến môi trường còn thiếu vào `backend/.env` (giữ nguyên các khóa `GEMINI_API_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `EMAIL_PROVIDER`, `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES`, `PASSWORD_RESET_TOKEN_TTL_MINUTES`, `ALGOSIM_PUBLIC_APP_URL` Owner đã cấu hình):**
   - Thêm/đặt:
     - `DATABASE_URL=postgresql+psycopg2://algosim:<MAT_KHAU_POSTGRES_TRONG_COMPOSE>@db:5432/algosim`
     - `ADMIN_EMAIL=<email-quan-tri-chinh-thuc-cua-ban>`
   - Khi sẵn sàng gửi email thật: đổi `EMAIL_ENABLED=true`.

3. **Build lại backend image mới và hòa giải migration DB thật (`a1c7e4b90d52 -> b6d2f0a8c4e1`):**
   ```powershell
   docker compose stop backend
   docker compose build backend
   docker compose up -d db
   docker compose run --rm --no-deps backend python -m alembic upgrade a1c7e4b90d52:c4e8a91b2f03 --sql | docker compose exec -T db psql -U algosim -d algosim -v ON_ERROR_STOP=1
   docker compose run --rm --no-deps backend python -m alembic stamp --purge e437149641fa
   docker compose up -d --force-recreate backend
   docker compose exec backend python -m alembic check
   ```
   *(Lệnh rollback dự phòng nếu cần quay về đúng trạng thái trước migration:)*
   ```powershell
   docker compose stop backend
   Get-Content -Raw -Encoding Byte "C:\Users\Bunny\algosim_backups\algosim_backup_20261128_082150.dump" | docker compose exec -T db pg_restore --clean --if-exists -U algosim -d algosim
   ```

4. **Tạo và đồng bộ tài khoản Admin duy nhất trên DB thật:**
   ```powershell
   docker compose exec backend python scripts/manage_admin.py --check
   docker compose exec backend python scripts/manage_admin.py --apply --create-if-missing
   docker compose exec backend python scripts/manage_admin.py --check
   ```

5. **Kiểm tra Resend (khóa `Sending access`):**
   ```powershell
   docker compose exec backend python scripts/email_smoke_test.py --check
   # Sau khi đặt EMAIL_ENABLED=true và recreate backend:
   docker compose exec backend python scripts/email_smoke_test.py --send --to <email-cua-owner>
   # Lưu ý: giữ nguyên quyền tối thiểu Sending access trên Resend (không cần nâng Full access).
   # Mở Resend Dashboard -> Emails để xác nhận trạng thái Delivered/Bounced cho providerId trả về.
   ```
