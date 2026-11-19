# AXO — FINAL RELEASE GATE CLOSURE & PRE-MERGE INTEGRATION ACCEPTANCE REPORT

**Ngày lập báo cáo:** `2026-11-19`  
**Worktree nghiệm thu cô lập:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\final-pre-merge-acceptance`  
**Nhánh ứng viên:** `release/axo-final-pre-merge-acceptance`  
**Commit ứng viên đầu vào:** `897d70c9f9a3862ef5dcaa45a3f91ffd326e91ed` (chỉ bổ sung gói bằng chứng `final-pre-merge-acceptance/` trên nhánh đánh giá, giữ nguyên toàn bộ mã nguồn & test từ `892e15f06fc53c623a1392f0766d69c21291436a`)  
**Product Commit (`product-paths-excluding-test-only/1`):** `600f5105d4222cd6835cc916b34d5cb3f11610e6` · **Measured Tree Hash:** `78edfa1784625e9bca8f1a4cd70b60359d198ba77530986903175a57e18206a7` (`109` file) · **`CACHE_VERSION`:** `132`  
**Baseline `main`:** `bb046fa22aceff47abe22aa783aa64fc65caee13` (`134` commit phía sau nhánh ứng viên; **chưa merge, chưa push**)

---

## 1. Kết Luận Điều Hành & Trạng Thái Chính Thức

Toàn bộ các cổng kỹ thuật (A, B, D, E, F, G) của đợt **Final Release Gate Closure & Pre-Merge Integration Acceptance** đã được thực thi độc lập và **ĐẠT (`PASS`)**, bao gồm việc đóng dứt điểm **Gate A (Docker Linux Container + PostgreSQL 16.16 Runtime Gate)** từng bị môi trường chặn ở đợt trước. Cổng **Gate C (`C-Classroom`)** đã đóng xong theo **Option B**; ba hạng mục quản trị phạm vi thuộc quyền Owner (**`C-Landing`**, **`C-Workspace`**, **`C-Release`**) đang ở trạng thái chờ Owner chốt trong [`owner-approval-checklist.md`](owner-approval-checklist.md).

| Trường trạng thái | Giá trị xác nhận |
| --- | --- |
| `RELEASE_DECISION` | `READY_FOR_OWNER_APPROVAL` |
| `MERGE_STATUS` | `NOT_MERGED` |
| `PUSH_STATUS` | `NOT_PUSHED` |
| `DOCKER_RUNTIME_GATE` | `PASS` |
| `MODEL_STATUS` | `MODEL_NOT_TRAINED` |
| `PRODUCTION_DEPLOYMENT_VERIFIED` | `NO` |
| `INDEPENDENT_H1_VALIDATION` | `NOT_MEASURED` |

| Cổng kiểm chứng | Trạng thái | Tệp bằng chứng chính |
| --- | --- | --- |
| **Gate A — Docker Runtime Gate** | `PASS` | [`docker-runtime-verification.json`](docker-runtime-verification.json) |
| **Gate B — PG16 Backup, Restore & Rollback** | `PASS` | [`postgres-recovery-verification.json`](postgres-recovery-verification.json) |
| **Gate C — Ownership & Scope Audit** | `PENDING_OWNER_DECISION` (`C-Classroom` Verified Option B) | [`ownership-scope-decision-matrix.json`](ownership-scope-decision-matrix.json) |
| **Gate D — Geometry Oracle, Step Editor & Perf/Memory** | `PASS` | [`geometry-independent-oracle.json`](geometry-independent-oracle.json), [`step-editor-state-consistency.json`](step-editor-state-consistency.json), [`performance-memory-verification.json`](performance-memory-verification.json) |
| **Gate E — Clean Candidate Suites & Merge Sim** | `PASS` | [`integration-candidate-manifest.json`](integration-candidate-manifest.json) |
| **Gate F — Host Live Stack, Browser 6 Viewports & REA MCP** | `PASS` | [`browser-e2e-summary.json`](browser-e2e-summary.json) + 15 ảnh `images/fpa-*.png` |
| **Gate G — Repo Safety, Governance & Deliverables** | `PASS` | [`release-gates-summary.json`](release-gates-summary.json), [`run.json`](run.json), [`owner-approval-checklist.md`](owner-approval-checklist.md) |

---

## 2. Gate A — Khôi Phục & Đóng Cổng Docker Runtime (`PASS`)

- **Môi trường Docker Linux thật:** Docker Desktop `4.97.0 (244584)`, Docker Engine `29.9.2`, kiến trúc `linux/amd64` trên WSL2 kernel `6.6.87.2-microsoft-standard-WSL2`, DB container `postgres:16-alpine` (`PostgreSQL 16.16`, `pg_dump` / `pg_restore` `16.16`).
- **Build image từ candidate hiện hành:** Image `algosim-backend:fpa-gate` (`sha256:b08c86bea3d570912bd4cc59286f1a084a547cdfaa91d82ad215a848527ecd36`, `790,342,908` B, build `7,508.31 ms`) nhúng nhãn `org.algosim.backend.git-sha = 897d70c9f9a3862ef5dcaa45a3f91ffd326e91ed`.
- **Boot 1 & Persistence qua container restart (Boot 2):**
  - **Boot 1:** Health `healthy` sau `5,400.58 ms`; log khởi động xác nhận `MIGRATION_PREFLIGHT=PASS reason=SAFE_NO_DESTRUCTIVE_OPERATIONS` và Alembic upgrade tới `f8a2c41d9e05`. Kiểm tra Option B: `/api/classes`, `/api/assignments`, `/api/live-sessions` đều trả HTTP `404`. Thực hiện Step Edit #1 thành công HTTP `200` (`committed_version = 1`, `after_digest = fb7c6b2f5fd5e197`).
  - **Boot 2 (`docker restart`):** Health `healthy` sau `5,994.42 ms`; truy vấn `GET /api/simulation/sessions/fpa-docker-s1/state` trả nguyên vẹn `committed_scene` khớp byte với Boot 1.
- **Ma trận từ chối fail-closed âm tính (6 kịch bản trong container):**
  - `unstamped_existing_db`: exit `23` (`UNSTAMPED_EXISTING_DATABASE`).
  - `schema_drift_db`: exit `23` (`SCHEMA_DRIFT_DETECTED`).
  - `partial_migration_db`: exit `23` (`PARTIAL_MIGRATION_PRE_EXISTING_OBJECT`).
  - `destructive_pending_migration`: exit `23` (`DESTRUCTIVE_MIGRATION_FORBIDDEN_AT_STARTUP`).
  - `startup_downgrade_attempt`: exit `1` (`DOWNGRADE_FORBIDDEN_AT_STARTUP`).
  - `hybrid_route_mode_off`: HTTP `503` (`INVALID_HYBRID_ROUTE_MODE`).
- **Official `pg_dump -Fc` & `pg_restore` trong Docker:** Dump `82,075` B (`sha256: b69f94445b8ff45998780fe6554f2d35cfb3d75cd4be30367f394d5c95f9392d`) -> restore vào DB mới đạt 100% parity trên cả 20 bảng (SHA-256 từng bảng, constraint, index), sau đó container thực hiện Step Edit #2 thành công HTTP `200` (`committed_version = 2`). Đã dọn sạch container/network/image Gate A sau khi lấy bằng chứng.

---

## 3. Gate B — Sao Lưu, Khôi Phục PostgreSQL 16 & Rollback Nhị Phân (`PASS`)

- **Backup & Restore:** Archive `D:\Documents\projects\algo-sim\.superpowers\db-safety-backups\2026-11-19-final-pre-merge-acceptance\pg16_fpa_src.snapshot.tar.gz` (`15,136` B, `sha256: 389b65588ec219b20b80dd43d5bffd908ee113ed892e0c0417563a13e897f38b`) restore sang DB mới đạt 100% parity trên toàn bộ `20` bảng (19 bảng ứng dụng + `alembic_version`), ràng buộc khóa ngoại (`ForeignKeyViolation`), khóa duy nhất (`UniqueViolation`), `nextval` sequence (`+3`) và Step Edit #2 sau restore (`200`, `committed_version = 2`).
- **Rollback nhị phân xuống `main` (`bb046fa22aceff47abe22aa783aa64fc65caee13`):**
  - **Mode A (app-only rollback trên schema 20 bảng giữ legacy Classroom):** Health check & `/api/classes` xác thực trả HTTP `200`.
  - **Mode B1 (`9c4d8e2b7a10`):** Hạ cấp không phá hủy dữ liệu đạt `PASS`.
  - **Mode B2 (`e437149641fa`):** Startup tự động & downgrade phá hủy chưa duyệt bị chặn đúng hợp đồng (`DOWNGRADE_FORBIDDEN_AT_STARTUP`, `DESTRUCTIVE_DOWNGRADE_DATA_LOSS_BLOCKED`); khi Owner cấp phép rõ ràng, schema hạ về `17` bảng với 100% parity dữ liệu Classroom gốc.
- **Bảo toàn DB legacy trên máy host:** Kiểm tra chỉ đọc (bản sao cô lập) trên `D:\Documents\projects\algo-sim\backend\algosim.db` ghi nhận `16` bảng (`46` users, `12` classrooms, `10` assignments, `100` auth_sessions, `16` practice_sessions, `2` simulation_cache) và SHA-256 trước/sau bất biến (`39D676C7B50A925975828434A00D38E3BAC3C5F50E4E2A724A695768C7C83EE3`).

---

## 4. Gate C — Kiểm Toán Phạm Vi Thay Đổi, Option B, LandingView & Workspace

Đối chiếu đầy đủ toàn bộ **`789`** file thay đổi giữa `bb046fa22` và `897d70c9f` (`228` file non-doc + `561` file docs/evaluation):

| Nhóm phạm vi | Số file | Trạng thái kỹ thuật | Trạng thái Owner |
| --- | ---: | --- | --- |
| `C-Classroom (Option B)` | 27 | Đóng & xác minh (`0` route Classroom trong OpenAPI, 18 API cũ trả `404`, `0` caller frontend, 5 bảng legacy giữ nguyên) | `OPTION_B_IMPLEMENTED_AND_VERIFIED` |
| `C-Landing` | 40 | Xác minh kỹ thuật (`0` legacy Informatics, CTA `/ -> /app`, `/` <-> `/library`, auth/guest & responsive đạt) — gồm 38 file đợt trước + 2 file landing bổ sung ở `892e15f0` | `PENDING_OWNER_DECISION` |
| `C-Workspace` | 119 | Xác minh kỹ thuật (host trực tiếp Step Editor & WebGL/Scene3D invariance) | `PENDING_OWNER_DECISION` |
| `Step_Editor_Core` | 20 | Xác minh đầy đủ | `REQUIRED_FOR_RELEASE` |
| `Backend_Hybrid_Geometry_Ingestion` | 12 | Xác minh đầy đủ | `REQUIRED_FOR_RELEASE` |
| `DB_Migration_Safety` | 7 | Xác minh đầy đủ | `REQUIRED_FOR_RELEASE` |
| `Root_Config_Docker` | 3 | Xác minh đầy đủ (`.gitignore`, `GEOMETRY_VISUAL_SPEC.md`, `backend/Dockerfile`) | `SAFE_TO_INCLUDE` / `REQUIRED_FOR_RELEASE` |
| `Docs_And_Evaluation` | 561 | Xác minh bằng `audit_docs_information_architecture.py` | `SAFE_TO_INCLUDE` |

*(Ghi chú đối soát phân loại trong [`ownership-scope-decision-matrix.json`](ownership-scope-decision-matrix.json): `NEEDS_OWNER_DECISION = 159` [`C-Landing 40 + C-Workspace 119`], `REQUIRED_FOR_RELEASE = 61`, `SAFE_TO_INCLUDE = 569`.)*

---

## 5. Gate D — Oracle Hình Học Độc Lập, Nhất Quán Step Editor & Hiệu Năng/Bộ Nhớ (`PASS`)

### 5.1. Oracle `fractions.Fraction` + `math.isqrt` thuần túy (0 import `app.simulation.geometry`)

- **`C1` (`S.ABCD` cạnh đáy `4`, `SA = 4`, mặt cầu ngoại tiếp):** Tâm `I = (2, 2, 2)`, bán kính bình phương `R² = 12` (`2√3`), `IA² = IB² = IC² = ID² = IS² = 12`; mặt trung trực trước sửa (`AB`, trung điểm `(2, 0, 0)`) và sau sửa (`SB`, trung điểm `(2, 0, 2)`) có vector pháp tuyến song song đoạn thẳng, điểm giữa nằm trên mặt và cách đều hai đầu mút; `truc_day` nằm trong cả hai mặt phẳng và đi qua `I`. Ba trường hợp suy biến bị từ chối fail-closed: `collinear_AOC -> COLLINEAR_POINTS`, `duplicate_AA -> INVALID_OPERAND`, `missing_SZ -> MISSING_DEPENDENCY`. Bất biến theo `3` góc camera (`geometry_sha256 = f74cb313be87253fba1bc158c4b9b7b9fbbd722d78b666ef263ecfc4ef90d4c1`).
- **`C2` & `C3` (Xuyên suốt API <-> `StepEditor` <-> `_sync_rebuilt_event` <-> PostgreSQL 16):**
  - Chuỗi sửa: `(α)->(P)`, `AB->SB` (helper hoist `M_AB` cập nhật thành `"Dựng trung điểm của S và B."`, `truc_day` thành `"Dựng giao tuyến của (P) và (β)."`), `SB->AB`, và tỉ lệ `M = 1/3` kéo theo dựng lại `(Q)` và `"Thiết diện MBPF"` với ID đối tượng giữ nguyên.
  - Kiểm toán cả `7` nhánh `_sync_rebuilt_event` + `justification_text` (`"Vì (P) cắt (β) theo giao tuyến d"`) cho `0` token cũ rò rỉ; lặp `5` lần cho cùng digest `fb7c6b2f5fd5e197`.
  - Nguyên tử hóa PG16: `422 MISSING_DEPENDENCY` (`SZ`) giữ nguyên `committed_count = 3`, digest `committed_scene_json` bất biến, ghi audit `ROLLED_BACK`, giữ draft UI; `409 STALE_REVISION_CONFLICT` giữ snapshot PG16 giống hệt từng byte.
- **`C4` (Tổng quát hóa `6` họ hình học):**
  1. **Chóp (`chop-mat-cau-ngoai-tiep`, `the-tich-chop`):** `V² = 256/9` (`V = 16/3`).
  2. **Lăng trụ (`lang-tru-tam-giac-thiet-dien`):** Sửa tỉ lệ `1/3` -> thiết diện 5 đỉnh đồng phẳng, lồi, `area² = 244`.
  3. **Thiết diện (`chop-thiet-dien-ba-diem`, `lap-phuong-thiet-dien-bat-ky`):** Chóp qua các tỉ lệ `1/4` (`area² = 425/2`), `3/4` (`9801/50`), `1/2` (`216`); lập phương thiết diện 6 đỉnh đồng phẳng lồi (`area² = 751109/1764`).
  4. **Mặt phẳng (`mp-vuong-goc-duong`, `mat-phang-tiep-xuc-mat-cau`):** Đổi điểm qua `D`, pháp tuyến `(2, 2, -4)`, `dist(S, Q)² = 50/3` (`5√6/3`).
  5. **Oxyz & giao tuyến (`oxyz-giao-diem-duong-mat`, `mat-phang` cắt mặt cầu):** `M = (1, 1, 0)`, `H = (3, 3, 0)`, `dist(E, P)² = 36`, định lý Pythagoras đường tròn giao tuyến đạt.
  6. **Khoảng cách & vuông góc (`khoang-cach-hai-duong-cheo-nhau`, `khoang-cach-diem-mat-phang-nghieng`):** Giải Gram 2x2 đoạn vuông góc chung `u_SC = 2/3, v_BD = 1/2, norm² = 8/3`; `AH` mặt phẳng nghiêng `norm² = 36/5`.

### 5.2. Hiệu năng, Khởi động lại Backend & Vòng đời Bộ nhớ (`performance-memory-verification.json`)

- **Backend Cold/Warm Kernel & Live PG16 HTTP (`127.0.0.1:18000`):**
  - Khởi động lại Uvicorn `--workers 1` (`N = 5`): `uvicorn_boot_to_health` `p50 = 2,357.529 ms` (`p95 = 2,405.711 ms`), fetch `/state` PG16 đầu tiên `p50 = 47.702 ms`.
  - Cold subprocess (`N = 3`): `cold_first_call` `p50 = 29.543 ms`, `engine_total` `p50 = 16.983 ms`.
  - Warm kernel (`N = 120`): S11 `p50 = 11.046 ms` (`p95 = 17.718 ms`); S1 ratio cascade `p50 = 12.613 ms` (`p95 = 19.820 ms`).
  - Live PG16 HTTP: commit hợp lệ (`N = 40`) RTT `p50 = 70.352 ms` (server engine `p50 = 15.681 ms`, pg commit `p50 = 10.994 ms`); `422` (`N = 30`) `p50 = 36.413 ms`; `409` (`N = 30`) `p50 = 22.491 ms`; `/state` reload (`N = 40`) `p50 = 32.665 ms`.
  - `python tracemalloc` sau `50` chu kỳ edit: bộ nhớ giữ lại sau GC chỉ `0.8 KB` (`peak = 694.04 KB`).
- **Frontend Browser E2E (`N = 20`) & CDP WebGL/DOM Lifecycle:**
  - N=20 E2E step edit roundtrip: mở inline editor `p50 = 40.998 ms`, frontend completion `p50 = 120.570 ms`, Scene3D render `p50 = 37.200 ms`, tổng E2E `p50 = 223.369 ms` (`p95 = 313.897 ms`).
  - CDP 50 chu kỳ sửa liên tiếp: `nodeDelta50Edits = 0`, `listenerDelta50Edits = 0`, `heapGrowthWarmupTo50EditsMB = 2.242 MB` (`31.211 -> 33.453 MB`).
  - CDP 20 lần chuyển bài qua các slug: `webglCreatedTotal = 1` (singleton `_sharedWebGLRenderer` pooling có kiểm soát, không tạo 20 GPU context), `heapGrowth50To20SwitchesMB = 1.901 MB`.
  - Unmount Scene3D về `/library`: `domCanvases = 0`, `scene3dCanvases = 0`, heap giảm từ `35.354` về `33.950 MB` (`+2.739 MB` so với warmup trên workspace). *(Ghi nhận trung thực: ở snapshot sau unmount `/library`, do 1 tab workspace & danh sách bài mở sẵn còn trên thanh tab/DOM `/library`, `domNodeCount = 767`, `cdpNodes = 1631`, `cdpJsEventListeners = 466` so với `/library` ban đầu `714 / 919 / 200`; trong 50 chu kỳ edit liên tục, delta DOM node và listener đều bằng `0`, và khi rời workspace mọi canvas WebGL đều được gỡ khỏi DOM.)*

---

## 6. Gate E — Clean Integration Candidate & Kiểm Thử Toàn Bộ (`PASS`)

- **Mô phỏng Merge cô lập vào `main` (`bb046fa22`):**
  - `git merge-base --is-ancestor`: exit `0` (`134` commit phía trước).
  - `git merge-tree --write-tree`: `7d0b96e4c51655af23dbb7ae0b07be4e860c92ff == HEAD^{tree}`.
  - `git merge --ff-only`: exit `0`; `git merge --no-ff --no-commit`: exit `0`, **`0` xung đột** (dùng `-c core.longpaths=true` trên clone tạm Windows cho đường dẫn ảnh run lịch sử `20260928-...`).
- **Kết quả chạy tuần tự từng suite trên `final-pre-merge-acceptance`:**

| Bộ kiểm thử | Kết quả trực tiếp | Thời gian | Ghi chú `-rsx` / sai lệch thực tế |
| --- | --- | ---: | --- |
| `freeze_evaluation_candidate.py --verify` | `PASS` (exit `0`, `109` file, `78edfa17...`) | `82.6s` | `CACHE_VERSION=132` khớp |
| PG16 `migration_preflight` + `alembic check` | `PASS` (exit `0`, `f8a2c41d9e05`) | `522.2s` | `19` bảng app + `alembic_version`, `No new upgrade operations detected` |
| SQLite sạch `upgrade head` + `preflight` + `check` | `PASS` (exit `0`, `f8a2c41d9e05`) | `697.2s` | `19` bảng app, sạch DDL |
| Backend PG16 (7 module `@pytest.mark.postgres`) | `8 passed, 33 deselected` (exit `0`) | `105.63s` | Bản chạy full-tree 14.029 item bị OS commit-charge `MemoryError` ở `ast.parse` lúc thu thập; tách riêng 7 module postgres đạt `8/8` |
| `pytest -q tests/geometry -rsx` | `12000 passed, 6 skipped, 3 deselected, 9 xfailed` (exit `0`) | `409.78s` | 6 skip do 3 mẫu không có `residual_volume` goal; 3 deselect `-m postgres` đã chạy ở suite trên; 9 xfail đã đăng ký trước |
| `pytest -q tests/semantic_program -rsx` | `1192 passed, 1 skipped` (exit `0`) | `39.14s` | 1 skip `test_scalar_obligations.py:95` (đã có test riêng) |
| Backend root `52` file `test_*.py -k "not postgres"` | `815 passed, 8 deselected` (exit `0`) | `220.00s` | 8 test tên postgres do PG suite đảm nhiệm |
| `npx tsc -b` | `PASS` (exit `0`) | `6.6s` | `0` lỗi kiểu |
| `npm run build` (`tsc -b && vite build`) | `PASS` (exit `0`, 129 module) | `16.4s` | Bundle sạch |
| `npx vitest run --maxWorkers=1` | `193/193` file, **`2278/2278` passed** (exit `0`) | `220.59s` | Ở mặc định `maxWorkers=2` trên host đang tải 16 GiB, `192/193` đạt và `axo-pedagogical-presentation-hardening.test.tsx:425` chạm timeout `5000ms` (`5117ms`) do `GEOMETRY_SAMPLES` tăng từ 11 lên 22 mẫu; chạy `--maxWorkers=1` đạt `3011ms` (<5000ms) và `2278/2278` không sửa test |
| `audit_docs_information_architecture.py` | `PASS` (exit `0`) | `<3s` | `29` root docs, `167` catalogued, `0` unclassified/broken/secrets |

---

## 7. Gate F — Chạy Full-Stack Live Host, Trình Duyệt Desktop/Mobile & REA MCP (`PASS`)

- **Kiến trúc kiểm thử sạch trên host:** Bảo toàn hoàn toàn tiến trình ngoài cổng `127.0.0.1:8000` (`PID 17696/19052`), dựng Uvicorn `--workers 1` cô lập trên `127.0.0.1:18000` nối PG16 `algosim_fpa_live` (`git_sha = 897d70c9f9a3862ef5dcaa45a3f91ffd326e91ed`, `cache_version = 132`) sau Vite `:3001` qua file cấu hình scratch (`vite-fpa.config.mjs`).
- **Luồng người dùng & Edit E2E:**
  - Landing `/` (HTTP `200`) -> `/app`, mở menu đính kèm & upload PNG thật, deep-link `/library` & `/login` kèm reload F5 giữ route đúng.
  - Option B API probes `/api/classes`, `/api/assignments`, `/api/classes/1/session` đều HTTP `404`.
  - Hover pencil (`opacity: 0 -> 1`), ẩn bút khi đang mở textarea, chuyển tab giữa chừng vẫn giữ bản nháp; sửa `(α)->(P)` và `AB->SB` trả `0` stale token, camera chưa orbit giữ `maxDeltaPx = 0`, camera đã orbit & zoom giữ `threeJsCameraPositionDelta = 0`, `threeJsCameraTargetDelta = 0`.
  - Negative `422` (`SZ`, `AOC`, cú pháp) & `409` (`STALE_REVISION_CONFLICT`, `EDIT_SUPERSEDED`) giữ draft UI; F5 sau cascade giữ trạng thái; cuộn dock cô lập không làm dịch canvas; restart backend phục hồi phiên PG16 từ `committedVersion = 20` lên `21` (`latestClientSeq = 25`, `M = [0, 0, 3/2]`).
  - `accept-product-scope.mjs`: **`48/48` checks PASS**, `sourceFingerprint = eda6ced6c56f0827`, `0` lỗi console/page; `accept-live-classroom.mjs --json`: exit `2` (`CLASSROOM_FEATURE_RETIRED`).
  - **REA MCP (`127.0.0.1:9342`):** Kiểm định target `960B9B7E25DA33DB2A16F4F4D37302BD` (`inspect_web_page` `ev_fa4a00ad...`, `capture_web_screenshot` `ev_0a6f715b...`, `150,135` B -> [`images/fpa-rea-mcp.png`](images/fpa-rea-mcp.png)).
  - **Responsive (`overflowX = 0` trên cả 6 viewport + VKB `390x460`):** `1920x1080`, `1440x900`, `1366x768`, `768x1024`, `390x844` (chạm giữ bút hiển thị), `320x568`, `390x460` VKB (`taInViewport=true`, `runInViewport=true`, `cancelInViewport=true`); `0` console error, `0` pageerror, `0` unexpected 5xx.

---

## 8. Gate G — Bảo Toàn Cây Kho, Rủi Ro Tồn Đọng & Checklist Owner

- **An toàn kho & dữ liệu:** Nhánh `main` (`bb046fa22aceff47abe22aa783aa64fc65caee13`), worktree chính `D:\Documents\projects\algo-sim` (chỉ giữ `?? ocr_reconcile.py` nguyên trạng), các worktree bảo vệ (`step-editor-release-candidate`, `pre-merge-risk-closure`, `owner-scope-resolution`) và file DB `D:\Documents\projects\algo-sim\backend\algosim.db` đều nguyên vẹn tuyệt đối; không chạm cổng `8000`.
- **Rủi ro / Hạng mục tồn đọng minh bạch sau phát hành (không chặn quyết định merge):**
  1. Quyết định phạm vi từ Owner cho `C-Landing` (`40` file), `C-Workspace` (`119` file) và lệnh merge/push (`C-Release`).
  2. Hậu merge nên tách hoặc cấp timeout rõ ràng cho sweep 22 mẫu `axo-pedagogical-presentation-hardening.test.tsx:425` để chạy ổn định cả khi bật `--maxWorkers=2` trên máy dev 16 GiB RAM.
  3. Theo dõi đơn worker `--workers 1` (khoá thiết kế hiện tại của `StepEdit` lock bộ nhớ + PG16 `FOR UPDATE`) nếu tương lai mở rộng multi-worker cần chuyển lock request/seq vào PG/Redis.
  4. `MODEL_STATUS = MODEL_NOT_TRAINED`, `PRODUCTION_DEPLOYMENT_VERIFIED = NO`, `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`.

Mời Owner xem và chốt quyết định tại [`owner-approval-checklist.md`](owner-approval-checklist.md).
