# MIGRATION_CHECKLIST.md — Cổng Chuyển Đổi Kiến Trúc Hybrid `/4` & Hồ Sơ Lịch Sử Compiler-First

> **Cập nhật trạng thái hiện hành (2026-11-04 — `FINAL_HYBRID_ARCHITECTURE_CUTOVER`):**
> - Tuyến mặc định của `POST /api/analyze` trên `main` đã chuyển sang **Hybrid `/4`** (`HYBRID_ROUTE_MODE = live`; `staging-replay` cho dev/test; `CACHE_VERSION = 132` / `ROUTE_D_CACHE_POLICY = 132:route-d`; `typed-fact-next/2` → `Source Gate` → `geometry-fact-planner/26` → `geometry-functions/33` → `geometry-function-engine/24` → `hybrid-simulation-adapter/4`).
> - Đường thực thi `LLM_ONLY` (`pipeline.py`), `Adapter /3` (`adapter3_simulation.py`) và `Compiler C` (`geometry_compiler/`) đã gỡ bỏ (`HYBRID_DEFAULT_CUTOVER_COMPLETE = YES`, `LEGACY_EXECUTION_RETIRED = YES`, `LEGACY_FULLY_RETIRED = NO` do `semantic_program/route.py` giữ `COMPATIBILITY_REQUIRED`).
> - **Mục 1 (`GATE-01..GATE-20`)** dưới đây được giữ nguyên làm hồ sơ lịch sử của thế hệ `Compiler C` (trừ các cổng nghiên cứu dùng chung `GATE-15` và `GATE-20` vẫn mở). **Mục 2 (`D-01..D-13`)** là bảng kiểm soát chính thức của kiến trúc **Hybrid `/4`**.
> - **Nguyên tắc trung thực bằng chứng:** Quyết định cutover sản phẩm của Owner **không** thay thế kiểm chứng nghiên cứu độc lập — `INDEPENDENT_H1_VALIDATION = NOT_MEASURED`, `NEW_LIVE_SMOKE_NOT_MEASURED`, `PRODUCTION_DEPLOYMENT_VERIFIED = NO` (tuyệt đối không mô tả C26 hay Full T3 offline thành kiểm định độc lập trên `H-1`).

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
- **CUTOVER (2026-11-04):** `SUPERSEDED_BY_HYBRID_CUTOVER` — cả `geometry_compiler/routing.py` lẫn `pipeline.py` đã bị xoá; `POST /api/analyze` định tuyến trực tiếp qua Hybrid `/4` (`main.py::_analyze_hybrid_route`, `route_policy.py`).

### GATE-12: Fallback Mechanism
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Chưa có cơ chế chuyển giao lỗi sang LLM synthesis fallback.
- **BLOCKER:** Cần định nghĩa rõ các mã lỗi compiler có thể chuyển tiếp (recoverable) và không thể chuyển tiếp (fatal).
- **NEXT_TEST:** Test kịch bản cố tình đưa bài toán ngoài diện hỗ trợ để kiểm tra fallback suôn sẻ.
- **AUDIT (2026-10-05, `cuboid-final-review`):** evidence trên đã cũ. Quyết định `FALLBACK_TO_LLM` có thật (`UNSUPPORTED` ⇒ trả về cho caller, compiler không tự gọi provider; `INVALID` ⇒ `REFUSE`, không lùi về LLM), test đơn vị `backend/tests/geometry/test_geometry_primitive_compiler.py::test_AD_unsupported_tra_fallback_cho_caller_chu_khong_tu_gui`; trong `backend/app/ai/pipeline.py` mọi quyết định khác `USE_COMPILER`/`REFUSE` đi tiếp vào `stage_semantic_program`. Chưa thấy test nào đi trọn nhánh lùi qua `run_pipeline` — NEXT_TEST trên vẫn còn nguyên. STATUS để nguyên — chấm lại là việc của wave di chuyển.
- **CUTOVER (2026-11-04):** `RETIRED_BY_DESIGN` — Hybrid `/4` cấm tuyệt đối fallback sang sinh chương trình theo từng đề (`LLM_ONLY` đã xoá); mọi ca ngoài phạm vi hoặc mâu thuẫn đều từ chối fail-closed có cấu trúc.

