# Báo cáo Nghiệm thu Cuối cùng — Admin UI & Functional Closure

> **Task Slug:** `admin-ui-functional-closure`  
> **Ngày thực hiện:** `2026-11-28`  
> **Nhánh:** `main`  
> **Phạm vi:** Đóng phạm vi phát triển giao diện & chức năng quản trị (Admin) và tinh chỉnh cuối cùng cho Footer, đối soát bằng chứng từ đợt `local-activation-admin-refinement`, khắc phục tài liệu rollback PostgreSQL trên Windows, kiểm thử toàn diện và xác minh sau phát hành để sẵn sàng chuyển sang giai đoạn **Backend Performance**.

---

## 1. Tóm tắt điều hành (Executive Summary)

Nhiệm vụ **Admin UI & Functional Closure** đã hoàn tất toàn bộ các hạng mục kỹ thuật, giao diện, chức năng, đối soát bằng chứng và quản trị đóng băng (`Freeze Governance`) mà không thay đổi kiến trúc xác thực, không làm suy giảm tối ưu hiệu năng frontend, và không đụng chạm dữ liệu/container thật của Owner:

- **Đối soát bằng chứng (§3):** Đã xác minh nguyên nhân `csvAuditStatus: 404` ở đợt trước là do script E2E gọi nhầm `/api/admin/export/audit` (thiếu `-logs`) trong khi nút `#btn-admin-export-audit` gọi đúng `/api/admin/export/audit-logs` (`HTTP 200`); xác minh Docker provenance bằng image nướng mới `algo-sim-backend:closure-verify` (`sha256:3a05302ef580...`, 0 bind mount); phân loại rõ taxonomy telemetry Admin và xác nhận `/api/*` 404 trên `hoclieu.tech` là do `BACKEND_DEPLOYMENT_PENDING`.
- **Tinh gọn Admin UI & chức năng (§4–§13):** Header giữ đúng 2 nút không viền (`[Bell]` và `[Avatar ▾]`, gỡ `#btn-admin-refresh`); Sidebar giữ đúng 4 mục điều hướng quản trị (`Tổng quan`, `Tài khoản`, `Thống kê`, `Nhật ký quản trị`); di chuyển `Về không gian học` vào menu Avatar (điều hướng đúng `/app`, bảo toàn phiên & bản nháp); Tổng quan rút gọn 6 → **4 thẻ KPI** với số liệu thực tế từ máy chủ (gỡ `4–10 req/phút` và các badge trang trí, ưu tiên bảng duyệt Giáo viên lên đầu trên di động); Tài khoản gộp cột hạn mức thành `Sử dụng hôm nay`, bỏ chữ lặp `"Chưa đo token"`, bố cục gọn trên di động không cuộn ngang; Phân trang tối giản (`1–10 trên 15 tài khoản`, `10 / trang ▾`, `‹ 1 / 2 ›`); Thống kê nâng cấp lên **4 KPI** (nhận `Token tiêu thụ (7 ngày)` và gỡ badge gây hiểu nhầm `"Kiểm chứng tất định"`) cùng biểu đồ **3 chuỗi cột** (`Xử lý thành công`, `Từ chối an toàn`, `Lỗi xử lý`) khớp 100% bảng chi tiết; Cài đặt hệ thống hiển thị thêm trạng thái chỉ đọc của Model AI, Resend và PostgreSQL (không lộ bí mật).
- **Footer (§14):** Bỏ lặp thương hiệu (`© Hình học không gian 3D` cạnh logo `Axo`), Việt hóa `Workspace` → `không gian học tập`, và căn lưới 2×2 cân đối tại `320px`.
- **Runbook Rollback (§15):** Bổ sung quy trình khôi phục PostgreSQL an toàn bằng `docker compose cp` + đối chiếu SHA-256 + `pg_restore` vào CSDL sạch tại [`docs/OPERATIONS.md`](../../../OPERATIONS.md), cảnh báo rõ không dùng PowerShell `Get-Content -Raw -Encoding Byte | docker compose exec`.
- **Kiểm chứng & Đóng băng:** Frontend `196/196` file (`2.329/2.329` test PASS), Backend `15.267` test duy nhất PASS (`0` fail, không đếm trùng), Playwright E2E + `21` cặp ảnh BEFORE/AFTER sạch toast (`0` console/page/network error, `0px` tràn ngang trên cả 7 độ phân giải), và Integrated Candidate mới `9385d4965` (`measured_system = e332983ec2e7858c...`, `CACHE_VERSION = 158`) đã đóng băng sạch qua `freeze_evaluation_candidate.py --verify` và `--verify-historical --json`.

---

## 2. Trạng thái Baseline & Môi trường ban đầu

- **Baseline commit trước nhiệm vụ:** `9a729e2c795553905d863462acb827274ffa26fd` (`HEAD == origin/main`), 0 git lock (`index.lock`, `MERGE_HEAD`, `REBASE_HEAD`).
- **Tài nguyên của Owner được giữ nguyên trạng 100%:**
  - Bản sao lưu CSDL: `C:\Users\Bunny\algosim_backups\algosim_backup_20261128_082150.dump` (`136.255` bytes, `SHA256 = cc18110f89565f79049a17c2f17988cdfa42ba1e109cb992706748b9a7f71ff8`).
  - Container & volume gốc: `algo-sim-backend-1` (`Exited`), `algo-sim-db-1` (`Exited`), volume `algo-sim_pgdata`, tệp `backend/.env`, `backend/algosim.db`.
  - 4 worktree dưới `.superpowers/worktrees/` và thư mục untracked `docs/evaluation/geometry/runs/post-merge-cleanup-closure/`.
