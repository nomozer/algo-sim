# AXO — FINAL RELEASE READINESS ACCEPTANCE REPORT

- **Campaign:** AXO — Final Release Readiness: Root-Cause Verification, Docker/PostgreSQL Closure & Safe Merge Preparation
- **Date:** `2026-11-19`
- **Overall Release Verdict:** **`TECHNICALLY_READY_PENDING_OWNER_APPROVAL`**
- **Release Branch (`step-editor-release-candidate`):** `release/axo-final-release-readiness`
- **Root-Cause Fix Commit:** `ccedfabdb3deb67563a6bf4bc42d00b793c844c9` (`ccedfabdb`)
- **Final Verified Candidate Commit (`HEAD` & Seal Sync):** `a0f4a516630bb582d982463cd1160f7668154221` (`a0f4a5166`)
- **Merge / Push / Production Deploy Status:** `NOT_MERGED` · `NOT_PUSHED` · `PRODUCTION_DEPLOYMENT_VERIFIED = NO`

---

## 1. Executive Verdict

Release candidate **`a0f4a5166`** trên nhánh cô lập `release/axo-final-release-readiness` đạt trạng thái **`TECHNICALLY_READY_PENDING_OWNER_APPROVAL`**:

- **Hai cổng từng `BLOCKED_ENVIRONMENT` ở báo cáo `2026-11-19` trước (`e02266634`) nay đã ĐÓNG THÀNH CÔNG với `PASS`:**
  1. **Gate A — Real Docker Linux Container Runtime (`PASS`):** Docker Engine `29.9.2` (`linux/amd64`, `desktop-linux`) build image thực tế `axo-release-readiness-backend:rc` (`790,333,245` B) từ `a0f4a5166`, boot với `CMD` mặc định (`migration_preflight.py --startup && alembic upgrade head && uvicorn`), xử lý HTTP `POST /api/simulation/steps/edit`, sống sót qua `docker restart`, và từ chối fail-closed với exit code `23` trước mọi DDL/API cho 4 kịch bản DB nguy hiểm.
  2. **Gate B — Official PostgreSQL 16 Backup/Restore & Rollback (`PASS`):** Dùng bộ công cụ chính thức `postgres` / `pg_dump` / `pg_restore` / `psql` phiên bản `16.15`, tạo dump `-Fc` (`92,078` B, `192` TOC entries), restore sạch vào `staging_restored` với 100% đối chiếu `20` bảng (row counts, per-row SHA-256, constraints, indexes, sequences), xác nhận FK & UNIQUE từ chối dữ liệu vi phạm, boot container trực tiếp trên DB sau restore để ghi revision `v=3` và restart thành công, đồng thời chứng minh `B3` application rollback về `main` (`bb046fa22`) và parity 16 bảng cho DB SQLite legacy trước khi stamp.
- **Một root-cause bug mới đã được phát hiện và sửa triệt để trước khi niêm phong cuối:**
  - `ISSUE-SE-ABSORBED-HELPER-AND-HOISTED-EVENT-SYNC` (`step_editor.py`, commit `ccedfabdb`): Khi người dùng sửa `mp_tt_AB` thành `"Dựng mặt phẳng trung trực (P) của cạnh SB"`, đối tượng helper bị gộp `M_AB` đã cập nhật `label`/`depends` sang `S, B`, nhưng sự kiện dựng (`events[].learner_text`) của `M_AB` và các sự kiện phụ thuộc được nâng (hoisted) vẫn giữ nguyên chuỗi cũ `"Dựng trung điểm của A và B."`. Lỗi đã được xử lý tận gốc qua helper dùng chung `_sync_rebuilt_event` và thêm test hồi quy mới trong [`test_pre_merge_release_acceptance.py`](../../../../../backend/tests/test_pre_merge_release_acceptance.py).
- **Lý do chưa kết luận `APPROVED_FOR_MERGE` (dừng tại Owner Review Gate):**
  - **Gate C1–C2 (`BLOCKED_OWNERSHIP`)**: Mặc dù mô phỏng merge kỹ thuật với `main` (`bb046fa22`) có **`0` conflict cơ học**, nhánh chứa **9 miền thay đổi** (`124` commits, `688` files), gồm 2 thay đổi hành vi/API lớn cần Owner duyệt tường minh: chuyển route mặc định `/` sang LandingView (`/app` làm workspace) và gỡ HTTP router Classroom/Live Session (trong khi giữ nguyên bảng DB legacy).

### Bảng Trạng Thái Theo Cổng (§9 Release Decision Matrix)

| Cổng | Phạm vi | Trạng thái | Tóm tắt bằng chứng |
| :--- | :--- | :--- | :--- |
| **Gate A** | Real Linux Docker build, boot/restart & 4 fail-closed exit-`23` containers | **`PASS`** | [gate-a-docker-runtime.json](results/gate-a-docker-runtime.json) · [log](logs/gate-a-docker-runtime.log) |
| **Gate B** | Official PG `16.15` `pg_dump`/`pg_restore`/`psql`, legacy parity & B3 rollback | **`PASS`** | [gate-b-official-pg-backup-restore.json](results/gate-b-official-pg-backup-restore.json) · [log](logs/gate-b-official-pg-backup-restore.log) |
| **Gate C (C1–C2)** | Release scope audit 9 miền & Owner scope decisions (`/`, Classroom API retirement) | **`BLOCKED_OWNERSHIP`** | [gate-c-scope-and-merge-simulation.json](results/gate-c-scope-and-merge-simulation.json) |
| **Gate C (C3)** | Isolated merge simulation (`merge-tree`, `ff-only`, `no-ff --no-commit`) vs `main` | **`PASS`** | [gate-c-scope-and-merge-simulation.json](results/gate-c-scope-and-merge-simulation.json) |
| **Gate D (D1–D4)** | Step Editor valid/invalid/409, persistence F5/tab/restart & independent oracle | **`PASS`** | [gate-d4-independent-oracle.json](results/gate-d4-independent-oracle.json) · [phase1](results/gate-e-browser-phase1.json) |
| **Gate E** | Live host `:8000`/`:3001`, 6 responsive viewports + touch/VKB, camera/draft, REA MCP | **`PASS`** | [phase1](results/gate-e-browser-phase1.json) · [phase2](results/gate-e-browser-phase2.json) · [rea](results/gate-e-rea-mcp.json) · [pg](results/gate-e-postgres-survival.json) |
| **Gate F1** | Seal verify, drift check, full backend/PG/frontend test suites + skip/xfail audit | **`PASS`** | [gate-f1-test-integrity.json](results/gate-f1-test-integrity.json) |
| **Gate F2** | 6-metric backend + live PG commit + frontend browser benchmark vs `2026-11-19` baseline | **`PASS`** | [gate-f2-performance-comparison.json](results/gate-f2-performance-comparison.json) |
| **Hybrid Gate** | Docs IA audit + secret/link scan + zero protected DB mutation | **`PASS`** | [docs-ia-audit.log](logs/docs-ia-audit.log) |

- **MODEL STATUS:** `MODEL_NOT_TRAINED` (`GET /api/simulation/feedback/status` trả `model_trained: false`).
- **INDEPENDENT H-1 VALIDATION:** `NOT_MEASURED` (không chạy API AI trả phí; các test K-1/R-1/S-2 giữ chế độ offline contract).

---

## 2. Repository Identity & Candidate SHA

