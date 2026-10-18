# MIGRATION_CHECKLIST.md — 20 Cổng Di Chuyển Sang Compiler-First

> **Tài liệu Canonical kiểm soát việc chuyển giao từ chế độ mặc định `LLM_ONLY` sang `COMPILER_FIRST`.**
> Mọi cổng đều bắt buộc có trạng thái rõ ràng, bằng chứng máy, blocker hiện tại và bước kiểm thử kế tiếp.
> **Nguyên tắc thẩm quyền:** Không dùng kết quả thử nghiệm quy mô nhỏ (pilot) để đánh giá `PRODUCTION_READY`.

---

## 1. Danh Sách 20 Cổng Kiểm Soát Di Chuyển

### GATE-01: Structured Analyze
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `docs/evaluation/reports/STRUCTURED_GEOMETRY_RELATION_ANALYZE_LIVE_VALIDATION.md`, Analyze trích xuất `structured_relations` chính xác cho các bài chóp cơ sở.
- **BLOCKER:** Chưa đánh giá độ ổn định trên các họ bài toán phức tạp hơn (hình lăng trụ, khối tròn xoay).
- **NEXT_TEST:** Benchmark Analyze trên 20 bài toán thuộc họ hình học thứ hai.

### GATE-02: Contract Validation
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `backend/app/simulation/semantic_program/request_contract.py` (`RequestContract`; đường dẫn cũ `backend/app/simulation/contract.py` không tồn tại — sửa 2026-10-05, `cuboid-final-review`), Pydantic schema validation bắt các quan hệ lỗi và đóng băng `RequestContract`. `docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/report.md` đã hoàn thành thiết kế và tiền đăng ký hợp đồng topology đa diện tổng quát dạng 2 lớp (Internal Discriminated Union vs Model Transport Flattened Schema), giải quyết bế tắc kỹ thuật SSOT.
- **BLOCKER:** Chưa triển khai vertical slice mã sản phẩm (cần triển khai trên `RequestContract` và `contract_adapter`).
- **NEXT_TEST:** Triển khai và kiểm thử vertical slice trong wave `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE`.

### GATE-03: FactGraph Safety
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `backend/app/simulation/geometry_compiler/fact_graph.py`, `backend/tests/geometry/test_geometry_primitive_compiler.py::test_I_du_kien_do_dai_MAU_THUAN__INVALID_CONFLICT` (hai tên cũ `backend/app/simulation/fact_graph.py`, `test_fact_graph_contract_extension.py` không có trong kho — sửa 2026-10-05, `cuboid-final-review`) (fail-closed khi dữ kiện mâu thuẫn).
- **BLOCKER:** Chưa tích hợp suy diễn quan hệ bắc cầu (transitive relation inference) cho đa giác phức tạp.
- **NEXT_TEST:** Kiểm thử FactGraph với dữ kiện tam giác đồng dạng và thiết diện cắt.

### GATE-04: Primitive Coverage
- **STATUS:** PARTIAL
- **EVIDENCE:** `backend/app/simulation/geometry_compiler/`, hỗ trợ `right_triangle_base_pyramid_volume`. Đã tiền đăng ký họ thứ hai `right_triangle_base_right_prism_volume` (`docs/evaluation/geometry/photo-problem-to-scene/primitive-compiler-second-family-selection/report.md`), đính chính bằng chứng lựa chọn (`docs/evaluation/geometry/photo-problem-to-scene/second-family-preregistration-evidence-repair/report.md`), đối soát danh tính mã nguồn (`docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/report.md`), và tiền đăng ký hợp đồng topology (`docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/report.md`).
- **BLOCKER:** Chưa triển khai vertical slice trong mã nguồn sản phẩm cho họ lăng trụ đứng đáy tam giác vuông.
- **NEXT_TEST:** Triển khai vertical slice trong wave `PRIMITIVE_COMPILER_SECOND_FAMILY_VERTICAL_SLICE`.

### GATE-05: Compiler Correctness
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `docs/evaluation/reports/GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE.md`, compiler sinh `SemanticProgramSpec` tất định không lỗi.
- **BLOCKER:** Chưa có cơ chế giải phương trình tham số cho các bài toán định lượng biến thiên.
- **NEXT_TEST:** Unit test tính đúng đắn cho bộ tham số tổng quát.

