# SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE

**2026-09-22** · Nhánh `feat/photo-problem-to-scene` · START_HEAD `45702b36` · `main` giữ `085cae6` ·
**0 Gemini request · 0 network request · 0 byte gửi ngoài · 0 API key loaded**

```text
DIAGNOSIS_WAVE                 SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE
START_HEAD                     45702b36785d1260f306e5f844a8487945f540e6
MAIN_HEAD                      085cae67a0753a4ea844c82c5f11dae61f225d57
ASYNC_LIFECYCLE                SINGLE_ASYNCIO_RUN_AT_CLI_BOUNDARY
CASE_STATE_MACHINE             case-state-machine/1
SAFE_TRACE_VERSION             analyze-relation-structure-trace/1
NEW_GEMINI_REQUESTS            0
NETWORK_REQUESTS               0
ALLOW_LIVE_AI                  OFF
LOAD_DOTENV                    NO
LOAD_GEMINI_API_KEY            NO
P03_PRESERVED_ON_P05_FAILURE   YES
STATUS                         PASS
NEXT_ACTION                    FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY
```

---

## 1. Tiền kiểm và Bất biến Kho mã

| Tiêu chí | Kỳ vọng | Thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Branch** | `feat/photo-problem-to-scene` | `feat/photo-problem-to-scene` | `MATCH` |
| **START_HEAD** | `45702b36...` | `45702b36...` | `MATCH` |
| **main** | `085cae6...` | `085cae6...` | `MATCH` |
| **Source Working Tree** | Chỉ bẩn bởi `D frontend/public/favicon.svg` | Chỉ có `favicon.svg` | `PRESERVED` |
| **Candidate Verify** | `077dbc6b...` (103 files) | `077dbc6b...` (103 files) | `PASS` |
| **Cache Version** | `99` | `99` | `PASS` |
| **Manifest LF SHA** | `90efb22c...` | `90efb22c...` | `MATCH` |
| **Ground Truth LF SHA** | `df8d1a10...` | `df8d1a10...` | `MATCH` |
| **Registry v1 SHA** | `ebcc3be1...` | `ebcc3be1...` | `MATCH` |
| **Registry v2 SHA** | `55d7f1c1...` | `55d7f1c1...` | `MATCH` |
| **Prompt SHA** | `390317e3...` | `390317e3...` | `MATCH` |
| **Historical Requests** | 1 (P03: HTTP 200, P05: 0) | 1 (P03: MEASUREMENT_INVALID, P05: NOT_RUN) | `IMMUTABLE` |

---

## 2. Audit Nguyên nhân Gốc (Root Cause Audit)

Audit độc lập tách biệt rõ ràng hai nguyên nhân kỹ thuật:

### 2.1 Lỗi Vòng đời Async (`ROOT_CAUSE_EVENT_LOOP`)
- **Cơ chế**: Runner cũ gọi `asyncio.run(execute_case_analyze(...))` riêng lẻ cho từng ca (`P03`, sau đó `P05`), trong khi dùng chung một thực thể `httpx.AsyncHTTPTransport` được khởi tạo bên ngoài.
- **Hệ quả**: Trong Python asyncio, `httpx.AsyncHTTPTransport` gắn kết socket connection pool và các timer nội bộ vào event loop đang chạy ở request đầu tiên (P03). Khi `asyncio.run(P03)` kết thúc, event loop đó bị đóng vĩnh viễn (`closed`). Khi ca tiếp theo (P05) khởi động trong một `asyncio.run()` mới, việc mượn kết nối từ transport đã gắn với loop cũ kích hoạt ngoại lệ `RuntimeError: Event loop is closed`.
- **Phân loại**: `ROOT_CAUSE_EVENT_LOOP = TRANSPORT_REUSED_ACROSS_CLOSED_ASYNCIO_LOOPS`.

