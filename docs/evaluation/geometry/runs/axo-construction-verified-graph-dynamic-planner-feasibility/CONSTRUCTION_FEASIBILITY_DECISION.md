# CONSTRUCTION FEASIBILITY DECISION (`AXO CONSTRUCTION /1`)

- **Run ID:** `axo-construction-verified-graph-dynamic-planner-feasibility`
- **Verified Base HEAD:** `498f354608c45ce98ba4f75a0222afbe56139ce2` (`feat/local-first-geometry-understanding`)
- **Product Freeze Baseline:** `6310113f2202bc3a4919406b26fad08cb09b38c9` / `9a9352d586caa360f82052ba1b76fe9b4227f26c` (`123` files, `measured_system_sha256 = 113a6a7cf6bbc15ac23119150b805437e785d2b0714b26c2157d147514c2ef67`, `CACHE_VERSION = 145`)
- **Feasibility Verdict:** **`FEASIBLE_IN_ISOLATED_PROTOTYPE_NEEDS_INTEGRATION_WAVE`**
- **Prototype Status:** `RESEARCH_PROTOTYPE_NON_PRODUCTION` (`HYBRID_ROUTE_MODE = "live"` default preserved; `ALLOW_LIVE_AI = 0`, `external_ai_calls = 0`)

---

## 1. Bảng kết luận các cổng kiểm chứng (`Gate E0`–`E9`)

| Cổng | Nội dung | Kết luận | Bằng chứng chính xác |
| --- | --- | --- | --- |
| **Gate E0** | Kiểm toán kiến trúc hiện hành (`Planner /26`, `Registry /33`, `Exact Kernel /24`, `Scene3D`) | **`PASS`** | [EXISTING_CONSTRUCTION_ARCHITECTURE_AUDIT.md](EXISTING_CONSTRUCTION_ARCHITECTURE_AUDIT.md) + [CONSTRUCTION_CAPABILITY_INVENTORY.json](CONSTRUCTION_CAPABILITY_INVENTORY.json) (`64` hàm: `24` fact, `23` ask, `16` construct, `1` escape; `15/64` có `PlanningContract`; `ask_distance_point_plane` `has_auxiliary_foot_point = false`) |
| **Gate E1** | Thiết kế tách 2 tầng đồ thị (`verified-construction-graph/1` + `presentation-step-graph/1`) | **`PASS`** | [VERIFIED_CONSTRUCTION_GRAPH_DESIGN.md](VERIFIED_CONSTRUCTION_GRAPH_DESIGN.md) (`16`-field `ConstructionNode`, tách `GIVEN_OBJECT`/`DERIVED_OBJECT`/`AUXILIARY_CONSTRUCTION`, `canonical_geom_key`, `validate_construction_graph`) |
| **Gate E2** | Thư viện toán tử dựng hình nguyên tử (`construction-operator/1`) | **`PASS`** | [CONSTRUCTION_OPERATOR_INVENTORY.json](CONSTRUCTION_OPERATOR_INVENTORY.json) (`23` toán tử dựng & định lý suy diễn, tách biệt `evaluate_goal_if_witnessed`) |
| **Gate E3** | Dynamic Construction Planner tìm kiếm có giới hạn (`dynamic-construction-planner/1`) | **`PASS`** | [DYNAMIC_PLANNER_SEARCH_DESIGN.md](DYNAMIC_PLANNER_SEARCH_DESIGN.md) (Best-first dependency-aware search, premise-only `build_initial_frame`, canonical state dedup, multi-plan collection & ranking) |
| **Gate E4** | Kiểm chứng chính xác độc lập `L0`–`L4` | **`PASS`** | [CONSTRUCTION_EXACT_VERIFICATION_REPORT.md](CONSTRUCTION_EXACT_VERIFICATION_REPORT.md) (`33/33` ca dương đạt `L0`–`L4` + khớp oracle `axo-math-evaluator/2`) |
| **Gate E5** | Kiểm soát suy biến, mâu thuẫn & từ chối fail-closed (§13) | **`PASS`** | `7/7` ca âm/suy biến/bất khả thi bị từ chối sạch (kể cả `D02` trùng điểm `AA` mà `Baseline A` trả nhầm `0a`) |
| **Gate E6** | Cầu nối tương thích `Scene3D` (`construction-scene3d-bridge/1`) | **`PASS_ARTIFACT_ONLY`** | [SCENE3D_COMPATIBILITY_REPORT.md](SCENE3D_COMPATIBILITY_REPORT.md) (`33/33` ca `Scene3D` có `0` lỗi `validate_construction_continuity`, đa phương án trên `C01`; `frontend/` là `BLOCKED_OWNERSHIP` dưới `axo-geometry-library`) |
| **Gate E7** | Giao diện chuẩn bị chỉ đọc cho Model 2 (`model2-action-interface/1`) | **`PASS`** | [MODEL2_INTERFACE_READINESS.md](MODEL2_INTERFACE_READINESS.md) (`0` phụ thuộc Needle 3 runtime, `5/5` ranh giới bảo mật fail-closed) |
| **Gate E8** | Thực nghiệm 40 ca Gold Typed Facts + Novelty Audit (`Groups A–E`) | **`PASS`** | [GOLD_CONSTRUCTION_BENCHMARK_RESULTS.json](GOLD_CONSTRUCTION_BENCHMARK_RESULTS.json), [DYNAMIC_COMPOSITION_EVALUATION.json](DYNAMIC_COMPOSITION_EVALUATION.json), [CONSTRUCTION_PERFORMANCE.json](CONSTRUCTION_PERFORMANCE.json) (`Candidate B = 40/40`, `28 CASE_B_DYNAMIC_COMPOSITION`, `5/5` đa phương án) |
| **Gate E9** | Hồi quy, bất biến an toàn & cổng quản trị | **`PASS`** | [CONSTRUCTION_REGRESSION_REPORT.md](CONSTRUCTION_REGRESSION_REPORT.md) (`0` sửa đổi `backend/app/**`, `frontend/**`, `/5`–`/8`; `76` pytest mục tiêu PASS; full backend pytest & `check_publication_safety` sạch) |

