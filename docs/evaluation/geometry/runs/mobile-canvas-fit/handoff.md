# mobile-canvas-fit — handoff

## 1. Trạng thái bàn giao

- Nhánh `feat/regular-square-pyramid`, chỉ local; không push, merge, PR, xoá nhánh hay viết lại lịch sử.
- Product `c9bcdcdb`; candidate `7f3f042309dd1c54767d60d111c445298e081e726389bbce2048171613c4d1c0` (102 file, cây đo
  không đổi; đóng băng lại `002185a8` chỉ dời `product_commit_sha`); bằng chứng `3f874fed` (đo `90921f53`, chạy lại bước
  suite đỏ ở `a51c788b`).
- `CACHE_VERSION` 118 (không bump — chỉ frontend, không envelope nào đổi); `LLM_ONLY`; 0 model call.
- Thay đổi của người dùng `D frontend/public/favicon.svg` giữ ngoài staging.
- Duyệt hình **NOT_APPROVED**; D5 đã triển khai, **chờ người dùng duyệt** (`review.md`).

## 2. Cổng

Tại commit tài liệu `76600a5d`, worktree tách rời sạch CRLF có dấu cách (`D:/tmp/mobile fit`), 0 model call; commit ghi log đi
sau (chỉ thêm log và mục này):

- T3 `FULL_PRODUCT_GATE_PASS` (`diagnostics/t3_76600a5d.log`): pytest **7239 passed, 1 skipped, 2 deselected**; vitest
  **67 files / 1032 tests**; typecheck + build; tập demo; bề mặt sập 6/6.
- Cổng danh tính (`diagnostics/gates_76600a5d.log`): candidate `7f3f0423…` khớp; cache 118 / `b1714b566e25c912…` khớp; xuất
  lược đồ ×2 trùng byte; `LLM_ONLY`; bề mặt mô hình 0 file đổi; ngoài thư mục run chỉ `EVALUATION_CANDIDATE.json`
  (product_commit_sha) và `EVIDENCE_INDEX.md` (mục mới); `git diff --check` sạch; docs audit PASS; node harness 95 pass,
  2 skipped, 0 fail; worktree sạch trước/sau.

## 3. Việc của người dùng

1. Duyệt `review.md` (E-R1–E-R6; E-R6 cần thao tác tay trên điện thoại) và các mục chuyển tiếp của gói cũ — cùng gói
   ngoài kho `Documents/AlgoSim-Human-Review/20261008T204842/` (đã cập nhật).
2. Quyết `ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD` và `ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN` (cả hai có
   từ trước D5; không chặn merge nếu người dùng chấp nhận).
3. Duyệt thì merge thẳng vào `main`, push, xoá nhánh — ở một lượt riêng có lệnh (AGENTS §2).
