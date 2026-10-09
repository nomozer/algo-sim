# classroom-band-fit — handoff

## 1. Trạng thái bàn giao

- `READY_FOR_USER_ACCEPTANCE`. Nhánh `feat/regular-square-pyramid`, chỉ local; không push, merge, PR, xoá nhánh hay viết lại
  lịch sử.
- Product `45f5a7f0`; candidate `7f3f042309dd1c54767d60d111c445298e081e726389bbce2048171613c4d1c0` (102 file, cây đo không đổi;
  đóng băng lại `83db0e97`); đo `6a1801e7` lần 3 trọn một lượt; bằng chứng `3095e4f0`.
- `CACHE_VERSION` 118 (không bump — chỉ frontend); `LLM_ONLY`; 0 model call.
- Thay đổi của người dùng `D frontend/public/favicon.svg` và `M .gitignore` (dòng `.playwright-cli/`, không phải của run này)
  giữ ngoài staging.
- Dải lớp học: 24/24 (trước 9/24); không dải lớp 55/56 như trước; Tier-A 8/8; W02 16/16, W04 24/24, W05 23/24 (một trang
  không tải — `report.md` §4).
- Duyệt hình **NOT_APPROVED**; E-R6, F-R7, G-1…G-9 và C-1…C-4 cần thao tác tay trên điện thoại.

## 2. Cổng

Tại commit tài liệu `1f4e74fe`, worktree tách rời sạch CRLF có dấu cách (`D:/tmp/class band fit`), 0 model call; commit ghi
log đi sau (chỉ thêm log, `gates.sh` và mục này):

- T3 `FULL_PRODUCT_GATE_PASS` (`diagnostics/t3_1f4e74fe.log`): pytest **7239 passed, 1 skipped, 2 deselected**; vitest
  **67 files / 1040 tests**; typecheck + build; tập demo; bề mặt sập.
- Cổng danh tính (`diagnostics/gates_1f4e74fe.log`, từ `1086da7f`): candidate `7f3f0423…` khớp; cache 118 / `b1714b566e25c912…`
  khớp; xuất lược đồ ×2 trùng byte; `LLM_ONLY`; bề mặt mô hình 0 file đổi; ngoài thư mục run chỉ `EVALUATION_CANDIDATE.json`
  (product_commit_sha) và `EVIDENCE_INDEX.md` (mục mới); `git diff --check` sạch; docs audit PASS; node harness 95 pass,
  2 skipped, 0 fail; worktree sạch trước/sau.
- Trình duyệt trên candidate cuối: lần đo 3 (`6a1801e7`) — `report.md` §3–§4.

## 3. Việc của người dùng

1. `review.md` của run này (H-1…H-3, C-1…C-4) cùng `runs/final-acceptance/review.md` (G-1…G-9, D-2…D-4) và các gói cũ.
2. Quyết H-3: chip ở 640–667 px ngang chỉ hiện chấm màu — chấp nhận hay muốn chữ trạng thái ngắn hơn.
3. Duyệt thì merge thẳng vào `main`, push, xoá nhánh — một lượt LOCAL riêng có lệnh (AGENTS §2).
