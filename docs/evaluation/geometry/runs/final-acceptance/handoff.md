# final-acceptance — handoff

## 1. Trạng thái

- `READY_FOR_USER_ACCEPTANCE`. Nhánh `feat/regular-square-pyramid`, chỉ local; không push, merge, PR, xoá nhánh, viết lại lịch sử.
- Product `95a56a17` (không đổi trong run này); candidate `7f3f0423…` (102 file, `--verify` khớp); `CACHE_VERSION` 118; `LLM_ONLY`;
  0 model call. Tier-A 8/8 và T3 PASS của `phone-landscape-layout` thuộc đúng phiên bản cuối (`report.md` §1) — không đo lại.
- Thay đổi của người dùng `D frontend/public/favicon.svg` giữ ngoài staging.

## 2. Mới trong run

- Dải lớp học vỡ hàng trên trên điện thoại (ngang ≤ 844×390 có thanh trình duyệt, 640/667 px; dọc 360 px): **có từ `main`**,
  nhánh 11/24 so với `main` 5/24, không dòng nào hồi quy ⇒ ghi `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW` (OPEN, không
  chặn merge theo đánh giá của run; người dùng quyết). Đề xuất sửa tối thiểu: `report.md` §2.
- Chạm giả lập 8/8 (`results/TOUCH_PROXY_PROBE.json`) — hỗ trợ, không thay E-R6/F-R7.
- UX debt người dùng chấp nhận tạm, vẫn OPEN: `ISSUE-ARCH-LANDSCAPE-FLOATING-PANEL-COVERS-CANVAS`,
  `ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`, `ISSUE-ARCH-MOBILE-HEADER-TOOLBAR-LAYOUT`.

## 3. Việc của người dùng

1. Thao tác tay trên điện thoại theo `review.md` §1–§2 (G-1…G-9).
2. Quyết D-1…D-4 (`review.md` §3).
3. Duyệt thì merge thẳng vào `main`, push, xoá nhánh — một lượt LOCAL riêng có lệnh (AGENTS §2). Trước merge: cổng trên cây
   tích hợp như các lần tích hợp trước.
