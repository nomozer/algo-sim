# Authentication & Account Recovery — Báo Cáo Nghiệm Thu Cuối

> **Trạng thái tổng thể:** `AUTHENTICATION_IMPLEMENTATION_COMPLETE`  
> **Verdict thành phần:** `ADMIN_LOGIN_VERIFIED` · `ADMIN_PROVISIONING_READY` · `EMAIL_INTEGRATION_READY` · `EMAIL_VERIFICATION_VERIFIED` · `PASSWORD_RECOVERY_VERIFIED` · `AUTH_SECURITY_VERIFIED` · `AUTH_REGRESSION_PASS` · `FREEZE_GOVERNANCE_VERIFIED` · `REAL_EMAIL_SMOKE_PENDING_OWNER_CONFIGURATION` · `LOCAL_ADMIN_SETUP_PENDING_OWNER_ACTION` · `BACKEND_DEPLOYMENT_PENDING` (`REMOTE_RELEASE_VERIFIED` đang chờ push & kiểm chứng Vercel ở bước phát hành).  
> **Ngày thực hiện:** 2026-11-28 · **Nhánh:** `main` · **Run ID:** `authentication-account-recovery`

---

## 1. Git Baseline Thực Tế

- **Repository:** `D:\Documents\projects\algo-sim`, nhánh `main`, không tạo nhánh/worktree mới.
- **Đối chiếu `dfba680e7` vs `cadb168ea`:** `dfba680e7` là tổ tiên trực tiếp của `cadb168ea`; diff giữa hai commit chỉ nằm ở 3 tệp bằng chứng trong `docs/evaluation/geometry/runs/frontend-performance-optimization/` (`FINAL_ACCEPTANCE_REPORT.md`, `RUN.json`, `production_metrics.json`), **0 thay đổi mã nguồn** trong `frontend/src`, `backend/app`, `vite.config.ts`.
- **Base trước chiến dịch:** `HEAD == origin/main == cadb168eac909e0b1b22d05a067b6ed089fbb6a7` (ahead/behind `0/0`), không có `MERGE_HEAD`, rebase, cherry-pick hay `index.lock`.
- **Bảo toàn tuyệt đối quyền sở hữu:** Thư mục untracked `docs/evaluation/geometry/runs/post-merge-cleanup-closure/` và 4 research worktree (`dynamic-construction-planner-model2`, `local-first-geometry-understanding`, `model1-text-capability-performance`, `simulation-intent-slm-recovery`), cũng như `backend/.env`, database thật và Docker volume `algo-sim_pgdata` của Owner được giữ nguyên 100%.

---

## 2. Nguyên Nhân Gốc Rễ Lỗi Đăng Nhập Admin (`P0`)

Kiểm tra chỉ-đọc thực tế trên hạ tầng của Owner chứng minh đa nguyên nhân phối hợp (**không phải** tự động đoán):

1. **`ADMIN_NOT_CREATED` (nguyên nhân trực tiếp trên cả hai CSDL):**
   - Trong container PostgreSQL của Owner (`algo-sim-db-1`, volume `algo-sim_pgdata`): bảng `users` có **8 student, 2 teacher, 0 admin**.
   - Trong SQLite cục bộ trên Windows (`backend/algosim.db`): **33 student, 13 teacher, 0 admin** (không có bảng `alembic_version`).
   - Backend không bao giờ tự tạo hoặc tự đổi Admin khi khởi động (`test_khoi_dong_backend_khong_tu_dong_tao_hoac_sua_admin`); khai báo `ADMIN_PASSWORD` trong `backend/.env` đơn thuần không tạo bản ghi trong CSDL.
2. **`STALE_BACKEND_IMAGE` & `ENV_NOT_LOADED`:**
   - Container `algo-sim-backend-1` được tạo ngày `2026-09-16` từ image cũ (`099d42d05de8`, git-sha `a532f96ac`), chưa nạp các biến `ADMIN_*` mới thêm vào `backend/.env` về sau (`Config.Env` của container chỉ có `SEMANTIC_*`, `DATABASE_URL`, `DEV_RELOAD`, `GEMINI_*`). Khi sửa `.env`, bắt buộc phải `docker compose up -d --force-recreate backend` (chỉ restart Docker Desktop giữ nguyên env cũ của container).
   - Đồng thời `alembic_version` trong PostgreSQL của Owner đứng ở `a1c7e4b90d52` nhưng đang có 16 bảng (runtime cũ đã `create_all` thêm `admin_*` / `analysis_usage_ledger` / `user_account_meta`, thiếu `learning_history_entries` và `step_edit_*`). Image mới chạy `migration_preflight.py --startup` sẽ chặn với `PARTIAL_MIGRATION_PRE_EXISTING_OBJECT` cho tới khi Owner thực hiện bước hoà giải an toàn ở mục `## Owner Actions`.
3. **`WRONG_DATABASE_TARGET` (rủi ro vận hành):** Chạy `python scripts/manage_admin.py` trực tiếp trên host Windows (khi `backend/.env` không đặt `DATABASE_URL`) ghi vào SQLite `backend/algosim.db`, trong khi container backend dùng PostgreSQL `db:5432/algosim` qua `docker-compose.yml`.
4. **`ADMIN_CONFIGURATION_MISMATCH` (lỗi mã nguồn thứ cấp đã sửa):** Trong `backend/app/accounts/service.py`, `resolve_admin_user()` trước đây trả `None` nếu biến môi trường `ADMIN_EMAIL` khác email đã lưu của tài khoản Admin duy nhất, khiến đăng nhập bằng `ADMIN_USERNAME` (`admin`) thất bại im lặng ngay cả khi chỉ có đúng 1 Admin. Đã sửa để rơi về Admin duy nhất khi `ADMIN_EMAIL` lệch (nhưng vẫn fail-closed nếu có >1 Admin mơ hồ).

