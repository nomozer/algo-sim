# frontend-freeze — handoff cho CLOUD (kiến trúc hình học và backend)

Viết cho: phiên agent Cloud đầu tiên của giai đoạn backend. Đọc trước khi sửa: `AGENTS.md` → `docs/RULES.md` →
`docs/ARCHITECTURE_MAP.md` §2–§8 → `docs/MIGRATION_CHECKLIST.md` → `docs/OPEN_ISSUES.md` (mục `default_switch_blocker: YES`)
→ `docs/CODE_INDEX.md`. Frontend **đóng băng** (`report.md`): không giao, không nhận việc UI.

## 1. Pipeline đang chạy — hợp đồng phải bảo toàn

`LLM_ONLY` (mặc định, tuyến duy nhất được nối): đề → `detect_domain` (tất định) → `stage_semantic_analyze` (LLM) →
`RequestContract` → `stage_semantic_program` (LLM, ≤ 3 lần) → **Semantic Program** (bước dựng; IR ở
`backend/app/simulation/semantic_program/contract.py`) → `ir_static_check` · grounding · coverage → interpreter → nhân hình học
`backend/app/simulation/geometry/` (hữu tỉ + căn, chính xác) → checkers/hậu điều kiện → `pipeline_adapter` → **Scene3D** →
envelope → Three.js.

Bất biến không được phá:
- **R0**: LLM không phán toạ độ; mọi toán hạng hình học trong IR là TÊN vật đã dựng (cưỡng chế ở lược đồ).
- Tính đúng thuộc engine tất định; fail-closed (`unsupported`/`inconsistent`), không xấp xỉ gây hiểu lầm.
- Không hardcode mã ca, nhãn đỉnh, dữ kiện, đáp số.
- Đổi lược đồ/prompt/thẻ văn phạm/bảng năng lực = đổi **bề mặt mô hình** ⇒ đo lại + quyết `CACHE_VERSION` bằng bằng chứng;
  `contract.py` đổi ⇒ chạy `scripts/export_semantic_program_schema.py` (hai bản).
- Envelope/Scene3D là hợp đồng với frontend đang đóng băng: thêm trường được, **không đổi nghĩa trường cũ**.
- Đổi chế độ mặc định sang compiler-first: chỉ khi đủ 20 cổng `MIGRATION_CHECKLIST.md` + quyết định riêng của người dùng.

## 2. Hiện trạng tuyến tất định (có nhưng chưa bật)

`backend/app/simulation/geometry_compiler/`: `contract_adapter.py` (RequestContract → `GeometryFactGraph`), `fact_graph.py`,
`primitives.py`, `routing.py` (`che_do()`; `GEOMETRY_COMPILER_MODE`), `compiler.py` sinh Semantic Program cho **6 họ thể tích**
(`SUPPORTED_FAMILIES`: chóp đáy tam giác vuông, lăng trụ tam giác vuông, chóp đáy chữ nhật, hộp chữ nhật, lập phương, lăng trụ
tứ giác đều) rồi đi qua nguyên bộ cổng của tuyến LLM. 20 cổng: PROVED_ON_PILOT 8 · PARTIAL 4 · NOT_STARTED 7 · PRODUCTION_READY 1
(NOT_STARTED: GATE-10 hidden lines, 11 routing, 12 fallback, 13 canary, 14 rollback, 15 holdout, 20 sư phạm). Blocker mở:
`ISSUE-ARCH-COMPILER-COVERAGE-NARROW`, `…-NO-COMPILER-FIRST-ROUTING`, `…-NO-FALLBACK-MECHANISM`, `…-NO-CANARY-OR-ROLLBACK`,
`…-PRISM-COMPILER-GAP`, `…-REQUEST-CONTRACT-PRISM-GAP`. Năng lực SẢN PHẨM ≠ năng lực HỆ: `simulation/product_capability.py`;
họ hình trong phạm vi: `docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json`.

## 3. Hướng nghiên cứu (chưa có tài liệu trong kho — bắt đầu từ đây)

Đề → biểu diễn dữ kiện hình học có cấu trúc → FactGraph/compiler → kernel → Scene3D. **Compact DSL** và **JSON dữ kiện** là
hai ứng viên biểu diễn phải được đánh giá ĐỘC LẬP (cùng corpus, cùng tiêu chí đăng ký trước), không mặc định bên nào tốt hơn
khi chưa đo. Semantic Program hiện có là IR bước dựng, không phải biểu diễn dữ kiện — đừng nhập hai tầng.

## 4. Phạm vi đề xuất cho lượt Cloud đầu tiên

1. Rà soát kiến trúc: chỉ ra chính xác nút thắt khiến mỗi dạng toán mới cần mã riêng (bằng chứng: mã + `SUPPORTED_FAMILIES`
   + các nhánh theo họ), không suy từ tên.
2. Viết hợp đồng vào/ra ổn định giữa AI ↔ biểu diễn dữ kiện ↔ compiler ↔ kernel ↔ renderer (`docs/architecture/`), có lược
   đồ và ví dụ dương/âm.
3. Mở rộng primitive/phép dựng tái sử dụng được (không theo họ), mỗi cái có invariant + oracle độc lập.
4. Một vertical slice chứng minh mở rộng được: một quan hệ/phép dựng mới phục vụ ≥ 2 dạng đề khác nhau mà không thêm nhánh
   theo họ.
5. Giữ `LLM_ONLY` chạy được và xanh; mọi đổi tuyến mặc định là quyết định riêng.

Không được tuyên bố «kiến trúc mới hoàn thành» chỉ vì thêm một họ hình hoặc một schema.

## 5. Kiểm thử giai đoạn backend

Unit; property-based/metamorphic khi phù hợp; oracle hình học độc lập (tham khảo
`docs/evaluation/geometry/custodian/geometry_oracle.py` — cố ý khác thuật toán); kiểm hợp đồng dữ liệu; corpus đề độc lập với tập
phát triển (đăng ký trước); bằng chứng JSON. Trình duyệt/ảnh chỉ khi cần xác nhận tích hợp renderer. Gemini: chỉ với
`ALLOW_LIVE_AI=1`, ngân sách + luật dừng đăng ký trước, quyết định người dùng. Offline mặc định: pytest/vitest 0 API call.