| Thực thể / Worktree | Nhánh | Commit SHA | Trạng thái bảo toàn |
| :--- | :--- | :--- | :--- |
| Protected checkout `D:\Documents\projects\algo-sim` | `axo-ui-consistency` | `bb046fa22aceff47abe22aa783aa64fc65caee13` | Nguyên vẹn (`?? ocr_reconcile.py` của user giữ nguyên; `backend\algosim.db` `413,696` B SHA-256 `39D676C7B50A925975828434A00D38E3BAC3C5F50E4E2A724A695768C7C83EE3`) |
| `main` / `origin/main` | `main` | `bb046fa22aceff47abe22aa783aa64fc65caee13` | Không merge, không push, không sửa byte |
| Preserved geometry worktree `D:\Documents\projects\axo-geometry-library` | `feat/axo-geometry-library-verification` | `aa860d7def12c03c05907e56e5fdca385b1e8dd2` | Nguyên vẹn |
| Baseline acceptance branch | `release/axo-pre-merge-final-acceptance` | `e022666343189e19b9c0dfd139e45a2b50dd3d6d` | Bảo toàn nguyên vẹn làm mốc đối chiếu |
| Release candidate worktree `.superpowers\worktrees\step-editor-release-candidate` | `release/axo-final-release-readiness` | `a0f4a516630bb582d982463cd1160f7668154221` (code+seal); `ccedfabdb3deb67563a6bf4bc42d00b793c844c9` (product fix) | Tree `2510c29e57db9737c0cb111b1c8e7302b747a50b` |
| Measured System Seal (`EVALUATION_CANDIDATE.json`) | — | `ea6626e7a205e33a14a6229fa9b4586b27ebda1619bfce516db0437b8e79ec90` | `109` file sản phẩm; `CACHE_VERSION = 132`; `--verify` thoát `0` |

---

## 3. Baseline Comparison

So sánh trực tiếp với báo cáo `AXO-PRE-MERGE-FINAL-ACCEPTANCE-REPORT.md` (branch `release/axo-pre-merge-final-acceptance`, report `e02266634`, verified code `2a44ac921`, measured tree hash cũ `702c98f5a0ae65ef5bc275a383736b5288214c64c67b449fcf744fee77fa68eb`):

1. **Đóng hai cổng môi trường bị chặn trước đây:**
   - Trước (`2a44ac921`): Docker Engine đang dừng và thiếu client `pg_dump`/`pg_restore`/`psql` khiến Gate C Docker và Gate B1 `pg_dump`/`pg_restore` phải xếp loại `BLOCKED_ENVIRONMENT`.
   - Nay (`a0f4a5166`): Docker Engine `29.9.2` (`linux/amd64`) và image `postgres:16-alpine` (`postgres 16.15`, `pg_dump 16.15`, `pg_restore 16.15`, `psql 16.15`) hoạt động thật, đóng toàn bộ Gate A & Gate B bằng chạy thật.
2. **Thay đổi mã nguồn & niêm phong giữa `2a44ac921` và `a0f4a5166`:**
   - Sửa lỗi gốc `ISSUE-SE-ABSORBED-HELPER-AND-HOISTED-EVENT-SYNC` ở `backend/app/simulation/geometry_functions/step_editor.py` (`ccedfabdb`, `+48/-36` dòng ở lớp `_sync_rebuilt_event`) + thêm regression test.
   - Đóng băng lại `EVALUATION_CANDIDATE.json` (hash hệ đo đổi từ `702c98f5...` sang `ea6626e7...`, cùng `109` file, `CACHE_VERSION = 132`) và đồng bộ C21 templates (`k1`, `r1`, `s2`) tại commit `a0f4a5166`.
3. **Toàn bộ test/oracle/browser/perf đều chạy mới 100% trên `a0f4a5166`**, không kế thừa số PASS từ `2a44ac921`.

---

## 4. Docker Runtime Evidence (Gate A)

- **Môi trường:** Docker Client/Server `29.9.2`, OS/Arch `linux/amd64`, Context `desktop-linux`. Container sẵn có trên máy (`algo-sim-backend-1`, `algo-sim-db-1`, `Exited (0) 2 days ago`) không bị chạm vào.
- **Build & Image Metadata:**
  - Image tag tạm phục vụ kiểm định: `axo-release-readiness-backend:rc` (`sha256:ceed2ce3e65e05b5d5e10fc22a289a41525f9da8ff3a4c5a76f28125f3c684b8`, kích thước `790,333,245` B, `linux/amd64`).
  - Nhãn build khớp chính xác `HEAD = a0f4a516630bb582d982463cd1160f7668154221`, `requirements_sha256 = 8653237b274670619374f98f4a2138e6e5776b3be4cae7301d0211b1f630c164`, `image_inputs_sha256 = 3bc1b8b3a4c484183245c114571af694cfcf2f2b4b380e32139938204919ee96`.
  - Entrypoint/CMD dùng nguyên bản từ `backend/Dockerfile`: `python alembic/migration_preflight.py --startup && alembic upgrade head && ... exec uvicorn app.main:app --host 0.0.0.0 --port 8000` (truyền thêm `--health-cmd` theo đúng `docker-compose.yml` khi gọi `docker run`).
- **Boot 1 & Boot 2 (`docker restart`):**
  - PostgreSQL container cô lập `axo-rr-pg16` (`postgres 16.15`) trên network riêng `axo-rr-net`.
  - **Boot 1:** Logs ghi nhận `MIGRATION_PREFLIGHT=PASS`, Alembic chạy đủ chuỗi migration từ rỗng tới `f8a2c41d9e05`, container đạt trạng thái `running|healthy|0`. `GET /api/health` trả `200` (`db="postgresql"`, `runtime.git_sha == a0f4a5166...`), `GET /api/simulation/feedback/status` trả `200` (`MODEL_NOT_TRAINED`), `POST /api/simulation/steps/edit` sửa `mp_tt_AB -> (P) cạnh SB` trả `200`, `M_AB.learner_text == "Dựng trung điểm của S và B."`, `GET /state` trả `committed_version = 1`.
  - **Boot 2 (`docker restart axo-rr-backend`):** Container khởi động lại đạt `running|healthy|0`, preflight & alembic idempotent, `GET /state` vẫn trả `committed_version = 1`.
- **Ma trận khởi động Fail-Closed (`4/4` container bị từ chối với exit code `23`, Uvicorn không bao giờ khởi chạy):**
  1. `algosim_rr_unstamped` (DB populated thiếu `alembic_version`) → exit `23` (`UNSTAMPED_EXISTING_DATABASE`), 1 dòng `users` nguyên vẹn.
  2. `algosim_rr_drift` (thêm cột lạ `rogue_docker_col`) → exit `23` (`SCHEMA_DRIFT_DETECTED`).
  3. `algosim_rr_partial` (bảng `step_edit_sessions` tồn tại sẵn khi DB ở rev `e437149641fa`) → exit `23` (`PARTIAL_MIGRATION_PRE_EXISTING_OBJECT`).
  4. `algosim_rr_badmig` (mount read-only migration chứa `op.drop_table("users")`) → exit `23` (`DESTRUCTIVE_MIGRATION_FORBIDDEN_AT_STARTUP`), 1 dòng `users` nguyên vẹn.
- **Trạng thái Gate A:** **`PASS`** ([gate-a-docker-runtime.json](results/gate-a-docker-runtime.json)). Toàn bộ container và network tạm `axo-rr-*` đã được gỡ sạch sau khi chạy.

---

## 5. Official PostgreSQL 16 Backup/Restore Evidence (Gate B)

