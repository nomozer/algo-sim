# HYBRID_ARCHITECTURE_EVALUATION_PROTOCOL — Quy Trình Tiền Đăng Ký Đánh Giá So Sánh Kiến Trúc Hybrid và LLM_ONLY

> **Trạng thái:** Tiền đăng ký Hiệu chỉnh Phương pháp Ngoại tuyến (Method Reconciliation) — Nghiên cứu Khóa luận tốt nghiệp  
> **Schema Version:** `2.1.0`  
> **Wave:** `HYBRID_EVALUATION_PROTOCOL_METHOD_RECONCILIATION_OFFLINE`  
> **Base Commit HEAD:** `f3b098fc7d98acb7a6fbabe0a8b11a30b068db16`  
> **Candidate Tree Hash:** `6ebfcb9002b5c3ee…` (`CACHE_VERSION = 100`)  
> **File Dữ Liệu Máy Đọc:** [`docs/research/hybrid_architecture_evaluation_manifest.json`](file:///d:/Documents/projects/algo-sim/docs/research/hybrid_architecture_evaluation_manifest.json)  
> **Bất Biến Bắt Buộc:** `DEFAULT_MODE = LLM_ONLY` (không đổi), `PRODUCT_CODE_CHANGED = NO`, `OFFLINE_REQUEST_BUDGET = 0`, `ACTUAL_REQUESTS = 0`.

---

## 1. Bối Cảnh & Mục Tiêu Nghiên Cứu

Trong khuôn khổ khóa luận tốt nghiệp về ứng dụng AI và công nghệ mô phỏng tương tác trong dạy học Hình học Không gian, hệ thống đối mặt với thách thức cốt lõi: **độ tin cậy và tính chính xác hình học của các mô hình ngôn ngữ lớn (LLM)**.

Khi giao toàn bộ quy trình sinh mã dựng hình không gian ba chiều cho LLM, các hiện tượng phổ biến thường xảy ra:
- **Ảo giác hình học (Geometric Hallucination):** Tự bịa tọa độ không thỏa mãn các quan hệ vuông góc hoặc độ dài đề bài cho.
- **Lỗi tô-pô (Topology Inconsistency):** Nhầm lẫn số đỉnh, số cạnh, số mặt (ví dụ: lăng trụ tam giác nhưng sinh ra 8 đỉnh hoặc 6 mặt).
- **Tính ngẫu nhiên (Non-determinism):** Cùng một đề bài nhưng giữa các lần chạy sinh ra các cấu trúc khác nhau hoặc đáp số sai lệch.
- **Thiếu khả năng từ chối an toàn (Unsafe Compliance):** Vẫn cố gắng vẽ hình và tính toán trên các đề bài thiếu dữ kiện hoặc chứa dữ kiện tự mâu thuẫn.

Để giải quyết các hạn chế trên, đề tài đề xuất **Kiến trúc Lai (Hybrid Architecture)**:
- **LLM:** Chỉ đóng vai trò trích xuất ngữ nghĩa đề bài thành hợp đồng dữ kiện có cấu trúc (`RequestContract`), tận dụng năng lực hiểu ngôn ngữ tự nhiên.
- **Engine Tất Định (Deterministic Engine):** Sử dụng Đồ thị dữ kiện (`FactGraph`) và Trình biên dịch nguyên thủy (`Primitive Compiler`) để suy diễn hình học, kiểm tra tính nhất quán, tính toán tọa độ và dựng cảnh 3D (`Scene3D`) với độ chính xác số học tuyệt đối.

Tài liệu này xác lập **phương pháp luận tiền đăng ký nghiêm ngặt** nhằm so sánh thực nghiệm một cách khách quan, minh bạch giữa hai kiến trúc trên hai họ hình học đã được cài đặt và kiểm chứng đầy đủ.

---

## 2. Xác Định Primary Estimand & Hai Tầng Đánh Giá

Để đo lường chính xác tác động của tầng sinh chương trình hình học (`SemanticProgram`), quy trình thực nghiệm quy định nguyên tắc đầu vào chung (`COMMON_INPUT`):

```
                                [ COMMON_INPUT ]
                     Cùng một RequestContract chuẩn tắc
                           đã parse & lưu bền vững
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
        [ Nhánh A: LLM_ONLY ]                 [ Nhánh B: HYBRID ]
           RequestContract                       RequestContract
                  │                                     │
                  ▼                                     ▼
           Gemini Synthesis                         FactGraph
       (hoặc cached synthesis)                          │
                  │                                     ▼
                  ▼                             Primitive Compiler
           Validator/Kernel                             │
                  │                                     ▼
                  ▼                             SemanticProgramSpec
               Scene3D                                  │
                                                        ▼
                                                 Validator/Kernel
                                                        │
                                                        ▼
                                                     Scene3D
```

### Nguyên tắc bất biến về Paired Comparison
**Tuyệt đối không sử dụng hai kết quả Analyze độc lập để tạo một paired comparison chính.** Việc để hai nhánh chạy hai lượt Analyze riêng biệt sẽ đưa vào biến thiên ngẫu nhiên của tầng trích xuất ngữ nghĩa (confounding variable), làm sai lệch kết luận về hiệu năng thực sự của Primitive Compiler so với LLM Synthesis.

### Đăng ký hai tầng đánh giá:

1. **PRIMARY_ARCHITECTURE_ISOLATED_EVALUATION (Primary Estimand):**
   - **Định nghĩa:** Cả hai kiến trúc nhận chính xác cùng một `RequestContract` đã chuẩn hóa và lưu bền vững (`COMMON_INPUT`).
   - **Bản chất COMMON_INPUT:** `COMMON_INPUT` là `ORACLE_CANONICAL_STRUCTURED_FIXTURE`. Một số `RequestContract` được xây dựng từ fixture ngữ nghĩa chuẩn có tham chiếu semantic fields trong ground truth (các dữ kiện độ dài và quan hệ đề bài cho).
   - **Bảo toàn cách ly đáp số:** Expected-output ground truth, đáp số và nhãn chấm điểm không được nạp vào generation runner hoặc request payload. Tuyệt đối không có `expected_volume`, `expected_answer`, `expected_topology`, `expected_rejection` hoặc nhãn chấm điểm nào được đưa vào request payload. Runner chỉ nhận canonical `RequestContract` đã đóng băng.
   - **Mục tiêu & Phạm vi Estimand:** *“So sánh LLM Synthesis với Primitive Compiler với điều kiện cả hai nhận cùng một RequestContract hợp lệ và đúng về ngữ nghĩa.”*
   - **Ranh giới khoa học (Scientific Boundary):** Primary evaluation không đo chất lượng Gemini Analyze. Không được dùng kết quả primary để tuyên bố hiệu quả end-to-end từ văn bản/ảnh đầu vào.
   - **Trạng thái thực tế:** `OFFLINE_HYBRID_REPLAY_READY_BUT_PAIRED_LLM_BASELINE_GAP` (Compiler sẵn sàng replay 100% ngoại tuyến; baseline LLM_ONLY đang thiếu bản ghi cached synthesis cho tập đánh giá đóng băng).

2. **SECONDARY_END_TO_END_EVALUATION (Secondary Exploratory):**
   - **Định nghĩa:** Đánh giá toàn trình bắt đầu từ văn bản đề bài tự nhiên thô (`problem_text`):  
     $$\text{Problem Text} \longrightarrow \text{Gemini Analyze} \longrightarrow \text{RequestContract} \longrightarrow \text{Compiler / Synthesis} \longrightarrow \text{Kernel} \longrightarrow \text{Scene3D}$$
   - **Mục tiêu:** Khảo sát sự tương tác giữa độ trôi dạt ngữ nghĩa của tầng Analyze và khả năng xử lý/phòng vệ của hai kiến trúc. Toàn bộ việc đo lường chất lượng Analyze thuộc về tầng đánh giá này.
   - **Ràng buộc:** Chỉ được thực hiện ở một wave live độc lập được tiền đăng ký riêng kèm ngân sách HTTP định trước. **Tuyệt đối không chạy trong task offline hiện tại.**

---

## 3. Định Nghĩa Chi Tiết Hai Nhánh Kiến Trúc

### Kiến Trúc A: Baseline (`LLM_ONLY`)
- **Pipeline sơ cấp (Primary):**  
  $$\text{COMMON\_INPUT (RequestContract)} \longrightarrow \text{Gemini Synthesis} \longrightarrow \text{Validator/Kernel} \longrightarrow \text{Scene3D}$$
- **Pipeline toàn trình (Secondary):**  
  $$\text{Problem Text} \longrightarrow \text{Gemini Analyze} \longrightarrow \text{RequestContract} \longrightarrow \text{Gemini Synthesis} \longrightarrow \text{Validator/Kernel} \longrightarrow \text{Scene3D}$$
- **Đặc trưng:** Cả hai bước phân tích ngữ nghĩa và sinh chương trình hình học (`SemanticProgramSpec`) đều phụ thuộc vào mô hình sinh (`gemini-2.5-flash`, temperature = 0.1).
- **Cách kích hoạt:** Mặc định của hệ thống (`DEFAULT_MODE = "LLM_ONLY"`, khi biến môi trường `GEOMETRY_COMPILER_MODE` không được đặt hoặc khác `"DETERMINISTIC_FIRST"`).

### Kiến Trúc B: Đề Xuất (`HYBRID`)
- **Pipeline sơ cấp (Primary):**  
  $$\text{COMMON\_INPUT (RequestContract)} \longrightarrow \text{FactGraph} \longrightarrow \text{Primitive Compiler} \longrightarrow \text{SemanticProgramSpec} \longrightarrow \text{Validator/Kernel} \longrightarrow \text{Scene3D}$$
- **Pipeline toàn trình (Secondary):**  
  $$\text{Problem Text} \longrightarrow \text{Gemini Analyze} \longrightarrow \text{RequestContract} \longrightarrow \text{FactGraph} \longrightarrow \text{Primitive Compiler} \longrightarrow \text{SemanticProgramSpec} \longrightarrow \text{Validator/Kernel} \longrightarrow \text{Scene3D}$$
- **Đặc trưng:** Gemini chỉ được gọi ở tầng trích xuất ngữ nghĩa (nếu chạy end-to-end). Tầng sinh chương trình và tọa độ do trình biên dịch tất định đảm nhiệm (0 lượt gọi model).
- **Cơ chế phòng vệ:**
  - *Fail-closed Refusal:* Nếu dữ kiện tự mâu thuẫn (ví dụ: tam giác vuông tại cả 2 đỉnh), hệ thống từ chối an toàn ngay tại `FactGraph` (`REFUSE`).
  - *Safe Fallback:* Nếu đề bài ngoài phạm vi mẫu hình của compiler, hệ thống chuyển về LLM synthesis (`FALLBACK_TO_LLM`).
- **Cách kích hoạt:** Kích hoạt có kiểm soát thông qua cờ môi trường `GEOMETRY_COMPILER_MODE="DETERMINISTIC_FIRST"` tại [`backend/app/simulation/geometry_compiler/routing.py`](file:///d:/Documents/projects/algo-sim/backend/app/simulation/geometry_compiler/routing.py).

---

## 4. Câu Hỏi Nghiên Cứu (Research Questions)

Nghiên cứu tập trung vào 3 câu hỏi chính, phân định rõ giữa câu hỏi kỹ thuật, câu hỏi về tính giải thích, và loại trừ câu hỏi sư phạm (dành cho thực nghiệm dạy học sau này):

### RQ1 (Kỹ thuật — Tính Đúng Đắn Hình Học & Đáp Số)
> **Kiến trúc Hybrid có cải thiện tính đúng đắn hình học (tô-pô đỉnh/cạnh/mặt, quan hệ vuông góc) và độ chính xác của đáp số thể tích so với kiến trúc LLM_ONLY trên hai họ hình được hỗ trợ hay không?**
- *Mục tiêu:* Đối chiếu tỷ lệ sinh mesh hợp lệ, tỷ lệ đúng số đỉnh/cạnh/mặt và tỷ lệ đáp số thể tích khớp chính xác với Ground Truth.
- *Chỉ số chính:* `topology_exact_match_rate`, `final_answer_exact_match_rate`, `end_to_end_valid_scene_rate`.

### RQ2 (Kỹ thuật — Tính Tái Lập & An Toàn Fail-Closed)
> **Kiến trúc Hybrid có cải thiện tính tất định (tái lập 100% qua các lần chạy lặp lại), đồng thời phát hiện và từ chối an toàn các đề bài thiếu hoặc mâu thuẫn dữ kiện tốt hơn kiến trúc LLM_ONLY hay không?**
- *Mục tiêu:* Đo lường phương sai giữa các lần chạy và tỷ lệ bắt đúng các ca lỗi/mâu thuẫn mà không sinh ảo giác.
- *Chỉ số chính:* `deterministic_cross_run_consistency`, `contradiction_detection_rate`, `safe_refusal_rate`.

### RQ3 (Khả Năng Giải Thích — Traceability & Provenance)
> **Trace dựng hình có cấu trúc của kiến trúc Hybrid có cung cấp bằng chứng giải thích minh bạch, truy xuất được xuất xứ dữ kiện (provenance) so với output sinh trực tiếp từ LLM_ONLY hay không?**
- *Mục tiêu:* Đánh giá chuỗi liên kết từ dữ kiện đề bài (`source_fact_id`) qua các bước suy diễn đến đối tượng hiển thị trên màn hình.
- *Chỉ số chính:* `backend_trace_completeness` (chính), `ui_trace_consumption` (riêng biệt).

---

## 5. Kiểm Kê Bằng Chứng Ngoại Tuyến (Evidence Availability Audit)

Quá trình kiểm kê chỉ đọc (read-only audit) đối với 18 ca đánh giá đóng băng (`Frozen Evaluation Set`) đã được thực hiện nghiêm ngặt trên toàn bộ repository.

### 5.1. Hai Họ Hình Học Được Hỗ Trợ
1. **Hình chóp đáy tam giác vuông có cạnh bên vuông góc với đáy** (`right_triangle_base_pyramid_volume`).
2. **Hình lăng trụ đứng có đáy là tam giác vuông** (`right_triangle_base_right_prism_volume`).

### 5.2. Phân Chia Tập Đo Lường (Tách Biệt Pilot và Frozen Evaluation)
1. **Tập Thử Nghiệm / Pilot Set (6 ca):**
   - Pyramid: `B01`, `B02`, `B03`, `B04` ([`docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-ab-benchmark/PRIMITIVE_COMPILER_AB_MANIFEST.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-ab-benchmark/PRIMITIVE_COMPILER_AB_MANIFEST.json)).
   - Prism: `PRISM_P01` (dương chuẩn), `PRISM_N01` (âm thiếu chiều cao) ([`docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json)).
   - *Mục đích:* Dùng để kiểm tra pipeline kỹ thuật, không dùng trong tập so sánh chính thức.
2. **Tập Đánh Giá Đóng Băng / Frozen Evaluation Set (18 ca):**
   - **12 ca Dương:**
     - Pyramid (8 ca): `P01`, `P02`, `P03`, `P04`, `P05`, `P06`, `P07`, `P08`.
     - Prism (4 ca): `PRISM_P02`, `PRISM_P03`, `PRISM_P04`, `PRISM_P05`.
   - **6 ca Âm:**
     - Pyramid (4 ca): `N01` (thiếu đỉnh vuông), `N02` (thiếu góc vuông), `N03` (thiếu quan hệ chiều cao), `N04` (mâu thuẫn: 2 đỉnh vuông).
     - Prism (2 ca): `PRISM_N02` (mâu thuẫn: 2 đỉnh vuông), `PRISM_N03` (ngoài phạm vi: lăng trụ xiên).

### 5.3. Bảng Kiểm Kê Bằng Chứng (EVIDENCE_INVENTORY)

| Chỉ Số Kiểm Kê | Giá Trị | Ghi Chú Phương Pháp Luận |
|---|---|---|
| `frozen_case_count` | **18** | 12 ca dương, 6 ca âm thuộc 2 họ hình |
| `analyze_response_available_count` | **0** | Toàn bộ raw response từ Gemini Analyze đã được redact theo quy tắc an toàn |
| `request_contract_available_count` | **18** | Đầy đủ 18 đặc tả hợp đồng chuẩn tắc trong manifest và fixture có thể xác minh băm |
| `llm_synthesis_response_available_count` | **0** | Không có bản ghi cached LLM synthesis nào cho 18 ca này trong repository |
| `cases_with_complete_paired_evidence` | **0** | Chưa đủ cặp bằng chứng ngoại tuyến hoàn chỉnh (Compiler + LLM Synthesis) |
| `cases_with_missing_llm_baseline` | **18** | Cả 18 ca đều thiếu nhánh đối chứng LLM synthesis ngoại tuyến |
| `cases_with_truncated_or_unverifiable_artifacts` | **0** | Không có artifact nào bị cắt xén, sai lệch băm hoặc không thể xác minh |
| `missing_case_ids` | `P01`–`P08`, `N01`–`N04`, `PRISM_P02`–`PRISM_P05`, `PRISM_N02`–`PRISM_N03` | Toàn bộ 18 ca evaluation |

### 5.4. Kết Luận Kiểm Kê & Bất Biến An Toàn
- **Tính khả thi của nhánh Hybrid:** 100% (18/18) ca có `RequestContract` xác thực, cho phép chạy replay kiểm chứng trình biên dịch tất định hoàn toàn ngoại tuyến.
- **Khoảng trống nhánh LLM_ONLY:** Do các wave trước tập trung vào thẩm định compiler và prompt diagnostic, repository **hoàn toàn không lưu cache LLM synthesis response** cho 18 ca evaluation này.
- **Bất biến liêm chính dữ liệu:** Nghiêm cấm mọi hành vi suy đoán hoặc tái tạo dữ liệu còn thiếu từ `problem_text`, ground truth, báo cáo Markdown hoặc đoạn preview bị cắt. Thiếu dữ liệu phải ghi rõ `NOT_AVAILABLE` hoặc `GAP`.

---

## 6. Quy Tắc Lặp & Tiêu Chí Tái Lập (Repetition Policy)

Quy định cố định số lần lặp:

$$\text{REPETITION\_COUNT\_K} = 3$$

### 1. Nhánh Baseline (`LLM_ONLY`)
- Thu thập tối đa $K=3$ quan sát synthesis độc lập trên cùng một `COMMON_INPUT` (nếu có evidence).
- Trong task hiện tại: Ghi nhận trạng thái `NOT_AVAILABLE`; **tuyệt đối không tự ý phát lệnh gọi live API để lấp đầy dữ liệu.**

### 2. Nhánh Đề Xuất (`HYBRID`)
- Thực hiện replay trình biên dịch tất định $K=3$ lần liên tiếp trên cùng một `COMMON_INPUT`.
- **Tiêu chuẩn PASS về Reproducibility:**  
  $$\text{semantic\_program\_hash\_run\_1} == \text{semantic\_program\_hash\_run\_2} == \text{semantic\_program\_hash\_run\_3}$$  
  đồng thời Scene3D hash và final volume answer phải giống nhau 100%. Bất kỳ sai lệch dù ở mức bit nào đều bị đánh rớt tiêu chí tái lập.

---

## 7. Hệ Thống Tiêu Chí Đánh Giá (Evaluation Metrics)

Mọi tiêu chí đều được định nghĩa công thức toán học, mẫu số xác định, cách xử lý trường hợp không áp dụng (N/A) và nguyên tắc fail-closed:

| Tiêu Chí | Hạng | Tử Số (Numerator) | Mẫu Số (Denominator) | Quy Tắc N/A & Fail-Closed | Đơn Vị |
|---|---|---|---|---|---|
| **Structured Contract Validity Rate (SCVR)** | Primary (E2E) / Eligibility (Primary Isolated) | Số ca trích xuất được `RequestContract` hợp lệ cú pháp và Pydantic schema | Tổng số ca đánh giá ($N=18$) | Trong PRIMARY_ARCHITECTURE_ISOLATED_EVALUATION: đóng vai trò `COMMON_INPUT_ELIGIBILITY_CHECK` (điều kiện cần vào benchmark, không phải comparative outcome). Trong SECONDARY_END_TO_END_EVALUATION: là primary comparative metric hợp lệ. Lỗi JSON hoặc schema validation tính là $0$. Không có N/A. | Ca đề bài |
| **Semantic Fact Exact Match (SFE-EM)** | Primary | Số quan hệ hình học và độ dài khớp chính xác với Ground Truth | Tổng số quan hệ và độ dài kỳ vọng trong Ground Truth của positive cases | **Báo cáo chính trên positive cases.** Với ca âm: chỉ chấm tập valid facts nếu Ground Truth đã định nghĩa rõ; nếu chưa định nghĩa thì ghi `N/A`, không tự suy diễn. Thừa/thiếu/sai nhãn đỉnh tính là $0$. | Quan hệ / Độ dài |
| **Topology Exact Match Rate (TEMR)** | Primary | Số ca dương sinh ra Scene3D có đúng số đỉnh $V$, cạnh $E$, mặt $F$ | Tổng số ca dương ($N_{\text{pos}}=12$) | Ca âm là N/A (loại khỏi mẫu số). Sai bất kỳ số lượng $V, E, F$ nào tính là $0$. | Ca dương |
| **Final Answer Exact Match Rate (FAEMR)** | Primary | Số ca dương có đáp số thể tích trong `final_memory` khớp giá trị phân số (`Fraction`) trong Ground Truth | Tổng số ca dương ($N_{\text{pos}}=12$) | Ca âm là N/A. So sánh phân số chính xác tuyệt đối, không dùng float xấp xỉ. Lệch tính là $0$. | Ca dương |
| **End-to-End Valid Scene Rate (EVSR)** | Primary | Số ca dương vượt qua toàn bộ các cổng thẩm định và hiển thị thành công trên Scene3D | Tổng số ca dương ($N_{\text{pos}}=12$) | Ca âm là N/A. Bất kỳ lỗi visual obligation hay render fail đều tính là $0$. | Ca dương |
| **Contradiction Detection Rate (CDR)** | Secondary | Số ca âm có dữ kiện mâu thuẫn (`N04`, `PRISM_N02`) bị từ chối an toàn với mã `REFUSE` / `CONTRADICTION` | Tổng số ca mâu thuẫn ($N_{\text{contra}}=2$) | Ca không có mâu thuẫn là N/A. Chấp nhận vẽ hình hoặc tính đáp số cho đề mâu thuẫn tính là $0$. | Ca mâu thuẫn |
| **Safe Refusal Rate (SRR)** | Secondary | Số ca âm (thiếu dữ kiện, mâu thuẫn, out-of-scope) được từ chối an toàn mà không sinh cảnh giả | Tổng số ca âm ($N_{\text{neg}}=6$) | Ca dương là N/A. Sinh cảnh hoặc đáp số cho ca âm tính là vi phạm an toàn ($0$). | Ca âm |
| **Deterministic Consistency (CRC)** | Secondary | Số ca mà $100\%$ các lần chạy lặp lại ($K=3$) cho ra cùng băm `SemanticProgramSpec` | Tổng số ca được phục vụ | Ca bị từ chối xét theo tính nhất quán của mã lỗi. Lệch băm giữa các lần chạy tính là không nhất quán ($0$). | Ca phục vụ |
| **Token Cost Breakdown** | Secondary | Số token phân tách theo từng tầng kiến trúc qua API telemetry | Số ca đánh giá | Tách bạch 4 thành phần: (a) shared analyze, (b) llm synthesis, (c) compiler incremental = 0, (d) total end-to-end. | Token / ca |
| **Pipeline Latency** | Secondary | Thời gian thực thi (Wall-clock time) theo từng chặng | Số ca đánh giá | **Báo cáo median, IQR và min–max.** Phân rã: Analyze ms, Synthesis/Compile ms, Scene build ms. Phân vị p95 chỉ là mô tả bổ sung nếu đủ quan sát. | Millisecond |
| **Backend Trace Completeness** | Secondary | Số bước suy diễn hình học trong `FactGraph` và `Compiler` có gắn `source_fact_id` và kiểu thao tác tường minh | Tổng số bước trong trace | Nhánh LLM_ONLY không có FactGraph trace thì đánh dấu `NOT_AVAILABLE`. | Bước suy diễn |
| **UI Trace Consumption** | Secondary | Mức độ tiếp nhận và hiển thị trace của Scene3D UI controller | Tổng số ca hiển thị | **Nếu UI chưa hỗ trợ thì ghi `NOT_ESTABLISHED`, tuyệt đối không tính là $0$.** | Tỷ lệ hỗ trợ |

---

## 8. Phân Tầng Kết Quả & Giới Hạn Phương Pháp Luận

### 8.1. Phân Tầng Kết Quả Bắt Buộc (Family Stratification)
Để tránh hiện tượng che giấu sai lệch giữa các họ hình khác nhau, mọi báo cáo kết quả phải phân rã độc lập theo 4 tầng:
1. **Pyramid Strata:** 8 ca dương (`P01`–`P08`) và 4 ca âm (`N01`–`N04`).
2. **Prism Strata:** 4 ca dương (`PRISM_P02`–`PRISM_P05`) và 2 ca âm (`PRISM_N02`–`PRISM_N03`).
3. **Pooled Micro-Average:** Tính trung bình gộp trên toàn bộ $N=18$ ca đánh giá.
4. **Family Macro-Average:** Tính trung bình cộng giản đơn giữa hai họ hình học (Pyramid và Prism), đảm bảo trọng số ngang nhau.

### 8.2. Tuyên Bố Phương Pháp Luận Về Cỡ Mẫu (Methodological Statement)
> **“Do mẫu nhỏ, có chủ đích và không đại diện ngẫu nhiên, nghiên cứu không dựa vào giả định tham số để suy rộng quần thể.”**

- Cỡ mẫu $N=18$ (12 dương, 6 âm) được xây dựng có chủ đích (`Purposive Sampling`) nhằm bao phủ các hiện tượng ngôn ngữ và hình học phức tạp, không phải là mẫu ngẫu nhiên độc lập từ một phân phối tự nhiên.
- Nghiên cứu **tuyệt đối không áp dụng các kiểm định thống kê tham số hình thức** (như Student's t-test, ANOVA, hoặc tính toán p-value). Việc gán các giá trị p-value hình thức trên bộ dữ liệu kiểm thử phần mềm này là ngụy biện thống kê.
- Toàn bộ phân tích khoa học dựa trên:
  1. Thống kê mô tả (Descriptive Statistics: median, IQR, min–max).
  2. Tỷ lệ chính xác tuyệt đối (Exact Match Percentage).
  3. Bảng chéo ghép cặp (Paired Contingency Table).
  4. Phân tích định tính bệnh học từng ca (Case-by-case Failure Pathology).

---

## 9. Ngân Sách Request & Cơ Chế Cổng Dừng (Decision Gate)

### 9.1. Ngân Sách Request Của Task Hiện Tại
- `OFFLINE_REQUEST_BUDGET = 0`
- `ACTUAL_REQUESTS = 0`
- Tuyệt đối không thực hiện bất kỳ lệnh gọi mạng hoặc API nào trong task hiệu chỉnh ngoại tuyến.

### 9.2. Công Thức Đăng Ký Ngân Sách Cho Wave Live Tương Lai
Mọi ước lượng cho đợt thu thập dữ liệu trực tuyến tiếp theo phải tuân theo công thức tiền đăng ký:

$$\text{TOTAL\_LIVE\_REQUESTS} = \text{shared\_analyze\_requests} + \text{llm\_only\_synthesis\_requests} + \text{permitted\_retries}$$

- Mọi con số live cụ thể phải được quyết định dựa trên kết quả kiểm kê bằng chứng (`evidence_inventory`) và phải có một tài liệu tiền đăng ký riêng biệt trước khi bấm máy.

### 9.3. Cổng Ra Quyết Định (Decision Gate)

Sau khi hoàn tất kiểm kê bằng chứng ngoại tuyến, hệ thống đối chiếu với 3 kịch bản:

- **Kịch bản A:** Đủ common `RequestContract` và đủ cached `LLM_ONLY` synthesis responses.  
  $\longrightarrow$ `FINAL_DECISION = OFFLINE_PAIRED_COMPARATIVE_BENCHMARK_READY`  
  $\longrightarrow$ `NEXT_ACTION = RUN_OFFLINE_PAIRED_COMPARATIVE_BENCHMARK`

- **Kịch bản B:** Có đầy đủ `RequestContract` chuẩn tắc nhưng thiếu cached `LLM_ONLY` synthesis responses cho tập 18 ca đóng băng.  
  $\longrightarrow$ **`FINAL_DECISION = OFFLINE_HYBRID_REPLAY_READY_BUT_PAIRED_LLM_BASELINE_GAP`**  
  $\longrightarrow$ **`NEXT_ACTION = PREREGISTER_LIMITED_LIVE_BASELINE_COLLECTION`**

- **Kịch bản C:** Thiếu cả `RequestContract` chuẩn tắc có thể xác minh được.  
  $\longrightarrow$ `FINAL_DECISION = EVALUATION_EVIDENCE_NOT_READY`  
  $\longrightarrow$ `NEXT_ACTION = BUILD_VERIFIABLE_COMMON_INPUT_DATASET`

### Kết luận thẩm định:
Căn cứ trên kết quả kiểm kê thực tế tại Mục 5, repository xác lập quyết định chính thức:

```yaml
STATUS: METHOD_RECONCILIATION_VERIFIED
FINAL_DECISION: OFFLINE_HYBRID_REPLAY_READY_BUT_PAIRED_LLM_BASELINE_GAP
NEXT_ACTION: PREREGISTER_LIMITED_LIVE_BASELINE_COLLECTION
```

---

## 10. Kế Hoạch Chuyển Tiếp

1. Giữ nguyên working tree sạch (chỉ bảo toàn trạng thái deleted của `frontend/public/favicon.svg` của người dùng).
2. Chuẩn bị tài liệu tiền đăng ký cho đợt gọi live có kiểm soát nhằm thu thập $K=3$ mẫu baseline `LLM_ONLY` synthesis cho 18 ca đóng băng theo đúng công thức `TOTAL_LIVE_REQUESTS`.
