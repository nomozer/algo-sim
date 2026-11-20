# AXO — PRE-MERGE RISK CLOSURE, ARCHITECTURE CONTRACT VERIFICATION & OWNER DECISION REPORT

- **Campaign:** `AXO — PRE-MERGE RISK CLOSURE, ARCHITECTURE CONTRACT VERIFICATION & OWNER DECISION GATE`
- **Date:** `2026-11-19`
- **Branch (`pre-merge-risk-closure` worktree):** `audit/axo-pre-merge-risk-closure`
- **Overall Release Verdict:** **`TECHNICALLY_READY_PENDING_OWNER_APPROVAL`**
- **Baseline Reference (`final-release-readiness`):**
  - Baseline report commit: `86b62adbb63688ad09124eca033535a329c611a7` (`42` file hoàn toàn nằm trong `docs/evaluation/geometry/runs/final-release-readiness/`, **`0` file code/runtime**)
  - Baseline code commit: `a0f4a516630bb582d982463cd1160f7668154221`
  - Baseline `main` / `origin/main`: `bb046fa22aceff47abe22aa783aa64fc65caee13` (`130` commits ahead, `732` files changed, `0` merge conflicts)
- **Root-Cause Fixes Landed in This Campaign:**
  1. `014a2fd24160b25039f589f5adaf3b762ba985f8` — `ISSUE-ALEMBIC-STAMP-AND-DRIFT-PREFLIGHT-GAP` ([migration_preflight.py](../../../../../backend/alembic/migration_preflight.py), [env.py](../../../../../backend/alembic/env.py))
  2. `3f3afb25b84bf845267fbda6f6e6c128c6ee502b` — `ISSUE-FE-UNORBITED-CAMERA-JUMP-ON-STEP-EDIT-COMMIT` ([scene3d-view.tsx](../../../../../frontend/src/simulations/domains/geometry/scene3d-view.tsx), [SimulationWorkspace.tsx](../../../../../frontend/src/components/SimulationWorkspace.tsx))
  3. `600f5105d4222cd6835cc916b34d5cb3f11610e6` — `ISSUE-SE-CROSS-CONTEXT-CLIENT-SEQ-DESYNC` ([step_edit_router.py](../../../../../backend/app/simulation/step_edit_router.py), [construction-step-edits.ts](../../../../../frontend/src/state/construction-step-edits.ts), [SimulationWorkspace.tsx](../../../../../frontend/src/components/SimulationWorkspace.tsx))
- **Final Sealed Candidate (`EVALUATION_CANDIDATE.json`):**
  - Seal commit: **`dbfbcf31256b60f076d8ff4464aac9223a213f09`** (`product_commit_sha = 600f5105d4222cd6835cc916b34d5cb3f11610e6`)
  - Measured system tree hash: `78edfa1784625e9bca8f1a4cd70b60359d198ba77530986903175a57e18206a7` (`109` files, `CACHE_VERSION = 132`, `--verify` exit `0`)
- **Governance Flags:** `MERGE_STATUS = NOT_MERGED` · `PUSH_STATUS = NOT_PUSHED` · `MODEL_STATUS = MODEL_NOT_TRAINED` · `PRODUCTION_DEPLOYMENT_VERIFIED = NO` · `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`

---

## 1. Executive Summary & Quality Gates Matrix

Đợt đóng rủi ro tiền hợp nhất đã kiểm chứng độc lập toàn bộ các câu hỏi kiến trúc P0/P1, phát hiện và **sửa tận gốc 3 lỗ hổng kỹ thuật thực tế** trước khi niêm phong lại tại commit **`dbfbcf31256b60f076d8ff4464aac9223a213f09`**:

