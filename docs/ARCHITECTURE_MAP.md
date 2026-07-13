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
| Vị trí object lúc chạy | `GenericState.pos` (engine-owned) | spec bất biến; drag chỉ đổi state |
| Định tuyến bài → mô phỏng | `catalog.py` + classify (LLM) + capability gate (tất định) | gate có quyền phủ quyết |
| Đúng/sai của thao tác học sinh | **chỉ rule tất định** | không có rule → `unsupported_to_verify` |
| Cấu hình đang chạy | store (`active.config`) — **opaque**, bất biến | store mù domain |

## 4. Hướng phụ thuộc (không được đảo)

```
manifest ← validator ← catalog ← pipeline ← main
manifest ← representation / semantic / patterns / patch
types ← registry ← store ← components
module (domain) → types/registry;  renderer → state (chỉ ĐỌC)
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

## 6. Bốn trục khái niệm

**Specialized ↔ Generic DSL.** Specialized = engine viết tay cho một bài (8
algorithm, logic.and_gate, binary, network) — chính xác tuyệt đối, không dùng
DSL. Generic = `generic.rule_scene` chạy SimulationSpec do AI compose trong DSL.
Gap của DSL **không** được lây sang specialized (bất biến #5).

**Interaction ↔ Edit.** *Interaction* đổi **state** (toggle/drag/what-if) qua
`module.apply` — spec không đổi. *Edit* đổi **cấu trúc spec** qua SimulationPatch
→ validate → rebuild. Không được trộn hai đường; UI không tự sửa scene.

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
6. **Toolbar/affordance vô điều kiện** — UI phải dẫn xuất từ capability (đây
   chính là vấn đề M7.14D đang sửa).
7. **Chạy full live eval theo thói quen** — tốn quota; theo chính sách trong
   `CORRECTNESS.md §7`.

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
