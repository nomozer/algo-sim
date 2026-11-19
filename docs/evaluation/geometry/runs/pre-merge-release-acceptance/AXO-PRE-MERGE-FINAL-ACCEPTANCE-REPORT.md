# AXO — BÁO CÁO NGHIỆM THU TÍCH HỢP CUỐI CÙNG TRƯỚC KHI MERGE (`pre-merge-release-acceptance`)

**Ngày lập:** `2026-11-19`  
**Nhánh kiểm định độc lập:** `release/axo-pre-merge-final-acceptance`  
**Worktree kiểm định:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\step-editor-release-candidate`  
**Trạng thái tổng hợp:** **`READY_FOR_OWNER_REVIEW`** (`MERGE_STATUS = NOT_MERGED` · `PUSH_STATUS = NOT_PUSHED` · `MODEL_STATUS = MODEL_NOT_TRAINED` · `DOCKER_CONTAINER_RUNTIME = BLOCKED_ENVIRONMENT` · `OFFICIAL_PG_DUMP_RESTORE = BLOCKED_ENVIRONMENT`)

---

## 1. Executive Summary & Release Manifest

Đợt nghiệm thu này kiểm chứng độc lập toàn bộ kết luận `PASS` trong báo cáo `AXO — DATABASE SAFETY ROOT-CAUSE CLOSURE & MAIN RELEASE PREPARATION REPORT` (`2026-11-19`) trên các cổng **Gate A–G**, đồng thời sửa tận gốc **03 lỗi nguyên nhân gốc thật sự** và đồng bộ `02` nhóm ràng buộc kiểm định phát hiện trong quá trình xác minh trực tiếp.

| Thành phần danh tính | Giá trị xác minh trực tiếp |
| --- | --- |
| Baseline `main` / `origin/main` | `bb046fa22aceff47abe22aa783aa64fc65caee13` (không thay đổi) |
| Nhánh RC gốc được bảo toàn | `release/axo-step-editor-db-safe-rc` @ `aa860d7def12c03c05907e56e5fdca385b1e8dd2` (`feat/axo-geometry-library-verification` giữ nguyên) |
| Protected checkout `algo-sim` | Nhánh `axo-ui-consistency` @ `bb046fa22aceff47abe22aa783aa64fc65caee13` (`0` thay đổi tracked; `?? ocr_reconcile.py` giữ nguyên) |
| Protected `algo-sim/backend/algosim.db` | `413,696` bytes · `SHA-256 = 39d676c7b50a925975828434a00d38e3bac3c5f50e4e2a724a695768c7c83ee3` (bất biến 100%) |
| Commit sửa mã sản phẩm trên nhánh kiểm định | `67af0f8f94d2e9ebc60f7f181f22286c95e04441` (`ISSUE-DB-DRIFT-AND-PARTIAL-MIGRATION-PREFLIGHT` + `ISSUE-SE-STALE-REVISION-METADATA`) |
| Commit đóng băng lại `EVALUATION_CANDIDATE.json` | `36e7c11a0c2b71242345c9c740a05374187040dc` |
| Commit đồng bộ mẫu phê duyệt C21 (`K-1`, `R-1`, `S-2`) | `7259a3eca838f73f38e1bb94401967549844960d` (`owner_decision = PENDING_OWNER_DECISION`, `paid_project_confirmed = false`) |
| Commit cô lập SQLite ephemeral test DB (`conftest.py`) | `dbd33de2eb90264a7cc171fd82a0245f8cd572ec` (`ISSUE-TEST-WINDOWS-PID-DB-REUSE`) |
| Commit portable 46-user/66-row SQLite test fixture | `2a44ac92125a1c2df8017dcfa909d0124365d871` (`tree = 7d1ed11780b9e5d7cd4db29e980bcb75704cee8e`, `121` commit so với `main`) |
| `measured_system` (niêm phong mới nhất) | `109` file · `tree_hash = 702c98f5a0ae65ef5bc275a383736b5288214c64c67b449fcf744fee77fa68eb` · `CACHE_VERSION = 132` · `SEALED = DA_NIEM_PHONG` |

> [!WARNING]
> **Vì sao kết luận là `READY_FOR_OWNER_REVIEW` chứ chưa phải `READY_TO_MERGE` tự động:**
> 1. **Hai cổng môi trường vẫn là `BLOCKED_ENVIRONMENT`** trên máy Windows hiện tại (`Docker` daemon chưa chạy và bộ nhị phân PostgreSQL 16 portable thiếu `pg_dump`/`pg_restore`), chưa thể thay thế bằng kiểm thử tương đương mà không ghi nhận giới hạn môi trường.
> 2. **Quyết định phạm vi thuộc Owner (`GOVERNANCE_SCOPE`):** Nhánh `release/axo-pre-merge-final-acceptance` gộp `121` commit mã/test (`644` file trước commit tài liệu run này) thuộc 9 miền chức năng, bao gồm `LandingView` thay `/` bằng landing page (`39` commit), gỡ route API Classroom/Live Session (`bf1ee2a57`), và nâng cấp Attachment/Workspace cùng Step Editor.

---

## 2. Gate D — Kiểm Toán Phạm Vi Git (`121` Commit / `644` File)

Bằng chứng máy: [results/gate-d-scope-audit.json](results/gate-d-scope-audit.json).

- **Sai lệch thực tế phát hiện so với báo cáo cũ:** Báo cáo trước nêu `115` commit / `607` file (mốc `0fe3873a4`); RC được báo cáo `aa860d7de` thực tế đã là `116` commit / `642` file; cộng thêm 5 commit kiểm định/sửa lỗi gốc/niêm phong (`67af0f8f9`, `36e7c11a0`, `7259a3eca`, `dbd33de2e`, `2a44ac921`), nhánh kiểm định chứa **`121` commit** và **`644` file** thay đổi so với `main` (`M: 93`, `A: 531`, `D: 18`, `R: 2`) trước commit lưu thư mục run này.
- **Phân bổ tệp theo 9 nhóm kỹ thuật (`file_categories`):**
  - `tests_docs_eval`: `441` file
  - `workspace_attachment_ui`: `95` file
  - `geometry_kernel_scene3d_semantic`: `55` file
  - `landing_page_ui`: `17` file
  - `other_config_scripts`: `17` file
  - `auth_classroom_retirement`: `7` file
  - `step_editor_core`: `6` file
  - `database_migration`: `4` file
  - `platform_app_wiring`: `2` file (`backend/Dockerfile`, `backend/app/main.py`)
- **Phân tích tách nhánh vs giữ nguyên khối (`split_vs_unified`):**
  - Việc naive cherry-pick các commit Step Editor gây rủi ro cao vì: [`backend/app/main.py`](../../../../../backend/app/main.py) đan xen wiring Step Editor + gỡ Classroom routes (`bf1ee2a57`) + startup policy; chuỗi Alembic tuyến tính đến `f8a2c41d9e05`; `App.tsx` / `SimulationWorkspace.tsx` / `global.css` / `scene3d-view.tsx` / `step_editor.py` chia sẻ coupling chặt giữa Step Editor, Attachment UI, Landing routing (`/ -> /app`) và kiểm tra đồng bộ toàn cây của [`docs/CODE_INDEX.md`](../../../../CODE_INDEX.md).
  - **Khuyến nghị:** Chỉ merge nguyên khối **nếu Owner chấp thuận rõ ràng** cả Landing Page V1.8, rút route Classroom API (bảng dữ liệu cũ đã được bảo toàn) và cụm Attachment/Workspace; hoặc lập kế hoạch tách nhánh có kiểm soát nếu Owner từ chối một trong các phân hệ trên.

---

## 3. Gate A — Ma Trận An Toàn Migration Database (`A1` & `A2`)

Bằng chứng máy: [results/gate-a-migration-safety-matrix.json](results/gate-a-migration-safety-matrix.json) · [logs/gate-a-forensic.log](logs/gate-a-forensic.log).

### 3.1 Kiểm toán DAG Alembic (`A1`) & Đính chính so với báo cáo trước
- **Chuỗi tuyến tính thực tế (đã kiểm AST cả 8 revision, `0` câu lệnh điều khiển/nhánh ẩn):**
  `None → 72095b7dd318 → f32f9b107b77 → a1c7e4b90d52 → c4e8a91b2f03 → d5f9b82c3a14 → e437149641fa → 9c4d8e2b7a10 → f8a2c41d9e05`
- **Đính chính sự thật:** Revision `HEAD` trên `main` (`bb046fa22`) là **`e437149641fa_analysis_usage_ledger.py`** (`16` bảng, bao gồm `user_account_meta`, `admin_*`, `learning_history_entries`, `analysis_usage_ledger`), không phải `a1c7e4b90d52` như diễn đạt chưa đầy đủ ở một số mô tả cũ. `upgrade()` và `downgrade()` của [`f8a2c41d9e05_remove_classroom_and_live_session_tables.py`](../../../../../backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py) hiện là no-op (`0` lệnh xóa bảng/cột).

### 3.2 Trạng thái 4 database quan sát được trên host

| Database | Revision ghi nhận | Bảng & dữ liệu chính | Phán quyết `migration_preflight.py --startup` |
| --- | --- | --- | --- |
| `algo-sim/backend/algosim.db` (protected) | `None` (chưa stamp) | `16` bảng (khớp `100%` cột/bảng của `e437149641fa`), `46` users, `66` Classroom rows (`12` classrooms, `20` memberships, `8` classroom_sessions, `10` assignments, `16` practice_sessions), `100` auth_sessions | `BLOCKED` (`exit 23`: `UNSTAMPED_EXISTING_DATABASE`), không tự stamp/DDL |
| `axo-geometry-library/backend/algosim.db` | `None` (chưa stamp) | `14` bảng (`74` step_edit_sessions, `280` revisions, `280` feedback, `1116` auth_sessions) | `BLOCKED` (`exit 23`: `UNSTAMPED_EXISTING_DATABASE`) |
| `pg16:algosim_acceptance` | `f8a2c41d9e05` | `15` bảng (`alembic_version` + `14` user tables), trước live browser: `8` sessions, `18` revisions, `18` feedback, `23` auth_sessions | `ALLOW` (`exit 0`: `SAFE_NO_DESTRUCTIVE_OPERATIONS`) |
| `pg16:algosim_host` | `f8a2c41d9e05` | `15` bảng (`7` sessions, `9` revisions, `9` feedback, `12` auth_sessions) | `ALLOW` (`exit 0`: `SAFE_NO_DESTRUCTIVE_OPERATIONS`) |

### 3.3 Kết quả 8 kịch bản Gate A2 (cả SQLite & PostgreSQL 16)
1. **DB mới tinh:** Preflight `SAFE_NO_DESTRUCTIVE_OPERATIONS`, `alembic upgrade head` -> `alembic check` `exit 0` -> `PASS`.
2. **DB ở `e437149641fa` có đủ bảng/dữ liệu Classroom:** Nâng cấp `9c4d8e2b7a10 -> f8a2c41d9e05` giữ `100%` bảng & SHA-256 dữ liệu -> `PASS`.
3. **DB đã có bảng Step Editor (`9c4d8e2b7a10`):** Nâng cấp lên `f8a2c41d9e05` không xóa/ghi đè bản ghi Step Editor -> `PASS`.
4. **Bản sao cô lập của DB `46` users / `66` Classroom rows chưa stamp:** Khởi động tự động **từ chối trước DDL** (`exit 23`, `UNSTAMPED_EXISTING_DATABASE`, SHA-256 tệp không đổi `0` byte); vận hành có kiểm soát (`stamp e437149641fa -> preflight --startup -> upgrade head -> check`) bảo toàn `46/46` users và `66/66` Classroom rows (`100%` digest match) -> `PASS` (kèm cổng vận hành bắt buộc cho DB chưa stamp).
5. **DB đã chạy `f8a2c41d9e05` cũ (không còn bảng Classroom):** Preflight và `alembic check` trên schema hiện hành đều `PASS`.
6. **DB có schema drift** (cột lạ trên `reuse_metrics` hoặc `rogue_pg_col` trên PostgreSQL 16): bị chặn ở preflight `exit 23` (`SCHEMA_DRIFT_DETECTED`) -> `PASS` (nhờ bản sửa `67af0f8f9`).
7. **DB có migration đang dở** (`step_edit_sessions` đã tồn tại trước khi `9c4d8e2b7a10` chạy): bị chặn `exit 23` (`PARTIAL_MIGRATION_PRE_EXISTING_OBJECT`) trước DDL -> `PASS` (nhờ bản sửa `67af0f8f9`).
8. **Application rollback giữ bảng + dữ liệu Step Editor cộng thêm:** Schema mới (`step_edit_*`) cùng tồn tại sạch với bảng legacy -> `PASS`.

---

## 4. Gate B — Backup, Restore (`B1`) & Rollback Rehearsal (`B2`)

Bằng chứng máy: [results/gate-b-backup-restore-rollback.json](results/gate-b-backup-restore-rollback.json) · [logs/gate-b-backup-restore-rollback.log](logs/gate-b-backup-restore-rollback.log).

### 4.1 Backup & Restore (`B1`)
- **Công cụ chính thức PostgreSQL (`pg_dump` / `pg_restore`):** **`BLOCKED_ENVIRONMENT`** (`gate_b1_official_pg_dump_restore_cli_available = false`). Bộ portable PG16 tại `.superpowers/pgsql16/pgsql/bin` chỉ có `initdb.exe`, `pg_ctl.exe`, `postgres.exe`, không có `pg_dump`/`pg_restore`. Phần kiểm chứng bằng binary `pg_dump`/`pg_restore` (custom format `-Fc`, parallel restore, ACL/tablespace flags) **chưa được kiểm chứng** trên máy này.
- **Kiểm chứng thực tế đạt chuẩn trong giao dịch `REPEATABLE READ READ ONLY` trên PG16 (`algosim_acceptance`, `algosim_host`) và SQLite `.backup()`:**
  - Đối chiếu đủ 9 tiêu chí trên bản restore cô lập: số bảng & số dòng (`100%` parity), PK/FK thực thi (tiêm dòng mồ côi vào `step_edit_revisions` / `auth_sessions` bị `IntegrityError` chặn `fk_enforced = true`), Index/UNIQUE thực thi (`unique_enforced = true`), Sequence (`12` sequences, `nextval` vượt `last_value` trước restore `nextval_above_pre_last_value = 10`), Trigger (`0`), Function (`0`), Extension (`plpgsql`), `alembic_version` (`f8a2c41d9e05`), insert/update + boot Uvicorn trực tiếp trên DB phục hồi + `POST /steps/edit` + `GET /state` đều HTTP `200` (`post_restore_step_edit_and_state_roundtrip = PASS`).

### 4.2 Application Rollback Rehearsal (`B2`)
- Thực hiện cô lập hoàn toàn từ archive commit `bb046fa22` và RC:
  1. Nâng cấp DB tạm từ `e437149641fa` (có `3` users + `5` bản ghi Classroom trong các bảng) lên `head` -> khởi chạy RC -> tạo `2` revision Step Editor (`step_edit_sessions = 1`, `step_edit_revisions = 2`).
  2. Tắt RC -> khởi chạy mã nguồn baseline `main` (`bb046fa22`) trên **cùng database đó** (không chạy `alembic downgrade` phá hủy): `/api/health` trả `ok: true, db: "postgresql"`; route Classroom `/api/classes` và `/api/assignments` sống lại và trả `401` (đã kích hoạt guard auth, không `404`), toàn bộ `3` users, `1` classroom, `2` practice sessions, `1` step_edit_sessions và `2` step_edit_revisions còn nguyên.
  3. Tắt baseline -> khởi chạy lại RC -> `GET /api/simulation/sessions/{sid}/state` trả `found = true`, `committed_version = 2`, `M.xyz = ["0", "0", "3/2"]`.
- **Phân biệt rõ:** Rollback ứng dụng là chuyển binary/image về commit `bb046fa22` mà **giữ nguyên schema mở rộng** (an toàn tuyệt đối, không mất dữ liệu mới/cũ); không dùng `alembic downgrade` phá bảng dữ liệu làm cơ chế rollback.

---

## 5. Gate C — Môi Trường Chạy Thực Tế & Docker/Uvicorn

Bằng chứng máy: [results/gate-c-runtime-environment.json](results/gate-c-runtime-environment.json) · [logs/gate-c-runtime-environment.log](logs/gate-c-runtime-environment.log).

- **Docker container verification:** **`BLOCKED_ENVIRONMENT`**. Probe `docker info` thoát mã `1` (`//./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`). Do đó build image đa tầng thực tế, trích xuất layer `COPY`, chạy non-root container và forward OS signal bên trong Linux container **chưa được kiểm chứng trực tiếp** trên host này.
- **Kiểm chứng trực tiếp luồng tương đương `backend/Dockerfile` (`CMD`):**
  - Kiểm tra tĩnh [`backend/Dockerfile`](../../../../../backend/Dockerfile): có `ENV ALGOSIM_STARTUP_MODE=1`, có `python alembic/migration_preflight.py --startup && alembic upgrade head` trước `uvicorn`.
  - Thực thi đúng chuỗi shell `&&` trên PG16 cô lập (`boot1` & `boot2` restart idempotence): preflight `exit 0` -> `alembic upgrade head` `exit 0` -> Uvicorn `/api/health` HTTP `200` (`ok: true, db: "postgresql"`).
  - Kiểm chứng 3 kịch bản từ chối trước khi Uvicorn khởi động: bản sao SQLite chưa stamp -> dừng ở preflight `exit 23` (`UNSTAMPED_EXISTING_DATABASE`, `sha256_preserved = true`, `started_uvicorn = false`); DB có drift -> dừng `exit 23` (`SCHEMA_DRIFT_DETECTED`); pending migration chứa `drop_table` -> dừng `exit 23` (`DESTRUCTIVE_MIGRATION_FORBIDDEN_AT_STARTUP`).