| Hạng mục / Cổng | Nhóm | Kết quả | Tóm tắt bằng chứng |
| :--- | :--- | :--- | :--- |
| **Baseline `86b62adbb` Audit** | §1 | **`PASS`** | Diff `a0f4a5166..86b62adbb` chạm đúng `42` file docs/artifact trong `runs/final-release-readiness/`, `0` tác động runtime |
| **P0 §2 Schema Contract (`15` vs `20`) & Stamp Safety** | P0 | **`PASS`** | Lý giải 100% chênh lệch `5` bảng Classroom legacy; vá 3 lỗ hổng `migration_preflight` / `alembic stamp` (`014a2fd24`); bảo toàn DB gốc `46u/66c` ([schema-contract-diff.json](schema-contract-diff.json), [migration-safety-results.json](migration-safety-results.json)) |
| **P0 §3 `M_AB`/`mp_tt_AB` Semantic Identity & Rebuild** | P0 | **`PASS`** | Chứng minh khóa mờ ổn định qua cả 9 tầng vòng đời (`0` lần parse tên ID); `9/9` kịch bản đổi nhiều bước + Oracle `Fraction` PASS ([semantic-identity-audit.json](semantic-identity-audit.json), [dependency-rebuild-regression.json](dependency-rebuild-regression.json)) |
| **P0 §4 Classroom / Live Session Retirement** | P0 | **`BLOCKED_OWNERSHIP`** | Kiểm toán AST xác nhận **`18` endpoints** bị gỡ (`404`), `0` caller trong UI mới, giữ `5` bảng DB; yêu cầu Owner chọn Option A vs Option B ([classroom-api-impact-matrix.json](classroom-api-impact-matrix.json)) |
| **P1 §5 Single-Worker Constraint & PG16 Concurrency** | P1 | **`PASS`** | Fail-closed `503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY`; tải thật PG16 `1 / 5 / 20` phiên đồng thời (`78` commits + `26` `422`, `0` `5xx`, `0` lost update) ([single-worker-concurrency-results.json](single-worker-concurrency-results.json)) |
| **P1 §6 Performance Variance Root Cause (`S11` p95)** | P1 | **`PASS`** | Chứng minh độ lệch do Python Gen-2 cyclic GC (`44–84 ms` mỗi `~26` lượt) + `N=30` aliasing; GC-OFF `2a44ac92` vs current cho `delta_p50 = -0.592 ms`, `delta_p95 = -0.324 ms` (`0` hồi quy code) ([performance-remeasurement.json](performance-remeasurement.json)) |
| **P1 §7 Camera Invariance, Responsive UI, Restart & REA MCP** | P1 | **`PASS`** | Vá nhảy camera unorbited (`3f3afb25b`, `maxDeltaPx = 0 px`) & vá desync `latest_client_seq` qua restart/ngữ cảnh mới (`600f5105d`); orbited delta `= 0`; `6` viewport + VKB `390x460` + restart `v15 -> v16` + REA MCP PASS ([browser-responsive-results.json](browser-responsive-results.json)) |
| **P0 §8 Owner Decision Package** | P0 | **`BLOCKED_OWNERSHIP`** | 4 quyết định phạm vi × 10 trường bắt buộc; giữ `PENDING_OWNER_DECISION` ([owner-decision-matrix.md](owner-decision-matrix.md)) |
| **§9 Authoritative Sequential Regressions (`dbfbcf312`)** | §9 | **`PASS`** | Seal `--verify` exit `0`; Offline `23 passed`; PG16 `5+2 passed`; Step Editor `132 passed`; Semantic `1,192 passed, 1 skipped`; `npm run build` PASS; Vitest `193 files / 2,277 passed`; `git merge-tree` `0` conflicts |

---

## 2. Phân Tích Chi Tiết Các Hạng Mục P0

### 2.1. P0 §2 — Độ Chuẩn Hợp Đồng Schema (`15` vs `20` Bảng) & An Toàn `alembic stamp`

- **Vì sao tồn tại hai trạng thái hợp lệ `20` bảng và `15` bảng tại revision `f8a2c41d9e05`:**
  - Bộ ORM đang hoạt động của sản phẩm định nghĩa **14 bảng core** (+ `alembic_version` = **15 bảng**).
  - Migration lịch sử [f32f9b107b77](../../../../../backend/alembic/versions/f32f9b107b77_m18_accounts_and_classroom.py) và [a1c7e4b90d52](../../../../../backend/alembic/versions/a1c7e4b90d52_live_classroom_session.py) từng tạo **5 bảng Classroom legacy** (`assignments`, `class_memberships`, `classroom_sessions`, `classrooms`, `practice_sessions`).
  - Migration [f8a2c41d9e05](../../../../../backend/alembic/versions/f8a2c41d9e05_remove_classroom_and_live_session_tables.py) sau khi khắc phục `BLOCKER-DB-1` giữ nguyên hoàn toàn 5 bảng Classroom legacy bằng `no-op` an toàn dữ liệu. Vì thế mọi DB đi qua chuỗi migration chuẩn `base -> head` hoặc nâng từ `e437149641fa -> head` đều có **`20` bảng**, còn các DB core-only (`algosim_acceptance`, `algosim_host`, hoặc DB tạo bằng `Base.metadata.create_all()`) có **`15` bảng**.
  - Đối chiếu catalog thực tế trong [schema-contract-diff.json](schema-contract-diff.json) xác nhận **`0` sai khác** trên cả 15 bảng chung giữa `fresh 20`, `legacy migrated 20`, `algosim_acceptance 15`, và `ORM 15`.
- **Ba lỗ hổng preflight/stamp đã phát hiện và sửa tận gốc tại commit `014a2fd24`:**
  1. `unexpected_tables` (bảng lạ drift ngoài lịch sử Alembic) trước đây chưa bị chặn → nay `migration_preflight.py` từ chối với exit `23` (`SCHEMA_DRIFT_DETECTED`).
  2. Retention các bảng Classroom legacy tại `f8a2c41d9e05` nay bắt buộc nguyên tử **đủ cả 5 bảng hoặc 0 bảng** — tập con bán phần `1..4` bảng bị chặn `SCHEMA_DRIFT_DETECTED`.
  3. Lệnh `alembic stamp` online (`do_stamp` + `validate_stamp_preflight`) nay kiểm tra trùng khớp schema sống theo revision đích và chặn mọi phiên bản sai lệch (`INVALID_STAMP_SCHEMA_MISMATCH`, `STAMP_ON_ALREADY_VERSIONED_DATABASE`, `STAMP_FORBIDDEN_AT_STARTUP`), đồng thời được chứng minh bảo toàn 100% dữ liệu trên bản sao cô lập của DB gốc `46 users / 66 Classroom rows` (`SHA-256` file gốc `algo-sim\backend\algosim.db` giữ nguyên `39D676C7B50A925975828434A00D38E3BAC3C5F50E4E2A724A695768C7C83EE3`).

