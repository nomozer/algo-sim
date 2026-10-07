# Gói duyệt hình — chóp tam giác đều + tứ diện đều, sửa giao diện D1–D4 (regular-triangular-pyramid-w01)

Nhánh `feat/regular-square-pyramid` · bằng chứng đo ở lượt đo 3 (`1bb11018`; product `1e90ca0e`, candidate `92c9e198…`,
`CACHE_VERSION` 116), worktree tách rời sạch, đường dẫn có dấu cách, 0 lượt gọi model.

Trạng thái duyệt: **NOT_APPROVED** — chỉ người dùng ghi `APPROVED_BY_USER`. Ảnh là ảnh thật của bộ đo; đường dẫn tương
đối từ thư mục run này. Tập ảnh được chọn TRƯỚC lượt đo (`inputs/REVIEW_SET.json`, mỗi mục một yêu cầu); ảnh khác chỉ được
giữ khi oracle thị giác cần hoặc họ có lượt thất bại (`results/IMAGE_POLICY.json` ghi sha256 cả ảnh đã bỏ). "Trước" là ảnh
W5 cùng fixture, khổ và góc nhìn: `../regular-square-pyramid-w05/images/...`.

## 1. Cần anh/chị xem và quyết định

| # | Mục | Ảnh (sau) | Trước (W5) | Đánh dấu |
|---|---|---|---|---|
| R1 | Họ mới: chóp tam giác đều cạnh đáy 3√2, chiều cao √3 ở bước cuối — đáy nằm ngang (phép xoay hiển thị), trung tuyến AI, BJ, trọng tâm G, đường cao SG nét khuất, ký hiệu vuông góc tại G | `images/regular-triangular-pyramid/desktop/neutral_final.png` | — (họ mới) | ☐ |
| R2 | Họ mới sau cú xoay đã chấm: nét khuất đổi đúng | `images/regular-triangular-pyramid/desktop/rotated_neutral.png` | — | ☐ |
| R3 | Ô soi họ mới: V = 1/3 · S(ABC) · SG, S(ABC) = 9√3/2, SG = √3, V = 9/2; chọn S(ABC) tô đáy, chọn SG tô đoạn SG | `images/regular-triangular-pyramid/desktop/detail_*.png`, `.../selected_*.png` | — | ☐ |
| R4 | Bảng bước họ mới (trung tuyến, trọng tâm, chiều cao) | `images/rerun/regular-triangular-pyramid/desktop/steps_panel_floating.png` | — | ☐ |
| R5 | Tứ diện đều cạnh 3√2 phục vụ V = 9; bốn ca từ chối đúng (thiếu chiều cao, trọng tâm sai danh tính, chiều cao không có trong đề, cạnh bằng 0) | `images/regular-triangular-pyramid/served/regular_tetrahedron/*/served.png`, `images/regular-triangular-pyramid/negative/*/desktop/refusal.png` | — | ☐ |
| R6 | **D1** — thể tích thiết diện: ô soi hiện giá trị + «Đo trên» (W5: chỉ tiêu đề và nút) | `images/cross-section/desktop/detail_volume.png` | `../regular-square-pyramid-w05/images/cross-section/desktop/detail_volume.png` | ☐ |
| R7 | **D2** — chọn S(ABCD): đáy được tô; chọn d(S, (ABC)): đoạn SO được tô, vẫn nét khuất | `images/regular-square-pyramid/desktop/selected_area.png`, `.../selected_length.png` | cùng tên dưới `../regular-square-pyramid-w05/images/regular-square-pyramid/desktop/` | ☐ |
| R8 | **D3** — biểu tượng trước/phát/sau căn giữa, cùng khe với chữ | `images/focus/regular-square-pyramid/desktop/focus_layout.png` | `../regular-square-pyramid-w05/images/focus/regular-square-pyramid/desktop/focus_layout.png` | ☐ |
| R9 | **D4** — bốn bước nối cạnh thiết diện mang tên theo mặt; bước dữ kiện không in lời kể lần hai | `images/rerun/cross-section/desktop/steps_panel_floating.png`, `images/rerun/regular-square-pyramid/desktop/steps_panel_floating.png` | cùng tên dưới W5 | ☐ |
| R10 | **Khung nhìn ban đầu (sửa ở lượt này, ảnh hưởng MỌI họ)** — hình nay nằm GIỮA canvas (W5: lệch trái 65–100 px vì hộp bao dự phòng lọt vào khung ở bước 0); chiều cao hình không đổi; xoay quanh tâm hình nên không văng khỏi khung | `images/<họ>/desktop/neutral_final.png` | `../regular-square-pyramid-w05/images/<họ>/desktop/neutral_final.png` | ☐ |
| R11 | **D5 — CHƯA sửa, cần quyết định:** mobile còn dải trắng trên/dưới hình và bảng mở dưới nếp gấp; bốn phương án ở `OPEN_ISSUES.md` (`ISSUE-ARCH-MOBILE-CANVAS-WHITESPACE-AND-PANEL-SCROLL`) | `images/focus/regular-square-pyramid/mobile/focus_layout.png`, `images/rerun/regular-square-pyramid/mobile/steps_sheet_open.png`, `images/focus/regular-triangular-pyramid/*/focus_layout.png` | — | ☐ |
| R12 | **D6** — zoom W5 giữ; không đặt lại camera qua menu, đổi cỡ, toàn màn hình, bảng nổi | đầu dò W05 (`results/W05_FOCUS_PROBE.json`), đầu dò W04 (`results/W04_PANELS_PROBE.json`) | — | ☐ |

## 2. Đã đạt (đo thật, lượt đo 3)

Suite 8/8 họ (16/16 lượt dương, 31/31 ca âm) · đầu dò W02 16/16 (chạy lại riêng) · W04 24/24 (23 ở lượt chính + cross_section
3/3 chạy lại riêng) · W05 24/24 · occlusion pass (cảnh chờ người duyệt như W5) · phát lại 16/16 · 72 crop cạnh khuất, 0 bất
đồng oracle, 0 owner trùng. Bốn ảnh bảng bước (R4, R9, R11) lấy từ lượt chạy lại W02 (`images/rerun/`) vì đầu dò W02 của lượt
chính treo trước khi chụp chúng. Ba lượt đo trước và lý do: `MEASUREMENT_ATTEMPTS.json`.

## 3. Sau khi duyệt

Ghi quyết định vào sổ người duyệt. Merge vào `main`, push, xoá nhánh là việc của một lượt riêng có lệnh — run này không
merge, không push, không mở PR.
