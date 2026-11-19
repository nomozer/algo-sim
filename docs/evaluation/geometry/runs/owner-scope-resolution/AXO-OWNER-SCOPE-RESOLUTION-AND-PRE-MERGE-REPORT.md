# AXO — Owner Scope Resolution, Option B Verification & Final Pre-Merge Gate

- **Ngày báo cáo:** `2026-11-19`
- **Worktree đánh giá:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\owner-scope-resolution`
- **Nhánh:** `release/axo-owner-scope-resolution`
- **Baseline `main` / `origin/main`:** `bb046fa22aceff47abe22aa783aa64fc65caee13`
- **Candidate Code/Test Commit:** `892e15f06fc53c623a1392f0766d69c21291436a` (Option B + docs/tests: `6880a03eb295cd45152e8114a8867cfee7b2ee4c`, niêm phong từ `9c1c8bca8ce900bb2125c7459a4f60469d3660f2`)
- **Measured System Tree Hash (`freeze_evaluation_candidate.py --verify`):** `78edfa1784625e9bca8f1a4cd70b60359d198ba77530986903175a57e18206a7` (`109` file sản phẩm)

---

## A. Executive Summary

Đợt kiểm định `owner-scope-resolution` đã triển khai và xác minh dứt điểm **Option B** cho phạm vi **Classroom / Live Session** (gỡ bỏ vĩnh viễn giao diện và các endpoint HTTP lớp học/phiên dạy trực tiếp trong V1, đồng thời bảo toàn nguyên vẹn 100% 5 bảng cơ sở dữ liệu lịch sử), đóng đầy đủ các kiểm thử end-to-end từ backend, PostgreSQL 16, semantic events đến Scene3D và frontend trên trình duyệt thực tế.

| Chỉ số / Trạng thái | Giá trị xác minh |
| --- | --- |
| **RELEASE_DECISION** | `TECHNICALLY_READY_PENDING_OWNER_APPROVAL` |
| **C_CLASSROOM_DECISION** | `OPTION_B_IMPLEMENTED_AND_VERIFIED` |
| **NON_CLASSROOM_OWNER_GATES** | `PENDING_OWNER_DECISION` (`C-Landing`, `C-Workspace`, `C-Release`) |
| **DOCKER_RUNTIME_GATE** | `ENVIRONMENT_BLOCKED` (`com.docker.service` stopped trên host Windows) |
| **MODEL_STATUS** | `MODEL_NOT_TRAINED` |
| **MERGE_STATUS / PUSH_STATUS** | `NOT_MERGED` / `NOT_PUSHED` |
| **PRODUCTION_DEPLOYMENT_VERIFIED** | `NO` (`Hybrid /4`, `CACHE_VERSION = 132`) |
| **INDEPENDENT_H1_VALIDATION** | `NOT_MEASURED` |

> [!IMPORTANT]
> Cả ba checkout được bảo vệ (`D:\Documents\projects\algo-sim` tại `bb046fa22`, `step-editor-release-candidate` tại `86b62adbb`, `pre-merge-risk-closure` tại `9c1c8bca8`) và `D:\Documents\projects\algo-sim\backend\algosim.db` (SHA-256 `39D676C7B50A925975828434A00D38E3BAC3C5F50E4E2A724A695768C7C83EE3`) được giữ nguyên hoàn toàn không chạm tới.

---

## B. Ownership & Scope Resolution Table (`bb046fa22..892e15f06`)

Tổng số file thay đổi giữa `main` (`bb046fa22aceff47abe22aa783aa64fc65caee13`) và candidate (`892e15f06fc53c623a1392f0766d69c21291436a`): **761 files** ([ownership-domain-audit.json](results/ownership-domain-audit.json)).

| Domain / Bucket | Số file | Quyết định hiện tại | Bằng chứng & Phạm vi đã kiểm |
| --- | ---: | --- | --- |
| **C-Classroom** (`C-Classroom_Auth_Admin`) | 20 | **`OPTION_B_IMPLEMENTED_AND_VERIFIED`** | 0 route lớp học trong `app.openapi()`; 18/18 endpoint Classroom/Live Session trả `404 {"detail":"Not Found"}` qua ẩn danh/student/teacher; `seed_classroom_fixture.py` & `accept-live-classroom.mjs` fail-closed (`exit 2`, `CLASSROOM_FEATURE_RETIRED`); `accept-product-scope.mjs` (`48/48` PASS) không còn gọi `/api/classes*` hay `/api/assignments*`; tài liệu `CODE_INDEX.md`, `ARCHITECTURE_MAP.md`, `CLASSROOM_AUTH_CONTRACT.md` đã đồng bộ Option B. |
| **C-Landing** (`C-Landing`) | 38 | **`PENDING_OWNER_DECISION`** | Đã kiểm chứng kỹ thuật (`/` -> `LandingView`, `/app` -> Workspace, HTTP `200`, 0 nhãn Tin học cũ, 0 lỗi console/page), chờ Owner phê duyệt đưa Landing mới lên `main`. |
| **C-Workspace** (`C-Workspace_Attachment_Scene3D_UI`) | 127 | **`PENDING_OWNER_DECISION`** | Đã kiểm chứng kỹ thuật qua `tsc -b`, `npm run build`, `2,278` Vitest tests, nút đính kèm composer (`#btn-composer-plus`), Scene3D và 6 viewport + VKB, chờ Owner phê duyệt phạm vi UI Workspace/Attachment. |
| **Step Editor Core** | 15 | **`TECHNICALLY_VERIFIED`** | Truy vết 8 tầng không lỗi, bất biến camera, `422`/`409` fail-closed, PG16 recovery. |
| **DB Migration Safety** | 6 | **`TECHNICALLY_VERIFIED`** | Preflight AST/drift/stamp guard (`BLOCK_EXIT_CODE=23`), `f8a2c41d9e05` giữ nguyên 5 bảng lịch sử, backup/restore & `bb046fa22` rollback PASS. |
| **Backend Hybrid / Geometry / Ingestion** | 20 | **`TECHNICALLY_VERIFIED`** | `12,000` geometry + `1,192` semantic program + `815` root tests PASS. |
| **Docs & Evaluation** | 533 | **`TECHNICALLY_VERIFIED`** | `audit_docs_information_architecture.py` PASS (`0` liên kết gãy, `0` stale `CODE_INDEX` path, `0` secret leak, `29` root docs, `167` catalogued). |
| **Root Config / Docker** | 2 | **`PENDING_OWNER_DECISION` / `ENVIRONMENT_BLOCKED`** | Daemon Docker Windows không khả dụng trên host (`com.docker.service` `Stopped`). |
| **C-Release** (Merge / Push / Deploy) | — | **`PENDING_OWNER_DECISION`** | Giữ `NOT_MERGED` / `NOT_PUSHED` chờ Owner nghiệm thu cuối. |