---

## 6. Gate E — Step Editor, Geometry Integrity & Oracle Độc Lập (`E1`–`E3`)

Bằng chứng máy: [results/gate-e-independent-geometry-oracle.json](results/gate-e-independent-geometry-oracle.json) · [results/gate-e-f-browser-phase1.json](results/gate-e-f-browser-phase1.json) · [results/gate-e-f-browser-phase2.json](results/gate-e-f-browser-phase2.json) · [results/gate-f-postgres-live-survival.json](results/gate-f-postgres-live-survival.json).

### 6.1 Oracle hình học độc lập (`E3` — Pure `Fraction` 3D)
Cài đặt bộ kiểm định tọa độ/phẳng/đa giác lồi bằng `fractions.Fraction` thuần túy (zero import từ `app.simulation.geometry`) kiểm tra trực tiếp đầu ra `execute_step_edit`:
- **Đổi tên + cạnh mặt phẳng trung trực `(α) -> (P)`, `AB -> SB` (`chop-mat-cau-ngoai-tiep`):** Vector pháp tuyến `[4, 0, -4] // SB`, đi qua trung điểm `M_SB`, giao tuyến `truc_day` đồng thời nằm trên `(P)` và `(β)`, tâm mặt cầu `I = (2, 2, 2)` thỏa `IA^2 = IB^2 = IC^2 = ID^2 = IS^2 = 12` (`V = 32π√3`) -> `PASS`.
- **Thiết diện hình chóp (`chop-thiet-dien-ba-diem`, cascade `SM/SA = 1/4 -> 3/4 -> 1/2`):** Đỉnh ngũ giác thiết diện đồng phẳng, lồi thuần nhất (`convex_winding = true`), giao điểm `E ∈ SB` (`t = 1/2, 9/10, 3/4`) & `F ∈ SD`, `area_sq_exact` khớp tuyệt đối `425/2`, `9801/50`, `216` -> `PASS`.
- **Thiết diện lăng trụ (`CP = 1/3 CC′`, `area^2 = 244`) & hình lập phương (`AM/AD = 1/3`, `area^2 = 751109/1764`):** `PASS`.
- **Đoạn vuông góc chung (`khoang-cach-hai-duong-cheo-nhau`):** `P ∈ SC (2/3)`, `Q ∈ BD (1/2)`, `PQ ⟂ SC`, `PQ ⟂ BD`, `||PQ||^2 = 8/3` -> `PASS`.
- **6 trường hợp biên suy biến / âm tính fail-closed:** `collinear_AOC -> COLLINEAR_POINTS`, `duplicate_points_AA -> INVALID_OPERAND`, `undefined_SZ -> MISSING_DEPENDENCY`, `ratio_gt_1 -> INVALID_RATIO`, `circular_M -> MISSING_DEPENDENCY`, `unsupported_spiral -> UNSUPPORTED_STEP_SYNTAX` -> `6/6 PASS`.

