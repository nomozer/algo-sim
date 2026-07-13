# CURRENT_STATE.md — Trạng thái hiện tại

Cập nhật **sau mỗi milestone**. Chỉ ghi việc **đã thật sự xong** (có commit +
test). Không ghi việc đang định làm vào mục "đã xong".

Cập nhật lần cuối: sau **M7.14D.1** (xem bảng milestone).

## 1. Baseline

| | |
|---|---|
| pytest | **251 pass** (0 API call thật — guard là bằng chứng) |
| vitest | **137 pass** (0 network call) |
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
| M7.14D.1 | *(commit này)* | UI-only: ẩn nút "Chỉnh sửa" khi policy không có công cụ thật (`hasMeaningfulEditAffordance`) — value_only/observation không còn chế độ sửa RỖNG; backend policy giữ nguyên |

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

## 7. Roadmap gần

1. ~~Phase 0 — 3 file context~~ (xong, `9034d7c`).
2. ~~M7.14D — capability-driven EditPolicy + UI/UX hardening~~ (xong).
3. Chưa chốt: M7.15 (geometry constraints) hoặc M8 (3D).
