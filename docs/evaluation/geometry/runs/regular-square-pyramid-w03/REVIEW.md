# Gói duyệt hình — chóp tứ giác đều (W1 + W2 + W3)

Run `regular-square-pyramid-w03` · nhánh `feat/regular-square-pyramid` · bằng chứng đo tại `a5d233ce` (product `45beaed3`,
candidate `5dec4572…`, `CACHE_VERSION` 114) trong worktree tách rời sạch, đường dẫn có dấu cách, 0 lượt gọi model.

Trạng thái duyệt: **NOT_APPROVED** — chỉ người dùng ghi `APPROVED_BY_USER`. Mọi ảnh dưới đây là ảnh thật của bộ đo;
đường dẫn tương đối từ thư mục run này.

## 1. Cần anh/chị xem và quyết định

| # | Mục | Ảnh | Đánh dấu |
|---|---|---|---|
| R1 | Chóp đều: khung cuối trung tính — SO nét đứt + ký hiệu ⊥ tại O; AC, BD đã ẩn sau khi có O; không có mặt phẳng phụ | `images/regular-square-pyramid/desktop/final_neutral.png` | ☐ |
| R2 | Chọn thể tích: "V = 1/3 × S(ABCD) × SO = 16" ở ô soi, nhãn d(S,(ABC)) = 3, S(ABCD) = 16; mặt phẳng đáy hiện vì nằm trong chuỗi của đại lượng | `images/regular-square-pyramid/desktop/selected_volume.png` | ☐ |
| R3 | **(W3, H-W2-4)** «Các bước dựng» còn 8 bước — không còn bước «Mặt phẳng qua A, B, C» đứng yên khi hình phụ tắt | `images/regular-square-pyramid/desktop/steps_panel_floating.png`, `images/regular-square-pyramid/mobile/steps_sheet_open.png` | ☐ |
| R4 | **(W3, H-W2-4)** Bật «Hình phụ»: AC, BD và mặt phẳng qua A, B, C hiện ở khung cuối | `images/regular-square-pyramid/desktop/auxiliary_shown.png` | ☐ |
| R5 | **(W3, H-W2-2)** "Tính độ dài đoạn SH": bước cuối «Dựng đoạn SH», chọn đáp số ⇒ nhãn d(S, H) = 3√6 bám trên đoạn SH (nét đứt vì bị mặt bên che) | `images/cross-section/served/projection_correct/desktop/served.png` (+ `mobile/served.png`) | ☐ |
| R6 | Bảng nổi «Các bước dựng» desktop: kéo, về mặc định; mobile: trong dòng chảy, thu gọn | `images/regular-square-pyramid/desktop/steps_panel_dragged.png`, `images/regular-square-pyramid/mobile/steps_sheet_collapsed.png` | ☐ |
| R7 | Nhãn theo bước ("Hiện tất cả"), lưới | `images/regular-square-pyramid/desktop/show_all.png`, `grid_on.png`; `images/triangular-pyramid/desktop/` | ☐ |
| R8 | Diễn tiến dựng hình từng bước của chóp đều (8 khung) | `images/regular-square-pyramid/desktop/formation/formation_step_0..7.png`, `images/regular-square-pyramid/FILMSTRIP.png` | ☐ |
| R9 | Sáu họ cũ không đổi (tổng quan theo họ) | `images/<họ>/SHEET.png`, `images/overview/INDEX.png` | ☐ |
| R10 | Bốn cảnh occlusion W14 vẫn chờ người duyệt (product = oracle ở mọi trạng thái; không phải lỗi theo quyết định U2) | `results/OCCLUSION_MEASUREMENT.json` → `human_review_pending`; `images/<họ>/hidden-edges/` | ☐ |

## 2. Đã đạt (đo thật ở máy local)

- Tiếp nhận: `origin/feat/regular-square-pyramid` = `fe68b4ca` (đúng EXPECTED_CLOUD_HEAD); W1 head `e821b9b5` là tổ tiên;
  0 commit riêng ở local; fast-forward. Xoá `frontend/public/favicon.svg` của người dùng giữ nguyên, không stage.
