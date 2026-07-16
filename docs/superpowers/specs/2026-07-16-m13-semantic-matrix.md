# M13 — Generic Primitive Semantic Matrix Audit (Task 1, docs-only)

Ngày: 2026-07-16 · Nguồn: `docs/superpowers/specs/2026-07-16-m13-generic-semantic-soundness-design.md`
§2 (E1–E17) + §9b · Plan: `docs/superpowers/plans/2026-07-16-m13-generic-semantic-soundness.md`
(Task 2–11, đọc để lấy tên RED test khi gán `TASK-N`).

**Phương pháp:** mọi hàng dưới đây được đối chiếu TRỰC TIẾP với source hiện tại
(không tin số dòng của spec — spec tự ghi "số dòng sẽ trôi, symbol là neo").
Số dòng ghi ở đây là số dòng ĐÃ ĐỌC THẬT ngày 2026-07-16, có thể trôi tiếp — khi
đó dùng symbol để định vị lại. File đã đọc toàn văn:

- `backend/app/simulation/dsl/manifest.py`
- `backend/app/simulation/dsl/validator.py`
- `backend/app/simulation/generic_engine.py`
- `backend/app/simulation/semantic.py`
- `backend/app/simulation/catalog.py` (khối schema `_GENERIC_SCHEMA`, dòng ~366–420)
- `frontend/src/simulations/domains/generic/model.ts`
- `frontend/src/simulations/domains/generic/validate.ts`
- `frontend/src/simulations/domains/generic/index.ts`
- `frontend/src/data/sim-samples.ts` (mẫu `GENERIC_BINARY_SPEC`, `GENERIC_PACKET_SPEC`)
- `backend/tests/test_dsl.py`, `frontend/src/simulations/domains/generic/generic.test.ts`
  (để xác nhận EXISTING có test thật, không suy đoán)

**Kết luận luật dừng (đọc trước khi đọc phần còn lại):** sau khi audit toàn bộ
19 hàng, **0 hàng STOP-UNRESOLVED**. Mọi lỗ ngữ nghĩa xác nhận được đều đã có
TASK-N xử lý trong plan hiện hành, hoặc là hành vi ĐANG ĐÚNG (EXISTING, có
test), hoặc là vắng-mặt-có-chủ-ý (OUT-OF-SCOPE, có rationale — không phải né
tránh). Chi tiết §7. Vì vậy: **không dừng, Task 2 được phép tiếp tục.**

---

## 0. Bảng tổng quan (scan nhanh)

| # | Primitive | Loại | Vai trò cung cấp (provider, khi làm input) | Vai trò output hợp lệ (khi làm target) | ENFORCEMENT DISPOSITION |
|---|---|---|---|---|---|
| 1 | `switch` | object | interactive, logical, numeric | logical, numeric | TASK-3/4/5/6 |
| 2 | `lamp` | object | logical, numeric | logical, numeric | TASK-3/4/5/6 |
| 3 | `value_box` | object | numeric | numeric | TASK-3/4/5/6 |
| 4 | `node` | object | *(không — chỉ relational)* | *(không)* | TASK-3/4/5/6 |
| 5 | `edge` | object | *(không — chỉ relational)* | *(không)* | TASK-3/4/5/6 (fixture khoá: TASK-7) |
| 6 | `moving_entity` | object | *(không — chỉ movement)* | *(không)* | TASK-3/4/5/6 |
| 7 | `label` | object | *(không — chỉ textual)* | *(không)* | TASK-3/4/5/6 + TASK-11 (display) |
| 8 | `container` | object | *(không — chỉ structural)* | *(không)* | TASK-3/4/5/6 |
| 9 | `group` | object | *(không — chỉ structural)* | *(không)* | TASK-3/4/5/6 |
| 10 | `heading` | object | *(không — chỉ textual)* | *(không)* | TASK-3/4/5/6 |
| 11 | `paragraph` | object | *(không — chỉ textual)* | *(không)* | TASK-3/4/5/6 |
| 12 | `text` | object | *(không — chỉ textual)* | *(không)* | TASK-3/4/5/6 |
| 13 | `boolean` | rule | cần input role `logical` | sinh `logical` | TASK-3/4/5/6 (dependency/cycle: EXISTING) |
| 14 | `weighted_sum` | rule | cần input role `numeric` | sinh `numeric` | TASK-3/4/5/6 (numeric coherence) + TASK-9 (chống lạm dụng làm thuật toán giả) + TASK-7/10 (khoá case Dijkstra) |
| — | *comparison rule* | rule | **VẮNG MẶT** | **VẮNG MẶT** | OUT-OF-SCOPE |
| 15 | `toggle` | interaction | N/A (thao tác base value, không sinh giá trị) | N/A | EXISTING |
| 16 | `drag` | interaction | N/A (thao tác position) | N/A | EXISTING |
| 17 | `reveal_sequence` | process | N/A (visibility, không sinh giá trị) | N/A | EXISTING (cấu trúc) + TASK-9 (lạm dụng làm "diễn" thuật toán) |
| 18 | `move_along_path` | process | N/A (entityPos, không sinh giá trị) | N/A | EXISTING (cấu trúc) + TASK-3/4/5/6 (nếu bị dùng làm rule input/target) + TASK-9 (lạm dụng — ĐÂY LÀ CƠ CHẾ CHÍNH của bug Dijkstra) + TASK-7 |

**Tổng:** 19 hàng dữ liệu (12 object + 2 rule + 1 rule-vắng-mặt + 2 interaction +
2 process). Disposition: **0 STOP-UNRESOLVED · 17 hàng có TASK-N (một số kèm
EXISTING cho phần con đã đúng) · 2 hàng thuần EXISTING (toggle, drag) · 1 hàng
OUT-OF-SCOPE (comparison rule)**.

---

## 1. Bằng chứng bổ sung (F1–F5) — vượt ngoài E1–E17 của spec nguồn

Spec nguồn đã có E1–E17. Audit Task 1 xác nhận thêm các điểm sau (đọc thật,
chưa từng ghi trong spec §2):

**F1 — Rule TARGET không được kiểm role phù hợp (ràng buộc 2 của Task 3, CHƯA
CÀI tại thời điểm audit).** `validator.py` vòng dựng `rules` (dòng 325–344)
chỉ kiểm `r.get("target") not in ids` (dòng 328–329) — không kiểm type/role
của object đó. `validate.ts` song song, dòng 287–289. Hệ quả xác nhận bằng đọc
code: một `weighted_sum` CÓ THỂ ghi (target) vào `node`/`edge`/`label`/
`container`… (chỉ có role `relational`/`textual`/`structural`, không có
`numeric`) mà validator hiện tại không từ chối gì cả — cấu trúc hợp lệ, ngữ
nghĩa sai. Plan Task 3 Step 3 đã thiết kế đúng ràng buộc 2 để đóng lỗ này
(`out_role not in PRIMITIVE_ROLES.get(target_obj["type"], set())`), có RED
test `test_rule_output_ghi_vao_target_sai_role_bi_tu_choi`.

**F2 — Rule INPUT không được kiểm role theo object type (tổng quát hoá E6/E16
cho MỌI object type, không riêng `edge`).** `validator.py` dòng 330–333
(`for inp in inputs: if inp not in ids: return None, …`) chỉ kiểm TỒN TẠI,
không đối chiếu `PRIMITIVE_ROLES[obj.type]` với role rule cần. `validate.ts`
dòng 290–293 song song. Điều này có nghĩa bug lớp E6 (Dijkstra: input là
`edge`) chỉ là MỘT TRƯỜNG HỢP của một lỗ rộng hơn: `node`, `moving_entity`,
`label`, `container`, `group`, `heading`, `paragraph`, `text` đều lọt qua
cổng y hệt nếu chúng tồn tại và (tình cờ) có trường `"value"`.

**F3 — `SpecObject.weight` (trường "weight" cấp OBJECT) là trường CHẾT — khai
báo nhưng không nơi nào đọc.** Khai trong Gemini schema
(`backend/app/simulation/catalog.py:384`, `"weight": {"type": "NUMBER", …}`);
copy vào spec chuẩn hoá ở cả hai validator (`validator.py` dòng 263–265, vòng
`for key in ("x", "y", "value", "weight")`; `validate.ts` dòng 217–219); được
liệt trong `ADD_FIELDS` cho phép patch tăng dần
(`backend/app/simulation/patch.py:40`, `frontend/.../patch.ts:37`). Nhưng
`evalRule` (`model.ts` dòng 185–205) và `_eval_rule` (`generic_engine.py` dòng
24–39) **không đọc `object.weight` ở đâu cả** — trọng số THẬT dùng để tính
`weighted_sum` luôn là `rule.weights[i]` (mảng riêng trên RULE, không phải
trên object). Xác nhận bằng grep: không có site đọc `.weight` ngoài
`rule.weights`/`r.weights` trong toàn bộ `frontend/src/simulations/domains/generic/`.
Mẫu `GENERIC_BINARY_SPEC` (`frontend/src/data/sim-samples.ts` dòng 123–130)
đặt CẢ HAI (`switch.weight` và `rule.weights`) trùng khớp (8/4/2/1) — vô hại vì
trùng, nhưng nếu một spec khác đặt chúng LỆCH NHAU, `object.weight` bị NGÓ LƠ
HOÀN TOÀN mà không có cảnh báo.

