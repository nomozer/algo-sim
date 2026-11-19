# AXO V9.4.4 — kiểm toán trước thay đổi

Worktree `D:/Documents/projects/axo-geometry-library`, nhánh `feat/axo-geometry-library-verification`, HEAD `d2aeec4a85312b545f6215843dbdd2687eeb009d`; các thay đổi chưa commit là baseline của người dùng. Ảnh trước chụp nhầm landing `/`, không có ảnh composer trước thay đổi. Các báo cáo V9.4.2/V9.4.3 không tìm thấy bằng tên tệp; test tương ứng hiện có trong `frontend/src/components/__tests__/`.

| Requirement | Trạng thái hiện tại | Evidence | Files liên quan | Hướng xử lý |
|---|---|---|---|---|
| Attachment Cards | PARTIAL | Card ngang nhỏ, state và preview hiện có | ProblemInput.tsx, global.css | Tái dùng state, cải thiện kích thước |
| One-step Capture | NOT DONE | Thành công mở preview xác nhận | ProblemInput.tsx, ScreenCaptureDialog.tsx | Đính kèm trực tiếp |
| Header theo từng màn hình | PARTIAL | Có workspace header và draft tab | SimulationWorkspace.tsx | Kiểm tra theo ngữ cảnh |
| Sidebar Toggle Icon | NOT DONE | Hai biểu tượng hiện có | LeftSidebar.tsx | Dùng SVG panel chung |
| Logo Hover | PARTIAL | CSS cần kiểm tra tương tác | global.css, LeftSidebar.tsx | Loại bỏ nền hover nếu có |
| Heading Typography | PARTIAL | Quy tắc typography hiện hữu | global.css, HomeView.tsx | Điều chỉnh theo viewport |
| Sidebar Title Width | PARTIAL | Test V9.4.3 có kiểm tra CSS | LeftSidebar.tsx, global.css | Bảo toàn và kiểm tra lại |
| Conversation Lifecycle | PARTIAL | Test V9.4.3 hiện có | store.ts, history.ts | Chạy regression |
| Responsive | PARTIAL | Chưa đo đủ viewport | global.css | Playwright và báo cáo giới hạn |

Thực hiện test hành vi trước, tái sử dụng validation/state và kiểm chứng frame; sau đó kiểm tra card, shell, build và báo cáo. Không gửi request live tới AI.
