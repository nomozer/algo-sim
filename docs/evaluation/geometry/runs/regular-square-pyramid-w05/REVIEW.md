# Gói duyệt hình — chế độ tập trung, công cụ nhóm, bỏ thẻ lời giải (W5)

Run `regular-square-pyramid-w05` · nhánh `feat/regular-square-pyramid` · bằng chứng đo tại `f01df0e5` (product `82225a7b`,
candidate `5e1c0639…`, `CACHE_VERSION` 115) trong worktree tách rời sạch, đường dẫn có dấu cách, 0 lượt gọi model.

Trạng thái duyệt: **NOT_APPROVED** — chỉ người dùng ghi `APPROVED_BY_USER`. Ảnh là ảnh thật của bộ đo; đường dẫn tương
đối từ thư mục run này. Khung nhìn thật: desktop 1422×804 (xin 1440×900), màn thấp 1348×554 (xin 1366×650), mobile 390×844.
"Trước" là ảnh W4 ở `../regular-square-pyramid-w04/images/review/<họ>/<khổ>/` (cùng fixture, trùng byte).

## 1. Cần anh/chị xem và quyết định

| # | Mục | Ảnh trước (W4) → sau (W5) | Đánh dấu |
|---|---|---|---|
| R1 | Không gian mô phỏng lấp trang: không còn thanh đăng nhập/điều hướng; hàng trên mảnh «← Trang chủ · tên bài · Đề bài · Khám phá · Hiển thị · Thêm»; canvas lấy phần còn lại; thanh phát + «Bước n/N» + «Các bước dựng» sát đáy, trang không cuộn | `../regular-square-pyramid-w04/images/review/<họ>/desktop/layout_neutral.png` → `images/focus/<họ>/desktop/focus_layout.png` | ☐ |
| R2 | Màn thấp 1366×650 và đổi cỡ: hình + điều khiển cùng trong khung, không khoảng trắng dưới thanh phát | `../regular-square-pyramid-w04/images/review/<họ>/low/layout_low.png` → `images/focus/<họ>/low/focus_layout.png`, `.../focus_resized.png` | ☐ |
| R3 | Mobile 390×844: bốn nút nhóm lưới 2 × 2, hộp menu trải theo bề rộng (không tràn mép), hình rồi điều khiển, trang cuộn được, không trần chiều cao canvas | `../regular-square-pyramid-w04/images/review/<họ>/mobile/layout_mobile.png` → `images/focus/<họ>/mobile/focus_layout.png`, `.../menu_hien_thi.png` | ☐ |
| R4 | Menu «Hiển thị»: ba công tắc (Hiện tất cả số đo, Hình phụ khi có, Lưới nền) + chú giải màu (Đang xét, Vừa dựng, Dữ kiện số, Đại lượng trung gian, Hình liên quan) | `images/focus/<họ>/desktop/menu_hien_thi.png` | ☐ |
| R5 | Thẻ lời giải dưới thanh phát đã gỡ; đáp số và mọi đại lượng chọn ở «Khám phá → Đại lượng» (nhãn + giá trị + vai trò nhân quả khi đang chọn), công thức + «Từ dữ kiện đề cho / Tính trực tiếp từ» ở ô soi | `images/<họ>/desktop/quantity_picker.png`, `images/<họ>/desktop/detail_volume.png`, `images/<họ>/desktop/solution_causal_selected.png` | ☐ |
| R6 | Nút quay lại về đúng trang đã vào (ở bộ đo: Trang chủ), thanh trên toàn cục trở lại | `images/focus/<họ>/desktop/after_back.png` | ☐ |
| R7 | Bảng nổi W4 vẫn đúng trong bố cục mới (nhiều bảng cùng mở, kéo, đổi cỡ) | `images/review/<họ>/desktop/panels_all_open.png`, `panels_resized_1100x700.png` | ☐ |
| R8 | Bảy họ không đổi phần hình (nhãn theo bước, nét khuất, tô, phát lại) | `images/<họ>/SHEET.png`, `images/overview/INDEX.png` | ☐ |
| R9 | Bốn cảnh occlusion W14 vẫn chờ người duyệt (product = oracle ở mọi trạng thái; U2) | `results/OCCLUSION_MEASUREMENT.json` → `human_review_pending` | ☐ |
| R10 | Đề `AB = 4, SA = SB = SC = SD = 3` nay được phục vụ `V = 16/3` (trước: từ chối oan) — backend, không có ảnh; kiểm bằng `pytest tests/geometry/test_regular_square_pyramid.py -q` | `REPORT.md` §2 | ☐ |

## 2. Đã đạt (đo thật, lần đo 4)

Suite 7/7, 14/14 lượt dương; đầu dò W2 14/14; W4 21/21; W05 21/21 (không thanh trên toàn cục, không cuộn ngang, hàng trên
không đè canvas, trang vừa một màn ở desktop/màn thấp, ba menu chuột + bàn phím, chú giải, lưới, «Tách khối» theo cảnh,
bước + lựa chọn + góc nhìn giữ qua menu · đổi cỡ · toàn màn hình, quay lại); occlusion pass; phát lại 14/14; 68 crop
cạnh khuất 0 bất đồng. Ba lần đo trước: `MEASUREMENT_ATTEMPTS.json`.

## 3. Sau khi duyệt

Ghi quyết định vào sổ người duyệt; merge vào `main` + push + xoá nhánh là việc của một lượt riêng có lệnh — W5 không
merge, không push, không mở PR.