**RECLASSIFY (duyệt 2026-07-17) — `UNSUPPORTED_SEMANTIC_FIELD` / TASK-2b, KHÔNG
phải OUT-OF-SCOPE.** Bản audit đầu kết luận "vô hại vì không được đọc" — kết
luận đó **thiếu một site quyết định**: [`manifest.py:321`](../../../backend/app/simulation/dsl/manifest.py)
là **contract text nạp thẳng vào prompt simulate**, nguyên văn *"Đổi nhị phân =
switch bit (**có weight**) + value_box + rule weighted_sum."* Tức hệ thống
**chủ động DẠY LLM viết một field mà chính nó không đọc**, trong khi cùng prompt
đó (`manifest.py:96`) định nghĩa `weighted_sum` = tổng inputs nhân `rule.weights`.
Hai chữ "weight" trong một prompt: một thật, một giả.

Đây **là** silent semantic no-op đúng lớp bug §9b (*"tham số lặng lẽ đổi
nghĩa"*): field được quảng bá trong public schema (`catalog.py:384`), được cả
hai validator chấp nhận + giữ lại (`validator.py:263`, `validate.ts:217`), được
patch allowlist cho sửa (`patch.py:40`, `patch.ts:37`), **và được prompt dạy** —
nhưng không runtime nào đọc. Một LLM đặt `switch.weight = 8` tin rằng mình đã
cấu hình phép đổi nhị phân; giá trị đó không tạo hệ quả nào. Cùng họ với
`weighted_sum` trên id cạnh — thứ M13 sinh ra để diệt.

Xử lí = **GỠ BỎ, không thêm ngữ nghĩa**: không cài trọng-số-cạnh, không thêm
accessor. Chi tiết ở **Task 2b** của plan.

**F4 — `initialBase`/`initial_base` không lọc theo object type, chỉ theo "có
trường `value`" + "không phải rule target".** `model.ts` dòng 176–183:
`if (o.value !== undefined && !targets.has(o.id)) base[o.id] = o.value;`;
`generic_engine.py` dòng 15–21 song song. Về mặt CƠ CHẾ, một `edge`/`node` CÓ
`"value"` (nếu LLM/patch gán) sẽ được nạp vào `base` giống hệt `switch`. Vậy lý
do E1 quan sát "cạnh không bao giờ vào bảng" là **LLM tình cờ không gán
`value` cho cạnh** trong ca Dijkstra thật, KHÔNG PHẢI vì code có một bộ lọc
theo role đang hoạt động. Xác nhận gốc rễ đúng là "thiếu ràng buộc role" (F1/
F2), không phải "một cơ chế lọc có sẵn nhưng bị lỗi".

**F5 — `check_semantic`/`_check_weighted_sum` (`backend/app/simulation/semantic.py`
dòng 110–135, 374–381) chỉ chạy khi có `expectation` gắn kèm, và CHỈ được
import bởi `backend/app/evaluation/harness.py:23,225`** (grep xác nhận: không
site nào khác trong `backend/app` import `check_semantic`) — **không phải một
validator runtime áp dụng cho MỌI request người dùng thật** (input tự do từ
`/api/analyze` không có `expectation` nào, và `pipeline.py`/`patterns.py`
không import hàm này). Đính chính so với suy đoán ban đầu: `run_gates`
(`patterns.py:184-203`, đường pattern reuse E8) **KHÔNG** gọi `check_semantic`
— nó gọi `check_semantic_compatibility` (role-set mismatch, KHÔNG thực thi
hành vi, dòng 193) làm gate 3, và **tự thực thi `build_timeline`/`values_of`
làm gate 4** (dòng 196-202, bọc `try/except Exception` → reject
`f"engine: {exc}"`). Xác nhận trực tiếp bằng đọc `patterns.py`: đây CHÍNH LÀ
cơ chế mà plan Task 4 dựa vào ("`run_gates` đã bọc `values_of` trong
try/except — TỰ ĐỘNG chuyển lỗi thành reject, không sửa `run_gates`") — một
khi Task 4 làm `values_of`/`build_timeline` ném `GenericEvaluationError` cho
operand/role sai, `run_gates` tự động reject MÀ KHÔNG CẦN SỬA GÌ THÊM ở
`patterns.py`. Kết luận không đổi: không có lưới an toàn nào (kể cả
`run_gates`) hiện đang chặn ca Dijkstra — `check_semantic_compatibility` chỉ
kiểm role-SET có giao nhau, không kiểm operand-level coherence; `values_of`
hiện tại (trước Task 4) không ném lỗi gì cho input edge/node (chỉ trả 0) nên
gate 4 của `run_gates` cũng đã lọt ca đó — khớp chính xác với E8's mô tả
"pattern adapt chạy đủ 4 cổng... siết validator ⇒ pattern cũ tự động bị kiểm
lại".

---

## 2. Ma trận — OBJECT primitives

Nguồn vai trò: `PRIMITIVE_ROLES` — `backend/app/simulation/dsl/manifest.py`
dòng 45–69 (dict), xác nhận dòng chính xác từng khoá dưới đây (đã đọc lại
2026-07-16, khác nhẹ so với E14 ghi "46–70" trong spec — dict thật bắt đầu
dòng 45, đóng dòng 69; dùng số ở đây).

### 2.1 `switch` — `manifest.py:47` → `{"interactive", "logical", "numeric"}`

- **Input/provider role:** logical, numeric — cung cấp `value` (0/1) làm toán
  hạng cho CẢ `boolean` LẪN `weighted_sum`.
- **Output role (khi là target):** logical, numeric — về NGUYÊN TẮC hợp lệ làm
  target của cả hai loại rule (dù chủ ý thiết kế là NGUỒN, không phải đích —
  không có gì trong validator hiện tại CẤM switch làm target; nếu là target
  thì tự động bị loại khỏi `initialBase`/`initial_base` vì `targets.has(id)`).
- **Trường bắt buộc:** `value` (0/1) để có nghĩa làm nguồn base; không bắt
  buộc ở validator (object không có `value` vẫn hợp lệ CẤU TRÚC, chỉ vô nghĩa
  khi dùng làm input/toggle).
- **Input thiếu là gì:** switch không có `value`, không phải rule target,
  được dùng làm rule input → HIỆN TẠI: `values[id] ?? 0` (model.ts:186) /
  `values.get(i, 0)` (generic_engine.py:25) — lặng lẽ = 0 (E2/E16). ĐÚNG RA
  đây phải là `INVALID_SOURCE` (switch là provider hợp lệ về TYPE nhưng thiếu
  cấu hình `value` — lỗi khai báo, không phải "optional").
- **Hành vi dependency:** là NGUỒN gốc (base), không phụ thuộc rule khác trừ
  phi bị gán làm target (F1).
- **Bound tất định:** N/A trực tiếp (không lặp trừ khi tham gia fixed-point
  của rule tiêu thụ nó).
- **Hành vi fail runtime hiện tại:** KHÔNG BAO GIỜ fail — luôn ra 0 nếu thiếu.
- **Bản chất biểu diễn:** tương tác (input nguồn do học sinh điều khiển qua
  `toggle`).
- **ENFORCEMENT DISPOSITION: TASK-3** (validator INVALID_SOURCE khi switch
  thiếu `value` được dùng làm input — RED test
  `test_provider_thieu_value_bi_tu_choi`, plan Task 3 Step 1) **/ TASK-4**
  (runtime `GenericEvaluationError`, `backend/tests/test_generic_engine_m13.py`)
  **/ TASK-5/TASK-6** (frontend parity, `generic.test.ts` khối "M13 operand
  coherence"/"M13 runtime").

### 2.2 `lamp` — `manifest.py:48` → `{"logical", "numeric"}`

- **Input/provider role:** logical, numeric.
- **Output role:** logical, numeric — thường LÀ target (manifest mô tả "đèn
  hiển thị giá trị 0/1, thường là target của rule", `manifest.py:76`) nhưng
  role khai gồm CẢ `numeric` nên `weighted_sum` cũng được phép ghi vào lamp
  một giá trị KHÔNG phải 0/1 (vd 13) — renderer (`ui.tsx` dòng 376–390) vẽ
  `on = v >= 1` (mọi giá trị ≥1 đều "sáng") và in số thật (`{v}`) bên trong —
  KHÔNG sai (số hiển thị đúng giá trị đã tính), chỉ là ẩn dụ "đèn" bị dùng cho
  một số bất kỳ. Đây là một lỏng-lẻo về mô hình hoá SẴN CÓ trong manifest, kế
  thừa nguyên vẹn từ Task 2 (dẫn xuất, không phát minh) — không gây "kết quả
  sai trông như đúng" (số hiển thị luôn đúng), nên không phải bug lớp §9b nào;
  ghi nhận nhưng KHÔNG redesign UI (cấm theo Global Constraint của plan).
- **Trường bắt buộc:** không bắt buộc field nào ở object-level; nếu KHÔNG là
  target của rule nào thì có thể mang `value` khởi tạo (dùng làm nguồn boolean
  tĩnh — hợp lệ, validator không cấm).
- **Input thiếu:** giống switch — `?? 0`/`.get(i, 0)` lặng lẽ, E2/E3/E16.
- **Hành vi dependency:** nếu là target — tham gia DAG rule (EXISTING, xem
  §3). Nếu không — là nguồn tĩnh như switch.
- **Bound:** như trên.
- **Fail runtime:** không, giống switch.
- **Bản chất biểu diễn:** hiển thị dẫn xuất (target điển hình) hoặc nguồn tĩnh.
- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6** (cùng cơ chế provider/target như
  switch — RED test dùng chung `test_rule_output_ghi_vao_target_dung_role_hop_le`,
  `test_derived_target_sai_role_bi_tu_choi_weighted_sum_nuoi_boolean` cho
  trường hợp lamp là target logical bị numeric-derived nuôi sai role).

### 2.3 `value_box` — `manifest.py:49` → `{"numeric"}`

- **Input/provider role:** numeric (chỉ numeric — KHÔNG có logical, nên sau
  Task 3, value_box KHÔNG được dùng làm input cho `boolean` — RED test
  `test_boolean_input_value_box_bi_tu_choi`, plan Task 3 Step 1, chính là ca
  đại diện chuẩn cho lớp bug "object numeric làm input boolean" mà §9b yêu cầu
  audit phải bắt).
- **Output role:** numeric.
- **Trường bắt buộc:** thường KHÔNG có `value` (là target điển hình của
  `weighted_sum`); có thể có `value` nếu dùng làm hằng số numeric nguồn.
- **Input thiếu:** như trên — hiện lặng lẽ 0.
- **Dependency:** DAG rule như trên.
- **Bound:** như trên.
- **Fail runtime:** không.
- **Bản chất biểu diễn:** hiển thị dẫn xuất numeric (target điển hình của
  weighted_sum — đây chính là loại object đóng vai "tổng đường đi" giả trong
  ca Dijkstra, `calc_path_ABC`/`calc_path_AC` trong fixture Task 7).
- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6.**

### 2.4 `node` — `manifest.py:50` → `{"relational"}`

- **Input/provider role:** KHÔNG có role logical/numeric — chỉ relational.
  Sau Task 3, `value_provider_types("numeric")` = `{switch, lamp, value_box}`
  (RED test `test_relational_khong_phai_value_provider`, plan Task 2 Step 1) —
  `node` bị loại tự động, không cần allowlist viết tay riêng cho node.
- **Output role:** không có role logical/numeric — KHÔNG được là target hợp
  lệ của `boolean`/`weighted_sum` sau Task 3. RED test cụ thể trong plan dùng
  `node` làm ví dụ chính xác: `test_rule_output_ghi_vao_target_sai_role_bi_tu_choi`
  (`{"id": "n1", "type": "node", …}` làm target của `weighted_sum` → reject,
  chuỗi lỗi chứa `"không nhận được"`).
- **Trường bắt buộc:** không có; `node_type` là chuỗi tự do tuỳ chọn
  (`manifest.py:114-117`, không phải enum).
- **Input thiếu là gì:** HIỆN TẠI (trước Task 3) — nếu một node CÓ `"value"`
  (F4: không có gì ngăn LLM/patch gán) và được dùng làm rule input, nó qua
  cổng y hệt switch/value_box — validator KHÔNG phân biệt theo role
  (F1/F2). Đây CHÍNH LÀ lớp bug tổng quát mà `edge` (Dijkstra) chỉ là một ca
  cụ thể.
- **Dependency:** N/A trực tiếp (node không tham gia DAG rule trừ khi bị lạm
  dụng làm input/target — điều Task 3 sẽ chặn).
- **Bound:** N/A.
- **Fail runtime:** không hiện tại — sẽ thành `INVALID_SOURCE` (Task 3) /
  `invalid_numeric_source` (Task 4, lưới sau cùng).
- **Bản chất biểu diễn:** cấu trúc (đỉnh đồ thị/điểm hình học) — KHÔNG mang
  giá trị số hay logic theo hợp đồng DSL hiện hành.
- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6.**

### 2.5 `edge` — `manifest.py:51` → `{"relational"}`

Cấu trúc y hệt `node` (chỉ relational, không numeric/logical) — đây là object
type CHÍNH của ca Dijkstra kích hoạt milestone (`edge_AB`, `edge_BC`,
`edge_AC` làm input cho `weighted_sum`, E1/E6).

- **Input/provider role:** KHÔNG — `value_provider_types("numeric")` loại trừ
  edge (Task 2). RED test trực tiếp: `test_weighted_sum_input_edge_bi_tu_choi`
  (plan Task 3 Step 1) — đúng shape bug E6, chuỗi lỗi chứa
  `"không có nguồn giá trị"`.
- **Output role:** KHÔNG — cùng cơ chế ràng buộc 2 như node (không có test
  edge-làm-target riêng trong danh sách Task 3 Step 1, nhưng code path
  (`out_role not in PRIMITIVE_ROLES.get(target_obj["type"], set())`) tổng quát
  cho MỌI type kể cả edge — không cần allowlist riêng).
- **Trường bắt buộc:** `from`/`to` phải là id object có thật
  (`validator.py:275-278`, `validate.ts:228-235`) — **EXISTING**, tuy không có
  test tên riêng biệt lộ ra trong lần đọc `test_dsl.py` (kiểm tra bằng
  `PACKET_SPEC`/`test_packet_spec_hop_le`, dòng 56-60, chứng minh gián tiếp
  qua case dương; case âm "from/to không tồn tại" không có tên hàm riêng tìm
  thấy — xem §8).
- **Input thiếu:** như node — HIỆN TẠI lặng lẽ 0 nếu edge có `value` (hiếm khi
  xảy ra trong thực tế vì LLM không được dạy gán value cho edge, nhưng CODE
  không cấm).
- **Dependency:** N/A trực tiếp.
- **Bound:** N/A.
- **Fail runtime:** không hiện tại.
- **Bản chất biểu diễn:** cấu trúc (cạnh đồ thị/đoạn nối) — relational thuần
  tuý, KHÔNG mang trọng số theo hợp đồng DSL v1 (spec §3.2: "Không giả định
  cạnh là numeric... DSL hiện hành KHÔNG có accessor trọng-số-cạnh").
- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6**, khoá regression cụ thể bằng
  **TASK-7** (`backend/tests/fixtures/m13_dijkstra_pseudo_algorithm.json` +
  `test_artifact_dijkstra_cu_bi_validator_tu_choi`) và **TASK-10** (pattern
  reuse revalidation, `test_m13_pattern_revalidate.py`).

### 2.6 `moving_entity` — `manifest.py:52` → `{"movement"}`

- **Input/provider role:** KHÔNG (chỉ movement).
- **Output role:** KHÔNG.
- **Trường bắt buộc:** không có field riêng; được tham chiếu qua
  `process.entity` (phải type `moving_entity`, kiểm tại `validator.py:429-430`
  / `validate.ts:406-408` — **EXISTING**, test backend
  `test_process_entity_khong_phai_moving_entity_bi_reject` (`test_dsl.py:174-180`),
  test frontend gián tiếp qua `GENERIC_PACKET_SPEC` benchmark
  (`generic.test.ts` §"BENCHMARK") — không có case ÂM tường minh phía frontend
  cho "entity sai type" (xem §8).
- **Input thiếu:** như node/edge nếu bị lạm dụng làm rule input (F2) — cùng
  gap tổng quát.
- **Dependency:** "position" của moving_entity bị `move_along_path` SỞ HỮU
  (`_PROCESS_CONTROLS`, `validator.py:109`) — không được đồng thời `drag`
  cùng entity đó (`ownership_conflict`, `validator.py:112-130`) — **EXISTING**,
  test frontend "drag chính entity của process → allowlist chặn trước"
  (`generic.test.ts` dòng ~585-587) — thực ra bị chặn ở TẦNG ALLOWLIST
  (`DRAG_TARGET_TYPES = {node}`, moving_entity không đủ điều kiện drag từ đầu)
  trước khi chạm tới ownership check — cả hai lớp phòng thủ đều đúng.
- **Bound:** N/A.
- **Fail runtime:** không hiện tại (ngoài phạm vi numeric).
- **Bản chất biểu diễn:** chuyển động (thực thể do process điều khiển vị trí).
- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6** (nếu bị dùng làm rule input/target
  — gap tổng quát F2/F1, tự động đóng bởi cơ chế role-derivation, không cần
  allowlist riêng); phần entity-type/ownership: **EXISTING**.

### 2.7 `label` — `manifest.py:53` → `{"textual"}`

- **Input/provider role:** KHÔNG (chỉ textual).
- **Output role:** KHÔNG.
- **Trường bắt buộc:** không bắt buộc `label`-nội-dung ở validator (khác với
  `heading`/`paragraph`/`text` — những type đó BẮT BUỘC `"text"` không rỗng,
  `validator.py:298-304`; type `label` KHÔNG nằm trong `TEXT_CONTENT_TYPES`
  nên không bị bắt buộc gì). Hệ quả trực tiếp: một object `type: "label"`
  KHÔNG có field `.label` vẫn hợp lệ cấu trúc — và khi hiển thị,
  `objLabel`/`objLabel`-tương-đương rơi vào `o?.label ?? id` (E5,
  `model.ts:226-229`) → **rò id thô ra UI học sinh** (`node_A`,
  `calc_path_ABC` trong ca Dijkstra thật).
- **Input thiếu:** như các object textual khác nếu bị lạm dụng làm rule input
  (F2).
- **Dependency:** N/A.
- **Bound:** N/A.
- **Fail runtime (display, không phải numeric):** hiện tại — id thô lộ ra nếu
  `label`/`text` trống HOẶC bằng chính id HOẶC dạng kỹ thuật (`node_A`,
  `edge_AB`) — chính là bug lớp Workstream C (E5/E13).
- **Bản chất biểu diễn:** nội dung chữ tĩnh (nhãn trang trí/chú thích).
- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6** (value-role gap tổng quát) **+
  TASK-11** (`displayLabel` sanitize — label thiếu ∨ `label === id` ∨ dạng
  định danh kỹ thuật; RED test 4 case trong plan Task 11 Step 1, file
  `generic.test.ts`).

### 2.8 `container` — `manifest.py:55` → `{"structural"}`

- **Input/provider role:** KHÔNG.
- **Output role:** KHÔNG.
- **Trường bắt buộc:** `"text"` TUỲ CHỌN (tiêu đề khung, `manifest.py:88`) —
  KHÔNG bắt buộc (container không nằm trong `TEXT_CONTENT_TYPES`). `parent`
  (nếu có) phải trỏ tới container/group khác, không chu trình, độ sâu ≤ 4
  (`MAX_NESTING_DEPTH`) — **EXISTING**, test
  `test_parent_khong_phai_container_bi_reject`, `test_parent_chu_trinh_bi_reject`
  (`test_dsl.py:274+`).
- **Input thiếu:** N/A trực tiếp trừ khi lạm dụng làm rule input (F2).
- **Dependency:** cây `parent` — nesting, chu trình, độ sâu đều **EXISTING**
  (dẫn ở trên).
- **Bound:** `MAX_NESTING_DEPTH = 4` (`manifest.py:130`) — **EXISTING**,
  cấu trúc chứ không phải hội tụ evaluation.
- **Fail runtime:** không (validator gác hết ở tầng cấu trúc).
- **Bản chất biểu diễn:** cấu trúc/bố cục (KHÔNG mang giá trị tính toán).
- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6** (value-role gap nếu bị lạm dụng
  làm rule input/target — chưa từng thấy trong thực tế nhưng CODE hiện không
  cấm); nesting/parent: **EXISTING**.

### 2.9 `group` — `manifest.py:56` → `{"structural"}`

Giống hệt `container` về mặt validator (cả hai đều thuộc `CONTAINER_TYPES =
{"container", "group"}`, `validator.py:32`), khác biệt DUY NHẤT là ngữ nghĩa
hiển thị ("khung nổi bật" vs "không khung") — không tạo khác biệt ở engine.

- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6** (value-role gap); nesting/parent:
  **EXISTING** (dùng chung code path với container).

### 2.10 `heading` — `manifest.py:57` → `{"textual"}`

- **Input/provider role:** KHÔNG.
- **Output role:** KHÔNG.
- **Trường bắt buộc:** `"text"` KHÔNG rỗng, ≤ `MAX_TEXT_LEN` = 500
  (`validator.py:298-304`, `manifest.py:129`) — **EXISTING**, test
  `test_heading_thieu_text_bi_reject` (`test_dsl.py:264-271`),
  `test_text_qua_dai_bi_reject` (`test_dsl.py:294+`).
- **Input thiếu:** N/A trừ khi lạm dụng làm rule input (F2).
- **Dependency:** có thể có `parent` (như container/group con) — cùng cơ chế
  EXISTING.
- **Bound:** `MAX_TEXT_LEN = 500` — EXISTING.
- **Fail runtime:** không.
- **Bản chất biểu diễn:** nội dung chữ (tiêu đề) — thuần tuý hiển thị.
- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6** (value-role gap); text-length/
  requiredness: **EXISTING**.

### 2.11 `paragraph` — `manifest.py:58` → `{"textual"}`

Cùng nhánh `TEXT_CONTENT_TYPES` với heading — hành vi validator ĐỒNG NHẤT
(`validator.py:298-304` lặp qua `TEXT_CONTENT_TYPES = {"heading", "paragraph",
"text"}`). Không có test tên riêng cho "paragraph thiếu text" (chỉ có test
tên `test_heading_thieu_text_bi_reject`), nhưng case dương `WEB_SPEC`
(`test_web_structural_spec_hop_le`, `test_dsl.py:256-261`) xác nhận đường
paragraph-CÓ-text hoạt động đúng; nhánh thiếu-text dùng CHUNG code nên hành vi
được suy ra đúng bằng đối chiếu code, không phải đoán (xem §8 cho ghi chú test
coverage).

- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6** (value-role gap); text-content
  requiredness: **EXISTING** (hành vi đúng qua code chung với heading; xem §8
  về test riêng).

### 2.12 `text` — `manifest.py:59` → `{"textual"}`

Cùng nhánh `TEXT_CONTENT_TYPES`, cùng phân tích như `paragraph`.

- **ENFORCEMENT DISPOSITION: TASK-3/4/5/6** (value-role gap); text-content
  requiredness: **EXISTING** (xem §8).

---

## 3. Ma trận — RULE primitives

Nguồn: `RULE_TYPES` (`model.ts:41`, chỉ `["boolean", "weighted_sum"]`),
`rule_types()` (`manifest.py:140-141`, dẫn từ `MANIFEST["rule_types"]`
dòng 94-97, đúng 2 khoá). `PRIMITIVE_ROLES["boolean"] = {"logical"}`
(`manifest.py:61`), `PRIMITIVE_ROLES["weighted_sum"] = {"numeric"}`
(`manifest.py:62`).

### 3.1 `boolean`

- **Input/provider role cần:** `logical` (ngầm định qua vai trò RULE tự thân;
  Task 2 sẽ tường minh hoá thành `RULE_IO_ROLES["boolean"] =
  {"input_role": "logical", "output_role": "logical"}`).
- **Output role sinh ra:** `logical`.
- **Trường bắt buộc:** `op` ∈ `BOOL_OPS = {and, or, not, xor}`
  (`manifest.py:98`, `validator.py:335-338`, `validate.ts:295-299`); `inputs`
  (≥0 phần tử, tồn tại); `target` (tồn tại). Kiểm `op` hợp lệ — **EXISTING**
  về code nhưng KHÔNG có test riêng cho GIÁ TRỊ `op` sai (vd `"nand"`) — chỉ
  có test cho rule TYPE sai (`test_rule_type_la_bi_reject`, khác biến); xem §8.
- **Input thiếu là gì (HIỆN TẠI):** `values[id] ?? 0` (`model.ts:186`) /
  `values.get(i, 0)` (`generic_engine.py:25`) → lặng lẽ = 0 = **false** (E2,
  E16). Đây là bug lớp §9b #2 ("giá trị thiếu lặng lẽ nhận default") VÀ #4
  ("unresolved dependency bị lẫn với 0/false", qua seed `values[t] = 0`/
  `setdefault(t, 0)` — E17, `model.ts:210`, `generic_engine.py:46`).
- **Hành vi dependency:** DAG qua target-làm-input rule khác (M11) — hợp lệ,
  **EXISTING + test** `test_rule_long_qua_trung_gian_hop_le` (`test_dsl.py:127-131`)
  và `_check_nested_boolean` (`semantic.py:281-340`, dò bảng chân trị hợp
  thành, id-agnostic). Hai rule cùng ghi MỘT target → reject, **EXISTING +
  test** `test_hai_rule_cung_target_bi_reject` (`test_dsl.py:134-144`). Chu
  trình phụ thuộc → reject, **EXISTING + test**
  `test_chu_trinh_rule_bi_reject` (`test_dsl.py:85-96`, dùng `_detect_cycle`,
  `validator.py:46-63`).
- **Bound tất định:** fixed-point tối đa `len(rules) + 1` lượt
  (`model.ts:212`, `generic_engine.py:48`) — **EXISTING**, DAG hợp lệ (không
  chu trình, validator đã cấm) luôn hội tụ trong bound này. Task 4/6 GIỮ
  NGUYÊN kết quả cho spec hợp lệ (khẳng định rõ trong plan: "kết quả giống
  hệt" khi chuyển sang forward-resolve DAG).
- **Hành vi fail runtime hiện tại:** KHÔNG BAO GIỜ fail — toán hạng thiếu/sai
  role vẫn cho ra 0 hoặc 1 (không typed error).
- **Bản chất biểu diễn:** tính toán dẫn xuất tất định (phép logic) trên toán
  hạng ĐÃ khai — hợp lệ như một primitive độc lập, KHÔNG phải "thuật toán tuỳ
  ý" (arbitrary_algorithm) miễn operand đúng role.
- **ENFORCEMENT DISPOSITION:** operand/target role coherence →
  **TASK-3** (backend, RED test `test_boolean_input_value_box_bi_tu_choi`,
  `test_rule_output_ghi_vao_target_dung_role_hop_le`) **/ TASK-4** (runtime
  3-state + `GenericEvaluationError`) **/ TASK-5** (frontend validator mirror)
  **/ TASK-6** (frontend runtime + store fail-closed). DAG/dup-target/cycle:
  **EXISTING** (dẫn test ở trên).

### 3.2 `weighted_sum` — primitive kích hoạt milestone

- **Input/provider role cần:** `numeric`.
- **Output role sinh ra:** `numeric`.
- **Trường bắt buộc:** `inputs`, `weights` (CÙNG ĐỘ DÀI với inputs, đều là số
  — `validator.py:339-343`, `validate.ts:300-306`) — **EXISTING** cho ĐỘ DÀI/
  KIỂU SỐ của weights, nhưng **KHÔNG** kiểm operand có nguồn giá trị số theo
  role (E6, chính là lỗ đã kích hoạt milestone).
- **Input thiếu là gì (HIỆN TẠI):** operand thiếu → `?? 0` (E2,
  `model.ts:186`/`generic_engine.py:25`); WEIGHT thiếu cũng `?? 0` (E3,
  `model.ts:203-204` — `const weights = rule.weights ?? []`, dòng 204
  `weights[i] ?? 0`; `generic_engine.py:38-39`). Cả hai đều lặng lẽ = 0 —
  chính là cơ chế khiến ca Dijkstra ra "0" ở bước cuối 10/10 dù trông như chạy
  trơn tru.
- **Hành vi dependency:** DAG giống `boolean` — **EXISTING** (cùng cơ chế
  `_detect_cycle`/`detectCycle`, cùng test dựng trên `weighted_sum`:
  `test_chu_trinh_rule_bi_reject` dùng chính `weighted_sum` làm ví dụ,
  `test_dsl.py:85-96`).
- **Bound tất định:** cùng fixed-point `len(rules) + 1` — **EXISTING**.
- **Hành vi fail runtime hiện tại:** KHÔNG fail — kể cả khi input có role sai
  (edge/node) HAY kết quả tràn số (không kiểm `Infinity`/`NaN` — bug lớp §9b
  #6 "kết quả numeric non-finite tới được renderer", hiện KHÔNG bị chặn ở bất
  kỳ tầng nào).
- **Bản chất biểu diễn:** tính toán TUYẾN TÍNH tất định trên toán hạng có role
  numeric — bản thân phép toán ĐÚNG ("tổng inputs nhân weights",
  `manifest.py:96`), nhưng CÓ THỂ BỊ LẠM DỤNG để giả một cơ chế thuật toán
  (Dijkstra: dùng `weighted_sum` trên id cạnh của MỘT ĐƯỜNG ĐI KHAI SẴN để giả
  "tổng trọng số đường đi", trong khi thuật toán thật cần extract-min/
  relaxation/predecessor mà DSL không có, spec §4.2). Việc "primitive đúng
  nhưng bị chọn sai để biểu diễn bài cần thuật toán" là vấn đề TẦNG ROUTING
  (Workstream B), không phải bản thân phép `weighted_sum` sai.
- **ENFORCEMENT DISPOSITION:** operand/target role coherence + non-finite
  guard → **TASK-3** (RED test `test_weighted_sum_input_edge_bi_tu_choi`,
  `test_chuoi_dan_xuat_khai_bao_dao_van_hop_le`,
  `test_derived_target_sai_role_bi_tu_choi_weighted_sum_nuoi_boolean`,
  `test_derived_target_dung_role_van_hop_le_chain_numeric`,
  `test_rule_output_ghi_vao_target_sai_role_bi_tu_choi`) **/ TASK-4** (mã lỗi
  `invalid_numeric_source`, `missing_weight`, `non_finite_numeric_value`,
  `unresolved_dependency_after_bound` — RED test
  `test_toan_hang_khong_ton_tai_trong_values_nem_typed_error`,
  `test_ket_qua_non_finite_nem_typed_error`,
  `backend/tests/test_generic_engine_m13.py`) **/ TASK-5/TASK-6** (frontend
  parity). Chống LẠM DỤNG làm thuật toán giả → **TASK-9** (computation gate
  2 kênh: `known_gap_roles()` + `result_ownership` fail-closed,
  `backend/tests/test_m13_routing.py`). Khoá case cụ thể (Dijkstra) →
  **TASK-7** (fixture + regression lock hai phía) **/ TASK-10** (pattern reuse
  revalidation, `backend/tests/test_m13_pattern_revalidate.py`).

### 3.3 Comparison rule — **VẮNG MẶT**

`RULE_TYPES` (`model.ts:41`) chỉ có 2 phần tử: `["boolean", "weighted_sum"]`.
`MANIFEST["rule_types"]` (`manifest.py:94-97`) chỉ có 2 khoá. `rule_types()`
(`manifest.py:140-141`) trả `set(MANIFEST["rule_types"])` — xác nhận KHÔNG có
rule so sánh (`>`, `<`, `==`, `>=`, "ít nhất k trong n"…) trong DSL v1. Vai trò
`numeric_threshold` được khai trong `SEMANTIC_ROLES` (`manifest.py:36`) nhưng
KHÔNG có primitive nào cover nó (`known_gap_roles()`, `manifest.py:199-201`,
trả về đúng vai trò này) — đây là gap ĐÃ BIẾT VÀ CÓ CHỦ Ý (dùng để trigger
`capability_gap`, không phải một lỗ audit mới phát hiện).

- **ENFORCEMENT DISPOSITION: OUT-OF-SCOPE.** Rationale: (1) DSL v1 không có
  primitive so sánh — không có hành vi runtime nào để audit ("vắng mặt" theo
  đúng yêu cầu spec §9b: "mục nào không tồn tại trong manifest thì matrix ghi
  vắng mặt, không phát minh primitive mới"); (2) plan Global Constraint cấm
  tường minh "KHÔNG primitive DSL mới" (`docs/superpowers/plans/2026-07-16-m13-generic-semantic-soundness.md`
  dòng 15); (3) nhu cầu so sánh/ngưỡng đã có đường thoát TRUNG THỰC sẵn có —
  `numeric_threshold` → `known_gap_roles()` → `capability_gap` (không dựng
  cảnh giả bằng cách lách qua `weighted_sum` với trọng số âm để giả phép so
  sánh — nếu phát hiện LLM làm vậy trong live testing, đó là vấn đề của
  TASK-9's taxonomy/prompt, không phải của rule so sánh không tồn tại). Thêm
  comparison rule thật (nếu cần trong tương lai) đòi hỏi milestone/approval
  riêng, không phải phạm vi Task 1.

---

## 4. Ma trận — INTERACTION primitives

Nguồn: `INTERACTION_TYPES` (`model.ts:47`, 2 phần tử: `toggle`, `drag`).

### 4.1 `toggle` — `manifest.py:64`, role `{"interactive"}`

- **Input/provider role:** N/A — interaction không sinh giá trị số/logic, nó
  THAO TÁC `base[target]` trực tiếp: `index.ts:44-49` —
  `if (action.target in state.base) { … cur >= 1 ? 0 : 1 … }` — **chỉ base
  value 0/1**, đúng như brief mô tả, KHÔNG chạy qua `evalRule`/`valuesOf`.
- **Output role:** N/A (side-effect thuần, không phải giá trị dẫn xuất).
- **Trường bắt buộc:** `target` phải (a) tồn tại, (b) CÓ `"value"` khởi tạo,
  (c) KHÔNG phải target của rule nào. Cả ba — **EXISTING**:
  - (a) tồn tại: kiểm chung với mọi interaction (`validator.py:368-369`,
    `validate.ts:333-335`).
  - (b) có value: `validator.py:377-383` (thông báo lỗi chỉ sang `drag`),
    `validate.ts:345-352` — test backend
    `test_toggle_object_khong_value_bi_reject` (`test_dsl.py:404-413`), test
    frontend describe "toggle cần value — M7.13A" (`generic.test.ts:658-672`).
  - (c) không phải rule target: `validator.py:374-376`, `validate.ts:341-344`
    — test backend `test_toggle_gia_tri_dan_xuat_bi_reject`
    (`test_dsl.py:168-171`). **Frontend KHÔNG có test riêng cho case (c)**
    (xem §8 — hành vi đúng qua đọc code, chỉ thiếu test khoá).
- **Input thiếu là gì:** N/A theo nghĩa numeric-provider (toggle không tiêu
  thụ giá trị số). Nếu action dispatch với `target` KHÔNG có trong
  `state.base` (vd bug UI gọi sai id) → `index.ts:43-49` rơi vào nhánh cuối
  `return state;` (dòng 53) — **no-op an toàn, không throw, không crash**,
  nhưng cũng KHÔNG có `InteractionFeedback` báo học sinh (khác `drag`'s
  `hitBounds` feedback, `model.ts:390-395`). Không phải bug — chỉ là
  interaction không tạo phản hồi cho trường hợp lẽ ra không thể xảy ra sau
  validate (validator đã gác `target` phải tồn tại + có value từ trước).
- **Hành vi dependency:** `_INTERACTION_CONTROLS = {"drag": "position",
  "toggle": "value"}` (`validator.py:108`) nhưng `_PROCESS_CONTROLS` (dòng
  109) CHỈ có `move_along_path → "position"` — KHÔNG process nào điều khiển
  `"value"` trong DSL v1 hiện tại, nên nhánh `ownership_conflict` cho toggle
  **không bao giờ được kích hoạt trong thực tế** (code phòng thủ cho tương
  lai, không phải bug — không gây sai hành vi, chỉ là chưa có kịch bản kích
  hoạt).
- **Bound tất định:** N/A.
- **Hành vi fail runtime:** no-op nếu target không hợp lệ về cấu trúc — an
  toàn.
- **Bản chất biểu diễn:** tương tác (học sinh điều khiển NGUỒN, không sinh giá
  trị dẫn xuất).
- **ENFORCEMENT DISPOSITION: EXISTING** (backend đầy đủ test hai case chính;
  frontend đủ test case "thiếu value", THIẾU test case "trên rule target" —
  ghi nhận ở §8, không nâng thành STOP-UNRESOLVED vì hành vi CODE đã đúng,
  chỉ thiếu regression lock ở một phía).

### 4.2 `drag` — `manifest.py:65`, role `{"interactive"}`

- **Input/provider role:** N/A.
- **Output role:** N/A (side-effect: cập nhật `state.pos[target]`,
  `applyMove`, `model.ts:372-404`).
- **Trường bắt buộc:** `target` ∈ `DRAG_TARGET_TYPES = {"node"}`
  (`manifest.py:109`, `validator.py:36/384-390`, `validate.ts:356-361`) —
  **EXISTING + test** `test_drag_ngoai_allowlist_bi_reject`
  (`test_dsl.py:352-362`, cả edge lẫn switch bị chặn), frontend "drag ngoài
  allowlist (edge/switch) bị reject" (`generic.test.ts:542-555`). Constraints
  (`bounds`/`axis`/`snap`) hợp lệ — **EXISTING + test**
  `test_drag_constraints_sai_bi_reject` (`test_dsl.py:372-386`, 7 case), frontend
  "constraints sai bị reject" (`generic.test.ts:557-569`, 5 case).
- **Input thiếu là gì:** N/A (không có khái niệm numeric-provider cho drag).
- **Hành vi dependency:** ownership — không được đồng thời `drag` + process
  cùng điều khiển `"position"` của CÙNG object — **EXISTING + test**
  `test_ownership_mot_thuoc_tinh_khong_hai_chu` (`test_dsl.py:389-401`),
  frontend "ownership — drag vật đang bị process điều khiển bị reject; node
  waypoint thì OK" (`generic.test.ts:571-588`). Node LÀM WAYPOINT của path
  (không phải entity) vẫn kéo được — **EXISTING + test**
  `test_drag_node_lam_waypoint_van_hop_le` (`test_dsl.py:416+`).
- **Bound tất định:** N/A.
- **Hành vi fail runtime:** `applyMove` trả state cũ (no-op) nếu target không
  tồn tại/sai type/không visible ở frame hiện tại/không khai `drag`
  (`model.ts:372-379`) — **EXISTING + test** "apply move: từ chối khi chưa
  visible / không khai drag / action lạ" (`generic.test.ts:624-636`).
- **Bản chất biểu diễn:** tương tác hình học thuần tuý (bounds/axis/snap chỉ
  ràng buộc hình học, không mang ý nghĩa domain).
- **ENFORCEMENT DISPOSITION: EXISTING** (đầy đủ test hai phía cho mọi nhánh).

---

## 5. Ma trận — PROCESS primitives

Nguồn: `PROCESS_TYPES` (`model.ts:53-54`, 2 phần tử). Cả hai đều role
`temporal` (`temporal_process_types()`, `manifest.py:171-174`, dẫn xuất từ
`PRIMITIVE_ROLES`, không hard-code tên).

### 5.1 `reveal_sequence` — `manifest.py:67`, role `{"temporal"}`

- **Input/provider role:** N/A trực tiếp — `steps[].objects` tham chiếu id
  object có thật (existence check, không phải value-provider check).
- **Output role:** N/A — sinh `Frame.visibleIds` tích luỹ (hiển thị/ẩn),
  KHÔNG phải giá trị logic/numeric.
- **Trường bắt buộc:** `steps` (1..20 phần tử, `MAX_REVEAL_STEPS`), mỗi
  `step.objects` không rỗng và mọi id tồn tại, chỉ field `objects`/`narration`
  được phép. TẤT CẢ — **EXISTING + test đầy đủ**:
  `test_reveal_spec_hop_le` (`test_dsl.py:210-214`, case dương),
  `test_reveal_ref_object_khong_ton_tai_bi_reject` (`test_dsl.py:217-219`,
  **đây chính là câu hỏi "step trỏ object không tồn tại" mà brief yêu cầu trả
  lời — ĐÃ bị validator chặn, không phải STOP-UNRESOLVED**),
  `test_reveal_field_la_bi_reject` (`test_dsl.py:222-226`),
  `test_reveal_qua_gioi_han_step_bi_reject` (`test_dsl.py:229-232`),
  `test_reveal_step_rong_bi_reject` (`test_dsl.py:235-237`). Frontend song
  song: "reveal tích lũy đúng" (`generic.test.ts:252-266`), "validator reject
  reveal step tham chiếu object không tồn tại" (`generic.test.ts:351-355+`).
- **Input thiếu là gì:** id không tồn tại → `INVALID` reject NGAY TẠI
  VALIDATOR (không phải runtime, không phải silent-default) — bug lớp §9b #5
  ("object cấu trúc bị tiêu thụ như giá trị đã tính") KHÔNG áp dụng ở đây vì
  `reveal_sequence` không "tính giá trị" từ object, chỉ hiển thị/ẩn nó.
- **Hành vi dependency:** nhiều `reveal_sequence`/process khác nhau chạy TUẦN
  TỰ theo thứ tự khai báo mảng `processes`
  (`buildTimeline`/`build_timeline` lặp `for proc of spec.processes`); visible
  TÍCH LUỸ trong CÙNG một `reveal_sequence` — **EXISTING + test** (dẫn ở
  trên). Trường hợp NHIỀU hơn một `reveal_sequence` process trong CÙNG một
  spec (thay vì nhiều step trong MỘT process) KHÔNG có test khoá — xem §8
  (quan sát, không phải bug: code lặp tuần tự, không có lý do kỹ thuật để
  tin nó sai, chỉ chưa được test tường minh).
- **Bound tất định:** giới hạn CẤU TRÚC `MAX_REVEAL_STEPS = 20`
  (`manifest.py:128`) — không phải bound HỘI TỤ kiểu numeric fixed-point
  (`reveal_sequence` không lặp/không có fixed-point, mỗi step sinh đúng 1
  frame, tất định tuyến tính theo số step).
- **Hành vi fail runtime:** không có nhánh fail runtime (validator đã gác hết
  tham chiếu trước khi tới `buildTimeline`).
- **Bản chất biểu diễn:** DỰNG TIẾN TRÌNH (process thị giác — hình thành cảnh
  từng bước) — KHÔNG PHẢI kết quả thuật toán. Đây là bug lớp §9b #8 ("process
  thị giác bị coi là kết quả thuật toán") NẾU bị LẠM DỤNG để "diễn" các bước
  của một thuật toán không có engine (vd dùng reveal để show "duyệt Dijkstra"
  từng bước mà không có cơ chế extract-min/relaxation thật đứng sau) — rủi ro
  này thuộc TẦNG ROUTING (Workstream B/TASK-9), KHÔNG phải lỗi trong cấu trúc
  của `reveal_sequence` (cấu trúc của nó đúng và đủ test).
- **ENFORCEMENT DISPOSITION: EXISTING** (mọi ràng buộc cấu trúc, có test đầy
  đủ hai phía) **+ TASK-9** (chống lạm dụng làm "diễn" kết quả thuật toán giả
  — thuộc computation gate, không sửa `reveal_sequence` bản thân).

### 5.2 `move_along_path` — `manifest.py:68`, role `{"movement", "temporal"}`

Primitive THỨ HAI cấu thành ca Dijkstra (hai `moving_entity` "runner_ABC"/
"runner_AC" chạy theo path khai sẵn trong khi ô `weighted_sum` giả vờ là "kết
quả tính toán" — spec §0).

- **Input/provider role:** N/A trực tiếp — nhưng CÂU HỎI BẮT BUỘC trả lời của
  brief:
  - **"entity của move_along_path không phải moving_entity?"** →
    `by_id.get(p.get("entity", ""), {}).get("type") != "moving_entity"` reject
    (`validator.py:429-430`); `byId[p.entity]?.type !== "moving_entity"`
    reject (`validate.ts:406-408`). **ĐÃ BỊ CHẶN — EXISTING + test**
    `test_process_entity_khong_phai_moving_entity_bi_reject`
    (`test_dsl.py:174-180`). Frontend: hành vi đúng qua code, KHÔNG có case
    ÂM tường minh (chỉ có case DƯƠNG qua `GENERIC_PACKET_SPEC` benchmark) —
    xem §8.
  - **"path id không tồn tại → validator có chặn không, engine làm gì?"** →
    ĐÃ ĐỌC CODE THẬT (không đoán): `for nid in path: if by_id.get(nid,
    {}).get("type") != "node": return None, 'Process "path" phải toàn id của
    object type node.'` (`validator.py:434-436`). Khi `nid` KHÔNG tồn tại,
    `by_id.get(nid, {})` trả `{}`, `.get("type")` trả `None ≠ "node"` → BỊ TỪ
    CHỐI TẠI VALIDATOR — engine (`build_timeline`/`buildTimeline`) KHÔNG BAO
    GIỜ nhận được path chứa id rác. `validate.ts:412-415` song song
    (`typeof nid !== "string" || byId[nid]?.type !== "node"`). **ĐÃ BỊ CHẶN
    ĐÚNG — nhưng KHÔNG CÓ TEST RIÊNG khoá nhánh này ở CẢ HAI PHÍA** (đã grep
    xác nhận, xem §8) — đây là câu hỏi brief đặc biệt cảnh báo "dễ có
    STOP-UNRESOLVED thật"; kết luận sau khi đọc code: **KHÔNG PHẢI
    STOP-UNRESOLVED** (hành vi đúng), mà là một khoảng trống KIỂM THỬ.
- **Output role:** N/A — sinh `Frame.entityPos` (entityId → nodeId hiện tại),
  không phải giá trị logic/numeric.
- **Trường bắt buộc:** `entity` (moving_entity có thật), `path` (2..12 node
  id, `MAX_PATH`). Độ dài `2 ≤ len(path) ≤ 12`
  (`validator.py:432-433`/`validate.ts:409-411`) — **EXISTING về code**,
  KHÔNG có test riêng cho biên (path 1 phần tử hoặc >12) — xem §8.
- **Input thiếu là gì:** id không tồn tại/không phải node → `INVALID` reject
  tại validator (đã xác nhận ở trên) — KHÔNG phải silent-default, KHÔNG chạm
  bug lớp "unresolved bị lẫn 0/false" (lớp đó riêng cho numeric rule).
- **Hành vi dependency:** nhiều `move_along_path` trong CÙNG spec chạy TUẦN
  TỰ theo thứ tự khai báo `processes`, mỗi process CỘNG DỒN độc lập vào
  `entityPos` dùng chung (`buildTimeline`, `model.ts:266-298`) — không có test
  khoá cho ca "≥2 move_along_path cùng lúc" — xem §8 (quan sát, không phải
  bug). Ownership: `"position"` của `entity` bị process SỞ HỮU — không được
  đồng thời `drag` chính entity đó — **EXISTING + test** (dẫn ở §4.2); node
  LÀ WAYPOINT trong `path` (không phải `entity`) KHÔNG bị sở hữu, vẫn kéo được
  — **EXISTING + test** `test_drag_node_lam_waypoint_van_hop_le`.
- **Bound tất định:** giới hạn CẤU TRÚC `MAX_PATH = 12` — không phải bound hội
  tụ (mỗi bước path sinh đúng 1 frame, tất định tuyến tính theo độ dài path,
  không có fixed-point).
- **Hành vi fail runtime:** không có nhánh fail (validator gác hết tham chiếu
  trước khi tới `buildTimeline`/`build_timeline`).
- **Bản chất biểu diễn:** DỰNG TIẾN TRÌNH — di chuyển tất định theo đường ĐÃ
  CHO SẴN (`path` là danh sách node LLM/patch tự khai, engine chỉ "chạy theo",
  KHÔNG tính toán route/khoảng cách/đường ngắn nhất). **ĐÂY LÀ CHÍNH XÁC CƠ CHẾ
  BỊ LẠM DỤNG trong ca Dijkstra** — hai `moving_entity` chạy theo 2 path khai
  sẵn (`node_A→node_B→node_C` và `node_A→node_C`), tạo ẢO GIÁC "so sánh 2
  đường đi" trong khi KHÔNG process nào tính toán gì — con số "kết quả" đến từ
  `weighted_sum` hỏng riêng biệt (§3.2), không phải từ chính `move_along_path`.
  Bug lớp §9b #8 áp trực tiếp vào primitive NÀY khi kết hợp với `weighted_sum`
  giả trên cùng một spec.
- **ENFORCEMENT DISPOSITION:** entity-type/ownership/drag-waypoint —
  **EXISTING** (test đầy đủ, dẫn ở trên). Value-role gap nếu `entity`/node
  trong `path` bị lạm dụng làm rule input/target — **TASK-3/4/5/6** (gap tổng
  quát F1/F2, tự động đóng, không cần allowlist riêng cho process). LẠM DỤNG
  làm "kết quả thuật toán giả" khi kết hợp `weighted_sum` trên path cố định —
  **TASK-9** (computation gate — đây là cơ chế CHÍNH mà taxonomy
  `arbitrary_algorithm` mở rộng ở Task 9 Step 1 nhắm tới: "ĐỪNG ép về
  generic.rule_scene bằng cách khai sẵn các đường đi ứng viên + ô tổng trọng
  số"). Khoá case cụ thể — **TASK-7** (fixture) **/ TASK-10** (pattern reuse).

---

## 6. Lớp bug §9b → hàng nào phủ

| Lớp bug (§9b) | Hàng phủ | Bằng chứng | Task xử lý |
|---|---|---|---|
| 1. tham chiếu tồn tại nhưng SAI kiểu giá trị ngữ nghĩa | `weighted_sum` input=`edge`/`node`/…; `boolean` input=`value_box` | E6, F2 — `validator.py:330-333`/`validate.ts:290-293` chỉ kiểm tồn tại | TASK-3/5 |
| 2. giá trị thiếu lặng lẽ nhận default | `boolean`, `weighted_sum` (operand) | E2 `model.ts:186`, `generic_engine.py:25` | TASK-4/6 |
| 3. tham số thiếu lặng lẽ đổi nghĩa | `weighted_sum` (weight) | E3 `model.ts:203-204`, `generic_engine.py:38-39` | TASK-4/6 |
| 4. unresolved dependency bị lẫn với 0/false | `boolean`, `weighted_sum` (target seed) | E17 `model.ts:210`, `generic_engine.py:46` | TASK-4/6 |
| 5. object cấu trúc bị tiêu thụ như giá trị đã tính | `node`, `edge`, `moving_entity`, `label`, `container`, `group`, `heading`, `paragraph`, `text` khi làm rule input | F2, F4 | TASK-3/5 |
| 6. kết quả numeric non-finite tới được renderer | `weighted_sum` | Đọc code: không có `Infinity`/`NaN` guard ở `evalRule`/`_eval_rule` hiện tại | TASK-4/6 (`non_finite_numeric_value`) |
| 7. chu trình/chuỗi không hội tụ mà trông như thành công | `boolean`, `weighted_sum` (dependency) | Chu trình: **EXISTING** (`_detect_cycle`, đã chặn). Không-hội-tụ-sau-bound: hiện KHÔNG có typed signal (chỉ vòng lặp fixed-point dừng lặng lẽ khi hết bound, không phân biệt "hội tụ đúng" với "hết bound mà còn unresolved" — vì mọi target đã seed=0 nên LUÔN "hội tụ" về một số nào đó, kể cả sai) | TASK-4/6 (`unresolved_dependency_after_bound`) |
| 8. process thị giác bị coi là kết quả thuật toán | `move_along_path`, `reveal_sequence` (khi kết hợp `weighted_sum`/`boolean` giả) | Ca Dijkstra thật (spec §0); cấu trúc riêng của 2 process này ĐÚNG (EXISTING) — lạm dụng là vấn đề composition/routing | TASK-9 (+ TASK-7/10 khoá case) |

---

## 7. Các hàng STOP-UNRESOLVED

**Không có.** Sau khi audit toàn bộ 19 hàng (12 object + 2 rule + 1 rule-vắng-
mặt + 2 interaction + 2 process) đối chiếu trực tiếp với
`manifest.py`/`validator.py`/`generic_engine.py`/`model.ts`/`validate.ts`/
`index.ts` và test hiện có:

- Mọi câu hỏi "PHẢI trả lời bằng source" trong brief (path id thiếu, reveal
  step object thiếu, drag target sai type, toggle target không value, entity
  sai type) đều có kết quả: **validator ĐÃ chặn đúng** — không phải
  STOP-UNRESOLVED, dù một số thiếu test khoá riêng (§8, khác bản chất với lỗ
  ngữ nghĩa).
- Lỗ ngữ nghĩa THẬT duy nhất — operand/target không kiểm role
  (E6/E16/F1/F2), unresolved-lẫn-0 (E17), non-finite không chặn, lạm dụng
  process làm "kết quả thuật toán" (E7/E15) — ĐỀU đã có TASK-N cụ thể với RED
  test đặt tên trong plan (Task 2–11), không phải khoảng trống chưa ai xử lý.
- `object.weight` (F3) — **RECLASSIFY 2026-07-17: `UNSUPPORTED_SEMANTIC_FIELD`
  / TASK-2b.** Kết luận OUT-OF-SCOPE ban đầu dựa trên "không được đọc nên không
  làm lệch kết quả" — đúng về runtime nhưng **bỏ sót `manifest.py:321`**:
  contract text nạp vào prompt simulate DẠY LLM đặt `weight` lên switch. Field
  được quảng bá + validate + patch được + prompt dạy, nhưng không ai đọc =
  silent semantic no-op, đúng lớp bug M13 phải diệt (§9b). Xử lí: GỠ (Task 2b),
  không thêm ngữ nghĩa. Đây là bài học phương pháp: "không site nào ĐỌC" chưa
  đủ để kết luận vô hại — phải hỏi cả "có site nào QUẢNG BÁ/DẠY nó không".
- Nhánh ownership `toggle`↔`"value"` chưa từng kích hoạt — **OUT-OF-SCOPE**:
  code phòng thủ chưa có kịch bản, không chạy sai gì, không quảng bá gì cho
  LLM (khác hẳn F3).
- Comparison rule vắng mặt — **OUT-OF-SCOPE** có rationale (§3.3): không tồn
  tại nghĩa là không có hành vi runtime nào để audit, và Global Constraint của
  plan cấm thêm primitive DSL mới trong M13.

**Kết luận:** Luật dừng KHÔNG kích hoạt. Task 2 được phép bắt đầu theo đúng
matrix này.

---

## 8. Ghi chú kiểm thử (hành vi ĐÚNG, chỉ thiếu test khoá riêng)

Các mục dưới đây được audit trong lúc trả lời các câu hỏi bắt buộc của brief.
KHÔNG mục nào là lỗ ngữ nghĩa — code đã đọc và xác nhận đúng — nhưng thiếu một
test đặt tên riêng khoá đúng nhánh đó (khác với STOP-UNRESOLVED, vốn đòi hỏi
hành vi SAI hoặc CHƯA XÁC ĐỊNH). Liệt kê để bất kỳ Task nào chạm lại các file
này (đặc biệt Task 3, Task 5, Task 8) tiện bổ sung nếu thấy hợp lý — KHÔNG bắt
buộc trong phạm vi Task 1 (docs-only):

1. `move_along_path.path` chứa id không tồn tại hoặc không phải `node` —
   `validator.py:434-436`/`validate.ts:412-415` từ chối đúng, không có test
   riêng (chỉ có test cho `entity` sai type).
2. `move_along_path.path` độ dài ngoài [2, 12] — kiểm đúng
   (`validator.py:432-433`/`validate.ts:409-411`), không có test riêng.
3. `toggle` trên rule target — có test backend
   (`test_toggle_gia_tri_dan_xuat_bi_reject`), KHÔNG có test frontend tương
   ứng (chỉ có test cho "thiếu value").
4. `boolean.op` ngoài `{and, or, not, xor}` — kiểm đúng
   (`validator.py:336-338`/`validate.ts:296-299`), không có test riêng cho
   GIÁ TRỊ op sai (chỉ có test cho rule TYPE sai, biến khác).
5. `paragraph`/`text` thiếu `"text"` — dùng chung nhánh với `heading`
   (`TEXT_CONTENT_TYPES`), chỉ `heading` có test tên riêng
   (`test_heading_thieu_text_bi_reject`).
6. ≥2 process `reveal_sequence` hoặc ≥2 `move_along_path` trong CÙNG một spec
   — không có test khoá thứ tự/tương tác giữa chúng.
7. `edge` với `from`/`to` không tồn tại — kiểm đúng
   (`validator.py:275-278`/`validate.ts:228-235`), không tìm thấy tên test
   riêng biệt (chỉ có case dương gián tiếp qua `PACKET_SPEC`).

Ghi chú thêm (không phải test-coverage, mà là quan sát mô hình hoá — không cần
hành động trong M13, không redesign UI):

- `lamp` có role `numeric` (không chỉ `logical`) nên hợp lệ làm target của
  `weighted_sum` với giá trị bất kỳ (không chỉ 0/1); renderer (`ui.tsx:376-390`)
  vẫn hiển thị ĐÚNG số đã tính, chỉ là ẩn dụ "đèn" bị dùng cho một số tuỳ ý —
  không gây "kết quả sai trông như đúng", không redesign trong M13.
- `object.weight` (F3) là trường chết — khai báo, patch được, nhưng không bao
  giờ đọc; nếu muốn dọn (xoá field hoặc làm nó có tác dụng) là refactor hygiene
  ngoài phạm vi 2 lỗi kích hoạt milestone.

---

## 9. Tổng kết disposition

| Disposition | Số hàng | Danh sách |
|---|---|---|
| EXISTING (thuần, không kèm TASK-N) | 2 | `toggle`, `drag` |
| EXISTING + TASK-N (phần cấu trúc đúng, phần role/computation cần Task) | 16 | 12 object + `boolean` + `weighted_sum` + `reveal_sequence` + `move_along_path` |
| OUT-OF-SCOPE | 1 | comparison rule (vắng mặt) |
| STOP-UNRESOLVED | 0 | — |

**19/19 hàng có disposition** (2 + 16 + 1 = 19 — bản đầu ghi 16 thành 17, tổng
ra 20; sửa 2026-07-17). **0 hàng STOP-UNRESOLVED. Luật dừng không kích hoạt.**

### Field-level disposition (ngoài 19 hàng primitive)

| Field | Disposition | Ghi chú |
|---|---|---|
| `object.weight` | **UNSUPPORTED_SEMANTIC_FIELD / TASK-2b** | Reclassify 2026-07-17 (§7). Gỡ khỏi schema/normalization/patch-allowlist/contract-text/sample; validator từ chối config legacy chứa nó (không strip im lặng). KHÔNG thêm ngữ nghĩa trọng-số-cạnh, KHÔNG accessor. |
