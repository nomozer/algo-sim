# OPEN_ISSUES.md — Danh mục các vấn đề kỹ thuật đang mở

> **Tài liệu Canonical cho việc theo dõi các vấn đề và giới hạn kỹ thuật của hệ thống.**
> Mọi issue đều có Stable ID theo tiền tố chuẩn: `ISSUE-ARCH-*`, `ISSUE-EVAL-*`, `ISSUE-DOCS-*`, `ISSUE-OPS-*`, `ISSUE-RESEARCH-*`.
> Chỉ ghi nhận các vấn đề được xác nhận bởi bằng chứng thực tế từ repository.

---

### ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE
- **description:** The compiler writes one hand-made statement sequence per family. The triangular pyramid (`bien_dich`) and triangular prism (`_bien_dich_prism`) emit no height segment, no lateral-edge group and (prism) no top face, so their timeline is only givens/points → base → whole solid; the rectangular pyramid and box paths have those steps. Root cause of the w12 human findings W12-H1/H2.
- **evidence:** `backend/app/simulation/geometry_compiler/compiler.py` (`bien_dich` ~917, `_bien_dich_prism` ~1046, `_bien_dich_rectangular_pyramid` ~1153, `_bien_dich_cuboid` ~1315); `docs/evaluation/geometry/runs/w13-geometry-preregistration/inputs/W12_HUMAN_VISUAL_REVIEW.json`; inventory item NA-18.
- **impact:** Formation quality depends on which family a problem lands in; patching the two families alone would repeat the defect for every new shape.
- **scope:** `backend/app/simulation/geometry_compiler/`, trace events / `scene3d` formation.
- **status:** PARTIAL (w14, `44f2dd32`) — one shape-class completion pass (`semantic_program/formation.py::hoan_thien_dung_hinh`, face-table leaf `solid_faces.py`) runs in `route.verify_and_compile` and `pipeline._dung_scene3d` for compiler **and** LLM programs; the compiler no longer hand-writes height, lateral or top statements; roles are produced in `simulation_state` and only carried by `scene3d`; an AST guard forbids family branches. Measured at `380db58c`: role coverage 12/12 (six families × desktop/mobile) against an independent expectation, playback 12/12 × 19, filmstrips in `docs/evaluation/geometry/runs/w14-generic-formation-assumption/images/<family>/FILMSTRIP.png`; served gold p1, p2 `COMPLETED`, answers unchanged. **Not closed:** the refused thesis-gold negative `n2_khoi_ghep_bu_can_boolean` (an untyped box) stays `AMBIGUOUS_TOPOLOGY` — the enforced set as written includes it (user decision W14-D1 in the run's `HANDOFF.md`); the frozen hidden-line expectations no longer transfer to the four scenes S4 changed (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`). No human has reviewed the new formation.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** `COMPLETE_SHAPE_CLASS_FORMATION` (after W14-D1), then human re-review
- **default_switch_blocker:** NO
- **acceptance:** S1–S3 of the preregistration: every pyramid/prism family shows the required semantic roles as separate observable steps from one code path, with no branch on a family ID.
- **verify:** the semantic-coverage tests and AST guard named in the preregistration.

### ISSUE-ARCH-SOURCE-LENGTH-UNLABELLED-PHRASE
- **description:** A labelled length the source reader does not recognise (*"AB dài 5 cm"*) binds no segment, so the number falls under the standalone-value rule and a program may declare a different segment (`AC = 5`) as GIVEN without any gate objecting.
- **evidence:** `docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/SOURCE_GROUNDING_PHRASING_PROBE.json` row `standalone_wrong_segment` (offline, 0 model calls); inventory item NA-57.
- **impact:** A GIVEN value can be attached to the wrong segment; the figure and the answer can be wrong while every gate is green.
- **scope:** `backend/app/simulation/semantic_program/segment_relation.py`, `grounding_gate.py` (one length reader).
- **status:** RESOLVED (w14, `2f2c97b2`; `CACHE_VERSION` 105 → 106 in `733435ac`, served → rejected) — one closed connector vocabulary `segment_relation._NOI_DO_DAI` (`=`, `bằng`, `dài`, `có độ dài`) for the length reader and the GIVEN-evidence labeler (`nhan_doan_truoc`; `_NHAN_TRUOC` and `_DO_DAI_CO` deleted). The w13 probe rerun differs in exactly the two registered rows (`docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/SOURCE_GROUNDING_PHRASING_PROBE_W14.json`); `"cạnh AB có độ dài 5"` with `AC = 5` is refused (`tests/geometry/test_source_length_reader.py`). No fuzzy matching: `"AB dài hơn 5"` stays unread.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** `W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION` (Track C)
- **default_switch_blocker:** NO
- **acceptance:** `XY dài v [unit]` is read as a labelled length; the probe row is refused and every other probe row keeps its result.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/source_grounding_probe.py <new-output.json>` and compare its rows with the w13 file (the probe refuses to overwrite an existing result).

### ISSUE-OPS-TEST-EXTERNAL-EVIDENCE-PATH
- **description:** `test_raw_response_identity_reproduced` asserts that `D:/tmp/live_retry_evidence/PRISM_SCHEMA_LIVE_P01_raw_response.json` exists. The file lives outside git and the test has no marker or skip, so it runs in the default pytest and in T3.
- **evidence:** `backend/tests/geometry/test_evidence_identity_reconciliation.py:97-107`; inventory item NA-05.
- **impact:** T3 passes only on the machine that holds that directory; a clean checkout fails for a reason unrelated to the product. The raw model output cannot be committed (AGENTS.md §4).
- **scope:** Backend test environment only.
- **status:** RESOLVED (w14, `0daa6354`) — the test carries the opt-in marker `external_evidence` (deselected by default in `backend/pytest.ini`) and reads `ALGOSIM_LIVE_RETRY_EVIDENCE_DIR`, failing with `NOT_PORTABLE_EXTERNAL_EVIDENCE` when it is unset; `tests/test_test_portability.py` (AST) forbids absolute paths outside opt-in tests.
- **owner_class:** TEST HARNESS
- **suggested_wave:** backlog item 1 of the W13 preregistration
- **default_switch_blocker:** NO
- **acceptance:** the check sits behind an opt-in marker and reports `NOT_PORTABLE_EXTERNAL_EVIDENCE` when the file is absent; the default suite never reads a path outside the repository.
- **verify:** `cd backend && .venv/Scripts/python.exe -m pytest tests/geometry/test_evidence_identity_reconciliation.py -q` on a checkout without `D:/tmp/live_retry_evidence`.

### ISSUE-ARCH-PROMPT-OBLIQUE-SECTION-STALE
- **description:** The production geometry synthesis prompt (`program_skill_for` → `geometry_program_generator.md`) still tells the model that an oblique plane through a cylinder or cone "cannot be expressed", while the IR has `intersect_plane_curved_ellipse` (cylinder 2026-09-07, cone 2026-09-08) and the grammar card sent with the prompt lists it.
- **evidence:** `backend/app/ai/skills/geometry_program_generator.md:85-86`; `backend/app/simulation/semantic_program/ir_static_check.py` (`_CHU_KY`); inventory item NA-52.
- **impact:** Contradictory model-facing guidance. The final acceptance still served both ellipse cases, so the card wins today; the contradiction can cost repairs on other problems.
- **scope:** Model-facing surface (prompt hash ⇒ `CACHE_VERSION` decision and re-measurement).
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** a wave allowed to change the model surface (backlog item 2)
- **default_switch_blocker:** NO
- **acceptance:** the prompt states the oblique-section capability and its closure (ellipse only; parabola/hyperbola refused) consistently with the card; the surface change is measured.
- **verify:** `grep -n "xiên" backend/app/ai/skills/geometry_program_generator.md` and the prompt fingerprint in `runtime_doctor.py`.

### ISSUE-ARCH-EXACT-PLACEMENT-FEASIBILITY
- **description:** Points live in Q³ only. A figure without a rational placement (an equilateral triangle in a coordinate plane needs √3; a regular pyramid given by base and lateral edge usually needs an irrational height) cannot be built exactly, and there is no stable refusal code for it. `geometry/exact.py::hf` turns a JSON float into `Fraction(x).limit_denominator(10**9)` while its docstring says floats keep their exact binary value, so approximate decimal coordinates enter the exact kernel looking exact.
- **evidence:** `backend/app/simulation/geometry/exact.py:71-93`; inventory items NA-42, NA-54; matrix v2 groups G01–G04.
- **impact:** Regular solids and angle-defined oblique solids are not exactly constructible; whether approximate coordinates are ever served is NOT_MEASURED.
- **scope:** `backend/app/simulation/geometry/` (kernel boundary), grounding of coordinates.
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** backlog item 3 (measure first with a 0-call probe)
- **default_switch_blocker:** NO
- **acceptance:** a deterministic placement-feasibility check with a stable refusal code; the float policy is either a refusal or a stated contract; the docstring matches the code.
- **verify:** the probe named in the W13 preregistration §7.

### ISSUE-DOCS-STALE-CAPABILITY-CLAIMS
- **description:** Living docs still state retired capability absolutes: "8 expressions · 6 statements · 5 measures" and `CURVED_GEOMETRY_SUPPORT = NONE` (CURRENT_STATE §3), curved and non-convex solids as deliberate gaps (CURRENT_STATE §4), "convex polyhedra only, no curved surfaces" (README §9–10), non-convex out of scope (THESIS_ARCHITECTURE §A/§J).
- **evidence:** inventory item NA-53; sync-locked identity row of CURRENT_STATE (11 · 9 · 7); `backend/app/simulation/product_capability.py`.
- **impact:** A reader of the "current" sections learns the opposite of the code.
- **scope:** `docs/CURRENT_STATE.md`, `README.md`, `docs/THESIS_ARCHITECTURE.md`.
- **status:** PARTIAL — W13 added correction banners to CURRENT_STATE §3/§4; README and THESIS_ARCHITECTURE are not edited yet.
- **owner_class:** DOCS
- **suggested_wave:** documentation wave (backlog item 8)
- **default_switch_blocker:** NO
- **acceptance:** no living doc states a capability list that differs from `runtime_identity()` / `product_capability.py`; lists link to the authority instead of copying it.
- **verify:** `grep -n "CURVED_GEOMETRY_SUPPORT\|LỒI" README.md docs/CURRENT_STATE.md docs/THESIS_ARCHITECTURE.md`

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

### ISSUE-EVAL-CDP-SEND-NO-TIMEOUT
- **description:** `BrowserSession._send` (`frontend/scripts/browser-runner.mjs`) returns a promise with no deadline, and pending requests are never rejected when the DevTools socket closes or errors. One DevTools request whose response never arrives stalls a browser run forever instead of failing it with a reason.
- **evidence:** w12 attempt PLAYBACK-2a (`docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/diagnostics/logs/PLAYBACK_attempt1_HANG_7b039621.log`, `diagnostics/MEASUREMENT_ATTEMPTS.json`): the learner runner wrote all nine captures of cuboid/desktop, then printed nothing for about 20 minutes in an orbit lap; a separate DevTools probe of the same page answered at once (render loop running, "Bước 5/5", nothing selected). The rerun at the same commit passed 12/12 under a `timeout` watchdog.
- **impact:** A stalled run produces no verdict and has to be found and killed by hand; until then authoritative browser runs need an external watchdog.
- **scope:** Browser evidence harness (`browser-runner.mjs`, used by the suite and the playback runner).
- **status:** OPEN — found in w12; the harness was not changed in that wave (a deadline turns a hang into a failure, not into a pass).
- **owner_class:** TEST HARNESS
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** every `_send` has a deadline and pending requests are rejected on socket close/error; a run fails with a named reason instead of hanging.
- **verify:** a node test that drops one DevTools response and expects a rejection within the deadline.

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
- **w13_audit:** the description and paths are stale at `bf5a7907` — the package is `backend/app/simulation/geometry_compiler/` and `compiler.py:41-53` supports six families (right-triangle pyramid and prism, rectangular pyramid, cuboid, cube, right square prism). What remains narrow is listed by layer in `docs/architecture/geometry_capability_matrix_v2.json` (`L08 compiler_rule`) and in `ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE`.
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
- **w13_audit:** the evidence line is stale — a photo route exists (`POST /api/image/extract`, `backend/app/ingestion/image_extraction.py`: multimodal transcription, deterministic assessment, learner review before analyze). A dedicated OCR pipeline is still absent; whether this issue is still wanted is a scope decision.
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
- **evidence:** Thư mục `D:/tmp/` chứa các artifacts bằng chứng máy từ các wave trước. w10 để lại, NGOÀI git: `D:/tmp/w10-out` và `D:/tmp/w10-build.log` (bản dựng/thử nghiệm dev), `D:/tmp/w10-freeze4` (worktree đóng băng đã gỡ khỏi git; xoá thư mục bị từ chối vì một tiến trình đang giữ — chỉ còn bản sao file đã commit), `D:/Documents/projects/tmp-dist-exp` (bản dựng thử nghiệm depth test). Không chứa gì cần giữ; mọi bằng chứng đã nằm trong run w10. w11 để lại: hai worktree detached CÒN ĐĂNG KÝ — `D:/tmp/w11-d1` (đo) và `D:/tmp/w11 space/algo-sim` (T3) — gỡ bằng `git worktree remove <path>`; `D:/tmp/w11-before` (đã gỡ đăng ký, xoá bị từ chối quyền); `D:/tmp/w11-gen`, `D:/tmp/w11-attempt1`, `D:/tmp/w11-*.log`, `D:/tmp/w11-schema-*.txt`. Mọi thứ cần giữ đã nằm trong run w11. **w12 (2026-10-01) dọn:** cả tám worktree tạm đã đăng ký (hai của w11, sáu của w12) đã gỡ bằng `git worktree remove <đường dẫn>`, không ép, sau khi so từng file chưa commit với blob đã commit (0 artifact duy nhất có rủi ro) — chi tiết `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/diagnostics/WORKTREE_CLEANUP.json`. Còn lại, KHÔNG đăng ký, đánh dấu `SAFE_TO_DELETE` (không tự xoá): thư mục rỗng `D:/tmp/w11-d1`, `D:/tmp/w11 space`, `D:/tmp/w12 space`; `D:/tmp/w11-before` (383 MB), `D:/tmp/w10-freeze4` (324 MB), `D:/tmp/w11-attempt1`, `D:/tmp/w11-gen`, `D:/tmp/w10-out` và các log `D:/tmp/w10-*.log`, `D:/tmp/w11-*`, `D:/tmp/w12-backend-*.log`.
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
- **status:** RESOLVED — verified by the W13 audit at `bf5a7907`: `geometry_compiler/primitives.py` has `construct_prism`, `fact_graph.py::LOAI_NUT` has `prism`, `compiler.py` supports `right_triangle_base_right_prism_volume` (vertical slice `5a5534fe`, 2026-09-22, `docs/EVIDENCE_INDEX.md`).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-REQUEST-CONTRACT-PRISM-GAP
- **description:** `RequestContract` tại baseline thiếu trường chở `prism identity`, `base_cycle`, `top_cycle`, hay `correspondence` (`REQUEST_CONTRACT = CHANGE_REQUIRED`). Bế tắc kiến trúc giữa Direction A và Direction B đã được giải quyết về mặt thiết kế tại `docs/GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE.md` thông qua kiến trúc 2 lớp (Internal Discriminated Union vs Model Transport Flattened Schema). Vấn đề hiện tại là triển khai mã nguồn sản phẩm trong vertical slice.
- **evidence:** `docs/SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE.md`, `docs/GENERIC_SOLID_TOPOLOGY_CONTRACT_DESIGN_AND_PREREGISTRATION_OFFLINE.md`.
- **impact:** Cần áp dụng hợp đồng đã thiết kế vào `request_contract.py` và `contract_adapter.py` trong vertical slice tiếp theo.
- **scope:** `backend/app/simulation/semantic_program/request_contract.py`, `backend/app/simulation/geometry_compiler/contract_adapter.py`
- **status:** RESOLVED — verified by the W13 audit at `bf5a7907`: `request_contract.py` carries `solid_topology: PrismTopologySpec | PyramidTopologySpec | None` (base cycle, top cycle, correspondence). The remaining contract gaps (one solid only, no regularity, no curved topology) are tracked by layer in `docs/architecture/geometry_capability_matrix_v2.json`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-LLM-ROUTE-LENGTH-NOT-TEXT-GROUNDED
- **description:** On the default `LLM_ONLY` route a length that exists only in an analyze-authored `input_fact` — not in the problem text, so absent from the server-extracted length invariants — can ground a GIVEN quantity: the grounding gate checks program ↔ contract, not contract ↔ text. A volume problem whose height is not stated can then be served with an invented height.
- **evidence:** `docs/evaluation/geometry/runs/w11-pedagogical-polish/diagnostics/logs/INVENTED_HEIGHT_PROBE_48c676d5.log` (offline, 0 model calls): prism contract with the `AD` invariant removed and `AD = 5` removed from the text — compiler route `FALLBACK_TO_LLM` (`REQUIRED_LENGTH_MISSING AD`), the program is served `ok` because the analyze fact still carries `5`; the pyramid analogue is refused (`input_not_grounded`) because its SA fact carries no value. The fact-value channel dates from `2bdd2f73` (before w11); the w11 channel `_do_dai_bat_bien` requires a server-extracted invariant and does not widen this.
- **impact:** A hallucinated length in the analyze output is not caught deterministically on the LLM route; the opt-in compiler route fails closed.
- **scope:** `backend/app/simulation/semantic_program/grounding_gate.py` (fact-value channel) and analyze-contract provenance.
- **status:** RESOLVED (w12, `79eb1e59` + `8aaeae80`; `CACHE_VERSION` 104 → 105 in `d17550c3`, served → rejected) — a GIVEN length (integer, decimal with `.` or `,`, fraction, radical) and every P1-only atom must be backed by the problem text itself (`gia_tri_khong_chung_minh_duoc`, recomputed from the text, shared by the frozen boundary, the gate and the invariant builders); a point pinned to a coordinate claim whose digits the text does not state is refused. Stable codes `GIVEN_VALUE_NOT_IN_SOURCE` / `SOURCE_SPAN_MISMATCH` / `SOURCE_EVIDENCE_CONFLICT`, never sent to repair; the envelope carries `reason_code` + `reason_subjects` and a point- or segment-aware Vietnamese message. The probe's prism case now returns `unsupported` (`input_not_grounded`, `GIVEN_VALUE_NOT_IN_SOURCE`, subject `AD`). Evidence: `backend/tests/geometry/test_source_grounding_closure.py`; red logs and the browser negatives (one ungrounded fixture per family, refused with no canvas and no answer) in `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/`. Residual: `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION`.
- **owner_class:** ARCHITECTURE
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO (an argument for compiler-first)
- **acceptance:** a GIVEN `XY_length` whose literal has no server-extracted length invariant is refused or labelled; the probe returns `unsupported` for the prism case.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_source_grounding_closure.py -q`

### ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION
- **description:** After w12 a length the problem does not state can no longer reach the answer as a GIVEN, but it can still fix a dimension through coordinates: a program that places a vertex with `LAYOUT_DERIVED` provenance or a `model_assumption` (the LLM's documented channel for free choices of axes) can encode an unstated height, and the volume follows from those coordinates. Neither channel claims GIVEN, so the grounding gate has nothing to check.
- **evidence:** `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/diagnostics/logs/ASSUMPTION_CHANNEL_PROBE_79eb1e59.log` (offline, 0 model calls): prism text without "AD = 5" — the program with the `AD_length` GIVEN is refused (`GIVEN_VALUE_NOT_IN_SOURCE`); the same placement through `LAYOUT_DERIVED` vertices or through `model_assumption` is served with `V = 30`.
- **impact:** A hallucinated dimension can still surface as a coordinate choice on the LLM route. It is never labelled as given by the problem, and the compiler route does not use this channel.
- **scope:** `backend/app/simulation/semantic_program/` (which free coordinate choices may carry a metric the text does not state).
- **status:** OPEN — found in w12; changing what a layout or an assumption may decide is a separate grounding-policy decision, measured separately.
- **w13:** policy and acceptance criteria preregistered (`docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md` §3: GIVEN_VALUE / DERIVED_VALUE / MODEL_ASSUMPTION / VISUAL_DEFAULT, rules P1–P6, AC1–AC7); w12 human review lists this issue as W12-H4.
- **w14:** STILL OPEN — Track B stopped (`ASSUMPTION_POLICY_INCOMPLETE`). A three-valued gate (certificates C0/C1 ⇒ `PROVEN_SAFE`, validated counterexample ⇒ `UNSAFE`, else `UNDETERMINED`, both refused) was measured on a corpus hand-labelled before any mechanism ran: 0 `PROVEN_SAFE` on DEPENDS rows and every AC1/adversarial row refused, but **0/18** contract-bearing gold rows certified (C1 blocked: the compiler families' relations cite facts not confirmed as InputFacts; LLM gold/demo programs are not compiler-recognized), and the counterexample search raised 11 false counterexamples on invariant rows. No gate shipped; the probe's two variants are still served; 16 gate tests are strict xfail. Corpus result inside the certificate scope only, not a soundness proof. Evidence: `docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/ASSUMPTION_CENSUS.json`, `ASSUMPTION_MECHANISM_DECISION.json`, `ASSUMPTION_COUNTEREXAMPLES.md`. Next: user decision W14-D2 (certificate scope).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** after user decision W14-D2 (`USER_DECISION_ON_ASSUMPTION_CERTIFICATE_SCOPE`); W14 Track B stopped
- **default_switch_blocker:** NO (an argument for compiler-first)
- **acceptance:** a dimension that the answer depends on is either stated in the text, derived from stated facts, or shown to the learner as an assumption; the probe's layout and assumption variants are refused or labelled.
- **verify:** rerun the script embedded in the probe log.

### ISSUE-OPS-OFFLINE-SAMPLES-STALE
- **description:** `frontend/src/data/geometry-samples.json` (offline demo problems) is no longer what `backend/scripts/build_geometry_samples.py` produces from the current product, and the drift test its header names (`frontend/src/data/geometry-samples.test.ts`) does not exist.
- **evidence:** measured in the w11 worktree at `ac19e03d` (restored afterwards): regenerating changes the file by +4343/−274 lines; the committed samples date from `47c255d9` (2026-09-03), 66 `backend/app` commits ago, and lack `dependency_edges`, `edge_ownership`, `surfaces`, `occludes_edges`, `display_label` — so offline scenes have no typed provenance (causal tiers) and no canonical edge ownership.
- **impact:** Opening the app without an API key shows scenes built by an older engine; no gate reads these samples.
- **scope:** Offline demo data (`frontend/src/data/`).
- **status:** OPEN — not regenerated in w11 (a product-file change outside the reviewed families).
- **owner_class:** OPERATIONS
- **suggested_wave:** after human visual review
- **default_switch_blocker:** NO
- **acceptance:** samples regenerated in a product commit; a test fails when the committed JSON differs from the generator's output.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/build_geometry_samples.py` then `git diff --stat frontend/src/data/geometry-samples.json` (empty).

### ISSUE-OPS-DIST-ACL-OWNERSHIP
- **description:** In the main working tree `frontend/dist/assets` is owned by another Windows account (`CodexSandboxOffline`); `npm run build` cannot replace it and fails with `EPERM`.
- **evidence:** `docs/evaluation/geometry/runs/w11-pedagogical-polish/diagnostics/logs/DIAG1_SUITE_BUILD_EPERM_main-tree.log`.
- **impact:** Builds, browser measurements and T3 must run in a worktree; running them in the main tree fails at the build step.
- **scope:** Local environment (ACL outside git).
- **status:** OPEN — ownership not changed by the agent (needs the user).
- **owner_class:** OPERATIONS
- **suggested_wave:** any
- **default_switch_blocker:** NO
- **acceptance:** `cd frontend && npm run build` succeeds in the main tree.
- **verify:** `icacls frontend\dist\assets`

### ISSUE-ARCH-TEXTLESS-CONTRACT-UNCHECKED
- **description:** Before w14, a `RequestContract` with an empty `problem_text` made `check_grounding` skip every source check, so a contract without its text was treated as trusted by default.
- **evidence:** `docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/TRUST_POLICY_CALLERS.json` (20 test callers and 44 scripts classified one by one) and `diagnostics/logs/TRUST_POLICY_TRACE.json`.
- **impact:** A production path that lost the text would have served answers no gate had checked against the problem.
- **scope:** `backend/app/simulation/semantic_program/grounding_gate.py`, `route.py`, `backend/app/ai/pipeline.py` (`KHONG_SUA_NGUON`).
- **status:** RESOLVED (w14, `d537cf74`) — `NguonDe.CAN_DE` is the default; an empty text is refused `SOURCE_TEXT_MISSING` at stage `grounding` and never sent to repair; only an explicit `NguonDe.FIXTURE_TIN_CAY` argument takes the unchecked path and records `source_check = UNCHECKED_TRUSTED_FIXTURE`. The policy is a Python argument only: not parsed from HTTP payloads, headers or model output; no reference from `app/ai`, `app/main.py` or `app/api` (AST test).
- **owner_class:** ARCHITECTURE
- **suggested_wave:** —
- **default_switch_blocker:** NO
- **acceptance:** a textless production contract is refused; isolated unit fixtures declare the policy explicitly.
- **verify:** `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest tests/geometry/test_assumption_gate.py -q -k "fixture_tin_cay or thieu_de or bypass or NguonDe"`

### ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4
- **description:** The frozen human hidden-line expectations (`docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/human_expected_visibility.json`) were reviewed on scenes that w14's formation pass changed: the triangular pyramid, triangular prism and cross-section gain drawn segments/faces, and the rectangular pyramid's lateral IDs are renamed (declared Q1 delta). `transfer_expectation` refuses, by design, to carry a reviewed expectation onto changed geometry.
- **evidence:** `docs/evaluation/geometry/runs/w14-generic-formation-assumption/results/OCCLUSION_MEASUREMENT.json` (product = oracle 24/24; 4 × `SCENE_GEOMETRY_CHANGED`, cuboid and cube transfer) and `diagnostics/OCCLUSION_TRANSFER_DIAGNOSTIC.json` (the oracle reproduces the reviewed sets 4/4 at the registered and the new camera; known-answer fault caught).
- **impact:** For those four scenes the hidden-line gate cannot be green without a person; no visibility regression is measured.
- **scope:** Evaluation evidence (human registry); no product code.
- **status:** OPEN — needs human re-review of the four scenes and a new registry layer (the reviewed registry stays byte-identical).
- **owner_class:** EVALUATION
- **suggested_wave:** human visual re-review (W14-D3)
- **default_switch_blocker:** NO
- **acceptance:** a reviewed registry layer for the current scenes; the occlusion measurement passes against it.
- **verify:** `measure_scene3d_occlusion.py` with the new registry (command at the top of `diagnostics/logs/OCCLUSION_380db58c.log` in the w14 run).