### GATE-13: Canary Deployment
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Chưa có hạ tầng phân luồng phần trăm request thực nghiệm.
- **BLOCKER:** Cần cấu hình reverse proxy hoặc feature flag có trọng số.
- **NEXT_TEST:** Test phân bổ tải 10% compiler-first và 90% default.

### GATE-14: Rollback Mechanism
- **STATUS:** NOT_STARTED (cho circuit breaker tự động); rollback kiến trúc sau cutover xác định qua Git/deployment tag.
- **EVIDENCE:** Quy trình rollback kiến trúc dựa trên bản phát hành trước cutover (`pre-hybrid-cutover-f986e897`) kèm công tắc dừng khẩn cấp `ALLOW_LIVE_AI=0` (`503 LIVE_AI_DISABLED`).
- **BLOCKER:** Chưa có cơ chế ngắt mạch (circuit breaker) tự động ở tầng hạ tầng và `PRODUCTION_DEPLOYMENT_VERIFIED = NO`.
- **NEXT_TEST:** Kiểm thử quy trình rollback deployment và circuit breaker khi triển khai môi trường thật.

### GATE-15: Holdout Benchmark
- **STATUS:** NOT_STARTED (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`)
- **EVIDENCE:** Hạ tầng đánh giá độc lập `H-1` đã sẵn sàng nhưng bộ 60 đề tiếng Việt độc lập (`H-1`) chưa được biên soạn/duyệt và chưa chạy live (lượt đo C26 70-case và Full T3 là kiểm chứng hồi quy phát triển/tích hợp, **không** phải kiểm định độc lập `H-1`).
- **BLOCKER:** Chưa tiếp nhận và niêm phong bộ đề kiểm thử độc lập `H-1` kèm ngân sách live được duyệt.
- **NEXT_TEST:** Tiếp nhận bộ 60 đề độc lập `H-1`, đóng băng oracle và chạy đánh giá live có trần ngân sách.

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
- **CUTOVER (2026-11-04):** `CACHE_VERSION = "132"`, `ROUTE_D_CACHE_POLICY = "132:route-d"`, `RoutePolicy.default_route_mode = "HYBRID"` (`backend/app/ai/route_policy.py`, `backend/app/ai/hybrid_offline.py::prepare_live_hybrid` + `backend/app/main.py::_cache_lookup`); khoá cache băm toàn bộ surface phiên bản (`typed-fact-next/2`, `planner/26`, `registry/33`, `engine/24`, `adapter/4`), model/prompt fingerprint và nguyên văn đề bài; không lưu kết quả từ chối hay lỗi hạ tầng (`test_hybrid_cutover_verification.py`).

---

## 2. Route D (Hybrid: text → typed facts → planner → geometry functions) — checklist RIÊNG

20 cổng ở §1 viết cho tuyến C (compiler tất định trên `RequestContract`). Tuyến D là đường khác (`backend/app/ai/fact_extraction.py` → `function_route.py` → `simulation/geometry_functions/`), nên cổng §1 không thay được các cổng dưới đây và ngược lại. Đổi bất cứ gì của tuyến D khỏi `NO-GO` cần đủ các cổng D-*; trạng thái đọc từ bằng chứng nêu ở từng cổng, không chép số sống vào đây.

### D-01: Đường mặc định không chạm tuyến D (Lịch sử trước Cutover) → Nay Tuyến D `/4` Là Mặc Định Duy Nhất
- **STATUS:** HISTORICAL_SUPERSEDED (2026-11-04) — trước cutover, cổng này cô lập tuyến D khỏi `LLM_ONLY`; từ cutover `FINAL_HYBRID_ARCHITECTURE_CUTOVER`, Hybrid `/4` trở thành tuyến duy nhất của `POST /api/analyze`, còn `LLM_ONLY` (`pipeline.py`), `Adapter /3` và `Compiler C` đã xoá và bị khoá chống tái xuất hiện bởi `backend/tests/geometry/test_hybrid_cutover_verification.py`.
- **HISTORICAL EVIDENCE (pre-cutover):** PROVED trên đường mặc định cũ (`test_structured_geometry_relations.py::test_Y_*` thời `LLM_ONLY`).
- **BLOCKER:** —
- **NEXT_TEST:** Duy trì guard chống import/khôi phục legacy trong `test_hybrid_cutover_verification.py`.

### D-02: Cache identity theo tuyến
- **STATUS:** PROVED offline (hybrid-master, `backend/tests/test_hybrid_route_d_cache_and_rollback.py`) cho tuyến D trên `/api/analyze` opt-in (`HYBRID_V2_LOCAL=offline-replay` + loopback):
  - Khoá `prepare_local_replay(...).cache_key` gồm tuyến, surface Registry/Planner/Engine/hợp đồng/adapter/envelope, extraction đã ghi, và đề NGUYÊN VĂN (không chuẩn hoá như khoá `LLM_ONLY`).
  - Nhãn `ROUTE_D_CACHE_POLICY` làm phép cách ly hai chiều: hàng tuyến D không đọc được bằng identity `LLM_ONLY`, và ngược lại (`test_hybrid_v2_local_analyze.py`).
  - Chỉ lưu SERVED. MISS khi extraction ghi lại khác hoặc surface khác. Hàng không phải phản hồi SERVED ⇒ MISS và bị thay. Xung đột ghi đồng thời không làm hỏng phản hồi.
  - Hai mutant bị bắt.
  - Preview `/api/preview/hybrid` vẫn không cache.
- **LUẬT BUMP (review kiến trúc M-2):** khoá tuyến D chỉ băm hằng phiên bản (`REGISTRY_VERSION`, `PLANNER_VERSION`, `ENGINE_VERSION`, hợp đồng, adapter, envelope), không băm mã. Vì vậy mọi sửa đổi đổi kết quả của kernel/engine/planner/adapter /4 **phải** bump hằng phiên bản tầng ấy (hoặc `CACHE_VERSION`) cùng commit, nếu không hàng SERVED cũ vẫn được phục vụ. Đây là cùng kỷ luật mà cache `LLM_ONLY` đang dựa vào.
- **CUTOVER (2026-11-04):** PROVED cho cả `live` và `staging-replay` trên `POST /api/analyze` (`CACHE_VERSION = 132`, `ROUTE_D_CACHE_POLICY = 132:route-d`, `hybrid_offline.py::prepare_live_hybrid` + `main.py::_cache_lookup` băm surface phiên bản + model/prompt/schema fingerprint + nguyên văn đề bài; khoá tại `test_hybrid_cutover_verification.py`).
- **BLOCKER:** —
- **NEXT_TEST:** Duy trì bump hằng phiên bản hoặc `CACHE_VERSION` khi đổi hành vi bất kỳ tầng nào trên Route D `/4`.

### D-03: Cấu hình theo lượt, không theo biến toàn cục
- **STATUS:** PROVED — `RoutePolicy` chụp một lần ở biên API; `run_ai_fact_route(contract=…)` chốt hợp đồng một lần mỗi lượt (`test_response_contract_is_one_snapshot_per_call`: trước đó đổi biến toàn cục giữa request và cổng kiểm làm một phản hồi xin theo v3 được phục vụ mà không qua cổng v3).
- **BLOCKER:** —
- **NEXT_TEST:** adapter nối tuyến D nhận hợp đồng từ `RoutePolicy`, không đọc `RESPONSE_CONTRACT`.

### D-04: Hợp đồng trích xuất
- **STATUS:** ACTIVE trên sản phẩm: **`TypedFactNext /2`** (`typed-fact-next/2` tại `typed_fact_next.py` + `typed_fact_next_extraction.py`, qua `bridge_v2` `typed-fact-next-bridge/2`; `RoutePolicy.response_contract = "flat"` giữ cho tương thích snapshot; hợp đồng `v3` cũ giữ `NO-GO`).
- **BLOCKER:** Kiểm chứng độc lập trên tập 60 đề mới `H-1` vẫn chưa thực hiện (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`).
- **NEXT_TEST:** Đánh giá trên bộ held-out độc lập `H-1` trước mọi mở rộng lớn về bề mặt trích xuất.

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
- **CUTOVER (2026-11-04):** Envelope sản phẩm chính thức trên `POST /api/analyze` là **Adapter `/4`** (`backend/app/ai/adapter4_route.py`, `hybrid-simulation-adapter/4`, schema `hybrid-route-d-simulation/4`, bước dựng tích lũy liên tục `construction_continuity.py`, làm rõ `route-d-clarification/1`); frontend tiêu thụ trực tiếp envelope này (`test_hybrid_cutover_verification.py`, `test_final_backend_product_completion.py`). Ghi chú bên dưới là lịch sử thời preview `/1`–`/2`.
- **NEXT_TEST:** khi UI đọc nó: goal kiểm trên một cấu hình không bao giờ hiển thị là "đã chứng minh".
- **UPDATE (run `hybrid-preview-contract-hardening`):**
  - Lời từ chối mang `failure_category` + `refusal_cause` theo từ vựng hiện có (`classify_refusal`). Lỗi toàn vẹn, nguồn
    chưa xác minh hay thiếu chứng chỉ không còn bị gọi là `capability_gap`. Khoá quét nguồn: mã từ chối mới phải được
    xếp nhóm.
  - Lớp chặn văn bản chứng minh chuẩn hoá NFKC và gộp mọi dấu gạch / dấu trừ (kể cả U+2212).
  - Hợp đồng dữ liệu cho frontend: `docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md`. Bộ 41 fixture adapter `/2`
    xuất từ chính endpoint (`fixtures-adapter-2/`, khoá ở `test_hybrid_preview_fixtures.py`).