### GATE-06: Topology Verification
- **STATUS:** PROVED_ON_PILOT
- **EVIDENCE:** `backend/tests/geometry/test_model_variance_evidence_review.py` (chóp cơ sở); `docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/report.md` xác lập phạm vi `SUPPORTED_TOPOLOGY_CLASS` là closed polygonal 2-manifold genus-0 (Euler $V - E + F = 2$), bảo toàn chu kỳ $D_n$, và bộ 16 fixtures kiểm chứng không phụ thuộc tọa độ.
- **BLOCKER:** Chưa triển khai bộ validator độc lập vào runtime compiler pipeline của sản phẩm.
- **NEXT_TEST:** Tích hợp validator topology vào `contract_adapter` và `compiler` trong vertical slice.

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
- **EVIDENCE:** `docs/evaluation/reports/SCENE3D_DYNAMIC_HIDDEN_LINES_AND_READABILITY.md`, renderer hiện chưa tính toán nét đứt động theo góc nhìn.
- **BLOCKER:** Thuật toán Raycasting hoặc Depth-buffer pass cho nét khuất chưa được cài đặt trong Three.js renderer.
- **NEXT_TEST:** Viết prototype phân tách nét khuất trong `frontend/src/simulations/domains/geometry/`.

### GATE-11: Compiler-First Routing
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Hệ thống hiện tại gọi LLM synthesis trực tiếp trong `ai/pipeline.py`.
- **BLOCKER:** Chưa xây dựng module `Router` kiểm tra tính hợp lệ (`is_compiler_eligible`) trước khi gọi LLM.
- **NEXT_TEST:** Tạo router middleware và unit tests rẽ nhánh.
- **AUDIT (2026-10-05, `cuboid-final-review`):** evidence và blocker trên đã cũ. Router có thật và đã nối, ở dạng opt-in: `backend/app/simulation/geometry_compiler/routing.py::quyet_dinh_dinh_tuyen` trả `DISABLED` · `USE_COMPILER` · `FALLBACK_TO_LLM` · `REFUSE`; `backend/app/ai/pipeline.py` gọi nó ngay sau analyze, và compiler chỉ chạy khi `GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST` (mặc định `LLM_ONLY` ⇒ `DISABLED`, không chạm dòng nào của compiler). Test qua `run_pipeline`: `backend/tests/geometry/test_prism_production_route.py` (`…deterministic_compiler_success`, `test_default_mode_bypasses_compiler`). Chưa có lượt live nào chạy ở chế độ này. STATUS để nguyên — chấm lại là việc của wave di chuyển.

### GATE-12: Fallback Mechanism
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Chưa có cơ chế chuyển giao lỗi sang LLM synthesis fallback.
- **BLOCKER:** Cần định nghĩa rõ các mã lỗi compiler có thể chuyển tiếp (recoverable) và không thể chuyển tiếp (fatal).
- **NEXT_TEST:** Test kịch bản cố tình đưa bài toán ngoài diện hỗ trợ để kiểm tra fallback suôn sẻ.
- **AUDIT (2026-10-05, `cuboid-final-review`):** evidence trên đã cũ. Quyết định `FALLBACK_TO_LLM` có thật (`UNSUPPORTED` ⇒ trả về cho caller, compiler không tự gọi provider; `INVALID` ⇒ `REFUSE`, không lùi về LLM), test đơn vị `backend/tests/geometry/test_geometry_primitive_compiler.py::test_AD_unsupported_tra_fallback_cho_caller_chu_khong_tu_gui`; trong `backend/app/ai/pipeline.py` mọi quyết định khác `USE_COMPILER`/`REFUSE` đi tiếp vào `stage_semantic_program`. Chưa thấy test nào đi trọn nhánh lùi qua `run_pipeline` — NEXT_TEST trên vẫn còn nguyên. STATUS để nguyên — chấm lại là việc của wave di chuyển.

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
- **STATUS:** PRODUCTION_READY cho `LLM_ONLY`; cách ly theo tuyến có từ run `hybrid-pre-main-hardening` (2026-10-18).
- **EVIDENCE:** giá trị hiện hành đọc ở nguồn (`grep -n 'CACHE_VERSION = ' backend/app/main.py`) và bảng danh tính `docs/CURRENT_STATE.md`, không chép vào đây; sync-lock `backend/tests/test_api.py` + `backend/tests/semantic_program/test_evaluation_candidate.py`. Cách ly theo tuyến: `backend/app/main.py::_policy_identity` + `backend/app/ai/pipeline.py::RoutePolicy`, khoá bởi `backend/tests/test_route_aware_cache.py`.
- **BLOCKER:** Không có cho `LLM_ONLY`.
- **NEXT_TEST:** Duy trì kiểm chứng tự động trước mọi commit.
- **AUDIT (2026-10-18, `hybrid-pre-main-hardening`):** evidence cũ ghi `CACHE_VERSION = 99` và "103 files" — số của thời điểm viết, không phải trạng thái hiện hành. Và chính sách cũ MÙ TUYẾN: khoá cache là băm đề, lookup chỉ so `CACHE_VERSION`, nên bật `GEOMETRY_COMPILER_MODE` phục vụ envelope `LLM_ONLY` cũ và rollback phục vụ envelope compiler. Nay một ảnh chụp tuyến mỗi lượt; mặc định giữ identity = `CACHE_VERSION` (không bump), chế độ khác mang hậu tố băm chế độ + phiên bản các tầng.