### 6.2 Live Browser Step Editor E2E & PostgreSQL Consistency (`E1` & `E2`)
Kiểm thử trên stack thật (`:3001` Vite -> `:8000` Uvicorn PG16 `algosim_acceptance`, **không truncate** dữ liệu cũ):
- **Tỷ lệ sống sót PG16:** `100%` khóa chính có sẵn trước khi chạy (`8` sessions, `18` revisions, `18` feedback, `23` auth_sessions, `1` alembic_version) sống sót; thêm `5` session và `17` revision mới qua chạy thực tế.
- **Kiểm chứng triệt để lỗi `(α) -> (P)` (`ISSUE-SE-STALE-REVISION-METADATA`):** Trước khi sửa có `3` step row chứa `(α)`; sau khi chạy `Dựng mặt phẳng trung trực (P) của cạnh SB` trên giao diện -> HTTP `200`, `staleAlphaRowsAfter = 0`, `renamedPRowsAfter = 3`, `I.role = "Giao điểm của «Giao tuyến của (P) và (β)» và (γ)"`, nội dung hàng `I` và drawer `"Xem giải thích"` đều cập nhật `(P)`, không còn `M_AB`/`mid_`/`(α)`.
- **Các trường hợp không hợp lệ & đồng thời (`E2`):** Input khoảng trắng khóa nút `Chạy`; `422` (`MISSING_DEPENDENCY`, `COLLINEAR_POINTS`, `UNSUPPORTED_STEP_SYNTAX`, `DOWNSTREAM_ORTHOGONALITY_BROKEN` với `BQ/BD = 1/5`) giữ nguyên bản nháp trên textarea và không làm hỏng `Scene3D`; `409 STALE_REVISION_CONFLICT` (`expected_committed_version = 0`) và **`409 EDIT_SUPERSEDED`** (request trễ `client_seq = 1` gửi sau khi phiên đã commit `version 10`) đều trả `409` đúng hợp đồng.
- **Cascade, chuyển bài, reload F5 & restart backend:** Chuỗi `SM/SA` (10 lần tuần tự kết thúc ở `1/4`), reload F5, sửa lăng trụ `CP = 1/3 CC′`, đóng/mở lại tab bài 1, cô lập cuộn `.dock-scroll`, **tắt Uvicorn (`task-5362`) và khởi động lại process Uvicorn mới (`task-5384`)**: trình duyệt phục hồi `GET /api/simulation/sessions/.../state` HTTP `200`, `found = true`, `committed_version = 10`, `M = ["0", "0", "9/2"]`, UI giữ nguyên `1/4` (`0` console/page/5xx error).

