# ANALYZE_FAILURE_CLUSTER_DIAGNOSIS

**2026-09-22** · Nhánh `feat/photo-problem-to-scene` · START_HEAD `12df583` · `main` giữ `085cae6` ·
Thực thi hoàn toàn offline · **0 request Gemini · 0 request mạng · 0 model token**

```text
DIAGNOSIS_WAVE                 ANALYZE_FAILURE_CLUSTER_DIAGNOSIS
TARGET_CLUSTER                 [P03, P05] (MODEL_MALFORMED_RELATION)
CONTROL_GROUP                  [P01, P02, P04, P06, P07, P08] (FULL_PIPELINE_PASS)
DATASET_CLASS                  MIXED_DEVELOPMENT_EVIDENCE (12/12 ca có kết cục)
SCHEMA_CAPABILITY              PRESENT (schema hiện tại biểu diễn đầy đủ cả 2 ca)
PROMPT_COVERAGE                EXPLICITLY_COVERED (prompt Analyze phủ đủ từ vựng và cấu trúc)
CORRECTED_CONTRACT_REPLAY      PASS (cả P03 và P05 đều compile thành công, đáp số đúng, bất biến hoán vị)
NORMALIZATION_FEASIBILITY      NOT_MEASURABLE_FROM_HISTORICAL_EVIDENCE (thiếu raw structured relation payload)
P03_ROOT_CAUSE                 HISTORICAL_EVIDENCE_INSUFFICIENT (CONFIDENCE: NOT_ESTABLISHED)
P05_ROOT_CAUSE                 HISTORICAL_EVIDENCE_INSUFFICIENT (CONFIDENCE: NOT_ESTABLISHED)
CLUSTER_HOMOGENEITY            PARTIAL (cùng pha/mã/schema; khác wording; thiếu raw payload để chứng minh đơn nguyên)
CLUSTER_ROOT_CAUSE             HISTORICAL_EVIDENCE_INSUFFICIENT (CONFIDENCE: NOT_ESTABLISHED)
NEXT_ACTION                    FRESH_PREREGISTERED_FAILURE_REPRODUCTION
```

---

## 1. Bối cảnh và Nguyên tắc Thực thi

Wave chẩn đoán này được thiết kế để giải quyết câu hỏi: **Cụm thất bại Analyze của P03 và P05 có thực sự xuất phát từ cùng một nguyên nhân gốc hay không, và nguyên nhân đó nằm ở đâu (Prompt, Schema, Normalizer, Model hay Downstream)?**

Thực thi tuân thủ nghiêm ngặt **Chế độ thực thi thận trọng**:
1. **Tách bạch hai pha**:
   - **Pha A — Evidence Extraction**: Thu thập và chuẩn hóa dữ kiện từ các artifact đã commit. Không gán `ROOT_CAUSE`, không dựng lại output mô hình, không dùng đáp số đúng hay case ID làm logic.
   - **Pha B — Constrained Classification**: Phân loại dựa trên tiêu chí loại trừ chặt chẽ. Đánh giá độc lập P03 và P05 trước khi xem xét cluster.
2. **Confidence Policy**:
   - `HIGH`: Tái hiện trực tiếp và loại trừ toàn bộ giả thuyết cạnh tranh.
   - `MODERATE`: Nhiều bằng chứng cùng hướng nhưng còn ít nhất một giả thuyết chưa loại trừ.
   - `LOW`: Chỉ có tương quan hoặc suy luận gián tiếp.
   - `NOT_ESTABLISHED`: Artifact không đủ để phân biệt nguyên nhân.
3. **Chính sách không suy đoán**:
   - Khi artifact lịch sử chỉ lưu kết quả rút gọn (`RAW_RELATION_COUNT = 2, ACTUAL_GIVEN = 0, STRUCTURED_RELATION_INVALID`) mà không lưu unredacted raw JSON payload do mô hình sinh ra, **bắt buộc chọn** `HISTORICAL_EVIDENCE_INSUFFICIENT` và `NOT_ESTABLISHED`. Tuyệt đối không quy kết là `MODEL_NONCOMPLIANCE` hay `PROMPT_INSTRUCTION_GAP` khi chưa có bằng chứng loại trừ.
4. **Không sửa mã sản phẩm**:
   - Toàn bộ pipeline (`backend/app`, `frontend/src`, prompt, schema, adapter, FactGraph, compiler, runner, aggregator) được bảo toàn nguyên vẹn từng byte.

---

## 2. Pha A — Trích xuất Bằng chứng Lịch sử

