# AXO Step Editor — Final Integration, Root-Cause Closure & Main Merge Gate Report

- **Campaign:** `AXO STEP EDITOR — FINAL INTEGRATION, ROOT-CAUSE CLOSURE & MAIN MERGE GATE`
- **Date:** `2026-11-18`
- **Branch / Worktree:** `feat/axo-geometry-library-verification` @ `D:/Documents/projects/axo-geometry-library`
- **Base HEAD Before This Run:** `a493d89c0d3f58c87612faf3d1b2c1840569cac8` (`docs(step-editor): complete final pre-merge verification and local approval gate`)
- **Model Status:** `MODEL_NOT_TRAINED` (deterministic zero-LLM closed grammar + Exact Kernel `Fraction`/`Radical`; zero external LLM calls during step edits)
- **PostgreSQL Live Verification:** `POSTGRES_MIGRATION = BLOCKED` · `POSTGRES_VERIFICATION = NOT_VERIFIED`
- **Physical Mobile Hardware:** `PHYSICAL_MOBILE = NOT_VERIFIED` (verified only in headless Chromium mobile viewports + touch emulation)

---

## 1. Executive Summary

Chiến dịch đóng rủi ro tích hợp cuối cùng trên nhánh `feat/axo-geometry-library-verification` đã hoàn tất việc truy tìm và khắc phục **5 nguyên nhân gốc còn tồn tại (`IC-1`..`IC-5`)** sau đợt Final Pre-Merge, kiểm chứng lại toàn bộ hệ thống trên kiến trúc chính thức `Hybrid /4` + đơn worker Uvicorn:

1. **Khóa race condition Post-Commit Cancel (`IC-1`):** Cancel trễ của Request A (gồm cả `abort` khi bị supersede hoặc gửi muộn từ tab/mạng chậm) đến sau khi Request B đã commit **không bao giờ** ghi đè hoặc rollback Request B; server kiểm tra cả `_client_request_id`, `_head_revision_id`, `_head_version_number` trên bản ghi DB và chỉ cho phép rollback đúng 1 cấp active head (`_prev_snapshot` bounded O(1)), từ chối cancel lỗi thời với `rolled_back_commit = false` và `noop_reason = "SUPERSEDED_BY_NEWER_COMMIT"`.
2. **Idempotency & Monotonic Sequence xuyên `F5` Reload (`IC-2`):** Retry cùng `client_request_id` (từ bộ đệm draft `pendingRetryKeys` khi rớt mạng/timeout) trả thẳng trạng thái đã commit (`idempotent_replay = true`) và ghi đúng `0` bản ghi `step_edit_revisions` / `step_edit_feedback` trùng lặp; đồng thời đồng hồ `client_seq` lưu qua `localStorage` (`axo:step-edit-seq:v1` trong `allocateMonotonicSubmitSeq()`) bảo đảm mọi lượt sửa sau `F5` reload đều tăng ngặt, chấm dứt lỗi `409 EDIT_SUPERSEDED` giả sau reload.
3. **Timeout Pre-Commit vs Post-Commit Reconciliation (`IC-3`):** Hủy do timeout client gửi cờ `only_if_uncommitted = true` để chỉ hủy tác vụ chưa commit và không hoàn tác commit đã chốt trên server (`ALREADY_COMMITTED`), kết hợp hòa giải có giới hạn qua `GET /api/simulation/sessions/{session_id}/state` (`POST_COMMIT_RECOVERED`) có bảo vệ tín hiệu `if (!recoverCtrl.signal.aborted)`.
4. **Migration Alembic & Handoff PostgreSQL (`IC-4`):** Phát hiện và sửa triệt để 3 lỗi schema/index/env drift trên bản nháp migration (`backend/alembic/env.py` nạp `step_edit_models` vào `Base.metadata`, bỏ `server_default` lệch ORM, bỏ `UniqueConstraint` trùng bên cạnh index `unique=True`), xác minh `alembic check` (`No new upgrade operations detected`) + upgrade/downgrade/seed survival trên SQLite cô lập và đóng gói thành patch [postgres-step-edit-alembic-handoff.patch](patches/postgres-step-edit-alembic-handoff.patch). PostgreSQL container chưa có trên host nên `POSTGRES_MIGRATION = BLOCKED` / `POSTGRES_VERIFICATION = NOT_VERIFIED`.
5. **Ranh giới Concurrency & Topology (`IC-5`):** Xác nhận `Dockerfile` + `docker-compose.yml` chạy đơn worker Uvicorn, đồng thời gắn guard runtime `_assert_single_worker_runtime()` trong `step_edit_router.py` fail-closed HTTP `503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` nếu cấu hình `WEB_CONCURRENCY > 1`, `UVICORN_WORKERS > 1`, hoặc `GUNICORN_CMD_ARGS` `--workers > 1`.
6. **Phân loại đầy đủ toàn bộ failure & Gate sống:** Phân loại minh bạch 100% các failure ngoài phạm vi Step Editor (`13` candidate hash drift + `1` `test_evaluation_candidate.py` hash drift + `4` stale Classroom path trong `docs/CODE_INDEX.md` + `1` `test_curriculum_coverage.py::test_KHONG_co_mat_cong...` + `audit-layout.mjs` exit `2`), chứng minh oracle đa bước sớm (`SM/SA = 1/2 -> 1/4 -> 3/4`), kiểm tra Uvicorn subprocess restart thật (`:8019`), live host QA Cases 1–7 + 8 viewports (`:3001` & `:8000`), và REA MCP CDP (`:9338`).

---

## 2. Input Baseline & Ownership Audit

| Hạng mục | Trạng thái xác minh |
|---|---|
| Worktree thực thi | `D:/Documents/projects/axo-geometry-library` |
| Branch mục tiêu | `feat/axo-geometry-library-verification` |
| Commit nền đầu chiến dịch | `a493d89c0d3f58c87612faf3d1b2c1840569cac8` |
| Root checkout được bảo vệ | `D:/Documents/projects/algo-sim` (branch `axo-ui-consistency`, **không chạm tới**) |
| Tài sản `OWNERSHIP_BLOCKED` của phiên song song | Toàn bộ `77` file/hunk trên working tree (`backend/app/main.py`, `backend/app/accounts/*`, `backend/app/persistence/classroom_models.py`, `backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py`, `backend/tests/test_postgres_axo_history_migration.py`, `docs/EVIDENCE_INDEX.md`, `frontend/package*.json`, Landing/Auth/Classroom components, `SimulationWorkspace.tsx`) được giữ nguyên hoàn toàn |
| Chính sách Git & Staging | Chỉ stage allowlist từng đường dẫn qua `git add <path>`; kiểm tra `git diff --cached --name-only`; chỉ commit cục bộ trên `feat/axo-geometry-library-verification`; **không `git merge main`, không `git push`** |

