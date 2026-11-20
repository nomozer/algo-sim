# AXO V9.4.4 — Attachment Fidelity & File Preview Fix Report

**Owner Approval: PENDING_OWNER_REVIEW. Visual: NOT VERIFIED. Regression: FAIL.**

## Workspace và phạm vi

Worktree `D:/Documents/projects/axo-geometry-library`, nhánh `feat/axo-geometry-library-verification`, HEAD `d2aeec4a85312b545f6215843dbdd2687eeb009d`. Worktree đã có nhiều thay đổi chưa commit trước vòng này, kể cả các tệp giao diện liên quan; không tạo nhánh/worktree, commit, merge, push hay deploy. Không thay Sidebar, hệ thống thông báo, Scene3D, Geometry Engine hoặc backend trong vòng này.

Thay đổi trong `ProblemInput.tsx`, `global.css`, test composer và test mới `attachment-fidelity.test.tsx`. Tái dùng state attachment, validation, popover và modal sẵn có. Kiểm tra source phát hiện menu lật xuống khi có va chạm với textarea dù phía trên đủ không gian; card DOCX là thanh ngang với icon lớn và metadata kích thước; ảnh dùng modal tài liệu.

## REA và tham chiếu

REA `list_browser_targets` không kết nối được CDP `127.0.0.1:9222` (endpoint unreachable). Không có DOM, bounding box hoặc computed CSS Claude được đo; yêu cầu được gửi dưới dạng văn bản không kèm ảnh Claude. Card tài liệu 120×120px và các khoảng cách là **lựa chọn ước lượng theo mô tả**, không phải số liệu Claude. Không có cơ sở đánh giá độ giống trực tiếp.

## Thay đổi

- Card tài liệu gần vuông, tên giới hạn ba dòng ở trên, nhãn loại ở dưới; danh sách cuộn ngang, thanh cuộn ẩn nhưng vùng cuộn vẫn hỗ trợ chuột, touch và bàn phím. Card ảnh tiếp tục dùng thumbnail. Nút xóa hiện khi hover/focus và trên thiết bị touch.
- Menu ưu tiên phía trên khi viewport đủ chỗ, kể cả khi chồng lên nội dung composer; vẫn lật khi không đủ chỗ. Các style menu, animation và reduced motion hiện có được tái sử dụng.
- Ảnh mở lightbox tối, có Escape, focus vào nút đóng và trả focus về card. Ảnh lỗi có thông báo. DOCX/PDF dùng thông báo không hỗ trợ xem trước cùng liên kết tải tệp cục bộ; URL được thu hồi khi đóng/thay preview. Không tải tệp lên server để preview.
- HTML chưa thuộc `COMPOSER_ACCEPT` hay pipeline backend được xác minh; bị từ chối sớm, không render hoặc chạy HTML. Không tuyên bố hỗ trợ HTML.

## Before/After và browser

Ảnh thực tế cùng viewport 1440×900 và 390×844, zoom mặc định: `images/before-1440.png`, `images/after-1440.png`, `images/before-menu-1440.png`, `images/after-menu-1440.png`, và cặp tương ứng 390. Các file DOCX trong ảnh là dữ liệu tổng hợp để quan sát layout, không phải tài liệu thực. `images/after-lightbox.png` là ảnh canvas tổng hợp; `images/after-pdf-fallback.png` ghi giao diện fallback cho một PDF tổng hợp.

Playwright với năm DOCX giả ở 1920×1080, 1440×900, 1366×768, 1024×768, 768×1024, 390×844 và 360×800: card 120×120, menu báo placement `top`, không phát hiện tràn ngang hoặc `pageerror`; preview DOCX có fallback và download, Escape đóng, xóa một tệp giữ văn bản. Chromium mô phỏng touch không chứng minh hành vi thiết bị thật. Image lightbox: nút đóng nhận focus, Escape đóng và trả focus về card. PDF: thông báo fallback và liên kết tải đúng tên. HTML bị từ chối và script thử không chạy. Các script tái lập ở `capture.cjs`, `capture-after.cjs`, `responsive.cjs`, `lightbox.cjs`, `pdf-check.cjs`.

## Verification và giới hạn

- `npm run build`: PASS, có cảnh báo bundle >500 kB.
- Nhóm `attachment-fidelity`, `slice2-composer`, `v944-screen-capture`: **27/27 PASS** trước bổ sung trạng thái lỗi ảnh; build sau bổ sung PASS.
- Bộ frontend đầy đủ: **2038/2046 PASS, 8 FAIL**. Các test lỗi thuộc `axo-error-navigation-matrix` (2), `phase-b-views` (1), `v28-ux-functional` (1), `axo-cross-family-scene3d-acceptance` (2), `axo-pedagogical-presentation-hardening` (1), `semantic-dumb-frontend` (1). Worktree có nhiều thay đổi từ trước; chưa xác định nguyên nhân từng lỗi. Lượt trước vòng này ghi 7 lỗi; không suy diễn khác biệt là do thay đổi mới.
- DOCX/PDF không có nội dung preview và không đọc số trang; HTML không được hỗ trợ. Chưa kiểm tra JPG/WEBP, PDF/DOCX thực, lỗi preview và download trên thiết bị thật, screen capture thực, zoom, tất cả tương tác menu, integration backend hay lint riêng. Chưa có bằng chứng so sánh Claude, không đánh dấu Visual PASS.
- Trong lượt browser, backend local không nghe cổng proxy: `/api/health` và `/api/auth/me` bị từ chối kết nối. Các quan sát preview và layout là client-side, không chứng minh pipeline server.

Technical: **FAIL** (full suite chưa sạch). Functional: **PARTIAL**. Visual: **NOT VERIFIED**. Regression: **FAIL / chưa phân loại hết**. Owner Approval: **PENDING_OWNER_REVIEW**.
