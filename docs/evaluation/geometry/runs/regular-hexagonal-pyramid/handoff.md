# regular-hexagonal-pyramid — bàn giao cho LOCAL

Nhánh `feat/g05-geometry-capability-expansion` (từ `f20caf8a`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `3357994` | khảo sát G05, tiền đăng ký: plan (ma trận năng lực), 17 nhãn, oracle, ca, probe baseline |
| `6c79243` | bộ đọc + T11 + metric lục giác + C0 lục giác, năng lực sản phẩm, `CACHE_VERSION` 124, khoá, test, ghim, đính chính N4 |
| (commit cuối) | report, handoff, bằng chứng cache, so sánh pytest, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh (renderer: cảnh lục giác dùng `chart_metric`, đường
   frontend `scene3d-chart.ts` sẵn có — không đổi mã frontend; T3 xác nhận khung affine hiển thị đúng).
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) — mã sản phẩm
   đổi (`shape_constraint.py`, `assumption_gate.py`, `product_capability.py`, `main.py`). Năm test danh tính candidate đỏ
   tới bước này (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 124 (`cache/decision.json`, `diagnostics/probe_f20caf8a.log` ↔ `probe_candidate.log`).
4. Xem đính chính nhãn N4 (`label_corrections.json`). Người dùng duyệt; không mở việc mới trong lượt này.
