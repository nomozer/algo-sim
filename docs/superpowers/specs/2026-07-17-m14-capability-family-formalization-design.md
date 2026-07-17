# M14 — Capability Family Formalization & End-to-End Pilot — DESIGN

**Trạng thái:** DRAFT — chờ user duyệt. Chưa có implementation plan, chưa có
production code.

**Đề tài (giữ nguyên chính xác):** *"Hệ thống mô phỏng tương tác 2D/3D kết hợp
LLM phân tích bài toán bằng ngôn ngữ tự nhiên hỗ trợ dạy học môn Tin học THPT"*

**North star M14–M16:** UNIFORM LLM-FACING SPEC SURFACE, HETEROGENEOUS
DETERMINISTIC EXECUTION. Mỗi public capability family có một bounded family
spec mà LLM sinh được và validator kiểm định được; phía sau spec surface,
executor/state model/renderer giữ dị biệt khi cơ chế yêu cầu. KHÔNG viết lại
executor để đồng nhất kiến trúc. M14 formalize abstraction sẵn có + MỘT pilot
end-to-end (phương án E3 — hybrid pilot-first, đã duyệt); M15 migrate catalog;
M16 comprehensive evaluation.

**Nguồn:** discovery report M14 Phase 1 (A–D) + Phase 2 (E–G) đã duyệt trong
phiên làm việc 2026-07-17; 19 quyết định chốt của user. Baseline: `main`
@ `fef4d96` (+ `2da744d` docs-only sửa hai claim lệch source).

### Revision log

**Rev 2 (2026-07-18)** — chỉnh sau review có điều kiện (6 điểm). Tóm tắt thay đổi
theo section:
- **§C (viết lại)** — mô hình multi-family. Bỏ `family_id`/`result_authority`/
  `spec_version`/`llm_facing` ĐƠN LẺ trên SimSpec; chuyển sang
  `family_memberships[]` (điểm 1). Tách hai LOẠI trong cùng một nguồn:
  *runtime SimSpec* (có module/executor) và *FAMILY_SELECTORS* (bề mặt LLM của
  family, không có executor trực tiếp). `llm_facing` trở thành DẪN XUẤT ở cấp
  "lựa chọn classify", không phải boolean tay (điểm 2).
- **§D (sửa ontology)** — `algorithm.comparison_sort` KHÔNG còn là "concrete
  runtime SimSpec"; nó là một FAMILY_SELECTOR (điểm 2). Token id chỉ xuất hiện
  ở classify enum, KHÔNG BAO GIỜ trong envelope.
- **§E4 (viết lại)** — thêm **mechanism-consistency gate** thật giữa yêu cầu
  ngữ nghĩa (analyze) và family/variant đã chọn; selection/quick sort →
  `capability_gap` vì cơ chế không executor nào sở hữu (điểm 3). Không còn để
  hở "LLM điền bừa variant" như residual risk.
- **§F3+§F5 (sửa + thêm)** — **SỬA LỖI THẬT**: doc rev1 tuyên bố "metric giữ
  nguyên định nghĩa" là SAI — harness đo output của `stage_classify`
  (`classified_ok = predicted == expect`), không phải final envelope; family
  routing ĐỔI ngữ nghĩa metric. Tách family-selection / variant-selection /
  final-route metrics (điểm 5). Thêm §F5 side-effect isolation của eval (điểm 4).
- **§C4+§F5 (làm rõ)** — `capability-descriptors.json` là artifact TEST/generated,
  KHÔNG phải production FE dependency (điểm 6).
- **§J (sửa lỗi)** — bỏ câu sai "hai case sorting trong frozen dataset" (grep xác
  nhận frozen 30-case KHÔNG có case sorting nào).

**Chỗ căng cần user để mắt (không tự quyết):** §C dùng một cấu trúc family-level
`FAMILY_SELECTORS` cạnh CATALOG. Đây là diễn giải lại NHẸ quyết định 7 ("không
tạo registry thứ hai"): FAMILY_SELECTORS giữ một *fact khác* (bề mặt LLM của
family — thứ span cả bubble+insertion, không thuộc về SimSpec concrete nào),
cross-lock với memberships để không drift. Nếu user coi đây là vi phạm decision
7, cần veto. Và §E4 mechanism gate buộc thêm MỘT tín hiệu analyze mới
(`prescribed_mechanism`) → chạm hợp đồng AI → cần live smoke (cái giá thật).

---

## A. Problem statement (đã được source chứng minh)

Kiến trúc hiện tại ĐÃ là capability architecture ngầm (registry + `SimSpec` +
hợp đồng module + manifest-derived contracts). Nó thiếu đúng năm thứ, mỗi thứ
có evidence:

1. **Spec versioning không đồng đều.** Chỉ `algorithm.scan` có version riêng
   trong schema (`scan_version` enum một giá trị, `catalog.py` `_SCAN_SCHEMA`)
   và generic có `dsl_version`. 12 entry còn lại — gồm 8 `algorithm.*` dùng
   config AnalysisOk legacy (`_ALGO_CONFIG_SCHEMA`) — không có version field.
2. **Capability metadata không machine-readable.** `family`, `executor`,
   `curriculum anchor`, `known gaps`, `reachability` chỉ sống trong
   `description` tiếng Việt của SimSpec + `docs/COVERAGE.md` — không kiểm được
   bằng test, không derive được view nào từ đó.
3. **Evaluator không chạy production lifecycle.** `evaluate_item`
   (`harness.py`) tự tái dựng chuỗi stage, KHÔNG gọi `run_pipeline`, KHÔNG gọi
   `check_computation_ownership` (0 match toàn `app/evaluation/`), KHÔNG chạy
   `check_semantic_compatibility` trong vòng retry; phân loại lỗi bằng
   string-match message tiếng Việt (`classify_error`) — đã cắn thật ở 7f.
   (CURRENT_STATE §5.1 + 7d, đã sửa lại đúng source ở `2da744d`.)
4. **Bằng chứng end-to-end cho "family spec surface" chưa tồn tại** trên một
   family chuyên biệt: LLM hiện điền config per-simulation-id; chưa từng có
   classify-chọn-family → FamilySpec → adapter → executor sẵn có.
5. **Reachability không được phân loại.** `algorithm.scan` registered +
   AI-reachable nhưng KHÔNG library-discoverable (không sample offline nào);
   4 fixture generic là internal — tất cả chỉ nhận ra được bằng đọc code, không
   có metadata.

M14 giải đúng năm thứ này, không hơn.

## B. Current architecture facts (nền tảng thiết kế — FACT từ discovery)

- **14 simulation id, parity 1:1 backend CATALOG ↔ frontend registry.**
  8 `algorithm.*` + `algorithm.scan` + `logic.and_gate` +
  `binary.decimal_to_binary` + `network.packet_routing` +
  `network.protocol_encapsulation` + `generic.rule_scene`.
