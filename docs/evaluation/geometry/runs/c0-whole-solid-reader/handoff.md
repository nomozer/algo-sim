# c0-whole-solid-reader — bàn giao cho LOCAL

Nhánh `fix/c0-whole-solid-reader` (từ `a1350da3`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `3660523` | tiền đăng ký: plan, 27 nhãn C0, luật tương đương C1, oracle, probe baseline C0 + C1 |
| `7d55153` | bộ đọc (hai lối viết chóp đều, phủ định), `CACHE_VERSION` 121, khoá danh tính, test, ghim |
| (commit cuối) | report, handoff, bằng chứng cache, so sánh pytest, probe candidate, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP, amendment §23 |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) theo thủ tục của
   run trước — mã sản phẩm đổi (`shape_constraint.py`, `main.py`). Các test danh tính candidate đỏ tới khi làm bước này
   (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 121 (`cache/decision.json`; `diagnostics/probe_a1350da3.log` ↔ `probe_candidate.log`,
   `probe_c1_equivalence_a1350da3.log` ↔ `probe_c1_equivalence_candidate.log`).
4. Người dùng duyệt; quyết định về chóp đều không tên (`ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`) là
   việc riêng; không mở việc mới trong lượt này.
