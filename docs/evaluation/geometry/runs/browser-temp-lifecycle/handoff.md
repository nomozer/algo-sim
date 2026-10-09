# browser-temp-lifecycle — handoff

## 1. Trạng thái

- Sửa hạ tầng kiểm thử `3cb0630a` (`browser-runner.mjs`, `openFixture`, test `browser-runner.node-test.mjs`); không đổi sản
  phẩm, candidate (`7f3f0423…`, product `45f5a7f0`), `CACHE_VERSION` 118, `LLM_ONLY`; 0 model call.
- Nhánh `feat/regular-square-pyramid`, chỉ local; không push, merge, PR, xoá nhánh. Trạng thái nghiệm thu của nhánh không
  đổi: `READY_FOR_USER_ACCEPTANCE` (`runs/classroom-band-fit/handoff.md`).
- `D frontend/public/favicon.svg` và `M .gitignore` (`.playwright-cli/`) của người dùng giữ ngoài staging.

## 2. Cổng

Tại commit tài liệu `ac7b1d07`, worktree tách rời sạch có dấu cách (`D:/tmp/browser lifecycle`), 0 model call; commit
ghi log đi sau (chỉ thêm log và mục này):

- T3 `FULL_PRODUCT_GATE_PASS` (`diagnostics/t3_ac7b1d07.log`): pytest **7239 passed, 1 skipped, 2 deselected**; vitest
  **67 files / 1040 tests**; typecheck + build; tập demo; bề mặt sập.
- Cổng danh tính (`diagnostics/gates_ac7b1d07.log`, từ `7834ea4e`): candidate `7f3f0423…` khớp; cache 118 / `b1714b566e25c912…`
  khớp; xuất lược đồ ×2 trùng byte; `LLM_ONLY`; bề mặt mô hình 0 file đổi; bằng chứng ngoài thư mục run 0 file đổi (chỉ
  `EVIDENCE_INDEX.md` thêm mục); `git diff --check` sạch; docs audit PASS; node harness 100 pass, 2 skipped, 0 fail
  (gồm `browser-runner.node-test.mjs`); worktree sạch trước/sau.
- Sau T3: gốc `D:/tmp/algosim-browser` 0 thư mục, `%TEMP%\w12-*` 671 (không tăng), 0 Chrome của bộ đo còn chạy.

## 3. Việc của người dùng

1. Duyệt xoá 671 hồ sơ `%TEMP%\w12-*` (`VERIFIED_ORPHAN`, 33,5 GB) bằng lệnh ở `report.md` §4 — run không xoá.
2. `%TEMP%\scoped_dir*` (229, 1,3 GB, `UNKNOWN`): tuỳ ý, chỉ khi mọi trình duyệt Chromium đã đóng.
3. Ảnh/log trung gian `D:/tmp/classband-logs-*` của lượt đo trước (log đã ở trong kho): xoá hay giữ.
