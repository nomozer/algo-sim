# ARCHITECTURE_MAP.md — Bản đồ kiến trúc AlgoSim

Tài liệu **nguồn chân lý bền vững** của repo (CLAUDE.md bị gitignore nên không
mang được sự thật lâu dài). Cập nhật khi **kiến trúc** đổi, không cập nhật theo
từng commit.

## 0. Đọc gì trước khi sửa code

Trước MỌI thay đổi không tầm thường:

1. Đọc `docs/ARCHITECTURE_MAP.md` (file này).
2. Đọc `docs/CURRENT_STATE.md` (milestone, baseline test, gap, việc đã hoãn).
3. Đọc phần liên quan trong `docs/CODE_INDEX.md`.
4. **Đọc chính source file** — docs là bản đồ, không phải lãnh thổ.
5. **Nếu docs mâu thuẫn với code/test → CODE/TEST THẮNG.** Sửa docs, đừng sửa
   code cho khớp docs.

Sau khi xong milestone: cập nhật `CURRENT_STATE.md`; chỉ sửa file này khi kiến
trúc thật sự đổi; sửa `CODE_INDEX.md` khi module/export công khai đổi.

## 1. Hệ thống là gì

Học sinh dán một đề bài bằng lời → LLM **chỉ** trích xuất ngữ nghĩa, phân loại,
và điền **config** → **engine tất định** (frontend) sinh toàn bộ bước chạy, trạng
thái, kết quả, hoạt cảnh. Toàn bộ chuỗi chữ hiển thị và prompt đều tiếng Việt.

## 2. Luồng chính (backend → frontend)

```
input (text/docx/code/image)
  → ingestion/input.py            chuẩn hóa MỌI loại về text (không loại nào bypass)
  → [exact cache]                 simulation_cache, version-aware → 0 call LLM
  → ai/pipeline.stage_analyze     LLM: trích semantic requirements + vai trò
  → simulation/representation     TẤT ĐỊNH: plan + scene_mode + CAPABILITY GATE
  → ai/pipeline.stage_classify    LLM: chọn simulation_id theo NĂNG LỰC
  → [capability gate]             vai trò gap + classify chọn generic → unsupported
  → [pattern reuse]               chỉ sau classify, chỉ generic.rule_scene
      hoặc ai/pipeline.stage_simulate  LLM điền config + retry
  → validate (2 tầng)             dsl/validator.py + validation/simulation.py
  → ValidatedSimulationEnvelope
frontend:
  store.loadEnvelope → module.validateConfig (tầng 2) → module.init → engine state
  → renderer ĐỌC state
```

Chỉnh sửa tăng dần (M7.14) là **con đường thứ ba sinh spec hợp lệ**, song song
với compose và pattern reuse:

```
spec hiện tại + yêu cầu → (LLM đề xuất patch) → SimulationPatch
  → validate patch → full validator → guard tiến trình → engine smoke
  → spec mới → rebuild state (giữ pos/base) — KHÔNG chạy analyze/classify/simulate
```

## 3. Sở hữu sự thật (source-of-truth ownership)