---

## C. Option B Database & Migration Proof (PostgreSQL 16.6)

### 1. Schema Parity & Non-Destructive Retention (`algosim_osr_live`)
Bằng chứng tại [pg16_live_setup.json](results/pg16_live_setup.json):
- Khởi tạo DB sạch `algosim_osr_live` trên host PostgreSQL `16.6` (`127.0.0.1:55432`) ở revision `e437149641fa`, bơm đầy đủ đồ thị dữ liệu 5 bảng Classroom lịch sử + 3 tài khoản `users`.
- Chạy `migration_preflight.py --startup --json` -> `allowed=true` (`SAFE_NO_DESTRUCTIVE_OPERATIONS`, nhận diện đủ 5 bảng giữ lại), `alembic upgrade head` -> `f8a2c41d9e05`, và `alembic check` -> `No new upgrade operations detected.`.
- Tổng số bảng: **20 tables** (`15` bảng hoạt động + `5` bảng Classroom lịch sử: `classrooms`, `class_memberships`, `assignments`, `practice_sessions`, `classroom_sessions`).
- **SHA-256 Digest Parity 100%** trước upgrade, sau upgrade, và **sau toàn bộ Playwright E2E + restart** (`4` phiên Step Editor, `41` revisions đã ghi nhưng 0 byte bị thay đổi trên 5 bảng Classroom & `users`):
  - `classrooms`: `1` hàng (`00f8d608d0fb4baf86bfb2d63ab0d582a2237639c8690db50b322c7555721196`)
  - `class_memberships`: `2` hàng (`b8fa76ffa3d5489ed35b0285950581b99b53609ea31420e239736ceaefafd540`)
  - `assignments`: `1` hàng (`eb837caad541c7996eb68c2223cc973d59a5492096732fabf556bfb75c975d44`)
  - `practice_sessions`: `2` hàng (`9e00005aac1d23f8f768f6e2e4385a81b0fe82322a9a1e69d5b569915cbd24a5`)
  - `classroom_sessions`: `1` hàng (`19a4c7122bc381f6b8e4c58a2e98ded7edc964bb82bc5ada47edc2c6e833b7ab`)
  - `users`: `3` hàng (`d670c95961a8738e60d2cf2eaf5cfde49fb894fb58dd642f6bf66da81b0fad67`)

