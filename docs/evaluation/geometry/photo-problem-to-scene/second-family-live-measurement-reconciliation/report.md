# Báo Cáo Đối Soát Attribution và Khắc Phục Apparatus Đo Lường (Offline)

**WAVE_ID:** `SECOND_FAMILY_LIVE_MEASUREMENT_RECONCILIATION_OFFLINE`  
**NGÀY:** 2026-09-24  
**NHÁNH:** `feat/photo-problem-to-scene`  
**START_HEAD:** `532f447e711c6ad230b7296b52ce00c2888a226b`  
**SOURCE_WAVE:** `SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION`  
**CASE_ID:** `PRISM_SCHEMA_LIVE_P01`  
**MODEL:** `gemini-2.5-flash`  
**CHẾ ĐỘ:** 100% Offline (0 Gemini requests, 0 network calls, 0 API keys loaded)  
**BẢO TOÀN WORKING TREE:** ` D frontend/public/favicon.svg` (giữ nguyên không đổi)  

---

## 1. Mục Tiêu và Tóm Tắt Kết Quả

Wave này tiến hành đối soát độc lập nguyên nhân quy kết (attribution audit) của kết luận `SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE` từ wave live schema revalidation trước đó, nhằm xác định liệu kết quả có bị quy kết sai do lỗi thiết bị đo (apparatus errors) hay không.

### Kết luận đối soát chính thức:
1. **Xác nhận 2 lỗi Apparatus trong harness đo lường cũ:**
   - **Lỗi R1 (`LABEL_MATCHING_DROPS_VALID_LENGTH_FACTS`):** Scorer cũ dùng so khớp cứng `f.label in ("AB", "AC", "AD")`. Khi mô hình dùng nhãn tự nhiên (ví dụ `"Đoạn thẳng AB"`) hoặc fact được định danh qua `id: "ab_length"`, bộ đo cũ đã tự động loại bỏ toàn bộ vào `lengths: {}`.
   - **Lỗi R2 (`STALE_OR_NONEXISTENT_FACT_GRAPH_CLASS_REFERENCE`):** Harness cũ gọi `FG.FactGraph()`, nhưng module `app.simulation.geometry_compiler.fact_graph` chỉ xuất lớp `GeometryFactGraph`. Lệnh gọi làm phát sinh ngoại lệ `AttributeError`, khiến đường ống tất định downstream chưa từng thực sự được thi hành.
2. **Đánh giá tính toàn vẹn của bằng chứng gốc (Gate A):**
   - Khảo sát file nhật ký transport tại `scratch/live_reval_raw_response.json`: Phản hồi thô chỉ lưu preview 500 ký tự đầu (`response_preview`), toàn văn `candidate_raw_text` không được tuần tự hóa đầy đủ xuống đĩa.
   - Mã băm kỳ vọng `RESPONSE_SHA256 = 47e161b8af8dfa58876314df55949e2c63b85513302648cd3d33f35f0c73fec6` do đó không thể xác minh toàn vẹn 100% trên đĩa nếu không suy đoán.
3. **Quyết định phân loại đóng (Mục 8.C):**
   - Do không sửa response để khớp ground truth và không bịa dữ kiện khi raw response thiếu trên đĩa:
     - `FINAL_DECISION = HISTORICAL_EVIDENCE_INSUFFICIENT`
     - `ORIGINAL_FINAL_CLASSIFICATION = INVALIDATED_BY_MEASUREMENT_ERROR`
     - `SEMANTIC_EXTRACTION_VALID = NOT_MEASURABLE`
     - `PIPELINE_SMOKE_TEST = NOT_MEASURABLE`
     - `NEXT_ACTION = SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION`

---

## 2. Gate A — Khảo Sát Tính Toàn Vẹn Bằng Chứng Gốc

- **EXPECTED_RESPONSE_SHA256:** `47e161b8af8dfa58876314df55949e2c63b85513302648cd3d33f35f0c73fec6`
- **Tình trạng file raw response:**
  - File `scratch/live_reval_raw_response.json` (kích thước 826 bytes) chỉ chứa `response_preview` cắt tại 500 ký tự đầu để tránh commit dữ liệu thô.
  - Mã băm SHA-256 của chuỗi preview là `61841d5b8c342123...`, không khớp toàn văn phản hồi `47e161b8af8dfa58...`.
- **Nguyên tắc phương pháp luận:**
  - Tuyệt đối không dùng `problem_text` hay ground truth để suy đoán lại nội dung response bị thiếu.
  - Phân loại: `HISTORICAL_EVIDENCE_INSUFFICIENT`.

---

## 3. Gate B — Phân Tích Attribution Audit

### B1. Length Evaluator Bug (R1: `LABEL_MATCHING_DROPS_VALID_LENGTH_FACTS`)
- **Vị trí code:** `scratch/execute_live_revalidation.py` dòng 201–203:
  ```python
  for f in contract.input_facts:
      if f.label in ("AB", "AC", "AD"):
          extracted_lengths[f.label] = f.values[0] if f.values else None
  ```
