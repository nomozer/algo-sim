# N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION

**2026-09-21** · nhánh `feat/photo-problem-to-scene` · START_HEAD `cac49a0` ·
commit registry + công cụ `330334a` · `main` giữ `085cae6` ·
**0 request Gemini · 0 request mạng**

```text
N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION = PASS
REGISTRY v1   52bc6379…  trùng byte ở mọi revision (tạo ở 25c3f5b, không commit nào khác chạm)
REGISTRY v2   OVERLAY 03a87ba3…, chỉ ghi đè N04, đăng ký TRƯỚC mọi request sau bản sửa
N04 đọc đúng  SAFE_REJECTION · ORIGINAL_PREREPAIR_EXPECTATION_RESULT = NO
                             · POST_REPAIR_REGRESSION_EXPECTATION_RESULT = YES
PHÂN LOẠI CHÍNH  không đổi — trần lượt retry vẫn NOT_READY (cụm P03/P05)
CANDIDATE     077dbc6b… → 077dbc6b…      CACHE_VERSION 99 → 99
```

## 1. Vì sao cần v2

Registry v1 (`completion-runner-repair-offline/NEGATIVE_TARGETED_REJECTION_REGISTRY.json`)
ghim N04 `allowed_exact_codes = ["INVALID_CONFLICT"]`. Lúc đăng ký, đó là mã mâu
thuẫn duy nhất tồn tại. Nhưng `INVALID_CONFLICT` là **trạng thái adapter**, không
phải **mã từ chối**. Sau `STRUCTURED_RELATION_SAFETY_REPAIR`, N04 đọc đúng bị bác
ở FactGraph với mã `STRUCTURED_RELATION_CONTRADICTION`, nên nó ra
`SAFE_REJECTION = YES` mà `TARGETED_REJECTION_MATCH = NO`. Chỉ số ấy chấm sai một
hành vi đúng.

Sửa v1 là viết lại một kỳ vọng đã đăng ký sau khi đã thấy kết quả. Nên v1 **giữ
nguyên byte** và vẫn là kỳ vọng gốc trước sửa. v2 là một **overlay** đăng ký
trước mọi request sau bản sửa, và bộ đo báo **cả hai** kết quả, riêng rẽ.

## 2. Hợp đồng overlay

`n04-targeted-rejection-registry-v2-preregistration/NEGATIVE_TARGETED_REJECTION_REGISTRY_V2.json`:

- trỏ base bằng đường dẫn + SHA-256 (LF) + git blob + commit tạo;
- ghim commit hành vi `cac49a0` và candidate `077dbc6b…`, cùng băm manifest và
  ground truth;
- `allowed_override_case_ids = ["N04"]`; chính sách **đóng**, bộ nạp đối chiếu cả
  hằng `CHO_PHEP_GHI_DE` trong mã;
- N04 → `dataset_role = DEVELOPMENT_REGRESSION_CASE` và một tuple **chính xác**:

| trường | kỳ vọng | đọc từ bản ghi runner |
|---|---|---|
| adapter_status | `INVALID_CONFLICT` | `BUILD.ADAPTER_STATUS` |
| rejection_code | `STRUCTURED_RELATION_CONTRADICTION` | `REJECTION_CODE` |
| rule_id | `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE` | `BUILD.ADAPTER_RULE_ID` |
| rejection_phase | `FACT_GRAPH` | `BUILD.ADAPTER_PHASE` |
| compiler_reached | false | `COMPILER_ELIGIBILITY ∉ {null, NO_GRAPH}` |
| program_created | false | `COMPILE_STATUS == COMPILED` |
| scene_created | false | `SCENE_NON_EMPTY` |
| final_memory_created | false | `PYDANTIC_PROGRAM_VALIDATION == PASS` |
| answer_created | false | `FINAL_MEMORY_OK` |

Pha lấy từ **mã** ở `cac49a0`: `fact_graph._kiem_nhieu_dinh_vuong` phát
`("PHASE", "FACT_GRAPH")` trong bằng chứng, và adapter chuyển nó vào
`KetQuaAdapter.evidence`. Không đặt tên pha mới.

`TARGETED_REJECTION_V2 = YES` khi và chỉ khi:

- thông tin tối thiểu đủ (cùng luật v1);
- không có quan hệ cấm dùng được;
- **mọi** trường của tuple quan sát bằng kỳ vọng.

Không có danh sách mã rộng. Bản ghi thiếu trường tuple ra `NOT_MEASURED`: bộ đo
không đoán và không mượn kết quả v1. Với ca không bị ghi đè, v2 ≡ v1 trên entry v1
trùng byte.

## 3. Bộ nạp và ràng buộc của runner

