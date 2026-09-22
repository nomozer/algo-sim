# OPEN_ISSUES.md — Danh mục các vấn đề kỹ thuật đang mở

> **Tài liệu Canonical cho việc theo dõi các vấn đề và giới hạn kỹ thuật của hệ thống.**
> Mọi issue đều có Stable ID theo tiền tố chuẩn: `ISSUE-ARCH-*`, `ISSUE-EVAL-*`, `ISSUE-DOCS-*`, `ISSUE-OPS-*`, `ISSUE-RESEARCH-*`.
> Chỉ ghi nhận các vấn đề được xác nhận bởi bằng chứng thực tế từ repository.

---

### ISSUE-ARCH-COMPILER-COVERAGE-NARROW
- **description:** Primitive compiler hiện tại chỉ hỗ trợ một họ bài toán đơn lẻ là tính thể tích khối chóp có đáy tam giác vuông (`right_triangle_base_pyramid_volume`).
- **evidence:** `backend/app/simulation/compiler/primitive_compiler.py`, báo cáo `docs/GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE.md`.
- **impact:** Hệ thống chưa thể biên dịch tất định các họ hình học không gian phổ biến khác trong chương trình THPT.
- **scope:** `backend/app/simulation/compiler/`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-COMPILER-FIRST-ROUTING
- **description:** Cổng định tuyến compiler-first trong pipeline chính chưa được xây dựng; hệ thống hiện tại vẫn đi qua LLM synthesis mặc định.
- **evidence:** `backend/app/ai/pipeline.py`, cờ `DEFAULT_MODE = LLM_ONLY`.
- **impact:** Người dùng chưa được hưởng lợi từ tốc độ và tính tất định của compiler trong luồng chạy thực tế.
- **scope:** `backend/app/ai/pipeline.py`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-FALLBACK-MECHANISM
- **description:** Chưa có cơ chế chuyển giao tự động và an toàn từ compiler sang LLM synthesis khi bài toán nằm ngoài tập primitive được hỗ trợ.
- **evidence:** `backend/app/simulation/compiler/` chưa có module router/fallback adapter.
- **impact:** Nếu bật compiler-first mà gặp bài toán không thuộc diện hỗ trợ thì hệ thống sẽ dừng thay vì fallback.
- **scope:** `backend/app/ai/pipeline.py`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-CANARY-OR-ROLLBACK
- **description:** Chưa có cơ chế phân luồng canary để thử nghiệm tỉ lệ nhỏ trên production và chưa có kịch bản rollback tức thì khi gặp lỗi biên dịch.
- **evidence:** Chưa có middleware/routing layer hỗ trợ canary splitting trong `backend/app/main.py`.
- **impact:** Rủi ro gián đoạn dịch vụ khi kích hoạt tính năng mới trên toàn hệ thống.
- **scope:** `backend/app/`
- **status:** OPEN
- **owner_class:** OPERATIONS / ARCHITECTURE
- **suggested_wave:** P5 (Migration)
- **default_switch_blocker:** YES

### ISSUE-ARCH-NO-SPATIAL-LAYOUT-SOLVER
- **description:** Chưa có bộ giải bố cục không gian 3D tự động; tọa độ các điểm hiện do các bước dựng hình cơ sở xác định cục bộ, có thể gây mất cân đối thị giác ở các góc phức tạp.
- **evidence:** `backend/app/simulation/` thiếu solver tối ưu hóa ràng buộc tọa độ toàn cục.
- **impact:** Một số hình vẽ phức tạp có thể bị dồn góc hoặc khó nhìn trong không gian 3D.
- **scope:** `backend/app/simulation/` & `frontend/src/`
- **status:** OPEN
- **owner_class:** VISUALIZATION
- **suggested_wave:** P3 (Visualization)
- **default_switch_blocker:** NO

