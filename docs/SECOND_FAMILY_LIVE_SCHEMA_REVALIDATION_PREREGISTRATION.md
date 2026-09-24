# Báo Cáo Tiền Đăng Ký Kiểm Chứng Live Schema Họ Bài Thứ Hai (Prism Volume)

**WAVE_ID:** `SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION`  
**NGÀY:** 2026-09-24  
**NHÁNH:** `feat/photo-problem-to-scene`  
**START_HEAD:** `002b8da51cf28dcfb6588a5bc62b987ff41d96be`  
**CHẾ ĐỘ:** 100% Offline (0 Gemini requests, 0 network calls, 0 API keys loaded)  
**BẢO TOÀN WORKING TREE:** ` D frontend/public/favicon.svg` (giữ nguyên không đổi)  

---

## 1. Mục Tiêu Khoa Học và Kỹ Thuật

Wave này thực hiện kiểm tra thiết bị đo (apparatus check) và tiền đăng ký chính xác một lần chạy live duy nhất trong wave kế tiếp nhằm trả lời câu hỏi thực nghiệm:
> *Gemini live API có chấp nhận schema model-facing mới (`solid_topology` cho khối lăng trụ) và trả về phản hồi có cấu trúc hợp lệ hay không?*

### Giới hạn phương pháp luận và khẳng định khoa học
- **RESEARCH_DIRECTION_PRESERVED:** `YES`
- **LITERATURE_GAP_STATUS:** `NOT_EVALUATED_IN_THIS_WAVE`
- **NOVELTY_CLAIM:** `NOT_ESTABLISHED`
- **STATISTICAL_SIGNIFICANCE:** `NOT_APPLICABLE` (đây là apparatus smoke test trên đúng 1 request, không dùng để tuyên bố tổng quát hóa hay hiệu quả sư phạm).

---

## 2. Gate 0 — Post-Refreeze Acceptance Check (Read-Only)

### A. Kiểm tra phạm vi commit (Commit Scope)
Kiểm tra hai commit gần nhất:
1. `6eb23e8daef5ece1349859a5a73641f245ca8a42` (`fix(schema): restore semantic program schema coherence`):
   - `backend/tests/semantic_program/test_schema_sync.py`
   - `docs/schemas/semantic_program.schema.json`
   - `frontend/src/simulations/domains/semantic/semantic_program.schema.json`
   - Đúng 3 file đã đăng ký.
2. `002b8da51cf28dcfb6588a5bc62b987ff41d96be` (`docs(eval): refreeze coherent prism evaluation candidate`):
   - Đúng các file harness đo lường, freeze candidate và tài liệu.
3. Không chạm `frontend/public/favicon.svg`.
4. `git diff 6eb23e8d~1..002b8da5 -- backend/app/` hoàn toàn rỗng (0 dòng thay đổi mã sản phẩm).
5. Không có prompt drift, compiler drift, FactGraph drift hay routing drift.

### B. Giải thích tree-hash cross-check mismatch
- **Dự kiến pháp y trước đó:** `669ea2f1a63c8704044ffc70cb5c6fcb5b82c786ad9bcba0ce022b7d5bf296f0`
- **Candidate canonical thực tế ghi:** `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95`
- **Phân tích đối soát:**
  1. Manifest 103 file mã sản phẩm được sinh bằng đúng thuật toán của `freeze_evaluation_candidate.py`.
  2. So sánh manifest giữa `c69eef96` và `6eb23e8d`: Duy nhất đúng 1 file thay đổi mã băm:
     - `frontend/src/simulations/domains/semantic/semantic_program.schema.json`:  
       `3db1e1cfeb320eb15378f022da79c532fb811e6d813422420061852f35246afe` → `7610ff090b50646fb98a46dd261b2f82014c292dcd6f74392a5f95c850016fa1`.
  3. Toàn bộ 102 file mã sản phẩm còn lại trùng khớp 100% từng byte (`UNEXPECTED_MEASURED_FILE_DRIFT = 0`).
  4. Mã băm cây thực tế `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95` tái lập tuyệt đối qua 2 lần chạy độc lập (`TREE_HASH_REPRODUCIBLE = YES`).
  5. **Nguyên nhân gốc và phân loại mismatch:**
     - Trong `freeze_evaluation_candidate.py`, hằng số `MEASURED_SYSTEM_PATHS` liệt kê cả thư mục `frontend/src/simulations/domains/semantic` lẫn file `frontend/src/simulations/domains/semantic/semantic_program.schema.json`. Danh sách file quét được không deduplicate dẫn tới file schema xuất hiện 2 lần liên tiếp trong danh sách băm.
     - Giá trị dự đoán `669ea2f1a63c...` trùng 8 ký tự đầu hex (`669ea2f1...`) nhưng lệch phần sau do tính toán phân tích phỏng đoán trước đây không phản ánh chính xác cấu trúc lặp này.
     - **Phân loại:** `FORENSIC_PREDICTION_ERROR` (Mã băm thực tế `669ea2f16081...` là chân lý máy chuẩn tắc).