- **Công cụ chính thức sử dụng:** `postgres (PostgreSQL) 16.15`, `pg_dump (PostgreSQL) 16.15`, `pg_restore (PostgreSQL) 16.15`, `psql (PostgreSQL) 16.15` (trong container cô lập `postgres:16-alpine`).
- **Quy trình 10 bước trên `staging_source` → `staging_restored`:**
  1. Dựng `staging_source` tại `e437149641fa`, nạp đồ thị Classroom populated (`3 users`, `2 practice_sessions`, classrooms, assignments, submissions), nâng cấp lên `head` (`f8a2c41d9e05`), rồi chạy 2 revision Step Editor thật (`v=1`, `v=2`) qua HTTP container `BE_SRC_CONT`. Tổng cộng `20` bảng.
  2. Chạy `pg_dump -d staging_source -Fc --no-owner --no-privileges` → tạo file backup `staging_source.pgdump` (`92,078` bytes, SHA-256 `b7af1f05009a776ea0fade168fa01d0ee49d9872cce69e2d54557f82d8b33ffa`).
  3. Đọc mục lục bằng `pg_restore --list` → `192` TOC entries hợp lệ.
  4. Tạo DB mới `staging_restored` bằng `psql` (`ON_ERROR_STOP=1`) và phục hồi bằng `pg_restore --clean --if-exists --no-owner --no-privileges`.
  5. **Đối chiếu độc lập toàn bộ danh mục PostgreSQL (`_inspect_pg_catalog`):** Khớp 100% giữa `staging_source` và `staging_restored` trên mọi phương diện: `20` bảng, `row_counts` từng bảng, per-row sorted SHA-256 digest từng bảng (`table_hashes`), toàn bộ `constraints`, `indexes`, `sequences`, và `alembic_version == ["f8a2c41d9e05"]`.
  6. **Kiểm tra cưỡng bức ràng buộc & sequence trên `staging_restored`:**
     - `INSERT INTO classrooms (teacher_id=999999, ...)` → bị PostgreSQL từ chối (`IntegrityError`, FK enforced).
     - `INSERT` trùng `(owner_scope, session_id)` vào `step_edit_sessions` → bị từ chối (`IntegrityError`, `uq_step_edit_session_owner_sid` enforced).
     - `SELECT nextval('step_edit_revisions_id_seq')` → trả về `3` (`> 2`), xác nhận sequence phục hồi đúng offset.
  7. **Khởi động backend container `BE_REST_CONT` trực tiếp trên `staging_restored`:** Tạo thêm revision `v=3` (`SM/SA = 1/2` → `M=['0', '0', '3']`), chạy `docker restart BE_REST_CONT`, đọc lại `GET /state` vẫn trả `found=true`, `committed_version=3`, `M=['0', '0', '3']`.
- **Host PostgreSQL 16 (`127.0.0.1:55432`, `algosim_acceptance`) & giới hạn ghi nhận trung thực:**
  - Host PG16 được khởi chạy bind `127.0.0.1:55432` (loopback-only) và thư mục `.superpowers\pgsql16\pgsql\bin` trên host chỉ có `postgres.exe` & `pg_ctl.exe` (không có `pg_dump.exe`). Vì vậy bước đối chiếu trên `algosim_acceptance` thực hiện inspect catalog chỉ-đọc (`15` bảng, `alembic=['f8a2c41d9e05']`, `13` sessions, `35` revisions trước live E2E) và không chỉnh sửa cấu hình listen của host PG16; toàn bộ quy trình `pg_dump`/`pg_restore`/`psql` chính thức đã được chứng minh trọn vẹn trên `staging_source -> staging_restored` với đầy đủ schema `f8a2c41d9e05` + Classroom + Step Editor.
- **Trạng thái Gate B:** **`PASS`** ([gate-b-official-pg-backup-restore.json](results/gate-b-official-pg-backup-restore.json)).

---

## 6. Migration Safety & Application Rollback Evidence

1. **Bảo toàn Database Legacy (46 users / 66 classrooms SQLite `algo-sim\backend\algosim.db`):**
   - Trong môi trường cô lập sao lưu read-only, schema `iso_root.db` (16 bảng) khớp 100% tên bảng và toàn bộ tên cột với revision `e437149641fa`.
   - Khi chưa stamp `alembic_version`, `migration_preflight.py --startup` từ chối với exit code `23` (`UNSTAMPED_EXISTING_DATABASE`), giữ nguyên SHA-256 của file.
   - Chỉ sau khi chứng minh tương thích schema, thực hiện `alembic stamp e437149641fa` → `migration_preflight.py --startup` (`PASS`) → `alembic upgrade head` (`f8a2c41d9e05`) → `alembic check` (`No new upgrade operations`), giữ nguyên 100% SHA-256 dữ liệu `users` và các bảng Classroom legacy.
   - File gốc `D:\Documents\projects\algo-sim\backend\algosim.db` giữ nguyên không đổi (`413,696` B, SHA-256 `39D676C7B50A925975828434A00D38E3BAC3C5F50E4E2A724A695768C7C83EE3`).
2. **Diễn tập Application Rollback `B3` về `main` (`bb046fa22`) trên PG16 (`b3_rollback`):**
   - Khởi động Uvicorn từ mã nguồn RC `a0f4a5166` tạo Step Editor `v=1` trên DB chứa sẵn 3 `users` + 2 `practice_sessions` → dừng app RC.
   - Trích archive code `main` (`bb046fa22aceff47abe22aa783aa64fc65caee13`) vào thư mục tạm và boot Uvicorn từ **`main` trên chính DB `b3_rollback` đó** (không chạy `alembic downgrade`): `/api/health` trả `200`, các route `/api/classes` và `/api/assignments` hoạt động trở lại (`401` khi chưa đăng nhập thay vì `404`), chứng minh toàn bộ dữ liệu legacy còn nguyên.
   - Quay lại app RC `a0f4a5166`: `GET /state` đọc lại đúng `v=1`, và `users = 3`, `practice_sessions = 2` giữ nguyên.
3. **Phân biệt 3 thao tác không tương đương:**
   - *Application rollback*: Hạ binary/code ứng dụng về `bb046fa22` trên DB giữ nguyên bảng additive (an toàn, zero data loss).
   - *Database restore*: Khôi phục toàn bộ DB về thời điểm bản dump `pg_dump`/`pg_restore`.
   - *Database schema rollback*: Chạy `alembic downgrade` (có nguy cơ mất dữ liệu nếu drop bảng đang có bản ghi — không dùng làm phương án rollback sự cố).

---

## 7. Release Scope Audit (9 Miền Chức Năng — Gate C1–C2)

Tổng phạm vi diff từ `main` (`bb046fa22`) tới `a0f4a5166`: **`124` commits, `688` files** (`93` modified, `575` added, `18` deleted, `2` renamed). Chi tiết machine-readable tại [gate-c-scope-and-merge-simulation.json](results/gate-c-scope-and-merge-simulation.json).

