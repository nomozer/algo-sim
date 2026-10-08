# Báo Cáo Tiền Đăng Ký Kiểm Chứng Live Retry Họ Bài Thứ Hai (Prism Volume Retry)

**WAVE_ID:** `SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION`  
**NGÀY:** 2026-09-24  
**NHÁNH:** `feat/photo-problem-to-scene`  
**START_HEAD:** `462645ec391c04a8cf0db1ed66e8db5cbf0f976d`  
**CHẾ ĐỘ:** 100% Offline (0 Gemini requests, 0 network calls, 0 API keys loaded, 0 .env loaded)  
**BẢO TOÀN WORKING TREE:** ` D frontend/public/favicon.svg` (giữ nguyên không đổi)  

---

## 1. Trạng Thái Đầu Vào và Mục Tiêu Giới Hạn

### A. Trạng thái đầu vào
- **CASE_ID:** `PRISM_SCHEMA_LIVE_P01`
- **SOURCE_WAVE:** `SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE`
- **MODEL:** `gemini-2.5-flash`
- **TEMPERATURE:** `0.1`
- **CACHE_VERSION:** `100`
- **CANDIDATE_TREE_HASH:** `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95` (103 files)
- **PREVIOUS_REQUEST_BODY_SHA256:** `4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082`
- **PROMPT_SHA256:** `a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f`
- **SANITIZED_RESPONSE_SCHEMA_SHA256:** `90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c`
- **USER_CHANGE_TO_PRESERVE:** `D frontend/public/favicon.svg`

### B. Mục tiêu giới hạn
Tiền đăng ký chính xác một request retry cho `PRISM_SCHEMA_LIVE_P01` nhằm đo đạc độc lập 5 chiều chất lượng:
1. `SCHEMA_ACCEPTED`: Nhà cung cấp chấp nhận schema không trả về HTTP 400.
2. `RAW_RESPONSE_DURABLY_PERSISTED`: Dữ liệu phản hồi đầy đủ được ghi bền vững nguyên bản bằng atomic write và kiểm chứng read-back trước khi parse/scoring.
3. `RESPONSE_PARSE_VALID`: Khớp JSON và hợp đồng RequestContract mà không crash Pydantic.
4. `SEMANTIC_EXTRACTION_VALID`: Trích xuất đầy đủ và chính xác các facts hình học không gian (solid kind, cycles, correspondence, lengths, perpendicular relations).
5. `PIPELINE_SMOKE_TEST`: FactGraph $\to$ Compiler $\to$ Topology $\to$ Solvers chạy tất định ra thể tích $V = 30$.

### C. Giới hạn phương pháp luận
- **RESEARCH_DIRECTION_PRESERVED:** `YES`
- **GENERALIZATION_CLAIM:** `NOT_ALLOWED`
- **BENCHMARK_WIDE_ACCURACY_CLAIM:** `NOT_ALLOWED`
- **PEDAGOGICAL_EFFICACY_CLAIM:** `NOT_ALLOWED`
- Đây là apparatus verification và single-case smoke test trên đúng 1 request retry; không dùng để kết luận khái quát hóa hay hiệu quả sư phạm.

---

## 2. Bất Biến Bắt Buộc (Invariants)

Toàn bộ wave tuân thủ nghiêm ngặt các bất biến:
- `NEW_GEMINI_REQUESTS = 0`
- `NETWORK_REQUESTS = 0`
- `API_KEY_LOADED = NO`
- `DOTENV_LOADED = NO`
- `PRODUCT_CODE_CHANGED = NO` (`backend/app/**` nguyên vẹn 100%)
- `PROMPT_CHANGED = NO`
- `SCHEMA_CHANGED = NO`
- `COMPILER_CHANGED = NO`
- `ROUTING_CHANGED = NO`
- `CACHE_VERSION_CHANGED = NO` (`CACHE_VERSION = 100`)
- `CANDIDATE_REFREEZE = NO` (`CANDIDATE_TREE_HASH = 669ea2f1...`)
- `HISTORICAL_REPORTS_CHANGED = NO`
- `HISTORICAL_ARTIFACTS_CHANGED = NO`
- `USER_FAVICON_PRESERVED = YES`

---

## 3. Gate A — Precheck và Request Parity

