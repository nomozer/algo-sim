# CURRENT_STATE.md — Trạng thái hiện tại

Cập nhật **sau mỗi milestone**. Chỉ ghi việc **đã thật sự xong** (có commit +
test). Không ghi việc đang định làm vào mục "đã xong".

Cập nhật lần cuối: sau **M9-UX3** — Home gọn + preview đúng cơ chế + vá rò rỉ fixture.

> ## ✅ M8 SLICE 1+2 HOÀN THÀNH — SCOPE FREEZE §5b VẪN HIỆU LỰC CHO PHẦN CÒN LẠI
>
> - **M8 đã chứng minh tuyên bố kiến trúc**: cùng config → cùng engine tất định →
>   cùng state/timeline/action/prediction → renderer 2D **hoặc** 3D
>   (`network.packet_routing` là PoC duy nhất, đúng kế hoạch).
> - **3D là renderer, không phải domain**: không có simulation_id "_3d" nào,
>   không fork engine (bất biến #16, `ARCHITECTURE_MAP.md §5`).
> - **M8 Slice 3 (mạng phân tầng) HOÃN post-M8**: cần năng lực tất định MỚI
>   (đóng gói/mở gói qua tầng — biến đổi trạng thái PDU), không fake bằng
>   reveal-boxes (xem §6).
> - M7.15 (geometry) vẫn KHÔNG nằm trong kế hoạch; danh sách §5b vẫn áp dụng
>   cho mọi thứ không phải blocker renderer.

## 1. Baseline

| | |
|---|---|
| pytest | **289 pass** (0 API call thật — guard là bằng chứng) |
| vitest | **271 pass** (0 network call; +2 M9-UX3: một-tranh-một-cơ-chế · InputPanel công khai) |
| build | `tsc -b && vite build` sạch — bundle chính 258.6KB; chunk Three.js 549KB **code-split**, chỉ tải khi bấm 3D |
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
| **M8 (Slice 1+2)** | frontend-only: kiến trúc renderer + network 3D; nghiệm thu bằng bài mẫu offline trên browser thật | **0** | 0 | 0 |

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
| **M8-PRE** | `cb31adc` | **Coverage + Pedagogical audit → hardening trước M8** (`docs/COVERAGE.md`). **S1**: metadata `EvalItem` (optional, backward-compat) + 4 pool đề mới (`curriculum`/`capability`/`cross_domain`/`thesis` 12 case) + **luật kết nạp** thực thi bằng code; `dataset.py` 30 case **ĐÓNG BĂNG**. Vá lỗ hổng bằng chứng **sắp xếp** (engine có từ lâu, benchmark 0 case). **S2**: `edge.directed` (manifest-first) + node_type mở rộng (actor/process/data_store/input/output) + mũi tên ở renderer + analyze/classify/simulate hỗ trợ **sơ đồ hệ thống thông tin** → đề "phân tích hệ thống" **không còn bị từ chối im lặng**. `CACHE_VERSION` 5→6 |
| M8-PRE-LIP | `f4e3793` | **PredictionCapability** (`predict?` cùng khuôn `timeline?`/`edit?`) + **một** `PredictionBar` dùng chung 2 domain (network: chọn nút; algorithm: có/không); engine tất định chấm; kết quả ở `store.prediction` TÁCH khỏi engine state |
| **M9-UX2** | `08a9a7a` | **Onboarding trực quan + simulation-first + phạm vi luận văn.** `OfflineSample.visibility` (metadata tường minh; "public" mặc định · "internal_fixture") — `publicCatalog()` 12 mẫu Tin học THPT cho học sinh; tam giác + 3 bản "(tổng quát)" thành fixture nội bộ (giữ năng lực + parity coverage; lịch sử vẫn reopen bằng envelope — không phụ thuộc danh mục). `SamplePreview` — 8 preview SVG tĩnh theo simulation_id/metadata (fallback generic). Home: rộng 1040, card preview + chữ, recent card khác biệt ("Tiếp tục ▸"), trạng thái máy chủ im khi ổn. Workspace: cột 264/1fr/300, panel trái đóng mặc định — sân khấu là tiêu điểm. GỠ thẻ "Ứng dụng của cơ chế này" + metadata `applications` (chỉ nuôi thẻ đó). Nguyên tắc #7 vào COVERAGE §2. Acceptance browser 22/22; 0 live AI |
| **M9-UX3** | *(nhánh `m9-ux3-home-preview`)* | **Home gọn + preview ĐÚNG CƠ CHẾ + vá rò rỉ fixture.** `SamplePreview` 7 → **13 kind**, luật mới **một tranh = một cơ chế = một bài**: 8 bài thuật toán có 8 tranh riêng (`algorithm-bars` find_max · `bars-min` · `sum-threshold` Σ · `count-threshold` bộ đếm · `linear-scan` · `search-range` binary · `sort-swap` bubble · `insertion-lift`). Vá **2 tranh DẠY SAI** (không chỉ trùng): `linear_search` mượn trái/giữa/phải của binary (tìm tuần tự không có mid); `insertion_sort` mượn mũi tên đổi chỗ của bubble (chèn là DỜI — chính `decision.ts` hỏi hai câu khác nhau). Vi phạm nguyên tắc sư phạm #6 (COVERAGE §2.6), nay khoá bằng test "không hai bài thuật toán nào dùng chung một tranh". `ProblemInput` **hai vỏ một lõi** (`variant` hero pill / compact) — hết textarea 5 dòng rỗng + nút xanh kín chiều ngang. Home: card **hàng ngang** (cao bằng nhau bất kể tiêu đề), 2 cột, chấm màu `DOMAIN_COLOR` (hằng số có sẵn, Home chưa từng dùng), cột 1040 → **920**, "xem tất cả" **gom nhóm** theo domain. `InputPanel`: `offlineCatalog()` → **`publicCatalog()`** + bỏ `simulation_id` khỏi UI — luật phạm vi M9-UX2 trước đó **mới chỉ áp ở Home**, panel trái vẫn rò tam giác + 3 bản "(tổng quát)" + chuỗi `algorithm.find_max`. Nghiệm thu browser thật (headless Chrome); **0 live AI** |
| **M9-UX1** | `1f95e92` | **Home + phiên học + lịch sử zero-AI + vệ sinh RULES.** Home thật (view mặc định): MỘT hành động chính + gợi ý chọn lọc + "Tiếp tục học"; không inspector/timeline rỗng trước khi có bài. `state/history.ts`: lịch sử BỀN (localStorage schema v1, whitelist, dedup theo id tất định, max 30 evict, corrupt-safe) lưu **envelope đã validate** → **mở lại ZERO-AI** (bất biến #17) + khôi phục lastCursor/visualMode; reset/goHome không phá lịch sử. Header gọn [Trang chủ][Lịch sử]; HistoryView đủ item + xóa. §17: `applications?` trên module (tĩnh, không LLM) cho 4 domain chuyên biệt. RULES.md → con trỏ ngắn (thứ tự đọc + 10 luật cứng); bản v0.3 lưu `docs/legacy/RULES_v0.3.md` kèm cảnh báo LEGACY (khoá bằng `rules-hygiene.test.ts`). Acceptance browser thật 23/23 (reload + reopen 0 /api/analyze); 0 live AI |
| **M9-S1** | `548f1fc` | **Mechanism-aligned interactions (algorithm).** `decision.ts` — điểm quyết định theo cơ chế từng bài: max/min "có cập nhật?", sum/count "cộng/tăng?", linear "tìm thấy chưa?", binary "**nửa nào bị loại**" (3 lựa chọn, hỏi ở bước lấy mid), sorts "đổi chỗ?/dời?"; đáp án + bằng chứng nhân quả (số thật, biến trước → sau) DẪN XUẤT từ sự kiện trace kế tiếp; MỘT nguồn nuôi cả predict lẫn dải nhân quả. `interaction-policy.ts` — hết "một swap cho cả 8 bài": free (sorts) · framed (linear: chi phí) · challenge (find_max/min: bất biến vùng-đã-duyệt; binary: tiền điều kiện dãy-đã-sắp — ẩn mặc định, mở qua nút thí nghiệm có khung) · hidden (sum/count). Engine: narration bước quyết định thành CÂU HỎI (không lộ đáp án sớm), marks `eliminated` cho phần tử đã duyệt. Nguyên tắc sư phạm #6 vào `COVERAGE.md §2`. UX acceptance 18/18 trên browser thật; 0 live AI |
| **M8 Slice 1+2** | `f83b635`, `18e4c2a`, `cce75fc` | **Shared 2D/3D renderer.** S1: `renderers?` trên SimulationModule ("2d" mặc định = Workspace), `simulations/renderer.ts` (khả dụng = tuyên bố ∩ có renderer thật), `store.visualMode` (lát TRÌNH BÀY — đổi mode không đụng active/cursor/prediction, không rebuild, không AI), `VisualModeToggle` theo capability. S2: `network/ui3d.tsx` — Three.js thuần (KHÔNG R3F), `React.lazy` code-split; `layout3d` renderer-owned (route z=0, ngoài route lùi sâu); OrbitControls xoay+zoom khoá pan; reset GÓC NHÌN ≠ reset mô phỏng; WebGL fail → fallback tiếng Việt; nội suy HÌNH ẢNH gói tin, sự thật vẫn là `packetAt`. Nghiệm thu browser thật 16/16 (headless Chrome + SwiftShader, bài mẫu offline). **Bất biến #16** vào ARCHITECTURE_MAP. Slice 3 (mạng phân tầng) HOÃN — cần semantics đóng gói tất định mới |

Milestone trước đó (M1–M7.12) đã có trong lịch sử commit gộp/ban đầu; kiến trúc
của chúng được mô tả trong `ARCHITECTURE_MAP.md`.

## 3. Năng lực đang hỗ trợ

**Chuyên biệt (engine tất định riêng, không dùng DSL):**
- `algorithm.*`: find_max, find_min, sum_if, count_if, linear_search,
  binary_search, bubble_sort, insertion_sort. **M9-S1**: mỗi bài có ĐIỂM QUYẾT
  ĐỊNH riêng theo cơ chế ẩn (dự đoán + dải nhân quả cùng nguồn `decision.ts`) và
  **chính sách what-if theo cơ chế** (`interaction-policy.ts`) — what-if branch
  chỉ mở nơi nó dạy được điều gì đó.
- `logic.and_gate` (bảng chân trị), `binary.decimal_to_binary` (bits⇄decimal),
  `network.packet_routing` (**route = BFS tất định**, không phải LLM) — M8:
  module DUY NHẤT có renderer **2D + 3D** (cùng engine state; các module khác
  CỐ Ý 2D-only vì 3D không thêm giá trị sư phạm, `COVERAGE.md §8`).

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
- hệ learner-feedback mới — **đã MỞ HẸP MỘT LẦN cho M8-PRE-LIP, nay ĐÓNG LẠI** (xem §5c);
- undo/redo · pan/zoom · style editor · topology editing;
- rule DSL mới không liên quan blocker M8.

Mục đích: chấm dứt vòng lặp M7.x tự nuôi chính nó.

## 5c. M8-PRE-LIP — Learning Interaction Proof (ĐÃ XONG, ĐÃ RE-FREEZE)

**Đây KHÔNG phải `practice_activity` đầy đủ.** Đây là **bằng chứng tối thiểu** rằng
**MỘT** optional capability + **MỘT** UI dùng chung phục vụ được **NHIỀU** domain:

> Quan sát → Dự đoán/Chọn → Nộp → **engine TẤT ĐỊNH chấm** → phản hồi là **dữ liệu
> kết quả** → **mô phỏng canonical KHÔNG ĐỔI**.

- `PredictionCapability` (`predict?` trong `SimulationModule`) — cùng khuôn
  `timeline?` / `edit?`: **không khai → không có UI** (3 domain còn lại giữ nguyên).
- Một component **duy nhất** `components/PredictionBar.tsx` phục vụ **cả hai**:
  `network` (N lựa chọn — chọn nút) và `algorithm` (2 lựa chọn — có/không).
- Ground truth **có sẵn miễn phí** trong engine: BFS route (network) · trace thật
  (algorithm). **Không engine mới, không LLM, không gọi mạng.**
- `network.packet_routing` **hết watch-only**: trước đây `apply: (state) => state`.
- Kết quả chấm sống ở `store.prediction`, **TÁCH KHỎI** engine state → học sinh sai
  cũng không đụng được dòng chính (khoá bằng test).
- Phát ngôn thận trọng (network): chỉ nói *"không phải chặng kế tiếp trên đường đi
  ngắn nhất mà engine BFS đã tính"*; nếu nút học sinh chọn **cũng** nằm trên một
  đường ngắn nhất khác thì **phải nói rõ**. **Cấm** nói "đi lối đó là không thể".

**FREEZE ĐÃ ĐÓNG LẠI.** Mở rộng tiếp (chấm điểm, mục tiêu/nhiệm vụ, theo dõi tiến
độ, gợi ý, phản hồi hội thoại, dashboard) → **post-M8**, cần duyệt riêng.

**M9-S1 dùng LẠI capability này, không thêm framework thứ hai**: nội dung câu hỏi
của domain algorithm được nâng từ MỘT câu chung ("có biến nào được cập nhật
không?") thành câu hỏi ĐÚNG CƠ CHẾ từng bài (kể cả 3 lựa chọn cho binary_search —
hợp đồng `PredictionCapability` vốn đã hỗ trợ N lựa chọn). Không đổi
`PredictionBar`, không đổi store, không đổi hợp đồng module.

> **`practice_activity` vẫn là PARTIAL / CHƯA IMPLEMENT** (xem `COVERAGE.md` §6).
> M9-S1 **không** thay đổi điều này: vẫn không có chấm điểm / mục tiêu-nhiệm vụ /
> theo dõi tiến độ / gợi ý / dashboard.

## 6. Việc hoãn CÓ CHỦ ĐÍCH

- **M7.11 Slice 2 — CHƯA hoàn thành.**
- **M7.15 — Minimal Constraint-Aware Geometry**: projection/perpendicular/
  intersection/circle thành rule tất định. Chỉ khi đó `invalid_with_feedback` mới
  có producer thật và generic experimental branch mới có nền.
- **`invalid_with_feedback`**: đã có trong taxonomy, **chưa có producer** nào.
- **`code_experiment`**: deferred — cần sandbox, không được bypass engine tất
  định, **không** pivot thành IDE.
- **3D phân tầng (M8 Slice 3)**: hoãn post-M8 — cần semantics đóng gói/mở gói
  tất định (trạng thái PDU biến đổi qua tầng); **cấm** giả bằng reveal-boxes.
- **M9-S2 / M9-S3** (theo M9-PED-AUDIT §8): *binary — thử thách dựng số N* và
  *packet routing — học sinh tự dẫn gói tin, engine so chi phí với BFS*. Chưa làm.
- **Topology editing cho cảnh network-like**: chỉ mở khi EditPolicy cho phép
  tường minh.
- **Embeddings/pgvector/RAG/OCR/GraphRAG**: cố ý không làm.

## 7. Roadmap

1. ~~Phase 0 — 3 file context~~ (`9034d7c`).
2. ~~M7.14D / D.1 — capability-driven EditPolicy + UI/UX~~ (`27c0f1f`, `af6dc4f`).
3. ~~M7.FREEZE — gỡ blocker 3D, đóng M7.x~~ (`7452cbf`).
4. ~~M8-PRE — coverage/pedagogical audit + S1 dataset + S2 directed data-flow~~
   (`cb31adc`). Quyết định mở #8 (`max_objects`) đã chốt ở plan C: giữ 20 + nén.
5. ~~M8-PRE-LIP — PredictionCapability (2 domain, 1 UI)~~ (`f4e3793`).
6. ~~**M8 Slice 1+2 — shared 2D/3D renderer + network 3D PoC**~~ (nhánh
   `m8-shared-renderer`). Đã chứng minh: cùng config/state/timeline/action/
   prediction → renderer 2D hoặc 3D; 3D là renderer, không phải domain.
   - **Tuyên bố được phép**: "AlgoSim dùng lại config/state/timeline tất định trên
     nhiều renderer, và **chỉ** áp dụng 3D cho nội dung mà chiều sâu/phân tầng thực
     sự mang giá trị biểu diễn." **CẤM** tuyên bố "3D luôn giúp học tốt hơn"
     (`COVERAGE.md §8`).
   - **KHÔNG 3D hoá** (giữ nguyên): cổng logic · nhị phân · **sắp xếp** · **mảng** ·
     trang web · **bảng CSDL**.
   - **Slice 3 (mạng phân tầng) HOÃN post-M8**: có cơ sở sư phạm (T12 B4; 12CS
     B22–24) nhưng đòi năng lực tất định MỚI — trạng thái PDU biến đổi khi qua
     tầng (đóng gói/mở gói). Reveal-boxes chỉ là progressive visualization,
     KHÔNG được gọi là executable simulation.
   - Chưa làm (không phải blocker M8): `z?` optional cho `pos`/`SimAction.move`;
     3D cho cảnh generic `node+edge+moving_entity` — mở khi có nhu cầu thật.
7. ~~**M9-PED-AUDIT** — audit chất lượng sư phạm + tham chiếu bên ngoài (PhET
   implicit scaffolding; Mayer coherence)~~. Kết luận: kiến trúc đúng, nhưng
   nhiều cảnh còn *watch-heavy*; **một** affordance kéo-đổi-chỗ dùng cho cả 8
   thuật toán là khiếm khuyết lớn nhất (hệ quả hầu như bằng 0, riêng
   binary_search còn gây hiểu lầm vì phá tiền điều kiện mà không có khung).
8. ~~**M9-S1 — mechanism-aligned interactions (algorithm)**~~ (`548f1fc`). Vá đúng
   khiếm khuyết trên: điểm quyết định theo cơ chế + chính sách what-if 4 mode.
   **Bất biến mới** (`COVERAGE.md §2.6`): *mọi tương tác phải chạm cơ chế ẩn và
   sinh hệ quả tất định; tương tác trang trí không được admit.*
9. ~~**M9-UX1 — Home + lịch sử học cục bộ zero-AI + vệ sinh RULES**~~ (`1f95e92`).
   Nền sản phẩm: vào cửa đơn giản → phiên học → liên tục học không tốn AI;
   RULES.md hết gây nhiễu cho coding agent tương lai.
9b. ~~**M9-UX2 — onboarding trực quan + simulation-first + phạm vi luận văn**~~
   (`08a9a7a`). Preview trực quan cho starter; sân khấu là tiêu điểm; danh mục
   công khai khoanh Tin học THPT (nguyên tắc COVERAGE §2.7); gỡ thẻ Ứng dụng.
9c. ~~**M9-UX3 — Home gọn + preview đúng cơ chế**~~ (nhánh `m9-ux3-home-preview`).
   Composer pill; card hàng ngang; gom nhóm khi mở rộng. Sửa **2 tranh dạy sai cơ
   chế** và đóng lỗ hổng "luật phạm vi chỉ áp ở Home" (`InputPanel` vẫn rò fixture).
   Bất biến mới khoá bằng test: **một tranh = một cơ chế = một bài**.
10. **Kế tiếp — M9-S2: binary "dựng số N"** (`COVERAGE.md §6`, M9-PED-AUDIT §8):
   `binary.decimal_to_binary` là cảnh thao-tác-trực-tiếp tốt nhất nhưng học sinh
   **không thể sai** (không có đích) → thêm thử thách tất định dùng LẠI
   `PredictionCapability`, ground truth `bitsOf`/`decimalOf`/`placeValues` có sẵn.
   Sau đó M9-S3 (packet routing: học sinh tự dẫn đường, engine so chi phí với BFS).
11. Sau M9: `table/grid` (mở khoá CSDL) · practice_activity đầy đủ (cần duyệt
    riêng — vẫn **PARTIAL / CHƯA IMPLEMENT**).
12. Không có M7.15.