### ISSUE-ARCH-NO-HIDDEN-LINES
- **description:** Chưa có giải thuật phát hiện và diễn họa nét khuất động học (dynamic hidden-line detection) khi người dùng xoay phối cảnh 3D.
- **evidence:** `docs/SCENE3D_DYNAMIC_HIDDEN_LINES_AND_READABILITY.md`, renderer hiện dùng nét liền hoặc quy ước cố định.
- **impact:** Học sinh có thể gặp khó khăn trong việc phân biệt các cạnh bị che khuất khi quan sát khối đa diện.
- **scope:** `frontend/src/simulations/domains/geometry/`
- **status:** OPEN
- **owner_class:** VISUALIZATION
- **suggested_wave:** P3 (Visualization)
- **default_switch_blocker:** NO

### ISSUE-ARCH-NO-OCR-IMAGE-PIPELINE
- **description:** Chưa triển khai đường ống bóc tách vùng đề bài và OCR nhận diện văn bản toán học từ ảnh chụp camera điện thoại.
- **evidence:** `backend/app/ingestion/input.py` chỉ tiếp nhận text đầu vào.
- **impact:** Người dùng phải gõ lại đề bài bằng văn bản thay vì chụp ảnh trực tiếp từ sách giáo khoa.
- **scope:** `backend/app/ingestion/`
- **status:** OPEN
- **owner_class:** INGESTION
- **suggested_wave:** P4 (Image Acquisition)
- **default_switch_blocker:** NO

### ISSUE-EVAL-TOKEN-OPTIMIZATION-NOT-ESTABLISHED
- **description:** Việc giảm token tiêu thụ của compiler so với LLM synthesis mới chỉ là quan sát thực nghiệm trên một lát cắt nhỏ, chưa được xác lập như một đặc tính đo lường tin cậy ở quy mô production.
- **evidence:** `docs/MODEL_VARIANCE_EVIDENCE_REVIEW.md`, `FINAL_DECISION.json`.
- **impact:** Không được tuyên bố trong luận văn rằng compiler đã tối ưu hóa token ở mức độ hệ thống hoàn chỉnh.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P6 (Thesis Evaluation)
- **default_switch_blocker:** NO

### ISSUE-EVAL-STATISTICAL-SIGNIFICANCE-UNESTABLISHED
- **description:** Số lượng mẫu kiểm thử (n-count) của các phép đo live hiện tại còn nhỏ, chưa đủ để đưa ra các kết luận có ý nghĩa thống kê.
- **evidence:** `docs/THESIS_READINESS.md §7`, `docs/EVIDENCE_INDEX.md`.
- **impact:** Các công bố định lượng cần được giới hạn trong phạm vi thực nghiệm định tính hoặc nghiên cứu tình huống (case study).
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P6 (Thesis Evaluation)
- **default_switch_blocker:** NO

### ISSUE-EVAL-P03-P05-HISTORICAL-CAUSE-NOT-ESTABLISHED
- **description:** Nguyên nhân gốc rễ của cụm lỗi lịch sử Analyze P03/P05 (`MODEL_MALFORMED_RELATION`) chưa được xác lập chắc chắn vì hai ca live retry đều trả về kết quả hợp lệ mà không tái hiện lỗi.
- **evidence:** `docs/MODEL_VARIANCE_EVIDENCE_REVIEW.md`, `FINAL_DECISION.json` (`HISTORICAL_ROOT_CAUSE = NOT_ESTABLISHED`).
- **impact:** Cần duy trì giả thuyết về tính biến thiên tự nhiên của mô hình (model variance) và tiếp tục theo dõi qua các lần đo sau.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** NO

### ISSUE-EVAL-P03-P05-TOKEN-UNKNOWN
- **description:** Lượng token sử dụng của hai request P03 và P05 trong đợt live retry trước đây được ghi nhận là 0 do giới hạn của client HTTP, sau đó được đính chính thành UNKNOWN.
- **evidence:** `docs/evaluation/geometry/photo-problem-to-scene/fresh-preregistered-failure-reproduction-retry/MACHINE_RAW_OUTPUT.json`.
- **impact:** Số liệu token của wave đó không được đưa vào bảng phân tích so sánh định lượng của luận văn.
- **scope:** `docs/evaluation/`
- **status:** OPEN
- **owner_class:** EVALUATION
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** NO

