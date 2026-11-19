# AXO STEP EDITOR — FINAL PRE-MERGE AUDIT, SAFE MAIN INTEGRATION & RELEASE VERIFICATION REPORT

**Ngày kiểm định:** 2026-11-19  
**Nhánh được kiểm định:** `feat/axo-geometry-library-verification`  
**Release Candidate / Audited HEAD:** `27f2c98d2a0f7e9cbe4de8d23837db29e86f0aea` (mã sản phẩm) · `fdf3e5e79d907c533da50cb4dca56bd48069cde1` (HEAD trước audit)  
**Main & Origin/Main:** `bb046fa22aceff47abe22aa783aa64fc65caee13` (không đổi, chưa merge, chưa push)

---

## 1. Executive Verdict

- **RELEASE_DECISION:** `NOT_READY_FOR_MAIN_INTEGRATION`
- **RELEASE_GATE:** `BLOCKED_DATABASE_SAFETY`
- **MERGE_STATUS:** `NOT_MERGED`
- **PUSH_STATUS:** `NOT_PUSHED`
- **MODEL_STATUS:** `MODEL_NOT_TRAINED`

**Kết luận điều hành:** Toàn bộ logic hình học chính xác (`Fraction`/`Radical`) của **AXO Step Editor**, cây phụ thuộc, rollback HTTP `422`/`409`, lưu bền PostgreSQL `16.6` qua restart server, toàn bộ bộ test Frontend (`2.274` tests) và Backend (`13.985` default + `4` Postgres tests), cùng kiểm thử trình duyệt trực tiếp Playwright/REA MCP **đều PASS** trên mã nguồn ứng viên. Tuy nhiên, **cổng phát hành bị chặn cứng tại Giai đoạn E (`BLOCKED_DATABASE_SAFETY`)** do phát hiện hai blocker an toàn dữ liệu và một phát hiện phạm vi governance vượt ngoài giới hạn tích hợp an toàn lên `main`:
1. **`BLOCKER-DB-1` (CRITICAL):** Migration `f8a2c41d9e05` gọi `op.drop_table(...)` vô điều kiện lên 5 bảng Classroom còn dữ liệu sống (66 bản ghi trên `D:\Documents\projects\algo-sim\backend\algosim.db`), `downgrade()` chỉ tạo lại schema rỗng (`0` dòng), và `backend/Dockerfile:53` tự chạy `alembic upgrade head` ngay khi container khởi động mà không có cổng backup/export/archival.
2. **`BLOCKER-DB-2` (HIGH):** Script vận hành `backend/scripts/seed_classroom_fixture.py` lỗi `ImportError` ngay khi chạy vì các ORM symbol Classroom đã bị xóa trong `bf1ee2a57`.
3. **`GOVERNANCE-SCOPE-1` (HIGH):** Gói 113 commit ahead (`563` file thay đổi so với `main`) gom 34 commit Landing Page (đổi route `/` sang `LandingView`), gỡ bỏ Classroom, Attachment, Workspace tabs/sidebar, thư viện 11 bài Geometry/Scene3D và 17 commit Step Editor thành một khối duy nhất.

Theo nguyên tắc release gate an toàn dữ liệu, quá trình tích hợp đã **DỪNG trước Giai đoạn F/G**: không merge lên `main`, không push `origin/main`, không sửa lịch sử commit đã được kiểm định, và không huấn luyện Model 2.

---

## 2. Trạng thái Git trước và sau

