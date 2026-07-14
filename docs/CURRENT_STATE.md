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
| pytest | **289 pass** (0 API call thật — guard là bằng chứng) |
| vitest | **153 pass** (0 network call) |
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
| M8-PRE (S3) | verify có mục tiêu: đề "phân tích hệ thống" + guard quan hệ đời thường; 3 lần diag đếm object/attempt; 1 lần probe schema | **55** | 6 | 9 (1 ReadTimeout + 8× HTTP 503 "high demand" ở lần chạy cuối) |
| M8-PRE (plan C) | inspect composition (2 dump) + verify sau nén (V1 + V2) | **15** | 1 | 1 |
| M8-PRE (stability smoke) | đề "phân tích hệ thống" × **5 lần hoàn tất** | **19** | 2 | 2 (429/5xx — retry nuốt trọn, **0 run bị hỏng**) |

**TRẠNG THÁI của đề "phân tích hệ thống" — sau STABILITY SMOKE 5 lần chạy hoàn tất:**
- Định tuyến: ✅ **đã sửa** — **0/5** lần `unsupported` im lặng; **5/5** vào `generic.rule_scene`.
- Vai trò hệ thống: ✅ **5/5** có đủ actor + process + data_store (4/5 có cả input/output).
- Chiều luồng dữ liệu: ✅ **39/39 edge (100%) có `directed`** — cổng suy tất định hoạt
  động ổn định (LLM vẫn không tự khai, đúng như đã đo).
- Kết quả: ✅ **5/5 validate end-to-end**, đều là `executable_simulation`
  (`reveal_sequence` 5/5; `move_along_path` 3/5) — **result mode khai báo trung thực**.
- Ngân sách object: **KHÔNG cảnh hợp lệ nào cần > 20** (spec cuối: 13, 14, 15, 17, 17).
  Khẳng định lại kết luận plan C: **không nâng hạn mức, không cần capability-aware budget.**
- **Nén dư thừa: fired 0/5.** Nó là LƯỚI AN TOÀN, không phải thứ đang gánh tính năng.
  Ở run 4 có một bản nháp 27 object bị từ chối vì hạn mức — nén **cố ý KHÔNG cứu** vì
  các label đó **không trùng hệt** nhãn inline nào (không có dư thừa chứng minh được),
  đúng thiết kế bảo thủ; **retry của pipeline** phục hồi (27 → 16 → 15 ✅).
- Cách diễn đạt ĐƯỢC PHÉP: *"Repeated targeted live verification showed consistent
  end-to-end success across a five-run stability sample."*
  **CẤM** nói: ~~"đã chứng minh tin cậy về mặt thống kê"~~ (n = 5, không đủ).