---

## 2. Đối chiếu thực chứng `Baseline A` vs `Candidate B` (40 ca Gold, seed=0)

| Chỉ số | `Baseline A` (`Planner /26 -> Engine /24 -> Adapter /4`) | `Candidate B` (`dynamic-construction-planner/1`) |
| --- | --- | --- |
| **Tổng đạt chuẩn (toán / từ chối)** | `32/40` (`26/33` dương phục vụ, `6/7` âm từ chối) | **`40/40`** (`33/33` dương `L0`–`L4` + oracle, `7/7` âm từ chối) |
| **Ca dương có chứng nhân phụ trong `Scene3D`** | **`0/33`** (`ask_distance_point_plane`, … không dựng điểm chiếu `H` vào `Scene3D`) | **`33/33`** (bắt buộc có `AUXILIARY_CONSTRUCTION` & chứng chỉ `L2`) |
| **Khả năng đa phương án (`Group_E`, `5` ca)** | `0/5` (gộp về 1 chuỗi duy nhất) | **`5/5`** (`>= 2` phương án khác biệt bản chất, đều `L0`–`L4 PASS`) |
| **Chuỗi dài 19 bước (`B09`)** | `REFUSED` (`IR_MEMORY_BUDGET_EXCEEDED` > `32` decls) | **`GOAL_VERIFIED`** (`26.2 ms`, `31` đồ thị / ngân sách tách biệt) |
| **Chia đoạn theo tỉ số (`B01`, `B06`)** | `REFUSED` (`UNDERDETERMINED_POINT`) | **`GOAL_VERIFIED`** (`a√21/2`, `a√10/10`) |
| **Đoạn suy biến trùng điểm (`D02` — `AA`)** | **`SERVED 0a`** (bỏ lọt điểm trùng ở metric query) | **`REFUSED DEGENERATE_COINCIDENT_POINTS`** |
| **Độ trễ trung bình / lớn nhất** | `avg = 105.534 ms` | `avg_search_ms = 26.096 ms` (`max = 155.941 ms`), `avg_verify = 0.431 ms`, `max_peak_mem = 335.87 KiB`, `timeout_rate = 0.0` |

