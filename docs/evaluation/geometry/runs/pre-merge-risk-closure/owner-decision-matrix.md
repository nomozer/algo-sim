# AXO — OWNER DECISION MATRIX (PRE-MERGE SCOPE GATE P0 §8)

- **Branch:** `audit/axo-pre-merge-risk-closure`
- **Final Sealed Commit:** `dbfbcf31256b60f076d8ff4464aac9223a213f09` (`product_commit_sha = 600f5105d4222cd6835cc916b34d5cb3f11610e6`)
- **Measured System Tree Hash:** `78edfa1784625e9bca8f1a4cd70b60359d198ba77530986903175a57e18206a7` (`109` files)
- **Baseline `main`:** `bb046fa22aceff47abe22aa783aa64fc65caee13` (`130` commits ahead, `732` files changed, `0` merge conflicts)
- **Gate Status:** `BLOCKED_OWNERSHIP` — **Mọi quyết định dưới đây giữ `PENDING_OWNER_DECISION` cho đến khi Owner duyệt tường minh; agent không tự phê duyệt.**

---

## Quyết Định 1: Chuyển Route Mặc Định `/` Sang LandingView & Di Chuyển Workspace Sang `/app`

- **(1) Summary of change:**
  Trên `main` (`bb046fa22`), `/` mở thẳng vào Workspace mô phỏng. Trên release candidate (`dbfbcf312`), route `/` phục vụ `LandingView` (giới thiệu sản phẩm, hero 3D tương tác, CTA mở mô phỏng), trong khi toàn bộ Workspace học tập/mô phỏng được phục vụ tại `/app`, `/simulation/:id`, và `/workspace` (`history.ts`, `App.tsx`, `LandingView.tsx`).
- **(2) Commits / Key files:**
  - [App.tsx](../../../../../frontend/src/App.tsx)
  - [LandingView.tsx](../../../../../frontend/src/components/LandingView.tsx)
  - [history.ts](../../../../../frontend/src/state/history.ts)
  - Landing components & tests dưới `frontend/src/components/landing/` và `frontend/src/components/__tests__/landing-*.test.tsx` (chuỗi commit Landing V1.4–V1.8 trước `aa860d7de`).
- **(3) User / Learner / Teacher impact:**
  - Người dùng mới vào `/` nhìn thấy trang Landing giới thiệu Axo thay vì giao diện dựng hình ngay lập tức.
  - Người dùng quen bookmark `/` sẽ cần bấm CTA vào `/app` hoặc dùng bookmark `/app`, `/simulation/:id`. Deep link `/simulation/<slug>` và `/app` hoạt động trực tiếp (`HTTP 200`, `0` console error).
- **(4) API Contract impact:**
  - Không thay đổi endpoint backend `/api/*`; chỉ thay đổi định tuyến SPA phía client (`/`, `/app`, `/simulation/:id`).
- **(5) Database impact:**
  - Không tác động schema DB hay phiên `step_edit_sessions` (`localStorage` `axo:client-session-id:v1` giữ nguyên qua điều hướng SPA `/` ↔ `/app`).
- **(6) Rollback impact:**
  - Nếu cần hoàn nguyên hành vi cũ, chỉ cần trỏ route `/` lại Workspace trong [App.tsx](../../../../../frontend/src/App.tsx) / [history.ts](../../../../../frontend/src/state/history.ts) hoặc rollback Git về `bb046fa22`; không ảnh hưởng DB hay Step Editor.
- **(7) Risks if merged:**
  - Người dùng hiện hữu đang bookmark `/` có thể bất ngờ vì gặp Landing trước khi bấm vào `/app`; tuy nhiên CTA và navigation chuyển vào `/app` / `/simulation/*` không cần tải lại trang.
- **(8) Risks if deferred / separated:**
  - Tách riêng cụm Landing khỏi nhánh RC `130` commits khá sạch về mặt code nếu cần merge riêng Step Editor + Hybrid, nhưng phải kiểm chứng lại routing test & bundle build cho cấu hình tách nhánh.
- **(9) Technical recommendation:** **`RECOMMENDED`** (Giữ nguyên mô hình `/` → `LandingView`, `/app` → Workspace nếu Owner đã thống nhất đưa Landing V1 cùng đợt Step Editor V1; thêm banner/redirect hoặc tách PR riêng chỉ khi Owner muốn giữ `/` là Workspace trực tiếp).
- **(10) Owner approval status:** **`PENDING_OWNER_DECISION`**

---