### 2.1 Bằng chứng từ Benchmark và Completion Log
- **Tệp nguồn provenance**:
  - `docs/evaluation/geometry/photo-problem-to-scene/benchmark-completion-repair/BENCHMARK_COMPLETION_REPORT.json`
  - `docs/evaluation/geometry/photo-problem-to-scene/benchmark-completion-repair/cases/P03.json`
  - `docs/evaluation/geometry/photo-problem-to-scene/cases/P05.json`
- **P03**:
  - Pha thất bại: `ANALYZE`
  - Mã quy kết: `MODEL_MALFORMED_RELATION`
  - Rule / Pointer: `index 0: perpendicular_lines, index 1: perpendicular_line_plane`
  - Trạng thái relation: Cả 2 quan hệ đều bị adapter từ chối (`STRUCTURED_RELATION_INVALID`). `RAW_RELATION_COUNT = 2`, `ACTUAL_GIVEN_RELATION_COUNT = 0`.
  - Adapter nhận contract: `True` (bước phân tích cú pháp hợp lệ, chuyển tiếp tới semantic adapter).
  - FactGraph: `False` (không thể dựng vì thiếu quan hệ hợp lệ).
  - Compiler: `False` (bị chặn ở cổng Analyze).
- **P05**:
  - Pha thất bại: `ANALYZE`
  - Mã quy kết: `MODEL_MALFORMED_RELATION`
  - Rule / Pointer: `index 0: perpendicular_lines, index 1: perpendicular_line_plane`
  - Trạng thái relation: Tương tự P03, cả 2 quan hệ đều bị từ chối (`STRUCTURED_RELATION_INVALID`). `RAW_RELATION_COUNT = 2`, `ACTUAL_GIVEN_RELATION_COUNT = 0`.
  - FactGraph / Compiler: `False`.
- **Trạng thái lưu trữ Raw Output**:
  - Cả P03 và P05 đều chỉ lưu bản ghi đã khử thô (redacted envelope).
  - `RAW_HISTORICAL_OUTPUT_AVAILABLE = False`.
  - Không thể trích xuất chính xác payload JSON cụ thể mà mô hình đã gửi (các trường nào bị thiếu/sai tên/sai kiểu).

### 2.2 Ma trận So sánh P03, P05 và 6 Ca Đối chứng Thành công

| Trục so sánh | P03 (Thất bại) | P05 (Thất bại) | P01 (PASS) | P02 (PASS) | P04 (PASS) | P06 (PASS) | P07 (PASS) | P08 (PASS) | Phân loại yếu tố |
|---|---|---|---|---|---|---|---|---|---|
| Diễn đạt góc vuông | `góc VUW bằng 90°` | `HI ⊥ HJ` | `tam giác ABC vuông tại A` | `tam giác ABC vuông cân tại A` | `tam giác ABC vuông tại B` | `tam giác ABC vuông tại B` | `tam giác ABC vuông cân tại B` | `tam giác ABC vuông tại A` | Wording khác biệt ở P03/P05 |
| Đường vuông góc đường | `UV ⊥ UW` | `HI ⊥ HJ` | `AB ⊥ AC` | `AB ⊥ AC` | `BA ⊥ BC` | `BA ⊥ BC` | `BA ⊥ BC` | `AB ⊥ AC` | Đều quy về 2 đường vuông góc |
| Đường vuông góc mặt | `TV ⊥ (UVW)` | `SH ⊥ (HIJ)` | `SA ⊥ (ABC)` | `SA ⊥ (ABC)` | `SA ⊥ (ABC)` | `SA ⊥ (ABC)` | `SA ⊥ (ABC)` | `SA ⊥ (ABC)` | Cấu trúc quan hệ tương đồng |
| Đặt tên đỉnh | `T, U, V, W` | `S, H, I, J` | `S, A, B, C` | `S, A, B, C` | `S, A, B, C` | `S, A, B, C` | `S, A, B, C` | `S, A, B, C` | Đỉnh khác SABC chỉ có ở P03/P05 |
| Độ dài phân số | Không (`7`, `6`, `3`) | Có (`3/2`, `4`, `5`) | Không (`4`, `3`, `5`) | Không (`2`, `3`) | Không (`3`, `4`, `5`) | Không (`7`, `3`, `4`) | Có (`15/2`, `3`, `5`) | Không (`60`, `3`, `4`, `5`) | P07 cũng có phân số (PASS) |
| Source fact ID | `fact_base_right`, `fact_h_perp` | `fact_base_right`, `fact_h_perp` | Tương đương | Tương đương | Tương đương | Tương đương | Tương đương | Tương đương | Yếu tố chung |
| Model assumption | `false` | `false` | `false` | `false` | `false` | `false` | `false` | `false` | Yếu tố chung |
| Arity đường/mặt | 2 điểm / 3 điểm | 2 điểm / 3 điểm | 2 điểm / 3 điểm | 2 điểm / 3 điểm | 2 điểm / 3 điểm | 2 điểm / 3 điểm | 2 điểm / 3 điểm | 2 điểm / 3 điểm | Khớp schema |
| Schema capability | PRESENT | PRESENT | PRESENT | PRESENT | PRESENT | PRESENT | PRESENT | PRESENT | Khớp schema |