### ISSUE-DOCS-CRLF-GITATTRIBUTES-RISK
- **description:** Rủi ro chuyển đổi ký tự kết thúc dòng (CRLF / LF) giữa môi trường phát triển Windows và máy chủ Linux có thể ảnh hưởng đến hash SHA-256 của các artifact văn bản.
- **evidence:** `.gitattributes` hiện quản lý chuẩn hóa LF cho các file text và JSON.
- **impact:** Cần đảm bảo mọi công cụ đo lường và kiểm chứng đều áp dụng chuẩn hóa LF trước khi băm nội dung.
- **scope:** Repository configuration
- **status:** OPEN
- **owner_class:** DOCUMENTATION / OPS
- **suggested_wave:** P0 (Documentation Hardening)
- **default_switch_blocker:** NO

### ISSUE-OPS-ORPHANED-TEMP-DIRECTORIES
- **description:** Các thư mục tạm được tạo trong quá trình chạy test worktree (ví dụ `D:/tmp/mvep-*`, `D:/tmp/algo-sim-*`) có thể tồn đọng nếu quy trình dọn dẹp gặp sự cố ngoài ý muốn.
- **evidence:** Thư mục `D:/tmp/` chứa các artifacts bằng chứng máy từ các wave trước.
- **impact:** Chiếm dụng dung lượng đĩa và có nguy cơ gây nhầm lẫn nếu không được quản lý vòng đời rõ ràng.
- **scope:** Scripts & Test harnesses
- **status:** OPEN
- **owner_class:** OPERATIONS
- **suggested_wave:** P0 (Documentation Hardening)
- **default_switch_blocker:** NO

### ISSUE-ARCH-PRISM-COMPILER-GAP
- **description:** Primitive compiler thiếu primitive construct_prism(name, base_cycle, top_cycle, correspondence), FactGraph thiếu loại nút prism, và 10 tầng phối hợp khác (RequestContract, relations, adapter, eligibility, IR, gates, topology, measurement, routing, frontend renderer) chưa hỗ trợ họ lăng trụ đứng đáy tam giác vuông đã tiền đăng ký (right_triangle_base_right_prism_volume).
- **evidence:** `docs/SECOND_FAMILY_PREREGISTRATION_EVIDENCE_REPAIR_OFFLINE.md`, `docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/VERTICAL_SLICE_SCOPE_MAP.json`.
- **impact:** Họ bài `right_triangle_base_right_prism_volume` chưa thể biên dịch tất định cho đến khi hoàn thành vertical slice qua đủ 12 tầng kỹ thuật.
- **scope:** `backend/app/simulation/geometry_compiler/`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES

### ISSUE-ARCH-REQUEST-CONTRACT-PRISM-GAP
- **description:** `RequestContract` tại `START_HEAD` không có trường chứa `prism identity`, `base_cycle`, `top_cycle`, hay `correspondence` (`REQUEST_CONTRACT = CHANGE_REQUIRED`). Do `contract_adapter` bị cấm đọc `problem_text` (R0 / fail-closed), tồn tại bế tắc kiến trúc giữa Direction A (mở rộng schema gửi LLM, đòi hỏi bump `CACHE_VERSION`, làm mất hiệu lực candidate freeze 103 files và yêu cầu live revalidation) và Direction B (suy diễn nội bộ tất định nhưng chưa có cơ chế trích xuất các thông tin này từ các trường hiện có mà không đọc text).
- **evidence:** `docs/SECOND_FAMILY_SOURCE_SCOPE_RECONCILIATION_OFFLINE.md`, `docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/FINAL_DECISION.json`.
- **impact:** Chưa thể triển khai vertical slice cho họ lăng trụ (`VERTICAL_SLICE_ALLOWED = NO`, `FINAL_DECISION = INCOMPLETE`) cho đến khi kiến trúc dữ liệu đầu vào của lăng trụ được giải quyết và phê duyệt.
- **scope:** `backend/app/simulation/contract.py`, `backend/app/simulation/contract_adapter.py`
- **status:** OPEN
- **owner_class:** ARCHITECTURE
- **suggested_wave:** P1 (Primitive Compiler Expansion)
- **default_switch_blocker:** YES



