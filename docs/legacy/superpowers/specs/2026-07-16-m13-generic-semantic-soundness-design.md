# M13 — Generic Semantic Soundness & Algorithmic Right-or-Refuse (design)

Ngày: 2026-07-16 · Trạng thái: **ĐÃ DUYỆT CÓ ĐIỀU KIỆN** (bản amend v2 —
ba trạng thái numeric source, Q1–Q4 chốt, matrix audit bắt buộc) — chưa viết
production code cho tới khi writing-plan được review.
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
| E14 | `PRIMITIVE_ROLES` | `backend/app/simulation/dsl/manifest.py:46-70` | Manifest **đã khai** vai trò từng primitive: `switch` {interactive, logical, **numeric**} · `lamp` {logical, **numeric**} · `value_box` {**numeric**} · `node`/`edge` {relational} · rules `boolean` {logical}, `weighted_sum` {numeric} · interactions `toggle`/`drag` · processes `reveal_sequence`/`move_along_path`. Nguồn chân lý sẵn có cho chính sách numeric-provider VÀ phôi của semantic matrix (§9b). |
| E15 | `known_gap_roles()` — `arbitrary_algorithm`, `numeric_threshold`, `geometric_*`, `continuous_motion` | `manifest.py:30-44` | Từ vựng known-gap **đã tồn tại**, gồm chính `arbitrary_algorithm` ("thuật toán tự do không có engine tương ứng"). Cổng B xây trên từ vựng này, không dựng song song. Ca Dijkstra lọt = role không được gắn/không tới gate trên đường generic — audit Phase A xác định điểm đứt. |
| E16 | `evalRule`/`_eval_rule` nhánh boolean | `model.ts:186-188` · `generic_engine.py:25-27` | **Cùng dòng `?? 0` phục vụ cả boolean**: input boolean thiếu lặng lẽ thành 0 = false. Lớp bug rộng hơn weighted_sum — căn cứ trực tiếp của matrix audit §9b. |
| E17 | Seed rule targets = 0 trước vòng lặp điểm bất động | `model.ts:210` (`values[t] = 0`) · `generic_engine.py:46` (`setdefault(t, 0)`) | Trạng thái "chưa resolve" và "đã tính ra 0" hiện bị **xóa nhòa thành một** — lý do bắt buộc mô hình ba trạng thái (§3.2). |

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

### 3.2 Bất biến bắt buộc — mô hình BA TRẠNG THÁI numeric source

**Mọi toán hạng được một numeric rule chấp nhận phải có nguồn giá trị số được
validate theo hợp đồng DSL hiện hành.** Tồn tại một object id là KHÔNG đủ.
Phân loại nguồn thành ĐÚNG BA trạng thái:

1. **`INVALID_SOURCE`** — id không có hợp đồng cung cấp giá trị (vd `edge`,
   `node`: vai trò chỉ `relational`, E14) → **validator reject** ngay tầng
   validate, spec không tới được engine.
2. **`UNRESOLVED_DERIVED_SOURCE`** — id là **target của một numeric rule hợp
   lệ** nhưng provider chưa được evaluate do thứ tự khai báo → **defer**:
   không biến thành 0, không fail ngay. Bảo tồn order-independence và chuỗi
   rule hợp lệ (fixed-point hiện hành cho phép rule khai báo trước provider —
   fail-closed ngây thơ sẽ phá chính M11).
3. **`RESOLVED_NUMERIC_SOURCE`** — có giá trị hợp lệ → evaluate.

Sau **bounded evaluation** (giới hạn vòng lặp điểm bất động hiện hành),
unresolved còn sót lại mới sinh **typed execution failure**. Hệ quả cài đặt
(E17): resolution status phải được theo dõi TÁCH khỏi value — hiện hai runtime
seed mọi rule target = 0 trước vòng lặp, xóa nhòa "chưa resolve" với "bằng 0".

- Không vá theo id literal kiểu `edge_AB`.
- Không giả định cạnh là numeric chỉ vì “cạnh có thể có trọng số về mặt khái
  niệm”. DSL hiện hành **không có** accessor trọng-số-cạnh → spec như vậy bị
  **từ chối**, không phát minh accessor trong M13.
- Không giả định `switch` là numeric mà không kiểm chứng: manifest khai
  `switch` {numeric} (E14) và bài đổi nhị phân dùng switch-có-weight nuôi
  `weighted_sum` — nhưng plan phải **xác nhận bằng fixture/hợp đồng runtime
  hiện hành** trước khi khóa vào allowlist dẫn xuất.