- **Môi trường kiểm thử cô lập:** Mạng `closure-net`, PostgreSQL 16 `closure-pg` (`127.0.0.1:47432`, CSDL `admin_closure_db`, migration `b6d2f0a8c4e1`), backend nướng `algo-sim-backend:closure-verify` (`ALLOW_LIVE_AI=0`, `EMAIL_ENABLED=false`, 0 bind mount), dữ liệu giả lập tất định (`15` tài khoản, `76` bản ghi telemetry 7 ngày gồm `succeeded`/`refused`/`failed`/`cached`, `4` bản ghi audit log). Toàn bộ container/mạng/image tạm `closure-*` đã dọn sạch sau kiểm thử.

---

## 3. Đối soát bằng chứng từ `local-activation-admin-refinement`

1. **Xuất CSV Nhật ký quản trị (`csvAuditStatus: 404` vs `200` thật):**
   - Trong `local-activation-admin-refinement`, script đo trước đó gọi nhầm đường dẫn `/api/admin/export/audit` (thiếu `-logs`) dẫn tới `404` trong receipt.
   - Mã sản phẩm thật tại `AdminWorkspaceView.tsx` (`#btn-admin-export-audit`) và `backend/app/accounts/router.py` định nghĩa đúng tuyến `GET /api/admin/export/audit-logs`.
   - Đã kiểm chứng trực tiếp bằng thao tác bấm nút `#btn-admin-export-audit` trong Chromium thật (`e2e_closure_receipt.json`): `HTTP 200`, `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="axo-nhat-ky-quan-tri-20261128.csv"`, UTF-8 BOM + tiếng Việt chuẩn + vô hiệu hóa công thức spreadsheet (`'=SUM(A1:B2)`, `'+cmd|...`).
2. **Nguồn gốc Docker Image (Provenance):**
   - Đợt trước giữ lại image digest build từ commit `7a9dc97bc`.
   - Đợt này build image nướng mới `algo-sim-backend:closure-verify` (`sha256:3a05302ef580f0b6fcab361f3a694758556c4ce48bceae655a58f4af39696421`, `473.574.834` bytes, `REQUIREMENTS_SHA256 = 72615aebb69ab948176ca036d3ba6d5f11632406af3abb4bb067754cc0f5cdbd`, `bindMounts = []`), ghi rõ tại [`docker_provenance_receipt.json`](docker_provenance_receipt.json).
3. **Phân loại Telemetry quản trị:**
   - Bảng `admin_analysis_telemetry` lưu tách biệt `outcome` (`succeeded` | `refused` | `failed`), `cached` (`bool`), `latency_ms`, `tokens_measured` và `input/output/thoughts/total_tokens`.
   - Mở rộng additive tại `GET /api/admin/overview` trả thêm `cachedToday`, `cached7d`, `cachedTotal`, `dailyBreakdown[].cachedRequests`, `dbConnected`, `databaseDialect`, `allowLiveAi`, và tóm tắt an toàn `emailReadiness` (không chứa bí mật).
4. **Lỗi `404` cho `/api/*` trên `https://hoclieu.tech`:**
   - Do kiến trúc triển khai đã khóa: Vercel chỉ phục vụ Frontend SPA tĩnh, còn FastAPI backend đang ở trạng thái `BACKEND_DEPLOYMENT_PENDING` chờ VPS riêng. Mọi asset tĩnh và SPA route đều `200`, không có liên kết hay tài nguyên frontend nào hỏng.

---

## 4. Tinh chỉnh Header Admin

- Gỡ hoàn toàn nút làm mới thủ công `#btn-admin-refresh` khỏi Header; dữ liệu vẫn tự đồng bộ khi mount, sau mỗi thao tác ghi, khi đổi tab sau lỗi và qua nút `#btn-admin-retry-overview`.
- Vùng phải Header (`#admin-header-right`) chỉ giữ đúng 2 nút: **Thông báo** (`#btn-admin-notif-bell`) và **Avatar** (`#btn-admin-account-menu`), bỏ viền ô vuông và viền viên thuốc (`border-width: 0px`), giữ nền hover nhẹ (`var(--canvas-soft)`) và viền focus bàn phím rõ (`2px solid var(--primary)`).
- Trên di động (`<= 640px`), ẩn mũi tên caret, giữ vùng chạm `36×36px` tròn gọn bên phải đối xứng nút menu trái, `0px` tràn ngang tại `390px` và `320px`.

---

## 5. Hoàn thiện chức năng Thông báo (Notification)

- Tiêu đề popover chuẩn hóa thành `"Thông báo"` kèm bộ đếm thực tế (`{pendingTeachers.length} chờ duyệt`), không dùng khái niệm "chưa đọc" giả và không có nút `"Đánh dấu tất cả đã đọc"`.
- Bỏ nền xanh `.is-unread` trên các mục thông báo; bổ sung trạng thái lỗi có nút `"Thử lại"` (`#admin-notif-error`) khi mất kết nối máy chủ, trạng thái rỗng rõ ràng khi `0` hồ sơ.
- Đóng/mở độc quyền với menu Avatar (mở menu này tự đóng menu kia), hỗ trợ click ra ngoài và phím `Escape`, chiều rộng an toàn `min(320px, calc(100vw - 24px))`.
- Kiểm chứng E2E: duyệt 1 hồ sơ Giáo viên làm badge giảm tức thì `2 → 1` không cần F5; đăng xuất xóa sạch phiên.

---

## 6. Tinh gọn Menu Avatar & Điều hướng về Không gian học

- Loại bỏ kicker chữ hoa `"THÔNG TIN TÀI KHOẢN"` và sửa lỗi bọc 2 lớp badge xung quanh chip `"Quản trị viên"` trong phần đầu menu.
- Menu giữ đúng 4 mục không trùng lặp: `Cài đặt tài khoản`, `Cài đặt hệ thống`, `Về không gian học` (`#btn-admin-back-workspace`, `data-admin-acc-act="learning"`), và `Đăng xuất`.
- Kiểm chứng E2E: bấm `Về không gian học` gỡ hash `#admin` (nếu có) và điều hướng về `/app` (không gian học tập, không rơi về Landing), giữ nguyên phiên `admin` và bản nháp/lịch sử.

