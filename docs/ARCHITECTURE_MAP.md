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
| Vị trí object lúc chạy | `GenericState.pos` (engine-owned, **toạ độ miền 0–100**) | spec bất biến; drag chỉ đổi state |
| **Bố cục/kích thước canvas** | **RENDERER** — không bao giờ là engine state | xem quy tắc renderer-neutral bên dưới |
| Định tuyến bài → mô phỏng | `catalog.py` + classify (LLM) + capability gate (tất định) | gate có quyền phủ quyết |
| Đúng/sai của thao tác học sinh | **chỉ rule tất định** | không có rule → `unsupported_to_verify` |
| Cấu hình đang chạy | store (`active.config`) — **opaque**, bất biến | store mù domain |
| **Visual mode (2D/3D) đang hiển thị** | store — **lát trình bày** (`visualMode`, cạnh `leftOpen`) | M8: không bao giờ vào engine state/spec; **không do LLM chọn**; đổi mode không đụng active/cursor/prediction |
| Renderer khả dụng của một module | hợp đồng module (`supportedVisualModes` ∩ `renderers`) qua `simulations/renderer.ts` | **cấm** switch-case theo simulation_id |
| Mặt trình bày đang mở (home/workspace/history) | store — `view` (M9-UX1) | như visualMode: trình bày thuần, không đụng engine |
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
| 18 | **Nghĩa của chiều sâu 3D phải TRUNG THỰC** (M10): module có 3D khai `threeD.role` = `architectural_poc` (Z chỉ là bố cục, vd `network.packet_routing`) hoặc `pedagogical` (Z mã hoá biến khái niệm thật, vd `network.protocol_encapsulation`: **Z = tầng giao thức**, X = chiều truyền). PoC KHÔNG được giả vờ có nghĩa khái niệm. PDU là state ngữ nghĩa dùng chung (2D+3D đọc cùng), 3D không tính lại PDU | `SimulationModule.threeD` (`types.ts`) + caption trong `encap-ui3d.tsx` | `render3d.test.tsx` (packet_routing=poc), `encap-render3d.test.tsx` (encap=pedagogical) |

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
