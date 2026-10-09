# general-polygon-base — bàn giao cho LOCAL

Nhánh `feat/general-polygon-base` (rẽ từ `d5287ff7`), đã push lên `origin`; không merge, không PR. Đọc `report.md`.

| commit | nội dung |
|---|---|
| `5e1e3e9` | tiền đăng ký: `plan.md`, `labels.json`, `oracle.py`, amendment §20 — trước mọi thay đổi sản phẩm |
| `4e30a21` | sản phẩm + test: kernel chuỗi góc vuông, bộ đọc hình thang vuông, T10, họ compiler `polygon_base_*`, `product_capability` |
| (commit cuối) | CODE_INDEX, OPEN_ISSUES, quyết định cache, report, handoff, CURRENT_STATE, ROADMAP |

## Việc LOCAL (theo thứ tự)

1. Toàn bộ pytest + T3 (`full-gate.mjs`) trên worktree sạch của nhánh, so baseline local.
2. Đóng băng lại candidate MỘT lần (`backend/scripts/freeze_evaluation_candidate.py` — không có `--help`, gọi là ghi)
   và khai theo thủ tục của run oblique-prism (`inputs/candidate_divergence.json`, `KHAI_LECH`, manifest Tier-A) — bốn
   test danh tính đỏ tới khi làm bước này. Không sửa hash/test tay.
3. Kiểm độc lập quyết định `CACHE_VERSION` 118 (`cache/decision.json`).
4. Người dùng quyết tích hợp; không bắt đầu họ hình tiếp theo trong lượt này. Mục còn mở: `ISSUE-ARCH-G05-REMAINING-BASES`
   (đa giác toạ độ trên compiler là phần rẻ nhất — không đổi bề mặt mô hình), `ISSUE-ARCH-COMPILER-UNTAGGED-RECTANGLE-ASSUMPTION`.