---

## 7. Tinh gọn Sidebar quản trị

- Gỡ nút `Về không gian học` khỏi `#admin-sidebar`, giữ đúng **4 mục quản trị**: `Tổng quan`, `Tài khoản`, `Thống kê`, `Nhật ký quản trị`.
- Bảo toàn logo thương hiệu, trạng thái active, chế độ thu gọn desktop (`sidebar_collapsed_1440.png`) và ngăn kéo di động (`<= 820px`).

---

## 8. Đơn giản hóa Trang Tổng quan (Overview)

- Rút gọn từ 6 thẻ xuống **4 thẻ KPI** (`repeat(4, 1fr)` trên desktop rộng, `2×2` trên tablet, `1` cột trên di động):
  1. `Tổng số tài khoản` — phân rã vai trò không cộng trùng (`12 Học sinh · 2 Giáo viên · 1 Quản trị (1 đang khóa)` thay vì liệt kê `1 Đã khóa` ngang hàng vai trò).
  2. `Yêu cầu cấp quyền Giáo viên` — hiển thị chip cảnh báo duy nhất khi `> 0` và liên kết trực tiếp tới danh sách chờ duyệt.
  3. `Lượt phân tích hôm nay` — giữ nguyên số đo server trung thực (`analysesToday`, không ép theo tổng quota người dùng).
  4. `Trạng thái hệ thống` — phản ánh trạng thái thực từ server (`dbConnected`, `databaseDialect`, `aiServiceConfigured`, `allowLiveAi`), loại bỏ hoàn toàn chuỗi cấu hình tĩnh `4–10 req/phút` và các badge trang trí (`Đang quản lý`, `Hôm nay`, `Đã ghi nhận`, `Đang bảo vệ`).
- **Ưu tiên di động (`<= 680px`):** Khi có yêu cầu chờ duyệt Giáo viên (`> 0`), khối `#admin-pending-panel` tự động đưa lên đầu (`order: -1`) và bảng `#admin-pending-table` ẩn cột phụ trên màn hình nhỏ (`<= 768px`) để hiển thị ngay người đăng ký cùng nút `Cấp quyền Giáo viên` / `Chi tiết` mà không phải cuộn ngang.

---

## 9. Tinh chỉnh Trang Tài khoản (Accounts)

- Gộp 2 cột `Hạn mức AI / ngày` và `Đã dùng hôm nay` thành 1 cột duy nhất **`Sử dụng hôm nay`** (`4/15 lượt`), loại bỏ dòng phụ lặp `"Chưa đo token"` khỏi mọi hàng bảng (thông tin chi tiết vẫn đầy đủ trong modal Chi tiết tài khoản).
- Tách chỉ báo `Đã xác minh email` / `Chưa xác minh email` thành thẻ gọn cùng hàng tên người dùng để tránh gãy dòng xấu và phân biệt rõ xác minh email với trạng thái tài khoản / quyền Giáo viên; tuyệt đối không tự đánh dấu email đã xác minh cho tài khoản Admin tạo qua CLI.
- Cập nhật placeholder tìm kiếm: `"Tìm theo tên, email, tên đăng nhập hoặc trường học..."` (khớp đủ 4 trường hỗ trợ).
- **Responsive di động (`<= 768px`):** Ẩn các cột phụ (`Vai trò`, `Trạng thái`, `Ngày đăng ký`, `Sử dụng hôm nay`) và gom chip Vai trò, Trạng thái, Hạn mức vào dòng meta gọn ngay trong cột `Người dùng`, giữ `Chi tiết` + `⋯` luôn hiện rõ bên phải với `0px` cuộn ngang.

---

## 10. Thiết kế lại Thanh Phân trang (Pagination)

- Giữ nguyên logic thuần đã kiểm chứng (`computeAdminPagination`, `buildAdminPaginationItems`).
- Thiết kế tối giản theo ngôn ngữ phẳng:
  - Trái: `1–10 trên 15 tài khoản` (hoặc `0 tài khoản`).
  - Phải: bộ chọn `10 / trang ▾` không khung nặng + điều hướng gọn `‹  1 / 2  ›` dùng nút chevron không viền, ẩn cụm điều hướng khi chỉ có `<= 1` trang, bỏ dãy nút số đóng khung và bỏ nhãn dài `"Số dòng mỗi trang:"` / `"Trước"` / `"Sau"`.
- Kiểm chứng đầy đủ chuyển trang 1↔2, đổi cỡ trang `10 → 20 → 10`, tìm kiếm lọc về 1 kết quả, và bố cục 2 dòng sạch sẽ trên di động `390px`.

---

## 11. Tinh chỉnh Trang Thống kê (Analytics)

- Nâng cấp lên **4 thẻ KPI**: `Tổng yêu cầu (7 ngày)` (hiển thị kèm số lượt phục vụ từ bộ nhớ đệm `cached7d`), `Tỷ lệ xử lý thành công` (gỡ bỏ badge gây hiểu nhầm `"Kiểm chứng tất định"` vì đây là tỷ lệ phục vụ vận hành chứ không phải độ chính xác toán học), `Thời gian phản hồi TB`, và `Token tiêu thụ (7 ngày)` (chuyển từ Tổng quan sang).
- Nâng cấp `buildAdminAnalyticsChartModel` và biểu đồ cột từ 2 chuỗi lên **3 chuỗi cột ghép**: `Xử lý thành công` (xanh dương chính), `Từ chối an toàn` (`#c85a32`), và `Lỗi xử lý` (`#64748b`), tỷ lệ trục Y chia đều theo đỉnh của cả 3 chuỗi, chú giải + tooltip + bảng trợ năng khớp 100% với bảng chi tiết bên dưới.

---

## 12. Đóng phạm vi Cài đặt hệ thống (System Settings)