**M8-PRE (S3) — điều live PHÁT HIỆN ra mà offline không thấy được:**
1. LLM dựng đúng `actor→process→data_store` trong `from`/`to` nhưng **KHÔNG BAO GIỜ khai
   `directed`** — kể cả khi contract yêu cầu tường minh, kể cả sau khi bị từ chối kèm
   lý do (3 attempt liên tiếp). Probe riêng chứng minh **schema KHÔNG phải thủ phạm**
   (gọi trực tiếp thì Gemini phát `directed: true` bình thường) → **không phải
   anti-pattern #1**, mà là *salience* trong prompt dài.
   → **Xử lí đúng kiến trúc: SUY tất định ở server**, không đi xin LLM. Chiều đã nằm
   sẵn trong `from`/`to`; validator (cả hai tầng) tự gắn `directed` cho cạnh nối hai
   node vai trò hệ thống. Không đụng hình học, không đụng topology mạng (2 chiều).

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
| **M7.FREEZE** | `7452cbf` | **Đóng M7.x.** Gỡ bố cục pixel khỏi `NetworkState` (blocker 3D duy nhất): state chỉ còn topology + route + steps + cursor; `layout2d` chuyển sang renderer. Quy tắc **renderer-neutral state** vào ARCHITECTURE_MAP. Danh sách **DO NOT ADD BEFORE M8** |
| **M8-PRE** | *(commit này)* | **Coverage + Pedagogical audit → hardening trước M8** (`docs/COVERAGE.md`). **S1**: metadata `EvalItem` (optional, backward-compat) + 4 pool đề mới (`curriculum`/`capability`/`cross_domain`/`thesis` 12 case) + **luật kết nạp** thực thi bằng code; `dataset.py` 30 case **ĐÓNG BĂNG**. Vá lỗ hổng bằng chứng **sắp xếp** (engine có từ lâu, benchmark 0 case). **S2**: `edge.directed` (manifest-first) + node_type mở rộng (actor/process/data_store/input/output) + mũi tên ở renderer + analyze/classify/simulate hỗ trợ **sơ đồ hệ thống thông tin** → đề "phân tích hệ thống" **không còn bị từ chối im lặng**. `CACHE_VERSION` 5→6 |

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
8. **[M8-PRE plan C — ĐÃ XỬ LÍ bằng nén dư thừa; hạn mức GIỮ NGUYÊN 20]**
   Cảnh sơ đồ hệ thống từng vượt `max_objects = 20` → 422.
   **Ngữ nghĩa của con số 20** (đã inspect): **KHÔNG phải bất biến ngữ nghĩa** —
   vào repo từ `0621910` cùng DSL v1, không có lý do ghi trong RULES.md. Thực chất
   là **ngân sách CHỨA đầu ra LLM + ngân sách DỄ ĐỌC của renderer** (canvas 600×340,
   toạ độ miền 0–100). Engine không phụ thuộc con số này. Khoá bởi
   `test_manifest.py` (assert `== 20`) + test dẫn xuất; **hard-code ngoài manifest
   đúng MỘT chỗ**: `frontend/.../generic/validate.ts` (mirror `MAX_OBJECTS`).
   **Bằng chứng quyết định (đo live):** MỌI cảnh hệ thống HỢP LỆ về ngữ nghĩa đều
   **nằm gọn trong 20** (đếm được: 11, 12, 14, 14, **19** object). Chỉ các bản nháp
   BỊ PHỒNG mới vượt — do Gemini vừa đặt `label` inline cho node/edge, VỪA tạo thêm
   **một object `label` rời lặp lại đúng chuỗi đó** (11 label rời cho 5 node + 6 edge).
   → **Không nâng hạn mức. Không cần capability-aware budget.** Thay vào đó:
   `compact_redundant_labels` (validator, cả hai tầng) gỡ **chỉ** label rời TRÙNG HỆT
   nhãn inline của node/edge có thật, **chỉ khi cảnh đã vượt hạn mức**, và **không bao
   giờ** gỡ label mang chữ riêng hay đang bị tham chiếu cấu trúc. Cảnh trong hạn mức
   không bị đụng tới → **0 bề mặt regression**.

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
3. ~~M7.FREEZE — gỡ blocker 3D, đóng M7.x~~ (`7452cbf`).
4. ~~M8-PRE — coverage/pedagogical audit + S1 dataset + S2 directed data-flow~~ (commit này).
   Còn **1 quyết định mở**: known issue #8 (`max_objects`).
5. **M8 — Generic 3D Renderer: *architectural-first, pedagogically bounded*** (kế tiếp).
   - **Tuyên bố được phép**: "AlgoSim dùng lại config/state/timeline tất định trên
     nhiều renderer, và **chỉ** áp dụng 3D cho nội dung mà chiều sâu/phân tầng thực
     sự mang giá trị biểu diễn." **CẤM** tuyên bố "3D luôn giúp học tốt hơn"
     (`COVERAGE.md §8` — audit không tìm được bằng chứng cho điều đó).
   - PoC ưu tiên: **kiến trúc mạng phân tầng / topology / dữ liệu di chuyển**.
   - **KHÔNG 3D hoá**: cổng logic · nhị phân · **sắp xếp** · **mảng** · trang web ·
     **bảng CSDL**.
6. **Sau M8 — ưu tiên #1: learner practice/experimental mode** (`COVERAGE.md §6`) —
   giá trị sư phạm cao hơn thêm primitive mới, vì **ground truth đã có sẵn miễn phí**
   trong mọi engine tất định. Sau đó mới tới `table/grid` (mở khoá CSDL).
   - Slice 1: renderer selection (thêm renderer vào **cùng module**, dùng thật
     `supportedVisualModes` + `visualMode` trong store) · `z?` optional cho
     `pos`/`SimAction.move`/drag bounds.
   - PoC đầu tiên: **`network.packet_routing`** + cảnh generic
     `node+edge+moving_entity+move_along_path` (cùng primitive; `packetAt`/
     `entityPos` đã là id nút nên 3D chỉ cần bố cục riêng).
   - **KHÔNG 3D hoá**: trang web/structural · cổng AND · đổi nhị phân —
     3D chỉ để trang trí, không thêm giá trị sư phạm.
5. Không có M7.15.
