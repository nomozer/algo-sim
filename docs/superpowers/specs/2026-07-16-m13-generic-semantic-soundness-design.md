# M13 — Generic Semantic Soundness & Algorithmic Right-or-Refuse (design)

Ngày: 2026-07-16 · Trạng thái: **CHỜ DUYỆT** — chưa viết production code.
Đề tài: “Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích bài toán
bằng ngôn ngữ tự nhiên hỗ trợ dạy học môn Tin học THPT.”

> **STOP feature expansion.** M13 là correctness blocker: chặn README rewrite
> và mọi milestone năng lực mới cho tới khi hoàn tất. Sau M13 chỉ cập nhật
> README nếu tuyên bố right-or-refuse đã thật sự đúng.

## 0. Sự cố kích hoạt

Một đề nghị mô phỏng **Dijkstra** được định tuyến vào `generic.rule_scene` và
render thành: tam giác 3 nút, 2 đường đi khai báo sẵn, 2 ô `weighted_sum` hiển
thị **0** ở bước cuối 10/10, một vật di chuyển theo path định trước, tiêu đề
LLM đặt “Mô phỏng so sánh đường đi trong thuật toán Dijkstra”. Cảnh chạy trơn
tru, báo “Hoàn tất!” — một mô phỏng **hỏng-mà-tự-tin**, vi phạm trực tiếp
`docs/CORRECTNESS.md` (canonical simulation: đúng-hoặc-từ-chối).

Ảnh chụp phơi ra **hai lỗi độc lập**, cả hai đều là blocker:

1. **Numeric false positive** — spec `weighted_sum` trên toán hạng không mang
   giá trị số (`edge_AB`, `edge_BC`, `edge_AC`) được cả hai tầng validator chấp
   nhận, và cả hai runtime lặng lẽ tính ra 0.
2. **Algorithmic routing false positive** — một yêu cầu *thuật toán tính kết
   quả* (shortest path có trọng số) được chấp nhận vào generic dưới dạng cảnh
   dựng-cho-giống, không có cơ chế thuật toán nào tồn tại.

Hai lỗi gộp chung một milestone vì tuyên bố right-or-refuse của README chỉ đúng
khi **cả hai** được sửa.

## 1. Mission

Generic composition chỉ được dùng khi các primitive khai báo hiện có **biểu
diễn trung thực** cơ chế được yêu cầu. Một cảnh đồ thị trông-hợp-lý không bao
giờ được chấp nhận như một mô phỏng thuật toán thực thi được. Toán hạng số
không có nguồn giá trị không bao giờ được lặng lẽ thành 0.

## 2. Bằng chứng source đã xác nhận (đọc tận dòng, 2026-07-16)

Ghi cả **symbol** lẫn số dòng — số dòng sẽ trôi, symbol là neo chính.