| Mục kiểm tra | Trước audit (đầu phiên) | Sau audit (kết thúc) | Bằng chứng |
| :--- | :--- | :--- | :--- |
| Protected checkout `D:\Documents\projects\algo-sim` | Branch `axo-ui-consistency`, HEAD `bb046fa22aceff47abe22aa783aa64fc65caee13`, chỉ có untracked `?? ocr_reconcile.py` | Giữ nguyên hoàn toàn (`axo-ui-consistency` tại `bb046fa22`, chỉ `?? ocr_reconcile.py`, `ocr_reconcile_in_diff = false`) | [`phase-a-git-preflight-audit.json`](results/phase-a-git-preflight-audit.json) |
| Development worktree `D:\Documents\projects\axo-geometry-library` | `feat/axo-geometry-library-verification` tại `fdf3e5e79d907c533da50cb4dca56bd48069cde1` (clean) | Chỉ thêm commit báo cáo audit trong `docs/evaluation/geometry/runs/step-editor-main-integration-audit/` (clean) | [`git-preflight.log`](logs/git-preflight.log) |
| Clean candidate worktree `.superpowers\worktrees\step-editor-release-candidate` | Detached HEAD `fdf3e5e79d907c533da50cb4dca56bd48069cde1` (clean) | Đồng bộ detached HEAD tới commit báo cáo audit mới trên nhánh feature (clean) | `run.json` |
| Quan hệ `main` vs `feat/axo-geometry-library-verification` | `0` behind, `113` ahead, fast-forwardable = `true`, merge-base `bb046fa22aceff47abe22aa783aa64fc65caee13` | Không merge, không rebase, `main` không đổi | [`phase-a-git-preflight-audit.json`](results/phase-a-git-preflight-audit.json) |
| Trạng thái `origin/main` | `bb046fa22aceff47abe22aa783aa64fc65caee13` (`git fetch origin` = `0`) | Không đổi (`bb046fa22aceff47abe22aa783aa64fc65caee13`) | Kiểm tra post-audit |

---

## 3. SHA chính xác của Release Candidate, local `main` và `origin/main`

- **Clean Release Candidate (code benchmark đã đóng băng):**
  - Commit SHA: `27f2c98d2a0f7e9cbe4de8d23837db29e86f0aea`
  - Tree SHA: `9d3dd5530eb5b75ff8bec0a3f02b6f6894939f1b`
- **Audited Feature HEAD (trước khi ghi báo cáo audit này):**
  - Commit SHA: `fdf3e5e79d907c533da50cb4dca56bd48069cde1`
  - Tree SHA: `1df68d679a6dd2adf439a6132f3754c7c48de6eb`
  - Measured Product Tree Hash (`freeze_evaluation_candidate.py --verify`): `e0ea792d71667f12911fa7b0425bc4761aabdc337ad605491bc06c33137076a4` (`109` file sản phẩm, khớp 100%, xem [`seal-verify.log`](logs/seal-verify.log)).
- **Local `main` (trước và sau):**
  - Commit SHA: `bb046fa22aceff47abe22aa783aa64fc65caee13`
  - Tree SHA: `ce05bcd3a4cc58553117375f9a63a16a9f4388a2`
- **Remote `origin/main` (trước và sau):**
  - Commit SHA: `bb046fa22aceff47abe22aa783aa64fc65caee13`
- **Merge-base (`main` .. `fdf3e5e79`):** `bb046fa22aceff47abe22aa783aa64fc65caee13`

---

## 4. Phân tích Diff và Ownership

- **Diff `27f2c98d2a0f7e9cbe4de8d23837db29e86f0aea..fdf3e5e79d907c533da50cb4dca56bd48069cde1`:** gồm đúng **22 file** báo cáo, ảnh chụp và kết quả đo thêm mới trong `docs/evaluation/geometry/runs/step-editor-independent-acceptance-main-prep/` (`0` thay đổi mã nguồn sản phẩm, migration hay test).
- **Diff `bb046fa22aceff47abe22aa783aa64fc65caee13..fdf3e5e79d907c533da50cb4dca56bd48069cde1`:** tổng **563 file** thay đổi trên **113 commit** ahead (`33` file thuộc Landing Page, `3` file Alembic):