| # | Miền chức năng | Files | Thay đổi & Lý do | Phụ thuộc & Tác động người dùng | Rủi ro tương thích | Tests đã chạy / Thiếu | Rollback | Quyết định Owner |
| :-: | :--- | :---: | :--- | :--- | :---: | :--- | :--- | :--- |
| 1 | Geometry Kernel, Semantic Program & Scene3D | 55 | Mở rộng kernel exact (`Fraction`/`Radical`), IR, primitive 2D, camera retention & WebGL recovery | Phụ thuộc domain 2, 4; đổi `CACHE_VERSION=132` (cô lập cache 131 vs 132) | LOW–MED | `12,000` geometry, `1,192` semantic, Vitest scene3d, Gate D4 oracle / Thiếu: live paid Gemini K-1/R-1/S-2 | App rollback `bb046fa22` | Chấp thuận cùng Step Editor + `CACHE_VERSION=132` |
| 2 | Step Editor & Revision Persistence | 6 | Inline editor UI, `/steps/edit`, `/steps/cancel`, `/state`, PG row lock `FOR UPDATE NOWAIT`, sync helper metadata (`ccedfabdb`) | Phụ thuộc domain 1, 3, 4, 7; bổ sung API mới, không phá API cũ | LOW | Gate A/B/D/E/F1 + `test_pre_merge_release_acceptance` / Thiếu: không (Model 2 cố ý `MODEL_NOT_TRAINED`) | App rollback; bảng `step_edit_*` additive | Duyệt core deliverable Step Editor V1 |
| 3 | Database Migration | 4 | Linear rev `9c4d8e2b7a10` (`step_edit_*`), `f8a2c41d9e05` (no-op giữ bảng Classroom), `migration_preflight.py` AST + drift + partial + unstamped exit `23` | Phụ thuộc `alembic/env.py`, `Dockerfile`, `main.py`; DB legacy chưa stamp cần backup + kiểm parity + stamp trước `upgrade head` | MEDIUM (ops runbook) | Gate A (4 container exit `23`), Gate B (`pg_dump`/`pg_restore`), `test_database_safety_closure` / Thiếu: không | `pg_restore` hoặc app rollback (không `alembic downgrade` phá dữ liệu) | Phê duyệt runbook vận hành cho DB unstamped legacy |
| 4 | Workspace & Attachment | 95 | Single-instance tab model, recovery snapshot, `+` menu (`ScreenCaptureDialog`, `pdfjs-dist`), left sidebar & `global.css` | Phụ thuộc `App.tsx`, `SimulationWorkspace.tsx`, deps frontend; đổi luồng mở tab và nhập đề | MEDIUM | `192` files / `2,274` Vitest + Playwright smoke (`#btn-composer-plus` -> `#plus-popover-menu`, tab close/reopen, dock scroll) / Thiếu: multi-page PDF & webcam hardware E2E | App rollback | **Cần duyệt gộp Workspace/Attachment UI trong cùng đợt merge** |
| 5 | Landing Page | 17 | Thêm LandingView V1.8 hero/storytelling/closing 3D và **đổi route mặc định `/` thành Landing page** (chuyển workspace sang `/app`) | Phụ thuộc `App.tsx`; **BREAKING NAVIGATION CHANGE** với người dùng/bookmark/test quen vào `/` là workspace ngay | **HIGH** | Vitest landing + Playwright `GET / (200)` & `GET /app (200)` / Thiếu: chữ ký Owner cho phép `/` trỏ LandingView | Đổi route trong `App.tsx` hoặc rollback `bb046fa22` | **Bắt buộc Owner duyệt việc `/` mở LandingView thay vì workspace** |
| 6 | Auth & Classroom/Live Session Retirement | 7 | Gỡ HTTP router `classroom_router.py`, `session_router.py` và ORM khỏi runtime; bảng DB giữ nguyên bằng `f8a2c41d9e05` | **BREAKING API REMOVAL**: `/api/classes*`, `/api/assignments*`, live classroom session trả `404` trên RC | **HIGH** | `backend-other` (`808` passed) + Gate B3 rollback xác nhận route phục hồi `401` khi lùi binary / Thiếu: xác nhận nghiệp vụ ngừng dùng API Classroom | Rollback binary về `bb046fa22` khôi phục ngay mọi API Classroom | **Bắt buộc Owner duyệt ngừng phục vụ HTTP API Classroom/Live Session** |
| 7 | Platform App Wiring | 2 | Gắn router ở `main.py`, preflight CMD ở `Dockerfile`, ràng buộc single-worker PG (`503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY`) | Ràng buộc vận hành deploy Uvicorn `workers=1` với PostgreSQL row lock | MEDIUM | Gate A real Docker, Gate B3 rollback, `test_dev_backend_launcher`, `test_step_editor_integration_closure` / Thiếu: prod TLS/ingress soak test | Rollback container `bb046fa22` | Xác nhận kiến trúc deploy single-worker với PG16 |
| 8 | Config, Scripts & Runtime | 17 | `conftest.py` (PID+nonce SQLite test isolation), `backend/scripts/*`, `vite`/`package.json`/`index.html` | Quy trình dev/CI (`dev_backend.py`, `freeze_evaluation_candidate.py`) | LOW | `backend-other`, `--verify`, `vite build` / Thiếu: không | Git revert | Thay đổi kỹ thuật phát hành thường lệ |
| 9 | Tests, Docs & Eval Artifacts | 485 | Test suites mới, `EVALUATION_CANDIDATE.json`, C21 templates, `CODE_INDEX.md`, báo cáo các wave eval | Không ảnh hưởng runtime | NONE | `audit_docs_information_architecture.py PASS`, `code-index-sync.test.ts PASS`, `--verify PASS` / Thiếu: không | Git branch sạch | Quản trị tài liệu & bằng chứng chuẩn |

---

## 8. Merge Simulation Result (Gate C3)

Thực hiện trên repo cô lập tạm `.superpowers\merge-sim-tmp` từ `HEAD` hiện tại (`a0f4a5166`) so với `main` (`bb046fa22aceff47abe22aa783aa64fc65caee13`) và dọn sạch ngay sau kiểm tra:

- `git merge-base --is-ancestor main HEAD`: `EXIT = 0` (`main` là tổ tiên trực tiếp của RC).
- `git merge-tree --write-tree main a0f4a5166`: `EXIT = 0`, resulting tree `2510c29e57db9737c0cb111b1c8e7302b747a50b` **khớp 100%** với `HEAD^{tree}`.
- `git merge --ff-only` trên nhánh tạm trỏ `bb046fa22`: `EXIT = 0`, resulting tree khớp RC.
- `git merge --no-commit --no-ff` trên nhánh tạm trỏ `bb046fa22`: `EXIT = 0`.
- **Conflict cơ học:** `0` file.
- **Conflict hành vi / sản phẩm (không thể tự quyết bằng merge cơ học):** (1) `/` đổi thành LandingView thay vì workspace trực tiếp (`/app`); (2) API Classroom & Live Session trả `404` do đã gỡ router runtime.
- `main` và `origin/main` vẫn ở `bb046fa22aceff47abe22aa783aa64fc65caee13`.

---

## 9. Step Editor & Scene3D Regression + Independent Oracle (Gate D)

### D1. Valid Edit (`chop-mat-cau-ngoai-tiep` trên Chrome thực tế + PG16 `:55432`)
- Sửa bước 8 (`mp_tt_AB`) từ `"Dựng mặt phẳng trung trực (α) của cạnh AB"` → `"Dựng mặt phẳng trung trực (P) của cạnh SB"`:
  - `POST /api/simulation/steps/edit` → `200 OK`, `recomputed_ids = 9`, `mp_tt_AB.normal = ["4", "0", "-4"]`, `I = ["2", "2", "2"]`, `R² = 12`.
  - **Zero stale leak check (DOM + Scene3D + Events):** `0` dòng chứa `(α)` còn lại trong `#dock-steps-ul`, `3` dòng cập nhật `(P)`, điểm `I` (`pointIRoleAfter`) hiển thị `"Giao điểm của «Giao tuyến của (P) và (β)» và (γ)"`, và **`M_AB.learner_text == "Dựng trung điểm của S và B."`** (đóng triệt để lỗi gốc `ISSUE-SE-ABSORBED-HELPER-AND-HOISTED-EVENT-SYNC`), `leakedRawHelperOrOldNotation = false`.

