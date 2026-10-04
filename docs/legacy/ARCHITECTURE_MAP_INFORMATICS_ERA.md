# ARCHITECTURE_MAP.md — phần đã tách, chép nguyên văn

> Tách khỏi [`ARCHITECTURE_MAP.md`](../ARCHITECTURE_MAP.md) ở run `cuboid-final-review` (2026-10-05): trục specialized/DSL và interaction/edit, điểm mở rộng, tầng cache pattern reuse và hướng tương lai của hệ Tin học đã gỡ.
> Nguồn: `docs/ARCHITECTURE_MAP.md` tại commit `4048ff83d14ad2a1fcd940d127590ca777dbc7cf` (blob `06bef93306dc8f60f89d8245d4fa826adbae21ae`). Mỗi khối dưới đây là **nguyên văn** (byte-identical)
> các dòng ghi trong chú thích của nó, theo thứ tự của bản gốc. Đây là lịch sử: không sửa, không thêm.
> Đường dẫn tương đối trong các khối viết cho thư mục `docs/`, nên từ `legacy/` chúng trỏ lệch một cấp
> (`README.md`). Kiểm lại: `docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --verify`.

<!-- khối 1/4 · dòng 366–385 của bản gốc · §6: specialized/DSL and interaction/edit axes of the removed system · sha256 43fe069daed0cb77004c285dfb113eb2d052aef2a9bd398595d7880afe372505 -->
**Specialized ↔ Generic DSL.** Specialized = engine viết tay cho một bài (8
algorithm, logic.and_gate, binary, network) — chính xác tuyệt đối, không dùng
DSL. Generic = `generic.rule_scene` chạy SimulationSpec do AI compose trong DSL.
Gap của DSL **không** được lây sang specialized (bất biến #5).

**Interaction ↔ Edit.** *Interaction* đổi **state** (toggle/drag/what-if) qua
`module.apply` — spec không đổi. *Edit* đổi **cấu trúc spec** qua SimulationPatch
→ validate → rebuild. Không được trộn hai đường; UI không tự sửa scene.

*EditPolicy v1 (M7.14D)*: thao tác sửa được suy từ **cấu trúc spec**, không mặc
định giống nhau cho mọi cảnh generic — `spatial` (node/edge: thêm điểm/nối/xóa),
`structural` (container/heading/paragraph: thêm/sửa/xóa nội dung, **không** thêm
điểm), `value_only` (switch/lamp/value_box: chỉ tương tác sẵn có), `observation`
(có `move_along_path`: **khóa topology**). reason_code hai namespace: `policy.*`
(không hợp năng lực cảnh) vs `structure.*` (vi phạm luật DSL).
**LIMITATION có chủ đích**: cảnh LAI (vừa structural vừa node/edge) dùng
precedence bảo thủ (`move > structural > spatial > value_only`) — **multi-family
edit CHƯA được hỗ trợ**. `EditFamily` là phân loại của EditPolicy **v1**, không
phải taxonomy vĩnh viễn của hệ (taxonomy vĩnh viễn là `SEMANTIC_ROLES`).

<!-- hết khối 1 -->

<!-- khối 2/4 · dòng 393–409 của bản gốc · §7: extension points of the removed system · sha256 6ea0d4baa76ad1e43fbd952311caa6595de191582d2817339abf93b06e17a81e -->
## 7. Điểm mở rộng

- **Domain chuyên biệt mới**: thêm `SimSpec` vào `catalog.py` + validator, tạo
  `frontend/src/simulations/domains/<domain>/` và một dòng `register…()`. Không
  đụng pipeline/store/registry.
- **Primitive DSL mới**: **chỉ sửa manifest** — validator, contract prompt,
  capability summary, `_GENERIC_SCHEMA` enum đều tự dẫn xuất. Nhớ mirror TS.
- **Suite eval mới**: gắn `tags` trong `dataset.py`.
- **Capability tùy chọn của module**: thêm field optional vào `SimulationModule`
  (tiền lệ: `timeline?` → `SimulationControls` hiện nút theo capability). Module
  không khai → UI mặc định **không** cho tính năng đó.
- **Renderer mới cho module có sẵn (M8)**: khai `renderers[mode]` + thêm mode vào
  `supportedVisualModes` — cả hai điều kiện mới có toggle (chống affordance rỗng).
  KHÔNG tạo simulation_id mới, KHÔNG fork engine, KHÔNG đụng store/registry/pipeline.
  Renderer nặng (Three.js) nạp qua `React.lazy` để code-split. Tiền lệ:
  `network/ui3d.tsx`.

<!-- hết khối 2 -->

<!-- khối 3/4 · dòng 491–495 của bản gốc · §9: pattern-reuse tier and the M7.14 edit path · sha256 09eb5be999938244e19e1f76c7e0c043762994c4bd71ce9b2e03f1f1302ee5ff -->
- **Tầng 2 — pattern reuse** (`patterns.py`, bảng `simulation_patterns`): **sau
  classify**, chỉ generic; matching **tất định** (không embedding); template đóng
  băng cấu trúc/op, chỉ điền content slot; mọi spec adapt vẫn qua **4 cổng**.
- Edit (M7.14) **không** ghi cache, **không** persist pattern (chống poison).

<!-- hết khối 3 -->

<!-- khối 4/4 · dòng 496–503 của bản gốc · §10: future directions of the informatics system · sha256 c2d1718bd1d573fe3454993713df3ab2a017b0b6361efdd27ccefed095ebea7d -->
## 10. Hướng khả dĩ trong tương lai (chưa làm, không phải cam kết)

- **M7.15 — Minimal Constraint-Aware Geometry**: projection/perpendicular/
  intersection/circle thành **rule tất định** → khi đó `invalid_with_feedback`
  mới có producer thật và generic experimental branch mới có nền.
- **`code_experiment`** (deferred): nếu sau này cho học sinh chạy code, **bắt
  buộc** sandbox (vd Pyodide), **không được bypass engine tất định**, và dự án
  **không** pivot thành IDE/code playground.
<!-- hết khối 4 -->
