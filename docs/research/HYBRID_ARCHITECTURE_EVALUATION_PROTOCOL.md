# HYBRID_ARCHITECTURE_EVALUATION_PROTOCOL — Quy Trình Tiền Đăng Ký Đánh Giá So Sánh Kiến Trúc Hybrid và LLM_ONLY

> **Trạng thái:** Tiền đăng ký (Preregistration Draft) — Nghiên cứu Khóa luận tốt nghiệp  
> **Base Commit HEAD:** `f3b098fc7d98acb7a6fbabe0a8b11a30b068db16`  
> **Candidate Tree Hash:** `6ebfcb9002b5c3ee…` (`CACHE_VERSION = 100`)  
> **File Dữ Liệu Máy Đọc:** [`docs/research/hybrid_architecture_evaluation_manifest.json`](file:///d:/Documents/projects/algo-sim/docs/research/hybrid_architecture_evaluation_manifest.json)  
> **Bất Biến:** `DEFAULT_MODE = LLM_ONLY` (không đổi), `PRODUCT_CODE_CHANGED = NO`, `LIVE_REQUESTS_EXECUTED = 0`.

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

Tài liệu này xác lập **phạm vi đánh giá khoa học tối thiểu** nhằm so sánh thực nghiệm một cách khách quan, minh bạch giữa hai kiến trúc trên hai họ hình học đã được cài đặt và kiểm chứng đầy đủ.

---

## 2. Định Nghĩa Hai Nhánh Kiến Trúc

### Kiến Trúc A: Baseline (`LLM_ONLY`)
- **Luồng xử lý:**  
  $$\text{Đề bài văn bản} \longrightarrow \text{Gemini Analyze} \longrightarrow \text{RequestContract} \longrightarrow \text{Gemini Synthesis} \longrightarrow \text{Validator/Kernel} \longrightarrow \text{Scene3D}$$
- **Đặc trưng:** Cả hai bước phân tích ngữ nghĩa và sinh chương trình hình học (`SemanticProgramSpec`) đều phụ thuộc vào mô hình sinh (`gemini-2.5-flash`, temperature = 0.1).
- **Cách kích hoạt:** Mặc định của hệ thống (`DEFAULT_MODE = "LLM_ONLY"`, khi biến môi trường `GEOMETRY_COMPILER_MODE` không được đặt hoặc khác `"DETERMINISTIC_FIRST"`).

### Kiến Trúc B: Đề Xuất (`HYBRID`)
- **Luồng xử lý:**  
  $$\text{Đề bài văn bản} \longrightarrow \text{Gemini Analyze} \longrightarrow \text{RequestContract} \longrightarrow \text{FactGraph} \longrightarrow \text{Primitive Compiler} \longrightarrow \text{SemanticProgramSpec} \longrightarrow \text{Validator/Kernel} \longrightarrow \text{Scene3D}$$
- **Đặc trưng:** Gemini chỉ được gọi ở tầng trích xuất ngữ nghĩa. Tầng sinh chương trình và tọa độ do trình biên dịch tất định đảm nhiệm (0 lượt gọi model).
- **Cơ chế phòng vệ:**
  - *Fail-closed Refusal:* Nếu dữ kiện tự mâu thuẫn (ví dụ: tam giác vuông tại cả 2 đỉnh), hệ thống từ chối an toàn ngay tại `FactGraph` (`REFUSE`).
  - *Safe Fallback:* Nếu đề bài ngoài phạm vi mẫu hình của compiler, hệ thống chuyển về LLM synthesis (`FALLBACK_TO_LLM`).
- **Cách kích hoạt:** Kích hoạt có kiểm soát thông qua cờ môi trường `GEOMETRY_COMPILER_MODE="DETERMINISTIC_FIRST"` tại [`backend/app/simulation/geometry_compiler/routing.py`](file:///d:/Documents/projects/algo-sim/backend/app/simulation/geometry_compiler/routing.py).

---

## 3. Câu Hỏi Nghiên Cứu (Research Questions)

Nghiên cứu tập trung vào 3 câu hỏi chính, phân định rõ giữa câu hỏi kỹ thuật, câu hỏi về tính giải thích, và loại trừ câu hỏi sư phạm (dành cho thực nghiệm dạy học sau này):

### RQ1 (Kỹ thuật — Tính Đúng Đắn Hình Học & Đáp Số)
> **Kiến trúc Hybrid có cải thiện tính đúng đắn hình học (tô-pô đỉnh/cạnh/mặt, quan hệ vuông góc) và độ chính xác của đáp số thể tích so với kiến trúc LLM_ONLY trên hai họ hình được hỗ trợ hay không?**
- *Mục tiêu:* Đối chiếu tỷ lệ sinh mesh hợp lệ, tỷ lệ đúng số đỉnh/cạnh/mặt và tỷ lệ đáp số thể tích khớp chính xác với Ground Truth.
- *Phân loại:* Câu hỏi kỹ thuật định lượng.

### RQ2 (Kỹ thuật — Tính Tái Lập & An Toàn Fail-Closed)
> **Kiến trúc Hybrid có cải thiện tính tất định (tái lập 100% qua các lần chạy lặp lại), đồng thời phát hiện và từ chối an toàn các đề bài thiếu hoặc mâu thuẫn dữ kiện tốt hơn kiến trúc LLM_ONLY hay không?**
- *Mục tiêu:* Đo lường phương sai giữa nhiều lần chạy (cross-run variance) và tỷ lệ bắt đúng các ca lỗi/mâu thuẫn mà không sinh ảo giác.
- *Phân loại:* Câu hỏi kỹ thuật định lượng và an toàn hệ thống.

### RQ3 (Khả Năng Giải Thích — Traceability & Provenance)
> **Trace dựng hình có cấu trúc của kiến trúc Hybrid có cung cấp bằng chứng giải thích minh bạch, truy xuất được xuất xứ dữ kiện (provenance) so với output sinh trực tiếp từ LLM_ONLY hay không?**
- *Mục tiêu:* Đánh giá chuỗi liên kết từ dữ kiện đề bài (`source_fact_id`) qua các bước suy diễn đến đối tượng hiển thị trên màn hình.
- *Phân loại:* Câu hỏi về tính giải thích và kiểm chứng của hệ thống.

---

## 4. Kiểm Kê Năng Lực Đo Lường & Dữ Liệu Thực Tế

### 4.1. Hai Họ Hình Học Được Hỗ Trợ
1. **Hình chóp đáy tam giác vuông có cạnh bên vuông góc với đáy** (`right_triangle_base_pyramid_volume`).
2. **Hình lăng trụ đứng có đáy là tam giác vuông** (`right_triangle_base_right_prism_volume`).

### 4.2. Kiểm Kê Dataset Văn Bản (Text Cases)
Repository hiện lưu trữ 24 ca bài toán văn bản độc lập có cấu trúc rõ ràng:
- **Họ Hình Chóp (Pyramid — 16 ca):**
  - 4 ca Pilot A/B (`B01`, `B02`, `B03`, `B04`) tại [`docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-ab-benchmark/PRIMITIVE_COMPILER_AB_MANIFEST.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-ab-benchmark/PRIMITIVE_COMPILER_AB_MANIFEST.json).
  - 8 ca Dương Đa Dạng (`P01`–`P08`) tại [`docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/CASE_REGISTRY.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/CASE_REGISTRY.json).
  - 4 ca Âm Kiểm Thử Biên (`N01`–`N04`) tại cùng registry trên.
- **Họ Hình Lăng Trụ (Prism — 8 ca):**
  - 5 ca Dương (`PRISM_P01`–`PRISM_P05`) tại [`docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_MANIFEST.json).
  - 3 ca Âm Kiểm Thử Biên (`PRISM_N01`–`PRISM_N03`) tại cùng manifest trên.

### 4.3. Phân Chia Tập Đo Lường (Tách Biệt Pilot và Frozen Evaluation)
Để đảm bảo tính khách quan khoa học, không dùng tập đánh giá để tinh chỉnh hệ thống:
1. **Tập Phát Triển / Thử Nghiệm (Development / Pilot Set — 6 ca):**
   - Pyramid: `B01`, `B02`, `B03`, `B04` (đã dùng trong wave A/B benchmark cũ).
   - Prism: `PRISM_P01` (dương chuẩn), `PRISM_N01` (âm thiếu chiều cao).
   - *Mục đích:* Dùng để kiểm tra cấu hình runner, kiểm thử tích hợp và kiểm tra định dạng dữ liệu thô.
2. **Tập Đánh Giá Đóng Băng (Frozen Evaluation Set — 18 ca):**
   - **12 ca Dương:**
     - Pyramid: `P01` (chuẩn hóa định nghĩa), `P02` (quan hệ chữ tường minh), `P03` (ký hiệu 90°), `P04` (đảo trật tự câu hỏi), `P05` (phân số), `P06` (xuống dòng và gạch đầu dòng), `P07` (vuông góc với nhau + phân số), `P08` (chiều cao đứng trước).
     - Prism: `PRISM_P02` (hoán đổi toàn bộ nhãn điểm MNP.QRS), `PRISM_P03` (dữ kiện phân số 3/2, 4/3, 5/4), `PRISM_P04` (đáy vuông tại B), `PRISM_P05` (đảo trật tự và khai đầy đủ correspondence).
   - **6 ca Âm:**
     - Pyramid: `N01` (không xác định đỉnh vuông), `N02` (bộ số 3-4-5 không nêu góc vuông), `N03` (không cho cạnh bên vuông góc đáy), `N04` (mâu thuẫn: tam giác vuông ở 2 đỉnh).
     - Prism: `PRISM_N02` (mâu thuẫn: đáy vuông ở 2 đỉnh A và B), `PRISM_N03` (ngoài phạm vi: lăng trụ xiên).

### 4.4. Đánh Giá Hiện Trạng Ảnh Đề Bài (Image Cases Gap)
- `IMAGE_CASE_COUNT = 0`.
- **Lý do khoa học:** Trong repository hiện chỉ có 12 ảnh tổng hợp Pillow (`c01`–`c12`) phục vụ kiểm thử kỹ thuật pipeline đọc ảnh tầng A, không có ảnh nào chứa bài toán về hai họ hình của compiler. Bộ ảnh chụp thực tế từ học sinh chưa được thu thập kèm Ground Truth có thẩm quyền (`REAL_PHOTO_CORPUS = NOT_ESTABLISHED`). Do đó, phạm vi đánh giá khoa học này tập trung vào bài toán dạng văn bản nhằm đảm bảo tính chặt chẽ.

### 4.5. Nguồn Ground Truth Đã Đóng Băng
Ground Truth được định nghĩa trước độc lập với mọi output của hệ thống tại:
- [`docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/GROUND_TRUTH.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/multicase-benchmark/GROUND_TRUTH.json)
- [`docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_GROUND_TRUTH.json`](file:///d:/Documents/projects/algo-sim/docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/SECOND_FAMILY_GROUND_TRUTH.json)
- Tuyệt đối không lấy kết quả chạy của model hoặc compiler để gán ngược làm Ground Truth.

---

## 5. Hệ Thống Tiêu Chí Đánh Giá (Evaluation Metrics)

Mọi tiêu chí đều được định nghĩa tường minh công thức, phạm vi mẫu số, cách xử lý trường hợp không áp dụng (N/A) và quy tắc fail-closed:

| Tiêu Chí | Hạng | Tử Số (Numerator) | Mẫu Số (Denominator) | Quy Tắc N/A & Fail-Closed | Đơn Vị Phân Tích |
|---|---|---|---|---|---|
| **Structured Contract Validity Rate (SCVR)** | Primary | Số ca trích xuất được `RequestContract` hợp lệ cú pháp và lược đồ Pydantic | Tổng số ca đánh giá ($N=18$) | Lỗi JSON hoặc schema tính là $0$. Không có N/A. | Ca đề bài |
| **Semantic Fact Exact Match (SFE-EM)** | Primary | Số quan hệ hình học và độ dài khớp chính xác với Ground Truth | Tổng số quan hệ và độ dài kỳ vọng trong Ground Truth | Thừa/thiếu/sai đỉnh tính là sai fact đó. Ca âm không có fact kỳ vọng. | Quan hệ / Độ dài |
| **Topology Exact Match Rate (TEMR)** | Primary | Số ca dương sinh ra Scene3D có đúng số đỉnh $V$, cạnh $E$, mặt $F$ | Tổng số ca dương ($N_{\text{pos}}=12$) | Ca âm là N/A (loại khỏi mẫu số). Sai bất kỳ số lượng $V, E, F$ nào tính là $0$. | Ca dương |
| **Final Answer Exact Match Rate (FAEMR)** | Primary | Số ca dương có đáp số thể tích trong `final_memory` khớp giá trị phân số (`Fraction`) trong Ground Truth | Tổng số ca dương ($N_{\text{pos}}=12$) | Ca âm là N/A. Dùng phân số chính xác, không dùng float xấp xỉ. Lệch tính là $0$. | Ca dương |
| **End-to-End Valid Scene Rate (EVSR)** | Primary | Số ca dương vượt qua toàn bộ các cổng thẩm định và mount render thành công trên Scene3D | Tổng số ca dương ($N_{\text{pos}}=12$) | Ca âm là N/A. Bất kỳ lỗi visual obligation hay render fail đều tính là $0$. | Ca dương |
| **Contradiction Detection Rate (CDR)** | Secondary | Số ca âm có dữ kiện mâu thuẫn (`N04`, `PRISM_N02`) bị từ chối an toàn với mã `REFUSE` / `CONTRADICTION` | Tổng số ca mâu thuẫn ($N_{\text{contra}}=2$) | Ca không có mâu thuẫn là N/A. Nếu hệ thống vẽ hình hoặc tính đáp số cho đề mâu thuẫn thì tính là $0$. | Ca mâu thuẫn |
| **Safe Refusal Rate (SRR)** | Secondary | Số ca âm (thiếu dữ kiện, mâu thuẫn, out-of-scope) được từ chối an toàn mà không sinh cảnh sai | Tổng số ca âm ($N_{\text{neg}}=6$) | Ca dương là N/A. Sinh cảnh hoặc đáp số cho ca âm tính là vi phạm an toàn ($0$). | Ca âm |
| **Deterministic Consistency (CRC)** | Secondary | Số ca mà $100\%$ các lần chạy lặp lại ($K=3$) cho ra cùng băm `SemanticProgramSpec` | Tổng số ca được phục vụ | Ca bị từ chối xét theo tính nhất quán của mã lỗi. Lệch băm tính là không nhất quán. | Ca phục vụ |
| **Token Usage** | Secondary | Tổng số token (prompt + completion) tiêu thụ qua API | Số ca đánh giá | Đo lường riêng cho tầng analyze và synthesis. Compiler có synthesis token = $0$. | Token / ca |
| **Pipeline Latency** | Secondary | Thời gian thực thi (Wall-clock time) theo từng chặng | Số ca đánh giá | Phân rã: Analyze ms, Synthesis/Compile ms, Scene build ms. | Millisecond |
| **Trace Completeness** | Secondary | Số bước suy diễn hình học có gắn `source_fact_id` và kiểu thao tác | Tổng số bước trong trace | Nhánh LLM_ONLY không có FactGraph trace thì đánh dấu `NOT_AVAILABLE`. | Bước dựng |

---

## 6. Thiết Kế Thực Nghiệm & Kiểm Soát Thiên Lệch

1. **Nguyên Tắc Ghép Cặp (Paired Input):**
   - Cùng một chuỗi văn bản đầu vào (chuẩn hóa UTF-8, LF, không khoảng trắng thừa) được chuyển đến cả hai nhánh A và B.
   - Không cung cấp bất kỳ gợi ý hay tham số phụ nào cho riêng một nhánh.
2. **Cố Định Bề Mặt Mô Hình:**
   - Cùng sử dụng mô hình `gemini-2.5-flash`, `temperature = 0.1`, cùng prompt và schema trích xuất tại tầng Analyze.
3. **Kiểm Soát Tính Ngẫu Nhiên & Tái Lập:**
   - Nhánh Hybrid (B): Do tính chất toán học tất định, chỉ cần chạy 1 lần và kiểm chứng tái lập qua băm SHA-256.
   - Nhánh LLM_ONLY (A): Chạy $K=3$ lần lặp lại độc lập để đo phương sai và tính nhất quán (variance).
4. **Bộ Chấm Độc Lập (Independent Evaluator):**
   - Output của hai nhánh được lưu trữ vào tệp kết quả riêng biệt.
   - Bộ chấm (Scorer) đọc output và đối chiếu với Ground Truth độc lập; không có sự can thiệp của con người vào quá trình đối chiếu.
5. **Ngân Sách & Trần Gọi API (Request Budget):**
   - Mọi request ra bên ngoài phải tuân thủ trần HTTP cứng đã đăng ký trước.
   - Áp dụng quy tắc dừng khẩn cấp (Fail-closed Stop Rule): Nếu gặp lỗi mạng, lỗi hạn mức hạn ngạch (429/503), dừng toàn bộ benchmark ngay lập tức, không retry ngầm.
6. **Đóng Băng Hệ Thống Tuyệt Đối:**
   - Sau khi quy trình này được phê duyệt và bắt đầu đo, tuyệt đối không chỉnh sửa code sản phẩm (`backend/app`, `frontend/src`), không sửa prompt hay schema để "làm đẹp số liệu".

---

## 7. Giới Hạn Phương Pháp Luận & Suy Luận Thống Kê

Để bảo vệ tính liêm chính học thuật trong khóa luận tốt nghiệp:
1. **Cỡ Mẫu Hạn Chế ($N = 18$ ca đóng băng):**
   - Cỡ mẫu 18 ca là tập bài toán đại diện chuyên biệt (purposive sample), được thiết kế bao phủ các hiện tượng ngôn ngữ và hình học phức tạp.
   - **Tuyên bố phương pháp luận:** Cỡ mẫu này **KHÔNG thỏa mãn các giả định phân phối chuẩn** để áp dụng các kiểm định thống kê suy diễn phức tạp (như Student's t-test, ANOVA hay p-value). Việc gán các giá trị p-value hình thức trên cỡ mẫu nhỏ là ngụy biện thống kê.
2. **Hình Thức Báo Cáo Được Phép:**
   - Báo cáo thống kê mô tả (Descriptive Statistics): Tỷ lệ phần trăm chính xác tuyệt đối, trung bình token, thời gian trễ trung vị (p50) và phân vị 95 (p95).
   - Bảng chéo ghép cặp (Paired Contingency Table): Phân tích trực tiếp các ca mà Hybrid đạt còn LLM_ONLY thất bại (hoặc ngược lại).
   - Phân tích bệnh học từng ca (Case-by-case Failure Pathology): Chỉ ra chính xác cơ chế thất bại (do ngữ nghĩa, do tô-pô, hay do kernel).
3. **Giới Hạn Phạm Vi Kết Luận:**
   - Kết luận về sự vượt trội của kiến trúc Hybrid chỉ có giá trị khẳng định trong phạm vi hai họ hình học đã được cài đặt trình biên dịch.
   - Không khái quát hóa thành tuyên bố *"Hybrid vượt trội trên toàn bộ toán học phổ thông"* khi chưa mở rộng compiler sang các họ hình khác.

---

## 8. Kế Hoạch Chuyển Tiếp (Next Action)

Sau khi tài liệu tiền đăng ký này được ghi nhận vào git tree:
1. Giữ nguyên working tree sạch (chỉ bảo toàn trạng thái deleted của `favicon.svg`).
2. Sẵn sàng cho wave thực thi benchmark ngoại tuyến (Offline Replay Benchmark) sử dụng các cached response và deterministic compiler, hoàn toàn không tốn quota live.
