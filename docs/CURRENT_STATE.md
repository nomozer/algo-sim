# CURRENT_STATE.md — Trạng thái hiện tại

Cập nhật **sau mỗi milestone**. Chỉ ghi việc **đã thật sự xong** (có commit +
test). Không ghi việc đang định làm vào mục "đã xong".

Cập nhật lần cuối: sau **M7.FREEZE**.

> ## 🔒 M7.x ĐÃ ĐÓNG — 2D FEATURE FREEZE ĐANG HIỆU LỰC
>
> - **M7.x CLOSED.** 2D core đủ cho mục tiêu luận văn.
> - **M7.15 (geometry) KHÔNG nằm trong kế hoạch.**
> - Geometry solver · theorem prover/CAS · code playground · RAG/OCR:
>   **hoãn hoặc ngoài phạm vi** (xem §6, §8).
> - **Milestone kế tiếp: M8 — Generic 3D Renderer.**

## 1. Baseline

| | |
|---|---|
| pytest | **251 pass** (0 API call thật — guard là bằng chứng) |
| vitest | **141 pass** (0 network call) |
| build | `tsc -b && vite build` sạch |
| Docker | `docker compose up -d --build` OK (backend :8787 + Postgres) |
| Live smoke gần nhất (M7.14T) | 8/8 OK · 22 HTTP request · 0 retry · 0 transient · `gap_gate_recall = 1.0` · không false positive |

**Không chạy full live eval theo mặc định.**

### Nhật ký live call (ghi chính xác, không ghi khoảng)

| Khi nào | Suite/case | HTTP request | retry | transient |
|---|---|---|---|---|
| M7.14T | smoke suite (8 đề) | **22** | 0 | 0 |
| M7.14D — run A (code trước fix empty-ops) | 3 case edit: structural+đoạn văn (1) · structural+"thêm điểm P1" (2) · spatial+"thêm D nối A" (1) | **4** | 0 | 0 |
| M7.14D — run B (sau fix, chỉ case 2) | LLM đề xuất `node` trước → policy reject → retry → từ chối | **3** | 0 | 0 |
| M7.14D — run C (sau fix, chỉ case 2, đo lại) | LLM từ chối ngay lần đầu | **1** | 0 | 0 |
| **Tổng M7.14D** | | **8** | 0 | 0 |

Case 2 tốn 1 hoặc 3 request tùy LLM có thử đề xuất `node` trước hay không —
**cả hai đường đều ra đúng phán quyết** `policy.operation_not_allowed`.
M7.14D.1 là **UI-only: 0 live call**.

## 2. Milestone đã hoàn thành (có commit)

| Milestone | Commit | Nội dung |
|---|---|---|
| M7.13A | `7fa4046` | Generic interaction semantics: `drag` (allowlist `node`), constraints (bounds/axis/snap), ownership rule, **position state-owned** (`GenericState.pos`), scene-mode consistency (exploratory/progressive/hybrid) truyền vào simulate |
| M7.13B | `d1d518c` | Exact cache version-aware (`simulation_cache`), validated **pattern reuse** (`simulation_patterns`), matcher tất định (không embedding), hybrid adaptation (deterministic fill + 1 call adapt), metrics reuse |
| M7.14 | `7835330` | **Correctness audit** (8 gap role, canonical↔learner policy, `docs/CORRECTNESS.md`), **SimulationPatch v1** + NL edit + manual edit generic, viewport safety (fit/reset, layering, label flip, edge label) |
| M7.14T | `72a715d` | Offline-first testing: hard network guard, gỡ key khỏi env test, `ALLOW_LIVE_AI=1` opt-in, suite smoke/full/boundary, API budget, metric **`gap_gate_recall`** song song |
| Phase 0 | `9034d7c` | Context docs: `ARCHITECTURE_MAP` / `CODE_INDEX` / `CURRENT_STATE` |
| M7.14D | `27c0f1f` | **EditPolicy v1**: affordance sửa suy từ spec (spatial/structural/value_only/observation), reason_code `policy.*` vs `structure.*`, enforce 3 tầng; EditBar tách component (fix lag); stable control shell; Esc hủy công cụ |
| M7.14D.1 | `af6dc4f` | UI-only: ẩn nút "Chỉnh sửa" khi policy không có công cụ thật (`hasMeaningfulEditAffordance`) — value_only/observation không còn chế độ sửa RỖNG; backend policy giữ nguyên |
| **M7.FREEZE** | *(commit này)* | **Đóng M7.x.** Gỡ bố cục pixel khỏi `NetworkState` (blocker 3D duy nhất): state chỉ còn topology + route + steps + cursor; `layout2d` chuyển sang renderer. Quy tắc **renderer-neutral state** vào ARCHITECTURE_MAP. Danh sách **DO NOT ADD BEFORE M8** |

Milestone trước đó (M1–M7.12) đã có trong lịch sử commit gộp/ban đầu; kiến trúc
của chúng được mô tả trong `ARCHITECTURE_MAP.md`.

## 3. Năng lực đang hỗ trợ

**Chuyên biệt (engine tất định riêng, không dùng DSL):**
- `algorithm.*`: find_max, find_min, sum_if, count_if, linear_search,
  binary_search, bubble_sort, insertion_sort (+ what-if branch).
- `logic.and_gate` (bảng chân trị), `binary.decimal_to_binary` (bits⇄decimal),
  `network.packet_routing` (**route = BFS tất định**, không phải LLM).

**Generic (`generic.rule_scene`, DSL v1):**
- Object: `switch`, `lamp`, `value_box`, `node`, `edge`, `moving_entity`, `label`,
  `container`, `group`, `heading`, `paragraph`, `text`.