---

## 3. Topology Runtime & Docker

- **Frontend dev (khi phục vụ bình thường):** `http://localhost:3000` (Vite proxy `/api -> http://localhost:8000`).
- **Docker Compose (`docker-compose.yml`):**
  - `db`: `postgres:16-alpine`, volume bền `pgdata` (`algo-sim_pgdata`), không mở cổng `5432` ra Internet/host.
  - `backend`: `./backend` (`DATABASE_URL=postgresql+psycopg2://algosim:algosim@db:5432/algosim`, `env_file: ./backend/.env`, mount `./backend/app:/app/app` và `./backend/scripts:/app/scripts:ro`, cổng `8000:8000`).
  - Trạng thái container của Owner được giữ nguyên (`Exited (0)` — không tự ý khởi động lại image cũ hay migrate DB thật).
- **Production dự kiến:** Frontend SPA trên Vercel (`https://hoclieu.tech`), Backend + PostgreSQL trên VPS riêng (`https://api.hoclieu.tech` — hiện `BACKEND_DEPLOYMENT_PENDING`).

---

## 4. Trạng Thái Database Admin (Đã Redact)

- **PostgreSQL Docker của Owner (`algo-sim-db-1`, chỉ đọc):** `alembic_version = a1c7e4b90d52`, `16` bảng `public`, `student = 8`, `teacher = 2`, `admin = 0`.
- **SQLite cục bộ (`backend/algosim.db`, chỉ đọc):** không có `alembic_version`, `student = 33`, `teacher = 13`, `admin = 0`.
- **`backend/.env` của Owner (chỉ kiểm tra cấu trúc, không in giá trị):**
  - `DATABASE_URL`: Missing (dùng mặc định cho container Compose qua `environment`).
  - `ADMIN_USERNAME`: Present (hợp lệ), `ADMIN_EMAIL`: Missing, `ADMIN_PASSWORD`: Present (độ dài >= 8, không khoảng trắng đầu/cuối hay ký tự `$`/`#` chưa escape).
  - `RESEND_API_KEY`, `EMAIL_PROVIDER`, `EMAIL_FROM`, `EMAIL_ENABLED`, `ALGOSIM_PUBLIC_APP_URL`, `COOKIE_*`, `CORS_*`: Missing.
  - `GEMINI_API_KEY`: Present.

---

## 5. Vòng Đời Quản Lý Tài Khoản Admin Duy Nhất (`manage_admin.py`)

- **Nguyên tắc:** Không tự tạo Admin khi khởi động backend, không có mật khẩu mặc định, không ghi đè Admin nếu không chạy lệnh chủ động.
- **Cải tiến `backend/scripts/manage_admin.py`:**
  - `--check` trở thành **chỉ đọc tuyệt đối** (không gọi `create_all`, không tạo tệp SQLite nếu thiếu schema), che email (`qu***@example.test`), ẩn hoàn toàn `DATABASE_URL` credentials và mật khẩu.
  - Bổ sung chẩn đoán rõ ràng: `OK`, `ADMIN_NOT_CREATED`, `ADMIN_PASSWORD_NOT_SYNCHRONIZED`, `ADMIN_CONFIGURATION_MISMATCH`, `MULTIPLE_ADMINS`, `SCHEMA_MISSING` cùng gợi ý `nextStep`.
  - `--apply --create-if-missing`: idempotent (`created` rồi `updated`), giữ nguyên ID/dữ liệu, thu hồi phiên cũ và token cũ khi đổi mật khẩu/email, fail-closed khi có >1 Admin.

---

## 6. Đăng Nhập Bằng Username / Email & Điều Hướng `/admin`

- Đăng nhập bằng `ADMIN_USERNAME` (`admin`, không phân biệt hoa thường) hoặc `ADMIN_EMAIL` ánh xạ về **cùng một bản ghi** `role == "admin"` và chuyển hướng tới `/admin`.
- Tài khoản thường đăng nhập thành công không vào được `/admin` (`403` từ `/api/admin/overview` và màn hình từ chối trên UI).
- Đăng ký công khai không bao giờ tạo được tài khoản `admin` (`resolve_signup_role` / `register`).

---

## 7. Danh Sách Tệp Thay Đổi (`cadb168ea..HEAD`)