---

## 7. Gate F — Frontend UX, `Scene3D` Visual Audit & REA MCP

Bằng chứng máy: [results/gate-f-rea-mcp.json](results/gate-f-rea-mcp.json) · [images/](images/).

- **Tương tác editor & bố cục (`1920×1080`):** Hover bút chì mượt `opacity: 0 -> 1`, `hoverHeightDeltaPx = 0`, `Enter`/`Escape` hợp lệ, `canvasShiftDuringEditPx = 0`, `canvasShiftAfterCommitPx = 0`, không scrollbar thừa (`textareaHorizontalOverflow = false`).
- **Kiểm định trực quan `Scene3D` (WebGL SwiftShader + DOM bounding box + thao tác chuột):**
  - `data-webgl-phase = "healthy"`.
  - Camera orbit drag (`mouse down -> move (+85,-40) -> up`) và wheel zoom hoạt động ổn định; trước và sau orbit có `8` nhãn đỉnh + `3` nhãn mặt phẳng hiển thị rõ, `clippedLabels = []`, `vertexLabelOverlaps = []`, độ phủ hình học trên canvas đạt `40.9% × 52.3%` -> `45.1% × 47.3%`.
  - Step scrubber (`Bước trước` / `Bước sau`) cập nhật đồng bộ `#dock-steps-counter` (`Bước 12/17 -> Bước 11/17 -> Bước 12/17`).
