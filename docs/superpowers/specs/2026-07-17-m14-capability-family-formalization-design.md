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

### C1. CapabilityDescriptor — đặt Ở ĐÂU (quyết định 7: không registry mới)

Descriptor là **trường mở rộng của chính `SimSpec`** trong `catalog.py` — không
class registry mới, không dict song song, không file cấu hình riêng. CATALOG
tiếp tục là nguồn sự thật duy nhất phía backend; mọi view (classify enum,
catalog_text, descriptor export) DERIVE từ nó.

Trường descriptor tối thiểu trên mỗi SimSpec (đủ 14 entry hiện có + entry
family mới — quyết định 8, 16):

| Trường | Kiểu | Ý nghĩa | Ràng buộc lock |
|---|---|---|---|
| `families` | tuple các FamilyMembership | entry thuộc (những) family nào | ≥1; family_id thuộc taxonomy đóng (C3) |
| `executor_id` | str | module FE sở hữu execution (concrete id; với family entry: xem `variants`) | phải tồn tại trong registry FE (lock qua JSON export, C4) |
| `reachability` | enum | `registered` / `library_discoverable` / `ai_reachable_public` / `internal_fixture` — tập giá trị, một entry có thể mang nhiều mức | khớp thực tế FE (lock qua JSON export) |
| `spec_version` | str | version của config/spec surface entry này (vd `"algo-legacy-1"`, `"scan-1"` = SCAN_VERSION, `"dsl-1"` = DSL, `"sort-fam-1"`) | non-empty; family entry: khớp `family_version` trong schema |
| `curriculum_anchor` | str | tham chiếu SGK/chương trình (khớp COVERAGE.md) | non-empty cho mọi entry public |
| `known_gaps` | tuple[str] | giới hạn trung thực (vd encap: handshake/phân mảnh) | được phép rỗng |

`FamilyMembership = {family_id, result_authority, variant_id?}` với
`result_authority ∈ {computation, representation}`. Lý do membership là danh
sách: `generic.rule_scene` thuộc HAI family (F4 boolean composition —
computation; F8 representation); `logic.and_gate` thuộc F4 như một capability
surface riêng, KHÔNG hợp nhất với generic trong M14 (quyết định 10).

**Runtime FamilySpec KHÔNG chứa curriculum metadata** (quyết định 8): mọi
trường trên là catalog-side; spec LLM sinh chỉ có bounded instance input (D).

### C2. Trường điều khiển bề mặt LLM: `llm_facing`

Thêm một trường dẫn xuất-được-kiểm `llm_facing: bool` trên SimSpec:
- `True` cho 12 entry hiện tại (trừ 2 sort) + entry family sorting mới;
- `False` cho `algorithm.bubble_sort` và `algorithm.insertion_sort` — chúng
  vẫn nằm TRONG CATALOG làm **runtime target** (quyết định 6): validator +
  make_title + envelope id vẫn dùng; chỉ biến mất khỏi menu của classify.

Hai chỗ tiêu thụ (duy nhất): `_classify_schema()` enum và `catalog_text()`
lọc theo `llm_facing`. Không chỗ nào khác đọc trường này. Rollback pilot =
đảo 3 giá trị boolean + bump cache — bán kính nhỏ nhất có thể (L).

### C3. Taxonomy family (đóng, từ discovery C, tên đã chốt)

| family_id | Cơ chế | result_authority | Entry thành viên |
|---|---|---|---|
| `single_pass_scan` | quét dãy 1 lượt, accumulator/so sánh/cập nhật, dừng ≤ n | computation | find_max, find_min, sum_if, count_if, linear_search, scan |
| `interval_elimination` | loại nửa khoảng có bất biến, tiền điều kiện dãy sắp | computation | binary_search |
| `comparison_sort` | sắp xếp so-sánh, trace = compare/swap/shift | computation | **family entry mới** + bubble_sort, insertion_sort (variant) |
| `boolean_composition` | điểm bất động trên DAG rule boolean/weighted | computation | and_gate (surface 1), generic.rule_scene (surface 2) |
| `positional_representation` | giá trị theo vị trí bits⇄decimal | computation | decimal_to_binary |
| `graph_traversal` | BFS route + timeline chặng | computation | packet_routing |
| `layered_pdu_transform` | delta PDU qua 4 tầng cố định | computation | protocol_encapsulation |
| `structural_progressive_representation` | **Structural / Progressive Representation Family** (quyết định 9) — reveal/movement do engine dựng frame; KHÔNG được coi là executable domain computation | **representation** | generic.rule_scene (membership thứ hai) |