**Nhận xét:**
- Yếu tố gây nhiễu tiềm tàng: Tên đỉnh không phải `S, A, B, C` (P03 dùng `T, U, V, W`; P05 dùng `S, H, I, J`). Tuy nhiên, bản thân compiler và FactGraph không phụ thuộc vào nhãn chữ cái.
- Từ vựng đề bài: P03 dùng cụm từ `góc VUW bằng 90°` thay vì `vuông tại`; P05 dùng ký hiệu hình học trực tiếp `HI ⊥ HJ`.

---

## 3. Pha B — Phân loại có Ràng buộc

### 3.1 Kiểm tra Năng lực Schema (Schema Capability)
Tạo hai `RequestContract` tối thiểu offline chỉ từ các dữ kiện đã cho trong đề, không dùng đáp số, không dùng tọa độ bố trí:
- **P03 Minimal Contract**:
  - Điểm: `T, U, V, W`
  - Đáy: `U, V, W` (vuông tại `U` qua `perpendicular_lines(line1=['U', 'V'], line2=['U', 'W'])`)
  - Chiều cao: `perpendicular_line_plane(line=['T', 'V'], plane=['U', 'V', 'W'])`
  - Độ dài: `UW = 7`, `UV = 6`, `TV = 3`
- **P05 Minimal Contract**:
  - Điểm: `S, H, I, J`
  - Đáy: `H, I, J` (vuông tại `H` qua `perpendicular_lines(line1=['H', 'I'], line2=['H', 'J'])`)
  - Chiều cao: `perpendicular_line_plane(line=['S', 'H'], plane=['H', 'I', 'J'])`
  - Độ dài: `HI = 4`, `HJ = 5`, `SH = 3/2`

**Kết quả kiểm tra:**
- Pydantic validation: `PASS`
- RequestContract validation: `PASS`
- Relation canonicalization: `PASS`
- Point-reference validation: `PASS`
- FactGraph construction: `PASS`
- Compiler eligibility: `PASS`
- Kết luận: `SCHEMA_CAPABILITY = PRESENT`. `SCHEMA_CHANGE_REQUIRED = False`.

### 3.2 Audit Độ Phủ Prompt (Prompt Coverage)
Khảo sát tài liệu `backend/app/prompts/geometry_analyze.md`:
- Định nghĩa góc 90° và quan hệ vuông góc: Được quy định rõ ràng trong phần `perpendicular_lines` và `perpendicular_line_plane`.
- Quy tắc `source_fact_id` và `model_assumption`: Có hướng dẫn rõ rệt, yêu cầu `model_assumption = false` cho dữ kiện trực tiếp từ đề.
- Không được đưa hệ quả vào GIVEN: Quy định rõ.
- Kết quả đánh giá từng wording:
  - Wording P03 (`góc VUW bằng 90°`): `EXPLICITLY_COVERED` (prompt yêu cầu chuyển hóa góc 90° thành `perpendicular_lines`).
  - Wording P05 (`HI ⊥ HJ`): `EXPLICITLY_COVERED` (ký hiệu vuông góc được hỗ trợ trực tiếp).
  - Wording các ca thành công (`tam giác vuông tại...`): `EXPLICITLY_COVERED`.

### 3.3 Counterfactual Corrected-Contract Replay
Thực hiện replay phản chứng: Giữ nguyên toàn bộ đề bài và dữ kiện độ dài của P03 và P05, chỉ thay hai quan hệ bị malformed bằng hai canonical relations chuẩn tắc từ ground truth. Chạy toàn bộ pipeline downstream qua FactGraph -> Compiler -> Type Check -> Grounding -> Scene Builder -> Visual Obligations -> Topology -> Answer.