- **Ma trận 8 viewport + Touch + Bàn phím ảo (`VKB`):** Toàn bộ 8 kích thước (`1920×1080`, `1440×900`, `1366×768`, `1280×800`, `1024×768`, `768×1024`, `390×844`, `320×568`) đều `overflowX = 0`, canvas hiển thị rõ, nút `Chạy`/`Hủy` không bị che hay cắt mép; Touch `390×844` bật nút bút chì khi chạm hàng bước và VKB `390×460` giữ textarea + nút hành động trong viewport.
- **REA MCP quan sát bị động (`cdp_endpoint :9339`, URL `/simulation/pyramid-circumscribed-sphere`):** `783` DOM nodes, `3` console events (`['debug', 'info']`, `console_error_count = 0`), chụp ảnh viewport `150,127` bytes (`ev_5c030f99dc342884b4e9fe3f49aaef626118d25a2d5fb5eaf4953e95cf3fdd35`). Ảnh trực quan trọng tâm đã được mở đọc kiểm tra trực tiếp ([`final-acceptance-1920-sb-rename-P.png`](images/final-acceptance-1920-sb-rename-P.png), [`final-acceptance-1920-422-rollback.png`](images/final-acceptance-1920-422-rollback.png), [`final-acceptance-1920-cascade-f5.png`](images/final-acceptance-1920-cascade-f5.png), [`final-acceptance-post-restart.png`](images/final-acceptance-post-restart.png), [`final-acceptance-vkb-390x460.png`](images/final-acceptance-vkb-390x460.png), [`final-acceptance-vp-1280x800.png`](images/final-acceptance-vp-1280x800.png), [`final-acceptance-vp-320x568.png`](images/final-acceptance-vp-320x568.png), [`final-acceptance-rea-mcp.png`](images/final-acceptance-rea-mcp.png)).

---

## 8. Gate G — Hiệu Năng, Toàn Bộ Test Suites & Phân Tích `xfail`/`skipped`

Bằng chứng máy: [results/gate-g-performance.json](results/gate-g-performance.json) · [results/gate-g-test-and-xfail-audit.json](results/gate-g-test-and-xfail-audit.json).

### 8.1 Đo lường hiệu năng (`11th Gen Intel Core i5-11400H`, Python `3.12.10`, Windows)
- **Backend internal stage benchmark (`N = 30` lần đo sau 3 warm-up):**

| Kịch bản | Đối tượng tái tính | `parser_ms` (p50) | `planner_ms` (p50) | `kernel+rebuild` (p50) | `scene3d_build_ms` (p50) | `validation_ms` (p50) | **`total_ms` p50 / p95 (min–max)** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `s11_bisector_sb_partial` | `9` | `0.113` | `2.021` | `0.540` | `2.979` | `2.912` | **`10.269 / 11.748`** (`9.801–23.016`) |
| `s11_bisector_sb_full_rebuild` | `26` | `0.107` | `1.993` | `0.776` | `2.947` | `2.937` | **`10.426 / 11.236`** (`10.109–21.389`) |
| `s1_ratio_cascade_partial` | `6` | `0.160` | `1.540` | `3.149` | `2.561` | `4.233` | **`11.808 / 24.884`** (`11.437–25.850`) |

- **Live Fullstack Browser E2E roundtrip (từ click `Chạy` đến commit PG16 + đóng textarea trên `SM/SA` cascade, `N = 10`):** **`p50 = 129.5 ms`**, **`p95 = 194.05 ms`**, `min = 117 ms`, `max = 199 ms`. (Lưu ý: không có số đo baseline trước RC được đo lại trên cùng máy nên không suy diễn tỷ lệ tăng tốc.)

### 8.2 Tổng hợp toàn bộ test suite & kiểm tra xây dựng

