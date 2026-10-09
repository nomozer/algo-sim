# merge-readiness — dọn cuối, housekeeping Git, danh sách nghiệm thu

Máy local, 0 lượt gọi model. Không đổi geometry kernel, FactGraph, Compact DSL, pipeline Gemini, giao diện. Trạng thái nhánh:
`READY_FOR_USER_ACCEPTANCE` — run này không ghi `APPROVED_BY_USER` cho mục nào.

## 1. Dọn hồ sơ Chrome mồ côi (`results/TEMP_CLEANUP.json`)

Manifest `runs/browser-temp-lifecycle/results/TEMP_INVENTORY.json` (671 `%TEMP%\w12-*`, `VERIFIED_ORPHAN`). Trước khi xoá:
0 `chrome.exe` đang chạy, không tiến trình kiểm thử nào. Dry-run 07:43Z: 671/671 qua đủ kiểm tra (tên trong manifest · con trực
tiếp của `%TEMP%` · không link/junction/reparse point · giờ tạo trùng manifest · không mới hơn lúc kiểm kê · có bố cục hồ sơ
Chrome · không dòng lệnh tiến trình nào tham chiếu), ~35,1 GB. Người dùng xác nhận xoá. Áp dụng 07:46Z, mỗi mục kiểm lại
ngay lúc xoá, từng tên (không wildcard): **671 xoá · 0 hỏng · 0 bỏ qua**. Ổ C: trống **43,87 → 77,43 GB**.
`%TEMP%\scoped_dir*` 234 → 234 — không đụng (`UNKNOWN`/`ACTIVE`). Script: `diagnostics/clean-orphans.mjs`.

Chỉ đề xuất, không xoá: `D:/tmp/classband-logs-6a1801e7` (6,6 MB; 32 PNG không phải bằng chứng), `D:/tmp/classband-logs-9284202d`
(9 KB), `D:/tmp/classband-logs-9284202d-a2` (413 KB), `D:/tmp/classband-gates-1f4e74fe`, `D:/tmp/browserlifecycle-gates-ac7b1d07`
— log đã chép vào các thư mục run trong kho.

## 2. Housekeeping Git (`f89a1a8b`)

Hai thay đổi người dùng cho phép commit: `.gitignore` (`.playwright-cli/`) và xoá `frontend/public/favicon.svg`. Thêm hai sửa
bắt buộc theo đó:
- `frontend/index.html` trỏ tới tệp đã xoá ⇒ `<link rel="icon" href="data:," />` (không favicon mới; trình duyệt không xin
  `/favicon.ico`). Bản dựng: mọi asset trang tham chiếu tồn tại.
- `backend/scripts/audit_second_family_preregistration_evidence.py`: tiền kiểm coi favicon thiếu là sạch CHỈ khi còn là thay
  đổi chưa stage (` D`) — sau khi commit việc xoá, 4 test đỏ (`test_12_final_decision…`, `test_audit_second_family_precheck…`
  × 3 nhánh; đo bằng cách trả điều kiện cũ). Nay sạch khi chưa stage HOẶC tệp không còn được theo dõi; bị stage vẫn không sạch.

Danh tính: candidate `7f3f0423…` (102 file) không đổi — `index.html` ngoài `MEASURED_SYSTEM_PATHS`; `product_commit_sha`
vẫn `45f5a7f0` (định nghĩa: `backend/app` + `frontend/src`). Nhưng **bản dựng frontend phát hành ĐÃ đổi** (một dòng `<head>`)
— không tuyên bố «sản phẩm không đổi». Không đo lại trình duyệt: dòng ấy không chạm bố cục, canvas, camera, dữ liệu.
`CACHE_VERSION` 118, `LLM_ONLY`.

## 3. Vòng đời trình duyệt (`3cb0630a`, mã không đổi từ đó)

Bằng chứng còn hiệu lực: Chrome thật 7/7 kịch bản, unit 5/5, T3 PASS tại `ac7b1d07`. Kiểm ngắn bây giờ: gốc
`D:/tmp/algosim-browser` 0 thư mục, 0 Chrome của bộ đo, `%TEMP%\w12-*` 0 (sau khi dọn — tăng lên là thấy ngay). Không chạy
thêm bài kiểm tra trình duyệt. Nợ: 20 script độc lập chưa dùng `BrowserSession` (`ISSUE-OPS-BROWSER-SESSION-PROFILE-LEAK`).

## 4. Danh sách nghiệm thu

**Đã kiểm chứng tự động — không cần chạy lại:**
- Tier-A 8/8 một lượt (product `45f5a7f0`, `runs/classroom-band-fit`); dải lớp 24/24; không dải lớp 55/56 (ca có từ trước);
  W02 16/16 · W04 24/24 · W05 23/24 (một trang không tải, ghi rõ).
- T3 PASS (`ac7b1d07`; và tại commit tài liệu cuối của run này — `handoff.md` §2); candidate/cache/lược đồ/bề mặt mô hình.
- Occlusion bốn cảnh W14: sản phẩm = oracle, oracle tái tạo tập đã duyệt 4/4 (`runs/phone-landscape-layout`).
- Vòng đời trình duyệt 7/7; dọn 671 hồ sơ.

**Cần anh/chị kiểm tra trực tiếp** (chưa mục nào `APPROVED_BY_USER`):
1. Điện thoại thật — `runs/final-acceptance/review.md` G-1…G-9 (= E-R6 + F-R7).
2. Chip lớp học — `runs/classroom-band-fit/review.md` H-1…H-3 (H-3: chấp nhận chip chỉ chấm màu ở 640–667 px ngang?) và
   C-1…C-4 (cần backend + tài khoản giáo viên/học sinh).
3. Ảnh đã chụp, chưa duyệt — `runs/phone-landscape-layout/review.md` F-R1–F-R6, `runs/mobile-canvas-fit/review.md` E-R1–E-R5,
   `runs/exact-dimensions/review.md` R1–R10, `runs/regular-triangular-pyramid-w01/REVIEW.md` R1–R12, gói W5
   (`runs/regular-square-pyramid-w05/REVIEW.md`) và W4 (`runs/regular-square-pyramid-w04/REVIEW.md`) R1–R10 (gộp W1–W3;
   H-W1-1 ghi là chặn merge).
4. Bốn cảnh W14 (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`, OPEN): nhìn nét đứt/liền của chóp tam giác, lăng trụ tam
   giác, chóp tứ giác, thiết diện; issue khép khi có lớp registry đã duyệt.
5. `runs/final-acceptance/review.md` D-2…D-4.

**Nợ kỹ thuật / UX đã biết — vẫn OPEN:** bảng nổi che canvas khi ngang; nhãn rời canvas sau cú xoay ở màn thấp; header/thanh
công cụ mobile (gồm nút quay lại chỉ mũi tên khi có chip); chip lớp ở 640–667 px chỉ hiện chấm màu, giơ tay hai chạm; 20
script trình duyệt độc lập; `%TEMP%\scoped_dir*` (229 `UNKNOWN`, 1,3 GB).