### 2.2. P0 §3 — Định Danh Ngữ Nghĩa (`M_AB`, `mp_tt_AB`) & Dependency Rebuild

- Kiểm toán mã nguồn toàn repo ([semantic-identity-audit.json](semantic-identity-audit.json)) cho **`0` kết quả** parse chuỗi `M_AB` hoặc `mp_tt_AB` để suy diễn hình học (`sem_m_ab_hits: 0`). Chúng chỉ là khóa ổn định mờ (opaque keys) gắn qua 9 tầng: `InlineConstructionStepEditor` → parser câu lệnh → IR `ParsedStepEdit` → DAG `depends` → `Fraction`/`Radical` kernel → metadata đối tượng (`label`, `notation`, `reference`, `display_label`, `role`, `computational_depends`, `visible_prerequisites`, `dependency_edges`) → `_sync_rebuilt_event` → renderer (`shortSym`, `SimulationWorkspace.tsx` nhận diện `absorbedHelperIds` từ `pObj.depends` của point3 không tên) → PostgreSQL session persistence.
- Kết quả `9/9` chuỗi biến đổi phức tạp với Oracle `Fraction` độc lập ([dependency-rebuild-regression.json](dependency-rebuild-regression.json)):
  - Đổi trực tiếp `AB -> SB` và `(α) -> (P)` cập nhật đồng bộ `M_AB` (`["2","0","2"]`), `I` (`["2","2","2"]`), tạo `line_S_B`, không sót `(α)`.
  - Ép đổi trực tiếp `SB -> AD` khi `(β)` đang là trung trực `AD` bị **từ chối fail-closed `422 CONTAINED_INFINITE_INTERSECTION`** đúng bản chất toán học (hai mặt phẳng trùng nhau).
  - Sau khi chuyển `(β): AD -> SC`, đổi `SB -> AD` rồi `AD -> AB` & `(P) -> (α)` thành công, rút gọn sạch `line_S_B` (`retired_ids`), mọi điểm đáy & đỉnh kiểm chứng `||V - I||^2 == Fraction(12)`.
  - Chỉnh kép `"Gọi K là trung điểm của SB; dựng mặt phẳng (Q) qua K và vuông góc với SB"` rút gọn `M_AB`, sau đó quay về `"Dựng mặt phẳng trung trực (P) của cạnh AD"` rút gọn `K` & `line_S_B`, tạo mới `mid_A_D` với `0` orphan và `0` lỗi continuity.

### 2.3. P0 §4 — Kiểm Toán Gỡ Bỏ 18 API Classroom & Live Session

- Đối chiếu AST toàn bộ `@router.*` giữa `bb046fa22` (`main`) và candidate ([classroom-api-impact-matrix.json](classroom-api-impact-matrix.json)): chính xác **`18` HTTP endpoints** bị gỡ (`404 Not Found` trên RC):
  - `backend/app/accounts/router.py` (**6 routes**): `GET/POST /api/classes`, `POST/DELETE /api/classes/{class_id}/code`, `POST /api/classes/join`, `GET /api/classes/{class_id}/members`.
  - `backend/app/accounts/classroom_router.py` (đã xóa, **5 routes**): `POST/GET /api/assignments`, `GET /api/assignments/{assignment_id}`, `POST /api/assignments/{assignment_id}/progress`, `GET /api/classes/{class_id}/observe`.
  - `backend/app/accounts/session_router.py` (đã xóa, **7 routes**): `POST/GET/DELETE /api/classes/{class_id}/session`, `POST /api/classes/{class_id}/session/command`, `POST /api/assignments/{assignment_id}/help`, `POST /api/classes/{class_id}/help/{student_id}/clear`, `GET /api/classes/{class_id}/monitor`.
- Frontend RC `frontend/src/` không còn caller hoạt động nào; `5` bảng Classroom trong DB vẫn giữ nguyên vẹn (`0` mất dữ liệu). Tuy nhiên đây là **thay đổi hợp đồng HTTP phá vỡ tương thích ngược** đối với người dùng/script Classroom bên ngoài → gắn nhãn **`OWNER_DECISION_REQUIRED`** giữa **Option A (khôi phục router)** và **Option B (chính thức ngừng trên V1 + changelog)**.

---

## 3. Phân Tích Chi Tiết Các Hạng Mục P1 & Hai Root-Cause Fix Phát Hiện Trong Chiến Dịch

### 3.1. P1 §5 — Ràng Buộc Kiến Trúc Đơn Worker (`workers=1`) & Tải Đồng Thời PG16

