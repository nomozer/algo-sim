# MIGRATION_CHECKLIST.md — 20 Cổng Di Chuyển Sang Compiler-First

> **Tài liệu Canonical kiểm soát việc chuyển giao từ chế độ mặc định `LLM_ONLY` sang `COMPILER_FIRST`.**
> Mọi cổng đều bắt buộc có trạng thái rõ ràng, bằng chứng máy, blocker hiện tại và bước kiểm thử kế tiếp.
> **Nguyên tắc thẩm quyền:** Không dùng kết quả thử nghiệm quy mô nhỏ (pilot) để đánh giá `PRODUCTION_READY`.

---

## 1. Danh Sách 20 Cổng Kiểm Soát Di Chuyển

### GATE-01: Structured Analyze
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `docs/STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION.md`, Analyze trích xuất `structured_relations` chính xác cho các bài chóp cơ sở.
- **BLOCKER:** Chưa đánh giá độ ổn định trên các họ bài toán phức tạp hơn (hình lăng trụ, khối tròn xoay).
- **NEXT_TEST:** Benchmark Analyze trên 20 bài toán thuộc họ hình học thứ hai.

### GATE-02: Contract Validation
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `backend/app/simulation/contract.py`, Pydantic schema validation bắt các quan hệ lỗi và đóng băng `RequestContract`.
- **BLOCKER:** Chưa mở rộng schema cho các quan hệ không gian bậc cao (ví dụ: góc nhị diện, khoảng cách chéo).
- **NEXT_TEST:** Kiểm thử schema validation với quan hệ mặt phẳng vuông góc và lăng trụ đều.

### GATE-03: FactGraph Safety
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `backend/app/simulation/fact_graph.py`, `test_fact_graph_contract_extension.py` (fail-closed khi dữ kiện mâu thuẫn).
- **BLOCKER:** Chưa tích hợp suy diễn quan hệ bắc cầu (transitive relation inference) cho đa giác phức tạp.
- **NEXT_TEST:** Kiểm thử FactGraph với dữ kiện tam giác đồng dạng và thiết diện cắt.

### GATE-04: Primitive Coverage
- **STATUS:** PARTIAL
- **EVIDENCE:** `backend/app/simulation/geometry_compiler/`, hỗ trợ `right_triangle_base_pyramid_volume`. Đã tiền đăng ký họ thứ hai `right_triangle_base_right_prism_volume` (`docs/PRIMITIVE_COMPILER_SECOND_FAMILY_SELECTION_AND_PREREGISTRATION.md`).
- **BLOCKER:** Chưa triển khai vertical slice cho họ lăng trụ đứng đáy tam giác vuông (`construct_prism` primitive và nút `prism` trong `FactGraph`).
- **NEXT_TEST:** Triển khai `construct_prism` và vertical slice trong wave `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE`.

### GATE-05: Compiler Correctness
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `docs/GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE.md`, compiler sinh `SemanticProgramSpec` tất định không lỗi.
- **BLOCKER:** Chưa có cơ chế giải phương trình tham số cho các bài toán định lượng biến thiên.
- **NEXT_TEST:** Unit test tính đúng đắn cho bộ tham số tổng quát.

### GATE-06: Topology Verification
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `backend/tests/geometry/test_model_variance_evidence_review.py`, topology của khối chóp được dựng đầy đủ (đỉnh, cạnh, mặt).
- **BLOCKER:** Chưa kiểm chứng tính đúng đắn tô-pô cho đa diện không lồi hoặc khối có lỗ.
- **NEXT_TEST:** Kiểm tra tính đóng (closed 2-manifold) của lưới đa diện sau biên dịch.

### GATE-07: Final-Memory & Answer Correctness
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `backend/tests/geometry/test_model_variance_evidence_review.py`, `final_memory` và đáp số thể tích khớp 100% với ground truth.
- **BLOCKER:** Cần mở rộng sang các bài toán hỏi về góc, khoảng cách và diện tích thiết diện.
- **NEXT_TEST:** Benchmark đối chiếu kết quả tính toán số học trên tập dữ liệu mở rộng.

### GATE-08: Visual Quality & Fidelity
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** Cổng bao phủ nghĩa vụ trực quan C1/C2 (`Visual Obligation Gate`), browser contact sheet trên desktop/mobile.
- **BLOCKER:** Tỉ lệ co giãn trục tọa độ trong một số trường hợp làm hình vẽ khó quan sát.
- **NEXT_TEST:** Đánh giá điểm thẩm mỹ trực quan tự động dựa trên độ phân tán góc nhìn.

### GATE-09: Layout & Camera
- **STATUS:** PARTIAL
- **EVIDENCE:** Camera orbit mặc định hoạt động ổn định trên `SimulationWorkspace`.
- **BLOCKER:** Chưa có bộ giải tự động căn chỉnh camera theo hướng quan sát tối ưu của từng họ hình.
- **NEXT_TEST:** Triển khai thuật toán tính bounding sphere và đặt camera tự động.