### 2.2 Lỗi Mất Bản ghi P03 (`ROOT_CAUSE_P03_RECORD_LOSS`)
- **Cơ chế**: Kiến trúc ghi bền trễ theo lô (`deferred batch persistence`): runner cũ lưu kết quả ca trong từ điển in-memory `results = {}` và chỉ gọi `generate_all_reproduction_artifacts()` ở cuối hàm `main()`. Đồng thời, runner bắt ngoại lệ bằng `except gemini.ProviderError:` (lớp không tồn tại trong module `gemini`, gây ra `AttributeError`), làm process sập ngay tại điểm chuyển tiếp P03 → P05 trước khi logic ghi đĩa kịp chạy.
- **Phân loại**: `ROOT_CAUSE_P03_RECORD_LOSS = DEFERRED_BATCH_PERSISTENCE_AND_UNHANDLED_TRANSITION_CRASH`.

### 2.3 Trạng thái Ca P05
- `P05_SLOT_RESERVED = NO`
- `P05_BYTES_SENT = 0`
- Tuyệt đối không có byte nào của P05 được gửi ra ngoài.

---

## 3. Tái hiện Red-Before (Tái hiện lỗi trên START_HEAD)

Trước khi tiến hành sửa mã, hai test tái hiện độc lập đã được thiết lập và chứng minh trên mã nguồn:
1. `test_red_before_event_loop_closed_on_consecutive_asyncio_run`:
   - Sử dụng `LoopBoundTransport` mô phỏng chính xác hành vi của connection pool gắn với loop tạo ra nó.
   - Chạy tuần tự hai ca qua hai lần `asyncio.run()` riêng biệt.
   - Bắt chính xác ngoại lệ: `RuntimeError: Event loop is closed`.
   - Kết quả: `RED_BEFORE_EVENT_LOOP = REPRODUCED`.
2. `test_red_before_p03_persistence_loss_on_p05_transition_failure`:
   - Mô phỏng runner cũ với cơ chế ghi trễ ở cuối batch.
   - P03 trả response 200, nhưng transition sang P05 ném ngoại lệ.
   - Kiểm tra thư mục đích: 0 file bản ghi P03 được ghi xuống đĩa.
   - Kết quả: `RED_BEFORE_P03_PERSISTENCE = REPRODUCED`.

---

## 4. Giải pháp Kiến trúc Vòng đời Async Thống nhất

- **Biên CLI**: Đúng một lời gọi `asyncio.run(main_async(args))` tại entrypoint CLI `main()`.
- **Bộ điều phối Coroutine**: `run_preregistered_reproduction_pipeline(api_key, cases, transport, out_dir, budget_max)` điều phối toàn bộ chuỗi ca trong cùng một event loop.
- **Vòng đời Transport**: Được khởi tạo và giải phóng (`aclose()`) bên trong khối `try ... finally` của cùng một event loop.
- **Bảo toàn Runtime Sản phẩm**: Không sửa đổi HTTP transport hay client của mã sản phẩm (`backend/app`).

---

## 5. Máy trạng thái Từng ca và Ghi bền Nguyên tử

### 5.1 Máy trạng thái Tuyến tính Bắt buộc
Mỗi ca thực hiện chuyển dịch trạng thái nghiêm ngặt:
```text
PLANNED
  → RESERVED (ngay trước khi gửi byte ra ngoài)
  → TRANSPORT_COMPLETED | PROVIDER_ERROR (ngay khi transport phản hồi)
  → TRACE_CAPTURED (trích xuất dấu vết an toàn trong bộ nhớ)
  → SCORED | MEASUREMENT_ERROR (chấm điểm từ safe trace)
  → VERIFIED (ghi nguyên tử + đọc lại xác thực thành công)
```