| Suite / Audit | Lệnh thực thi | Kết quả chính xác | Exit | Thời gian | Mốc commit |
| --- | --- | --- | --- | --- | --- |
| Candidate Seal Verify | `freeze_evaluation_candidate.py --verify` | `109` file · `702c98f5a0ae65ef…` khớp niêm phong | `0` | `<1s` | `2a44ac921` |
| Backend Postgres (`PG16`) | `pytest -m postgres -v -rsx` | `6 passed`, `14016 deselected`, `1 warning` | `0` | `80.67s` | `2a44ac921` |
| Backend Geometry | `pytest tests/geometry -rsx -q` | `12000 passed`, `6 skipped`, `3 deselected`, `9 xfailed` | `0` | `319.76s` | `dbd33de2e` (`*`) |
| Backend Semantic Program | `pytest tests/semantic_program -rsx -q` | `1192 passed`, `1 skipped` | `0` | `38.08s` | `dbd33de2e` (`*`) |
| Backend Other (`auth/db/api/portability`) | `pytest tests --ignore=... -rsx -q` | `807 passed`, `4 deselected` | `0` | `140.93s` | `2a44ac921` |
| Demo Replay & Crash Audit | `replay_demo_cases.py` & `audit_demo_crash_surface.py` | `5/5` demo, `1/1` reduced; `6/6` boundary, `0` 500s | `0` | `<5s` | `2a44ac921` |
| Independent Geometry Oracle (`E3`) | `gate_e_independent_oracle.py` | `5/5` bài dựng/đổi tên + `6/6` biên âm | `0` | `<3s` | `2a44ac921` |
| Frontend TypeScript Check | `tsc.cmd -b` | `0` errors | `0` | `<5s` | `2a44ac921` |
| Frontend Production Build | `vite build` | built cleanly (`dist/prototypes` absent = `True`) | `0` | `5.02s` | `2a44ac921` |
| Frontend Unit / Integration | `vitest run` | `192` files · `2274 passed` | `0` | `104.78s` | `2a44ac921` |
| Docs Information Architecture | `audit_docs_information_architecture.py` | `0` broken links · `0` secret leaks · balanced | `0` | `<3s` | `pre-commit` |

`*` *Ghi chú minh bạch:* Commit `2a44ac921` ngay sau `dbd33de2e` chỉ thay đổi duy nhất tệp `backend/tests/test_pre_merge_release_acceptance.py` (nằm trong `backend-other`), không chạm mã nguồn hay test thuộc `tests/geometry` hoặc `tests/semantic_program`. Tổng các case qua trên backend (`6 + 12000 + 1192 + 807 = 14005` lượt pass riêng từng phân vùng; `backend-postgres` chạy `6` case đặc hiệu PostgreSQL riêng biệt).

### 8.3 Đánh giá từng mục `xfail` (`9`) và `skipped` (`7` lượt từ `4` nguồn)
Không mục nào che khuất lỗi mới của Step Editor hay migration:
- **`2` xfails** tại `test_generalized_goal_entry.py` + **`1` xfail** tại `test_premise_source_coverage.py` + **`1` xfail** tại `test_source_grounding_reliability.py`: giới hạn có chủ đích của bộ từ chối bảo thủ Source Gate M1 (`REQUEST_NOT_ANSWERED` / `INCONSISTENT_FACTS` / mệnh đề `và` gắn vào goal).
- **`4` xfails** tại `test_hybrid_compiler_benchmark.py` (`B27-facts/pipeline`, `B28-facts/pipeline`): giới hạn NL-to-TypedFact baseline (`'trung điểm của SC'` trong câu hỏi, `'tâm'` vs `'trọng tâm'`).
- **`1` xfail** tại `test_hybrid_simulation_capability_probes.py` (`ISSUE-ARCH-ENGINE-CENTRE-LABEL-EXHAUSTION`): lỗi baseline ở luồng trích xuất full-problem cũ.
- **`6` skipped (`[2] × 3`)** tại `test_unified_solid_scope.py:186` (`A3-DEV-02`, `A3-DEV-09`, `demo1-pyramid-derived-section`): bỏ qua hợp lệ các fixture không có mục tiêu `residual_volume`.
- **`1` skipped** tại `test_scalar_obligations.py:95`: bỏ qua nhánh thiếu `term` vì đã có test riêng kiểm chứng mặc định `identity`.

---

## 9. Các Lỗi Nguyên Nhân Gốc Đã Xử Lý Trong Đợt Nghiệm Thu (`§10`)

1. **`ISSUE-DB-DRIFT-AND-PARTIAL-MIGRATION-PREFLIGHT` (Severity: HIGH — Commit `67af0f8f9`)**
   - **Tái hiện:** Chạy `migration_preflight.py --startup` trên DB đã stamp nhưng thiếu/dư cột (`SCHEMA_DRIFT`), DB mới tạo thủ công `step_edit_sessions` trước khi nâng cấp `9c4d8e2b7a10` (`PARTIAL_MIGRATION`), hoặc DB có bảng `alembic_version` rỗng.
   - **Kỳ vọng vs Thực tế:** Kỳ vọng từ chối trước khi chạy DDL (`exit 23`); thực tế preflight cũ chỉ quét AST `drop_table`/`drop_column` và thiếu `alembic_version` hoàn toàn nên lọt `SAFE_NO_DESTRUCTIVE_OPERATIONS`.
   - **Nguyên nhân gốc & Phạm vi sửa:** [`backend/alembic/migration_preflight.py`](../../../../../backend/alembic/migration_preflight.py) bổ sung `scan_revision_creates`, phát hiện `EMPTY_ALEMBIC_VERSION_TABLE`, `PARTIAL_MIGRATION_PRE_EXISTING_OBJECT` và `SCHEMA_DRIFT_DETECTED` (tính đến ngoại lệ có kiểm soát cho `RETAINED_LEGACY_CLASSROOM_TABLES` khi nâng cấp qua `f8a2c41d9e05`).
   - **Regression test & Kết quả:** `test_gate_a2_schema_drift_blocked_before_ddl_after_upgrade`, `test_gate_a2_partial_migration_colliding_object_blocked_before_ddl`, `test_gate_a2_postgres16_drift_and_partial_migration_guards` (`PASS` trên cả SQLite & PG16).

