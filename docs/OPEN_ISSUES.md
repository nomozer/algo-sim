# OPEN_ISSUES.md — Danh mục các vấn đề kỹ thuật đang mở

> **Tài liệu Canonical cho việc theo dõi các vấn đề và giới hạn kỹ thuật của hệ thống.**
> Mọi issue đều có Stable ID theo tiền tố chuẩn: `ISSUE-ARCH-*`, `ISSUE-EVAL-*`, `ISSUE-DOCS-*`, `ISSUE-OPS-*`, `ISSUE-RESEARCH-*`.
> Chỉ ghi nhận các vấn đề được xác nhận bởi bằng chứng thực tế từ repository.

---

### ISSUE-OPS-FRONTEND-TESTS-SPACE-PATH
- **description:** 11 frontend test files build repository paths from `new URL(..., import.meta.url).pathname`, which keeps `%20`; from a worktree path containing a space they fail with ENOENT (and `spawnSync git` with a bad cwd).
- **evidence:** `docs/evaluation/geometry/runs/w09-verify-cleanup/diagnostics/logs/T3_FULL_GATE_SPACED_PATH_fe3eccee.log` (vitest 23 failed / 860).
- **impact:** Authoritative runs must use a path without spaces; `full-gate.mjs` itself is space-safe (`repoRootOf`).
- **scope:** Frontend test path resolution only.
- **status:** RESOLVED (w10, `1eca93d7` + `c7fee8f8`) — 12 test files and the two scripts they import (`evidence.mjs`, `certify-sweep-w12.mjs`) use `fileURLToPath`/`URL`; a guard in `src/test-tiers.test.ts` follows test imports transitively and forbids the old pattern (red on 12 files, then on the 2 scripts, before the fixes). T3 from `D:/tmp/w10 space/algo-sim` at `40ce889f`: `FULL_PRODUCT_GATE_PASS`. Evidence: `docs/evaluation/geometry/runs/w10-pedagogical-playback/diagnostics/logs/T3_FULL_GATE_SPACED_40ce889f.log`. Residual (hand-run browser scripts): `ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH`
- **owner_class:** TEST HARNESS
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** every test resolves paths with `fileURLToPath`; `npm run test:full` passes from a detached worktree whose path contains a space.
- **verify:** `git worktree add --detach "<tmp with space>" HEAD` then `cd "<tmp with space>/frontend" && npm ci --offline && npm run test:full`

### ISSUE-OPS-BROWSER-SCRIPTS-SPACE-PATH
- **description:** About twenty hand-run browser scripts in `frontend/scripts/` (`accept-*.mjs`, `certify-*.mjs`, `audit-composition.mjs`, …) still build paths from `new URL(...).pathname`, which keeps `%20`.
- **evidence:** `grep -n "\.pathname" frontend/scripts/*.mjs` (w10); the test graph itself is clean (`src/test-tiers.test.ts` guard).
- **impact:** Those scripts fail when run by hand from a checkout whose path contains a space; no gate or test depends on them.
- **scope:** Hand-run browser tooling only.
- **status:** OPEN
- **owner_class:** TEST HARNESS
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** every script under `frontend/scripts/` resolves paths with `fileURLToPath`; the guard is extended from the test import graph to the whole directory.
- **verify:** `grep -c "\.pathname\.replace" frontend/scripts/*.mjs` = 0

### ISSUE-EVAL-ORBIT-EVIDENCE-INTERMITTENT
- **description:** The browser orbit evidence can abort with `ORBIT_EVIDENCE_TIMEOUT` when point labels are still at their unprojected positions; the immediate rerun at the same commit passes.
- **evidence:** `docs/evaluation/geometry/runs/w09-verify-cleanup/diagnostics/logs/BROWSER_ATTEMPT1_ORBIT_TIMEOUT_defb77ed.log`, `diagnostics/MEASUREMENT_ATTEMPTS.json`.
- **impact:** An authoritative run may need a second attempt; every attempt is recorded, none is hidden.
- **scope:** Browser evidence harness (label readiness before orbit).
- **status:** RESOLVED (w10) — root causes named: fixed pixel drags could end at a view that changes no hidden edge (the gate then waited for something that never came), and clicks/drags acted blind (a click under the sticky navigation bar opened the sign-in overlay). Now the orbit is PLANNED from the product's own view metrics (`planOrbit`: keeps depth AND changes the predicted hidden set), readiness is condition-based (camera settle within tolerance → gesture → hidden set changed) with transitions and timeout reasons recorded, and `trustedClick`/`trustedOrbit` verify the target is uncovered (`5e6e1583`, `40ce889f`). Authoritative run `40ce889f`: suite orbit 12/12 with the planned gesture passing first time 12/12; learner runner 60/60 orbit laps (5 per family × viewport). Evidence: `docs/evaluation/geometry/runs/w10-pedagogical-playback/`
- **owner_class:** EVALUATION
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** root cause named; 5 consecutive authoritative runs without an orbit abort.
- **verify:** `node frontend/scripts/compiler-scene-replay.mjs --suite frontend/scripts/generic-tier-a-scenarios.json --fixture-root <inputs> --ra <out>` (x5)