### D-08: Nối API chính thức (`POST /api/analyze`) & Cổng Preview
- **STATUS:** PROVED & ACTIVE (2026-11-04) — `POST /api/analyze` nối trực tiếp vào **Hybrid `/4`** (`HYBRID_ROUTE_MODE=live` mặc định; `staging-replay` cho dev/test offline; `off` hoặc giá trị lạ trả HTTP `503 INVALID_HYBRID_ROUTE_MODE`; thiếu `GEMINI_API_KEY` ở `live` trả HTTP `503 MISSING_API_KEY`; `ALLOW_LIVE_AI=0` trả HTTP `503 LIVE_AI_DISABLED`). Endpoint `POST /api/preview/hybrid` vẫn giữ cơ chế khoá token loopback riêng cho fixture preview.
- **HISTORICAL NOTE (pre-cutover):** Trước 2026-11-04, cổng này chỉ bật cho `/api/preview/hybrid` khi `LLM_ONLY` còn tồn tại.
- **BLOCKER:** `NEW_LIVE_SMOKE_NOT_MEASURED` và `PRODUCTION_DEPLOYMENT_VERIFIED = NO`.
- **NEXT_TEST:** Live smoke có ngân sách và xác minh môi trường triển khai thật.

### D-09: Quan sát được
- **STATUS:** PROVED — `GET /api/diagnostics/runtime` mang `route_policy` và `hybrid_route_d_preview` (phiên bản, surface, fingerprint, trạng thái bật; không lộ token).
- **BLOCKER:** —
- **NEXT_TEST:** —