2. **`ISSUE-SE-STALE-REVISION-METADATA` (Severity: MEDIUM-HIGH — Commit `67af0f8f9`)**
   - **Tái hiện:** Sửa bước dựng `mp_tt_AB` trên bài mặt cầu ngoại tiếp thành `"Dựng mặt phẳng trung trực (P) của cạnh SB"` (vừa đổi cạnh `AB -> SB`, vừa đổi tên `(α) -> (P)`).
   - **Kỳ vọng vs Thực tế:** Toàn bộ `role`, `computational_depends`, `visible_prerequisites`, `dependency_edges`, event `explanation`/`details` của đối tượng phụ thuộc (`truc_day`, tâm `I`) phải phản ánh `(P)` và không rò rỉ `(α)` hay `M_AB`; thực tế bản cũ giữ chuỗi `(α)` trong `I["role"]`, mảng phụ thuộc `computational_depends`/`visible_prerequisites`/`dependency_edges`, và `new_events`.
   - **Nguyên nhân gốc & Phạm vi sửa:** [`backend/app/simulation/geometry_functions/step_editor.py`](../../../../../backend/app/simulation/geometry_functions/step_editor.py) đồng bộ lại mảng dependency, bổ sung `"role"` vào vòng lặp `notation_renames` và cập nhật `visible_prerequisites`/`display_label`/`explanation`/`details` trong `new_events`. Đóng băng lại candidate tại `36e7c11a0` và đồng bộ 3 template C21 (`7259a3eca`).
   - **Regression test & Kết quả:** `test_step_editor_rename_and_dependency_clear_stale_revision_metadata` + Live Playwright (`staleAlphaRowsAfter = 0`, `renamedPRowsAfter = 3`).

3. **`ISSUE-TEST-WINDOWS-PID-DB-REUSE` + Portable 46-user SQLite Test Fixture (`7259a3eca`, `dbd33de2e`, `2a44ac921`)**
   - **Tái hiện:** Trong lượt chạy `pytest tests/geometry` full (`task-5212`), `test_default_analyze_route_call_graph_and_retired_legacy_absence` đôi lúc trả hit cache giả (`0 == 1`); đồng thời `test_test_portability.py` chặn đường dẫn Windows tuyệt đối cứng trong tệp test mới.
   - **Nguyên nhân gốc & Phạm vi sửa:** [`backend/conftest.py`](../../../../../backend/conftest.py) trước đây đặt tên DB tạm chỉ theo `os.getpid()` và gọi `unlink()` khi `engine` còn giữ handle Windows -> PID tái sử dụng mở nhầm DB cũ; đã thêm `_SESSION_NONCE` và `engine.dispose()` trước `unlink`. Đồng thời thay `ROOT_CHECKOUT_DB` trong `backend/tests/test_pre_merge_release_acceptance.py` bằng fixture SQLite tự dựng 46 users / 66 Classroom rows trong `tmp_path` (bên cạnh kiểm toán trực tiếp tệp `algo-sim/backend/algosim.db` trong Gate A/B).

---

## 10. Phân Tách 5 Nhóm Nhận Thức (Epistemological Separation) & Giới Hạn

1. **Dữ kiện đã kiểm chứng trực tiếp trong phiên này:**
   - Trạng thái 17 worktree, hash `39d676c7...` của `algo-sim/backend/algosim.db`, chuỗi 8 revision Alembic, toàn bộ kết quả Gate A1/A2, Gate B1 (`REPEATABLE READ READ ONLY` + 9 tiêu chí), Gate B2 rollback (`RC -> bb046fa22 -> RC`), Gate C tương đương host, Gate D (`121` commit), Gate E1/E2/E3, Gate F (`Playwright` + `REA MCP` + nhìn ảnh trực quan), Gate G (`tsc`/`vite build`/`vitest`/backend suites/oracle/benchmark).
2. **Kết quả kế thừa từ báo cáo trước (chưa chạy lại trong phiên này):**
   - Các thông số từ `hybrid-master-backend-replacement` và đánh giá live Gemini trả phí lịch sử (do các mẫu `K-1`, `R-1`, `S-2` giữ nguyên `PENDING_OWNER_DECISION` / `paid_project_confirmed: false`); `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`; `PRODUCTION_DEPLOYMENT_VERIFIED = NO`.
3. **Suy luận kỹ thuật (không phải thực nghiệm trực tiếp trong container):**
   - Hành vi bên trong Docker image (`COPY alembic`, `ENV ALGOSIM_STARTUP_MODE=1`, `uvicorn`) được suy luận từ kiểm tra tĩnh `Dockerfile` kết hợp chạy thực tế lệnh shell tương đương trên PG16 host.
4. **Rủi ro & Hạng mục chưa được đóng (`BLOCKED_ENVIRONMENT` / Ngoài phạm vi phiên):**
   - `DOCKER_CONTAINER_RUNTIME = BLOCKED_ENVIRONMENT` (Docker daemon tắt trên máy host).
   - `OFFICIAL_PG_DUMP_PG_RESTORE = BLOCKED_ENVIRONMENT` (thiếu `pg_dump`/`pg_restore` CLI trong bản portable PG16).
   - `MODEL_STATUS = MODEL_NOT_TRAINED` (chủ ý dự án không huấn luyện/nạp Model 2).
   - Database cũ trên SQLite (`algo-sim/backend/algosim.db`, `axo-geometry-library/backend/algosim.db`) chưa có `alembic_version`: sẽ **bị từ chối khởi động tự động (`exit 23`)** cho đến khi người vận hành sao lưu + đối chiếu + `stamp` đúng revision (`e437149641fa` với root DB).
5. **Quyết định bắt buộc cần Owner phê duyệt:**
   - Có chấp thuận gộp **toàn bộ 9 miền chức năng** trên nhánh (bao gồm Landing Page V1.8 tại `/`, việc rút route API Classroom/Live Session trong giữ nguyên bảng legacy DB, và cụm Attachment/Workspace) vào `main` hay yêu cầu tách phạm vi phát hành?
   - Ký xác nhận (hoặc chạy bổ sung ở CI/staging có Linux Docker + `pg_dump`/`pg_restore`) đối với 2 mục `BLOCKED_ENVIRONMENT` trước cutover production.

---

## 11. Trả Lời Rõ Ràng 07 Câu Hỏi Cuối Đợt Nghiệm Thu