### D2. Invalid Edits & Concurrency (`422` & `409`)
- Nhập toàn dấu cách (`"   "`) → nút `Chạy` bị disable, không gửi HTTP.
- 3 đầu vào sai trên S11 (`undefined_point_SZ` → `422 MISSING_DEPENDENCY`, `collinear_AOC` → `422 COLLINEAR_POINTS`, `unsupported_syntax` → `422 UNSUPPORTED_STEP_SYNTAX`) đều giữ nguyên draft trong textarea, giữ nguyên vị trí bước hiện tại (`counterPreservedOn422 = true`), và không làm hỏng `(P)` / `SB` đã commit.
- Ràng buộc hình học downstream trên bài toán khoảng cách hai đường chéo nhau (`Lấy điểm Q thuộc BD sao cho BQ/BD = 1/5`) → `422 DOWNSTREAM_ORTHOGONALITY_BROKEN`.
- Thăm dò concurrency trên S1 (`v=10`): `expected_committed_version = 0` → `409 STALE_REVISION_CONFLICT`; `client_seq = 1 < 10` → `409 EDIT_SUPERSEDED`.

### D3. Persistence (F5, Tab Close/Reopen, Multi-Problem Switch & Backend Restart Recovery)
- Chạy chuỗi 10 lượt chỉnh tỷ số `SM/SA` (`1/4 -> 3/4 -> 1/2 ... -> 1/4`) trên `chop-thiet-dien-ba-diem`, nhấn `F5` reload trang → giữ đúng `SM/SA = 1/4`.
- Chuyển sang `lang-tru-tam-giac-thiet-dien` sửa `CP = 1/3 CC′` (`200 OK`), đóng tab đang mở và mở lại `chop-thiet-dien-ba-diem` → khôi phục đúng `SM/SA = 1/4`.
- Dừng hoàn toàn tiến trình Uvicorn `:8000` (`task-5747`), khởi động lại tiến trình Uvicorn mới (`task-5829`) kết nối PG16 `algosim_acceptance`, mở phiên trình duyệt sạch với client token đã lưu → `GET /api/simulation/sessions/{sid}/state` trả `200`, `found = true`, `committed_version = 10`, `revision_count = 10`, `M.xyz = ["0", "0", "9/2"]`, UI dòng 6 hiển thị `"Lấy điểm M thuộc SA sao cho SM/SA = 1/4"`.

### D4. Independent Pure-`Fraction` Geometry Oracle ([gate-d4-independent-oracle.json](results/gate-d4-independent-oracle.json))
Oracle thuần Python `fractions.Fraction` (zero import từ `app.simulation.geometry`) kiểm chứng độc lập 6 nhóm bài toán:
1. **Trung điểm, mặt phẳng trung trực & mặt cầu ngoại tiếp (`chop-mat-cau-ngoai-tiep` -> `(P)` cạnh `SB`):** kiểm tra `M_AB = (S+B)/2 = ["2", "0", "2"]`, `M_AB.depends = ["S", "B"]`, `mp_normal × (B-S) = 0`, giao tuyến `truc_day` nằm trên cả `(P)` và `(β)`, `|A-I|² = |B-I|² = |C-I|² = |D-I|² = |S-I|² = 12`, `0` rò rỉ `"A và B"` hay `"(α)"`.
2. **Điểm theo tỉ số & thiết diện chóp (`SM/SA = 1/4, 3/4, 1/2`):** vị trí `M`, đồng phẳng & thứ tự lồi polygon 5 cạnh, `E ∈ SB`, `F ∈ SD` nội bộ đoạn (`t ∈ (0,1)`), khớp chính xác `area_sq_exact` (`425/2`, `9801/50`, `216`).
3. **Lăng trụ & Lập phương (`CP = 1/3 CC′`, `AM/AD = 1/3`):** thiết diện ngũ giác (`area² = 244`) và lục giác (`area² = 751109/1764`) đồng phẳng, lồi, khớp `S_td`.
4. **Đường vuông góc chung hai đường chéo nhau (`SC` & `BD`):** giải độc lập hệ Gram `2×2` khẳng định `(P, Q)` khớp nghiệm giải tích `u = 2/3, v = 1/2`, `PQ ⟂ SC`, `PQ ⟂ BD`, `|PQ|² = 8/3`.
5. **Đo đạc chính xác:** đối chiếu `R² = 12`, `V = 32π√3`, chuỗi `S_td²`, khoảng cách `d² = 8/3`.
6. **Biên suy biến & từ chối (`6/6` fail-closed):** `COLLINEAR_POINTS`, `INVALID_OPERAND`, `MISSING_DEPENDENCY` (điểm chưa định nghĩa & tham chiếu vòng), `INVALID_RATIO` (`5/4`), `UNSUPPORTED_STEP_SYNTAX`.
- **Giới hạn tổng quát hóa của oracle:** Oracle chỉ kiểm chứng độc lập trên tập bài toán Euclidean chính xác đã dựng sẵn bằng Step Editor; **không** gọi API AI trả phí (K-1/R-1/S-2 giữ chế độ offline), **không** kiểm tra dựng mới mặt cong tổng quát từ ngôn ngữ tự nhiên tự do hay Model 2 (`MODEL_NOT_TRAINED`).

---

## 10. Live Host & Responsive Browser Evidence (Gate E)

- **Port thực tế đo được:** Frontend Vite dev server `http://localhost:3001` (`task-5736`) · Backend FastAPI Uvicorn `http://127.0.0.1:8000` (`task-5747`/`task-5829`, `ALGOSIM_GIT_SHA = a0f4a5166...`) · PostgreSQL 16.6 `127.0.0.1:55432` (`algosim_acceptance`).
- **Hành vi camera, scrubber & draft:**
  - Kéo orbit + zoom (`maxOrbitMovePx = 171.234 px`) trước khi mở editor; sau khi sửa `mp_tt_AB` và commit thành công, đọc trực tiếp trạng thái camera Three.js từ snapshot cho **`threeJsCameraPositionDelta = 0` và `threeJsCameraTargetDelta = 0`** (camera 3D giữ nguyên tuyệt đối; các nhãn 2D chỉ tự né đè để không che đường/nhãn mới).
  - Mở editor bằng phím `Enter` và nhấn `Escape` giữ nguyên vị trí scrubber (`Bước 15/17 -> Bước 15/17`); commit hợp lệ ở bước 8 chủ động focus scrubber tới bước vừa sửa (`Bước 8/17`, hành vi thiết kế sẵn từ `7607f0d6` qua `pendingFocusTargetIdRef`, không reset về `Bước 1/17`). Toàn bộ 3 ca `422` đều giữ nguyên bước hiện tại.
  - Draft chưa lưu trong textarea giữ nguyên nguyên vẹn khi cuộn `.dock-scroll`; wheel trong `.dock-scroll` được cô lập (`overscrollBehaviorY: contain`), canvas không dịch chuyển (`canvasShiftDuring = 0`, `canvasShiftAfter = 0`).
- **Ma trận Viewport Responsive & Touch/VKB (`0` console errors, `0` page errors, `0` unexpected 5xx):**

