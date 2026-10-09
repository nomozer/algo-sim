# c0-whole-solid-grounding — bàn giao cho LOCAL

Nhánh `fix/c0-whole-solid-grounding` (từ `9762f441`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `3bbd8c2` | tiền đăng ký: plan, 28 nhãn, oracle, amendment §22, probe baseline |
| `139aa1a` | hàng `edge_all` (kind đã đăng ký, thiếu nhãn) + probe baseline của nó — trước mọi sửa sản phẩm |
| `c11e8c9` | sửa C0 (§22), `CACHE_VERSION` 120, khoá danh tính, test, ghim |
| (commit cuối) | report, handoff, bằng chứng cache, so sánh pytest, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) theo thủ tục của
   run trước. Các test danh tính candidate đỏ tới khi làm bước này (`results/pytest_compare.json` `new_red`). Không sửa
   hash tay.
3. Kiểm độc lập bump 120 (`cache/decision.json`, `diagnostics/probe_9762f441*.log` ↔ `diagnostics/probe_c11e8c9.log`).
4. Người dùng duyệt; không mở việc mới trong lượt này.