| Nhóm commit | Số commit | Phạm vi & Ownership | Đánh giá rủi ro tích hợp |
| :--- | :---: | :--- | :--- |
| `step_editor` | 17 | Inline Step Editor UI/UX (`IA-RC1..IA-RC3`), parser ngữ nghĩa, partial rebuild, rollback `422`/`409`, feedback persistence | Đã kiểm chứng đầy đủ; đạt chuẩn kỹ thuật |
| `geometry_scene3d_library` | 24 | 11 bài mẫu THPT, Scene3D camera/projection/labels, hiển thị đối tượng phụ | Đã kiểm chứng qua suite + Playwright |
| `workspace_tabs_sidebar` | 14 | Single-instance workspace tabs, sidebar toggle, draft recovery | Đã kiểm chứng qua tab close/reopen |
| `attachment_composer` | 10 | ScreenCaptureDialog, PDF/image preview, attachment inputs | Đã smoke-test route `/app` (`fileInputCount = 3`) |
| `landing_page` | 34 | Đổi root route `/` sang `LandingView` (V1.2–V1.8) + route workspace chuyển sang `/app` | Nằm ngoài mô tả hẹp "Step Editor", cần xác nhận scope release |
| `classroom_retirement` | 1 | `bf1ee2a57` xóa Classroom/Live Session ORM + rebase migration `f8a2c41d9e05` | Chứa `BLOCKER-DB-1` và `BLOCKER-DB-2` |
| `eval_seal_docs_tests` | 13 | Seal candidate, PostgreSQL 16 harness, chuẩn hóa test & báo cáo đánh giá | Phụ trợ kiểm chứng |

Chi tiết danh sách 113 commit được lưu tại [`phase-a-git-preflight-audit.json`](results/phase-a-git-preflight-audit.json).

---

## 5. Migration / Data-Safety Audit

Kiểm định thực nghiệm được thực hiện cô lập trên cơ sở dữ liệu PostgreSQL 16.6 tạm thời `algosim_migration_safety_probe` (đã drop sạch trong khối `finally`), đồng thời kiểm tra runtime khởi động trong [`backend/Dockerfile`](../../../../../backend/Dockerfile) và dữ liệu thực tế trên root checkout ([`phase-b-database-safety-audit.json`](results/phase-b-database-safety-audit.json), [`phase-b-migration-safety.log`](logs/phase-b-migration-safety.log)):

- **Chuỗi Alembic 8 phiên bản:** `72095b7dd318 -> f32f9b107b77 -> a1c7e4b90d52 -> c4e8a91b2f03 -> d5f9b82c3a14 -> e437149641fa -> 9c4d8e2b7a10 -> f8a2c41d9e05`.
- **Kiểm định `e437149641fa -> 9c4d8e2b7a10` (thêm bảng Step Editor):**
  - Tạo 3 bảng `step_edit_sessions`, `step_edit_revisions`, `step_edit_feedback` cùng PK và chỉ mục duy nhất (`uq_step_edit_session_owner_sid`, `uq_step_edit_revision_version`), `0` SQL foreign key bắt buộc chéo bảng cũ.
  - Bảo toàn **100%** dữ liệu đã seed trước nâng cấp: `users: 2, auth_sessions: 1, learning_history_entries: 1, analysis_usage_ledger: 1, simulation_cache: 1, classrooms: 2, class_memberships: 2, assignments: 2, practice_sessions: 2, classroom_sessions: 1`.
- **Kiểm định `9c4d8e2b7a10 -> f8a2c41d9e05` (`remove_classroom_and_live_session_tables`):**
  - `upgrade()` gọi `op.drop_table(...)` **vô điều kiện** trên `classrooms`, `class_memberships`, `assignments`, `practice_sessions`, `classroom_sessions`.
  - Sau đó chạy `alembic downgrade e437149641fa`: chỉ tái tạo 5 bảng với **`0` dòng** (`2->0, 2->0, 2->0, 2->0, 1->0` — **mất dữ liệu không thể khôi phục**).
  - `alembic check` trả mã thoát `0` vì cả SQLAlchemy ORM lẫn migration `head` đều đã bỏ 5 bảng này, chứng minh `alembic check` **không** phát hiện được phá hủy dữ liệu khi xóa đồng thời model và bảng.