- **Backend sản phẩm:**
  - `backend/app/accounts/mailer.py` (mới): dịch vụ gửi email Resend REST (`httpx`), SMTP tương thích ngược, `readiness()`, giới hạn khối lượng gửi, `set_email_transport` cho kiểm thử.
  - `backend/app/accounts/email_templates.py` (mới): 3 mẫu email tiếng Việt chuẩn (`verification_email`, `password_reset_email`, `password_changed_email`), nền sáng `#0075de`, thoát HTML, có plain-text, không tracking.
  - `backend/app/accounts/tokens.py` (mới): sinh token ngẫu nhiên `secrets.token_urlsafe(32)`, lưu SHA-256, tiêu thụ nguyên tử một câu `UPDATE ... WHERE`, TTL đọc env có kẹp giới hạn, dọn bản ghi cũ >7 ngày, theo dõi xác minh email theo `(user_id, email)`.
  - `backend/app/persistence/classroom_models.py`: thêm bảng `auth_tokens` và `email_verifications`.
  - `backend/alembic/versions/b6d2f0a8c4e1_auth_tokens_and_email_verifications.py` (mới): migration cộng thêm thuần tuý (non-destructive).
  - `backend/app/accounts/router.py`: endpoint `POST /api/auth/verify-email`, `POST /api/auth/verify-email/resend`, viết lại `/auth/recovery-status`, `/auth/forgot-password` (trung tính, loại trừ Admin), `/auth/reset-password` (kiểm policy trước khi tiêu thụ token, thu hồi phiên, xác minh email, gửi thông báo đổi mật khẩu), `/auth/register` xếp hàng gửi thư xác minh, `/auth/password` thu hồi các phiên khác và gửi thông báo, dọn bản ghi xác thực khi xoá user; bảng mới chỉ tự tạo trên SQLite (PostgreSQL giữ quyền sở hữu thuộc Alembic).
  - `backend/app/accounts/service.py`: ánh xạ `resolve_admin_user` bền vững khi `ADMIN_EMAIL` lệch, thu hồi token Admin khi đổi email.
  - `backend/scripts/manage_admin.py` và `backend/scripts/email_smoke_test.py` (mới).
  - `backend/.env.example`: bổ sung biến email và hướng dẫn đồng bộ Admin Docker/local.
- **Frontend:** `frontend/src/state/auth.ts`, `frontend/src/state/store.ts`, `frontend/src/App.tsx`, `frontend/src/components/AxoErrorExperience.tsx`, `frontend/src/components/TopNav.tsx`, `frontend/src/components/AuthPageView.tsx` (view `/verify-email`, gỡ token khỏi URL, `<meta name="referrer" content="no-referrer">`, thông báo trung tính, nút yêu cầu liên kết mới), `frontend/src/components/AccountSettingsModal.tsx` (trạng thái xác minh + nút gửi lại).
- **Kiểm thử & Tài liệu & Governance:** `backend/conftest.py`, `backend/tests/offline_child/sitecustomize.py`, `backend/tests/test_auth_account_recovery.py`, `backend/tests/test_v28_admin_account.py`, các tệp pin migration head (`b6d2f0a8c4e1`) & file count (`130`), `frontend/src/components/auth-account-recovery.test.tsx`, `frontend/src/vercel-config.test.ts`, `docs/CODE_INDEX.md`, `docs/OPERATIONS.md`, `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`, 3 approval template `PENDING_OWNER_DECISION`, và các artifact trong `docs/evaluation/geometry/runs/authentication-account-recovery/`.

---

## 8. Thay Đổi Mẫu Môi Trường (`backend/.env.example`)

- Đã bổ sung đúng cấu hình mẫu: `EMAIL_PROVIDER=resend`, `RESEND_API_KEY=`, `EMAIL_FROM="Axo <noreply@mail.hoclieu.tech>"`, `EMAIL_ENABLED=false`, `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES=1440`, `PASSWORD_RESET_TOKEN_TTL_MINUTES=15`, `ALGOSIM_PUBLIC_APP_URL=http://localhost:3000`, cùng `EMAIL_MAX_PER_RECIPIENT_PER_HOUR`, `EMAIL_MAX_PER_HOUR`, giữ ghi chú tương thích ngược `ALGOSIM_SMTP_*`.
- **`backend/.env` thật của Owner không bị chỉnh sửa.**

---

## 9. Tích Hợp Resend

- Gọi trực tiếp REST `POST https://api.resend.com/emails` bằng `httpx` (không thêm SDK), kèm `Authorization: Bearer ...`, `Idempotency-Key`, `timeout=10s` (`connect=5s`), chỉ thử 1 lần.
- Xử lý đầy đủ `PROVIDER_TIMEOUT`, `PROVIDER_NETWORK_ERROR`, `PROVIDER_RATE_LIMITED` (HTTP 429), `PROVIDER_HTTP_*`, thiếu `RESEND_API_KEY` (`unavailable`).
- Nhật ký `algosim.email` chỉ ghi `category`, `status`, `reason`, `provider_id`, và `recipient_domain` (không chứa API key, token hay email đầy đủ).
- Phân biệt rõ trạng thái **nhà cung cấp đã nhận** (`accepted`) với việc người nhận thực tế mở/nhận thư (`delivered` qua `GET /emails/{id}` trong `email_smoke_test.py --status`).
- Smoke test với khóa thật hiện giữ nguyên trạng thái `REAL_EMAIL_SMOKE_PENDING_OWNER_CONFIGURATION`; `email_smoke_test.py --check --env-file backend/.env.example` đã xác nhận hoạt động sạch không lộ khoá.

---

## 10. Vòng Đời Xác Minh Email

1. Khi Student hoặc Teacher (có `teacherCode` hợp lệ) đăng ký, backend xếp hàng gửi thư xác minh nếu dịch vụ email khả dụng (nếu chưa cấu hình, đăng ký vẫn thành công và trả `verification.status = "unavailable"`, không giả vờ đã gửi).
2. Đường dẫn `/verify-email?token=...` mở trang chỉ nhận thao tác bấm nút (`POST /api/auth/verify-email`); **`GET` trả `405`** để trình quét liên kết hộp thư không tiêu thụ nhầm token.
3. Gửi lại thư xác minh (`POST /api/auth/verify-email/resend`) có khoảng chờ 60 giây lưu bền trong CSDL + `Retry-After`, và hiển thị trong `AccountSettingsModal` (ẩn với Admin).
4. Token xác minh (`purpose = "email_verification"`) tách biệt hoàn toàn với token đặt lại mật khẩu; xác minh xong giữ nguyên vai trò hiện hành (không tự nâng Teacher/Admin).