- Nghiệm thu W2 nguyên trạng tại `fe68b4ca` (`diagnostics/baseline_fe68b4ca/`): T3 `FULL_PRODUCT_GATE_PASS`
  (pytest 7152 passed / 1 skipped, vitest 1089/1089, build, demo 5/5, bề mặt sập 6/6); cổng danh tính xanh; test node
  đường dẫn Windows có dấu cách qua; trình duyệt 14/14 lượt dương xanh trọn — `camera_settled_rotated_neutral` lắng ở mọi
  lượt, `causal_restore` thiết diện qua ở desktop và mobile. Hai cổng đỏ trên cloud là lỗi môi trường (SwiftShader).
- Sau hai bản sửa W3, đo lại tại `a5d233ce`: suite 7/7 họ PASS, 14/14 lượt dương xanh trọn; đầu dò W2 14/14; occlusion
  pass, 0 lỗi; phát lại PASS với "mọi bước dựng đổi hình" KHÔNG còn miễn trừ; 68 crop, 0 bất đồng oracle, 0 chủ sở
  hữu trùng. Tại commit tài liệu `4c0f9219`: T3 `FULL_PRODUCT_GATE_PASS` (pytest 7156 passed, vitest 1091/1091, build,
  demo 5/5, bề mặt sập 6/6) và mọi cổng danh tính xanh (`HANDOFF.md` §2).

## 3. Đánh giá bốn câu hỏi của W2

| Câu | Phân loại | Việc đã làm |
|---|---|---|
| H-W2-4 bước mặt phẳng phụ không đổi hình | **LỖI** — vi phạm bất biến W12, và W2 đã nới ba cổng để nó qua | Đã sửa (`824924d7`): mặt phẳng phụ chỉ để đo không mở bước dựng; gỡ miễn trừ ở cả ba cổng |
| H-W2-2 đáp số trên đoạn chưa dựng | **LỖI** — mất nhãn đáp số mà W18 đã đăng ký; W2 hạ kỳ vọng thành "vắng" (PC1-W2) | Đã sửa (`45beaed3`): dựng đoạn đề hỏi trước đáp số; khôi phục kỳ vọng W18; `CACHE_VERSION` 113 → 114 theo bằng chứng row |
| H-W2-3 ô soi làm canvas co lại (≥ 1100 px) | **LỰA CHỌN TRÌNH BÀY** — không sai giá trị, không mất thao tác; causal restore đo ở trạng thái chọn bằng nhau | Chưa đổi. Đề nghị: giữ cột trong nhánh này, quyết định ở đợt UI kế tiếp (`ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS` vẫn OPEN) |
| H-W2-5 tên nhóm "Giao điểm của AC và BD" | **LỰA CHỌN TRÌNH BÀY** — tên đúng với phép dựng; "Dựng tâm O của đáy" cần nhãn ngữ nghĩa từ backend (đổi envelope) | Chưa đổi. Đề nghị: giữ, hoặc anh/chị chọn đổi tên ở đợt sau |

Đề nghị hoãn ở trên **chưa được người dùng chấp nhận** — cần anh/chị xác nhận.

## 4. Còn mở / giới hạn

- **H-W2-1 (chặn merge):** duyệt hình — mục 1.
- Giới hạn của bản sửa H-W2-2: nếu đoạn được hỏi nằm trên một cạnh đã có (vd SM với M là trung điểm SA), đoạn mới vẽ
  chồng lên cạnh ấy. Corpus hiện không có ca này; ghi ở `OPEN_ISSUES.md` (`ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE`).
- Nhãn khoảng cách hai điểm hiển thị "d(S, H) = 3√6", không phải "SH = 3√6" — ký hiệu vẫn đúng; đổi là lựa chọn trình bày.
- Hai worktree đo (`D:/tmp/rsp w03`, `D:/tmp/rsp w03b`) đã gỡ bằng `git worktree remove` không ép buộc, sau khi dọn đầu
  ra đã chép vào run bằng `git clean` giới hạn trong thư mục run của chính worktree ấy.

## 5. Sau khi duyệt

Ghi quyết định vào sổ người duyệt; nếu duyệt thì merge vào `main` + push + xoá nhánh là việc của một lượt riêng có
lệnh của anh/chị — W3 không merge, không push, không mở PR.
