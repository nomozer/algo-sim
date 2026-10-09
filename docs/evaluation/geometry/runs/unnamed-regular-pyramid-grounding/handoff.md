# unnamed-regular-pyramid-grounding — bàn giao cho LOCAL

Nhánh `fix/unnamed-regular-pyramid-grounding` (từ `ede8d329`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `94b2f89` | tiền đăng ký: plan, 47 hàng C1 + 11 hàng C0, oracle, probe baseline C0 + C1 |
| `12edf57` | bộ đọc (`()` cho chóp đều không tên), cổng (§24 gắn + kiểm), vùng U3, `formation`, `CACHE_VERSION` 122, khoá, test, ghim |
| (commit cuối) | oracle + nhân chứng nhập nhằng, report, handoff, bằng chứng cache, so sánh pytest, chuyển trạng thái, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) theo thủ tục
   hiện hành — mã sản phẩm đổi (`shape_constraint.py`, `assumption_gate.py`, `formation.py`, `main.py`). Các test danh tính
   candidate đỏ tới khi làm bước này (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 122 (`cache/decision.json`; `diagnostics/probe_c0_ede8d329.log` ↔ `probe_c0_candidate.log`,
   `probe_c1_variants_ede8d329.log` ↔ `probe_c1_variants_candidate.log`).
4. Người dùng duyệt; quyết định kiến trúc cho 21 đề gọi tên điểm thiếu toạ độ (phương án a/b/c trong `report.md` §5 và
   `ISSUE-ARCH-UNNAMED-REGULAR-PYRAMID-OUTSIDE-REFUSAL-ZONE`) là việc riêng; không mở việc mới trong lượt này.