---

## 3. Root-Cause Closure Matrix (`IC-1` .. `IC-5` + `FP-1` .. `FP-6`)

| Mã lỗi | Thành phần | Hiện tượng RED trước sửa | Nguyên nhân gốc | Cách khắc phục tận gốc | Trạng thái sau sửa |
|---|---|---|---|---|---|
| **IC-1** | `backend/app/simulation/step_edit_router.py` | Cancel trễ của Request A (sau khi B đã commit) rollback luôn hoặc làm mất dữ liệu Commit B; `_LAST_COMMIT_SNAPSHOT` lưu thuần in-memory nên mất qua restart | Bảng snapshot cũ chỉ map theo `(owner_scope, session_id, client_request_id)` trên RAM, không vô hiệu hóa bản cũ khi B commit và không đối chiếu active head revision trên DB | Lưu `_prev_snapshot` (đúng 1 cấp nhờ `_build_head_snapshot_dep`), `_client_request_id`, `_head_revision_id`, `_head_version_number`, `_head_committed_version`, `_head_feedback_id`, `_head_response_meta` bền vững trong `StepEditSessionRecord.dependency_graph_json`; `cancel_construction_step_edit` kiểm tra `is_head_commit` trước khi rollback và từ chối cancel cũ với `SUPERSEDED_BY_NEWER_COMMIT` | **CLOSED** (`test_ic1...`, Case 5b live QA, `:8019` restart) |
| **IC-2** | `step_edit_router.py` & `frontend/src/state/construction-step-edits.ts` | (a) Retry cùng `client_request_id` (từ network retry/timeout) tạo bản ghi revision/feedback trùng hoặc dính `409 EDIT_SUPERSEDED`; (b) Bộ đếm `nextSubmitSeq` trong module reset về `1` sau `F5` reload gây `409` giả với backend còn nhớ `_LATEST_CLIENT_SEQ` | (a) Chưa lưu `_client_request_id` bền vào revision/session để replay idempotent; (b) `nextSubmitSeq` không lưu bền qua reload và `pendingRetryKeys` chưa tái sử dụng khóa request giữa các lần retry cùng draft lỗi | (a) Lưu `_client_request_id` trong `stage_timings_json` & `dependency_graph_json`, bổ sung `_replay_existing_request` trả `200 idempotent_replay=true` (và hoàn `client_seq <= latest_seq`); (b) Dùng `pendingRetryKeys` giữ nguyên `clientRequestId` khi retry cùng draft và lưu `allocateMonotonicSubmitSeq()` qua `localStorage` (`axo:step-edit-seq:v1`) | **CLOSED** (`test_ic1...`, HTTP 10 retries `[25,25]`, Case 2 post-`F5`) |
| **IC-3** | `step_edit_router.py` & `construction-step-edits.ts` | Client timeout gửi `/steps/cancel` có thể xóa luôn commit đã hoàn tất trên server hoặc treo `fetch("/state")` với `AbortSignal` đã abort | `StepEditCancelRequest` không phân biệt hủy tác vụ đang kẹt vs rollback commit; nhánh `timeout` gọi `fetch("/state", { signal: recoverCtrl.signal })` khi `recoverCtrl` đã hết hạn 60ms | Thêm `only_if_uncommitted: bool = False` trên `/steps/cancel` (chặn xóa `ALREADY_COMMITTED`); client gọi `/steps/cancel` với `only_if_uncommitted: true` khi timeout, kiểm tra `if (!recoverCtrl.signal.aborted)` trước `fetch("/state")`, hòa giải `POST_COMMIT_RECOVERED` hoặc giữ draft cùng `clientRequestId` để retry | **CLOSED** (`test_ic1...`, Vitest `BUG-3` `24/24`) |
| **IC-4** | `backend/alembic/env.py` + patch `postgres-step-edit-alembic-handoff.patch` | Bản nháp migration có 3 điểm lệch schema so với ORM `step_edit_models.py` khi chạy `alembic check` | (1) `env.py` chưa import `app.persistence.step_edit_models`; (2) cột khai báo `server_default` không tồn tại trên ORM; (3) khai báo thêm `UniqueConstraint` thừa bên cạnh index `unique=True` | Đối chiếu schema bằng SQLAlchemy introspection, tạo bản nâng cấp sạch `9c4d8e2b7a10` trong `patches/postgres-step-edit-alembic-handoff.patch` + test `test_ic4...` xác minh `alembic check` báo `"No new upgrade operations detected"` trên SQLite cô lập | **HANDOFF PATCH VERIFIED** (PostgreSQL live: `BLOCKED` / `NOT_VERIFIED`) |
| **IC-5** | `step_edit_router.py` (`_assert_single_worker_runtime`) | Chưa có chốt chặn runtime nếu triển khai bật multi-worker (`WEB_CONCURRENCY > 1`, `--workers > 1`) dùng chung lock in-memory | Lock `_SESSION_LOCKS`, `_CANCELLED_REQUESTS`, `_LATEST_CLIENT_SEQ` nằm trong tiến trình đơn; thiếu guard từ chối khi env multi-worker được bật | Xác minh `Dockerfile` & `docker-compose.yml` đơn worker (`no --workers`); thêm `_assert_single_worker_runtime()` trả HTTP `503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` trên `/steps/edit`, `/steps/cancel`, `/sessions/{id}/state` | **CLOSED** (`test_ic5...`) |
| **FP-1..FP-6** | `step_editor.py`, `scene3d-model.ts`, `step_edit_router.py`, `construction-step-edits.ts` | Toàn bộ 6 nguyên nhân gốc đã đóng ở commit nền `a493d89c0` (unnamed bisector / comma ratio parser, exact equivalence `before_after_diff`, `before_mem` `quantity` & global invariants, Hybrid rebind mark, `committed_version` clock, DB `503` isolation) | Kế thừa toàn bộ | Giữ nguyên và kiểm chứng lại không hồi quy (`167 passed` trên toàn bộ 8 suite Step Editor) | **PRESERVED** |

---

## 4. Post-Commit Cancel Race & Idempotency Verification

Mọi kịch bản dưới đây đã được chứng minh trên cả backend tự động (`test_ic1_ic2_ic3_cancel_race_timeout_idempotency_and_restart`, HTTP real Uvicorn `:8019`, HTTP 25+10 retries) và live browser (`integration-closure-qa.mjs`):