| Viewport / Chế độ | `overflowX` | Canvas (`W×H`) | Nút `Chạy`/`Hủy` | `Scene3D` controls & labels | Ảnh chụp |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `1920 × 1080` (Desktop) | `0` | `1289 × 1042` | Không cắt, không bị che | WebGL `healthy`, `0` clipped, `0` occluded, `0` overlap | [vp-1920](images/final-readiness-vp-1920x1080.png) · [rename-P](images/final-readiness-1920-sb-rename-P.png) · [422](images/final-readiness-1920-422-rollback.png) |
| `1440 × 900` (Laptop) | `0` | `809 × 862` | Không cắt, không bị che | WebGL `healthy`, `0` clipped, `0` occluded | [vp-1440](images/final-readiness-vp-1440x900.png) |
| `1280 × 800` (Compact) | `0` | `673 × 762` | Không cắt, không bị che | WebGL `healthy`, `0` clipped, `0` occluded | [vp-1280](images/final-readiness-vp-1280x800.png) |
| `768 × 1024` (Tablet) | `0` | `472 × 986` | Không cắt, không bị che | WebGL `healthy`, `0` clipped, `0` occluded | [vp-768](images/final-readiness-vp-768x1024.png) |
| `390 × 844` (Mobile) | `0` | `390 × 444` | Không cắt, không bị che | WebGL `healthy`, `0` clipped, `0` occluded | [vp-390](images/final-readiness-vp-390x844.png) |
| `320 × 568` (Small Mobile) | `0` | `320 × 293` | Không cắt, không bị che | WebGL `healthy`, `0` clipped, `0` occluded | [vp-320](images/final-readiness-vp-320x568.png) |
| Touch `390×844` → VKB `390×460` | `0` | Đang hiển thị | Cả textarea + `Chạy` + `Hủy` nằm trọn viewport | Nút bút chì bật rõ sau chạm (`pencilVisibleOnTouchActive = true`) | [vkb-390x460](images/final-readiness-vkb-390x460.png) |

- **Kiểm tra độc lập bằng REA MCP (headless Chromium CDP tạm `:9339` tại `1440×900`, đã tắt port `:9339` ngay sau capture):**
  - `list_browser_targets`: `ev_6b939fff27994a5244fe0a4c6665babb41aa5b5bad6e1d88b1fc364cc6fb86a0`
  - `inspect_web_page`: `ev_06015a0f6f1a2f5cfbe05bd7709ffeb3c35742360c4a85f270e044fbb30d7e42` (`console_error_count = 0`, `storage.values_redacted = true`)
  - `capture_web_screenshot`: `ev_973b14770495dac5c29bf584f6bdc09a75159ae0caeca44a62dbd9f0ea52aa31` → [final-readiness-rea-mcp.png](images/final-readiness-rea-mcp.png) (`150,127` B, SHA-256 `64513149a1cef8ea1d37aaf9bdbd5994a1507dbdacd32044807ac075fe3a4db4`).
- **Kiểm chứng sống sót dữ liệu PostgreSQL `algosim_acceptance` ([gate-e-postgres-survival.json](results/gate-e-postgres-survival.json)):**
  - `100%` khóa chính có sẵn trước khi chạy browser & live HTTP bench đều sống sót nguyên vẹn (`no_truncate_used = true`, `lost_pre_pks = []` trên toàn bộ `15` bảng); delta mới thực ghi: `auth_sessions` `36 -> 53 (+17)`, `step_edit_sessions` `13 -> 25 (+12)`, `step_edit_revisions` `35 -> 91 (+56)`, `step_edit_feedback` `35 -> 91 (+56)`.

---

## 11. Test Suites & Skipped / XFail / Deselected Audit (Gate F1)

Tất cả suite chạy **tuần tự tuyệt đối không chồng lấn** trên đúng commit **`a0f4a5166`** ([gate-f1-test-integrity.json](results/gate-f1-test-integrity.json)):

| Suite | Kết quả thực chạy | Ghi chú & Đường dẫn log |
| :--- | :--- | :--- |
| Candidate Seal `--verify` | **`PASS`** (`109` files, `ea6626e7a205e33a…`) | [seal-verify.log](logs/seal-verify.log) |
| Migration Drift (`alembic check` + `preflight --startup`) | **`PASS`** (`No new upgrade operations`, `SAFE_NO_DESTRUCTIVE_OPERATIONS`) | [migration-drift.log](logs/migration-drift.log) |
| `pytest -m postgres -v -rsx` | **`6 passed`**, `0` failed, `14,017` deselected | Chạy PG16 thật; xem phân tích deselected bên dưới · [backend-postgres.log](logs/backend-postgres.log) |
| `pytest tests/geometry -rsx -q` | **`12,000 passed`**, `0` failed, `6 skipped`, `3 deselected`, `9 xfailed` | Tăng +1 test so với mốc `11,999` nhờ test mới `ccedfabdb` · [backend-geometry.log](logs/backend-geometry.log) |
| `pytest tests/semantic_program -rsx -q` | **`1,192 passed`**, `0` failed, `1 skipped` | [backend-semantic-program.log](logs/backend-semantic-program.log) |
| `pytest tests --ignore=tests/geometry --ignore=tests/semantic_program -rsx -q` | **`808 passed`**, `0` failed, `4 deselected` | Bao gồm `test_absorbed_helper_and_hoisted_event_learner_text_sync_without_stale_operands` · [backend-other.log](logs/backend-other.log) |
| Demo Replay & Crash Surface Audit | **`PASS`** (`5/5` demo replay, `1/1` reduced chain, `6/6` crash boundaries, `0` uncaught) | [backend-demo-audits.log](logs/backend-demo-audits.log) |
| Frontend `tsc -b` | **`PASS`** (`EXIT 0`, 0 lỗi) | [frontend-tsc.log](logs/frontend-tsc.log) |
| Frontend `vite build` | **`PASS`** (`129` modules, `4.88s`, không tồn tại `dist/prototypes`) | [frontend-vite-build.log](logs/frontend-vite-build.log) |
| Frontend `vitest run` | **`192 files / 2,274 passed`**, `0` failed, `0` skipped | [frontend-vitest.log](logs/frontend-vitest.log) |

### Kiểm toán Skipped, XFailed & Deselected (`0` ca bỏ qua vô căn cứ)
- **Skipped (`6` ở `tests/geometry` + `1` ở `tests/semantic_program` = `7`):**
  - `tests\geometry\test_unified_solid_scope.py:186` × `6` (3 case `A3-DEV-02`, `A3-DEV-09`, `demo1-pyramid-derived-section`, mỗi case 2 tham số hóa vì không có mục tiêu `residual_volume`).
  - `tests\semantic_program\test_scalar_obligations.py:95` × `1` (thiếu `term` mặc định về identity — đã có test riêng).
- **XFailed (`9` ở `tests/geometry`, toàn bộ đều là defect/gap đã đăng ký trước):**
  - `test_generalized_goal_entry.py::test_length_goal_refusal[unread-second-ask]` & `[contradictory-length]` (2).
  - `test_hybrid_compiler_benchmark.py::test_case_outcome[B27-facts|B27-pipeline|B28-facts|B28-pipeline]` (4).
  - `test_hybrid_simulation_capability_probes.py::test_centre_label_exhaustion_is_a_coded_outcome` (1).
  - `test_premise_source_coverage.py::test_goal_fact_quote_does_not_cover_a_hypothesis[...]` (1).
  - `test_source_grounding_reliability.py::test_targeted_case_meets_its_preregistered_label[E05-unsupported-second-quantity]` (1).
- **Deselected (`7` ở chế độ offline mặc định do `pytest.ini` `addopts = -m "not postgres and not external_evidence"`):**
  - `6` test `@pytest.mark.postgres` (2 trong `tests/geometry/test_step_editor_integration_closure.py`, 4 ở `tests/test_database_safety_closure.py`, `test_postgres_axo_history_migration.py`, `test_postgres_integration.py`, `test_pre_merge_release_acceptance.py`) → **Tất cả `6/6` ĐÃ CHẠY & `PASSED` trong lượt `pytest -m postgres`.**
  - Duy nhất `1` test toàn repo vẫn là opt-in ngoài kho: `tests/geometry/test_evidence_identity_reconciliation.py::test_raw_response_identity_reproduced` (`@pytest.mark.external_evidence`, `NA-05`, cần `ALGOSIM_LIVE_RETRY_EVIDENCE_DIR` bên ngoài kho).

