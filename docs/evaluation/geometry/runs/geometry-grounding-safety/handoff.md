# geometry-grounding-safety — bàn giao cho LOCAL

Nhánh `fix/geometry-grounding-safety` (từ `e6c3cf68`), đã push; không merge, không PR.

| commit | nội dung |
|---|---|
| `17353c3` | tiền đăng ký: plan, labels, oracle, amendment §21 |
| `fbade46` | sửa C0 + compiler, `CACHE_VERSION` 119, test, đính chính nhãn R06, bằng chứng cache |
| (commit cuối) | report, handoff, OPEN_ISSUES (hai issue RESOLVED), CODE_INDEX, CURRENT_STATE, ROADMAP |

## Việc LOCAL

1. Toàn bộ pytest + T3 `full-gate.mjs` trên worktree sạch của nhánh.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`) theo thủ tục của
   hai run trước (`inputs/candidate_divergence.json`, `KHAI_LECH`, manifest Tier-A). Năm test danh tính đỏ tới khi làm
   bước này (gồm `test_cache_version_khop_nguon`: candidate ghi 118). Không sửa hash tay.
3. Kiểm độc lập bump 119 (`cache/decision.json`, hai log probe).
4. Người dùng duyệt; không mở việc mới trong lượt này.
