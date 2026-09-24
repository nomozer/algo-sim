# Báo Cáo Thực Nghiệm Live Retry Họ Bài Thứ Hai (Prism Volume Retry)

**WAVE_ID:** `SECOND_FAMILY_LIVE_RETRY`  
**NGÀY:** 2026-09-24  
**NHÁNH:** `feat/photo-problem-to-scene`  
**START_HEAD:** `5d92afa241c2bcb1c18b39e0be8060964ffd951d`  
**MODEL:** `gemini-2.5-flash`  
**TEMPERATURE:** `0.1`  
**CASE_ID:** `PRISM_SCHEMA_LIVE_P01` (source case: `PRISM_P01`)  
**CHẾ ĐỘ MẶC ĐỊNH:** `LLM_ONLY`  
**BẢO TOÀN WORKING TREE:** ` D frontend/public/favicon.svg` (giữ nguyên không đổi)  

---

## 1. Mục Tiêu Thực Nghiệm và Kết Quả Cốt Lõi

Wave này thực thi chính xác một lần chạy live retry duy nhất đã được tiền đăng ký tại [`docs/SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION.md`](SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION.md) nhằm kiểm chứng độc lập năm chiều đo lường với thiết bị đo đã được chuẩn hóa và sửa lỗi (R1 evaluator sửa dùng canonical references, R2 pipeline harness gọi entry point chuẩn tắc sản xuất, và durable persistence contract nguyên tử).

### Kết luận thực nghiệm năm chiều
1. **Provider Schema Acceptance (`SCHEMA_ACCEPTED`):** **THÀNH CÔNG (`YES`)**  
   Gemini API (`gemini-2.5-flash`) chấp nhận trọn vẹn request body wire chứa cấu trúc `solid_topology` phức tạp, trả về mã trạng thái **HTTP 200** trong **5,882 ms**, không gặp lỗi 400 Bad Request hay từ chối schema.
2. **Durable Raw Persistence (`RAW_RESPONSE_DURABLY_PERSISTED`):** **THÀNH CÔNG (`YES`)**  
   Phản hồi candidate được ghi bền vững ra thư mục ngoài repository bằng giao thức atomic write (temp file $\to$ `flush()` $\to$ `os.fsync()` $\to$ `os.replace()`), kiểm chứng đối soát read-back SHA-256 (`f1bd804584bfe18f5a3ead539a2eb8043696d53465a7f852c2f1cf92920d91b0`, 2,322 bytes) trùng khớp 100% trước khi parse hoặc scoring.
3. **Response Parsing (`RESPONSE_PARSE_VALID`):** **THÀNH CÔNG (`YES`)**  
   Payload đọc lại từ đĩa được parse JSON và khởi tạo hợp đồng `RequestContract` biên mà không gặp bất kỳ lỗi cú pháp hay ngoại lệ Pydantic nào.
4. **Semantic Extraction (`SEMANTIC_EXTRACTION_VALID`):** **THÀNH CÔNG (`YES`)**  
   Mô hình trích xuất đầy đủ và chính xác toàn bộ facts hình học không gian:
   - `solid_kind`: `"prism"`
   - `base_cycle`: `["A", "B", "C"]`
   - `top_cycle`: `["D", "E", "F"]`
   - `correspondence`: `[["A", "D"], ["B", "E"], ["C", "F"]]`
   - `lengths`: $AB = 3, AC = 4, AD = 5$ (được nhận diện chính xác qua corrected evaluator R1)
   - `geometric_relations`: $\text{perpendicular\_lines}(AB, AC)$ và $\text{perpendicular\_line\_plane}(AD, ABC)$
5. **Deterministic Pipeline Smoke Test (`PIPELINE_SMOKE_TEST`):** **THÀNH CÔNG (`PASS`)**  
   Đường ống tất định downstream chạy từ output của mô hình qua entry point sản xuất:
   - `FactGraph`: `VALID` (xác thực mạng dữ kiện đầy đủ cho lăng trụ đứng)
   - `compiler.danh_gia_eligibility`: `SUPPORTED`
   - `compiler.bien_dich`: `COMPILED`
   - `topology`: `PASS` (đa diện 6 đỉnh, 9 cạnh, 5 mặt, Euler $V - E + F = 6 - 9 + 5 = 2$)
   - `interpreter & final_memory`: `PASS`
   - `answer`: **`30`** (thể tích lăng trụ tính chính xác tuyệt đối $V = \frac{1}{2} \cdot 3 \cdot 4 \cdot 5 = 30$).