1. **Working Tree & HEAD:**
   - Nhánh: `feat/photo-problem-to-scene`
   - START_HEAD: `462645ec391c04a8cf0db1ed66e8db5cbf0f976d`
   - Working tree: Duy nhất `frontend/public/favicon.svg` bị xóa bởi user (giữ nguyên không stage).
2. **Candidate & Cache Identity:**
   - Candidate tree hash: `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95` (103 files, verified qua `freeze_evaluation_candidate.py --verify`).
   - Cache version: `100` (verified qua `lock_cache_identity.py --verify`).
3. **Request Parity:**
   - Dựng thân request wire độc lập hai lần bằng production request builder (`app.ai.gemini.call_gemini` payload structure + `httpx.Request`).
   - Kết quả Run 1 và Run 2 trùng khớp 100% từng byte (`REQUEST_BODY_TWO_RUN_PARITY = YES`).
   - Wire request body SHA-256: `4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082` (10,827 bytes).
   - Trùng khớp tuyệt đối với request hash của lần chạy live trước: `DRIFT_DETECTED = NO`.
   - `PROMPT_SHA256`: `a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f`.
   - `SANITIZED_RESPONSE_SCHEMA_SHA256`: `90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c`.
4. **Phán quyết Gate A:** `PASS`.

---

## 4. Gate B — Thiết Kế và Hợp Đồng Persistence Bắt Buộc