### ISSUE-EVAL-OCCLUSION-TERMINAL-CAMERA-IDENTITY
- **description:** Fixed-camera evidence đang băm snapshot trước khi OrbitControls damping đạt terminal state; 2 cases (`triangular_prism`, `cube`) lệch frozen identity.
- **evidence:** `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/results/VERIFICATION_SUMMARY.json` (`FROZEN_CAMERA_IDENTITY_MISMATCH`).
- **impact:** Frozen human expected sets không thể được dùng làm authority cho hai case cho tới khi terminal camera được canonicalize và đăng ký bằng commit test-only riêng.
- **scope:** Browser evidence harness / camera snapshot registration.
- **status:** RESOLVED (w09, 7b8528a9 + fe3eccee) — verified preimages of the registered hashes + projection equivalence ≤ 0.5 px; 3 EXACT, 3 CANONICAL_EQUIVALENT; registry byte-identical. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`
- **owner_class:** EVALUATION / VISUALIZATION
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** Camera hash lấy sau khi damping dừng (float canonicalized); 0 `FROZEN_CAMERA_IDENTITY_MISMATCH` trên sáu family trong một run mới, registry đóng băng không bị sửa bởi product/oracle.
- **verify:** `cd frontend && node scripts/compiler-scene-suite.mjs` rồi `backend/.venv/Scripts/python.exe backend/scripts/measure_scene3d_occlusion.py` (run mới theo `docs/evaluation/RUN_NAMING.md`)

### ISSUE-EVAL-OCCLUSION-IMMUTABLE-AFTER-SETTLE
- **description:** Mobile immutable-frame gate bắt đầu trước khi camera thực sự settled, nên 5 families ghi nhận recomputation trong 120 frame được coi là immutable.
- **evidence:** Cùng `VERIFICATION_SUMMARY.json`, mobile `immutable_120_frames` failures.
- **impact:** Performance evidence chưa sạch dù product classifier correctness đã khớp oracle.
- **scope:** Browser/performance gate scheduling.
- **status:** RESOLVED (w09, 7b8528a9 + 91d3e9c3) — root cause was also in the product: the classifier keyed on raw floats while idle damping rewrote the pose every mobile frame; canonical camera key, settle gate, and zeroed window counters. 12/12 windows, 0 recomputes. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`
- **owner_class:** EVALUATION / PERFORMANCE
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** Cửa sổ 120 frame chỉ bắt đầu sau khi camera settled; mobile `immutable_120_frames` PASS 6/6 family, fault gate vẫn đỏ khi tiêm recomputation.
- **verify:** `cd frontend && npx vitest run src/simulations/domains/geometry/scene3d-occlusion-gates.test.ts && node scripts/compiler-scene-suite.mjs`