### 3.3 Chính sách numeric-source dẫn xuất từ manifest

- Allowlist “kiểu object nào cung cấp giá trị số” **dẫn xuất từ semantic
  roles/contracts trong manifest** (E12) ở cả hai tầng — không nhân bản
  allowlist viết tay giữa Python và TypeScript (anti-pattern #1,
  `ARCHITECTURE_MAP.md`: enum viết tay từng trôi khỏi manifest và làm Gemini
  fail mọi retry không rõ lý do).

### 3.4 Runtime defense in depth (fail-closed) — Q3 ĐÃ CHỐT

- Gỡ ngữ nghĩa của `values[id] ?? 0` / `values.get(i, 0)`: toán hạng
  thiếu/không-numeric phải sinh **typed failure**, không bao giờ thành số 0 —
  theo mô hình ba trạng thái §3.2 (unresolved được defer trong bound, chỉ fail
  khi hết bound).
- Weight thiếu không được lặng lẽ thành 0 khi validation kỳ vọng vector weight
  đầy đủ.
- Validator vẫn là ranh giới chính; runtime là lưới sau cùng, fail-closed.
- **Hình dạng typed failure (Q3 resolved):** `GenericExecutionError` có kiểu,
  tại **ranh giới executor/module** — KHÔNG dùng `InteractionFeedback`, KHÔNG
  nhét vào canonical state. Mã lỗi tối thiểu: `invalid_numeric_source` ·
  `missing_weight` · `unresolved_dependency_after_bound` ·
  `non_finite_numeric_value` (Infinity/NaN không bao giờ tới renderer).

### 3.5 Test parity bắt buộc (backend + frontend, offline)

- toán hạng numeric hợp lệ;
- toán hạng edge/node/không-mang-giá-trị → validator từ chối
  (`INVALID_SOURCE`);
- giá trị thiếu → typed failure, không phải 0;
- weights lệch độ dài; weights thiếu → fail closed;
- chuỗi giá trị dẫn xuất hợp lệ (rule target làm input rule khác);
- **thứ tự khai báo đảo ngược** — chuỗi hợp lệ vẫn hội tụ
  (`UNRESOLVED_DERIVED_SOURCE` defer, không fail, không thành 0);
- unresolved còn sót sau bound → `unresolved_dependency_after_bound`;
- nguồn boolean 0/1 nuôi numeric rule: CHỈ chấp nhận nếu fixture/hợp đồng
  hiện hành chứng minh được hỗ trợ — không suy diễn;
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
— mô tả nào khẳng định “trước classify” là sai với source.) Kiến trúc cổng đã
chốt (Q1, §11): **hai tầng** — policy gate trên đường generic sau classify +
semantic validator trên spec generic đã sinh; giữ carve-out chuyên biệt.

## 5. False-positive budget

Cổng hiện hành **đã có** từ chối nhầm được ghi nhận (E11). Không tối ưu chỉ
cho việc chặn Dijkstra. Controls khoá — mỗi cái một test/case, báo cáo **cả
hai chiều** (required-gap rejection · supported-case preservation):

Hai lớp, tách bạch:

- **Offline (CI, 0 API call):** MỌI spec/envelope/fixture/sample xanh sẵn có
  của M11 + M12 + sample offline (`data/sim-samples.ts`, bài đổi nhị phân
  switch-weight → `weighted_sum`) phải qua validator/cổng MỚI mà vẫn xanh —
  trọn bộ, không lấy một case đại diện.
- **Live (opt-in, chỉ khi prompt/classifier đổi hành vi):** trọn suite
  `m11_compose` (5 case) + `m12_scan` (4 case) + các control routing dưới đây,
  trong ngân sách có mục tiêu.

| Control | Kỳ vọng |
|---|---|
| M12 scan flagship (“ngày đầu tiên vượt 35°C”) | vẫn `algorithm.scan`, **xanh bất chấp** analyze-role noise đã biết |
| Trọn suite `m12_scan` còn lại (count/linear đối chứng, loop-gap) | giữ nguyên phán quyết từng case |
| `sum_if` / `count_if` chuyên biệt chính xác | giữ nguyên route chuyên biệt |
| `linear_search` so bằng | giữ nguyên route chuyên biệt |
| Trọn suite `m11_compose` (canonical, NOT, access, paraphrase, loop-gap) | giữ nguyên phán quyết từng case |
| **`weighted_sum` HỢP LỆ** — cảnh frozen hiện hành (nguồn numeric thật; chuỗi dẫn xuất hợp lệ; thứ tự khai báo đảo) | vẫn xanh — cổng mới không giết use-case hợp pháp |
| `weighted_sum` nguồn edge/node | validator từ chối |
| `weighted_sum` thiếu weights | fail closed |
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