Mô-đun apparatus đo lường chuẩn tắc được đặt tại [`backend/scripts/live_retry_apparatus.py`](file:///d:/Documents/projects/algo-sim/backend/scripts/live_retry_apparatus.py), thiết lập máy trạng thái (state machine) 7 bước:

$$\text{PLANNED} \to \text{RESERVED} \to \text{TRANSPORT\_COMPLETED} \to \text{RAW\_PERSISTED} \to \text{PARSED} \to \text{SCORED} \to \text{PIPELINE\_COMPLETED}$$

### Quy tắc persistence bắt buộc:
1. **Ghi trước Parsing:** Toàn bộ candidate response text/bytes phải được ghi bền vững ra đĩa trước khi bất kỳ thao tác parse, scoring hay pipeline nào bắt đầu.
2. **Atomic Write Protocol:**
   - Tạo file tạm thời cùng thư mục đích (`tempfile.NamedTemporaryFile` trên cùng volume).
   - Ghi bytes $\to$ `flush()` $\to$ `os.fsync()` $\to$ đóng descriptor $\to$ `os.replace(tmp, dest)`.
   - Đọc lại toàn bộ file vừa ghi (`read_bytes()`) và đối soát SHA-256 + độ dài byte (`read_back_validation`).
3. **Phân Vùng Lưu Trữ:**
   - Raw response lưu tại execution directory bên ngoài repo (hoặc thư mục scratch gitignored), tuyệt đối không commit raw response vào git tree.
   - Báo cáo và artifacts trong repo chỉ lưu metadata: SHA-256, byte count, đường dẫn execution-relative đã ẩn danh hóa, và trạng thái persistence.
4. **Bảo Mật Bí Mật (Secret Scrubbing):**
   - API key (regex `AIza[0-9A-Za-z-_]{35}`) và Authorization header (`Bearer ...`) bị tẩy xóa tự động trước khi ghi journal hay metadata.
5. **Cấm Bypass Bộ Nhớ (Memory Bypass Prohibition):**
   - Nếu persistence hoặc read-back thất bại: Dừng ngay lập tức với `FINAL_CLASSIFICATION = MEASUREMENT_ERROR`, `PIPELINE_RESULT = NOT_RUN`, `RETRY_ALLOWED_AUTOMATICALLY = NO`. Cấm đọc biến RAM để chạy tiếp như thể đã persist thành công.

---

## 5. Gate C — Kiểm Chứng Apparatus Bằng Fake Transport

Toàn bộ apparatus đo lường được thẩm định qua 12 test độc lập tại [`backend/tests/geometry/test_live_retry_apparatus.py`](file:///d:/Documents/projects/algo-sim/backend/tests/geometry/test_live_retry_apparatus.py), 100% offline với fake transport:

| STT | Invariant Kiểm Chứng | Kết Quả |
|---|---|---|
| 1 | Raw response đầy đủ được ghi trước parsing (`test_inv_01_raw_persisted_before_parsing`) | **PASSED** |
| 2 | Process death ngay sau transport vẫn bảo toàn file raw hợp lệ và hash kiểm chứng được (`test_inv_02_process_death_resilience`) | **PASSED** |
| 3 | Payload preview/truncated bị từ chối fail-closed (`test_inv_03_preview_rejected`) | **PASSED** |
| 4 | Hash mismatch giữa transport bytes và file đọc lại gây fail-closed (`test_inv_04_hash_mismatch_fails_closed`) | **PASSED** |
| 5 | File bị cắt cụt (truncate) làm fail-closed (`test_inv_05_truncated_file_fails_closed`) | **PASSED** |
| 6 | Thất bại atomic write / replace / read-back làm fail-closed (`test_inv_06_atomic_write_failure_fails_closed`) | **PASSED** |
| 7 | API key và Authorization header bị tẩy sạch khỏi journal và metadata (`test_inv_07_secrets_scrubbed_from_journal`) | **PASSED** |
| 8 | Ngăn chặn tự động gửi lại request khi đã RESERVED hoặc TRANSPORT_COMPLETED (`test_inv_08_no_automatic_resend`) | **PASSED** |
| 9 | Evaluator R1 sửa dùng canonical references (`["A", "B"]`), không so khớp cứng display label (`test_inv_09_corrected_evaluator_uses_canonical_references`) | **PASSED** |
| 10 | Pipeline harness R2 dùng production entry point `contract_adapter.build_fact_graph` $\to$ `compiler.danh_gia_eligibility` $\to$ `compiler.bien_dich` (`test_inv_10_pipeline_harness_production_entry_point`) | **PASSED** |
| 11 | Không còn bất kỳ lệnh gọi `FG.FactGraph()` nào trong toàn bộ codebase qua AST verification (`test_inv_11_zero_calls_to_fact_graph_class`) | **PASSED** |
| 12 | Ngân sách request thứ hai bị chặn đứng trước transport (`test_inv_12_single_request_budget_enforced`) | **PASSED** |

**Tổng kết Gate C:** `12/12 PASSED` (0 network, 0 live calls).

---

## 6. Gate D — Tiêu Chí Đóng Băng Cho Lần Live Kế Tiếp

### A. Ngân sách Transport nghiêm ngặt
- `TRANSPORT_BUDGET = 1`
- `ANALYZE_HTTP_REQUESTS_MAX = 1`
- `VISION_HTTP_REQUESTS_MAX = 0`
- `SYNTHESIS_HTTP_REQUESTS_MAX = 0`
- `REPAIR_REQUESTS_MAX = 0`
- `RETRIES_MAX = 0`

### B. Kỳ vọng trích xuất ngữ nghĩa (Semantic Extraction Target)
- `solid_kind`: `"prism"`
- `base_cycle`: `["A", "B", "C"]`
- `top_cycle`: `["D", "E", "F"]`
- `correspondence`: `[["A", "D"], ["B", "E"], ["C", "F"]]`
- `lengths`:
  - $AB = 3$
  - $AC = 4$
  - $AD = 5$
- `relations`:
  - $\text{perpendicular\_lines}(AB, AC)$ (vuông tại A)
  - $\text{perpendicular\_line\_plane}(AD, ABC)$ ($AD \perp (ABC)$)

### C. Kỳ vọng pipeline tất định downstream
- `FACT_GRAPH_RESULT = VALID`
- `COMPILER_RESULT = SUPPORTED`
- `TOPOLOGY_RESULT = PASS` (6 đỉnh, 9 cạnh, 5 mặt, Euler = 2)
- `FINAL_MEMORY_RESULT = PASS`
- `ANSWER_RESULT = PASS`
- `ANSWER = 30`

Cấm tuyệt đối dùng problem_text hay ground truth để vá dữ kiện còn thiếu vào contract đã parse.

---

## 7. Bảng Phân Loại Đóng (Closed Outcome Classification)

Chỉ cho phép đúng một trong 5 kết quả sau trong lần chạy live kế tiếp:

1. **`SCHEMA_ACCEPTED_PIPELINE_PASS`:**
   Provider chấp nhận schema, raw response được ghi bền vững và xác minh hash, contract parse hợp lệ, ngữ nghĩa trích xuất đầy đủ chính xác, downstream compiler tính toán ra thể tích $30$.
2. **`SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE`:**
   Provider chấp nhận schema và raw response được ghi bền vững, nhưng phản hồi canonical thiếu hoặc sai các facts hình học không gian. Không cho phép sửa prompt/schema trong cùng wave.
3. **`SCHEMA_REJECTED`:**
   Gemini API trả về HTTP 400 hoặc từ chối schema `solid_topology`. Dừng ngay lập tức, 0 retries.
4. **`PROVIDER_ERROR`:**
   Lỗi hạ tầng HTTP 5xx, timeout, hoặc ngắt kết nối transport từ phía Google.
5. **`MEASUREMENT_ERROR`:**
   Lỗi ghi bền vững, không khớp read-back hash, lỗi bộ bọc parse, lỗi evaluator hoặc lỗi pipeline harness. Tuyệt đối không quy kết là lỗi mô hình nếu rơi vào nhóm này.

---

## 8. Danh Mục Artifact Đã Tạo

Các artifacts được lưu tại:  
`docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/`

- [`PRECHECK.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/PRECHECK.json): Bằng chứng nghiệm thu Gate A và request parity.
- [`REQUEST_BINDING.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/REQUEST_BINDING.json): Đóng băng thông số request body wire SHA-256, prompt hash, schema hash và transport budget.
- [`PERSISTENCE_CONTRACT.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/PERSISTENCE_CONTRACT.json): Hợp đồng ghi bền vững raw response, quy tắc atomic write, read-back verification và state machine.
- [`ACCEPTANCE_CRITERIA.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/ACCEPTANCE_CRITERIA.json): 5 chiều đo lường độc lập, kỳ vọng ngữ nghĩa/pipeline và bảng phân loại kết quả đóng.
- [`FINAL_DECISION.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry-preregistration/FINAL_DECISION.json): Quyết định nghiệm thu wave tiền đăng ký retry.

---

## 9. Kết Luận và Phán Quyết Wave

```text
WAVE = SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION
BRANCH = feat/photo-problem-to-scene
START_HEAD = 462645ec391c04a8cf0db1ed66e8db5cbf0f976d
APPARATUS_COMMIT = ab7d94eb651c33842c94317a41ec5bc0d0999516

REQUEST_BODY_SHA256 = 4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082
REQUEST_PARITY = PASS
PROMPT_SHA256 = a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f
SANITIZED_RESPONSE_SCHEMA_SHA256 = 90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c

RAW_PERSISTENCE_POLICY = DURABLE_ATOMIC_WRITE_WITH_READ_BACK
ATOMIC_WRITE_RESULT = PASS
READ_BACK_VALIDATION = PASS
PROCESS_DEATH_RECOVERY = PASS
RESERVED_CASE_RESEND_POLICY = FAIL_CLOSED
TRANSPORT_COMPLETED_RESEND_POLICY = FAIL_CLOSED

R1_EVALUATOR_FIX_VERIFIED = YES
R2_PIPELINE_HARNESS_FIX_VERIFIED = YES
FAKE_TRANSPORT_TEST_RESULT = 12_OF_12_PASSED

TRANSPORT_BUDGET = 1
NEW_GEMINI_REQUESTS = 0
NETWORK_REQUESTS = 0
API_KEY_LOADED = NO

PRODUCT_CODE_CHANGED = NO
PROMPT_CHANGED = NO
SCHEMA_CHANGED = NO
COMPILER_CHANGED = NO
ROUTING_CHANGED = NO
CACHE_VERSION = 100
CANDIDATE_TREE_HASH = 669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95
CANDIDATE_VERIFY = PASS
CACHE_VERIFY = PASS

TARGETED_TEST_RESULT = PASS
FULL_BACKEND_RERUN = NO
HISTORICAL_REPORTS_CHANGED = NO
HISTORICAL_ARTIFACTS_CHANGED = NO
SECRET_LEAKS = NO
COMMITS_CREATED = 1 (apparatus tooling and test suite)
USER_FAVICON_DELETION_PRESERVED = YES

FINAL_DECISION = PASS
LIVE_RETRY_ALLOWED = YES
MERGE_ALLOWED = NO
NEXT_ACTION = SECOND_FAMILY_LIVE_RETRY
```
