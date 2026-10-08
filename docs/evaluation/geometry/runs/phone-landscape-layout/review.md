# Gói duyệt hình — điện thoại ngang, điện thoại nhỏ 360 px (phone-landscape-layout)

Trạng thái: **NOT_APPROVED** — chỉ người dùng ghi `APPROVED_BY_USER`. Ảnh là ảnh thật của bộ đo ở candidate cuối
(`7f3f0423…`, product `95a56a17`, `CACHE_VERSION` 118), đo tại `221ec0a0` (lần đo 3, trọn mọi bước trong một lượt) trong
worktree tách rời sạch; đường dẫn tương đối từ thư mục run này; tập ảnh chọn TRƯỚC lượt đo (`inputs/REVIEW_SET.json`).
Số đo: `results/MOBILE_LAYOUT_PROBE.json`; trước sửa: `diagnostics/baseline_f6ebe946/`.

## 1. Cần anh/chị xem và quyết định

| # | Mục | Ảnh | Đánh dấu |
|---|---|---|---|
| F-R1 | Điện thoại ngang 844×390, tám họ: thanh điều khiển thành cột bên phải canvas — ba nút phát, thanh trượt, «Các bước dựng» và hai nút xem đều trong khung (trước: thanh phát dưới mép 37 px); canvas 320 px như trước ⇒ hình giữ cỡ; không nút nào phủ lên hình | `images/mobile/<họ>/landscape/layout.png` | ☐ |
| F-R2 | Điện thoại ngang hẹp 667×375 và ngang có thanh trình duyệt 844×340: hàng trên một dòng (tên bài cắt «…»), cột điều khiển trong khung; đáy canvas (dải trống dưới hình) rơi dưới mép vì sàn 320 px được giữ | `images/mobile/<họ>/landscape_small/layout.png`, `images/mobile/{cross-section,cuboid}/landscape_browser/layout.png` | ☐ |
| F-R3 | Bảng bước dài khi ngang: bảng nổi trên canvas như desktop, bước đang xem thấy được; bảng che một phần canvas hẹp — thu gọn/kéo được (cơ chế bảng nổi W4) | `images/mobile/cross-section/{landscape,landscape_small}/steps_last.png` | ☐ |
| F-R4 | Điện thoại nhỏ 360×640: ba nút phát chung một hàng ⇒ thanh phát trong khung (trước: ba hàng, rơi dưới mép); mở «Các bước dựng» vẫn thấy hình + điều khiển | `images/mobile/<họ>/portrait_small/layout.png`, `images/mobile/regular-triangular-pyramid/portrait_small/steps_open.png` | ☐ |
| F-R5 | Xoay máy giữa chừng (390×844 → 844×390, 360×640 → 640×360): cùng bước, cùng lựa chọn, cùng camera; điều khiển trong khung | `images/mobile/regular-triangular-pyramid/{portrait,portrait_small}/rotated.png` | ☐ |
| F-R6 | Có từ trước, không sửa: lăng trụ tam giác trên màn thấp — nhãn rời canvas sau cú xoay; «Xem lại toàn hình» trả đúng góc nhìn ban đầu | `images/mobile/triangular-prism/low/after_orbit.png`, `.../after_overview.png` | ☐ |
| F-R7 | Tương tác thật trên điện thoại ngang (cần thao tác tay): chạm nút trong cột, kéo/thu gọn bảng nổi, xoay hình bằng ngón tay | — `REQUIRES_INTERACTIVE_HUMAN_CHECK` | ☐ |

E-R6 của gói `mobile-canvas-fit` (tương tác thật trên điện thoại dọc) vẫn chờ anh/chị.

## 2. Sau khi duyệt

Ghi quyết định vào sổ người duyệt. Merge vào `main`, push, xoá nhánh là việc của một lượt riêng có lệnh — run này không
merge, không push, không mở PR.