---

## 2. Route D (Hybrid: text → typed facts → planner → geometry functions) — checklist RIÊNG

20 cổng ở §1 viết cho tuyến C (compiler tất định trên `RequestContract`). Tuyến D là đường khác (`backend/app/ai/fact_extraction.py` → `function_route.py` → `simulation/geometry_functions/`), nên cổng §1 không thay được các cổng dưới đây và ngược lại. Đổi bất cứ gì của tuyến D khỏi `NO-GO` cần đủ các cổng D-*; trạng thái đọc từ bằng chứng nêu ở từng cổng, không chép số sống vào đây.

### D-01: Đường mặc định không chạm tuyến D
- **STATUS:** PROVED trên đường mặc định ĐÃ CHẠY (một fixture, trọn tới envelope `ok`); phần mã probe không chạy chỉ có danh sách cấm cơ chế nạp động đã biết + bao đóng tĩnh — `backend/tests/geometry/test_structured_geometry_relations.py::test_Y_*`: danh sách cấm (không chống được mọi cách viết — review độc lập tìm 11 cách lọt); bao đóng import tĩnh chỉ với compiler qua cổng `routing`; module nạp thật khi chạy `run_pipeline` ở `LLM_ONLY` (subprocess sạch, chặn mạng) ⊆ bao đóng tĩnh, tuyến D không nạp; tiêm lỗi 8 cách lách + import cắt chuỗi ở đầu đường và trong đuôi tất định.
- **BLOCKER:** —
- **NEXT_TEST:** khi nối tuyến D, cổng nối phải được KHAI (như `_CONG_COMPILER`), không lách guard.

### D-02: Cache identity theo tuyến
- **STATUS:** PARTIAL — `RoutePolicy` có chế độ preview tuyến D (run `hybrid-route-d-preview-wiring`); `fingerprint()` gồm Registry/Planner/Engine, surface trích xuất, adapter/envelope; preview KHÔNG có cache (`_policy_identity` từ chối policy preview), nên chưa có cache tuyến D nào để cách ly.
- **BLOCKER:** chỉ khi tuyến D được phục vụ qua `/api/analyze` (chưa được duyệt) mới cần cache tuyến D.
- **NEXT_TEST:** khi ấy: bộ test hai chiều của `test_route_aware_cache.py` cho chế độ tuyến D.

### D-03: Cấu hình theo lượt, không theo biến toàn cục
- **STATUS:** PROVED — `RoutePolicy` chụp một lần ở biên API; `run_ai_fact_route(contract=…)` chốt hợp đồng một lần mỗi lượt (`test_response_contract_is_one_snapshot_per_call`: trước đó đổi biến toàn cục giữa request và cổng kiểm làm một phản hồi xin theo v3 được phục vụ mà không qua cổng v3).
- **BLOCKER:** —
- **NEXT_TEST:** adapter nối tuyến D nhận hợp đồng từ `RoutePolicy`, không đọc `RESPONSE_CONTRACT`.

### D-04: Hợp đồng trích xuất
- **STATUS:** flat = hợp đồng sản phẩm; v3 = NO-GO.
- **BLOCKER:** v3 không diễn đạt được diện tích / góc tại điểm không tên (flat phục vụ được — thoái lui năng lực); 16/24 gold LOCKED lệch v3 vì cách viết gold (`solid` trên đoạn, ghi chú `reason`), không phải đo hành vi mô hình; held-out LOCKED đã tiếp xúc ⇒ không dùng để chỉnh prompt/schema.
- **NEXT_TEST:** bộ held-out MỚI, tiền đăng ký, trước mọi đổi bề mặt.

### D-05: Đúng toán
- **STATUS:** PROVED trên corpus hiện có — `test_174_historical_answers_regression_and_independent_source_expectations`: hồi quy (status, mã, bình phương đáp số) với baseline đóng băng TÁCH khỏi đối chiếu độc lập với kỳ vọng của corpus nguồn; khoảng trống năng lực khoá trong `CAPABILITY_GAPS_174`. Oracle step-math là kiểm tự nhất quán của cảnh, không phải đối chiếu với đề.
- **BLOCKER:** —
- **NEXT_TEST:** mọi họ mới thêm kỳ vọng độc lập (oracle Fraction viết trước) vào corpus nguồn.

### D-06: Fail-closed với dữ kiện suy biến
- **STATUS:** PROVED — độ dài 0 ⇒ `NON_POSITIVE_LENGTH` (tuyến A và B); độ dài âm không qua văn phạm; `Metric` từ chối ma trận không đối xứng / không xác định dương; engine đổi thành từ chối có mã.
- **BLOCKER:** —
- **NEXT_TEST:** —