- **Hai bề mặt LLM-facing đều derive từ CATALOG toàn phần:**
  `_classify_schema()` enum = `list(CATALOG.keys())` (`pipeline.py`) và
  `catalog_text()` duyệt `CATALOG.values()` (`catalog.py`). → Điểm can thiệp
  duy nhất cho classify surface là một derived filter tại hai chỗ này.
- **`run_pipeline` orchestration:** analyze → representation plan (tất định)
  → classify → computation gate (chỉ đường generic/None) → [pattern reuse
  (generic-only) | simulate: validate + scene-mode + system-flow +
  semantic-compat trong vòng retry ×3] → envelope; cache write chỉ khi ok
  (`main.py`, `CACHE_VERSION = "10"`).
- **FE hội tụ về MỘT `loadEnvelope`:** AI / offline sample / history reopen
  đều qua validateConfig (tầng 2) + `mod.init` fail-closed (M13). Envelope
  mang concrete simulation_id; đổi id nghĩa là đổi module FE.
- **Sorting hiện tại:** hai entry CATALOG (`algorithm.bubble_sort`,
  `algorithm.insertion_sort`) chung `_ALGO_CONFIG_SCHEMA` + contract; FE
  validator ép `data.order` bắt buộc; executor `runAlgorithm` (core) sinh
  trace; what-if `free`; predict theo cơ chế (M9-S1).
- **Harness:** `evaluate_item` + `_simulate_with_metrics` (mirror chép tay);
  metrics trong `EvalReport.metrics()`; suite đăng ký trong `SUITES` tuple
  (`live.py`); dataset 30 case ĐÓNG BĂNG + pools mới có luật kết nạp.

## C. Descriptor / family model

### C0. Ba khái niệm PHẢI tách rời (nền của cả §C — điểm 1, 2)

Rev1 gộp nhầm ba thứ vào "một SimSpec có family_id + llm_facing". Rev2 tách:

- **(A) Runtime target** — một mô phỏng concrete CÓ module/executor FE thật.
  Đây là thành viên của CATALOG. 14 cái hiện nay (gồm cả bubble_sort,
  insertion_sort — chúng GIỮ NGUYÊN là runtime target, quyết định 6).
- **(B) Mechanism membership** — cơ chế của một runtime target thuộc (những)
  capability family nào. Metadata phân loại thuần; một target có THỂ thuộc >1
  family với `result_authority` khác nhau (vd generic).
- **(C) LLM-facing selection choice** — thứ classifier chọn. Có HAI kiểu choice:
  (c1) một runtime target trực tiếp (generic, logic, binary, network×2, scan,
  các algorithm không-sort…); (c2) một **family selector** không có executor
  trực tiếp, luôn resolve về một runtime target qua adapter (sorting pilot).

Sai lầm rev1: coi `algorithm.comparison_sort` là (A). Đúng: nó là (c2). Nó
KHÔNG có module FE, KHÔNG BAO GIỜ là envelope id.

### C1. Nguồn sự thật: CATALOG (runtime targets) + FAMILY_SELECTORS (bề mặt LLM family)

Cả hai sống trong `catalog.py`, KHÔNG registry class mới, KHÔNG file config
riêng. Chúng giữ HAI FACT KHÁC NHAU nên không phải "hai nguồn cho một fact":

**(1) Mỗi runtime SimSpec (A) được annotate `family_memberships[]`** — thay cho
`family_id`/`result_authority`/`spec_version` đơn lẻ của rev1 (điểm 1):

```
FamilyMembership = {
  family_id:            FamilyId            # taxonomy đóng C3
  variant_id:          str | None          # vd "bubble"; None khi family không cấu trúc theo variant
  result_authority:    "computation" | "representation"
  family_spec_version: str | None          # version của bề mặt LLM family mà target này được với tới; None nếu target KHÔNG được với qua selector
}
```

Ví dụ then chốt:
- `generic.rule_scene.family_memberships = [`
  `{boolean_composition, variant_id=None, computation, family_spec_version="dsl-1"},`
  `{structural_progressive_representation, variant_id=None, representation, family_spec_version="dsl-1"}]`
  → **hai membership, result_authority khác nhau** (điểm 1 giải trực tiếp).
- `algorithm.bubble_sort.family_memberships = [{comparison_sort, variant_id="bubble", computation, family_spec_version="sort-fam-1"}]`
- `logic.and_gate.family_memberships = [{boolean_composition, None, computation, family_spec_version=None}]`
  → **cùng family với generic nhưng là capability surface RIÊNG** (quyết định
  10); `family_spec_version=None` vì and_gate không được với qua selector nào —
  nó là choice (c1) độc lập.

**(2) Metadata cấp-entry (A) — không thuộc quan hệ family:** trên mỗi SimSpec:

| Trường | Ý nghĩa | Lock |
|---|---|---|
| `executor_id` | module FE sở hữu execution (= chính simulation_id với mọi runtime target) | tồn tại trong registry FE (test, C4) |
| `reachability` | tập con của `{registered, library_discoverable, ai_reachable_public, internal_fixture}` | khớp `publicCatalog()`/registry thật (test, C4) |
| `curriculum_anchor` | tham chiếu SGK (khớp COVERAGE.md) | non-empty cho entry public |
| `known_gaps` | giới hạn trung thực | được phép rỗng |

**(3) FAMILY_SELECTORS — bề mặt LLM của family (c2).** Một mapping
`family_id → FamilySelector`, CHỈ cho family trình một selector cho LLM (M14:
đúng một cái — `comparison_sort`):

```
FamilySelector = {
  family_id:            FamilyId
  selector_token:       str                 # "algorithm.comparison_sort" — CHỈ là token classify enum, KHÔNG phải SimSpec id
  family_spec_version:  str                 # "sort-fam-1" — phải khớp memberships (lock)
  config_schema:        dict                # FamilySpec structured-output (D)
  contract:             str                 # text cho simulate
  validate_family_spec: callable            # fail-closed (D, H)
  owned_mechanisms:     tuple[MechanismId]  # cơ chế family THỰC SỰ sở hữu (E4 — đóng near-miss)
  variants:             tuple[VariantSpec]  # mỗi VariantSpec = {variant_id, concrete_simulation_id, mechanism_id}
  resolve:              callable            # FamilySpec + analysis → (concrete_id, concrete_config); tất định (E2)
}
```

FAMILY_SELECTORS giữ đúng thứ KHÔNG có nhà trên bất kỳ SimSpec concrete nào:
schema/contract/resolve span **cả bubble lẫn insertion**. Đặt nó lên một trong
hai target sẽ là tùy tiện (vì sao bubble mà không insertion?). Vì thế đây là
fact riêng, không phải bản sao của CATALOG — và được cross-lock (C4) để không
drift.

### C2. `llm_facing` là DẪN XUẤT, ở cấp "selection choice" (điểm 2)

