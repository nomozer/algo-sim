# CURRENT_STATE.md — Trạng thái hiện tại

Cập nhật **sau mỗi milestone**. Chỉ ghi việc **đã thật sự xong** (có commit +
test). Không ghi việc đang định làm vào mục "đã xong".

Cập nhật lần cuối: sau **M7.14T** (`72a715d`).

## 1. Baseline

| | |
|---|---|
| pytest | **238 pass** (0 API call thật — guard là bằng chứng) |
| vitest | **115 pass** (0 network call) |
| build | `tsc -b && vite build` sạch |
| Docker | `docker compose up -d --build` OK (backend :8787 + Postgres) |
| Live smoke gần nhất (M7.14T) | 8/8 OK · 22 HTTP request · 0 retry · 0 transient · `gap_gate_recall = 1.0` · không false positive |

**Không chạy full live eval theo mặc định.**

## 2. Milestone đã hoàn thành (có commit)

| Milestone | Commit | Nội dung |
|---|---|---|
| M7.13A | `7fa4046` | Generic interaction semantics: `drag` (allowlist `node`), constraints (bounds/axis/snap), ownership rule, **position state-owned** (`GenericState.pos`), scene-mode consistency (exploratory/progressive/hybrid) truyền vào simulate |
| M7.13B | `d1d518c` | Exact cache version-aware (`simulation_cache`), validated **pattern reuse** (`simulation_patterns`), matcher tất định (không embedding), hybrid adaptation (deterministic fill + 1 call adapt), metrics reuse |
| M7.14 | `7835330` | **Correctness audit** (8 gap role, canonical↔learner policy, `docs/CORRECTNESS.md`), **SimulationPatch v1** + NL edit + manual edit generic, viewport safety (fit/reset, layering, label flip, edge label) |
| M7.14T | `72a715d` | Offline-first testing: hard network guard, gỡ key khỏi env test, `ALLOW_LIVE_AI=1` opt-in, suite smoke/full/boundary, API budget, metric **`gap_gate_recall`** song song |

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
3. **Toolbar edit của generic hiện vô điều kiện** — cảnh structural/binary cũng
   thấy "Thêm điểm/Nối/Xóa". Đang sửa ở **M7.14D**.
4. **Chuyển Quan sát ↔ Chỉnh sửa cảm giác giật**: đã đo — render compute chỉ
   ~0.7 ms/lần (không phải thủ phạm). Nguyên nhân thật: `editText` nằm cùng
   component với SVG (mỗi ký tự re-render toàn bộ SVG) + layout shift khi thêm
   hàng toolbar + StrictMode nhân đôi render ở dev. Sửa ở **M7.14D**.
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

1. **Phase 0** — 3 file context (`ARCHITECTURE_MAP`, `CODE_INDEX`, `CURRENT_STATE`).
2. **M7.14D** — capability-driven EditPolicy + UI/UX hardening + fix lag đã chẩn đoán.
3. (sau đó) M7.15 geometry hoặc M8 3D — chưa chốt.