- Giữ nguyên toàn bộ kiểm tra hợp lệ hạn mức, phân tách rõ `Ngân sách dự kiến tháng (VND)` với chi phí thực tế, cảnh báo hủy thay đổi chưa lưu và ghi nhật ký quản trị khi lưu.
- Tab **Dịch vụ AI** hiển thị trung thực 3 trạng thái `true` / `false` / `null` (khắc phục nhánh rơi nhầm `"Đang kết nối"` khi `aiServiceConfigured === null`), đồng thời bổ sung thông tin chỉ đọc: `Model AI đang cấu hình (chỉ đọc)`, `Dịch vụ Email giao dịch (Resend)` (`emailReadiness`), và `Cơ sở dữ liệu máy chủ` (`PostgreSQL`/`SQLite`). Tuyệt đối không hiển thị API key hay bí mật nào.

---

## 13. Đóng phạm vi Nhật ký quản trị (Audit Logs) & Xuất CSV

- Xác minh sắp xếp ổn định phía server `(time_ts DESC, id DESC)` trong `_list_audit_logs` và mặc định mới nhất trước trên UI.
- Kiểm chứng xuất CSV thực trên trình duyệt cho cả `/api/admin/export/audit-logs` (`200`, `6` dòng gồm tiêu đề + 4 bản ghi mẫu + 1 bản ghi tự ghi nhận thao tác xuất) và `/api/admin/export/users` (`200`, `16` dòng, không có `password_hash`, có cột `Xác minh email`).
- Xác minh vô hiệu hóa công thức bảng tính (`=`, `+`, `-`, `@`) qua `_csv_safe_cell`.
- **Nợ kỹ thuật ghi nhận (không migrate ở đợt này):** Cột `admin_audit_logs.time_ts` hiện là `INTEGER` 32-bit lưu giây epoch (an toàn tới năm 2038); ghi nhận kế hoạch nâng `BigInteger` vào giai đoạn tối ưu backend/schema sau.

---

## 14. Tinh chỉnh cuối cùng cho Footer

- Giữ nguyên đồ họa hình học đóng trang, CTA chính `Bắt đầu dựng hình`, bố cục desktop và phong cách tối giản của `LandingFooter.tsx`.
- Tinh chỉnh có mục tiêu:
  1. Bỏ lặp chữ `Axo` trong dòng bản quyền cạnh logo: `© Axo · Hình học không gian 3D` → **`© Hình học không gian 3D`**.
  2. Thay từ tiếng Anh `Workspace` trong câu dẫn: `"Nhập đề tiếng Việt hoặc mở nhanh bài mẫu trong không gian học tập."`
  3. Tại `<= 359px` (như `320px`), xếp 4 liên kết chân trang thành lưới `2×2` thẳng hàng, triệt tiêu dòng mồ côi của mục `Thư viện`, `0px` tràn ngang trên cả 7 viewport.
- **Backlog công khai (không bịa trang giả):** Đã xác minh repo chưa có route `/privacy` hay `/terms` — ghi nhận vào backlog trước ngày mở public; không gắn link chết và không dùng `noreply@mail.hoclieu.tech` làm email hỗ trợ.

---

## 15. An toàn kích hoạt cục bộ & Khắc phục Runbook Rollback PostgreSQL

- Đã xác minh sự tồn tại và mã băm nguyên vẹn của tệp sao lưu: `C:\Users\Bunny\algosim_backups\algosim_backup_20261128_082150.dump` (`SHA256 = cc18110f89565f79049a17c2f17988cdfa42ba1e109cb992706748b9a7f71ff8`).
- Bổ sung mục **Khôi phục sao lưu PostgreSQL an toàn (Rollback `pg_restore` trên Windows & Linux)** vào [`docs/OPERATIONS.md`](../../../OPERATIONS.md):
  - Cấm pipe tệp nhị phân `.dump` qua `Get-Content -Raw -Encoding Byte | docker compose exec -T db pg_restore`.
  - Dùng `docker compose cp` → đối chiếu `Get-FileHash` (host) với `sha256sum` (container) → `DROP DATABASE` / `CREATE DATABASE` sạch → `pg_restore --no-owner --no-privileges` (tránh để sót bảng mới như `auth_tokens`, `email_verifications` khi dùng `--clean` trên DB đã nâng cấp).
- **Không tự ý thao tác lên CSDL thật / `.env` / container của Owner**; toàn bộ lệnh áp dụng do Owner tự quyết nằm ở mục `## Owner Actions`.

---

## 16. Đối chiếu hình ảnh BEFORE / AFTER (21 cặp ảnh sạch Toast)

Toàn bộ `21` ảnh BEFORE (`screenshots/before/`) và `21` ảnh AFTER (`screenshots/after/`) đều được chụp trên cùng dữ liệu tất định (`15` tài khoản, `76` telemetry, `4` audit log) với **`0` toast hiển thị** (`screenshots_before_manifest.json`, `screenshots_after_manifest.json`) và đã được kiểm tra trực quan từng màn hình:

