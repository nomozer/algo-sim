# browser-temp-lifecycle — handoff

## 1. Trạng thái

- Sửa hạ tầng kiểm thử `3cb0630a` (`browser-runner.mjs`, `openFixture`, test `browser-runner.node-test.mjs`); không đổi sản
  phẩm, candidate (`7f3f0423…`, product `45f5a7f0`), `CACHE_VERSION` 118, `LLM_ONLY`; 0 model call.
- Nhánh `feat/regular-square-pyramid`, chỉ local; không push, merge, PR, xoá nhánh. Trạng thái nghiệm thu của nhánh không
  đổi: `READY_FOR_USER_ACCEPTANCE` (`runs/classroom-band-fit/handoff.md`).
- `D frontend/public/favicon.svg` và `M .gitignore` (`.playwright-cli/`) của người dùng giữ ngoài staging.

## 2. Cổng

Ghi sau T3 + cổng danh tính ở commit tài liệu cuối của run (commit ghi log đi sau).

## 3. Việc của người dùng

1. Duyệt xoá 671 hồ sơ `%TEMP%\w12-*` (`VERIFIED_ORPHAN`, 33,5 GB) bằng lệnh ở `report.md` §4 — run không xoá.
2. `%TEMP%\scoped_dir*` (229, 1,3 GB, `UNKNOWN`): tuỳ ý, chỉ khi mọi trình duyệt Chromium đã đóng.
3. Ảnh/log trung gian `D:/tmp/classband-logs-*` của lượt đo trước (log đã ở trong kho): xoá hay giữ.
