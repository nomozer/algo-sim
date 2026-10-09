# unnamed-pyramid-vertex-binding — bàn giao cho LOCAL

Nhánh `fix/unnamed-pyramid-vertex-binding` (từ `a7c56942`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `9f9e66d`, `07afbd4` | nghiên cứu phương án B: nhãn toán học, oracle, probe khả thi ⇒ `ARCHITECTURE_DECISION_REQUIRED` |
| `1bb5c02` | nhãn chính sách A (`policy_a_labels.json`) — trước commit sản phẩm |
| `5669292` | chính sách A (§25): vùng U3 + lý do của cổng, `CACHE_VERSION` 123, khoá, test, ghim |
| (commit cuối) | report, handoff, plan §4, bằng chứng cache, so sánh pytest, chuyển trạng thái, OPEN_ISSUES, CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) — mã sản phẩm
   đổi (`shape_constraint.py`, `assumption_gate.py`, `main.py`). Năm test danh tính candidate đỏ tới bước này
   (`results/pytest_compare.json` `new_red`). Không sửa hash tay.
3. Kiểm độc lập bump 123 (`cache/decision.json`; `diagnostics/probe_c1_variants_a7c56942.log` ↔
   `probe_c1_variants_candidate.log`).
4. Người dùng duyệt tích hợp. Sau đó: quay lại G05 (ROADMAP); phương án B là nâng cấp tuỳ chọn, không mở trong lượt này.