### 2. Logical Backup, Restore & `bb046fa22` Rollback Rehearsal
Bằng chứng tại [pg16-backup-restore-rollback.json](results/pg16-backup-restore-rollback.json):
- **Single-Transaction Snapshot (`REPEATABLE READ READ ONLY`):** sao lưu cả DDL, ràng buộc, index, sequence và dữ liệu CSV cả 20 bảng thành `pg16_algosim_osr_live.snapshot.tar.gz` (`89,236` bytes, SHA-256 `fe0903cf2685162a9c967a1bea2f679df9cdfa03daf475a178d780b60e183ac8`).
- **Restore & Parity (`algosim_osr_restored`):** khớp 100% toàn bộ 20 bảng, kiểm thử âm tính FK (`ForeignKeyViolation=true`) và UNIQUE (`UniqueViolation=true`) đều kích hoạt đúng, `nextval('step_edit_sessions_id_seq') = 6` vượt giá trị trước sao lưu, khởi động Uvicorn candidate trên `algosim_osr_restored` và thực hiện thành công 1 Step Edit (`HTTP 200`, `committed_version=1`).
- **Rollback về `main` (`bb046fa22`):**
  - **Mode A (Application-only rollback trên DB 20 bảng giữ nguyên):** trích xuất `backend/` từ `bb046fa22` bằng `git archive`, khởi động trực tiếp trên DB đã khôi phục -> `/api/health` trả `200`, `/api/classes` & `/api/assignments` khôi phục đúng (`401` khi chưa đăng nhập, `200` sau khi đăng nhập).
  - **Mode B1 (`alembic downgrade 9c4d8e2b7a10`):** hạ cấp không phá hủy từ `f8a2c41d9e05` thành công (exit `0`).
  - **Mode B2 (`alembic downgrade e437149641fa`):** `ALGOSIM_STARTUP_MODE=1` chặn với `DOWNGRADE_FORBIDDEN_AT_STARTUP`; `ALGOSIM_GUARD_DESTRUCTIVE_DOWNGRADE=1` chặn khi chưa có backup approval (`DESTRUCTIVE_DOWNGRADE_DATA_LOSS_BLOCKED`); khi cấp `ALGOSIM_BACKUP_VERIFIED=1` + `ALGOSIM_ALLOW_DESTRUCTIVE_MIGRATION=9c4d8e2b7a10`, hạ cấp còn `17` bảng bảo toàn 100% digest 5 bảng Classroom và `bb046fa22` đọc `/api/classes` trả `200`.

### 3. Docker Container Gate (`ENVIRONMENT_BLOCKED`)
Bằng chứng tại [docker-runtime-check.json](results/docker-runtime-check.json):
- Thử khởi động có kiểm soát `Docker Desktop.exe` và thăm dò 60 giây trên host Windows: dịch vụ `com.docker.service` vẫn ở trạng thái `Stopped` (`Manual`), `docker version` thoát mã `1` (`"Server": null`, lỗi pipe `//./pipe/dockerDesktopLinuxEngine`). Cổng Docker được ghi nhận trung thực là **`ENVIRONMENT_BLOCKED`** (không đánh nhãn `PASS`).

---

## D. Step Editor End-to-End Root-Cause Trace

Đã truy vết đầy đủ chuỗi **Edit Request -> Validation -> Dependency Analysis -> Rebuild -> Semantic Events -> Scene3D -> Persistence -> Frontend State** qua cả `pytest` (`test_owner_scope_resolution.py`), `vitest` (`construction-step-editor.test.tsx` gồm `OSR-SCENE3D-CONSISTENCY`) và trình duyệt thật trên `:3001`/`:8000` + PostgreSQL 16 ([browser-responsive-results.json](results/browser-responsive-results.json)):

1. **Rename & Retarget (`chop-mat-cau-ngoai-tiep`, `mp_tt_AB` `(α)`/`AB` -> `(P)`/`SB`):**
   - `execute_step_edit` / `POST /api/simulation/steps/edit` trả `200` (`committed_version=1`): `M_AB = ["2","0","2"]`, `I = ["2","2","2"]`, `R = "2√3"`, `V_cau = "32π√3"`, sự kiện `truc_day` cập nhật thành `"Dựng giao tuyến của (P) và (β)."`.
   - **0** ký tự `(α)` còn sót trong toàn bộ `objects`, `events`, `formation.steps` của `Scene3D`, và trên tất cả các bước dựng hiển thị ở UI dock/step narration.
