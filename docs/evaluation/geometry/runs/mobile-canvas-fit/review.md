# Gói duyệt hình — D5: canvas vừa hình trên điện thoại (mobile-canvas-fit)

Trạng thái: **NOT_APPROVED** — chỉ người dùng ghi `APPROVED_BY_USER`. Ảnh là ảnh thật của bộ đo ở candidate cuối
(`7f3f0423…`, product `c9bcdcdb`, `CACHE_VERSION` 118), đo tại `90921f53` trong worktree tách rời sạch; đường dẫn tương
đối từ thư mục run này; tập ảnh chọn TRƯỚC lượt đo (`inputs/REVIEW_SET.json`). Số đo: `results/MOBILE_LAYOUT_PROBE.json`;
trước sửa: `diagnostics/baseline_38a19c65/`.

## 1. D5 — cần anh/chị xem và quyết định

| # | Mục | Ảnh | Đánh dấu |
|---|---|---|---|
| E-R1 | Điện thoại dọc 390×844, tám họ: canvas cao vừa hình — không còn dải trắng lớn trên/dưới; hình giữ nguyên cỡ (bề ngang không đổi) | `images/mobile/<họ>/portrait/layout.png` | ☐ |
| E-R2 | Mở «Các bước dựng» / «Đại lượng» trên điện thoại: hình và bảng cùng thấy được, không phải cuộn qua lại | `images/mobile/<họ>/portrait/steps_open.png`, `.../quantity_open.png` | ☐ |
| E-R3 | Hình ràng theo chiều cao (chóp tứ giác `rectangular-pyramid`): canvas giữ trọn chiều cao như trước (519 px) — không trần, không thu nhỏ; với họ này không còn chỗ trống để thu, bảng dài hơn ~240 px sẽ phải cuộn | `images/mobile/rectangular-pyramid/portrait/layout.png`, `.../steps_open.png` | ☐ |
| E-R4 | Bảng bước dài: bước đang xem luôn nằm trong vùng nhìn của bảng khi tua (trước sửa bị giấu ở 19/40 lượt, kể cả desktop) | `images/mobile/cross-section/*/steps_last.png` | ☐ |
| E-R5 | Khổ khác không đổi: điện thoại nhỏ 360×640 (canvas ở sàn 320 px), điện thoại ngang 844×390 (bố cục desktop, canvas ở sàn — thanh phát dưới nếp gấp, như trước), màn thấp, desktop | `images/mobile/regular-triangular-pyramid/{portrait_small,landscape}/layout.png`, `images/focus/<họ>/{low,desktop}/focus_layout.png` | ☐ |
| E-R6 | Tương tác thật trên điện thoại (cần thao tác tay): xoay hình, chọn trên hình, tua/phát khi bảng bước mở, mở nhiều bảng | — `REQUIRES_INTERACTIVE_HUMAN_CHECK` | ☐ |

## 2. Mục của gói cũ — nay có ảnh ở candidate cuối

| Mục cũ | Ảnh ở candidate cuối | Ghi chú |
|---|---|---|
| exact-dimensions R8 · regular-triangular-pyramid-w01 R5 | `images/regular-triangular-pyramid/negative/*/desktop/refusal.png` | lời từ chối thiếu kích thước sau `f967ba24` (nguyên nhân `SOURCE`, nêu đại lượng thiếu) |
| W5 R1 · R2 · R3 | `images/focus/<họ>/{desktop,low,mobile}/focus_layout.png`, `images/focus/regular-square-pyramid/mobile/menu_hien_thi.png` | khung nhìn ban đầu ở giữa (sau RTP-W01) + canvas D5 trên mobile |
| W5 R9 | `images/<họ>/desktop/neutral_final.png` của triangular-pyramid, triangular-prism, rectangular-pyramid, cross-section; `results/OCCLUSION_MEASUREMENT.json` → `human_review_pending` | bốn cảnh occlusion W14 có ảnh ở candidate cuối |

## 3. Sau khi duyệt

Ghi quyết định vào sổ người duyệt. Merge vào `main`, push, xoá nhánh là việc của một lượt riêng có lệnh — run này không
merge, không push, không mở PR.