**Dataset placement trung thực:** nếu §10 kết luận Dijkstra NGOÀI phạm vi
curriculum công khai được duyệt, **không gán `curriculum_area` giả** chỉ để
qua admission. Dùng hợp đồng dataset unsupported/boundary sẵn có, hoặc điều
chỉnh admission **nhỏ nhất-trung thực nhất** nếu hợp đồng hiện hành không chứa
nổi case này. Kết luận mặc định hiện tại: **Dijkstra ngoài phạm vi công khai
của đề tài**, trừ khi audit tìm được anchor được duyệt trong COVERAGE.

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

## 9b. GENERIC PRIMITIVE SEMANTIC MATRIX AUDIT (bắt buộc, trong implementation planning)

Dijkstra và `weighted_sum` là **ví dụ kích hoạt, không phải toàn bộ phạm vi**
của bản vá đúng đắn. E16 chứng minh cùng lớp bug đã chạm nhánh boolean (input
thiếu lặng lẽ = false). Kiểm kê **mọi primitive generic đang thực thi được**
— nguồn chân lý: `PRIMITIVE_ROLES` + `MANIFEST` (E14). Bề mặt hiện hành:

- object: `switch` · `lamp` · `value_box` · `node` · `edge` · `moving_entity`
  · `label` · `container` · `group` · `heading` · `paragraph` · `text`
- rule: `boolean` · `weighted_sum`
- interaction: `toggle` · `drag`
- process: `reveal_sequence` · `move_along_path`

Danh mục audit tối thiểu theo yêu cầu duyệt: numeric rules · boolean rules ·
comparison rules · chuỗi giá trị dẫn xuất · object đồ thị cấu trúc · path và
process di chuyển · process reveal/tiến trình · tương tác người học · rule
target và dependency. **Ghi thật, không bịa**: mục nào không tồn tại trong
manifest (vd `RULE_TYPES` hiện chỉ có `boolean`/`weighted_sum` — KHÔNG có
comparison rule) thì matrix ghi *vắng mặt*, không phát minh primitive mới.

Với TỪNG primitive, matrix ghi:

| Trường | Nội dung |
|---|---|
| input/provider roles chấp nhận | dẫn từ manifest, không viết tay |
| output role sinh ra | — |
| trường bắt buộc | — |
| input thiếu là gì | `invalid` / `unresolved` / `optional` — phân loại tường minh |
| hành vi dependency | thứ tự khai báo, chuỗi, chu trình |
| bound tất định | giới hạn evaluation/step |
| hành vi fail runtime | typed error nào, khi nào |
| bản chất biểu diễn | cấu trúc · tương tác · dựng tiến trình · **tính toán thực thi** |

Lớp bug matrix phải bắt được (ngoài weighted_sum):

- tham chiếu tồn tại nhưng SAI kiểu giá trị ngữ nghĩa;
- giá trị thiếu lặng lẽ nhận default;
- tham số thiếu lặng lẽ đổi nghĩa;
- unresolved dependency bị lẫn với 0/false;
- object cấu trúc bị tiêu thụ như giá trị đã tính;
- kết quả numeric non-finite tới được renderer;
- chu trình / chuỗi không hội tụ mà trông như thành công;
- process thị giác bị coi là kết quả thuật toán.

Ràng buộc: **không mở rộng DSL, không cài primitive mới.** Manifest là nguồn
chân lý; nếu manifest chưa diễn đạt được hợp đồng provider/consumer cần thiết
→ thêm **metadata khai báo nhỏ nhất đủ dùng** và khóa parity backend/frontend
bằng test.