| Bề mặt | BEFORE | AFTER | Cải thiện xác nhận trực quan |
|---|---|---|---|
| Header Desktop (`1440px`) | [`header_desktop_1440.png`](screenshots/before/header_desktop_1440.png) | [`header_desktop_1440.png`](screenshots/after/header_desktop_1440.png) | Bỏ nút Refresh & khung viền thừa, chỉ còn Bell + Avatar phẳng gọn |
| Header Mobile (`390px`, `320px`) | [`header_mobile_320.png`](screenshots/before/header_mobile_320.png) | [`header_mobile_320.png`](screenshots/after/header_mobile_320.png) | Bỏ caret & viền trên màn hình nhỏ, `0px` tràn ngang |
| Notification Popover (`1440px`) | [`notification_dropdown_desktop_1440.png`](screenshots/before/notification_dropdown_desktop_1440.png) | [`notification_dropdown_desktop_1440.png`](screenshots/after/notification_dropdown_desktop_1440.png) | Tiêu đề `"Thông báo"`, đếm `"2 chờ duyệt"`, bỏ nền xanh unread giả |
| Avatar Dropdown (`1440px`) | [`avatar_dropdown_desktop_1440.png`](screenshots/before/avatar_dropdown_desktop_1440.png) | [`avatar_dropdown_desktop_1440.png`](screenshots/after/avatar_dropdown_desktop_1440.png) | Sửa lỗi bọc 2 badge vai trò, bỏ kicker thừa, 4 mục gọn có `Về không gian học` |
| Sidebar Thu gọn & Mở rộng | [`sidebar_collapsed_1440.png`](screenshots/before/sidebar_collapsed_1440.png) | [`sidebar_collapsed_1440.png`](screenshots/after/sidebar_collapsed_1440.png) | Đúng 4 mục quản trị thuần túy |
| Overview Desktop (`1440px`) | [`overview_desktop_1440.png`](screenshots/before/overview_desktop_1440.png) | [`overview_desktop_1440.png`](screenshots/after/overview_desktop_1440.png) | 6 → 4 thẻ KPI, số vai trò không cộng trùng, trạng thái hệ thống thật |
| Overview Mobile (`390px`) | [`overview_mobile_390.png`](screenshots/before/overview_mobile_390.png) | [`overview_mobile_390.png`](screenshots/after/overview_mobile_390.png) | Bảng duyệt GV lên đầu, nút duyệt hiện ngay không cuộn ngang |
| Accounts Desktop (`1440px`) | [`accounts_desktop_1440.png`](screenshots/before/accounts_desktop_1440.png) | [`accounts_desktop_1440.png`](screenshots/after/accounts_desktop_1440.png) | 6 cột gọn, gộp `Sử dụng hôm nay`, bỏ `"Chưa đo token"`, chip email sạch |
| Accounts Mobile (`390px`) | [`accounts_mobile_390.png`](screenshots/before/accounts_mobile_390.png) | [`accounts_mobile_390.png`](screenshots/after/accounts_mobile_390.png) | Không cắt badge, `Chi tiết` + `⋯` luôn bấm được không cuộn ngang |
| Pagination Desktop & Mobile | [`pagination_desktop_1440.png`](screenshots/before/pagination_desktop_1440.png) | [`pagination_desktop_1440.png`](screenshots/after/pagination_desktop_1440.png) | Thanh phân trang phẳng tối giản `1–10 trên 15 tài khoản · 10 / trang ▾ · ‹ 1 / 2 ›` |
| Analytics Desktop (`1440px`) | [`analytics_desktop_1440.png`](screenshots/before/analytics_desktop_1440.png) | [`analytics_desktop_1440.png`](screenshots/after/analytics_desktop_1440.png) | 4 KPI gồm Token 7 ngày, bỏ badge `"Kiểm chứng tất định"`, biểu đồ 3 chuỗi cột |
| System Settings Service | [`system_settings_service_1440.png`](screenshots/before/system_settings_service_1440.png) | [`system_settings_service_1440.png`](screenshots/after/system_settings_service_1440.png) | Hiện rõ Model chỉ đọc, trạng thái Resend và PostgreSQL, 0 bí mật |
| Footer Desktop & `320px` | [`footer_mobile_320.png`](screenshots/before/footer_mobile_320.png) | [`footer_mobile_320.png`](screenshots/after/footer_mobile_320.png) | Không lặp `Axo`, Việt hóa `không gian học tập`, lưới liên kết 2×2 thẳng hàng |

---

## 17. Ma trận Responsive 7 Viewport

Kiểm tra tự động bằng Playwright trên bản build `frontend/dist` (`e2e_closure_receipt.json`):

| Viewport | Admin Overview (`overflowX`) | Admin Header (H / Bell / Avatar trong khung) | Landing Footer (`overflowX`) |
|---|---:|---|---:|
| `1920 × 1080` | `0px` | `52px` · Bell & Avatar trong khung (`36×36`) | `0px` |
| `1440 × 900` | `0px` | `52px` · Bell & Avatar trong khung (`36×36`) | `0px` |
| `1366 × 768` | `0px` | `52px` · Bell & Avatar trong khung (`36×36`) | `0px` |
| `1024 × 768` | `0px` | `52px` · Bell & Avatar trong khung (`36×36`) | `0px` |
| `768 × 1024` | `0px` | `52px` · Bell & Avatar trong khung (`36×36`) | `0px` |
| `390 × 844` | `0px` | `52px` · Bell & Avatar trong khung (`36×36`) | `0px` |
| `320 × 700` | `0px` | `52px` · Bell & Avatar trong khung (`36×36`) | `0px` |

---

## 18. Bảo toàn Hiệu năng Frontend, Cô lập Bundle & Smoke 3D Offline

- **Build sản xuất (`frontend/dist`, Vite 6.4.3):**
  - `index-*.js`: `475.80 kB` (`140.94 kB` gzip)
  - `AdminWorkspaceView-*.js`: `140.93 kB` (`31.63 kB` gzip)
  - `vendor-three-*.js`: `568.24 kB` (`143.15 kB` gzip) — **cô lập hoàn toàn**
  - `geometry-samples-public-*.js`: `543.42 kB` (`57.27 kB` gzip) — **cô lập hoàn toàn**
- **Cô lập tải thực tế trong Chromium (`e2e_closure_receipt.json`):**
  - `/` (Landing): `1` script, `hasVendorThree = false`, `hasGeometrySamples = false`.
  - `/login`: `7` scripts, `hasVendorThree = false`, `hasGeometrySamples = false`.
  - `/admin`: `8` scripts, `hasVendorThree = false`, `hasGeometrySamples = false`.