1. **Có an toàn để merge RC vào `main` không?**  
   **Về kỹ thuật Step Editor, Geometry Kernel, Scene3D, Frontend và Migration an toàn dữ liệu: CÓ ĐIỀU KIỆN — nhưng CHƯA ĐỦ ĐIỀU KIỆN tự động merge ngay (`READY_FOR_OWNER_REVIEW`).** Lý do: (i) Nhánh RC mang thêm `121` commit thuộc 9 miền (gồm Landing `/` -> `/app` và rút API Classroom), cần Owner duyệt phạm vi; (ii) Hai kiểm chứng môi trường (`Docker container build/run` và `pg_dump`/`pg_restore` chính thức) đang là `BLOCKED_ENVIRONMENT` trên máy Windows hiện tại và phải chạy lại trên CI/staging mục tiêu trước production cutover.

2. **Có cần giới hạn phạm vi phát hành không?**  
   **Cần Owner quyết định rõ.** Về mặt kỹ thuật, việc cherry-pick đơn lẻ Step Editor rủi ro cao vì coupling qua `main.py`, Alembic DAG, `SimulationWorkspace.tsx`, `scene3d-view.tsx` và `CODE_INDEX.md`. Nếu Owner đồng ý phát hành đồng thời Landing Page V1.8 + Workspace/Attachment + rút API Classroom (không mất bảng DB) + Step Editor -> nên merge nguyên khối. Nếu Owner **không** muốn thay `/` hoặc **không** muốn rút API Classroom khỏi production -> cần lập chiến dịch tách nhánh riêng có kiểm thử hồi quy độc lập, không naive cherry-pick.

3. **Database cũ có đường nâng cấp an toàn chưa?**  
   **ĐÃ CÓ và đã kiểm chứng trực tiếp trên mọi trạng thái.** DB đang có `alembic_version` hợp lệ (`e437149641fa` hoặc `9c4d8e2b7a10`) tự nâng cấp `head` không mất bảng Classroom hay dữ liệu. DB legacy chưa có `alembic_version` (như `algo-sim/backend/algosim.db` với `46` users / `66` Classroom rows) được bảo vệ fail-closed `UNSTAMPED_EXISTING_DATABASE` (`exit 23`, 0 byte thay đổi) và có đường nâng cấp vận hành kiểm soát (`backup -> đối chiếu schema -> alembic stamp e437149641fa -> alembic upgrade head -> alembic check`), chứng minh giữ nguyên `100%` `46` users và `66` Classroom rows. DB bị schema drift hoặc migration dở đều bị chặn trước DDL (`67af0f8f9`).

4. **Có thể rollback mà không mất dữ liệu không?**  
   **CÓ, bằng application rollback (không dùng destructive DB downgrade).** Gate B2 đã diễn tập thực tế trên PG16: tạo `2` revision Step Editor trên RC -> chuyển code về baseline `main` (`bb046fa22`) dùng cùng DB -> `bb046fa22` khởi động `200 OK`, API `/api/classes` & `/api/assignments` trả `401` (sống lại), giữ nguyên `100%` dữ liệu legacy lẫn `step_edit_*` -> bật lại RC đọc lại `committed_version = 2` (`M = ["0", "0", "3/2"]`) bình thường.

5. **Docker startup đã được kiểm chứng thực tế chưa?**  
   **CHƯA (`BLOCKED_ENVIRONMENT` trên host này).** `docker info` trả lỗi `exit 1` vì Docker Desktop Linux engine không chạy. Đã kiểm chứng trực tiếp quy trình shell tương đương 1:1 với `CMD` trong `backend/Dockerfile` (`ALGOSIM_STARTUP_MODE=1 migration_preflight.py --startup -> alembic upgrade head -> uvicorn`) trên PostgreSQL 16 (cả đường thành công, restart và 3 đường từ chối fail-closed).

6. **Step Editor và Scene3D đã đồng bộ chính xác chưa?**  
   **ĐÃ ĐỒNG BỘ CHÍNH XÁC sau khi sửa `ISSUE-SE-STALE-REVISION-METADATA` (`67af0f8f9`).** Đã chứng minh đồng thời qua Oracle hình học `Fraction` độc lập, Playwright E2E trên PG16 thật (đổi `AB -> SB` và đổi tên `(α) -> (P)` với `0` rò rỉ `(α)` ở bảng bước, điểm `I`, drawer giải thích và nhãn 3D; cascade `SM/SA`, `422` bảo toàn draft, `409` stale & superseded, F5, restart Uvicorn), `8` viewport + VKB và REA MCP.

7. **Những công việc nào còn bắt buộc trước khi triển khai production?**  
   1. **Owner phê duyệt phạm vi release 9 miền** (Landing `/`, rút Classroom HTTP API, Attachment/Workspace, Step Editor) và ra quyết định merge `release/axo-pre-merge-final-acceptance` -> `main`.  
   2. **Chạy Gate B1 & Gate C trên Linux staging/CI thật** nơi có Docker daemon + bộ CLI PostgreSQL chính thức (`pg_dump`/`pg_restore`) + kiểm tra lại startup container & health check.  
   3. **Thực hiện checklist nâng cấp DB có kiểm soát trước cutover:** backup đầy đủ DB mục tiêu -> kiểm tra `alembic_version` (nếu là DB cũ chưa stamp giống root `algosim.db`, thực hiện `stamp e437149641fa` sau khi đối chiếu schema parity) -> `alembic upgrade head` -> `alembic check` -> giữ cấu hình single-worker Uvicorn cho PostgreSQL `FOR UPDATE NOWAIT`.  
   4. *(Ngoài phạm vi Step Editor V1 hiện hành nếu muốn bật AI gợi ý bước dựng về sau):* giữ nguyên trạng thái `MODEL_NOT_TRAINED`, chưa kích hoạt đường model tự động và tuân thủ cổng phê duyệt tài chính nếu chạy live pilot `K-1`/`R-1`/`S-2`.