- `_assert_single_worker_runtime()` trong [step_edit_router.py](../../../../../backend/app/simulation/step_edit_router.py) fail-closed `HTTP 503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY` khi cấu hình > 1 worker vì các cấu trúc đồng bộ hóa in-process (`_SESSION_LOCKS`, `_CANCELLED_REQUESTS`, `_LATEST_CLIENT_SEQ`, `_LAST_COMMIT_SNAPSHOT`) nằm trong bộ nhớ của một tiến trình, kết hợp với `db.rollback()` trước khi giữ lock, PostgreSQL `SELECT ... FOR UPDATE`, và `QueuePool(pool_size=10, max_overflow=20)`. Endpoint là `def` đồng bộ chạy trên threadpool AnyIO nên không block event loop chính.
- Thử nghiệm tải thật trên staging HTTP `:8012` + PostgreSQL 16 ([single-worker-concurrency-results.json](single-worker-concurrency-results.json)):
  - **1 phiên đồng thời (`3` commits + `1` `422`):** `0` `5xx`, `0` lost update; HTTP RTT `p50 = 78.355 ms, p95 = 101.634 ms` (engine `p50 = 19.203 ms`).
  - **5 phiên đồng thời (`15` commits + `5` `422`):** `0` `5xx`, `0` lost update; HTTP RTT `p50 = 273.089 ms, p95 = 368.716 ms` (engine `p50 = 27.946 ms`).
  - **20 phiên đồng thời (`60` commits + `20` `422`):** `0` `5xx`, `0` lost update, `100%` cách ly chéo phiên; HTTP RTT `p50 = 1,121.432 ms, p95 = 1,381.371 ms` (chủ yếu do xếp hàng CPU đơn tiến trình & PG transaction pool ~`1,028.569 ms`; engine `p50 = 27.255 ms`).
  - **8 ping `/api/auth/me` song song trong lúc tải 20 phiên:** `100% HTTP 200`, `p50 = 16.313 ms, p95 = 18.130 ms`.
  - **Va chạm cùng phiên (`5` luồng ghi `version=0` cùng lúc):** `1` commit `200`, `4` từ chối an toàn `409` (`STALE_REVISION_CONFLICT` / `EDIT_SUPERSEDED`), DB dừng chính xác ở `committed_version = 1`.
  - **Idempotent replay (`same client_request_id`):** trả `200` `idempotent_replay=true`, không tạo revision trùng.

### 3.2. P1 §6 — Nguyên Nhân Gốc Biến Động `S11` p95 (`11.748 ms -> 22.686 ms`)

- Đo tách bạch `3 × 120` lượt trên từng chế độ (`GC_AUTO` có `gc.callbacks`, loại Gen-2 pause, `GC_ISOLATED`, `tracemalloc` tách riêng pass để tránh làm chậm `~7x` đồng hồ tường, cộng cold subprocesses & so sánh đối đầu trực tiếp trong cùng tiến trình `2a44ac92` vs hiện tại trong [performance-remeasurement.json](performance-remeasurement.json)):
  - **Bằng chứng xác nhận `CONFIRMED_PYTHON_GEN2_GC_SPIKE_PLUS_N30_QUANTILE_ALIASING_ZERO_REGRESSION`:**
    1. Với `GC_AUTO` (`N=120`), Python Generation-2 GC kích hoạt theo chu kỳ đều mỗi `~26` lượt gọi (`iter 26, 52, 79, 105` — chiếm `3–5` sự kiện/`120` lượt = `~3.3%`), gây pause `44–84 ms` khiến `max` lên `91.9–100.2 ms` và đẩy `p95` nếu mẫu nhỏ `N=30` lọt 2 spike vào đuôi phân vị (`index 27.55`). Khi loại riêng `4–5` lượt dính Gen-2 GC, `non_gen2_gc_total_ms` tụt từ `p99 = 92.424 ms` xuống **`20.819 ms`** (`max = 32.456 ms`).
    2. So sánh đối đầu **cùng tiến trình `GC_OFF` (`N=120`)** giữa baseline `2a44ac92` (`p50 = 14.110 ms, p95 = 19.577 ms`) và candidate hiện hành (`p50 = 13.518 ms, p95 = 19.253 ms`) cho kết quả **`delta_p50 = -0.592 ms, delta_p95 = -0.324 ms`** (thậm chí nhanh hơn nhẹ; `tracemalloc` peak `557.28 KB`, retained `27.12 KB`).
    3. Tách riêng thời gian E2E thật trên staging `:8012` + PG16 (`N=50`): Server engine `p50 = 16.488 ms, p95 = 41.563 ms`, PG commit `p50 = 12.817 ms, p95 = 15.097 ms`, HTTP transport/serialize `p50 = 34.171 ms, p95 = 48.826 ms`, Client RTT `p50 = 66.249 ms, p95 = 89.129 ms`; và trong trình duyệt Chromium (`N=15` vòng sửa liên tiếp trên `S1`): mở form `p50 = 43.505 ms`, cập nhật UI hoàn tất `p50 = 134.587 ms` (`rAF` Scene3D `p50 = 46.000 ms`), tổng E2E trình duyệt `p50 = 265.579 ms, p95 = 353.492 ms`.

### 3.3. P1 §7 — Hai Lỗi Gốc Mới Được Phát Hiện & Khắc Phục Triệt Để Trong Chiến Dịch

