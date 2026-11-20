# AXO Step Editor — Integration & Regression Closure (`step-editor-integration-closure`)

Báo cáo đầy đủ 12 mục theo chuẩn chiến dịch **Integration & Regression Closure** nằm tại [AXO-STEP-EDITOR-INTEGRATION-CLOSURE-REPORT.md](AXO-STEP-EDITOR-INTEGRATION-CLOSURE-REPORT.md).

## Tóm tắt xác minh

- **Commits trên `feat/axo-geometry-library-verification`:**
  - Base HEAD đầu đợt: `bae665e79d69b6b47fae34187b0ea1b02d722e50` (`92` commits ahead `main = bb046fa22aceff47abe22aa783aa64fc65caee13`).
  - Product Commit `P`: `37b7460ddd6f01dc07e5999dd09e29abe3ac2486` (`10` file owned).
  - Candidate Seal Commit `C`: `3eabbf674bfca82d19ca00b2894d2576dd87a5e5` (`EVALUATION_CANDIDATE.json` + `{k1,r1,s2}-owner-approval.template.json`, `111` file sản phẩm, `tree_hash = c1323d0a7bd9fda0e13114bfc4a03fe36124bb8d733ef472cf5430f967378b38`).
- **Các nhóm vấn đề Step Editor đã đóng (`FIXED_AND_VERIFIED`):**
  1. Tách `ERR_KHONG_NGOAI_TIEP` & `circumscribed_sphere` từ `kernel.py` sang `curved.py` và re-export tại `geometry/__init__.py` -> `test_curriculum_coverage.py` + `test_axo_11_advanced_samples.py` (`23 passed`).
  2. Nối chuỗi migration thật `backend/alembic/env.py` + `9c4d8e2b7a10_add_step_edit_tables.py` (`down_revision = "e437149641fa"`, không phụ thuộc Classroom WIP) -> `test_migration_drift.py` (`2 passed` zero drift trên clean worktree) + tạo [classroom-wip-rebase-onto-step-editor.patch](patches/classroom-wip-rebase-onto-step-editor.patch).
  3. Sửa concurrency/retry & đồng hồ version: `.with_for_update()` trên dialect non-SQLite, `expected_committed_version` (`409 STALE_REVISION_CONFLICT`), dời cập nhật `_LATEST_CLIENT_SEQ` xuống **sau `db.commit()`**, lưu `_latest_client_seq`, chuẩn hóa `version_number = effectiveVer` trên `construction-step-edits.ts` -> `82 passed` backend Step Editor + `22 passed` `construction-step-editor.test.tsx`.
  4. Làm mới Candidate Seal `EVALUATION_CANDIDATE.json` trên worktree sạch `step-editor-clean-candidate` -> `freeze_evaluation_candidate.py --verify` exit `0`, `tests/semantic_program` `1192 passed, 1 skipped`.
  5. Kiểm chứng E2E sống trên host (`:3001` PID `11008`, `:8000` PID `12604 -> 8688`) qua 4 bài toán, 6 tình huống (gồm restart `:8000` thật & fresh browser context `found=true`), 7 viewport (`1920..320`), touch emulation & REA MCP (`:9338`).
- **Final Verdict: `BLOCKED`** (không tự merge `main`, không push):
  - `ENVIRONMENT_BLOCKED`: `docker desktop start` thoát `0` nhưng `npipe:////./pipe/dockerDesktopLinuxEngine` không mở (`com.docker.service = Stopped`, không có PostgreSQL cục bộ), khiến `@pytest.mark.postgres` bị skip (`4 skipped`).
  - `OWNERSHIP_BLOCKED / PRE_EXISTING`: trên clean `HEAD`, `ProblemInput.tsx` / `WorkspaceTabBar.tsx` từ commit trước tham chiếu `ScreenCaptureDialog.tsx` / `store.ts` còn nằm uncommitted WIP (`npx tsc -b` & `vite build` fail trên clean worktree nhưng pass trên worktree tích hợp `axo-geometry-library` với `2272/2272` Vitest, `0` lỗi `tsc --noEmit`, `vite build` `exit 0`), và `CODE_INDEX.md:7` tham chiếu `frontend/scripts/attachment-resize.node-test.mjs` đang untracked (`1` stale path duy nhất; toàn bộ 4 đường dẫn Classroom = `0` stale trên clean `HEAD`).