## Quyết Định 2: Gỡ 18 HTTP Endpoint Classroom / Live Session (Giữ Nguyên 5 Bảng Legacy Trong DB)

- **(1) Summary of change:**
  So với `main` (`bb046fa22`), candidate đã xóa `classroom_router.py` (`5` routes), `session_router.py` (`7` routes) và bỏ `6` route `/api/classes*` trong `accounts/router.py` — tổng cộng **`18` HTTP endpoints** bị gỡ (`404 Not Found` trên RC), đồng thời loại bỏ UI/state Classroom tương ứng ở frontend. Bù lại, migration `f8a2c41d9e05` giữ nguyên toàn bộ **`5` bảng legacy Classroom** (`assignments`, `class_memberships`, `classroom_sessions`, `classrooms`, `practice_sessions`) không DROP để không mất dữ liệu lịch sử. Ma trận đầy đủ xem tại [classroom-api-impact-matrix.json](classroom-api-impact-matrix.json).
- **(2) Commits / Key files:**
  - Deleted: `backend/app/accounts/classroom_router.py`, `backend/app/accounts/session_router.py`, `backend/tests/test_classroom_api.py`.
  - Modified: [accounts/router.py](../../../../../backend/app/accounts/router.py), [accounts/service.py](../../../../../backend/app/accounts/service.py), [accounts/policy.py](../../../../../backend/app/accounts/policy.py), [classroom_models.py](../../../../../backend/app/persistence/classroom_models.py), [seed_classroom_fixture.py](../../../../../backend/scripts/seed_classroom_fixture.py), [f8a2c41d9e05](../../../../../backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py).
  - Evidence: [classroom-api-impact-matrix.json](classroom-api-impact-matrix.json) (`18` endpoints + danh sách consumer).
- **(3) User / Learner / Teacher impact:**
  - **Option A (Khôi phục Classroom/Live Session routers trước khi merge):** Giáo viên và học sinh tiếp tục dùng được luồng tạo lớp (`/api/classes`), giao bài (`/api/assignments`), theo dõi trực tiếp (`/api/classes/{id}/session`, `/monitor`, `/help`). Không gây gián đoạn quy trình lớp học cũ.
  - **Option B (Chính thức ngừng tính năng Classroom HTTP trên V1 & lưu giữ DB):** Học sinh cá nhân/tự học dùng Step Editor + Mô phỏng 3D bình thường (frontend RC đã bỏ hoàn toàn mọi lời gọi Classroom); giáo viên/script ngoài gọi 18 route Classroom sẽ nhận `404`.
- **(4) API Contract impact:**
  - **Breaking Change:** `18` HTTP routes chuyển từ active trên `main` sang `404 Not Found` trên RC (`6` routes `/api/classes*`, `5` routes `/api/assignments*` & `/observe`, `7` routes `/session*` & `/help*` & `/monitor`). `0` caller Classroom còn lại trong `frontend/src/` của RC.
- **(5) Database impact:**
  - Không mất dữ liệu ở cả 2 phương án nếu nâng cấp đúng quy trình: `5` bảng Classroom legacy (`46` users / `66` rows trong DB gốc `algo-sim\backend\algosim.db`) được giữ nguyên 100% khi đi từ `e437149641fa -> f8a2c41d9e05`. Schema state `20` bảng (giữ 5 bảng legacy) và `15` bảng (core-only) đều hợp lệ tại `f8a2c41d9e05`.
- **(6) Rollback impact:**
  - Vì dữ liệu 5 bảng DB không bị xóa, cả sau khi chọn Option B vẫn có thể rollback code về `main` (`bb046fa22`) hoặc khôi phục router trên DB `20` bảng mà toàn bộ lớp học & phiên thực hành cũ còn nguyên vẹn (`100%` SHA-256 parity đã chứng minh ở Gate B3).
- **(7) Risks if merged:**
  - Nếu merge theo Option B mà chưa thông báo/chưa có đồng ý của Owner: bất kỳ giáo viên hoặc script tích hợp nào gọi `/api/classes/*`, `/api/assignments/*`, `/api/classes/*/session*` sẽ lỗi `404`.
- **(8) Risks if deferred / separated:**
  - Nếu chọn Option A (khôi phục lại router Classroom trước merge), cần khôi phục ORM mappings (`classroom_models.py`) + router + frontend views (hoặc backend API compat) và chạy lại toàn bộ test Classroom cùng Step Editor trước khi merge.
