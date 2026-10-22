# architecture/ — nguyên tắc và contract

> Hai loại file, đọc khác nhau: **contract đang hiệu lực** (sửa được, luôn đi kèm wave và test) và **tiền đăng ký /
> snapshot kiểm kê** (bất biến — đọc như bằng chứng tại thời điểm ghi). Không đặt bảng kết quả test ở đây; số đo thuộc
> thư mục run và [`../EVIDENCE_INDEX.md`](../EVIDENCE_INDEX.md). Hệ đang chạy: [`../ARCHITECTURE_MAP.md`](../ARCHITECTURE_MAP.md).

## Contract đang hiệu lực

| file | phạm vi |
|---|---|
| [`ASSUMPTION_CERTIFICATE_AMENDMENT.md`](ASSUMPTION_CERTIFICATE_AMENDMENT.md) | chứng chỉ giả định (W15), ràng buộc phép dựng với đề (W17 §15, W18 §16); mã sản phẩm trích đường dẫn này |
| [`OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`](OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md) | edge identity, visual owner, occlusion span, oracle độc lập |
| [`HYBRID_B_TARGET_ARCHITECTURE_DECISION.md`](HYBRID_B_TARGET_ARCHITECTURE_DECISION.md) | **quyết định kiến trúc đích Hybrid (2026-10-11)**: AI trích xuất JSON Typed Facts → Semantic Grounding → Goal-Directed Construction Planner tất định tự phối hợp Geometry Functions → Compiler / Construction IR → Engine / Kernel → Scene3D; tuyến AI gọi hàm trực tiếp (A) là baseline đối chứng; `LLM_ONLY` vẫn là mặc định sản phẩm (`AS-IS`) |
| [`TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md`](TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md) | **quyết định nền tảng Text-to-Geometry Functions (2026-10-10)**: tách việc đọc đề khỏi quyết định hình học; `LLM_ONLY` là legacy (giữ làm mặc định sản phẩm, không thêm năng lực mới). Cơ chế chọn hàm ban đầu (AI gọi hàm trực tiếp) đã được kế nhiệm bởi kiến trúc **Hybrid** tại [`HYBRID_B_TARGET_ARCHITECTURE_DECISION.md`](HYBRID_B_TARGET_ARCHITECTURE_DECISION.md) (so sánh thực nghiệm tại [`runs/hybrid-compiler-selection/ARCHITECTURE_COMPARISON.md`](../evaluation/geometry/runs/hybrid-compiler-selection/ARCHITECTURE_COMPARISON.md)) |
| [`TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md`](TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md) | hợp đồng thư viện Geometry Functions (`geometry-functions/11`, 35 hàm), Planner tất định (`geometry-fact-planner/11`), Engine (`geometry-function-engine/9`), cổng nguồn 6 tầng, chuẩn hoá có tiền điều kiện, bố cục khung affine + Gram, độ dài ký hiệu `a`, và adapter |
| [`TWO_LINE_PLANE_SECTION_CONTRACT.md`](TWO_LINE_PLANE_SECTION_CONTRACT.md) | mặt phẳng xác định bởi hai đường thẳng cắt nhau / song song và thiết diện tương ứng trên kiến trúc Hybrid |
| [`GENERALIZED_GOAL_ENTRY_CONTRACT.md`](GENERALIZED_GOAL_ENTRY_CONTRACT.md) | cổng mục tiêu tổng quát hóa và phân rã đích dựng hình có kiểm chứng nguồn cho Planner tất định |
| [`GROUNDED_GOAL_COMPLETENESS_CONTRACT.md`](GROUNDED_GOAL_COMPLETENESS_CONTRACT.md) | hợp đồng bảo đảm tính đầy đủ và gắn kết nguồn của mệnh đề mục tiêu/câu hỏi trong tuyến Hybrid |
| [`HYBRID_ROUTE_D_PREVIEW.md`](HYBRID_ROUTE_D_PREVIEW.md) | hợp đồng đường preview thực nghiệm của kiến trúc Hybrid (`hybrid-preview-adapter/2`, schema `hybrid-route-d-preview/1`), cô lập khỏi tuyến mặc định `LLM_ONLY` |
| [`HYBRID_PREVIEW_FRONTEND_CONTRACT.md`](HYBRID_PREVIEW_FRONTEND_CONTRACT.md) | hợp đồng tích hợp và hiển thị dữ liệu preview Hybrid trên frontend (`Scene3DExplorer`) không phá vỡ thẩm quyền toán học của backend |
| [`GEOMETRY_CAPABILITY_EXPANSION_CONTRACT.md`](GEOMETRY_CAPABILITY_EXPANSION_CONTRACT.md) | hợp đồng mở rộng năng lực hình học theo đợt (wave) trên kiến trúc Hybrid |
| [`CUBOID_CUBE_CONTRACT_DECISION.md`](CUBOID_CUBE_CONTRACT_DECISION.md) | hình hộp chữ nhật / lập phương / lăng trụ đứng đáy vuông: trường topo, luật nhất quán, fail-closed (đưa về từ `legacy/` ở run `docs-cleanup`) |
| [`COMPOSITE_GEOMETRY_CONTRACT.md`](COMPOSITE_GEOMETRY_CONTRACT.md) | Wave 2C: hình chóp dẫn xuất và nhiều hình chóp có mặt chung trong cùng một hệ trục hữu tỉ + Gram (`composite-geometry`) |
| [`TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md) | TypedFactNext (`typed-fact-next/1`) & Adapter /3 (`hybrid-simulation-adapter/3`): hợp đồng biểu diễn dữ kiện hướng mô phỏng (đỉnh thiết diện không tên, khối dẫn xuất, định danh đỉnh có tiền tố khối `solid_id::label`) (`typedfact-next-adapter3-simulation`) |
| [`WAVE3A_CONTRACT_DECISION.md`](WAVE3A_CONTRACT_DECISION.md) | Wave 3A: tỉ số thể tích chính xác (`ask_volume_ratio`) và thể tích phần còn lại có chứng chỉ bao hàm/tách rời (`ask_residual_volume`) (`volume-reasoning`) |

## Tiền đăng ký và snapshot (bất biến)

| file | nội dung |
|---|---|
| [`GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`](GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md) | tiền đăng ký W13 → W14: dựng hình theo lớp, chính sách giả định, grounding nguồn |
| [`GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md`](GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md) + [`geometry_capability_matrix_v2.json`](geometry_capability_matrix_v2.json) | kiểm kê W13 tại `bf5a7907`: giả định tuyệt đối A–J, năng lực **theo tầng** của 17 nhóm hình — **không** phải năng lực sản phẩm |
| [`ARCHITECTURE_CAPABILITY_MATRIX.md`](ARCHITECTURE_CAPABILITY_MATRIX.md) + [`architecture_capability_matrix.json`](architecture_capability_matrix.json) | kiểm kê v1 (2026-09-25); v2 trích như bản bất biến |

## Contract nằm ở gốc `docs/`

Mã sản phẩm trích các đường dẫn này nên chúng giữ chỗ (sửa chú thích trong `backend/app` hay `frontend/src` sẽ đổi
candidate): [`../CORRECTNESS.md`](../CORRECTNESS.md), [`../DESIGN_BRIEF.md`](../DESIGN_BRIEF.md),
[`../CLASSROOM_AUTH_CONTRACT.md`](../CLASSROOM_AUTH_CONTRACT.md),
[`../OBLIGATION_BINDING_CONTRACT.md`](../OBLIGATION_BINDING_CONTRACT.md),
[`../CURVED_GEOMETRY_FOUNDATION_DESIGN.md`](../CURVED_GEOMETRY_FOUNDATION_DESIGN.md),
[`../GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE.md`](../GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE.md),
[`../CURVED_V3_RESEAL_PREFLIGHT.md`](../CURVED_V3_RESEAL_PREFLIGHT.md),
[`../REACT_ERROR_BOUNDARY_HARDENING.md`](../REACT_ERROR_BOUNDARY_HARDENING.md).

## Thẩm quyền ngoài thư mục này

- Năng lực sản phẩm: `backend/app/simulation/product_capability.py`.
- Đổi chế độ mặc định: [`../MIGRATION_CHECKLIST.md`](../MIGRATION_CHECKLIST.md) (20 cổng).
- Thiết kế gốc đã thực thi của route Semantic Program (2026-08-20): [`../legacy/architecture/`](../legacy/architecture/).
- Thiết kế mới do skill/agent sinh đặt ở đây khi nó là contract đang hiệu lực; kế hoạch triển khai nằm trong thư mục run
  của việc (`../evaluation/geometry/runs/<run>/plan.md`) — không mở thư mục tài liệu mới.