| # | Kịch bản kiểm chứng | Kỳ vọng | Bằng chứng thực tế |
|---|---|---|---|
| 1 | Hủy khi request đang kẹt / trước commit (`only_if_uncommitted=true` hoặc flag `_CANCELLED_REQUESTS`) | Không commit lên DB, giữ state cũ sau `F5` | Live Case 5a (`cancelHttpStatus=200`, `cancelledEditDidNotPersistAfterReload=true`) & `test_ic1...` |
| 2 | Hủy active head khi chỉ có 1 request vừa commit (`rolled_back_commit=true`, explicit `Cancel B`) | Hoàn tác 1 cấp về snapshot trước (`v1`) sạch trên DB | `:8019` restart check (`head_cancel_B_after_restart.rolled_back_commit=true`, `restored_M=["0","0","9/2"]`) & `test_ic1...` |
| 3 | Cancel trễ của Request A đến **sau** khi Request B đã commit | Từ chối rollback B (`rolled_back_commit=false`, `noop_reason="SUPERSEDED_BY_NEWER_COMMIT"`), giữ nguyên B và dữ liệu B | Live Case 5b (`reqAClientSeq=8`, `bSurvivedInUiAfterF5=true`, `bMCoordsInServerStateAfterF5=["0","0","24/5"]`, `bCommittedVersionInState=4`) & `test_ic1...` |
| 4 | Hủy A rồi retry cũ của A | Từ chối đúng mã (`409 EDIT_SUPERSEDED` khi B đã vượt sequence hoặc `EDIT_CANCELLED` khi A bị hủy thực sự) | `test_ic1...` (fixed stale cancel popping `canc_key` when `not cancelled_result`) |
| 5 | Client timeout **trước** khi server commit | Client gửi `only_if_uncommitted=true` -> abort tác vụ chưa commit, giữ state cũ | `test_ic1...` & `BUG-3` Vitest (`24 passed`) |
| 6 | Client timeout **sau** khi server đã commit | `only_if_uncommitted=true` trả `ALREADY_COMMITTED` (không xóa commit); client gọi `GET /state` hòa giải về `POST_COMMIT_RECOVERED` khớp `backend === frontend` | `test_ic1...` & Vitest `BUG-3` (`24 passed`) |
| 7 | Offline/network retry với **cùng `client_request_id`** | Server trả `200 idempotent_replay=true`, **`0` bản ghi `step_edit_revisions` / `step_edit_feedback` trùng** | HTTP 25 commits + 10 retries (`revisions=[25,25]`, `feedback=[25,25]`), Live Case 5 (`reusedClientRequestIdOnRetry=true`, `reconnectStatus=200`), `:8019` retry sau restart |
| 8 | Sửa liên tiếp **sau `F5` reload** | `client_seq` từ `localStorage` tăng đơn điệu (`6 -> 7`), commit `200` (không dính `409 EDIT_SUPERSEDED`) | Live Case 2 (`postF5Edit.httpStatus=200`, `clientSeqBeforeF5=6`, `clientSeqAfterF5=7`, `monotonicAcrossReload=true`, `rebuiltMCoords=["0","0","4"]`) |
| 9 | Đóng hẳn tab & mở lại trang mô phỏng | Frontend gọi `GET /api/simulation/sessions/{sid}/state`, khôi phục đúng commit mới nhất với **`0` duplicate `POST /steps/edit`** | Live Case 6 (`restoredViaGetStateCount=2`, `duplicateEditPostsOnReopen=0`, `expectedLastRatioRestored=true`) |
| 10 | Restart tiến trình Uvicorn giữ state head/cancel/idempotency | State v2, từ chối stale `Cancel A`, idempotent retry B và rollback head B sống sót hoàn toàn qua restart PID (`16176 -> 2608`) | `integration_closure_perf_and_restart.py` trên `127.0.0.1:8019` (`sqlite://.../restart_verify.db`) |

---

## 5. PostgreSQL Migration & Persistence Verification

- **Trạng thái trung thực:** `POSTGRES_MIGRATION = BLOCKED` · `POSTGRES_VERIFICATION = NOT_VERIFIED`.
  - Hai file khóa chuỗi Alembic chính là `backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py` và `backend/tests/test_postgres_axo_history_migration.py` (cố định `AXO_HEAD = "f8a2c41d9e05"`) thuộc danh sách **`OWNERSHIP_BLOCKED`** của phiên song song.
  - Máy host hiện tại không chạy Docker (`docker info` lỗi thiếu `//./pipe/dockerDesktopLinuxEngine`) và không cài dịch vụ PostgreSQL cục bộ.
- **Sửa 3 lỗi drift (`IC-4`) & Đóng gói Handoff Patch:**
  1. `backend/alembic/env.py` cần import `app.persistence.step_edit_models` để `Base.metadata` nhận diện 3 bảng `step_edit_sessions`, `step_edit_revisions`, `step_edit_feedback`.
  2. Toàn bộ cột trong `step_edit_models.py` có `server_default=None`; bản migration handoff loại bỏ `server_default` lệch ORM.
  3. Cột `revision_id` và `feedback_id` khai báo `unique=True, index=True`, phát sinh index duy nhất `ix_step_edit_revisions_revision_id` và `ix_step_edit_feedback_feedback_id` (`unique=True`) mà không đẻ thêm `UniqueConstraint` thừa.
- **Kiểm chứng trên SQLite cô lập (`test_ic4_alembic_handoff_migration_upgrade_downgrade_zero_drift`):**
  - Copy chuỗi migration sang thư mục tạm, áp bản nâng cấp `9c4d8e2b7a10` (con trực tiếp của `f8a2c41d9e05`):
  - Upgrade từ `a1c7e4b90d52` -> seed dữ liệu nền (`users`, `learning_history_entries`) -> `upgrade head` (`9c4d8e2b7a10`) -> chạy `alembic check` thu đúng chuỗi **`No new upgrade operations detected`** -> CRUD Step Edit -> `downgrade f8a2c41d9e05` kiểm tra bảng `step_edit_*` bị gỡ sạch và dữ liệu seed nền nguyên vẹn -> `upgrade head` lần hai.
  - File patch sẵn sàng áp dụng cho Owner/Admin khi tích hợp hai nhánh: [postgres-step-edit-alembic-handoff.patch](patches/postgres-step-edit-alembic-handoff.patch).
  - Trong `backend/app/persistence/step_edit_models.py`, hàm `ensure_step_edit_tables()` dùng `Base.metadata.create_all(..., checkfirst=True)` cho dev/test SQLite cục bộ; đường production PostgreSQL cần chạy patch Alembic trước khi mở lưu lượng.

---

## 6. Concurrency & Deployment Topology Scope