1. **`ISSUE-FE-UNORBITED-CAMERA-JUMP-ON-STEP-EDIT-COMMIT` (Commit `3f3afb25b`):**
   - **Triệu chứng thực tế phát hiện qua Playwright:** Nếu học sinh chưa xoay camera 3D (`initialCameraPose === null` vì `baoCaoCameraPose` bỏ qua pose từ auto-fit) rồi sửa bước dựng (`AB -> SB`), lần dựng lại `Scene3DView` tính lại góc nhìn mặc định (`chonHuongNhin`) + lens offset mới làm chóp xoay `~30°` (đỉnh `C` nhảy `195 px` ở `S11`, đỉnh `A` nhảy `59 px` ở `S1`).
   - **Sửa tận gốc:** Gắn `sceneIdentityKey` từ `SimulationWorkspace` sang `Scene3DView`, duy trì `liveCameraStateRef` đồng bộ `position`, `target` và `offset` (`ViewOffset`), chỉ kích hoạt khôi phục `sameIdentitySceneRebuild` khi cùng bài toán mà giữ `fitToken` / chuyển bài vẫn auto-fit bình thường. Thêm test hồi quy [step-edit-camera-invariance.test.tsx](../../../../../frontend/src/components/__tests__/step-edit-camera-invariance.test.tsx).
   - **Kiểm chứng lại trên trình duyệt thật (`dbfbcf312`):** `unorbitedCameraInvariance.maxDeltaPx = 0` (`S=0, B=0, C=0, D=0` px!), `orbitedCameraInvariance` (`positionDelta = 0, targetDelta = 0`).

2. **`ISSUE-SE-CROSS-CONTEXT-CLIENT-SEQ-DESYNC` (Commit `600f5105d`):**
   - **Triệu chứng thực tế phát hiện ở Phase 2 Restart:** Backend lưu `_latest_client_seq = 20` vào `step_edit_sessions.dependency_graph_json` trong PostgreSQL, nhưng `GET /api/simulation/sessions/{id}/state` trước đây lọc bỏ khóa `_` nội bộ và **không trả `latest_client_seq`**. Khi người dùng đăng nhập hoặc mang token sang trình duyệt mới / ngữ cảnh sạch / sau khi xóa `localStorage`, UI khôi phục được cảnh `committed_version = 15` nhưng gửi `client_seq = 1`, khiến `POST /steps/edit` bị backend từ chối `409 EDIT_SUPERSEDED` liên tiếp `20` lần và `SimulationWorkspace.tsx` nuốt im thông báo lỗi.
   - **Sửa tận gốc ở tầng sở hữu hợp đồng:**
     - [step_edit_router.py](../../../../../backend/app/simulation/step_edit_router.py): thêm `_current_latest_client_seq`, trả `latest_client_seq` trong `GET /sessions/{id}/state` (`found=true` lẫn `found=false`) và trong response `409 EDIT_SUPERSEDED`.
     - [construction-step-edits.ts](../../../../../frontend/src/state/construction-step-edits.ts): thêm `syncServerClientSeqWatermark` tự động đồng bộ watermark từ `GET /state` (cũng như từ `409` / post-commit reconciliation) trước khi cấp `allocateMonotonicSubmitSeq`, và gắn cờ `local_abort: true/false` tách bạch hủy cục bộ trong tab với xung đột `409` từ server.
     - [SimulationWorkspace.tsx](../../../../../frontend/src/components/SimulationWorkspace.tsx): chỉ ẩn thông báo lỗi với `res.local_abort`, hiển thị rõ `learner_error` cho xung đột server thật.
   - **Kiểm chứng lại trên trình duyệt thật (`dbfbcf312`):** Sau khi khởi động lại Uvicorn `:8012`, ngữ cảnh trình duyệt hoàn toàn mới đọc `GET /state` (`committed_version=15`, `M=["0","0","9/2"]`) và bấm `Chạy` đổi `SM/SA = 1/3` thành công ngay ở lần bấm đầu tiên (`200 OK`, `committed_version=16`, `M=["0","0","4"]`).

### 3.4. Responsive Viewports, Touch/VKB & REA MCP Inspection (`dbfbcf312`)

- Kiểm thử trên cả 6 khung hình (`1920x1080`, `1440x900`, `1280x800`, `768x1024`, `390x844` touch, `320x568` touch) + VKB `390x460`: `overflowX = 0` trên mọi viewport, cả 8 nhãn đỉnh nhìn rõ (`visibleVertexLabels = 8`, `clippedLabels = []`), `Chạy`/`Hủy` và textarea nằm trọn trong khung nhìn VKB `390x460`, chạm kích hoạt nút bút trên thiết bị cảm ứng hoạt động đúng (`@media (hover: none)`).
- REA MCP (`list_browser_targets` `ev_20118e13...`, `inspect_web_page` `ev_73255d1b...`, `capture_web_screenshot` `ev_974bb9e0...`): xác nhận `783` DOM nodes, `445` accessibility nodes, điều khiển Step Editor `Chạy`/`Hủy` hiển thị trong accessibility tree, `0` console error, `0` page error, screenshot PNG `150,127` bytes khớp SHA-256 `64513149a1cef8ea1d37aaf9bdbd5994a1507dbdacd32044807ac075fe3a4db4` ([rc-rea-mcp.png](images/rc-rea-mcp.png)).