| # | Symbol | Vị trí (hiện tại) | Hành vi xác nhận |
|---|---|---|---|
| E1 | `initialBase` (TS) | `frontend/src/simulations/domains/generic/model.ts:176-183` | Chỉ nạp object **có trường `value`** và không phải rule target vào bảng giá trị. Cạnh (`edge_*`) không có `value` → không bao giờ vào bảng. |
| E2 | `evalRule` (TS) | `model.ts:186` | `(rule.inputs ?? []).map((id) => values[id] ?? 0)` — toán hạng thiếu **lặng lẽ thành 0**. |
| E3 | `evalRule` (TS) | `model.ts:204` | Weight thiếu cũng fallback `?? 0`. |
| E4 | `_eval_rule` (Python mirror) | `backend/app/simulation/generic_engine.py:25,39` | `values.get(i, 0)` + weight fallback 0 — **parity chính-xác-đến-cả-bug** với TS. |
| E5 | `objLabel` (TS) | `model.ts:226-229` | `o?.label ?? id` — LLM bỏ trống `label` → id thô (`node_A`, `calc_path_ABC`) rò thẳng ra narration/UI học sinh. |
| E6 | validator hai tầng | `backend/app/simulation/dsl/validator.py:330-344` · `frontend/.../generic/validate.ts:303` | `weighted_sum` chỉ kiểm `weights` cùng độ dài `inputs` + là số. **Không kiểm toán hạng có nguồn giá trị số** — tồn tại id là đủ qua cổng. |
| E7 | `run_pipeline` carve-out | `backend/app/ai/pipeline.py:315-343` | Plan tính sau analyze, nhưng **phán quyết gap nằm sau classify và có điều kiện**: bài classify về module chuyên biệt đi tiếp bất kể unsupported roles (vá bug live `sum_if` bị vạ lây). Cổng chỉ thực chặn trên đường generic. |
| E8 | `try_pattern_reuse` | `pipeline.py:277-301` | Pattern adapt xong **chạy đủ 4 cổng** (`run_gates`, dòng 297) rồi mới trả — siết validator ⇒ pattern cũ tự động bị kiểm lại. Fail → fallback compose, không poison store. |
| E9 | `CACHE_VERSION` | `backend/app/main.py:73` (hiện `"9"`), kiểm ở `main.py:117` | Cache exact-match trả envelope **không re-validate**; chỉ đối chiếu `policy_version`. Không bump ⇒ đề Dijkstra cũ được trả thẳng từ cache, **né mọi cổng mới**. |
| E10 | `reopenFromHistory` → `loadEnvelope` | `frontend/src/state/store.ts:247-258` → `store.ts:198-205` | Reopen **đã gọi** `mod.validateConfig(env.config)`; fail → set `analysisError`, không render, không crash, không AI. Máy móc fail-closed đã tồn tại — M13 chỉ cần khoá bằng test. |
| E11 | Gap-gate false positives đã ghi nhận | `pipeline.py:322-337` (carve-out sum_if) · `docs/CURRENT_STATE.md` §5 (M12 flagship: analyze gắn `numeric_threshold` sai, dừng đuổi có chủ đích) | Cổng năng lực hiện hành **đã có** hành vi từ chối nhầm được ghi nhận — siết thêm phải đo cả false positive. |
| E12 | Semantic role của `weighted_sum` | `backend/app/simulation/dsl/manifest.py:62,96` | Manifest đã khai `weighted_sum → {"numeric"}` và mô tả “tổng inputs nhân weights” — nguồn chân lý để **dẫn xuất** chính sách numeric-source, không viết tay. |
| E13 | `ui-hygiene.test.ts` | `frontend/src/` | Guard quét **mã nguồn** — về cấu trúc không thể thấy id do LLM sinh lúc runtime. Ba lần rò trước là hằng số trong source; lần này khác lớp. |

## 3. Workstream A — Numeric Rule Coherence (blocker hạng nhất)

### 3.1 Audit bắt buộc (Phase A, offline)

- Đường resolve từng `input` id của `weighted_sum` ở cả hai runtime (E1–E4).
- Kiểu object nào **thực sự** cung cấp giá trị số theo hợp đồng DSL hiện hành
  (đối chiếu manifest E12; thực nghiệm: `switch` có weight, `value_box` có
  value; `edge`/`node` không).
- Điều gì xảy ra khi input không có giá trị (đã xác nhận: thành 0 im lặng).
- Validator Python/TS có kiểm operand-value coherence không (đã xác nhận: không).
- Ngữ nghĩa runtime backend/frontend có lệch nhau không (đã xác nhận: parity,
  cùng bug — sửa phải giữ parity).

### 3.2 Bất biến bắt buộc

**Mọi toán hạng được một numeric rule chấp nhận phải có nguồn giá trị số được
validate theo hợp đồng DSL hiện hành.** Tồn tại một object id là KHÔNG đủ.

- Không vá theo id literal kiểu `edge_AB`.
- Không giả định cạnh là numeric chỉ vì “cạnh có thể có trọng số về mặt khái
  niệm”. DSL hiện hành **không có** accessor trọng-số-cạnh → spec như vậy bị
  **từ chối**, không phát minh accessor trong M13.

### 3.3 Chính sách numeric-source dẫn xuất từ manifest

- Allowlist “kiểu object nào cung cấp giá trị số” **dẫn xuất từ semantic
  roles/contracts trong manifest** (E12) ở cả hai tầng — không nhân bản
  allowlist viết tay giữa Python và TypeScript (anti-pattern #1,
  `ARCHITECTURE_MAP.md`: enum viết tay từng trôi khỏi manifest và làm Gemini
  fail mọi retry không rõ lý do).