KHÔNG có boolean `llm_facing` viết tay trên SimSpec nữa. Tập lựa chọn LLM
(classify enum + catalog_text) được DERIVE tất định:

```
llm_choices(CATALOG, FAMILY_SELECTORS) =
    { selector_token của mỗi FamilySelector }              # (c2)
  ∪ { simulation_id của runtime target t                   # (c1)
      | KHÔNG membership nào của t có family_id nằm trong FAMILY_SELECTORS }
```

- `comparison_sort` selector → token `"algorithm.comparison_sort"` vào menu.
- `bubble_sort`/`insertion_sort` bị LOẠI khỏi menu vì membership của chúng
  (`comparison_sort`) CÓ selector → chúng là runtime target ẩn sau selector.
- `generic.rule_scene` VẪN trong menu (bằng id của chính nó): các family của nó
  (boolean_composition, structural_progressive) KHÔNG có selector nào → nó là
  choice (c1). and_gate tương tự.

Hệ quả: "ẩn 2 sort khỏi classify" không phải 3 boolean tay mà là hệ quả TẤT
ĐỊNH của việc tồn tại `FAMILY_SELECTORS["comparison_sort"]`. **Rollback pilot =
gỡ đúng một entry khỏi FAMILY_SELECTORS + bump cache** → bubble/insertion tự
tái xuất hiện; không có cờ mồ côi nào để quên. Hai chỗ tiêu thụ duy nhất:
`_classify_schema()` enum và `catalog_text()`, cả hai gọi `llm_choices(...)`.

### C3. Taxonomy family (đóng, từ discovery C, tên đã chốt)

| family_id | Cơ chế | result_authority | Entry thành viên |
|---|---|---|---|
| `single_pass_scan` | quét dãy 1 lượt, accumulator/so sánh/cập nhật, dừng ≤ n | computation | find_max, find_min, sum_if, count_if, linear_search, scan |
| `interval_elimination` | loại nửa khoảng có bất biến, tiền điều kiện dãy sắp | computation | binary_search |
| `comparison_sort` | sắp xếp so-sánh, trace = compare/swap/shift | computation | runtime targets: bubble_sort (variant "bubble"), insertion_sort (variant "insertion"); bề mặt LLM = **FAMILY_SELECTOR** (không phải entry CATALOG) |
| `boolean_composition` | điểm bất động trên DAG rule boolean/weighted | computation | and_gate (surface 1), generic.rule_scene (surface 2) |
| `positional_representation` | giá trị theo vị trí bits⇄decimal | computation | decimal_to_binary |
| `graph_traversal` | BFS route + timeline chặng | computation | packet_routing |
| `layered_pdu_transform` | delta PDU qua 4 tầng cố định | computation | protocol_encapsulation |
| `structural_progressive_representation` | **Structural / Progressive Representation Family** (quyết định 9) — reveal/movement do engine dựng frame; KHÔNG được coi là executable domain computation | **representation** | generic.rule_scene (membership thứ hai) |

### C4. Derived views + consistency locks (không nguồn sự thật thứ hai)

1. **Classify view:** enum + catalog_text = `llm_choices(...)` (C2) — dẫn xuất,
   không lọc cờ tay.
2. **Descriptor export = ARTIFACT TEST/GENERATED, KHÔNG phải FE production
   dependency (điểm 6).** Generator sinh `capability-descriptors.json` (khuôn
   `dsl-contract.json` M13 — script chạy tay, commit vào repo) từ CATALOG +
   FAMILY_SELECTORS. **Người tiêu thụ CHỈ là test:** (a) test backend sync-lock
   chống trôi so với CATALOG/FAMILY_SELECTORS; (b) **test FE** đối chiếu
   `executor_id`↔registry thật và `reachability`↔`publicCatalog()`/
   `offlineCatalog()` thật. **Production FE KHÔNG import file này** — renderer
   availability đã dẫn xuất từ hợp đồng module (`renderer.ts`), FE không cần
   descriptor lúc chạy. Lock: một test (khuôn `ui-hygiene.test.ts` quét nguồn)
   cấm mọi module runtime FE import `capability-descriptors.json` → JSON chỉ
   là công cụ khóa hai chiều BE↔FE, không phải bề mặt runtime.
3. **Locks tối thiểu (offline):**
   - đủ 14 runtime target có metadata cấp-entry đầy đủ (không None/rỗng ngoài
     known_gaps) + ≥1 membership; mỗi FamilySelector có đủ trường;
   - family_id ∈ taxonomy đóng C3; mọi `variant_id` trong membership khớp một
     VariantSpec của selector cùng family (và ngược lại — song ánh variant);
   - **selector ↔ membership cross-lock:** với mỗi FamilySelector s, mọi
     `s.variants[*].concrete_simulation_id` là runtime target CÓ THẬT, có
     membership `{s.family_id, variant_id khớp, family_spec_version==s.family_spec_version}`;
     và ngược lại mọi target mang membership family có selector phải xuất hiện
     đúng một VariantSpec — chống mồ côi hai chiều (thay "llm_facing=False ⟺…"
     của rev1);
   - `mechanism_id` của mỗi VariantSpec ∈ `s.owned_mechanisms` (E4);
   - JSON export khớp CATALOG+FAMILY_SELECTORS (sync-lock BE) + khớp
     registry/publicCatalog (lock FE);
   - **parity lock công thức MỚI (CATALOG vẫn 14 entry, registry 14):** song ánh
     `{simulation_id ∈ CATALOG} ↔ {module id ∈ registry FE}` GIỮ NGUYÊN 1:1 —
     vì `comparison_sort` KHÔNG vào CATALOG (nó là selector, C0/C1). Cái mới cần
     lock là: mọi `selector_token` KHÔNG trùng bất kỳ simulation_id nào (nó là
     token ảo), và mọi `concrete_simulation_id` trong selector CÓ trong CATALOG.
     (Sửa rev1: rev1 nói "CATALOG 15 entry" — sai, do rev1 nhét selector vào
     CATALOG.)

## D. SortingFamilySpec (bounded — không field mở, quyết định 4)

**KHÔNG entry CATALOG mới.** `FAMILY_SELECTORS["comparison_sort"]` (C1.3) mang
`selector_token = "algorithm.comparison_sort"` — token này CHỈ xuất hiện trong
classify enum + catalog_text; nó KHÔNG có SimSpec, KHÔNG có module FE, và
**KHÔNG BAO GIỜ là `envelope.simulation_id`** (adapter luôn resolve về concrete
trước khi có envelope — E). Token vẫn khớp regex `^[a-z_]+\.[a-z0-9_]+$` để hợp
lệ trong enum, nhưng lock C4 cấm nó trùng bất kỳ simulation_id thật nào.

FamilySpec (structured-output LLM điền) — schema đóng hoàn toàn:

