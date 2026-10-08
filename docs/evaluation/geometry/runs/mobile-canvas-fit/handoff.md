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

T3 và cổng danh tính chạy ở commit tài liệu cuối của run trong worktree tách rời sạch: log `diagnostics/t3_<sha>.log`,
`diagnostics/gates_<sha>.log` (commit ghi log đi sau commit tài liệu).

## 3. Việc của người dùng

1. Duyệt `review.md` (E-R1–E-R6; E-R6 cần thao tác tay trên điện thoại) và các mục chuyển tiếp của gói cũ — cùng gói
   ngoài kho `Documents/AlgoSim-Human-Review/20261008T204842/` (đã cập nhật).
2. Quyết `ISSUE-ARCH-PHONE-LANDSCAPE-CONTROLS-BELOW-FOLD` và `ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN` (cả hai có
   từ trước D5; không chặn merge nếu người dùng chấp nhận).
3. Duyệt thì merge thẳng vào `main`, push, xoá nhánh — ở một lượt riêng có lệnh (AGENTS §2).
