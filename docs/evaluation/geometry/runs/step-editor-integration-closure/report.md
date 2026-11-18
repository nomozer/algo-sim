# AXO Step Editor — Final Integration, Root-Cause Closure & Main Merge Gate (`step-editor-integration-closure`)

Báo cáo đầy đủ **17 mục** cho chiến dịch đóng rủi ro tích hợp cuối cùng trước cổng merge `main` nằm tại [AXO-STEP-EDITOR-INTEGRATION-CLOSURE-REPORT.md](AXO-STEP-EDITOR-INTEGRATION-CLOSURE-REPORT.md).

## Tóm tắt kết quả xác minh

- **Branch / Base HEAD:** `feat/axo-geometry-library-verification` trên nền commit `a493d89c0d3f58c87612faf3d1b2c1840569cac8` (`D:/Documents/projects/axo-geometry-library`). Root checkout `D:/Documents/projects/algo-sim` (`axo-ui-consistency`) và toàn bộ `77` file/hunk `OWNERSHIP_BLOCKED` của phiên song song không bị chạm tới.
- **Root Causes Closed (`IC-1`..`IC-5`):**
  - `IC-1`: Sửa race condition post-commit cancel — `_prev_snapshot` (1 cấp, O(1)) và metadata head active (`_client_request_id`, `_head_revision_id`, `_head_version_number`, `_head_committed_version`) lưu bền trong `StepEditSessionRecord.dependency_graph_json`. Cancel trễ của Request A đến sau Commit B bị từ chối sạch (`rolled_back_commit = false`, `noop_reason = "SUPERSEDED_BY_NEWER_COMMIT"`).
  - `IC-2`: Idempotency dựa trên `client_request_id` (`idempotent_replay = true`, `0` bản ghi revision/feedback trùng lặp trong DB qua restart) + đồng hồ `client_seq` đơn điệu qua `F5` reload (`localStorage` key `axo:step-edit-seq:v1`).
  - `IC-3`: Timeout trước commit gửi `only_if_uncommitted = true` lên `POST /api/simulation/steps/cancel` (chặn xóa nhầm commit đã chốt trên server); timeout sau commit hòa giải qua `GET /state` (`POST_COMMIT_RECOVERED`) có kiểm tra `recoverCtrl.signal.aborted`.
  - `IC-4`: Khắc phục 3 lỗi schema/index/env drift trên Alembic PostgreSQL (`alembic/env.py` import `step_edit_models`, `server_default=None`, index `unique=True` thay cho `UniqueConstraint` trùng); đóng gói patch chuyển giao tại [postgres-step-edit-alembic-handoff.patch](patches/postgres-step-edit-alembic-handoff.patch); xác minh `alembic check` (`No new upgrade operations detected`) + upgrade/downgrade/seed survival trên SQLite cô lập. PostgreSQL live giữ `POSTGRES_MIGRATION = BLOCKED` & `POSTGRES_VERIFICATION = NOT_VERIFIED` do `f8a2c41d9e05` đang `OWNERSHIP_BLOCKED` và host không có Docker/PostgreSQL daemon.
  - `IC-5`: Khóa cấu hình đơn worker Uvicorn (`Dockerfile`, `docker-compose.yml`) + guard runtime fail-closed trả HTTP `503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` nếu bật `WEB_CONCURRENCY > 1`, `UVICORN_WORKERS > 1`, hoặc `GUNICORN_CMD_ARGS` `--workers > 1`.
- **Sequential Regression Gates (sau lần sửa code cuối cùng):**
  - `pytest tests/geometry/test_step_editor_integration_closure.py -v`: `4 passed, 1 deselected in 17.85s`.
  - Toàn bộ 8 suite Step Editor backend: `167 passed, 1 deselected in 56.02s` (`0` failures).
  - `pytest tests/geometry -q`: `11976 passed, 6 skipped, 2 deselected, 9 xfailed, 15 failed in 394.53s` (`0` failure Step Editor).
  - `pytest tests/semantic_program --ignore=tests/semantic_program/test_evaluation_candidate.py -q`: `1166 passed, 1 skipped in 6.94s`; `test_evaluation_candidate.py`: `25 passed, 1 failed` (`measured_system.tree_hash` drifted từ candidate đóng băng `88ff25730`).
  - `pytest tests --ignore=tests/geometry --ignore=tests/semantic_program -q`: `793 passed, 2 deselected in 95.13s`.
  - `replay_demo_cases.py`: `5/5 + 1/1` PASS; `audit_demo_crash_surface.py`: `6/6` (`0` unhandled `500`).
  - `npx vitest run` (standalone): `192 passed (192)` files, `2271 passed (2271)` tests (`151.86s`); `npx tsc -b` & `npx vite build`: `0` lỗi, built trong `8.48s`.
- **Host Sống (`:3001` & `:8000`) + Isolated Restart (`:8019`) + REA MCP (`:9338`):** Toàn bộ Cases 1–7, `8` viewport (`1920..320` `overflowX = 0`), post-`F5` monotonic `client_seq`, late stale cancel, tab close/reopen, isolated Uvicorn subprocess restart (`pid 16176 -> 2608`), và REA MCP (`ev_fcfecf8a...`, `ev_3337f7f4...`, `ev_ca0b352d...`) đều đạt.

```text
GEOMETRY_MUTATION = PASS
DOWNSTREAM_REBUILD = PASS
ATOMIC_COMMIT = PASS
CANCEL_RACE_SAFETY = PASS
PERSISTENCE_INTEGRITY = PASS
POSTGRES_MIGRATION = BLOCKED
CONCURRENCY_SINGLE_WORKER = PASS
CONCURRENCY_MULTI_WORKER = NOT_SUPPORTED
STEP_EDITOR_UX = PASS
REGRESSION_GATES = PARTIAL
OWNERSHIP = CLEAN
HOST_QA = PASS
MODEL_STATUS = MODEL_NOT_TRAINED
MERGE_READINESS = CONDITIONAL
OWNER_APPROVAL = PENDING_OWNER_REVIEW
```
