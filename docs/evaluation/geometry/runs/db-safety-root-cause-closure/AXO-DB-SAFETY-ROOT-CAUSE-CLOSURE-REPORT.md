# AXO — DATABASE SAFETY ROOT-CAUSE CLOSURE & MAIN RELEASE PREPARATION REPORT

**Ngày kiểm định:** 2026-11-19  
**Nhánh làm việc:** `feat/axo-geometry-library-verification`  
**Release Candidate Clean Branch:** `release/axo-step-editor-db-safe-rc`  
**Closure Commit SHA:** `0fe3873a4fbeaa95006a6d7a36dea68a0828b1f2` (Tree: `e5493ccac443a13228eb8fed46bb2bcd01073932`)  
**Audited Code Seal Baseline (`product_commit_sha`):** `2ff70ce455f0b298a7878880ab7eb3fee21cc572` (`109` files, `e0ea792d71667f12911fa7b0425bc4761aabdc337ad605491bc06c33137076a4`)  
**Baseline `main` & `origin/main`:** `bb046fa22aceff47abe22aa783aa64fc65caee13` (không đổi, chưa merge, chưa push)

---

## 1. Executive Verdict & 12-Gate Release Readiness Table

- **RELEASE_DECISION:** `READY_FOR_OWNER_REVIEW`
- **RELEASE_GATE:** `READY_FOR_OWNER_REVIEW`
- **MERGE_STATUS:** `NOT_MERGED`
- **PUSH_STATUS:** `NOT_PUSHED`
- **MODEL_STATUS:** `MODEL_NOT_TRAINED`

Ba blocker trong báo cáo `AXO-STEP-EDITOR-MAIN-INTEGRATION-REPORT.md` (`BLOCKER-DB-1`, `BLOCKER-DB-2`, `GOVERNANCE-SCOPE-1`) đã được đóng tận gốc bằng kiến trúc an toàn dữ liệu hai lớp (migration non-destructive + startup migration preflight), dọn script legacy không làm gãy contract, giải trình phụ thuộc phạm vi kèm xóa 2 prototype HTML thừa, và kiểm chứng độc lập toàn bộ trên clean worktree `step-editor-release-candidate` (`release/axo-step-editor-db-safe-rc`). Không có mã sản phẩm cốt lõi (`backend/app`, `frontend/src`) bị thay đổi; chứng chỉ đóng băng `EVALUATION_CANDIDATE.json` khớp 100%.

| # | Cổng kiểm định (Gate) | Trạng thái | Tóm tắt bằng chứng thực nghiệm | Artifact |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `DB_SAFETY` | `PASS` | `f8a2c41d9e05` không còn `drop_table`; AST + state preflight chặn `UNSTAMPED_EXISTING_DATABASE` & destructive op chưa duyệt (`9/9` SQLite/unit closure tests PASS) | [phase-b-migration](../../../../../backend/alembic/migration_preflight.py), [backend-other.log](logs/backend-other.log) |
| 2 | `BACKUP_RESTORE` | `PASS` | 4 bản sao lưu nóng (`root_algosim.sqlite3.bak`, `dev_algosim.sqlite3.bak`, `pg16_algosim_acceptance.snapshot.tar.gz`, `pg16_algosim_host.snapshot.tar.gz`) phục hồi thử vào DB cô lập đạt 100% SHA-256 parity, 0 lỗi FK | [phase-a-db-forensic-and-backup-restore.json](results/phase-a-db-forensic-and-backup-restore.json), [phase-a-backup-restore.log](logs/phase-a-backup-restore.log) |
| 3 | `MIGRATION_COMPATIBILITY` | `PASS` | Scenario 1–8 SQLite + PostgreSQL 16.6 (`test_b4_postgres16_full_matrix_and_mid_migration_atomic_rollback`, `test_ic4`, `test_migration_drift`, `test_dev_backend_launcher`) `EXIT 0`, `alembic check` sạch | [backend-postgres.log](logs/backend-postgres.log), [test_database_safety_closure.py](../../../../../backend/tests/test_database_safety_closure.py) |
| 4 | `CLASSROOM_DEPENDENCIES` | `PASS` | `seed_classroom_fixture.py` trả exit `2` (`CLASSROOM_FEATURE_RETIRED`), 0 `ImportError`; `seed_demo_accounts.py` từ chối ghi khi phát hiện bảng Classroom còn dữ liệu; 3 tài liệu vận hành đồng bộ | [seed_classroom_fixture.py](../../../../../backend/scripts/seed_classroom_fixture.py), [seed_demo_accounts.py](../../../../../backend/scripts/seed_demo_accounts.py) |
| 5 | `RELEASE_SCOPE` | `PASS` | `115` commit (`607` file so với `bb046fa22`) phân loại 9 miền, ma trận file dùng chung chứng minh cherry-pick ngây thơ mất an toàn; gỡ 2 HTML prototype vô thừa; giữ `release/axo-step-editor-db-safe-rc` thống nhất | [phase-d-commit-scope-governance.json](results/phase-d-commit-scope-governance.json) |
| 6 | `GEOMETRY_REGRESSION` | `PASS` | `tests/geometry`: `12,000 passed, 6 skipped, 3 deselected, 9 xfailed`; `tests/semantic_program`: `1,192 passed, 1 skipped`; `tests` khác: `802 passed, 3 deselected`; `replay_demo`: `5/5`, `crash_audit`: `6/6`, 0 lỗi 500 | [phase-e-test-summary.json](results/phase-e-test-summary.json), [backend-geometry.log](logs/backend-geometry.log) |
| 7 | `STEP_EDITOR` | `PASS` | Khớp 5/5 họ hình học chính xác (`Fraction`/`Radical`) + 8/8 lớp biên `422`/`409` (`MISSING_DEPENDENCY`, `COLLINEAR_POINTS`, `UNSUPPORTED_STEP_SYNTAX`, `INVALID_RATIO`, `DOWNSTREAM_ORTHOGONALITY_BROKEN`, `STALE_REVISION_CONFLICT`, `EDIT_SUPERSEDED`) | [phase-e-geometry-exactness.json](results/phase-e-geometry-exactness.json) |
| 8 | `POSTGRES_E2E` | `PASS` | `pytest -m postgres`: `5/5 passed`; Live PG 16 `algosim_acceptance` giữ nguyên 100% ID cũ (`4→8` sessions, `9→18` revisions, `9→18` feedback, `12→23` auth_sessions), sống sót qua restart Uvicorn `:8000` | [backend-postgres.log](logs/backend-postgres.log), [phase-f-postgres-live-state.json](results/phase-f-postgres-live-state.json) |
| 9 | `FRONTEND` | `PASS` | `tsc -b` (`EXIT 0`), `vitest run`: `192 passed (192)` files / `2,274 passed (2,274)` tests (`EXIT 0`, gồm `code-index-sync.test.ts` & `rules-hygiene.test.ts`) | [frontend-tsc.log](logs/frontend-tsc.log), [frontend-vitest.log](logs/frontend-vitest.log) |
| 10 | `BUILD` | `PASS` | `vite build` (`EXIT 0`, `dist/index.html` + chunk build thành công, `dist/prototypes` = `False` xác nhận 2 prototype bị xóa không rò vào bản dựng) | [frontend-vite-build.log](logs/frontend-vite-build.log) |
| 11 | `BROWSER_VERIFICATION` | `PASS` | Playwright Phase 1 + Phase 2 (`#btn-composer-plus` → `#plus-popover-menu`, `AB→SB`, `422` rollbacks, skew `422`, `SM/SA` cascade + F5 + restart, 7 viewport + touch/VKB) & REA MCP đều `PASS` (`0` console/page/5xx) | [phase-f-browser-e2e-phase1.json](results/phase-f-browser-e2e-phase1.json), [phase-f-browser-e2e-phase2.json](results/phase-f-browser-e2e-phase2.json), [phase-f-rea-mcp.json](results/phase-f-rea-mcp.json) |
| 12 | `DOCS_AUDIT` | `PASS` | `audit_docs_information_architecture.py` (`EXIT 0`), `freeze_evaluation_candidate.py --verify` (`EXIT 0`), `SECRET_LEAK_HITS=0`, root `D:\Documents\projects\algo-sim` không bị chạm | [seal-verify.log](logs/seal-verify.log) |

