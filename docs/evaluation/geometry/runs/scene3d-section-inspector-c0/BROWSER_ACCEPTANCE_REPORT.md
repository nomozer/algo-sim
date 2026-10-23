# Browser acceptance (candidate `ce2aa0f1`)

**Human visual approval: `PENDING`.** Agent không ghi `HUMAN_VISUAL_APPROVED`.

| kiểm | kết quả |
|---|---|
| Adapter /4 consumer, 47 fixture × 1440×900 + 390×844, cảnh thật từ backend `4d3b8849` (`results/adapter4-export-reviewed/fixtures.json`) | **`FRONTEND_CONSUMER_ACCEPTANCE_PASS` 94/94**, source `ce2aa0f1`, `tree_clean: true`, 0 lỗi trang/console, 0 request bị chặn, harness `24e471c2…`, fixtures `1ef4d98c…` ([`verification/browser/receipt.json`](verification/browser/receipt.json)) |
| Mới ở harness: narration `config.frames` không lên trang (F5) | mọi khung × 2 viewport; 16–23 narration ẩn mỗi cảnh, 0 xuất hiện; negative control đỏ đúng (xem `NARRATION_AND_FAIL_CLOSED_REGRESSION.md`) |
| Màn từ chối | **`REFUSAL_SCREEN_CHECK_PASS` 50/50**, source `ce2aa0f1`, `tree_clean: true`, mỗi refusal sau một cảnh served có canvas, 20 PNG ([`verification/refusal/receipt.json`](verification/refusal/receipt.json)) |
| Lượt trung gian (bị thay) | `c3916629` và `d268c222`: 94/94 + 50/50 PASS mỗi lượt ([`verification/superseded/`](verification/superseded/)) |

## Gói ảnh cho Owner (ảnh thật)

| nhóm | trước | sau (`verification/browser/`) | điều cần nhìn |
|---|---|---|---|
| Lăng trụ, inspector đỉnh | `scene3d-plane-section-display-identity/verification/browser-final/CORPUS-DEV10-prism-area-1440.png` (`5ff08439…`): "Các đỉnh: Đỉnh 1 – M – Đỉnh 3" | `CORPUS-DEV10-prism-area-1440.png` (`1374fa65…`): "Các đỉnh: Giao điểm của BB′ và (α) – M – Giao điểm của CC′ và (α)" | ô inspector trái; tiêu đề "Thiết diện bởi (α)", "Mặt phẳng cắt (α)", pill canvas "(α)" |
| Lăng trụ, mobile | `…-390.png` (`742f1290…`) | `…-390.png` (`c816c16a…`) | |
| Chóp, thiết diện tên đủ | `PARA-0-1440.png` (`a5426db2…`) | trùng byte | "Thiết diện MNPQ", "(α)": không đổi |
| Giao điểm suy diễn | `PARTIAL-1of2-construct-1440.png` (`04d35767…`) | trùng byte | "Giao điểm của SC và (α)", Điểm dựng phụ |
| Ratio / residual | `PARA-0` | trùng byte | đáp số ẩn với người học (chính sách) |
| Refusal desktop/mobile | — | `verification/refusal/` | thông điệp người học, không canvas, không mã |

Trên canvas lăng trụ, nhãn H, H1 vẫn hiện tại hai đỉnh, vì đó là điểm dựng phụ có thật. Inspector nay nói đỉnh là giao điểm nào.

## Bản ghi Owner (agent không điền)

| mục | quyết định |
|---|---|
| Inspector lăng trụ (C0) | PENDING |
| Nhãn H/H1 trên canvas tại đỉnh (giữ hay ẩn) | PENDING |
| Refusal | PENDING |
| Desktop / mobile | PENDING |