| Cấu hình | Mô tả | Trạng thái | Căn cứ kỹ thuật |
|---|---|---|---|
| **Config A** | Đơn tiến trình Uvicorn (`1` worker HTTP, nhiều thread async/sync qua FastAPI threadpool) | **PASS** | `Dockerfile` (`CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`) & `docker-compose.yml` không bật `--workers`; `_SESSION_LOCKS` (`RLock`), `_CANCELLED_REQUESTS`, `_LATEST_CLIENT_SEQ` đồng bộ hóa toàn bộ request cùng session; khóa bởi `test_analyze_idempotency.py:296` và `test_ic5...` |
| **Config B** | Đa tiến trình truy cập trực tiếp file SQLite (`test_fp6` với 2 process đua + 4 process `USER_0..3`) | **PASS (chỉ lớp SQLite DB)** | Đã kiểm thực nghiệm ở SQLite file locking + DB unique constraints. **Không ngoại suy** thành hỗ trợ đa worker HTTP vì khóa in-memory không chia sẻ giữa các worker process |
| **Config C** | Đa worker HTTP Uvicorn / Gunicorn (`WEB_CONCURRENCY > 1`, `UVICORN_WORKERS > 1`, hoặc `--workers > 1`) | **NOT_SUPPORTED (Fail-Closed)** | Bị khóa cứng ở cả deploy config lẫn runtime guard `_assert_single_worker_runtime()` trả HTTP `503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` (`test_ic5...` PASS). Muốn mở khóa Config C về sau bắt buộc chuyển trạng thái hủy/sequence/lock sang Postgres advisory lock / bảng trạng thái phân tán hoặc Redis |

---

## 7. Geometry Rebuild & Exact Kernel Proof

- **Independent Pure-`Fraction` Early-Step Multi-Hop Cascade (`test_mission_f_early_step_multi_hop_cascade_analytical_oracle` & `backend-perf-comparison.json`):**
  - Hình chóp tứ giác vuông tổng hợp `S.ABCD` (`SA=8`, đáy vuông tâm `O` cạnh `4`), nhánh độc lập `K = midpoint(B,D) = (2, 2, 0)` không phụ thuộc `M`.
  - Đột biến bước sớm `M` trên `SA` hai lần liên tiếp: `SM/SA = 1/2 -> 1/4 -> 3/4`:
    - Tại `r = 1/4`: `M = ['0','0','6']`, `E = ['2','0','4']`, `F = ['0','2','4']`, diện tích thiết diện ngũ giác `MENPF` = **`10√3`**, `K` giữ nguyên `['2','2','0']` trong `skipped_unaffected_ids`.
    - Tại `r = 3/4`: `M = ['0','0','2']`, `E = ['18/5','0','4/5']`, `F = ['0','18/5','4/5']`, diện tích `S_td` = **`22√11/5`**, `K` tiếp tục bảo toàn chính xác, khớp 100% công thức giải tích thuần `Fraction` độc lập với Kernel.
- **Nhóm A / B / C / D (`test_step_editor_final_premerge.py` — `14 passed`):**
  - Group A: ngữ nghĩa tương đương (`before_after_diff.changed = false`, chu trình `MENPF` bất biến nhị diện).
  - Group B: tứ diện vuông `O.ABC` khớp oracle giải tích độc lập và bảo toàn qua `GET /state`.
  - Group C (`6/6`): từ chối `422` khi phá bất biến toàn cục (tâm mặt cầu ngoại tiếp, vuông góc chung `PQ ⊥ BD`, góc nhị diện, chân hình chiếu mặt bên, liên thuộc mặt phẳng `(MNP)`, đường cao `SA`).
  - Group D (`9/9`): từ chối có cấu trúc với điểm thiếu (`SZ`), snake_case (`d_khong_ton_tai`), thẳng hàng (`A,O,C`), sai loại bước, chu trình phụ thuộc, khối cong ngoài phạm vi, tỉ số âm.
- **Quét 22 mẫu thư viện thực tế (`backend-perf-comparison.json`):**
  - `22` mẫu · `166` bước UI trích xuất bằng bộ trích xuất thật của `SimulationWorkspace.tsx` -> `135` editable thử nghiệm -> **`117 passed`**, **`0` `identity_false_diff_changed`**, **`0` rò rỉ `_prime`**, `18` bước còn lại từ chối đúng thiết kế (hình nón/trụ/cầu ngoài phạm vi V1, bước readout tự động, hoặc mô tả trơn thiếu phép dựng tường minh).

---

## 8. Step Editor V1 UX Preservation Check

- **Zero sửa đổi giao diện V1 & Landing Page:** `ConstructionStepEditor.tsx`, `SimulationWorkspace.tsx`, `global.css`, `LandingView`, `/`, `/gioi-thieu` không bị thay đổi bất kỳ dòng nào trong chiến dịch này (`git diff` phần `OWNERSHIP` riêng của Step Editor = `0` byte UI component).
- **Xác minh DOM trực tiếp trên `:3001` (`live-host-qa.json`):**
  - Hover hàng bước `(α)`: `defaultHeightPx = 56.875 px === hoverHeightPx = 56.875 px` (`heightDeltaPx = 0`), nút bút chì ẩn mặc định (`opacity: "0"`) và hiện khi hover (`opacity: "1"`).
  - Mở editor: `openMs = 69.23 ms`, chỉ gồm đúng `["Hủy", "Chạy"]` (không thêm nút `"Lưu"`/`"Huấn luyện"`), focus cô lập trong textarea (`Space` / `ArrowLeft` không đổi bước đang chọn `#pa-short-title`, `Escape` đóng editor).
  - `MODEL_STATUS = MODEL_NOT_TRAINED` (giữ trung thực tuyệt đối theo API `/api/simulation/feedback/status`).

---

## 9. Full Regression Gate Classification (Chạy Tuần Tự Sau Lần Sửa Code Cuối Cùng)