**Adversarial offline fixtures** cho các mismatch ngữ nghĩa đại diện (không
chỉ fixture Dijkstra). Controls bắt buộc: numeric rule hợp lệ · object cấu
trúc làm input numeric (reject) · boolean rule hợp lệ · object numeric làm
input boolean (phân loại theo hợp đồng, không im lặng) · comparison hợp lệ /
operand thiếu (**chỉ khi primitive tồn tại** — hiện: vắng mặt, ghi nhận) ·
chuỗi dẫn xuất hợp lệ · thứ tự khai báo đảo · unresolved sau bound · chu
trình dependency · process thiếu target bắt buộc · cảnh đồ thị cấu trúc hợp
lệ · yêu cầu tính toán thuật toán không có executor.

**Claim cuối cùng của implementation bắt buộc là:**

> “Generic specs are accepted according to manifest-derived semantic
> contracts; unsupported computational mechanisms are rejected.”

**KHÔNG được là:** ~~“Dijkstra is blocked.”~~ Không keyword-fix cho Dijkstra.

## 10. Curriculum scope (quyết định tài liệu hóa, không quyết định theo độ nổi tiếng)

Đối chiếu `docs/COVERAGE.md` + phạm vi Tin học THPT được duyệt (bằng chứng ban
đầu: COVERAGE.md không nhắc Dijkstra; chỉ BFS làm oracle packet routing):

- **A. Ngoài phạm vi công khai của đề tài** → `capability_gap` là câu trả lời
  đúng **dài hạn**; `graph.shortest_path` không được đưa vào roadmap đề tài.
- **B. Trong phạm vi được duyệt** → `capability_gap` là tạm thời;
  `graph.shortest_path` được ghi là future work (tài liệu, không code).

Không cài `graph.shortest_path` trong M13, bất kể kết luận A/B.

## 11. Câu hỏi kiến trúc — ĐÃ CHỐT (duyệt 2026-07-16)

- **Q1 — Vị trí cổng B (RESOLVED): HAI TẦNG.** (a) computation-obligation
  policy gate trên **đường generic, sau classify và trước khi generic được
  chấp nhận thực thi**; (b) semantic validator trên spec generic đã sinh.
  Giữ nguyên carve-out chuyên biệt (E7). Không keyword-patch. Xây trên từ
  vựng known-gap sẵn có (`arbitrary_algorithm`, E15), không dựng song song.
- **Q2 — Tín hiệu “kết quả phải được tính” (RESOLVED): ưu tiên DẪN XUẤT tất
  định** từ `result_mode`, representation requirements và capability
  contracts sẵn có. **Lưu ý trung thực từ audit:** `result_mode` hiện là
  metadata phía eval dataset (`EvalItem`), CHƯA chảy trong pipeline runtime —
  nếu audit chứng minh dữ liệu hiện hành không đủ, thêm **một trường enum
  hẹp** duy nhất; đổi prompt/schema ⇒ bắt buộc live smoke có mục tiêu.
- **Q3 — Typed failure runtime (RESOLVED):** `GenericExecutionError` có kiểu
  tại ranh giới executor/module — không `InteractionFeedback`, không canonical
  state. Mã lỗi: `invalid_numeric_source` · `missing_weight` ·
  `unresolved_dependency_after_bound` · `non_finite_numeric_value` (§3.4).
- **Q4 — Granularity numeric-source (RESOLVED): hợp đồng semantic
  value-provider DẪN XUẤT TỪ MANIFEST** (E14), không phải allowlist object
  type đơn giản. Hỗ trợ CẢ giá trị khởi tạo của object LẪN numeric derived
  rule target (ba trạng thái §3.2). Khóa bằng contract-lock test hai phía
  backend/frontend.

## 12. COMPLETE criteria

M13 chỉ COMPLETE khi **tất cả**:

- [ ] toán hạng numeric không hợp lệ không thể lặng lẽ evaluate thành 0;
- [ ] mô hình ba trạng thái §3.2 cài đúng: `INVALID_SOURCE` reject ở
      validator · `UNRESOLVED_DERIVED_SOURCE` defer trong bound (chuỗi hợp lệ
      + thứ tự đảo vẫn xanh) · unresolved sau bound → typed failure;
- [ ] ngữ nghĩa numeric backend/frontend nhất quán (parity test);
- [ ] runtime không thể chuyển toán hạng/weight thiếu thành 0 im lặng;
- [ ] matrix audit §9b hoàn tất cho MỌI primitive hiện hành + adversarial
      fixtures đại diện cho từng lớp mismatch (không chỉ Dijkstra);
- [ ] cảnh `weighted_sum` hợp lệ hiện hành (frozen) vẫn xanh sau siết;
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
