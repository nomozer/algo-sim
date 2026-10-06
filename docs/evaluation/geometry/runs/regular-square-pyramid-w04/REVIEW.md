# Gói duyệt hình — bảng thông tin chung, bố cục, chọn thành phần (W4)

Run `regular-square-pyramid-w04` · nhánh `feat/regular-square-pyramid` · bằng chứng đo tại `103494c4` (product `53e4bec5`,
candidate `8a27a58b…`, `CACHE_VERSION` 115) trong worktree tách rời sạch, đường dẫn có dấu cách, 0 lượt gọi model.

Trạng thái duyệt: **NOT_APPROVED** — chỉ người dùng ghi `APPROVED_BY_USER`. Ảnh là ảnh thật của bộ đo; đường dẫn tương
đối từ thư mục run này. Khung nhìn thật của trình duyệt đo: desktop 1422×804 (xin 1440×900), màn thấp 1348×554 (xin
1366×650), mobile 390×844 — bộ đo ghi `innerWidth/innerHeight`, không ghi cỡ đã xin.

## 1. Cần anh/chị xem và quyết định

| # | Mục | Ảnh | Đánh dấu |
|---|---|---|---|
| R1 | Năm bảng cùng mở (ô soi, Thành phần, Đại lượng, Các bước dựng, Đề bài): đều nổi, không chiếm cột, không bảng nào che tiêu đề bảng khác; canvas và camera không đổi khi mở/đóng/chọn | `images/review/regular-square-pyramid/desktop/panels_all_open.png` (+ 6 họ khác cùng tên) | ☐ |
| R2 | Kéo bảng bằng tiêu đề (không xoay hình); thu cửa sổ 1100×700: mọi bảng còn trong khung, bảng bị phủ được đặt lại lên trên | `.../desktop/panels_dragged.png`, `.../desktop/panels_resized_1100x700.png` | ☐ |
| R3 | Canvas lấy chiều cao còn lại, thanh phát/bước sát đáy; «Bước n/N» trong thanh, «Các bước dựng» bên phải thanh; không còn dòng lời kể dài dưới thanh; mô tả bước nằm dưới mục hiện tại trong bảng | `.../desktop/layout_neutral.png`, `.../desktop/layout_resized_1100x760.png`, `.../low/layout_low.png` | ☐ |
| R4 | Mobile: bảng là tấm trong dòng chảy dưới hình (nút đầu bảng 44 px, thu gọn được); hình vẫn xoay được; canvas cao theo khung nhìn — hình giới hạn theo bề ngang nên phía dưới canvas còn khoảng trống: giữ, hay đặt trần chiều cao canvas trên mobile? | `.../mobile/layout_mobile.png`, `.../mobile/sheets_open.png`, `.../mobile/figure_after_orbit.png` | ☐ |
| R5 | Chọn thẳng trên hình: bấm một đỉnh ⇒ chọn + ô soi; cây tự mở đúng nhóm và đánh dấu vật; kéo để xoay không đổi lựa chọn | `.../desktop/direct_select_tree.png` | ☐ |
| R6 | Cây «Thành phần» theo bước: nhóm thu gọn mặc định (có mũi tên), chỉ vật đã dựng — không còn tên vật tương lai ở dạng mờ | `.../desktop/tree_by_step.png` | ☐ |
| R7 | SM (M trung điểm SA): không còn nét thứ hai đè lên SA; chọn SM chỉ sáng khúc S–M (nét đứt vì SA khuất), M–A giữ trung tính | `images/sm-overlap-after/sm_neutral.png`, `sm_selected.png`; trước sửa: `diagnostics/sm_overlap/before/` | ☐ |
| R8 | Câu chữ: «Thiết diện (T) là đa giác 4 đỉnh, giao của mặt phẳng (α) với khối S.ABCD.» thay câu cũ có "chop", "mp" và danh từ lặp | `diagnostics/scene_hash/SCENE_DIFF.json`; bảng «Các bước dựng» ở họ thiết diện `images/review/cross-section/desktop/panels_all_open.png` | ☐ |
| R9 | Bảy họ không đổi phần hình (nhãn theo bước, nét khuất, tô, phát lại) | `images/<họ>/SHEET.png`, `images/overview/INDEX.png`, `images/<họ>/desktop/formation/` | ☐ |
| R10 | Bốn cảnh occlusion W14 vẫn chờ người duyệt (product = oracle ở mọi trạng thái; không tính lỗi theo U2) | `results/OCCLUSION_MEASUREMENT.json` → `human_review_pending`; `images/<họ>/hidden-edges/` | ☐ |

## 2. Đã đạt (đo thật ở máy local, lần đo 4)

- Suite 7/7 họ, 14/14 lượt dương xanh trọn; đầu dò W2 14/14; đầu dò W4 **21/21** (7 họ × desktop · màn thấp · mobile:
  bảng nổi, bố cục, chọn trên hình, cây); ca SM: chọn được, chỉ khúc S–M sáng, 0 owner trùng; occlusion pass (4 cảnh
  chờ duyệt, U2); phát lại pass; 68 crop cạnh khuất, 0 bất đồng oracle, 0 owner trùng.
- Ba lần đo trước không dùng để nghiệm thu, đều ghi lại (`MEASUREMENT_ATTEMPTS.json`): lần 1 bắt canvas WebGL không
  theo khung trên mobile; lần 2 đỏ một cổng lắng camera (camera đã đứng yên, trình duyệt vẽ quá ít khung) — lần 3 chạy
  lại trọn vẹn thì xanh; soát lần 3 bắt khúc S–M không sáng (khối bị làm dịu kéo theo). Hai lỗi sản phẩm đã sửa có test
  đỏ trước; không cổng nào bị nới.
- Cổng T3 và cổng danh tính tại commit tài liệu: `HANDOFF.md` §2.

## 3. Còn mở / giới hạn

- **Duyệt hình (chặn merge):** mục 1, gồm câu hỏi R4 (chiều cao canvas trên mobile).
- Bộ đo trình duyệt chạy ở khung nhìn thật nhỏ hơn cỡ xin (1422×804 thay 1440×900) — kết luận theo khung thật.
- Khi năm bảng cùng mở trên khung 1100×700, các bảng chồng một phần lên nhau và che phần lớn hình; mọi bảng vẫn còn
  bấm được tiêu đề (đưa lên trên) — đó là giới hạn chủ ý, không dành cột.
- `ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS` và `ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE`: RESOLVED trong
  `docs/OPEN_ISSUES.md`, chờ duyệt hình.

## 4. Sau khi duyệt

Ghi quyết định vào sổ người duyệt; nếu duyệt thì merge vào `main` + push + xoá nhánh là việc của một lượt riêng có lệnh
của anh/chị — W4 không merge, không push, không mở PR.