### C. Kiểm tra Telemetry Collector
- `backend/scripts/collect_docs_telemetry_evidence.py` thực hiện gọi trực tiếp `freeze_evaluation_candidate.py --verify` và `lock_cache_identity.py --verify`.
- Cả hai lệnh thẩm định đều trả về exit code 0 (`VALIDATOR_SOURCE_OF_TRUTH = PASS`).

### D. Bằng chứng Full Backend Suite
- Suite 6,143 passed (0 failed, 0 errors, 1 skipped, 1 deselected) đã chạy tại đúng `002b8da5` qua `task-731` (log lưu tại `.system_generated/tasks/task-731.log`).
- **Phân loại Provenance:** `CONSOLE_RESULT_ONLY` (không có file JSON lưu trữ lâu dài trong docs/evaluation, đúng theo quy định trung thực bằng chứng của Section 3.D).
- Không có bất kỳ executable file nào thay đổi sau lần chạy đó.

### Kết Luận Gate 0: PASS
- `SCHEMA_SYNC_STRICT = PASS`
- `CANDIDATE_VERIFY = PASS`
- `CACHE_VERIFY = PASS`
- `TREE_HASH_REPRODUCIBLE = YES`
- `UNEXPECTED_MEASURED_FILE_DRIFT = 0`
- `VALIDATOR_SOURCE_OF_TRUTH = PASS`

---

## 3. Thiết Kế và Ràng Buộc Thử Nghiệm Live (Request Binding)

### A. Định danh ca và đề bài chuẩn tắc
- **CASE_ID:** `PRISM_SCHEMA_LIVE_P01`
- **SOURCE_CASE:** `PRISM_P01` (đọc từ manifest canonical `docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json`)
- **Văn bản đề bài canonical:**
  ```text
  Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4. Cạnh bên AD = 5. Tính thể tích khối lăng trụ ABC.DEF.
  ```
- **Mã băm đề bài (SHA-256):** `64a51dfbd95b0859eec44721870c30704418a1172b3d880e07a4da7d4d7cf2a0`

### B. Cấu hình Model và Prompt
- **Model:** `gemini-2.5-flash` (đọc từ `app.ai.gemini.MODEL`, không có config drift)
- **Temperature:** `0.1` (theo chuẩn `pipeline.stage_semantic_analyze`)
- **Domain:** `hinh_hoc`
- **Skill:** `geometry_analyze` (`app/ai/skills/geometry_analyze.md`)
- **PROMPT_SHA256:** `a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f`

### C. Lược đồ phản hồi (Response Schema)
- Dẫn xuất trực tiếp từ `analyze_schema_for("hinh_hoc")` qua `_sanitize_gemini_schema`.
- **SANITIZED_RESPONSE_SCHEMA_SHA256:** `90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c`
- **Xác nhận chứa `solid_topology`:** `YES` (loại `prism`, `base_cycle`, `top_cycle`, `correspondence`).

### D. Thân Request Wire (Httpx Wire Bytes)
- Sinh từ production builder (`call_gemini` payload structure qua `httpx.Request`).
- **REQUEST_BODY_SHA256:** `4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082`
- **Độ dài wire bytes:** `10827` bytes.
- **REQUEST_BODY_TWO_RUN_PARITY:** `YES` (trùng khớp từng byte giữa hai lần sinh độc lập).
- **GROUND_TRUTH_ABSENT_FROM_REQUEST:** `YES` (không chứa bất kỳ chuỗi ground truth nào).

### E. Ngân sách Transport nghiêm ngặt
- `MAX_ANALYZE_HTTP_REQUESTS = 1`
- `VISION_HTTP_REQUESTS = 0`
- `SYNTHESIS_HTTP_REQUESTS = 0`
- `REPAIR_REQUESTS = 0`
- `RETRIES = 0`
- Dừng ngay sau lỗi đầu tiên, không retry transient.

---

## 4. Tách Biệt Các Chiều Đo Lường (Isolated Measurement Dimensions)

Tuyệt đối không gộp các chiều đo lường thành một nhãn PASS duy nhất:

