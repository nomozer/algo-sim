# Quyết định kiến trúc: Text-to-Geometry Functions là kiến trúc đích

**Status:** accepted — 2026-10-10 (người dùng, theo ý tưởng của GVHD). Bất biến: bản gốc bên dưới giữ nguyên; quyết định
sau thay nó bằng một tệp mới và ghi `superseded by` ở đây.

> **Superseded in part by:** [`HYBRID_B_TARGET_ARCHITECTURE_DECISION.md`](HYBRID_B_TARGET_ARCHITECTURE_DECISION.md) (2026-10-11)
> và mở rộng tại [`TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md`](TYPEDFACT_NEXT_ADAPTER3_CONTRACT.md).
> - **Điểm giữ nguyên hiệu lực:** Nguyên lý cốt lõi tách việc đọc đề khỏi quyết định hình học (R0 chặt hơn, thư viện
>   `geometry_functions`, Engine tất định sở hữu khung affine + metric Gram hữu tỉ, kiểm chứng mọi dữ kiện và xuất
>   `Scene3D`); `LLM_ONLY` vẫn là tuyến sản phẩm mặc định hiện hành (`AS-IS: DEFAULT_MODE = LLM_ONLY`) và không nhận thêm
>   năng lực mô phỏng mới; `geometry_compiler/` (Primitive Compiler/FactGraph theo họ bài) giữ nguyên trạng thái opt-in,
>   không phải kiến trúc đích.
> - **Điểm đã được kế nhiệm trong kiến trúc mục tiêu (`TO-BE: Hybrid`):** Thay vì để AI trực tiếp chọn và ghép chuỗi lời
>   gọi hàm dựng hình (Baseline A — `function_calling.py` / `function_route.py`, nay chỉ giữ làm đường đối chứng thực
>   nghiệm), kiến trúc **Hybrid** giao cho AI chỉ trích xuất **JSON Typed Facts** (`TypedFact` / `TypedFactNext`), qua
>   **Semantic Grounding**, rồi **Goal-Directed Construction Planner** tất định (`planner.py`) tự chọn và phối hợp các
>   **Geometry Functions** → **Compiler / Construction IR** → **Engine / Kernel** → **Scene3D**.

AlgoSim chuyển hướng phát triển chính sang **Text-to-Geometry Functions**: AI đọc đề theo từng mệnh đề và chỉ **chọn và
tham số hoá** lời gọi trong một thư viện hàm dựng hình hữu hạn, có kiểu, mỗi lời gọi chép nguyên văn đoạn đề làm căn cứ;
engine tất định chuẩn hoá quan hệ (có tiền điều kiện), giải phụ thuộc, tự chọn bố cục chính xác (khung affine + metric
Gram hữu tỉ), kiểm lại mọi dữ kiện và xuất Scene3D. Ý gốc của GVHD: *"bóc tách các hình thành hàm cơ bản để vẽ … cho AI
đọc đề sử dụng các hàm có sẵn để vẽ hình chứ không để AI vẽ hết"*. Lý do: giảm phần việc giao cho mô hình về đúng
thứ mô hình làm được (đọc câu), giữ mọi quyết định hình học ở engine có kiểm chứng.

## Hệ quả (đã chốt)

- `LLM_ONLY` (mô hình viết cả Semantic Program) là **legacy**: giữ chạy làm mặc định sản phẩm và làm đường đối chứng,
  **không thêm năng lực mô phỏng mới** trên nó.
- Mọi năng lực dựng hình mới triển khai trên kiến trúc này (`backend/app/simulation/geometry_functions/`,
  `backend/app/ai/function_route.py`, `backend/app/ai/function_calling.py`); tái sử dụng kernel, interpreter, IR,
  Scene3D và bộ tạo câu lệnh IR (`semantic_program/ir_builders.py`) khi kiểm chứng được phù hợp.
- Chưa xoá legacy, chưa đổi mặc định cho tới khi đường AI thật được nghiệm thu (đo có ngân sách, xem
  `docs/evaluation/geometry/runs/ai-function-route/EXPERIMENT_PROTOCOL_V2.md`) **và** qua cổng đổi mặc định
  ([`../MIGRATION_CHECKLIST.md`](../MIGRATION_CHECKLIST.md)).
- DSL gọn, FactGraph, constrained decoding, compiler-in-the-loop là **ứng viên nghiên cứu**, không phải yêu cầu: chỉ
  thêm một tầng khi có phép đo riêng cho thấy cần.
- Ranh giới R0 chặt hơn: mô hình không phát toạ độ, không phát mã; ô số phải neo vào đoạn đề; quan hệ tương đương chỉ
  được chuẩn hoá khi ngữ cảnh hình học chứng minh.

## Phương án đã cân nhắc

- **Tiếp tục `LLM_ONLY`** — loại: pilot G05 thật (`feat/real-model-pilot-tooling`, 0/10 dương) cho thấy chi phí lớn
  nằm ở chỗ mô hình phải tự chọn toạ độ hữu tỉ và nhãn xuất xứ; số đó *không* dùng để chứng minh kiến trúc mới tốt hơn
  (chưa có đối chứng — Q1 của giao thức).
- **Compiler họ-bài** (`geometry_compiler/`) — không chọn làm đích: việc chọn phép dựng nằm trong mã theo từng họ, đầu
  vào là `RequestContract` do LLM sinh; giữ nguyên (opt-in), không mở rộng tiếp.
- **DSL riêng làm biểu diễn trung gian** — hoãn: lời gọi hàm có kiểu đã là biểu diễn trung gian; chưa có số đo token/độ
  chính xác cho thấy cần thêm tầng.

Hợp đồng đang hiệu lực: [`TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md`](TEXT_TO_GEOMETRY_FUNCTIONS_CONTRACT.md).