2. **Đổi mặt cắt & lặp lại + Lan truyền ngược dòng (`chop-thiet-dien-ba-diem`):**
   - Đổi `(MNP)` -> `(Q)` qua `M, B, P`: `thiet_dien` thành `"Thiết diện MBPF"`, `S_td = "4√109/3"`.
   - Sửa lặp lại sang `S, A, C`: suy biến hợp lệ tại đỉnh `E = F = ["0","0","6"]`, `"Thiết diện ACS"`, `S_td = "12√2"`.
   - Sửa tỷ lệ thượng nguồn `M` trên `SA` (`1/3` -> `["0","0","4"]`, `1/4` -> `["0","0","9/2"]`): đồ thị phụ thuộc cập nhật đồng bộ xuống `mp_MNP`, `thiet_dien`, `S_td`.
3. **Từ chối Fail-Closed (`422`) & Giữ nguyên bản nháp:**
   - Cạnh `SZ` không tồn tại -> `422 MISSING_DEPENDENCY`.
   - Ba điểm thẳng hàng `A, O, C` -> `422 COLLINEAR_POINTS`.
   - Cú pháp ngoài miền (`"Vẽ parabol bất kỳ qua M."`) -> `422 UNSUPPORTED_STEP_SYNTAX`.
   - Cả 3 ca đều giữ nguyên text đang gõ trên `.step-edit-textarea`, không tăng `committed_version`.
4. **Xung đột & Khôi phục qua Restart (`409` & `latest_client_seq`):**
   - `expected_committed_version` cũ -> `409 STALE_REVISION_CONFLICT`.
   - `client_seq` thấp hơn mức server đã ghi -> `409 EDIT_SUPERSEDED`.
   - Khởi động lại hoàn toàn backend Uvicorn `:8000` (`task-6864`) và mở browser context mới **không có** `axo:step-edit-seq:v1` trong `localStorage`: frontend đọc `GET /api/simulation/sessions/{sid}/state` (`committed_version=15`, `latest_client_seq=20`, `M=["0","0","9/2"]`) và commit tiếp thành công `v15 -> v16` (`HTTP 200`).
5. **Bất biến Camera Scene3D:**
   - Khi chưa orbit: độ dịch đỉnh `S, B, C, D` sau rebuild là **`0.0 px`**.
   - Khi người dùng đã orbit + zoom: sau khi sửa `SB -> SC`, sai lệch vị trí camera Three.js = **`0`**, mục tiêu = **`0`**.

---

## E. Host, Responsive & Browser Evidence (`:3001` / `:8000`)

- **Option B Scope Audit (`accept-product-scope.mjs`):** `48/48` checks PASS tại đúng commit cuối `892e15f06fc53c623a1392f0766d69c21291436a` (`sourceFingerprint=eda6ced6c56f0827`, `dirty=false`), kiểm tra `/`, `/app`, `/simulation/chop-mat-cau-ngoai-tiep` trên `1920x1080`, `1366x768`, `390x844`, 0 lỗi console/page, `/api/classes` & `/api/assignments` trả `404`. Artifact: [product-scope-acceptance.json](results/product-scope-acceptance.json).
- **Retired Classroom CLI (`accept-live-classroom.mjs --json`):** exit `2` (`CLASSROOM_FEATURE_RETIRED`), không sửa DB hay docs ([accept-live-classroom-retired.json](results/accept-live-classroom-retired.json)).
- **Kiểm tra Responsive 6 Viewport + VKB (`390x460`):** toàn bộ đều có `overflowX = 0`, `webglPhase = "healthy"`, `clippedLabels = []`, `occludedSceneControls = []`, nút `Hủy`/`Chạy` và ô nhập luôn nằm gọn trong khung nhìn kể cả khi bàn phím ảo mobile mở ở `390x460`.
- **REA MCP (`cdp_endpoint=http://127.0.0.1:9342`):** kiểm tra `target_id=1A80CDFA8A20AB78979326C82B871E8F`, thu artifact `inspect_web_page` (`ev_f9407fd49ddd75c06ca33e1983d5e8dbc38716a80cb6bdc7c1679354e72e3686`) và ảnh chụp `osr-rea-mcp.png` (`150,127` bytes, `ev_7586d28dc26545d1f8f88b3c8efb1043c1ad29b8c86fc2c8dc9b18fad5f71a45`, [rea-mcp-verification.json](results/rea-mcp-verification.json)).