- **(9) Technical recommendation:** **`RECOMMENDED` — BẮT BUỘC LỰA CHỌN TƯỜNG MINH TỪ OWNER GIỮA OPTION A VÀ OPTION B** (Về mặt kỹ thuật thuần túy, **Option B — Ngừng chính thức Classroom HTTP API cho đợt phát hành Step Editor V1 kèm giữ nguyên 5 bảng DB legacy + thông báo/export runbook** giúp giữ bề mặt phát hành gọn, an toàn dữ liệu và có thể bật lại bất cứ lúc nào vì 5 bảng DB vẫn nguyên; **Option A** chỉ nên chọn nếu production hiện đang phục vụ tính năng Classroom/Live Session hoạt động).
- **(10) Owner approval status:** **`PENDING_OWNER_DECISION`**

---

## Quyết Định 3: Nâng Cấp Workspace / Attachment UI & Đóng Băng `CACHE_VERSION = 132`

- **(1) Summary of change:**
  Cập nhật đồng bộ giao diện Workspace v6.2 (`SimulationWorkspace.tsx`, `DockPanel`, `AxoScrollbar`, `PdfPreview`, đính kèm ảnh/PDF), đồng bộ Hybrid `/4` metadata/narration/continuity, Step Editor V1 + 3 bản sửa lỗi gốc mới trong chiến dịch này (`014a2fd24`, `3f3afb25b`, `600f5105d`), và tăng `CACHE_VERSION = 132` (`EVALUATION_CANDIDATE.json` niêm phong `109` file mã sản phẩm, `tree_hash = 78edfa1784625e9bca8f1a4cd70b60359d198ba77530986903175a57e18206a7`).
- **(2) Commits / Key files:**
  - [SimulationWorkspace.tsx](../../../../../frontend/src/components/SimulationWorkspace.tsx), [scene3d-view.tsx](../../../../../frontend/src/simulations/domains/geometry/scene3d-view.tsx), [construction-step-edits.ts](../../../../../frontend/src/state/construction-step-edits.ts)
  - [step_editor.py](../../../../../backend/app/simulation/geometry_functions/step_editor.py), [step_edit_router.py](../../../../../backend/app/simulation/step_edit_router.py)
  - [main.py](../../../../../backend/app/main.py) (`CACHE_VERSION = 132`), [EVALUATION_CANDIDATE.json](../../../semantic-benchmark/EVALUATION_CANDIDATE.json)
- **(3) User / Learner / Teacher impact:**
  - Học sinh có thể chỉnh sửa trực tiếp bước dựng tiếng Việt, xem Scene3D cập nhật đúng toán học `Fraction`/`Radical` mà **không nhảy camera** (`maxDeltaPx = 0`), và giữ nguyên tiến độ qua `F5`, chuyển tab, đổi thiết bị/ngữ cảnh (`latest_client_seq` sync) hoặc restart backend.
- **(4) API Contract impact:**
  - Thêm cụm `/api/simulation/steps/edit`, `/api/simulation/steps/cancel`, `/api/simulation/sessions/{session_id}/state`, `/api/simulation/feedback/*`. Mở rộng thêm field `latest_client_seq` ở `GET /state` & `409 EDIT_SUPERSEDED` (backward-compatible).
- **(5) Database impact:**
  - Bổ sung 3 bảng Step Editor (`step_edit_sessions`, `step_edit_revisions`, `step_edit_feedback`) tại revision `9c4d8e2b7a10` + retain-only `f8a2c41d9e05`.
- **(6) Rollback impact:**
  - Rollback an toàn bằng `git revert` hoặc quay về `bb046fa22` mà 3 bảng Step Editor không cản trở code `main` (đã chứng minh trong Gate B3). `CACHE_VERSION = 132` làm cache phân tích cũ (`v < 132`) tự động miss và tính lại bằng pipeline hiện hành thay vì đọc cache sai schema.
- **(7) Risks if merged:**
  - Đổi `CACHE_VERSION` lên `132` khiến cache `/api/analyze` cũ (nếu có) không được dùng lại -> các câu hỏi mới qua Gemini live tốn quota/latency lần đầu sau cutover.
- **(8) Risks if deferred / separated:**
  - Nếu trì hoãn, Step Editor V1 cùng 3 bản vá camera/concurrency/preflight chưa thể lên `main`.
- **(9) Technical recommendation:** **`RECOMMENDED`** (Chấp nhận gộp cùng Step Editor V1; toàn bộ test, seal `dbfbcf312`, live PG16 & trình duyệt responsive đã PASS).
- **(10) Owner approval status:** **`PENDING_OWNER_DECISION`**