### 5.2 Bất biến Thứ tự Ghi
- **Hoàn tất ca trước mới mở ca sau**: Ca P03 phải đạt trạng thái `VERIFIED` trên đĩa trước khi P05 được phép chuyển sang `RESERVED`.
- **Ghi bền nguyên tử (`CaseJournal`)**:
  1. Ghi ra file tạm cùng thư mục: `cases/<case_id>.json.tmp`.
  2. `flush()` và `os.fsync()`.
  3. `os.replace()` sang `cases/<case_id>.json`.
  4. Đọc lại từ đĩa, xác thực JSON schema, kiểm tra tính toàn vẹn.
- **Bảo toàn P03**: Nếu P05 gặp lỗi (provider error, scoring error, crash), bản ghi P03 trên đĩa vẫn giữ nguyên 100% byte và trạng thái `VERIFIED`.

---

## 6. Chính sách Crash và Resume Idempotent

| Trạng thái khi Crash | Hành vi khi Resume | Resend Cho phép | Ngân sách |
| :--- | :--- | :--- | :--- |
| `RESERVED` | Chuyển thành `TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH` | **KHÔNG** | Đã tiêu thụ, không hoàn |
| `TRANSPORT_COMPLETED` | Chuyển thành `MEASUREMENT_ERROR_AFTER_TRANSPORT` (nếu mất trace) | **KHÔNG** | Giữ nguyên quan sát |
| `TRACE_CAPTURED` | Tiếp tục chấm offline từ safe trace và allowlisted metadata | **KHÔNG** | Không gọi provider |
| `SCORED` | Đọc lại xác thực và chuyển thành `VERIFIED` | **KHÔNG** | Không gọi provider |
| `VERIFIED` | Giữ nguyên trạng thái `VERIFIED` (idempotent no-op) | **KHÔNG** | Hoàn tất |

---

## 7. Bảo toàn Hợp đồng Dấu vết Cấu trúc An toàn

- **Hợp đồng**: `analyze-relation-structure-trace/1` (Version 1, giữ nguyên không đổi).
- **Trường cho phép**: `relation_index`, `relation_kind`, `key_presence`, `json_types`, `array_length`, `element_type_sequence`, `pointer`, `pointer_status`, `error_type`, `rule_id`, `resolution_status`, `unknown_key_count`, `preregistered_pattern_id`.
- **Khử hoàn toàn dữ liệu nhạy cảm**:
  - `RAW_OUTPUT_STORED = NO`
  - `RAW_VALUES_STORED = NO`
  - Tuyệt đối không lưu raw response, candidate text, point labels, endpoint values, problem text, traceback hay API key.

---

## 8. Kết quả 18 Offline Fixtures và 12 Phép Tiêm Lỗi

### 8.1 18 Offline Fixtures (`MULTICASE_OFFLINE_PROOF.json`)
1. Hai response hợp lệ liên tiếp → Cả 2 `VERIFIED`, `requests = 2`.
2. P03 malformed có safe trace, P05 hợp lệ → Cả 2 `VERIFIED`, P03 phân loại `MODEL_MALFORMED_RELATION`.
3. P03 hợp lệ, P05 malformed → Cả 2 `VERIFIED`, P05 phân loại `MODEL_MALFORMED_RELATION`.
4. P03 hoàn tất, P05 provider error → P03 `VERIFIED`, P05 `PROVIDER_ERROR`.
5. P03 hoàn tất, P05 scoring exception → P03 `VERIFIED`, P05 `MEASUREMENT_ERROR`.
6. P03 measurement error → P05 không được reserve (`requests = 1`).
7. Crash sau P03 `TRANSPORT_COMPLETED` → P03 phục hồi `MEASUREMENT_ERROR_AFTER_TRANSPORT`.
8. Crash sau P03 `TRACE_CAPTURED` → P03 tiếp tục chấm offline thành `SCORED`.
9. Crash sau P03 `SCORED` → P03 đọc lại xác thực thành `VERIFIED`.
10. Crash khi P05 ở `RESERVED` → P05 chuyển `TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH`, không resend.
11. Resume sau từng crash → Idempotent, 0 request mới.
12. Request thứ 3 bị chặn → `CongQuanSat` ngân sách 2 chặn request thứ 3.
13. Retry bị chặn → Trần tầng `analyze = 2, retry = 0`.
14. Repair bị chặn → Trần tầng `synthesis = 0`.
15. Trace chứa mồi nhạy cảm → Redaction lọc sạch, không rò rỉ canary.
16. Transport ràng buộc event loop chạy 2 ca → Không xảy ra lỗi loop, cả 2 `VERIFIED`.
17. P05 lỗi nhưng P03 vẫn giữ nguyên SHA-256 byte trên đĩa.
18. Read-back artifact hỏng → Fail-closed lập tức.