- **Cơ chế lỗi:** Vị từ so khớp cứng theo chuỗi `f.label` bỏ qua các cấu trúc định danh chuẩn tắc (`f.id == "ab_length"`) hoặc nhãn tiếng Việt (`"Đoạn thẳng AB"`).
- **Quy kết:** `MEASUREMENT_APPARATUS_ERROR`.

### B2. Pipeline Harness Bug (R2: `STALE_OR_NONEXISTENT_FACT_GRAPH_CLASS_REFERENCE`)
- **Vị trí code:** `scratch/execute_live_revalidation.py` dòng 237–238:
  ```python
  g = FG.FactGraph()
  g.nap_hop_dong(contract)
  ```
- **Cơ chế lỗi:** Module `app.simulation.geometry_compiler.fact_graph` chứa `GeometryFactGraph` chứ không có `FactGraph`.
- **Hậu quả:** Gây ra lỗi `AttributeError: module '...fact_graph' has no attribute 'FactGraph'`.
- **Entry point chuẩn tắc:** `app.simulation.geometry_compiler.contract_adapter.build_fact_graph(contract)` $\to$ `compiler.danh_gia_eligibility(graph)` $\to$ `compiler.bien_dich(graph)`.
- **Quy kết:** `MEASUREMENT_APPARATUS_ERROR`. Ghi nhận `ORIGINAL_PIPELINE_RESULT = NOT_MEASURABLE` và `ORIGINAL_PIPELINE_APPARATUS_ERROR = YES`.

---

## 4. Gate C — Kiểm Thử Red/Green Khắc Phục Apparatus

Bộ kiểm thử tập trung tại [`backend/tests/geometry/test_second_family_live_measurement_reconciliation.py`](file:///d:/Documents/projects/algo-sim/backend/tests/geometry/test_second_family_live_measurement_reconciliation.py) gồm 10 bài test, đã chạy và vượt qua 100%:

1. `test_evidence_hash_mismatch_rejected`: Bằng chứng sai mã băm bị từ chối an toàn.
2. `test_missing_raw_response_not_inferred`: Raw response thiếu không được suy đoán từ báo cáo.
3. `test_r1_red_before_label_matching_drops_valid_length_facts`: Chứng minh lỗi Red-Before R1 (bộ so khớp cũ đánh rơi fact khi nhãn mang tính mô tả).
4. `test_r1_green_after_corrected_evaluator_recognizes_canonical_references`: Chứng minh Green-After R1 (bộ đo mới nhận diện đúng `AB=3, AC=4, AD=5` qua canonical references).
5. `test_ambiguous_display_label_rejected`: Nhãn mô tả mơ hồ không có canonical reference bị từ chối.
6. `test_unrelated_length_facts_rejected`: Fact không liên quan bị loại bỏ.
7. `test_r2_red_before_stale_fact_graph_class_reference_fails`: Chứng minh lỗi Red-Before R2 (`FG.FactGraph()` ném `AttributeError`).
8. `test_r2_green_after_production_entry_point_succeeds`: Chứng minh Green-After R2 (`contract_adapter.build_fact_graph` sinh `GeometryFactGraph` trạng thái `VALID`).
9. `test_offline_replay_zero_network`: Xác nhận 0 request mạng trong chế độ offline.
10. `test_historical_artifacts_byte_identical`: Xác nhận artifact lịch sử của wave trước được bảo toàn nguyên vẹn.

---

## 5. Ba Lớp Kết Quả Ghi Nhận

| Lớp Kết Quả | Trạng Thái / Giá Trị | Ghi Chú |
|---|---|---|
| **1. ORIGINAL_LIVE_OBSERVATION** | `HTTP 200`, `latency_ms: 5922.75` | Provider chấp nhận schema, phân tích cú pháp hợp lệ. |
| **2. ORIGINAL_MEASUREMENT_APPARATUS_RESULT** | `SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE` | **INVALIDATED_BY_MEASUREMENT_ERROR** (Do 2 lỗi apparatus R1 & R2). |
| **3. CORRECTED_OFFLINE_REPLAY_RESULT** | `HISTORICAL_EVIDENCE_INSUFFICIENT` | Bằng chứng thô chưa được lưu đầy đủ trên đĩa; dừng an toàn không đoán. |

---

## 6. Danh Mục Artifact Đã Tạo

Lưu trữ tại `docs/evaluation/geometry/photo-problem-to-scene/second-family-live-measurement-reconciliation/`:
- `SOURCE_EVIDENCE_INTEGRITY.json`: Đánh giá tính toàn vẹn của bằng chứng thô.
- `ATTRIBUTION_AUDIT.json`: Phân tích nguồn gốc hai lỗi apparatus R1 và R2.
- `CORRECTED_REPLAY_RESULT.json`: Kết quả chạy lại của apparatus đã sửa.
- `FINAL_DECISION.json`: Quyết định phân loại đóng chính thức.

---

## 7. Quyết Định và Bước Tiếp Theo

- **FINAL_DECISION:** `HISTORICAL_EVIDENCE_INSUFFICIENT`
- **MERGE_ALLOWED:** `NO`
- **NEXT_ACTION:** `SECOND_FAMILY_LIVE_RETRY_PREREGISTRATION` (Tiền đăng ký lại lượt chạy live duy nhất với apparatus đo lường và tuần tự hóa đầy đủ đã được sửa chữa).