- Rule: `boolean` (and/or/not/xor), `weighted_sum`.
- Interaction: `toggle`, `drag` (chỉ `node`; bounds/axis/snap).
- Process: `reveal_sequence`, `move_along_path`.
- Scene mode: exploratory / progressive / hybrid (tất định từ analysis).
- Chỉnh sửa tăng dần: 5 patch op + NL edit; viewport fit/reset.
- **EditPolicy v1 (M7.14D)**: công cụ sửa suy từ spec — `spatial` (thêm điểm/nối/
  xóa) · `structural` (thêm/sửa/xóa nội dung, KHÔNG thêm điểm) · `value_only`
  (chỉ tương tác sẵn có) · `observation` (có `move_along_path` → khóa topology).
  M7.14D.1: cảnh không có công cụ thật (value_only/observation) **không hiện nút
  "Chỉnh sửa"** — không quảng bá affordance rỗng; toggle/kéo vẫn chạy.

**Hạ tầng:** exact cache + pattern reuse; eval harness (30 đề, suite smoke/full/
boundary); ingest text/docx/code/image.

## 4. Capability gap CỐ Ý (không phải bug — `docs/CORRECTNESS.md §5`)

Không primitive nào cover → `capability_gap`, **không** render xấp xỉ:

`geometric_projection` · `geometric_perpendicular` · `geometric_intersection` ·
`geometric_circle` · `geometric_locus` · `numeric_threshold` ·
`continuous_motion` · `arbitrary_algorithm`

Hệ quả đã verify live: bài hình học phức tạp (chân đường cao / giao điểm / đường
tròn ngoại tiếp / quỹ tích), "đèn sáng khi ít nhất 2 trong 3", quỹ đạo hành tinh,
"thuật toán em tự nghĩ" → **unsupported đúng và ổn định**.

## 5. Known issues / giới hạn đã biết

1. **`_simulate_with_metrics` (harness) mirror `stage_simulate` (pipeline)** —
   nguy cơ drift; chưa hợp nhất.
2. **`move_along_path` không bắt path phải đi theo edge có thật** (waypoint tường
   minh vẫn hợp lệ) — giữ có chủ đích; bài routing thật được specialized bảo vệ.
3. **Multi-family edit chưa hỗ trợ** (M7.14D): cảnh LAI (vừa structural vừa
   node/edge) dùng precedence bảo thủ → chỉ sửa được theo family thắng.
4. **StrictMode nhân đôi render ở dev** — chỉ ảnh hưởng cảm nhận khi chạy
   `npm run dev`, không ảnh hưởng bản build.
5. **`CLAUDE.md` bị gitignore** → sự thật bền vững phải nằm ở `docs/*`.
6. **Không có migration system** (SQLAlchemy `create_all`): thêm bảng OK, ALTER
   bảng cũ thì không. Bảng `problems` cũ còn orphan trong volume dev.
7. **Pattern chứa bool op lưu `status="candidate"`** → không auto-reuse (chống
   mẫu AND bị dùng cho đề OR). Cần benchmark/người duyệt để nâng `verified`.

## 5b. DO NOT ADD BEFORE M8 (scope freeze tạm thời)

Cho tới khi M8 bắt đầu, **không thêm** — trừ khi một **blocker 3D thật sự** đòi hỏi:

- specialized domain module mới;
- geometry solver (projection/perpendicular/intersection/circle/locus);
- theorem prover / CAS;
- code playground (`code_experiment`);
- mở rộng RAG / OCR;
- edit mode mới;
- primitive DSL mới tùy hứng;
- hệ learner-feedback mới;
- undo/redo · pan/zoom · style editor · topology editing;
- rule DSL mới không liên quan blocker M8.

Mục đích: chấm dứt vòng lặp M7.x tự nuôi chính nó.

## 6. Việc hoãn CÓ CHỦ ĐÍCH

- **M7.11 Slice 2 — CHƯA hoàn thành.**
- **M7.15 — Minimal Constraint-Aware Geometry**: projection/perpendicular/
  intersection/circle thành rule tất định. Chỉ khi đó `invalid_with_feedback` mới
  có producer thật và generic experimental branch mới có nền.
- **`invalid_with_feedback`**: đã có trong taxonomy, **chưa có producer** nào.
- **`code_experiment`**: deferred — cần sandbox, không được bypass engine tất
  định, **không** pivot thành IDE.
- **3D (M8)**: chưa bắt đầu.
- **Topology editing cho cảnh network-like**: chỉ mở khi EditPolicy cho phép
  tường minh.
- **Embeddings/pgvector/RAG/OCR/GraphRAG**: cố ý không làm.

## 7. Roadmap

1. ~~Phase 0 — 3 file context~~ (`9034d7c`).
2. ~~M7.14D / D.1 — capability-driven EditPolicy + UI/UX~~ (`27c0f1f`, `af6dc4f`).
3. ~~M7.FREEZE — gỡ blocker 3D, đóng M7.x~~ (commit này).
4. **M8 — Generic 3D Renderer** (kế tiếp).
   - Slice 1: renderer selection (thêm renderer vào **cùng module**, dùng thật
     `supportedVisualModes` + `visualMode` trong store) · `z?` optional cho
     `pos`/`SimAction.move`/drag bounds.
   - PoC đầu tiên: **`network.packet_routing`** + cảnh generic
     `node+edge+moving_entity+move_along_path` (cùng primitive; `packetAt`/
     `entityPos` đã là id nút nên 3D chỉ cần bố cục riêng).
   - **KHÔNG 3D hoá**: trang web/structural · cổng AND · đổi nhị phân —
     3D chỉ để trang trí, không thêm giá trị sư phạm.
5. Không có M7.15.