### GATE-10: Hidden Lines Detection
- **STATUS:** NOT_STARTED
- **EVIDENCE:** `docs/SCENE3D_DYNAMIC_HIDDEN_LINES_AND_READABILITY.md`, renderer hiện chưa tính toán nét đứt động theo góc nhìn.
- **BLOCKER:** Thuật toán Raycasting hoặc Depth-buffer pass cho nét khuất chưa được cài đặt trong Three.js renderer.
- **NEXT_TEST:** Viết prototype phân tách nét khuất trong `frontend/src/simulations/domains/geometry/`.

### GATE-11: Compiler-First Routing
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Hệ thống hiện tại gọi LLM synthesis trực tiếp trong `ai/pipeline.py`.
- **BLOCKER:** Chưa xây dựng module `Router` kiểm tra tính hợp lệ (`is_compiler_eligible`) trước khi gọi LLM.
- **NEXT_TEST:** Tạo router middleware và unit tests rẽ nhánh.

### GATE-12: Fallback Mechanism
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Chưa có cơ chế chuyển giao lỗi sang LLM synthesis fallback.
- **BLOCKER:** Cần định nghĩa rõ các mã lỗi compiler có thể chuyển tiếp (recoverable) và không thể chuyển tiếp (fatal).
- **NEXT_TEST:** Test kịch bản cố tình đưa bài toán ngoài diện hỗ trợ để kiểm tra fallback suôn sẻ.

### GATE-13: Canary Deployment
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Chưa có hạ tầng phân luồng phần trăm request thực nghiệm.
- **BLOCKER:** Cần cấu hình reverse proxy hoặc feature flag có trọng số.
- **NEXT_TEST:** Test phân bổ tải 10% compiler-first và 90% default.

### GATE-14: Rollback Mechanism
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Quy trình rollback hiện tại dựa trên Git commit reversion thủ công.
- **BLOCKER:** Chưa có cơ chế ngắt mạch (circuit breaker) tự động ngắt compiler-first khi tỉ lệ lỗi vượt ngưỡng.
- **NEXT_TEST:** Kiểm thử circuit breaker ngắt mạch trong 500ms khi tiêm lỗi hàng loạt.

### GATE-15: Holdout Benchmark
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Tập bài toán kiểm thử hiện tại là tập phát triển (development set).
- **BLOCKER:** Chưa niêm phong bộ dữ liệu kiểm thử độc lập (held-out test set) do người ngoài cung cấp.
- **NEXT_TEST:** Tiếp nhận và đóng băng bộ đề kiểm thử độc lập từ giáo viên hướng dẫn.

### GATE-16: Token & Latency Measurement
- **STATUS:** PARTIAL
- **EVIDENCE:** Đo lường đơn lẻ cho thấy compiler tiết kiệm thời gian và 0 token synthesis so với LLM.
- **BLOCKER:** Chưa có hạ tầng đo lường telemetry tự động ghi nhận token consumption chính xác ở production.
- **NEXT_TEST:** Tích hợp bộ đo token chính xác vào HTTP transport client.

### GATE-17: Unsafe Acceptance Gate
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** Kiểm định fail-closed đã ngăn chặn việc chấp nhận các hợp đồng sai lệch hoặc mâu thuẫn.
- **BLOCKER:** Cần kiểm tra ma trận biên với các dạng quan hệ hình học suy biến (điểm trùng nhau, các điểm thẳng hàng).
- **NEXT_TEST:** Suite kiểm thử fuzzing các cấu hình hình học suy biến.

### GATE-18: Observability & Diagnostics
- **STATUS:** PARTIAL
- **EVIDENCE:** Endpoint `GET /api/diagnostics/runtime` kiểm tra danh tính và cache version.
- **BLOCKER:** Chưa có dashboard thời gian thực theo dõi tỉ lệ thành công của từng đường rẽ nhánh.
- **NEXT_TEST:** Bổ sung metric counter cho `compiler_hit`, `compiler_miss`, `fallback_success`.

### GATE-19: Cache & Version Policy
- **STATUS:** PRODUCTION_READY
- **EVIDENCE:** `CACHE_VERSION = 99` với sync-lock trong test suite và candidate verification hash 103 files.
- **BLOCKER:** Không có.
- **NEXT_TEST:** Duy trì kiểm chứng tự động trước mọi commit.

### GATE-20: User & Pedagogical Evaluation
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Chưa thực hiện khảo sát hoặc đo lường tác động sư phạm trên người học thật.
- **BLOCKER:** Cần chuẩn bị kịch bản thực nghiệm sư phạm và bảng câu hỏi khảo sát chuẩn SUS/TAM.
- **NEXT_TEST:** Thiết kế đề cương thử nghiệm đánh giá hiệu quả học tập với nhóm học sinh đối chứng.
