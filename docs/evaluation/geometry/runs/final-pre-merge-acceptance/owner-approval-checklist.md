# Owner Approval Checklist — AXO Final Pre-Merge Acceptance

- **Nhánh đánh giá:** `release/axo-final-pre-merge-acceptance` (`897d70c9f9a3862ef5dcaa45a3f91ffd326e91ed` + gói nghiệm thu `final-pre-merge-acceptance`)
- **Commit mã & test:** `892e15f06fc53c623a1392f0766d69c21291436a` (`product_commit_sha`: `600f5105d4222cd6835cc916b34d5cb3f11610e6`)
- **Baseline `main`:** `bb046fa22aceff47abe22aa783aa64fc65caee13` (`134` commit phía trước; cây hợp nhất sạch `0` xung đột)
- **Trạng thái cổng kỹ thuật:** Gate A `PASS` · Gate B `PASS` · Gate D `PASS` · Gate E `PASS` · Gate F `PASS` · Gate G `PASS` · Gate C `PENDING_OWNER_DECISION` (`C-Classroom = OPTION_B_IMPLEMENTED_AND_VERIFIED`; `C-Landing` / `C-Workspace` / `C-Release` = `PENDING_OWNER_DECISION`)
- **Quyết định đề xuất:** `READY_FOR_OWNER_APPROVAL`

> Checklist này dành cho Owner điền quyết định cuối cùng. Tự động hóa không tự phê duyệt bất kỳ hạng mục nào.

---

## Hạng mục 1 — `C-Classroom` (27 file — Đã thực thi & Kiểm chứng theo Option B)

- **Hiện trạng kỹ thuật đã xác minh:**
  - Route Classroom / Live Session bị loại khỏi Surface API (`0` route Classroom/Live Session trong OpenAPI; 18 endpoint cũ trả HTTP `404`).
  - Frontend không còn caller active; CLI `accept-live-classroom.mjs --json` trả exit code `2` (`CLASSROOM_FEATURE_RETIRED`).
  - Năm bảng legacy DB (`classrooms`, `class_memberships`, `assignments`, `practice_sessions`, `classroom_sessions`) được **bảo toàn nguyên trạng** qua `f8a2c41d9e05` và kiểm chứng 100% parity qua rollback Gate B xuống `bb046fa22`.
- **Xác nhận Owner cần chốt:**
  - [ ] Chấp thuận giữ nguyên **Option B** (ngưng Classroom runtime API/UI nhưng giữ 5 bảng legacy trong PostgreSQL để phục vụ rollback an toàn).

---

## Hạng mục 2 — `C-Landing` (40 file — Chờ Owner phê duyệt phạm vi)

- **Phạm vi thay đổi so với `main` (`bb046fa22`):** 40 file thuộc `LandingView` / `components/landing/*` / landing CSS & Vitest suites (bao gồm 38 file ở lần kiểm kê trước + 2 file test/component Landing bổ sung trước commit `892e15f0`).
- **Tác động sản phẩm:** Đổi route mặc định `/` từ Workspace trực tiếp sang `LandingView` (CTA điều hướng mượt sang `/app`, `/workspace`, `/library`); không còn thuật ngữ Tin học cũ (`0` legacy informatics hits), không vòng lặp redirect, giữ nguyên auth/guest session và vượt qua 100% Vitest + browser desktop/mobile `1920x1080`–`320x568`.
- **Lựa chọn của Owner:**
  - [ ] **CHẤP THUẬN ĐƯA VÀO (`INCLUDE`)** cùng Step Editor vào `main`.
  - [ ] **TỪ CHỐI / TÁCH RIÊNG (`EXCLUDE`)** (khôi phục `/` về Workspace trước khi merge Step Editor).

---

## Hạng mục 3 — `C-Workspace` (119 file — Chờ Owner phê duyệt phạm vi)

- **Phạm vi thay đổi so với `main` (`bb046fa22`):** 119 file thuộc `SimulationWorkspace.tsx`, `LeftSidebar.tsx`, `WorkspaceTabBar.tsx`, `HomeView.tsx`, `scene3d-view.tsx`, CSS & test Workspace/Scene3D (kết nối trực tiếp `StepEditPencilButton` & `InlineConstructionStepEditor`, pooling 1 `WebGLRenderer`, camera pose invariance, docking & responsive mobile VKB).
- **Lựa chọn của Owner:**
  - [ ] **CHẤP THUẬN ĐƯA VÀO (`INCLUDE`)** cùng Step Editor (khuyến nghị kỹ thuật vì `SimulationWorkspace.tsx` là host trực tiếp của Step Editor & bất biến camera Scene3D).
  - [ ] **TÁCH RIÊNG (`DEFER_AND_EXTRACT`)** (yêu cầu tách tối giản Step Editor ra khỏi các nâng cấp Workspace còn lại).

---

## Hạng mục 4 — `C-Release` (Merge `main`, Push & Backup Trước Merge)

- **Điều kiện tiên quyết đã đạt:**
  - Isolated merge simulation: `is-ancestor = true`, `merge-tree` khớp `HEAD_TREE` (`7d0b96e4c51655af23dbb7ae0b07be4e860c92ff`), `--ff-only` exit `0`, `--no-ff --no-commit` exit `0` (`0` xung đột).
  - Docker container build (`algosim-backend:fpa-gate`) + startup preflight (`f8a2c41d9e05`) + `pg_dump -Fc` / `pg_restore` `PASS`.
  - Backup PostgreSQL 16 (`pg16_fpa_src.snapshot.tar.gz`) & rollback về `bb046fa22` (Mode A, B1, B2) `PASS`.
- **Quyết định của Owner về phát hành:**
  - [ ] Cho phép merge nhánh sạch vào `main` theo hình thức: `[ ] --ff-only` hoặc `[ ] --no-ff`.
  - [ ] Cho phép push `origin/main` sau khi test post-merge trên `main` xanh.
  - [ ] Xác nhận chụp bản sao lưu `pg_dump -Fc` trước khi chạy `alembic upgrade head` trên PostgreSQL đích theo SOP:
    1. Backup DB hiện hành (`pg_dump -Fc ...`) và xác minh sha256.
    2. Chạy `python alembic/migration_preflight.py --startup --json` -> bắt buộc `SAFE_NO_DESTRUCTIVE_OPERATIONS`.
    3. Chạy `alembic upgrade head` -> `f8a2c41d9e05` + `alembic check`.
    4. Khởi động backend đơn worker (`--workers 1` trong `Dockerfile`) và kiểm tra `/api/health` (`git_sha`, `db=postgresql`, `cache_version=132`).
- **Lưu ý giới hạn hiện hành:** `MODEL_STATUS = MODEL_NOT_TRAINED` · `PRODUCTION_DEPLOYMENT_VERIFIED = NO` · `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`.
