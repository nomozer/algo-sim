# architecture/ — nguyên tắc và contract

> Hai loại file, đọc khác nhau: **contract đang hiệu lực** (sửa được, luôn đi kèm wave và test) và **tiền đăng ký /
> snapshot kiểm kê** (bất biến — đọc như bằng chứng tại thời điểm ghi). Không đặt bảng kết quả test ở đây; số đo thuộc
> thư mục run và [`../EVIDENCE_INDEX.md`](../EVIDENCE_INDEX.md). Hệ đang chạy: [`../ARCHITECTURE_MAP.md`](../ARCHITECTURE_MAP.md).

## Contract đang hiệu lực

| file | phạm vi |
|---|---|
| [`ASSUMPTION_CERTIFICATE_AMENDMENT.md`](ASSUMPTION_CERTIFICATE_AMENDMENT.md) | chứng chỉ giả định (W15), ràng buộc phép dựng với đề (W17 §15, W18 §16); mã sản phẩm trích đường dẫn này |
| [`OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`](OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md) | edge identity, visual owner, occlusion span, oracle độc lập |
| [`CUBOID_CUBE_CONTRACT_DECISION.md`](CUBOID_CUBE_CONTRACT_DECISION.md) | hình hộp chữ nhật / lập phương / lăng trụ đứng đáy vuông: trường topo, luật nhất quán, fail-closed (đưa về từ `legacy/` ở run `docs-cleanup`) |

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