**Kết quả:**
- **P03 Replay**:
  - `COMPILE_STATUS`: `SUPPORTED`
  - `TOPOLOGY_RESULT`: `PASS`
  - `ANSWER_NUMERICAL`: `21.0` (Khớp đúng thể tích $V = \frac{1}{3} \times \frac{1}{2} \times 6 \times 7 \times 3 = 21$)
  - Tính tất định: Trùng khớp 100% qua 2 lần chạy.
  - Bất biến hoán vị nhãn đỉnh: Đổi nhãn `(T, U, V, W) -> (S, A, B, C)` vẫn giữ nguyên hành vi biên dịch và thể tích = 21.
- **P05 Replay**:
  - `COMPILE_STATUS`: `SUPPORTED`
  - `TOPOLOGY_RESULT`: `PASS`
  - `ANSWER_NUMERICAL`: `5.0` (Khớp đúng thể tích $V = \frac{1}{3} \times \frac{1}{2} \times 4 \times 5 \times \frac{3}{2} = 5$)
  - Tính tất định: Trùng khớp 100% qua 2 lần chạy.
  - Xử lý số học phân số `3/2`: Biên dịch chính xác qua `Fraction`.
- **Kết luận Replay**: Hạ tầng downstream (FactGraph, Compiler, Scene Builder) hoàn toàn không có lỗi đối với cả hai dạng bài toán này. Lỗi dừng lại thuần túy ở tầng Analyze.

### 3.4 Đánh giá Khả năng Chuẩn hóa Tất định (Deterministic Normalization)
Theo quy tắc nghiêm ngặt của wave chẩn đoán:
- Normalizer chỉ được coi là khả thi nếu có thể sửa quan hệ **duy nhất và an toàn** từ chính cấu trúc JSON mà mô hình trả về, không đọc problem text, không đọc ground truth, không đọc expected answer.
- Vì unredacted raw model output không được lưu lại trong artifact lịch sử (`RAW_HISTORICAL_OUTPUT_AVAILABLE = False`), chúng ta không có bằng chứng về việc mô hình đã xuất ra trường dữ liệu nào (ví dụ: mô hình có gửi `points: ['U', 'V', 'W']` cho perpendicular_lines hay gửi sai key `line_a`, hay thiếu field).
- Do đó, việc giả định một normalizer tất định có thể khắc phục được là không có cơ sở thực chứng.
- Phân loại: `NORMALIZATION_FEASIBILITY = NOT_MEASURABLE_FROM_HISTORICAL_EVIDENCE`.

### 3.5 Phân loại Cụm Lỗi (Failure Classification)
- **P03**:
  - `P03_ROOT_CAUSE`: `HISTORICAL_EVIDENCE_INSUFFICIENT`
  - `CAUSALITY_CONFIDENCE`: `NOT_ESTABLISHED`
- **P05**:
  - `P05_ROOT_CAUSE`: `HISTORICAL_EVIDENCE_INSUFFICIENT`
  - `CAUSALITY_CONFIDENCE`: `NOT_ESTABLISHED`
- **Cluster Evaluation**:
  - Cả hai ca cùng thất bại ở pha `ANALYZE`.
  - Cùng mã `MODEL_MALFORMED_RELATION`.
  - Cùng hai loại quan hệ (`perpendicular_lines` và `perpendicular_line_plane`).
  - Cùng có `SCHEMA_CAPABILITY = PRESENT` và `PROMPT_COVERAGE = EXPLICITLY_COVERED`.
  - Tuy nhiên, wording đề bài khác nhau (`góc 90°` vs `⊥`), và thiếu raw payload để chứng minh cơ chế hỏng hóc giống hệt nhau.
  - `CLUSTER_HOMOGENEITY = PARTIAL`.
  - `CLUSTER_ROOT_CAUSE = HISTORICAL_EVIDENCE_INSUFFICIENT` (`CLUSTER_CAUSALITY_CONFIDENCE = NOT_ESTABLISHED`).

---

## 4. Các Audit Phụ

### 4.1 Audit Mã Từ chối của N03 (N03 Code Alignment Audit)
- Trong benchmark lịch sử, ca âm N03 bị từ chối an toàn với mã: `LINE_PLANE_RELATION_MISSING`.
- Registry v1 khai báo N03 là một ca từ chối chủ đích (`TARGETED_REJECTION = YES`), nhưng danh sách mã chấp nhận trong bản ghi cũ lại chưa liệt kê tường minh `LINE_PLANE_RELATION_MISSING`.
- Kết quả chính: Không ảnh hưởng đến phân loại an toàn (`SAFE_REJECTION`).
- Đánh giá: Cần bổ sung lớp điều chỉnh registry để cập nhật mã chấp nhận cho N03.
- Phân loại: `N03_ACCEPTABLE_CODE_CORRECTION_LAYER_REQUIRED = YES`.