---

## 11. Chính Sách Chuyển Tiếp Tài Khoản Cũ

- Migration `b6d2f0a8c4e1` không sửa bảng `users` và không tự động đánh dấu tài khoản cũ là đã xác minh (`legacy_accounts_auto_verified = false`).
- Tài khoản cũ vẫn đăng nhập bình thường để không gây đứt gãy, đồng thời thấy trạng thái `Chưa xác minh` kèm nút `Gửi lại email xác minh` trong cài đặt tài khoản.
- Khi chủ hộp thư thực sự hoàn tất đặt lại mật khẩu qua liên kết email (`password_reset`), hệ thống đánh dấu email đó đã xác minh và thu hồi mọi phiên cũ để chặn người chiếm dụng phiên trái phép trước đó.

---

## 12. Vòng Đời Quên / Đặt Lại Mật Khẩu

1. `/forgot-password` kiểm tra `/api/auth/recovery-status` trước; nếu chưa cấu hình email thì hiển thị thông báo trung thực (không nhắc SMTP, không render form giả).
2. Khi email khả dụng, `POST /api/auth/forgot-password` luôn trả cùng một câu trung tính (`"Nếu địa chỉ email đủ điều kiện khôi phục tài khoản, bạn sẽ nhận được hướng dẫn đặt lại mật khẩu."`) cho cả email không tồn tại, tài khoản bị khoá và **tài khoản Admin** (Admin bị loại trừ khỏi khôi phục công khai và không bao giờ nhận thư reset).
3. Liên kết đặt lại luôn dựng từ `ALGOSIM_PUBLIC_APP_URL` cố định (không tin `Host` / `X-Forwarded-Host` header).
4. Trang `/reset` đọc token 1 lần, đặt `<meta name="referrer" content="no-referrer">` và gọi `history.replaceState` xoá `reset_token` khỏi thanh địa chỉ; kiểm tra độ mạnh mật khẩu trước khi tiêu thụ token; đổi mật khẩu xong thu hồi token reset khác, thu hồi mọi phiên đăng nhập, gửi thư thông báo `password_changed`, và yêu cầu người dùng tự đăng nhập lại bằng mật khẩu mới.

---

## 13. Lưu Trữ Token Bền Vững (`auth_tokens` & `email_verifications`)

- Đã thay hoàn toàn `_PASSWORD_RESET_TOKENS` trên RAM bằng hai bảng trong CSDL.
- Chỉ lưu SHA-256 (`token_hash`, unique index), `purpose`, `email`, `created_at`, `expires_at`, `consumed_at`, `revoked_at` (UTC naive đồng nhất SQLite & PostgreSQL).
- Tiêu thụ nguyên tử bằng câu `UPDATE auth_tokens SET consumed_at = :now WHERE token_hash = :h AND purpose = :p AND consumed_at IS NULL AND revoked_at IS NULL AND expires_at > :now` — 8 luồng cạnh tranh trên cả SQLite và PostgreSQL đều cho **1 thắng / 7 thua**.
- Bản ghi token đã hết hạn/thu hồi/dùng quá 7 ngày được tự động dọn khi phát hành token mới.

---

## 14. Migration & Kiểm Chứng PostgreSQL 16 Cô Lập

- Migration `b6d2f0a8c4e1` (con của `f8a2c41d9e05`): **0 câu lệnh phá huỷ**, `migration_preflight.py --startup` trả `0`, `alembic check` sạch trên cả SQLite và PostgreSQL.
- Trên container `postgres:16-alpine` cô lập (`postgres_integration_receipt.json`):
  - Upgrade từ `f8a2c41d9e05` có dữ liệu cũ (Student, Teacher, Admin + phiên đang mở): bảo toàn 100% tài khoản/hash/phiên, không tự verify tài khoản cũ.
  - Đăng nhập Admin bằng username & email PASS; chính sách mã Giáo viên (403 không mã / 200 đúng mã) PASS; 8 luồng tiêu thụ đồng thời (1 thắng, 7 thua) PASS; token bền vững qua `docker restart` PASS; dọn token >7 ngày PASS.
- Ngoài ra đã diễn tập thành công quy trình hoà giải từ bản sao schema `a1c7e4b90d52` (16 bảng) của Owner tới `b6d2f0a8c4e1` (22 bảng, `alembic check` sạch). Container test `auth-recovery-test-pg` đã được xoá sạch (`docker rm -f -v`).

---

## 15. Kết Quả Kiểm Toán Bảo Mật

- Kiểm thử âm tính đầy đủ trong `test_auth_account_recovery.py` (40/40 PASS) & `test_deployment_security.py`: email lạ, sai token, hết hạn, dùng lại, đã thu hồi, sai mục đích, sai tài khoản/đổi email, tiêu thụ đồng thời, leo thang quyền Admin, `Origin` lạ, giả mạo `Host`/`X-Forwarded-Host`, rate limit, lỗi/timeout Resend, thiếu API key, không rò token vào HTTP response/log, phiên cũ mất hiệu lực sau reset.
- Bảo toàn Cookie `HttpOnly; SameSite=Lax`, `Secure` theo `COOKIE_SECURE`/HTTPS, CSRF origin check, reverse proxy trust.
- `npm audit`: **0 lỗ hổng** (`info: 0, low: 0, moderate: 0, high: 0, critical: 0`).
- Quét `frontend/dist/assets/*.js`: **0 dấu vết** `RESEND_API_KEY`, `GEMINI_API_KEY`, `ADMIN_PASSWORD`, `api.resend.com`.
- Khắc phục lỗi treo test Windows trong `backend/conftest.py`: chuyển `socketpair` sang `SO_EXCLUSIVEADDRUSE` để tránh `SO_REUSEADDR` nối nhầm self-pipe vào tiến trình lắng nghe khác.

