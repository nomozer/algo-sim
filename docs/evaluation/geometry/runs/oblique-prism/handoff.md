# oblique-prism — bàn giao cho LOCAL

Nhánh `feat/oblique-prism` (rẽ từ `ba995887`), đã push lên `origin` (không merge, không PR). Đọc `report.md` trước.

## 1. Commit

| commit | nội dung |
|---|---|
| `e39ed32` | tiền đăng ký: `plan.md`, `labels.json`, `oracle.py`, amendment §19 (T9) — trước mọi thay đổi sản phẩm |
| `0fe4edc` | sản phẩm + test: T9, họ compiler `oblique_prism_volume`, lời kể vectơ (chỉ compiler), `product_capability` |
| `cd591dd` | CODE_INDEX, OPEN_ISSUES, bằng chứng `CACHE_VERSION` (không bump) |
| (commit cuối) | `report.md`, `handoff.md`, `results/pytest_compare.json`, CURRENT_STATE, ROADMAP |

## 2. Kết quả kiểm trên Cloud (worktree tách rời sạch)

- pytest tại `cd591dd`: 7151 passed / 135 failed / 4 errors; baseline sạch `ba995887` cùng máy: 7104 / 131 / 4.
  131 đỏ + 4 lỗi có sẵn TRÙNG HỆT (môi trường Cloud: bằng chứng ngoài kho, đường dẫn, lịch sử git); 4 đỏ MỚI đều là
  danh tính candidate (mục 3). `results/pytest_compare.json`.
- `test_oblique_prism.py` 51/51; red-before trên `ba995887`: 39 đỏ.
- Demo 5/5, bề mặt sập 6/6; 49/49 fixture Tier-A trùng byte.
- KHÔNG chạy: T3 `full-gate.mjs`, vitest, build, trình duyệt (frontend không cài trên Cloud; mã frontend không đổi).

## 3. Việc LOCAL phải làm (theo thứ tự)

1. Chạy T3 (`full-gate.mjs`) và toàn bộ pytest trên worktree sạch của nhánh — so với baseline local.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py`, ghi đè
   `docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`) và khai candidate mới ở tài liệu nghiệm thu
   (`test_thesis_acceptance_matrix::test_C2b`) — bốn test danh tính đỏ cho tới khi làm bước này. Cloud KHÔNG làm vì
   đây là quyết định nghiệm thu. (⚠️ script không có `--help`: gọi trơn là ghi luôn.)
3. Người dùng xem `report.md` §3–§5 và quyết: (a) tích hợp; (b) có mở lát G04 kế tiếp (chân ở trung điểm/trọng tâm —
   đổi hợp đồng ⇒ cần ngân sách đo live, `ISSUE-ARCH-OBLIQUE-PRISM-FOOT-VOCABULARY`) hay sang họ khác của §0.2.

`CACHE_VERSION` giữ 118 (`cache/decision.json`). `LLM_ONLY` mặc định. 0 lượt gọi model.