---

## 4. Kết Quả Regression Toàn Diện Trên Bản Niêm Phong Cuối `dbfbcf312` (§9)

Toàn bộ các bộ kiểm thử sau được chạy **tuần tự nghiêm ngặt (không chồng chéo CPU/DB)** trực tiếp trên HEAD **`dbfbcf31256b60f076d8ff4464aac9223a213f09`**:

| Suite / Kiểm chứng | Kết quả chính xác | Ghi chú / Phạm vi |
| :--- | :--- | :--- |
| `scripts/freeze_evaluation_candidate.py --verify` | **`PASS`** (exit `0`) | `109` file sản phẩm, hash `78edfa1784625e9bca8f1a4cd70b60359d198ba77530986903175a57e18206a7`, `cay_lam_viec_sach: true`, `CACHE_VERSION = 132` |
| Backend migration/safety/acceptance/risk (offline) | **`23 passed, 3 deselected`** (`148.37s`) | 3 test PG được tách chạy riêng ở hàng dưới |
| Backend PostgreSQL 16 integration (`-m postgres`, 5 files) | **`5 passed, 21 deselected`** (`131.38s`) | Dùng `ALGOSIM_PG16_BIN` v16.6 thật |
| Backend Step Editor (`9` files `tests/geometry/`) | **`132 passed, 2 deselected`** (`42.13s`) + **`2 passed`** (`-m postgres`, `28.03s`) | **Tổng `134/134` PASS** qua cả 9 file |
| Backend `tests/semantic_program/` | **`1,192 passed, 1 skipped`** (`46.49s`) | 1 skip chủ định tại `test_scalar_obligations.py:95` |
| Frontend production build (`npm run build`) | **`PASS`** (`6.08s`) | `tsc -b && vite build`, `0` lỗi TypeScript/bundler |
| Frontend full Vitest (`npx vitest run`) | **`193 files, 2,277 passed`** (`142.40s`) | `0` failed, `0` skipped |
| Git merge simulation vs `main` (`bb046fa22`) | **`0 conflicts` / FF-eligible** | `merge-base --is-ancestor` exit `0`, `merge-tree` tree `ffdfab57...` |
| Docs Information Architecture & Link Audit | **`PASS`** (`leak_count = 0`) | `audit_docs_information_architecture.py` & scan liên kết tương đối `0` lỗi |

---

## 5. Trả Lời Đầy Đủ 10 Câu Hỏi Bắt Buộc (§11)

### Q1. Bản mới hơn ở `step-editor-release-candidate` (`86b62adbb`) khác gì `a0f4a5166`, có ảnh hưởng runtime hay không, và `a0f4a5166` có còn giữ nguyên kết quả đã chứng minh không?
- **Có bằng chứng diff trực tiếp:** `git diff --name-only a0f4a516630bb582d982463cd1160f7668154221 86b62adbb63688ad09124eca033535a329c611a7` chứa chính xác **`42` file**, tất cả đều nằm trong thư mục artifact đánh giá `docs/evaluation/geometry/runs/final-release-readiness/` (`0` file trong `backend/`, `frontend/`, hay cấu hình runtime).
- Do đó `86b62adbb` **không có bất kỳ ảnh hưởng runtime nào**, `a0f4a5166` giữ nguyên toàn bộ kết quả cũ, và đợt đóng rủi ro này tiếp nối sạch bằng nhánh cô lập `audit/axo-pre-merge-risk-closure` đến bản niêm phong cuối **`dbfbcf31256b60f076d8ff4464aac9223a213f09`** gồm 3 sửa lỗi gốc mới.

### Q2. Vì sao các DB sau `f8a2c41d9e05` có cả bản `15` bảng và `20` bảng; trạng thái nào là chuẩn?
- Xem [schema-contract-diff.json](schema-contract-diff.json). **Cả `20` bảng và `15` bảng đều hợp lệ theo thiết kế**, nhưng **20 bảng** (`14` bảng ORM hiện hành + `alembic_version` + `5` bảng Classroom legacy: `assignments`, `class_memberships`, `classroom_sessions`, `classrooms`, `practice_sessions`) là trạng thái chuẩn cho mọi DB nâng cấp qua chuỗi Alembic `base -> head` hoặc nâng từ `e437149641fa -> head` vì `f8a2c41d9e05` không xóa bảng legacy. Trạng thái **15 bảng** xảy ra ở DB core-only (`Base.metadata.create_all()` hoặc `algosim_acceptance` khởi tạo trước khi vá `BLOCKER-DB-1`). Trạng thái trung gian **16–19 bảng** (`1..4` bảng legacy) là drift bất hợp lệ và nay bị chặn fail-closed.