| Thứ | Ai sở hữu | Ghi chú |
|---|---|---|
| Từ vựng capability (types/limits/roles) | `simulation/dsl/manifest.py` | mọi allowlist/enum/prompt **dẫn xuất** từ đây |
| Luật hợp lệ của spec | `dsl/validator.py` (+ mirror TS `generic/validate.ts`) | hai tầng, cùng luật |
| Timeline / state / kết quả | **engine tất định** (`core/algorithms.ts`, `generic/model.ts`, `generic_engine.py`) | LLM **không bao giờ** |
| **Chương trình ngữ nghĩa (IR)** | LLM tổng hợp, **server đóng băng nghĩa vụ trước** (`RequestContract`) | IR là *chương trình ứng viên*; chạy nó KHÔNG phải việc của LLM |
| **Trace thực thi** | `semantic_program/interpreter.py` — **authority tất định** | ngân sách **thực thi**; chạm trần phải BÁO |
| **Khung hình (frame)** | `semantic_program/visual_adapter.py` | song ánh `frame k ⇔ trace[k]` — điều kiện để bất biến #31 là định lý |
| **Bước xem (view step)** | `semantic_program/pacer.py` | ngân sách **trình bày**, tách hẳn ngân sách thực thi; gộp KHÔNG bỏ |
| Vị trí object lúc chạy | `GenericState.pos` (engine-owned, **toạ độ miền 0–100**) | spec bất biến; drag chỉ đổi state |
| **Bố cục/kích thước canvas** | **RENDERER** — không bao giờ là engine state | xem quy tắc renderer-neutral bên dưới |
| Định tuyến bài → mô phỏng | `catalog.py` + classify (LLM) + capability gate (tất định) | gate có quyền phủ quyết |
| Đúng/sai của thao tác học sinh | **chỉ rule tất định** | không có rule → `unsupported_to_verify` |
| Cấu hình đang chạy | store (`active.config`) — **opaque**, bất biến | store mù domain |
| **Visual mode (2D/3D) đang hiển thị** | store — **lát trình bày** (`visualMode`, cạnh `leftOpen`) | M8: không bao giờ vào engine state/spec; **không do LLM chọn**; đổi mode không đụng active/cursor/prediction |
| Renderer khả dụng của một module | hợp đồng module (`supportedVisualModes` ∩ `renderers`) qua `simulations/renderer.ts` | **cấm** switch-case theo simulation_id |
| Mặt trình bày đang mở (home/workspace/history) | store — `view` (M9-UX1) | như visualMode: trình bày thuần, không đụng engine |
| **Chế độ học sinh đang mở (Khám phá / Thử thách)** | store — `exploreOpen` / `challengeOpen` (W4B-3A), **mù domain** | HAI cờ vì hai chế độ khác nhau ở chỗ AI PHÁN XÉT (xem bất biến #24); trước đây là `useState` cục bộ tên `labOpen` trong hai renderer miền |
| **Chỗ đặt lối vào hai chế độ** | `components/SimulationControls.tsx` — chủ sở hữu **DUY NHẤT** | renderer miền **cấm** dựng `sim-secondary-action`; miền chỉ cấp CÂU MỜI qua `predict.entry`/`explore.entry` |
| **Lịch sử học BỀN** | `state/history.ts` → localStorage (schema v1, whitelist) | M9-UX1: envelope ĐÃ VALIDATE + tiến độ trình bày an toàn (lastCursor/visualMode); **runtime reset/goHome không phá lịch sử** |

## 3b. Quy tắc RENDERER-NEUTRAL STATE (M7.FREEZE — điều kiện để có 3D)

**Engine state chỉ chứa sự thật NGỮ NGHĨA. Bố cục là chuyện của renderer.**

- Vị trí trong không gian **mô phỏng** (vd `GenericState.pos`, toạ độ miền 0–100)
  là ngữ nghĩa → ở engine. **Toạ độ pixel / kích thước canvas / viewBox** là
  trình bày → **cấm** nằm trong state.
- Diễn biến chuyển động diễn đạt bằng **định danh ngữ nghĩa**, không bằng toạ độ:
  `Frame.entityPos: entityId → **nodeId**` (generic) và `NetStep.packetAt =
  **nodeId**` (network). Nhờ vậy renderer 3D tính vị trí riêng mà **dùng lại
  nguyên state**.
- 2D và 3D **dùng chung** config/state/timeline/action của **cùng một module**.
  **Không** tạo `simulation_id` riêng cho 3D, **không** fork engine.

*Tiền lệ đã sửa (M7.FREEZE):* `NetworkState` từng chứa `positions` là **toạ độ
pixel** do `layout()` sinh (COL=150, X0=80…) — dữ liệu trình bày lọt vào state
quyền uy. Nay `layout2d` sống trong `network/ui.tsx`; state chỉ còn topology +
route (BFS) + steps + cursor. Khóa bằng test: state không được chứa
`positions/width/height` hay bất kỳ `"x"/"y"` số nào.

*Quy tắc này ĐÃ ĐƯỢC HIỆN THỰC HÓA (M8):* `network/ui3d.tsx` là renderer 3D
(Three.js) đọc **nguyên** NetworkState đó — `layout3d` (nodeId → Vector3),
camera, mesh, nội suy chuyển động đều renderer-owned trong ref/closure của
component; state không thêm một trường nào (khoá bởi `render3d.test.tsx`).
Renderer 3D được phép **nội suy hình ảnh** giữa hai bước ngữ nghĩa nhưng không
bịa trạng thái trung gian: sự thật vẫn là `packetAt` của bước hiện tại.

## 4. Hướng phụ thuộc (không được đảo)

```
manifest ← validator ← catalog ← pipeline ← main
manifest ← representation / semantic / patterns / patch
types ← registry ← store ← components
module (domain) → types/registry;  renderer → state (chỉ ĐỌC)

# Route sinh ngữ nghĩa (2026-08-20) — KHÔNG được đảo:
contract ← validator ← interpreter ← visual_adapter ← pacer ← envelope
```

Renderer **không bao giờ** nắm state quyền uy; nó phát `SimAction` và đọc lại.
Store **không** biết domain (không import Trace/SimulationSpec/mảng).

## 5. Bất biến (mỗi cái kèm nơi thực thi + test khóa)

| # | Bất biến | Thực thi ở | Test |
|---|---|---|---|
| 1 | LLM không phải nguồn state runtime | `skills/*.md` cấm sinh timeline; validator có `FORBIDDEN` keys | `test_pipeline::test_simulate_sinh_timeline_bi_chan` |
| 2 | Engine tất định là nguồn chân lý | `init/apply/timeline` của module | `algorithms.test.ts`, `generic.test.ts` |
| 3 | Renderer không sở hữu state | `WorkspaceProps` chỉ có `state` + `dispatch` | `patch.test.ts` (drag qua action) |
| 4 | Manifest là từ vựng capability | mọi enum/allowlist dẫn xuất | `test_manifest::*_dan_xuat_tu_manifest` |
| 5 | Specialized **không** bị chặn bởi gap của DSL generic | `pipeline.run_pipeline` (gate chỉ chặn đường generic) | `test_capability_boundary::test_gap_role_khong_va_lay_specialized` |
| 6 | Pattern reuse chỉ **sau classify**, chỉ `generic.rule_scene` | `pipeline.run_pipeline` | `test_reuse::test_case_g_specialized_khong_dung_store` |
| 7 | Reuse **không** bypass validation (4 cổng) | `patterns.run_gates` | `test_patterns::test_run_gates_khong_bypass_validation` |
| 8 | Thà `capability_gap` còn hơn mô phỏng xấp xỉ gây hiểu lầm | `representation.build_representation_plan` + `semantic.check_semantic_compatibility` | `test_capability_boundary::*` |
| 9 | Canonical simulation: đúng hoặc từ chối trung thực | như trên | như trên |
| 10 | Learner **được phép sai** | what-if branch (algorithm), drag tự do | `registry.test.ts`, `patch.test.ts` |
| 11 | Chỉ engine/rule tất định mới phán đúng/sai | `InteractionFeedback` sinh từ rule | `patch.test.ts::drag bounds` |
| 12 | Feedback là **state data**, không phải lượt chat | `GenericState.feedback` | như trên |
| 13 | `pytest`/`vitest` mặc định = **0 call AI thật** | `backend/conftest.py`, `frontend/src/test-setup.ts` | `test_offline_guard.py`, `offline-guard.test.ts` |
| 14 | Live eval là **opt-in**, không phải thói quen | `evaluation/live.py` (`ALLOW_LIVE_AI=1`) | `test_live_budget::test_live_khong_co_opt_in_thi_abort` |
| 15 | Patch fail → spec hiện tại **nguyên vẹn** | `patch.py` áp trên bản sao | `test_patch::test_patch_fail_giua_chung_khong_mutate_spec` |
| 16 | **3D là renderer, không phải domain** (M8): 2D/3D dùng chung module/config/state/timeline/action/prediction; `visualMode` là trình bày thuần; renderer khả dụng dẫn xuất từ hợp đồng module | `simulations/renderer.ts` + `SimulationWorkspace` (không switch-case id) | `visual-mode.test.tsx`, `render3d.test.tsx`, `m8-acceptance.test.tsx` |
| 17 | **Mở lại từ lịch sử = ZERO-AI** (M9-UX1): lưu envelope ĐÃ VALIDATE, mở lại qua `loadEnvelope` + engine tất định — không đi pipeline, không LLM; chỉ persist trường whitelist (không prediction/branch/camera/secret); runtime reset không phá lịch sử | `state/history.ts` + `store.reopenFromHistory` | `history.test.ts`, `view-history.test.tsx` |
| 18 | **Nghĩa của chiều sâu 3D phải TRUNG THỰC, và chỉ nghĩa SƯ PHẠM mới được bày cho học sinh** (M10, siết ở W4B-2R): module có 3D khai `threeD.role` = `pedagogical` (Z mã hoá biến khái niệm thật — `network.protocol_encapsulation`: **Z = tầng giao thức**, X = chiều truyền). W4B-2R nâng M10 từ *khai báo trung thực* lên *chính sách*: `architectural_poc` (Z chỉ là bố cục) **KHÔNG đủ tư cách bày toggle 2D/3D** — đó chính là `2D_AND_3D_BY_DEFAULT`. Tiền lệ: `network.packet_routing` tự khai `architectural_poc` + `meaningOfZ = "bố cục, không mang nghĩa khái niệm"`, nên W4B-2R **hạ nó về 2D_ONLY và gỡ `ui3d.tsx`**. Danh mục nay **22 × 2D_ONLY · 0 × 3D_ONLY · 1 × 2D_AND_3D_JUSTIFIED**. PDU là state ngữ nghĩa dùng chung (2D+3D đọc cùng), 3D không tính lại PDU | `SimulationModule.threeD` (`types.ts`) + **`renderer.ts::representationPolicyOf` / `representationPolicyProblems`** (chủ sở hữu chính sách). **W4B-2S siết tiếp**: `role: "pedagogical"` chỉ là NHÃN TỰ NHẬN nên chưa đủ — target có 3D phải khai `threeD.pedagogicalFit[]` (3D thắng ở tiêu chí nào) **và** `whyNot2d` (vì sao 2D không diễn đạt được). Kèm luật thứ hai: **vai trò miền phải chở bằng HÌNH, không bằng chữ** — chủ sở hữu `domains/network/node-glyph.ts` (`NodeType` engine → hình), khoá bằng phép thử XOÁ HẾT CHỮ | `representation-policy-w4b2r.test.ts` (guard toàn danh mục, dẫn xuất từ registry), `encap-render3d.test.tsx` (encap=pedagogical) |
| 19 | **Alembic sở hữu schema Postgres bền** (DB-HARDEN-2, *chất lượng triển khai — không phải đóng góp học thuật*): tạo & tiến hoá schema PostgreSQL do **Alembic** sở hữu DUY NHẤT (`alembic upgrade head` ở entrypoint Docker). `create_all()` chỉ dành cho SQLite ephemeral/test, KHÔNG phải cơ chế migration của Postgres; runtime **không** lặng lẽ `create_all()` trên Postgres (quyết định theo `engine.dialect.name`, không string-check URL). Không tự động `stamp` DB lạ | `db.py::init_db` (gate qua `sqlite_owns_schema`) + entrypoint Docker | `test_db_ownership.py`, `test_migration_drift.py` (cổng chống trôi, có fault-injection proof), `test_postgres_integration.py` (smoke opt-in) |
| 20 | **Toán hạng numeric/logical của một rule generic phải có nguồn giá trị theo hợp đồng ngữ nghĩa DẪN XUẤT TỪ MANIFEST — không có thì reject, không bao giờ hoá 0 im lặng** (M13): validator hai tầng từ chối operand không phải *value-provider* của role rule cần (`INVALID_SOURCE` — vd `edge`/`node` không có `value`) và từ chối derived-target sai role theo `role_satisfies()` — subtyping **MỘT CHIỀU** dẫn xuất từ `role_compatibility` trong contract (M13 hotfix: `logical` satisfies `numeric` — boolean executor sinh đúng 0/1, KHÔNG runtime conversion; vd `weighted_sum` numeric vẫn không được ghi vào `node` relational). Mọi cặp khác **DENY mặc định**; chiều ngược `numeric ↛ logical` LUÔN deny (đó chính là coercion ngầm `v>=1` mà check này sinh ra để diệt) — chỉ mở cặp mới khi matrix audit chứng minh được fixture thật; runtime hai tầng KHÔNG BAO GIỜ seed/fallback một giá trị thiếu/chưa resolve thành 0 — ném lỗi TYPED fail-closed tại ranh giới evaluator (4 mã: `invalid_numeric_source` / `missing_weight` / `unresolved_dependency_after_bound` / `non_finite_numeric_value`). Sự cố gốc đã sửa: `weighted_sum` ăn input là id một `edge` (fixture "pseudo-Dijkstra" — TÁI DỰNG, artifact gốc không khôi phục được từ cache/localStorage) từng lặng lẽ hoá 0 → cảnh "chạy" đủ bước, kết quả sai câm; validator siết chặt tự động bảo vệ luôn cả đường pattern-reuse (fixture cũ mang shape cấm bị chặn ngay ở cổng 1 `run_gates`, không cần sửa riêng) | Validator: `dsl/validator.py` (khối coherence, dòng ~369) + mirror `generic/validate.ts` (dòng ~339, import trực tiếp `dsl-contract.json` — không hằng viết tay). Runtime: `generic_engine.py` (`GenericEvaluationError`) + mirror `generic/model.ts` (`GenericExecutionError`) + `state/store.ts` bọc `mod.init` fail-closed. Nguồn hợp đồng: `manifest.py::dsl_semantic_contract()` → sinh `dsl-contract.json` (`scripts/generate_dsl_contract.py`, chạy tay, sync-lock chống trôi) | `test_dsl.py` khối M13 Task 3 · `test_generic_engine_m13.py` · `generic.test.ts` (`describe("M13 operand coherence")`, `describe("M13: valuesOf ba trạng thái...")`) · `test_manifest_providers.py` (bao gồm `test_dsl_contract_json_khong_troi_khoi_manifest` — sync-lock) · fixture pseudo-Dijkstra: `test_m13_dijkstra_fixture.py` (validator reject) + `generic.test.ts` describe `"M13 Task 7"` (history reopen fail-closed, không throw) + `test_m13_pattern_revalidate.py` (chặn ở cổng 1 khi thử reuse) |
| 22 | **Evaluation của luồng AI tạo mô phỏng phải thực thi CÙNG production orchestration với `/api/analyze`; evaluator KHÔNG được tái dựng riêng chuỗi analyze→classify→gate→simulate** (M14). `evaluate_item` gọi THẲNG `run_pipeline` với `observer` THỤ ĐỘNG (chỉ thu event; không đổi routing/retry/gate/output; `observer=None` → hành vi production không đổi một bit). Hệ quả: computation gate (M13) + mechanism gate (M14) NAY sống trong eval — case bị gate từ chối được chấm ĐÚNG là honest refusal (trước M14 harness bỏ qua gate, chấm sai). Side-effect isolation: eval `pattern_store=None` (reuse/persist bị guard bỏ qua) + `run_pipeline` không chứa code cache (cache sống ở `main.py`) → 0 row mới ở `simulation_cache`/`simulation_patterns`/`reuse_metrics`. `_simulate_with_metrics` (mirror chép tay, known-issue #1 drift) ĐÃ RETIRE sau transcript-parity proof. KHÔNG áp cho `/api/edit`, history reopen, offline catalog, renderer init. **M16 chứng minh bất biến này ở quy mô TOÀN catalog**: offline scripted evaluation (50 case, provider mock per-case, fault-injection) chứng minh **pipeline/gate correctness** — mọi record đi qua `run_pipeline` thật, parity 50/50; live evaluation (24 case baseline, user duyệt) đo **hành vi LLM thật** trên cùng orchestration, parity 24/24; observer THỤ ĐỘNG (diff pipeline toàn M16 = 2 dòng `_emit` no-op khi `observer=None`); pre-fix baseline giữ nguyên vẹn (trace + artifacts `docs/evaluation/m16/*-baseline.json`), correction count = 0. Hai lớp offline/live là hai run_label RIÊNG, không ghi đè | `ai/pipeline.py::run_pipeline(observer=...)` + `evaluation/observer.py::AttemptObserver` + `evaluation/harness.py::evaluate_item` (+ M16: `evaluation/m16_record.py`, `evaluation/m16_metrics.py`, `evaluation/m16_offline_scripts.py`) | `test_eval_convergence.py` (đi qua run_pipeline, observer passive), `test_eval_parity.py` (parity proof — skip sau retire), `test_eval_side_effects.py` (0-row lock + fault-injection: classify qua nhưng gate chặn → honest refusal), M16: `test_m16_offline_eval.py` (50/50 qua production pipeline + hard correctness + parity 1.0) |
| 23 | **Mechanism ownership được khai ở mức FamilyMembership; mechanism taxonomy dùng canonical namespaced IDs với một compatibility alias boundary duy nhất; consistency gate so sánh tín hiệu cơ chế có cấu trúc trên final route sau bounded reclassification** (M15). Giải thích: family mới khai `owned_mechanisms` máy-đọc-được ngay trên membership; giá trị analyze legacy được normalize tại ĐÚNG MỘT chỗ (`canonical_mechanism` — alias một chiều, không phải taxonomy thứ hai); gate và descriptor CHỈ so canonical values; route-consistency chạy trên FINAL route (không route-dependent gate nào chạy trên route tạm — `analyze → classify → recovery ≤1 reclassify → FINAL ROUTE → gates → simulate`); cơ chế không sở hữu → retry có giới hạn (cross-family mismatch, `ROUTE_MECHANISM_FAMILY_MISMATCH`) hoặc fail-closed `capability_gap` (cùng-family unowned, `GATE_MECHANISM_OWNERSHIP`); định tuyến KHÔNG dựa keyword-patch — chỉ so tín hiệu cấu trúc. Giá trị analyze-exposed không ai sở hữu phải khai tường minh trong `INTENTIONAL_GAP_MECHANISMS` (owned XOR intentional-gap) | `simulation/mechanisms.py` (taxonomy đóng + `canonical_mechanism` + `INTENTIONAL_GAP_MECHANISMS` + `FORMALIZED_FAMILIES`) + `descriptor.py::FamilyMembership.owned_mechanisms` + `mechanism_gate.py::check_mechanism_consistency_for_target` + `ai/pipeline.py::classify_with_one_route_recovery` | `test_mechanisms.py` (taxonomy/alias/exposed) · `test_descriptor.py` (owned canonical, family-prefix khớp) · `test_capability_descriptors.py` (khóa-2 XOR + K1 14/14) · `test_pipeline_mechanism_consistency.py` (ordering, budget analyze=1/classify≤2/simulate≤1, no-bypass, no-recursion) · `test_mechanism_gate.py` (3 nhánh 2 mã) |
| 21 | **Yêu cầu tính-kết-quả-thuật-toán mà không có executor tất định nào sở hữu → `capability_gap` trên đường generic, KHÔNG dựng cảnh minh hoạ đáp án** (M13): SERVER ra phán quyết cuối, tất định, trên **tín hiệu CÓ CẤU TRÚC** — hai kênh bổ sung nhau: (1) `known_gap_roles()` lọt vào `unsupported_capabilities` của representation plan (vd role `arbitrary_algorithm`); (2) `analysis.result_ownership` **fail-closed** — chỉ `"provided"`/`"rule_derivable"` được đi tiếp, `"algorithmic"` HOẶC thiếu/ngoài enum đều → gap (không default sang giá trị nào). Kênh 2 bắt được cả khi kênh 1 bị bỏ sót role (không phụ thuộc MỘT kênh prompt duy nhất). Giữ nguyên carve-out chuyên biệt (bất biến #5 — gap của DSL generic không lây sang specialized). Đây là lớp phòng thủ TRƯỚC khi simulate chạy (chặn ở classify/analyze), bổ sung — không thay thế — invariant #20 (chặn Ở VALIDATOR nếu vẫn lọt qua tới đó); artifact "pseudo-Dijkstra" là ca cụ thể bị #20 chặn, còn #21 là cơ chế chặn SỚM HƠN dựa trên ý định của đề bài | `simulation/computation_gate.py::check_computation_ownership`, gọi trong `ai/pipeline.py::run_pipeline` **sau classify**, scoped vào đường generic bằng kết quả classify (giữ carve-out chuyên biệt); taxonomy dạy bằng ví dụ ở `analyze.md`/`classify.md` (KHÔNG keyword-patch), `CACHE_VERSION` 9→10 | `test_m13_routing.py` (2 kênh, kể cả khi kênh 1 bị bỏ sót role) — offline, mock. **Verify LIVE CHƯA CHẠY**: eval case `cap-dijkstra-gap` (`evaluation/datasets/capability.py`) là bài kiểm thật với LLM thật, nằm sau Task 14 (STOP GATE, chờ `ALLOW_LIVE_AI=1`) |

| 24 | **KHÁM PHÁ và THỬ THÁCH là hai trách nhiệm khác nhau, phân biệt bằng AI PHÁN XÉT — và LỐI VÀO của chúng thuộc shell, không thuộc renderer miền** (W4B-3A). Thử thách: học sinh CAM KẾT một quyết định, `predict.check` (engine tất định) phán đúng/sai. Khám phá: học sinh ĐỔI mô hình, `module.apply` tính lại, **không ai phán gì** — hệ quả tất định LÀ câu trả lời. Một cửa cho cả hai dạy học sinh rằng kéo một cột cũng là "trả lời đúng/sai". Sự cố gốc: cả hai từng nằm sau MỘT `useState` cục bộ tên `labOpen` do renderer miền tự dựng nút mở, nên (a) dưới sân khấu luôn thừa một dải `experimentTrigger` (đo được ở 8 target thuật toán + `packet_routing`, cả 4 bề rộng), (b) chuyển phiên là mất chế độ, (c) SSR luôn thấy `false` nên không test nào chạm được trạng thái MỞ (xem §8 #13). Hệ quả kèm theo: `presentedInStage` từng tắt CẢ lối vào chứ không chỉ bề mặt thứ hai — đó mới là thứ ép miền phải tự dựng nút. Luật nay: `presentedInStage` chỉ chặn `PredictionBar`; **một cửa, nhiều nhất một bề mặt**; lối vào ở bước không dùng được thì **MỜ, không biến mất** (4/13 → 21/40 bước mời được tuỳ bài — tự gỡ mình là nhấp nháy). Store vẫn **mù domain**: nó giữ hai boolean và không biết "khám phá" ở bài này là kéo cột hay bấm liên kết mạng | `state/store.ts` (`exploreOpen`/`challengeOpen`; M18-UI: nhiều phiên đã gỡ, hai cờ nay ở thẳng store) + `components/SimulationControls.tsx` (chủ sở hữu DUY NHẤT của lối vào) + `components/SimulationWorkspace.tsx` (`challengeEntry`/`exploreEntry`/`challengeSurfaceVisible`) + hợp đồng `ExploreCapability`/`PresentationEntry` (`simulations/types.ts`) + `domains/algorithm/interaction-policy.ts` (`challengeEntryOf`/`exploreEntryOf`, hàm thuần) | `explore-ownership-w4b3a.test.ts` · `secondary-actions-w4b2w.test.ts` (0 dải `experiment-trigger`, đúng MỘT chủ sở hữu) · `workspace-lifecycle.test.ts` (bài mới luôn mở ở Quan sát, đổi bài 0 fetch) · `interaction-family-w1.test.tsx` (cửa ≠ bề mặt) · nghiệm thu trình duyệt 4 bề rộng `frontend/scripts/accept-w4b3a.mjs` |

| 25 | **Tiêu đề là ĐỀ BÀI, mô hình là thứ học sinh đang cầm — và khi hai bên lệch nhau thì màn hình phải NÓI RA** (W4B-4D). Trước khi có tham số đổi được, hai thứ này luôn trùng nên bất biến chưa cần tồn tại. Từ khi `count_if`/`sum_if` đổi được điều kiện, `tree`/`graph_traversal` đổi được cách duyệt, `database` đổi được truy vấn, `binary` đổi được cơ số/văn bản, thì đề viết "đếm học sinh **từ 8,0 trở lên**" trong khi mô hình đang đếm từ 6 — và con số cuối cùng đọc như đáp số của bài gốc. Đó là màn hình **khẳng định một điều sai**, không phải chuyện thẩm mỹ. Chủ sở hữu là SHELL, không phải từng miền: một chỗ so, một nhãn, không miền nào phải tự nhớ. Hai luật của phép so: (a) so bằng **GIÁ TRỊ** — mọi `apply` dựng config mới nên so tham chiếu sẽ báo "đã đổi" vĩnh viễn kể từ thao tác đầu, kể cả khi học sinh vừa quay về đúng chỗ cũ; (b) so **ĐÚNG các khoá module khai** — `web` giữ kiểu trong state nên phải tự dựng lại hình dạng config và nó không giữ `notes` của đề, so cả khối thì mọi đề có `notes` đều "đã đổi" ngay khi vừa mở. Nhãn kêu oan là nhãn bị học sinh học cách phớt lờ, đúng lúc nó cần được đọc. Module KHÔNG khai `currentConfig` ⇒ không so, không nhãn — bài không đổi được tham số thì không lệch được; và thao tác KHÔNG rời đề (bật một đầu vào của mạch logic) phải để nhãn IM | `components/SimulationWorkspace.tsx` (`specDrift` — hàm thuần, tách khỏi JSX vì luật chôn trong JSX là luật chỉ kiểm được bằng trình duyệt) + hợp đồng `currentConfig?` (`simulations/types.ts`) + 7 module khai (`algorithm` · `binary.base_conversion` · `binary.character_encoding` · `network.graph_traversal` · `tree.traversal` · `database` · `web`) | `spec-drift-w4b4d.test.ts` (im lúc mở trên TOÀN danh mục · bật khi đổi ở 8 target · tắt khi quay về giá trị cũ · chỉ so khoá đã khai) · nghiệm thu Chrome 4 bề rộng `frontend/scripts/accept-experience-w4b4c.mjs` (SSR không chạm tới được — zustand trả trạng thái ĐẦU cho server snapshot, xem §8 #13) |

| 26 | **Một lối vào Khám phá phải dẫn tới thao tác CÓ HỆ QUẢ; và "thao tác được" phải đo bằng CỬA THẬT, không bằng cờ khai báo** (W4B-4A/4D). Hai vế của cùng một bất biến. Vế trình bày: module mời vào Khám phá mà không action nào đổi được mô hình thì lời mời là hứa suông (COVERAGE §2.6 cấm bày tương tác trang trí). Vế ĐO: phép đo phủ danh mục từng đọc `!!mod.explore`, mà **mọi** module thuật toán khai chung một khối `explore` — nên cờ ấy `true` kể cả ở bài `explore.entry()` trả `null` và học sinh không thấy cửa nào. Hệ quả đo được: `count_if`/`sum_if` tính là "thao tác được" suốt từ baseline nhờ `whatif_swap` mà chính sách của chúng TẮT — **dương tính giả**, và nó che mất việc hai bài này thật sự không có gì để khám phá. Đọc `explore.entry()` thì hết lọt. Kèm theo: quyết định GIỮ TRACE phải khai lý do **CƠ CHẾ** trong `KEEP_TRACE`, guard hai chiều (thiếu lý do là đỏ; lý do còn sót sau khi target đã có tương tác cũng đỏ — giải thích lỗi thời đánh lừa người đọc sau), và lý do nói "chưa kịp"/"TODO" bị từ chối | `simulations/experience-audit-w4b4a.test.ts` (`hasExploreEntry` + `KEEP_TRACE`, ghi `docs/evaluation/m17/w4b4a-experience/probe.json`) + `domains/algorithm/interaction-policy.ts` (`exploreEntryOf` — không khai `exploreLabel` ⇒ không cửa) + `domains/algorithm/condition-param.ts` (miền đóng của điều kiện: `count_if`/`sum_if` nay có thao tác THẬT) | `experience-audit-w4b4a.test.ts` (phép đo phủ ĐÚNG registry — sàn `rows.length > 10` cũ nuốt mất một target biến mất khỏi catalog) · `explore-ownership-w4b3a.test.ts` (cửa ⇒ hệ quả; và tiền đề "hoán vị không đổi tổng/đếm" nay được ĐO chứ không tin) · `condition-param.test.ts` (từ chối ≠ kẹp) |

| 27 | **Tầng lớp học ĐỌC bằng chứng, KHÔNG phán đúng/sai** (M18). Correctness thuộc về engine tất định và `predict.check`; LLM không phán, và bảng quan sát của giáo viên cũng không. Bảng đó chở TRẠNG THÁI CÓ CẤU TRÚC — vị trí trên timeline (đọc qua hợp đồng `timeline` của module, KHÔNG đọc renderer), cờ Khám phá/Thử thách đang mở, số thao tác, số lần đã cam kết — và không có trường nào tên `verdict`/`correct`/điểm. Cũng KHÔNG chiếu màn hình hay chụp DOM: nặng hơn, lộ nhiều thứ ngoài giờ học hơn, và buộc phải dựng một hạ tầng truyền hình ảnh mà kiến trúc này không có. Đọc màn hình thay vì đọc hợp đồng sẽ khiến bằng chứng lớp học đổi theo renderer nào đang vẽ và panel nào đang mở | `accounts/classroom_router.py::observe_class` + `components/PracticeReporter.tsx` (chuyển state engine → bằng chứng) + `persistence/classroom_models.py::PracticeSession` | `test_classroom_api.py` (bảng quan sát không chứa verdict/correct/score, không chứa screenshot/DOM; con số bị KẸP về miền hợp lệ thay vì tin client) · `accept-classroom-m18.mjs` |

| 28 | **Chữ của giáo viên không bao giờ thành sự thật runtime** (M18). Giao bài = giao một **envelope ĐÃ QUA `SimSpec.validate`**, đúng cổng mà pipeline LLM đi; lời dặn là CHỮ hiển thị cạnh mô phỏng. Hai hệ quả bắt buộc: (a) mở bài KHÔNG gọi LLM — sinh lại lúc mở nghĩa là ba mươi học sinh mở ra ba mươi mô phỏng khác nhau và giáo viên không giao được thứ mình đã xem; (b) config lưu là bản ĐÃ CHUẨN HOÁ của validator, không phải bản thô của client. Bỏ cổng này thì một config engine không chạy nổi sẽ nổ trên màn hình học sinh giữa tiết | `accounts/classroom_router.py::_validated_envelope` + `persistence/classroom_models.py::Assignment.envelope_json` | `test_classroom_api.py` (envelope sai config/target lạ/chưa phân tích xong đều 400; hai học sinh mở ra CÙNG một envelope) · `accept-classroom-m18.mjs` (envelope hỏng ⇒ 400 ở cả 4 bề rộng) |

| 29 | **Vai trò do MÁY CHỦ sở hữu; thanh điều hướng ứng dụng nằm NGOÀI lưới workspace** (M18). Client gửi `role` gì cũng không đổi được quyền — server tra `users.role` theo phiên, và đăng ký thường luôn ra học sinh (vai trò giáo viên cần mã mời; không cấu hình ⇒ ĐÓNG). Vai trò ở frontend là bản chiếu để VẼ: sửa nó trong devtools thì thấy được thanh điều hướng giáo viên và không gọi nổi endpoint nào. Về bố cục: thanh điều hướng mới KHÔNG được lặp lại cột 208px đã gỡ ở W4B-3B — cột đó nằm TRONG lưới workspace nên nó trải qua cả hàng sân khấu lẫn hàng điều khiển và bóp cả hai. Thanh mới nằm ngoài lưới, thu gọn thành dải biểu tượng trong mô phỏng, và thành ngăn kéo tạm dưới 900px | `accounts/policy.py::resolve_signup_role` + `accounts/router.py::Caller.require_role` + `components/AppSidebar.tsx` + `.app-root/.app-nav` (global.css) | `test_auth_api.py` (tự khai giáo viên bị chặn; thiếu cấu hình vẫn đóng) · `test_classroom_api.py` (6 ca từ chối của `§36`) · `ux-shell.test.tsx` (hai vai không dùng chung thanh điều hướng) · `accept-classroom-m18.mjs` (403 ở cả 4 bề rộng) |

| 30 | **Khung mô phỏng lấy bề rộng từ CƠ CHẾ, và mọi thứ của cùng một cơ chế đứng trên MỘT rail** (M19). Trước wave này thẻ luôn 1624px @1920 trong khi mực dao động 276–1597px, và từng renderer tự căn giữa hình bên trong lớp giãn ấy — đo được 23/23 target hỏng, rail lệch tới 722px. Nguyên nhân là một: thẻ là flex column STRETCH nên con nào cũng giãn hết cửa sổ rồi phải tự căn giữa lại. Luật nay: cột nội dung + thẻ đều `fit-content`, có SÀN SƯ PHẠM `min-width` (không bóp sát từng pixel SVG — phải còn chỗ cho nhãn/chú giải/một câu thuyết minh), và MỌI con lấp trọn thẻ nên mép trái của hình CHÍNH LÀ rail của chữ. Khay điều khiển nằm cùng cột nên tự bằng bề rộng thẻ (giữ W4B-3H). SVG sân khấu phải khai bề rộng THẬT qua `stageSvgSize` — `width="100%"` không sizing được cha `fit-content` (Chrome rơi về 300px mặc định) và buộc phải `margin: 0 auto`, chính là rail thứ hai. Ngoại lệ phải KHAI kèm lý do cơ chế: `web.style_model` được bám cửa sổ (trang web lấp bề rộng khả dụng LÀ hành vi đang dạy), `logic.boolean_dag` được đặt chú giải cạnh sơ đồ | `styles/global.css` (`.app-layout` cột `auto` + `.workspace-card` `fit-content` + `.workspace-card > * { width: 100% }`) + `simulations/stage-size.ts` | `frontend/scripts/audit-composition.mjs` — 23 target × 4 bề rộng, hai lỗi tách bạch. **Lỗi A đo bằng câu FALSIFIABLE "khung có bám cửa sổ không"** (so 1920 vs 1366): so mực/khung là không thể sai vì chữ luôn giãn đầy khung. Tiêm lỗi: cột `1fr` + thẻ `100%` ⇒ ĐỎ · căn giữa hình ⇒ ĐỎ rail · nới khoảng cách cột sơ đồ ⇒ ĐỎ ở `dag.test` |

| 31 | **Khung hình thứ `k` suy được HOÀN TOÀN từ `trace[k].memory_snapshot` qua `visual_bindings`, không phụ thuộc gì khác** (2026-08-20). Đây là bất biến khoá trục hiển thị, và nó sinh ra từ một bug đã ship: cầu nối giữ `frames[0].objects` rồi vứt mọi khung sau, nên lời thuyết minh chạy tới bước 15 trong khi ngăn xếp trên hình vẫn RỖNG và các ô giá trị vẫn `0`. Chương trình do AI sinh **đúng**, interpreter chạy **đúng**, trace **đúng** — chỉ khúc nối vứt trạng thái; chẩn đoán nhầm thành "lỗi của AI" sẽ dẫn tới quyết định kiến trúc sai. Hệ quả bắt buộc: envelope mang **toàn bộ** chuỗi khung với snapshot đầy đủ mỗi khung (không delta — logic replay chính là chỗ trục hiển thị lệch khỏi trục ngữ nghĩa); renderer chỉ ĐỌC, được nội suy **pixel** giữa hai khung nhưng **cấm** bịa trạng thái ngữ nghĩa trung gian | `semantic_program/pipeline_adapter.py::compile_semantic_program_to_envelope` + `visual_adapter.py` | `test_frame_state_invariant.py` (envelope giữ đủ mọi khung của adapter; và hồi quy trực tiếp: không được mọi khung đều có ngăn xếp rỗng) |

| 32 | **Gộp bước nằm NGOÀI adapter, và pacer PHÂN HOẠCH chứ không CẮT** (2026-08-20). Gộp đặt trong `VisualTraceAdapter` là phá song ánh `frame k ⇔ trace[k]`, tức phá luôn tư cách định lý của bất biến #31 — nên nó thuộc `PresentationPacer`, chạy sau. Bất biến của pacer yếu hơn nhưng vẫn kiểm được: mỗi bước xem là một đoạn **liên tiếp** các khung máy; các đoạn phân hoạch **đầy đủ**, **không chồng lấn**, **không sinh khung mới**. Ngân sách trình bày tách hẳn ngân sách thực thi: chạm trần trình bày KHÔNG phải lỗi (hạ mức chi tiết cho tới khi vừa, và khai đang xem ở mức gộp nào), còn chạm trần thực thi thì phải BÁO. Gộp hai con số này làm một chính là nguyên nhân gốc của `MAX_REVEAL_STEPS` cắt `steps[:20]` không báo lỗi | `semantic_program/pacer.py::pace` | `test_pacer_partition.py` (phân hoạch đầy đủ · không chồng lấn · tổng khung bảo toàn ở 5000 khung — cắt là ĐỎ) |

| 33 | **Mọi primitive khai trong enum của contract BẮT BUỘC có nhánh xử lý trong adapter** (2026-08-20). Sinh ra từ `bar_chart`: contract liệt kê nó trong `VisualContainerBinding.primitive` nhưng `_adapt_single_step` không có nhánh nào, nên LLM khai `bar_chart` là ra object rỗng — lỗi CÂM, không đỏ ở đâu. Vá riêng một nhánh thì primitive kế tiếp lại rơi y hệt; nên luật là **đối sánh hai chiều** giữa enum và `HANDLED_PRIMITIVES`, thiếu hoặc thừa đều ĐỎ | `semantic_program/visual_adapter.py::VisualTraceAdapter.HANDLED_PRIMITIVES` | `test_primitive_coverage.py` (enum ⊆ handled **và** handled ⊆ enum) |

| 34 | **Binding bắt buộc không phân giải được → FAIL-CLOSED, không render một phần** (2026-08-20). Luật **không phải** "bỏ con trỏ rồi vẫn vẽ phần còn lại" — đó là hạ cấp âm thầm, đúng loại lỗi đã sinh ra bất biến #31 (con trỏ `i` neo vào container rỗng nên đè lên dòng chữ thuyết minh). Một `visual_binding` bắt buộc mà không phân giải được ở **bất kỳ** khung nào là hỏng hợp đồng: adapter/validation thất bại và **không phát canonical envelope**. Học sinh thà không thấy gì còn hơn thấy một cảnh thiếu thành phần mà không ai nói cho biết là đang thiếu. Lưu ý phạm vi: đòi phân giải **ít nhất một lần trong trace**, không đòi ở mọi khung — một con trỏ chưa được gán ở bước 0 là bình thường | `semantic_program/pipeline_adapter.py::_assert_bindings_resolvable` | `test_binding_fail_closed.py` (`VisualBindingUnresolved` khi binding không bao giờ phân giải) |

## 6. Bốn trục khái niệm

**Specialized ↔ Generic DSL.** Specialized = engine viết tay cho một bài (8
algorithm, logic.and_gate, binary, network) — chính xác tuyệt đối, không dùng
DSL. Generic = `generic.rule_scene` chạy SimulationSpec do AI compose trong DSL.
Gap của DSL **không** được lây sang specialized (bất biến #5).

**Interaction ↔ Edit.** *Interaction* đổi **state** (toggle/drag/what-if) qua
`module.apply` — spec không đổi. *Edit* đổi **cấu trúc spec** qua SimulationPatch
→ validate → rebuild. Không được trộn hai đường; UI không tự sửa scene.

*EditPolicy v1 (M7.14D)*: thao tác sửa được suy từ **cấu trúc spec**, không mặc
định giống nhau cho mọi cảnh generic — `spatial` (node/edge: thêm điểm/nối/xóa),
`structural` (container/heading/paragraph: thêm/sửa/xóa nội dung, **không** thêm
điểm), `value_only` (switch/lamp/value_box: chỉ tương tác sẵn có), `observation`
(có `move_along_path`: **khóa topology**). reason_code hai namespace: `policy.*`
(không hợp năng lực cảnh) vs `structure.*` (vi phạm luật DSL).
**LIMITATION có chủ đích**: cảnh LAI (vừa structural vừa node/edge) dùng
precedence bảo thủ (`move > structural > spatial > value_only`) — **multi-family
edit CHƯA được hỗ trợ**. `EditFamily` là phân loại của EditPolicy **v1**, không
phải taxonomy vĩnh viễn của hệ (taxonomy vĩnh viễn là `SEMANTIC_ROLES`).

**Canonical ↔ Learner.** Mô phỏng hệ sinh ra: đúng hoặc `capability_gap`. Thao
tác học sinh: được phép sai; sai mà có rule kiểm được → feedback; không có rule →
`unsupported_to_verify`, **không phán bừa**. Chi tiết: `docs/CORRECTNESS.md`.

**Offline ↔ Live.** Test mặc định không chạm mạng (guard ở biên httpx/fetch).
Live eval opt-in, có suite (smoke/full/boundary) và ngân sách API.

## 7. Điểm mở rộng

- **Domain chuyên biệt mới**: thêm `SimSpec` vào `catalog.py` + validator, tạo
  `frontend/src/simulations/domains/<domain>/` và một dòng `register…()`. Không
  đụng pipeline/store/registry.
- **Primitive DSL mới**: **chỉ sửa manifest** — validator, contract prompt,
  capability summary, `_GENERIC_SCHEMA` enum đều tự dẫn xuất. Nhớ mirror TS.
- **Suite eval mới**: gắn `tags` trong `dataset.py`.
- **Capability tùy chọn của module**: thêm field optional vào `SimulationModule`
  (tiền lệ: `timeline?` → `SimulationControls` hiện nút theo capability). Module
  không khai → UI mặc định **không** cho tính năng đó.
- **Renderer mới cho module có sẵn (M8)**: khai `renderers[mode]` + thêm mode vào
  `supportedVisualModes` — cả hai điều kiện mới có toggle (chống affordance rỗng).
  KHÔNG tạo simulation_id mới, KHÔNG fork engine, KHÔNG đụng store/registry/pipeline.
  Renderer nặng (Three.js) nạp qua `React.lazy` để code-split. Tiền lệ:
  `network/ui3d.tsx`.

## 8. Anti-pattern (đã từng gây bug thật)

1. **Viết tay enum song song manifest** — `_GENERIC_SCHEMA` từng thiếu `drag` →
   Gemini **không thể** phát ra dù prompt cho phép; fail cả 3 retry, không manh
   mối. Mọi enum phải dẫn xuất từ manifest.
2. **Hard-code theo tên bài/môn/tiêu đề** ("triangle", "web", "tam giác") — mọi
   quyết định phải suy từ **capability/cấu trúc spec**.
3. **Vá capability gap bằng tọa độ LLM đoán** — tạo "hình nhìn có vẻ đúng" mà sai
   bản chất (kéo M thì E/F/P đứng yên). Phải `capability_gap`.
4. **Mock LLM ở module consumer** — `call_gemini` được import vào 4 module với 4
   binding riêng; mock một chỗ không che chỗ khác. Guard phải ở **biên mạng**.
5. **Renderer tự sửa state/spec** — mọi biến đổi qua `apply` hoặc patch.
6. **Toolbar/affordance vô điều kiện** — UI phải dẫn xuất từ capability. Đã sửa
   ở M7.14D: `EditPolicy` suy từ chính spec (`edit_policy.py` + mirror
   `generic/edit-policy.ts`), thực thi ở **cả ba tầng** (affordance UI, patch FE,
   patch/edit BE) — ẩn nút là KHÔNG đủ.
7. **Chạy full live eval theo thói quen** — tốn quota; theo chính sách trong
   `CORRECTNESS.md §7`.
8. **`renderToString(<App/>)` để kiểm một view CÓ DỮ LIỆU** (M9-UX4) — zustand v5
   dùng `useSyncExternalStore`; khi SSR, React lấy **getServerSnapshot = initial
   state**, nên state vừa mutate KHÔNG hiện ra. Test kiểu này xanh/đỏ vì lý do
   sai: một assert `toContain("Thuật toán")` tưởng là đang kiểm thẻ Lịch sử, thực
   ra khớp nhãn domain của starter card ở **Home**. **Luật**: test SSR qua `App`
   chỉ hợp lệ ở **trạng thái đầu**; muốn kiểm view có dữ liệu thì **render thẳng
   component với prop** (vd `SessionCard` nhận `item`) hoặc assert trên `store()`.
9. **Ký tự Unicode hình khối làm icon** (M9-UX4) — `◧`/`◨` (U+25E7/25E8) không có
   glyph trong font hệ thống Windows → hiện **ô vuông rỗng (tofu)** ngay trên
   header. Icon phải là SVG, đừng phụ thuộc font.
10. **Chuỗi kĩ thuật lọt lên UI học sinh** (M9-UX3/UX4) — `simulation_id`
   (`algorithm.bubble_sort`) từng bị render ở `InputPanel` rồi `HistoryView`. Vá
   một chỗ **không** vá chỗ kia: luật phạm vi phải áp ở **mọi bề mặt** học sinh
   thấy, và tốt nhất là gom về **một component chung** (nay là `SessionCard`).
14. **Tin một bản soát "sạch" mà không chứng minh nó bắt được lỗi** (M9-UX7) —
   `scripts/audit-layout.mjs` lần chạy đầu báo "TẤT CẢ SẠCH". Đó đúng là loại kết
   quả xanh vì **đo nhầm trang** (cùng họ với anti-pattern #13). Hai thứ bắt buộc
   phải có trước khi tin: (a) **dấu vân tay trang** — soát xong phải khẳng định
   mình đã ở đúng route, sai thì thoát mã 2; (b) **tiêm lỗi giả** — cố ý thêm
   `margin-top: 7px` + icon lệch 9px, chạy lại, thấy nó bắt đủ, rồi mới trả CSS về.
   Một guard chưa từng thấy màu đỏ là một guard chưa được chứng minh.
12. **Tự chế ngôn ngữ thị giác trong khi dự án ĐÃ CÓ `DESIGN.md`** (M9-UX6) —
   `DESIGN.md` §Don't nói rõ: *"Don't paint a CTA or structural fill in any
   sticker-palette colour — those are decoration only"* và *"Don't introduce a
   second structural accent alongside primary"*. Tím/hồng/cam/teal là **trang trí**
   (chấm phân loại, minh hoạ); màu DUY NHẤT sơn hành động là `--primary`. Muốn một
   thẻ nổi lên thì dùng **surface tint** (`canvas-soft`), KHÔNG viền màu — đúng
   khuôn `pricing-plan-card-featured`. Ngoại lệ hợp lệ: §Semantic cho phép sticker
   palette mang **status** (xanh lá = đúng, cam = sai). Khoá bằng
   `components/ui-hygiene.test.ts`.
13. **Đặt guard ở chỗ phụ thuộc route** (M9-UX6) — guard cấm-emoji đầu tiên quét
   `renderToString(<App/>)`, mà SSR chỉ đi qua **trạng thái đầu** (Home) nên không
   bao giờ chạm workspace: emoji 🔮 (`PredictionBar`) và chuỗi `find_max`
   (`AnalysisCard`) **lọt qua guard xanh lè**. Guard vệ sinh phải quét **MÃ NGUỒN**,
   không quét HTML đã render — như vậy mọi component đều bị soi, kể cả component
   chưa có test nào đi qua.
11. **`var(--token)` trỏ vào token KHÔNG TỒN TẠI** (M9-UX5) — lỗi **IM LẶNG** và
   nguy hiểm nhất trong CSS: trình duyệt vứt **cả dòng khai báo**, không cảnh báo,
   không đỏ ở đâu. `global.css` gọi `var(--sp-2xl)` trong khi token thật là
   `--sp-xxl` → `.home-composer` mất `margin: 0 auto` → **ô nhập lệch hẳn sang
   trái**, `.home-title` mất margin → **chữ dí sát ô**, `.app-single` mất padding
   đáy. Trôi từ M9-UX1 tới M9-UX5 mới bị phát hiện — bằng cách **đo trong browser
   thật**, không phải bằng đọc code. Cùng lúc lộ thêm `--border`/`--radius-sm`/
   `--radius-md` (M8-PRE-LIP): `PredictionBar` suốt nay **không có viền, không bo
   góc**. Nay khoá bằng `styles/tokens.test.ts` (mọi `var()` phải có định nghĩa).

15. **Cầu nối giữ khung ĐẦU rồi phát narration chạy** (2026-08-20) — đã ship bug
    thật. `compile_semantic_program_to_envelope` lấy `frames[0].objects` rồi vứt
    toàn bộ khung còn lại, nên trên màn hình: thuyết minh đọc *"lấy `[` ra khỏi
    ngăn xếp, so với `]`, khớp nhau"* — **chính xác từng chi tiết** — trong khi
    ngăn xếp RỖNG, "Ký tự hiện tại" = `0`, "Kết quả" = `0`, con trỏ đè lên chữ.
    Hai bài học tách bạch: (a) **hình đóng băng mà lời vẫn chạy là lỗi CẦU NỐI,
    không phải lỗi của LLM** — chương trình sinh ra đúng, interpreter chạy đúng,
    trace đúng; đổ cho AI ở đây là chẩn đoán nhầm rồi sửa nhầm chỗ. (b) lỗi này
    **không có test nào bắt được** vì hợp đồng envelope không hề đòi khung thứ
    `k` phải khớp trạng thái bước `k` — cho tới khi bất biến #31 được viết ra.
    Cùng họ với #13: chỗ nào không có bất biến thì chỗ đó trôi im lặng.

## 9. Vị trí cache & pattern reuse

- **Tầng 1 — exact cache** (`main.py`, bảng `simulation_cache`): trước pipeline;
  version ở **cột** (`dsl_version`/`policy_version`), lệch → miss. Chỉ cache
  `status == "ok"`.
- **Tầng 2 — pattern reuse** (`patterns.py`, bảng `simulation_patterns`): **sau
  classify**, chỉ generic; matching **tất định** (không embedding); template đóng
  băng cấu trúc/op, chỉ điền content slot; mọi spec adapt vẫn qua **4 cổng**.
- Edit (M7.14) **không** ghi cache, **không** persist pattern (chống poison).

## 10. Hướng khả dĩ trong tương lai (chưa làm, không phải cam kết)

- **M7.15 — Minimal Constraint-Aware Geometry**: projection/perpendicular/
  intersection/circle thành **rule tất định** → khi đó `invalid_with_feedback`
  mới có producer thật và generic experimental branch mới có nền.
- **`code_experiment`** (deferred): nếu sau này cho học sinh chạy code, **bắt
  buộc** sandbox (vd Pyodide), **không được bypass engine tất định**, và dự án
  **không** pivot thành IDE/code playground.
