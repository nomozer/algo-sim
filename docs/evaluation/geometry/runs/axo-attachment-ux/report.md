# AXO V9.4.5 — Root-Cause Audit & Attachment UX Completion Report

**Trạng thái: PARTIAL; Owner Approval: PENDING_OWNER_REVIEW.**

## Workspace

Worktree `D:/Documents/projects/axo-geometry-library`, nhánh `feat/axo-geometry-library-verification`, HEAD `d2aeec4a85312b545f6215843dbdd2687eeb009d`; có nhiều thay đổi chưa commit từ trước, được giữ nguyên ngoài phạm vi trực tiếp. Không tạo nhánh/worktree, không commit, merge, push hay deploy.

## Root-cause audit

| Phân loại / tái hiện | Nguyên nhân và vị trí | Sửa / kiểm chứng |
|---|---|---|
| DESIGN MISMATCH: mở DOCX thấy badge, metadata, trạng thái và ba nút | Khối preview cũ trong `ProblemInput.tsx` trộn quản lý attachment vào xem trước | Bỏ khối metadata và footer; Playwright kiểm tra không còn nút đổi/gỡ, vẫn tải xuống. |
| CONFIRMED BUG: PDF dài hơn 32 byte nhưng sai chữ ký vẫn bật gửi | `validateComposerFile` chỉ xét tên/MIME/kích thước | Kiểm tra chữ ký bất đồng bộ, đánh dấu lỗi và khóa gửi; browser tái hiện trước/sau. |
| CONFIRMED BUG: PDF 14 byte được nhận | Chưa kiểm tra độ dài tối thiểu | Từ chối sớm tệp bị cắt ngắn; browser và unit test. |
| POTENTIAL ISSUE: PDF có chữ ký đúng nhưng cấu trúc hỏng | Frontend không có PDF parser; backend mới parse bằng PyMuPDF | Không tuyên bố hợp lệ; giữ fallback và ghi giới hạn. |
| DESIGN MISMATCH: chưa chứng minh pixel parity Claude | REA không kết nối endpoint CDP; không có ảnh Claude trong yêu cầu | Giữ thiết kế hiện có, không tự tuyên bố giống pixel. |

## Luồng và thay đổi

File input → `validateComposerFile` → `ComposerAttachmentItem` trong `ProblemInput` → card → preview → `readAsBase64` → `/api/input/prepare`. Camera/capture cùng state; URL thumbnail được thu hồi khi xóa hoặc kết thúc vòng đời, URL tải tệp được effect thu hồi khi đổi/đóng preview. PDF mới được đánh dấu `loading` khi kiểm tra, `error` nếu sai chữ ký; attachment lỗi hoặc đang kiểm tra chặn gửi. Kiểm tra chữ ký/độ dài **không** chứng minh cấu trúc PDF hợp lệ. Backend kiểm tra magic bytes và parse PDF khi submit; không upload tự động chỉ để preview.

Modal document nay chỉ có tên, nút X, thông báo và download. Loại bỏ handler/state thay tệp không còn caller. Image lightbox và luồng capture một bước được giữ. Không đổi backend, Sidebar, Notification System, Scene3D hay Geometry Engine.

## REA

`list_browser_targets` tại `127.0.0.1:9222` trả endpoint unreachable; không đo DOM hoặc CSS Claude. Card 120×120 là thông số ước lượng từ vòng trước, không phải số đo Claude. Không có bằng chứng đối chiếu pixel.

## Preview matrix

| Loại | Preview / fallback | Test |
|---|---|---|
| DOCX | Chưa render nội dung; download cục bộ | Browser với tệp tổng hợp; không còn nút quản lý |
| PDF hợp lệ | Chưa có parser/viewer client; fallback download | PDF thật do Chromium tạo, 37064 byte; không chứng minh xử lý server |
| PDF hỏng | Từ chối PDF 14 byte; chữ ký sai thành card lỗi, khóa gửi | Browser và unit; cấu trúc hỏng nhưng chữ ký đúng chưa được phát hiện cục bộ |
| HTML | Không được pipeline backend hỗ trợ; từ chối sớm | Không render HTML không tin cậy |
| PNG | Lightbox | Browser với ảnh canvas tổng hợp, Escape và trả focus |
| JPG/WEBP | Dùng cùng nhánh ảnh | Chưa kiểm tra riêng |

## Kiểm chứng

- `npm run build` (gồm `tsc -b`): PASS; Vite cảnh báo chunk >500 kB. Không có script lint riêng trong `package.json`.
- Nhóm test composer, attachment, capture và input: 48/48 PASS sau sửa.
- Full frontend sau các chỉnh sửa cuối: 2044/2049 PASS, 5 FAIL (`axo-error-navigation-matrix` 2; `phase-b-views` 1; `v28-ux-functional` 1; `semantic-dumb-frontend` 1). Không có baseline sạch của worktree chưa commit để quy nguyên nhân; chưa coi regression PASS.
- `git diff --check`: FAIL vì dòng trắng cuối `scene3d-tool-menu.tsx` và `global.css` trong working tree; không sửa tệp Scene3D ngoài phạm vi.
- Browser tám viewport 1920×1080, 1440×900, 1366×768, 1280×800, 1024×768, 768×1024, 390×844, 360×800: năm DOCX tổng hợp, menu top, preview fallback, gỡ riêng giữ text, không tràn ngang / `pageerror`. Touch giả lập không chứng minh thiết bị thật.
- Capture: chỉ kiểm tra nguồn canvas mô phỏng; card xuất hiện, không modal, text giữ nguyên, track ended. Chưa chụp màn hình thật; chưa xác minh retry/submission backend, role Student/Teacher, JPG/WEBP, zoom hay toàn bộ menu/cross-component.
- Ảnh chạy thực tế tại `images/`, gồm `after-docx.png`, `after-valid-pdf.png`, `after-lightbox.png`, `responsive-*.png` và `after-capture-simulated.png`. Ảnh DOCX before do script ghi đè trong lượt xác minh; không dùng làm bằng chứng so sánh trước/sau. Không có ảnh HTML preview vì định dạng không được hỗ trợ.

## Localhost

Frontend Vite đang chạy `npm run dev -- --host 127.0.0.1 --port 3001 --strictPort`, PID lắng nghe 13284 tại thời điểm kiểm tra. `http://localhost:3001/app` trả HTTP 200 và Playwright mở composer, menu, card, preview. HMR phản ánh code sửa. `/api/health` không phản hồi qua proxy: backend chưa sẵn sàng, nên không xác nhận submit thật. Không tắt server sau kiểm tra.

## Acceptance

Technical: PARTIAL (build PASS, full suite/diff check FAIL). Functional: PARTIAL. Visual: NOT VERIFIED. Regression: FAIL / chưa phân loại. Owner Approval: **PENDING_OWNER_REVIEW**.