### C4. Derived views + consistency locks (không nguồn sự thật thứ hai)

1. **Classify view:** enum + catalog_text lọc `llm_facing` (C2).
2. **Descriptor export:** generator sinh `capability-descriptors.json` (khuôn
   `dsl-contract.json` M13 — script chạy tay, commit vào repo). Người tiêu
   thụ: (a) test backend sync-lock chống trôi so với CATALOG; (b) **test FE**
   đối chiếu `executor_id` với registry thật và `reachability` với
   `publicCatalog()`/`offlineCatalog()` thật — đây là cách duy nhất khóa
   metadata backend vào thực tế frontend mà không tạo nguồn thứ hai (JSON là
   BẢN SINH, không phải bản viết tay).
3. **Locks tối thiểu (offline):**
   - đủ 14+1 entry có descriptor đầy đủ (không None/rỗng ngoài known_gaps);
   - family_id ∈ taxonomy đóng C3; mỗi entry ≥1 membership;
   - `llm_facing=False` ⟺ entry là runtime-target của một family entry có
     variant trỏ tới nó (không mồ côi);
   - JSON export khớp CATALOG (sync-lock backend) + khớp registry/publicCatalog
     (lock FE);
   - **parity lock công thức MỚI:** mọi FE module id có đúng một entry CATALOG
     `llm_facing` bất kỳ; mọi entry CATALOG hoặc là FE module id, hoặc là
     family entry mà TẤT CẢ variant resolve về FE module id có thật. (Thay
     công thức 1:1 cũ — CATALOG nay 15 entry, registry vẫn 14.)

## D. SortingFamilySpec (bounded — không field mở, quyết định 4)

Entry CATALOG mới: `simulation_id = "algorithm.comparison_sort"` (khớp regex
`^[a-z_]+\.[a-z0-9_]+$`), `llm_facing=True`, domain `algorithm`.

Schema structured-output (đóng hoàn toàn):

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

Validator `validate_sorting_family_spec` (server, tầng 1): kiểm đủ
bound/enum/độ dài labels/số hữu hạn; `family_version` đúng hằng; trả
`(config chuẩn hóa, None)` hoặc `(None, error có mã — xem H)`.

**Near-miss trong-family** (selection/quick/merge sort): KHÔNG biểu diễn được
trong spec (enum đóng) — phòng tuyến ở E4.

## E. Lifecycle: classify → family → adapter → concrete envelope

### E1. Chuỗi đầy đủ (một đường, chèn đúng một bước mới)

```
analyze → plan → classify (menu có "algorithm.comparison_sort";
                            KHÔNG có 2 id sort concrete)
       → computation gate (không đổi — vẫn scoped generic/None)
       → simulate: LLM điền SortingFamilySpec theo contract D
                 → validate_sorting_family_spec (tầng family)
       → ADAPTER (tất định, mới):
             variant "bubble"    → simulation_id "algorithm.bubble_sort"
             variant "insertion" → simulation_id "algorithm.insertion_sort"
             FamilySpec → config AnalysisOk-shape hiện hành
                          {problem, data{array, labels, order}, notes}
       → validate_algorithm_config(variant_id, config)  ← TÁI DÙNG validator
         concrete hiện có → validation KÉP tự nhiên, không viết lại
       → envelope: simulation_id = CONCRETE id (quyết định 5), config =
         config concrete — FE load module sẵn có, KHÔNG một dòng FE thay đổi
```