---

## Quyết Định 4: Runbook Di Trú Legacy DB (`alembic stamp -> upgrade head`) & Ràng Buộc Runtime Đơn Worker (`uvicorn --workers 1`)

- **(1) Summary of change:**
  1. Các DB SQLite/PG legacy chưa có bảng `alembic_version` (như `D:\Documents\projects\algo-sim\backend\algosim.db` với 46 users / 66 rows Classroom) **bị chặn fail-closed** bởi `migration_preflight.py --startup` (exit code `23`, `UNSTAMPED_EXISTING_DATABASE`), buộc vận hành viên dùng quy trình backup -> kiểm parity -> `alembic stamp e437149641fa` -> `alembic upgrade head` (đã cứng hóa kiểm parity online trong `env.py` tại commit `014a2fd24`).
  2. API Step Editor V1 giữ lock/seq/cancel fast-path theo tiến trình trong bộ nhớ (`_SESSION_LOCKS`, `_CANCELLED_REQUESTS`, `_LATEST_CLIENT_SEQ`, `_LAST_COMMIT_SNAPSHOT`) kết hợp `SELECT ... FOR UPDATE` trên PG16, và fail-closed trả `503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` nếu cấu hình multi-worker (`WEB_CONCURRENCY > 1`, `UVICORN_WORKERS > 1`, `GUNICORN_CMD_ARGS --workers > 1`).
- **(2) Commits / Key files:**
  - [migration_preflight.py](../../../../../backend/alembic/migration_preflight.py), [env.py](../../../../../backend/alembic/env.py) (commit `014a2fd24`)
  - [step_edit_router.py](../../../../../backend/app/simulation/step_edit_router.py), [Dockerfile](../../../../../backend/Dockerfile) (`--workers 1`)
  - Evidence: [migration-safety-results.json](migration-safety-results.json), [single-worker-concurrency-results.json](single-worker-concurrency-results.json)
- **(3) User / Learner / Teacher impact:**
  - Không ảnh hưởng trải nghiệm người dùng cuối ở tải V1 (`20` phiên đồng thời / `60` commits chạy song song trên 1 worker PG16: `0` lỗi `5xx`, `0` lost updates, health ping `/api/auth/me` đạt `p50 = 16.313 ms` ở `100% 200 OK`). Tuy nhiên hệ thống không scale ngang multi-worker cho `/api/simulation/steps/*` trong V1.
- **(4) API Contract impact:**
  - Khi chạy sai cấu hình multi-worker, `/api/simulation/steps/*` chủ động trả `503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` thay vì tạo race condition mất đồng bộ.
- **(5) Database impact:**
  - Đảm bảo 0 DDL phá hủy lúc khởi động; chặn `alembic stamp` sai phiên bản (`INVALID_STAMP_SCHEMA_MISMATCH`), chặn drift bảng/cột lạ (`SCHEMA_DRIFT_DETECTED`), và chặn giữ bảng Classroom bán phần (`1..4` trên `5` bảng).
- **(6) Rollback impact:**
  - Runbook nâng cấp DB bảo toàn 100% bảng/dòng cũ nên rollback code về `main` an toàn. Nếu V2 muốn scale multi-worker, cần chuyển `_CANCELLED_REQUESTS` & distributed per-session lock sang Redis/PostgreSQL advisory lock + bảng transient trạng thái request.
- **(7) Risks if merged:**
  - Nếu team vận hành triển khai Docker/systemd mà đặt `UVICORN_WORKERS=4` hoặc `WEB_CONCURRENCY=2`, toàn bộ tính năng Step Editor sẽ từ chối `503` ngay để bảo vệ dữ liệu. Cần tuân thủ bắt buộc `--workers 1` trong runbook V1.
- **(8) Risks if deferred / separated:**
  - Không thể tách `workers=1` khỏi Step Editor V1 vì đó là bất biến an toàn concurrency hiện tại; mọi nâng cấp multi-worker thuộc phạm vi V2.
- **(9) Technical recommendation:** **`RECOMMENDED`** (Phê duyệt áp dụng kèm Runbook vận hành V1 bắt buộc `--workers 1` và quy trình `backup -> alembic stamp e437149641fa -> upgrade head` cho DB legacy; lên kế hoạch V2 chuyển cancel/lock state sang store chia sẻ nếu cần scale ngang).
- **(10) Owner approval status:** **`PENDING_OWNER_DECISION`**