### Q3. `alembic stamp` trên DB chưa gắn phiên bản và `migration_preflight.py` đã đủ an toàn cho dữ liệu production chưa?
- Trước chiến dịch này: **chưa đủ**, vì thiếu kiểm tra `unexpected_tables`, thiếu kiểm tra nguyên tử `0`-or-`5` bảng legacy, và chưa chặn `alembic stamp` online sai revision.
- Sau commit **`014a2fd24`** ([migration_preflight.py](../../../../../backend/alembic/migration_preflight.py), [env.py](../../../../../backend/alembic/env.py)): **đủ an toàn** khi đi kèm Runbook bắt buộc (`backup -> kiểm parity -> stamp -> upgrade head`). Mọi DB drift bảng lạ, thiếu bảng/cột, giữ bán phần bảng legacy, hoặc stamp sai version (`stamp head` trên DB `e437149641fa`) đều bị từ chối trước DDL; toàn bộ 46 users / 66 dòng Classroom trên bản sao cô lập của `algo-sim\backend\algosim.db` được giữ nguyên 100%, file gốc không đổi 1 byte. Xem [migration-safety-results.json](migration-safety-results.json).

### Q4. Các ID lịch sử `M_AB`, `mp_tt_AB` là khóa mờ ổn định hay vẫn bị phân tích ngữ nghĩa ngầm?
- **Là khóa mờ ổn định (opaque keys) có đồng bộ metadata đầy đủ** qua cả 9 tầng vòng đời; tổng số vị trí parse ngữ nghĩa `M_AB` hoặc `mp_tt_AB` trong mã sản phẩm là **`0`** ([semantic-identity-audit.json](semantic-identity-audit.json)). Kể cả khi người dùng đổi tên mặt phẳng `(α) -> (P) -> (Q)`, chuyển cạnh `AB -> SB -> AD -> AB`, tạo/rút gọn điểm trung gian hợp thành `K` hay `mid_A_D`, frontend và backend đều suy xuất tên hiển thị và phụ thuộc từ trường cấu trúc (`notation`, `label`, `reference`, `display_label`, `depends`, `computational_depends`, `visible_prerequisites`), không suy diễn từ ID. Xem [dependency-rebuild-regression.json](dependency-rebuild-regression.json).

### Q5. Độ tin cậy khi người dùng đổi nhiều bước liên tiếp và qua các nhánh phụ thuộc?
- Đã kiểm chứng thành công **`9/9` kịch bản đa bước** ([dependency-rebuild-regression.json](dependency-rebuild-regression.json)): đổi đơn bước, từ chối fail-closed `422 CONTAINED_INFINITE_INTERSECTION` khi hai mặt phẳng trùng nhau, chuyển nhánh phụ thuộc `mp_tt_AD` trước rồi chuyển `mp_tt_AB`, hoàn tác chuỗi, gộp bước trung điểm thành bước tường minh `K` rồi rút gọn sạch `K` và `line_S_B`, và thay đổi tỉ số thượng nguồn trên `chop-thiet-dien-ba-diem` kéo theo tái dựng chính xác thiết diện `MENPF`. Toàn bộ đầu ra đều vượt qua bộ kiểm tính liên tục và Oracle độc lập dùng số hữu tỷ chính xác `Fraction`.

### Q6. Việc gỡ các endpoint Classroom / Live Session tác động thế nào tới user/API hiện hữu, và cần Owner chốt phương án nào?
- Chính xác **`18` HTTP endpoints** (`/api/classes*`, `/api/assignments*`, `/api/classes/*/session*`, `/api/assignments/*/help`, `/api/classes/*/monitor`) bị gỡ khỏi candidate (`404 Not Found`), trong khi `0` caller Classroom còn trong UI RC và **`5` bảng Classroom trong DB vẫn giữ nguyên 100%**. Đây là Breaking Change về API cho mọi người dùng Classroom/Live Session hoặc script tích hợp cũ. Owner cần chốt tường minh giữa **Option A (khôi phục Classroom routers trước khi merge)** hoặc **Option B (chính thức ngừng Classroom HTTP API ở V1, giữ nguyên 5 bảng DB và ban hành changelog)**. Xem [classroom-api-impact-matrix.json](classroom-api-impact-matrix.json) và [owner-decision-matrix.md](owner-decision-matrix.md).

### Q7. Giới hạn 1 Uvicorn worker ảnh hưởng thế nào ở concurrency trung bình và có là rủi ro kiến trúc?
- Đây là **ràng buộc kiến trúc có chủ đích của V1 (`PROVEN_ARCHITECTURAL_V1_CONSTRAINT`)** do các cấu trúc `_SESSION_LOCKS`, `_CANCELLED_REQUESTS`, `_LATEST_CLIENT_SEQ`, `_LAST_COMMIT_SNAPSHOT` nằm trong bộ nhớ tiến trình, được bảo vệ fail-closed `HTTP 503 UNSUPPORTED_MULTI_WORKER_TOPOLOGY`. Trên PostgreSQL 16 thực tế ([single-worker-concurrency-results.json](single-worker-concurrency-results.json)), 1 worker chịu tải **`20` phiên đồng thời (`60` commits + `20` `422`)** với **`0` lỗi `5xx`**, **`0` mất cập nhật**, health ping `/api/auth/me` đạt `p50 = 16.313 ms` (`100% 200 OK`); tuy nhiên HTTP RTT của phiên edit tăng từ `p50 = 78.355 ms` (`1` phiên) → `273.089 ms` (`5` phiên) → `1,121.432 ms` (`20` phiên) do xếp hàng xử lý trên 1 tiến trình Python. Nếu V2 cần scale ngang nhiều worker, sẽ cần chuyển lock/cancel state sang store phân tán.