### E2. Adapter đặt ở đâu

Trường optional mới trên SimSpec của family entry (vd `resolve(config,
analysis) → (concrete_id, concrete_config)`), `None` với mọi entry thường.
`run_pipeline` sau khi validate config: nếu spec có `resolve` → gọi (tất
định, không LLM) → validate lại qua SimSpec concrete → build envelope bằng
spec concrete (`make_title` của concrete entry dùng lại nguyên vẹn). Đây là
CƠ CHẾ CHUNG cho mọi family entry M15 dùng lại — không phải nhánh if theo id
(tránh anti-pattern switch-theo-tên-bài).

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

### E4. Từ chối trung thực cho sort ngoài hỗ trợ (quyết định 18)

Hai phòng tuyến, đều đã có tiền lệ:
1. **Classify:** contract mô tả family ghi rõ chỉ bubble/insertion; classify.md
   dạy biến thể khác (selection/quick/merge/heap) → `unsupported` (khuôn
   M12 quy tắc 2c + `cur-t12-tcp-advanced`).
2. **Computation gate (đã có, không sửa):** nếu classify chệch một đề
   selection-sort về generic, `result_ownership="algorithmic"` → kênh 2 chặn
   → `capability_gap`. "Unsupported sort không fallback generic" được test
   bằng case near-miss (I).

Giới hạn thừa nhận: nếu classify chọn family entry cho đề selection-sort và
LLM điền bừa `variant: "bubble"`, spec hợp lệ cú pháp sẽ qua — phòng tuyến là
prompt + eval case, không phải validator (validator không đọc đề — đúng
nguyên tắc không keyword-patch). Ghi nhận ở L như residual risk có đo.

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

### F3. Metric: giữ cũ + song song (tiền lệ M7.14T)

- Mọi metric cũ giữ NGUYÊN định nghĩa, tính từ event log (so sánh được
  baseline). `gap_gate_fired` cũ (kênh 1, từ plan) giữ nguyên cách tính.
- Metric mới song song: `computation_gate_fired` theo kênh (đo đóng góp kênh
  2 — biến biết-giới-hạn 7d thành số đo được).
- `retry_count`/`spec_valid`/`failure`/`detail` map từ `simulate_attempt`.

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

## G. Version / cache / history behavior (quyết định 14)

- `CACHE_VERSION` "10" → "11", bump ĐÚNG MỘT LẦN (classify policy đổi: menu
  family). Cache cũ miss theo cơ chế version-aware sẵn có (`_cache_lookup`
  so `policy_version`) — không xóa dữ liệu, không Alembic migration.
- `family_version = "sort-fam-1"` sống TRONG FamilySpec (khuôn
  `scan_version`); descriptor `spec_version` của family entry phải khớp hằng
  này (lock C4). Per-family cache invalidation: ĐỂ M15 (khi ≥2 family).
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
    `gate_known_gap`, `gate_result_ownership`;
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
| 6 | selection-sort near-miss: classify mock trả unsupported HOẶC generic → gate kênh 2 chặn — cả hai nhánh đều KHÔNG ra envelope | pipeline mock 2 nhánh |
| 7 | quick-sort near-miss: như 6 | pipeline mock |
| 8 | invalid/unknown variant (vd "selection") → `family_spec_invalid`, không strip, không đoán | unit validator |
| 9 | adapter final simulation_id: bảng variant→id đúng, config AnalysisOk-shape qua được `validate_algorithm_config` | unit adapter |
| 10 | executor trace preservation: cùng array/order — envelope từ đường family và config cũ tương đương → `runAlgorithm` sinh trace giống hệt (vitest, so trace) | FE vitest |

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
- **Frozen dataset (30 case):** KHÔNG SỬA. Hai case sorting hiện chấm theo
  final envelope (runner hội tụ đọc `envelope.simulation_id` — vẫn là concrete
  id sau adapter) → kỳ vọng cũ đúng nguyên vẹn, số liệu so sánh được.