---

## 2. Phân Tích Nguyên Nhân Gốc Rễ (`BLOCKER-DB-1`, `BLOCKER-DB-2`, `GOVERNANCE-SCOPE-1`)

1. **`BLOCKER-DB-1` (CRITICAL — Đã đóng):**
   - Commit `bf1ee2a57` gỡ toàn bộ ORM Classroom/Live Session khỏi `backend/app/persistence/` nhưng đồng thời sửa migration `f8a2c41d9e05_remove_classroom_and_live_session_tables.py` để gọi `op.drop_table(...)` vô điều kiện trên 5 bảng (`classroom_sessions`, `practice_sessions`, `assignments`, `class_memberships`, `classrooms`). Hàm `downgrade()` chỉ tạo lại schema rỗng (`0` dòng dữ liệu).
   - `backend/Dockerfile` chạy `alembic upgrade head` ngay trong `CMD` khởi động container mà không kiểm tra tồn tại bảng có dữ liệu hay `alembic_version`. Trong khi đó, `D:\Documents\projects\algo-sim\backend\algosim.db` chứa **46 users** và **66 bản ghi Classroom sống** với `alembic_version = NULL`. Chạy `alembic check` trên schema mới trả về `0` do model SQLAlchemy và `head` khớp nhau, che khuất rủi ro xóa dữ liệu khi chạy trên DB cũ hoặc upgrade không kiểm soát.
2. **`BLOCKER-DB-2` (HIGH — Đã đóng):**
   - `backend/scripts/seed_classroom_fixture.py` vẫn giữ import cũ tới `Assignment`, `ClassMembership`, `Classroom` đã bị xóa trong `bf1ee2a57`, gây `ImportError` ngay tại startup script; đồng thời `seed_demo_accounts.py` không có cơ chế từ chối khi phát hiện bảng Classroom còn dữ liệu.
3. **`GOVERNANCE-SCOPE-1` (HIGH — Đã giải trình & thu gọn bloat):**
   - Nhánh tích hợp chứa `115` commit ahead (`607` file thay đổi so với `bb046fa22`) gộp nhiều domain phụ thuộc chéo qua các file dùng chung (`main.py`, `App.tsx`, `SimulationWorkspace.tsx`, `store.ts`, `scene3d-*`, `global.css`, `CODE_INDEX.md`, chuỗi Alembic tuyến tính `9c4d8e2b7a10 → f8a2c41d9e05`). Ngoài ra còn sót 2 file prototype HTML chưa được tham chiếu trong `frontend/public/prototypes/`.