| Gate / Lệnh kiểm tra | Kết quả thực đo | Phân loại |
|---|---|---|
| `pytest tests/geometry/test_step_editor_integration_closure.py -v` | **`4 passed, 1 deselected in 17.85s`** (`IC-1..IC-5`, multi-hop oracle; deselect đúng 1 `@pytest.mark.postgres` do không có PostgreSQL) | **PASS** |
| Toàn bộ 8 suite Step Editor backend (`test_center_radius_ball.py`, `test_curved_foundation.py`, `test_curved_v1_e2e_qa.py`, `test_step_editor_v22.py`, `test_step_editor_root_cause_stabilization.py`, `test_step_editor_independent_acceptance.py`, `test_step_editor_final_premerge.py`, `test_step_editor_integration_closure.py`) | **`167 passed, 1 deselected in 56.02s`** (`0` failures) | **PASS** |
| `pytest tests/geometry -q` (toàn bộ 26 file) | **`11976 passed, 6 skipped, 2 deselected, 9 xfailed, 15 failed in 394.53s`** (`0` failure Step Editor) | **PARTIAL (15 non-Step-Editor failures đã phân loại đủ bên dưới)** |
| `pytest tests/semantic_program --ignore=tests/semantic_program/test_evaluation_candidate.py -q` | **`1166 passed, 1 skipped in 6.94s`** | **PASS** |
| `pytest tests/semantic_program/test_evaluation_candidate.py -q` | **`25 passed, 1 failed in 31.62s`** | **EXPECTED_EXCEPTION (`88ff25730` hash drift)** |
| `pytest tests --ignore=tests/geometry --ignore=tests/semantic_program -q` | **`793 passed, 2 deselected in 95.13s`** | **PASS** |
| `python scripts/replay_demo_cases.py` & `python scripts/audit_demo_crash_surface.py` | **`5/5 + 1/1` PASS**, **`6/6` bounded (`NÉM RA NGOÀI (=500): 0`)** | **PASS** |
| `npx vitest run src/components/construction-step-editor.test.tsx src/code-index-sync.test.ts` | **`24 passed (2 files)` (`21/21` + `3/3`, `5.83s`)** | **PASS** |
| `npx vitest run` (full standalone) | **`192 passed (192)` files, `2271 passed (2271)` tests (`151.86s`), `0` failures** | **PASS** |
| `npx tsc -b` & `npx vite build` | **`0` TS errors; production `dist/` built trong `8.48s`** | **PASS** |
| `python backend/scripts/audit_docs_information_architecture.py` | `Ownership domains valid: True`, **`Internal links broken: 0`**, `Secret leaks: 0`, `Docs root closed list: True (29 root docs, 167 catalogued, unclassified [])`, exit `1` chỉ vì **`CODE_INDEX stale paths: 4`** | **BLOCKED_OWNERSHIP (4 path Classroom)** |
| `node frontend/scripts/audit-layout.mjs --port 3001` | Exit `2` (`✖ KHÔNG TỚI ĐƯỢC "Trang chủ" — đang ở "UNKNOWN". Bản soát này KHÔNG hợp lệ.`) | **PRE_EXISTING (script cũ)** |

### Bảng Pháp Y Đầy Đủ Toàn Bộ Failure / Exception Ngoài Step Editor (7 Tiêu Chí Bắt Buộc)

| 1. Tên test / script (chính xác) | 2. Nguyên nhân gốc | 3. Lỗi sản phẩm hay outdated test/seal/ownership | 4. Liên quan Step Editor | 5. Ảnh hưởng phát hành | 6. Chủ sở hữu | 7. Bằng chứng an toàn |
|---|---|---|---|---|---|---|
| `tests/semantic_program/test_evaluation_candidate.py::test_ma_san_pham_khong_troi_khoi_ban_da_dong_bang` | `measured_system.tree_hash` hiện là `e7723a3cc3e164b4ac04eb411794691bf56c29f2dc349194c3d67b5b723d5d1c` (`109` file) khác mốc đóng băng `88ff25730` (`b1a8d439fe488c2a192d4ce48ef2a7e43f265957f37a9204d466534bf44f4bfc`, `106` file) do sản phẩm thêm `step_editor.py`, `step_edit_router.py`, `step_edit_models.py`, `step_edit_route.py`, `feedback_dataset.py` dưới `backend/app/` | **Outdated frozen seal** (thay đổi sản phẩm hợp pháp sau mốc `88ff25730`; không được sửa lén manifest đóng băng) | Không phải lỗi chức năng Step Editor; Step Editor thêm file vào `backend/app/` nên kích hoạt cảnh báo con dấu | Không gây lỗi runtime; cần Owner quyết định re-seal chính thức khi tổng hợp `main` | Owner evaluation manifest (`docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json`) | `25/26` test còn lại trong cùng file PASS; toàn bộ `1166` test `semantic_program` PASS |
| `tests/geometry/test_docs_information_architecture.py::test_inv_20_candidate_and_cache_verify_only` | Cùng nguyên nhân: gọi `freeze_evaluation_candidate.py --verify` so sánh `tree_hash` live (`e7723a3cc3e1...`) với `EVALUATION_CANDIDATE.json` (`b1a8d439fe48...`) | **Outdated frozen seal** | Nt. | Nt. | Nt. | `test_docs_information_architecture.py` các bất biến còn lại (trừ `inv_08` & `inv_20`) đều PASS |
| `tests/geometry/test_docs_test_telemetry.py::test_inv_05_candidate_and_cache_verify_only` | Gọi `collect_candidate_cache_proof()` kiểm tra `tree_hash` khớp candidate `88ff25730` | **Outdated frozen seal** | Nt. | Nt. | Nt. | Các bất biến telemetry khác PASS |
| `tests/geometry/test_hybrid_backend_integration.py::test_version_constants_surface_fingerprints_and_historical_receipt_preservation` | Mọi version constants (`registry /33`, `planner /26`, `engine /24`, `CACHE_VERSION 132`, `RESPONSE_CONTRACT="flat"`) & surface fingerprints đều PASS tới dòng 526, chỉ fail ở `assert (combined_hash, file_count) == (frozen["tree_hash"], frozen["so_file"])` (`('e7723a3cc3e...', 109) == ('b1a8d439fe48...', 106)`) | **Outdated frozen seal** | Nt. | Zero lỗi ở pipeline `Hybrid /4` | Nt. | Traceback dòng 526 chứng minh 100% assertion trước đó PASS |
| `tests/geometry/test_independent_holdout_equivalence.py::test_h1_corpus_integrity_receipt_honest_pre_corpus_and_sealing_guards` | Guard kiểm chứng trước khi tạo H-1 receipt gọi check `measured_system` đối chiếu candidate `88ff25730` | **Outdated frozen seal** | Nt. | Không ảnh hưởng runtime app | Owner H-1 / seal | Chỉ fail ở guard hash candidate |
| `tests/geometry/test_independent_holdout_equivalence.py::test_c28_stratum_semantic_annotations_oracle_review_and_template_completeness` | Template C28 khóa `measured_system` SHA theo mốc cũ | **Outdated frozen seal** | Nt. | Không ảnh hưởng runtime app | Nt. | Nt. |
| `tests/geometry/test_live_campaign_c26.py::test_delegated_terms_bind_the_campaign` | Template/runner C26 đối chiếu `measured_system` live với `EVALUATION_CANDIDATE.json` `88ff25730` | **Outdated frozen seal** | Nt. | Không ảnh hưởng runtime app | Nt. | Nt. |
| `tests/geometry/test_live_campaign_c26.py::test_canary_then_full_suite_reuses_canary_rows_under_one_carried_ledger` | `run_delegated_c21_suite` ném `LiveRefused("measured_system differs from frozen EVALUATION_CANDIDATE.json")` | **Outdated frozen seal** | Nt. | Nt. | Nt. | Nt. |
| `tests/geometry/test_s2_student_language_pilot_runner.py` (**6 test**: `test_c21_delegated_authorization_accepts_in_scope_pilots_and_refuses_h1_or_forged_terms`, `test_c21_suite_halts_before_first_request_when_paid_not_verified_and_redacts_aq_key`, `test_c21_suite_executes_k1_s2_r1_automatically_and_enforces_global_caps_and_model_check`, `test_c21_review_r1_interrupt_persists_ledger_and_receipt_and_100pct_failure_is_not_verified_live`, `test_c21_registered_approval_templates_bind_current_runtime_identity_and_stale_runner_is_refused`, `test_sha256_file_and_approval_terms_are_invariant_under_windows_crlf_checkout`) | Cả 6 test đều fail duy nhất tại `LiveRefused("measured_system differs from frozen EVALUATION_CANDIDATE.json")` hoặc `K-1 template measured_system drifted from runtime_identity` (vì `measured_system` hiện tại là `e7723a3cc3e1...` khác template đóng băng tại `88ff25730`) | **Outdated frozen seal** | Nt. | Zero lỗi ở runtime app hay Step Editor; đây là guard ngân sách live API cho thí nghiệm S2/K1/R1 cũ | Chủ sở hữu pilot K-1/S-2/R-1 & candidate seal | Log `task-2859.log` dòng 865–938 xác nhận cùng một chuỗi hash drift |
| `tests/geometry/test_docs_information_architecture.py::test_inv_08_code_index_paths_exist` (và `audit_docs_information_architecture.py`) | 4 dòng Classroom trong `docs/CODE_INDEX.md` (`4612 LiveClassDock.tsx`, `4626 LiveClassStrip.tsx`, `4641 MonitorView.tsx`, `4653 classroom-sync.ts`) trỏ tới file đã bị phiên song song xóa (`D`) | **`BLOCKED_OWNERSHIP`** (không được sửa vùng Classroom của phiên song song trong `docs/CODE_INDEX.md`) | Không liên quan (phần Step Editor dòng 13–14 đã đồng bộ, `code-index-sync.test.ts` PASS `3/3`) | Cần đồng bộ trước khi merge `main` để CI tài liệu XANH | Phiên song song Classroom (`f8a2c41d9e05`) | Phần còn lại của audit: `Internal links broken: 0`, `Secret leaks: 0`, `unclassified []` |
| `tests/geometry/test_curriculum_coverage.py::test_KHONG_co_mat_cong_va_KHONG_co_phep_chieu_song_song` | Assert `not any("sphere" in f for f in dir(K))`, trong khi `kernel.py` đã thêm `circumscribed_sphere_center` ở commit `ef9c20160` trước đây | **Outdated pre-existing test** (không phải regression Step Editor) | Không liên quan (Step Editor không đụng `kernel.py` hay test này) | Không ảnh hưởng phát hành; các phép dựng hình cầu (`test_center_radius_ball.py`, `test_curved_foundation.py`) đều PASS | Nhóm phát triển Curved Kernel (`ef9c20160`) | `test_center_radius_ball.py` & `test_curved_foundation.py` đều PASS `100%` trong `167/167` |
| `frontend/scripts/audit-layout.mjs --port 3001` | Script viết ở `4db3558b5`/`422297b32` (M9-UX7) vào `/` và tìm `.nav-link` `"Trang chủ"` + `.history-view`; hiện `/` là `<LandingView />` còn workspace nằm tại `/app` (`App.tsx:698-700`) | **Outdated pre-existing audit script** | Không liên quan | Không ảnh hưởng phát hành; mọi route `/`, `/gioi-thieu`, `/app`, `/simulation/*` đạt `200` | Nhóm Landing / Navigation (`d04a445a6`) | `live-host-qa.json` kiểm chứng `8/8` viewport `overflowX = 0` trực tiếp trên `:3001` |