- **CATALOG 15 entry / registry 14:** parity lock công thức mới (C4). Audit
  khi implement: không test hiện hành nào assert đếm 14 (đã grep — không có),
  nhưng implementation plan phải re-verify trước khi merge.
- **Rollback:** đảo `llm_facing` 3 entry + bump cache — không đụng executor,
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
| Classify sụp trên menu mới (family entry làm lệch các id khác) | live smoke 3 case + offline mock | DỪNG, rollback `llm_facing`, báo user — không đuổi theo bằng prompt-patch quá 1 vòng (bài học M8-PRE S3 salience) |
| LLM điền bừa `variant` cho sort ngoài hỗ trợ | live near-miss case | ghi nhận residual risk; nếu tái diễn ổn định → đề xuất carve-out analyze (tất định) ở milestone sau, KHÔNG keyword-patch trong M14 |
| Parity proof harness ĐỎ (metric lệch ngoài danh sách khác-biệt-hợp-lệ) | test F4 | DỪNG retire; giữ `_simulate_with_metrics` cho tới khi giải thích được từng lệch — không merge convergence nửa vời |
| Observer làm đổi hành vi pipeline | lock observer-passive (mock, so envelope) | thiết kế lại observer; đây là blocker merge |
| Adapter output không qua được validator concrete | offline control 9 | bug adapter — sửa trước mọi bước sau |
| Ngân sách live vượt trần | `ApiBudget` sẵn có | dừng sạch, in report, báo user (không tự tăng trần) |
| Phát hiện thêm drift production/eval ngoài danh mục D3 | trong lúc implement convergence | báo user trước khi mở rộng phạm vi sửa (chống scope creep) |

Stop-conditions kế thừa từ khung M14 (catalog lệch docs, executor không sở
hữu canonical result, family không bounded-được, milestone phình thành
migration toàn catalog…) vẫn hiệu lực nguyên vẹn.

## M. COMPLETE criteria (quyết định 18 — dạng kiểm được)

1. Descriptor đầy đủ + consistency locks XANH cho toàn bộ entry (14 + family).
2. Classify chọn được `algorithm.comparison_sort` (mock + live); hai id sort
   concrete không còn trong menu LLM nhưng còn nguyên trong CATALOG.
3. `validate_sorting_family_spec` hoạt động fail-closed, có error code.
4. Adapter resolve đúng bảng variant→concrete; envelope cuối mang concrete id.
5. Executor/renderer/FE không đổi (diff FE = 0 ngoài test).
6. Production và evaluation dùng CHUNG `run_pipeline` (invariant #22 đăng
   ARCHITECTURE_MAP + fault-injection proof); `_simulate_with_metrics` đã
   XÓA sau parity proof.
7. Frozen dataset 30 case không sửa; số liệu chạy qua runner mới so sánh được.
8. 10 offline controls (I1) + locks xanh; pytest/vitest/build sạch.
9. Live targeted suite (I2) đạt acceptance đã ghi trước; nhật ký live ghi vào
   CURRENT_STATE §1.
10. Sort ngoài hỗ trợ → unsupported/capability_gap, KHÔNG fallback generic
    (case 6/7 offline + near-miss live).
11. Không family thứ hai bị migrate; docs checkpoint (CURRENT_STATE hàng §2,
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
4. **Vị trí hằng `family_version` + bảng variant→id:** module backend mới
   (`simulation/families/…`?) hay trong catalog.py cạnh entry — chọn theo
   nguyên tắc một-nguồn (schema/contract/descriptor cùng import một chỗ).
5. **`llm_facing` vs dẫn xuất từ reachability:** trường riêng (tường minh,
   dễ rollback) hay suy từ metadata khác — mặc định trường riêng, xác nhận
   khi viết locks.
6. **Tên suite live + vị trí case:** `m14_sorting` trong pool `capability`
   (mặc định) hay `curriculum` — chốt khi viết case theo luật kết nạp.