---

## 3. Phase A — Sao Lưu Cô Lập & Kiểm Chứng Khôi Phục (Backup & Restore Parity)

- **Bối cảnh hạ tầng:** Docker daemon không chạy trên máy kiểm định (`daemon_running = false`, 0 container/volume); gói PostgreSQL 16 di động không kèm `pg_dump.exe`/`pg_restore.exe`. Toàn bộ sao lưu PostgreSQL dùng transaction `REPEATABLE READ` + trích xuất DDL từ catalog (`pg_class`, `pg_attribute`, `pg_index`) + `COPY TO STDOUT WITH CSV HEADER`; SQLite dùng `sqlite3.Connection.backup` ở chế độ `ro` với kiểm tra khóa ngoại & integrity.
- **Thư mục sao lưu gitignored:** `D:\Documents\projects\algo-sim\.superpowers\db-safety-backups\2026-11-19\`.

| Nguồn DB | File Backup (Gitignored) | Kích thước (bytes) | SHA-256 Backup | Thẩm định khôi phục vào DB tạm cô lập |
| :--- | :--- | ---: | :--- | :--- |
| Root SQLite (`algo-sim/backend/algosim.db`) | `root_algosim.sqlite3.bak` | `413,696` | `2b13b63d6a04136df064babaa7da269649eadf46ae14d1c2da97231401367e8a` | `46` users, `66` Classroom rows (`12+20+10+16+8`), `integrity_check=ok`, `0` FK errors, 100% SHA-256 digest parity |
| Dev SQLite (`axo-geometry-library/backend/algosim.db`) | `dev_algosim.sqlite3.bak` | `7,757,824` | `13beeaa713e4a001bf74e7f6acf2b0feaa55221f1f31fd0ea2e0ac3487c35b24` | `74` `step_edit_sessions`, `280` revisions, `280` feedback, `integrity_check=ok`, `0` FK errors, 100% digest parity |
| PG 16 `algosim_acceptance` | `pg16_algosim_acceptance.snapshot.tar.gz` | `44,590` | `ffe017e1df9a93bc06df2ddb15ecc8a20d7e52fbe8b6b13d2564350617d5d8d8` | Restore sang DB tạm `algosim_restore_verify_*`, 100% SHA-256 parity (`4` sessions, `9` rev, `9` feedback, `12` auth_sessions), drop tạm sau verify |
| PG 16 `algosim_host` | `pg16_algosim_host.snapshot.tar.gz` | `60,720` | `2f92bde9484d4d05a6683b1adc7419bfe9af2827aa5ba34d7204f7057a407430` | Restore sang DB tạm `algosim_restore_verify_*`, 100% SHA-256 parity (`7` sessions, `9` rev, `9` feedback, `12` auth_sessions), drop tạm sau verify |

- Chi tiết đầy đủ trong [`phase-a-db-forensic-and-backup-restore.json`](results/phase-a-db-forensic-and-backup-restore.json) và [`phase-a-backup-restore.log`](logs/phase-a-backup-restore.log).

---

## 4. Phase B — Đóng Tận Gốc `BLOCKER-DB-1` (Non-Destructive Migration & Preflight)

1. **[`backend/alembic/migration_preflight.py`](../../../../../backend/alembic/migration_preflight.py):**
   - AST scanner kiểm tra toàn bộ script revision pending theo DAG (`op.drop_table`, `batch_op.drop_table`, `op.drop_column`, `batch_op.drop_column`, và `op.execute(...)` chứa `DROP TABLE`, `TRUNCATE`, `ALTER ... DROP COLUMN`, `DELETE FROM`).
   - Bảo vệ DB chưa stamp (`UNSTAMPED_EXISTING_DATABASE`): từ chối nếu DB có bảng ứng dụng sẵn nhưng không có bảng/dòng `alembic_version`.
   - Startup gate (`--startup` / `ALGOSIM_STARTUP_MODE=1`): cấm cả upgrade chứa thao tác hủy dữ liệu (`DESTRUCTIVE_MIGRATION_FORBIDDEN_AT_STARTUP`) lẫn mọi downgrade (`DOWNGRADE_FORBIDDEN_AT_STARTUP`, exit `23`).
   - Manual gate: từ chối destructive upgrade thiếu phê duyệt tường minh (`DESTRUCTIVE_UPGRADE_UNAPPROVED`) và destructive downgrade trên bảng còn dòng (`DESTRUCTIVE_DOWNGRADE_DATA_LOSS_BLOCKED`).
2. **[`backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py`](../../../../../backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py):**
   - `upgrade()` chuyển sang **non-destructive retention (`return None`)** — giữ nguyên toàn bộ 5 bảng legacy Classroom và dữ liệu bên trong.
   - `downgrade()` kiểm tra `sa.inspect(bind)` và chỉ tạo schema cho những bảng thực sự vắng mặt.
3. **[`backend/alembic/env.py`](../../../../../backend/alembic/env.py) & [`backend/Dockerfile`](../../../../../backend/Dockerfile):**
   - `env.py` nạp `migration_preflight` qua `importlib.util` (giữ `backend/alembic/` không có `__init__.py`), loại 5 bảng legacy giữ lại khỏi `alembic check` (`_include_name`), và gọi `_run_online_preflight(connection)` trước `context.begin_transaction()` (kèm `if connection.in_transaction(): connection.rollback()` tránh lỗi SQLAlchemy 2.0 autobegin nuốt DDL transaction).
   - `Dockerfile` thiết lập `ENV ALGOSIM_STARTUP_MODE=1` và chạy `CMD python alembic/migration_preflight.py --startup && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1`.
4. **Kiểm chứng Scenario 1–8 (`tests/test_database_safety_closure.py`, `test_migration_drift.py`, `test_step_editor_integration_closure.py`, `test_dev_backend_launcher.py`):**
   - `51 passed, 3 deselected, 0 failed` (SQLite/unit) và `5 passed, 14011 deselected, 0 failed` (PostgreSQL 16, gồm atomic mid-migration rollback verification).

---

## 5. Phase C — Đóng Tận Gốc `BLOCKER-DB-2` & Đồng Bộ Tài Liệu

1. **[`backend/scripts/seed_classroom_fixture.py`](../../../../../backend/scripts/seed_classroom_fixture.py):** Thay thế bằng entrypoint thông báo trạng thái retired an toàn — dùng `User` + `scripts.seed_demo_accounts` (0 `ImportError`), hỗ trợ `--help` (exit `0`), `--json` / chạy mặc định trả exit `2` (`CLASSROOM_FEATURE_RETIRED`), tuyệt đối không chạm DB.
2. **[`backend/scripts/seed_demo_accounts.py`](../../../../../backend/scripts/seed_demo_accounts.py):** Trước khi seed/update 3 tài khoản demo trên `users`, quét 5 bảng Classroom legacy; nếu bất kỳ bảng nào có `COUNT(*) > 0` lập tức dừng với `RuntimeError("RETAINED_CLASSROOM_DATA_PRESENT: ...")` để bảo vệ dữ liệu cũ.
3. **Đồng bộ tài liệu:** Cập nhật [`docs/CLASSROOM_AUTH_CONTRACT.md`](../../../../CLASSROOM_AUTH_CONTRACT.md), [`docs/OPERATIONS.md`](../../../../OPERATIONS.md), và [`docs/CODE_INDEX.md`](../../../../CODE_INDEX.md) (đồng thời sửa ký tự corrupt `\x08` ở mục `seed_demo_accounts.py`, bổ sung `migration_preflight.py`, cập nhật trạng thái `seed_classroom_fixture.py` và `classroom_models.py`). Kiểm tra bởi `vitest` `code-index-sync.test.ts` (`PASS`).

---

## 6. Phase D — Giải Trình Phạm Vi Commit & Dọn Prototype Thừa (`GOVERNANCE-SCOPE-1`)

- Đã xóa sạch **2 HTML prototype chưa tham chiếu** khỏi Git tracking (`git rm`):
  - `frontend/public/prototypes/axo-left-sidebar-prototype.html`
  - `frontend/public/prototypes/axo-multi-problem-workspace.html`
  - Kiểm tra `vite build` sau xóa: `dist/prototypes` không tồn tại (`DIST_PROTOTYPES_EXISTS = False`).
- Tổng diff trên `release/axo-step-editor-db-safe-rc` (`0fe3873a4`) so với `main` (`bb046fa22`): **`115` commit**, **`607` file thay đổi**, phân nhóm tại [`phase-d-commit-scope-governance.json`](results/phase-d-commit-scope-governance.json):

| Miền (Domain) | Số commit | Ví dụ / Ghi chú coupling |
| :--- | ---: | :--- |
| `landing_page` | 39 | Chuyển route `/` sang `LandingView`, app sang `/app` qua `App.tsx`, `AxoErrorExperience.tsx` |
| `geometry_core_scene3d` | 21 | Thư viện 11 bài Geometry, `scene3d-model.ts`, `scene3d-semantic-policy.ts`, `scene3d-view.tsx`, `geometry2d/*` |
| `tests_docs_eval` | 16 | Bộ regression, seal `EVALUATION_CANDIDATE`, docs đánh giá |
| `workspace_sidebar` | 13 | Single-instance tab bar, sidebar, `store.ts` |
| `step_editor` | 11 | Step Editor UI + `step_edit_router.py` + `step_editor.py` |
| `attachment_composer` | 9 | Composer `+` (`#btn-composer-plus`), ScreenCaptureDialog, `ProblemInput.tsx`, `global.css` |
| `database_migration` | 4 | Alembic `9c4d8e2b7a10` + Postgres 16 integration tests |
| `classroom_retirement` | 1 | `bf1ee2a57` trong `backend/app/main.py` & `f8a2c41d9e05` |
| `database_safety_closure` | 1 | `0fe3873a4`: đóng toàn bộ `BLOCKER-DB-1`, `BLOCKER-DB-2`, `GOVERNANCE-SCOPE-1` (15 file) |

- **Bằng chứng coupling khiến cherry-pick tách rời mất an toàn:** Các file lõi (`backend/app/main.py`, `frontend/src/App.tsx`, `SimulationWorkspace.tsx`, `store.ts`, `scene3d-model.ts`, `scene3d-semantic-policy.ts`, `scene3d-view.tsx`, `global.css`, `CODE_INDEX.md`) và chuỗi Alembic tuyến tính `9c4d8e2b7a10 → f8a2c41d9e05` chia sẻ trực tiếp giữa các miền trên. Vì vậy phương án an toàn nhất là tích hợp thống nhất nhánh `release/axo-step-editor-db-safe-rc`.

---

## 7. Nhánh Release Candidate An Toàn & Phương Án Rollback Về `bb046fa22`

- **Release Candidate Branch:** `release/axo-step-editor-db-safe-rc` (tạo mới tại clean worktree `D:\Documents\projects\algo-sim\.superpowers\worktrees\step-editor-release-candidate`), HEAD code đóng `0fe3873a4fbeaa95006a6d7a36dea68a0828b1f2`, clean tree (`RC_DIRTY_COUNT = 0`).
- **Rollback không mất dữ liệu về `main` (`bb046fa22aceff47abe22aa783aa64fc65caee13`):**
  1. Do `f8a2c41d9e05.upgrade()` đã không còn `DROP TABLE`, việc triển khai RC lên DB có dữ liệu Classroom giữ nguyên **100% bảng và bản ghi Classroom** (`0` mất mát).
  2. Nếu cần rollback ứng dụng về `bb046fa22`: thực hiện rollback Git/image deployment (hoặc `git revert` tiến tới), sau đó trên DB đã nâng schema mới chỉ cần chạy `alembic downgrade bb046fa22` không? **Lưu ý:** Trước `9c4d8e2b7a10`, revision ngay trước nhánh Step Editor là `a1c7e4b90d52`; khi `ALGOSIM_STARTUP_MODE` tắt trong cửa sổ bảo trì có kiểm soát, `downgrade` khôi phục mọi bảng legacy còn thiếu nếu chưa có và không xóa dữ liệu đang tồn tại, hoặc an toàn nhất là giữ bảng Step Editor cộng thêm (`additive tables`) song song và rollback container/app code về `bb046fa22` (backward-compatible DB state, 0 downtime mất dữ liệu).
  3. Đối với `algo-sim\backend\algosim.db` (`alembic_version = NULL`): `migration_preflight.py` từ chối mọi upgrade tự động (`UNSTAMPED_EXISTING_DATABASE`), buộc vận hành sao lưu + đối chiếu schema thủ công theo [`docs/OPERATIONS.md`](../../../../OPERATIONS.md).

---

## 8. Tổng Hợp Kết Quả Chạy Test & Audit Trên Clean `step-editor-release-candidate` (Phase E)

Tất cả các lượt kiểm thử bên dưới chạy tuần tự trên clean worktree `step-editor-release-candidate` ở commit `0fe3873a4fbeaa95006a6d7a36dea68a0828b1f2` ([`phase-e-test-summary.json`](results/phase-e-test-summary.json)):

| Hạng mục kiểm thử | Lệnh / Phạm vi | Passed | Failed | Skipped | Xfailed | Deselected | Exit | Log |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| Seal Verify | `python scripts/freeze_evaluation_candidate.py --verify` | 1 (`109` file) | 0 | 0 | 0 | 0 | `0` | [`seal-verify.log`](logs/seal-verify.log) |
| Postgres 16 Integration | `pytest -m postgres -v` | **5** | **0** | 0 | 0 | 14,011 | `0` | [`backend-postgres.log`](logs/backend-postgres.log) |
| Geometry Suite | `pytest tests/geometry -rsx -q` | **12,000** | **0** | 6 | 9 | 3 | `0` | [`backend-geometry.log`](logs/backend-geometry.log) |
| Semantic Program Suite | `pytest tests/semantic_program -rsx -q` | **1,192** | **0** | 1 | 0 | 0 | `0` | [`backend-semantic-program.log`](logs/backend-semantic-program.log) |
| Other Backend Tests | `pytest tests --ignore=tests/geometry --ignore=tests/semantic_program -rsx -q` | **802** | **0** | 0 | 0 | 3 | `0` | [`backend-other.log`](logs/backend-other.log) |
| Demo Replay Audit | `python scripts/replay_demo_cases.py` | **5/5** (`1/1` chain) | **0** | 0 | 0 | 0 | `0` | [`backend-replay-demo.log`](logs/backend-replay-demo.log) |
| Crash Surface Audit | `python scripts/audit_demo_crash_surface.py` | **6/6** (`0` uncaught 500) | **0** | 0 | 0 | 0 | `0` | [`backend-crash-audit.log`](logs/backend-crash-audit.log) |
| Frontend Typecheck | `.\node_modules\.bin\tsc.cmd -b` | **PASS** | **0** | 0 | 0 | 0 | `0` | [`frontend-tsc.log`](logs/frontend-tsc.log) |
| Frontend Build | `node ./node_modules/vite/bin/vite.js build` | **PASS** (`dist/prototypes=False`) | **0** | 0 | 0 | 0 | `0` | [`frontend-vite-build.log`](logs/frontend-vite-build.log) |
| Frontend Vitest Suite | `node ./node_modules/vitest/vitest.mjs run` | **2,274** (`192` files) | **0** | 0 | 0 | 0 | `0` | [`frontend-vitest.log`](logs/frontend-vitest.log) |

**Danh sách đầy đủ node ID `xfail` (`9`) và `skipped` (`7`, gồm 3x grouped `[2]` ở `test_unified_solid_scope.py` + `1` ở `test_scalar_obligations.py`) được ghi nguyên văn trong [`phase-e-test-summary.json`](results/phase-e-test-summary.json):**
- `XFAIL`:
  - `tests/geometry/test_generalized_goal_entry.py::test_length_goal_refusal[unread-second-ask]`
  - `tests/geometry/test_generalized_goal_entry.py::test_length_goal_refusal[contradictory-length]`
  - `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B27-facts]`
  - `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B27-pipeline]`
  - `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B28-facts]`
  - `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B28-pipeline]`
  - `tests/geometry/test_hybrid_simulation_capability_probes.py::test_centre_label_exhaustion_is_a_coded_outcome`
  - `tests/geometry/test_premise_source_coverage.py::test_goal_fact_quote_does_not_cover_a_hypothesis[Chứng minh SC vuông góc với BD và đáy là hình chữ nhật.]`
  - `tests/geometry/test_source_grounding_reliability.py::test_targeted_case_meets_its_preregistered_label[E05-unsupported-second-quantity]`
- `SKIPPED`:
  - `tests/geometry/test_unified_solid_scope.py:186` `[2]` (`A3-DEV-02 has no residual_volume goal`)
  - `tests/geometry/test_unified_solid_scope.py:186` `[2]` (`A3-DEV-09 has no residual_volume goal`)
  - `tests/geometry/test_unified_solid_scope.py:186` `[2]` (`demo1-pyramid-derived-section has no residual_volume goal`)
  - `tests/semantic_program/test_scalar_obligations.py:95` `[1]` (`thiếu term mặc định về identity — đã có test riêng`)

---

## 9. Kiểm Chứng 5 Họ Hình Học Chính Xác (`Fraction`/`Radical`) & 8 Lớp Từ Chối `422`/`409`

Thực thi qua `phase_e_geometry_exactness.py` trên SQLite tạm cô lập (`results/phase-e-geometry-exactness.json` — `PHASE_E_GEOMETRY_EXACTNESS_PASS`):

| Họ bài toán / Tình huống | Kiểm chứng toán học & hợp đồng | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| 1. Mặt cầu ngoại tiếp (`chop-mat-cau-ngoai-tiep`) | Sửa bước `(α)` của `AB` → `SB`, xác minh pháp tuyến, `I`, `R²`, `V`, không lộ `M_AB`/`mid_` | `mp_normal=["4","0","-4"]`, `I=["2","2","2"]`, `r²=12`, `V=32π√3`, `leaked_M_AB=false`, recomputed `9` đối tượng | `PASS` |
| 2. Thiết diện chóp (`chop-thiet-dien-ba-diem`) | Sửa tuần tự `M` trên `SA`: `1/4 → 3/4 → 1/2`, kiểm tra phẳng chứa đa giác thiết diện & diện tích dương chính xác | `M=["0","0","9/2"]` (`5` đỉnh, `5√34/2`), `["0","0","3/2"]` (`99√2/10`), `["0","0","3"]` (`6√6`) | `PASS` |
| 3. Thiết diện lăng trụ (`lang-tru-tam-giac-thiet-dien`) | Sửa `P` trên `CC′` tỉ số `1/3`, không rò `_prime` | `P=["0","4","4/3"]`, `5` đỉnh, `2√61`, `no_underscore_prime_leak=true` | `PASS` |
| 4. Thiết diện lập phương (`lap-phuong-thiet-dien-bat-ky`) | Gốc `6` đỉnh `12√3`; sửa `M` trên `AD` (`AM/AD=1/3`) không rò `_prime` | `M=["0","4/3","0"]`, `6` đỉnh, `71√149/42`, `recomputed=8` đối tượng | `PASS` |
| 5. Khoảng cách chéo nhau (`khoang-cach-hai-duong-cheo-nhau`) | Kiểm tra đoạn vuông góc chung `PQ` thuộc `SC, BD` | `P=["8/3","8/3","4/3"]`, `Q=["2","2","0"]`, `PQ·SC=0`, `PQ·BD=0`, `‖PQ‖²=8/3`, `2√6/3` | `PASS` |
| 6–13. 8 lớp biên HTTP (`6` mã `422` + `2` mã `409`) | Fail-closed, `draft_preserved=true` ở `422`; xung đột phiên bản/thứ tự `409` | `undefined_point_SZ→422 MISSING_DEPENDENCY`, `collinear_AOC→422 COLLINEAR_POINTS`, `unsupported_syntax→422 UNSUPPORTED_STEP_SYNTAX`, `invalid_ratio_gt_1→422 INVALID_RATIO`, `circular_self_ref→422 MISSING_DEPENDENCY`, `skew_orthogonality_break→422 DOWNSTREAM_ORTHOGONALITY_BROKEN`, `stale_revision_conflict→409 STALE_REVISION_CONFLICT`, `edit_superseded_seq→409 EDIT_SUPERSEDED` | `PASS` |

---

## 10. Phase F — Kiểm Chứng Sống Trên PostgreSQL 16.6 (`algosim_acceptance`) Không Truncate

1. Chạy `migration_preflight.py --startup --json` trên `algosim_acceptance` (`127.0.0.1:55432`) ở trạng thái live: `allowed=true`, `reason_code="SAFE_NO_DESTRUCTIVE_OPERATIONS"`, `user_tables_count=14`, `destructive_operations=[]` (`EXIT 0`).
2. **Không thực hiện bất kỳ lệnh `TRUNCATE` hay `DELETE` nào.** Toàn bộ 4 hàng `step_edit_sessions`, 9 hàng `step_edit_revisions`, 9 hàng `step_edit_feedback`, 12 hàng `auth_sessions` trước khi chạy Phase F được kiểm tra bảo toàn 100% theo khóa chính (`missing_pre_ids = []`):

| Bảng (`algosim_acceptance`) | Trước Phase F | Sau Phase F | Pre-IDs được giữ nguyên | Hàng mới do Phase F ghi thêm |
| :--- | ---: | ---: | ---: | ---: |
| `step_edit_sessions` | 4 | 8 | `4/4` (`missing=[]`) | +4 |
| `step_edit_revisions` | 9 | 18 | `9/9` (`missing=[]`) | +9 |
| `step_edit_feedback` | 9 | 18 | `9/9` (`missing=[]`) | +9 |
| `auth_sessions` | 12 | 23 | `12/12` (`missing=[]`) | +11 |
| `users` | 0 | 0 | `0/0` (`missing=[]`) | +0 |

3. **Chứng minh sống qua restart server thật (Phase 2):** Khởi động lại Uvicorn `:8000` giữa chừng (kill tiến trình cũ, xác nhận cổng tắt + startup preflight lại + khởi động tiến trình mới PID `18508`), tải lại `/simulation/chop-thiet-dien-ba-diem`: `/state` trả HTTP `200`, `found=true`, `committedVersion=3`, `revisionCount=3`, `backendMXyzAfterRestart=["0", "0", "9/2"]`, UI dock hiển thị đúng `"6\nLấy điểm M thuộc SA sao cho SM/SA = 1/4"` (`images/db-closure-post-restart.png`). Chi tiết tại [`phase-f-postgres-live-state.json`](results/phase-f-postgres-live-state.json).

---

## 11. Ma Trận Trình Duyệt Playwright (Routes, Composer, Step Editor, 7 Viewport, Touch & VKB)

Thực thi trên host thật `http://localhost:3001` (Vite) ↔ `http://127.0.0.1:8000` (Uvicorn PG16), kết quả lưu tại [`phase-f-browser-e2e-phase1.json`](results/phase-f-browser-e2e-phase1.json) & [`phase-f-browser-e2e-phase2.json`](results/phase-f-browser-e2e-phase2.json):

- **Routes & Composer `+`:** `GET /` (`200`, `"Axo — Mô phỏng tương tác"`), `GET /app` (`200`), `fileInputCount=3`, click `#btn-composer-plus` mở `#plus-popover-menu` (`plusMenuOpened=true`).
- **Step Editor UX & Integrity:** Hover đổi opacity `0 -> 1` với `hoverHeightDeltaPx=0`; Enter/Escape hoạt động; `AB → SB` hợp lệ HTTP `200`, `leakedRawHelper=false`, `recomputedCount=9`; input trắng vô hiệu nút Chạy; 3 test `422` + skew `422` (`DOWNSTREAM_ORTHOGONALITY_BROKEN`) giữ nguyên draft (`draftPreserved=true`) và không làm hỏng scene; chuỗi `SM/SA 1/4 → 3/4 → 1/4` + F5 + chuyển sang lăng trụ + đóng/mở tab giữ nguyên `1/4`; `.dock-scroll` cô lập cuộn khỏi canvas (`overscrollBehaviorY="contain"`); stale probe trả `409 STALE_REVISION_CONFLICT`. Tổng `consoleErrors=[]`, `pageErrors=[]`, `unexpected5xx=[]`.

| Viewport / Chế độ | `overflowX` | Canvas Visible (`W×H`) | `runClipped` / `cancelClipped` | `textareaHorizontalOverflow` | `controlsOccludeActions` | `navOperable` | Ảnh chụp |
| :--- | ---: | :--- | :--- | :--- | :--- | :--- | :--- |
| `1920×1080` | `0` | `true` (`1289×1042`) | `false` / `false` | `false` (`h=85px`, `overflowY=hidden`) | `false` | `true` | [vp-1920x1080](images/db-closure-vp-1920x1080.png) |
| `1440×900` | `0` | `true` (`809×862`) | `false` / `false` | `false` (`h=85px`) | `false` | `true` | [vp-1440x900](images/db-closure-vp-1440x900.png) |
| `1366×768` | `0` | `true` (`735×730`) | `false` / `false` | `false` (`h=85px`) | `false` | `true` | [vp-1366x768](images/db-closure-vp-1366x768.png) |
| `1024×768` | `0` | `true` (`704×730`) | `false` / `false` | `false` (`h=85px`) | `false` | `true` | [vp-1024x768](images/db-closure-vp-1024x768.png) |
| `768×1024` | `0` | `true` (`472×986`) | `false` / `false` | `false` (`h=85px`) | `false` | `true` | [vp-768x1024](images/db-closure-vp-768x1024.png) |
| `390×844` | `0` | `true` (`390×444`) | `false` / `false` | `false` (`h=85px`) | `false` | `true` | [vp-390x844](images/db-closure-vp-390x844.png) |
| `320×568` | `0` | `true` (`320×293`) | `false` / `false` | `false` (`h=85px`) | `false` | `true` | [vp-320x568](images/db-closure-vp-320x568.png) |
| Touch `390×844` + VKB `390×460` | `0` | `pencilVisibleOnTouchActive=true` | `taInViewport=true`, `runInViewport=true`, `cancelInViewport=true` | `—` | `—` | `—` | [vkb-390x460](images/db-closure-vkb-390x460.png) |

---

## 12. Bằng Chứng Quan Sát Độc Lập REA MCP (`http://127.0.0.1:9339`)

| Thao tác MCP REA | Evidence ID | Kết quả chính ([`phase-f-rea-mcp.json`](results/phase-f-rea-mcp.json)) |
| :--- | :--- | :--- |
| `list_browser_targets` | `ev_8fee1d916af71c7bd4be68d8ca5375774f779961ee3deba273c9ae692634b5be` | Phát hiện target `AF2409009889398096EAD3D83F6C92FD` trên `http://localhost:3001/simulation/pyramid-circumscribed-sphere` |
| `inspect_web_page` | `ev_3794817351eeaba52fc0aea92256dd060051e95598f6e05cde11d0d8f18b762d` | `dom_node_count=783`, `console_error_count=0`, `network_5xx_count=0`, 0 lộ token nhạy cảm |
| `capture_web_screenshot` | `ev_ba95843d6e3daf05c189a9c3a0db2e4bcd93d7537789a286bf1ca718575ed425` | [`images/db-closure-rea-mcp.png`](images/db-closure-rea-mcp.png) (`150,135` bytes, SHA-256 `6cb0d56f69c6838fc6ee537158a68be86bb02d9f384647c40b031da3d5780537`) |

---

## 13. Toàn Vẹn Seal & Worktree Root Được Bảo Vệ (`algo-sim`)

- **`freeze_evaluation_candidate.py --verify`:** `Candidate khớp bản đã đóng băng (mã sản phẩm: 109 file, e0ea792d71667f12…)` ([`seal-verify.log`](logs/seal-verify.log), `product_commit_sha = 2ff70ce455f0b298a7878880ab7eb3fee21cc572`).
- **Protected root checkout `D:\Documents\projects\algo-sim`:** Vẫn giữ nguyên nhánh `axo-ui-consistency` tại `bb046fa22aceff47abe22aa783aa64fc65caee13`, chỉ có untracked gốc `?? ocr_reconcile.py`; tệp `backend\algosim.db` giữ nguyên `413,696` bytes và SHA-256 `39d676c7b50a925975828434a00d38e3bac3c5f50e4e2a724a695768c7c83ee3`.
- **`main` & `origin/main`:** Cả hai vẫn nằm tại `bb046fa22aceff47abe22aa783aa64fc65caee13`.

---

## 14. Kiểm Tra Che Mật Khẩu & Dữ Liệu Nhạy Cảm (`Secret Audit`)

- Toàn bộ artifact trong `docs/evaluation/geometry/runs/db-safety-root-cause-closure/` (`json`, `log`, `md`) được quét regex tự động cho DSN kèm mật khẩu, chuỗi mật khẩu host DB, header Cookie/Authorization, và `client:`/`session_id` đầy đủ (`sessionId` chỉ ghi prefix `se-be5cdbf3-sa…` / `se-be5cdbf3-…`).
- **Kết quả quét:** `SECRET_LEAK_HITS = 0`.

---

## 15. Giới Hạn & Biên Còn Lại (Honest Residual Boundaries)

1. **`MODEL_STATUS = MODEL_NOT_TRAINED`:** Model 2 (`step-feedback`) chưa huấn luyện; `/api/simulation/feedback/status` xác nhận `model_trained=false, total_records=0`.
2. **Môi trường Docker & `pg_dump`:** Máy host Windows không chạy Docker daemon và bộ PG16 portable không có `pg_dump.exe`; tính tương thích runtime `Dockerfile` được chứng minh qua nội dung Dockerfile/preflight CLI (`tests/test_dev_backend_launcher.py`) và chạy trực tiếp PG 16 + Uvicorn với `ALGOSIM_STARTUP_MODE=1`.
3. **Database cũ chưa stamp (`algosim.db` có `alembic_version=NULL`):** `migration_preflight.py` từ chối nâng cấp tự động có chủ đích (`UNSTAMPED_EXISTING_DATABASE`), yêu cầu người vận hành backup và thực hiện quy trình đối chiếu/stamp thủ công tại [`docs/OPERATIONS.md`](../../../../OPERATIONS.md).
4. **Live Gemini key:** Kiểm định offline/live PG tại localhost dùng fallback/offline endpoints theo phạm vi Step Editor (`hasKey=false` tại `/api/health`); xác thực đầu cuối với `GEMINI_API_KEY` production nằm ngoài phạm vi kiểm thử offline này.

---

## 16. Lệnh Bàn Giao Cho Owner Sau Nghiệm Thu

- **Trạng thái hiện hành (KHÔNG ĐỔI cho tới khi Owner duyệt):**
  - `RELEASE_GATE = READY_FOR_OWNER_REVIEW`
  - `MERGE_STATUS = NOT_MERGED`
  - `PUSH_STATUS = NOT_PUSHED`
  - `MODEL_STATUS = MODEL_NOT_TRAINED`

Nếu Owner nghiệm thu đạt và muốn tích hợp clean candidate `release/axo-step-editor-db-safe-rc` lên `main`:

```powershell
# 1. Tạo bản sao lưu DB trước mọi thao tác phát hành (xem docs/OPERATIONS.md)
# 2. Chuyển sang repo/worktree có quyền merge lên main (chờ Owner thực hiện)
git fetch origin
git checkout main
git merge --ff-only release/axo-step-editor-db-safe-rc
# 3. Kiểm tra lại trên main sau merge trước khi push:
cd backend
python scripts/freeze_evaluation_candidate.py --verify
python scripts/audit_docs_information_architecture.py
python alembic/migration_preflight.py --startup --json
# 4. Chỉ push khi kiểm thử sau merge đạt:
git push origin main
```