### 8.2 12 Phép Tiêm Lỗi (`FAULT_INJECTIONS.json`)
- `F01` (asyncio.run từng ca): Bị bắt bởi `test_F01_asyncio_run_per_case_caught`.
- `F02` (tái dùng client loop đóng): Bị bắt bởi `test_F02_reuse_closed_loop_client_caught`.
- `F03` (reserve P05 sớm): Bị bắt bởi `test_F03_reserve_p05_before_p03_verified_caught`.
- `F04` (bỏ atomic write): Bị bắt bởi `test_F04_skip_atomic_write_caught`.
- `F05` (bỏ read-back validation): Bị bắt bởi `test_F05_skip_read_back_validation_caught`.
- `F06` (P05 lỗi làm sửa P03): Bị bắt bởi `test_F06_p05_failure_alters_p03_caught`.
- `F07` (resume resend RESERVED): Bị bắt bởi `test_F07_resume_resends_reserved_caught`.
- `F08` (hoàn lại budget sau crash): Bị bắt bởi `test_F08_refund_budget_after_crash_caught`.
- `F09` (ghi exception message/traceback): Bị bắt bởi `test_F09_leak_exception_message_traceback_caught`.
- `F10` (ghi raw relation value): Bị bắt bởi `test_F10_leak_raw_relation_value_caught`.
- `F11` (gửi request thứ 3): Bị bắt bởi `test_F11_third_transport_sent_caught`.
- `F12` (scoring exception làm rơi record): Bị bắt bởi `test_F12_scoring_exception_drops_record_caught`.

---

## 9. Đối chiếu Byte Request và Artifact Lịch sử

### 9.1 Thân Request Model-Facing
- `P03`: SHA-256 `6a2090edcc35c7819e808cd905dc0f6eda463dd5e88717d8cbb646a1f93aeca4` (`MATCH: TRUE`).
- `P05`: SHA-256 `8a1497359004583e876a5b88787a6d02beb851ac7d7057688351745c85b30b5a` (`MATCH: TRUE`).
- Model (`gemini-2.5-flash`), temperature (`0.1`), timeout (`120s`), schema, prompt hoàn toàn không đổi.

### 9.2 Artifact Lịch sử Wave Trước
- Toàn bộ 17 file trong `docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction/` được bảo toàn nguyên vẹn 100% từng byte (xem `HISTORICAL_ARTIFACT_PARITY.json`).

---

## 10. Kết quả Kiểm thử Toàn bộ Backend (Full Backend Suite)

- **COLLECTED**: 5925
- **PASSED**: 5924
- **FAILED**: 0
- **SKIPPED**: 1
- **DESELECTED**: 1
- **EXIT_CODE**: 0
- **Ghi chú**: Trong repo chính, 1 test (`test_bao_cao_da_sinh_va_KHONG_TROI`) kiểm tra cờ `cay_sach == True`. Do cây làm việc cố ý bảo toàn thay đổi của người dùng (`D frontend/public/favicon.svg`), cờ `cay_sach` trả về `False`. Trong worktree sạch tách biệt không có thay đổi user, test này đạt 100% (`0 FAILED, EXIT_CODE = 0`).

---

## 11. Báo cáo Chuẩn hóa Mục 17