### 3.4 Runtime defense in depth (fail-closed)

- Gỡ ngữ nghĩa của `values[id] ?? 0` / `values.get(i, 0)`: toán hạng
  thiếu/không-numeric phải sinh **typed failure**, không bao giờ thành số 0.
- Weight thiếu không được lặng lẽ thành 0 khi validation kỳ vọng vector weight
  đầy đủ.
- Validator vẫn là ranh giới chính; runtime là lưới sau cùng, fail-closed.
- Hình dạng cụ thể của typed failure (lỗi ở `init` vs `InteractionFeedback` vs
  cấu trúc khác) chốt ở bước writing-plans (câu hỏi mở Q3, §11).

### 3.5 Test parity bắt buộc (backend + frontend, offline)

- toán hạng numeric hợp lệ;
- toán hạng edge/node/không-mang-giá-trị → validator từ chối;
- giá trị thiếu → typed failure, không phải 0;
- weights lệch độ dài;
- chuỗi giá trị dẫn xuất (rule target làm input rule khác) nơi được hỗ trợ;
- evaluation tất định;
- **không còn hành vi undefined-thành-0 im lặng** ở cả hai runtime.

## 4. Workstream B — Algorithmic Computation Gate

### 4.1 Ranh giới khái niệm (tái dùng, không phát minh)

**Không** phân biệt theo hình thức thị giác (“đồ thị”, “timeline”, “nhiều
bước”) — generic hợp pháp vẫn dựng cảnh có timeline (sơ đồ hệ thống M8-PRE S2,
chuỗi boolean M11). Tái dùng ranh giới đã có: biểu diễn cấu trúc/tiến trình ↔
tính kết quả thực thi; `result_mode`; tách “tiến trình diễn biến engine dựng”
khỏi “dựng cảnh từng bước” (đã có trong `classify.md` từ M10-AI-ROUTE).

Câu hỏi quyết định: **kết quả được yêu cầu có buộc phải được TÍNH ra từ dữ
liệu đầu vào qua một cơ chế thuật toán cụ thể không?**

- Có → một deterministic executor hiện hành phải **sở hữu** cơ chế đó.
- Không executor nào phủ → `capability_gap`, kể cả khi primitive generic vẽ
  được cảnh trông-hợp-lý.

### 4.2 Trường hợp Dijkstra

Cơ chế tối thiểu (xác minh trong Phase A): đồ thị có trọng số; nguồn/đích;
khoảng cách tạm; extract-min; nới cạnh (relaxation); tập visited/finalized;
predecessor; kết thúc tất định. Không capability nào trong số này tồn tại →
kết quả đúng là `capability_gap`.

**Cấm xấp xỉ** bằng: candidate path khai báo sẵn; ô `weighted_sum` trên id
cạnh; `reveal_sequence`; `move_along_path`; bước “canonical” do LLM soạn.
**Không** định tuyến Dijkstra sang `network.packet_routing` trừ khi engine đó
thật sự cài Dijkstra có trọng số (hiện tại: BFS — không phải).

### 4.3 Vị trí cổng

Ổn định theo hành vi, không theo vị trí code: *“Sau khi phân tích yêu cầu và
trước khi một cấu hình generic được chấp nhận để thực thi, hệ thống kiểm tra
capability coverage.”* (E7: phán quyết gap hiện nằm sau classify, có điều kiện
— mô tả nào khẳng định “trước classify” là sai với source.) Tầng cài đặt cụ
thể (representation plan / classify contract / semantic validator / tổ hợp)
là câu hỏi mở Q1 (§11), chốt sau audit Phase A.

## 5. False-positive budget

Cổng hiện hành **đã có** từ chối nhầm được ghi nhận (E11). Không tối ưu chỉ
cho việc chặn Dijkstra. Controls khoá — mỗi cái một test/case, báo cáo **cả
hai chiều** (required-gap rejection · supported-case preservation):