---

## 12. Performance Comparison vs Baseline 19/11/2026 (Gate F2)

- **Cấu hình máy & điều kiện đo:** Intel Core i5-11400H @ 2.70GHz, Python 3.12.10, Windows (`win32`), headless Chromium + SwiftShader WebGL + Uvicorn single-worker `:8000` kết nối PG16 `127.0.0.1:55432` ([gate-f2-performance-comparison.json](results/gate-f2-performance-comparison.json)).

| Nhóm chỉ số (6 chỉ số bắt buộc F2) | Số mẫu | p50 (ms) | p95 (ms) | Baseline `2a44ac921` p50 / p95 (ms) | Delta p50 / p95 | Đánh giá / Ngưỡng đề xuất Owner |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 1. **Validate edit** (`validation_ms` S11 partial / S1 cascade) | 30 | `2.962` / `4.143` | `4.253` / `4.394` | `2.912/3.572` · `4.233/6.115` | `+0.050` / `-0.090` | Ổn định; đề xuất budget p95 `< 15 ms` |
| 2. **Rebuild object graph** — S11 partial (`9` objs `total_ms`) | 30 | `11.163` | `22.686` | `10.269 / 11.748` | `+0.894 / +10.938` | p50 tương đương (`< 1 ms`), min `10.376`; p95 do GC spike; đề xuất p95 `< 35 ms` |
| 2b. **Rebuild object graph** — S11 full rebuild (`26` objs) & S1 cascade (`6` objs) | 30 | `11.152` / `11.511` | `11.754` / `12.230` | `10.426/11.236` · `11.808/24.884` | `+0.726` / `-0.297` (`-12.654` p95) | Không regression |
| 3. **PostgreSQL 16 commit + HTTP RTT** (`POST /steps/edit` qua `:8000` -> PG16) | 30 | `54.245` (`srv 12.991`) | `84.665` (`srv 13.811`) | Chưa đo tách riêng ở baseline | — (chỉ số mới) | Sub-100ms end-to-end PG ACID; đề xuất budget p95 `< 120 ms` |
| 4. **Frontend update completion** (POST resp → detach + 2 rAF) | 10 | `121.188` | `169.240` | Chưa đo tách riêng | — | Đề xuất budget p95 `< 250 ms` |
| 5. **UI interaction open latency** (click pencil → textarea visible) | 10 | `22.695` | `29.216` | Chưa đo tách riêng | — | Tức thời với người dùng; đề xuất budget p95 `< 60 ms` |
| 6. **Scene3D post-edit render** (`__AXO_LAST_STEP_EDIT_METRICS__`) & **Full E2E Roundtrip** | 10 | `29.600` (render) · `209.395` (E2E) | `34.775` (render) · `259.164` (E2E) | Render chưa đo riêng · E2E `129.500 / 194.050` | `+79.895 / +65.114` (do phương pháp đo)* | \*Baseline cũ dừng đồng hồ ngay lúc textarea đóng; đợt này đợi thêm **2 `requestAnimationFrame`** hoàn tất dựng Scene3D; không phải regression thuật toán |

---

## 13. Root-Cause Issues & Fix Commits

### Lỗi gốc phát hiện và xử lý triệt để trong chiến dịch này
- **ID:** `ISSUE-SE-ABSORBED-HELPER-AND-HOISTED-EVENT-SYNC`
- **Triệu chứng tái hiện:** Trên `chop-mat-cau-ngoai-tiep`, khi sửa bước `mp_tt_AB` sang `"Dựng mặt phẳng trung trực (P) của cạnh SB"`, đối tượng helper bị gộp `M_AB` trong `scene3d.objects` đã cập nhật sang trung điểm của `S` và `B`, nhưng sự kiện tạo `M_AB` (`events[9]["learner_text"]`) vẫn giữ nguyên chuỗi cũ `"Dựng trung điểm của A và B."`, đồng thời các sự kiện phụ thuộc được nâng (`hoist_ev_by_obj`) không đi qua bước làm mới `details`/`depends`/`visible_prerequisites`.
- **Nguyên nhân gốc & invariant vi phạm:** `rebuild_dependent_steps` trong `backend/app/simulation/geometry_functions/step_editor.py` chỉ cập nhật metadata sự kiện ở vòng lặp chính mà bỏ qua các sự kiện nằm trong nhánh hoisted, và không đồng bộ `learner_text` của các helper `CREATE` bị gộp (`kept_helpers`) theo nhãn/toán hạng mới.
- **Sửa tận gốc:** Trích một helper dùng chung `_sync_rebuilt_event(ev_copy)` tại chính nơi sở hữu sự kiện ở `step_editor.py` để đồng bộ thống nhất cả nhánh hoisted lẫn vòng lặp chính; bổ sung regression test [`test_absorbed_helper_and_hoisted_event_learner_text_sync_without_stale_operands`](../../../../../backend/tests/test_pre_merge_release_acceptance.py).
- **Commits:** Fix `ccedfabdb3deb67563a6bf4bc42d00b793c844c9` · Refreeze seal + C21 sync `a0f4a516630bb582d982463cd1160f7668154221` (khôi phục thành công `M_AB.learner_text == "Dựng trung điểm của S và B."` qua cả Oracle D4, Docker Boot 1 và live browser E2E).

*(Lưu ý các root-cause đã sửa từ các đợt trước đó — `ISSUE-DB-DRIFT-AND-PARTIAL-MIGRATION-PREFLIGHT`, `ISSUE-SE-STALE-REVISION-METADATA`, `ISSUE-TEST-WINDOWS-PID-DB-REUSE` — tiếp tục được xác nhận xanh qua toàn bộ suite trên `a0f4a5166`.)*

---

## 14. Remaining Risks

1. **Rủi ro nghiệp vụ/tương thích ngược (cần Owner quyết định trước khi merge):**
   - Route `/` mở LandingView thay vì trực tiếp solver (`/app`).
   - API Classroom (`/api/classes*`, `/api/assignments*`) và Live Session HTTP routes đã được gỡ khỏi runtime (dữ liệu DB giữ nguyên).
2. **Ràng buộc vận hành triển khai:**
   - Backend trên PostgreSQL yêu cầu chạy **single-worker Uvicorn (`workers=1`)** để bảo đảm semantic đúng của khóa phiên chỉnh sửa (`503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` nếu cấu hình nhiều worker).
   - Mọi database SQLite/PostgreSQL legacy chưa có bảng `alembic_version` sẽ bị preflight chặn với exit `23`; cần thực hiện backup + kiểm chứng schema parity với `e437149641fa` + `alembic stamp e437149641fa` trước khi `alembic upgrade head`.