---

## 10. Live Host QA Matrix

Xác minh trực tiếp trên host sống sau khi restart `:8000` (`PID 17600`) và giữ nguyên Vite `:3001` (`results/live-host-qa.json`):

- **Public Routes:** `/` (`200`, `textLen=1907`, `overflowX=0`), `/gioi-thieu` (`200`), `/gioi-thieu?preview=v1.4` (`200`), `/app` (`200`).
- **Cases 1–6:**
  - **Case 1 (Sample 11 `(α)` `"Dựng mặt phẳng trung trực của AB."`):** `200`, `beforeAfterDiffChanged = false`, `defaultHeightPx = hoverHeightPx = 56.875`.
  - **Case 2 (Sample 1 `M` `"SM/SA = 1/4"` -> `F5` -> `"SM/SA = 1/3"`):** `200`, cập nhật `6` đối tượng (`["M","mp_MNP","E","F","thiet_dien","S_td"]`), `M = ["0","0","9/2"]`, `F5` giữ `1/4`, edit kế tiếp sau `F5` dùng `client_seq = 7 > 6` commit `200` (`M = ["0","0","4"]`). Cạnh bên lăng trụ `CC′` giữ Unicode `′` với `0` `_prime` leaks.
  - **Case 3 (Sample 11 `SZ`):** `422 MISSING_DEPENDENCY`, giữ draft & step cũ.
  - **Case 4 (`khoang-cach-hai-duong-cheo-nhau` `BP/BD = 1/5`):** `422 DOWNSTREAM_ORTHOGONALITY_BROKEN`, giữ draft & hình 3D sạch.
  - **Case 5 (Cancel race & Offline retry):** (5a) Cancel giữa chừng gửi `/steps/cancel` (`200`) + `F5` không lưu; (5b) Commit A (`reqAClientSeq=8`) -> Commit B (`1/5`) -> gửi cancel trễ cho A trả `{ rolled_back_commit: false, noop_reason: "SUPERSEDED_BY_NEWER_COMMIT" }` -> `F5` giữ B (`["0","0","24/5"]`); Offline giữ draft + retry tái sử dụng cùng `clientRequestId` trả `200`.
  - **Case 6 (Close & reopen tab):** Đóng page, mở tab mới tới `/simulation/chop-thiet-dien-ba-diem` -> gọi `GET /state` (`2` calls), **`0` duplicate `POST /edit`**, khôi phục đúng `"Lấy điểm M thuộc SA sao cho SM:MA = 3:1"`.
- **Case 7 — Responsive 8 Viewport (`overflowX = 0`, `canvasVisible = true`, `textareaHorizontalOverflow = false`, `controlsOccludeActions = false`, `runClipped = false`, `cancelClipped = false`):**

