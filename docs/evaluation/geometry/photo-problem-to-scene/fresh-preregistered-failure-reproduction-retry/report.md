# FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY

## 1. TỔNG QUAN VÀ BỐI CẢNH

* **Repository**: `D:\Documents\projects\algo-sim`
* **Branch**: `feat/photo-problem-to-scene`
* **START_HEAD**: `c6c6448e3fc045fb44252700fcb8c008e6b09a02`
* **PREREGISTRATION_COMMIT**: `934b4aebf46d37a222b5805453744e7506063b60`
* **MAIN_HEAD**: `085cae67392d3607ad0a58a7f48c17d8a5e5157d`
* **CANDIDATE_HASH**: `077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1` (103 files)
* **CACHE_VERSION**: `99`
* **Model**: `gemini-2.5-flash`, Temperature: `0.1`, Timeout: `120 s`
* **Dataset Class**: `DEVELOPMENT_FAILURE_REPRODUCTION_RETRY`
* **Execution Worktree**: `D:\tmp\fpfr-retry-clean` (detached, clean)
* **Architecture Mode**: `LLM_ONLY`

Wave đo live retry này gửi đúng một Analyze request cho từng ca `P03` và `P05` (tổng ngân sách transport: 2 Analyze, 0 Vision, 0 Synthesis, 0 Repair, 0 Retry), nhằm kiểm chứng độc lập xem lỗi lịch sử `MODEL_MALFORMED_RELATION` có tái diễn hay không sau khi runner async lifecycle và bằng chứng đo đã được sửa và đối soát hoàn toàn.

---

## 2. KIỂM CHỨNG TRƯỚC LIVE (PRE-LIVE GATES)

18/18 cổng tiền kiểm pre-live đã PASS:
1. **Branch & HEAD**: Đúng nhánh `feat/photo-problem-to-scene` tại START_HEAD `c6c6448e`.
2. **Main HEAD**: Giữ nguyên `085cae67392d3607ad0a58a7f48c17d8a5e5157d`.
3. **Source Tree**: Chỉ bẩn bởi ` D frontend/public/favicon.svg` của user.
4. **Execution Worktree**: Sạch hoàn toàn tại `D:\tmp\fpfr-retry-clean`.
5. **Candidate Verify**: `077dbc6b...` (103 files) PASS.
6. **Cache Identity**: Khóa khớp version 99 PASS.
7. **Manifest & Ground Truth**:
   - Manifest: `e043903849ebd5799ac87e788bacea95e31277cbc528cff21060ff873e29b60a` (LF)
   - Ground Truth: `115c0518a1997fa719500415d876a0a864a7fcb695170e88369e9ba9177793af` (LF)
8. **Prompt & Schema**:
   - Prompt: `backend/app/ai/skills/geometry_analyze.md` -> `50a076e15ed9189ab1e664d7d26f3a4b3450178802bc3826a3b4164e52d63500`
   - Schema: `analyze_schema_for("hinh_hoc")` -> `0542161e56ecca5e224964200208be93a648af93a14f6e733c94dedef99c2b7b`
9. **Runner Identity**:
   - Runner Path: `backend/scripts/run_preregistered_failure_reproduction.py`
   - Runner File SHA-256 (LF): `089de2103b495b157504daaf4c8c0d267f35713c2c2e7ffe788cc371b964356f`
   - Runner Code Commit: `866a1257bf85ad742ed61e65c77578e0f5373352`
10. **Trace Contract**: `analyze-relation-structure-trace/1` -> `b429618c8577e591baa3050c20ebf579f6cc49717f62eaaae294313bbb5ab416`
11. **Request Body Determinism**: Tái lập 2 lần độc lập trùng byte 100%.
12. **Request Hash Parity**:
    - P03: `6a2090edcc35c7819e808cd905dc0f6eda463dd5e88717d8cbb646a1f93aeca4`
    - P05: `8a1497359004583e876a5b88787a6d02beb851ac7d7057688351745c85b30b5a`
13. **Budget Proof**: Chặn request thứ 3 trước transport.
14. **Fake Transport Proof**: 18 mock fixtures kiểm chứng state machine và atomic journal.
15. **Focused Tests**: 67/67 passed (100%).
16. **Full Backend Suite**: 5942 passed, 1 skipped, 3 deselected, 0 failed.
17. **Secret Scan Pre-live**: 0 findings, 0 leaks.
18. **Preregistration Commit**: Đã tạo commit `934b4aeb` đóng băng trước request đầu tiên.

---

## 3. KẾT QUẢ ĐO LIVE CHO TỪNG CA

### Ca P03

* **HTTP Status**: 200
* **Latency**: 5776.31 ms
* **Transport Outcome**: Hoàn tất thành công (1 request duy nhất)
* **Số lượng quan hệ**: 2 quan hệ hình học
* **Các quan hệ trả về**:
  1. `perpendicular_lines`: `line` (2 điểm), `other_line` (2 điểm), `source_fact_id` hợp lệ.
  2. `perpendicular_line_plane`: `line` (2 điểm), `plane` (3 điểm), `source_fact_id` hợp lệ.
* **Pydantic Validation**: `pydantic_error_type: null` — PASS.
* **Semantic Contract Validation**: `SR._chuan_hoa_mot` trả về `loi = None` — PASS.
* **Source Fact Resolution**: `source_fact_resolved: true` (cả 2 quan hệ ghim đúng fact khai báo).
* **Point Reference Validity**: `point_reference_valid: true` (toàn bộ điểm nằm trong danh sách khai báo).
* **Accepted**: `true` cho cả 2 quan hệ.
* **Downstream Replay (Offline)**:
  - Primitive Compiler: `SUPPORTED`
  - Topology Validation: `PASS`
  - Final Memory: `PASS`
  - Đáp số số học: `21.0` (Khớp 100% với đáp số ground truth!)
* **Outcome Phân Loại**: `FAILURE_NOT_REPRODUCED`
* **Root Cause**: `CANONICAL_VALID`
* **Độ tin cậy**: `HIGH`

### Ca P05

* **HTTP Status**: 200
* **Latency**: 4372.73 ms
* **Transport Outcome**: Hoàn tất thành công (1 request duy nhất)
* **Số lượng quan hệ**: 2 quan hệ hình học
* **Các quan hệ trả về**:
  1. `perpendicular_lines`: `line` (2 điểm), `other_line` (2 điểm), `source_fact_id` hợp lệ.
  2. `perpendicular_line_plane`: `line` (2 điểm), `plane` (3 điểm), `source_fact_id` hợp lệ.
* **Pydantic Validation**: `pydantic_error_type: null` — PASS.
* **Semantic Contract Validation**: `SR._chuan_hoa_mot` trả về `loi = None` — PASS.
* **Source Fact Resolution**: `source_fact_resolved: true` (cả 2 quan hệ ghim đúng fact khai báo).
* **Point Reference Validity**: `point_reference_valid: true` (toàn bộ điểm nằm trong danh sách khai báo).
* **Accepted**: `true` cho cả 2 quan hệ.
* **Downstream Replay (Offline)**:
  - Primitive Compiler: `SUPPORTED`
  - Topology Validation: `PASS`
  - Final Memory: `PASS`
  - Đáp số số học: `5.0` (Khớp 100% với đáp số ground truth!)
* **Outcome Phân Loại**: `FAILURE_NOT_REPRODUCED`
* **Root Cause**: `CANONICAL_VALID`
* **Độ tin cậy**: `HIGH`

---

## 4. KẾT LUẬN CLUSTER VÀ PHÂN TÍCH NGUYÊN NHÂN

* **P03_RESULT**: `FAILURE_NOT_REPRODUCED`
* **P05_RESULT**: `FAILURE_NOT_REPRODUCED`
* **CLUSTER_REPRODUCTION_RESULT**: `NOT_REPRODUCED`
* **CLUSTER_HOMOGENEITY**: `HIGH`
* **ROOT_CAUSE**: `CANONICAL_VALID`
* **CAUSALITY_CONFIDENCE**: `HIGH`

### Nhận định kỹ thuật

1. **Lỗi không tái diễn trong lần đo này**:
   Trong đợt đo live retry này, cả hai ca `P03` và `P05` đều trả về phản hồi JSON hợp lệ với cấu trúc quan hệ hoàn toàn chuẩn tắc theo đúng schema `analyze_schema_for("hinh_hoc")`. Không xuất hiện lỗi `MODEL_MALFORMED_RELATION`.
2. **Khớp nối xuôi dòng thành công (End-to-End)**:
   Khi đưa các quan hệ do mô hình sinh qua FactGraph, Primitive Compiler, Topology, Final Memory và Answer Scorer, cả hai ca đều được biên dịch thành công (`SUPPORTED`) và cho ra kết quả số học chính xác tuyệt đối (`21.0` cho P03 và `5.0` cho P05).
3. **Biến thiên mô hình (Model Variance)**:
   Bằng chứng cho thấy hiện tượng thất bại trước đây ở `P03` và `P05` trong benchmark ban đầu mang tính chất biến thiên xác suất của mô hình (sampling / model stochasticity) tại thời điểm đo cũ, chứ không phải do thiếu sót cấu trúc vĩnh viễn trong prompt hay schema hiện tại.
4. **Quy tắc dừng**:
   Không sửa prompt, schema hay normalizer khi lỗi không tái hiện và hợp đồng hợp lệ hoàn toàn. Theo đúng ma trận quyết định `NEXT_ACTION MAPPING`, hành động tiếp theo là `MODEL_VARIANCE_EVIDENCE_REVIEW`.

---

## 5. BẢO TOÀN DỮ LIỆU VÀ BẢO MẬT

* **Lưu trữ dữ liệu thô**: `RAW_OUTPUT_STORED = NO`. Dữ liệu thô của mô hình đã bị loại bỏ ngay trong bộ nhớ trước khi ghi đĩa.
* **Rò rỉ bí mật**: `SECRET_LEAKS = 0`. Toàn bộ 17 tệp JSON artifact đều được quét và đạt trạng thái PASS.
* **Tính bất biến của lịch sử**: Báo cáo và artifact của các wave trước (`fresh-preregistered-failure-reproduction/`, `safe-structure-trace-repair-offline/`) được giữ nguyên vẹn 100%.
* **Thay đổi mã nguồn**: `PRODUCT_CODE_CHANGED = NO`, `RUNNER_CHANGED = NO`, `PROMPT_CHANGED = NO`, `SCHEMA_CHANGED = NO`.
* **Thay đổi working tree user**: ` D frontend/public/favicon.svg` được bảo tồn nguyên trạng, không bị chạm, không stage, không commit.

---

## 6. DANH MỤC ARTIFACT TẠO RA

Thư mục: `docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/`

1. `PRECHECK.json`
2. `PREREGISTRATION.json`
3. `RUNNER_BINDING.json`
4. `REQUEST_HASH_REGISTRY.json`
5. `TRANSPORT_BUDGET_PROOF.json`
6. `SAFE_STRUCTURE_TRACE_CONTRACT.json`
7. `CASE_JOURNAL_REDACTED.json`
8. `SAFE_STRUCTURE_TRACE_REDACTED.json`
9. `CASE_RESULTS_REDACTED.json`
10. `RELATION_QUALITY_BY_CASE.json`
11. `DOWNSTREAM_REPLAY.json`
12. `TOKEN_USAGE_BY_CASE.json`
13. `LATENCY_BY_CASE.json`
14. `STATE_MACHINE_PROOF.json`
15. `TEST_RESULTS.json`
16. `SECRET_SCAN.json`
17. `FINAL_CLASSIFICATION.json`