3. **Phạm vi AI & H-1 chưa kích hoạt:**
   - Paid live Gemini NLU pilot (K-1/R-1/S-2) chưa chạy (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`); Model 2 vẫn ở `MODEL_NOT_TRAINED` (chế độ tất định Step Editor V1 hoạt động hoàn chỉnh không cần Model 2).
   - Kiểm chứng live PG/browser thực hiện trên single-host staging (`Windows + Docker Desktop linux/amd64`), chưa bao gồm soak test multi-replica / production TLS ingress.

---

## 15. Owner Decisions Required (Cổng Quyết Định Chủ Sở Hữu)

Trước khi cho phép merge `release/axo-final-release-readiness` vào `main`, Owner cần phê duyệt rõ 4 điểm sau:

1. **Phạm vi Landing Page & chuyển route `/` → LandingView (`/app` → Workspace):** Chấp thuận gộp `17` file LandingPage V1.8 và đổi trang chủ `/` khỏi màn hình workspace trực tiếp.
2. **Gỡ HTTP Router Classroom & Live Session (`7` files Domain 6):** Xác nhận nghiệp vụ ngừng phục vụ `/api/classes*`, `/api/assignments*`, live classroom sessions ở đợt phát hành này (trong khi giữ nguyên bảng & dữ liệu legacy trong DB để có thể rollback binary về `bb046fa22`).
3. **Gộp cải tiến Workspace & Attachment (`95` files Domain 4) + `CACHE_VERSION = 132`:** Đồng ý đưa hệ thống tab đơn phiên, thanh bên, composer đính kèm cùng đợt phát hành Step Editor V1.
4. **Quy trình vận hành Legacy DB Unstamped & Ngân sách Hiệu năng/AI tiếp theo:** Phê chuẩn runbook backup → parity → stamp cho `algo-sim\backend\algosim.db` (nếu migrate DB cũ), xác nhận single-worker Uvicorn trên PG16, và phê duyệt riêng (nếu muốn) ngân sách cho đợt đo live Gemini K-1/R-1/S-2 sau này.

---

## 16. Final Release Recommendation & 10 Closing Answers

- **Khuyến nghị phát hành:** Giữ trạng thái **`TECHNICALLY_READY_PENDING_OWNER_APPROVAL`**. Về mặt kỹ thuật, toàn bộ các cổng Docker runtime thật, official PostgreSQL `16.15` backup/restore, migration safety, regression toàn repo, independent geometry oracle, responsive browser/REA MCP và performance đều đã đạt **`PASS`**. Tuy nhiên **chưa merge vào `main` và chưa push/deploy** cho tới khi Owner ký duyệt 4 quyết định phạm vi ở Mục 15.

### Trả Lời Dứt Khoát 10 Câu Hỏi Kết Thúc (§12)

1. **Docker runtime thật đã PASS chưa?** — **Rồi (`PASS`)**. Image `axo-release-readiness-backend:rc` (`linux/amd64`, Docker Engine `29.9.2`) đã build từ `a0f4a5166`, boot chạy thật với preflight + Alembic + Uvicorn, xử lý Step Editor qua HTTP, sống sót qua `docker restart`, và chặn fail-closed với exit `23` ở cả 4 ca DB nguy hiểm.
2. **PostgreSQL official backup/restore đã PASS chưa?** — **Rồi (`PASS`)**. Đã dùng `pg_dump 16.15`, `pg_restore 16.15`, `psql 16.15` chính thức (`-Fc`, `92,078` B, `192` TOC objects) khôi phục sạch sang DB độc lập với `100%` parity `20` bảng, FK/UNIQUE/sequence hoạt động đúng, container mới ghi tiếp `v=3` và sống sót qua restart. *(Ghi chú trung thực: host `:55432` lắng nghe chỉ `127.0.0.1` và `pgsql16/bin` không có `pg_dump.exe` nên không chạy `pg_dump` xuyên container vào `:55432`, mà chứng minh đầy đủ trên `staging_source -> staging_restored` dùng cùng schema `f8a2c41d9e05` + dữ liệu Classroom + Step Editor).*
3. **Có phát hiện root-cause bug mới không?** — **Có, 1 lỗi (`ISSUE-SE-ABSORBED-HELPER-AND-HOISTED-EVENT-SYNC`) và đã sửa triệt để + refreeze**. Đã vá tại [`step_editor.py`](../../../../../backend/app/simulation/geometry_functions/step_editor.py) (commit `ccedfabdb`), bổ sung regression test và đóng băng lại seal tại `a0f4a5166`.
4. **Các regression tests còn PASS trên candidate cuối cùng không?** — **Có (`PASS` 100%)**. Mọi suite chạy tuần tự lại trên chính `a0f4a5166`: `6/6` Postgres, `12,000` Geometry (`0` fail, `6` skipped, `3` deselected, `9` xfailed), `1,192` Semantic (`1` skipped), `808` Backend other (`4` deselected PG đã chạy riêng), `5/5` demo + `6/6` crash boundaries, `tsc 0`, `vite build` sạch, `192 files / 2,274` Vitest passed, `seal --verify 0`, `alembic check` sạch.
5. **Phạm vi 9 miền có rủi ro gì khi merge?** — Có rủi ro phạm vi/tương thích ở cấp sản phẩm thuộc **Domain 4, 5, 6**: `/` chuyển thành LandingView (`/app` thành workspace), HTTP API Classroom/Live Session ngừng phục vụ (`404`), và gộp thay đổi UI Workspace/Attachment cùng `CACHE_VERSION = 132`. Rủi ro kỹ thuật dữ liệu thấp nhờ bảo toàn bảng DB và cơ chế fail-closed preflight.
6. **Mô phỏng tích hợp với `main` có conflict không?** — **Không có conflict cơ học (`0` conflicts)** khi chạy `git merge-tree --write-tree`, `ff-only` và `no-ff --no-commit` từ `main` (`bb046fa22`) lên `a0f4a5166`. Tuy nhiên có **2 xung đột hành vi/sản phẩm** (`/` route và gỡ API Classroom) cần Owner quyết định.
7. **Database legacy có được bảo toàn không?** — **Có (`100%`)**. File gốc `algo-sim\backend\algosim.db` (`413,696` B, SHA-256 `39D676C7...`) nguyên vẹn hoàn toàn; trên bản sao cô lập đã chứng minh 100% khớp 16 bảng với `e437149641fa` trước stamp và giữ nguyên 100% digest dữ liệu qua `upgrade head`; `algosim_acceptance` giữ nguyên 100% khóa chính có sẵn sau mọi ca live browser/bench.
8. **Có thể khôi phục ứng dụng và dữ liệu khi xảy ra sự cố không?** — **Có (`PASS`)**. Đã diễn tập thực tế application rollback về code `main` (`bb046fa22`) trên cùng DB PG16 `b3_rollback` (khôi phục `/api/classes` & `/api/assignments`, giữ nguyên dữ liệu Classroom lẫn revision Step Editor khi quay lại RC) và database restore từ file `.pgdump` chính thức `16.15` với `0` mất dữ liệu.
9. **Release candidate có đủ điều kiện kỹ thuật để merge không?** — **Có về mặt kỹ thuật (`TECHNICALLY_READY_PENDING_OWNER_APPROVAL`)** cho phiên bản tất định Step Editor V1 trên single-worker Uvicorn + PG16 (`MODEL_NOT_TRAINED`, chưa đo H-1 live AI). Chưa đủ điều kiện pháp lý/sản phẩm để tự ý merge vì đang đợi Owner phê duyệt phạm vi.
10. **Owner còn phải quyết định những vấn đề cụ thể nào?** — 4 quyết định ở Mục 15: (i) cho phép `/` chuyển sang LandingView V1.8; (ii) xác nhận ngừng phục vụ HTTP API Classroom/Live Session; (iii) đồng ý gộp 95 file Workspace/Attachment + `CACHE_VERSION=132` cùng đợt; (iv) phê chuẩn runbook stamp/upgrade cho DB legacy, ràng buộc single-worker PG, và (tùy chọn về sau) ngân sách chạy pilot live Gemini H-1.
