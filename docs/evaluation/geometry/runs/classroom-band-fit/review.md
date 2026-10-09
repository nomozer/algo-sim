# Duyệt — dải lớp học trên điện thoại (classroom-band-fit)

Trạng thái: **NOT_APPROVED** — chỉ người dùng ghi `APPROVED_BY_USER`. Bản dựng: product `45f5a7f0`, candidate `7f3f0423…`,
`CACHE_VERSION` 118. Cách mở AlgoSim trên điện thoại: `runs/final-acceptance/review.md` §1. Chế độ lớp cần tài khoản
giáo viên + học sinh và backend (`backend/scripts/dev_backend.py up`); bài mẫu offline không có dải lớp.

## 1. Cần anh/chị xem bằng mắt

| # | Mục | Ảnh | Đánh dấu |
|---|---|---|---|
| H-1 | 640×360 ngang, học sinh và giáo viên: hàng trên một dòng (mũi tên quay lại · tên bài cắt «…» · chip lớp · bốn nút công cụ), cột điều khiển trong khung | `images/class-band/student_live__landscape_640.png`, `.../teacher_live__landscape_640.png` | ☐ |
| H-2 | 360×640 dọc, học sinh: chip «● Đang the…» cạnh tên bài, thanh phát trong khung | `images/class-band/student_live__portrait_small.png` | ☐ |
| H-3 | Chip ở 640–667 px ngang chỉ hiện chấm màu + «…» — chấp nhận, hay muốn chữ trạng thái ngắn hơn (quyết riêng) | `report.md` §5 | ☐ |

## 2. Cần thao tác tay trên điện thoại thật (`REQUIRES_INTERACTIVE_HUMAN_CHECK`)

| # | Làm | Đạt khi | Đánh dấu |
|---|---|---|---|
| C-1 | Học sinh, máy ngang: chạm chip lớp → «Em cần hỗ trợ» → chạm ra ngoài | hộp mở/đóng, giơ tay được, chip đổi trạng thái | ☐ |
| C-2 | Giáo viên, máy ngang: chạm chip → «Bắt đầu tiết» / đổi chế độ / «Gọi cả lớp về đây» | dock hoạt động trong hộp, không che nút cần bấm | ☐ |
| C-3 | Xoay máy dọc ↔ ngang khi hộp lớp đang mở | không kẹt hộp, bước/lựa chọn/camera giữ | ☐ |
| C-4 | Bàn phím ngoài (nếu có): Tab tới chip, Enter mở, Escape đóng | tiêu điểm về chip | ☐ |

E-R6 (`mobile-canvas-fit`), F-R7 (`phone-landscape-layout`) và G-1…G-9 (`final-acceptance`) vẫn chờ anh/chị — run này
không đánh dấu chúng.
