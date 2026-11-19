# AXO V9.4.6 — Attachment Scroll & Preview Fidelity Report

**Owner Approval: PENDING_OWNER_REVIEW. Visual: NOT VERIFIED.**

## Workspace và nguyên nhân

Worktree `D:/Documents/projects/axo-geometry-library`, nhánh `feat/axo-geometry-library-verification`, HEAD `d2aeec4a85312b545f6215843dbdd2687eeb009d`; worktree đã chứa nhiều thay đổi chưa commit trước vòng này. Không tạo nhánh/worktree, không commit, merge, push hay deploy.

| Issue | Root cause | Fix / verification |
|---|---|---|
| Scrollbar attachment ẩn | `global.css` dùng `scrollbar-width: none` và ẩn WebKit; tám card có `scrollWidth > clientWidth` nhưng không có chỉ báo kéo | Khôi phục native scrollbar; trên trình duyệt dùng overlay scrollbar bổ sung range điều khiển đồng bộ `scrollLeft`. Kéo chuột tới cuối và về đầu; keyboard và touch giả lập được kiểm tra. |
| Nút xóa quá lớn | `.file-card-remove` vẽ nền trên toàn vùng 32px | Vùng bấm 32px giữ nguyên; vòng nhìn thấy 22px bằng pseudo-element, dùng shadow token. |
| PDF không có thumbnail/số trang | V9.4.5 chỉ có fallback, chưa có parser client | Thêm `PdfPreview.tsx`, PDF.js 6.5.438, worker và cleanup; chỉ tải thư viện khi mở PDF. PDF một/hai trang và PDF hỏng được kiểm tra bằng browser. |
| DOCX modal nhỏ | Kích thước modal document cũ | Modal document tối đa 760×560px theo viewport, fallback và download ở giữa; không thêm renderer DOCX. |
| Vị trí đóng lightbox | Nút đặt theo góc viewport | Neo nút vào vùng ảnh; kiểm tra ảnh 1600×800 và 800×1600. |

Không thay Sidebar, Notification System, Geometry Engine, Scene3D hoặc backend. `docs/CODE_INDEX.md` được cập nhật cho component mới. Package và lockfile thêm PDF.js; asset worker khoảng 1,27 MB và module PDF khoảng 501 kB được tách khỏi bundle chính và chỉ dùng cho preview.

## REA và visual

REA `list_browser_targets` không kết nối được endpoint CDP `127.0.0.1:9222`; không có DOM/computed style Claude và không có ảnh tham chiếu Claude trong tệp yêu cầu. Kích thước card, modal và nút là lựa chọn thử nghiệm, không phải phép đo Claude. Không đánh dấu Visual PASS.

Ảnh tại `images/`: `before-1440.png`, `after-1440.png` (thử native scrollbar trước khi thêm điều khiển overlay), `start.png`, `middle.png`, `after-drag-end.png`, `hover.png`, `after-docx.png`, `after-pdf.png`, `after-image.png`, `after-image-portrait.png`, `mobile-swipe.png`, `end-*.png`. Ảnh tệp DOCX và ảnh bitmap là fixture tổng hợp; PDF được tạo hợp lệ bằng Chromium, không phải tài liệu người dùng. Các script cùng thư mục ghi cách thực hiện.

## Functional results

- **PASS trong browser giả lập:** 8 tệp, `scrollLeft` từ 0 tới giới hạn và về 0 bằng phím ở 1920×1080, 1440×900, 1366×768, 1280×800, 1024×768, 768×1024, 390×844, 360×800; tệp cuối nằm trong vùng nhìn; đóng preview giữ vị trí; không có tràn ngang toàn trang hoặc `pageerror` trong lượt đo.
- **PASS trong browser giả lập:** kéo thanh điều khiển từ 0 tới 406/406 và về 0; touch emulation vuốt đạt `scrollLeft=197`; xóa tệp giữa, thêm tệp mới, tới tệp mới và giữ text. Một tệp không overflow không tạo thanh điều khiển bổ sung.
- **PARTIAL:** PDF một và hai trang hiển thị thumbnail, số trang tương ứng và tải xuống; PDF hỏng có thông báo và download. Chưa kiểm tra tập PDF thực đa dạng, tài liệu mã hóa, rất lớn, hoặc accessibility đầy đủ.
- **PARTIAL:** DOCX fallback và ảnh ngang/dọc hiển thị; chưa có so sánh Claude, chưa kiểm tra điện thoại thật hoặc mọi loại PNG/JPG/WEBP. HTML vẫn bị từ chối vì backend chưa hỗ trợ.
- **NOT TESTED:** capture màn hình thật, submit/retry với backend, kiểm tra scrollbar native trên mọi hệ điều hành, kiểm thử toàn bộ role và zoom.

## Testing và localhost

- `npm run build` (bao gồm typecheck): PASS; Vite cảnh báo chunk >500 kB.
- Nhóm test liên quan, đồng bộ CODE_INDEX và token: **66/66 PASS**.
- Full suite sau sửa: **2044/2049 PASS, 5 FAIL**: `axo-error-navigation-matrix` (2), `phase-b-views` (1), `v28-ux-functional` (1), `semantic-dumb-frontend` (1). Cùng năm test lỗi đã được ghi ở V9.4.5; chưa có baseline sạch cho toàn bộ worktree nên chưa kết luận nguyên nhân. Hai lỗi phát sinh của vòng này (CODE_INDEX và shadow token) đã sửa và xác minh.
- `git diff --check`: FAIL do dòng trắng cuối `scene3d-tool-menu.tsx` và `global.css` đã có trong working tree; không sửa Scene3D ngoài phạm vi. Không có script lint riêng.
- `http://localhost:3001/app` là Vite đang chạy từ đúng worktree; browser đã kiểm tra upload, cuộn, DOCX, PDF và image. Backend local chưa phản hồi, nên không xác minh submit. Server frontend được giữ chạy.

Functional: PARTIAL. Visual: NOT VERIFIED. Regression: chưa PASS. Owner Approval: **PENDING_OWNER_REVIEW**.