- **Tác động sản xuất:** [`backend/Dockerfile`](../../../../../backend/Dockerfile#L53) dòng 53 tự động chạy `alembic upgrade head && ... exec uvicorn app.main:app`, trong khi `D:\Documents\projects\algo-sim\backend\algosim.db` (`413.696` bytes, không có bảng `alembic_version`) đang chứa **66 bản ghi Classroom** (`classrooms: 12`, `class_memberships: 20`, `assignments: 10`, `practice_sessions: 16`, `classroom_sessions: 8`) và `46` bản ghi `users`.
- **Script bị gãy:** `python scripts/seed_classroom_fixture.py` trong [`backend/scripts/seed_classroom_fixture.py`](../../../../../backend/scripts/seed_classroom_fixture.py) thoát mã `1` với `ImportError: cannot import name 'Assignment' from 'app.persistence.classroom_models'`.

---

## 6. Kết quả các bộ test

Tất cả các bộ test được chạy độc lập trên commit `fdf3e5e79d907c533da50cb4dca56bd48069cde1` (bảng chi tiết tại [`phase-d-quality-gates.json`](results/phase-d-quality-gates.json)). Số lượng `skipped`, `xfailed`, `deselected` được báo cáo tách bạch, **không** gộp vào `passed`:

| Hạng mục / Suite | Exit | Passed | Failed | Skipped | XFailed | Deselected | Thời gian / Log |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `freeze_evaluation_candidate.py --verify` | `0` | 109 files | 0 | 0 | 0 | 0 | [`seal-verify.log`](logs/seal-verify.log) |
| Frontend `tsc -b` | `0` | PASS | 0 | — | — | — | [`frontend-tsc.log`](logs/frontend-tsc.log) |
| Frontend `vite build` | `0` | 129 modules | 0 | — | — | — | `5.15s` ([`frontend-vite-build.log`](logs/frontend-vite-build.log)) |
| Frontend `vitest run` | `0` | 2274 tests (192 files) | 0 | 0 | 0 | 0 | `104.24s` ([`frontend-vitest.log`](logs/frontend-vitest.log)) |
| Backend `tests/geometry` | `0` | 12000 | 0 | 6 | 9 | 3 | `451.37s` ([`backend-geometry.log`](logs/backend-geometry.log)) |
| Backend `tests/semantic_program` | `0` | 1192 | 0 | 1 | 0 | 0 | `36.57s` ([`backend-semantic-program.log`](logs/backend-semantic-program.log)) |
| Backend `tests --ignore=geometry --ignore=semantic_program` | `0` | 793 | 0 | 0 | 0 | 2 | `107.56s` ([`backend-other.log`](logs/backend-other.log)) |
| **Tổng Backend mặc định (mặc định `-m "not postgres and not external_evidence"`)** | **`0`** | **13985** | **0** | **7** | **9** | **5** | Tổng cộng `14006` collected |
| Backend Postgres opt-in (`pytest -m postgres -v`) | `0` | 4 | 0 | 0 | 0 | 14002 | `53.39s` ([`backend-postgres.log`](logs/backend-postgres.log)) |
| Migration drift (`test_migration_drift.py`) | `0` | 2 | 0 | 0 | 0 | 0 | `5.85s` ([`backend-migration-drift.log`](logs/backend-migration-drift.log)) |
| 7 Step Editor Acceptance Suites | `0` | 87 | 0 | 0 | 0 | 2 | `25.45s` ([`backend-step-editor-suites.log`](logs/backend-step-editor-suites.log)) |
| `replay_demo_cases.py` | `0` | 5/5 + 1/1 | 0 | 0 | 0 | 0 | [`backend-replay-demo.log`](logs/backend-replay-demo.log) |
| `audit_demo_crash_surface.py` | `0` | 6/6 (`0` HTTP 500) | 0 | 0 | 0 | 0 | [`backend-crash-audit.log`](logs/backend-crash-audit.log) |

**Liệt kê đầy đủ các node `SKIPPED` (7), `XFAIL` (9) và `DESELECTED` (5) theo `pytest -rsx`:**
- **Skipped (7):**
  1. `SKIPPED [2] tests\geometry\test_unified_solid_scope.py:186: A3-DEV-02 has no residual_volume goal`
  2. `SKIPPED [2] tests\geometry\test_unified_solid_scope.py:186: A3-DEV-09 has no residual_volume goal`
  3. `SKIPPED [2] tests\geometry\test_unified_solid_scope.py:186: demo1-pyramid-derived-section has no residual_volume goal`
  4. `SKIPPED [1] tests\semantic_program\test_scalar_obligations.py:95: thiếu term mặc định về identity — đã có test riêng`
- **XFailed (9):**
  1. `tests/geometry/test_generalized_goal_entry.py::test_length_goal_refusal[unread-second-ask]`
  2. `tests/geometry/test_generalized_goal_entry.py::test_length_goal_refusal[contradictory-length]`
  3. `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B27-facts]`
  4. `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B27-pipeline]`
  5. `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B28-facts]`
  6. `tests/geometry/test_hybrid_compiler_benchmark.py::test_case_outcome[B28-pipeline]`
  7. `tests/geometry/test_hybrid_simulation_capability_probes.py::test_centre_label_exhaustion_is_a_coded_outcome`
  8. `tests/geometry/test_premise_source_coverage.py::test_goal_fact_quote_does_not_cover_a_hypothesis[Chứng minh SC vuông góc với BD và đáy là hình chữ nhật.]`
  9. `tests/geometry/test_source_grounding_reliability.py::test_targeted_case_meets_its_preregistered_label[E05-unsupported-second-quantity]`
- **Deselected khỏi suite mặc định (5 node theo [`backend/pytest.ini`](../../../../../backend/pytest.ini)):**
  - `4` Postgres tests (đã chạy riêng trong `pytest -m postgres -v` -> **4 passed**):
    - `tests/geometry/test_step_editor_integration_closure.py::test_step_edit_postgres_migration_handoff_live_container`
    - `tests/geometry/test_step_editor_integration_closure.py::test_postgres_real_step_editor_end_to_end_persistence_restart_and_rollback`
    - `tests/test_postgres_axo_history_migration.py::test_axo_migrations_and_history_api_on_postgres`
    - `tests/test_postgres_integration.py::test_postgres_migrate_persist_reconnect`
  - `1` `external_evidence` test (cần kho evidence ngoài `ALGOSIM_LIVE_RETRY_EVIDENCE_DIR`, chưa chạy offline):
    - `tests/geometry/test_evidence_identity_reconciliation.py::test_raw_response_identity_reproduced`

---

## 7. Root-Cause Regression Evidence (`IA-RC1..IA-RC3`, 5 Họ Hình học & HTTP `422`/`409`)

1. **Xác minh 5 họ bài toán & bất biến toán học chính xác ([`phase-c-geometry-and-pipeline-audit.json`](results/phase-c-geometry-and-pipeline-audit.json)):**
   - **Họ 1 — Chóp & mặt cầu ngoại tiếp (`chop-mat-cau-ngoai-tiep`, sửa `AB -> SB` + kiểm tra `IA-RC1`):** `mp_tt_AB` có `display_label = "Mặt phẳng (α) qua «Trung điểm của S và B» và vuông góc với SB"`, `mid_helper_xyz = ["2", "0", "2"]`, `mp_normal = ["4", "0", "-4"]`, `leaked_M_AB = false`, `9` ID tái dựng dây chuyền, `det3_orig = "64"`, `det3_after_sb = "64"`, tâm mặt cầu `I_xyz = ["2", "2", "2"]`, `radius_sq = "12"`, `ball_volume_exact = "32*pi*sqrt(3)"`.
   - **Họ 2 — Thiết diện hình chóp (`chop-thiet-dien-ba-diem`, chuỗi `1/4 -> 3/4 -> 1/2`):** `M_xyz` cập nhật lần lượt `["0","0","9/2"] -> ["0","0","3/2"] -> ["0","0","3"]`, mỗi trạng thái giữ 5 đỉnh thiết diện đồng phẳng nằm trên cạnh, diện tích chính xác `5/2*pi^0*sqrt(34)`, `99/10*pi^0*sqrt(2)`, `6*pi^0*sqrt(6)`.
   - **Họ 3 — Lăng trụ tam giác (`lang-tru-tam-giac-thiet-dien`, `CP = 1/3 CC′`):** `P_xyz = ["0", "4", "4/3"]`, 5 đỉnh thiết diện vòng khép kín, diện tích chính xác `2*pi^0*sqrt(61)`, `no_underscore_prime_leak = true`.
   - **Họ 4 — Lập phương cắt thiết diện (`lap-phuong-thiet-dien-bat-ky`, `AM/AD = 1/3`):** gốc 6 đỉnh (`S_td = "12√3"`); sau sửa `M_xyz = ["0", "4/3", "0"]`, 6 đỉnh vòng khép kín, diện tích chính xác `71/42*pi^0*sqrt(149)`, `8` ID tái dựng.
   - **Họ 5 — Khoảng cách hai đường thẳng chéo nhau (`khoang-cach-hai-duong-cheo-nhau`):** `P_xyz = ["8/3", "8/3", "4/3"]` (`t_SC = "2/3"`), `Q_xyz = ["2", "2", "0"]` (`t_BD = "1/2"`), `PQ_dot_SC = "0"`, `PQ_dot_BD = "0"`, `PQ_norm_sq_exact = "8/3"`, `kernel_distance_sq_skew_lines = "8/3"`, `display_distance = "2√6/3"`; khi sửa `BQ/BD = 1/5`, backend từ chối fail-closed `422 DOWNSTREAM_ORTHOGONALITY_BROKEN`.
2. **Ma trận lỗi & xung đột HTTP (`8/8` PASS):** `422` (`MISSING_DEPENDENCY`, `COLLINEAR_POINTS`, `UNSUPPORTED_STEP_SYNTAX`, `INVALID_RATIO`, self-reference `MISSING_DEPENDENCY`, `DOWNSTREAM_ORTHOGONALITY_BROKEN`) + `409` (`STALE_REVISION_CONFLICT`, `EDIT_SUPERSEDED`).
3. **Sửa lỗi UI gốc (`IA-RC1`, `IA-RC2`, `IA-RC3`):**
   - `IA-RC1`: nhãn mặt phẳng giữ tham chiếu người đọc tự nhiên (`«Trung điểm của S và B»`), không rò `M_AB` hay `mid_`.
   - `IA-RC2`: khung nhập liệu & nút `Hủy` / `Chạy` hiển thị đầy đủ trong `.dock-scroll` tại `1024x768` và khi mở rộng nhiều dòng / lỗi inline (`controlsOccludeActions: false`, `runClipped: false`, `cancelClipped: false`).
   - `IA-RC3`: viewport bàn phím ảo di động `390x460` giữ trọn textarea (`taInViewport: true`) và cả 2 nút (`runInViewport: true`, `cancelInViewport: true`), `overflowX = 0`.

---

## 8. Playwright & REA MCP Evidence

1. **Playwright E2E Phase 1 ([`phase-d-browser-e2e-phase1.json`](results/phase-d-browser-e2e-phase1.json) -> `FINAL_AUDIT_BROWSER_PHASE1_PASS`):**
   - Route smoke: `/` (`200`, title `Axo — Mô phỏng tương tác`), `/app` (`200`, `fileInputCount = 3`). Lưu ý trung thực: selector thăm dò `.plus-popover-menu, [role='menu']` ghi nhận `plusMenuOpened: false` trong script smoke tự động.
   - Hover & Keyboard: `.step-edit-pencil-btn` opacity chuyển `0 -> 1` với `hoverHeightDeltaPx = 0`; `Enter` mở editor và `Escape` đóng sạch.
   - Valid `AB -> SB`: HTTP `200`, `mp_tt_AB` `normal = ["4","0","-4"]`, `leakedRawHelper = false`, `9` recomputed IDs (ảnh [`main-integration-1920-sb-valid.png`](images/main-integration-1920-sb-valid.png)).
   - Rollback `422` (`empty_whitespace` disable `Run`, `SZ` `MISSING_DEPENDENCY`, `AOC` `COLLINEAR_POINTS`, `UNSUPPORTED_STEP_SYNTAX`, skew `BQ/BD = 1/5` `DOWNSTREAM_ORTHOGONALITY_BROKEN`): `draftPreserved = true`, scene giữ nguyên (ảnh [`main-integration-1920-422-rollback.png`](images/main-integration-1920-422-rollback.png)).
   - Chuỗi cascade `1/4 -> 3/4 -> 1/4` + reload `F5` + lăng trụ `CP = 1/3 CC′` + đóng/mở lại tab + cuộn dock cô lập + probe `409 STALE_REVISION_CONFLICT`: PASS (ảnh [`main-integration-1920-cascade-f5.png`](images/main-integration-1920-cascade-f5.png)).
   - Responsive **7 viewports** (`1920x1080`, `1440x900`, `1366x768`, `1024x768`, `768x1024`, `390x844`, `320x568`) + Touch `390x844` + VKB `390x460`: `0` tràn ngang (`overflowX = 0`), `0` nút bị cắt hay che khuất (ảnh [`main-integration-vp-1024x768.png`](images/main-integration-vp-1024x768.png), [`main-integration-vkb-390x460.png`](images/main-integration-vkb-390x460.png)).
   - `consoleErrors: []`, `pageErrors: []`, `unexpected5xx: []`.
2. **Playwright E2E Phase 2 sau restart Uvicorn `:8000` ([`phase-d-browser-e2e-phase2.json`](results/phase-d-browser-e2e-phase2.json) -> `FINAL_AUDIT_BROWSER_PHASE2_PASS`):**
   - `GET /api/simulation/sessions/.../state`: `200`, `found = true`, `committedVersion = 3`, `revisionCount = 3`, `M_xyz = ["0", "0", "9/2"]`, dòng UI giữ nguyên `"Lấy điểm M thuộc SA sao cho SM/SA = 1/4"`, `consoleErrors: []`, `pageErrors: []` (ảnh [`main-integration-post-restart.png`](images/main-integration-post-restart.png)).
3. **REA MCP thụ động trên Chromium CDP tạm `:9339` (đã thu hồi tiến trình `:9339` sau chụp, [`phase-d-rea-mcp.json`](results/phase-d-rea-mcp.json)):**
   - `list_browser_targets`: `ev_be8d658ff0823ac821d0f79b89b11855475f891cfd0f42417612b368bf9d8cfc`
   - `inspect_web_page`: `ev_81951b80a15adf43055b9137a11296636e663e93f8d671f18d14ae98b26090f8` (`dom_total_nodes = 783`, `accessibility_total_nodes = 445`, `console_error_count = 0`)
   - `capture_web_screenshot`: `ev_762ef12fc56eef118018b06afd150c91a9554ce0f1738f6f5bbc837a18a9897d` (`sha256 = 6cb0d56f69c6838fc6ee537158a68be86bb02d9f384647c40b031da3d5780537`, `150.135 bytes`, khớp SHA-256 decode `100%`, ảnh [`main-integration-rea-mcp.png`](images/main-integration-rea-mcp.png)).

---

## 9. Các vấn đề tồn đọng và mức độ nghiêm trọng

| Mã | Mức độ | Nguyên nhân gốc | Bước xử lý bắt buộc trước khi gỡ gate |
| :--- | :---: | :--- | :--- |
| **`BLOCKER-DB-1`** | **CRITICAL** | Migration [`f8a2c41d9e05`](../../../../../backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py) xóa thẳng 5 bảng Classroom mà không có bước snapshot/archival/export hay công tắc xác nhận dữ liệu; đồng thời [`backend/Dockerfile`](../../../../../backend/Dockerfile#L53) chạy tự động `alembic upgrade head` khi khởi động trong khi DB SQLite trên root checkout chứa `66` dòng Classroom và `46` user. | 1) Xuất/lưu trữ dữ liệu Classroom cần giữ (JSON/SQL dump có chữ ký hash + chính sách retention được Owner phê duyệt). 2) Tách hoặc bảo vệ `f8a2c41d9e05` bằng cổng pre-flight/env flag (chỉ cho phép drop khi xác nhận đã archive hoặc bảng đích = 0 dòng), không để `Dockerfile` tự xóa bảng có dữ liệu khi boot. 3) Kiểm chứng upgrade/rollback từ DB có dữ liệu mẫu trên PostgreSQL 16.6 và SQLite `algosim.db`. |
| **`BLOCKER-DB-2`** | **HIGH** | [`backend/scripts/seed_classroom_fixture.py`](../../../../../backend/scripts/seed_classroom_fixture.py) vẫn import `Assignment`, `ClassMembership`, `Classroom` đã bị xóa ở `bf1ee2a57`. | Gỡ bỏ script lỗi thời cùng các tham chiếu liên quan nếu Classroom chính thức ngừng hỗ trợ, hoặc chuyển sang fixture snapshot archive tương ứng. |
| **`GOVERNANCE-SCOPE-1`** | **HIGH** | 113 commit ahead gói chung 34 commit Landing Page (`/` -> `LandingView`), gỡ bỏ Classroom, Attachment, Workspace tabs, Geometry library và Step Editor. Root checkout đang đứng ở nhánh `axo-ui-consistency` kèm file cá nhân untracked `ocr_reconcile.py`. | Owner xác nhận bằng văn bản hoặc tách PR/release train theo phạm vi (Landing + Classroom retirement vs Step Editor + Geometry Library), và chuẩn hóa chiến lược tích hợp với nhánh root checkout trước khi merge `main`. |

---

## 10. Trạng thái Merge thực tế

- **`MERGE_STATUS = NOT_MERGED`**
- Local `main` giữ nguyên tại `bb046fa22aceff47abe22aa783aa64fc65caee13` (`0` thay đổi).

---

## 11. Trạng thái Push thực tế

- **`PUSH_STATUS = NOT_PUSHED`**
- Remote `origin/main` giữ nguyên tại `bb046fa22aceff47abe22aa783aa64fc65caee13` (`0` thay đổi).

---

## 12. Trạng thái PostgreSQL

- PostgreSQL `16.6` (`PostgreSQL 16.6, compiled by Visual C++ build 1942, 64-bit`) đang chạy sạch tại cổng cục bộ `55432`, phục vụ backend preview `127.0.0.1:8000` (trên DB `algosim_acceptance`) và frontend `localhost:3001`.
- Bản ghi trạng thái sau Phase 1 + restart `:8000` + Phase 2 ([`phase-d-postgres-host-state.json`](results/phase-d-postgres-host-state.json)): Alembic `version_num = f8a2c41d9e05`, `step_edit_sessions: 4`, `step_edit_revisions: 9`, `step_edit_feedback: 9`, `auth_sessions: 10`.
- Cơ sở dữ liệu thử nghiệm tạm `algosim_migration_safety_probe` đã được drop sạch sau Phase B. Không có DSN, mật khẩu hay token thô trong các artifact.

---

## 13. Trạng thái Model 2

- **`MODEL_STATUS = MODEL_NOT_TRAINED`**
- Xác nhận trực tiếp qua `GET /api/simulation/feedback/status`: `model_status = "MODEL_NOT_TRAINED"`, `model_trained = false`, `total_records = 0`. Không thực hiện bất kỳ quá trình huấn luyện hay tinh chỉnh model nào trong đợt kiểm định này.

---

## 14. Các công việc được phép triển khai sau phát hành

*(Chỉ được thực thi **sau khi** Owner xử lý xong `BLOCKER-DB-1`, `BLOCKER-DB-2`, chốt `GOVERNANCE-SCOPE-1`, vượt qua lại release gate và phê duyệt merge `main`)*:
1. Vận hành nâng cấp lược đồ trên staging/production theo quy trình backup/archival trước `alembic upgrade head`.
2. Giữ nguyên Step Editor V1 đã nghiệm thu trên `main`; mọi mở rộng biên dạng hình học mới phải đi qua hợp đồng `TypedFactNext /2` -> `Planner /26` -> `Exact Kernel /24`.
3. Kiểm toán và phê duyệt thủ công nhãn `TRAINING_ELIGIBLE` cho bảng `step_edit_feedback` trước khi lên kế hoạch tách đợt thu thập dữ liệu cho Model 2 (`MODEL_NOT_TRAINED` vẫn được giữ nguyên cho tới khi có phê duyệt riêng).
4. Mọi chỉnh sửa Landing Page (nếu Owner yêu cầu đợt mới) chỉ thực hiện sau khi trạng thái `main` đã tích hợp an toàn hoặc trên nhánh tách biệt được cấp phép.
