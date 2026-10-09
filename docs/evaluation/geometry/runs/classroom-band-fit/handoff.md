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

Ghi sau T3 + cổng danh tính ở commit tài liệu cuối của run (commit ghi log đi sau).

## 3. Việc của người dùng

1. `review.md` của run này (H-1…H-3, C-1…C-4) cùng `runs/final-acceptance/review.md` (G-1…G-9, D-2…D-4) và các gói cũ.
2. Quyết H-3: chip ở 640–667 px ngang chỉ hiện chấm màu — chấp nhận hay muốn chữ trạng thái ngắn hơn.
3. Duyệt thì merge thẳng vào `main`, push, xoá nhánh — một lượt LOCAL riêng có lệnh (AGENTS §2).