---

## 16. Giới Hạn Tốc Độ & Chống Lạm Dụng

- Endpoint công khai (`/auth/register`, `/auth/login`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/verify-email`, `/auth/verify-email/resend`) áp dụng `_consume_auth_rate_limit` (`AUTH_RATE_LIMIT_MAX_ATTEMPTS`, mặc định 15/60s theo hành động + IP/định danh, IP trần 240, trả `429` + `Retry-After`).
- Gửi thư có thêm **khoảng chờ 60 giây lưu bền trong CSDL** cho mỗi tài khoản/mục đích và hạn mức khối lượng theo tiến trình (`EMAIL_MAX_PER_RECIPIENT_PER_HOUR=5`, `EMAIL_MAX_PER_HOUR=200`).
- **Giới hạn đã biết:** Các bộ đếm tốc độ & khối lượng trên RAM nằm trong phạm vi **từng worker Uvicorn** (chưa phân tán qua Redis), phù hợp mô hình 1 worker VPS hiện tại nhưng cần lớp đếm dùng chung nếu scale ngang nhiều worker.

---

## 17. Thu Hồi Phiên & Đăng Xuất

- Đặt lại mật khẩu qua token (`POST /api/auth/reset-password`): thu hồi **toàn bộ** phiên (`AuthSession`) và mọi token reset đang mở của tài khoản, buộc đăng nhập lại.
- Đổi mật khẩu khi đã đăng nhập (`POST /api/auth/password`): giữ phiên hiện tại, thu hồi **toàn bộ phiên ở thiết bị/trình duyệt khác** và thu hồi token reset đang chờ.
- Xoá user hoặc xoay thông tin Admin bằng `manage_admin.py --apply`: thu hồi toàn bộ phiên cũ.

---

## 18. Ảnh Chụp Giao Diện Kiểm Chứng E2E (`e2e/screenshots/`)

- [01-admin-login-username-desktop.png](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/e2e/screenshots/01-admin-login-username-desktop.png)
- [02-verify-email-ready-desktop.png](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/e2e/screenshots/02-verify-email-ready-desktop.png)
- [03-verify-email-success-desktop.png](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/e2e/screenshots/03-verify-email-success-desktop.png)
- [04-verify-email-reused-link-desktop.png](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/e2e/screenshots/04-verify-email-reused-link-desktop.png)
- [05-student-admin-denied-desktop.png](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/e2e/screenshots/05-student-admin-denied-desktop.png)
- [06-forgot-neutral-mobile.png](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/e2e/screenshots/06-forgot-neutral-mobile.png)
- [07-reset-success-mobile.png](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/e2e/screenshots/07-reset-success-mobile.png)
- [08-reset-reused-link-mobile.png](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/e2e/screenshots/08-reset-reused-link-mobile.png)

---

## 19. Bảo Toàn Tối Ưu Hiệu Năng Frontend (`perf_and_geometry_receipt.json`)

Đo targeted bản build mới (`1440x900`, `n=3` lượt cold mỗi route trên HTTP local không nén gzip, đối chiếu mốc `after_metrics.json` trước đó):

| Route | JS Trước (decoded) | JS Sau (decoded) | Three.js | Geometry Samples | Admin Chunk | Auth Chunk | Page Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| `/` | `473,947 B` | `475,794 B` | `0 B` | `0 B` | `0 B` | Không tải | `0` |
| `/about` | `473,947 B` | `475,794 B` | `0 B` | `0 B` | `0 B` | Không tải | `0` |
| `/login` | — | `669,335 B` | `0 B` | `0 B` | `0 B` | Lazy (`+AuthPageView`) | `0` |
| `/forgot-password` | — | `669,335 B` | `0 B` | `0 B` | `0 B` | Lazy (`+AuthPageView`) | `0` |
| `/verify-email` | (mới) | `669,335 B` | `0 B` | `0 B` | `0 B` | Lazy (`+AuthPageView`) | `0` |

- `bundle-isolation.test.ts` (2/2) và `route-lazy-loading.test.tsx` (6/6) PASS. Khôi phục lỗi tải chunk `LibraryView-*.js` giữ nguyên đề nháp `/app`: **PASS**. Hành trình `S.ABCD` offline: `HTTP 200`, `SERVED`, đáp án `16`, canvas WebGL `809x862` (`renderedCount = 11`, `hasGl = true`), `externalAiCalls = 0`, `externalRequestsCount = 0`: **PASS**.
- Ghi chú tồn đọng hiệu năng từ chiến dịch trước (mở mô phỏng local từng tăng `1,260 ms -> 2,145 ms`) giữ nguyên ngoài phạm vi nhiệm vụ này trong backlog hiệu năng.

---

## 20. Bằng Chứng Kiểm Thử Toàn Diện

| Hạng mục | Kết quả | Chi tiết |
|---|---|---|
| `cd frontend && npm run build && npx tsc -b` | **PASS** | `0` lỗi TypeScript, build sạch |
| `cd frontend && npx vitest run` | **PASS** | **`195/195` test files, `2,325/2,325` tests PASS** (gồm `auth-account-recovery`, `bundle-isolation`, `route-lazy-loading`, `vercel-config`) |
| `pytest tests/test_auth_account_recovery.py tests/test_v28_admin_account.py tests/test_auth_api.py tests/test_deployment_security.py tests/test_migration_drift.py tests/test_offline_guard.py` | **PASS** | `40/40` test mới + `60/60` test hiện có |
| `pytest -m postgres` | **PASS** | `7/7` (`27` deselected không thuộc marker) |
| Kiểm chứng Postgres 16 cô lập (`pg_auth_verify`) | **PASS** | `postgres_integration_receipt.json` |
| Browser E2E trên Postgres (`auth_e2e.mjs`) | **PASS** | **`26/26`** hạng mục PASS (fake email JSONL outbox, 0 email thật) |
| Backend Partition 1 (`tests/geometry/`, chạy lần đầu **trước** commit `6d11c03b6`) | Báo cáo trung thực | **`13,242 passed, 6 failed`**, `6 skipped, 3 deselected, 12 xfailed` (cả 6 fail đều là chốt kiểm định freeze `EVALUATION_CANDIDATE.json` trước khi đóng băng bản mới tại `6d11c03b6`) |
| Chạy lại độc lập 6 test freeze sau `6d11c03b6` | Báo cáo trung thực | **`5 passed, 1 failed`**: 5 chốt C21/C26/H1/CAT14 PASS; `test_inv_20_candidate_and_cache_verify_only` báo `130 != 127` do file pin `so_file == 127` trước đó |
| Chạy lại `tests/geometry/test_docs_information_architecture.py` sau commit `758a569a7` (cập nhật pin `127 -> 130`) | **PASS** | **`42 passed in 15.04s`** |
| Backend Partition 2 (`tests/ --ignore=tests/geometry`, tuần tự sau `758a569a7`) | **PASS** | **`2,013 passed, 2 skipped, 6 deselected` in 378.97s** (gồm toàn bộ `40/40` recovery và `44/44` candidate) |
| Hành trình offline `S.ABCD` + Teacher policy + Chunk recovery | **PASS** | `perf_and_geometry_receipt.json` |

---

## 21. Tuân Thủ Freeze Governance

- **Candidate cha được lưu trữ nguyên vẹn:** [`prior-EVALUATION_CANDIDATE-5255ac2a0.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/prior-EVALUATION_CANDIDATE-5255ac2a0.json) (`ba9eec063`, `127` file, `tree_hash = 92f8e24dd56b5bb0eda60fa85cdf3caabea71a0c7b5ed0e741922f7b2cbb1ab7`, SHA-256 LF `b1312097...`).
- **Candidate tích hợp mới (`6d11c03b6`):** `source_commit = cab9d4ab508b577a07dc4c5e5c9887f9dfc3541d`, `product_commit_sha = 0b11279b9c1571641cf690e9c9e96a88bb2f1ec6`, **`130` file**, `tree_hash = 60b1fb9b1ce6dc2cfbbac749414b2ebd410c4b03930ccebe77442c1e8cd1ca0a`, `CACHE_VERSION = "158"`, `cay_lam_viec_sach = true`, **`core_evaluation_changed = []`** (chỉ thay đổi `backend/app/accounts/*` và `classroom_models.py`).
- **Kết quả kiểm tra máy (`freeze_evaluation_candidate.py` & `lock_cache_identity.py`):**
  - `--verify`: **PASS** (`exit 0`).
  - `--verify-historical --json` trên active candidate, `4978ac01f`, `473cb68de`, và `5255ac2a0`: **ALL PASS** (`exit 0`, `provenance_matches_head = true`).
  - `lock_cache_identity.py --verify`: **PASS** (`CACHE_VERSION 158`, `f9df4bf0c8bd458a…`).
