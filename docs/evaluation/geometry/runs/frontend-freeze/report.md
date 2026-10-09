# frontend-freeze — quyết định hoãn frontend và trạng thái nghiệm thu thật

Máy local, 0 lượt gọi model, không đổi mã. Ghi theo chỉ đạo của người dùng ngày 2026-10-09; agent không ghi
`APPROVED_BY_USER`.

## 1. Quyết định của người dùng (tóm tắt chỉ đạo trong phiên)

Người dùng đã xem bộ ảnh nghiệm thu C1–C6, **chưa hài lòng với chất lượng giao diện**, và quyết định **tạm dừng phát triển
frontend** để ưu tiên kiến trúc hình học mới và backend. Đây là **hoãn hoàn thiện UI, KHÔNG phải xác nhận** mọi chức năng và
trải nghiệm đã đạt. Frontend sẽ được thiết kế lại có chủ đích ở giai đoạn sau. Ngoại lệ duy nhất: lỗi nghiêm trọng khiến không
kiểm chứng được năng lực hình học hoặc không dùng được chức năng cốt lõi.

Hoãn (không làm tiếp): thiết kế lại header/toolbar/chip lớp; tối ưu thẩm mỹ desktop/mobile; chỉnh bảng nổi vì bố cục; chụp
ảnh/contact sheet mới; mở rộng chế độ lớp học; chạy lại bộ đo trình duyệt đã có bằng chứng hợp lệ.

## 2. Trạng thái nghiệm thu — giữ nguyên, không đổi thành PASS

| Mục | Trạng thái |
|---|---|
| C1–C6 (ảnh) | người dùng ĐÃ XEM; **chưa phê duyệt** chức năng/giao diện là hoàn chỉnh |
| P1–P4 (điện thoại thật) | **PENDING** — chưa có bằng chứng thử trên máy thật |
| P5–P6 (lớp học trên điện thoại) | **PENDING** — backend/tài khoản lớp chưa sẵn sàng (Docker tắt) |
| UX debt (nhãn rời canvas màn thấp, bảng nổi che canvas khi ngang, chip lớp 640–667 px, header/toolbar mobile) | **OPEN / DEFERRED** |
| W05 | lượt chính **23/24** (một trang không tải); kiểm lại riêng không ghép |
| W14 (bốn cảnh) | oracle tự động đạt (sản phẩm = oracle; tái tạo tập đã duyệt 4/4) ≠ duyệt bằng mắt; registry đã duyệt chưa có — issue OPEN |

## 3. Merge — điều kiện theo quy định

`AGENTS.md §2`: chỉ merge khi người dùng cho phép **rõ ràng** VÀ mọi điều kiện nghiệm thu của việc đã đạt. Với P1–P6 PENDING
và C1–C6 chưa phê duyệt, điều kiện ấy **chưa đạt** theo nghĩa đen. Phương án hợp lệ duy nhất mà không sửa chính sách: người dùng
**định nghĩa lại điều kiện nghiệm thu** cho lần tích hợp này thành «baseline tạm thời có ngoại lệ», bằng một tin nhắn tường
minh; agent chép nguyên văn vào `runs/frontend-freeze/APPROVAL.md` (tiền lệ `runs/cuboid-merge/APPROVAL.md`: lời người dùng
nguyên văn, nhóm nào ACCEPTED, giới hạn nào được hoãn và **vẫn mở**). Tệp ấy phải nói rõ: tích hợp mã đã ổn định; KHÔNG công bố
frontend hoàn thiện; P1–P6 vẫn PENDING; UX debt OPEN; C1–C6 «đã xem, chưa phê duyệt chất lượng».

Kỹ thuật (đã kiểm 2026-10-09, sau `git fetch --prune origin`): `origin/main` = `main` = `38d41588`, là tổ tiên của HEAD ⇒
**fast-forward được** (175 commit, 0 bị tụt lại); candidate `7f3f0423…` (102 file) khớp; `CACHE_VERSION` 118; `LLM_ONLY`;
không có thay đổi ngoài `docs/` từ commit đã qua T3 (`ac55186e`) ⇒ T3 vẫn phủ đúng cây mã. Cổng trên cây tích hợp theo tiền lệ
`cuboid-merge`: candidate, cache, `LLM_ONLY`, tài liệu — không chạy lại T3/bộ đo trình duyệt.