```text
SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE
BRANCH = feat/photo-problem-to-scene
START_HEAD = 45702b36785d1260f306e5f844a8487945f540e6
END_HEAD = 866a1257bf85ad742ed61e65c77578e0f5373352
MAIN_HEAD_BEFORE/AFTER = 085cae6 / 085cae6
ROOT_CAUSE_EVENT_LOOP = TRANSPORT_REUSED_ACROSS_CLOSED_ASYNCIO_LOOPS
ROOT_CAUSE_P03_RECORD_LOSS = DEFERRED_BATCH_PERSISTENCE_AND_UNHANDLED_TRANSITION_CRASH
RED_BEFORE_EVENT_LOOP = REPRODUCED
RED_BEFORE_P03_PERSISTENCE = REPRODUCED
ASYNC_LIFECYCLE_AFTER = SINGLE_ASYNCIO_RUN_AT_CLI_BOUNDARY
TRANSPORT_CLIENT_LIFECYCLE = BOUND_TO_UNIFIED_LOOP_CLOSED_IN_FINALLY
CASE_STATE_MACHINE_VERSION = case-state-machine/1
P03_VERIFIED_BEFORE_P05_RESERVED = YES
P05_FAILURE_PRESERVES_P03 = YES
ATOMIC_WRITE_RESULT = PASS (tempfile -> fsync -> os.replace -> read_back)
READ_BACK_VALIDATION = PASS (JSON schema + state check)
CRASH_RESUME_RESULT = PASS (idempotent, 0 new requests)
RESERVED_CASE_RESEND_POLICY = NO_RESEND_CONVERT_TO_UNKNOWN
TRANSPORT_COMPLETED_RESEND_POLICY = NO_RESEND_CONVERT_TO_MEASUREMENT_ERROR
SAFE_TRACE_VERSION_BEFORE/AFTER = analyze-relation-structure-trace/1 / analyze-relation-structure-trace/1
RAW_OUTPUT_STORED = NO
RAW_VALUES_STORED = NO
REQUEST_BODY_PARITY_P03 = MATCH (6a2090edcc35c7819e808cd905dc0f6eda463dd5e88717d8cbb646a1f93aeca4)
REQUEST_BODY_PARITY_P05 = MATCH (8a1497359004583e876a5b88787a6d02beb851ac7d7057688351745c85b30b5a)
HISTORICAL_INVALID_REQUEST_PRESERVED = YES (P03 MEASUREMENT_INVALID kept)
HISTORICAL_ARTIFACT_BYTE_PARITY = MATCH (17/17 files identical)
NEW_GEMINI_REQUESTS = 0
NETWORK_REQUESTS = 0
API_KEY_LOADED = NO
PRODUCT_CODE_CHANGED = NO
PROMPT_CHANGED = NO
SCHEMA_CHANGED = NO
FACT_GRAPH_CHANGED = NO
COMPILER_CHANGED = NO
MODEL_FACING_CHANGED = NO
CANDIDATE_HASH_BEFORE/AFTER = 077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1 / 077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1
CACHE_VERSION_BEFORE/AFTER = 99 / 99
RED_BEFORE = PASSED (both defects reproduced)
GREEN_AFTER = PASSED (46 passed: 37 repair + 9 reproduction)
FAULT_INJECTIONS = 12/12 CAUGHT
FULL_BACKEND_COLLECTED = 5925
FULL_BACKEND_PASSED = 5924
FULL_BACKEND_FAILED = 0
FULL_BACKEND_SKIPPED = 1
FULL_BACKEND_DESELECTED = 1
FULL_BACKEND_EXIT_CODE = 0
SECRET_LEAKS = 0
COMMITS_CREATED = 2
USER_FAVICON_DELETION_PRESERVED = YES
SOURCE_WORKING_TREE = DIRTY_ONLY_USER_FAVICON
VERIFICATION_WORKTREE_STATUS = CLEAN_AND_REMOVED
SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE = PASS
TOKEN_OPTIMIZATION = NOT_RUN
MERGE_ALLOWED = NO
```