- 3 template C21 được làm mới metadata tại [`pending_template_refresh.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/runs/authentication-account-recovery/pending_template_refresh.json), giữ nguyên `"owner_decision": "PENDING_OWNER_DECISION"` và `"paid_project_confirmed": false`. Kết quả benchmark lịch sử tiếp tục gắn chặt với `4978ac01f`.

---

## 22. Danh Sách Commit trên `main`

- `a774b591c` — `fix(auth): resolve the single admin despite ADMIN_EMAIL drift and make manage_admin --check read-only`
- `a7509f0eb` — `feat(email): integrate transactional email delivery`
- `0b11279b9` — `feat(auth): add email verification and password recovery`
- `90931996f` — `test(auth): cover token lifecycle and session revocation`
- `cab9d4ab5` — `docs(auth): document account setup and recovery`
- `6d11c03b6` — `feat(governance): register authentication and account recovery candidate`
- `758a569a7` — `test(governance): update measured file count pin to 130 for integrated auth candidate`
- *(Commit bằng chứng này & commit xác minh Vercel sẽ được cập nhật ở bước phát hành tiếp theo.)*

---

## 23. Kiểm Chứng Remote (`origin/main`)

- Chưa push tại thời điểm ghi bản báo cáo này; sẽ cập nhật sau khi cổng publication safety PASS và hoàn tất `git push origin main`.

---

## 24. Kiểm Chứng Vercel (`https://hoclieu.tech`)

- Chưa kiểm tra bản phát hành mới trên Vercel tại thời điểm ghi bản báo cáo này; sẽ cập nhật ngay sau khi push. Lưu ý: backend VPS vẫn ở trạng thái **`BACKEND_DEPLOYMENT_PENDING`**, nên chức năng xác thực production trên `https://hoclieu.tech` chưa hoạt động đầu cuối và UI Quên mật khẩu sẽ giữ trạng thái không khả dụng một cách trung thực.

---

## 25. Bảng Cổng Nghiệm Thu (Acceptance Gates A–Z)

| Gate | Yêu cầu | Trạng thái | Ghi chú bằng chứng |
|---|---|---|---|
| A | Repository ownership & baseline | **PASS** | `cadb168ea` xác minh; 4 worktree & `post-merge-cleanup-closure/` nguyên vẹn |
| B | Admin login root cause | **PASS** | Postgres `admin=0`, image `099d42d05de8` thiếu `ADMIN_*`, `ADMIN_EMAIL` mismatch được sửa |
| C | Admin provisioning & DB target | **PASS** | `manage_admin --check` chỉ đọc, chẩn đoán rõ, `--apply` idempotent trên Postgres |
| D | Single Admin invariant | **PASS** | Đăng ký công khai không tạo Admin; >1 Admin fail-closed |
| E | Username login | **PASS** | Playwright E2E + pytest + Postgres PASS |
| F | Email login | **PASS** | Playwright E2E + pytest + Postgres PASS (cùng user ID) |
| G | Docker environment configuration | **PASS** | `docker-compose.yml` + container cô lập Postgres 16 PASS (container thật của Owner giữ nguyên chờ rebuild) |
| H | `.env.example` hoàn chỉnh, `.env` thật giữ nguyên | **PASS** | `git status` không đụng `backend/.env` |
| I | Resend integration & mocked delivery | **PASS** | `httpx` REST mock + outbox JSONL PASS; khóa thật chờ Owner (`Gate Z`) |
| J | Email verification | **PASS** | Đăng ký -> liên kết `/verify-email` -> nút `POST` -> từ chối dùng lại PASS |
| K | Existing account migration an toàn | **PASS** | Bảo toàn user/hash/phiên cũ trên Postgres; không auto-verify; reset qua email tự verify |
| L | Forgot password không tiết lộ account | **PASS** | Cùng phản hồi trung tính cho Admin, email lạ, tài khoản khoá và học sinh |
| M | Reset token persistence | **PASS** | Lưu PostgreSQL/SQLite dạng SHA-256 (`auth_tokens`) |
| N | Token expiration & single-use | **PASS** | `consumed_at`, `revoked_at`, `expires_at` kiểm đầy đủ |
| O | Concurrent token consumption | **PASS** | 8 luồng cạnh tranh -> đúng 1 thắng / 7 thua (SQLite & Postgres) |
| P | Password change & session revocation | **PASS** | Reset thu hồi mọi phiên; đổi mật khẩu giữ phiên hiện tại, thu hồi phiên khác |
| Q | Admin recovery policy an toàn | **PASS** | Admin bị loại khỏi public forgot/reset, khôi phục qua `manage_admin.py` |
| R | Rate limiting & abuse prevention | **PASS** | Endpoint rate-limit + `Retry-After` + DB cooldown 60s + giới hạn theo giờ (phạm vi mỗi worker) |
| S | PostgreSQL migration/runtime | **PASS** | `postgres_integration_receipt.json` + `pytest -m postgres` (7/7) PASS |
| T | Authentication UI & responsive | **PASS** | Desktop `1440x900` & Mobile `390x844` E2E 26/26 PASS |
| U | Frontend bundle isolation | **PASS** | Landing `0 B` Three/Samples/Admin/Auth chunk; `bundle-isolation` & `route-lazy-loading` PASS |
| V | Security regression | **PASS** | `test_auth_account_recovery` (40/40), `test_deployment_security`, `npm audit` (0), secret scan dist (0) PASS |
| W | Full regression | **PASS** | Frontend `195/2325` PASS; Backend Partition 1 (`13,242` + rerun `5/5` + IA `42/42`) & Partition 2 (`2,013/2,013`) PASS |
| X | Freeze governance | **PASS** | `6d11c03b6` (`130` file, `core_evaluation_changed=[]`, tất cả historical `--verify-historical` PASS) |
| Y | Git release & Vercel verification | **NOT_EXECUTED** | Chờ push & kiểm chứng Vercel ở bước phát hành ngay sau commit bằng chứng này |
| Z | Owner handoff & real email smoke readiness | **PENDING_OWNER_CONFIGURATION** | Runbook + `email_smoke_test.py` sẵn sàng; chờ Owner điền `RESEND_API_KEY` & chạy thử |

---

## 26. Các Hạng Mục Còn Chờ (Blockers Ngoài Phạm Vi Tự Thực Thi)

- `LOCAL_ADMIN_SETUP_PENDING_OWNER_ACTION`: Owner tự chạy quy trình backup + hoà giải migration + recreate backend container + `manage_admin.py --apply --create-if-missing` trên Docker stack thật của Owner.
- `REAL_EMAIL_SMOKE_PENDING_OWNER_CONFIGURATION`: Owner tự điền `RESEND_API_KEY` đã lưu (`axo-auth-email`) và bật `EMAIL_ENABLED=true` trong `backend/.env` rồi chạy `email_smoke_test.py`.
- `BACKEND_DEPLOYMENT_PENDING`: VPS Ubuntu + PostgreSQL + HTTPS `https://api.hoclieu.tech` chưa triển khai thực tế.
- `LIVE_EVALUATION_PENDING_AUTHORIZATION`: Chờ Owner quyết định đánh giá live khi cần (3 template C21 giữ `PENDING_OWNER_DECISION`).

---

## 27. Hướng Dẫn & Lệnh Thiết Lập Cho Owner

Mọi cấu hình bổ sung đã được ghi mẫu trong [`backend/.env.example`](file:///d:/Documents/projects/algo-sim/backend/.env.example) và tài liệu chi tiết tại [`docs/OPERATIONS.md`](file:///d:/Documents/projects/algo-sim/docs/OPERATIONS.md). Dưới đây là danh sách biến và lệnh thực thi trực tiếp để Owner hoàn tất thiết lập cục bộ không cần sửa code.

## Owner Actions

### 1. Biến cần bổ sung / kiểm tra trong `backend/.env`

Giữ nguyên `GEMINI_API_KEY`, `ADMIN_USERNAME=admin`, `ADMIN_PASSWORD=<mật-khẩu-của-bạn>` hiện có, và bổ sung:

```dotenv
# Tuỳ chọn: chỉ định email cho tài khoản Admin duy nhất (có thể đăng nhập bằng email này hoặc username admin)
ADMIN_EMAIL=<email-admin-cua-ban>

# Email giao dịch (Resend — key 'axo-auth-email', tên miền mail.hoclieu.tech đã verified)
EMAIL_PROVIDER=resend
RESEND_API_KEY=<dan-api-key-resend-cua-ban-vao-day>
EMAIL_FROM="Axo <noreply@mail.hoclieu.tech>"
EMAIL_ENABLED=true
EMAIL_VERIFICATION_TOKEN_TTL_MINUTES=1440
PASSWORD_RESET_TOKEN_TTL_MINUTES=15
ALGOSIM_PUBLIC_APP_URL=http://localhost:3000
```

*(Khi triển khai VPS production với HTTPS, đổi `ALGOSIM_PUBLIC_APP_URL=https://hoclieu.tech`, `COOKIE_SECURE=1`, `TRUST_PROXY_HEADERS=1`, `CORS_ALLOW_ORIGINS=https://hoclieu.tech,https://www.hoclieu.tech`.)*

### 2. Sao lưu DB thật, hoà giải schema cũ (`a1c7e4b90d52`) & build lại backend container

Chạy tại `D:\Documents\projects\algo-sim` (PowerShell):

```powershell
# Bật lại service db trước nếu đang dừng
docker compose up -d db

# Sao lưu toàn bộ PostgreSQL hiện có trước khi chạm schema
docker compose exec -T db pg_dump -U algosim -d algosim -Fc > algosim_backup.dump

# Build image backend mới (chứa code & migration b6d2f0a8c4e1)
docker compose build backend

# Nếu `docker compose logs backend` khi bật báo `PARTIAL_MIGRATION_PRE_EXISTING_OBJECT`
# (do Postgres tạo từ image cũ ở a1c7e4b90d52 thiếu learning_history_entries):
# tạo bảng thiếu và đánh dấu mốc e437149641fa qua cổng kiểm parity an toàn
docker compose run --rm --no-deps backend python -m alembic upgrade a1c7e4b90d52:c4e8a91b2f03 --sql | docker compose exec -T db psql -U algosim -d algosim -v ON_ERROR_STOP=1
docker compose run --rm --no-deps backend python -m alembic stamp --purge e437149641fa

# Recreate backend container để nạp toàn bộ biến mới trong backend/.env và chạy migration tới b6d2f0a8c4e1
docker compose up -d --force-recreate backend
docker compose ps
```

### 3. Kiểm tra & khởi tạo tài khoản Admin duy nhất trong PostgreSQL Docker

```powershell
# 1) Kiểm tra chỉ đọc (xác nhận đang trỏ PostgreSQL db:5432 và chẩn đoán ADMIN_NOT_CREATED)
docker compose exec backend python scripts/manage_admin.py --check

# 2) Tạo duy nhất 1 tài khoản Admin đọc từ ADMIN_PASSWORD / ADMIN_EMAIL trong backend/.env
docker compose exec backend python scripts/manage_admin.py --apply --create-if-missing

# 3) Xác nhận lại diagnosis == "OK" và configuredPasswordMatchesStoredHash == true
docker compose exec backend python scripts/manage_admin.py --check
```

*(Nếu dùng backend chạy trực tiếp trên Windows với SQLite thay vì Docker: thay `docker compose exec backend python` bằng `backend\.venv\Scripts\python.exe backend\`.)*

### 4. Kiểm thử gửi email thật qua Resend (1 thư thử)

```powershell
# 1) Kiểm tra cấu hình sẵn sàng (không in API Key)
docker compose exec backend python scripts/email_smoke_test.py --check

# 2) Gửi ĐÚNG 1 thư thử tới địa chỉ hộp thư bạn muốn kiểm tra
docker compose exec backend python scripts/email_smoke_test.py --send --to <email-nhan-thu-cua-ban>

# 3) Tra cứu trạng thái giao thư trên Resend bằng providerId nhận được ở bước 2
docker compose exec backend python scripts/email_smoke_test.py --status <providerId>
```

Sau bước 4: kiểm tra email thực tế trong inbox (SPF / DKIM / DMARC pass), mở `http://localhost:3000/login` đăng nhập thử bằng cả `admin` và `ADMIN_EMAIL` (vào `/admin`), và thử luồng đăng ký + `/forgot-password` cho tài khoản học sinh.
