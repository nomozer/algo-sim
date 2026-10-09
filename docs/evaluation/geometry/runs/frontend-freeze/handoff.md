# frontend-freeze — handoff cho CLOUD (mở rộng họ hình trên kiến trúc sẵn có, rồi OCR)

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

## 3. Định hướng (quyết định người dùng 2026-10-09, `APPROVAL.md` §4)

Kiến trúc hình học theo hàm **đã có** — Cloud KHÔNG nghiên cứu, thiết kế lại hay xây kiến trúc mới từ đầu (bản nháp trước của
mục này đề xuất rà soát kiến trúc và so Compact DSL/JSON dữ kiện; đã bỏ theo quyết định trên). Giai đoạn tiếp theo:
**mở rộng các họ hình còn thiếu theo roadmap đã thống nhất**, tận dụng kiến trúc, hàm và cơ chế sẵn có. Sau giai đoạn ấy:
**OCR** theo kế hoạch (ROADMAP §0.4, P4 — hiện bằng chứng FIXTURE). Frontend đóng băng: chỉ sửa lỗi nghiêm trọng ảnh hưởng
chức năng cốt lõi.

## 4. Phạm vi lượt Cloud đầu tiên

1. Chọn họ kế tiếp từ bảng ứng viên `docs/ROADMAP.md` §0.2 theo thứ tự người dùng duyệt (ROADMAP: «người dùng chọn họ hình
   từ bảng ứng viên §0.2»), đối chiếu `docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json` và
   `simulation/product_capability.py` — «thêm một họ hình» phải đi qua ma trận ấy trước.
2. Hiện thực bằng primitive/phép dựng/luật compiler **tổng quát, dùng lại được**, trên `semantic_program/`, `geometry/`,
   `geometry_compiler/` hiện có — không nhánh theo mã đề, không hardcode dữ kiện/đáp số; mở IR chỉ khi thiếu thật (hỏi trước:
   thiếu năng lực hay chỉ thiếu cách nói cho mô hình biết).
3. Giữ `LLM_ONLY` là mặc định và xanh; mọi đổi tuyến mặc định là quyết định riêng.
4. Hồi quy bắt buộc §0.3 của ROADMAP (sáu họ compiler, corpus gold, demo, bề mặt sập, T3) — không hàng đang phục vụ nào bị
   từ chối mới mà không có quyết định ghi trước.

Không tuyên bố «xong» chỉ vì thêm một họ hay một schema: phải có hợp đồng, invariant, oracle độc lập và hồi quy.

## 5. Kiểm thử giai đoạn backend

Unit; property-based/metamorphic khi phù hợp; oracle hình học độc lập (tham khảo
`docs/evaluation/geometry/custodian/geometry_oracle.py` — cố ý khác thuật toán); kiểm hợp đồng dữ liệu; corpus đề độc lập với tập
phát triển (đăng ký trước); bằng chứng JSON. Trình duyệt/ảnh chỉ khi cần xác nhận tích hợp renderer. Gemini: chỉ với
`ALLOW_LIVE_AI=1`, ngân sách + luật dừng đăng ký trước, quyết định người dùng. Offline mặc định: pytest/vitest 0 API call.