### Phán quyết phân loại đóng
- **FINAL_CLASSIFICATION:** **`SCHEMA_ACCEPTED_PIPELINE_PASS`**
- **FINAL_DECISION:** **`PASS`**
- **LIVE_RETRY_ALLOWED:** **`NO`** (đã hoàn thành trọn vẹn mục tiêu)
- **MERGE_ALLOWED:** **`NO`** (cần review sẵn sàng merge cho vertical slice)
- **NEXT_ACTION:** **`PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW`**

---

## 2. Kiểm Tra Tiền Kiểm (Gate 0 Preflight) & Cách Ly Thực Thi

Toàn bộ các cổng an toàn tiền kiểm được thẩm định nghiêm ngặt offline trước khi nạp API key:

| Chỉ Số Tiền Kiểm | Giá Trị Kỳ Vọng | Giá Trị Thực Tế Đo Đạc | Kết Luận |
|---|---|---|---|
| **Branch & Commit HEAD** | `feat/photo-problem-to-scene` @ `5d92afa2` | `5d92afa241c2bcb1c18b39e0be8060964ffd951d` | PASS |
| **Working Tree Cleanliness** | Duy nhất `frontend/public/favicon.svg` bị xóa | Chỉ `deleted: frontend/public/favicon.svg` | PASS |
| **Candidate Tree Hash** | `669ea2f1...` (103 files) | `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95` | PASS |
| **Cache Identity** | `CACHE_VERSION = 100` | `100` (`lock_cache_identity.py --verify`: PASS) | PASS |
| **Focused Fake-Transport Tests** | 48/48 passed | 48 passed in 1.01s (0 network, 0 live calls) | PASS |
| **Prompt SHA-256** | `a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f` | `a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f` | PASS |
| **Sanitized Schema SHA-256** | `90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c` | `90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c` | PASS |
| **Request Wire SHA-256** | `4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082` | `4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082` (10,827 bytes) | PASS |
| **Zero Calls to FactGraph Class**| AST walk: 0 active calls | 0 active calls in codebase | PASS |
| **Execution Worktree Isolation** | Detached worktree không chứa `.env` | `d:\tmp\live_retry_worktree` clean, 0 `.env` | PASS |
| **API Key Source** | Strictly process environment | Process environment (length=53) | PASS |

---

## 3. Nhật Ký Transport và Lưu Trữ Bền Vững (Durable Persistence)

- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- **Ngân sách transport tiêu thụ:**
  - `ANALYZE_HTTP_REQUESTS`: 1 (tối đa: 1)
  - `VISION_HTTP_REQUESTS`: 0
  - `SYNTHESIS_HTTP_REQUESTS`: 0
  - `REPAIR_REQUESTS`: 0
  - `RETRIES`: 0
- **HTTP Status:** `200 OK`
- **Độ trễ transport:** `5,882 ms`
- **Token telemetry:**
  - `prompt_tokens`: 1,703
  - `candidate_tokens`: 559
  - `thought_tokens`: 583
  - `total_tokens`: 2,845
- **Giao thức lưu trữ bền vững (State Machine):**
  $$\text{PLANNED} \to \text{RESERVED} \to \text{TRANSPORT\_COMPLETED} \to \text{RAW\_PERSISTED} \to \text{PARSED} \to \text{SCORED} \to \text{PIPELINE\_COMPLETED}$$
- **Vị trí lưu file raw response:** `D:\tmp\live_retry_evidence\PRISM_SCHEMA_LIVE_P01_raw_response.json` (thư mục ngoài repo, không bị commit vào git tree).
- **Mã băm SHA-256 file raw response:** `f1bd804584bfe18f5a3ead539a2eb8043696d53465a7f852c2f1cf92920d91b0`
- **Độ dài bytes file raw:** `2,322 bytes`
- **Xác thực đọc lại (Read-Back Validation):** Trùng khớp 100% từng byte và mã băm SHA-256.

---

## 4. Chi Tiết Kết Quả Đo Lường 5 Chiều

