# Kiểm kê bảng thông tin của xưởng mô phỏng — regular-square-pyramid-w04

Đọc từ mã tại `f3db0f6f` (đầu lượt W4) bằng `grep` trên `frontend/src/simulations/domains/geometry/`. Bảng
"thông tin" là vùng chữ người học mở ra để đọc hay chọn, nằm trên hoặc cạnh khung hình. Không tính menu ngắn và
tooltip — yêu cầu không đòi chúng kéo được.

| Bảng | Mở bằng | Cơ chế trước W4 (f3db0f6f) | Cơ chế sau W4 |
|---|---|---|---|
| Chi tiết đối tượng (ô soi) | chọn một vật (trên hình, cây, đại lượng, nhãn số đo) | `<aside class="geo3d-soi">`; ≥ 1100 px thành **cột lưới** cạnh khung (canvas co lại, camera đổi tỉ lệ — H-W2-3); khổ hẹp chảy dưới khung | `BangNoi panel="soi"`; đóng = bỏ chọn |
| Xem đề | chip «Xem đề» | **một** ngăn chung `geo3d-ngan` phủ mép phải; mở ngăn khác thì đóng ngăn này; mobile phủ lên hình | `BangNoi panel="de"`, độc lập |
| Các thành phần của hình | chip «Thành phần» | cùng ngăn chung | `BangNoi panel="thanh-phan"`, độc lập; cây theo bước, nhóm thu gọn |
| Các đại lượng | chip «Đại lượng» | cùng ngăn chung; chọn một đại lượng **đóng** ngăn | `BangNoi panel="dai-luong"`, độc lập; chọn giữ bảng mở |
| Các bước dựng | nút «Các bước dựng» ở thanh điều khiển | `BangNoi` (W2), vị trí do trình phát giữ | `BangNoi panel="cac-buoc"`; vị trí do host giữ; mô tả bước dưới mục hiện tại |

Ngoài phạm vi: thẻ lời giải (`scene3d-solution.tsx`) nằm dưới khung trong dòng chảy, không phủ hình — giữ nguyên.
Nút nổi «Tách khối» / «Xem lại toàn hình» (`.geo3d-noi`) là điều khiển, không phải bảng; các bảng tránh chúng.

Một cơ chế: `scene3d-floating-panel.tsx` (`BangNoiHost` giữ vị trí từng bảng + thứ tự lớp; `BangNoi` kéo tiêu đề,
phím mũi tên, Escape, về mặc định, thu gọn, kẹp khi đổi cỡ; khổ hẹp tĩnh trong dòng chảy). Không cơ chế riêng theo họ hình.