| Kịch bản / Viewport | Ảnh chụp xác minh |
| --- | --- |
| Trước khi sửa (`(α)` / `AB`) | [osr-1920-before-edit.png](images/osr-1920-before-edit.png) |
| Sau khi sửa `(α)->(P)` & `AB->SB` (`0` `(α)`) | [osr-1920-sb-rename-P.png](images/osr-1920-sb-rename-P.png) |
| Bắt lỗi `422` & giữ bản nháp (`SZ`) | [osr-1920-422-rollback.png](images/osr-1920-422-rollback.png) |
| `F5` & Cascade trên `chop-thiet-dien-ba-diem` | [osr-1920-cascade-f5.png](images/osr-1920-cascade-f5.png) |
| Sau restart `:8000` (`v15 -> v16`) | [osr-post-restart.png](images/osr-post-restart.png) |
| Landing `/` & Workspace `/app` | [osr-landing-1920.png](images/osr-landing-1920.png) · [osr-workspace-app-1920.png](images/osr-workspace-app-1920.png) |
| Viewport `1920x1080` / `1440x900` / `1366x768` | [osr-vp-1920x1080.png](images/osr-vp-1920x1080.png) · [osr-vp-1440x900.png](images/osr-vp-1440x900.png) · [osr-vp-1366x768.png](images/osr-vp-1366x768.png) |
| Tablet `768x1024`, Mobile `390x844`, `320x568`, VKB `390x460` | [osr-vp-768x1024.png](images/osr-vp-768x1024.png) · [osr-vp-390x844.png](images/osr-vp-390x844.png) · [osr-vp-320x568.png](images/osr-vp-320x568.png) · [osr-vkb-390x460.png](images/osr-vkb-390x460.png) |
| REA MCP CDP Capture (`1440x900`) | [osr-rea-mcp.png](images/osr-rea-mcp.png) |

---

## F. Performance & Memory Stability Summary

Nguồn số liệu: [performance-and-memory.json](results/performance-and-memory.json).

| Phép đo | p50 | p95 | max | Ghi chú |
| --- | ---: | ---: | ---: | --- |
| Cold Subprocess 1st Edit (`N=3`, S11) | 29.390 ms | 30.393 ms | 30.504 ms | `import_ms` ~617–673 ms |
| Warm Kernel Engine (`N=120`, S11 `(α)->(P)`) | 10.869 ms | 13.216 ms | 34.317 ms | `gc.disable()`, 0 regression |
| Warm Kernel Engine (`N=120`, S1 `SM/SA=1/4`) | 12.751 ms | 15.527 ms | 30.527 ms | `gc.disable()`, 0 regression |
| Live HTTP + PG16 Commit `200` (`N=30`) | 56.270 ms | 89.098 ms | 121.802 ms | PG commit `p50=8.425 ms` |
| Live HTTP + PG16 Refusal `422` (`N=15`) | 30.690 ms | 38.492 ms | 41.186 ms | Fail-closed không ghi session |
| Live HTTP + PG16 Conflict `409` (`N=15`) | 19.463 ms | 24.716 ms | 26.123 ms | Chặn `client_seq` cũ |
| Live HTTP + PG16 `GET /state` Recovery (`N=15`) | 14.876 ms | 33.665 ms | 40.608 ms | Khôi phục + đồng bộ `seq` |
| Frontend Mở Editor (`N=15`, Playwright) | 22.862 ms | 38.560 ms | 50.800 ms | — |
| Frontend Scene3D Render Sau Commit (`N=15`) | 32.000 ms | 50.110 ms | 53.400 ms | Telemetry `__AXO_LAST_STEP_EDIT_METRICS__` |
| Frontend E2E Edit -> Render Hoàn Tất (`N=15`) | 196.833 ms | 255.098 ms | 263.593 ms | Bao gồm HTTP RTT + rAF |
| Frontend Stress 50 Chu Kỳ Liên Tiếp | 207.17 ms | 257.01 ms | 348.18 ms | — |

- **Python `tracemalloc` 50 chu kỳ (`execute_step_edit`):** biến thiên giữ lại sau `gc.collect()` là **`+0.80 KB`** (`current_traced=0.69 KB`, `peak=694.04 KB`).
- **Chromium JS Heap & DOM 50 chu kỳ sửa liên tiếp:** `28.287 MB -> 33.788 MB` (`+5.501 MB`), `nodeDelta = -12` DOM nodes (`717 -> 705`), `canvasCountAfter = 1` (không rò rỉ WebGL context).