### Q8. Hiện tượng nhảy `S11` `p95` (`11.748 ms -> 22.686 ms`) có phải regression mã nguồn không?
- **Không — đó thuần túy là spike chu kỳ Python Gen-2 cyclic GC cộng hiệu ứng mẫu nhỏ `N=30`**, **0% hồi quy mã nguồn**. Khi bật `gc.callbacks` qua `3 × 120` lượt ([performance-remeasurement.json](performance-remeasurement.json)), Gen-2 GC dừng thế giới `44–84 ms` mỗi `~26` lượt (`~3.3%` mẫu), đẩy đuôi `p95` của cửa sổ `N=30` lên bất thường. Loại các lượt Gen-2 GC đưa `p99` từ `92.424 ms` về `20.819 ms`; và chạy đối đầu trực tiếp trong cùng tiến trình với `GC_OFF (N=120)` cho thấy bản hiện tại đạt `p50 = 13.518 ms, p95 = 19.253 ms` so với `2a44ac92` (`p50 = 14.110 ms, p95 = 19.577 ms`, tức **`-0.592 ms` p50 và `-0.324 ms` p95**).

### Q9. Khi commit chỉnh bước (chưa orbit hoặc đã orbit), chuyển viewport, bật bàn phím ảo và khởi động lại backend, camera + UI + DB có an toàn không?
- **Có — sau khi vá tận gốc 2 lỗi phát hiện được trong chính đợt kiểm thử này:**
  - `3f3afb25b` đóng lỗi nhảy camera khi chưa orbit (`maxDeltaPx = 0 px`, trước sửa là `195 px` ở `C`); camera đã orbit có `positionDelta = 0` và `targetDelta = 0`.
  - `600f5105d` đóng lỗi desync `latest_client_seq` qua ngữ cảnh trình duyệt mới/khởi động lại backend; sau restart `:8012`, ngữ cảnh mới đọc lại `committed_version = 15` (`M = ["0","0","9/2"]`) và commit ngay `SM/SA = 1/3` (`committed_version = 16`, `M = ["0","0","4"]`) ở lần bấm đầu tiên.
  - Toàn bộ `6` viewport (`1920x1080` → `320x568`) + VKB `390x460` đều đạt `overflowX = 0`, textarea + `Hủy` + `Chạy` nằm gọn trong viewport và `0` console/page/5xx error ([browser-responsive-results.json](browser-responsive-results.json)).

### Q10. Nhánh `feat/axo-geometry-library-verification` / ứng viên hiện tại đã sẵn sàng để Owner quyết định đưa vào `main` chưa, kèm điều kiện gì?
- Về mặt **kỹ thuật phần mềm, hình học chính xác, an toàn cơ sở dữ liệu, trình duyệt và hiệu năng**: **ĐÃ SẴN SÀNG (`TECHNICALLY_READY_PENDING_OWNER_APPROVAL`)** tại bản niêm phong cô lập **`dbfbcf31256b60f076d8ff4464aac9223a213f09`** (`0` merge conflict với `main`, fast-forward hợp lệ).
- Tuy nhiên **`MERGE_STATUS = NOT_MERGED` và `PUSH_STATUS = NOT_PUSHED`** vì còn **4 điều kiện Ownership / Vận hành** bắt buộc Owner ký quyết định trong [owner-decision-matrix.md](owner-decision-matrix.md): (1) đồng ý route `/` → `LandingView` & `/app` → Workspace; (2) chọn **Option A** (khôi phục Classroom HTTP) hoặc **Option B** (ngừng chính thức 18 API Classroom & giữ 5 bảng DB); (3) chấp nhận `Workspace / Attachment Overhaul + CACHE_VERSION = 132`; (4) phê duyệt Runbook triển khai V1 (`uvicorn --workers 1` + `backup -> alembic stamp e437149641fa -> upgrade head` cho DB legacy). Lưu ý bổ sung: `MODEL_STATUS = MODEL_NOT_TRAINED`, `PRODUCTION_DEPLOYMENT_VERIFIED = NO`, `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`.

---

## 6. Bằng Chứng Bảo Toàn Môi Trường Gốc

- `D:\Documents\projects\algo-sim` (`axo-ui-consistency` @ `bb046fa22aceff47abe22aa783aa64fc65caee13`): giữ nguyên tuyệt đối, chỉ giữ nguyên trạng file untracked sẵn có `?? ocr_reconcile.py` của user; `backend\algosim.db` giữ nguyên `413,696` bytes (`SHA-256 = 39D676C7B50A925975828434A00D38E3BAC3C5F50E4E2A724A695768C7C83EE3`).
- Worktree `.superpowers\worktrees\step-editor-release-candidate` (`86b62adbb63688ad09124eca033535a329c611a7`) và các dịch vụ host của user (`:3001`, `:8000`, `:55432` `algosim_acceptance`): giữ nguyên hoàn toàn, hoạt động bình thường.
- Các tiến trình và DB staging tạm của chiến dịch (`:3012`, `:8012`, `:9341`, `algosim_risk_closure_staging`): đã dọn dẹp hoàn toàn.