### ISSUE-EVAL-FRONTEND-BOUNDARY-GUARD-FALSE-POSITIVE
- **description:** Legacy frontend whole-source regex cấm chuỗi `boundary` quá rộng và bắt nhầm field hợp lệ `boundary_edge_ids`.
- **evidence:** Frontend full result 904 pass, 1 fail trong correction report 2026-09-28.
- **impact:** Full frontend gate đỏ dù failure hiện được chẩn đoán là guard defect; phải thay bằng assertion đúng ranh giới trước khi gọi sạch.
- **scope:** Frontend architecture/source guard test only.
- **status:** RESOLVED (w09, 1f151f8d) — assertion on declared field names; frontend full 906/0. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`
- **owner_class:** TEST HARNESS
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** Regex `/boundary|corners|extent/` tại `frontend/src/simulations/domains/geometry/scene3d.test.tsx` thay bằng assertion cấm đúng field cũ nhưng cho `boundary_edge_ids`; guard vẫn đỏ khi tiêm field bị cấm; frontend full 0 fail.
- **verify:** `cd frontend && npx vitest run src/simulations/domains/geometry/scene3d.test.tsx && npm test`

### ISSUE-EVAL-BACKEND-35-FAILURES-UNCLASSIFIED
- **description:** 35 backend full-suite failures chưa được phân loại riêng thành intended golden update, stale candidate/report guard, harness/environment defect hoặc real product regression.
- **evidence:** Backend full result 6268 pass, 35 fail, 1 skip, 1 deselect trong correction report 2026-09-28.
- **impact:** Không được suy tất cả là stale test hoặc tất cả là product regression; verification vẫn đỏ cho tới khi từng failure có classification và rerun evidence.
- **scope:** Backend full regression triage.
- **status:** RESOLVED (w09) — fresh reproduction 31 (main) + 3 (detached-only) = 34, each reconciled; 28 were a REAL_PRODUCT_REGRESSION (raw kernel objects in scene3d.events, HTTP 500 at the cache write), fixed in f337323f. The 35th of the prior count was never itemized: NOT_RECOVERABLE. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`results/BACKEND_FAILURE_RECONCILIATION.json
- **owner_class:** EVALUATION / TEST HARNESS / PRODUCT
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** Mỗi failure có một nhãn (golden update có chủ đích · stale guard · harness/env · product regression) kèm rerun; không đổi golden/hash khi chưa có classification.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q -rf`

### ISSUE-OPS-FULL-GATE-PYTHON-ENV-RESOLUTION
- **description:** Full-gate runner chưa resolve Python interpreter/environment một cách độc lập khi chạy trong detached worktree.
- **evidence:** Handoff và verification summary của run occlusion 2026-09-28.
- **impact:** Authoritative clean-worktree verification có thể thất bại do environment path thay vì product state.
- **scope:** Full-gate runner / detached-worktree environment discovery.
- **status:** RESOLVED (w09, 1d1397fa + defb77ed) — resolvePython with structured failure; detached T3 FULL_PRODUCT_GATE_PASS with main_worktree_venv. Evidence: `docs/evaluation/geometry/runs/w09-verify-cleanup/`
- **owner_class:** OPERATIONS / TEST HARNESS
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO
- **acceptance:** `full-gate.mjs` chạy trong detached worktree sạch mà tìm được interpreter backend có khai báo (không ngầm dựa vào `.venv` của cây chính), ghi đường dẫn interpreter vào artifact.
- **verify:** `git worktree add --detach <tmp> HEAD` rồi `cd <tmp>/frontend && npm run test:full`

### ISSUE-ARCH-COMPILER-COVERAGE-NARROW
- **description:** Primitive compiler hiện tại chỉ hỗ trợ một họ bài toán đơn lẻ là tính thể tích khối chóp có đáy tam giác vuông (`right_triangle_base_pyramid_volume`).
- **evidence:** `backend/app/simulation/compiler/primitive_compiler.py`, báo cáo `docs/GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE.md`.
- **impact:** Hệ thống chưa thể biên dịch tất định các họ hình học không gian phổ biến khác trong chương trình THPT.
- **scope:** `backend/app/simulation/compiler/`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-COMPILER-FIRST-ROUTING
- **description:** Cổng định tuyến compiler-first trong pipeline chính chưa được xây dựng; hệ thống hiện tại vẫn đi qua LLM synthesis mặc định.
- **evidence:** `backend/app/ai/pipeline.py`, cờ `DEFAULT_MODE = LLM_ONLY`.
- **impact:** Người dùng chưa được hưởng lợi từ tốc độ và tính tất định của compiler trong luồng chạy thực tế.
- **scope:** `backend/app/ai/pipeline.py`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-FALLBACK-MECHANISM
- **description:** Chưa có cơ chế chuyển giao tự động và an toàn từ compiler sang LLM synthesis khi bài toán nằm ngoài tập primitive được hỗ trợ.
- **evidence:** `backend/app/simulation/compiler/` chưa có module router/fallback adapter.
- **impact:** Nếu bật compiler-first mà gặp bài toán không thuộc diện hỗ trợ thì hệ thống sẽ dừng thay vì fallback.
- **scope:** `backend/app/ai/pipeline.py`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-CANARY-OR-ROLLBACK
- **description:** Chưa có cơ chế phân luồng canary để thử nghiệm tỉ lệ nhỏ trên production và chưa có kịch bản rollback tức thì khi gặp lỗi biên dịch.
- **evidence:** Chưa có middleware/routing layer hỗ trợ canary splitting trong `backend/app/main.py`.
- **impact:** Rủi ro gián đoạn dịch vụ khi kích hoạt tính năng mới trên toàn hệ thống.
- **scope:** `backend/app/`
- **status:** OPEN
- **owner_class:** OPERATIONS / ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-SPATIAL-LAYOUT-SOLVER
- **description:** Chưa có bộ giải bố cục không gian 3D tự động; tọa độ các điểm hiện do các bước dựng hình cơ sở xác định cục bộ, có thể gây mất cân đối thị giác ở các góc phức tạp.
- **evidence:** `backend/app/simulation/` thiếu solver tối ưu hóa ràng buộc tọa độ toàn cục.
- **impact:** Một số hình vẽ phức tạp có thể bị dồn góc hoặc khó nhìn trong không gian 3D.
- **scope:** `backend/app/simulation/` & `frontend/src/`
- **status:** OPEN
- **owner_class:** VISUALIZATION
- **suggested_wave:** P3 (Visualization)
- **default_switch_blocker:** NO

### ISSUE-ARCH-NO-HIDDEN-LINES
- **description:** Product repair đã triển khai dynamic hidden-line spans và oracle độc lập, nhưng verification browser/camera/performance tổng vẫn chưa sạch.
- **evidence:** `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/REPORT.md`; architecture amendment `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`.
- **impact:** Không còn là missing implementation; vẫn chưa được nâng thành human-accepted hoặc merge-ready cho tới khi năm issue verification ở đầu file được khép bằng evidence mới.
- **scope:** `frontend/src/simulations/domains/geometry/`
- **status:** REPAIR_VERIFIED_PENDING_HUMAN_VISUAL_REVIEW (w09: all automated gates PASS)
- **owner_class:** VISUALIZATION
- **suggested_wave:** `VERIFICATION_CLEANUP_AFTER_OCCLUSION_REPAIR`
- **default_switch_blocker:** NO

### ISSUE-ARCH-NO-OCR-IMAGE-PIPELINE
- **description:** Chưa triển khai đường ống bóc tách vùng đề bài và OCR nhận diện văn bản toán học từ ảnh chụp camera điện thoại.
- **evidence:** `backend/app/ingestion/input.py` chỉ tiếp nhận text đầu vào.
- **impact:** Người dùng phải gõ lại đề bài bằng văn bản thay vì chụp ảnh trực tiếp từ sách giáo khoa.
- **scope:** `backend/app/ingestion/`
- **status:** OPEN
- **owner_class:** INGESTION
- **suggested_wave:** P4 (Image Acquisition)
- **default_switch_blocker:** NO

### ISSUE-EVAL-TOKEN-OPTIMIZATION-NOT-ESTABLISHED
- **description:** Việc giảm token tiêu thụ của compiler so với LLM synthesis mới chỉ là quan sát thực nghiệm trên một lát cắt nhỏ, chưa được xác lập như một đặc tính đo lường tin cậy ở quy mô production.
- **evidence:** `docs/MODEL_VARIANCE_EVIDENCE_REVIEW.md`, `FINAL_DECISION.json`.
- **impact:** Không được tuyên bố trong luận văn rằng compiler đã tối ưu hóa token ở mức độ hệ thống hoàn chỉnh.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P6 (Thesis Evaluation)
- **default_switch_blocker:** NO

### ISSUE-EVAL-STATISTICAL-SIGNIFICANCE-UNESTABLISHED
- **description:** Số lượng mẫu kiểm thử (n-count) của các phép đo live hiện tại còn nhỏ, chưa đủ để đưa ra các kết luận có ý nghĩa thống kê.
- **evidence:** `docs/THESIS_READINESS.md §7`, `docs/EVIDENCE_INDEX.md`.
- **impact:** Các công bố định lượng cần được giới hạn trong phạm vi thực nghiệm định tính hoặc nghiên cứu tình huống (case study).
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P6 (Thesis Evaluation)
- **default_switch_blocker:** NO

### ISSUE-EVAL-P03-P05-HISTORICAL-CAUSE-NOT-ESTABLISHED
- **description:** Nguyên nhân gốc rễ của cụm lỗi lịch sử Analyze P03/P05 (`MODEL_MALFORMED_RELATION`) chưa được xác lập chắc chắn vì hai ca live retry đều trả về kết quả hợp lệ mà không tái hiện lỗi.
- **evidence:** `docs/MODEL_VARIANCE_EVIDENCE_REVIEW.md`, `FINAL_DECISION.json` (`HISTORICAL_ROOT_CAUSE = NOT_ESTABLISHED`).
- **impact:** Cần duy trì giả thuyết về tính biến thiên tự nhiên của mô hình (model variance) và tiếp tục theo dõi qua các lần đo sau.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** NO

### ISSUE-EVAL-P03-P05-TOKEN-UNKNOWN
- **description:** Lượng token sử dụng của hai request P03 và P05 trong đợt live retry trước đây được ghi nhận là 0 do giới hạn của client HTTP, sau đó được đính chính thành UNKNOWN.
- **evidence:** `docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/MACHINE_RAW_OUTPUT.json`.
- **impact:** Số liệu token của wave đó không được đưa vào bảng phân tích so sánh định lượng của luận văn.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** NO

### ISSUE-DOCS-CRLF-GITATTRIBUTES-RISK
- **description:** Rủi ro chuyển đổi ký tự kết thúc dòng (CRLF / LF) giữa môi trường phát triển Windows và máy chủ Linux có thể ảnh hưởng đến hash SHA-256 của các artifact văn bản.
- **evidence:** `.gitattributes` hiện quản lý chuẩn hóa LF cho các file text và JSON.
- **impact:** Cần đảm bảo mọi công cụ đo lường và kiểm chứng đều áp dụng chuẩn hóa LF trước khi băm nội dung.
- **scope:** Repository configuration
- **status:** OPEN
- **owner_class:** DOCUMENTATION / OPS
- **suggested_wave:** P0 (Documentation Hardening)
- **default_switch_blocker:** NO

### ISSUE-OPS-ORPHANED-TEMP-DIRECTORIES
- **description:** Các thư mục tạm được tạo trong quá trình chạy test worktree (ví dụ `D:/tmp/mvep-*`, `D:/tmp/algo-sim-*`) có thể tồn đọng nếu quy trình dọn dẹp gặp sự cố ngoài ý muốn.
- **evidence:** Thư mục `D:/tmp/` chứa các artifacts bằng chứng máy từ các wave trước. w10 để lại, NGOÀI git: `D:/tmp/w10-out` và `D:/tmp/w10-build.log` (bản dựng/thử nghiệm dev), `D:/tmp/w10-freeze4` (worktree đóng băng đã gỡ khỏi git; xoá thư mục bị từ chối vì một tiến trình đang giữ — chỉ còn bản sao file đã commit), `D:/Documents/projects/tmp-dist-exp` (bản dựng thử nghiệm depth test). Không chứa gì cần giữ; mọi bằng chứng đã nằm trong run w10.
- **impact:** Chiếm dụng dung lượng đĩa và có nguy cơ gây nhầm lẫn nếu không được quản lý vòng đời rõ ràng.
- **scope:** Scripts & Test harnesses
- **status:** OPEN
- **owner_class:** OPERATIONS
- **suggested_wave:** P0 (Documentation Hardening)
- **default_switch_blocker:** NO

### ISSUE-ARCH-PRISM-COMPILER-GAP
- **description:** Primitive compiler thiếu primitive construct_prism(name, base_cycle, top_cycle, correspondence), FactGraph thiếu loại nút prism, và 10 tầng phối hợp khác (RequestContract, relations, adapter, eligibility, IR, gates, topology, measurement, routing, frontend renderer) chưa hỗ trợ họ lăng trụ đứng đáy tam giác vuông đã tiền đăng ký (right_triangle_base_right_prism_volume).
- **evidence:** `docs/SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE.md`, `docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/VERTICAL_SLICE_SCOPE_MAP.json`.
- **impact:** Họ bài `right_triangle_base_right_prism_volume` chưa thể biên dịch tất định cho đến khi hoàn thành vertical slice qua đủ 12 tầng kỹ thuật.
- **scope:** `backend/app/simulation/geometry_compiler/`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-REQUEST-CONTRACT-PRISM-GAP
- **description:** `RequestContract` tại baseline thiếu trường chở `prism identity`, `base_cycle`, `top_cycle`, hay `correspondence` (`REQUEST_CONTRACT = CHANGE_REQUIRED`). Bế tắc kiến trúc giữa Direction A và Direction B đã được giải quyết về mặt thiết kế tại `docs/GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE.md` thông qua kiến trúc 2 lớp (Internal Discriminated Union vs Model Transport Flattened Schema). Vấn đề hiện tại là triển khai mã nguồn sản phẩm trong vertical slice.
- **evidence:** `docs/SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE.md`, `docs/GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE.md`.
- **impact:** Cần áp dụng hợp đồng đã thiết kế vào `request_contract.py` và `contract_adapter.py` trong vertical slice tiếp theo.
- **scope:** `backend/app/simulation/semantic_program/request_contract.py`, `backend/app/simulation/geometry_compiler/contract_adapter.py`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES


