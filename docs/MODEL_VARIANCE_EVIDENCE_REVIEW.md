# MODEL_VARIANCE_EVIDENCE_REVIEW

## 1. TỔNG QUAN VÀ BỐI CẢNH

* **Repository**: `D:\Documents\projects\algo-sim`
* **Branch**: `feat/photo-problem-to-scene`
* **START_HEAD**: `d09331ea61d6a7d54b9516fb7ca97ac81de6087a`
* **MAIN_HEAD**: `085cae67392d3607ad0a58a7f48c17d8a5e5157d`
* **CANDIDATE_HASH**: `077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1` (103 files)
* **CACHE_VERSION**: `99`
* **Source Report**: `docs/FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY.md`
* **Source Report SHA-256**: `1aba30b4b9c1b720b87303ba7a9bd74c30966cd68bee1a23f206f56b2245e43e`
* **Số lượng artifact nguồn**: 17 JSON artifacts (toàn bộ 17 tệp đều được đối soát trùng byte 100%, không bị sửa đổi)
* **Tính chất wave**: 100% OFFLINE (0 Gemini requests, 0 network requests, API key không nạp, không sửa product code, không sửa live runner).

Wave này thực hiện rà soát độc lập và đính chính ba điểm chưa đáng tin cậy trong bằng chứng và báo cáo của wave đo live retry trước đó:
1. Giá trị token usage bị ghi nhận bằng `0` do lỗi chuyển đổi ngầm missing data.
2. Dấu vết quan hệ (structural trace) bị gắn nhãn false-positive `MULTIPLE_STRUCTURAL_DEFECTS` do cơ chế kiểm tra trường không nhận biết relation kind (kind-aware).
3. Nhầm lẫn giữa quan sát trạng thái đầu ra hiện tại (`CANONICAL_VALID`) với nguyên nhân gốc của lỗi lịch sử (`ROOT_CAUSE = CANONICAL_VALID`).

---

## 2. BẢO TOÀN KẾT QUẢ THỰC NGHIỆM ĐÃ ĐƯỢC CHỨNG MINH

Wave rà soát tái xác nhận và bảo toàn nguyên vẹn các kết quả thực nghiệm vững chắc từ wave live retry:
* **Không tái diễn lỗi lịch sử**: Cả hai ca `P03` và `P05` đều không gặp lỗi `MODEL_MALFORMED_RELATION`.
* **Hợp đồng ngữ nghĩa hợp lệ**: Hai hợp đồng Analyze đều vượt qua kiểm tra cú pháp JSON, xác thực Pydantic và chuẩn hóa quan hệ (`SR._chuan_hoa_mot` trả về `loi = None`).
* **Hạ nguồn xử lý thành công (End-to-End)**: FactGraph chấp nhận toàn bộ quan hệ, Primitive Compiler biên dịch thành công (`SUPPORTED`), Topology và Final Memory đều đạt chuẩn (`PASS`).
* **Đáp số chính xác tuyệt đối**: `P03` cho đáp số `21.0` (khớp ground truth `21.0`); `P05` cho đáp số `5.0` (khớp ground truth `5.0`).

---

## 3. AUDIT A — ĐÍNH CHÍNH TOKEN USAGE

### Nguyên nhân gốc
* Bộ chặn transport `CongQuanSat` chỉ quan sát các request gửi đi trước khi gửi mạng, không đọc nội dung phản hồi `httpx.Response` để trích xuất `usageMetadata`.
* Dữ liệu token usage trong nhật ký ca (`CaseJournal`) là dictionary rỗng `{}`.
* Bộ tổng hợp và báo cáo dùng `.get(..., 0)` để lấy giá trị số, vô tình biến dữ liệu không quan sát được / thiếu hụt thành số nguyên `0`.

### Chính sách và đính chính
* Theo quy định bất biến của kho (`aggregate_multicase_completion.py`): thiếu usage hoặc unobserved usage **bắt buộc** phải ghi `UNKNOWN`, tuyệt đối không dùng `0` thay thế cho missing data.
* Đính chính giá trị:
  - `P03_INPUT_TOKENS`: `UNKNOWN`
  - `P03_OUTPUT_TOKENS`: `UNKNOWN`
  - `P03_THOUGHT_TOKENS`: `UNKNOWN`
  - `P03_TOTAL_TOKENS`: `UNKNOWN`
  - `P05_INPUT_TOKENS`: `UNKNOWN`
  - `P05_OUTPUT_TOKENS`: `UNKNOWN`
  - `P05_THOUGHT_TOKENS`: `UNKNOWN`
  - `P05_TOTAL_TOKENS`: `UNKNOWN`
  - `AGGREGATE_TOKEN_RESULT`: `UNKNOWN`
  - `KNOWN_TOKEN_SUBTOTAL`: `NOT_AVAILABLE`

---

## 4. AUDIT B — ĐÍNH CHÍNH KIND-AWARE STRUCTURAL TRACE

### Nguyên nhân gốc
* Khi trích xuất dấu vết cấu trúc, `SafeStructureTraceExtractor` nhận dictionary sinh ra từ `GeometricRelation.model_dump()`.
* Model dump của Pydantic xuất toàn bộ các trường của model, bao gồm các tuple rỗng mặc định: `plane: ()` trên `perpendicular_lines` và `other_line: ()` trên `perpendicular_line_plane`.
* Extractor cũ:
  1. Kiểm tra độ dài mọi trường mà không lọc theo kind: thấy `plane` có độ dài 0 thay vì 3, `other_line` có độ dài 0 thay vì 2 -> báo `WRONG_ARRAY_ARITY`.
  2. Kiểm tra `"plane" in rel_obj` trên `perpendicular_lines` -> báo `KNOWN_FIELD_PLACED_AT_WRONG_LEVEL`.
* Việc phát hiện 2 defect trên các trường mặc định không áp dụng dẫn đến pattern `MULTIPLE_STRUCTURAL_DEFECTS`, tạo ra mâu thuẫn trực tiếp với trạng thái `accepted = True` và `loi = None`.

### Giải pháp và đính chính
* Xây dựng `kind_aware_trace_evaluator.py`:
  - Chỉ kiểm tra arity đối với các trường áp dụng cho relation kind tương ứng.
  - Tuple/list rỗng mặc định từ model dump không bị coi là lỗi sai tầng (`KNOWN_FIELD_PLACED_AT_WRONG_LEVEL`).
  - Thiết lập bất biến cốt lõi: Một quan hệ đã được normalizer và Pydantic chấp nhận (`accepted = True`) **tuyệt đối không bao giờ** mang nhãn structural defect.
* Đính chính dấu vết cấu trúc:
  - `P03_RELATION_0`: `CANONICAL_VALID`, pointer `/geometric_relations/0`, pointer_status `EXACT`.
  - `P03_RELATION_1`: `CANONICAL_VALID`, pointer `/geometric_relations/1`, pointer_status `EXACT`.
  - `P05_RELATION_0`: `CANONICAL_VALID`, pointer `/geometric_relations/0`, pointer_status `EXACT`.
  - `P05_RELATION_1`: `CANONICAL_VALID`, pointer `/geometric_relations/1`, pointer_status `EXACT`.
  - Số quan hệ accepted mang nhãn defect sau đính chính: `0`.

---

## 5. AUDIT C — TÁCH BẠCH OUTCOME VÀ CAUSALITY

Báo cáo live trước ghi `ROOT_CAUSE = CANONICAL_VALID` và `CAUSALITY_CONFIDENCE = HIGH`. Đây là sai sót về mặt phương pháp luận vì:
1. `CANONICAL_VALID` là trạng thái của đầu ra hiện tại, không phải là nguyên nhân gây ra thất bại lịch sử.
2. Một lượt retry thành công (`n = 1`) không đủ bằng chứng để xác lập cơ chế nhân quả của lỗi cũ trong quá khứ.
3. Không thể gán `CLUSTER_HOMOGENEITY = HIGH` cho một cụm lỗi khi không có lỗi nào xuất hiện trong lần chạy này.

### Ma trận phân tách chuẩn tắc
* **Trạng thái quan sát hiện tại**:
  - `P03_LIVE_OUTCOME = NOT_REPRODUCED_VALID_EXACT`
  - `P05_LIVE_OUTCOME = NOT_REPRODUCED_VALID_EXACT`
  - `CURRENT_OUTPUT_STATUS = CANONICAL_VALID`
  - `CURRENT_OUTCOME_CONCORDANCE = 2/2 NOT_REPRODUCED`
  - `CURRENT_OUTCOME_CONFIDENCE = HIGH`
* **Nguyên nhân lỗi lịch sử**:
  - `P03_HISTORICAL_ROOT_CAUSE = NOT_ESTABLISHED`
  - `P05_HISTORICAL_ROOT_CAUSE = NOT_ESTABLISHED`
  - `CLUSTER_HISTORICAL_ROOT_CAUSE = NOT_ESTABLISHED`
  - `CAUSALITY_CONFIDENCE = NOT_ESTABLISHED`
* **Đánh giá giả thuyết biến thiên mô hình (Model Variance)**:
  - `MODEL_VARIANCE_HYPOTHESIS = CONSISTENT_WITH_CURRENT_EVIDENCE` (Phù hợp với bằng chứng hiện có, nhưng chưa coi là chứng minh nhân quả tuyệt đối).
  - `FAILURE_CLUSTER_HOMOGENEITY = NOT_APPLICABLE_NO_CURRENT_FAILURES`

---

## 6. KIỂM THỬ VÀ TIÊM LỖI (FAULT INJECTIONS)

* **Red-before**: Đã chứng minh trên `START_HEAD` sự tồn tại của 3 lỗi diễn giải:
  1. Extractor cũ gán false-positive `MULTIPLE_STRUCTURAL_DEFECTS` trên quan hệ hợp lệ.
  2. Aggregator cũ biến dictionary rỗng `{}` thành số 0.
  3. Classifier cũ nâng `CANONICAL_VALID` thành `ROOT_CAUSE`.
* **Green-after**: 20/20 bài kiểm thử trong `backend/tests/geometry/test_model_variance_evidence_review.py` đều PASS.
* **10 Phép tiêm lỗi (F1 - F10)**:
  - F1: `.get("input_tokens", 0)` -> Bị chặn bởi `parse_token_count`.
  - F2: `usage or {'promptTokenCount': 0}` -> Bị chặn bởi `parse_token_count`.
  - F3: Dùng keyset chung cho mọi relation kind -> Bị chặn bởi kind-aware spec.
  - F4: Ép buộc `plane` cho `perpendicular_lines` -> Bị chặn bởi spec.
  - F5: Ép buộc `other_line` cho `perpendicular_line_plane` -> Bị chặn bởi spec.
  - F6: Gắn nhãn defect vào relation đã accepted -> Bị chặn bởi bất biến cốt lõi.
  - F7: Đổi historical root cause thành `CANONICAL_VALID` -> Bị chặn bởi `separate_outcome_and_causality`.
  - F8: Nâng causality confidence thành `HIGH` -> Bị chặn bởi `separate_outcome_and_causality`.
  - F9: Sửa đổi artifact lịch sử -> Bị phát hiện bởi kiểm tra tính toàn vẹn SHA-256.
  - F10: Rò rỉ dữ liệu raw cấm vào trace -> Bị bắt bởi cổng kiểm tra redaction.
* Toàn bộ 10 phép tiêm đều bị bắt và hoàn nguyên chính xác.

---

## 7. BẢO TOÀN TÍNH TOÀN VẸN VÀ BẢO MẬT

* **17 Artifact live và báo cáo lịch sử**: Giữ nguyên vẹn 100% SHA-256.
* **Mã nguồn sản phẩm**: `PRODUCT_CODE_CHANGED = NO`.
* **Live runner**: `LIVE_RUNNER_CHANGED = NO`.
* **Rò rỉ bí mật**: `SECRET_LEAKS = 0` (0 API keys, 0 raw model outputs, 0 traceback).
* **Working tree user**: ` D frontend/public/favicon.svg` được bảo tồn nguyên trạng.

---

## 8. PHÁN QUYẾT VÀ HÀNH ĐỘNG TIẾP THEO

* **Kết luận**: `CORE_OUTCOME_VALID_WITH_MEASUREMENT_CORRECTIONS`
  Kết quả thực nghiệm cốt lõi (không tái diễn lỗi quan hệ, hợp đồng chuẩn tắc, compiler và solver giải ra đáp số ground truth chính xác 100%) hoàn toàn vững chắc. Ba trục đo lường và diễn giải (token usage, safe trace, tách bạch nhân quả) đã được đính chính hoàn toàn trong correction layer.
* **Hành động tiếp theo**:
  `DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING`