### Chiều 1: Schema Acceptance (`SCHEMA_ACCEPTED = YES`)
Gemini API chấp nhận request body wire với schema lăng trụ mới mà không có bất kỳ cảnh báo không tương thích nào.

### Chiều 2: Durable Raw Persistence (`RAW_RESPONSE_DURABLY_PERSISTED = YES`)
Toàn bộ candidate response bytes được lưu vào đĩa bền vững trước khi parse. Không parse từ biến RAM.

### Chiều 3: Response Parsing (`RESPONSE_PARSE_VALID = YES`)
Cấu trúc JSON đầu ra tương thích hoàn toàn với Pydantic RequestContract boundary.

### Chiều 4: Semantic Extraction (`SEMANTIC_EXTRACTION_VALID = YES`)
Bóc tách ngữ nghĩa đạt độ chính xác 100%:
- Đỉnh đáy dưới: $A, B, C$
- Đỉnh đáy trên: $D, E, F$
- Tương ứng cạnh bên: $(A, D), (B, E), (C, F)$
- Độ dài: $AB = 3, AC = 4, AD = 5$
- Ràng buộc: $AB \perp AC$ tại $A$ và $AD \perp (ABC)$

### Chiều 5: Downstream Pipeline Smoke Test (`PIPELINE_SMOKE_TEST = PASS`)
- Entry point: `contract_adapter.build_fact_graph` $\to$ `compiler.danh_gia_eligibility` $\to$ `compiler.bien_dich` $\to$ `SemanticProgramInterpreter`.
- Tô-pô hình học: Đa diện lăng trụ đứng 6 đỉnh, 9 cạnh, 5 mặt, số đặc trưng Euler $\chi = 2$.
- Diện tích đáy: $S_{ABC} = \frac{1}{2} \cdot 3 \cdot 4 = 6$.
- Thể tích khối lăng trụ: $V = S_{ABC} \cdot h = 6 \cdot 5 = 30$.
- Đáp số tính toán được: **`30`** (khớp chính xác tuyệt đối với ground truth giải tích).

---

## 5. Danh Mục Artifact Đã Tạo

Thư mục lưu trữ:  
[`docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/)

1. [`REGISTRY_BINDING.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/REGISTRY_BINDING.json): Ràng buộc đóng băng các tham số preflight, commit HEAD, mã băm prompt/schema/wire request và apparatus.
2. [`REQUEST_OBSERVATION.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/REQUEST_OBSERVATION.json): Thông số đo đạc live request, HTTP 200, độ trễ 5,882 ms, token usage (2,845 tokens), và SHA-256 của response.
3. [`RAW_PERSISTENCE_PROOF.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/RAW_PERSISTENCE_PROOF.json): Bằng chứng lưu trữ nguyên tử bền vững, đường dẫn evidence ngoài repo, xác minh đối soát read-back và không commit raw data.
4. [`LIVE_RESULT.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/LIVE_RESULT.json): Kết quả chi tiết của việc chấp nhận schema và các facts trích xuất ngữ nghĩa.
5. [`PIPELINE_RESULT.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/PIPELINE_RESULT.json): Kết quả thực thi đường ống tất định downstream qua FactGraph, compiler và interpreter, xác nhận thể tích $V = 30$.
6. [`FINAL_DECISION.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/second-family-live-retry/FINAL_DECISION.json): Quyết định chính thức với phân loại `SCHEMA_ACCEPTED_PIPELINE_PASS` và `NEXT_ACTION = PRISM_VERTICAL_SLICE_MERGE_READINESS_REVIEW`.

---

## 6. Kết Luận Wave

Thực nghiệm live retry đã chứng minh thành công toàn diện:
1. Mô hình Gemini (`gemini-2.5-flash`) chấp nhận schema `solid_topology` và trích xuất đúng, đủ 100% dữ kiện hình học của họ bài lăng trụ đứng đáy tam giác vuông.
2. Thiết bị đo lường (apparatus) mới với atomic write và durable read-back persistence hoạt động hoàn hảo, loại bỏ mọi điểm mù đo lường.
3. Lát cắt dọc tất định (deterministic compiler vertical slice) kết nối liền mạch từ hợp đồng LLM bóc tách đến bộ giải hình học, tính ra thể tích $30$ mà không cần bất kỳ bước LLM synthesis hay vá dữ liệu nào.