- **Smoke 3D `S.ABCD` offline & Cổng chặn Live AI:**
  - Mở mẫu `S.ABCD` từ Thư viện trên Chromium: `lazyLoadedVendorThree = true`, WebGL `<canvas>` render thật kích thước `809 × 862 px`.
  - Gọi `POST /api/analyze` với `ALLOW_LIVE_AI=0`: máy chủ từ chối fail-closed `HTTP 503` (`reasonCode = "LIVE_AI_DISABLED"`), bảo đảm `0` request ra AI ngoài.

---

## 19. Kiểm toán Bảo mật & Phân quyền (RBAC / CSV / Secrets)

- **RBAC:** Khách (`401` trên `/api/admin/overview` & `/api/admin/export/audit-logs`, hiển thị `#view-admin-denied`), Học sinh (`403`, `#view-admin-denied`), Giáo viên (`403`, `#view-admin-denied`).
- **Bảo vệ Admin duy nhất:** Khóa nâng cấp lên `admin` (`403`) và khóa hạ cấp/khóa/xóa/bật `mustChangePassword` trên Admin duy nhất (`400`, đã khóa trong `test_v28_admin_account.py`).
- **Chống CSV Formula Injection & rò rỉ bí mật:** Đã kiểm chứng cả API lẫn tải tệp trình duyệt rằng `=SUM(...)`, `+cmd|...`, `=HYPERLINK(...)` đều được tiền tố `'`; không chứa `password_hash` hay API key; `DIST_SECRET_HITS = 0`; `npm audit --omit=dev` = `0` lỗ hổng (`info/low/moderate/high/critical = 0`).

---

## 20. Tổng hợp Hồi quy Toàn phần (Không đếm trùng)

| Hạng mục kiểm thử | Phạm vi / Lệnh | Kết quả duy nhất | Trạng thái |
|---|---|---|---|
| Frontend TypeScript + Build | `npx tsc -b && npm run build` | `0` lỗi, `4.81s` | `PASS` |
| Frontend Unit & Component Suite | `npx vitest run` | `196/196` file, `2.329/2.329` test PASS | `PASS` |
| Frontend Security & Audit | `dist` secret scan + `npm audit --omit=dev` | `0` secret hits, `0` prod vulnerabilities | `PASS` |
| Backend Partition 1 (Geometry) | `pytest -q tests/geometry/` + rerun 3 file governance sau đóng băng | `13.248` passed, `0` failed, `6` skipped, `3` deselected, `12` xfailed *(không đếm trùng)* | `PASS` |
| Backend Partition 2 (Core/API/Auth/Docs) | `pytest -q tests/ --ignore=tests/geometry` | `2.017` passed, `0` failed, `2` skipped, `7` deselected | `PASS` |
| Backend Postgres Integration (Opt-in) | `pytest -q -m postgres tests/test_postgres_integration.py` | `2` passed, `0` failed (`19.94s`) | `PASS` |
| **Tổng Backend duy nhất** | Tổng hợp Partition 1 + 2 + Postgres opt-in | **`15.267` passed, `0` failed** (`8` skipped, `8` deselected, `12` xfailed) | **`PASS`** |
| Playwright E2E + 7 Viewports + CSV + Smoke 3D | `closure_capture.mjs --phase after` trên `frontend/dist` + Docker | `21/21` ảnh `0` toast, `0` console/page/network errors, toàn bộ check `PASS` | `PASS` |

---

## 21. Quản trị Đóng băng (`Freeze Governance`) & Phả hệ Candidate

Do `backend/app/accounts/router.py` nằm trong vùng `measured_system` (`130` file), toàn bộ quy trình Freeze Governance đã được thực thi nghiêm ngặt trên bản clone sạch `HEAD`:

- **Source & Product Commit:** `9385d496597e309aa355ac60342115c6c6dc3491` (`cay_lam_viec_sach = true`).
- **Governance Commit:** `daf84640a821b7b951c4c8c2e4a976b40f6b267b`.
- **Candidate gốc đã lưu trữ bất biến:** `9568cf07b` → [`prior-EVALUATION_CANDIDATE-9568cf07b.json`](prior-EVALUATION_CANDIDATE-9568cf07b.json) (`SHA256 = a14c1070b28e4b0a00f453e94c318d81f78a1d6a9acde3911c1c8f1ce331763f`).
- **Integrated Candidate mới:** [`EVALUATION_CANDIDATE.json`](../../../semantic-benchmark/EVALUATION_CANDIDATE.json) — `measured_system.tree_hash = e332983ec2e7858c50499b8eee58f17646f5be207dae029c08800abdbf66dcf8` (`130` file), `CACHE_VERSION = "158"`, `core_evaluation_changed = []` (0 file trong lõi hình học/AI thay đổi).
- **Làm mới 3 mẫu phê duyệt chờ (`K-1`, `S-2`, `R-1`):** Thực thi qua `backend/scripts/refresh_pending_templates.py` với `owner_decision = "PENDING_OWNER_DECISION"`, `paid_project_confirmed = false` ([`pending_template_refresh.json`](pending_template_refresh.json), [`candidate_lineage.json`](candidate_lineage.json)).
- **Kiểm chứng CLI:**
  - `freeze_evaluation_candidate.py --verify`: `PASS` (`130 file, e332983ec2e7858c…`).
  - `freeze_evaluation_candidate.py --verify-historical --json`: `PASS` (`0` mismatches, `provenance_matches_head = true`).
  - `lock_cache_identity.py --verify`: `PASS` (`CACHE_VERSION 158`).
- **Chính sách kế thừa benchmark:** Kết quả benchmark lịch sử tiếp tục gắn chặt với `4978ac01f3240d08ae259d532edcc83c2c5af5e4`; không sao chép điểm sang candidate mới; live evaluation giữ nguyên `LIVE_EVALUATION_PENDING_AUTHORIZATION`.

---

## 22. Danh sách Commit trên `main`

