# Review độc lập — LOCAL, 2026-10-14

Người review: một subagent riêng (cùng mô hình, ngữ cảnh mới), chỉ đọc (`git show`, grep, đọc file/receipt), không chạy
build/test trong lúc T3 chạy. Phạm vi: `3db3a50f`, `632d7e15`, `eea6f3df`, `bfda732c`. **Phán quyết: NONBLOCKING.**
Độc lập người đánh giá: một phần — khác phiên, cùng họ mô hình; không phải người.

| # | phát hiện (NONBLOCKING) | xử lý |
|---|---|---|
| 1 | Producer điểm lạ không có phép kiểm ⇒ `all({})` qua | sửa `d4327342`: thất bại `producer_has_a_check`; lỗi tiêm `unknown_producer` |
| 2 | Không kiểm H, H1 dùng hai đường KHÁC nhau / M, H, H1 không thẳng hàng | sửa `d4327342`; lỗi tiêm `same_line_twice` |
| 3 | Đoạn thiết diện từng bước chỉ kiểm nằm trong mặt — đoạn vượt cạnh vẫn qua | sửa `d4327342`: tập đoạn = đúng tập cạnh vòng; lỗi tiêm `segment_past_edge` |
| 4 | Loại bước `?` không báo; `zip` cắt im khi lệch số | sửa `d4327342`; lỗi tiêm `unknown_step_kind` |
| 5 | Biến thể metamorphic không chạy kiểm bước | sửa `d4327342` |
| 6 | FAIL hình không vào `failures` của audit | sửa `d4327342`; `before/audit` nay đỏ đúng 19 bước học |
| 7 | Không đối chiếu `objectsAt` (frontend) với `formation.visible_ids` (backend) | sửa `d4327342` trong `--playback`; 35/35 bằng nhau trước và sau |
| 8 | Không kiểm chiều ngược: nhãn đang hiện không được chồng nhau | sửa `d4327342`; 0 cặp |
| 9 | Receipt trình duyệt không ghi commit | sửa `d4327342`: `git_head`, `git_dirty_paths` (là của CÂY ĐANG CHẠY; bundle harness đo xem `report.md` §5) |
| 10 | Kiểm chấm đỉnh lặp lại T của chính renderer — không độc lập | sửa lời: chứng cứ độc lập cho B/C là `world_checks` (TᵀT = G mọi cặp) + kiểm neo nhãn (đường `qRef·world → cam.project` của renderer vs `view·model·T·chart` của bộ đo) |
| 11 | "Thanh trượt thật" là `<input range>` của harness theo bước trace, không phải nút bước học của sản phẩm | sửa lời trong `report.md`; khung = `anchor` như `scene3d-playback.tsx` |
| 12 | Hộp nhãn của bộ đo chép quy ước CSS của sản phẩm, không đo `getBoundingClientRect` | ghi giới hạn; không đổi |
| 13 | `hopDiem` vẫn đọc `offsetWidth` sau khi ghi style (trái chú thích) | ghi lại; không sửa vì là mã sản phẩm (đóng băng lại + T3); không phải lỗi |
| 14 | Luật mới giấu nhiều hơn khi hai nhãn rộng trung bình > ~66 px; bộ đo bố cục chỉ đo khung đầu; orbit gate không cho tín hiệu | ghi rủi ro hồi quy còn mở (`report.md` §5) |
| 15 | Commit RED `632d7e15` truyền `w`/`h` vào kiểu chưa có ⇒ `tsc -b` đỏ ở commit ấy | ghi lại; HEAD xanh; không viết lại lịch sử |
| 16 | `CODE_INDEX`, `CURRENT_STATE`, `AI_CONTEXT_BUNDLE`, `STATUS_LEDGER` còn ghi product `2b42eb40` | ghi ngược trong commit tài liệu cuối |

Xác nhận của review: phép metric đúng (chỉ covector + tỉ số affine + diện tích Gram), sửa nhãn đúng và tất định, freeze
đúng luật (chỉ commit đổi, tree hash `c2ac6dbe…` giữ), số liệu báo cáo khớp receipt; kết luận đứng cho ba cảnh.