| Chiều Đo Lường | Tên Chỉ Số | Điều Kiện Đạt | Ý Nghĩa Kỹ Thuật |
|---|---|---|---|
| **A. Provider Acceptance** | `SCHEMA_ACCEPTED` | Gemini API chấp nhận request body, trả về HTTP 200 dạng JSON, không báo 400 Bad Request. | Xác nhận Gemini hỗ trợ cấu trúc schema `solid_topology`. Độc lập với việc model hiểu đúng hay sai đề. |
| **B. Response Parsing** | `RESPONSE_PARSE_VALID` | Phản hồi parse được bằng JSON và đi qua `build_request_contract` mà không ném ngoại lệ cấu trúc Pydantic. | Xác nhận phản hồi tương thích với hợp đồng biên của hệ thống. |
| **C. Semantic Extraction** | `SEMANTIC_EXTRACTION_VALID` | Trích xuất chính xác: `solid_kind="prism"`, `base_cycle=["A","B","C"]`, `top_cycle=["D","E","F"]`, `correspondence=[["A","D"],["B","E"],["C","F"]]`, quan hệ vuông góc đáy tại A, $AD \perp (ABC)$, và độ dài $AB=3, AC=4, AD=5$. | Đo năng lực hiểu đề tự nhiên của LLM. |
| **D. Pipeline Smoke Test** | `PIPELINE_SMOKE_TEST` | FactGraph nhận diện cấu trúc $\to$ compiler `SUPPORTED` $\to$ biên dịch ra 6 đỉnh, 9 cạnh, 5 mặt $\to$ bộ giải tính thể tích chính xác $V = 30$. | Xác nhận lát cắt tất định downstream chạy thông suốt từ đầu ra LLM. |

---

## 5. Bảng Phân Loại Kết Quả Wave Live Tương Lai

Bảng phân loại đóng cho lần chạy tiếp theo:

1. `SCHEMA_ACCEPTED_AND_PIPELINE_PASS`: Provider chấp nhận schema, model trích xuất đủ và đúng dữ kiện, pipeline tất định chạy ra đáp số $30$.
2. `SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE`: Provider chấp nhận schema, nhưng model trích xuất sai/thiếu dữ kiện. Schema được xác nhận hợp lệ; cấm sửa prompt/schema trong cùng wave.
3. `SCHEMA_ACCEPTED_CONTRACT_PARSE_FAILURE`: Provider chấp nhận schema, nhưng phản hồi vi phạm cấu trúc hợp đồng.
4. `PROVIDER_SCHEMA_REJECTED`: Gemini trả về HTTP 400 hoặc từ chối schema. Dừng ngay lập tức, 0 retry.
5. `PROVIDER_ERROR`: Lỗi hạ tầng HTTP 5xx từ phía Google.
6. `MEASUREMENT_ERROR`: Lỗi nội bộ trong quá trình đo đạc/ghi nhận.
7. `TRANSPORT_OUTCOME_UNKNOWN`: Tiến trình gặp sự cố bất ngờ trước khi ghi nhận xong phản hồi.

---

## 6. Danh Mục Artifact Đã Tạo

Các file artifact máy lưu tại thư mục:  
`docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation-preregistration/`

- `PRECHECK.json` — Kết quả kiểm tra nghiệm thu Gate 0 và bằng chứng tái lập tree-hash.
- `REQUEST_BINDING.json` — Ràng buộc đóng băng thông số request, model, prompt hash, schema hash và wire body SHA-256.
- `ACCEPTANCE_CRITERIA.json` — Đặc tả 4 chiều đo lường riêng biệt và bảng phân loại kết quả.
- `FINAL_DECISION.json` — Quyết định nghiệm thu tiền đăng ký chính thức.

---

## 7. Kết Luận và Phán Quyết Cuối Cùng

```text
POST_REFREEZE_ACCEPTANCE_GATE = PASS
TREE_HASH_REPRODUCIBLE = YES
TREE_HASH_MISMATCH_CLASSIFICATION = FORENSIC_PREDICTION_ERROR
VALIDATOR_SOURCE_OF_TRUTH = PASS
FULL_SUITE_EVIDENCE_PROVENANCE = CONSOLE_RESULT_ONLY

SCHEMA_SHA256 = 7610ff090b50646fb98a46dd261b2f82014c292dcd6f74392a5f95c850016fa1
CANDIDATE_TREE_HASH = 669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95
CANDIDATE_FILE_COUNT = 103
CACHE_VERSION = 100

CASE_ID = PRISM_SCHEMA_LIVE_P01
MODEL = gemini-2.5-flash
TEMPERATURE = 0.1
REQUEST_BODY_SHA256 = 4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082
PROMPT_SHA256 = a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f
SANITIZED_RESPONSE_SCHEMA_SHA256 = 90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c
REQUEST_BODY_TWO_RUN_PARITY = YES
SCHEMA_CONTAINS_SOLID_TOPOLOGY = YES

FUTURE_TRANSPORT_BUDGET = 1
FUTURE_RETRIES = 0
FUTURE_VISION_REQUESTS = 0
FUTURE_SYNTHESIS_REQUESTS = 0
FUTURE_REPAIR_REQUESTS = 0

NEW_GEMINI_REQUESTS = 0
NETWORK_REQUESTS = 0
API_KEY_LOADED = NO
PRODUCT_CODE_CHANGED = NO
PROMPT_CHANGED = NO
SCHEMA_CHANGED = NO
COMPILER_CHANGED = NO
ROUTING_CHANGED = NO
DEFAULT_MODE = LLM_ONLY

RESEARCH_DIRECTION_PRESERVED = YES
NOVELTY_CLAIM = NOT_ESTABLISHED
FINAL_DECISION = PASS
MERGE_ALLOWED = NO
NEXT_ACTION = SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION
```