---

## G. Full Test & Verification Matrix (Sequential, Zero Overlap)

Nguồn manifest: [gates-manifest.json](gates-manifest.json).

| # | Hạng mục kiểm định | Lệnh chạy thực tế | Kết quả | Exit |
| --- | --- | --- | --- | ---: |
| 1 | Candidate Seal | `python -X utf8 scripts/freeze_evaluation_candidate.py --verify` | `109` files (`78edfa1784625e9b...`) PASS | `0` |
| 2 | Offline Safety / Risk / Owner-Scope | `pytest -q tests/test_database_safety_closure.py tests/test_migration_drift.py tests/test_pre_merge_release_acceptance.py tests/test_pre_merge_risk_closure.py tests/test_owner_scope_resolution.py tests/test_auth_api.py -k "not postgres"` | `52 passed, 4 deselected` (`108.83s`) | `0` |
| 3 | PostgreSQL 16 Suite | `pytest -q -m postgres` (`algosim_osr_pytest`) | `8 passed, 14026 deselected` (`153.92s`) | `0` |
| 4 | Semantic Program | `pytest -q tests/semantic_program` | `1192 passed, 1 skipped` (`65.83s`) | `0` |
| 5 | Root Tests Offline | `pytest -q tests/test_*.py -k "not postgres"` | `815 passed, 8 deselected` (`261.93s`) | `0` |
| 6 | Geometry Kernel Suite | `pytest -q tests/geometry` | `12000 passed, 6 skipped, 3 deselected, 9 xfailed` (`402.38s`) | `0` |
| 7 | TypeScript Build Check | `npx tsc -b` | `0` errors | `0` |
| 8 | Production Vite Bundle | `npm run build` | `built in 4.65s` | `0` |
| 9 | Frontend Full Vitest | `npx vitest run` | `193 files passed, 2278 passed` (`119.62s`) | `0` |
| 10 | Docs Information Architecture | `python -X utf8 backend/scripts/audit_docs_information_architecture.py` | PASS (`0` broken, `0` stale, `0` secrets) | `0` |
| 11 | Product Scope Guard (`Option B`) | `node scripts/accept-product-scope.mjs --base http://localhost:3001 --out ...` | `48/48` PASS (`FRESH` tại `892e15f06`) | `0` |
| 12 | Retired Classroom CLI Guard | `node scripts/accept-live-classroom.mjs --json` | `CLASSROOM_FEATURE_RETIRED` | `2` |
| 13 | Browser E2E + Restart + REA MCP | `run-osr-browser.mjs phase1/phase2` + REA CDP `:9342` | All PASS (`0` console/page/5xx errors) | `0` |
| 14 | PG16 Backup/Restore & `bb046fa22` Rollback | `osr_pg_backup_restore_rollback.py` | 20 tables 100% parity + Modes A/B1/B2 PASS | `0` |
| 15 | Linux Container / Docker Gate | `docker version` / `docker info` | `com.docker.service Stopped` (`ENVIRONMENT_BLOCKED`) | `1` |

*(Ghi chú minh bạch: `browser-responsive-results.json` và `performance-and-memory.json` đo tại commit `6880a03eb`; sau đó chỉ sửa kiểu TypeScript trong `frontend/src/components/construction-step-editor.test.tsx` ở commit `892e15f06` mà không đổi một dòng mã sản phẩm nào trong `MEASURED_SYSTEM_PATHS`, đồng thời toàn bộ 10 cổng §6 và `accept-product-scope.mjs` đều chạy lại trên `892e15f06`.)*

---

## H. Final Owner Checklist Before Merge to `main`

1. **Xác nhận quyết định `C-Classroom = Option B`:** Đã triển khai và nghiệm thu hoàn tất (không còn HTTP/UI lớp học ở V1, 5 bảng DB lịch sử an toàn).
2. **Owner phê duyệt `C-Landing` (`PENDING_OWNER_DECISION`):** Duyệt việc đưa `/` -> `LandingView` và `/app` -> Workspace lên `main`.
3. **Owner phê duyệt `C-Workspace` (`PENDING_OWNER_DECISION`):** Duyệt gói đại tu Workspace/Composer/Scene3D đi cùng Step Editor V1.
4. **Owner quyết định `C-Release` (`PENDING_OWNER_DECISION`):** Quyết định có chạy lại Linux container gate (`Docker`) trên CI/host có quyền khởi động daemon hay không trước khi cho phép thao tác merge vào `main` và deploy production.