| Trường | Kiểu / miền | Bắt buộc | Ghi chú |
|---|---|---|---|
| `family_version` | enum MỘT giá trị `"sort-fam-1"` | ✓ | khuôn `scan_version` M12 — hằng import từ nơi định nghĩa spec, không viết tay ở schema (anti-pattern #1) |
| `variant` | enum `"bubble" \| "insertion"` | ✓ | thuật toán khác KHÔNG có trong enum — Gemini không thể phát |
| `array` | 2–15 số hữu hạn, đúng thứ tự đề | ✓ | cùng bound AnalysisOk hiện hành |
| `order` | enum `"asc" \| "desc"` | ✓ | |
| `labels` | mảng chuỗi cùng độ dài array | tùy chọn | contract hiện hành CÓ dùng cho sorting (đề "xếp hạng học sinh theo điểm" gắn tên với giá trị — `catalog.py` luật labels + FE validate); không bịa tên |
| `notes` | chuỗi | tùy chọn | đồng nhất mọi contract hiện có |

Không trường nào khác. **LLM không sinh result / trace / timeline / số bước /
trạng thái trung gian** — contract ghi tường minh như mọi contract hiện hành,
và mọi key ngoài schema bị validator từ chối (fail-closed, theo tiền lệ M13
Task 12b: reject, không strip im lặng).

Validator `selector.validate_family_spec` (server, tầng 1): kiểm đủ
bound/enum/độ dài labels/số hữu hạn; `family_version` đúng hằng; trả
`(config chuẩn hóa, None)` hoặc `(None, error có mã — xem H)`.

**Near-miss trong-family** (selection/quick/merge sort): enum đóng `bubble|
insertion` chặn cú pháp, nhưng đó KHÔNG đủ (điểm 3) — phòng tuyến THẬT là
mechanism-consistency gate ở E4 (cơ chế đề yêu cầu vs cơ chế family sở hữu).

## E. Lifecycle: classify → family → adapter → concrete envelope

### E1. Chuỗi đầy đủ (một đường, chèn đúng một bước mới)

```
analyze → plan → classify (menu llm_choices có token "algorithm.comparison_sort";
                            KHÔNG có 2 id sort concrete)
       → MECHANISM-CONSISTENCY GATE (E4, mới) + computation gate M13
       → simulate: LLM điền FamilySpec (D) theo selector.contract
                 → selector.validate_family_spec (tầng family, fail-closed)
                 → VARIANT-CONSISTENCY check (E4): variant khớp cơ chế đề yêu cầu?
       → ADAPTER = selector.resolve (tất định, không LLM):
             variant "bubble"    → concrete_simulation_id "algorithm.bubble_sort"
             variant "insertion" → concrete_simulation_id "algorithm.insertion_sort"
             FamilySpec → config AnalysisOk-shape hiện hành
                          {problem, data{array, labels, order}, notes}
       → validate_algorithm_config(variant_id, config)  ← TÁI DÙNG validator
         concrete hiện có → validation KÉP tự nhiên, không viết lại
       → envelope: simulation_id = CONCRETE id (quyết định 5) — token selector
         KHÔNG BAO GIỜ lọt vào envelope; config = config concrete — FE load
         module sẵn có, KHÔNG một dòng FE thay đổi
```

### E2. Adapter đặt ở đâu

Adapter LÀ `selector.resolve` (C1.3) — không phải trường trên SimSpec (vì
selector không phải SimSpec). `run_pipeline` sau classify: nếu id đã chọn là
một `selector_token` (tra FAMILY_SELECTORS) → chạy simulate với
`selector.config_schema`/`contract` → `validate_family_spec` → `resolve` (tất
định) → validate lại qua SimSpec concrete → build envelope bằng spec concrete
(`make_title` của concrete target dùng lại nguyên vẹn). Đây là CƠ CHẾ CHUNG cho
mọi family selector M15 dùng lại — dispatch bằng "id có trong FAMILY_SELECTORS
không", KHÔNG switch theo tên bài (tránh anti-pattern #2).

Adapter KHÔNG được: đọc text đề (không keyword), gọi LLM, sinh
result/timeline, đổi array/order so với spec đã validate.

### E3. Tính chất bảo toàn (lock bằng test)

- Envelope cuối **byte-tương-đương về shape** với envelope bubble/insertion
  hiện hành (config AnalysisOk) → history/cache/FE/explain không phân biệt
  được nguồn family hay nguồn cũ.
- Trace executor giữ nguyên (offline control "executor trace preservation",
  quyết định 15): cùng array/order → `runAlgorithm` sinh cùng trace như config
  cũ tương đương.
- `predict`/what-if/timeline của module FE hoạt động y nguyên (không đụng).

### E4. Mechanism-consistency gate — từ chối trung thực cho sort ngoài hỗ trợ (điểm 3, quyết định 18)

**Vấn đề rev1 để hở (điểm 3 đúng):** enum `bubble|insertion` KHÔNG chặn được
đề "hãy sắp xếp bằng Selection Sort" mà LLM điền `variant: "bubble"` — spec hợp
lệ cú pháp sẽ qua, dựng cảnh bubble sort để "minh hoạ" một cơ chế
(chọn-cực-tiểu-lặp) mà KHÔNG executor nào sở hữu. Đây đúng loại ảo giác M13
cấm. Rev1 chỉ ghi "residual risk + prompt" — không đủ.

**Nguyên tắc:** cơ chế đề YÊU CẦU phải là cơ chế family THỰC SỰ SỞ HỮU. Đây là
sibling của computation-ownership gate M13 (`result_ownership`), cùng triết lý:
tín hiệu ngữ nghĩa CÓ CẤU TRÚC từ analyze + bảng sở hữu KHAI BÁO, fail-closed,
**KHÔNG đọc text đề, KHÔNG keyword-patch tên thuật toán**.

**Tín hiệu mới ở analyze (sibling của `result_ownership`):**
`prescribed_procedure` — analyze phán đoán NGỮ NGHĨA xem đề có BẮT BUỘC một
thủ tục/cơ chế cụ thể không, và nếu có thì cơ chế đó thuộc lớp nào (đặc trưng
bằng thao tác định nghĩa, KHÔNG bằng tên):

```
prescribed_procedure ∈ {
  "none",                    # đề chỉ đòi KẾT QUẢ (vd "sắp xếp tăng dần") — không ép cơ chế
  "adjacent_compare_swap",   # đổi chỗ cặp kề (bubble sở hữu)
  "shift_into_sorted_prefix",# dời-chèn vào tiền tố đã sắp (insertion sở hữu)
  "select_extreme_repeated", # chọn cực trị lặp (selection — KHÔNG ai sở hữu)
  "partition_recursive",     # phân hoạch đệ quy (quick/merge — KHÔNG ai sở hữu)
  "other_unspecified"        # đề ép một cơ chế analyze không đặc trưng được
}   # fail-closed: thiếu/ngoài enum → xử như một cơ chế KHÔNG khớp owned (từ chối an toàn)
```

Đây KHÔNG phải keyword-patch: analyze nhận diện cơ chế bằng HIỂU NGỮ NGHĨA
(giống nó đã suy `result_ownership`, `entity_roles`…), phát ra tín hiệu có cấu
trúc; SERVER so tín hiệu đó với `owned_mechanisms` KHAI BÁO trên selector. Code
KHÔNG bao giờ quét chuỗi "selection sort" trong đề.

**Hai tầng kiểm (cả hai tất định, server-side):**

1. **Family-ownership gate — TRƯỚC simulate** (khuôn computation_gate): nếu
   classify chọn `comparison_sort` mà `prescribed_procedure` KHÔNG rỗng và
   KHÔNG nằm trong `selector.owned_mechanisms`
   (`{adjacent_compare_swap, shift_into_sorted_prefix}`) → **`capability_gap`**,
   `failure_category = capability_gap`, KHÔNG vào simulate. Selection/quick/
   merge/`other_unspecified`/thiếu đều rơi nhánh này → gap trung thực (cơ chế
   không executor sở hữu — giống Dijkstra M13).

2. **Variant-consistency check — SAU khi FamilySpec validate**: nếu
   `prescribed_procedure` ∈ owned NHƯNG variant LLM chọn không khớp cơ chế đó
   (đề đòi `shift_into_sorted_prefix` mà `variant="bubble"`) → **reject có mã
   `mechanism_variant_mismatch` → retry** (LLM sửa về đúng variant). Đây là
   sai khớp variant, KHÔNG phải gap (cơ chế VẪN được sở hữu). Check này so
   FamilySpec.variant × analysis.prescribed_procedure — **không chỉ nhìn
   FamilySpec** (đúng điểm 3: "không để validator chỉ nhìn FamilySpec rồi coi
   là đủ").

`prescribed_procedure = "none"` → cả hai tầng bỏ qua; bất kỳ variant hợp lệ
nào cũng chấp nhận (đề không ép cơ chế thì bubble hay insertion đều là minh
hoạ hợp lệ của "sắp xếp").

**Phòng tuyến prompt (bổ sung, không thay gate):** classify.md/analyze.md dạy
ranh giới bằng ví dụ trừu tượng (khuôn M12 quy tắc 2c) — nhưng gate tất định là
thứ CHỐT, không phải prompt (bài học M8-PRE S3: prompt một mình không đủ).

**Định vị trong pipeline:** tầng 1 chạy cùng chỗ `check_computation_ownership`
(sau classify, scoped vào classification là family selector hoặc generic);
tầng 2 chạy trong vòng retry của simulate (cạnh `check_semantic_compatibility`).
Cả hai phát event có mã cho observer (H) → đo được ở eval.

**Residual risk còn lại (đã thu hẹp, không còn ở variant):** nếu analyze phán
`prescribed_procedure` SAI (vd đề selection-sort mà analyze nói "none"), tầng 1
không nổ. Nhưng đây giờ là lỗi ĐO ĐƯỢC ở tầng analyze (eval near-miss bắt), tại
ĐÚNG nơi kiến trúc chịu trách nhiệm nhận diện ngữ nghĩa — không còn là "LLM
điền bừa field không ai kiểm" như rev1. Xử lý ở L.

## F. Production / evaluation convergence (invariant #22)

### F1. Bất biến mới (đăng ARCHITECTURE_MAP §5, nguyên văn đã duyệt)

> **#22 — Mọi evaluation của luồng AI tạo mô phỏng phải thực thi cùng
> production orchestration với `/api/analyze`; evaluator không được tái dựng
> riêng chuỗi analyze → classify → gate → simulate.** `/api/edit`, history và
> offline catalog không thuộc bất biến này.

### F2. Cơ chế: passive structured observer (quyết định 12)

- `run_pipeline` nhận tham số optional `observer` (mặc định None — hành vi
  production không đổi một bit). Observer là **collector thụ động**: nhận
  event có cấu trúc, không trả giá trị, không được phép ảnh hưởng quyết định
  (lock: chạy cùng input mock có/không observer → envelope giống hệt).
- Event tối thiểu (đủ tính lại mọi metric cũ): `analyze_done`,
  `gate_checked {fired, channel, reason_code}`, `classify_done
  {status, simulation_id}`, `simulate_attempt {n, rejected_by, error_code,
  message}`, `reuse {attempted, hit}`, `family_resolved {family_id,
  variant, concrete_id}`, `envelope {simulation_id, source}`.
- `evaluate_item` MỚI: gọi `run_pipeline(text, api_key, pattern_store=None,
  observer=...)` — `pattern_store=None` giữ đúng ngữ nghĩa đo compose của
  harness hiện tại. `BudgetExceeded` từ `call_gemini` truyền qua như cũ
  (reuse path không chạy khi store None nên không nuốt nhầm).
- **Kết quả:** kênh 2 của gate SỐNG trong eval lần đầu; case mà production
  từ chối bằng gate được chấm ĐÚNG là từ chối.

### F3. Metric semantics — SỬA claim sai của rev1 (điểm 5)

**Lỗi rev1:** rev1 nói "mọi metric cũ giữ NGUYÊN định nghĩa". SAI. FACT từ
source: harness hiện đo **output của `stage_classify`**, không phải final
envelope — `predicted = classification.get("simulation_id")`;
`classified_ok = predicted == item.expect_simulation_id` ([harness.py:216,225]).
Với đề được family-routing, `stage_classify` trả `"algorithm.comparison_sort"`
(token selector), trong khi `expect_simulation_id` là concrete id → nếu giữ
nguyên cách tính, metric SẼ ĐỎ oan. Ngữ nghĩa metric ĐÃ ĐỔI cho item family-
routed. Không được giấu điều này.

**Tách ba metric TÁCH BẠCH (không gộp):**
- **`family_selection_accuracy`** — `stage_classify` chọn đúng choice
  (selector token HOẶC concrete id cho item không-family). Đây là bước classify
  THẬT sau M14.
- **`variant_selection_accuracy`** — với item đi qua selector: FamilySpec.variant
  (+ adapter) resolve đúng cơ chế đề cần. Metric MỚI (M14 mới có khái niệm variant).
- **`final_route_accuracy`** — `envelope.simulation_id` (SAU adapter) ==
  `expect_simulation_id`. Đây là metric so được với `expect` của dataset.

**Ánh xạ về metric cũ, trung thực:**
- Cho item KHÔNG family-routed (mọi item hiện có, gồm cả frozen 30 — §J):
  `stage_classify` output == final envelope id → `final_route_accuracy` TRÙNG
  KHÍT `classification_accuracy` cũ về cả cách tính lẫn con số → so sánh baseline
  hợp lệ. Đây là lý do frozen dataset vẫn dùng được.
- Cho item family-routed (case sorting MỚI): "classification_accuracy" kiểu cũ
  KHÔNG áp dụng nguyên trạng — phải đọc là `final_route_accuracy` (đo envelope)
  HOẶC `family_selection_accuracy` (đo classify), hai con số KHÁC NHAU về ngữ
  nghĩa. Report ghi rõ item nào family-routed.
- **Runner mới đọc final envelope** cho `final_route_accuracy` (đây là THAY ĐỔI
  so với harness cũ vốn đọc classify output) — bắt buộc, và được lock bằng test
  parity F4 (nêu tường minh trong danh sách khác-biệt-hợp-lệ).
- `computation_gate_fired`/`mechanism_gate_fired` theo kênh: metric MỚI song
  song (đo đóng góp gate M13 kênh 2 + gate E4 — biến biết-giới-hạn 7d + điểm 3
  thành số đo được).
- `retry_count`/`spec_valid`/`failure`/`detail` map từ event `simulate_attempt`.

### F4. Parity proof rồi mới retire `_simulate_with_metrics`

1. Bước chuyển: runner mới chạy trên transcript MOCK (khuôn
   `test_evaluation.py` — monkeypatch `call_gemini` trả kịch bản ghi sẵn);
   assert metric cũ == metric `_simulate_with_metrics` trên cùng kịch bản
   (khác biệt HỢP LỆ duy nhất: case gate-refusal — trước chấm sai, nay chấm
   đúng; liệt kê tường minh trong test).
2. Sau khi parity proof xanh + suite offline xanh: **xóa
   `_simulate_with_metrics`** (quyết định 12 — retire, không giữ hai đường).
3. Fault-injection bắt buộc (khuôn audit-layout M9-UX7): một case mock mà
   classify cho qua nhưng gate chặn → report eval phải hiện từ chối; nếu ai
   đó tái dựng stage riêng bỏ qua gate → test đỏ. Đây là test khóa của #22.

### F5. Side-effect isolation của evaluation (điểm 4)

Bất biến #22 buộc eval dùng CÙNG orchestration production, nhưng eval TUYỆT ĐỐI
KHÔNG được để lại dấu vết. Chính sách side-effect tường minh:

- **Không ghi production cache.** FACT (grep xác nhận): `run_pipeline` KHÔNG
  chứa code cache — đọc/ghi `SimulationCache` sống trọn ở `main.py`/`/api/analyze`.
  Vì eval gọi THẲNG `run_pipeline` (không qua route API), nó **tự nhiên bỏ qua
  cache** — không cần no-op đặc biệt. Lock: test đếm 0 row `SimulationCache`
  mới sau một lần chạy eval.
- **Không ghi pattern store thật.** Eval mặc định gọi `run_pipeline(...,
  pattern_store=None)`; với None, cả `try_pattern_reuse` lẫn
  `persist_from_spec` đều bị guard `if pattern_store is not None` bỏ qua (FACT,
  `pipeline.py`). → 0 row `SimulationPattern`/`reuse_metrics` mới. Lock tương tự.
- **Không phụ thuộc giữa case.** `run_eval` lặp từng case độc lập; với
  `pattern_store=None` không có shared mutable state nào giữa case. Observer là
  collector TÁCH RIÊNG cho MỖI case (khởi tạo mới mỗi `evaluate_item`), không
  tích luỹ xuyên case.
- **Không đụng history/product state.** History là localStorage phía FE; backend
  eval không bao giờ chạm. `run_pipeline` không ghi history.
- **Observer passive** (F2): chỉ THU, cấm mọi side effect vào pipeline hay ra
  ngoài (lock: chạy có/không observer → envelope + mọi DB count giống hệt).
- **Suite pattern-reuse (nếu có sau này):** KHÔNG dùng `DbPatternStore`. Phải
  inject một **isolated seeded store** — in-memory/throwaway, seed pattern đã
  biết, sống trong một lần chạy, không đụng DB. Điều này giữ #22 (cùng
  orchestration) trong khi cô lập side-effect. M14 KHÔNG có suite reuse — ghi ở
  đây làm chính sách bắt buộc cho tương lai.
- **Lock tổng:** một test chạy suite eval mock rồi assert DB dev/test có ĐÚNG 0
  row mới ở cả ba bảng (`simulation_cache`, `simulation_patterns`,
  `reuse_metrics`) — biến "eval không side-effect" thành cổng đo được.

## G. Version / cache / history behavior (quyết định 14)

- `CACHE_VERSION` "10" → "11", bump ĐÚNG MỘT LẦN (classify policy đổi: menu
  family). Cache cũ miss theo cơ chế version-aware sẵn có (`_cache_lookup`
  so `policy_version`) — không xóa dữ liệu, không Alembic migration.
- `family_version = "sort-fam-1"` sống TRONG FamilySpec (khuôn
  `scan_version`); `FamilySelector.family_spec_version` + `family_spec_version`
  của mọi membership liên quan phải khớp hằng này (lock C4). Per-family cache
  invalidation: ĐỂ M15 (khi ≥2 family).
- **History:** envelope lưu là envelope CUỐI (concrete id, config concrete)
  → item cũ mở lại y nguyên, item mới không phân biệt được với item cũ; KHÔNG
  migration, KHÔNG đổi schema localStorage. Reopen vẫn qua
  validateConfig + init fail-closed (M13) — không đổi.
- **Pattern store:** không đụng (generic-only, family sorting không đi qua
  `run_gates`).

## H. Error & observability contracts (quyết định 13)

- **Structured error code là nguồn phân loại CHÍNH.** Hai mức, tối thiểu:
  - mức cổng (pipeline phát tại call-site, không sửa chữ ký validator hiện
    có): `structural_invalid`, `scene_mode_mismatch`, `system_flow_invalid`,
    `semantic_incompat`, `family_spec_invalid`, `adapter_target_invalid`,
    `gate_known_gap`, `gate_result_ownership`, `gate_mechanism_ownership`
    (E4 tầng 1 → capability_gap), `mechanism_variant_mismatch` (E4 tầng 2 →
    retry);
  - mức chi tiết (khi validator có sẵn mã — generic M13 `INVALID_SOURCE`…,
    family validator mới phát mã riêng): đính kèm trong event
    `simulate_attempt.error_code`.
- `classify_error` (harness): ưu tiên đọc `error_code`; string-match message
  tiếng Việt CHỈ còn là fallback tương thích cho transcript cũ — diệt lớp
  bug 7f tận gốc thay vì vá từng cụm chữ.
- Message tiếng Việt cho LLM retry GIỮ NGUYÊN vai trò (đó là feedback dạy
  LLM); code là kênh máy-đọc chạy song song, không thay message.
- Observer chỉ THU — cấm mọi side effect vào pipeline (lock F4).

## I. Offline / live evaluation design (quyết định 15)

### I1. Offline controls (tất cả pytest, 0 network — mock/tất định)

| # | Control | Loại test |
|---|---|---|
| 1 | bubble positive: spec hợp lệ → adapter → envelope `algorithm.bubble_sort` | pipeline mock end-to-end |
| 2 | insertion positive: tương tự → `algorithm.insertion_sort` | pipeline mock |
| 3 | paraphrase ("xếp hạng học sinh theo điểm…") có labels → spec + labels khớp độ dài | pipeline mock |
| 4 | descending: `order: "desc"` bảo toàn qua adapter | unit adapter |
| 5 | invalid bounds: array 1 phần tử / 16 phần tử / NaN → reject có mã | unit validator |
| 6 | selection-sort near-miss: analyze `prescribed_procedure="select_extreme_repeated"`, classify → comparison_sort → **mechanism gate tầng 1** → `capability_gap` (`gate_mechanism_ownership`), KHÔNG vào simulate, KHÔNG ra envelope | pipeline mock |
| 7 | quick-sort near-miss: `prescribed_procedure="partition_recursive"` → như 6 | pipeline mock |
| 7b | fail-closed gate: `prescribed_procedure` thiếu/ngoài enum + classify comparison_sort → gap (không default sang "none") | pipeline mock |
| 7c | variant-consistency (E4 tầng 2): đề `shift_into_sorted_prefix` nhưng FamilySpec `variant="bubble"` → `mechanism_variant_mismatch` → retry; retry đúng insertion → pass | pipeline mock |
| 7d | `prescribed_procedure="none"` ("sắp xếp tăng dần"): bất kỳ variant hợp lệ nào cũng qua, KHÔNG gap, KHÔNG mismatch | pipeline mock |
| 8 | invalid/unknown variant trong FamilySpec (vd "selection") → `family_spec_invalid`, không strip, không đoán | unit validator |
| 9 | adapter final simulation_id: bảng variant→id đúng, config AnalysisOk-shape qua được `validate_algorithm_config` | unit adapter |
| 10 | executor trace preservation: cùng array/order — envelope từ đường family và config cũ tương đương → `runAlgorithm` sinh trace giống hệt (vitest, so trace) | FE vitest |
| 11 | metric semantics: item family-routed → `final_route_accuracy` đọc `envelope.simulation_id` (concrete), `family_selection_accuracy` đọc classify (token) — hai số tách biệt; item non-family → hai số trùng | harness unit |
| 12 | eval side-effect isolation (F5): chạy suite mock → 0 row mới ở `simulation_cache`/`simulation_patterns`/`reuse_metrics` | harness/DB test |

Cộng: locks C4 (descriptor), F4 (parity + fault-injection + observer-passive),
E3 (envelope shape). Case eval mới vào pool `capability`/`curriculum` theo
luật kết nạp (`check_admission`), tag suite mới `m14_sorting` đăng ký vào
`SUITES` (`live.py`).

### I2. Live targeted suite (cần user duyệt ngân sách riêng — không tự chạy)

| Case | Kỳ vọng (acceptance ghi TRƯỚC khi chạy) |
|---|---|
| Bubble explicit ("sắp xếp nổi bọt dãy …") | classify → `algorithm.comparison_sort`; spec valid (≤3 attempt); envelope `algorithm.bubble_sort`; semantic: trace đúng oracle |
| Insertion explicit HOẶC paraphrase xếp hạng | tương tự → `algorithm.insertion_sort`; nếu paraphrase có tên người → labels đúng |
| Selection-sort near-miss | **honest gap**: `unsupported` (classify) hoặc `capability_gap` (gate) — TUYỆT ĐỐI không envelope generic, không bị ép bubble |

Đề xuất ngân sách (user chốt con số khi duyệt): trần ~15 HTTP call, khuôn
`--max-api-calls` + `ALLOW_LIVE_AI=1`; mọi failure ghi nhật ký live như tiền
lệ CURRENT_STATE §1. Pass = cả 3 case đạt acceptance; near-miss fail →
xử lý theo L trước khi tuyên bố COMPLETE.

## J. Migration / backward compatibility

- **FE: zero-change.** Không module/renderer/store/history nào sửa (E3).
- **Cache:** invalidate qua bump version — hành vi sẵn có, không migration.
- **History cũ:** mở lại nguyên vẹn (G).
- **Frozen dataset (30 case):** KHÔNG SỬA. **SỬA lỗi rev1**: frozen dataset
  KHÔNG có case sorting nào (grep xác nhận — chỉ có comment `capability_family`;
  rev1 nói "hai case sorting" là SAI). → không item nào trong frozen 30 bị
  family-routing; với chúng `stage_classify` output == `envelope.simulation_id`
  → `final_route_accuracy` trùng khít `classification_accuracy` cũ (F3) → số
  liệu so sánh được nguyên vẹn. Case sorting đi qua selector là case MỚI ở pool
  `capability`/`curriculum`, không đụng frozen.
- **CATALOG vẫn 14 entry / registry 14 (SỬA rev1):** `comparison_sort` là
  FAMILY_SELECTOR, KHÔNG vào CATALOG → song ánh 1:1 CATALOG↔registry GIỮ
  NGUYÊN. Parity lock cần thêm: selector_token không trùng simulation_id nào,
  concrete_simulation_id của selector có trong CATALOG (C4). Audit khi
  implement: không test hiện hành nào assert đếm 14 (đã grep — không có), nhưng
  implementation plan phải re-verify trước khi merge.
- **Rollback:** gỡ `FAMILY_SELECTORS["comparison_sort"]` + bump cache →
  bubble/insertion tự tái xuất hiện trong menu classify; không đụng executor,
  không đụng FE, envelope cũ/mới đều mở được. Descriptor + convergence GIỮ
  NGUYÊN giá trị kể cả khi rollback pilot classify.

## K. Non-goals (M14 KHÔNG làm)

- Không migrate family thứ hai (kể cả khi pilot xanh sớm — quyết định 18).
- Không gỡ hai entry sort concrete khỏi CATALOG (quyết định 6).
- Không viết lại/hợp nhất executor; không đụng `core/algorithms.ts`.
- Không hợp nhất `logic.and_gate` với generic Boolean DAG (quyết định 10).
- Không validator-contract parity cho mọi family — chỉ pilot + sync-lock
  generic sẵn có (quyết định 17); phần còn lại M15.
- Không per-family cache invalidation / Alembic migration (quyết định 14).
- Không đổi FE, renderer, 3D, DSL vocabulary, practice_activity, scope-freeze
  §5b.
- Không universal DSL; không module riêng cho từng đề; không Dijkstra.
- Không claim toàn catalog generation (quyết định 19) — phát ngôn được phép
  sau M14: *"kiến trúc capability-spec đã được chứng minh end-to-end trên MỘT
  family (sorting) với LLM thật"*, CẤM nói "toàn catalog đã chạy qua family
  spec".

## L. Failure modes & stop conditions

| Failure mode | Phát hiện bằng | Xử lý |
|---|---|---|
| Classify sụp trên menu mới (selector token làm lệch các id khác) | live smoke 3 case + offline mock | DỪNG, rollback = gỡ `FAMILY_SELECTORS["comparison_sort"]` + bump cache (C2), báo user — không đuổi theo bằng prompt-patch quá 1 vòng (bài học M8-PRE S3 salience) |
| LLM chọn `variant` không khớp cơ chế đề (đề insertion, điền bubble) | E4 tầng 2 (variant-consistency) | `mechanism_variant_mismatch` → retry; hết retry → 422 trung thực (không ship cảnh sai cơ chế) |
| Sort ngoài hỗ trợ (selection/quick) lọt tới simulate | E4 tầng 1 (mechanism-ownership gate) | `capability_gap` TRƯỚC simulate — không còn là residual risk như rev1 |
| analyze phán SAI `prescribed_procedure` (đề selection nhưng nói "none") | eval near-miss (offline 6/7 + live) | lỗi Ở TẦNG ANALYZE, đo được; nếu tái diễn ổn định → siết analyze.md bằng ví dụ (1 vòng), KHÔNG keyword-patch tên thuật toán trong code |
| Parity proof harness ĐỎ (metric lệch ngoài danh sách khác-biệt-hợp-lệ) | test F4 | DỪNG retire; giữ `_simulate_with_metrics` cho tới khi giải thích được từng lệch — không merge convergence nửa vời |
| Observer làm đổi hành vi pipeline | lock observer-passive (mock, so envelope) | thiết kế lại observer; đây là blocker merge |
| Adapter output không qua được validator concrete | offline control 9 | bug adapter — sửa trước mọi bước sau |
| Ngân sách live vượt trần | `ApiBudget` sẵn có | dừng sạch, in report, báo user (không tự tăng trần) |
| Phát hiện thêm drift production/eval ngoài danh mục D3 | trong lúc implement convergence | báo user trước khi mở rộng phạm vi sửa (chống scope creep) |

Stop-conditions kế thừa từ khung M14 (catalog lệch docs, executor không sở
hữu canonical result, family không bounded-được, milestone phình thành
migration toàn catalog…) vẫn hiệu lực nguyên vẹn.

## M. COMPLETE criteria (quyết định 18 — dạng kiểm được)

1. Descriptor cấp-entry + `family_memberships[]` + FAMILY_SELECTORS đầy đủ;
   consistency locks C4 (gồm cross-lock selector↔membership, song ánh 1:1
   CATALOG↔registry vẫn 14) XANH.
2. Classify chọn được token `algorithm.comparison_sort` qua `llm_choices(...)`
   (mock + live); hai id sort concrete không còn trong menu LLM nhưng còn
   nguyên là runtime target; token selector KHÔNG BAO GIỜ là envelope id.
3. `validate_family_spec` fail-closed, có error code.
4. Adapter (`selector.resolve`) resolve đúng bảng variant→concrete; envelope
   cuối mang concrete id.
5. Executor/renderer/FE không đổi (diff FE = 0 ngoài test); production FE KHÔNG
   import `capability-descriptors.json` (lock C4).
6. **Mechanism-consistency gate (E4)**: selection/quick → `capability_gap`
   (tầng 1); variant sai cơ chế → `mechanism_variant_mismatch`→retry (tầng 2);
   `prescribed_procedure="none"` không chặn oan — tất cả có test (I1 6/7/7b/7c/7d).
7. Production và evaluation dùng CHUNG `run_pipeline` (invariant #22 đăng
   ARCHITECTURE_MAP + fault-injection proof); `_simulate_with_metrics` đã
   XÓA sau parity proof; eval side-effect isolation (F5) có lock 0-row.
8. Metric tách bạch family-selection / variant-selection / final-route (F3);
   report ghi rõ item family-routed; frozen 30 case không sửa, số liệu so sánh
   được (final-route trùng classification cũ cho item non-family).
9. Offline controls I1 (12 mục) + locks xanh; pytest/vitest/build sạch.
10. Live targeted suite (I2) đạt acceptance đã ghi trước; nhật ký live ghi vào
    CURRENT_STATE §1.
11. Sort ngoài hỗ trợ → capability_gap, KHÔNG fallback generic (case 6/7
    offline + near-miss live).
12. Không family thứ hai bị migrate; docs checkpoint (CURRENT_STATE hàng §2,
    ARCHITECTURE_MAP #22, COVERAGE nếu chạm phát ngôn) cập nhật trung thực.

## N. Open implementation questions (để implementation plan trả lời — KHÔNG
chặn design)

1. **Hình thức mở rộng SimSpec:** thêm keyword-args mặc định vào `__init__`
   hiện có hay dataclass hóa — chọn theo diff nhỏ nhất khi implement.
2. **Observer API:** danh sách event append vào collector object đơn giản vs
   callback protocol — chọn theo khả năng test parity dễ nhất; ràng buộc cứng
   duy nhất: passive + optional + không đổi hành vi khi None.
3. **Độ mịn error code mức chi tiết:** M14 chỉ cần mức cổng (H) là đủ cho
   parity + categorization; mức chi tiết cho validator legacy (algorithm/
   network/binary/logic) có thể để M15 — xác nhận khi viết `classify_error`
   mới.
4. **Vị trí `FamilySelector` (schema/contract/resolve/owned_mechanisms/
   variants) + hằng `family_version`:** module backend mới
   (`simulation/families/…`?) hay trong catalog.py cạnh FAMILY_SELECTORS —
   chọn theo nguyên tắc một-nguồn (schema/contract/descriptor cùng import một chỗ).
5. **Granularity enum `prescribed_procedure` (E4):** năm lớp cơ chế ở E4 là đủ
   cho pilot sorting; có nên tổng quát hoá thành taxonomy cơ chế dùng chung
   nhiều family (sibling của SEMANTIC_ROLES) ngay M14 hay để M15 khi có family
   thứ hai cần nó? Mặc định: giữ hẹp cho sorting trong M14, thiết kế field sao
   cho mở rộng được. (`llm_facing` KHÔNG còn là câu hỏi mở — đã chốt: dẫn xuất
   từ `llm_choices`, C2.)
6. **Tên suite live + vị trí case:** `m14_sorting` trong pool `capability`
   (mặc định) hay `curriculum` — chốt khi viết case theo luật kết nạp.
7. **`prescribed_procedure` thêm vào ANALYZE_SCHEMA — bắt buộc hay nullable
   fail-closed?** Song song `result_ownership` (required, fail-closed). Mặc
   định: nullable + fail-closed (thiếu → xử như không khớp owned, E4 tầng 1) để
   không phá analyze của mọi domain khác; xác nhận khi chạm schema.