| Control | Kỳ vọng |
|---|---|
| M12 scan flagship (“ngày đầu tiên vượt 35°C”) | vẫn `algorithm.scan`, **xanh bất chấp** analyze-role noise đã biết |
| `sum_if` / `count_if` chuyên biệt chính xác | giữ nguyên route chuyên biệt |
| `linear_search` so bằng | giữ nguyên route chuyên biệt |
| M11 nested boolean generic | vẫn xanh |
| Cảnh đồ thị **cấu trúc** hợp pháp (mô tả quan hệ, không đòi tính kết quả) | vẫn generic |
| Packet routing đang hỗ trợ | giữ nguyên route |
| Vòng lặp biến tự do | vẫn `unsupported` |
| Dijkstra | `unsupported` / `capability_gap` với giải thích trung thực |

## 6. Two-layer regression

### 6.1 Lớp 1 — Offline deterministic fixture (khoá cổng)

Khôi phục artifact thật của phiên Dijkstra nếu còn: `simulation_cache`
(Postgres volume `pgdata` hoặc `backend/*.db` SQLite — chỉ analysis **thành
công** mới được cache, ca này thành công) và/hoặc localStorage lịch sử
(envelope whitelist theo bất biến #17). Đóng băng: analysis · representation
requirements · classification · spec sinh ra · envelope đã validate.

Không khôi phục được artifact chính xác → dựng **reconstructed fixture** từ
bằng chứng ảnh chụp/spec, ghi chú rõ là tái dựng.

Fixture phải chứng minh: cổng/validator tất định **không còn chấp nhận** thất
bại cũ — chạy trong CI, 0 API call.

### 6.2 Lớp 2 — Opt-in LLM evaluation (đo LLM, không thay lớp 1)

Case eval tiếng Việt: *“Mô phỏng thuật toán Dijkstra tìm đường ngắn nhất từ A
đến C trên đồ thị có trọng số.”* — kỳ vọng `capability_gap` với năng lực hiện
hành. Case phải qua `check_admission` (`datasets/__init__.py`, enforced bởi
`test_datasets.py`): `learning_objective`, `pedagogical_rationale` **nêu đích
danh cơ chế ẩn** và giải thích **vì sao capability_gap tốt hơn một
pseudo-simulation**, `capability_family`, `complexity`, `result_mode`,
`curriculum_area` hợp lệ.

Live AI chỉ khi prompt/classifier đổi hành vi: 1–3 case logic có mục tiêu,
báo cáo chính xác số case logic · HTTP request · retry · 429.

## 7. Cache invalidation & pattern reuse

- **Bump `CACHE_VERSION`** (`"9"` → `"10"`, `main.py:73`) khi semantic
  validation thay đổi — cache exact-match không re-validate (E9); không bump
  thì envelope theo luật cũ được trả lại nguyên vẹn và M13 vô nghĩa với đề
  trùng.
- Test chứng minh: envelope hợp lệ-theo-luật-cũ **không** được trả từ cache
  sau bump.
- Audit `simulation_patterns`: E8 xác nhận đường adapt đã chạy `run_gates` —
  yêu cầu còn lại là **chứng minh** `run_gates` bao gồm check coherence mới
  (check phải nằm ở tầng validator mà `run_gates` gọi) + một test khoá việc
  pattern cũ mang shape bị cấm sẽ fail và fallback compose.

## 8. Legacy history (localStorage)

E10 xác nhận máy móc đã có: reopen → `validateConfig` → fail-closed, 0 AI.
Yêu cầu M13:

- Test chứng minh artifact Dijkstra cũ khi reopen đi vào nhánh fail: **không
  crash, không render cảnh sai, không bypass validator, không gọi AI**.
- Thông báo lỗi learner-facing trung thực (không phải chuỗi kĩ thuật thô).
- Không “cho qua để khỏi vỡ lịch sử” — từ chối là hành vi đúng.

## 9. Workstream C — Runtime Label Hygiene (sau A và B)

Guard hiện hành quét mã nguồn, không thấy id sinh lúc runtime (E13). Chính
sách display-name learner-facing:

- id nội bộ là tham chiếu nội bộ;
- renderer dùng display label đã validate;
- label thiếu → fallback tất định thân thiện học sinh (điểm sửa: `objLabel`,
  E5 — không dùng id thô làm fallback);
- id thô (`node_A`, `edge_AB`, `calc_path_ABC`) không được là nhãn chính trên
  sân khấu học sinh;
- inspector debug/nội bộ được giữ id nơi phù hợp.

Không redesign UI. A và B xong trước.

## 10. Curriculum scope (quyết định tài liệu hóa, không quyết định theo độ nổi tiếng)

Đối chiếu `docs/COVERAGE.md` + phạm vi Tin học THPT được duyệt (bằng chứng ban
đầu: COVERAGE.md không nhắc Dijkstra; chỉ BFS làm oracle packet routing):

- **A. Ngoài phạm vi công khai của đề tài** → `capability_gap` là câu trả lời
  đúng **dài hạn**; `graph.shortest_path` không được đưa vào roadmap đề tài.
- **B. Trong phạm vi được duyệt** → `capability_gap` là tạm thời;
  `graph.shortest_path` được ghi là future work (tài liệu, không code).

Không cài `graph.shortest_path` trong M13, bất kể kết luận A/B.

## 11. Câu hỏi kiến trúc chưa chốt (chốt ở writing-plans, sau audit Phase A)

- **Q1 — Vị trí cổng B:** representation plan (mở rộng role) · classify
  contract · semantic validator trên spec generic · tổ hợp nhiều tầng? Ràng
  buộc: không phá carve-out chuyên biệt (E7), không keyword-patch.
- **Q2 — Tín hiệu “kết quả phải được tính”:** analyze output hiện hành đủ
  chưa, hay cần trường mới (⇒ đổi prompt ⇒ cần live smoke có mục tiêu)?
- **Q3 — Hình dạng typed failure runtime** (§3.4): lỗi validate ở `init` vs
  feedback có cấu trúc — chọn phương án không phá ba tầng config→state→render.
- **Q4 — Mức granularity của numeric-source trong manifest:** theo object type
  hay theo semantic role — chọn hướng ít làm phình bề mặt manifest nhất.

## 12. COMPLETE criteria

M13 chỉ COMPLETE khi **tất cả**:

- [ ] toán hạng numeric không hợp lệ không thể lặng lẽ evaluate thành 0;
- [ ] ngữ nghĩa numeric backend/frontend nhất quán (parity test);
- [ ] runtime không thể chuyển toán hạng/weight thiếu thành 0 im lặng;
- [ ] artifact Dijkstra cũ bị từ chối **offline** (fixture CI);
- [ ] Dijkstra không còn sinh cảnh pseudo-algorithm generic;
- [ ] yêu cầu tính-kết-quả không có executor → `capability_gap`;
- [ ] cảnh generic cấu trúc/tiến trình hợp lệ vẫn được hỗ trợ;
- [ ] M11 boolean xanh; M12 scan flagship xanh (bất chấp analyze-role noise);
- [ ] sum/count/search chuyên biệt + packet routing giữ nguyên route;
- [ ] vòng lặp biến tự do vẫn unsupported;
- [ ] `CACHE_VERSION` bumped; envelope Dijkstra cache cũ không né được cổng mới;
- [ ] pattern reuse re-validate theo luật hiện hành (test khoá);
- [ ] artifact history cũ fail có nhân phẩm (test khoá; 0 AI);
- [ ] offline fixture và live evaluation tách bạch rõ;
- [ ] id thô runtime không là nhãn chính learner-facing;
- [ ] trạng thái curriculum của Dijkstra được tài liệu hóa (A hoặc B, §10);
- [ ] không thêm module Dijkstra, không universal graph DSL, không redesign UI;
- [ ] full tests + build pass.

## 13. Ngoài phạm vi M13

Module Dijkstra / `graph.shortest_path` (kể cả khi §10 ra kết luận B) ·
universal graph DSL · accessor trọng-số-cạnh · redesign UI · README rewrite
(chỉ sau M13, và chỉ khi right-or-refuse đã đúng) · mọi mục trong scope-freeze
§5b `docs/CURRENT_STATE.md`.

## 14. Báo cáo cuối bắt buộc

Root cause (cả hai lỗi) · routing trước/sau · cổng semantic đã thêm ·
regression cases hai lớp · files changed · tests/build · live usage chính xác
(case logic/HTTP/retry/429) · limitations · phán quyết curriculum §10 · có/không
biện minh cho `graph.shortest_path` tương lai (tài liệu, không tự động bắt đầu).