### D-07: Adapter envelope
- **STATUS:** PROVED cho preview (`backend/app/ai/hybrid_preview.py::adapt_result`, `hybrid-route-d-preview/1`): envelope ngữ nghĩa đã thẩm định + `route_d` (Geometry IR, đáp số chính xác, provenance, trace, goal checks với `proof_status=UNVERIFIABLE` / `can_present_as_proven=false`, `length_unit`); từ chối giữ mã máy, lời người học tiếng Việt. Khoá: `backend/tests/test_hybrid_preview_api.py`.
- **BLOCKER:** frontend chưa đọc `route_d` (`frontend-handoff.md` của `hybrid-pre-main-hardening` F3, F4); đây là biểu diễn preview, chưa phải envelope sản phẩm của `/api/analyze`.
- **NEXT_TEST:** khi UI đọc nó: goal kiểm trên một cấu hình không bao giờ hiển thị là "đã chứng minh".
- **UPDATE (run `hybrid-preview-contract-hardening`):**
  - Lời từ chối mang `failure_category` + `refusal_cause` theo từ vựng hiện có (`classify_refusal`). Lỗi toàn vẹn, nguồn
    chưa xác minh hay thiếu chứng chỉ không còn bị gọi là `capability_gap`. Khoá quét nguồn: mã từ chối mới phải được
    xếp nhóm.
  - Lớp chặn văn bản chứng minh chuẩn hoá NFKC và gộp mọi dấu gạch / dấu trừ (kể cả U+2212).
  - Hợp đồng dữ liệu cho frontend: `docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md`. Bộ 41 fixture adapter `/2`
    xuất từ chính endpoint (`fixtures-adapter-2/`, khoá ở `test_hybrid_preview_fixtures.py`).

### D-08: Nối API sau cờ
- **STATUS:** PROVED cho preview — `POST /api/preview/hybrid`: cờ env + token server ≥ 32 ký tự + header + peer loopback, request có header `Origin` (trình duyệt) bị từ chối; TẮT ⇒ 404 trước mọi import tuyến D, và `/api/health` không nạp tuyến D; cổng trả lời trước khi đọc body; chỉ dữ liệu fixture offline (không transport, kể cả `ALLOW_LIVE_AI=1` có khoá); không cache; ngoài OpenAPI; `LLM_ONLY` của `/api/analyze` khớp băm byte với baseline trước khi nối.
- **BLOCKER:** phục vụ tuyến D qua `/api/analyze` hay qua provider thật chưa được duyệt.
- **NEXT_TEST:** —

### D-09: Quan sát được
- **STATUS:** PROVED — `GET /api/diagnostics/runtime` mang `route_policy` và `hybrid_route_d_preview` (phiên bản, surface, fingerprint, trạng thái bật; không lộ token).
- **BLOCKER:** —
- **NEXT_TEST:** —

### D-10: Trình bày chỉ từ chứng nhận
- **STATUS:** OPEN — ký hiệu góc vuông theo tên đoạn; `maTranKhung` không tự vệ (`frontend-handoff.md` F1, F2); `length_unit`, quan sát goal và `verification_gap` chưa được trình bày (F3, F4, F5 — tiêu chí ở `docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md` §9).
- **BLOCKER:** nhánh Scene3D đang sở hữu renderer.
- **NEXT_TEST:** theo tiêu chí nghiệm thu trong `frontend-handoff.md`.

### D-11: Đo live có ghép cặp với `LLM_ONLY`
- **STATUS:** NOT_STARTED — cần owner GO, ngân sách + luật dừng tiền đăng ký, `MEASUREMENT_CLASS` · `HELD_OUT_CLAIM` · `EVALUATOR_INDEPENDENCE`.
- **BLOCKER:** D-04 (held-out mới), D-08.
- **NEXT_TEST:** —

### D-12: Rollback
- **STATUS:** PARTIAL — tắt cờ là đủ về hành vi; preview không có cache nên không có gì để phục vụ chéo (D-02); một lượt đang chạy giữ ảnh chụp của nó.
- **BLOCKER:** D-02 khi tuyến D có cache.
- **NEXT_TEST:** bật → ghi cache → tắt ⇒ MISS; tắt → bật ⇒ MISS.

### D-13: Quyết định bật
- **STATUS:** NO-GO — `HYBRID_PRODUCT_ENABLEMENT = NO-GO` cho tới khi D-01…D-12 đạt và owner quyết.

### GATE-20: User & Pedagogical Evaluation
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Chưa thực hiện khảo sát hoặc đo lường tác động sư phạm trên người học thật.
- **BLOCKER:** Cần chuẩn bị kịch bản thực nghiệm sư phạm và bảng câu hỏi khảo sát chuẩn SUS/TAM.
- **NEXT_TEST:** Thiết kế đề cương thử nghiệm đánh giá hiệu quả học tập với nhóm học sinh đối chứng.
