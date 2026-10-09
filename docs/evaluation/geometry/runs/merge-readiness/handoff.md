# merge-readiness — handoff

## 1. Trạng thái

- `READY_FOR_USER_ACCEPTANCE`; nhánh `feat/regular-square-pyramid`, chỉ local; không push, merge, PR, xoá nhánh.
- Housekeeping `f89a1a8b`; cây làm việc sạch (favicon + `.gitignore` đã commit theo lệnh người dùng).
- 671 hồ sơ Chrome mồ côi đã xoá có xác nhận; C: trống 77,43 GB.
- Danh sách nghiệm thu: `report.md` §4.

## 2. Cổng

Tại commit tài liệu `ac55186e`, worktree tách rời sạch có dấu cách (`D:/tmp/merge readiness`, favicon thật sự vắng),
0 model call; commit ghi log đi sau (chỉ thêm log và mục này):

- T3 `FULL_PRODUCT_GATE_PASS` (`diagnostics/t3_ac55186e.log`): pytest **7239 passed, 1 skipped, 2 deselected**; vitest
  **67 files / 1040 tests**; typecheck + build; tập demo; bề mặt sập.
- Cổng danh tính (`diagnostics/gates_ac55186e.log`, từ `6c334121`): candidate `7f3f0423…` khớp; cache 118 / `b1714b566e25c912…`
  khớp; xuất lược đồ ×2 trùng byte; `LLM_ONLY`; bề mặt mô hình 0 file đổi; bằng chứng ngoài thư mục run 0 file đổi (chỉ
  `EVIDENCE_INDEX.md` thêm mục); `git diff --check` sạch; docs audit PASS; node harness 100 pass, 2 skipped, 0 fail; worktree
  sạch trước/sau.
- Sau T3: `D:/tmp/algosim-browser` 0 thư mục phiên, `%TEMP%\w12-*` 0.

## 3. Việc của người dùng

Nghiệm thu theo `report.md` §4; duyệt thì merge thẳng vào `main`, push, xoá nhánh ở một lượt LOCAL riêng có lệnh (AGENTS §2).