`aggregate_multicase_completion.doc_registry_tu_choi_v2` là tất định và
**fail closed**. Mọi lỗi ra `LoiRegistry(ma)` với mã ổn định, không bao giờ lùi
về v1:

- `REGISTRY_V2_MISSING` · `OVERLAY_VERSION_INVALID`
- `BASE_REGISTRY_MISSING` · `BASE_REGISTRY_HASH_MISMATCH`
- `PRODUCT_HEAD_INVALID`: commit không tồn tại, không phải tổ tiên HEAD, hoặc
  không mang `LUAT_NHIEU_DINH_VUONG`
- `DATASET_HASH_MISMATCH`
- `OVERRIDE_CASE_NOT_IN_BASE` · `OVERRIDE_CASE_NOT_ALLOWED`
- `REQUIRED_FIELD_MISSING` · `DATASET_ROLE_INVALID` · `INPUT_HASH_MISMATCH`
- `DUPLICATE_OVERRIDE` · `DUPLICATE_KEY`

`run_multicase_benchmark.kiem_rang_buoc_registry()` chạy sau kiểm khoá, **trước**
hàng đợi và request đầu tiên. Nó thêm hai điều chỉ runner cần:

- overlay phải **đã commit và trùng HEAD** (`REGISTRY_V2_NOT_COMMITTED`);
- mã sản phẩm phải khớp candidate đã khai (`PRODUCT_CANDIDATE_DRIFT`).

Nếu hỏng, runner ghi `PRECHECK_REGISTRY_BINDING.json` rồi trả `EXIT_PRECHECK`,
0 request. Nếu xanh, `REGISTRY_BINDING.json` được ghi trước request đầu tiên và
kết quả completion mang `TARGETED_REGISTRY`.

**Bằng chứng ràng buộc** (`main()` thật, transport giả):

- **đường xanh**: binding đã có khi request đầu tiên tới, rồi đủ 6 request;
- **bảy kịch bản hỏng**: overlay ngoài kho · overlay trong kho nhưng lệch HEAD ·
  overlay vắng · N04 còn holdout · commit hành vi thiếu bản sửa · thiếu trường
  tuple · candidate trôi. **Cả bảy** dừng với 0 request, mỗi kịch bản mang đúng mã
  của nó.

## 4. Kết quả

**N04, cùng hành vi sản phẩm `cac49a0`; chỉ bộ đo đổi:**

| đầu vào | SAFE | v1 (gốc, trước sửa) | v2 (hồi quy, sau sửa) | trường tuple lệch |
|---|---|---|---|---|
| đọc đúng | true | NO | **YES** | — |
| phản hồi `{}` | true | NO | NO | `rejection_code`, `rule_id`, `rejection_phase` |

Kết quả v1 không đổi từ START sang END. Ma trận test N04 (tất cả xanh ở `330334a`):

- **A** đọc đúng ⇒ v1 NO, v2 YES;
- **B** `{}` ⇒ an toàn nhưng v2 NO (thiếu thông tin);
- **C–F** sai mã · sai rule · compiler được gọi · có chương trình/cảnh/memory ·
  sai pha ⇒ mỗi lệch đều cho v2 NO;
- **G** hợp đồng chỉ một góc vuông ⇒ compiler chạy, v2 NO, không an toàn.

**N01–N03:** v2 = v1 cho cả đọc đúng và `{}`, và vai trò vẫn là
`DEVELOPMENT_HOLDOUT_PILOT`. Lớp đính chính N01 giữ nguyên.

**Request parity START ↔ END.** Cùng 6 thân request trùng byte, cùng thứ tự
`P06 P07 P08 N02 N03 N04`, và cả hai khớp `EXPECTED_REQUEST_HASHES.json`.
`MAX_HTTP_REQUESTS = 6`. Không chuỗi registry nào lọt vào thân request. Prompt,
schema, model, temperature và ngân sách transport đều không đổi.

**Phân loại chính không đổi.** Trên cùng đầu vào (chỉ lịch sử; lịch sử + completion
tổng hợp), START và END trùng nhau ở:

- `CLASSIFICATION`, `NEXT_ACTION`;
- `COUNTS`, `CLUSTERS`;
- mọi chỉ số ngoài `TARGETED*`.

Cụm `MODEL_MALFORMED_RELATION = [P03, P05]` còn nguyên (ngưỡng ≥ 2 ca không đổi),
nên trần của lượt retry vẫn là **`NOT_READY`**.

## 5. Kiểm chứng

- **Red → green.** Test viết trước công cụ: 36 ca. Ở `cac49a0` có
  **33 đỏ / 3 xanh**; ba ca xanh là khoá v1 trùng byte, khoá overlay và lớp đính
  chính N01, tức ba bất biến có từ trước. Ở `330334a`: **36/36 xanh**.