### 4.2 Audit Alias của NEXT_ACTION
- So sánh `STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS` (trong aggregator) và `ANALYZE_FAILURE_CLUSTER_DIAGNOSIS` (tên wave chẩn đoán hiện tại).
- Cả hai đều trỏ chính xác vào cụm lỗi `[P03, P05]`.
- Đây là hai tên gọi mang tính alias đồng nghĩa cho cùng một hành động tiếp theo.
- Khuyến nghị: Cần đồng bộ hóa alias trong aggregator ở đợt cập nhật tiếp theo. `NEXT_ACTION_ALIAS_ALIGNMENT_REQUIRED = YES`.

---

## 5. Đối chứng Âm và 10 Phép Tiêm Lỗi (Fault Injections)

Bộ chẩn đoán tích hợp 10 phép tiêm lỗi trong test suite `test_analyze_failure_cluster_diagnosis.py`, đảm bảo phát hiện mọi vi phạm nguyên tắc chẩn đoán:
- `F1`: Ép P03/P05 cùng nguyên nhân chỉ vì cùng error code -> **BỊ BẮT** (`AssertionError: Cluster cannot be declared FULLY HOMOGENEOUS`).
- `F2`: Dùng expected answer trong corrected replay -> **BỊ BẮT** (`RuntimeError: Counterfactual replay contaminated with expected answer`).
- `F3`: Normalizer đọc `problem_text` -> **BỊ BẮT** (`PermissionError: Normalizer read problem text`).
- `F4`: Normalizer đọc ground truth -> **BỊ BẮT** (`PermissionError: Normalizer read ground truth`).
- `F5`: Xếp thiếu raw evidence thành `MODEL_NONCOMPLIANCE` -> **BỊ BẮT** (`ValueError: Cannot attribute to MODEL_NONCOMPLIANCE without raw unredacted model evidence`).
- `F6`: Bỏ một ca thành công khỏi nhóm đối chứng -> **BỊ BẮT** (`ValueError: Control group incomplete`).
- `F7`: Sửa historical artifact -> **BỊ BẮT** (`ValueError: Historical artifact corrupted or drift detected`).
- `F8`: Lưu raw model output vào artifact -> **BỊ BẮT** (`ValueError: Raw model output leak detected in diagnostic artifact`).
- `F9`: Đổi phân loại chính vì N03 code mismatch -> **BỊ BẮT** (`ValueError: N03 secondary code mismatch cannot alter primary safe rejection classification`).
- `F10`: Ép NEXT_ACTION alias thành thay đổi product behavior -> **BỊ BẮT** (`ValueError: Diagnostic action alias must not modify product behavior`).

Toàn bộ 10 phép tiêm đều được hoàn nguyên trùng byte sau kiểm thử.

---

## 6. Bảo Toàn Tính Bất Biến (Parity Proof)

- Candidate verification (`freeze_evaluation_candidate.py --verify`): `077dbc6b7bf6f62f7d07838696f5bcf71c74d3210ae65fbfc36683ee19e42bc1` (103 files verified) -> `PASS`.
- Cache identity verification (`lock_cache_identity.py --verify`): `CACHE_VERSION = 99` -> `PASS`.
- Product code: Không có bất kỳ thay đổi nào trong `backend/app` hoặc `frontend/src`.
- User dirty tree: Thay đổi xóa `frontend/public/favicon.svg` được bảo lưu nguyên vẹn, không bị stage hay commit.
- Secret Scan: 0 API keys, 0 tracebacks, 0 raw model outputs trong các artifacts tạo ra.

---

## 7. Khuyến nghị Bước Tiếp theo (Next Action)

Vì nguyên nhân gốc của cụm lỗi P03 và P05 không thể khẳng định chắc chắn do thiếu raw model payload lịch sử, hành động hợp lệ duy nhất là:

**`NEXT_ACTION: FRESH_PREREGISTERED_FAILURE_REPRODUCTION`**

Trong wave tiếp theo:
1. Đăng ký trước cấu hình ghi nhận raw envelope (được bảo vệ/khử thông tin nhạy cảm).
2. Thực hiện một lượt chạy tái hiện có kiểm soát cho riêng P03 và P05 để thu thập chính xác cấu trúc quan hệ malformed mà mô hình sinh ra.
3. Dựa trên raw structure thu thập được, phân xử dứt khoát giữa `PROMPT_INSTRUCTION_GAP`, `DETERMINISTIC_NORMALIZATION_GAP`, và `MODEL_NONCOMPLIANCE`.
