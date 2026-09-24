# LLM_ONLY_PAIRED_BASELINE_COLLECTION_PREREGISTRATION — Đăng Ký Trước Đợt Thu Thập Baseline Đối Chứng Ngoại Tuyến

> **Trạng thái:** Tiền đăng ký Đóng băng (Pre-registered & Sealed) — Nghiên cứu Khóa luận Tốt nghiệp  
> **Wave:** `LLM_ONLY_PAIRED_BASELINE_COLLECTION_PREREGISTRATION`  
> **Schema Version:** `1.0.0`  
> **Tệp dữ liệu máy đọc:** [`docs/research/llm_only_paired_baseline_registry.json`](file:///d:/Documents/projects/algo-sim/docs/research/llm_only_paired_baseline_registry.json)  
> **Apparatus thực thi:** [`backend/scripts/collect_llm_only_paired_baseline.py`](file:///d:/Documents/projects/algo-sim/backend/scripts/collect_llm_only_paired_baseline.py)  
> **Bộ kiểm thử Fake Transport:** [`backend/tests/research/test_llm_only_paired_baseline_collector.py`](file:///d:/Documents/projects/algo-sim/backend/tests/research/test_llm_only_paired_baseline_collector.py)  
> **Bất biến bắt buộc:** `NETWORK_REQUESTS = 0`, `GEMINI_REQUESTS = 0`, `API_KEY_LOADED = NO`, `SHARED_ANALYZE_REQUESTS = 0`, `PLANNED_LIVE_SYNTHESIS_REQUESTS = 54`, `ABSOLUTE_REQUEST_CAP = 54`, `RETRIES_PER_OBSERVATION = 0`.

---

## 1. Bối Cảnh & Mục Đích Tiền Đăng Ký

Theo quy định tại [`docs/research/HYBRID_ARCHITECTURE_EVALUATION_PROTOCOL.md`](file:///d:/Documents/projects/algo-sim/docs/research/HYBRID_ARCHITECTURE_EVALUATION_PROTOCOL.md), kết quả kiểm kê bằng chứng ngoại tuyến (`EVIDENCE_INVENTORY`) xác nhận:
- Nhánh `HYBRID` (Deterministic Compiler) sẵn sàng 100% để replay ngoại tuyến trên 18 ca đánh giá đóng băng (`Frozen Evaluation Set`).
- Nhánh `LLM_ONLY` đang thiếu bản ghi cached synthesis cho 18 ca này, dẫn đến trạng thái `OFFLINE_HYBRID_REPLAY_READY_BUT_PAIRED_LLM_BASELINE_GAP`.

Tài liệu này xác lập quy trình **tiền đăng ký nghiêm ngặt và đóng băng apparatus ngoại tuyến** nhằm chuẩn bị cho đợt thu thập dữ liệu trực tuyến có giới hạn trong wave tiếp theo. **Trong wave hiện tại, tuyệt đối 0 request mạng và 0 request Gemini được thực hiện.**

---

## 2. Nguyên Tắc Phương Pháp Luận Cốt Lõi

1. **Primary Architecture-Isolated Evaluation (Đo lường cách ly kiến trúc sơ cấp):**
   - Đợt thu thập này chỉ phục vụ cho tầng sinh chương trình ngữ nghĩa (`SemanticProgram`).
   - Cả hai nhánh `HYBRID` và `LLM_ONLY` nhận **chính xác cùng một `RequestContract`** đã chuẩn hóa và lưu bền vững (`COMMON_INPUT`).
   - **Bản chất COMMON_INPUT:** `COMMON_INPUT` là `ORACLE_CANONICAL_STRUCTURED_FIXTURE`. Một số `RequestContract` được xây dựng từ fixture ngữ nghĩa chuẩn có tham chiếu semantic fields trong ground truth (các dữ kiện độ dài và quan hệ đề bài cho).
   - **Phạm vi Primary Estimand:** *“So sánh LLM Synthesis với Primitive Compiler với điều kiện cả hai nhận cùng một RequestContract hợp lệ và đúng về ngữ nghĩa.”*
   - **Ranh giới khoa học (Scientific Boundary):** Primary evaluation không đo chất lượng Gemini Analyze. Không được dùng kết quả primary để tuyên bố hiệu quả end-to-end từ văn bản/ảnh đầu vào. Chất lượng Analyze chỉ thuộc `SECONDARY_END_TO_END_EVALUATION` trong một preregistration riêng biệt.
2. **Không đo lại Analyze (`SHARED_ANALYZE_REQUESTS = 0`):**
   - Tầng trích xuất ngữ nghĩa (Analyze) không được gọi lại. Việc gọi Analyze độc lập sẽ đưa phương sai ngẫu nhiên của mô hình vào đầu vào, làm thiên lệch so sánh ghép cặp.
3. **Cách ly Ground Truth Kỳ Vọng (Blinding & Leakage Isolation):**
   - Expected-output ground truth, đáp số và nhãn chấm điểm không được nạp vào generation runner hoặc request payload. Runner chỉ nhận canonical RequestContract đã đóng băng.
   - Tuyệt đối không có `expected_volume`, `expected_answer`, `expected_topology`, `expected_rejection` hoặc nhãn chấm điểm nào được đưa vào request payload.
4. **Quy tắc lặp cố định ($K=3$):**
   - Mỗi ca hợp lệ thu thập đúng $K=3$ quan sát độc lập để đánh giá tính ngẫu nhiên và độ phân tán.
5. **Chính sách Không Thử Lại (No-Retry Rule):**
   - `RETRIES_PER_OBSERVATION = 0`. Mọi mã lỗi HTTP (400, 429, 500) hoặc timeout đều được ghi nhận nguyên trạng như một quan sát thất bại; không tự động backoff retry để tránh thiên lệch thời gian và che giấu lỗi nhà cung cấp.
6. **Lưu trữ bằng chứng bền vững ngoài Repository (External Durable Storage):**
   - Toàn bộ raw response từ nhà cung cấp phải được ghi ra thư mục ngoài repository bằng giao thức nguyên tử bền vững (`temp file -> flush -> fsync -> atomic replace -> read-back byte count & SHA-256 verify`).
   - Raw responses tuyệt đối không được commit vào git tree nhằm bảo vệ dung lượng và tính bảo mật.
   - Chỉ các chỉ số đã được khử nhạy cảm (sanitized metrics), mã lỗi và chuỗi băm xác minh SHA-256 mới được đưa vào artifact commit.
7. **Tính bất biến của Protocol (Protocol Invariance):**
   - Không được thay đổi bất kỳ tiêu chí hay giao thức nào sau khi quan sát dữ liệu live. Mọi hiệu chỉnh phát sinh sau này bắt buộc phải tạo một tầng sửa đổi riêng (`CORRECTION_LAYER`) và đăng ký chuỗi `CORRECTED_BY`.

---

## 3. Kiểm Kê & Thẩm Định Nguồn Gốc COMMON_INPUT (18 Ca Đóng Băng)

Toàn bộ 18 ca đánh giá đóng băng đã được kiểm toán toàn diện về nguồn gốc xuất xứ, tính tương thích với Pydantic schema của production và xác nhận không có hiện tượng rò rỉ dữ liệu (`Data Leakage`):

| Case ID | Họ Hình Học (Family) | Phân Loại | Nguồn Gốc Hợp Đồng (`request_contract_source`) | Canonical SHA-256 | Parse Valid | Leakage Check | Expected Execution Path |
|---|---|---|---|---|---|---|---|
| `P01` | Pyramid | Positive | `multicase-benchmark/CASE_REGISTRY.json` + `GROUND_TRUTH.json` | `d314876d5e3e...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `P02` | Pyramid | Positive | `multicase-benchmark/CASE_REGISTRY.json` + `GROUND_TRUTH.json` | `55902a6a1222...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `P03` | Pyramid | Positive | `multicase-benchmark/CASE_REGISTRY.json` + `GROUND_TRUTH.json` | `3d552b5e4fcc...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `P04` | Pyramid | Positive | `multicase-benchmark/CASE_REGISTRY.json` + `GROUND_TRUTH.json` | `412080196c57...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `P05` | Pyramid | Positive | `multicase-benchmark/CASE_REGISTRY.json` + `GROUND_TRUTH.json` | `82b4e8d167f2...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `P06` | Pyramid | Positive | `multicase-benchmark/CASE_REGISTRY.json` + `GROUND_TRUTH.json` | `b709aacc24bf...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `P07` | Pyramid | Positive | `multicase-benchmark/CASE_REGISTRY.json` + `GROUND_TRUTH.json` | `45d22af2982e...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `P08` | Pyramid | Positive | `multicase-benchmark/CASE_REGISTRY.json` + `GROUND_TRUTH.json` | `f9604fce9741...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `N01` | Pyramid | Negative | `test_completion_runner_repair.py:DOC_DUNG_CA_AM` | `725142be87b9...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `N02` | Pyramid | Negative | `test_completion_runner_repair.py:DOC_DUNG_CA_AM` | `f01b7bde48b4...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `N03` | Pyramid | Negative | `test_completion_runner_repair.py:DOC_DUNG_CA_AM` | `76ba79249c95...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `N04` | Pyramid | Negative | `test_completion_runner_repair.py:DOC_DUNG_CA_AM` | `73f20ad3e9c3...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `PRISM_P02` | Prism | Positive | `primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json` | `fa1d12c33224...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `PRISM_P03` | Prism | Positive | `primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json` | `2f11864eab0c...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `PRISM_P04` | Prism | Positive | `primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json` | `aa3dff92c71d...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `PRISM_P05` | Prism | Positive | `primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json` | `3e3f7f351836...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `PRISM_N02` | Prism | Negative | `primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json` | `b9f4a7342d61...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |
| `PRISM_N03` | Prism | Negative | `primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json` | `3eeaf8cbb0a8...` | `True` | `PASS` | `REACHES_LLM_SYNTHESIS` |

*Ghi chú:* Toàn bộ 18 chuỗi băm `canonical_request_contract_sha256` đã được kiểm chứng tái lập 100% qua hai lượt serialize độc lập không có sai khác.

---

## 4. Ngân Sách Request Xác Thực & Cấu Trúc Khóa Trần

Căn cứ trên đường thực thi của hệ thống production ở chế độ mặc định (`DEFAULT_MODE = "LLM_ONLY"`), khi hợp đồng dữ kiện `RequestContract` được truyền trực tiếp vào pipeline:
1. `quyet_dinh_dinh_tuyen(contract)` trả về `"DISABLED"` (compiler không được kích hoạt).
2. Không có bộ lọc hay cổng từ chối nào đứng trước tầng sinh chương trình.
3. Do đó, cả 18 ca đều đi thẳng vào `stage_semantic_program` (`CASES_REACHING_LLM_SYNTHESIS = 18`, `CASES_REJECTED_BEFORE_SYNTHESIS = 0`).

### Bảng tính toán ngân sách request chính xác:

$$\text{PLANNED\_LIVE\_SYNTHESIS\_REQUESTS} = 18 \times 3 = 54$$

- `SHARED_ANALYZE_REQUESTS` = **0**
- `PLANNED_OBSERVATIONS_PER_CASE` = **3**
- `MAX_SYNTHESIS_REQUESTS_PER_CASE` = **3**
- `RETRIES_PER_OBSERVATION` = **0**
- `ABSOLUTE_REQUEST_CAP` = **54**
- **Cấm hoàn toàn:** Không được gọi các stage `semantic_analyze`, `image_extraction` hoặc `repair`. Bất kỳ yêu cầu nào nằm ngoài stage `semantic_program` đều bị chặn dừng (`SecurityViolationError`).

---

## 5. Ràng Buộc Yêu Cầu Đóng Băng (Request Binding)

Mỗi yêu cầu gửi đến mô hình trong đợt live collection đều bị ràng buộc cố định bởi các tham số và băm danh tính:

- **Model:** `gemini-2.5-flash`
- **Temperature:** `0.1`
- **Timeout:** `120.0` giây
- **Observation Indexes:** `[1, 2, 3]`
- **System Prompt:** `skills/geometry_program_generator.md`  
  $$\text{SHA-256} = \text{0d370e116e6280b4b4e9a71ab67039b049571e487bb51cbacd77576a72077ddf}$$
- **Sanitized Response Schema:** `_sanitize_gemini_schema(generate_json_schema())`  
  $$\text{SHA-256} = \text{74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b}$$
- **Request Body Hash Rule:** Băm SHA-256 của chuỗi JSON chuẩn tắc (`sort_keys=True, separators=(',', ':'), ensure_ascii=False`) của phần thân `generateContent` (không chứa API key).
- **Tính Tất Định:** Hai lần dựng request body độc lập cho cùng một ca cho ra kết quả trùng khớp từng byte (byte-identical). Không có trường động nào (như timestamp hay nonce) trong thân request.

---

## 6. Cơ Chế Thẩm Định & Phòng Vệ Của Apparatus (`collect_llm_only_paired_baseline.py`)

Bộ runner thu thập được trang bị 2 chế độ vận hành:

1. **Chế độ `--dry-run` (Đã chạy & kiểm chứng PASS):**
   - Không yêu cầu API key (`api_key = None`).
   - Không kết nối mạng (`network_requests = 0`).
   - Kiểm tra tính toàn vẹn của registry 18 ca, kiểm toán ngân sách và khớp toàn bộ chuỗi băm.
2. **Chế độ `--execute-live` (Dành riêng cho wave live tương lai):**
   - Đòi hỏi cờ xác nhận tường minh: `--confirm-live-execution`.
   - Bắt buộc chỉ định thư mục xuất nằm ngoài repository: `--output-dir`.
   - Ghi đĩa nguyên tử bền vững: tệp tạm $\rightarrow$ `flush()` $\rightarrow$ `os.fsync()` $\rightarrow$ `os.replace` $\rightarrow$ đọc lại đối chiếu byte và SHA-256.
   - Cơ chế phòng vệ duplicate: một bộ đôi `(case_id, obs_index)` chỉ được thực thi đúng một lần duy nhất.
   - Cơ chế khóa cứng trần: request thứ 55 lập tức ngắt phiên với lỗi `BudgetExceededError`.

---

## 7. Bằng Chứng Kiểm Thử Ngoại Tuyến (Fake Transport Test Suite)

Tất cả 15 bài kiểm thử đơn vị tại [`backend/tests/research/test_llm_only_paired_baseline_collector.py`](file:///d:/Documents/projects/algo-sim/backend/tests/research/test_llm_only_paired_baseline_collector.py) đã đạt trạng thái **15/15 PASSED**:

1. `test_dry_run_offline_safe` — PASS
2. `test_durable_atomic_write_success` — PASS
3. `test_durable_atomic_write_partial_write_failure` — PASS
4. `test_durable_atomic_write_hash_mismatch_failure` — PASS
5. `test_fake_transport_http_200_valid` — PASS
6. `test_fake_transport_schema_parse_failure` — PASS
7. `test_fake_transport_http_400` — PASS
8. `test_fake_transport_http_429` — PASS
9. `test_fake_transport_http_500` — PASS
10. `test_fake_transport_timeout` — PASS
11. `test_budget_overflow_prevention` — PASS
12. `test_accidental_forbidden_stages_rejected` — PASS
13. `test_duplicate_case_observation_rejected` — PASS
14. `test_unconfirmed_live_execution_rejected` — PASS
15. `test_output_dir_inside_repo_rejected` — PASS

---

## 8. Cổng Quyết Định (Decision Gate)

```yaml
STATUS: LIVE_BASELINE_COLLECTION_PREREGISTERED
COMMON_INPUT_CASE_COUNT: 18
COMMON_INPUT_PARSE_VALID_COUNT: 18
COMMON_INPUT_LEAKAGE_FREE_COUNT: 18
CASES_REACHING_LLM_SYNTHESIS: 18
CASES_REJECTED_BEFORE_SYNTHESIS: 0
SHARED_ANALYZE_REQUESTS: 0
PLANNED_OBSERVATIONS_PER_CASE: 3
PLANNED_LIVE_SYNTHESIS_REQUESTS: 54
ABSOLUTE_REQUEST_CAP: 54
RETRIES: 0
DRY_RUN_RESULT: PASS
FAKE_TRANSPORT_TEST_RESULT: 15_OF_15_PASSED
FINAL_DECISION: LIVE_BASELINE_COLLECTION_PREREGISTERED
NEXT_ACTION: EXECUTE_LIMITED_LIVE_LLM_BASELINE_COLLECTION
```
