# phone-landscape-layout — handoff

## 1. Trạng thái bàn giao

- Nhánh `feat/regular-square-pyramid`, chỉ local; không push, merge, PR, xoá nhánh hay viết lại lịch sử.
- Product `95a56a17` (sửa `d8ad153b` + `95a56a17`); candidate `7f3f042309dd1c54767d60d111c445298e081e726389bbce2048171613c4d1c0`
  (102 file, cây đo không đổi; đóng băng lại `f884aa67`, `5892fefd` chỉ dời `product_commit_sha`); bằng chứng `b1ba2575`
  (đo `221ec0a0`, lần 3, trọn mọi bước trong một lượt).
- `CACHE_VERSION` 118 (không bump — chỉ frontend); `LLM_ONLY`; 0 model call.
- Thay đổi của người dùng `D frontend/public/favicon.svg` giữ ngoài staging.
- Duyệt hình **NOT_APPROVED**; E-R6 và F-R7 cần thao tác tay trên điện thoại.

## 2. Cổng

Tại commit tài liệu `d32bdb8d`, worktree tách rời sạch CRLF có dấu cách (`D:/tmp/landscape fit`), 0 model call; commit ghi
log đi sau (chỉ thêm log và mục này):

- T3 `FULL_PRODUCT_GATE_PASS` (`diagnostics/t3_d32bdb8d.log`): pytest **7239 passed, 1 skipped, 2 deselected**; vitest
  **67 files / 1034 tests**; typecheck + build; tập demo; bề mặt sập 6/6.
- Cổng danh tính (`diagnostics/gates_d32bdb8d.log`, từ `f6ebe946`): candidate `7f3f0423…` khớp; cache 118 / `b1714b566e25c912…`
  khớp; xuất lược đồ ×2 trùng byte; `LLM_ONLY`; bề mặt mô hình 0 file đổi; ngoài thư mục run chỉ `EVALUATION_CANDIDATE.json`
  (product_commit_sha) và `EVIDENCE_INDEX.md` (mục mới); `git diff --check` sạch; docs audit PASS; node harness 95 pass,
  2 skipped, 0 fail; worktree sạch trước/sau.
- Tier-A trên candidate cuối: 8/8 trong một lượt (lần đo 3, `221ec0a0`); oracle + kỳ vọng đã kiểm (`report.md` §5).

## 3. Việc của người dùng

1. Duyệt `review.md` (F-R1–F-R7) cùng gói ngoài kho `Documents/AlgoSim-Human-Review/20261008T204842/` (gói F, đã cập nhật).
2. Quyết: bảng nổi phủ canvas hẹp khi ngang (`ISSUE-ARCH-LANDSCAPE-FLOATING-PANEL-COVERS-CANVAS`); ca xoay màn thấp
   (`ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`). Cả hai không chặn merge nếu người dùng chấp nhận.
3. Duyệt thì merge thẳng vào `main`, push, xoá nhánh — ở một lượt riêng có lệnh (AGENTS §2).