| Viewport | `canvas` (px) | `overflowX` | Textarea h-scroll | Buttons clipped / occluded | Ảnh bằng chứng |
|---|---|---|---|---|---|
| `1920×1080` | `1289×1042` | `0` | `False` | `False` / `False` | [ic-1920-state2-editing-open.png](images/ic-1920-state2-editing-open.png) |
| `1440×900` | `809×862` | `0` | `False` | `False` / `False` | [ic-vp-1440x900-editing.png](images/ic-vp-1440x900-editing.png) |
| `1366×768` | `735×730` | `0` | `False` | `False` / `False` | [ic-vp-1366x768-editing.png](images/ic-vp-1366x768-editing.png) |
| `1024×768` | `704×730` | `0` | `False` | `False` / `False` | Đo DOM (`live-host-qa.json`) |
| `768×1024` | `472×986` | `0` | `False` | `False` / `False` | [ic-vp-768x1024-editing.png](images/ic-vp-768x1024-editing.png) |
| `390×844` | `390×444` | `0` | `False` | `False` / `False` | [ic-vp-390x844-editing.png](images/ic-vp-390x844-editing.png) |
| `360×800` | `360×420` | `0` | `False` | `False` / `False` | [ic-vp-360x800-editing.png](images/ic-vp-360x800-editing.png) |
| `320×568` | `320×293` | `0` | `False` | `False` / `False` | [ic-vp-320x568-editing.png](images/ic-vp-320x568-editing.png) |

- **Touch (`390×844`), Reduced Motion & REA MCP (`http://127.0.0.1:9338`):**
  - Touch: `opacityBeforeTap="0"` -> `opacityAfterRowSelect="1"`, `editorOpenedViaTap = true` (lưu ý `PHYSICAL_MOBILE = NOT_VERIFIED` — chỉ mô phỏng trong Chromium headless).
  - Reduced motion: `prefersReducedMotionMatched = true`, `committedCleanly = true`.
  - REA MCP CDP trên `http://localhost:3001/simulation/pyramid-three-point-section`: `list_browser_targets` (`ev_fcfecf8abccbdc7c32562992d70946b73d3cf2bc04fabf14074233e9411a19bc`), `inspect_web_page` (`ev_3337f7f446d9c90115ac0c2f28f4edcd4f5ebd2c687e6a3d6715840c07948b62`, `dom_total_nodes = 698`, `console_events = 0`, `dropped_events.total = 0`), `capture_web_screenshot` (`ev_ca0b352db8f9126eca9fd123547061a10cdfdccfead5a888038f790dcbe08e94`, `133,855` bytes PNG tại [rea-mcp-cdp-screenshot.png](images/rea-mcp-cdp-screenshot.png)).

---

## 11. Performance & Stability Comparison (Pre-Merge vs Integration Closure)

| Chỉ số | Final Pre-Merge Baseline | Integration Closure (Observed) | Chênh lệch & Nhận xét |
|---|---|---|---|
| 22-Sample UI Steps Passing (`166` tổng / `135` editable) | `117` | **`117`** | Giữ nguyên độ phủ, `0` false identity diff, `0` `_prime` leak |
| Backend 50-Step Median / Mean / p95 (`total_ms`) | Median `18.699 ms` · p95 `27.035 ms` | **Median `16.307 ms` · Mean `17.942 ms` · p95 `28.319 ms`** | Median nhanh hơn **`-2.392 ms`**; chi tiết median từng pha: `parser = 0.195 ms`, `planner = 3.936 ms`, `kernel = 0.196 ms`, `scene3d_build = 3.237 ms`, `validation = 6.418 ms` |
| HTTP 25 Sequential Commits (`persistence_commit_ms` & `total_ms`) | Chưa tách riêng `persistence_commit_ms` | **`persistence_commit_ms` median `11.076 ms` (p95 `16.244 ms`)** · `http_total_ms` median `64.213 ms` (p95 `131.59 ms`) | `nested_prev_snapshot_bloat = false` (chỉ giữ 1 cấp snapshot, tránh phình JSON tuyến tính) |
| Idempotent Retry (`10` retries cùng `client_request_id`) | N/A | **Median `21.888 ms` (p95 `30.643 ms`)**, `revisions = [25, 25]`, `feedback = [25, 25]` | **`0` bản ghi trùng**, phục hồi trực tiếp từ DB |
| 25-Edit Backend `tracemalloc` Peak / Mean | Mean `134.679 ms` · Peak `754.22 KB` | **Mean `137.606 ms` · Peak `714.19 KB`**, `objects 24 -> 24` | Peak giảm `-40.03 KB` |
| Live Browser 20-Edit UI Round-Trip | Mean `331.43 ms` · p95 `464.14 ms` · Heap `77.63 -> 77.63 MB` | **Mean `374.69 ms` · p95 `444.72 ms` · Max `674.88 ms` · `canvasCountFinal = 1` · Heap `77.63 -> 77.63 MB`** | p95 nhanh hơn `-19.42 ms`, `0` WebGL canvas leak, `0` page errors |

> **Giới hạn đo lường bộ nhớ (Honest Disclosure):** Kết quả `tracemalloc` (`25` lượt backend) và `performance.memory` (`20` lượt browser) xác nhận không có phình đối tượng theo từng lượt (`objects 24 -> 24`, `_prev_snapshot` bị giới hạn O(1) ở `1` cấp, `canvasCountFinal = 1`, `heapDeltaMb = 0` trong phiên kiểm ngắn), **chưa phải** bằng chứng soak test dài hạn hàng trăm/nghìn lượt.

---

## 12. Artifacts: Screenshots, Logs, Patches & Test Outputs

- Manifest đợt chạy: [run.json](run.json) · Tóm tắt run: [report.md](report.md)
- Patch Alembic chuyển giao PostgreSQL: [postgres-step-edit-alembic-handoff.patch](patches/postgres-step-edit-alembic-handoff.patch)
- JSON kết quả thực đo:
  - [backend-perf-comparison.json](results/backend-perf-comparison.json)
  - [live-host-qa.json](results/live-host-qa.json)
  - [rea-mcp-inspection.json](results/rea-mcp-inspection.json)
