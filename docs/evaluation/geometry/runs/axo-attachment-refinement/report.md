# AXO V9.4.7 — Attachment Visual Fidelity & Regression Report

**Trạng thái: PARTIAL. Owner Approval: PENDING_OWNER_REVIEW.**

## 1. Workspace và Git

Repository/worktree `D:/Documents/projects/axo-geometry-library`, nhánh `feat/axo-geometry-library-verification`, HEAD trước và sau `d2aeec4a85312b545f6215843dbdd2687eeb009d`. `localhost:3001/app` phục vụ code hiện tại của worktree. Working tree chứa nhiều thay đổi có từ trước; index ban đầu rỗng.

Chưa tạo commit. `ProblemInput.tsx` và `global.css` lần lượt có khoảng 1.445 và 5.941 dòng diff tổng so với HEAD, gồm các thay đổi trước vòng này, một số ngoài phạm vi attachment. Nền V9.4.6 mà các sửa V9.4.7 phụ thuộc chưa được commit, gồm các component còn untracked. Stage nguyên tệp sẽ đưa theo thay đổi không thuộc vòng này; commit riêng những mảnh mới trên HEAD sẽ không mô tả hệ thống đã kiểm thử. Chủ dự án đã chọn **giữ chưa commit**, không đưa thay đổi nền vào commit WIP. Không stage các thay đổi đó, không tạo commit WIP chỉ chứa báo cáo.

Phân loại: source và test mới `frontend/scripts/attachment-resize.node-test.mjs` giữ trong worktree; các script đo và ảnh trong run này là artifact kiểm thử untracked, không stage; báo cáo được giữ để người dùng xem. Không xóa các artifact trước đó hoặc tệp không rõ nguồn gốc.

## 2. Root cause và sửa

| Issue | Root cause | Files / fix | Verification |
|---|---|---|---|
| Track và mũi tên lộ | Style native và range đặt nền `#efedeb`; thumb custom cố định 48px | `global.css`, `ProblemInput.tsx`: track trong suốt, ẩn nút native trong phạm vi attachment, thumb custom theo tỷ lệ `clientWidth/scrollWidth` | Kéo từ 0 tới 406/406 và về 0; resize 8→9 tệp thay 370→328px, resize 390px thành 78px |
| Tệp mất khi resize với textarea rỗng | Listener draft trong `ProblemInput.tsx` coi bất kỳ store update nào khi có attachment là reset | Chỉ reset khi chuyển khỏi trạng thái navigation/workspace trước đó; test browser chính thức | 8→9 tệp, 1440→390px vẫn giữ 9 |
| X lớn | Vòng nhìn thấy 22px | Vòng 20px và icon 10px, giữ vùng bấm 32px; dành chỗ cho tên | Click X xóa đúng file, modal không mở, draft giữ nguyên |
| DOCX quá lớn | Kích thước 760×560 thử nghiệm V9.4.6 | Modal 520×380px, giới hạn viewport | 1440×900 đo 520×380; 390px và 360px đo rộng 358/328, cao 380 |
| Ảnh quá lớn và lệch tâm | Max size theo gần toàn viewport; wrapper lớn hơn ảnh | Giới hạn 800×600px, wrapper ôm ảnh, nút đóng gần ảnh | 1600×800 hiển thị 800×400, căn giữa x=320 tại viewport 1440; ảnh 800×1600 hiển thị 300×600 |
| Guard scrollbar bắt cả selector cục bộ | Regex cũ quét mọi `::-webkit-scrollbar-button` dù yêu cầu chỉ cho attachment | `scrollbar-ownership.test.ts` tiếp tục cấm ẩn nút toàn trang, xác nhận ngoại lệ được scope vào `.composer-files-row` | Test guard PASS; thao tác kéo được kiểm tra riêng |

Không sửa Sidebar, Notification System, Scene3D hay Geometry Engine. Giữ PDF.js và preview PDF có sẵn; không cài thêm thư viện trong vòng này.

## 3. Claude / visual

REA không kết nối được CDP `127.0.0.1:9222`; không đo được DOM/CSS Claude. Tệp yêu cầu không chứa ảnh Claude; 20px, 520×380 và 800×600 là kích thước thử nghiệm theo mô tả, không phải số đo Claude. Không khẳng định pixel parity hoặc Visual PASS.

Ảnh browser 1440×900, zoom mặc định: `images/before-scroll.png`, `images/after-scroll.png`, `images/before-docx.png`, `images/final-docx.png`, `images/final-image.png`, `images/final-portrait.png`, `images/after-hover.png`, `images/after-pdf.png`. Fixture DOCX/ảnh và PDF tạo bởi Chromium, không phải tệp chủ dự án. `images/after-<width>.png` ghi các viewport thử. Các script trong run là artifact tái lập, không phải production code.

**Correction:** trong vòng này, hai script của run V9.4.6 đã vô tình ghi đè `axo-attachment-scroll/images/after-drag-end.png` và `images/mobile-swipe.png`. Byte trước đó là `NOT_RECOVERABLE` trong working tree; các ảnh hiện tại không được dùng như bản gốc V9.4.6. Chuỗi đính chính được ghi trong `docs/EVIDENCE_INDEX.md`. Các ảnh mới của vòng này nằm tại `axo-attachment-refinement/images/`.

## 4. Functional / tests

- **PASS browser giả lập:** bảy viewport yêu cầu 1920×1080, 1366×768, 1280×800, 1024×768, 768×1024, 390×844, 360×800: 8 file, đi đến cuối và về đầu bằng phím, đóng preview giữ vị trí, draft giữ nguyên, không tràn ngang trang hoặc `pageerror` trong lượt đo.
- **PASS browser giả lập:** kéo thumb điều khiển `scrollLeft` 0→406/406→0; touch emulation vuốt 198px; xóa file không mở modal; PDF hai trang hiển thị canvas và `2 trang`. Không chứng minh tương tác trên thiết bị thật.
- **PASS browser giả lập:** menu mở phía trên, Escape và click ngoài đóng; heading không dịch chuyển trong phép đo desktop 1440×900.
- `node --test scripts/attachment-resize.node-test.mjs`: **1/1 PASS**. Test cần server tại `localhost:3001/app` hoặc `AXO_TEST_URL`.
- Nhóm Vitest liên quan, CODE_INDEX, token và scrollbar: **70/70 PASS**. `npm run build` (gồm typecheck): **PASS**, cảnh báo chunk >500 kB. Không có script lint riêng.
- Full suite đang được ghi nhận sau khi chạy; `git diff --check` FAIL do dòng trắng cuối `scene3d-tool-menu.tsx` và `global.css` trong working tree đã có. Không sửa Scene3D ngoài phạm vi.
- **NOT TESTED:** file PDF đa dạng hoặc được bảo vệ, camera/chụp màn hình thật, backend submit/retry, thiết bị mobile thật, vai trò Student/Teacher, so sánh trực tiếp Claude.

## 5. Localhost / acceptance

`http://localhost:3001/app` trả HTTP 200; Vite phục vụ worktree hiện tại và được giữ chạy. Backend local không phản hồi qua proxy, nên upload/preview chỉ được kiểm tra client-side và chưa xác minh submit thật.

Functional: **PARTIAL**. Visual: **NOT VERIFIED**. Regression: **chưa PASS**. Commit: **NOT CREATED**, vì không thể stage tách biệt an toàn khỏi các thay đổi nền chưa commit. Owner Approval: **PENDING_OWNER_REVIEW**.