*Lưu ý minh bạch:* `4` ca từ chối của `Baseline A` (`A10`, `B02`, `B07`, `C08`) bắt nguồn từ kiểm tra `SOURCE_OBJECT_MISMATCH` trên câu trích dẫn tổng hợp trong ngữ cảnh câu đề thử nghiệm; chúng **không** được thổi phồng thành khuyết tật toán học của Kernel `/24`, mà được tách rạch ròi với các giới hạn kiến trúc thực sự (`B01`, `B06`, `B09`, `D02`, `0/33` witness, `49/64` hàm thiếu `PlanningContract`).

---

## 3. Phân định năng lực (`Case A` / `Case B` / `Case C`) & Giới hạn

- **Case A (`5` ca):** Tương đương `Baseline A` trên cấu trúc tường minh trực tiếp (`A01`, `A05`, `A06`, `A08`, `A09`), nhưng nâng chuẩn từ truy vấn số vô hướng thành `ConstructionProofGraph` kèm `L0`–`L4` + `Scene3D`.
- **Case B (`28` ca):** **Tổ hợp động mới được chứng minh** gồm dựng hạ đường cao 2 bước qua chân đáy (`C01`, `E01`–`E05`), khoảng cách hai đường chéo nhau bằng đoạn vuông góc chung vs mặt phẳng song song (`C02`, `C03`, `E03`), góc nhị diện bằng tia vuông góc chung từ giao tuyến vs mặt phẳng vuông góc (`C04`, `E05`), thiết diện song song (`C08`, `B10`), phản xạ/trọng tâm/chia tỉ số đa bước (`B01`–`B09`), và chuỗi 19 bước (`B09`).
- **Case C (`1` ca):** Bài toán đường cong / tiếp xúc đa thức bậc cao (`D06`: hình nón ngoại tiếp) bị từ chối fail-closed `UNSUPPORTED_OPERATOR` do Kernel hiện hành chỉ đóng trong đại số hữu tỉ $\mathbb{Q}^3$ + căn bậc hai đơn.
- **Tích hợp UI (`Gate E6`):** Đã chứng minh đầy đủ gói JSON `Scene3D` nhiều phương án đạt `0` lỗi continuity từ backend; việc hiển thị bộ chọn `Plan #1 / Plan #2` và badge `AUXILIARY_CONSTRUCTION` trên `Scene3DExplorer.tsx` thuộc `BLOCKED_OWNERSHIP` (worktree `axo-geometry-library`).

---

## 4. Điều kiện cho đợt tích hợp tiếp theo (Integration Wave)

1. Được chủ sở hữu `backend/app/simulation/**` và `frontend/` (`axo-geometry-library`) phê duyệt bằng chiến dịch riêng để triển khai [CONSTRUCTION_OWNER_HANDOFF.md](CONSTRUCTION_OWNER_HANDOFF.md).
2. Tích hợp từng phần: (a) vá `distinct_points` cho metric query (`D02`), (b) buộc hoặc mở tùy chọn dựng witness trên `ask_distance_*` / `ask_angle_*`, (c) bổ sung `PlanningContract` hoặc nối `construction-operator/1` vào tầng lập kế hoạch, và (d) hỗ trợ chuyển đổi nhiều `PresentationStepGraph` trên `Scene3DExplorer.tsx`.
3. Giữ nguyên nguyên tắc kiến trúc: AI (SLM / Gemini) chỉ trích xuất hoặc chọn phương án diễn giải trên `PresentationStepGraph` đã khóa bằng chứng; mọi khẳng định tọa độ và công thức phải đi qua `Exact Kernel /24` và `construction-exact-verifier/1`.
