# Browser acceptance và gói ảnh cho Owner (sau sửa A/B)

**Human visual approval: `PENDING`.** Agent không ghi `HUMAN_VISUAL_APPROVED`. Ảnh không phải thẩm quyền toán học
(engine certificate + oracle mới là).

## 1. Kết quả máy (cảnh thật từ backend đã sửa)

| kiểm | nguồn | kết quả |
|---|---|---|
| browser acceptance Adapter /4 | `frontend/scripts/check-adapter4-browser.mjs` với `results/adapter4-export-final/fixtures.json` | **`FRONTEND_CONSUMER_ACCEPTANCE_PASS`** 94/94 hàng (47 fixture × 1440×900, 390×844), source `57138dbb`, `tree_clean: true`, 0 lỗi trang/console, 0 request bị chặn, harness `0585ed19…`, fixtures `cf39de44…` — [`verification/browser-final/receipt.json`](verification/browser-final/receipt.json) |
| màn từ chối | `publication-safety-remediation/check_refusal_screens.mjs` | **`REFUSAL_SCREEN_CHECK_PASS`** 50/50, source `57138dbb`, `tree_clean: true`, mỗi refusal nạp ngay sau một cảnh served có canvas — [`verification/refusal-final/receipt.json`](verification/refusal-final/receipt.json) |
| refusal của backend mới | `export_fixtures.py` | 25 refusal **bằng** Session 5 (route_d và envelope), nên harness refusal dùng fixture Session 5 vẫn đúng đối tượng |

Harness kiểm từng khung: không phụ thuộc treo, không vật sớm/lạ/trùng, không đáp số sớm, tiến độ thiết diện, điểm suy
diễn hiện là *Điểm dựng phụ* (8 hàng), không lộ tên nội bộ, không tràn ngang.

## 2. Gói ảnh (thật, không dựng minh hoạ)

"Trước" = Session 5 `hybrid-offline-consumer/results/browser-final-9f06ed2b/` (backend cũ, cùng harness).
"Sau" = `verification/browser-final/` (backend `41c7e6f8`; ảnh trùng byte với lượt trung gian ở `65cbdd6f`).

| nhóm | trước | sau | điều cần nhìn |
|---|---|---|---|
| Lăng trụ, nhãn mặt phẳng | `CORPUS-DEV10-prism-area-1440.png` (`f1d7a5ff…`): pill canvas "(MHH1)" | `CORPUS-DEV10-prism-area-1440.png` (`5ff08439…`): pill "(α)" | nhãn mặt cắt trên canvas |
| Lăng trụ, inspector thiết diện | tiêu đề "Thiết diện HMH1"; "Các đỉnh: Đỉnh 1 – M – Đỉnh 3"; "Mặt phẳng cắt (MHH1)" | tiêu đề "Thiết diện bởi (α)"; "Các đỉnh: Đỉnh 1 – M – Đỉnh 3" (**không đổi**, xem `SCENE3D_PROVENANCE_COMPATIBILITY.md` §4); "Mặt phẳng cắt (α)" | ô inspector bên trái |
| Lăng trụ, mobile | `…-390.png` (`2fb4cdd4…`) | `…-390.png` (`742f1290…`) | |
| Chóp có thiết diện (đỉnh đều có tên) | `PARA-0-1440.png` (`e720bf3c…`): pill "(MHH1)", "Mặt phẳng cắt (MHH1)" | `PARA-0-1440.png` (`a5426db2…`): pill "(α)", "Mặt phẳng cắt (α)"; "Thiết diện MNPQ" giữ nguyên | |
| Chóp, mobile | `PARA-0-390.png` (`d0995c7c…`) | `PARA-0-390.png` (`ecb2d1be…`) | |
| Giao điểm suy diễn (`DERIVED_FRESH`) | `PARTIAL-1of2-construct-1440.png` (`04d35767…`) | **trùng byte** với trước | "Giao điểm của SC và (α) — Điểm dựng phụ"; khung này không hiện phần bị đổi |
| Ratio / residual | `PARA-0` (`g_ratio = 1/8`, `g_res = 7a³/24`) | như trên | đáp số **ẩn** trong UI người học (chính sách simulation-first): ảnh không có số, đúng chủ ý |
| Refusal desktop/mobile | `publication-safety-remediation/refusal-screens/` (ở `76c6795c`) | `verification/refusal-final/` (20 PNG, 10 mã × 2 viewport) | thông điệp người học, không canvas, không mã |

Ghi chú khi xem: dải cam "Máy chủ thiếu khóa AI" là do harness giả lập `/api/health` (`allow_live_ai: false`);
H, H1 vẫn hiện trên canvas vì là điểm dựng phụ có thật của planner (ở lăng trụ, chúng nằm đúng tại hai đỉnh thiết diện).

## 3. Bản ghi Owner (agent không điền)

| mục | quyết định | ghi chú |
|---|---|---|
| A: nhãn (α) canvas + inspector | PENDING | |
| B: "Thiết diện bởi (α)" và đại lượng diện tích | PENDING | |
| B: "Đỉnh 1 – M – Đỉnh 3" (chọn C1/C2/C3) | PENDING | |
| B′: nhãn đại lượng plane-only | PENDING | |
| Refusal | PENDING | |
| Desktop / mobile | PENDING | |