- Screenshots đại diện (`16` ảnh PNG trong thư mục `images/`):
  - [ic-1920-state1-hover.png](images/ic-1920-state1-hover.png) · [ic-1920-state2-editing-open.png](images/ic-1920-state2-editing-open.png) · [ic-1920-case1-equiv.png](images/ic-1920-case1-equiv.png) · [ic-1920-case2-mutated-reloaded.png](images/ic-1920-case2-mutated-reloaded.png)
  - [ic-1920-case3-missing-dep-422.png](images/ic-1920-case3-missing-dep-422.png) · [ic-1920-case4-orthogonality-422.png](images/ic-1920-case4-orthogonality-422.png) · [ic-1920-prism-prime-check.png](images/ic-1920-prism-prime-check.png) · [rea-mcp-cdp-screenshot.png](images/rea-mcp-cdp-screenshot.png)
  - Viewports & Routes: [ic-vp-1440x900-editing.png](images/ic-vp-1440x900-editing.png) · [ic-vp-1366x768-editing.png](images/ic-vp-1366x768-editing.png) · [ic-vp-768x1024-editing.png](images/ic-vp-768x1024-editing.png) · [ic-vp-390x844-editing.png](images/ic-vp-390x844-editing.png) · [ic-vp-360x800-editing.png](images/ic-vp-360x800-editing.png) · [ic-vp-320x568-editing.png](images/ic-vp-320x568-editing.png) · [ic-route-landing.png](images/ic-route-landing.png) · [ic-route-gioi-thieu.png](images/ic-route-gioi-thieu.png)
- Video Playwright lưu tạm ngoài git tree trong thư mục scratch (không stage, không commit).

---

## 13. Changed Files & Ownership Verification

Các file sở hữu riêng trong commit allowlist của đợt này trên `feat/axo-geometry-library-verification`:

- `backend/app/simulation/step_edit_router.py`
- `backend/tests/geometry/test_step_editor_integration_closure.py`
- `frontend/src/state/construction-step-edits.ts`
- `frontend/src/components/construction-step-editor.test.tsx`
- `docs/CODE_INDEX.md` (chỉ dòng `13–14` cho mục Step Editor)
- `docs/evaluation/geometry/runs/step-editor-integration-closure/run.json`
- `docs/evaluation/geometry/runs/step-editor-integration-closure/report.md`
- `docs/evaluation/geometry/runs/step-editor-integration-closure/AXO-STEP-EDITOR-INTEGRATION-CLOSURE-REPORT.md`
- `docs/evaluation/geometry/runs/step-editor-integration-closure/patches/postgres-step-edit-alembic-handoff.patch`
- `docs/evaluation/geometry/runs/step-editor-integration-closure/results/*.json` (`3` files)
- `docs/evaluation/geometry/runs/step-editor-integration-closure/images/*.png` (`16` PNG files)

Toàn bộ `77` file/hunk `OWNERSHIP_BLOCKED` và `D:/Documents/projects/algo-sim` được bảo toàn nguyên vẹn.

---

## 14. Remaining Blockers Before `main`

1. **`POSTGRES_MIGRATION = BLOCKED` & `POSTGRES_VERIFICATION = NOT_VERIFIED`:** Sau khi nhánh Classroom tích hợp `f8a2c41d9e05`, cần áp [postgres-step-edit-alembic-handoff.patch](patches/postgres-step-edit-alembic-handoff.patch) vào `backend/alembic/env.py` và `backend/alembic/versions/`, rồi chạy `pytest -m postgres` trực tiếp trên PostgreSQL thật để xác nhận migration.
2. **Dọn `4` đường dẫn Classroom cũ trong `docs/CODE_INDEX.md` (dòng `4612–4653`):** Phiên sở hữu phần Classroom cần cập nhật 4 đường dẫn đã xóa (`LiveClassDock.tsx`, `LiveClassStrip.tsx`, `MonitorView.tsx`, `classroom-sync.ts`) để `audit_docs_information_architecture.py` và `test_inv_08_code_index_paths_exist` chuyển XANH.
3. **Owner quyết định Re-Seal Candidate (`EVALUATION_CANDIDATE.json`):** `measured_system.tree_hash` đã đổi từ `88ff25730` (`106` file) sang `e7723a3cc3e1...` (`109` file) do thêm module Step Editor dưới `backend/app/`. Cần một lần re-seal chính thức dưới thẩm quyền Owner trước khi hợp nhất hoàn chỉnh vào `main`.

---

## 15. Merge Gate Checklist

| Tiêu chí cổng | Trạng thái | Ghi chú |
|---|---|---|
| 1. Đóng toàn bộ lỗi gốc `IC-1`..`IC-5` (`FP-1`..`FP-6` bảo toàn) | **PASS** | `4/4` `test_step_editor_integration_closure.py`, `167/167` Step Editor suites |
| 2. Exact Kernel Geometry & Multi-Hop Analytical Oracle | **PASS** | `1/4 -> 3/4` khớp công thức giải tích thuần `Fraction`, `117/117` zero false diff |
| 3. Single-Worker HTTP Restart & Cancel Race Safety | **PASS** | Xác minh thực nghiệm qua `:8019` restart + Live Case 5b |
| 4. Multi-Worker Topology Refusal Fail-Closed | **PASS (NOT_SUPPORTED)** | Trả `503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` khi bật `>1` worker |
| 5. Frontend Full Vitest + TypeScript + Vite Build | **PASS** | `192/192` files (`2271/2271`), `tsc -b` 0 errors, `vite build` 8.48s |
| 6. Live Host QA Cases 1–7 + 8 Viewports + REA MCP | **PASS** | `:3001` & `:8000` sống, `0` pageErrors, `0` unexpected 5xx |
| 7. Ownership Boundary Clean | **PASS** | `0` file `OWNERSHIP_BLOCKED` bị sửa hay stage |
| 8. PostgreSQL Live Migration Verification | **BLOCKED / NOT_VERIFIED** | Bị chặn bởi `OWNERSHIP_BLOCKED` `f8a2c41d9e05` & thiếu Postgres trên host |
| 9. Frozen Seal & `CODE_INDEX` Classroom Sync | **PARTIAL** | Chờ re-seal Owner & phiên Classroom dọn 4 dòng `CODE_INDEX.md` |

---

## 16. Final Recommendation

Đề xuất **`MERGE_READINESS = CONDITIONAL`**: bản thân phân hệ **AXO Step Editor** trên cấu hình **đơn worker Uvicorn + Hybrid `/4`** đã hoàn thiện root-cause closure (`IC-1`..`IC-5`), ổn định UI V1, an toàn dữ liệu qua restart và vượt qua toàn bộ live host QA; **việc merge vào `main` chỉ nên thực hiện sau khi:** (1) áp [postgres-step-edit-alembic-handoff.patch](patches/postgres-step-edit-alembic-handoff.patch) và chạy kiểm chứng trên PostgreSQL thật, (2) phiên song song dọn `4` đường dẫn Classroom đã xóa khỏi `docs/CODE_INDEX.md`, và (3) Owner thực hiện re-seal hoặc cập nhật candidate cho các module Step Editor dưới `backend/app/`. Nhánh hiện tại chỉ được commit cục bộ chờ Owner nghiệm thu.

---

## 17. Mandatory Closing Status Lines

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