1. `9d4a4de36` — `feat(admin-api): expose operational readiness and cache telemetry in admin overview` (`backend/app/accounts/router.py`, `backend/tests/test_v28_admin_account.py`).
2. `d4506909f` — `refactor(admin-ui): close admin header, overview, accounts, pagination, and analytics scope` (`AdminWorkspaceView.tsx`, `global.css`, và 4 file test frontend).
3. `9385d4965` — `chore(footer-docs): refine landing footer copy and add safe pg_restore rollback runbook` (`LandingFooter.tsx`, `landing.css`, `landing-footer-layout.test.tsx`, `docs/OPERATIONS.md`).
4. `daf84640a` — `chore(governance): register integrated candidate for admin ui functional closure` (`EVALUATION_CANDIDATE.json`, 3 C21 templates, `prior-EVALUATION_CANDIDATE-9568cf07b.json`, `pending_template_refresh.json`, `candidate_lineage.json`).
5. Commit hồ sơ bằng chứng & báo cáo run `admin-ui-functional-closure` (+ cập nhật xác minh production live sau khi đẩy `origin/main`).

---

## 23. Xác minh Production Live (`https://hoclieu.tech`)

- **Trạng thái:** `VERIFIED` (`2026-11-28T04:21:47Z`, bản build từ commit đã đẩy `44e7b3a2a`, biên bản [`production_verification.json`](production_verification.json)):
  - **Bản build mới đang phục vụ:** `deployed_new_build = true`, Footer hiển thị chính xác `© Hình học không gian 3D` và `"Nhập đề tiếng Việt hoặc mở nhanh bài mẫu trong không gian học tập."`.
  - **Tuyến SPA:** `/`, `/app`, `/library`, `/login`, `/register`, `/admin` đều trả `HTTP 200`.
  - **Cô lập Bundle trên production:** `/` tải `1` script (`vendor-three = false`, `geometry-samples = false`); `/login` tải `7` scripts (`vendor-three = false`).
  - **Security Headers:** `strict-transport-security: max-age=63072000`, `x-content-type-options: nosniff`, `x-frame-options: DENY`, `referrer-policy: strict-origin-when-cross-origin`.
  - **Responsive:** `overflowX = 0` tại `1440px`, `768px`, `390px`, `320px`.
  - **Ghi chú Backend:** Vercel chỉ phục vụ Frontend SPA (`BACKEND_DEPLOYMENT_PENDING` chờ VPS riêng).

---

## 24. Bảng cổng nghiệm thu (`G01–G25`) & Phán quyết

| Cổng | Nội dung kiểm chứng | Trạng thái | Ghi chú / Bằng chứng |
|---|---|---|---|
| `G01` | Baseline & bảo toàn tài nguyên Owner | `PASS` | `9a729e2c7`, backup SHA-256 khớp, containers/volume/`.env`/worktrees nguyên trạng |
| `G02` | Đối soát CSV Audit 404 → 200 thật | `PASS` | Click `#btn-admin-export-audit` → `HTTP 200`, BOM UTF-8, chống formula injection |
| `G03` | Docker Provenance từ mã mới (0 bind mount) | `PASS` | `algo-sim-backend:closure-verify` (`sha256:3a05302ef580...`) |
| `G04` | Phân định Telemetry & `/api/*` Vercel 404 | `PASS` | Additive fields thật trong `admin_overview`; Vercel SPA-only (`BACKEND_DEPLOYMENT_PENDING`) |
| `G05` | Header Admin: chỉ Bell + Avatar không viền | `PASS` | `headerRightButtonIds = [bell, account]`, `border: 0px`, 0 `#btn-admin-refresh` |
| `G06` | Notification thật, không unread giả, tự đồng bộ | `PASS` | Tiêu đề `"Thông báo"`, giảm `2→1` không F5, hỗ trợ error/empty/Escape/độc quyền |
| `G07` | Avatar menu sạch & `Về không gian học` → `/app` | `PASS` | Sửa lỗi 2 badge, 4 mục không trùng, giữ phiên `admin` & bản nháp |
| `G08` | Sidebar giữ đúng 4 mục quản trị | `PASS` | `sidebarNavCount = 4`, bỏ `#btn-admin-back-workspace` khỏi Sidebar |
| `G09` | Overview 4 KPI thật, ưu tiên duyệt GV trên mobile | `PASS` | 4 thẻ, bỏ `req/phút` & badge trang trí, vai trò không cộng trùng, mobile `order: -1` |
| `G10` | Accounts gộp cột sử dụng, `emailVerified` gọn, mobile 0 cuộn ngang | `PASS` | 6 cột desktop, bỏ `"Chưa đo token"`, mobile thấy ngay `Chi tiết` + `⋯` |
| `G11` | Pagination tối giản bảo toàn logic thuần | `PASS` | `1–10 trên 15 tài khoản`, `10 / trang ▾`, `‹ 1 / 2 ›`, ẩn khi `<= 1` trang |
| `G12` | Analytics 4 KPI + biểu đồ 3 chuỗi khớp bảng | `PASS` | Có Token 7 ngày & cache hits, gỡ `"Kiểm chứng tất định"`, 3 cột thành công/từ chối/lỗi |
| `G13` | System Settings hiển thị Model, Resend, DB chỉ đọc | `PASS` | 0 bí mật lộ ra UI/API, xử lý đủ `true/false/null` |
| `G14` | Audit Logs sắp xếp ổn định & CSV an toàn | `PASS` | `(time_ts DESC, id DESC)`, CSV UTF-8 + formula escape, nợ 2038 đã ghi nhận |
| `G15` | Footer tinh chỉnh copy & `320px` cân đối | `PASS` | `© Hình học không gian 3D`, `không gian học tập`, lưới 2×2 ở `320px` |
| `G16` | Runbook Rollback `pg_restore` an toàn trên Windows | `PASS` | Đã cập nhật [`docs/OPERATIONS.md`](../../../OPERATIONS.md) dùng `docker compose cp` + SHA-256 |
| `G17` | 21 cặp ảnh BEFORE/AFTER khớp trạng thái, `0` toast | `PASS` | Đã đối chiếu trực quan 100% ảnh BEFORE/AFTER |
| `G18` | Responsive 7 viewport `1920..320px` | `PASS` | `overflowX = 0` trên cả 14 phép đo Admin & Footer |
| `G19` | Bảo toàn hiệu năng & cô lập bundle Three.js | `PASS` | `0` `vendor-three` trên Landing/Login/Admin; lazy load khi mở 3D |
| `G20` | Smoke 3D `S.ABCD` offline & `ALLOW_LIVE_AI=0` | `PASS` | WebGL `<canvas>` `809×862`, `/api/analyze` trả `503 LIVE_AI_DISABLED` |
| `G21` | Bảo mật RBAC, Single-Admin, `npm audit`, secret scan | `PASS` | `401`/`403` chặt, `0` dist secrets, `0` prod vulnerabilities |
| `G22` | Hồi quy toàn phần Frontend + Backend + Postgres | `PASS` | FE `2.329/2.329`, BE `15.267/15.267` duy nhất (`0` fail) |
| `G23` | Freeze Governance & C21 Pending Templates | `PASS` | `9385d4965` (`e332983e...`), `--verify` & `--verify-historical` PASS |
| `G24` | Cổng kiến trúc tài liệu & an toàn phát hành | `PASS` | `audit_docs_information_architecture.py` PASS, `42/42` test, `check_publication_safety` 0 vi phạm |
| `G25` | Xác minh `https://hoclieu.tech` & `http://localhost:3000` | `PASS` | `https://hoclieu.tech` VERIFIED (`production_verification.json`), `localhost:3000` `HTTP 200` |