### D-10: Trình bày chỉ từ chứng nhận
- **STATUS:** OPEN — ký hiệu góc vuông theo tên đoạn; `maTranKhung` không tự vệ (`frontend-handoff.md` F1, F2); `length_unit`, quan sát goal và `verification_gap` chưa được trình bày (F3, F4, F5 — tiêu chí ở `docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md` §9).
- **BLOCKER:** nhánh Scene3D đang sở hữu renderer.
- **NEXT_TEST:** theo tiêu chí nghiệm thu trong `frontend-handoff.md`.

### D-11: Kiểm định live & Tập đề độc lập `H-1`
- **STATUS:** `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (các lượt đo live trên tập phát triển/tích hợp C21 và C26 70-case đã hoàn tất và lưu nguyên vẹn trong `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/`, nhưng đánh giá độc lập trên 60 đề mới `H-1` chưa thực hiện; thực thi `LLM_ONLY` trong repo sản phẩm đã gỡ từ cutover 2026-11-04).
- **BLOCKER:** Chưa có bộ 60 đề tiếng Việt độc lập `H-1` được biên soạn/phê duyệt và ngân sách live tương ứng.
- **NEXT_TEST:** Thực thi đánh giá độc lập trên `H-1` theo quy trình ngân sách có trần khi Owner phê duyệt.

### D-12: Rollback
- **STATUS:** UPDATED POST-CUTOVER (2026-11-04, `test_hybrid_cutover_verification.py`).
  - **Cơ chế hiện hành trên `main`:** Vì `LLM_ONLY` và cờ `HYBRID_V2_LOCAL` đã bị xoá hoàn toàn, **rollback kiến trúc** là rollback phiên bản Git/deployment về tag trước cutover `pre-hybrid-cutover-f986e897` (hoặc tạo commit `git revert` tiến tới); dừng khẩn cấp gọi Gemini live dùng `ALLOW_LIVE_AI=0` (trả HTTP `503 LIVE_AI_DISABLED`). Đặt `HYBRID_ROUTE_MODE=off` **không** quay về `LLM_ONLY` mà trả lỗi HTTP `503 INVALID_HYBRID_ROUTE_MODE`.
  - **Không có `SILENT_LEGACY_FALLBACK`:** Thiếu dữ kiện, mâu thuẫn, ngoài phạm vi, cần làm rõ, quá hạn và lỗi hạ tầng đều fail-closed có mã, không ghi cache.
  - *(Lịch sử trước cutover: bằng chứng offline `ROLLBACK_TO_LEGACY_MODE` qua cờ `HYBRID_V2_LOCAL` thuộc giai đoạn chuyển tiếp trước khi xoá `pipeline.py`.)*
- **BLOCKER:** `PRODUCTION_DEPLOYMENT_VERIFIED = NO`.
- **NEXT_TEST:** Kiểm chứng thao tác rollback phiên bản trên môi trường deployment thật.

### D-13: Quyết định bật
- **STATUS:** ACTIVE_BY_OWNER_CUTOVER_DIRECTIVE (2026-11-04, `ALGOSIM_HYBRID_CUTOVER_FINAL_REPORT.md`) — Owner đã quyết định chuyển tuyến sản phẩm mặc định `POST /api/analyze` sang Hybrid `/4` (`HYBRID_ROUTE_MODE = live`, `CACHE_VERSION = 132`, gỡ thực thi `LLM_ONLY` / Compiler C / Adapter `/3`; rollback sau cutover là rollback phiên bản triển khai về tag `pre-hybrid-cutover-f986e897` / `f986e897bd266d06d4a9c5fa78c05463b7b247bf`, không còn là đổi cờ môi trường `HYBRID_ROUTE_MODE=off`). Giữ nguyên sự thật nghiên cứu: `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (GATE-15 / D-11 chưa đo trên tập độc lập H-1) và `PRODUCTION_DEPLOYMENT_VERIFIED = NO`.

### GATE-20: User & Pedagogical Evaluation
- **STATUS:** NOT_STARTED
- **EVIDENCE:** Chưa thực hiện khảo sát hoặc đo lường tác động sư phạm trên người học thật.
- **BLOCKER:** Cần chuẩn bị kịch bản thực nghiệm sư phạm và bảng câu hỏi khảo sát chuẩn SUS/TAM.
- **NEXT_TEST:** Thiết kế đề cương thử nghiệm đánh giá hiệu quả học tập với nhóm học sinh đối chứng.
