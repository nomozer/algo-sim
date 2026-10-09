# regular-prisms — bàn giao cho LOCAL

Nhánh `feat/g05-regular-prisms` (từ `ea85216b`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `680d830` | khảo sát G05 lăng trụ đều, tiền đăng ký: plan (ma trận năng lực), 25 nhãn, oracle, ca, probe baseline |
| `00770c3` | bộ đọc + T12 + metric lăng trụ + C0 lục giác đều / cạnh bên lăng trụ, năng lực sản phẩm, `CACHE_VERSION` 125, khoá, test, ghim, probe ứng viên + probe chuyển trạng thái ngoài nhãn |
| `d8b9da7` | sửa phát hiện ở so sánh toàn bộ pytest: "lăng trụ xiên … đều" không phát T12; ghim "đều" chưa đọc của `test_shape_constraint` chuyển sang lăng trụ tứ giác đều (cập nhật có chủ đích) |
| (commit cuối) | report, handoff, bằng chứng cache, chuyển trạng thái, so sánh pytest, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh. Frontend KHÔNG đổi mã: cảnh lăng trụ đều dùng
   `chart_metric` qua `scene3d-chart.ts` sẵn có (như T8/T11). Cần T3/trình duyệt xác nhận khung affine 60° của lục giác
   và lưới tam giác hiển thị thành đa giác đều thật, cạnh bên vuông góc đáy (chưa kiểm trên Cloud).
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py`) — mã sản phẩm đổi
   (`shape_constraint.py`, `assumption_gate.py`, `product_capability.py`, `main.py`). Năm test danh tính candidate đỏ tới
   bước này (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 125 (`cache/decision.json`, `diagnostics/probe_extra_ea85216b.log` ↔ `probe_extra_candidate.log`:
   6 hàng C0 served → refused).
4. Kiểm toán học độc lập 13 hàng dương (metric Gram từ độ dài của đề tại A, B, C, A′; V = (3√3/2)a²h | (√3/4)a²h).
   Người dùng duyệt; không mở việc mới trong lượt này.