**Trạng thái vận hành tách biệt (giữ trung thực, không tự thực thi thay Owner):**
- `LOCAL_DATABASE_MIGRATION_PENDING_OWNER_APPROVAL`
- `LOCAL_ADMIN_SETUP_PENDING_OWNER_ACTION`
- `REAL_EMAIL_SMOKE_PENDING_OWNER_CONFIGURATION`
- `BACKEND_DEPLOYMENT_PENDING`
- `LIVE_EVALUATION_PENDING_AUTHORIZATION`

**Phán quyết chính thức:**
- `ADMIN_UI_FUNCTIONAL_CLOSURE_COMPLETE`
- `FOOTER_FINAL_REFINEMENT_COMPLETE`
- `LOCAL_ACTIVATION_EVIDENCE_RECONCILED`
- `FRONTEND_PERFORMANCE_PRESERVED`
- `FREEZE_GOVERNANCE_VERIFIED`
- `READY_FOR_BACKEND_PERFORMANCE_PHASE`

---

## 25. Owner Actions

Toàn bộ tác vụ chạm vào CSDL PostgreSQL thật, container Docker thật, tài khoản Admin thật hoặc gửi email thật đều **chưa tự chạy**. Khi Owner sẵn sàng kích hoạt môi trường local, chạy tuần tự các khối lệnh sau trong PowerShell tại `D:\Documents\projects\algo-sim`:

### A. Kích hoạt CSDL Docker thật (`b6d2f0a8c4e1`) & Tạo/Đồng bộ tài khoản Admin duy nhất

```powershell
# 1. Xác nhận bản sao lưu nguyên vẹn trước khi nâng cấp
$backup = "C:\Users\Bunny\algosim_backups\algosim_backup_20261128_082150.dump"
(Get-FileHash $backup -Algorithm SHA256).Hash.ToLower()
# Phải khớp: cc18110f89565f79049a17c2f17988cdfa42ba1e109cb992706748b9a7f71ff8

# 2. Dừng backend cũ, build image backend mới và nâng cấp CSDL
docker compose stop backend
docker compose build backend
docker compose up -d db
docker compose run --rm --no-deps backend python -m alembic upgrade a1c7e4b90d52:c4e8a91b2f03 --sql | docker compose exec -T db psql -U algosim -d algosim -v ON_ERROR_STOP=1
docker compose run --rm --no-deps backend python -m alembic stamp --purge e437149641fa
docker compose up -d --force-recreate backend

# 3. Kiểm tra health & tạo/đồng bộ tài khoản Admin duy nhất (đọc từ backend/.env)
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health
docker compose exec backend python scripts/manage_admin.py --check
docker compose exec backend python scripts/manage_admin.py --apply --create-if-missing
```

### B. (Tùy chọn) Kiểm tra gửi Email thật qua Resend

```powershell
# Chỉ chạy sau khi Owner đặt EMAIL_ENABLED=true trong backend/.env và recreate backend:
docker compose up -d --force-recreate backend
docker compose exec backend python scripts/email_smoke_test.py --check
docker compose exec backend python scripts/email_smoke_test.py --send --to <email-cua-owner>
```

### C. Quy trình Rollback PostgreSQL an toàn (nếu cần hoàn nguyên CSDL về bản sao lưu)

```powershell
# KHÔNG dùng Get-Content -Raw -Encoding Byte | docker compose exec!
docker compose stop backend
$backup = "C:\Users\Bunny\algosim_backups\algosim_backup_20261128_082150.dump"
$hostHash = (Get-FileHash $backup -Algorithm SHA256).Hash.ToLower()
docker compose cp $backup db:/tmp/algosim_restore.dump
docker compose exec -T db sha256sum /tmp/algosim_restore.dump
# Xác nhận mã băm khớp $hostHash trước khi chạy tiếp:
docker compose exec -T db psql -U algosim -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'algosim' AND pid <> pg_backend_pid();"
docker compose exec -T db psql -U algosim -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE algosim; CREATE DATABASE algosim OWNER algosim;"
docker compose exec -T db pg_restore -U algosim -d algosim --no-owner --no-privileges /tmp/algosim_restore.dump
docker compose exec -T db rm -f /tmp/algosim_restore.dump
```