- **Tiêm lỗi 13/13 bị bắt**, hoàn nguyên trùng byte, worktree sạch sau đó:
  - đổi một byte v1 (48 test đỏ);
  - bộ nạp bỏ kiểm băm base · bỏ kiểm commit hành vi · nhận N04 là holdout;
  - bộ chấm v2 bỏ qua `rejection_code` · bỏ qua `rule_id`;
  - runner âm thầm lùi về v1 trước request · runner chấm v2 bằng kết quả v1;
  - bộ tổng hợp lùi về v1 khi v2 hỏng;
  - runner bỏ kiểm overlay đã commit · bỏ kiểm candidate;
  - overlay đổi kỳ vọng về `INVALID_CONFLICT`;
  - ca không bị ghi đè chấm lại v2 thay vì kế thừa v1.

  Mười một phép chỉ bị **1–2 test** bắt; `FAULT_INJECTIONS.json` liệt kê từng test.
- **Suite liên quan:** 154/154, gồm `completion_runner_repair`,
  `multicase_benchmark` và hai suite quan hệ có cấu trúc.
- **Full backend:** 5771 passed ở START; **5807 passed, 0 failed** ở `330334a`
  (worktree sạch).
- **Candidate** `--verify` PASS `077dbc6b…` (103 tệp). `CACHE_VERSION` 99. 0 tệp
  sản phẩm đổi.

## 6. Hai lỗ lộ ra khi chạy chứng cứ — đã sửa trong commit 1

1. **Không test nào bắt việc bộ tổng hợp lùi về v1** khi v2 hỏng. Đã thêm test:
   v2 hỏng ⇒ `MEASUREMENT_INVALID`, lý do
   `TARGETED_REGISTRY_V2_INVALID:<mã>`.
2. **Ca không bị ghi đè bị chấm lại v2** thay vì kế thừa v1. Bản ghi chỉ mang kết
   quả v1 (không có trường quan hệ thô) khiến N02/N03 ra `NOT_MEASURED` trong khi
   v1 là `YES`. Phép so request/phân loại START ↔ END lộ ra lỗi này. Đã sửa ở
   `_tom_tat_am` và thêm test.

Commit 1 được amend cục bộ (chưa push) để giữ trần hai commit. Red-before,
green-after, tiêm lỗi, parity và full backend đều chạy lại trên commit cuối.

## 7. Vai trò dataset

`N04: DEVELOPMENT_HOLDOUT_PILOT → DEVELOPMENT_REGRESSION_CASE` (đã dùng để tìm
lỗi và thiết kế bản sửa). `EVIDENCE_CLASS = MIXED_DEVELOPMENT_EVIDENCE` ·
`UNTOUCHED_HOLDOUT_CLAIM = false`. Các ca tiếp nối là P06, P07, P08, N02 và N03.
Case ID, ground truth và mọi artifact lịch sử **không đổi**. Quyết định canary vẫn
cần một ca âm **mới**.

## 8. Giới hạn

- **Không test riêng cho ba mã phòng thủ:** `DATASET_HASH_MISMATCH`,
  `INPUT_HASH_MISMATCH`, `DUPLICATE_KEY`. Chúng không nằm trong danh sách chặn
  bắt buộc của đặc tả.
- **v2 của N04 trên bản ghi lịch sử là `NOT_MEASURED`.** Output lịch sử đã khử thô
  không mang trường tuple. v2 chỉ đo được trên bản ghi runner mới.
- **v2 là chỉ số phụ.** Nó không vào `phan_loai`. `YES` ở N04 chỉ chứng minh hồi
  quy của một ca đã dùng để sửa hệ, không phải bằng chứng tổng quát.

## 9. Artifact

`docs/evaluation/geometry/photo-problem-to-scene/n04-targeted-rejection-registry-v2-preregistration/`
— overlay đã commit ở `330334a`, cộng 12 artifact:

- `PRECHECK` · `BASE_REGISTRY_IMMUTABILITY` · `REGISTRY_V2_OVERLAY_CONTRACT`
- `RESOLVED_REGISTRY` · `N04_TARGETED_BEFORE_AFTER` · `DATASET_ROLE_DECISION`
- `RUNNER_BINDING_PROOF` · `REQUEST_PARITY` · `RED_BEFORE_GREEN_AFTER`
- `FAULT_INJECTIONS` · `OFFLINE_GATES` · `SECRET_SCAN`

```text
NEXT_ACTION = RETRY_REMAINING_PREREGISTERED_CASES_POST_SAFETY_REPAIR
```
